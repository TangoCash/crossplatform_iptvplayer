# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
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
    return 'alltube.tv'

class AlltubeTV(CBaseHostClass):
    USER_AGENT = 'curl/7'
    MAIN_URL    = 'http://alltube.tv/'
    SRCH_URL    = MAIN_URL + 'szukaj'
    DEFAULT_ICON = 'http://alltube.tv/static/main/newlogoall.png'
    #{'category':'latest_added',       'title': _('Latest added'),  'url':MAIN_URL,                   'icon':DEFAULT_ICON},
    MAIN_CAT_TAB = [{'category':'genres_movies',      'title': _('Movies'),        'url':MAIN_URL+'filmy-online/',   'icon':DEFAULT_ICON},
                    {'category':'cat_series',         'title': _('Series'),        'url':MAIN_URL+'seriale-online/', 'icon':DEFAULT_ICON},
                    {'category':'list_movies',        'title': _('Junior'),        'url':MAIN_URL+'dla-dzieci/',     'icon':DEFAULT_ICON},
                    {'category':'search',             'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',     'title': _('Search history'), 'icon':DEFAULT_ICON} ]
                      
    SERIES_CAT_TAB = [{'category':'list_series_list', 'title': _('List'),                       'url':MAIN_URL+'seriale-online/', 'icon':DEFAULT_ICON},
                      {'category':'list_series_abc',  'title': _('ABC'),                        'url':MAIN_URL+'seriale-online/', 'icon':DEFAULT_ICON},
                      {'category':'list_series',      'title': _('All'), 'letter':'all',        'url':MAIN_URL+'seriale-online/', 'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AlltubeTV', 'cookie':'alltubetv.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.filterCache = {}
        self.seriesCache = {}
        self.seriesLetters = []
        self.episodesCache = []
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':'alltube.tv', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url.strip())
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE, ['PHPSESSID'])
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def _listFilters(self, cItem, data):
        printDBG("AlltubeTV._listFilters")
        ret = False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<form id="filter"', '</form>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<button', '</button>')
        for item in data:
            filter = self.cm.ph.getSearchGroups(item, 'value="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(item)
            if filter != '' and title != '':
                ret = True
                params = dict(cItem)
                params.update({'title':title, 'check_filter':False, 'post_data':{'filter':filter}})
                self.addDir(params)
        return ret
            
    def _listItemsTab(self, cItem, m1, m2, sp, category='video'):
        printDBG("AlltubeTV._listItemsTab >>>>>>> cItem[%r]" % cItem)
        
        url = cItem['url']
        if '' != cItem.get('cat', ''):
            url += 'kategoria[%s]+' % cItem['cat']
        if '' != cItem.get('ver', ''):
            url += 'wersja[%s]+' % cItem['ver']
        if '' != cItem.get('year', ''):
            url += 'rok[%s]+' % cItem['year']
        page = cItem.get('page', 1)
        if page > 1:
            if category == 'video':
                url += 'strona[%s]+' % page
            else: url += '/%s' % page
            
        if 'filter' in cItem:
            filter = cItem['filter']
        else: filter = None
            
        post_data = cItem.get('post_data', None)
        
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return 
        
        if cItem.get('check_filter', True):
            if self._listFilters(cItem, data): return
            else: cItem['check_filter'] = False
            
        pageM1 = '<div id="pager"'
        
        if ('strona[%s]+' % (page + 1)) in data or 'Następna strona' in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(sp)
        if len(data) and m1 != sp: del data[0]
        if len(data): data[-1] = data[-1].split(pageM1)[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1]
            if '' == title: 
                title = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1]
            if '' == title: 
                title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1]
            if '' == desc:
                desc = item.split('<p>')[-1]
            
            params = dict(cItem)
            params.update( {'good_for_fav': True, 'title': self.cleanHtmlStr( title ), 'url':self.getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self.getFullUrl(icon)} )
            if category != 'video': #or '/serial/' in params['url']:
                params['category'] = category
                self.addDir(params)
            else: self.addVideo(params)
            
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
    
    def fillFilterCache(self, url):
        sts, data = self.getPage(url)
        if not sts: return
        def _getFilters(m1, m2, key):
            tab = []
            dat = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
            dat = re.compile('<li[^>]*?data-id="([^>]+?)"[^>]*?>([^>]+?)</li>').findall(dat)
            for item in dat:
                tab.append({key:item[0], 'title':item[1]})
            if len(tab):
                tab.insert(0, {'title':_('All')})
            return tab
        self.filterCache['category'] = _getFilters('filter-category">', '</ul>', 'cat')
        self.filterCache['version']  = _getFilters('id="filter-version">', '</ul>', 'ver')
        self.filterCache['year']     = _getFilters('id="filter-year">', '</ul>', 'year')
        
    def listFilters(self, cItem, filter, category):
        printDBG("AlltubeTV.listFilters")
        tab = self.filterCache.get(filter, [])
        if 0 == len(tab):
            self.fillFilterCache(self.MAIN_URL + 'filmy-online/')
            tab = self.filterCache.get(filter, [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
         
    def listMovies(self, cItem):
        printDBG("AlltubeTV.listMovies")
        self._listItemsTab(cItem, '<div class="item-block clearfix">', '<script>', '<div class="item-block clearfix">', category='video')
        
    def listSeriesList(self, cItem, category):
        printDBG("AlltubeTV.listSeriesList")
        self._listItemsTab(cItem, '<div class="item-block clearfix">', '<script>', '<div class="item-block clearfix">', category=category)
        
    def fillSeriesCache(self, url):
        printDBG("AlltubeTV.fillSeriesCache")
        self.seriesCache = {}
        self.seriesLetters = []
        sts, data = self.getPage(url)
        if not sts: return
        data = CParsingHelper.getDataBeetwenMarkers(data, 'term-list clearfix">', '</ul>', False)[1]
        data = re.compile('<li[^>]*?data-letter="([^"]+)"[^>]*?>[^<]*?<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            letter = item[0]
            url    = item[1]
            title  = item[2]
            if letter not in self.seriesCache:
                self.seriesCache[letter] = []
                self.seriesLetters.append({'title':letter,  'letter':letter})
            self.seriesCache[letter].append({'good_for_fav':True, 'title': self.cleanHtmlStr( title ), 'url':self.getFullUrl(url)})
        for idx in range(len(self.seriesLetters)):
            letter = self.seriesLetters[idx]['letter']
            self.seriesLetters[idx]['title'] = letter + ' [%d]' % len(self.seriesCache[letter]) 
            
    def listSeriesABC(self, cItem, category):
        printDBG("AlltubeTV.listSeriesABC")
        if 0 == len(self.seriesLetters):
            self.fillSeriesCache(self.MAIN_URL + 'seriale-online/')
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.seriesLetters, cItem)
        
    def listSeries(self, cItem, category):
        printDBG("AlltubeTV.listSeries")
        
        if 0 == len(self.seriesLetters):
            self.fillSeriesCache(self.MAIN_URL + 'seriale-online/')
        
        if 'all' == cItem['letter']:
            letters = self.seriesLetters
        else:
            letters = [cItem]
        for item in letters:
            letter = item['letter']
            tab = self.seriesCache.get(letter, [])
            cItem = dict(cItem)
            cItem['category'] = category
            self.listsTab(tab, cItem)
        
    def listAllSeries(self, category):
        sts, data = self.getPage(cItem['url'])
        if not sts: return 

        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="term-list">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]

        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = ''
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( item ), 'url':self.getFullUrl(url), 'desc': '', 'icon':self.getFullUrl(icon)} )
            params['category'] = category
            self.addDir(params)
            
    def listSeasons(self, cItem, category):
        printDBG("AlltubeTV.listSeasons")
        self.episodesCache = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        seriesTitle =  self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-xs-12 col-sm-9">', '</h3>', False)[1] )
        if '' == seriesTitle: seriesTitle = cItem['title']    
        
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<div class="custome-panel clearfix">', '</div>', False)[1]
        icon = self.cm.ph.getSearchGroups(desc, 'src="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( desc )
        icon = self.getFullUrl( icon )
        
        if '' == icon: icon = cItem.get('icon', '')
        if '' == desc: desc = cItem.get('desc', '')
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'ta odcin', '<script>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<h3 class="headline">', '</div>')
        for season in data:
            seasonTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(season, '<h3', '</h3>')[1] )
            episodes = re.compile('<li[^>]*?class="episode"[^>]*?><a[^>]*?href="([^"]+?)">([^<]+?)</a>').findall( season )
            sort = True
            episodesList = []
            for item in episodes:
                try:
                    tmp = self.cm.ph.getSearchGroups(item[0], 'odcinek-([0-9]+?)-sezon-([0-9]+?)[^0-9]', 2)
                    season  = int(tmp[1])
                    episode = int(tmp[0])
                except Exception:
                    printExc()
                    season  = 0
                    episode = 0
                    sort    = False
                episodesList.append( {'good_for_fav': True, 'title': seriesTitle + ': ' + self.cleanHtmlStr( item[1] ), 'url':self.getFullUrl(item[0]), 'desc':  desc, 'icon':icon, 'season':season, 'episode':episode})
            if sort:
                episodesList.sort(key=lambda item: item['season']*1000 + item['episode'])#, reverse=True)
                #episodesList.reverse()
            if len(episodesList):
                params = dict(cItem)
                params.update({'good_for_fav': False, 'category':category, 'season_idx':len(self.episodesCache), 'title':seasonTitle, 'desc':  desc, 'icon':icon})
                self.addDir(params)
                self.episodesCache.append(episodesList)
        
    def listEpisodes(self, cItem):
        printDBG("AlltubeTV.listEpisodes")
        seasonIdx = cItem.get('season_idx', -1)
        
        if seasonIdx >= 0 and seasonIdx < len(self.episodesCache):
            episodesList = self.episodesCache[seasonIdx]
            self.listsTab(episodesList, cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AlltubeTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        sts, data = self.getPage(self.SRCH_URL, {}, post_data={'search':searchPattern})
        if not sts: return
        
        data = self.cm.ph.rgetDataBeetwenMarkers(data, '<div class="container-fluid">', 'Kontakt')[1]
        data = data.split('<h2 class="headline">')
        if len(data): del data[0]
        
        if searchType == 'series':
            marker = 'Seriale'
        elif searchType == 'movies':
            marker = 'Filmy'
        else:
            return
        
        found = False
        for idx in range(len(data)):
            if data[idx].startswith(marker):
                found = True
                break
                
        if not found: return
        data = data[idx]
        data = data.split('<div class="item-block clearfix">')
        if len(data): del data[0]

        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1]
            if '' == title: title = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1]
            if '' == title:  title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1]
            if '' == desc: desc = item.split('<p>')[-1]
            
            params = dict(cItem)
            params.update({'good_for_fav': True, 'title':self.cleanHtmlStr( title ), 'url':self.getFullUrl( url ), 'icon':self.getFullUrl( icon ), 'desc':self.cleanHtmlStr( desc )})
            if searchType == 'series':
                params['category'] = 'list_seasons'
                self.addDir(params)
            else:
                self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("AlltubeTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return urlTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            try:
                url  = self.cm.ph.getSearchGroups(item, 'data-iframe="([^"]+?)"')[0]
                url  = base64.b64decode(url)
                name = self.cleanHtmlStr(item)
                urlTab.append({'name':name, 'url':url, 'need_resolve':1})
            except Exception:
                printExc()
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("AlltubeTV.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = ''
        if self.MAIN_URL in baseUrl:
            sts, data = self.getPage(baseUrl)
            if not sts: return []
            url = self.cm.ph.getDataBeetwenMarkers(data, 'src="', '"', False, False)[1]
        else:
            url = baseUrl
        
        if '' != url: 
            videoUrl = url
            if url.startswith('//'):
                videoUrl = 'http:' + videoUrl
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('AlltubeTV.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem.get('desc', ''), 'icon':cItem.get('icon', '')}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('AlltubeTV.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('AlltubeTV.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        self.cm.clearCookie(self.COOKIE_FILE, ['PHPSESSID', '__cfduid', 'cf_clearance'])
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #MOVIES
        elif category == 'genres_movies':
            self.listFilters(self.currItem, 'category', 'list_version_filter')
        elif category == 'list_version_filter':
            self.listFilters(self.currItem, 'version', 'list_yer_filter')
        elif category == 'list_yer_filter':
            self.listFilters(self.currItem, 'year', 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #SERIES
        elif category == 'cat_series':
            self.listsTab(self.SERIES_CAT_TAB, {'name':'category'})
        elif category == 'list_series_abc':
            self.listSeriesABC(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_seasons')
        elif category == 'list_series_list':
            self.listSeriesList(self.currItem, 'list_seasons')
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
            self.listsHistory({'name':'history', 'category': 'search', 'icon':self.DEFAULT_ICON}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AlltubeTV(), True)#, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
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
    '''
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    '''
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Movies"), "movies"))
        searchTypesOptions.append((_("Series"), "series"))
    
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
        icon        =  self.host.getIconUrl( cItem.get('icon', '') )
        isGoodForFavourites = cItem.get('good_for_fav', False)
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem
