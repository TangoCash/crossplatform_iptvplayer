# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
try:    import json
except Exception: import simplejson as json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from Components.Language import language
###################################################


###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.movie4kto_language = ConfigSelection(default = "", choices = [("", _("Auto")), ("en", _("English")), ("de", _("German")), ("fr", _("French")), ("es", _("Spanish")), ("it", _("Italian")), ("jp", _("Japanese")), ("tr", _("Turkish")), ("ru", _("Russian")) ])
config.plugins.iptvplayer.movie4kto_use_proxy_gateway  = ConfigYesNo(default = True)
#config.plugins.iptvplayer.movie4kto_proxy_gateway_url  = ConfigText(default = "http://www.proxy-german.de/index.php?q={0}&hl=2e5", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( _("Language:"), config.plugins.iptvplayer.movie4kto_language) )
    optionList.append(getConfigListEntry(_("Use proxy gateway"), config.plugins.iptvplayer.movie4kto_use_proxy_gateway))
    #if config.plugins.iptvplayer.movie4kto_use_proxy_gateway.value:
    #    optionList.append(getConfigListEntry("    " + _("Url:"), config.plugins.iptvplayer.movie4kto_proxy_gateway_url))
    return optionList
###################################################

def gettytul():
    return 'movie4k.to'

class Movie4kTO(CBaseHostClass):
    MAIN_URL    = 'http://movie4k.to/'
    SRCH_URL    = MAIN_URL + 'searchAutoCompleteNew.php?search='
    MOVIE_GENRES_URL  = MAIN_URL + 'movies-genre-%s-{0}.html'
    TV_SHOWS_GENRES_URL  = MAIN_URL + 'tvshows-genre-%s-{0}.html'
    
    MOVIES_ABC_URL = MAIN_URL + 'movies-all-%s-{0}.html'
    TV_SHOWS_ABC_URL = MAIN_URL + 'tvshows-all-%s.html'
    MAIN_CAT_TAB = [{'category':'cat_movies',            'title': _('Movies'),     'icon':''},
                    {'category':'cat_tv_shows',          'title': _('TV shows'),   'icon':''},
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
                    
    MOVIES_CAT_TAB = [{'category':'cat_movies_list1',    'title': _('Cinema movies'),  'icon':'', 'url':MAIN_URL+'index.php'},
                      {'category':'cat_movies_list2',    'title': _('Latest updates'), 'icon':'', 'url':MAIN_URL+'movies-updates.html' },
                      {'category':'cat_movies_abc',      'title': _('All movies'),     'icon':'', 'url':MAIN_URL+'movies-all.html' },
                      {'category':'cat_movies_genres',   'title': _('Genres'),         'icon':'', 'url':MAIN_URL+'genres-movies.html' } ]
                      
    TV_SHOWS_CAT_TAB = [{'category':'cat_tv_shows_list1',  'title': _('Featured'),       'icon':'', 'url':MAIN_URL+'featuredtvshows.html'},
                        {'category':'cat_tv_shows_list2',  'title': _('Latest updates'), 'icon':'', 'url':MAIN_URL+'tvshows-updates.html'},
                        {'category':'cat_tv_shows_abc',    'title': _('All TV shows'),   'icon':'', 'url':MAIN_URL+'tvshows-all.html' },
                        {'category':'cat_tv_shows_genres', 'title': _('Genres'),         'icon':'', 'url':MAIN_URL+'genres-tvshows.html' } ]

    def __init__(self):
        printDBG("Movie4kTO.__init__")
        CBaseHostClass.__init__(self, {'history':'Movie4kTO', 'cookie':'Movie4kTO.cookie'})
        
    def getPage(self, url, params={}, post_data=None):
        lang = config.plugins.iptvplayer.movie4kto_language.value
        if '' == lang:
            try:
                lang = language.getActiveLanguage().split('_')[0]
            except Exception: lang = 'en'
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0', 'Cookie':'lang=%s;' % lang }
        params.update({'header':HTTP_HEADER})
        
        if config.plugins.iptvplayer.movie4kto_use_proxy_gateway.value and 'movie4k.to' in url:
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote(url, ''))
            params['header']['Referer'] = proxy
            params['header']['Cookie'] = 'flags=2e5; COOKIE%253Blang%253B%252F%253Bwww.movie4k.to={0}%3B'.format(lang)
            url = proxy
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and None == data:
            sts = False
        return sts, data
        
    def _getFullUrl(self, url):
        if 'proxy-german.de' in url:
            #printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + url)
            url = urllib.unquote(url.split('?q=')[1])
            
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem):
        printDBG("Movie4kTO.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
            
    def listEpisodes(self, cItem):
        printDBG("Movie4kTO.listEpisodes")
        url  = self._getFullUrl(cItem['url'])
        sts, data = self.getPage(url)
        if not sts: return
        testMark = '<FORM name="seasonform">'
        m1 = ''
        m2 = ''
        found = False
        for test in [{'m1':']="', 'm2':'";'}, {'m1':'id="tablemoviesindex"', 'm2':'</TABLE>'}, {}, None]:
            if testMark not in data:
                if None == test: continue
                m1 = test.get('m1', m1) 
                m2 = test.get('m2', m2) 
                sts, tmpData = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)
                tmpData = tmpData.replace('\\"', '"')
                url = self.cm.ph.getSearchGroups(tmpData, 'href="([^"]+?)"')[0]
                if '' == url: continue
                sts, data = self.getPage( self._getFullUrl(url) )
                if not sts: data = ''
            else:
                found = True
                break
        
        if not found: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, testMark, '</table>', False)
        if not sts: return 

        data = data.split('</FORM>')
        if len(data): del data [-1]
        if 0 == len(data): return
        seasons = re.compile('<OPTION[^>]+?>([^<]+?)</OPTION>').findall(data[0])
        episodesReObj = re.compile('<OPTION[^>]+?value="([^"]+?)"[^>]*?>([^<]+?)</OPTION>')
        del data[0]
        if len(seasons) != len(data): printDBG("Movie4kTO.listEpisodes >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> WRONG THIG HAPPENS seasons[%d] data[%d]", len(seasons), len(data))
        for idx in range(len(data)):
            if idx < len(seasons):
                season = seasons[idx]
            else: season = ''
            episodes = episodesReObj.findall( data[idx] )
            for episod in episodes:
                url   = episod[0]
                title = episod[1]
                if '' != url and '' != title:
                    params = dict(cItem)
                    params.update( {'title':'%s, %s, %s' % (cItem['title'], season, title), 'url':self._getFullUrl(url)} )
                    self.addVideo(params)
                    
    def listsTVShow1(self, cItem, category):
        printDBG("Movie4kTO.listsTVShow1")
        return self.listsItems1(cItem, category, m1='<div id="maincontenttvshow">', sp='</table>')
        
    def listsMovies1(self, cItem):
        printDBG("Movie4kTO.listsMovies1")
        return self.listsItems1(cItem, None)
            
    def listsItems1(self, cItem, category, m1='<div id="maincontent2">', m2='</body>', sp='<div id="maincontent2">'):
        printDBG("Movie4kTO.listsMovies1")
        page = cItem.get('page', 1)
        url  = self._getFullUrl(cItem['url'])
        if page > 1:
            if '?' in url: url += '?'
            else: url += '&'
            url += 'page=%s' % page
        
        sts, data = self.getPage(url)
        if not sts: return
        
        sts, nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'class="pagination"', '</div>', False)
        if sts:
            if ('>{0}<'.format(page + 1)) in nextPage:
                nextPage = True
        if nextPage != True:
            nextPage = False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)
        if not sts: 
            self.listsMovies2(cItem)
            return
        data = data.split(sp)
        
        for item in data:
            if None == category:
                sts, item = self.cm.ph.getDataBeetwenMarkers(item, '<div id="xline">', '<div id="xline">', False)
                if not sts: continue
            
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            lang = self.cm.ph.getSearchGroups(item, 'src="/img/([^"]+?)_small.png"')[0].replace('us', '').replace('_', '').replace('flag', '')
            #if '' == lang: lang = 'eng'
            if '' != lang: title += ' ({0})'.format(lang)
            
            desc  = self.cm.ph.getDataBeetwenMarkers(item, 'class="info">', '</div>', False)[1]

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'category':category, 'title':self.cleanHtmlStr(title.replace('kostenlos', '')), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
                if None == category: 
                    self.addVideo(params)
                else:
                    self.addDir(params)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
                    
                    
    def listsTVShow2(self, cItem, category):
        printDBG("Movie4kTO.listsTVShow2")
        return self.listsItems2(cItem, category)#, m1='<div id="maincontenttvshow">', sp='</table>')
        
    def listsMovies2(self, cItem):
        printDBG("Movie4kTO.listsMovies2")
        return self.listsItems2(cItem, None)
        
    def listsItems2(self, cItem, category):
        # m1='<div id="maincontent2">', m2='</body>', sp='<div id="maincontent2">'):
        printDBG("Movie4kTO.listsItems2")
        page = cItem.get('page', 1)
        baseUrl  = self._getFullUrl(cItem['url'])
        if '{0}' in baseUrl: url = baseUrl.format(page)
        else: url = baseUrl
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = False
        if '{0}' in baseUrl:
            tmp = baseUrl.format(page+1).split('/')[-1]
            if tmp in data: nextPage = True
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'id="tdmovies"', '</TABLE>', False)
        if not sts: return
        
        descRe = re.compile('<TD[^>]+?>(.+?)</TD>', re.DOTALL)
        data = data.split('id="tdmovies"')
        for item in data:
            
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, '<a [^>]+?>([^<]+?)</a>')[0]
            desc = ''
            try: 
                tmp = descRe.findall(item)
                for t in tmp: 
                    if 'watch on' not in t: desc += ' ' + t 
                desc = desc.replace('&nbsp;', ' ')
            except Exception: printExc()
            
            lang = self.cm.ph.getSearchGroups(item, 'src="/img/([^"]+?)_small.png"')[0].replace('us', '').replace('_', '').replace('flag', '')
            #if '' == lang: lang = 'eng'
            if '' != lang: title += ' ({0})'.format(lang)

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'category':category, 'title':title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':''} )
                if None == category:
                    self.addVideo(params)
                else: self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_("Next page"), 'page':page+1} )
            self.addDir(params)
            
    def listsTVShowABC(self, cItem, category):
        printDBG("Movie4kTO.listsTVShowABC")
        self.listsABC(cItem, category, self.TV_SHOWS_ABC_URL)
        
    def listsMoviesABC(self, cItem, category):
        printDBG("Movie4kTO.listsMoviesABC")
        self.listsABC(cItem, category, self.MOVIES_ABC_URL)
        
    def listsABC(self, cItem, category, ABC_URL):
        printDBG("Movie4kTO.listsABC")
        TAB = ['#1','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','W','X','Y','Z']
        for item in TAB:
            url = ABC_URL % item[-1]
            params = dict(cItem)
            params.update( {'title':item[0], 'url':self._getFullUrl(url), 'category': category} )
            self.addDir(params)
            
    def listsTVShowGenres(self, cItem, category):
        printDBG("Movie4kTO.listsTVShowGenres")
        self.listGenres(cItem, category, 'tvshows-genre-', self.TV_SHOWS_GENRES_URL)
        
    def listsMoviesGenres(self, cItem, category):
        printDBG("Movie4kTO.listsMoviesGenres")
        self.listGenres(cItem, category, 'movies-genre-', self.MOVIE_GENRES_URL)
        
    def listGenres(self, cItem, category, genreMarker, GENRES_URL):
        printDBG("Movie4kTO.listGenres")
        url  = self._getFullUrl(cItem['url'])
        
        sts, data = self.getPage(url)
        if not sts: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<TABLE id="tablemovies" cellpadding=5 cellspacing=5>', '</TABLE>', False)
        if not sts: return
        
        data = data.split('</TR>')
        if len(data): del data[-1]
        for item in data:
            
            genreID = self.cm.ph.getSearchGroups(item, genreMarker+'([0-9]+?)-')[0]
            title   = self.cleanHtmlStr( item ).replace('Random', '')

            if '' != genreID and '' != title:
                url = GENRES_URL % genreID
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'category': category} )
                self.addDir(params)
        
    def listCategories(self, cItem, category):
        printDBG("Movie4kTO.listCategories")
        sts, data = self.getPage(Movie4kTO.MAIN_URL)
        if not sts: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'aria-labelledby="menu_select">', '</ul>', False)
        if not sts: return
        data = data.split('</li>')
        if len(data): del data[-1]
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            url    = url[0:url.rfind('/')]
            title  = self.cleanHtmlStr( item )
            
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'category':category} )
                self.addDir(params)
        
    def listVideosFromCategory(self, cItem):
        printDBG("Movie4kTO.listVideosFromCategory")
        page = cItem.get('page', 1)
        url  = cItem['url'] + "/{0},{1}.html".format(page, config.plugins.iptvplayer.Movie4kTO_sort.value)
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if '"Następna"' in data: nextPage = True
        else: nextPage = False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-md-2" style="margin-bottom: 35px;">', '<script>', False)
        if not sts: return
        
        data = data.split('<div class="col-md-2" style="margin-bottom: 35px;">')
        if len(data): del data[0]
        
        for item in data:
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   =  ''
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':self.cleanHtmlStr(title.replace('kostenlos', '')), 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
                
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Następna strona'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Movie4kTO.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = Movie4kTO.SRCH_URL + urllib.quote(searchPattern)
        
        sts, data = self.getPage(url)
        if not sts: return
        
        data = data.split('</TD>')
        if len(data): del data[-1]
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if '' != url:
                params = dict(cItem)
                params.update( {'name':'category', 'category':'cat_movies_list2', 'title':self.cleanHtmlStr( item ), 'url':self._getFullUrl(url)} )
                self.addDir(params)
        
    def getArticleContent(self, cItem):
        printDBG("Movie4kTO.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'url' not in cItem: return retTab
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getSearchGroups(data, 'title" content="([^"]+?)"')[0]
        icon = self.cm.ph.getSearchGroups(data, 'image" content="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="moviedescription">', '</div>', False)[1] )

        return [{'title':title, 'text':desc, 'images':[]}]
    
    def getLinksForVideo(self, cItem):
        printDBG("Movie4kTO.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, pageData = self.getPage(cItem['url'])
        if not sts: return urlTab
        
        for idx in range(0, 2):
            if 0 != idx:
                sts, data = self.cm.ph.getDataBeetwenMarkers(pageData, 'links = new Array();', '</table>', False)
                data = data.replace('\\"', "'")
                data = re.compile(']="([^"]+?)";').findall(data) #, re.DOTALL
            else:
                #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                sts, data = self.cm.ph.getDataBeetwenMarkers(pageData, '<tr id="tablemoviesindex2"', '</table>', False)
                data = data.split('<tr id="tablemoviesindex2"')
                for idx in range(len(data)):
                    for marker in ['"<SCRIPT"', 'links = new Array();']:
                        tmpIdx = data[idx].find( marker )
                        if tmpIdx > 0:
                            data[idx] = data[idx][:tmpIdx]
                    data[idx] = data[idx].strip()
                    if not data[idx].startswith('<'):
                        data[idx] = '<' + data[idx]
                #printDBG(data)

            for item in data:
                url = self.cm.ph.getSearchGroups(item, '''href=["']([^"']+?)['"]''')[0]
                title = self.cleanHtmlStr( item )
                title += ' ' + self.cm.ph.getSearchGroups(item, '/img/smileys/([0-9]+?)\.gif')[0]
                
                if '' != url and '' != title:
                    urlTab.append({'name':title, 'need_resolve':1, 'url':self._getFullUrl(url)})
        
        if 0 == len(urlTab):
            urlTab.append({'name':'main url', 'need_resolve':1, 'url':cItem['url']})
            
        for idx in range(len(urlTab)):
            urlTab[idx]['name'] = urlTab[idx]['name'].split('Quality:')[0]
            
        doSort=True
        for item in urlTab:
            if '' == self.cm.ph.getSearchGroups(item['name'], '''([0-9]{2}/[0-9]{2}/[0-9]{4})''')[0]:
                doSort = False
                break
        if doSort:
            urlTab.sort(key=lambda item:item['name'], reverse=True)
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("Movie4kTO.getVideoLinks [%s]" % url)
        urlTab = []
        
        sts, data = self.getPage(url)
        if not sts: return urlTab
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<a target="_blank" href="([^"]+?)"')[0]
        if '' == videoUrl:
            videoUrl = self.cm.ph.getDataBeetwenMarkers(data, '-Download-', 'id="underplayer"', False)[1]
            videoUrl = self.cm.ph.getSearchGroups(videoUrl, '<iframe[^>]+?src="(http[^"]+?)"[^>]*?>')[0]
            
        videoUrl = self._getFullUrl(videoUrl)
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Movie4kTO.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Movie4kTO.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            self.listsTab(Movie4kTO.MAIN_CAT_TAB, {'name':'category'})
    #TV SHOW
        elif 'cat_tv_shows' == category:
            self.listsTab(Movie4kTO.TV_SHOWS_CAT_TAB, self.currItem)
        elif 'cat_tv_shows_list1' == category:
            self.listsTVShow1(self.currItem, 'episodes')
        elif 'cat_tv_shows_list2' == category:
            self.listsTVShow2(self.currItem, 'episodes')
        elif 'cat_tv_shows_genres' == category:
            self.listsTVShowGenres(self.currItem, 'cat_tv_shows_list2')
        elif 'cat_tv_shows_abc' == category:
            self.listsTVShowABC(self.currItem, 'cat_tv_shows_list2')
        elif 'episodes' == category:
            self.listEpisodes(self.currItem)
    #MOVIES
        elif 'cat_movies' == category:
            self.listsTab(Movie4kTO.MOVIES_CAT_TAB, self.currItem)
        elif 'cat_movies_list1' == category:
            self.listsMovies1(self.currItem)
        elif 'cat_movies_list2' == category:
            self.listsMovies2(self.currItem)
        elif 'cat_movies_genres' == category:
            self.listsMoviesGenres(self.currItem, 'cat_movies_list2')
        elif 'cat_movies_abc' == category:
            self.listsMoviesABC(self.currItem, 'cat_movies_list2')
    #CATEGORIES
        elif 'categories' == category:
            self.listCategories(self.currItem, 'list_videos')
    #LIST_VIDEOS
        elif 'list_videos' == category:
            self.listVideosFromCategory(self.currItem)
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Movie4kTO(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('movie4ktologo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

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
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "filmy"))
        #searchTypesOptions.append(("Seriale", "seriale"))
    
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
