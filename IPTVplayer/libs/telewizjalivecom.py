# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
try:    import json
except Exception: import simplejson as json
############################################

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

class TelewizjaLiveComApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'http://telewizja-live.com/'
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('telewizjalivecom.cookie')
        
        self.http_params = {}
        self.http_params.update({'header':self.HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        
        self.cacheList = {}
        
    def _getMainList(self, cItem):
        printDBG("TelewizjaLiveComApi._getMainList")
        channelsTab = []
        
        sts, data = self.cm.getPage(self.MAIN_URL, self.http_params)
        if not sts: return []
        
        nextCatTtile = ''
        catData = self.cm.ph.getDataBeetwenMarkers(data, '<div id="menu">', '</div>', False)[1]
        catData = catData.split('<ul class="submenu">')
        for item in catData:
            channels = []
            catTitle = nextCatTtile
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li>', '</a>')
            if len(tmp) > 0:
                nextCatTtile = self.cleanHtmlStr(tmp[-1])
            del tmp[-1]
            for channelItem in tmp:
                url   = self.cm.ph.getSearchGroups(channelItem, '''href=['"]([^'^"]+?)['"]''')[0]
                icon  = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''src=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(channelItem)
                if '' == icon: icon = cItem.get('icon', '')
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
                channels.append(params)
            if len(channels):
                self.cacheList[catTtile] = channels
                params = dict(cItem)
                params.update({'init_list':False, 'url':catTtile, 'title':catTtile})
                channelsTab.append(params)
        
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content">', '</div>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for channelItem in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(channelItem)
            try: 
                if title == '': title = '.'.join(icon.split('/')[-1].split('.')[:-1]).title()
            except Exception: printExc()
            if '' == icon: icon = cItem.get('icon', '')
            params = dict(cItem)
            params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
            channelsTab.append(params)
        return channelsTab
        
    def getList(self, cItem):
        printDBG("TelewizjaLiveComApi.getChannelsList")
        channelsTab = []
        
        #return self._getMainList(cItem)
        
        initList = cItem.get('init_list', True)
        if initList:
            rm(self.COOKIE_FILE)
            self.cacheList = {}
            sts, data = self.cm.getPage(self.MAIN_URL, self.http_params)
            if not sts: return []
            
            channels = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content">', '</div>', False)[1]
            catTitle = self.cleanHtmlStr(tmp)
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
            for channelItem in tmp:
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''href=['"]([^'^"]+?)['"]''')[0])
                icon  = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''src=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(channelItem)
                try: 
                    if title == '': title = '.'.join(icon.split('/')[-1].split('.')[:-1]).title()
                except Exception: printExc()
                if '' == icon: icon = cItem.get('icon', '')
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
                channels.append(params)
            if len(channels):
                self.cacheList[catTitle] = channels
                params = dict(cItem)
                params.update({'init_list':False, 'url':catTitle, 'title':catTitle})
                channelsTab.append(params)
            
            nextCatTtile = ''
            catData = self.cm.ph.getDataBeetwenMarkers(data, '<div id="menu">', '</div>', False)[1]
            catData = catData.split('<ul class="submenu">')
            for item in catData:
                channels = []
                catTitle = nextCatTtile
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li>', '</a>')
                if len(tmp) > 0:
                    nextCatTtile = self.cleanHtmlStr(tmp[-1])
                del tmp[-1]
                for channelItem in tmp:
                    url   = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''href=['"]([^'^"]+?)['"]''')[0])
                    icon  = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''src=['"]([^'^"]+?)['"]''')[0])
                    title = self.cleanHtmlStr(channelItem)
                    if '' == icon: icon = cItem.get('icon', '')
                    params = dict(cItem)
                    params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
                    channels.append(params)
                if len(channels):
                    self.cacheList[catTitle] = channels
                    params = dict(cItem)
                    params.update({'init_list':False, 'url':catTitle, 'title':catTitle})
                    channelsTab.append(params)
        else:
            channelsTab = self.cacheList.get(cItem.get('url', 'None'), [])
        return channelsTab
        
    def _getAttrVal(self, data, attr):
        return self.cm.ph.getSearchGroups(data, '''['"]?%s['"]?\s*:\s*['"]([^'^"]+?)['"]''' % attr)[0]
        
    def getVideoLink(self, cItem):
        printDBG("TeleWizjaComApi.getVideoLink")
        urlsTab = []
         
        sts, data = self.cm.getPage(cItem['url'], self.http_params)
        if not sts: return urlsTab
        
        #m = '<div class="article">'
        #data = self.cm.ph.getDataBeetwenMarkers(data, m, m)[1]
        frameUrl = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', ignoreCase=True)[0] )
        if not self.cm.isValidUrl(frameUrl): return urlsTab
        
        printDBG(frameUrl)
        
        sts, data = self.cm.getPage(frameUrl, self.http_params)
        if not sts: return urlsTab
        
        printDBG(data)
        return self.up.getAutoDetectedStreamLink(frameUrl, data)