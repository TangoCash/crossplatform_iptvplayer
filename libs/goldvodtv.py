# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, GetPyScriptCmd
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

from os import path as os_path
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
config.plugins.iptvplayer.goldvodtv_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.goldvodtv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry('goldvod.tv ' + _("email") + ':', config.plugins.iptvplayer.goldvodtv_login))
    optionList.append(getConfigListEntry('goldvod.tv ' + _("password") + ':', config.plugins.iptvplayer.goldvodtv_password))
    return optionList
    
###################################################

class GoldVodTVApi:
    MAIN_URL   = 'http://goldvod.tv/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAIN_URL }
    
    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('goldvodtv.cookie')
        self.sessionEx = MainSessionWrapper()
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        self.loggedIn = False
        
    def getFullUrl(self, url):
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return self.MAIN_URL + url[1:]
        else:
            return self.MAIN_URL + url
        return url
        
    def cleanHtmlStr(self, str):
        return CBaseHostClass.cleanHtmlStr(str)
        
    def getChannelsList(self, cItem):
        printDBG("TelewizjadaNetApi.getChannelsList")
        
        login    = config.plugins.iptvplayer.goldvodtv_login.value
        password = config.plugins.iptvplayer.goldvodtv_password.value
        if login != '' and password != '':        
            if self.doLogin(login, password):
                self.loggedIn = True
                self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
            else:
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
                self.loggedIn = False
        
        channelsTab = []
        
        nameMap = {'3':'Eleven','2':'TVP 1 HD','4':'Polsat HD','5':'Polsat 2 HD','6':'Canal+ Sport HD','7':'Eleven Sports',
        '8':'Canal+ Sport 2 HD','9':'Canal+ HD','10':'HGTV','11':'Eurosport 2 HD','12':'nSport HD',
        '13':'Eurosport HD','14':'Nickelodeon','15':'Comedy Central','16':'National Geographic Channel HD','17':'MTV',
        '18':'Polsat Sport News','19':'TTV','20':'TVN 7 HD','21':'MiniMini+','22':'Discovery Channel HD','23':'BBC Earth',
        '24':'Nat Geo Wild HD','25':'AXN HD','26':'TVP Seriale','27':'TVP Info','28':'Fokus TV','29':'TV Puls',
        '30':'TVP 2 HD','31':'TVN HD','32':'HBO HD','33':'TLC HD','34':'TVP HD','35':'TVP Sport HD','36':'Canal+ Film HD',
        '37':'Canal+ Family HD','38':'Canal+ Seriale','39':'Eska Rock','40':'Polo TV','41':'Eska go','42':'Eska TV',
        '43':'6','44':'Stopklatka TV','45':'Animal Planet HD','46':'TVN Style HD','47':'TVN Turbo HD','48':'TVN 24',
        '49':'KinoPolska PL','50':'HBO 2 HD','51':'HBO Comedy HD','52':'Travel Channel','53':'Polsat Sport HD',
        '54':'Fox HD','55':'TVP Historia','56':'TVN 24 Biznes i Świat','57':'AXN White','58':'AXN Black','59':'Polsat News',
        '60':'Cinemax 2 HD','61':'Discovery ID HD','62':'History HD','63':'Explorer','64':'Filmbox','65':'TVP Kultura',
        '66':'Comedy Central Family','67':'NickJR.','68':'Music VOX TV','69':'Eska Best Music TV','70':'Planete+',
        '71':'Tuba TV','72':'Music VOX TV','73':'TVK','74':'Czwórka Polskie Radio','75':'Disney XD','76':'Filmbox Family',
        '77':'TVP Pololnia','78':'Da Vinci Learning','79':'Polsat Film','80':'Disney Channel','81':'Kuchnia+','82':'History',
        '83':'4 Fun.TV','84':'SportKlub','85':'Domo+','86':'AXN Spin HD','87':'Discovery Historia','88':'4 Fun.TV','89':'Disney Junior',
        '94':'Kino Polska Muzyka', '102':'Boomerang', '97':'Polo Party TV', '96':'Fightklub', '100':'Canal+ HD', '101':'Canal+ Sport HD',
        '117':'nSport', '116':'Extreme Sport', '117':'Discovery Turbo', '118':'MGM', '109':'AXN Black', '106':'nSport', '134':'TVP ABC', 
        '135':'Puls 2', '113':'Polsat Sport Extra', '121':'NATGEO people HD', '119':'FilmBox HD', '139':'TV4', '146':'ATM rozrywka',
        '147':'Polsat Cafe HD', '123':'FilmBox Premium', '141':'JimJam Polsat', '167':'Animal Planet HD', '156':'Discovery life',
        '165':'Discovery life', '169':'Nat Geo Wild HD', '170':'Superstacja', '179':'4Fun TV', '126':'Polsat Play', '140':'Polsat Sport News',
        '206':'VOX Music TV', '193':'Filmbox', '192':'Filmbox Premium', '191':'8TV', '190':'Disco Polo Music', '202':'Polsat Sport Extra',
        '203':'Polsat Sport HD', '194':'Filmbox Family', '181':'Polsat 2', '204':'Polsat HD', '120':'Discovery Science', '205':'Canal+',
        '172':'Eleven Extra HD', '171':'Cartoon Network', '211':'13 Ulica HD', '212':'Lifetime HD', '213':'Universal Channel HD', '214':'BBC HD',
        '215':'FOX Comedy HD'}

        sts, data = self.cm.getPage(self.MAIN_URL + 'kanaly.html?show=on', self.http_params)
        if not sts: return []
        m1 = "<div class='box-channel'"
        if m1 not in data: m1 = "<a class='box-channel'"
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, m1, "<div id='footer'>")
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            printDBG("item [%r]" % item)
            url  = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
            icon = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            id   = self.cm.ph.getSearchGroups(url, '''[^0-9]([0-9]+?)[^0-9]''')[0]
            if '' != url:
                params = dict(cItem)
                params['url']   = self.getFullUrl(url)
                params['icon']  = self.getFullUrl(icon)
                params['title'] = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''')[0]
                if '' == params['title']: params['title'] = self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''')[0]
                if '' == params['title']: params['title'] = url.replace('.html', '').replace(',', ' ').title()
                params['title'] = nameMap.get(id, params['title'])
                params['desc']  = params['url']
                channelsTab.append(params)
            
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("GoldVodTVApi.getVideoLink")
        if self.loggedIn:
            url = strwithmeta(cItem['url'], {'params':{'load_cookie': True}})
        else:
            url = cItem['url']
        return self.up.getVideoLinkExt(url)
        
    def doLogin(self, login, password):
        logged = False
        loginUrl = self.MAIN_URL + 'login.html'
        
        params = dict(self.http_params)
        params['load_cookie'] = False
        sts, data = self.cm.getPage(loginUrl, params)
        if not sts: return False
        
        HTTP_HEADER= dict(GoldVodTVApi.HTTP_HEADER)
        HTTP_HEADER.update( {'Referer':loginUrl} )
        
        post_data = {'login': login, 'pass': password, 'remember': 1, 'logged': ''}
        params    = {'header': HTTP_HEADER, 'cookiefile': self.COOKIE_FILE, 'save_cookie': True, 'load_cookie': True}
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                if 'logout.html' in data:
                    printDBG('GoldVodTVApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('GoldVodTVApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('GoldVodTVApi.doLogin there is no cookie file after login')
        return logged
