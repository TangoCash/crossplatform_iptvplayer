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
    return 'http://kreskoweczki.pl/'

class KreskoweczkiPL(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  KreskoweczkiPL.tv', 'cookie':'kreskoweczkipl.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.abcCache = {}
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL      = 'https://www.kreskoweczki.pl/'
        self.SEARCH_URL    = self.MAIN_URL + 'szukaj'
        self.DEFAULT_ICON  = "http://svn.sd-xbmc.org/filedetails.php?repname=sd-xbmc&path=%2Ftrunk%2Fxbmc-addons%2Fsrc%2Fxbmc-addons%2Fkreskoweczki.png&rev=936&peg=936"

        self.MAIN_CAT_TAB = [{'icon':self.DEFAULT_ICON, 'category':'list_abc',        'title': 'Alfabetycznie',   'url':self.MAIN_URL },
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Ostatnio dodane', 'url':self.MAIN_URL + 'ostatnio-dodane/wszystkie'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Anime',           'url':self.MAIN_URL + 'typ/anime/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Bajki',           'url':self.MAIN_URL + 'typ/toon/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Seriale',         'url':self.MAIN_URL + 'typ/serial/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Pozostałe',       'url':self.MAIN_URL + 'typ/pozostale/'},
                             {'icon':self.DEFAULT_ICON, 'category':'search',          'title': _('Search'), 'search_item':True},
                             {'icon':self.DEFAULT_ICON, 'category':'search_history',  'title': _('Search history')} ]
        self.needProxy = None
        
    def isNeedProxy(self):
        if self.needProxy == None:
            sts, data = self.cm.getPage(self.MAIN_URL)
            self.needProxy = not sts
        return self.needProxy
        
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= dict(self.HEADER)
        params.update({'header':HTTP_HEADER})
        
        if self.isNeedProxy() and self.up.getDomain(self.MAIN_URL) in url:
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e1'.format(urllib.quote(url, ''))
            params['header']['Referer'] = proxy
            params['header']['Cookie'] = 'flags=2e5;'
            url = proxy
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and None == data:
            sts = False
        if sts and 'Duze obciazenie!' in data:
            SetIPTVPlayerLastHostError(self.cleanHtmlStr(data))
        return sts, data
        
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        if self.up.getDomain(self.MAIN_URL) in url and self.isNeedProxy():
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e1'.format(urllib.quote(url, ''))
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
        
    def listABC(self, cItem, category):
        printDBG("KreskoweczkiPL.listABC")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="category-list one-quarter">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr(item)
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url})
            self.addDir(params)
            
    def listTitles(self, cItem, nextCategory):
        printDBG("KreskoweczkiPL.listTitles")
        subCat = cItem.get('sub_cat', '')
        tab = self.abcCache.get(subCat, [])
        params = dict(cItem)
        params['category'] = nextCategory
        self.listsTab(tab, params)
            
    def listItems(self, cItem):
        printDBG("KreskoweczkiPL.listItems")
        
        url = cItem['url']
        page = cItem.get('page', 1)
        
        if page > 1:
            if '?' in url:
                url += '&page=%d' % page
            else:
                url += '/strona-%d' % page
        
        post_data = cItem.get('post_data', None)
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '''strona\-(%s)[^0-9]''' % (page + 1))[0]
        if nextPage == '': nextPage = self.cm.ph.getSearchGroups(data, '''page\,(%s)[^0-9]''' % (page + 1))[0]
        if nextPage != '':
            nextPage = True
        else: 
            nextPage = False
        
        videoMarker = '''/([0-9]+?)/'''
        if self.isNeedProxy():
            videoMarker = videoMarker.replace('/', '\\%2F')
        
        video = True
        m1 = '<a class="item" '
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, m1, '</li>')
        for item in data:
            video = True
            if '' == self.cm.ph.getSearchGroups(item, videoMarker)[0]:
                video = False
            # icon
            icon  = self.cm.ph.getSearchGroups(item, '''url\(['"]([^'^"]+?)['"]''')[0]
            if icon == '': icon = self.cm.ph.getSearchGroups(item, '''data-bg-url=['"]([^'^"]+?\.jpe?g)['"]''')[0]
            if icon == '': icon = cItem.get('icon', '')
            # url
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url == '': continue
            #title
            title = self.cm.ph.getDataBeetwenMarkers(item, '<div class="category-name"', '</div>')[1]
            if title == '': title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            if title == '': title = self.cm.ph.getDataBeetwenMarkers(item, '<a ', '</a>')[1]
            title = self.cm.ph.getDataBeetwenMarkers(item, '<span class="pm-category-name', '</span>')[1] + ' ' + title
            
            params = dict(cItem)
            params.pop('post_data', None)
            params.update({'page':1, 'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon':self.getFullUrl(icon)})
            printDBG(icon)
            if video:
                params.update({'desc':self.cleanHtmlStr(item)})
                self.addVideo(params)
            else:
                params.update({'desc':self.cleanHtmlStr(item.replace('</b>', '[/br]'))})
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("KreskoweczkiPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', caseSensitive=False)
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''action="([^"]+?)"''')[0]
            vid = self.cm.ph.getSearchGroups(item, '''value="([0-9]+?)"''')[0]
            if url != '' and vid != '':
                url = strwithmeta(self.getFullUrl(url), {'Referer':cItem['url'], 'vid':vid})
                urlTab.append({'name':self.cleanHtmlStr(item), 'url':url, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("KreskoweczkiPL.getVideoLinks [%s]" % videoUrl)

        videoUrl = strwithmeta(videoUrl)
        vid = videoUrl.meta.get('vid', '')
        ref = videoUrl.meta.get('Referer', '')
        if '' == vid: return []
        
        HEADER = dict(self.HEADER)
        HEADER['Referer'] = ref
        post_data = {'source_id' : vid}
        sts, data = self.getPage(videoUrl, {'header': HEADER}, post_data)
        if not sts: return []
        
        urlTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', caseSensitive=False)
        for item in data:
            videoUrl = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', ignoreCase=True)[0])
            if 1 != self.up.checkHostSupport(videoUrl): continue 
            urlTab.extend( self.up.getVideoLinkExt(videoUrl) )
        
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KreskoweczkiPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL
        cItem['post_data'] = {'query':searchPattern}
        self.listItems(cItem)
        
    def getFavouriteData(self, cItem):
        return str(cItem['url'])
        
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
        elif category == 'list_abc':
            self.listABC(self.currItem, 'list_items')
        elif category == 'list_titles':
            self.listTitles(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
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
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, KreskoweczkiPL(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
