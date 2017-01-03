# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
from Components.config import config, ConfigSelection, getConfigListEntry
###################################################


###################################################
# Config options for HOST
###################################################
 
def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'http://wrestlingnetwork.tv/'

class WrestlingNet(CBaseHostClass):
    MAIN_URL   = 'http://wrestlingnetwork.tv/'
    
    MAIN_CAT_TAB = [{'category':'search',                'title':_('Search'), 'search_item':True},
                    {'category':'search_history',        'title':_('Search history')} ]
    
    def __init__(self):
        printDBG("WrestlingNet.__init__")
        CBaseHostClass.__init__(self, {'history':'wrestling-network.net', 'cookie':'wrestlingnetwork.cookie'})
        self.DEFAULT_ICON = 'http://static-server1.wrestling-network.net/images/layout/wnhd_5years_bug.png'
        self.USER_AGENT = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.cacheSubCategory = {}
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url):
        if url == '':
            return url
            
        if url.startswith('.'):
            url = url[1:]
        
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if url.startswith('/'):
                url = url[1:]
            if not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def _getIconUrl(self, url):
        url = self._getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})

    def listsTab(self, tab, cItem):
        printDBG("WrestlingNet.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def getPage(self, baseUrl, params={}, post_data=None):
        params['cloudflare_params'] = {'domain':'wrestlingnetwork.tv', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self._getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
            
    def listsMainMenu(self, cItem, subNextCategory, nextCategory):
        printDBG("listsMainMenu")
        self.cacheSubCategory = {}
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        subCatsUrls = []
        catsData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<ul class="sub-menu">', '</ul>', withMarkers=False)
        for catItem in catsData:
            tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(catItem)
            for item in tmp:
                url   = self._getFullUrl(item[0])
                title = self.cleanHtmlStr(item[1])
                catUrl = '/'.join( url.split('/')[:-1] )
                if catUrl not in self.cacheSubCategory: 
                    self.cacheSubCategory[catUrl] = []
                self.cacheSubCategory[catUrl].append({'url':url, 'title':title})
                subCatsUrls.append(url)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="menu-main-menu', '</div>')[1]
        data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        prevUrl = ''
        categories = []
        for item in data:
            url   = self._getFullUrl(item[0])
            if url in subCatsUrls: continue
            title = self.cleanHtmlStr(item[1])
            if url in self.cacheSubCategory:
                category = subNextCategory
            else:
                category = nextCategory
            params = dict(cItem)
            params.update({'url':url, 'title':title})
            params['category'] = category
            self.addDir(params)
        
    def listSubCategory(self, cItem, nextCategory):
        printDBG("listSubCategory")
        tab =  self.cacheSubCategory.get(cItem['url'], [])
        params = dict(cItem)
        params['category'] = nextCategory
        self.listsTab(tab, params)
        
    def listVideosByCategory(self, cItem, category):
        printDBG("WrestlingNet.listVideosByCategory")
        self._listVideos(cItem)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("WrestlingNet.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        cItem.update({'url':self.MAIN_URL, 'srch':'?s=%s&submit=Search' % searchPattern})
        self._listVideos(cItem)
    
    def _listVideos(self, cItem):
        printDBG("WrestlingNet._listVideos")
        
        page = cItem.get('page', 1)
        url = cItem.get('url', '')
        if page > 1:
            url += '/page/%s' % page
        url += cItem.get('srch', '')
        
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''class=['"]pagination['"]'''), re.compile('</div>'), True)[1]
        if ('>%s<' % (page+1)) in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="content-container">', '<div class="solar-excerpt">', withMarkers=False)
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if '/contact' in url: continue
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1]
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc':self.cleanHtmlStr( item ), 'icon':self._getIconUrl(icon)} )
                self.addVideo(params)
        
        if nextPage:
            params = params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("WrestlingNet.getLinksForVideo [%s]" % cItem)
        urlTab = []
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return urlTab
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="solar-main-content">', '</div>', True)
        if not sts:
            SetIPTVPlayerLastHostError(_("Please visit '%s' from using web-browser form the PC. If links are available please report this problem.\nEmail: samsamsam@o2.pl") % cItem['url'])
            return urlTab
            
        data = data.split('<h2 style="text-align: center;">')
        if len(data): del data[0]
        re_links = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>')
        for item in data:
            type = self.cleanHtmlStr( item.split('</h2>')[0] )
            
            links = re_links.findall(item)
            for link in links:
                urlTab.append({'name':type + ' ' + link[1], 'url':link[0]})
            
        return urlTab
        
    def getResolvedURL(self, url):
        printDBG("WrestlingNet.getResolvedURL [%s]" % url)
        urlTab = []
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return urlTab
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if not videoUrl:
            videoUrl = self.cm.ph.getSearchGroups(data, "file: '([^']+?)'")[0]
            if '.m3u8' in videoUrl:
                urlTab = getDirectM3U8Playlist(videoUrl, checkExt=True)
            
        urlTab = self.up.getVideoLinkExt( videoUrl )
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('WrestlingNet.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "WrestlingNet.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            cItem = {'name':'category', 'url':self.MAIN_URL, 'icon':self._getIconUrl(self.DEFAULT_ICON)}
            self.listsMainMenu(cItem, 'list_subcategory', 'list_category')
            self.listsTab(WrestlingNet.MAIN_CAT_TAB, cItem)
        elif 'list_subcategory' == category:
            self.listSubCategory(self.currItem, 'list_category')
    #CATEGORY
        elif 'list_category' == category:
            self.listVideosByCategory(self.currItem, '')
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
        CHostBase.__init__(self, WrestlingNet(), True)
    
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
        urlList = self.host.getResolvedURL(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Filmy",  "filmy"))
        #searchTypesOptions.append(("Seriale","seriale"))
        
        for cItem in cList:
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
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

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

