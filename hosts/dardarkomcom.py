# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
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
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://dardarkom.com/'

class DardarkomCom(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://www.dardarkom.com/'
    SEARCH_URL    = MAIN_URL
    DEFAULT_ICON  = "https://lh5.ggpht.com/xTFuZwF3HX9yPcDhbyCNnjDtZZ1l9qEwUVwoWsPW9Pxry9JsNLSPvWpbvL9waHbHMg=h900"
    
    MAIN_CAT_TAB = [{'category':'categories', 'title': _('Categories'),     'url':MAIN_URL+'aflamonline/',  'icon':DEFAULT_ICON, 'filter':'main'},
                    {'category':'categories', 'title': _('Foreign films'),  'url':MAIN_URL+'aflamonline/',  'icon':DEFAULT_ICON, 'filter':'movies'},
                    {'category':'categories', 'title': _('Major rankings'), 'url':MAIN_URL+'aflamonline/',  'icon':DEFAULT_ICON, 'filter':'rankings'},
                    {'category':'categories', 'title': _('By year'),        'url':MAIN_URL+'aflamonline/',  'icon':DEFAULT_ICON, 'filter':'years'},
                    {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  DardarkomCom.tv', 'cookie':'dardarkomcom.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheFilters = {'main':[], 'movies':[], 'rankings':[]}
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
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("DardarkomCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCategories(self, url):
        printDBG("DardarkomCom.fillCategories")
        self.cacheFilters = {'main':[], 'movies':[], 'rankings':[]}
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        #movies and rankings 
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="archives-menu">', '<br>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<ul>', '</ul>')
        
        # main
        tmp2 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="left-menu">', '</ul>')[1]
        tmp.insert(0, tmp2)
        
        keys = ['main', 'movies', 'rankings', 'years'] 
        for idx in range(len(tmp)):
            if idx >= len(keys):
                break
            key  = keys[idx]
            self.cacheFilters[key] = [] 
            categories = self.cm.ph.getAllItemsBeetwenMarkers(tmp[idx], '<a ', '</a>')
            for cat in categories:
                url   = self.cm.ph.getSearchGroups(cat, '''href=['"]([^"^']+?)['"]''')[0]
                title = self.cleanHtmlStr(cat) 
                if url.endswith('/'):
                    title = '[%s] ' % url.split('/')[-2].replace('-', ' ').title() + title
                printDBG(title)
                printDBG(url)
                if 'dardarkom.com' in url and 'series-online' not in url:
                    desc  = self.cm.ph.getSearchGroups(cat, '''title=['"]([^"^']+?)['"]''')[0]
                    self.cacheFilters[key].append({'title':title, 'url':self._getFullUrl(url), 'desc':desc})
        
    def listCategories(self, cItem, nextCategory):
        printDBG("DardarkomCom.listCategories")
        filter = cItem.get('filter', '')
        tab = self.cacheFilters.get(filter, [])
        if 0 == len(tab):
            self.fillCategories(cItem['url'])
        tab = self.cacheFilters.get(filter, [])
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
            
    def listItems(self, cItem, nextCategory='explore_item'):
        printDBG("DardarkomCom.listItems")
        page      = cItem.get('page', 1)
        post_data = cItem.get('post_data', None) 
        url       = cItem['url'] 
        
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return
        
        pagnationMarker = '<div class="pagination"'
        tmp = self.cm.ph.getDataBeetwenMarkers(data, pagnationMarker, '</div>', False)[1]
        nextPageUrl = self.cm.ph.getSearchGroups(tmp, '<a[^>]+?href="([^"]+?)"[^>]*?><span[^>]*?>التالي</span></a>')[0]
        if nextPageUrl == '': nextPageUrl = self.cm.ph.getSearchGroups(tmp, '<a[^>]+?href="([^"]+?)"[^>]*?><span[^>]*?>الصفحة التالية</span></a>')[0]
        if '#' == nextPageUrl:
            if '&' in url and post_data == None:
                nextPageUrl = url.split('&search_start')[0] + '&search_start=%s' % (page+1)
            elif post_data != None:
                nextPageUrl = url
        
        m1 = '<div class="movies-single">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div class="archives-menu">', False)[1]
        data = data.split(m1)
        
        if len(data) and pagnationMarker in data[-1]:
            data[-1] =  data[-1].split(pagnationMarker)[0]
        
        for item in data:
            idx = item.find('<ul>')
            if idx > -1:
                desc = ' ' + self.cleanHtmlStr(item[idx:])
                item = item[0:idx]
            else:
                desc = ' ' + self.cleanHtmlStr(item)
            
            tmp   = self.cm.ph.getSearchGroups(item, '''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''', 2)
            url   = self._getFullUrl( tmp[0] )
            title = ' ' + self.cleanHtmlStr( tmp[1] )
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''data-load-image=['"]([^"^']+?)['"]''')[0] )
            
            if url.startswith('http'):
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
                params['category'] = nextCategory
                self.addVideo(params)
        
        if nextPageUrl.startswith('http'):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1, 'url':self._getFullUrl(nextPageUrl)})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("DardarkomCom.exploreItem")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = data.split('</button>')
        
        # trailer
        if 2 == len(data):
            tmp = self.cm.ph.getDataBeetwenMarkers(data[0], '<iframe', 'Watch Trailer', True)[1]
            videoUrl = self.cm.ph.getSearchGroups(tmp, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
            videoUrl = self._getFullUrl(videoUrl)
            if videoUrl.startswith('http'):
                params = dict(cItem)
                params.update({'title':_('Watch Trailer'), 'url':videoUrl})
                self.addVideo(params)
            del data[0]
        data = data[0]
        
        added = False 
        for m in [('<span style="color: ', '</iframe>', False, True),\
                  ('</iframe>', '<b>', True, True),\
                  ('<iframe ', '</iframe>', False, False)]:
                  
            #"<div style='clear: both;'>"
            if 1 == m[3]:
                idx = data.find('Γλώσσα:')
            else: idx = -1
            if idx > -1:
                tmp = data[idx:]
            else:
                tmp = data
                    
            if 0 == m[2]:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, m[0], m[1])
            else:
                tmp = self.cm.ph.rgetAllItemsBeetwenMarkers(tmp, m[0], m[1])
            
            #printDBG('=============================================================')
            #printDBG(tmp)
            #printDBG('=============================================================')
            
            for item in tmp:
                title = self.cleanHtmlStr(self.cleanHtmlStr(item).replace('\r', ' ').replace('\n', ' '))
                idx = title.find('Επεισόδιο')
                if idx > -1:
                    title = title[idx:]
                if title == "": title = cItem['title']
                videoUrl = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
                videoUrl = self._getFullUrl(videoUrl)
                if not videoUrl.startswith('http'): continue
                params = dict(cItem)
                params.update({'title':title, 'url':videoUrl})
                self.addVideo(params)
                added = True
            if added:
                break
    
    def getLinksForVideo(self, cItem):
        printDBG("DardarkomCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        # get tabs names
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'movies-seasons tabs', '</ul>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>') 
        tabsNames = []
        for item in tmp:
            tabsNames.append(self.cleanHtmlStr(item))
        
        m1 = '<div class="movies-episodes'
        m2 = '<div id="secretpopout'
        if m2 not in data: m2 = 'Vip/index.html'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(m1)
        
        if len(data) != len(tabsNames):
            printDBG('>>>>>>>>>>>>>>>>>>>ERROR<<<<<<<<<<<<<<<<<<<<')
            printDBG('>>>>>>>>>>>>>>>>>>> Something is wrong len(data)[%d] != len(tabsNames)[%d] !!!' % (len(data), len(tabsNames)) )
        
        for idx in range(len(data)):
            item = data[idx]
            if idx < len(tabsNames):
                tabName = self.cleanHtmlStr(tabsNames[idx])
            else:
                tabName = 'ERROR'
            
            url = ''
            if 'ViP' in tabName:
                # vip links are not supported
                continue
            elif 'روابط التحميل' in tabName:
                # download links not supported
                continue
            elif 'إعلان الفيلم' in tabName:
                # trailer
                url = self.cm.ph.getSearchGroups(item, '''file:[^"^']*?["'](http[^'^"]+?)["']''')[0]
                title = _('[Trailer]') + ' ' + tabName
            elif 'باقي السيرفرات' in tabName or '/templates/server/server.htm' in item:
                # diffrents servers
                servers   = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a ', '</a>')
                for server in servers:
                    url   = self._getFullUrl( self.cm.ph.getSearchGroups(server, '''href=['"]([^'^"]+?)['"]''')[0] )
                    title = tabName + ' ' + self.cleanHtmlStr( server )
                    if self.cm.isValidUrl(url):
                        urlTab.append({'name':title, 'url':url, 'need_resolve':1})
                url = ''
            elif 'iframe' in item:
                url = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
                title = tabName
            
            url = self._getFullUrl( url )
            if url.startswith('http'):
                params = {'name':title, 'url':url, 'need_resolve':1}
                if 'الإفتراضي' in title:
                    #when default insert as first
                    urlTab.insert(0, params)
                else:
                    urlTab.append(params)
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("DardarkomCom.getVideoLinks [%s]" % videoUrl)
        
        m1 = '?s=http'
        if m1 in videoUrl:
            videoUrl = videoUrl[videoUrl.find(m1)+3:]
        
        if 'dardarkom.com' in videoUrl or 'darkom.me' in videoUrl or 'jacvideo.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            url = ''
            urlTmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe ', '</iframe>', False, True)
            printDBG(urlTmpTab)
            for urlTmp in urlTmpTab:
                url = self.cm.ph.getSearchGroups(urlTmp, '''location\.href=['"]([^"^']+?)['"]''', 1, True)[0]
                if 'javascript' in url: 
                    url = ''
            if url == '': url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
            url = self._getFullUrl( url )
            videoUrl = url
        
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("DardarkomCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL
        cItem['post_data'] = {'do':'search', 'subaction':'search', 'story':searchPattern}
        if cItem.get('page', 1) > 1:
            cItem['post_data']['search_start'] = cItem['page']
        self.listItems(cItem)

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
        CHostBase.__init__(self, DardarkomCom(), True, favouriteTypes=[]) #, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('dardarkomcomlogo.png')])
    
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
