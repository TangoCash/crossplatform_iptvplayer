# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, \
                                                               getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import base64
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://arconaitv.me/'

class ArconaitvME(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  ArconaitvME.tv', 'cookie':'ArconaitvME.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL      = 'https://www.arconaitv.me/'
        self.DEFAULT_ICON_URL  = "https://arconaitv.me/wp-content/uploads/2017/05/logo-white-1.png"

        self.MAIN_CAT_TAB = [{'category':'list_main',      'title': _('Main'),      'url':self.MAIN_URL},
                             {'category':'list_channels',  'title': _('Channels'),  'url':self.MAIN_URL},
                             {'category':'list_cabletv',   'title': _('Cable Tv'),  'url':self.MAIN_URL},
                             {'category':'list_movies',    'title': _('Movies'),    'url':self.MAIN_URL} ]
    
    def isProxyNeeded(self, url):
        return 'arconaitv.me' in url
        
    def getDefaulIcon(self, cItem=None):
        return self.getFullIconUrl(self.DEFAULT_ICON_URL)
        
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= dict(self.HEADER)
        params.update({'header':HTTP_HEADER})
        
        if self.isProxyNeeded( url ):
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote(url, ''))
            params['header']['Referer'] = proxy
            params['header']['Cookie'] = 'flags=2e5;'
            url = proxy
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and None == data:
            sts = False
        return sts, data
    
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        if self.isProxyNeeded( url ):
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote(url, ''))
            params = {}
            params['User-Agent'] = self.HEADER['User-Agent'],
            params['Referer'] = proxy
            params['Cookie'] = 'flags=2e5;'
            url = strwithmeta(proxy, params) 
        return url
        
    def getFullUrl(self, url):
        if 'proxy-german.de' in url:
            url = urllib.unquote( self.cm.ph.getSearchGroups(url+'&', '''\?q=(http[^&]+?)&''')[0] )
        return CBaseHostClass.getFullUrl(self, url)
    
    def listMain(self, cItem):
        printDBG("ArconaitvME.listMain")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'vc_align_center">', '</a>', False)
        for item in data:
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon == '': icon = cItem['icon']
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            if url == '': continue
            title = self.getFullUrl( icon ).split('/')[-1][:-4].replace('-', ' ').title()
            desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0] )
            if desc == '': desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0] )
            
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':self.getFullIconUrl( icon ), 'desc':desc})
            self.addVideo(params)
            
    def listItems(self, cItem, m1='', m2=''):
        printDBG("ArconaitvME.listItems")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li ', '</a>')
        for item in data:
            if 'menu-item-has-children' in item: continue
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            if url == '': continue
            title = self.cleanHtmlStr( item )
            
            params = dict(cItem)
            params.update({'title':title, 'url':url})
            self.addVideo(params)
        
    def listChannels(self, cItem):
        printDBG("ArconaitvME.listChannels")
        self.listItems(cItem, 'Channels', 'Cable Tv')
        
    def listCableTv(self, cItem):
        printDBG("ArconaitvME.listCableTv")
        self.listItems(cItem, 'Cable Tv', 'Movies')
        
    def listMovies(self, cItem):
        printDBG("ArconaitvME.listMovies")
        self.listItems(cItem, 'Movies', 'Donate')
        
    def getLinksForVideo(self, cItem):
        printDBG("ArconaitvME.getLinksForVideo [%s]" % cItem)
        urlsTab = []
        sts, data = self.getPage(cItem['url'])
        if not sts: return urlsTab
        
        printDBG(data)
        
        playerUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]*?src=['"](https?:[^"^']+?\.m3u8[^"^']*?)['"]''', 1, ignoreCase=True)[0]
        try: playerUrl = byteify(json.loads('"%s"' % playerUrl))
        except Exception: printExc()
        if not self.cm.isValidUrl(playerUrl): playerUrl = self.cm.ph.getSearchGroups(data, '''"sources"\s*:\s*[^\]]*?"src"\s*:\s*"(https?:[^"]+?\.m3u8[^"]*?)"''', 1, ignoreCase=True)[0]
        try: playerUrl = byteify(json.loads('"%s"' % playerUrl))
        except Exception: printExc()
        if not self.cm.isValidUrl(playerUrl): playerUrl = self.cm.ph.getSearchGroups(data, '''"(https?:[^"]+?\.m3u8[^"]*?)"''', 1, ignoreCase=True)[0]
        try: playerUrl = byteify(json.loads('"%s"' % playerUrl))
        except Exception: printExc()
        
        if self.cm.isValidUrl(playerUrl):
            tmp = getDirectM3U8Playlist(playerUrl)
            for item in tmp:
                item['need_resolve'] = 0
                urlsTab.append(item)
        return urlsTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        filter   = self.currItem.get("filter", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_main':
            self.listMain(self.currItem)
        elif category == 'list_channels':
            self.listChannels(self.currItem)
        elif category == 'list_cabletv':
            self.listCableTv(self.currItem)
        elif category == 'list_movies':
            self.listMovies(self.currItem)
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, ArconaitvME(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO])
    