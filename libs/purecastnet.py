# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
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
try:    import json
except Exception: import simplejson as json
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
config.plugins.iptvplayer.purecastnet_login          = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.purecastnet_password       = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry( _("Email") + ": ", config.plugins.iptvplayer.purecastnet_login))
    optionList.append(getConfigListEntry( _("Password") + ": ", config.plugins.iptvplayer.purecastnet_password))
    return optionList
    
###################################################

class PurecastNetApi:
    MAIN_URL   = 'http://api.pure-cast.net/'
    MOVIE_URL  = MAIN_URL + 'filmy'
    LIVE_URL   = MAIN_URL + 'kanaly'
    VER_URL    = MAIN_URL + 'wersja'
    AUTH       = '?email={0}&pass={1}'
    HTTP_HEADER  = { 'User-Agent': 'XBMC', 'ContentType': 'application/x-www-form-urlencoded' }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        self.sessionEx = MainSessionWrapper()
        self.defParams = {'header':self.HTTP_HEADER}
        self.warned = False
        
    def id_generator(self, size=18, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
        
    def cleanHtmlStr(self, str):
        return CBaseHostClass.cleanHtmlStr(str)
    
    def getChannelsList(self, cItem):
        printDBG("PurecastNetApi.getChannelsList")
        
        login  = config.plugins.iptvplayer.purecastnet_login.value
        passwd = config.plugins.iptvplayer.purecastnet_password.value
        
        if ('' == login or '' == passwd) and not self.warned:
            self.sessionEx.open(MessageBox, _("There are no active premium account.\nUsing a limited version that may not work properly with congested links."), type = MessageBox.TYPE_INFO, timeout = 10 )
            self.warned = True
        
        channelsTab = []
        privCategory = cItem.get('priv_category', None)
        if None == privCategory:
            for item in [('Telewizja Online', 'tv'), ('Filmy Online', 'filmy')]:
                params = dict(cItem)
                params.update({'title':item[0], 'priv_category':item[1]})
                channelsTab.append(params)
            return channelsTab
        elif 'tv' == privCategory:
            url = self.LIVE_URL
            prefix = 'station'
        elif 'filmy' == privCategory:
            url = self.MOVIE_URL
            prefix = 'movie'
        
        url += self.AUTH.format(login, passwd)
        
        sts, data = self.cm.getPage(url, self.defParams)
        if not sts: return []
        try:
            data = byteify(json.loads(data))
            for item in data:
                params = dict(cItem)
                params.update({'type':'video', 'title':item[prefix+'Name'], 'icon':item[prefix+'Logo'], 'vid_url':item[prefix+'URL'].replace('swfVfy=true', ' ')})
                channelsTab.append(params)
        except Exception:
            printExc()
        return channelsTab
        
    def getPage(self, url, params={}, post_data=None):
        proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote_plus(url))
        params['header']['Referer'] = proxy
        url = proxy
        return self.cm.getPage(url, params, post_data)

    def getVideoLink(self, cItem):
        printDBG("PurecastNetApi.getVideoLink")
        
        urlsTab = [{'name':'kodi', 'url':cItem['vid_url']}]
        if 0:
            channelID = self.cm.ph.getSearchGroups(cItem['vid_url'], '[^\?]+?/([^/^\?]+?)\?')[0]
            url = 'http://pure-cast.net/kanalyPlayer?id=%s' %  channelID
            HTTP_HEADER = dict(self.HTTP_HEADER)
            HTTP_HEADER['User-Agent'] = self.id_generator()
            HTTP_HEADER['X-Forwarded-For'] = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
            
            sts, data = self.getPage(url, {'header':HTTP_HEADER})
            if not sts: return urlsTab
            
            rtmpUrl = self.cm.ph.getSearchGroups(data, '''["'](rtmp[^'^"]+?)['"]''')[0]
            url = rtmpUrl + ' swfUrl=http://pure-cast.net/jwplayer/jwplayer.flash.swf live=live'
            if url.startswith('rtmp://'):
                urlsTab.append({'name':'webpage', 'url':url})
        
        return urlsTab

