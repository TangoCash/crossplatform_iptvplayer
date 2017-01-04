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
import copy
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
    return 'http://www.cinemay.com/'

class Cinemay(CBaseHostClass):
    MAIN_URL    = 'http://www.cinemay.com/'
    SRCH_URL    = MAIN_URL + '?s='
    DEFAULT_ICON_URL = 'http://www.cinemay.com/wp-content/themes/cinema/images/logo.png'
    
    MAIN_CAT_TAB = [{'category':'movies', 'title': _('Movies'), 'url':MAIN_URL+'films/', 'icon':DEFAULT_ICON_URL },
                    {'category':'series', 'title': _('Series'), 'url':MAIN_URL+'serie/', 'icon':DEFAULT_ICON_URL },
                    {'category':'search',         'title': _('Search'),         'icon':DEFAULT_ICON_URL, 'search_item':True},
                    {'category':'search_history', 'title': _('Search history'), 'icon':DEFAULT_ICON_URL } 
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Cinemay', 'cookie':'Cinemay.cookie'})
        self.catCache = {'movies':[], 'series':[]}
        self.USER_AGENT = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.seriesCache = {}
    
    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Cinemay.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCatCache(self, url, key):
        self.catCache[key] = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul ', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr( item ).strip()
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if url != '':
                self.catCache[key].append({'title':title, 'url':url})

    def listCategories(self, cItem, category):
        printDBG("Cinemay.listCategories")
        tab = self.catCache.get(cItem['category'], [])
        if 0 == len(tab):
            self.fillCatCache(cItem['url'], cItem['category'])
            tab = self.catCache.get(cItem['category'], [])
        
        if len(tab):
            params = dict(cItem)
            params.update({'category':category, 'title':_('--All--')})
            self.addDir(params)
            
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['category'] = category
            self.addDir(params)
    
    def listSeasons(self, cItem, category):
        printDBG("Cinemay.listSeasons")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        seasons = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="css-tabs_series skin3">', '<div style="clear:both;">', True)[1]
        seasonsData = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="css-tabs_series skin3">', '</ul>', True)[1]
        seasonsData = re.compile('<a [^>]*?>([^<]+?)<').findall(seasonsData)
        idx = 0
        for item in seasonsData:
            title = item.strip()
            num   = self.cm.ph.getSearchGroups('/%s/' % item, '[^0-9]([0-9]+?)[^0-9]')[0]
            seasons.append({'title':title, 'num':num, 'idx':idx})
            idx += 1
        
        tmp = data.split('<div class="css-panes_series skin3">')
        if len(tmp) < 2: return
        seasonsData = self.cm.ph.getAllItemsBeetwenMarkers(tmp[1], '<div>', '</div>', False)
        seasonIdx = 0
        for season in seasonsData:
            season = season.split('</li>')
            if len(season): del season[-1]
            episodes = []
            self.seriesCache[seasonIdx] = []
            for item in season:
                title = self.cleanHtmlStr( item ).strip()
                if title.startswith('E-'): title = title[2:]
                title = 's{0}e{1}'.format(seasons[seasonIdx]['num'], title)
                url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                self.seriesCache[seasonIdx].append({'episode':True, 'title':'{0}: {1}'.format(cItem['title'], title), 'url':self._getFullUrl(url)})
            seasonIdx += 1
        
        for item in seasons:
            params = dict(cItem)
            params.update(item)
            params['category'] = category
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("Cinemay.listEpisodes")
        season = self.seriesCache.get(cItem['idx'], [])
        
        for item in season:
            params = dict(cItem)
            params.update(item)
            self.addVideo(params)
    
    def listItems(self, cItem, category=None):
        printDBG("Cinemay.listItems")
        
        tmp = cItem['url'].split('?')
        url = tmp[0]
        if len(tmp) > 1:
            arg = tmp[1]
        else: arg = ''
        
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%s/' % page
        if '' != arg:
            url += '?' + arg
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if ('/page/%s/' % (page+1)) in data:
            nextPage = True
        m1 = '<div class="unfilm">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div id="sidebar">', False)[1]
        data = data.split(m1)
        
        if len(data): data[-1] = data[-1].split('<div class="navigation">')[0]
        for item in data:
            cat = category
            params = dict(cItem)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            title = self.cleanHtmlStr( title )
            if title == '': continue
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            desc  = self.cleanHtmlStr( item.split('<div class="infob">')[-1] )
            params.update({'title':title, 'icon':self._getFullUrl(icon), 'desc':desc, 'url':self._getFullUrl(url)})
            if cat == None:
                if '/serie/' in url: 
                    itemType = 'serie'
                    cat = 'list_seasons'
                else: itemType = 'video'
            else:
                itemType = 'serie'
            if itemType == 'video':
                self.addVideo(params)
            else:
                params['category'] = cat
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + searchPattern
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("Cinemay.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        tmp = tmp.split('</tr>')
        if len(tmp): del tmp[-1]
        for item in tmp:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if '/voir/' in url or '/voire/' in url or '/ser/' in url:
                title = self.cm.ph.getSearchGroups(item, 'src="[^"]+?/([^/]+?)\.png"')[0]
                title = '[{0}] {1}'.format(title, self.cleanHtmlStr( item ))
                urlTab.append({'name':title, 'url':self._getFullUrl(url), 'need_resolve':1})
                
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="wbox2 video dark">', '</iframe>')
        for item in data:
            videoUrl = self.cm.ph.getSearchGroups(item, '<iframe[^>]+?src="(http[^"]+?)"', 1, True)[0]
            urlTab.append({'name':self.up.getHostName(videoUrl), 'url':self._getFullUrl(videoUrl), 'need_resolve':1})
        
        if 0 == len(urlTab):
            urlTab.append({'name':'Main url', 'url':cItem['url'], 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("Cinemay.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if 'cinemay.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="wbox2 video dark">', '</iframe>', False)[1]
            videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"', 1, True)[0]
        
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem.get('url', '')
        
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
        elif category == 'movies':
            self.listCategories(self.currItem, 'video_items')
        elif category == 'video_items':
            self.listItems(self.currItem)
    #SERIES
        elif category == 'series':
            self.listCategories(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listItems(self.currItem, 'list_seasons')
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
        CHostBase.__init__(self, Cinemay(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('cinemaylogo.png')])
    
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
