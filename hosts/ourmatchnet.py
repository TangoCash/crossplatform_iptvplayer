# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getF4MLinksWithMeta, getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
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
    return 'http://ourmatch.net/'

class OurmatchNet(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL   = 'http://ourmatch.net/'
    
    DEFAULT_ICON  = "http://ourmatch.net/wp-content/themes/OurMatch/images/logo.png"
    
    MAIN_CAT_TAB = [{'category':'list_items',      'title': _('Home'),              'url':MAIN_URL,                     'icon':DEFAULT_ICON},
                    {'category':'popular',         'title': _('Popular'),           'url':MAIN_URL,                     'icon':DEFAULT_ICON},
                    {'category':'allleagues',      'title': _('All Leagues'),       'url':MAIN_URL,                     'icon':DEFAULT_ICON},
                    {'category':'seasons',         'title': _('Previous Seasons'),  'url':MAIN_URL+'previous-seasons/', 'icon':DEFAULT_ICON},
                    {'category':'video',           'title': _('Goal Of The Month'), 'url':MAIN_URL+'goal-of-the-month/','icon':DEFAULT_ICON},                    
                    {'category':'search',          'title': _('Search'), 'search_item':True,                            'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),                                        'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'ourmatch.net', 'cookie':'ourmatchnet.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = {'popular':[], 'allleagues':[]}
        self.cache2 = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if 0 < len(url) and not url.startswith('http'):
                url =  self.MAIN_URL + url
            if not self.MAIN_URL.startswith('https://'):
                url = url.replace('https://', 'http://')
                
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)

        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("OurmatchNet.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir' and 'video' != item.get('category', ''):
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCache(self, cItem):
        printDBG("OurmatchNet.fillCache [%s]" % cItem)
        self.cache = {'popular':[], 'allleagues':[]}
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="popular-leagues-list">', '</ul>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li ', '</li>')
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''href=['"](http[^'^"]+?)['"]''')[0]
            if '' == url: continue
            title = self.cleanHtmlStr(item)
            self.cache['popular'].append({'title':title, 'url':url})
            
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="division">', '</div>')
        for division in tmp:
            division = division.split('<ul class="regions">')
            if 2 != len(division): continue
            divisionTitle = self.cleanHtmlStr(division[0])
            regionsTab = []
            regions = self.cm.ph.getAllItemsBeetwenMarkers(division[1], '<li ', '</li>')
            for region in regions:
                url = self.cm.ph.getSearchGroups(region, '''href=['"](http[^'^"]+?)['"]''')[0]
                if '' == url: continue
                title = self.cleanHtmlStr(region)
                regionsTab.append({'title':title, 'url':url})
            if len(regionsTab):
                self.cache['allleagues'].append({'title':divisionTitle, 'regions_tab':regionsTab})
            
    def listPopulars(self, cItem, category):
        printDBG("OurmatchNet.listPopulars [%s]" % cItem)
        tab = self.cache.get('popular', [])
        if 0 == len(tab): self.fillCache(cItem)
        tab = self.cache.get('popular', [])
        
        params = dict(cItem)
        params['category'] = category
        self.listsTab(tab, params)
        
    def listLeagues(self, cItem, category):
        printDBG("OurmatchNet.listLeagues [%s]" % cItem)
        tab = self.cache.get('allleagues', [])
        if 0 == len(tab): self.fillCache(cItem)
        tab = self.cache.get('allleagues', [])
        for idx in range(len(tab)):
            item = tab[idx]
            params = dict(cItem)
            params.update({'category':category, 'title':item['title'], 'idx':idx})
            self.addDir(params)
            
    def listLeagueItems(self, cItem, category):
        printDBG("OurmatchNet.listLeadItems [%s]" % cItem)
        idx = cItem['idx']
        tab = self.cache['allleagues'][idx]['regions_tab']
        
        params = dict(cItem)
        params['category'] = category
        self.listsTab(tab, params)
            
    def listYersTabs(self, cItem, category):
        printDBG("OurmatchNet.listYersTabs [%s]" % cItem)
        
        self.cache2 = {}
        
        sts, data = self.cm.getPage(cItem['url']) 
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="tabs_container">', '<div class="widget">')[1]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="tabs">', '</ul>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>')
        tabs = []
        for tab in tmp:
            tabId  = self.cm.ph.getSearchGroups(tab, '''href=['"]#([^'^"]+?)['"]''')[0]
            tabTitle = self.cleanHtmlStr(tab)
            tabs.append({'title':tabTitle, 'id':tabId})
            
        data = data.split('<div class="tab_content" ')
        if len(data): del data[0]
        if len(data) != len(tabs): return
        for idx in range(len(data)):
            tab = tabs[idx]
            divisionsTab = []
            divisions = self.cm.ph.getAllItemsBeetwenMarkers(data[idx], '<li class="header">', '</ul>')
            for division in divisions:
                divisionsTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(division, '<li class="header">', '</li>')[1] )
                regionsTab = []
                regions = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(division)
                for item in regions:
                    regionsTab.append({'title':self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0])})
                if len(regionsTab):
                    divisionsTab.append({'title':divisionsTitle, 'regions_tab':regionsTab})
            if len(divisionsTab):
                self.cache2[tab['id']] = divisionsTab
                params = dict(cItem)
                params.update({'category':category, 'title':tab['title'], 'tab':tab['id']})
                self.addDir(params)
                    
    def listLeagues2(self, cItem, category):
        printDBG("OurmatchNet.listLeagues2 [%s]" % cItem)
        tab = self.cache2.get(cItem['tab'], [])
        for idx in range(len(tab)):
            item = tab[idx]
            params = dict(cItem)
            params.update({'category':category, 'title':item['title'], 'idx':idx})
            self.addDir(params)
            
    def listLeagueItems2(self, cItem, category):
        printDBG("OurmatchNet.listLeadItems2 [%s]" % cItem)
        tab = self.cache2[cItem['tab']][cItem['idx']]['regions_tab']
        params = dict(cItem)
        params['category'] = category
        self.listsTab(tab, params)
        
    def listItems(self, cItem):
        printDBG("OurmatchNet.listItems [%s]" % cItem)
        page = cItem.get('page', 1)        
        url = cItem['url']
        if page > 1:
            url += 'page/%d/' % page
        if 's' in cItem:
            url += '?s=' + cItem['s']
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        if ('/page/%d/' % (page+1)) in data:
            nextPage = True
        else:
            nextPage = False
        sp = '<div class="vidthumb">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<footer id="footer">')[1]
        data = data.split(sp)
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, '''href=['"](http[^'^"]+?)['"]''')[0]
            if '' == url: continue
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]*(http[^'^"^>]+?)[>'"]''')[0]
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0] 
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="vidinfo">', '</div>')[1] )
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("OurmatchNet.getLinksForVideo [%s]" % cItem)
        urlTab = [] #{'name':'', 'url':cItem['url'], 'need_resolve':1}]
        
        sts, data = self.cm.getPage(cItem['url']) 
        if not sts: return
        
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li data-pos="top" ', '</li>')
        for item in tmp:
            name = self.cleanHtmlStr(item)
            url  = self.cm.ph.getDataBeetwenMarkers(item, 'data-config=&quot;', '&quot;', False)[1]
            if url != '':
                urlTab.append({'name':name, 'url':self._getFullUrl(url), 'need_resolve':1})
        
        videoContents = self.cm.ph.getDataBeetwenMarkers(data, 'var video_contents', '</script>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(videoContents, '{embed:', '}')
        for item in tmp:
            nameTab = []
            for key in ['lang', 'type', 'qualty', 'source']:
                name = self.cm.ph.getSearchGroups(item, '''['"]?%s['"]?:['"]([^'^"]+?)['"]''' % key)[0]
                if name != '': nameTab.append( name )
            
            url = self.cm.ph.getSearchGroups(item, '<iframe[^>]+?src="([^"]+?)"', 1, ignoreCase=True)[0]
            url = self._getFullUrl(url)
            if url != '':
                urlTab.append({'name':' '.join( nameTab ), 'url':self._getFullUrl(url), 'need_resolve':1})
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="details" class="section-box">', '</div>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<p>', '</p>')
        for item in tmp:
            name = self.cleanHtmlStr(item)
            url  = self.cm.ph.getDataBeetwenMarkers(item, 'data-config="', '"', False)[1]
            if url == '':
                url = self.cm.ph.getSearchGroups(item, '<iframe[^>]+?src="([^"]+?)"', 1, ignoreCase=True)[0]
            url = self._getFullUrl(url)
            if not url.startswith('http'): continue
            urlTab.append({'name':name, 'url':url, 'need_resolve':1})
        
        if 0 == len(urlTab):
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '//config.playwire.com/', '.json')
            for item in tmp:
                name = 'playwire.com'
                urlTab.append({'name':name, 'url':self._getFullUrl(item), 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("OurmatchNet.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if 'playwire.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            try:
                data = byteify(json.loads(data))
                if 'content' in data:
                    url = data['content']['media']['f4m']
                else:
                    url = data['src']
                sts, data = self.cm.getPage(url)
                baseUrl = self.cm.ph.getDataBeetwenMarkers(data, '<baseURL>', '</baseURL>', False)[1].strip()
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<media ', '>')
                for item in data:
                    url  = self.cm.ph.getSearchGroups(item, '''url=['"]([^'^"]+?)['"]''')[0]
                    name = self.cm.ph.getSearchGroups(item, '''height=['"]([^'^"]+?)['"]''')[0]
                    if name == '': self.cm.ph.getSearchGroups(item, '''bitrate=['"]([^'^"]+?)['"]''')[0]
                    if not url.startswith('http'):
                        url = baseUrl + '/' + url
                    if url.startswith('http'):
                        if 'm3u8' in url:
                            hlsTab = getDirectM3U8Playlist(url)
                            urlTab.extend(hlsTab)
                        else:
                            urlTab.append({'name':name, 'url':url})
            except Exception:
                printExc()
        elif videoUrl.startswith('http'):
            urlTab.extend(self.up.getVideoLinkExt(videoUrl))
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("OurmatchNet.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'url':self.MAIN_URL, 's':urllib.quote(searchPattern)})
        self.listItems(cItem)

    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'popular':
            self.listPopulars(self.currItem, 'list_items')
        elif category == 'allleagues':
            self.listLeagues(self.currItem, 'list_league')
        elif category == 'list_league':
            self.listLeagueItems(self.currItem, 'list_items')
        elif category == 'seasons':
            self.listYersTabs(self.currItem, 'allleagues2')
        elif category == 'allleagues2':
            self.listLeagues2(self.currItem, 'list_league2')
        elif category == 'list_league2':
            self.listLeagueItems2(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
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
        CHostBase.__init__(self, OurmatchNet(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('ourmatchnetlogo.png')])
    
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
