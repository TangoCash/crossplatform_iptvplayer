# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json
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
    return 'eskaGO'

class EskaGo(CBaseHostClass):
    # CHANNELS_URL and MAINURL_VOD taken from http://svn.sd-xbmc.org/filedetails.php?repname=sd-xbmc&path=%2Ftrunk%2Fxbmc-addons%2Fsrc%2Fplugin.video.polishtv.live%2Fhosts%2Feskago.py
    CHANNELS_URL =  'http://www.eskago.pl/indexajax.php?action=SamsungSmartTvV1&start=channelsGroups'

    MAINURL_VOD = 'http://www.eskago.pl/indexajax.php?action=MobileApi'

    MAIN_CAT_TAB = [{'category':'channels_group',        'title':_('Kanały'),   'url': CHANNELS_URL},
                    #{'category':'series_list_abc',       'title':_('Seriale'), 'url': SERIES_URL},
                    #{'category':'search',                'title':_('Search'), 'search_item':True},
                    #{'category':'search_history',        'title':_('Search history')} 
                    ]
    
    def __init__(self):
        printDBG("EskaGo.__init__")
        CBaseHostClass.__init__(self, {'history':'Joogle.pl'})
        self.cacheChannels = None
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        return url

    def listsTab(self, tab, cItem):
        printDBG("EskaGo.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _fillChannelsCache(self, url):
        printDBG("EskaGo._fillChannelsCache")
        sts, data = self.cm.getPage(url)
        if not sts: return
        try:
            data = byteify( json.loads(data) )
            self.cacheChannels = data
        except Exception:
            printExc()
            
    def listChannels(self, cItem):
        printDBG("EskaGo.listChannels")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        keysTab = cItem.get('channels_keys_tab', [])
        if 0 == len(keysTab):
            self._fillChannelsCache(cItem['url'])
            keysTab = [{'key':'result', 'meta_data':{}}]
        
        data = self.cacheChannels
        for item in keysTab:
            try:
                data = data[item['key']]
                meta_data = item['meta_data']
            except Exception:
                printExc()
                return
        idx = 0
        for item in data:
            newKeysTab = list(keysTab)
            newKeysTab.append({'key':idx, 'meta_data':{}})
                
            if 'channels' in item:
                title = item.get('title', '').replace("Kanały w klimacie ", '')
                icon  = item.get('image', '')
                newKeysTab.append({'key':'channels', 'meta_data':{}})
                
                params = dict(cItem)
                params.update({'title':title, 'icon':icon, 'channels_keys_tab':newKeysTab})
                self.addDir(params)
            elif 'subChannels' in item:
                title = item.get('name', '')
                newKeysTab.append({'key':'subChannels', 'meta_data':{'type':item.get('type', '')}})
                
                params = dict(cItem)
                params.update({'title':title, 'channels_keys_tab':newKeysTab})
                self.addDir(params)
            elif 'streamUrl' in item:
                title = item.get('name', '')
                if '' == title: title = item.get('subname', '')
                
                type = item.get('type', '')
                if '' == type: type = meta_data.get('type', '')
                
                tmpUrls = []
                if 'streamUrls' in item:
                    streamUrlHD = item['streamUrls'].get('hd', '').strip()
                    streamUrlSD = item['streamUrls'].get('sd', '').strip()
                    if streamUrlHD != '': tmpUrls.append({'name':'HD', 'url':streamUrlHD})
                    if streamUrlSD != '': tmpUrls.append({'name':'SD', 'url':streamUrlSD}) 
                else:
                    streamUrl  = item.get('streamUrl', '')
                    if None == streamUrl: streamUrl = ''
                    else: streamUrl = streamUrl.strip()
                    if streamUrl != '': tmpUrls.append({'name':'Normal', 'url':streamUrl}) 
                
                if len(tmpUrls):
                    params = dict(cItem)
                    params.update( {'title':title, 'urls':tmpUrls} )
                    if type == 'Radio':
                        self.addAudio(params)
                    else:
                        self.addVideo(params)
            idx += 1

    def getLinksForVideo(self, cItem):
        printDBG("EskaGo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        for urlItem in cItem.get('urls', []):
            url = urlItem['url']
            if url.split('?')[0].endswith('m3u8'):
                data = getDirectM3U8Playlist(url, checkExt=False)
                for item in data:
                    item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True})
                    urlTab.append(item)
            else:
                urlTab.append(urlItem)
        
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('EskaGo.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "EskaGo.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listChannels({'name':'category', 'url':EskaGo.CHANNELS_URL})
        else:
            self.listChannels(self.currItem)
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, EskaGo(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('eskagologo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host.cleanHtmlStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Filmy",  "filmy"))
        searchTypesOptions.append(("Seriale","seriale"))
        
        for cItem in cList:
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
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

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
