# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import urllib
import string
import random
import base64
import hashlib
from binascii import hexlify, unhexlify
from urlparse import urlparse, urljoin
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
    return 'http://videopenny.net/'

class VideoPenny(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'video.penny.ie', 'cookie':'video.penny.ie.cookie', 'cookie_type':'MozillaCookieJar'})
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.DEFAULT_ICON_URL = 'http://videopenny.net/wp-content/uploads/icons/VideoPennyNet-logo_126x30.png'
        self.MAIN_URL = None
        self.cacheSeries = []
        self.cachePrograms = []
        self.cacheLast = {}

        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self._getHeaders = None
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urljoin(baseUrl, url)
        
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def getFullUrl(self, url):
        url = CBaseHostClass.getFullUrl(self, url)
        try: url.encode('ascii')
        except Exception: url = urllib.quote(url, safe="/:&?%@[]()*$!+-=|<>;")
        return url
        
    def selectDomain(self):                
        self.MAIN_URL = 'http://videopenny.net/'
        self.MAIN_CAT_TAB = [{'category':'list_sort_filter',    'title': 'Seriale',           'url':self.getFullUrl('/kategoria-2/seriale-pl'),           'icon':self.getFullIconUrl('/wp-content/uploads/2014/05/Seriale-tv.png')},
                             {'category':'list_sort_filter',    'title': 'Programy online',   'url':self.getFullUrl('/kategoria-2/programy-rozrywkowe'),  'icon':self.getFullIconUrl('/wp-content/uploads/2014/05/Programy-online.png')},
                             {'category':'list_sort_filter',    'title': 'Filmy',             'url':self.getFullUrl('/category/filmy-pl/'),               'icon':self.getFullIconUrl('/wp-content/uploads/2014/05/Filmy.png')},
                             {'category':'list_sort_filter',    'title': 'Bajki',             'url':self.getFullUrl('/category/bajki/'),                  'icon':self.getFullIconUrl('/wp-content/uploads/2014/05/Bajki-tv.png')},
                             {'category':'list_last',           'title': 'Ostatnio dodane',   'url':self.getFullUrl('/ostatnio-dodane/')},
                             
                             {'category':'search',          'title': _('Search'), 'search_item':True, },
                             {'category':'search_history',  'title': _('Search history'),             } 
                            ]
            
    def listSortFilters(self, cItem, nextCategory):
        printDBG("VideoPenny.listSortFilters")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'video-listing-filter', '</div>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':title, 'url':url, 'category':nextCategory})
            self.addDir(params)
                
    def listItems(self, cItem, nextCategory=None):
        printDBG("VideoPenny.listItems")
        
        uniqueTab = []
        dirsTab = []
        
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a[^>]+?class=["']nextpostslink['"][^>]+?href=['"]([^"^']+?)['"]''')[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'listing-content', '</section>')[1]
        data = data.split('<div id="post')
        for item in data:
            if 'item-head"' not in item: continue
            
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>')[1])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data-lazy-src=['"]([^'^"]+?)['"]''')[0])
            if icon == '': icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''\ssrc=['"]([^'^"]+?)['"]''')[0])
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>')[1])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            if nextCategory != None and ('/seriale' in url or '/programy' in url) and not cItem.get('was_explored', False):
                params['category'] = nextCategory
                self.addDir(params)
            else:
                self.addVideo(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'url':nextPage, 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem, nextCategory):
        printDBG("VideoPenny.exploreItem")
        
        params = dict(cItem)
        self.addVideo(params)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'breadcrumbs'), ('</div', '>'))[1]
        data = self.cm.ph.rgetDataBeetwenNodes(data, ('</a', '>'), ('<a', '>'))[1]
        url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''\shref=['"]([^'^"]+?)['"]''')[0])
        title = self.cleanHtmlStr(data)
        if url != '':
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'category':nextCategory, 'was_explored':True})
            self.addDir(params)
        
    def listLast(self, cItem, nextCategory):
        printDBG("VideoPenny.listLast")
        self.cacheLast = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<article', '</article>')[1]
        data = data.split('<div class="smart-box-head"')
        if len(data): del data[0]
        for section in data:
            sectionTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(section, '<h2', '</h2>')[1])
            if sectionTitle == '': sectionTitle = 'Inne'
            section = section.split('<div class="video-item format')
            if len(section): del section[0]
            itemsTab = []
            for item in section:
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>')[1])
                if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                icon  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data-lazy-src=['"]([^'^"]+?)['"]''')[0])
                if icon == '': icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''\ssrc=['"]([^'^"]+?)['"]''')[0])
                desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>')[1])
                itemsTab.append({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            
            if len(itemsTab):
                self.cacheLast[sectionTitle] = itemsTab
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':sectionTitle, 'cache_key':sectionTitle})
                self.addDir(params)
    
    def listLastItems(self, cItem):
        printDBG("VideoPenny.listLastItems")
        cacheKey = cItem.get('cache_key', '')
        tab = self.cacheLast.get(cacheKey, [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("VideoPenny.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 1)
        
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('page/%s/?s=%s' % (page, urllib.quote_plus(searchPattern)))
        self.listItems(cItem, 'explore_item')
    
    def getLinksForVideo(self, cItem):
        printDBG("VideoPenny.getLinksForVideo [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        urlTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player-embed', '</div>')[1]
        tmp += '\n'.join(self.cm.ph.getAllItemsBeetwenNodes(data, ('<', '>', 'multilink'), ('</a', '>')))
        data = tmp
        printDBG(data)
        tmp = re.compile('''['"](\s*https?://[^"^']+?)\s*['"]''').findall(data)
        printDBG(tmp)
        for item in tmp:
            playerUrl = item.strip()
            if not self.cm.isValidUrl(playerUrl): continue
            if 1 != self.up.checkHostSupport(playerUrl): continue 
            urlTab.append({'name':self.up.getDomain(playerUrl, False), 'url':playerUrl, 'need_resolve':1})
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>')
        for item in tmp:
            if 'video/mp4' not in item and 'video/x-flv' not in item: continue
            type  = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].replace('video/', '')
            url   = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            label = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0]
            if label == '': label = self.cm.ph.getSearchGroups(item, '''res=\s*([^\s]+?)[\s>]''')[0]
            printDBG(url)
            if self.cm.isValidUrl(url):
                urlTab.append({'name':'[%s] %s' % (type, label), 'url':strwithmeta(url)})
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("VideoPenny.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('VideoPenny.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('VideoPenny.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('VideoPenny.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        if self.MAIN_URL == None:
            #rm(self.COOKIE_FILE)
            self.selectDomain()

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_sort_filter':
            self.listSortFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'list_last':
            self.listLast(self.currItem, 'list_last_items')
        elif category == 'list_last_items':
            self.listLastItems(self.currItem)
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_sort_filter')
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
        CHostBase.__init__(self, VideoPenny(), True, [])
    