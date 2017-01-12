﻿# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, GetPyScriptCmd, GetPluginDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CBaseHostClass
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
except Exception: import simplejson as json
from time import time
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
from os import path as os_path
from datetime import datetime, timedelta
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
def GetConfigList():
    optionList = []
    return optionList
    
###################################################

class Sport365LiveApi:
    MAIN_URL   = 'http://www.sport365.live/'
    HTTP_HEADER  = { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36', 'Referer': MAIN_URL }
    CACHE_AES_PASSWORD = ''
    
    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('sport365live.cookie')
        self.sessionEx = MainSessionWrapper()
        self.cm = common()
        self.up = urlparser()
        self.http_params = {'header': dict(self.HTTP_HEADER), 'use_cookie':True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.needRefreshAdvert = True
        
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
    
    def getMarketCookie(self, url, referer, num=1):
        try:
            id = url.split('.')[-2]
        except Exception:
            printExc()
            id = '403'
        xz = str(int(time() * 1000)) + id + str(int(random.random()*1000)) + str(2 * int(random.random()*4)) + str(num)
        xz = base64.b64encode(xz)
        return 'MarketGidStorage=%s; ' % urllib.quote('{"0":{"svspr":"%s","svsds":%s,"TejndEEDj":"%s"},"C%s":{"page":1,"time":%s}}' % (referer, num, xz, id, int(time() * 100)))
        
    def refreshAdvert(self):
        if not self.needRefreshAdvert: return
        
        self.sessionEx.open(MessageBox, _('Please remember to visit http://www.sport365.live/ and watch a few advertisements.\nThis will fix problem, if your playback is constantly interrupted.'), type=MessageBox.TYPE_INFO, timeout=10)
        self.needRefreshAdvert = False
        
        COOKIE_FILE = GetCookieDir('sport365live2.cookie')
        params = dict(self.http_params)
        params['cookiefile'] = COOKIE_FILE
        params['header'] = dict(params['header'])
        params['return_data'] = False
        baseUrl = self.MAIN_URL
        try:
            sts, response = self.cm.getPage(baseUrl, params)
            baseUrl = response.geturl()
            data = response.read()
            response.close()
        except Exception:
            printExc()
            return
        
        sessionCookie = self.cm.getCookieHeader(COOKIE_FILE)
        params['return_data'] = True
        params['header']['Referer'] = baseUrl
        
        awrapperUrls = re.compile('''['"]([^"^']*?/awrapper/[^'^"]*?)["']''').findall(data)
        
        D = datetime.now()
        timeMarker = '{0}{1}{2}{3}'.format(D.year-1900, D.month-1, D.day, D.hour)
        jscUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?jsc\.mgid[^'^"]*?)['"]''')[0]
        if jscUrl.endswith('t='): jscUrl += timeMarker
        adUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?\.adshell\.[^'^"]*?)['"]''')[0] 
        
        sts, data = self.cm.getPage(self.getFullUrl(adUrl), params)
        if sts: adUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?\.adshell\.[^'^"]*?)['"]''')[0] 
        
        sts, data = self.cm.getPage(self.getFullUrl(jscUrl), params)
        marketCookie = self.getMarketCookie(jscUrl, baseUrl)
        params['use_cookie'] = False
        params['header']['Cookie'] = marketCookie
        sts, data = self.cm.getPage(self.getFullUrl(adUrl), params)

        
        for awrapperUrl in awrapperUrls:
            awrapperUrl = self.getFullUrl(awrapperUrl)
            params['header']['Referer'] = baseUrl
            params['header']['Cookie'] = sessionCookie + marketCookie
            sts, data = self.cm.getPage(awrapperUrl, params)
            if not sts: continue
            
            adUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?\.adshell\.[^'^"]*?)['"]''')[0] 
            params['header']['Referer'] = awrapperUrl
            params['header']['Cookie'] = marketCookie
            
            sts, data = self.cm.getPage(self.getFullUrl(adUrl), params)
            if not sts: continue
            
            jscUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?jsc\.mgid[^'^"]*?)['"]''')[0]
            if jscUrl.endswith('t='): jscUrl += timeMarker
            if jscUrl != '':
                sts, tmp = self.cm.getPage(self.getFullUrl(jscUrl), params)
                if sts: params['header']['Cookie'] = self.getMarketCookie(jscUrl, awrapperUrl)
            adUrls = re.compile('''['"]([^'^"]*?bannerid[^'^"]*?)['"]''').findall(data)
            for adUrl in adUrls:
                adUrl = adUrl.replace('&amp;', '&')
                sts, tmp = self.cm.getPage(self.getFullUrl(adUrl), params)
        
        return
        
    def getMainCategries(self, cItem):
        printDBG("Sport365LiveApi.getMainCategries")
        channelsTab = []
        dt = datetime.now() - datetime.utcnow()
        OFFSET = (dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**6
        OFFSET /= 60
        if OFFSET % 10 == 9:
            OFFSET += 1
        url = self.getFullUrl('en/events/-/1/-/-/%s' % (OFFSET))
        sts, data = self.cm.getPage(self.MAIN_URL, self.http_params)
        sts, data = self.cm.getPage(url, self.http_params)
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
                tmp = self.cm.ph.getSearchGroups(item, '''onClick=[^(]*?\(([^)]+?)\)''')[0].split(',')
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
        
        eventId = linksData[0].replace('event_', '')
        url = self.getFullUrl('en/links/{0}/{1}'.format(eventId, linksData[-1]))
        sts, data = self.cm.getPage(url, self.http_params)
        if not sts: return []
        
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<table', '</table>')[1] ) + '[/br]' + cItem.get('desc', '')
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>')
        for item in data:
            sourceTitle = self.cleanHtmlStr(item.split('<span')[0])
            links = self.cm.ph.getAllItemsBeetwenMarkers(item, '<span ', '</span>')
            for link in links:
                linkTitle = self.cleanHtmlStr(link)
                if '{' in linkTitle: continue
                linkData  = self.cm.ph.getSearchGroups(link, '''onClick=[^(]*?\(([^)]+?)\)''')[0].split(',')[0].replace('"', '').replace("'", '').strip()
                #printDBG("=========================================================")
                #printDBG(linkData)
                #printDBG("=========================================================")
                if linkData != '':
                    params = dict(cItem)
                    params.update({'type':'video', 'link_data':linkData, 'event_id':eventId, 'desc':desc, 'title':sourceTitle + ' ' + linkTitle})
                    channelsTab.append(params)
        
        return channelsTab
        
    def getChannelsList(self, cItem):
        printDBG("Sport365LiveApi.getChannelsList")
        self.refreshAdvert()
        
        category = cItem.get('priv_cat', None)
        if None == category:
            return self.getMainCategries(cItem)
        elif 'streams_links' == category:
            return self.getStreamsLinks(cItem)
        
        return []
        
    def getAesPassword(self, cItem, forceRefresh=False):
        if Sport365LiveApi.CACHE_AES_PASSWORD != '' and not forceRefresh:
            return Sport365LiveApi.CACHE_AES_PASSWORD
        
        sts, data = self.cm.getPage(self.getFullUrl('en/home/' + cItem['event_id']), self.http_params)
        if not sts: return []
        
        aes = ''
        data = re.compile('''src=['"](http[^"^']*?/js/[0-9a-fA-F]{32}\.js[^'^"]*?)["']''').findall(data)
        deObfuscatedData = ''
        for commonUrl in data:
            sts, tmpData = self.cm.getPage(commonUrl, self.http_params)
            if not sts: return []
            aes = ''
            try:
                while 'eval' in tmpData:
                    tmp = tmpData.split('eval(')
                    if len(tmp): del tmp[0]
                    tmpData = ''
                    for item in tmp:
                        for decFun in [VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2, SAWLIVETV_decryptPlayerParams]:
                            tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                            if '' != tmpData:   
                                break
                        deObfuscatedData += tmpData
                        aes = self.cm.ph.getSearchGroups(tmpData, 'aes_key="([^"]+?)"')[0]
                        if '' == aes: 
                            aes = self.cm.ph.getSearchGroups(tmpData, 'aes\(\)\{return "([^"]+?)"')[0]
                        if aes != '':
                            break
                aes = aes.encode('utf-8')
            except Exception:
                printExc()
                aes = ''
            if aes != '':
                break;
        
        if aes == '':
            funname = self.cm.ph.getSearchGroups(deObfuscatedData, 'CryptoJS\.AES\.decrypt\([^\,]+?\,([^\,]+?)\,')[0].strip()
            printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
            printDBG("FUN NAME: [%s]" % funname)
            printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
            tmp = self.cm.ph.getDataBeetwenMarkers(deObfuscatedData, 'function %s' % funname, '}')[1]
            try: aes = self.cm.ph.getSearchGroups(tmp, '"([^"]+?)"')[0].encode('utf-8')
            except Exception: printExc()
            #aes = self.cm.ph.getSearchGroups(deObfuscatedData, '%s\s*\{\s*return\s*"([^"]+?)"' % funname)[0]
        
        if aes != '':
            Sport365LiveApi.CACHE_AES_PASSWORD = aes
        return aes
        
    def getVideoLink(self, cItem):
        printDBG("Sport365LiveApi.getVideoLink")
        
        if Sport365LiveApi.CACHE_AES_PASSWORD != '':
            tries = 2
        else:
            tries = 1
        
        urlsTab = []
        for checkIdx in range(tries):
            if checkIdx > 0:
                aes = self.getAesPassword(cItem, True)
            else:
                aes = self.getAesPassword(cItem)
            
            
            if aes == '': 
                return []
            
            #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % aes)
            try:
                linkData   = base64.b64decode(cItem['link_data'])
                linkData   = byteify(json.loads(linkData))
                
                ciphertext = base64.b64decode(linkData['ct'])
                iv         = a2b_hex(linkData['iv'])
                salt       = a2b_hex(linkData['s'])
                
                playerUrl = self.cryptoJS_AES_decrypt(ciphertext, aes, salt)
                printDBG(playerUrl)
                playerUrl = byteify(json.loads(playerUrl))
                
                if not playerUrl.startswith('http'): 
                    continue
                sts, data = self.cm.getPage(playerUrl, self.http_params)
                if not sts: return []
                data = self.cm.ph.getDataBeetwenMarkers(data, 'document.write(', '(')[1]
                playerUrl = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](http[^"^']+?)['"]''', 1, True)[0] )
                
                urlsTab = self.up.getVideoLinkExt(strwithmeta(playerUrl, {'aes_key':aes}))
                if len(urlsTab):
                    break
                
            except Exception:
                printExc()
            
        return urlsTab
