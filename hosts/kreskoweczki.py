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
    return 'http://kreskoweczki.pl/'

class KreskoweczkiPL(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  KreskoweczkiPL.tv', 'cookie':'kreskoweczkipl.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.abcCache = {}
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL      = 'http://www.kreskoweczki.pl/'
        self.SEARCH_URL    = self.MAIN_URL + 'search.php?keywords='
        self.DEFAULT_ICON  = "http://www.kreskoweczki.pl/uploads/custom-logo.png"

        self.MAIN_CAT_TAB = [{'icon':self.DEFAULT_ICON, 'category':'list_abc',        'title': 'Alfabetycznie',   'url':self.MAIN_URL + 'index.html'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Ostatnio dodane', 'url':self.MAIN_URL + 'index.html'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Anime',           'url':self.MAIN_URL + 'typ/anime/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Bajki',           'url':self.MAIN_URL + 'typ/toon/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Seriale',         'url':self.MAIN_URL + 'typ/serial/'},
                             {'icon':self.DEFAULT_ICON, 'category':'list_items',      'title': 'Pozostałe',       'url':self.MAIN_URL + 'typ/pozostale/'},
                             {'icon':self.DEFAULT_ICON, 'category':'search',          'title': _('Search'), 'search_item':True},
                             {'icon':self.DEFAULT_ICON, 'category':'search_history',  'title': _('Search history')} ]
            
    def listABC(self, cItem, category):
        printDBG("KreskoweczkiPL.listABC")
        
        sts, data = self.cm.getPage(cItem['url'])
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
                url += '?page=%d' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        #nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="loop-nav-inner">', '</div>', False)[1]
        if 'page,{0}/'.format(page+1) in data:
            nextPage = True
        else: 
            nextPage = False
        
        video = True
        m1 = '<div class="pm-li-video"'
        if m1 not in data: 
            m1 = '<a class="category-item"'
            video = False
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, m1, '</li>')
        for item in data:   
            # icon
            icon  = self.cm.ph.getSearchGroups(item, '''url\(['"]([^'^"]+?)['"]''')[0]
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
            params.update({'page':1, 'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon':self.getFullUrl(icon)})
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

        vid = self.cm.ph.getSearchGroups(cItem['url'], '''kreskowka/([0-9]+?)/''')[0]
        if '' == vid: return []
        
        HEADER = dict(self.HEADER)
        HEADER['Referer'] = cItem['url']
        post_data = {'vid' : vid}
        sts, data = self.cm.getPage('http://www.kreskoweczki.pl/fullscreen/', {'header': HEADER}, post_data)
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', caseSensitive=False)
        for item in data:
            videoUrl = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', ignoreCase=True)[0])
            if 1 != self.up.checkHostSupport(videoUrl): continue 
            urlTab.append({'name':self.up.getHostName(videoUrl), 'url':videoUrl.replace('&amp;', '&'), 'need_resolve':1})
            
        return urlTab

        sts, videoData = self.cm.ph.getDataBeetwenMarkers(data, 'Loader.skipBanners', 'Loader.skipBanners', False)
        if sts:
            videoUrl = self.cm.ph.getSearchGroups(videoData, '''Loader.loadFlashFile."([^"]+?)"''')[0]
            if '' == videoUrl:
                videoUrl = self.cm.ph.getSearchGroups(videoData, '''src="(.+?)"''')[0]
        
        if 'src=' in  videoUrl:
            videoUrl = self.cm.ph.getSearchGroups(videoUrl, '''src="(.+?)"''')[0]
            
        videoData = self.cm.ph.getSearchGroups(videoUrl, "/embed/proxy[^.]+?.php")
        if '' != videoData:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '''url: "[^?^"]+?\?url=([^"]+?)"''')[0]
            if videoUrl.split('?')[0].endswith('.m3u8'):
                urlTab = getDirectM3U8Playlist(videoUrl)
                for idx in len(urlTab):
                    urlTab[idx]['need_resolve'] = 0
        else: 
            if videoUrl.startswith('//'):
                videoUrl = 'http:' + videoUrl
            urlTab.append({'name':self.up.getHostName(videoUrl), 'url':videoUrl.replace('&amp;', '&'), 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("KreskoweczkiPL.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
            urlTab.extend( self.up.getVideoLinkExt(videoUrl) )
        
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KreskoweczkiPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + urllib.quote(searchPattern) 
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
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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

