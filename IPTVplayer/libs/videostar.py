# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
try:    import simplejson as json
except Exception: import json
import urllib
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

config.plugins.iptvplayer.videostar_streamprotocol = ConfigSelection(default = "2", choices = [("1", "rtmp"),("2", "HLS - m3u8")]) 
config.plugins.iptvplayer.videostar_defquality     = ConfigSelection(default = "950000", choices = [("400000", _("low")),("950000", _("average")),("1600000", _("high"))])
config.plugins.iptvplayer.videostar_premium        = ConfigYesNo(default = False)
config.plugins.iptvplayer.videostar_login          = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.videostar_password       = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.videostar_use_proxy_gateway  = ConfigYesNo(default = False)
config.plugins.iptvplayer.videostar_proxy_gateway_url  = ConfigText(default = "http://darmowe-proxy.pl/browse.php?u={0}&b=192&f=norefer", fixed_size = False)

#http://www.bramka-proxy.pl/browse.php?u={0}&b=192&f=norefer
#185.5.99.77

#http://darmowe-proxy.pl/browse.php?u={0}&b=192&f=norefer
#85.128.142.29
#http://proksiak.pl/show.php?u={0}&b=32


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('Preferred streaming protocol') + ": ", config.plugins.iptvplayer.videostar_streamprotocol))
    optionList.append(getConfigListEntry(_('Preferred quality') + ": ", config.plugins.iptvplayer.videostar_defquality))
    optionList.append(getConfigListEntry( _("Login") + ": ", config.plugins.iptvplayer.videostar_login))
    optionList.append(getConfigListEntry( _("Password") + ": ", config.plugins.iptvplayer.videostar_password))
    if '2' == config.plugins.iptvplayer.videostar_streamprotocol.value:
        optionList.append(getConfigListEntry(_("Use a proxy gateway") + ' ' + _('(unsafe)'), config.plugins.iptvplayer.videostar_use_proxy_gateway))
        #if config.plugins.iptvplayer.videostar_use_proxy_gateway.value:
        #    optionList.append(getConfigListEntry("    " + _("Url:"), config.plugins.iptvplayer.videostar_proxy_gateway_url))
    return optionList
###################################################

