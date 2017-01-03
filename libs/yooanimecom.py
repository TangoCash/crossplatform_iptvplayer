# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CBaseHostClass
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
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class YooanimeComApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'http://yooanime.com/'
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('yooanimecom.cookie')
        
        self.http_params = {}
        self.http_params.update({'header':self.HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        
        self.cacheList = {}
    
    def getList(self, cItem):
        printDBG("YooanimeComApi.getChannelsList")
        channelsTab = []
        initList = cItem.get('init_list', True)
        if initList:
            rm(self.COOKIE_FILE)
            self.cacheList = {}
            sts, data = self.cm.getPage(self.MAIN_URL, self.http_params)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'id="menu">', '<div class="row">', False)[1]
            data = data.split('</i>')
            for item in data:   
                tmp = item.split('<ul')
                if len(tmp) != 2: continue
                channels = []
                catTtile = self.cleanHtmlStr(tmp[0])
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp[1], '<li class="channel"', '</li>')
                for channelItem in tmp:
                    url   = self.cm.ph.getSearchGroups(channelItem, '''href=['"]([^'^"]+?)['"]''')[0]
                    icon  = self.getFullUrl(self.cm.ph.getSearchGroups(channelItem, '''src=['"]([^'^"]+?\.jpe?g[^'^"]*)['"]''')[0])
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
        else:
            channelsTab = self.cacheList.get(cItem.get('url', 'None'), [])
        return channelsTab
        
    def _getAttrVal(self, data, attr):
        return self.cm.ph.getSearchGroups(data, '''['"]?%s['"]?\s*:\s*['"]([^'^"]+?)['"]''' % attr)[0]
        
    def getVideoLink(self, cItem):
        printDBG("YooanimeComApi.getVideoLink")
        urlsTab = []
        if len(cItem['url']) < 3: return []
        
        sts, data = self.cm.getPage(self.MAIN_URL, self.http_params)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data,  'li.channel' , '$(document)', False)[1]
        
        printDBG(data)
        
        url     = self.getFullUrl(self._getAttrVal(data, 'url'))
        token   = self._getAttrVal(data, 'token')
        ip      = self._getAttrVal(data, 'ip')
        channel = cItem['url'][2:]
        post_data = {'token':token, 'ip':ip, 'channel':channel}
        
        http_params = dict(self.http_params)
        http_params['header'] = dict(self.AJAX_HEADER)
        http_params['header']['Referer'] = self.MAIN_URL
        
        sts, data = self.cm.getPage(url, http_params, post_data)
        if not sts: return []
        
        videoUrl = self._getAttrVal(data, 'ipadUrl')
        videoUrl = strwithmeta(videoUrl, {'Referer':self.MAIN_URL, 'User-Agent':self.HEADER['User-Agent']})
        urlsTab  = getDirectM3U8Playlist(videoUrl, checkContent=True)
        
        return urlsTab