# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.youtube import YoutubeIE
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, unescapeHTML
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, CSelOneLink, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import decorateUrl, getDirectM3U8Playlist, getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import base64
import copy
import urllib
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
try: import json
except Exception: import simplejson as json
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.moonwalk_format    = ConfigSelection(default = "m3u8", choices = [("hls/m3u8", "m3u8"),("f4m", "f4m/hds")]) 
config.plugins.iptvplayer.moonwalk_df_format = ConfigSelection(default = 9999, choices = [(0, _("the worst")), (360, "360p"), (480, "480p"), (720, "720"), (9999, _("the best"))])
config.plugins.iptvplayer.moonwalk_use_df    = ConfigYesNo(default = False)

class MoonwalkParser():
    USER_AGENT = 'Mozilla/5.0'
    def __init__(self):
        self.cm = common()
        self.HTTP_HEADER= {'User-Agent':self.USER_AGENT, 'Referer':''}
        self.COOKIEFILE = GetCookieDir("moonwalkcc.cookie")
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE}
        self.baseUrl = ''
        
    def _setBaseUrl(self, url):
        self.baseUrl = 'http://' + self.cm.ph.getDataBeetwenMarkers(url, '://', '/', False)[1]
        
    def _getSecurityData(self, data, params):
        printDBG('MoonwalkParser._getSecurityData')
        baseUrl = '/manifests/video/%s/all' % self.cm.ph.getSearchGroups(data, '''video_token['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
        sec_header = {}
        post_data = {}
        
        scriptUrl = self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^'^"]+?)['"]''')[0]
        if scriptUrl.startswith('/'):
            scriptUrl = self.baseUrl + scriptUrl
            
        sts, data2 = self.cm.getPage(scriptUrl, params)
        if not sts: data2 = ''
        
        tmp = self.cm.ph.getDataBeetwenReMarkers(data2, re.compile('getVideoManifests\s*:'), re.compile('onGetManifestSuccess'), False)[1]
        
        tmp2 = self.cm.ph.getAllItemsBeetwenMarkers(tmp, 'headers:', '}')
        for item in tmp2:
            printDBG("---------------------------------------------")
            printDBG(item)
            printDBG("---------------------------------------------")
            item = re.compile('''['"]([^'^"]+?)['"]\s*:([^\,^\}^\s}]+?)[\,\}\s]''').findall(item)
            for header in item:
                value = header[1].strip()
                if value[0] not in ['"', "'"]:
                    value = self.cm.ph.getSearchGroups(data, '''%s\s*:\s*['"]([^'^"]+?)['"]''' % value.split('.')[-1])[0]
                sec_header[header[0]] = value
        
        printDBG("---------------------------------------------------------")
        printDBG("SECURITY HEADER")
        printDBG("---------------------------------------------------------")
        printDBG(sec_header)
        printDBG("---------------------------------------------------------")
        
        tmp = self.cm.ph.getDataBeetwenReMarkers(tmp, re.compile('var\s[^\{]*?{'), re.compile('}'), False)[1]
        tmp2 = re.compile('''[\{\}\s\,]*?['"]?([^\:]+?)['"]?:([^\{^\}^\s^\,]+?)[\{\}\s\,]''').findall(tmp + ',')
        printDBG("---------------------------------------------------------")
        printDBG("PARAMS")
        printDBG("---------------------------------------------------------")
        printDBG(tmp)
        printDBG("---------------------------------------------------------")
        for item in tmp2:
            var = item[0].strip()
            val = item[1].strip()
            if val[0] in ['"', "'"]:
                val = val[1:-1]
            elif '.' in val:
                val = self.cm.ph.getSearchGroups(data, '''%s\s*:\s*['"]?([^'^"^\,]+?)['"\,]''' % val.split('.')[-1])[0].strip()
            if var[0] in ['"', "'"]:
                var = var[1:-1]
            post_data[var] = val
        
        return baseUrl, sec_header, post_data

    def getDirectLinks(self, url):
        printDBG('MoonwalkParser.getDirectLinks')
        linksTab = []
        try:
            self._setBaseUrl(url)
            params = copy.deepcopy(self.defaultParams)
            params['header']['Referer'] = url
            sts, data = self.cm.getPage( url, params)
            if not sts: return []
            
            url, sec_header, post_data = self._getSecurityData(data, params)
            params['header'].update(sec_header)
            params['header']['X-Requested-With'] = 'XMLHttpRequest'
            params['load_cookie'] = True
            sts, data = self.cm.getPage(self.baseUrl + url, params, post_data)
            printDBG("=======================================================")
            printDBG(data)
            printDBG("=======================================================")
            if not sts: return []
            
            try: 
                data = byteify( json.loads(data) )
                data = data['mans']
            except Exception: printExc()
            try:
                mp4Url = strwithmeta(data["manifest_mp4"], {'User-Agent':'Mozilla/5.0', 'Referer':url})
                sts, tmp = self.cm.getPage(mp4Url, {'User-Agent':'Mozilla/5.0', 'Referer':url})
                tmpTab = []
                tmp = byteify(json.loads(tmp))
                printDBG(tmp)
                for key in tmp:
                    mp4Url = tmp[key]
                    if mp4Url.split('?')[0].endswith('.mp4'):
                        tmpTab.append({'url':mp4Url, 'heigth':key})
                    
                def __getLinkQuality( itemLink ):
                    return int(itemLink['heigth'])
                    
                maxRes = config.plugins.iptvplayer.moonwalk_df_format.value
                tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
                if config.plugins.iptvplayer.moonwalk_use_df.value:
                    tmpTab = [tmpTab[0]]
                for item in tmpTab:
                    linksTab.append({'name':'[mp4] %sp' % __getLinkQuality(item), 'url':item['url']})
            except Exception:
                printExc()

            if 'm3u8' == config.plugins.iptvplayer.moonwalk_format.value:
                hlsUrl = strwithmeta(data["manifest_m3u8"], {'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Referer':url})
                tmpTab = getDirectM3U8Playlist(hlsUrl)
                def __getLinkQuality( itemLink ):
                    return int(itemLink['heigth'])
                maxRes = config.plugins.iptvplayer.moonwalk_df_format.value
                tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
                if config.plugins.iptvplayer.moonwalk_use_df.value:
                    tmpTab = [tmpTab[0]]
                for item in tmpTab:
                    linksTab.append({'name':'[hls/m3u8] %sp' % __getLinkQuality(item), 'url':item['url']})
            else:
                tmpTab = getF4MLinksWithMeta(data["manifest_f4m"])
                def __getLinkQuality( itemLink ):
                    printDBG(itemLink)
                    bitrate = int(self.cm.ph.getDataBeetwenMarkers(itemLink['name'], 'bitrate[', ']', False)[1])
                    if bitrate < 400:
                        return 360
                    elif bitrate < 700:
                        return 480
                    elif bitrate < 1200:
                        return 720
                    return 1080
                maxRes = config.plugins.iptvplayer.moonwalk_df_format.value
                tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
                if config.plugins.iptvplayer.moonwalk_use_df.value:
                    tmpTab = [tmpTab[0]]
                for item in tmpTab:
                    linksTab.append({'name':'[f4m/hds] %sp' % __getLinkQuality(item), 'url':item['url']})
        except Exception:
            printExc()
        return linksTab
        
    def getSeasonsList(self, url):
        printDBG('MoonwalkParser.getSeasonsList')
        seasonsTab = []
        try:
            self._setBaseUrl(url)
            params = copy.deepcopy(self.defaultParams)
            params['header']['Referer'] = url
            sts, data = self.cm.getPage( url, params)
            if not sts: return []
            
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            
            seasonData = self.cm.ph.getSearchGroups(data, '''seasons\s*:\s*\[([^\]]+?)\]''')[0]
            ref = self.cm.ph.getSearchGroups(data, '''ref\s*:[^'^"]*?['"]([^'^"]+?)['"]''')[0]
            printDBG(seasonData)
            
            seasonData = seasonData.split(',')
            for item in seasonData:
                item = item.strip()
                seasonsTab.append({'title':_('Season') + ' ' + item, 'id':int(item), 'url': '%s?season=%s&ref=%s' % (url, item, urllib.quote(ref))})
        except Exception:
            printExc()
        return seasonsTab
        
    def getEpiodesList(self, url, seasonIdx):
        printDBG('MoonwalkParser.getEpiodesList')
        episodesTab = []
        try:
            self._setBaseUrl(url)
            params = copy.deepcopy(self.defaultParams)
            params['header']['Referer'] = url
            sts, data = self.cm.getPage( url, params)
            if not sts: return []
            
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            
            episodeData = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''episodes\s*:'''), re.compile(']]'))[1]
            printDBG(episodeData)
            
            episodeData = re.compile('''\[\s*[0-9]+?\s*\,\s*([0-9]+?)[^0-9]''').findall(episodeData)
            for item in episodeData:
                item = item.strip()
                episodesTab.append({'title':_('Episode') + ' ' + item, 'id':int(item), 'url': '%s&episode=%s' % (url, item)})
        except Exception:
            printExc()
        return episodesTab
