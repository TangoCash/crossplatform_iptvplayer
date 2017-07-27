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
        
        self.MAIN_URL      = 'http://www.arconaitv.me/'
        self.DEFAULT_ICON_URL  = "https://pbs.twimg.com/profile_images/590745210000433152/2u_nu2TM.png"

        self.MAIN_CAT_TAB = [{'category':'list_main',      'title': _('Main'),      'url':self.MAIN_URL},
                             {'category':'list_shows',     'title': _('Shows'),     'url':self.MAIN_URL},
                             {'category':'list_cabletv',   'title': _('Cable'),     'url':self.MAIN_URL},
                             {'category':'list_movies',    'title': _('Movies'),    'url':self.MAIN_URL},
                             
                             {'category':'search',            'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',    'title': _('Search history'),            } 
                            ]
    
    def isProxyNeeded(self, url):
        return 'arconaitv.me' in url
        
    def getDefaulIcon(self, cItem=None):
        return self.getFullIconUrl(self.DEFAULT_ICON_URL)
        
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= dict(self.HEADER)
        if post_data != None: HTTP_HEADER['Content-Type'] = 'application/x-www-form-urlencoded'
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
    
    def listItems(self, cItem, m1='', m2='', post_data=None):
        printDBG("ArconaitvME.listItems")
        sts, data = self.getPage(cItem['url'], post_data=post_data)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>', False)
        
        for item in data:
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            if url == '': continue
            title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0] )
            
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':self.getFullIconUrl( icon )})
            self.addVideo(params)
        
    def listMain(self, cItem):
        printDBG("ArconaitvME.listMain")
        self.listItems(cItem, '<div class="content">', '<div class="row">')
        
    def listShows(self, cItem):
        printDBG("ArconaitvME.listShows")
        self.listItems(cItem, '''<div class='stream-category'>Shows</div>''', '<div class="box-content">')
        
    def listCableTv(self, cItem):
        printDBG("ArconaitvME.listCableTv")
        self.listItems(cItem, '''div class='stream-category'>Cable</div>''', '<div class="box-content">')
        
    def listMovies(self, cItem):
        printDBG("ArconaitvME.listMovies")
        self.listItems(cItem, '''<div class='stream-category'>Movies</div>''', '<div class="box-content">')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("ArconaitvME.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = self.getFullUrl('/search.php')
        cItem = dict(cItem)
        cItem['url'] = url
        self.listItems(cItem, '<div class="searchresults">', '<div class="acontainer">', post_data={'q':searchPattern})
        
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
        
        playerUrl = strwithmeta(playerUrl, {'Referer':cItem['url'], 'Origin':self.getMainUrl()})
        
        if self.cm.isValidUrl(playerUrl):
            tmp = getDirectM3U8Playlist(playerUrl, checkContent=True)
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
        elif category == 'list_shows':
            self.listShows(self.currItem)
        elif category == 'list_cabletv':
            self.listCableTv(self.currItem)
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, ArconaitvME(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO])
    