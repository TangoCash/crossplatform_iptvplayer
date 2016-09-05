# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################
# FOREIGN import
###################################################
import re
from Components.config import config, ConfigYesNo, ConfigText, ConfigSelection, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ekinotvPREMIUM = ConfigYesNo(default = False)
config.plugins.iptvplayer.ekinotv_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.ekinotv_password = ConfigText(default = "", fixed_size = False)

config.plugins.iptvplayer.ekinotv_sortby = ConfigSelection(default = "data-dodania", choices = [("alfabetycznie", "nazwy"), ("ocena", "oceny"),("odslony", "ilości odsłon"),("data-dodania", "daty dodania"),("data-premiery", "daty premiery"), ('data-aktualizacji', 'daty aktualizacji')])            
config.plugins.iptvplayer.ekinotv_sortorder = ConfigSelection(default = "desc", choices = [("desc", "malejąco"),("asc", "rosnąco")]) 

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry("Użytkownik PREMIUM Ekino TV?", config.plugins.iptvplayer.ekinotvPREMIUM))
    #if config.plugins.iptvplayer.ekinotvPREMIUM.value:
    #    optionList.append(getConfigListEntry("    Ekino TV login:", config.plugins.iptvplayer.ekinotv_login))
    #    optionList.append(getConfigListEntry("    Ekino TV hasło:", config.plugins.iptvplayer.ekinotv_password))
    optionList.append(getConfigListEntry("Sortuj według:", config.plugins.iptvplayer.ekinotv_sortby))
    optionList.append(getConfigListEntry("Kolejność wyświetlania:", config.plugins.iptvplayer.ekinotv_sortorder))
    return optionList
###################################################

def gettytul():
    return 'ekino.tv'

