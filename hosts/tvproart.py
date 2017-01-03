# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetDefaultLang, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
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
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://tvproart.pl/'

class TVProart(CBaseHostClass):
    MAIN_URL    = 'http://tvproart.pl/'
    API_URL     = MAIN_URL + 'ajaxVod/'
    SEARCH_URL  = MAIN_URL + 'search?q='
    
    MAIN_CAT_TAB = [{'category':'categories',            'title': 'VOD' },
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'TVProart', 'cookie':'tvproart.cookie'})
        self.categories = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
    
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("TVProart.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def addNextPage(self, cItem, nextPage, page):
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listCategories(self, cItem, category):
        printDBG("TVProart.listCategories [%s]" % cItem)
        if self.categories == {}:
            sts, data = self.cm.getPage(self.API_URL + 'categories')
            if not sts: return
            try:
                data = byteify(json.loads(data))
                if data['status'] != '200': return
                self.categories = data['content']
            except Exception:
                printExc()
        try:
            for item in self.categories['cats']:
                params = dict(cItem)
                params.update({'title':item['title'], 'id':item['id'], 'slug':item['slug'], 'icon':self._getFullUrl(item['image']), 'category':category})
                self.addDir(params)
        except Exception:
            printExc()
    
    def listVideos(self, cItem):
        printDBG("TVProart.listVideos [%s]" % cItem)
        page = cItem.get('page', 1)
        url = self.API_URL + 'movies?type=cats&crit_id={0}'.format(cItem['slug'])
        sts, data = self.cm.getPage(url + '&page={0}'.format(page))
        if not sts: return
        nextPage = False
        try:
            data = byteify(json.loads(data))
            if data['status'] != '200': return
            for item in data['content']:
                icon = self._getFullUrl( item['thumb'] )
                item = item['data']
                url = self.API_URL + 'video?id={0}&slug={1}'.format(item['id'], item['slug'])
                params = {'title':item['title'], 'url':url, 'icon':icon, 'desc':item['date']}
                self.addVideo(params)
        except Exception:
            printExc()
            
        nextPage = False
        try:
            sts, data = self.cm.getPage(url + '&page={0}'.format(page+1))
            data = byteify(json.loads(data))
            if len(data['content']) > 0:
                nextPage = True
        except Exception:
            pass
        self.addNextPage(cItem, nextPage, page)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TVProart.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 0)
        url = self.SEARCH_URL + urllib.quote(searchPattern)
        sts, data = self.cm.getPage(url + '&page={0}'.format(page))
        if not sts: return
        nextPage = False
        try:
            data = byteify(json.loads(data))
            if data['status'] != '200': return
            for item in data['content']['movies']:
                tmp = item['href'].split('/')
                url = self.API_URL + 'video?id={0}&slug={1}'.format(tmp[-2], tmp[-1])
                params = {'title':item['text'], 'url':url}
                self.addVideo(params)
        except Exception:
            printExc()
        
    def getLinksForVideo(self, cItem):
        printDBG("TVProart.getLinksForVideo [%s]" % cItem)
        urlTab = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        try:
            data = byteify(json.loads(data))
            urlTab.append({'name':'vod', 'url':data['content']['video']['movieFile'], 'need_resolve':0})
        except Exception:
            pass
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
    #CATEGORIES
        elif category == 'categories':
            self.listCategories(self.currItem, 'category')
    #CATEGORY
        elif category == 'category':
            self.listVideos(self.currItem)
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
        CHostBase.__init__(self, TVProart(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvproartlogo.png')])
    
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
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
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
