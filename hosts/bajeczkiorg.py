# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import base64
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://bajeczki.org/'

class BajeczkiOrg(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://bajeczki.org/'
    DEFAULT_ICON  = "http://i.gsmmaniak.pl/gsmmaniak/2012/06/bajki-medium.jpg"

    MAIN_CAT_TAB = [{'icon':DEFAULT_ICON, 'category':'categories',      'title': 'Bajki',  'url':MAIN_URL},
                    {'icon':DEFAULT_ICON, 'category':'search',          'title': _('Search'), 'search_item':True},
                    {'icon':DEFAULT_ICON, 'category':'search_history',  'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  BajeczkiOrg.tv', 'cookie':'bajeczkiorg.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.categoryCache = {}
    
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif url.startswith('/'):
            url = self.MAIN_URL + url[1:]
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)

        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("BajeczkiOrg.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem, category1, category2):
        printDBG("BajeczkiOrg.listCategories")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        #self.categoryCache
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="main-nav">', '<center>', False)[1]
        data = data.split('</ul>')
        
        for cat in data:
            tmp = cat.split('<ul class="sub-menu">')
            if 2 == len(tmp):
                catName = self.cleanHtmlStr(tmp[0])
                tmp = tmp[1]
            else:
                catName = '' 
                tmp = ' '.join( tmp )
                
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
            tab = []
            for item in tmp:
                title = self.cleanHtmlStr(item)
                url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                tab.append({'title':title, 'url':url})
            
            if len(tab):
                params = dict(cItem)
                if catName != '':
                    self.categoryCache[catName] = tab
                    params.update({'category':category1, 'title':catName, 'sub_cat':catName})
                    self.addDir(params)
                else:
                    params = dict(cItem)
                    params['category'] = category2
                    self.listsTab(tab, params)
            
    def listSubCategory(self, cItem, nextCategory):
        printDBG("BajeczkiOrg.listSubCategory")
        subCat = cItem.get('sub_cat', '')
        tab = self.categoryCache.get(subCat, [])
        params = dict(cItem)
        params['category'] = nextCategory
        self.listsTab(tab, params)
            
    def listItems(self, cItem):
        printDBG("BajeczkiOrg.listItems")
        
        url = cItem['url']
        page = cItem.get('page', 1)
        
        if page > 1:
            url += 'page/%d/' % page
        
        if 'search_pattern' in cItem:
            url += '?s=' + cItem['search_pattern']
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="loop-nav-inner">', '</div>', False)[1]
        if '/page/{0}/'.format(page+1) in nextPage:
            nextPage = True
        else: 
            nextPage = False
        
        m2 = '<!-- end #post-'
        #data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="products row">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="post', m2)
        for item in data:   
            # icon
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon == '': icon = cItem.get('icon', '')
            # url
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url == '': continue
            #title
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            #desc
            desc = self.cleanHtmlStr(item.split(m2)[0])
            
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon), 'desc':desc})
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("BajeczkiOrg.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', caseSensitive=False)
        for item in data:
            videoUrl = self._getFullUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', ignoreCase=True)[0])
            if 1 != self.up.checkHostSupport(videoUrl): continue 
            urlTab.append({'name':self.up.getHostName(videoUrl), 'url':videoUrl, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("BajeczkiOrg.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
            urlTab.extend( self.up.getVideoLinkExt(videoUrl) )
        
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("BajeczkiOrg.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['search_pattern'] = urllib.quote(searchPattern) 
        cItem['url'] = self.MAIN_URL
        self.listItems(cItem)
        
    def getFavouriteData(self, cItem):
        return str(cItem['url'])
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        filter   = self.currItem.get("filter", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_subcat', 'list_items')
        elif category == 'list_subcat':
            self.listSubCategory(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, BajeczkiOrg(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('bajeczkiorglogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except Exception:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
