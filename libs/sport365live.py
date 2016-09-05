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
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2, SAWLIVETV_decryptPlayerParams
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
###################################################

###################################################
# Config options for HOST
###################################################
def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class Sport365LiveApi:
    MAIN_URL   = 'http://sport365.live/'
    HTTP_HEADER  = { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36', 'Referer': MAIN_URL }
    
    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('sport365live.cookie')
        self.cm = common()
        self.up = urlparser()
        self.http_params = {'header': dict(self.HTTP_HEADER), 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
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
        
    def getMainCategries(self, cItem):
        printDBG("Sport365LiveApi.getMainCategries")
        channelsTab = []
        url = self.getFullUrl('en/events/-/1/-/-/120')
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        date = ''
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table', '</table>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>')
        for item in data:
            if '/types/' not in item:
                tmp = self.cm.ph.getSearchGroups(item, '''>([0-9]{2}\.[0-9]{2}\.[0-9]{4})<''')[0]
                if tmp != '': date = tmp
            else:
                if '/types/dot-green-big.png' in item:
                    title = '[live] '
                else:
                    title = ''
                title += self.cleanHtmlStr(item)
                desc  = self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0]
                desc  = date + ' ' + self.cleanHtmlStr(desc)
                linksData = []
                tmp = self.cm.ph.getDataBeetwenMarkers(item, '__showLinks(', ')', False)[1].split(',')
                for t in tmp:
                    linksData.append(t.replace('"', '').strip())
                printDBG(linksData)
                params = dict(cItem)
                params.update({'type':'category', 'priv_cat':'streams_links', 'links_data':linksData, 'title':title, 'desc':desc})
                channelsTab.append(params)
        return channelsTab
        
    def getStreamsLinks(self, cItem):
        printDBG("Sport365LiveApi.getStreamsLinks")
        channelsTab = []
        
        linksData = cItem.get('links_data', [])
        if len(linksData) < 4 or not linksData[0].startswith('event_'):
            return []
        
        url = self.getFullUrl('en/links/{0}/{1}'.format(linksData[0].replace('event_', ''), linksData[-1]))
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        marker = '__showWindow('
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<table', '</table>')[1] ) + '[/br]' + cItem.get('desc', '')
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>')
        for item in data:
            sourceTitle = self.cleanHtmlStr(item.split('<span')[0])
            links = self.cm.ph.getAllItemsBeetwenMarkers(item, '<span ', '</span>')
            for link in links:
                if marker not in link: continue
                linkTitle = self.cleanHtmlStr(link)
                linkData  = self.cm.ph.getDataBeetwenMarkers(link, marker, ')', False)[1].split(',')[0].replace('"', '').replace("'", '').strip()
                printDBG(linkData)
                params = dict(cItem)
                params.update({'type':'video', 'link_data':linkData, 'desc':desc, 'title':sourceTitle + ' ' + linkTitle})
                channelsTab.append(params)
        
        return channelsTab
        
    def getChannelsList(self, cItem):
        printDBG("Sport365LiveApi.getChannelsList")
        
        category = cItem.get('priv_cat', None)
        if None == category:
            return self.getMainCategries(cItem)
        elif 'streams_links' == category:
            return self.getStreamsLinks(cItem)
        
        return []
        
    def getVideoLink(self, cItem):
        printDBG("Sport365LiveApi.getVideoLink")
        sts, data = self.cm.getPage(self.getFullUrl('en/main'), self.http_params)
        if not sts: return []
        
        commonUrl = self.cm.ph.getSearchGroups(data, '''src=['"](http[^"^']*?/wrapper\.js[^"^']*?)["']''')[0]
        if commonUrl == '': return []
        sts, tmpData = self.cm.getPage(commonUrl, self.http_params)
        if not sts: return []
        aes = ''
        try:
            while 'eval' in tmpData:
                tmp = tmpData.split('eval(')
                if len(tmp): del tmp[0]
                tmpData = ''
                for item in tmp:
                    #printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    #printDBG(item)
                    #printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    for decFun in [VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2, SAWLIVETV_decryptPlayerParams]:
                        tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                        if '' != tmpData:   
                            break
                    #printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    #printDBG(tmpData)
                    #printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    aes = self.cm.ph.getSearchGroups(tmpData, 'aes_key="([^"]+?)"')[0]
                    if '' == aes: aes = self.cm.ph.getSearchGroups(tmpData, 'aes\(\)\{return "([^"]+?)"')[0]
                    if aes != '':
                        break
            aes = aes.encode('utf-8')
        except:
            printExc()
            aes = ''
        if aes == '': return []
        
        #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % aes)
        
        urlsTab = []
        try:
            linkData   = base64.b64decode(cItem['link_data'])
            linkData   = byteify(json.loads(linkData))
            
            ciphertext = base64.b64decode(linkData['ct'])
            iv         = a2b_hex(linkData['iv'])
            salt       = a2b_hex(linkData['s'])
            
            playerUrl = self.cryptoJS_AES_decrypt(ciphertext, aes, salt)
            printDBG(playerUrl)
            playerUrl = byteify(json.loads(playerUrl))
            
            if not playerUrl.startswith('http'): return []
            sts, data = self.cm.getPage(playerUrl, self.http_params)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'document.write(', '(')[1]
            playerUrl = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](http[^"^']+?)['"]''', 1, True)[0] )
            
            urlsTab = self.up.getVideoLinkExt(strwithmeta(playerUrl, {'aes_key':aes}))
            
        except:
            printExc()
        
        return urlsTab
