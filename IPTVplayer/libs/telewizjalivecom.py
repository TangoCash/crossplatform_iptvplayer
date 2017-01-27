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
        
    def getFullUrl(self, url):
        url  = CBaseHostClass.getFullUrl(self, url)
        return url.replace(' ', '%20')
        
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
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="m_title">Kategorie</div>', '</div>', False)[1]
            catTitle = self.cleanHtmlStr(tmp)
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</b>')
            for item in tmp:
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(item)
                params = dict(cItem)
                params.update({'init_list':False, 'url':url, 'title':title})
                channelsTab.append(params)
            if len(channelsTab):
                for item in [{'title':'Najnowsze', 'url':self.getFullUrl('/najnowsze/')}, 
                             {'title':'Najlepsze', 'url':self.getFullUrl('/najlepsze/')}]:
                    params = dict(cItem)
                    params.update({'init_list':False})
                    params.update(item)
                    channelsTab.insert(0, params)
        else:
            sts, data = self.cm.getPage(cItem['url'], self.http_params)
            if not sts: return []
            
            nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a\s*href="([^"]+?)"[^>]*?>></a>''')[0])
            
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div style="width:150px;', '</div>')
            for item in data:
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''<b>([^<]+?)</b>''')[0])
                icon  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                desc  = self.cleanHtmlStr(item)
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'desc':desc, 'icon':icon})
                channelsTab.append(params)
                
            if nextPage != '':
                params = dict(cItem)
                params.update({'title':_('Next page'), 'url':nextPage})
                channelsTab.append(params)
            
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