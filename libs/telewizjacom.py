# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
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
config.plugins.iptvplayer.iklubnet_categorization  = ConfigYesNo(default = True)

def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class TeleWizjaComApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'http://tele-wizja.com/'
        self.HTTP_HEADER = { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        self.COOKIE_FILE = GetCookieDir('telewizjacom.cookie')
        self.PROXY_URL   = 'http://www.proxy-german.de/index.php?q={0}&hl=2e5'
        self.http_params = {}
        self.useProxy    = False
        #self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        
    def getFullUrl(self, url):
        if 'proxy-german.de' in url and '?q=' in url:
            url = url.split('?q=')[1]
            if '&nf=' in url: url = url.split('&nf=')[0]
            url = urllib.unquote(url)
        return CBaseHostClass.getFullUrl(self, url)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if self.useProxy:
            proxy = self.PROXY_URL.format(urllib.quote(url, ''))
            params = {}
            params['User-Agent'] = self.HTTP_HEADER['User-Agent'],
            params['Referer']    = proxy
            params['Cookie']     = 'flags=2e5;'
            url = strwithmeta(proxy, params) 
        return url
        
    def getPage(self, url, params={}, post_data=None):
        
        if self.useProxy:
            params.update({'header':self.HTTP_HEADER})
            proxy = self.PROXY_URL.format(urllib.quote_plus(url))
            params['header']['Referer'] = proxy
            url = proxy
        return self.cm.getPage(url, params, post_data)
        
    def getListOfChannels(self, cItem):
        printDBG("TeleWizjaComApi.getListOfChannels")
        #cItem['url']
        sts, data = self.getPage(self.MAIN_URL, self.http_params)
        if not sts: return []
        
        retList = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<figure', '</figure>')
        printDBG(data)
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            url = self.getFullUrl(url)
            if url == '': continue
            title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0]
            if title == '': title = url.split('/')[-1].replace('.html', '')
            icon = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon == '': icon = self.cm.ph.getSearchGroups(item, '''data-original=['"]([^'^"]+?)['"]''')[0]
            
            params = dict(cItem)
            params.update({'type':'video', 'url':url, 'title':title, 'icon':self.getIconUrl(icon)})
            retList.append(params)
        return retList
        
    def getList(self, cItem):
        printDBG("TeleWizjaComApi.getChannelsList")
        channelsTab = []
        return self.getListOfChannels(cItem)
        
        initList = cItem.get('init_list', True)
        if initList:
            retList = []
            sts, data = self.getPage(self.getFullUrl(self.MAIN_URL), self.http_params)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="menu_nav">', '</ul>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                title = self.cleanHtmlStr(item)
                if url == '': continue
                if 'transmisje.html' in url: continue
                params = dict(cItem)
                params.update({'init_list':False, 'url':self.getFullUrl(url), 'title':title})
                retList.append(params)
            channelsTab = retList
        else:
            channelsTab = self.getListOfChannels(cItem)
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("TeleWizjaComApi.getVideoLink")
        urlsTab = []
         
        sts, data = self.getPage(cItem['url'], self.http_params)
        if not sts: return urlsTab
        
        #m = '<div class="article">'
        #data = self.cm.ph.getDataBeetwenMarkers(data, m, m)[1]
        frameUrl = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', ignoreCase=True)[0] )
        if not self.cm.isValidUrl(frameUrl): return urlsTab
        
        printDBG(frameUrl)
        
        sts, data = self.getPage(frameUrl, self.http_params)
        if not sts: return urlsTab
        
        tmp = re.compile('''(['"]http[^'^"]+?proxy\-german\.de[^'^"]+?['"])''').findall(data)
        for url in tmp:
            stripUrl = self.getFullUrl(url)
            data = data.replace(url, stripUrl)
        printDBG(data)
        return self.up.getAutoDetectedStreamLink(frameUrl, data)