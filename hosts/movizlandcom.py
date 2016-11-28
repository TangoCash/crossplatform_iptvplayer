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
    return 'http://movizland.com/'

class MovizlandCom(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://m.movizland.com/'
    SEARCH_URL    = MAIN_URL + '?s='
    DEFAULT_ICON  = "http://vb.movizland.com/movizland/images/logo.png"
    
    MAIN_CAT_TAB = [{'category':'categories',      'title': _('Categories'), 'url':MAIN_URL,      'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True,      'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),                  'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  MovizlandCom.tv', 'cookie':'movizlandcom.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheLinks = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if 0 < len(url) and not url.startswith('http'):
                url =  self.MAIN_URL + url
            if not self.MAIN_URL.startswith('https://'):
                url = url.replace('https://', 'http://')
                
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)

        return url
        
    def _getIconUrl(self, url):
        url = self._getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def getPage(self, baseUrl, params={}, post_data=None):
        params['cloudflare_params'] = {'domain':'m.movizland.com', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self._getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("MovizlandCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
    
    def listCategories(self, cItem, nextCategory):
        printDBG("MovizlandCom.listCategories")
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="tabs-ui">', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li>', '</li>')
        
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''', 1)[0]
            url = self._getFullUrl( url )
            if not url.startswith('http'): continue
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def listItems(self, cItem, nextCategory='explore_item'):
        printDBG("MovizlandCom.listItems")
        page      = cItem.get('page', 1)
        post_data = cItem.get('post_data', None) 
        url       = cItem['url']
        
        if page > 1:
            if url.endswith('/'):
                url += 'page/%d/' % page
            elif '?' not in url:
                url += '?page=%d' % page
            else:
                url += '&page=%d' % page
        
        sts, data = self.getPage(url, self.defaultParams, post_data)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="paging">', '</ul>', False)[1]
        if '>{0}<'.format(page + 1) in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<main ', '</main>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="grid-item ">', '</li>')
        
        for item in data:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a ', '</a>')
            item = ''
            for t in tmp:
                if '<img' in t:
                    item = t
                    break
            if item == '' and len(tmp): item = tmp[-1]
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''', 1)[0]
            if url == '': continue
            title = self.cleanHtmlStr(item)
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''', 1)[0]
            
            url = self._getFullUrl( url )
            url = self._getFullUrl( url )
            
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon)})
            
            if '/movies/ in url':
                self.addVideo(params)
            else:
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("MovizlandCom.exploreItem")
        # not implemented 
        # it seems that there are no series on this service
        return
    
    def getLinksForVideo(self, cItem):
        printDBG("MovizlandCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'class="iframeWide"', '<div class="footer">')[1]
        data = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"]''').findall(data)
        for url in data:
            if 'movizland.com' in url: continue
            if 'moshahda.net' in url and ('embedM-' in url or '?download' in url): continue
            if self.up.checkHostSupport(url) == 1:
                title = self.up.getHostName(url)
                urlTab.append({'name':title, 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("MovizlandCom.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MovizlandCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem)
        
    def getFavouriteData(self, cItem):
        printDBG("MovizlandCom.getFavouriteData")
        return str(cItem['url'])
        
    def getLinksForFavourite(self, fav_data):
        printDBG("MovizlandCom.getLinksForFavourite")
        return self.getLinksForVideo({'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
                self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
                self.listItems(self.currItem)
    #EXPLORE ITEM
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
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
        CHostBase.__init__(self, MovizlandCom(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('movizlandcomlogo.png')])
    
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
        
    #def getArticleContent(self, Index = 0):
    #    retCode = RetHost.ERROR
    #    retlist = []
    #    if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
    #
    #    hList = self.host.getArticleContent(self.host.currList[Index])
    #    for item in hList:
    #        title      = item.get('title', '')
    #        text       = item.get('text', '')
    #        images     = item.get("images", [])
    #        othersInfo = item.get('other_info', '')
    #        retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
    #    return RetHost(RetHost.OK, value = retlist)
    
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
        icon        =  self.host._getIconUrl( cItem.get('icon', '') )
        
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
