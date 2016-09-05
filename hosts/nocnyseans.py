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
    return 'nocnyseans.pl'

class NocnySeansPL(CBaseHostClass):
    MAIN_URL    = 'http://nocnyseans.pl/'
    SRCH_URL    = MAIN_URL + 'szukaj'
    VIDEO_URL   = MAIN_URL + 'film/video'
    
    MAIN_CAT_TAB = [{'category':'latest_added',       'title': _('Latest added'),  'url':MAIN_URL,                   'icon':''},
                    {'category':'genres_movies',      'title': _('Movies'),        'url':MAIN_URL+'filmy-online/',   'icon':''},
                    {'category':'list_series',        'title': _('Series'),        'url':MAIN_URL+'seriale-online/', 'icon':''},
                    {'category':'list_movies',        'title': _('Junior'),        'url':MAIN_URL+'filmy-online/',  'cat':'2,3,5', 'icon':''},
                    {'category':'list_rank',          'title': _('Ranking'),       'url':MAIN_URL+'ranking', 'icon':''},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]
                    
    LAST_ADDED_TAB = [{'category':'latest_added_movies',  'title': _('Movies'),        'url':MAIN_URL, 'icon':''},
                      {'category':'latest_added_series',  'title': _('Series'),        'url':MAIN_URL, 'icon':''},
                      {'category':'latest_added_episodes','title': _('Episodes'),      'url':MAIN_URL, 'icon':''} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'NocnySeansPL', 'cookie':'nocnyseans.cookie'})
        self.filterCache = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("NocnySeansPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def _listLatestAddedTab(self, cItem, m1, m2, category='video'):
        printDBG("NocnySeansPL._listLatestAddedTab >>>>>>> cItem[%r]" % cItem)
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split('<div class="listing-item">')
        if len(data): del data[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            if category != 'video':
                params['category'] = category
                self.addDir(params)
            else: self.addVideo(params)
            
    def listLatestAddedMovies(self, cItem):
        printDBG("NocnySeansPL.listLatestAddedMovies")
        self._listLatestAddedTab(cItem, 'Ostatnio dodane filmy', '<div class="normal radius">', 'video')
        
    def listLatestAddedSeries(self, cItem, category):
        printDBG("NocnySeansPL.listLatestAddedSeries")
        self._listLatestAddedTab(cItem, 'Ostatnio dodane seriale', '<div class="normal radius">', category)
        
    def listLatestAddedEpisodes(self, cItem):
        printDBG("NocnySeansPL.listLatestAddedEpisodes")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Ostatnio dodane odcinki', '</table>', False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'data-url="([^"]+?)"')[0]
            tmp    = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td>', '</td>')
            if len(tmp) < 5: continue
            title = self.cleanHtmlStr( tmp[4] ) + ': ' + '[s{0}e{1}]'.format(self.cleanHtmlStr(tmp[3]), self.cleanHtmlStr(tmp[2])) + ' ' + self.cleanHtmlStr( tmp[1] )
            params = dict(cItem)
            params.update( {'title': title, 'url':self._getFullUrl(url)} )
            self.addVideo(params)
            
    def fillFilterCache(self, url):
        sts, data = self.cm.getPage(url)
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
        self.filterCache['category'] = _getFilters('<ul id="filter-category">', '</ul>', 'cat')
        self.filterCache['version']  = _getFilters('<ul id="filter-version">', '</ul>', 'ver')
        self.filterCache['year']     = _getFilters('<ul id="filter-year">', '</ul>', 'year')
        
    def listFilters(self, cItem, filter, category):
        printDBG("NocnySeansPL.listFilters")
        tab = self.filterCache.get(filter, [])
        if 0 == len(tab):
            self.fillFilterCache(self.MAIN_URL + 'filmy-online/')
            tab = self.filterCache.get(filter, [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
        
    def _listItemsTab(self, cItem, category='video'):
        printDBG("NocnySeansPL._listItemsTab >>>>>>> cItem[%r]" % cItem)
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'strona[%s]+' % page
        if '' != cItem.get('cat', ''):
            url += 'kategoria[%s]+' % cItem['cat']
        if '' != cItem.get('ver', ''):
            url += 'wersja[%s]+' % cItem['ver']
        if '' != cItem.get('year', ''):
            url += 'rok[%s]+' % cItem['year']
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('strona[%s]+' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '"filter-year">', '<div class="col-xs-12">', False)[1]
        data = data.split('<div class="normal radius">')
        if len(data): del data[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            tmp    = item.split('<div class="row">')
            if len(tmp) < 2: continue
            title  = tmp[0]
            desc   = tmp[1]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            if category != 'video':
                params['category'] = category
                self.addDir(params)
            else: self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listMovies(self, cItem):
        printDBG("NocnySeansPL.listMovies")
        self._listItemsTab(cItem, 'video')
        
    def listSeries(self, cItem, category):
        printDBG("NocnySeansPL.listSeries")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 

        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="term-list">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]

        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = ''
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( item ), 'url':self._getFullUrl(url), 'desc': '', 'icon':self._getFullUrl(icon)} )
            params['category'] = category
            self.addDir(params)
        
    def listLatestMovies(self, cItem):
        printDBG("NocnySeansPL.listLatestMovies")
        self._listLatestItemsTab(cItem, 'video')
            
    def listLatestSeries(self, cItem, category):
        printDBG("NocnySeansPL.listLatestSeries")
        self._listLatestItemsTab(cItem, category)
        
    def listEpisodes(self, cItem):
        printDBG("NocnySeansPL.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        seriesTitle = cItem['title']
        
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<div id="single-series" class="normal-content clearfix">', '<ul class="episode-list">', False)[1]
        icon = self.cm.ph.getSearchGroups(desc, 'src="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( desc )
        icon = self._getFullUrl( icon )
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="episode-list">', '</ul>', False)[1]
        data = re.compile('<li[^>]*?class="episode"[^>]*?><a[^>]*?href="([^"]+?)">([^<]+?)</a></li>').findall( data )
        sort = True
        episodesList = []
        for item in data:
            try:
                tmp = self.cm.ph.getSearchGroups(item[0], 'odcinek-([0-9]+?)-sezon-([0-9]+?)[^0-9]', 2)
                season  = int(tmp[1])
                episode = int(tmp[0])
            except Exception:
                printExc()
                season  = 0
                episode = 0
                sort    = False
            episodesList.append( {'title': seriesTitle + ': ' + self.cleanHtmlStr( item[1] ), 'url':self._getFullUrl(item[0]), 'desc':  desc, 'icon':icon, 'season':season, 'episode':episode})
        if sort:
            episodesList.sort(key=lambda item: item['season']*1000 + item['episode'])#, reverse=True)
            #episodesList.reverse()
        self.listsTab(episodesList, cItem, 'video')
        
    def listRanking(self, cItem):
        printDBG("NocnySeansPL.listRanking")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1]
            if '' == title: title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            rank   = self.cm.ph.getSearchGroups(item, '>([0-9.]+?)<')[0]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': rank + ', ' + self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("NocnySeansPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        post_data = {'search':searchPattern}
        sts, data = self.cm.getPage(self.SRCH_URL, {}, post_data)
        if not sts: return
        
        if searchType == 'movies':
            key = 'film'
        elif searchType == 'series':
            key = 'serial'
        
        data = data.split('<div class="listing-item">')
        if len(data): del data[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]*?/%s/[^"]*?)"' % key)[0]
            if '' == url: continue
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<b>', '</b>', False)[1] )
            if '' == title: title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0] )
            if '' == title: title = self.cm.ph.getSearchGroups(url, '/%s/([^"/]*?)[/"]' % key)[0].replace('-', ' ').capitalize()
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1] )

            params = dict(cItem)
            params.update( {'title':title, 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
            if searchType == 'movies':
                self.addVideo(params)
            elif searchType == 'series':
                params['category'] =  'list_episodes'
                self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("NocnySeansPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, 'data-iframe="([^"]+?)"')[0]
            if '' == url: continue
            name = self.cleanHtmlStr(item)
            urlTab.append({'name':name, 'url':url, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("NocnySeansPL.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = ''
        if baseUrl == NocnySeansPL.VIDEO_URL:
            HTTP_HEADER= {  "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
                            "Accept":"application/json, text/javascript, */*; q=0.01",
                            "Accept-Language":"pl,en-US;q=0.7,en;q=0.3",
                            "Accept-Encoding":"gzip, deflate",
                            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
                            "X-Requested-With":"XMLHttpRequest" }
            HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
            
            sts, data = self.cm.getPage(NocnySeansPL.VIDEO_URL, {'header' : HTTP_HEADER}, {'hash':baseUrl.meta['hash']})
            if not sts: return urlTab
            try:
                #printDBG(data)
                data = byteify(json.loads(data))
                url = data['url']
            except Exception:
                printExc()
        else:
            url = baseUrl
            
        if 'nocnyseans.pl' in url:
            sts, data = self.cm.getPage(url)
            if sts:
                data = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
                if '' != data:
                    url = data
        
        if url.startswith('//'):
            url = 'http:' + url
        
        if '' != url: 
            videoUrl = url
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

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
    #MOVIES
        elif category == 'genres_movies':
            self.listFilters(self.currItem, 'category', 'list_version_filter')
        elif category == 'list_version_filter':
            self.listFilters(self.currItem, 'version', 'list_yer_filter')
        elif category == 'list_yer_filter':
            self.listFilters(self.currItem, 'year', 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
        elif category == 'latest_movies':
            self.listLatestMovies(self.currItem)
        elif category == 'list_rank':
            self.listRanking(self.currItem)
    #SERIES
        #elif category == 'genres_series':
        #    self.listGenres(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
        elif category == 'latest_series':
            self.listLatestSeries(self.currItem, 'list_episodes')
    #LATEST ADDED
        elif category == 'latest_added':
            self.listsTab(self.LAST_ADDED_TAB, {'name':'category'})
        elif category == 'latest_added_movies':
            self.listLatestAddedMovies(self.currItem)
        elif category == 'latest_added_series':
            self.listLatestAddedSeries(self.currItem, 'list_episodes')
        elif category == 'latest_added_episodes':
            self.listLatestAddedEpisodes(self.currItem)
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
        CHostBase.__init__(self, NocnySeansPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
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
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except Exception:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
