# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, GetCookieDir, GetPyScriptCmd
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CBaseHostClass
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, getConfigListEntry
import base64
import re
############################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.bilasportpw_port = ConfigInteger(8193, (1024,65535))

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('PORT') + ": ", config.plugins.iptvplayer.bilasportpw_port))
    return optionList
    
###################################################

class BilaSportPwApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL =  'http://www.bilasport.com/'
        self.DEFAULT_ICON_URL = 'https://projects.fivethirtyeight.com/2016-mlb-predictions/images/logos.png'
        self.HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('bilasport.pw.cookie')
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getList(self, cItem):
        printDBG("BilaSportPwApi.getChannelsList")
        mainItemsTab = []
        
        sts, data = self.cm.getPage(self.getMainUrl())
        if not sts: return mainItemsTab
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<table', '</table>')
        for idx in range(len(data)-1, -1, -1):
            sData = self.cm.ph.getAllItemsBeetwenMarkers(data[idx], '<td', '</td>')
            printDBG(sData)
            for item in sData:
                icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''\ssrc=['"]([^'^"]+?)['"]''')[0])
                url  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''\shref=['"]([^'^"]+?)['"]''')[0])
                if url == '': continue
                title = url.split('/')[-1].replace('.html', '').upper()
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
                mainItemsTab.append(params)
            if idx > 0:
                params = dict(cItem)
                params.update({'type':'marker', 'title':'\xE2\x9E\xA2', 'icon':self.DEFAULT_ICON_URL})
                mainItemsTab.append(params)
        
        return mainItemsTab
        
    def getVideoLink(self, cItem):
        printDBG("BilaSportPwApi.getVideoLink")
        urlsTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlsTab
        
        url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
        
        sts, data = self.cm.getPage(url)
        if not sts: return urlsTab
        
        replaceTab = self.cm.ph.getDataBeetwenMarkers(data, 'prototype.open', '};', False)[1]
        printDBG(replaceTab)
        replaceTab = re.compile('''\.replace\(['"](\s*[^'^"]+?)['"]\s*\,\s*['"]([^'^"]+?)['"]''').findall(replaceTab)
        printDBG(replaceTab)
        if len(replaceTab):
            scriptUrl = '|' + base64.b64encode(json_dumps(replaceTab).encode('utf-8'))
        else:
            scriptUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^"^']*?\.js)['"]''', 1, True)[0])
        
        hlsTab = []
        hlsUrl = re.compile('''(https?://[^'^"]+?\.m3u8(?:\?[^'^"]+?)?)['"]''', re.IGNORECASE).findall(data)
        if len(hlsUrl):
            hlsUrl = hlsUrl[-1]
            hlsTab = getDirectM3U8Playlist(hlsUrl, checkContent=True, sortWithMaxBitrate=9000000)
            for idx in range(len(hlsTab)):
                hlsTab[idx]['need_resolve'] = 1
                hlsTab[idx]['url'] = strwithmeta(hlsTab[idx]['url'], {'name':cItem['name'], 'Referer':url, 'priv_script_url':scriptUrl})
            
        return hlsTab
        
    def getResolvedVideoLink(self, videoUrl):
        printDBG("BilaSportPwApi.getResolvedVideoLink [%s]" % videoUrl)
        urlsTab = []
        
        baseUrl = self.cm.getBaseUrl(videoUrl.meta.get('Referer', ''))
        scriptUrl = videoUrl.meta.get('priv_script_url', '')
        
        sts, data = self.cm.getPage(videoUrl)
        if not sts or '#EXTM3U' not in data: return urlsTab
        
        keyUrl = set(re.compile('''#EXT\-X\-KEY.*?URI=['"](https?://[^"]+?)['"]''').findall(data))
        if len(keyUrl):
            keyUrl = keyUrl.pop()
            proto = keyUrl.split('://', 1)[0]
            pyCmd = GetPyScriptCmd('livesports') + ' "%s" "%s" "%s" "%s" "%s" ' % (config.plugins.iptvplayer.bilasportpw_port.value, videoUrl, baseUrl, scriptUrl, self.HTTP_HEADER['User-Agent'])
            meta = {'iptv_proto':'em3u8'}
            meta['iptv_m3u8_key_uri_replace_old'] = '%s://' % proto 
            meta['iptv_m3u8_key_uri_replace_new'] = 'http://127.0.0.1:{0}/{1}/'.format(config.plugins.iptvplayer.bilasportpw_port.value, proto)
            meta['iptv_refresh_cmd'] = pyCmd
        
        videoUrl = urlparser.decorateUrl("ext://url/" + videoUrl, meta)
        return [{'name':'direct', 'url':videoUrl}]