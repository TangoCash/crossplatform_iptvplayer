# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import urllib
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
    return 'Veetle.com'

class Veetle(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    
    MAIN_URL = 'http://veetle.com/'
    DEFAULT_ICON = 'https://lh4.ggpht.com/-1pIpAXI_87mxWc1776Jq6GBwj6wDnkzvGoltoZzf3PALPMSk2Pmi7Y06NFr0KwisQ=w300'
    MAIN_CAT_TAB = [{'category':'category',        'title':_('Explore'), 'url':MAIN_URL+'index.php/listing', 'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]

 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Veetle.com', 'cookie':'veetlecom.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Veetle.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def parseJSdata(self, url):
        self.cache = {'cats':[], 'sort_keys':[], 'version':'2.0'}
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return
        
        catData = self.cm.ph.getDataBeetwenMarkers(data, 'VEETLE.ChannelList.category={};', 'VEETLE.ChannelList.sort={};', False)[1]
        catData = re.compile('\.category\.([^;]+?)=([0-9]+?);').findall(catData)
        for item in catData:
            self.cache['cats'].append({'title':item[0].title(), 'cat':item[0], 'cat_id':item[1]})
            
        sortData = self.cm.ph.getDataBeetwenMarkers(data, 'VEETLE.ChannelList.sort={};', 'VEETLE.ChannelList.instance', False)[1]
        sortData = re.compile('\.sort\.([^;]+?)="([^"]+?)";').findall(sortData)
        for item in sortData:
            self.cache['sort_keys'].append({'title':item[0], 'sort':item[1]})
            
        self.cache['version'] = self.cm.ph.getSearchGroups(data, 'VEETLE.SearchHttp.SUPPORTED_VERSION="([^"]+?)";')[0]
        
    def listCategory(self, cItem, category):
        printDBG("Veetle.listCategory")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        jsUrl = self.cm.ph.getSearchGroups(data, '<script[^>]+?src="([^"]+?_minified\.js)"')[0]
        self.parseJSdata(self._getFullUrl(jsUrl))
        
        for item in self.cache['cats']:
            params = dict(cItem)
            params.update(item)
            params['category'] = category
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("Veetle.listItems")
        page   = cItem.get('page', 0)
        catId  = cItem.get('cat_id', '')
        search = cItem.get('search', '')
        
        ITEMS = 39
        if search != '' or cItem.get('cat', '') in ['all', 'mobile']:
            searchUrl   = 'index.php/stream/ajaxStreamBySearch/%s/%s/0/2.0/' % (page*ITEMS, ITEMS) + search
            url = searchUrl
        else:
            categoryUrl = 'index.php/listing/ajaxStreamByCategory/%s/%s/%s/0' % (catId, page*ITEMS, ITEMS)
            url = categoryUrl
        
        url = self._getFullUrl(url)

        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))
            if not data['success']: return
            totalCount = data['totalCount']
            totalItems = page*ITEMS + len(data['payload'])
            
            for item in data['payload']:
                params = dict(cItem)
                if True: icon = item['thumbnailUrl']
                else: icon = item['thumbnailUrlSmall']
                title = self.cleanHtmlStr(item['title'])
                if title == '': title = item['username']
                if item.get('isLive', True):
                    title = title + ' [%s]' % _('live')
                desc = self.cleanHtmlStr(item['description'])
                
                params.update({'title':title, 'desc':desc, 'icon':icon, 'channel_id':item['channelId']})
                self.addVideo(params)
            
            if totalItems < totalCount:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':page+1})
                self.addDir(params)
            
        except Exception:
            printExc()
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Veetle.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['search'] = urllib.quote(searchPattern)
        self.listItems(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("Veetle.getLinksForVideo [%s]" % cItem)
        urlTab = []
        from copy import deepcopy
        params = deepcopy(self.defaultParams)
        try:
            channelId = cItem['channel_id']
            url = self._getFullUrl('index.php/channel/view/' + channelId)
            
            sts, data = self.cm.getPage(url, params)
            if not sts: return []
            
            url = self._getFullUrl('index.php/stream/ajaxInfo/' + channelId)
            sts, data = self.cm.getPage(url, params)
            if not sts: return []
            
            data = byteify(json.loads(data))
            if not data['success']: return []
            data = data['payload']
            channelId = data['channelId']
            sessionId = data['sessionId']
            
            linksTypesTab = []
            if data.get('flashEnabled', False):
                linksTypesTab.append('flash')
            if data.get('iPadEnabled', False) or data.get('iPhoneEnabled', False):
                linksTypesTab.append('hls')
            
            for type in linksTypesTab:
                try:
                    baseVidUrl = self._getFullUrl('index.php/stream/ajaxStreamLocation/%s_%s/' %(channelId, sessionId) + type)
                    params['header']['Referer'] = url
                    
                    sts, data = self.cm.getPage(baseVidUrl, params)
                    if not sts: continue
                    data = byteify(json.loads(data))
                    if data['success'] and data['payload'].startswith('http'):
                        if type == 'flash':
                            need_resolve = 0
                        else:
                            need_resolve = 1
                        urlTab.append({'name':type, 'url':data['payload'], 'need_resolve':need_resolve})
                except Exception:
                    printExc()
        except Exception:
            printExc()
        return urlTab
    
    def getResolvedURL(self, url):
        linkTab = getDirectM3U8Playlist(url, False)
        for idx in range(len(linkTab)):
            linkTab[idx]['url'] = urlparser.decorateUrl(linkTab[idx]['url'], {'iptv_proto':'m3u8'})
        return linkTab
        
    def getFavouriteData(self, cItem):
        return cItem['channel_id']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'channel_id':fav_data})
        
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
        elif category == 'category':
            self.listCategory(self.currItem, 'list_items')
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
        CHostBase.__init__(self, Veetle(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('veetlelogo.png')])
    
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
        urlList = self.host.getResolvedURL(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
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
