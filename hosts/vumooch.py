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
    return 'http://vumoo.at/'

class Vumoo(CBaseHostClass):
    USER_AGENT = 'curl/7'
    MAIN_URL    = 'http://vumoo.at/'
    SRCH_URL    = MAIN_URL + 'videos/search/?search='
    DEFAULT_ICON_URL = 'http://pbs.twimg.com/profile_images/559558208411287552/fFKLeLBS.png'
    
    MAIN_CAT_TAB = [{'category':'movies',         'title': _('Movies'),       'url':MAIN_URL,                                         'icon':DEFAULT_ICON_URL},
                    {'category':'list_items',     'title': _('TV Shows'),     'url':MAIN_URL + 'videos/category/trending-television', 'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title': _('Search'),       'search_item':True},
                    {'category':'search_history', 'title': _('Search history')} 
                   ]
    MOVIES_TAB = [{'category':'genres',          'title':_('Genres')},
                  {'category':'list_items',      'title':_('Currently Watching'),      'url':MAIN_URL + 'videos/category/currently-watching'},
                  {'category':'list_items',      'title':_('Popular this Week'),       'url':MAIN_URL + 'videos/category/popular-this-week'},
                  {'category':'list_items',      'title':_('IMDB Top Rated'),          'url':MAIN_URL + 'videos/category/top-rated-imdb'},
                  {'category':'list_items',      'title':_('IMDB Top Rated'),          'url':MAIN_URL + 'videos/category/top-rated-imdb'},
                  {'category':'list_items',      'title':_('New Releases'),            'url':MAIN_URL + 'videos/category/new-releases'},
                  {'category':'list_items',      'title':_('Recently Added'),          'url':MAIN_URL + 'videos/category/recently-added'},
                 ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Vumoo', 'cookie':'Vumoo.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.genresCache = []
        self.linksCache = {}
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':'vumoo.at', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
        
    def listGenres(self, cItem, category):
        printDBG("Vumoo.listGenres")

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="multi-column-dropdown">', 'Adult', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url})
            self.addDir(params)
        
    def fillTvShowFilters(self, url):
        printDBG("Vumoo.fillTvShowFilters")
        self.tvshowGenresCache = []
        sts, data = self.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Subgenres', '<section', False)[1]
        data = data.split('<li>')
        if len(data): del data[0]
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            if url.startswith('http'):
                self.tvshowGenresCache.append({'title':title, 'url':url})
        
    def listTvShowsGenres(self, cItem, category):
        printDBG("Vumoo.listTvShowsGenres")
        if 0 == len(self.tvshowGenresCache):
            self.fillTvShowFilters(cItem['url'])
        
        if len(self.tvshowGenresCache):
            tab = [{'title':_('--All--'), 'url':cItem['url']}]
            cItem = dict(cItem)
            cItem['category'] = category
            tab.extend(self.tvshowGenresCache)
            self.listsTab(tab, cItem)
            
    def listItems(self, cItem, category='explore_item'):
        printDBG("Vumoo.listItems")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        url += '?'
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page=%d&' % page
        if post != '': 
            url += post
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = False
        #nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="navigation"', '</div>', False)[1]
        #if '>{0}<'.format(page+1) in nextPage: nextPage = True
        #else: nextPage = False
        
        num = 0
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<article', '</article>')       
        for item in data:
            num += 1
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            if icon == '': icon = self.cm.ph.getDataBeetwenMarkers(item, 'url(', ')', False)[1].strip()
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            if title == '': title = self.cm.ph.getSearchGroups(item, 'data-title="([^"]+?)"')[0]
            
            if url != '' and title != '': 
                params = dict(cItem)
                params.update( {'title': self.cleanHtmlStr( title ), 'url':self.getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self.getFullUrl(icon)} )
                params['category'] = category
                self.addDir(params)
        
        if nextPage or num >= 20:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def exploreItem(self, cItem, category):
        printDBG("Vumoo.exploreItem")
        self.linksCache = {}
        type = None
        #try:
        #    sts, response = self.cm.getPage(cItem['url'], {'return_data':False})
        #    url = response.geturl()
        #    response.close()
        #    if '/tv/' in url: type = 'tv'
        #    elif '/play/' in url: type = 'movie'
        #except Exception:
        #    printExc()
        
        if type == None:
            sts, data = self.getPage(cItem['url'])
            if not sts: return
            if 'tv-details-seasons' in data: type = 'tv'
            else: type = 'movie'
            
        if type == 'movie':
            printDBG('Vumoo.exploreItem - MOVIE')
            mov_id = self.cm.ph.getSearchGroups(data, '''mov_id[\s]*=[\s]*["']([0-9]+?)["']''')[0]
            t_id   = self.cm.ph.getSearchGroups(data, '''t_id[\s]*=[\s]*["']([0-9]+?)["']''')[0]
            googleLink    = self.cm.ph.getSearchGroups(data, 'googleLink[\s]*=[\s]*"(http[^"]+?)"')[0].replace('\\/', '/')
            openloadLink  = self.cm.ph.getSearchGroups(data, 'openloadLink[\s]*=[\s]*"(http[^"]+?)"')[0].replace('\\/', '/')
            self.linksCache[mov_id] = []
            #if googleLink.startswith('http'): self.linksCache[mov_id].append({'type':'google', 'url':googleLink})
            if openloadLink.startswith('http'): self.linksCache[mov_id].append({'type':'openload', 'url':openloadLink})
            params = dict(cItem)
            params.update({'links_id':mov_id, 't_id':t_id})
            self.addVideo(params)
        elif type == 'tv':
            printDBG('Vumoo.exploreItem - TV SERIES')
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tv-details-episodes synopsis-container">', '</ol>')[1]
            sp = '<li id=season'
            data = data.split(sp)
            if len(data): del data[0]
            num = 0 
            for item in data:
                num += 1
                item = sp + item
                tmp = self.cm.ph.getSearchGroups(item, 'season([0-9]+?)-([0-9]+?)[^0-9]', 2)
                sNum = tmp[0]
                eNum = tmp[1]
                title = ''
                if '' != eNum and '' != sNum: title = 's%se%s ' % (sNum.zfill(2), eNum.zfill(2))
                title += self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
                #icon   = self.cm.ph.getSearchGroups(item, 'data-poster="([^"]+?)"')[0]
                #if not icon.endswith('.jpg'): icon = cItem.get('icon', '')
                
                links_id = title + str(num)
                self.linksCache[links_id] = []
                tmp = re.compile('<[^>]+?id="([^"]+?)"[^>]+?data-click="([^"]+?)"').findall(item)
                for tmpItem in tmp:
                    link = tmpItem[1].strip()
                    if link.startswith('http') and '://' in link and 'ubershared.co' not in link:
                        self.linksCache[links_id].append({'type':tmpItem[0].strip(), 'url':link})
                if len(self.linksCache[links_id]):
                    params = dict(cItem)
                    params.update({'title':'{0}: {1}'.format(cItem['title'], title), 'links_id':links_id, 'desc': self.cleanHtmlStr( item ) }) #, 'icon':self.getFullUrl(icon)})
                    self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url']  = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("Vumoo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        linksID = cItem.get('links_id', 'none')
        if linksID in self.linksCache:
            for item in self.linksCache[linksID]:
                urlTab.append({'name':item['type'], 'url':item['url'], 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Vumoo.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        videoUrl = baseUrl
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
    #ITEMS
        elif category == 'movies':
            self.listsTab(self.MOVIES_TAB, self.currItem)
        elif category == 'genres':
            self.listGenres(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
    #EXPLORE
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
            
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
        CHostBase.__init__(self, Vumoo(), True, [])#[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('vumoochlogo.png')])
    
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
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem