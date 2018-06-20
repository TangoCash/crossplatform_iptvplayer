# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetPyScriptCmd
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

from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, ConfigInteger, getConfigListEntry
import base64
import re
import urllib
import random
import string
try:    import json
except Exception: import simplejson as json
from datetime import datetime, timedelta
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
config.plugins.iptvplayer.livesports_port = ConfigInteger(8193, (1024,65535))
config.plugins.iptvplayer.livesports_domain = ConfigText(default = "http://suphd.club/", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('PORT') + ": ", config.plugins.iptvplayer.livesports_port))
    optionList.append(getConfigListEntry(_('Service domain') + ": ", config.plugins.iptvplayer.livesports_domain))
    return optionList
    
###################################################


class LiveSportsApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL =  'http://suphd.club/' #'http://174.138.49.107/'
        self.DEFAULT_ICON_URL = 'https://i.ytimg.com/vi/_6ymsk8ESrI/hqdefault.jpg'
        self.HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('livesports.cookie')
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheSections = []
        self.dateReObj = re.compile('''([A-Z][a-z]{2})\s*([0-9]+?)[^0-9]+?([0-9]{4})\s*([0-9][0-9]?:[0-9]{2})\s(AM|PM)''')
        self.ABBREVIATED_MONTH_NAME_TAB = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
    def getMainUrl(self):
        if self.cm.isValidUrl(config.plugins.iptvplayer.livesports_domain.value):
            return config.plugins.iptvplayer.livesports_domain.value
        return self.MAIN_URL
        
    def gmt2local(self, txt):
        try:
            obj = self.dateReObj.search(txt)
            utc_date = '%s-%s-%s %s' % (obj.group(3), self.ABBREVIATED_MONTH_NAME_TAB.index(obj.group(1))+1, obj.group(2), obj.group(4))
            print(utc_date)
            utc_date = datetime.strptime(utc_date, '%Y-%m-%d %H:%M')
            if obj.group(5) == 'PM' and utc_date.time().hour < 12: utc_date = utc_date + timedelta(hours=12)
            if obj.group(5) == 'AM' and utc_date.time().hour == 12: utc_date = utc_date - timedelta(hours=12)
            utc_date = utc_date + self.OFFSET
            if utc_date.time().second == 59:
                utc_date = utc_date + timedelta(seconds=1)
            ret = utc_date.strftime('%H:%M, %Y-%m-%d')
        except Exception:
            printExc()
            ret = ''
        return ret
    
    def getList(self, cItem):
        printDBG("ViorTvApi.getChannelsList")
        
        category = cItem.get('iptv_category', '')
        mainItemsTab = []
        
        if category == '':
            self.OFFSET = datetime.now() - datetime.utcnow()
            self.cacheSections = []
            
            sts, data = self.cm.getPage(self.getMainUrl())
            if not sts: return mainItemsTab
            
            data = re.compile('''(<h3[^>]*?>[^<]+?</h3>)''').split(data)
            for idx in range(2, len(data)+1, 2):
                sTitle = self.cleanHtmlStr(data[idx-1])
                sItemsTab = []
                section = self.cm.ph.getAllItemsBeetwenNodes(data[idx], ('<div', '>', 'bbevent'), ('</a', '>'))
                for item in section:
                    url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                    title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1])
                    date  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h5', '</h5>')[1])
                    date  = '%s[/br]%s' % (self.gmt2local(date), date) 
                    sItemsTab.append({'url':url, 'title':title, 'desc':date})
                if len(sItemsTab):
                    if sTitle in ['NFL', 'NHL']: icon = self.getFullUrl('%s.jpg' % sTitle.lower())
                    else: icon = cItem['icon']
                    params = dict(cItem)
                    params.update({'iptv_category':'list_section', 'title':sTitle, 'icon':icon, 's_idx':len(self.cacheSections)})
                    mainItemsTab.append(params)
                    self.cacheSections.append(sItemsTab)
        elif category == 'list_section':
            idx = cItem['s_idx']
            for item in self.cacheSections[idx]:
                params = dict(cItem)
                params.update({'iptv_category':'list_links'})
                params.update(item)
                mainItemsTab.append(params)
        elif category == 'list_links':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return mainItemsTab
            
            tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>', '/stream/'), ('</a', '>'))
            for item in tmp:
                url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                title = '%s - %s' % (cItem['title'], self.cleanHtmlStr(item))
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'get_iframe':True})
                mainItemsTab.append(params)
            
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            params = dict(cItem)
            params.update({'type':'video', 'url':url})
            mainItemsTab.insert(0, params)
        
        return mainItemsTab
        
    def getVideoLink(self, cItem):
        printDBG("ViorTvApi.getVideoLink")
        urlsTab = []
        
        sts, data = self.cm.getPage(cItem['url'], {'with_metadata':True})
        if not sts: return urlsTab
        
        if cItem.get('get_iframe', False):
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            if url != '':
                sts, data = self.cm.getPage(url, {'with_metadata':True})
                if not sts: return urlsTab
        
        cUrl = data.meta['url']
        data = self.cm.ph.getDataBeetwenMarkers(data, 'unescape(', ')', False)[1].strip()
        data = urllib.unquote(data[1:-1])
        
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(data)
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        source  = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?source['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        replace = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?replace['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        keyurl  = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?keyurl['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        rewrittenUrl = self.cm.ph.getSearchGroups(data, '''\=\s*?['"]([^'^"]+?)['"]\s*?\+\s*?btoa''', 1, True)[0]
        
        replaceTab = self.cm.ph.getDataBeetwenMarkers(data, 'prototype.open', '};', False)[1]
        printDBG(replaceTab)
        replaceTab = re.compile('''\.replace\(['"](\s*[^'^"]+?)['"]\s*\,\s*['"]([^'^"]+?)['"]''').findall(replaceTab)
        printDBG(replaceTab)
        scriptUrl = ''
        hlsTab = getDirectM3U8Playlist(source, checkContent=True, sortWithMaxBitrate=9000000)
        if replace != '' and keyurl != '':
            for idx in range(len(hlsTab)):
                hlsTab[idx]['url'] = strwithmeta(hlsTab[idx]['url'], {'iptv_m3u8_key_uri_replace_old':replace, 'iptv_m3u8_key_uri_replace_new':keyurl})
        elif len(replaceTab):
            scriptUrl = '|' + base64.b64encode(json.dumps(replaceTab).encode('utf-8'))
        elif rewrittenUrl != '':
            scriptUrl = '<proxy>' + rewrittenUrl
        elif '/js/nhl.js' in data:
            scriptUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^"^']*?js/nhl\.js)['"]''', 1, True)[0])
        
        if scriptUrl != '':
            for idx in range(len(hlsTab)):
                hlsTab[idx]['need_resolve'] = 1
                hlsTab[idx]['url'] = strwithmeta(hlsTab[idx]['url'], {'name':cItem['name'], 'Referer':cUrl, 'priv_script_url':scriptUrl})
        
        urlsTab = hlsTab
        
        return urlsTab

    def getResolvedVideoLink(self, videoUrl):
        printDBG("ViorTvApi.getResolvedVideoLink [%s]" % videoUrl)
        urlsTab = []
        
        
        baseUrl = self.cm.getBaseUrl(videoUrl.meta.get('Referer', ''))
        scriptUrl = videoUrl.meta.get('priv_script_url', '')
        
        sts, data = self.cm.getPage(videoUrl)
        if not sts or '#EXTM3U' not in data: return urlsTab
        
        meta = {}
        keyUrl = set(re.compile('''#EXT\-X\-KEY.*?URI=['"](https?://[^"]+?)['"]''').findall(data))
        if len(keyUrl):
            keyUrl = keyUrl.pop()
            proto = keyUrl.split('://', 1)[0]
            pyCmd = GetPyScriptCmd('livesports') + ' "%s" "%s" "%s" "%s" "%s" ' % (config.plugins.iptvplayer.livesports_port.value, videoUrl, baseUrl, scriptUrl, self.HTTP_HEADER['User-Agent'])
            meta = {'iptv_proto':'em3u8'}
            meta['iptv_m3u8_key_uri_replace_old'] = '%s://' % proto 
            meta['iptv_m3u8_key_uri_replace_new'] = 'http://127.0.0.1:{0}/{1}/'.format(config.plugins.iptvplayer.livesports_port.value, proto)
            meta['iptv_refresh_cmd'] = pyCmd
        
        videoUrl = urlparser.decorateUrl("ext://url/" + videoUrl, meta)
        
        return [{'name':'direct', 'url':videoUrl}]