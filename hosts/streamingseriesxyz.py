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
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.components.asynccall import iptv_execute
###################################################

###################################################
# FOREIGN import
###################################################
import time
import datetime
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'Streaming-Series.xyz'

class StreamingSeriesXYZ(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    MAIN_URL = 'http://streaming-series.xyz/'
    DEFAULT_ICON = 'http://www.streaming-series.xyz/wp-content/uploads/2015/04/logo.png'
    MAIN_CAT_TAB = [{'category':'list_items',      'title':_('Last added'),   'url':MAIN_URL, 'icon':DEFAULT_ICON},
                    {'category':'categories',      'title':_('Categories'),   'url':MAIN_URL, 'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'streaming-series.xyz', 'cookie':'streaming-series.xyz.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url, api=True):
        baseUrl = self.MAIN_URL
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  baseUrl + url
        if not baseUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("StreamingSeriesXYZ.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem, category):
        printDBG("StreamingSeriesXYZ.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="menu-categories"', '</ul>')[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'url':item[0], 'title':item[1]})
            self.addDir(params)
    
    def listItems(self, cItem, category):
        printDBG("StreamingSeriesXYZ.listItems")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '''rel=["']next["'][^>]+?href=['"]([^'^"]+?)['"]''')[0]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filmcontent">', '<div class="filmcontent">')[1]
        data = data.split('<div class="moviefilm">')
        if len(data): del data[0]
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            title = self.cleanHtmlStr(item)
            season = self.cm.ph.getSearchGroups(url, 'saison-([0-9]+?)-' )[0]
            params = dict(cItem)
            params.update({'category':category, 'url':url, 'title':title, 'icon':icon, 'season':season})
            self.addDir(params)
            
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'url':nextPage})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("StreamingSeriesXYZ.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        descData  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filmicerik">', '<h2 class="tags">')[1]
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(descData, 'Synopsis', '</p>')[1])
        icon = self.cm.ph.getSearchGroups(descData, '''src=['"]([^'^"]+?)['"]''')[0]
        titleSeason = cItem['title'].split('Saison')[0]
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Episodes', '</div>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'url':url, 'title':titleSeason + ' s%se%s' % (cItem['season'], title), 'icon':icon, 'desc':desc})
            self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("StreamingSeriesXYZ.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL + '?s=' + urllib.quote(searchPattern)
        self.listItems(cItem, 'episodes')
    
    def getLinksForVideo(self, cItem):
        printDBG("StreamingSeriesXYZ.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filmicerik">', '<div id="alt">')[1]
        data = data.split('</iframe>')
        if len(data): del data[-1]
        
        lang = ''
        for item in data:
            tmp = self.cm.ph.getDataBeetwenMarkers(item, '<span class="lg">', '</span>', False)[1].strip()
            if tmp != '': lang = tmp
            name = self.cm.ph.getDataBeetwenMarkers(item, '<b>', '</b>', False)[1]
            if lang != '':
                name = '%s: %s' % (lang, name)
            url  = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''')[0]
            if url.startswith('http'):
                urlTab.append({'name': name, 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("StreamingSeriesXYZ.getVideoLinks [%s]" % url)
        urlTab = []
        
        if 'protect-stream.com' not in url: return []
            
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return []
        
        k = self.cm.ph.getSearchGroups(data, 'var k[^"]*?=[^"]*?"([^"]+?)"')[0]
        
        try:
            sts, tmp = self.cm.getPage('http://www.protect-stream.com/secur2.js', self.defaultParams)
            count = self.cm.ph.getSearchGroups(tmp, 'var count = ([0-9]+?);')[0]
            if int(count) < 15:
                time.sleep(int(count))
        except Exception:
            printExc()
            return []
        
        header = dict(self.defaultParams['header'])
        params = dict(self.defaultParams)
        header['Referer'] = url
        header['Content-Type'] = "application/x-www-form-urlencoded"
        params['header'] = header
        
        sts, data = self.cm.getPage('http://www.protect-stream.com/secur2.php', params, {'k':k})
        if not sts: return []
        printDBG('==========================================')
        printDBG(data)
        printDBG('==========================================')
        videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''')[0]
        if not videoUrl.startswith('http'):
            videoUrl = self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"]([^'^"]+?)['"]''')[0]
        return self.up.getVideoLinkExt(videoUrl)
        
    def getArticleContent(self, cItem):
        printDBG("MoviesNight.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'resource_uri' not in cItem:
            return []
            
        if 0 == len(self.loginData['api_key']) and 0 == len(self.loginData['username']):
            self.requestLoginData()
        
        url = cItem['resource_uri']
        url += '?api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
        url = self._getFullUrl(url, False)
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        title = cItem['title']
        desc  = cItem.get('desc', '')
        icon  = cItem.get('icon', '')
        otherInfo = {}
        try:
            data = byteify(json.loads(data))
            icon = self._viaProxy( self._getFullUrl(data['poster'], False) )
            title = data['title']
            desc = data['overview']
            otherInfo['actors'] = data['actors']
            otherInfo['director'] = data['director']
            genres = []
            for item in data['genre']:
                genres.append(item['name'])
            otherInfo['genre'] = ', '.join(genres)
            otherInfo['rating']= data['imdb_rating']
            otherInfo['year']  = data['year']
            otherInfo['duration'] = str(datetime.timedelta(seconds=data['runtime']))
        except Exception:
            printExc()
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo}]
        
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
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'episodes')
        elif category == 'episodes':
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
        CHostBase.__init__(self, StreamingSeriesXYZ(), True, [])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('streamingseriesxyzlogo.png')])
    
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
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        
        hList = self.host.getArticleContent(cItem)
        if 0 == len(hList):
            return RetHost(retCode, value=retlist)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
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