class EkinoTv(CBaseHostClass):
    MAIN_URL = 'http://ekino-tv.pl/'
    DEFAUL_ICON = 'http://ekino-tv.pl/views/img/logo.png'
    #LOGIN_URL     = MAIN_URL + 'logowanie.html'
    SEARCH_URL    = MAIN_URL + 'search/'
    FILMS_CAT_URL = MAIN_URL + 'movie/cat/'  
    SERIES_URL    = MAIN_URL + 'serie/'
    MAIN_CAT_TAB = [{'category':'list_cats',             'title': 'Filmy',           'url':FILMS_CAT_URL, 'icon':DEFAUL_ICON},
                    {'category':'series_abc',            'title': 'Seriale',         'url':SERIES_URL, 'icon':DEFAUL_ICON},
                    {'category':'list_movies',           'title': 'Dla dzieci',      'url':FILMS_CAT_URL, 'cat':'2,3,5,6', 'icon':DEFAUL_ICON},
                    {'category':'search',                'title': _('Search'), 'search_item':True, 'icon':DEFAUL_ICON},
                    {'category':'search_history',        'title': _('Search history'), 'icon':DEFAUL_ICON} ]
    
    SORT_MAP  = {'data-dodania':'add',
                 'data-aktualizacji':'update',
                 'data-premiery':'premiera',
                 'data-premiery':'premiera',
                 'odslony':'views',
                 'ocena':'rate',
                 'alfabetycznie':'alfa',}
    
    def __init__(self):
        printDBG("EkinoTv.__init__")
        CBaseHostClass.__init__(self, {'history':'EkinoTv.tv', 'cookie':'ekinotv.cookie'})
        self.cacheMovieFilters = {'cats':[], 'vers':[], 'years':[]}
        self.loggedIn = False
            
    def _checkNexPage(self, data, page):
        if -1 != data.find('strona[%s]' % page):
            return True
        else: return False
            
    def _getFullUrl(self, url):
        if url.startswith('//'):
            return 'http:' + url
        if url.startswith('/'):
            url = url[1:]
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
    
    ###################################################
    def _fillMovieFilters(self):
        self.cacheMovieFilters = { 'cats':[], 'vers':[], 'years':[]}
        sts, data = self.cm.getPage(EkinoTv.FILMS_CAT_URL)
        if not sts: return
        
        # fill cats
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="movieCategories">', '</ul>', False)[1]
        dat = re.compile('<a[^"]+?href="[^"]+?kategoria\[([0-9]+?)\][^>]*?>([^<]+?)<').findall(dat)
        for item in dat:
            self.cacheMovieFilters['cats'].append({'title': self.cleanHtmlStr(item[1]), 'cat': item[0]})
            
        # fill vers
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="quality"', '</ul>', False)[1]
        dat = re.compile('<li[^>]+?data-id="([^"]+?)"[^>]*?>(.+?)</li>').findall(dat)
        for item in dat:
            self.cacheMovieFilters['vers'].append({'title': self.cleanHtmlStr(item[1]), 'ver': item[0]})
            
        # fill years
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="filtyear">', '</ul>', False)[1]
        dat = re.compile('<li[^>]+?data-id="([^"]+?)"[^>]*?>(.+?)</li>').findall(dat)
        for item in dat:
            self.cacheMovieFilters['years'].append({'title': self.cleanHtmlStr(item[1]), 'year': item[0]})
    
    ###################################################
    def listMovieFilters(self, cItem, category):
        printDBG("EkinoTv.listMovieFilters")
        
        filter = cItem['category'].split('_')[-1]
        if 0 == len(self.cacheMovieFilters[filter]):
            self._fillMovieFilters()
        if len(self.cacheMovieFilters[filter]) > 0:
            filterTab = [{'title':'--Wszystkie--'}]
            filterTab.extend(self.cacheMovieFilters[filter])
            self.listsTab(filterTab, cItem, category)
        
    def listsTab(self, tab, cItem, category=None):
        printDBG("EkinoTv.listsTab")
        for item in tab:
            params = dict(cItem)
            if None != category:
                params['category'] = category
            params.update(item)
            self.addDir(params)
            
    def _addItems(self, cItem, dataTab, category='video'):
        for item in dataTab:
            item = item.split('</span>')
            title = self.cleanHtmlStr('<' + item[0])
            ids = self.cm.ph.getSearchGroups(item[0], 'id="([^"]+?)"')[0].split('-')
            if len(ids) > 2 and '' != ids[-1]:
                title += ' [%s]' % (ids[-1])
            url    = self.cm.ph.getSearchGroups(item[0], 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item[0], 'src="([^"]+?jpg)"')[0]
            if url == '': continue
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon': self._getFullUrl(icon), 'desc': self.cleanHtmlStr(item[-1])})
            if category == 'video':
                self.addVideo(params)
            else:
                params['category'] = category
                self.addDir(params)
        
    def listMovies(self, cItem):
        printDBG("EkinoTv.listMovies")
        
        # prepare url
        sortby    = config.plugins.iptvplayer.ekinotv_sortby.value          
        sortorder = config.plugins.iptvplayer.ekinotv_sortorder.value
        page = cItem.get('page', 1)
        url  = cItem['url'] + 'strona[%s]+sort[%s]+method[%s]+' % (page, self.SORT_MAP[sortby], sortorder)
        
        for item in [('cat', 'kategoria'), ('ver', 'wersja'), ('year', 'rok')]:
            if item[0] in cItem:
                url += '%s[%s]+' % (item[1], cItem[item[0]])
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        # parse data
        nextPage = self._checkNexPage(data, page+1)
        sp = '<div class="movies-list-item"'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="pager">', False)[1]
        data = data.split(sp)
        self._addItems(cItem, data)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
                
    def listsSeriesABC(self, cItem, category):
        printDBG('EkinoTv.listsSeriesABC start')
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="serialsmenu">', '</ul>', False)[1]
            data = re.compile('<a[^"]+?href="([^"]+?)"[^>]*?><span class="name">([^<]+?)</span><span class="count">([^<]+?)<').findall(data)
            for item in data:
                params = dict(cItem)
                params.update({'category':category, 'title':'%s (%s)' % (item[1], item[2]), 'url':self._getFullUrl(item[0])})
                self.addDir(params)
                
    def listsSeries(self, cItem, category):
        printDBG('EkinoTv.listsSeries start')
        page = cItem.get('page', 1)
        url  = cItem['url'] + ',strona=%s' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if (',strona=%s"' % (page+1)) in data:
            nextPage = True
        
        sp = '<div class="movies-list-item"'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="pager">', False)[1]
        data = data.split(sp)
        self._addItems(cItem, data, category)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG('EkinoTv.listEpisodes start')
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="list-series"', '<br style="clear:both">', False)[1]
        data = data.split('</ul>')
        if len(data): del data[-1]
        for season in data:
            sTitle = self.cm.ph.getDataBeetwenMarkers(season, '<p>', '</p>', False)[1]
            eData = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(season)
            for eItem in eData:
                s = self.cm.ph.getSearchGroups(eItem[0], 'season\[([0-9]+?)\]')[0]
                e = self.cm.ph.getSearchGroups(eItem[0], 'episode\[([0-9]+?)\]')[0]
                title = '%s s%se%s %s' % (cItem['title'], s.zfill(2), e.zfill(2), eItem[1])
                params = dict(cItem)
                params.update({'title':title, 'url':self._getFullUrl(eItem[0])})
                self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EkinoTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = searchPattern.replace(' ', '+')
        
        sts, data = self.cm.getPage(self.SEARCH_URL, {}, {'search_field':searchPattern})
        if not sts: return
        
        if 'movies' == searchType:
            sp = '<div class="movies-list-item"'
            data = self.cm.ph.getDataBeetwenMarkers(data, sp, 'Znalezione seriale', False)[1]
            data = data.split(sp)
            self._addItems(cItem, data)
        else:
            sp = '<div class="movies-list-item"'
            data = self.cm.ph.getDataBeetwenMarkers(data, 'Znalezione seriale', '<br style="clear:both">', False)[1]
            data = data.split(sp)
            if len(data): del data[0]
            self._addItems(cItem, data, 'series_episodes')

    def getLinksForVideo(self, cItem):
        printDBG("EkinoTv.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        if 'dmcabitch.jpg' in data:
            message = self.cm.ph.getDataBeetwenMarkers(data, '<div class="playerContainer"', '<br style="clear:both">', True)[1]
            SetIPTVPlayerLastHostError(self.cleanHtmlStr(message))
            return []
        
        playersData = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="players"', '</ul>', False)[1]
        
        playersData = playersData.split('</li>')
        if len(playersData): del playersData[-1]
        players = []
        for pItem in playersData:
            pItem = self.cm.ph.getDataBeetwenMarkers(pItem, '<li>', '</a>', False)[1]
            title = self.cleanHtmlStr(pItem)
            id = self.cm.ph.getSearchGroups(pItem, 'href="#([^"]+?)"')[0]
            title += ' ' + self.cm.ph.getSearchGroups(pItem, 'title="([^"]+?)"')[0]
            players.append({'title':title, 'id':id})
            
        #printDBG(players)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab-content">', '<script>', False)[1]
        data = data.split('</div>')
        if len(data): del data[-1]
        #printDBG(data)
        for item in data:
            id  = self.cm.ph.getSearchGroups(item, 'id="([^"]+?)"')[0]
            url = self.cm.ph.getSearchGroups(item, '''ShowPlayer[^"^']*?['"]([^"^']+?)['"]''')[0]
            if url == '': url = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url = self._getFullUrl(url)
            if url == '' or url.split('.')[-1] in ['jpg', 'jepg', 'gif']:
                continue
            for p in players:
                if p['id'] == id:
                    urlTab.append({'name':p['title'], 'url':url, 'need_resolve':1})
                    break
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("EkinoTv.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        url = ''
        if 'ekino-tv.pl' in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return urlTab
            url = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        else:
            url = baseUrl
        
        if url.startswith('//'):
            url = 'http:' + url
        
        if url.startswith('http'): 
            urlTab = self.up.getVideoLinkExt(url)
        return urlTab
        
    def getArticleContent(self, cItem):
        return []
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def tryTologin(self):
        printDBG('EkinoTv.tryTologin start')
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False 
        post_data = {'form_login_username':self.LOGIN, 'form_login_password':self.PASSWORD, "form_login_rememberme": "1"}
        params = {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage(EkinoTv.LOGIN_URL, params, post_data)         
        if sts and 'Wyloguj' in data:
            return True
        return False
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('EkinoTv.handleService start') 
        #self.PREMIUM         = config.plugins.iptvplayer.ekinotvPREMIUM.value
        #if False == self.loggedIn and self.PREMIUM:
        #    self.LOGIN           = config.plugins.iptvplayer.ekinotv_login.value
        #    self.PASSWORD        = config.plugins.iptvplayer.ekinotv_password.value
        #    self.loggedIn = self.tryTologin()
        #    if not self.loggedIn:
        #        self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
        #    else:
        #        self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
                
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "EkinoTv.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(EkinoTv.MAIN_CAT_TAB, {'name':'category'})
    #FILMS CATEGORIES
        elif 'list_cats' == category:
            self.listMovieFilters(self.currItem, 'list_vers')
        elif 'list_vers' == category:
            self.listMovieFilters(self.currItem, 'list_years')
        elif 'list_years' == category:
            self.listMovieFilters(self.currItem, 'list_movies')
        elif 'list_movies' == category:
            self.listMovies(self.currItem)
    #FILMS LETTERS
        elif 'series_abc' == category:
            self.listsSeriesABC(self.currItem, 'series_list')
    #LIST SERIALS
        elif 'series_list' == category:
            self.listsSeries(self.currItem, 'series_episodes')
        elif 'series_episodes' == category:
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
        CHostBase.__init__(self, EkinoTv(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('ekinotvlogo.png')])
    
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
        if not self.isValidIndex(Index): 
            return RetHost(retCode, value=retlist)

        cItem = self.host.currList[Index]
        if cItem.get('type') == 'video':
            hList = self.host.getArticleContent(cItem)
            for item in hList:
                title      = item.get('title', '')
                text       = item.get('text', '')
                images     = item.get("images", [])
                othersInfo = item.get('other_info', '')
                retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
                retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
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