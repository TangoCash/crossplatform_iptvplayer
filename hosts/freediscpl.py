# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
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
    return 'http://freedisc.pl/'

class FreeDiscPL(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://freedisc.pl/'
    SEARCH_URL    = MAIN_URL + 'search/get'
    DEFAULT_ICON  = "http://i.imgur.com/mANjWqL.png"

    MAIN_CAT_TAB = [{'icon':DEFAULT_ICON, 'category':'list_filters',  'title': 'Najnowsze publiczne pliki użytkowników',  'url':MAIN_URL+'explore/start/get_tabs_pages_data/%s/newest/'},
                    {'icon':DEFAULT_ICON, 'category':'list_filters',  'title': 'Ostatnio przeglądane pliki',              'url':MAIN_URL+'explore/start/get_tabs_pages_data/%s/visited/'},
                    {'icon':DEFAULT_ICON, 'category':'search',        'title': _('Search'), 'search_item':True},
                    {'icon':DEFAULT_ICON, 'category':'search_history','title': _('Search history')} ]
    
    FILTERS_TAB = [{'title':_('Movies'),    'filter':'movies'},
                   {'title':_('Music'),     'filter':'music'}]
                   #{'title':_('Pictures'),  'filter':'pictures'} ]
    TYPES = {'movies':7, 'music':6}#, 'pictures':2}
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  FreeDiscPL.tv', 'cookie':'FreeDiscPL.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, url, params={}, post_data=None):
        return self.cm.getPage(url, params, post_data)
        
    def _getIconUrl(self, url):
        url = self._getFullUrl(url)
        return url
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif url.startswith('/'):
            url = self.MAIN_URL + url[1:]
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)
        return url
        
    def getDefaultIcon(self):
        return self.DEFAULT_ICON
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("FreeDiscPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listItems(self, cItem):
        printDBG("FreeDiscPL.listItems")
        filter = cItem.get('filter', '')
        type = self.TYPES.get(filter, -1)
        if type == -1: return
        
        page      = cItem.get('page', 0)
        url       = cItem['url'] % (type) + '{0}'.format(page)
        
        sts, data = self.getPage(url)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))['response']
            if 'visited' in url:
                data = data['html_visited']
            else:
                data = data['html_newest']
            splitMarker = "<div class='imageDisplay'>"
            data = data.split(splitMarker)
            if len(data): del data[0]
            for item in data:
                icon  = self.cm.ph.getSearchGroups(item, '''url\(['"]([^'^"]+?)['"]''')[0]
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                if url == '': continue
                title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
                
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':self._getIconUrl(icon), 'desc': self.cleanHtmlStr(item)})
                
                if 'file_icon_7' in item:
                    self.addVideo(params)
                elif 'file_icon_6' in item:
                    self.addAudio(params)
                #elif 'file_icon_2' in item:
                #    self.addPicture(params)
        except Exception:
            printExc()
        
        params = dict(cItem)
        params.update({'title':_('Next page'), 'page':page+1})
        self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("FreeDiscPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        tab = self.up.getVideoLinkExt(cItem['url'])
        for item in tab:
            item['need_resolve'] = 0
            urlTab.append(item)
        return urlTab
        
    def getResolvedURL(self, videoUrl):
        printDBG("FreeDiscPL.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FreeDiscPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        post_data = {"search_phrase":searchPattern,"search_type":searchType,"search_saved":0,"pages":0,"limit":0}
        params = dict(self.defaultParams)
        params['raw_post_data'] = True
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer']= 'http://freedisc.pl/search/%s/%s' % (searchType, urllib.quote(searchPattern))
        sts, data = self.getPage(self.SEARCH_URL, params, json.dumps(post_data))
        if not sts: return
        printDBG(data)
        
        try:
            data   = byteify(json.loads(data))['response']
            logins = data['logins_translated']
            data   = data['data_files']['data']
            for item in data:
                icon  = 'http://img.freedisc.pl/photo/%s/7/2/%s.png' % (item['id'], item['name_url'])
                url   = 'http://freedisc.pl/%s,f-%s,%s' % (logins[str(item['user_id'])]['url'], item['id'], item['name_url'])
                if url == '': continue
                title = item['name']
                desc = '| '.join( [item['date_add_format'], item['size_format']] )
                
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':self._getIconUrl(icon), 'desc':desc})
                
                type = item.get('type_fk', '')
                if '7' in type:
                    self.addVideo(params)
                elif '6' in type:
                    self.addAudio(params)
                #elif '2' in type:
                #    self.addPicture(params)
        except Exception:
            printExc()

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        filter   = self.currItem.get("filter", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_items'
            self.listsTab(self.FILTERS_TAB, cItem)
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
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, FreeDiscPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('freediscpllogo.png')])
    
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
        urlList = self.host.getResolvedURL(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Movies"), "movies"))
        searchTypesOptions.append((_("Music"), "music"))
    
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
        elif 'picture' == cItem['type']:
            type = CDisplayListItem.TYPE_PICTURE
        urlSeparateRequest = 1
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_PICTURE]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, cItem.get('need_resolve', 0)))
        if type == CDisplayListItem.TYPE_PICTURE:
            urlSeparateRequest = 0
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        if icon == '': icon = self.host.getDefaultIcon()
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = urlSeparateRequest,
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
