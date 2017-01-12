# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
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
config.plugins.iptvplayer.telwizjadanet_categorization  = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('Categorization') + ": ", config.plugins.iptvplayer.telwizjadanet_categorization))
    return optionList
    
###################################################

class TelewizjadaNetApi:
    MAIN_URL   = 'http://www.telewizjada.net/'

    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('telewizjadanet.cookie')
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        
    def getFullUrl(self, url):
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return self.MAIN_URL + url[1:]
        return url
        
    def cleanHtmlStr(self, str):
        return CBaseHostClass.cleanHtmlStr(str)
        
    def getChannelsList(self, cItem):
        printDBG("TelewizjadaNetApi.getChannelsList")
        channelsTab = []
        getList = cItem.get('get_list', True)
        if getList:
            self.cacheList = {}
            channelUrl = self.MAIN_URL + 'get_channels.php'
            http_params = dict(self.http_params)
            http_params['load_cookie'] = False
            
            sts, data = self.cm.getPage(channelUrl, http_params)
            if not sts: return []
            try:
                self.cacheList = byteify(json.loads(data))
            except Exception:
                printExc()
                
        def __addChannel(item):
            icon  = self.getFullUrl(item['thumb'])
            title = item['displayName']
            cid   = item['id']
            desc  = item.get('description', '')
            params = dict(cItem)
            params.update({'type':'video', 'title':title, 'desc':desc, 'cid':cid, 'type':'video', 'icon':icon})
            channelsTab.append(params)
        
        addAdultCat = False
        if False == config.plugins.iptvplayer.telwizjadanet_categorization.value:
            try:
                for item in self.cacheList['channels']:
                    if 0 == item['online']: continue
                    
                    if int(item['isAdult']) == 1 and not cItem.get('adult_cat', False):
                        addAdultCat = True
                        continue
                    elif int(item['isAdult']) != 1 and cItem.get('adult_cat', False):
                        continue
                    __addChannel(item)
            
                if addAdultCat:
                    params = dict(cItem)
                    params.update({'title':_('Dla dorosłych'), 'adult_cat':True, 'get_list':False, 'pin_locked':True})
                    channelsTab.append(params)
            except Exception:
                printExc()
        else:
            try:
                if getList:
                    for idx in range(len(self.cacheList['categories'])):
                        cat = self.cacheList['categories'][idx]
                        adult = False
                        for item in cat['Categorychannels']:
                            if int(item['isAdult']) == 1:
                                adult = True
                                break
                        params = dict(cItem)
                        params.update({'cat_id':idx, 'title':cat['Categoryname'], 'desc':cat['Categorydescription'], 'get_list':False, 'pin_locked':adult})
                        channelsTab.append(params)
                else:
                    idx = cItem.get('cat_id', -1)
                    for item in self.cacheList['categories'][idx]['Categorychannels']:
                        __addChannel(item)
            except Exception:
                printExc()
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("TelewizjadaNetApi.getVideoLink")
        
        url = self.MAIN_URL + 'live.php?cid=%s' % cItem['cid']
        sts, data = self.cm.getPage(url, self.http_params)
        if not sts: return []
        
        http_params = dict(self.http_params)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        http_params.update({'header':HTTP_HEADER})
        http_params['header']['Referer'] = url
        
        url = self.MAIN_URL + 'get_mainchannel.php'
        sts, data = self.cm.getPage(url, http_params, {'cid':cItem['cid']})
        if not sts: return []
        try:
            data = byteify(json.loads(data))
            vid_url = data['url']
        except Exception:
            printExc()
            return []
        
        url = self.MAIN_URL + 'set_cookie.php'
        sts, data = self.cm.getPage(url, http_params, {'url':vid_url})
        if not sts: return []
        
        url = self.MAIN_URL + 'get_channel_url.php'
        sts, data = self.cm.getPage(url, http_params, {'cid':cItem['cid']})
        if not sts: return []
        
        try:
            vid_url = byteify(json.loads(data))
            vid_url = vid_url['url']
        except Exception:
            vid_url = data
        
        urlsTab = []
        vid_url = vid_url.strip()
        if vid_url.startswith('http://') and 'm3u8' in vid_url:
            try:
                sessid = self.cm.getCookieItem(self.COOKIE_FILE, 'sessid')
                msec   = self.cm.getCookieItem(self.COOKIE_FILE, 'msec')
                statid = self.cm.getCookieItem(self.COOKIE_FILE, 'statid')
                url = strwithmeta(vid_url, {'Cookie':'sessid=%s; msec=%s; statid=%s;' % (sessid, msec, statid)})
                urlsTab = getDirectM3U8Playlist(url)
            except Exception:
                SetIPTVPlayerLastHostError("Problem z dostępem do pliku \"%\".\nSprawdź, czy masz wolne miejsce na pliki cookies." % self.COOKIE_FILE)
        return urlsTab