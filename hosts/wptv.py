# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSelOneLink, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import time
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
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.wpDefaultformat = ConfigSelection(default = "2", choices = [("1", "Niska"), ("2", "Wysoka")])
config.plugins.iptvplayer.wpUseDF = ConfigYesNo(default = False)
#config.plugins.iptvplayer.wpSortBy = ConfigSelection(default = "2", choices = [("1", "Najczęściej oglądane"), ("2", "Najnowsze"), ("3", "Najwyżej oceniane"), ("4", "Najczęściej komentowane")])

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.wpSortBy))
    optionList.append( getConfigListEntry( "Domyślny jakość video:", config.plugins.iptvplayer.wpDefaultformat ) )
    optionList.append( getConfigListEntry( "Używaj domyślnej jakości video:", config.plugins.iptvplayer.wpUseDF ) )
    return optionList
###################################################


def gettytul():
    return 'WpTV'

class WpTV(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30", 'Accept': 'text/html'}
    
    MAIN_URL = 'http://wp.tv/'
    DEFAULT_ICON = 'http://i.wp.pl/a/i/wptv2/2010/logo_fb.png'
    MAIN_CAT_TAB_S = [{'category':'recommended',     'title': 'Polecane', 'url':MAIN_URL + 'app/recommended', 'icon':DEFAULT_ICON},
                      {'category':'list_items',      'title': 'Główna',   'url':MAIN_URL,                     'icon':DEFAULT_ICON}]
                    
    MAIN_CAT_TAB_E = [{'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                      {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'WpTV.com', 'cookie':'wp.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("WpTV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def getMainMenu(self, cItem, category):
        printDBG("WpTV.getMainMenu")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="submenu">', '</nav>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<ul>', '</ul>', False)
        self.cache = {'cats':[]}
        
        for item in data:
            catTitle = self.cm.ph.getDataBeetwenMarkers(item, '<li class="header">', '</li>', False)[1]
            catTitle = self.cleanHtmlStr( catTitle )
            catsData = re.compile('<a href="([^"]+?)">([^<]+?)</a>').findall(item)
            catsTab = []
            for cat in catsData:
                url   = self._getFullUrl(cat[0])
                title = self.cleanHtmlStr(cat[1])
                cid   = self.cm.ph.getSearchGroups(cat[0], 'cid\,([0-9]+?)\,')[0]
                if cid != '':
                    catsTab.append({'title':title, 'url':url, 'cid':cid})
            if len(catsTab):
                self.cache['cats'].append(catsTab)
                params = dict(cItem)
                params.update({'category':category, 'title':catTitle, 'cats_id': len(self.cache['cats'])-1})
                self.addDir(params)
        
    def listCategory(self, cItem, category):
        catsId = cItem.get('cats_id', -1)
        printDBG("WpTV.listCategory catsId [%s]" % catsId)
        if catsId < 0 or catsId > len(self.cache['cats']): return
        
        for item in self.cache['cats'][catsId]:
            params = dict(cItem)
            params.update(item)
            params['category'] = category
            self.addDir(params)
            
    def listRecommended(self, cItem):
        printDBG("WpTV.listRecommended")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        try:    
            data = byteify(json.loads(data))
            for item in data['clips']:
                url    = item['mobileUrl']
                if 'klip' not in url: continue
                icon   = item['image']
                title  = item['title']
                desc  = item['date'] + ' '
                desc   += self.cleanHtmlStr(item['description'])
                
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'desc':desc, 'icon':self._getFullUrl(icon), 'url':self._getFullUrl(url)})
                self.addVideo(params)
        except Exception:
            printExc()
    
    def listItems(self, cItem):
        printDBG("WpTV.listItems")
        
        search = cItem.get('search', None)
        if search != None:
            post_data = {'szukaj':search}
        else: post_data = None
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams, post_data)
        if not sts: return
        
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'teaser"', '</footer>', False)[1]
        nextPage = self.cm.ph.getSearchGroups(data, 'a href="([^"]+?)"[^>]*?class="paging__next"')[0]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>', True)
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if 'klip' not in url: continue
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cleanHtmlStr(item)
            
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'desc':desc, 'icon':self._getFullUrl(icon), 'url':self._getFullUrl(url)})
            self.addVideo(params)
        
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'url':self._getFullUrl(nextPage)})
            self.addDir(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("WpTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        #cItem['search'] = urllib.quote(searchPattern)
        cItem['url'] = self.MAIN_URL + 'query,%s,szukaj.html?' % urllib.quote(searchPattern)
        self.listItems(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("WpTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        vidId = self.cm.ph.getSearchGroups(data, 'data-mid="([^"]+?)"')[0]
        vidUrl = self.MAIN_URL + "player/mid,%s,embed.json" % vidId
        try:
            sts, data = self.cm.getPage(vidUrl, self.defaultParams)
            if not sts: return []
            
            tmpTab = []
            qMap = {"HQ":'2', "LQ":'1'}
            data = byteify(json.loads(data))
            for item in data['clip']['url']:
                if 'mp4' not in item['type']: continue
                urlTab.append({'name':item['quality'] + ' ' + item['type'], 'url':self._getFullUrl(item['url']), 'quality':qMap.get(item['quality'], '3'), 'need_resolve':0})
                
            if 0 < len(urlTab):
                max_bitrate = int(config.plugins.iptvplayer.wpDefaultformat.value)
                def __getLinkQuality( itemLink ):
                    if 'mobile' in itemLink['name']: return 0
                    return int(itemLink['quality'])
                urlTab = CSelOneLink(urlTab, __getLinkQuality, max_bitrate).getSortedLinks()
                if config.plugins.iptvplayer.wpUseDF.value:
                    urlTab = [urlTab[0]]
        except Exception:
            printExc()
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
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB_S, {'name':'category'})
            self.getMainMenu({'name':'category', 'url':self.MAIN_URL, 'icon':self.DEFAULT_ICON}, 'category')
            self.listsTab(self.MAIN_CAT_TAB_E, {'name':'category'})
        elif category == 'category':
            self.listCategory(self.currItem, 'list_items')
        elif category == 'recommended':
            self.listRecommended(self.currItem)
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
        CHostBase.__init__(self, WpTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('wptvlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
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
