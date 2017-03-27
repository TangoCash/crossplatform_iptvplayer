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
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="archives-menu', '<br>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<ul', '</ul>')
        
        # main
        tmp2 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="catlinksf">', '</ul>')[1]
        tmp.insert(0, tmp2)
        
        keys = ['movies', 'rankings', 'main', 'years'] 
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
            
    def listItems(self, cItem):
        printDBG("DardarkomCom.listItems")
        page      = cItem.get('page', 1)
        post_data = cItem.get('post_data', None) 
        url       = cItem['url'] 
        
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return
        
        pagnationMarker = '<div class="navigation-center">'
        tmp = self.cm.ph.getDataBeetwenMarkers(data, pagnationMarker, '</div>', False)[1]
        if tmp != '': hasPadinationMarker = True
        else: hasPadinationMarker = False
        nextPageUrl = self.cm.ph.getSearchGroups(tmp, '<a[^>]+?href="([^"]+?)"[^>]*?>{0}</a>'.format(page+1))[0]
        if '#' == nextPageUrl:
            if '&' in url and post_data == None:
                nextPageUrl = url.split('&search_start')[0] + '&search_start=%s' % (page+1)
            elif post_data != None:
                nextPageUrl = url
        
        if hasPadinationMarker: m2 = pagnationMarker
        else: m2 = '<div class="footer">'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="main-news"', m2, True)[1]
        
        data = re.split('<div class="main-news"[^>]*>', data)
        for item in data:
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?online\.html[^"^']*?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="main-news-title">', '</a>', False)[1])
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            desc  = self.cleanHtmlStr(item)
            
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addVideo(params)
        
        if nextPageUrl.startswith('http'):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1, 'url':self._getFullUrl(nextPageUrl)})
            self.addDir(params)
            
    
    def getLinksForVideo(self, cItem):
        printDBG("DardarkomCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        # get tabs names
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="index-tabs">', '</div>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<span', '</span>') 
        tabsNames = []
        for item in tmp:
            tabsNames.append(self.cleanHtmlStr(item))
            
        printDBG(tabsNames)
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="tt-panel"', '<div class="clearleech">') 
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
            if url == '': url = self.cm.ph.getSearchGroups(data, '''window\.open\(\s*['"](https?://[^"^']+?)['"]''', 1, True)[0]
            printDBG(url)
            url = self._getFullUrl( url )
            videoUrl = url
        
        urlTab = []
        if self.cm.isValidUrl(videoUrl):
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
        CHostBase.__init__(self, DardarkomCom(), True, favouriteTypes=[])