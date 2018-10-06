# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, RetHost, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from copy import deepcopy
###################################################


def gettytul():
    return 'http://hdfilme.tv/'

class HDFilmeTV(CBaseHostClass):
    USER_AGENT = 'Mozilla / 5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebkit / 538.1 (KHTML, podobnie jak Gecko) SamsungBrowser / 1.1 TV Safari / 538.1'
    HEADER = {'User-Agent': USER_AGENT, 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://hdfilme.tv/'
    SEARCH_URL    = MAIN_URL + 'movie-search'
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
        
    def getFullUrl(self, url):
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
        
        for filter in [{'m':'name="category"', 'key':'genre'}, {'m':'name="country"', 'key':'country'}, {'m':'name="sort"', 'key':'sort'}]:
            filterData = self.cm.ph.getDataBeetwenMarkers(data, filter['m'], '</select>', False)[1]
            filterData = self.cm.ph.getAllItemsBeetwenMarkers(filterData, '<option', '</option>')
            for item in filterData:
                title = self.cleanHtmlStr(item)
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                if value == '': continue
                self.filtersCache[filter['key']].append({'title':title, filter['key']:value})
            if len(self.filtersCache[filter['key']]) and filter['key'] != 'sort':
                self.filtersCache[filter['key']].insert(0, {'title':_('--All--'), filter['key']:''})
        # add sort_type to sort filter
        orderLen = len(self.filtersCache['sort'])
        for idx in range(orderLen):
            item = deepcopy(self.filtersCache['sort'][idx])
            # desc
            self.filtersCache['sort'][idx].update({'title':'\xe2\x86\x93 ' + self.filtersCache['sort'][idx]['title'], 'sort_type':'desc'})
            # asc
            item.update({'title': '\xe2\x86\x91 ' + item['title'], 'sort_type':'asc'})
            self.filtersCache['sort'].append(item)
            
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
            url += '?key=%s&page=%s' % (cItem['search_pattern'], (page))
        else:
            url += '?category=%s&country=%s&sort=%s&page=%s&sort_type=%s' % (cItem['genre'], cItem['country'], cItem['sort'], page, cItem['sort_type'])
        
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>', False)[1]
        if '>{0}<'.format(page+1) in nextPage:
            nextPage = True
        else: 
            nextPage = False
        
        numOfItems = 0
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
            params.update({'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':self.getFullUrl(url), 'icon':self.getIconUrl(icon), 'desc':desc})
            self.addDir(params)
            numOfItems += 1
        
        if nextPage or numOfItems >= itemsPerPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("HDFilmeTV.exploreItem")
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        trailerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a[^>]*?class="btn btn-xemnow pull-right"[^>]*?href=['"]([^'^"]+?)['"][^>]*?>\s*Trailer\s*<''')[0])
        if trailerUrl.startswith('http'):
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':'%s [%s]' % (cItem['title'], _('Trailer')), 'urls':[{'name':'trailer', 'url':trailerUrl.replace('&amp;', '&'), 'need_resolve':1}]})
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
        
        baseTitleReObj = re.compile('''staffel\s*[0-9]+?$''', flags=re.IGNORECASE)
        baseTitle = cItem['title']
        season = self.cm.ph.getSearchGroups(cItem['url'], '''staf[f]+?el-([0-9]+?)-''')[0]
        if season == '':
            season = self.cm.ph.getSearchGroups(baseTitle, '''staffel\s*([0-9]+?)$''', ignoreCase=True)[0]
            if season != '': baseTitle = baseTitleReObj.sub('', baseTitle, 1).strip()
        
        try: episodesTab.sort(key=lambda item: int(item))
        except Exception:
            printExc()
        for episode in episodesTab:
            title = baseTitle
            if season != '': title += ': ' + 's%se%s'% (season.zfill(2), episode.zfill(2))
            elif len(episodesTab) > 1: title += ': ' + 'e%s'% (episode.zfill(2))
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':title, 'urls':episodesLinks[episode]})
            self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("HDFilmeTV.getLinksForVideo [%s]" % cItem)
        return cItem.get('urls', [])
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDFilmeTV.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        sts, data = self.getPage(videoUrl, self.defaultParams)
        if not sts: return []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'initPlayer(', ')', False)[1].split(',')
        if len(tmp) > 1: 
            movieid = tmp[0].replace('"', '').strip()
            episode = tmp[1].replace('"', '').strip()

            sts, tmp = self.getPage(self.getFullUrl("/movie/getlink/"+movieid+"/"+episode), self.defaultParams)
            if sts:
                try:
                    tmp = base64.b64decode(tmp)
                    printDBG("+++")
                    printDBG(tmp)
                    printDBG("+++")
                    tmp = byteify( json.loads(tmp) )
                    for item in tmp['playinfo']:
                        try:
                            type = item.get('type', item.get('mine_type')).lower()
                        except Exception:
                            type = str(item['file']).split('?', 1)[0].rsplit('.', 1)[-1].lower()
                            
                        url = self.getFullUrl(str(item['file'])) 
                        url = strwithmeta(url, {'Accept':'*/*', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()[:-1], 'User-Agent':self.defaultParams['header']['User-Agent']})
                        printDBG(">> TYPE: " + type)
                        if 'mp4' in type or 'flv' in type:
                            urlTab.append({'name':str(item['label']), 'url':url})
                        elif 'hls' in type or 'm3u8' in type:
                            url.meta['iptv_m3u8_seg_download_retry'] = 10
                            urlTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999))
                except Exception:
                    printExc()
            if len(urlTab):
                return urlTab
            
            googleUrls = self.cm.ph.getSearchGroups(data, '''var hdfilme[^=]*?=[^[]*?(\[[^;]+?);''')[0].strip()
            if '' == googleUrls: googleUrls = self.cm.ph.getSearchGroups(data, '''[\s]['"]?sources['"]?[^=^:]*?[=:][\s]*[^[]*?(\[[^]]+?\])''')[0].strip()
            printDBG("+++")
            printDBG(googleUrls)
            printDBG("+++")
            
            if googleUrls != '':
                try:
                    googleUrls = byteify( json.loads(googleUrls) )
                    for item in googleUrls:
                        if 'mp4' not in item['type']:
                            continue
                        url = self.getFullUrl(str(item['file'])) 
                        url = strwithmeta(url, {'Referer':self.getMainUrl()})
                        urlTab.append({'name':str(item['label']), 'url':url})
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
        
    def getFavouriteData(self, cItem):
        printDBG('HDFilmeTV.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('HDFilmeTV.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('HDFilmeTV.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
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
        CHostBase.__init__(self, HDFilmeTV(), True, favouriteTypes=[])
    
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
