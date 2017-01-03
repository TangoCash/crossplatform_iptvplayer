# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSelOneLink, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
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
config.plugins.iptvplayer.wrzutaDefaultformat = ConfigSelection(default = "360", choices = [("0", "format: najgorszy"), ("240", "format: 240p"), ("360", "format: 360p"),  ("480", "format: 480p"), ("720", "format: 720"), ("9999", "format: najlepszy")])
config.plugins.iptvplayer.wrzutaUseDF = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Domyślny format video:", config.plugins.iptvplayer.wrzutaDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnego format video:", config.plugins.iptvplayer.wrzutaUseDF))
    return optionList
###################################################


def gettytul():
    return 'wrzuta.pl'

class Wrzuta(CBaseHostClass):
    MAIN_URL    = 'http://www.wrzuta.pl/'
    SEARCH_URL  = MAIN_URL + 'szukaj/audio/'
    MAIN_CAT_TAB = [{'category':'music_cats',            'title': 'Muzyka', 'url':MAIN_URL + 'audio/najnowsze' },
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
                    
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Wrzuta', 'cookie':'wrzuta.cookie'})
        self.filterCache = {}

    
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Wrzuta.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addAudio(params)
        
    def listMusicCategories(self, cItem, category):
        printDBG("Wrzuta.listMusicCategories [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="music-menu">', '<div class="advertisement', False)[1]
        data = data.split('</a>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cleanHtmlStr( item )
            params = dict(cItem)
            params.update( {'title':title, 'url':url} )
            params['category'] = category
            self.addDir(params)
    
    def listItems(self, cItem, m1 = '<div class="music-cat">', m2 = '</ul>', sp ='</li>'):
        printDBG("Wrzuta.listItems [%s]" % cItem)
        url = cItem['url']
        page = cItem.get('page', 1)
        if url[-1] != '/': url += '/{0}'.format(page)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        nextPage = False
        if '<a class="paging-next"' in data:
            nextPage = True
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(sp)
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cleanHtmlStr( item )
            params = dict(cItem)
            params.update( {'title':title, 'url':url, 'icon':icon, 'desc':desc} )
            self.addAudio(params)
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Wrzuta.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        currItem = dict(cItem)
        currItem['url'] = self.SEARCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(currItem, m1='<ul class="result-files music">')
        
    def getLinksForVideo(self, cItem):
        printDBG('WRZUTA.getVideoLinks')
        videoUrls = self.up.getVideoLinkExt(cItem['url'])
        
        if 0 < len(videoUrls):
            max_bitrate = int(config.plugins.iptvplayer.wrzutaDefaultformat.value)
            def __getLinkQuality( itemLink ):
                try:
                    value = self.cm.ph.getSearchGroups(itemLink['name'], '[^0-9]([0-9]+?)p')[0]
                    return int(value)
                except Exception:
                    printExc()
                    return 0
            videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.wrzutaUseDF.value:
                videoUrls = [videoUrls[0]]      
        for idx in range(len(videoUrls)):
            videoUrls[idx]['need_resolve'] = 0
        return videoUrls
        
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
        elif category == 'music_cats':
            self.listMusicCategories(self.currItem, 'category')
    #CATEGORY
        elif category == 'category':
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
        CHostBase.__init__(self, Wrzuta(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('wrzutalogo.png')])
    
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
