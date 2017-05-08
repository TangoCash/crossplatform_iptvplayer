# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
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

from os import path as os_path
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

class WiizTvApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL         = 'http://www.wiiz.tv/'
        self.DEFAULT_ICON_URL = self.getFullUrl('logowiiz.png')
        self.HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('wiiztv.cookie')
        self.http_params = {'header':self.HTTP_HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def getFullUrl(self, url):
        if url.startswith('//'): 
            url = 'http:' + url
        return CBaseHostClass.getFullUrl(self, url)
        
    def getFullIconUrl(self, url):
        if url.startswith('//'): 
            url = 'http:' + url
        return CBaseHostClass.getFullIconUrl(self, url)
    
    def getList(self, cItem):
        printDBG("WiizTvApi.getList")
        
        channelsTab = []
        
        category = cItem.get('wiiz_cat')
        if category == None:
            for item in [{'title':'TV', 'wiiz_cat':'list_tv', 'url':self.getFullUrl('/direct.php')}, {'title':'Radio', 'wiiz_cat':'list_radio', 'url':self.getFullUrl('/category/radio')}]:
                params = dict(cItem)
                params.update(item)
                channelsTab.append(params)
        elif category == 'list_tv':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return channelsTab
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul style="text-align:center" class="w3-navbar">', '</ul>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
            for item in data:
                event = self.cm.ph.getSearchGroups(item, '''event\,\s*['"]([a-z]+?)["']''')[0]
                if event == '': continue
                
                icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                printDBG(icon)
                title = event.upper()
                params = dict(cItem)
                params.update({'title':title, 'icon':icon, 'wiiz_event':event, 'wiiz_cat':'list_tv_channels'})
                channelsTab.append(params)
        elif category == 'list_tv_channels':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return channelsTab
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="%s"' % cItem['wiiz_event'], '</div>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                if title == '': title =  self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'icon':icon, 'url':url, 'wiiz_cat':'video'})
                channelsTab.append(params)
        elif category == 'list_radio':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return channelsTab
            data = self.cm.ph.getDataBeetwenMarkers(data, '<a class="btncatehome"', '</tbody>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                title = self.cleanHtmlStr(item)
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'wiiz_cat':'list_radio_channels'})
                channelsTab.append(params)
        elif category == 'list_radio_channels':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return channelsTab
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<td width="95" valign="top">', '</tbody>')
            for item in data:
                url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                title =  self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
                params = dict(cItem)
                params.update({'type':'audio', 'title':title, 'icon':icon, 'url':url, 'wiiz_cat':'radio'})
                channelsTab.append(params)
                
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("WiizTvApi.getVideoLink")
        urlsTab = []
        videoUrl = cItem['url']
        if cItem['type'] != 'video':
            sts, data = self.cm.getPage(videoUrl)
            if sts:
                playerUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](http[^'^"]+?/player/[^'^"]+?)['"]''')[0]
                if self.cm.isValidUrl(playerUrl):
                    videoUrl = playerUrl
        urlsTab = self.up.getVideoLinkExt(videoUrl)
        return urlsTab
