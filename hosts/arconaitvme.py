# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
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
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
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
        self.DEFAULT_ICON  = "https://arconaitv.me/wp-content/uploads/2015/06/svs.png"

        self.MAIN_CAT_TAB = [{'icon':self.getIconUrl(self.DEFAULT_ICON), 'category':'list_main',      'title': _('Main'),      'url':self.MAIN_URL},
                             {'icon':self.getIconUrl(self.DEFAULT_ICON), 'category':'list_channels',  'title': _('Channels'),  'url':self.MAIN_URL},
                             {'icon':self.getIconUrl(self.DEFAULT_ICON), 'category':'list_cabletv',   'title': _('Cable Tv'),  'url':self.MAIN_URL},
                             {'icon':self.getIconUrl(self.DEFAULT_ICON), 'category':'list_movies',    'title': _('Movies'),    'url':self.MAIN_URL} ]
    
    def isProxyNeeded(self, url):
        return 'arconaitv.me' in url
        
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
        
    def getIconUrl(self, url):
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
            params.update({'title':title, 'url':url, 'icon':self.getIconUrl( icon ), 'desc':desc})
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
        
        data = self.cm.ph.getSearchGroups(data, '<source[^>]*?src="([^"]+?)"', 1, ignoreCase=True)[0]
        if data.startswith('http'):
            tmp = getDirectM3U8Playlist(data)
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
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem
