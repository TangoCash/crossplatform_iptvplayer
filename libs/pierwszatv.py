# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, GetPyScriptCmd, GetPluginDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
import base64
try:    import json
except: import simplejson as json
from time import time
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
from os import path as os_path
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.pierwszatv_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.pierwszatv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry('pierwsza.tv ' + _("email") + ':', config.plugins.iptvplayer.pierwszatv_login))
    optionList.append(getConfigListEntry('pierwsza.tv ' + _("password") + ':', config.plugins.iptvplayer.pierwszatv_password))
    return optionList
    
###################################################

class PierwszaTVApi:
    MAIN_URL   = 'http://pierwsza.tv/'
    HTTP_HEADER  = { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36', 'Referer': MAIN_URL }
    
    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('pierwszatv.cookie')
        self.COOKIE_FILE2 = GetCookieDir('pierwszatv2.cookie')
        self.COOKIE_FILE3 = GetCookieDir('pierwszatv3.cookie')
        self.sessionEx = MainSessionWrapper()
        self.cm = common()
        self.up = urlparser()
        self.http_params = {'header': dict(self.HTTP_HEADER), 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.http_params2 = {'header': dict(self.HTTP_HEADER), 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE2}
        self.http_params3 = {'header': dict(self.HTTP_HEADER), 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE3}
        self.cacheList = {}
        
    def cryptoJS_AES_decrypt(self, encrypted, password, salt):
        def derive_key_and_iv(password, salt, key_length, iv_length):
            d = d_i = ''
            while len(d) < key_length + iv_length:
                d_i = md5(d_i + password + salt).digest()
                d += d_i
            return d[:key_length], d[key_length:key_length+iv_length]
        bs = 16
        key, iv = derive_key_and_iv(password, salt, 32, 16)
        cipher = AES_CBC(key=key, keySize=32)
        return cipher.decrypt(encrypted, iv)
        
    def getTimestamp(self, t, s=64):
        a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        e = ""
        t = int(t)
        while t > 0:
            e = a[t % s] + e
            t = int(t / s)
        return e
        
    def getFullUrl(self, url):
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return 'http:' + url
        elif url.startswith('/'):
            return self.MAIN_URL + url[1:]
        return self.MAIN_URL + url
        
    def cleanHtmlStr(self, str):
        return CBaseHostClass.cleanHtmlStr(str)
        
    def getChannelsList(self, cItem):
        printDBG("TelewizjadaNetApi.getChannelsList")
        
        login    = config.plugins.iptvplayer.pierwszatv_login.value
        password = config.plugins.iptvplayer.pierwszatv_password.value
        if login != '' and password != '':        
            if self.doLogin(login, password):
                self.loggedIn = True
                self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
            else:
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
        
        channelsTab = []
        sts, data = self.cm.getPage(self.MAIN_URL + 'player/watch?show=active')
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'window.sources =', ';', False)[1].strip()
        #data = self.cm.ph.getAllItemsBeetwenMarkers(data, '{', '}')
        try:
            data = byteify(json.loads(data))
            for idx in range(200):
                try:
                    if isinstance(data, list):
                        item = data[idx]
                    else: item = data[str(idx)] 
                except Exception: continue
                printDBG(item)
                printDBG("===============================================")
                url   = self.getFullUrl( 'player/watch/{0}'.format(item['id']) )
                if None != item.get('thumb_url', ''):
                    icon  = self.getFullUrl( item.get('thumb_url', '') )
                else:
                    icon = ''
                title = self.cleanHtmlStr( item['name'] )
                desc  = self.cleanHtmlStr( item.get('author', '') + ' ' + item.get('updated_at', '') )
                if not url.startswith('http'): continue
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
                channelsTab.append(params)
        except Exception:
            printExc()
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("TelewizjadaNetApi.getVideoLink")
        params    = {'header' : self.HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        sts, data = self.cm.getPage(cItem['url'], params)
        if not sts: return []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'connectToLive(', ')', False)[1]
        tmp = self.cm.ph.getSearchGroups(tmp, '''['"]([^'^"]+?)['"][^'^"]+?['"]([^'^"]+?)['"]''', 2, True)
        mainCon = {'url':tmp[0], 'token':tmp[1]}
        
        varData = data #self.cm.ph.getDataBeetwenMarkers(data, 'window.', 'var items')[1]
        window = {'streamUrl':'', 'endpoints':'', 'sourceId':'', 'sourceType':'', 'sourcePlayer':'', 'streamId':'', 'streamToken':'', 'serverId':''} 
        for key in window:
            val = self.cm.ph.getSearchGroups(varData, '''window\.%s[^'^"]*?=([^;]+?);''' % key, 1, True)[0].strip()
            if val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            window[key] = val
        
        window['urls'] = {}
        for keyUrl in ['playRecord', 'player', 'sync', 'multiLogin', 'reportError', 'reportOk', 'bumpToken']:
            window['urls'][keyUrl] = self.cm.ph.getSearchGroups(varData, '''window\.urls\['[^']+?\@%s'\][\s]*?=[\s]*?['"]([^'^"]+?)['"]''' % keyUrl, 1, True)[0].strip()
        
        for keyUrl in ['requestStream']:
            window['urls'][keyUrl] = self.cm.ph.getSearchGroups(varData, '''window\.routes\['[^']+?\@%s'\][\s]*?=[\s]*?['"]([^'^"]+?)['"]''' % keyUrl, 1, True)[0].strip()
        
        urlsTab = []
        try:
            printDBG(window)
            if '' != window['streamUrl']:
                tmp = window['streamUrl'].replace('\\"', '"')
            else:
                tmp = window['endpoints'].replace('\\"', '"')
            streamUrl = byteify(json.loads(tmp))
            ciphertext = base64.b64decode(streamUrl['ct'])
            iv         = a2b_hex(streamUrl['iv'])
            salt       = a2b_hex(streamUrl['s'])
            
            tmp = self.cryptoJS_AES_decrypt(ciphertext, 'number-one', salt)
            tmp = byteify(json.loads(tmp))
            tmp = byteify(json.loads(tmp))
            
            if isinstance(tmp, list):
                tmp = tmp[0]
            
            if isinstance(tmp, dict):
                baseUrl1     = mainCon['url']
                streamToken1 = mainCon['token']
                baseUrl2     = tmp['server']
                streamToken2 = tmp['token']
                
                serverId = str(tmp['id'])
                
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                printDBG(tmp)
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                
                #def _getSocketIoUrl1(baseUrl, params):
                #    t1 = self.getTimestamp(time()*1000)
                
                t1 = self.getTimestamp(time()*1000)
                url = baseUrl1 + '/socket.io/?EIO=3&transport=polling&t=' + t1
                sts, data = self.cm.getPage(url, self.http_params2)
                if sts:
                    baseParams1 = data[data.find('{'):]
                    baseParams1 = byteify(json.loads(baseParams1))
                    printDBG("=========================================================")
                    printDBG([data])
                else:
                    baseParams1 = {'sid':''}
                printDBG(baseParams1)
                printDBG("=========================================================")
                
                t2 = self.getTimestamp(time()*1000)
                url = baseUrl2.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t=' + t2
                sts, data = self.cm.getPage(url, self.http_params3)
                baseParams2 = data[data.find('{'):]
                baseParams2 = byteify(json.loads(baseParams2))
                printDBG("=========================================================")
                printDBG([data])
                printDBG(baseParams2)
                printDBG("=========================================================")
                
                #=====================
                t1 = self.getTimestamp(time()*1000)
                url = baseUrl1 + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t1, baseParams1['sid'])
                sts, data = self.cm.getPage(url, self.http_params2)
                if sts:
                    printDBG("=========================================================")
                    printDBG(data.split('\x00\x02\xff'))
                    printDBG("=========================================================")
                
                t2 = self.getTimestamp(time()*1000)
                url = baseUrl2.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, baseParams2['sid'])
                sts, data = self.cm.getPage(url, self.http_params3)
                printDBG("=========================================================")
                printDBG(data.split('\x00\x02\xff'))
                printDBG("=========================================================")
                
                #=====================
                #raw_post_data
                t1 = self.getTimestamp(time()*1000)
                url = baseUrl1 + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t1, baseParams1['sid'])
                self.http_params2['raw_post_data'] = True
                sts, data = self.cm.getPage(url, self.http_params2, '92:42["authorize",{"token":"%s"}]' % streamToken1)
                printDBG("=========================================================")
                printDBG([data])
                printDBG("=========================================================")
                    
                if 0:
                    t1 = self.getTimestamp(time()*1000)
                    url = baseUrl1 + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t1, baseParams1['sid'])
                    sts, data = self.cm.getPage(url, self.http_params2)
                    printDBG("=========================================================")
                    printDBG([data])
                    printDBG("=========================================================")
                
                #+++++
                t2 = self.getTimestamp(time()*1000)
                url = baseUrl2.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, baseParams2['sid'])
                self.http_params3['raw_post_data'] = True
                sts, data = self.cm.getPage(url, self.http_params3, '102:42["authorize","%s"]' % streamToken2)
                printDBG("=========================================================")
                printDBG([data])
                printDBG("=========================================================")
                
                t2 = self.getTimestamp(time()*1000)
                url = baseUrl2.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, baseParams2['sid'])
                sts, data = self.cm.getPage(url, self.http_params3)
                data = byteify( json.loads(data[data.find('42')+2:]) ) 
                stoken = data[1]['stoken']
                printDBG("=========================================================")
                printDBG([data])
                printDBG("=========================================================")
                
                n = sha256(serverId + '_' + window['sourceId'] + '_' + stoken + '_rabbit_foot').hexdigest()
                url = window['urls']["requestStream"] + "?token=" + streamToken2 + "&server=" + serverId + "&source=" + window['sourceId'] + "&cs=" + n
                sts, data = self.cm.getPage(url, self.http_params)
                data = byteify( json.loads(data) ) 
                streamId = str(data['id'])
                
                if 0:
                    t2 = self.getTimestamp(time()*1000)
                    url = baseUrl2.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, baseParams2['sid'])
                    self.http_params3['raw_post_data'] = True
                    sts, data = self.cm.getPage(url, self.http_params3, '84:42["subscribe","%s"]' % streamId)
                
                wsUrl2 = baseUrl2.replace(":8000",":8004").replace('http://', 'ws://') + '/socket.io/?EIO=3&transport=websocket&sid={0}'.format(baseParams2['sid'])
                wsUrl1 = baseUrl1.replace('http://', 'ws://') + '/socket.io/?EIO=3&transport=websocket&sid={0}'.format(baseParams1['sid'])
                
                libsPath = GetPluginDir('libs/')
                
                pyCmd = GetPyScriptCmd('pierwszatv') + ' "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" ' % (self.http_params['header']['User-Agent'], baseUrl2, wsUrl2, wsUrl1, stoken, streamId, libsPath, baseParams2['sid'])
                vidUrl = strwithmeta("ext://url/" + cItem['url'], {'iptv_proto':'em3u8', 'iptv_refresh_cmd':pyCmd, 'Referer':cItem['url'], 'User-Agent':self.http_params['header']['User-Agent']})
                
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                printDBG(pyCmd)
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                #return []
                return [{'name':'pierwsza_hls', 'url':vidUrl}]
            
        except:
            printExc()
            return []
        
        return urlsTab
        
    def doLogin(self, login, password):
        logged = False
        loginUrl = self.MAIN_URL + 'account/login'
        
        params = dict(self.http_params)
        params['load_cookie'] = False
        sts, data = self.cm.getPage(loginUrl, params)
        if not sts: return False
        
        _token = self.cm.ph.getSearchGroups(data, '''_token"[\s]*?value="([^"]+?)"''', 1, True)[0]
        
        HTTP_HEADER= dict(PierwszaTVApi.HTTP_HEADER)
        HTTP_HEADER.update( {'Referer':loginUrl} )
        
        post_data = {'email' : login, 'password' : password, '_token' : _token, 'remember_me' : 'on' }
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True, 'load_cookie' : True}
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                if 'dashboard/logout' in data:
                    printDBG('PierwszaTVApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('PierwszaTVApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('PierwszaTVApi.doLogin there is no cookie file after login')
        return logged
