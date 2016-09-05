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
from Plugins.Extensions.IPTVPlayer.libs.moonwalkcc import MoonwalkParser
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
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
    return 'http://hdprofili.weebly.com/'

class HDProfili(CBaseHostClass):
    MAIN_URL   = 'http://hdprofili.weebly.com/'
    SEARCH_URL = MAIN_URL + 'index.php?q='
    DEFAULT_ICON_URL = 'http://hdprofili.weebly.com/uploads/3/0/9/8/30985093/1449164652.png'
    
    MAIN_CAT_TAB = [
                    {'category':'movie_cats',  'title': _('Movie'),                 'url':MAIN_URL+'filma-me-titra-shqip',                   'icon':DEFAULT_ICON_URL },
                    {'category':'list_items1', 'title': _('Animation [dubbing]'),   'url':MAIN_URL+'filma-te-dubluar-ne-shqip.html',         'icon':DEFAULT_ICON_URL },
                    {'category':'list_items3', 'title': _('Series [dubbing]'),      'url':MAIN_URL+'seriale-dubluar-ne-shqip.html',          'icon':DEFAULT_ICON_URL },
                    {'category':'list_items2', 'title': _('Animation [subtitles]'), 'url':MAIN_URL+'filma-te-animuar-me-titra-shqip.html',   'icon':DEFAULT_ICON_URL },
                    {'category':'list_items3', 'title': _('Series [subtitles]'),    'url':MAIN_URL+'seriale-te-animuar-me-titra-shqip.html', 'icon':DEFAULT_ICON_URL },
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'HDProfili', 'cookie':'HDProfili.cookie'})

    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('/'):
                url = url[1:]
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("HDProfili.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
    
    def listMainMenu(self):
        printDBG("HDProfili.listMainMenu")
        self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        
    def listCategories(self, cItem, category):
        printDBG("HDProfili.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<p class="blog-category-list">', '</p>', False)[1]
        data = re.compile('<a[^<]+?href="([^"]+?)"[^<]*?>([^<]+?)</a>').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'title':item[1], 'url':self._getFullUrl(item[0]), 'category':category})
            self.addDir(params)
            
    def listItems1(self, cItem):
        printDBG("HDProfili.listItems1")
        page = cItem.get('page', 1)
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPageUrl = self.cm.ph.getDataBeetwenMarkers(data, '<div class="blog-page-nav-previous">', '</div>', False)[1]
        nextPageUrl = self.cm.ph.getSearchGroups(nextPageUrl, '<a[^<]+?href="([^"]+?)"[^<]*?>')[0]
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="blog-header">', '</table>', False)
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cm.ph.getDataBeetwenMarkers(item, '<h2 class="blog-title">', '</h2>', False)[1]
            title = self.cleanHtmlStr( title )
            if title == '': continue
            icon  = self.cm.ph.getSearchGroups(item, '<img[^>]+?src="([^"]+?)"')[0]
            desc  = self.cm.ph.getDataBeetwenMarkers(item, '<span class="date-text">', '</span>', False)[1]
            params = dict(cItem)
            params.update({'title':title, 'icon':self._getFullUrl(icon), 'desc':self.cleanHtmlStr(desc), 'url':self._getFullUrl(url)})
            self.addVideo(params)
            
        if nextPageUrl != '':
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1, 'url':self._getFullUrl(nextPageUrl)})
            self.addDir(params)
            
    def listItems2(self, cItem, data=None, serTitle=''):
        printDBG("HDProfili.listItems2")
        if data == None:
            url = cItem['url']
            sts, data = self.cm.getPage(url)
            if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<div class='galleryInnerImageHolder'>", '</a>', True)
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)["']''')[0]
            title = self.cleanHtmlStr( item )
            if title == '': title = self.cm.ph.getSearchGroups(item, '''title=["']([^"^']+?)["']''')[0]
            if title == '': continue
            icon  = self.cm.ph.getSearchGroups(item, '''<img[^>]+?src=["']([^"^']+?)["']''')[0]
            desc  = ''
            params = dict(cItem)
            params.update({'title':serTitle+title, 'icon':self._getFullUrl(icon), 'desc':self.cleanHtmlStr(desc), 'url':self._getFullUrl(url)})
            self.addVideo(params)
        
    def listItems3(self, cItem):
        printDBG("HDProfili.listItems3")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        sp = '<h2 class="wsite-content-title" style="text-align:center;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '</script>', False)[1]
        data = data.split(sp)
        
        for serItem in data:
            serieTitle = self.cleanHtmlStr( serItem.split('</h2>')[0] )
            self.listItems2(cItem, serItem, serieTitle + ': ')
        
    def getLinksForVideo(self, cItem):
        printDBG("HDProfili.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'hdprofili.weebly.com' in cItem['url']:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return []
            playerUrlTab = re.compile('''<iframe[^>]+?src=["']([^"^']+?)["']''', re.IGNORECASE).findall(data)
            for url in playerUrlTab:
                if url.startswith('//'):
                    url = 'http:' + url
                if not url.startswith('http'): continue
                if 1 != self.up.checkHostSupport(url): continue
                urlTab.append({'name':self.up.getHostName(url), 'url':url, 'need_resolve':1})
        else:
            urlTab.append({'name':'main', 'url':cItem['url'], 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDProfili.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
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
            self.listMainMenu()
        elif category == 'movie_cats':
            self.listCategories(self.currItem, 'list_items1')
        elif category == 'list_items1':
            self.listItems1(self.currItem)
        elif category == 'list_items2':
            self.listItems2(self.currItem)
        elif category == 'list_items3':
            self.listItems3(self.currItem)
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, HDProfili(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('HDProfililogo.png')])
    
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