class VideoStarApi:
    MAINURL_PC      = 'https://videostar.pl/'
    MAINURL_IOS     = 'https://videostar.pl/'
    HTTP_HEADER_PC   = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL_PC }
    HTTP_HEADER_IOS  = { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3', 'Referer': MAINURL_IOS }
    HTTP_HEADER2     = { 'User-Agent':'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16', 'Referer': MAINURL_IOS}

    API_URLS = { 'subscriptions_url'  : 'subscriptions',
                 'login_url'          : 'login',
                 'get_ad_show'        : 'api/ad/show',
                 'get_ad_urls'        : 'api/ad/urls',
                 'get_channels_list'  : 'api/channels/list/web',
                 'get_channel_url'    : 'api/channels/get/%s?format_id=%s',
                 'close_channel'      : 'api/channels/close',
               }
    VIDEO_STAR_T   = ''
    VIDEO_GUEST_M  = False

    def __init__(self):
        self.cm = common()#proxyURL= '', useProxy = True)
        self.up = urlparser()
        self.sessionEx = MainSessionWrapper()
        
    def printPageData(self, url, data):
        printDBG("printPageData")
        printDBG(": [%s]" % url)
        printDBG(data)
        printDBG("--------------------------------------------------")

    def doInit(self):
        if config.plugins.iptvplayer.videostar_use_proxy_gateway.value and '2' == config.plugins.iptvplayer.videostar_streamprotocol.value:
            self.proxy_gateway_url      = "http://www.bramka-proxy.pl/browse.php?u={0}&b=60" #192&f=norefer" #config.plugins.iptvplayer.videostar_proxy_gateway_url.value
            self.proxy_gateway_url_ssl  = "http://www.bramka-proxy.pl/includes/process.php?action=sslagree"
            self.my_ip = ''
            #self.my_ip                   = self.getProxyGatewayIP()
        else:
            self.my_ip = ''
            self.proxy_gateway_url = ''
            self.proxy_gateway_url_ssl = ''
        self._reInit()
        self.channelsList = []
        
    def getProxyGatewayIP(self):
        url = 'http://showip.net/'
        sts, data = self.cm.getPage(url, {'header':{'User-Agent':'Mozilla/5.0', 'Referer':self.proxy_gateway_url}, 'proxy_gateway':self.proxy_gateway_url})
        my_ip = ''
        if sts:
            try:
                my_ip = self.cm.ph.getSearchGroups(data, 'name="checkip"[^>]+?value="([^"]+?)"')[0]
                printDBG('getProxyGatewayIP my_ip[%s]' % my_ip)
            except Exception:
                printExc()
        if '' == my_ip:
            self.sessionEx.open(MessageBox, _('Problem z uzyskaniem IP bramki proxy!'), type = MessageBox.TYPE_INFO, timeout = 10 )
        return my_ip
        

    def _getUrl(self, key):
        if '2' == self.streamprotocol:
            MAINURL = VideoStarApi.MAINURL_IOS
        else:
            MAINURL = VideoStarApi.MAINURL_PC
        if key in VideoStarApi.API_URLS:
            return MAINURL + VideoStarApi.API_URLS[key]
        if not key.startswith('http'):
            return MAINURL + key
        return key
        
    def _reInit(self): 
        self.streamprotocol  = config.plugins.iptvplayer.videostar_streamprotocol.value
        if '2' == self.streamprotocol:
            self.MAINURL = VideoStarApi.MAINURL_IOS
            self.cm.HEADER = dict(VideoStarApi.HTTP_HEADER_IOS)
        else:
            self.MAINURL = VideoStarApi.MAINURL_PC
            self.cm.HEADER = dict(VideoStarApi.HTTP_HEADER_PC)
        if '' != self.my_ip:
            self.cm.HEADER['X-Forwarded-For'] = self.my_ip
        self.LOGIN           = config.plugins.iptvplayer.videostar_login.value
        self.PASSWORD        = config.plugins.iptvplayer.videostar_password.value
        
    def getDefaultQuality(self):
        return config.plugins.iptvplayer.videostar_defquality.value

    def getChannelsList(self, refresh=False):
        printDBG("VideoStarApi.getChannelsList")
        self.doInit()
        if not refresh and 0 < len(self.channelsList):
            return self.channelsList

        self.channelsList = []
        if '' != self.LOGIN.strip() and '' != self.PASSWORD.strip():
            if not self.doLogin(self.LOGIN, self.PASSWORD):
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
                return self.channelsList
        else:
            self.sessionEx.open(MessageBox, _('Strona wymaga darmowego konta na http://videostar.pl/.\nProszę uzupełnić dane w konfiguracji hosta.'), type = MessageBox.TYPE_INFO, timeout = 10 )
            return self.channelsList
         
        self._fillChannelsList()
        return self.channelsList 
        
    def _fillChannelsList(self):
        printDBG("VideoStarApi._fillChannelsList")
        
        HTTP_HEADER = dict(self.cm.HEADER)
        HTTP_HEADER.update( {'X-Reguested-With':'XMLHttpReguest'} )
        
        if self.proxy_gateway_url != '':
            HTTP_HEADER['Referer'] = self.proxy_gateway_url.format( urllib.quote(HTTP_HEADER['Referer']) )
            params = {'header': HTTP_HEADER, 'proxy_gateway':self.proxy_gateway_url}
        else:
            params = {'header': HTTP_HEADER}
        # get channels list
        url = self._getUrl('get_channels_list')
        sts, data = self.cm.getPage(url, params )
        if sts:
            self.printPageData(url, data)
            try:
                data = byteify(json.loads(data))
                if "ok" == data['status']:
                    self.channelsList = data['channels']
            except Exception:
                printExc()

    def getVideoLink(self, channelID):
        printDBG("VideoStarApi.getVideoLink")
        urlsTab = []
        
        #get referer page
        referer = ''
        guestMode   = False 
        for item in self.channelsList:
            if channelID == item['id']:
                referer = self.MAINURL  + '#' + item['slug'] # "slug" attrib can be also taken from stream_channel data
                linkType = 'basic'
                if "unsubscribed" == item['access_status']:
                    guestMode = True
                elif 'subscribed' == item['access_status']:
                    linkType = 'premium'
                break
        
        for tryNum in range(2):
        
            # there is need to close previuse played channel 
            #self._closePrevChannel()
            
            if tryNum > 0:
                # retrie if there was unknown problem with getting link
                self._reInit()
                if not guestMode:
                    self.doLogin(self.LOGIN, self.PASSWORD)
                else:
                    self.cm.HEADER = dict(VideoStarApi.HTTP_HEADER2)
            
            if '' != self.my_ip:
                self.cm.HEADER['X-Forwarded-For'] = self.my_ip
            
            url     = self._getUrl('get_channel_url') % (channelID, self.streamprotocol)
            
            HTTP_HEADER = dict(self.cm.HEADER)
            HTTP_HEADER.update( {'X-Reguested-With':'XMLHttpReguest'} )
            
            if self.proxy_gateway_url != '':
                HTTP_HEADER['Referer'] = self.proxy_gateway_url.format( urllib.quote(HTTP_HEADER['Referer']) )
                params = {'header': HTTP_HEADER, 'proxy_gateway':self.proxy_gateway_url}
            else:
                params = {'header': HTTP_HEADER}
            
            if guestMode: 
                url = url.replace('https://videostar.pl/api', 'https://api.videostar.pl/guest')
            sts, data = self.cm.getPage( url, params )
            try:
                self.printPageData(url, data)
                data = byteify(json.loads(data))
                if "ok" == data['status']:
                    VideoStarApi.VIDEO_STAR_T = data['stream_channel']['url_params'][-1].decode('utf-8')
                    url_param1 = data['stream_channel']['url_params'][1].decode('utf-8')
                    VideoStarApi.VIDEO_GUEST_M  = guestMode
                    if '1' == self.streamprotocol:
                        url = data['stream_channel']['url_base'].decode('utf-8')
                        sts, data = self.cm.getPage( url, params)
                        self.printPageData(url, data)
                        r = re.search('<baseURL>([^<]+?)</baseURL>', data).group(1)
                        
                        streams = re.findall('url="([^"]+?)" bitrate="([0-9]+?)"', data)
                        for item in streams:
                            # swfVfy=https://videostar.pl/javascripts/libs/flowplayer/flowplayer.netvi-x.swf protocol=1 
                            url = r + '/' + item[0] + ' live=1 swfUrl=https://videostar.pl/javascripts/libs/flowplayer/flowplayer.commercial-3.2.11.swf' + ' pageUrl=' + referer + (' conn=S:%s conn=S:%s token=%s' % (url_param1, VideoStarApi.VIDEO_STAR_T, VideoStarApi.VIDEO_STAR_T)) + ' flashVer=WIN 12,0,0,44 '
                            urlsTab.append({'url': strwithmeta(url, {'iptv_proto':'rtmp'}), 'name': item[1], 'bitrate':item[1]+'000', 'type':'rtmpt'})
                    else:
                        # hls
                        url = data['stream_channel']['url_base'].decode('utf-8')
                        meta = {'iptv_proto':'m3u8'}
                        if '' != self.proxy_gateway_url:
                            channelID = data['stream_channel']['channel_id']
                            #if url.startswith('https://'): url = 'http://' + url[8:]
                            server = self.cm.ph.getSearchGroups(url, r'://([^/]+?)/')[0]
                            #if linkType == 'basic':
                            #    meta['iptv_m3u8_custom_base_link'] = 'https://%s:443/%s/%s%s.stream/list.m3u8' % (server, channelID, channelID, 2)
                            #else:
                            meta['iptv_m3u8_custom_base_link'] = 'https://%s:443/%s/smil:%s.ism/list.m3u8' % (server, channelID, linkType) #'http://%s:1935/%s/smil:%s.ism/list.m3u8' % (server, channelID, linkType)
                            meta['iptv_proxy_gateway'] = self.proxy_gateway_url
                            meta['Referer'] =  self.proxy_gateway_url
                            meta['User-Agent'] = 'Mozilla/5.0'
                            if '' != self.my_ip:
                                meta['X-Forwarded-For'] = self.my_ip
                            meta['Cookie'] = self.cm.HEADER.get('Cookie', '')
                        urlsTab.append({'url': self.up.decorateUrl(url, meta), 'name': 'videostar hls', 'type':'hls'})
            except Exception:
                printExc()
                
            if 0 < len(urlsTab):
                break
        
        printDBG(urlsTab)
        return urlsTab
    
    def doLogin(self, login, password):
        HTTP_HEADER= dict(self.cm.HEADER)
        HTTP_HEADER.update( {'Content-Type':'application/x-www-form-urlencoded'} )
        
        cookiePath = GetCookieDir('videostar.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile': cookiePath, 'use_cookie': True, 'save_cookie':True}
        
        rm(cookiePath)
        
        if self.proxy_gateway_url_ssl != '':
            HTTP_HEADER['Referer'] = self.proxy_gateway_url
            sts, data = self.cm.getPage(self.proxy_gateway_url_ssl, params)
            self.printPageData(self.proxy_gateway_url_ssl, data)
            if not sts: return False
            params['load_cookie'] = True
            params['proxy_gateway'] = self.proxy_gateway_url

        post_data = {'login': login, 'password': password, 'permanent': '1'}
        url = self._getUrl('login')
        
        sts, data = self.cm.getPage(url, params, post_data)
        if not sts: return False
        
        self.printPageData(url, data)
        self.cm.HEADER['Cookie'] = self.cm.getCookieHeader(cookiePath)
        if self.proxy_gateway_url != '':
            HTTP_HEADER = dict(self.cm.HEADER)
            HTTP_HEADER['Referer'] = self.proxy_gateway_url.format(urllib.quote(HTTP_HEADER['Referer']))
            params = {'proxy_gateway':self.proxy_gateway_url, 'header':HTTP_HEADER}
        else:
            params = {}
        
        url = self._getUrl('subscriptions_url')
        sts, data = self.cm.getPage(url, params)
        if sts:
            self.printPageData(url, data)
            if 'Wyloguj' in data:
                return True

        return False