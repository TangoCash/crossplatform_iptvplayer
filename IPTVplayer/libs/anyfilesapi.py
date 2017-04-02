# -*- coding: utf-8 -*-

###################################################
# LOCAL import
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, rm
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
import Plugins.Extensions.IPTVPlayer.libs.xppod as xppod

###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config
import re
import urllib2
###################################################

class AnyFilesVideoUrlExtractor:
    COOKIEFILE  = GetCookieDir('anyfiles.cookie')
    MAINURL     = 'https://anyfiles.pl'
    LOGIN_URL_2 = MAINURL + '/j_security_check'
    LOGIN_URL   = MAINURL + '/Logo?op=l'
    
    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        self.defaultParams = {'header':{'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0'}, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': AnyFilesVideoUrlExtractor.COOKIEFILE}
        self.logged = False
    
    def isLogged(self):
        return self.logged
        
    def tryTologin(self):
        rm(AnyFilesVideoUrlExtractor.COOKIEFILE)
        login    = config.plugins.iptvplayer.anyfilespl_login.value
        password = config.plugins.iptvplayer.anyfilespl_password.value
        printDBG("AnyFilesVideoUrlExtractor.tryTologin login[%s]" % login)
        if 0 < len(login) and 0 < len(password):
            #First we need get JSESSIONID
            params = dict(self.defaultParams)
            params['load_cookie'] = False
            sts, data = self.cm.getPage(self.LOGIN_URL, params)
            
            #Then we login and get new JSESSIONID
            params = dict(self.defaultParams)
            params['header']['Referer'] = self.LOGIN_URL
            post_data = {'j_username':login, 'j_password':password}
            sts, data = self.cm.getPage(self.LOGIN_URL_2, params, post_data)
            
            # prev sts will be probably False due to ERROR 302, so there 
            # is there is no sens to check this status here
            sts,data = self.cm.getPage(self.MAINURL, self.defaultParams)
            if sts and 'href="/Logo?op=w"' in data:
                self.logged = True
                return True
        else:
            printDBG("AnyFilesVideoUrlExtractor.tryTologin wrong login data")
        self.logged = False
        return False

    def getVideoUrl(self, url):
        #show adult content
        #self.cm.addCookieItem(COOKIEFILE, {'name': 'AnyF18', 'value': 'mam18', 'domain': 'video.anyfiles.pl'}, False)
        if not self.isLogged():
            self.tryTologin()
        
        sts, data = self.cm.getPage(self.MAINURL, self.defaultParams)
        
        url = strwithmeta(url)
        
        params = dict(self.defaultParams)
        params['header'] = dict(params['header'])
        params['header']['Referer'] = url.meta.get('Referer', 'http://www.google.pl/')
        sts, data = self.cm.getPage(url, params)

        # GET VIDEO ID
        u = url.split('/')
        vidID = u[-1]
        tmp = self.cm.ph.getSearchGroups(url, '([0-9]+?)\,')[0]
        if tmp != '': vidID = tmp
        if tmp == '': tmp = self.cm.ph.getSearchGroups(url+'|', 'id=([0-9]+?)[^0-9]')[0]
        if tmp != '': vidID = tmp

        # get COOKIE
        url = self.MAINURL + '/videos.jsp?id=' + vidID
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: 
            return []
        fUrl = self.MAINURL + "/w.jsp?id=%s&width=640&height=360&start=0&skin=0&label=false&autostart=false" % vidID
        COOKIE_JSESSIONID = self.cm.getCookieItem(self.COOKIEFILE,'JSESSIONID')
        HEADER = {'Referer' : url, 'Cookie' : 'JSESSIONID=' + COOKIE_JSESSIONID + ';', 'User-Agent': self.defaultParams['header']['User-Agent']}
        request_param = {'header':HEADER}
        
        sts, data = self.cm.getPage(fUrl, request_param)
        if not sts: return []
        
        HEADER['Referer'] = fUrl
        
        tmp = re.compile('''['"](/video-js[^'^"]+?\.js)['"]''').findall(data)
        for item in tmp:
            sts, item = self.cm.getPage( self.MAINURL + item,  {'header': HEADER})
        
        linksTab = []
        config = CParsingHelper.getSearchGroups(data, '''['"](/AutocompleteData[^'^"]+?)['"]''', 1)[0]
        if '' != config:
            sts, data = self.cm.getPage( self.MAINURL + config.replace('&amp;', '&'),  {'header': HEADER})
            printDBG(data)
            if sts:
                source  = self.cm.ph.getSearchGroups(data, '''source\s*=\s*['"]([^'^"]+?)['"]''', 1)[0]
                extlink = self.cm.ph.getSearchGroups(data, '''extlink\s*=\s*['"]([^'^"]+?)['"]''', 1)[0]
                if self.cm.isValidUrl(extlink): linksTab.extend(self.up.getVideoLinkExt(extlink))
                if self.cm.isValidUrl(source): return [{'name':'AnyFiles.pl', 'url':source}]
        return linksTab
