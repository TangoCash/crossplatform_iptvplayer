# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetPluginDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta

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
from urlparse import urlparse
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from urlparse import urlparse, urljoin

from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
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
    return 'https://ngolos.com/'

class NGolosCOM(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'meczykipl', 'cookie':'meczykipl.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.USER_AGENT = 'Mozilla/5.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'https://www.ngolos.com/images/site.png'
        self.MAIN_URL = None
        self.cacheCategories = []
        
    def selectDomain(self):
        self.MAIN_URL   = 'https://www.ngolos.com/'
        self.SEARCH_URL = self.MAIN_URL + 'videos.php?dosearch=Y&search='
        self.MAIN_CAT_TAB = [{'category':'list_groups', 'title': _('Categories'),   'url':self.getMainUrl()},
                             
                             {'category':'search',          'title': _('Search'), 'search_item':True},
                             {'category':'search_history',  'title': _('Search history'),           },
                            ]
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = {'header':self.HEADER}
        
        return self.cm.getPage(baseUrl, addParams, post_data)
    
    def listGroups(self, cItem, nextCategory):
        printDBG("NGolosCOM.listGroups")
        self.cacheCategories = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table', '</table>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>')
        for groupItem in data:
            groupItem = groupItem.split('<td>')
            if len(groupItem) < 2: continue
            tab = []
            groupTitle = self.cleanHtmlStr(groupItem[0])
            groupUrl   = self.getFullUrl(self.cm.ph.getSearchGroups(groupItem[0], '''href=['"]([^'^"]+?)['"]''')[0])
            if self.cm.isValidUrl(groupUrl):
                tab.append({'title':_("--All--"), 'url':groupUrl})
            groupItem = self.cm.ph.getAllItemsBeetwenMarkers(groupItem[1], '<a', '</a>')
            for item in groupItem:
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                if title == '': title = self.cleanHtmlStr(item)
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if self.cm.isValidUrl(url):
                    tab.append({'title':title, 'url':url})
            if len(tab):
                params = dict(cItem)
                params.update({'category':nextCategory, 'title':groupTitle, 'cat_id':len(self.cacheCategories)})
                self.addDir(params)
                self.cacheCategories.append(tab)
        
    def listCatItems(self, cItem, nextCategory):
        printDBG("NGolosCOM.listCatItems")
        
        catId = cItem.get('cat_id', 0)
        if catId >= len(self.cacheCategories): return 
        
        tab = self.cacheCategories[catId]
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params.update({'good_for_fav':True, 'category':nextCategory})
            self.addDir(params)
             
    def listItems(self, cItem, nextCategory):
        printDBG("NGolosCOM.listItems |%s|" % cItem)
        
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'next-news', '>')[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<section id="mainContent">', '</section>')[1].split('<div class="pagination">')[0]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(item)
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon.startswith('..'): icon = icon[2:]
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon})
            self.addDir(params)
        
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'url':nextPage, 'page':page+1})
            self.addDir(params)
        
    def exploreItem(self, cItem):
        printDBG("OkGoals.exploreItem")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        titles = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, ' <div id="tab-1"', '</strong>')[1].split('</div>')
        for title in tmp:
            title = self.cleanHtmlStr(title) 
            if title != '': titles.append(title)
        
        tmp = re.compile('''['"]([^'^"]*?//config\.playwire\.com[^'^"]+?\.json)['"]''').findall(data)
        tmp.extend(re.compile('<iframe[^>]+?src="([^"]+?)"').findall(data))
        tmp.extend(re.compile('''<a[^>]+?href=['"](https?://[^'^"]*?ekstraklasa.tv[^'^"]+?)['"]''').findall(data))
        urlsTab = []
        for idx in range(len(tmp)):
            if 'facebook' in tmp[idx]: continue
            url = self.getFullUrl(tmp[idx])
            if not self.cm.isValidUrl(url): continue
            if 'playwire.com' not in url and  self.up.checkHostSupport(url) != 1: continue
            urlsTab.append(url)
        
        for idx in range(len(urlsTab)):
            title = cItem['title']
            if len(titles) == len(urlsTab): title += ' - ' + titles[idx]
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':title, 'url':urlsTab[idx]})
            self.addVideo(params)
            
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("OkGoals.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        page = cItem.get('page', 1)
        if page == 1:
            cItem['url'] = self.SEARCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'explore_item')
    
    def getLinksForVideo(self, cItem):
        printDBG("OkGoals.getLinksForVideo [%s]" % cItem)
        urlTab = []
        videoUrl = cItem['url']
        if 'playwire.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            try:
                data = byteify(json.loads(data))
                if 'content' in data:
                    url = data['content']['media']['f4m']
                else:
                    url = data['src']
                sts, data = self.cm.getPage(url)
                baseUrl = self.cm.ph.getDataBeetwenMarkers(data, '<baseURL>', '</baseURL>', False)[1].strip()
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<media ', '>')
                for item in data:
                    url  = self.cm.ph.getSearchGroups(item, '''url=['"]([^'^"]+?)['"]''')[0]
                    height = self.cm.ph.getSearchGroups(item, '''height=['"]([^'^"]+?)['"]''')[0]
                    bitrate = self.cm.ph.getSearchGroups(item, '''bitrate=['"]([^'^"]+?)['"]''')[0]
                    name = '[%s] bitrate:%s height: %s' % (url.split('.')[-1], bitrate, height)
                    if not url.startswith('http'):
                        url = baseUrl + '/' + url
                    if url.startswith('http'):
                        if 'm3u8' in url:
                            hlsTab = getDirectM3U8Playlist(url)
                            for idx in range(len(hlsTab)):
                                hlsTab[idx]['name'] = '[hls] bitrate:%s height: %s' % (hlsTab[idx]['bitrate'], hlsTab[idx]['height'])
                            urlTab.extend(hlsTab)
                        else:
                            urlTab.append({'name':name, 'url':url})
            except Exception:
                printExc()
        elif videoUrl.startswith('http'):
            urlTab.extend(self.up.getVideoLinkExt(videoUrl))
        return urlTab

        
    def getVideoLinks(self, videoUrl):
        printDBG("OkGoals.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('NGolosCOM.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('NGolosCOM.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('NGolosCOM.setInitListFromFavouriteItem')
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
        elif 'list_groups' == category:
            self.listGroups(self.currItem, 'list_cat_items')
        elif 'list_cat_items' == category:
            self.listCatItems(self.currItem, 'list_items')
        elif 'list_items' == category:
            self.listItems(self.currItem, 'explore_item')
        elif 'explore_item' == category:
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
        CHostBase.__init__(self, NGolosCOM(), True, [])

    