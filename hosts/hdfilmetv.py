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
    return 'http://hdfilme.tv/'

class HDFilmeTV(CBaseHostClass):
    USER_AGENT = 'curl/7' #'Mozilla/5.0'
    HEADER = {'User-Agent': USER_AGENT, 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://hdfilme.tv/'
    SEARCH_URL    = MAIN_URL + 'movie/search'
    DEFAULT_ICON  = "https://raw.githubusercontent.com/StoneOffStones/plugin.video.xstream/c88b2a6953febf6e46cf77f891d550a3c2ee5eea/resources/art/sites/hdfilme.png" #"http://hdfilme.tv/public/site/images/logo.png"

    MAIN_CAT_TAB = [{'icon':DEFAULT_ICON, 'category':'list_filters',    'filter':'genre',    'title': _('Movies'),  'url':MAIN_URL+'movie-movies'},
                    {'icon':DEFAULT_ICON, 'category':'list_filters',    'filter':'genre',    'title': _('Series'),  'url':MAIN_URL+'movie-series'},
                    {'icon':DEFAULT_ICON, 'category':'list_filters',    'filter':'genre',    'title': _('Trailers'),'url':MAIN_URL+'movie-trailer'},
                    {'icon':DEFAULT_ICON, 'category':'search',          'title': _('Search'), 'search_item':True},
                    {'icon':DEFAULT_ICON, 'category':'search_history',  'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  HDFilmeTV.tv', 'cookie':'hdfilmetv.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.filtersCache = {'genre':[], 'country':[], 'sort':[]}
        self.seasonCache = {}
        self.cacheLinks = {}
        self.needProxy = None
        
    def isNeedProxy(self):
        if self.needProxy == None:
            sts, data = self.cm.getPage(self.MAIN_URL)
            self.needProxy = not sts
        return self.needProxy
    
    def _getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= dict(self.HEADER)
        params.update({'header':HTTP_HEADER})
        
        if self.isNeedProxy() and 'hdfilme.tv' in url:
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote(url, ''))
            params['header']['Referer'] = proxy
            params['header']['Cookie'] = 'flags=2e5;'
            url = proxy
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and None == data:
            sts = False
        return sts, data
        
    def _getIconUrl(self, url):
        url = self.getFullUrl(url)
        if 'hdfilme.tv' in url and self.isNeedProxy():
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
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':'hdfilme.tv', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
            
    def fillFiltersCache(self, cItem):
        printDBG("HDFilmeTV.fillFiltersCache")
        self.filtersCache = {'genre':[], 'country':[], 'sort':[]}
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        for filter in [{'m':'name="cat"', 'key':'genre'}, {'m':'name="country"', 'key':'country'}, {'m':'name="order_f"', 'key':'sort'}]:
            filterData = self.cm.ph.getDataBeetwenMarkers(data, filter['m'], '</select>', False)[1]
            filterData = self.cm.ph.getAllItemsBeetwenMarkers(filterData, '<option', '</option>')
            for item in filterData:
                title = self.cleanHtmlStr(item)
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                if value == '': continue
                self.filtersCache[filter['key']].append({'title':title, filter['key']:value})
            if len(self.filtersCache[filter['key']]):
                self.filtersCache[filter['key']].insert(0, {'title':_('--All--'), filter['key']:''})
            
    def listFilters(self, cItem, nextCategory, nextFilter):
        filter = cItem.get('filter', '')
        printDBG("HDFilmeTV.listFilters filter[%s] nextFilter[%s]" % (filter, nextFilter))
        tab = self.filtersCache.get(filter, [])
        if len(tab) == 0:
            self.fillFiltersCache(cItem)
        tab = self.filtersCache.get(filter, [])
        params = dict(cItem)
        params['category'] = nextCategory
        params['filter'] = nextFilter
        self.listsTab(tab, params)
            
    def listItems(self, cItem, nextCategory):
        printDBG("HDFilmeTV.listItems")
        
        itemsPerPage = 50
        page      = cItem.get('page', 1)
        url       = cItem['url']
        
        if 'search_pattern' in cItem:
            url += '?key=%s&per_page=%s' % (cItem['search_pattern'], (page-1)*itemsPerPage)
        else:
            url += '?cat=%s&country=%s&order_f=%s&per_page=%s&order_d=desc' % (cItem['genre'], cItem['country'], cItem['sort'], (page-1)*itemsPerPage)
        
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>', False)[1]
        if '>{0}<'.format(page+1) in nextPage:
            nextPage = True
        else: 
            nextPage = False
        

        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="products row">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:   
            # icon
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon == '': icon = cItem['icon']
            # url
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url == '': continue
            #title
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="name">', '</span>')[1] )
            if title == '': title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3 ', '</h3>')[1] )
            #desc
            desc = self.cleanHtmlStr(item)
            
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':self.getFullUrl(url), 'icon':self.getIconUrl(icon), 'desc':desc})
            self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("HDFilmeTV.listItems")
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        trailerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a[^>]*?class="btn btn-xemnow pull-right"[^>]*?href=['"]([^'^"]+?)['"][^>]*?>Trailer<''')[0])
        if trailerUrl.startswith('http'):
            params = dict(cItem)
            params.update({'title':_('Trailer'), 'urls':[{'name':'trailer', 'url':trailerUrl.replace('&amp;', '&'), 'need_resolve':1}]})
            self.addVideo(params)
        
        episodesTab = []
        episodesLinks = {}
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<section class="box">', '</section>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<i class="fa fa-chevron-right">', '</ul>') #'<ul class="list-inline list-film"'
        for server in data:
            serverName = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(server, '<i ', '</div>')[1] )
            serverData = self.cm.ph.getAllItemsBeetwenMarkers(server, '<li', '</li>')
            for link in serverData:
                episodeName = self.cleanHtmlStr( link )
                episodeUrl  = self.getFullUrl( self.cm.ph.getSearchGroups(link, '''href=['"]([^'^"]+?)['"]''')[0] )
                if not episodeUrl.startswith('http'): continue
                if episodeName not in episodesTab:
                    episodesTab.append(episodeName)
                    episodesLinks[episodeName] = []
                episodesLinks[episodeName].append({'name':serverName, 'url':episodeUrl.replace('&amp;', '&'), 'need_resolve':1})
        
        season = self.cm.ph.getSearchGroups(cItem['url'], '''staf[f]+?el-([0-9]+?)-''')[0]
        try: episodesTab.sort(key=lambda item: int(item))
        except Exception:
            printExc()
        for episode in episodesTab:
            title = cItem['title']
            if season != '': title += ': ' + 's%se%s'% (season.zfill(2), episode.zfill(2))
            else: title += ': ' + 'e%s'% (episode.zfill(2))
            params = dict(cItem)
            params.update({'title':title, 'urls':episodesLinks[episode]})
            self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("HDFilmeTV.getLinksForVideo [%s]" % cItem)
        return cItem.get('urls', [])
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDFilmeTV.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        sts, data = self.getPage(videoUrl, self.defaultParams)
        if not sts: return []
        
        googleUrls = self.cm.ph.getSearchGroups(data, '''var hdfilme[^=]*?=[^[]*?(\[[^;]+?);''')[0].strip()
        if '' == googleUrls: googleUrls = self.cm.ph.getSearchGroups(data, '''[\s]['"]?sources['"]?[^=^:]*?[=:][\s]*[^[]*?(\[[^]]+?\])''')[0].strip()
        printDBG(googleUrls)
        
        if googleUrls != '':
            try:
                googleUrls = byteify( json.loads(googleUrls) )
                for item in googleUrls:
                    if item['type'] != 'mp4':
                        continue
                    urlTab.append({'name':item['label'], 'url':self.getFullUrl(item['file'])})
            except Exception:
                printExc()
        if len(urlTab):
            return urlTab
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', caseSensitive=False)
        for item in data:
            vidUrl = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', ignoreCase=True)[0])
            if 1 != self.up.checkHostSupport(vidUrl): continue 
            urlTab.extend( self.up.getVideoLinkExt(vidUrl) )
        
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("HDFilmeTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['search_pattern'] = urllib.quote(searchPattern) 
        cItem['url'] = self.SEARCH_URL
        self.listItems(cItem, 'explore_item')
        
    def getArticleContent(self, cItem):
        printDBG("HDFilmeTV.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return retTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="main">', '<div class="row">')[1]
        
        icon  = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''src=['"]([^'^"]+?)['"]''')[0])
        if icon == '': icon = cItem.get('icon', '')
        
        title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<b class="text-blue title-film">', '</b>', False)[1] )
        if title == '': title = cItem['title']
        
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="caption">', '</div>', False)[1] )
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie-info pull-left">', '</div>', False)[1]
        descData = self.cm.ph.getAllItemsBeetwenMarkers(descData, '<p', '</p>', caseSensitive=False)
        descTabMap = {"Genre":                   "genre",
                      "IMDB":                    "rating",
                      "Bewertung":               "rated",
                      "Veröffentlichungsjahr":   "year",
                      "Regisseur":               "director",
                      "Schauspieler":            "actors",
                      "Staat":                   "country",
                      "Zeit":                    "duration",
                      }
        
        otherInfo = {}
        for item in descData:
            item = item.split('</span>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            for dKey in descTabMap:
                if dKey in key:
                    if descTabMap[dKey] == 'rating':
                        val += ' IMDB'
                    otherInfo[descTabMap[dKey]] = val
                    break
                
        views = self.cm.ph.getSearchGroups(data, '''Aufrufe[^>]*?([0-9]+?)[^0-9]''')[0]
        if views != '':
            otherInfo['views'] = views
        
        return [{'title':self.cleanHtmlStr( title ), 'text': desc, 'images':[{'title':'', 'url':self.getIconUrl(icon)}], 'other_info':otherInfo}]

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
        elif category == 'list_filters':
            if filter == 'genre':
                nextFilter = 'country'
                nextCategory = 'list_filters'
            elif filter == 'country':
                nextFilter = 'sort'
                nextCategory = 'list_filters'
            else:
                nextFilter = ''
                nextCategory = 'list_items'
            self.listFilters(self.currItem, nextCategory, nextFilter)
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
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
        CHostBase.__init__(self, HDFilmeTV(), True, favouriteTypes=[]) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('hdfilmetvlogo.png')])
    
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
        cItem = self.host.currList[Index]
        
        if cItem['type'] != 'video' and cItem.get('category', '') != 'explore_item':
            return RetHost(retCode, value=retlist)
        hList = self.host.getArticleContent(cItem)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
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
