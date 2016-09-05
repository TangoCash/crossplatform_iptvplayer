# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from datetime import datetime
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
    return 'http://kwejk.tv/'

class KwejkTV(CBaseHostClass):
    MAIN_URL    = 'http://kwejk.tv/'
    SRCH_URL    = MAIN_URL + '?s='
    DEFAULT_ICON_URL = 'http://kwejk.tv/wp-content/uploads/2016/02/kwejk.png'
    
    MAIN_CAT_TAB = [{'category':'movies_cats',    'title': 'Kategorie',       'url':MAIN_URL,                 'icon':DEFAULT_ICON_URL},
                    {'category':'movies_top100',  'title': 'Top 100',         'url':MAIN_URL,                 'icon':DEFAULT_ICON_URL},
                    {'category':'movies_year',    'title': 'Rok',             'url':MAIN_URL,                 'icon':DEFAULT_ICON_URL},
                    {'category':'series_cats',    'title': 'Seriale',         'url':MAIN_URL+'lista-seriali', 'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title': _('Search'),       'search_item':True,             'icon':DEFAULT_ICON_URL},
                    {'category':'search_history', 'title': _('Search history'),                               'icon':DEFAULT_ICON_URL} 
                   ]
    
    TOP100_TAB = [{'category':'list_top100', 'title':'24 godz',   'url':MAIN_URL + '24-godz/'},
                  {'category':'list_top100', 'title':'Tydzień',   'url':MAIN_URL + 'tydzien/'},
                  {'category':'list_top100', 'title':'Miesiąc',   'url':MAIN_URL + 'miesiac/'},
                  {'category':'list_top100', 'title':'Kwartał',   'url':MAIN_URL + 'kwartal/'},
                  {'category':'list_top100', 'title':'Popularne', 'url':MAIN_URL + 'popularne'},
                 ]
                 
    SERIES_TAB = [{'category':'list_series',        'title':'Ostatnio zaktualizowane'},
                  {'category':'list_abc_series',    'title':'ABC'},
                  {'category':'list_all_series',    'title':'Wszystkie seriale'},
                 ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'KwejkTV', 'cookie':'KwejkTV.cookie'})
        self.catsCache = []
        self.seriesCache = []
        self.episodesCache = []
        
    def _getFullUrl(self, url, series=False):
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def getDefaultIcon(self):
        return self.DEFAULT_ICON_URL
        
    def fillFilters(self, url):
        printDBG("KwejkTV.fillFilters")
        self.catsCache = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="categories', '</ul>', True)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul>', '</ul>', False)[1]
        data = data.split('</li>')
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0]
            if url.startswith('http'):
                self.catsCache.append({'title':title, 'url':url})
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("KwejkTV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listYears(self, cItem, category):
        printDBG("KwejkTV.listYears")
        year = datetime.now().year
        tab = []
        while year >= 1978:
            tab.append({'title': str(year), 'url': self._getFullUrl('tag/%s/' % year)})
            year -= 1
        
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
        
    def listMoviesCategories(self, cItem, category):
        printDBG("KwejkTV.listMoviesCategories")
        if 0 == len(self.catsCache):
            self.fillFilters(cItem['url'])
        
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.catsCache, cItem)
            
    def listTop100(self, cItem):
        printDBG("KwejkTV.listTop100")
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ol class="wpp-list">', '</ol>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'url\((http[^\)]+?jpg)\)')[0]
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
            
    def listMoviesCategories(self, cItem, category):
        printDBG("KwejkTV.listMoviesCategories")
        if 0 == len(self.catsCache):
            self.fillFilters(cItem['url'])
            
        params = dict(cItem)
        params.update({'category':category, 'title':'--Wszystkie--'})
        self.addDir(params)
        
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.catsCache, cItem)
            
    def listMovies(self, cItem):
        printDBG("KwejkTV.listMovies")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%d/' % page
        if post != '': 
            url += '?' + post
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="nag cf">', '<!-- end .loop-content -->', False)[1]
        data = data.split('<div class="thumb">')
        if len(data): del data[0]
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listSeriesAbc(self, cItem, category):
        printDBG("KwejkTV.listSeriesAbc")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="listSeries">', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</li>')
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            params = dict(cItem)
            params.update( {'category':category, 'title': self.cleanHtmlStr( item ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self._getFullUrl(icon)} )
            self.addDir(params)
            
    def listSeries(self, cItem, category, m1='<ul id="latestSeries">'):
        printDBG("KwejkTV.listSeries")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            #printDBG("==========================================")
            #printDBG(item)
            url    = self.cm.ph.getSearchGroups(item, 'href=([^>^\t]+?)[">\t]')[0].replace('"', '').strip()
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            params = dict(cItem)
            params.update( {'category':category, 'title': self.cleanHtmlStr( item ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self._getFullUrl(icon)} )
            self.addDir(params)
            
    def listAllSeries(self, cItem, category):
        printDBG("KwejkTV.listAllSeries")
        self.listSeries(cItem, category, m1='class="filter"')
            
    def listSeasons(self, cItem, category):
        printDBG("KwejkTV.listSeasons")
        self.episodesCache = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<table>', '</table>', False)[1]
        seriesTitle = self.cm.ph.getDataBeetwenMarkers(tmp, '<h2 class="entry-title">', '</h2>', False)[1]
        seriesTitle = self.cleanHtmlStr( seriesTitle )
        
        icon = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?)"')[0]
        icon = self._getFullUrl( icon )
        
        desc = self.cleanHtmlStr( tmp )
        
        if '' == icon: icon = cItem.get('icon', '')
        if '' == desc: desc = cItem.get('desc', '')
        
        m1 = '<h1 style="background-color: #b74443;padding:8px;  margin-top: 20px;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<!--end .hentry-->', False)[1]
        data = data.split(m1)
        for season in data:
            tmp = season.split('</h1>')
            seasonTitle = tmp[0].strip()
            episodes = tmp[-1].split('</a>')
            episodesList = []
            for item in episodes:
                title = self.cleanHtmlStr( item )
                url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                if url != '':
                    episodesList.append( {'title': seriesTitle + ': ' + self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'desc':desc, 'icon':icon})
            if len(episodesList):
                params = dict(cItem)
                params.update({'category':category, 'season_idx':len(self.episodesCache), 'title':seasonTitle, 'desc':  desc, 'icon':icon})
                self.addDir(params)
                self.episodesCache.append(episodesList)
        
    def listEpisodes(self, cItem):
        printDBG("KwejkTV.listEpisodes")
        seasonIdx = cItem['season_idx']
        
        if seasonIdx >= 0 and seasonIdx < len(self.episodesCache):
            episodesList = self.episodesCache[seasonIdx]
            self.listsTab(episodesList, cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url']  = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listMovies(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("KwejkTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', False)
        for baseUrl in [self.MAIN_URL]: #, 'http://kinofan.tv/']:
            for item in data:
                url = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                if url == '': continue
                if 'facebook' in url: continue
                
                if url.startswith('..'):
                    url = self._getFullUrl( url[2:] )
                    
                if 1 == self.up.checkHostSupport(url):
                    urlTab.append({'name':self.up.getHostName(url), 'url':url, 'need_resolve':1})
                elif 'kwejk.tv' in url:    
                    urlTab.append({'name':'kwejk.tv', 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("KwejkTV.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        videoUrl = baseUrl
        if 'kwejk.tv' in baseUrl:
            sub = 0 
            while sub < 5:
                sub += 1
                sts, data = self.cm.getPage(videoUrl)
                if not sts: return []
                prevVideoUrl = videoUrl
                videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
                if '' == videoUrl: videoUrl = self.cm.ph.getSearchGroups(data, 'link[^;^<]*?"(http[^"]+?)"')[0]
                if '://' not in videoUrl:
                    import urlparse
                    videoUrl = urlparse.urljoin(prevVideoUrl, videoUrl)
                videoUrl = self._getFullUrl( videoUrl )
                if 1 == self.up.checkHostSupport(videoUrl):
                    break
        
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem.get('url', ''))
        if not sts: return retTab
        
        title = self.cm.ph.getDataBeetwenMarkers(data, '"og:title" content="', '"', False)[1].split('|')[0]
        desc  = self.cm.ph.getDataBeetwenMarkers(data, '"og:description" content="', '"', False)[1]
        icon  = self.cm.ph.getDataBeetwenMarkers(data, '"og:image" content="', '"', False)[1]
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<strong>', '<div id="extras">', False)[1].split('<strong>')
        printDBG(descData)
        descTabMap = {"Oryginalny tytuł": "alternate_title",
                      "Kraj": "country",
                      "Rok produkcji": "year",
                      "Reżyseria": "director",
                      "Scenariusz": "writer",
                      "Aktorzy": "actors",}
        otherInfo = {}
        for item in descData:
            item = item.split('</strong>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key in descTabMap:
                otherInfo[descTabMap[key]] = val
        
        cats = self.cm.ph.getAllItemsBeetwenMarkers(data, 'rel="category tag">', '</a>', False)
        if len(cats):
            otherInfo['genre'] = ', '.join(cats)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'movies_cats':
            self.listMoviesCategories(self.currItem, 'list_movies')
    #MOVIES
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #TOP 100
        elif category == 'movies_top100':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_top100'
            self.listsTab(self.TOP100_TAB, cItem)
        elif category == 'list_top100':
            self.listTop100(self.currItem)
    #YEAR
        elif category == 'movies_year':
            self.listYears(self.currItem, 'list_movies')
    #SERIES
        elif category == 'series_cats':
            self.listsTab(self.SERIES_TAB, self.currItem)
        elif category == 'list_abc_series':
            self.listSeriesAbc(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_seasons')
        elif category == 'list_all_series':
            self.listAllSeries(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, KwejkTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
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
        
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        if len(hList): retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
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
        if icon == '': icon = self.host.getDefaultIcon()
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

