# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.youtube import YoutubeIE
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, unescapeHTML
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, CSelOneLink, GetCookieDir, byteify
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
except: import simplejson as json
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.moonwalk_format    = ConfigSelection(default = "m3u8", choices = [("hls/m3u8", "m3u8"),("f4m", "f4m/hds")]) 
config.plugins.iptvplayer.moonwalk_df_format = ConfigSelection(default = 360, choices = [(0, _("the worst")), (360, "360p"), (480, "480p"), (720, "720"), (9999, _("the best"))])
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
        
    def _getSecurityData(self, data):
        printDBG('MoonwalkParser._getSecurityData')
        sec_header = {}
        post_data = {}

        contentData = self.cm.ph.getDataBeetwenMarkers(data, 'setRequestHeader|', '|beforeSend', False)[1]
        csrfToken = self.cm.ph.getSearchGroups(data, '<meta name="csrf-token" content="([^"]+?)"')[0] 
        xDataPool = self.cm.ph.getSearchGroups(data, '''['"]X-Data-Pool['"]\s*:\s*['"]([^'^"]+?)['"]''')[0] 
        
        cd = self.cm.ph.getSearchGroups(data, 'var condition_detected = ([^;]+?);')[0]
        if 'true' == cd: cd = 1
        else: cd = 0
        data = self.cm.ph.getDataBeetwenMarkers(data, '/sessions/new_session', '.success', False)[1]
        partner = self.cm.ph.getSearchGroups(data, 'partner: ([^,]+?),')[0]
        if 'null' in partner: partner = ''
        d_id = self.cm.ph.getSearchGroups(data, 'd_id: ([^,]+?),')[0]
        video_token = self.cm.ph.getSearchGroups(data, "video_token: '([^,]+?)'")[0]
        content_type = self.cm.ph.getSearchGroups(data, "content_type: '([^']+?)'")[0]
        access_key = self.cm.ph.getSearchGroups(data, "access_key: '([^']+?)'")[0]
        mw_pid = self.cm.ph.getSearchGroups(data, "mw_pid: ([0-9]+?)[^0-9]")[0]
        mw_did = self.cm.ph.getSearchGroups(data, "mw_did: ([0-9]+?)[^0-9]")[0]
        mw_domain_id = self.cm.ph.getSearchGroups(data, "mw_domain_id: ([0-9]+?)[^0-9]")[0]
        
        printDBG("=======================================================================")
        printDBG(data)
        printDBG("=======================================================================")
        sec_header['Encoding-Pool'] = base64.b64encode(contentData.replace('|', ''))
        sec_header['X-Data-Pool'] = xDataPool
        sec_header['X-CSRF-Token'] = csrfToken
        sec_header['X-Requested-With'] = 'XMLHttpRequest'
        post_data = {}
        if 'cd:' in data: post_data['cd'] = cd
        if 'partner:' in data: post_data['partner'] = partner
        if 'd_id:' in data: post_data['d_id'] = d_id
        if 'video_token:' in data: post_data['video_token'] = video_token
        if 'content_type:' in data: post_data['content_type'] = content_type
        if 'access_key:' in data: post_data['access_key'] = access_key
        if 'mw_pid:' in data: post_data['mw_pid'] = mw_pid
        if 'mw_did:' in data: post_data['mw_did'] = mw_did
        if 'mw_domain_id:' in data: post_data['mw_domain_id'] = mw_domain_id      
        #post_data['ad_attr'] =0
        
        return sec_header, post_data

    def getDirectLinks(self, url):
        printDBG('MoonwalkParser.getDirectLinks')
        linksTab = []
        try:
            self._setBaseUrl(url)
            params = copy.deepcopy(self.defaultParams)
            params['header']['Referer'] = url
            sts, data = self.cm.getPage( url, params)
            if not sts: return []
            
            sec_header, post_data = self._getSecurityData(data)
            params['header'].update(sec_header)
            
            sts, data = self.cm.getPage( '%s/sessions/new_session' % self.baseUrl, params, post_data)
            printDBG("=======================================================")
            printDBG(data)
            printDBG("=======================================================")
            if not sts: return []
            
            data = byteify( json.loads(data) )['mans']
            if 'm3u8' == config.plugins.iptvplayer.moonwalk_format.value:
                tmpTab = getDirectM3U8Playlist(data["manifest_m3u8"])
                def __getLinkQuality( itemLink ):
                    return itemLink['heigth']
                if config.plugins.iptvplayer.moonwalk_use_df.value:
                    maxRes = config.plugins.iptvplayer.moonwalk_df_format.value
                    tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
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
                if config.plugins.iptvplayer.moonwalk_use_df.value:
                    maxRes = config.plugins.iptvplayer.moonwalk_df_format.value
                    tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
                    tmpTab = [tmpTab[0]]
                for item in tmpTab:
                    linksTab.append({'name':'[f4m/hds] %sp' % __getLinkQuality(item), 'url':item['url']})
        except:
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
            
            seasonData = self.cm.ph.getDataBeetwenMarkers(data, 'id="season"', '</select>', False)[1]
            printDBG(seasonData)
            seasonData = re.compile('<option[^>]+?value="([0-9]+?)">([^<]+?)</option>').findall(seasonData)
            seasonMainUrl = self.cm.ph.getDataBeetwenMarkers(data, "$('#season').val();", '});', False)[1]
            seasonMainUrl = self.cm.ph.getSearchGroups(seasonMainUrl, "var url = '(http[^']+?)'")[0] + '?season='
            if not seasonMainUrl.startswith('http'): 
                return []
            
            for item in seasonData:
                seasonsTab.append({'title':item[1], 'id':int(item[0]), 'url': seasonMainUrl + item[0]})
        except:
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
            
            episodeData = self.cm.ph.getDataBeetwenMarkers(data, 'id="episode"', '</select>', False)[1]
            episodeData = re.compile('<option[^>]+?value="([0-9]+?)">([^<]+?)</option>').findall(episodeData)
            ref = urllib.quote(self.cm.ph.getSearchGroups(data, '''var\s*referer\s*=[^"^']*['"]([^"^']+?)["']''')[0])
            episodeMainUrl = self.cm.ph.getDataBeetwenMarkers(data, "$('#episode').val();", '});', False)[1]
            episodeMainUrl = self.cm.ph.getSearchGroups(episodeMainUrl, "var url = '(http[^']+?)'")[0] + '?season=' + str(seasonIdx) + '&ref=' + ref + '&episode='
            if not episodeMainUrl.startswith('http'): 
                return []
            
            for item in episodeData:
                episodesTab.append({'title':item[1], 'id':int(item[0]), 'url': episodeMainUrl + item[0]})
        except:
            printExc()
        return episodesTab
