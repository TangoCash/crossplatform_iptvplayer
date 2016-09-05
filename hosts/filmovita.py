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
#config.plugins.iptvplayer.alltubetv_premium  = ConfigYesNo(default = False)
#config.plugins.iptvplayer.alltubetv_login    = ConfigText(default = "", fixed_size = False)
#config.plugins.iptvplayer.alltubetv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #if config.plugins.iptvplayer.alltubetv_premium.value:
    #    optionList.append(getConfigListEntry("  alltubetv login:", config.plugins.iptvplayer.alltubetv_login))
    #    optionList.append(getConfigListEntry("  alltubetv hasło:", config.plugins.iptvplayer.alltubetv_password))
    return optionList
###################################################


def gettytul():
    return 'http://filmovita.com/'

class Filmovita(CBaseHostClass):
    MAIN_URL    = 'http://filmovita.com/'
    SRCH_URL    = MAIN_URL + 'szukaj'
    DEFAULT_ICON_URL = 'http://skini.filmovita.com/grafika/logo.png'
    
    MAIN_URL    = 'http://filmovita.com/'
    S_MAIN_URL  = 'http://serijex.com/'
    
    MAIN_CAT_TAB = [{'category':'list_movies',        'title': _('Main'),          'url':MAIN_URL,   'icon':DEFAULT_ICON_URL},
                    {'category':'genres_movies',      'title': _('Categories'),    'url':MAIN_URL,   'icon':DEFAULT_ICON_URL},
                    {'category':'list_series',        'title': _('TV series'),     'url':S_MAIN_URL, 'icon':DEFAULT_ICON_URL},
                    #{'category':'search',             'title': _('Search'), 'search_item':True},
                    #{'category':'search_history',     'title': _('Search history')} 
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Filmovita', 'cookie':'filmovita.cookie'})
        self.seriesCache = {}
        
    def _getFullUrl(self, url, series=False):
        if 'proxy-german.de' in url:
            url = urllib.unquote(url.split('?q=')[1])
        if url.startswith('//'):
            return 'http:' + url
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        params.update({'header':HTTP_HEADER})        
        printDBG(url)
        proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote_plus(url))
        params['header']['Referer'] = proxy
        url = proxy
        return self.cm.getPage(url, params, post_data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Filmovita.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listGenres(self, cItem, category):
        printDBG("Filmovita.listGenres")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="sub-menu">', '</ul>', False)[1]
        data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(data)
        tab = []
        for item in data:
            tab.append({'title':item[1], 'url':item[0]})
        defItem = dict(cItem)
        defItem['category'] = category
        self.listsTab(tab, defItem)
        
    def listMovies(self, cItem):
        printDBG("Filmovita.listMovies")
        
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%d/' % page
            
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<article id=', '<div class="section clearfix">', True)[1]
        data = data.split('</article>')
        if len(data): del data[-1]
        
        for item in data:
            tmp = item.split('</h1>')
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = tmp[0]
            desc   = tmp[1]
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listSeries(self, cItem, category):
        printDBG("Filmotopia.listSeries")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        self.seriesCache = {}
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="content">', '<div class="content">', False)[1]
        data = data.split('<center>')
        if len(data): del data[0]
        for item in data:
            idx  = item.find('</strong></p>')
            if idx < 0: continue
            icon = self.cm.ph.getSearchGroups(item[:idx], 'src="([^"]+?)"')[0]
            serieTitle = self.cleanHtmlStr( item[:idx].split('<strong>')[-1] )
            if '' == serieTitle: continue
            # get seasons items
            tmp = item[idx:].split('<p><strong>')
            seasons = {}
            seasonTab = []
            for season in tmp:
                seasonTitle = self.cleanHtmlStr( season.split('</strong><br/>')[0] )
                if '' == seasonTitle: continue
                eData = re.compile('<a[^>]*?href="(http[^"]+?)"[^>]*?>([^<]+?)</a>').findall(season)
                episodesTab = []
                for episode in eData:
                    if '-epizoda-' not in episode[0]: continue
                    episodesTab.append({'title':seasonTitle + ' - ' + episode[1], 'url':episode[0], 'season_id':seasonTitle})
                if len(episodesTab):
                    seasons[seasonTitle] = episodesTab
                    seasonTab.append({'title':seasonTitle, 'season_id':seasonTitle, 'serie_id':serieTitle})
            if len(seasonTab):
                self.seriesCache[serieTitle] = {'season_tab':seasonTab, 'seasons':seasons}
                params = dict(cItem)
                params.update( {'category':category, 'title': self.cleanHtmlStr( serieTitle ), 'serie_id':serieTitle, 'icon':icon} )
                self.addDir(params)
        
    def listSeasons(self, cItem, category):
        printDBG("Filmotopia.listSeasons")
        serie = cItem.get('serie_id', '')
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.seriesCache.get(serie, {}).get('season_tab', []), cItem, 'dir')
        
    def listEpisodes(self, cItem):
        printDBG("Filmotopia.listEpisodes")
        serie = cItem.get('serie_id', '')
        season = cItem.get('season_id', '')
        cItem = dict(cItem)
        self.listsTab(self.seriesCache.get(serie, {}).get('seasons', {}).get(season, []), cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        pass
        
    def getLinksForVideo(self, cItem):
        printDBG("Filmovita.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, mainData = self.getPage(cItem['url'])
        if not sts: return urlTab
        
        m1 = '<div class="entry-content">'
        m2 = '<div class="content">'
        if m1 not in mainData: 
            m1 = 'class="entry-content'
            m2 = '<footer '
            
        tmp = self.cm.ph.getDataBeetwenMarkers(mainData, m1, m2, False)[1]
        
        linksUrlTab = []
        tab = re.compile(' src="([^"]+?)"', re.IGNORECASE).findall(tmp)
        for item in tab: linksUrlTab.append([item,''])
        tab = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<', re.IGNORECASE).findall(tmp)
        if len(tab): linksUrlTab.extend(tab)
        for item in linksUrlTab:
            linksUrl = self._getFullUrl( item[0] )
            if 1 == self.up.checkHostSupport(linksUrl): 
                if 'videomega.tv/validatehash.php?' in linksUrl:
                    sts, data = self.cm.getPage(linksUrl, {'header':{'Referer':cItem['url'], 'User-Agent':'Mozilla/5.0'}})
                    if sts:
                        data = self.cm.ph.getSearchGroups(data, 'ref="([^"]+?)"')[0]
                        linksUrl = 'http://videomega.tv/view.php?ref={0}&width=700&height=460&val=1'.format(data)
                    else:
                        linksUrl = ''
                elif 'videomega.tv/validateemb.php' in linksUrl:
                    continue
                elif 'facebook' in linksUrl:
                    continue
                if '' != linksUrl:
                    urlTab.append({'name':self.up.getHostName(linksUrl), 'url':linksUrl, 'need_resolve':1})
            elif 'serijex.com' in linksUrl or 'filmovita.com' in linksUrl:
                name = item[1].replace('Gledaj na video servisu', '').strip()
                fakeUrl = name
                if '://' not in fakeUrl:
                    fakeUrl = 'http://' + fakeUrl + '/fake'
                if 'serijex.com' in linksUrl or 1 == self.up.checkHostSupport(fakeUrl): 
                    urlTab.append({'name':name, 'url':linksUrl, 'need_resolve':1})
        
        if 'serijex.com' in cItem['url']:
            enigmav = self.cm.ph.getSearchGroups(mainData, '''data-enigmav=['"]([^'^"]+?)['"]''')[0]
            enigmav = enigmav.replace('-', '\\u00').replace('=', '\\u')
            try:
                enigmav = byteify( json.loads('{"data":"%s"}' % enigmav) )['data']
                tab1 = re.compile('src="([^"]+?)"', re.IGNORECASE).findall(enigmav)
                tab2 = re.compile('href="([^"]+?)"', re.IGNORECASE).findall(enigmav)
                for tab in [tab1, tab2]:
                    for item in tab:
                        item = item.strip()
                        name = self.up.getHostName(item).strip()
                        if name == '' or not item.startswith('http') or 1 != self.up.checkHostSupport(item): continue
                        urlTab.append({'name':name, 'url':item, 'need_resolve':1})
            except Exception:
                printExc()
        else:
            linksUrl = self.cm.ph.getSearchGroups(mainData, '''["']([^'^"]+?/links/[^'^"]+?)["']''')[0] 
            if linksUrl != '':
                sts, data = self.getPage(self._getFullUrl(linksUrl))
                if not sts: return urlTab
                data = self.cm.ph.getDataBeetwenMarkers(data, '<body>', '</body>', False)[1]
                data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(data)
                for item in data:
                    name = item[1].split('servisu ')[-1]
                    url  = item[0]
                    #name = self.up.getHostName(url)
                    urlTab.append({'name':name, 'url':url, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Filmovita.getVideoLinks [%s]" % baseUrl)
        urlTab = []

        def _getKode(kode):
            kode = self.cm.ph.getSearchGroups(kode, 'kode="(.+[^\\\])";')[0]
            kode = kode.replace('\\"', '"')
            kode = kode.replace("\\'", "'")
            kode = kode.replace('\\\\', '\\')
            printDBG("=======================================")
            printDBG(kode)
            printDBG("---------------------------------------")
            return kode
        if 'filmovita.com' in baseUrl or 'serijex.com' in baseUrl:
            sts, data = self.getPage(baseUrl)
            if not sts: return []
            baseUrl = ''
            kode = self.cm.ph.getSearchGroups(data, 'var kode="(.+?)";var')[0]
            kode = kode.replace('\\"', '"')
            kode = kode.replace('\\\\', '\\')
            while True:
                marker = kode.split('";')[-1]
                printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                printDBG(kode)
                printDBG("+++++++++++++++++++++++++++++++++++++++")
                printDBG(".......................................")
                printDBG(marker)
                printDBG("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                if 'kode[i]-3' in marker:
                    kode = _getKode(kode)
                    kode = kode[:-1].split(' ')
                    try:
                        for item in kode:
                            baseUrl += chr(int(item)-3)
                    except Exception:
                        printExc()
                        break
                elif "x+='@'" in marker:
                    kode = _getKode(kode)
                    i = 0
                    while i < len(kode):
                        if kode[i] == '|' and kode[i+1] == '|':
                            baseUrl += '@'
                        else:
                            baseUrl += kode[i]
                        i += 2
                elif 'reverse()' in marker:
                    kode = _getKode(kode)
                    baseUrl = kode[::-1]
                elif 'kode.length?kode.charAt' in marker:
                    kode = _getKode(kode)
                    i = 0
                    try:
                        while i < (len(kode) - 1):
                            baseUrl += kode[i+1] + kode[i]
                            i += 2
                        if i < len(kode):
                            baseUrl += kode[-1]
                    except Exception:
                        printExc()
                        break
                if 'kode=' in baseUrl:
                    kode = baseUrl
                    baseUrl = ''
                    continue
                else:
                    baseUrl = baseUrl.replace('\\"', '"')
                    baseUrl = self.cm.ph.getSearchGroups(baseUrl, 'src="(http[^"]+?)"', 1, True)[0]
                    break
                
            if '' == baseUrl:
                enigmav = self.cm.ph.getSearchGroups(data, '''data-enigmav=['"]([^'^"]+?)['"]''')[0]
                enigmav = enigmav.replace('-', '\\u00').replace('=', '\\u')
                try:
                    data = byteify( json.loads('{"data":"%s"}' % enigmav) )['data']
                    baseUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"', 1, True)[0] 
                except Exception:
                    printExc()
                    return []
            
        urlTab = self.up.getVideoLinkExt(baseUrl)
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
            self.listGenres(self.currItem, 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #SERIES
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_seasons')
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
        CHostBase.__init__(self, Filmovita(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('filmovitalogo.png')])
    
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
