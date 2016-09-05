# -*- coding: utf-8 -*-

###################################################
# LOCAL import
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
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
    MAINURL     = 'http://video.anyfiles.pl'
    LOGIN_URL_2 = MAINURL + '/j_security_check'
    LOGIN_URL   = MAINURL + '/Logo?op=l'
    
    def __init__(self):
        self.cm = common()
        self.ytp = YouTubeParser()
        self.ytformats = 'mp4'
        self.defaultParams = {'header':{'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0'}, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': AnyFilesVideoUrlExtractor.COOKIEFILE}
        self.logged = False
    
    def isLogged(self):
        return self.logged
        
    def tryTologin(self):
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

    def getYTVideoUrl(self, url):
        printDBG("getYTVideoUrl url[%s]" % url)
        tmpTab = self.ytp.getDirectLinks(url, self.ytformats)
        
        movieUrls = []
        for item in tmpTab:
            movieUrls.append({ 'name': 'YouTube: ' + item['format'] + '\t' + item['ext'] , 'url':item['url'].encode('UTF-8') })
        
        return movieUrls

    def getVideoUrl(self, url):
        #show adult content
        #self.cm.addCookieItem(COOKIEFILE, {'name': 'AnyF18', 'value': 'mam18', 'domain': 'video.anyfiles.pl'}, False)
        if not self.isLogged():
            self.tryTologin()

        # GET VIDEO ID
        u = url.split('/')
        vidID = u[-1]
        match = re.search('([0-9]+?)\,', url )
        if match:
            vidID = match.group(1)

        # get COOKIE
        url = self.MAINURL + '/videos.jsp?id=' + vidID
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: 
            return []
        fUrl = self.MAINURL + "/w.jsp?id=%s&width=620&height=349&pos=0&skin=0" % vidID
        COOKIE_JSESSIONID = self.cm.getCookieItem(self.COOKIEFILE,'JSESSIONID')
        HEADER = {'Referer' : url, 'Cookie' : 'JSESSIONID=' + COOKIE_JSESSIONID + ';', 'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}
        request_param = {'header':HEADER}
        sts, data = self.cm.getPage(fUrl, request_param)
        if not sts: return []
        HEADER['Referer'] = fUrl
        config = CParsingHelper.getSearchGroups(data, 'src="/?(pcs\?code=[^"]+?)"', 1)[0]
        if '' != config:
            sts,data = self.cm.getPage( self.MAINURL + '/' + config,  {'header': HEADER})
            if sts:
                #var source = "<source src=\"http://50.7.220.66/video/60ExQvchsi4PbqMLr--I7A/1433518629/5e638de7a15c7a8dc7c979044cd2a953_147325.mp4\" type=\"video/mp4\" />";
                #var track = "<track label=\"izombie.112...\" srclang=\"pl\" kind=\"captions\"  src=\"http://video.anyfiles.pl/subtit/1433508336949.srt\"></track>\n";
                data = data.replace('\\"', '"')
                #printDBG(data)
                difSourcesSrc = CParsingHelper.getSearchGroups(data, '''difSourcesSrc[^=]*?=[^"']*?["'](http[^'^"]+?)['"]''', 1)[0] 
                url    = CParsingHelper.getSearchGroups(data, '''<source[^>]+?src=["'](http[^'^"]+?)['"]''', 1)[0]
                subUrl = CParsingHelper.getSearchGroups(data, '''<track[^>]+?src=["'](http[^'^"]+?)['"]''', 1)[0]
                if 'youtube' in difSourcesSrc: 
                    return self.getYTVideoUrl(difSourcesSrc)
                else:
                    return [{'name':'AnyFiles.pl', 'url':url}]
        return []
