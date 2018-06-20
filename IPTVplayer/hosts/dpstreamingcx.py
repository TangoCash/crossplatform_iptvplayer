# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_execute
###################################################

###################################################
# FOREIGN import
###################################################
import time
import datetime
import re
import urllib
import urlparse
import base64
try:    import json
except Exception: import simplejson as json
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
    return 'https://streaming-series.watch/'

class StreamingSeriesWatch(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'dpstreaming.cx', 'cookie':'dpstreaming.cx.cookie'})
        
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.MAIN_URL = 'https://www.streaming-series.watch/'
        self.DEFAULT_ICON_URL = 'http://reviewme.co.za/wp-content/uploads/2013/06/lista_series_7327_622x.jpg'
        self.MAIN_CAT_TAB = [{'category':'list_items',      'title':'Nouveaux Films',   'url':self.getMainUrl()},
                             {'category':'sort',            'title':'Parcourir',        'url':self.getFullUrl('/parcourir/')},
                             {'category':'search',          'title': _('Search'), 'search_item':True },
                             {'category':'search_history',  'title': _('Search history'),            } ]
                        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
            
    def listSort(self, cItem, nextCategory):
        printDBG("StreamingSeriesWatch.listSort")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'dropdown'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'url':url, 'title':title})
            self.addDir(params)
    
    def listItems(self, cItem, category):
        printDBG("StreamingSeriesWatch.listItems")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>\s*Suivante''')[0])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'space'), ('<div', '>', 'clear'), False)[1]
        data = re.compile('''<div[^>]+?video[^>]+?>''').split(data)
        if len(data): del data[0]
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'title'), ('</div', '>'))[1])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            desc = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<div', '</div>')
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': desc.append(t)
            season = self.cm.ph.getSearchGroups(url, 'saison-([0-9]+?)-' )[0]
            params = dict(cItem)
            params.update({'good_for_fav': True, 'category':category, 'url':url, 'title':title, 'desc':'[/br]'.join(desc), 'icon':icon, 'season':season})
            self.addDir(params)
            
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'url':nextPage})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("StreamingSeriesWatch.listEpisodes")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        descData  = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'video-container'), ('<div', '>', 'clear'))[1]
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(descData, 'Synopsis', '</p>')[1])
        icon = self.cm.ph.getSearchGroups(descData, '''src=['"]([^'^"]+?)['"]''')[0]
        titleSeason = cItem['title'].split('Saison')[0]
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Episodes', '</div>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav': False, 'url':url, 'title':titleSeason + ' s%se%s' % (cItem['season'], title), 'icon':icon, 'desc':desc})
            self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("StreamingSeriesWatch.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL + '?s=' + urllib.quote(searchPattern)
        self.listItems(cItem, 'episodes')
    
    def getLinksForVideo(self, cItem):
        printDBG("StreamingSeriesWatch.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'video-container'), ('</div', '>'))[1]
        data = data.split('</iframe>')
        if len(data): del data[-1]
        
        lang = ''
        for item in data:
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', '"lg"'), ('</span', '>'), False)[1])
            if tmp != '': lang = tmp
            name = self.cm.ph.getDataBeetwenMarkers(item, '<b', '</b>', False)[1]
            if lang != '':
                name = '%s: %s' % (lang, name)
            url = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''')[0]
            if self.cm.isValidUrl(url):
                urlTab.append({'name': name, 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("StreamingSeriesWatch.getVideoLinks [%s]" % url)
        urlTab = []
        
        if 'protect-stream.com' not in url: return []
            
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return []
        
        k = self.cm.ph.getSearchGroups(data, 'var\s+?k[^"]*?=[^"]*?"([^"]+?)"')[0]
        secure = self.cm.ph.getSearchGroups(data, '''['"/](secur[^\.]*?)\.js''')[0]
        
        try:
            sts, tmp = self.getPage('https://www.protect-stream.com/%s.js' % secure, self.defaultParams)
            count = self.cm.ph.getSearchGroups(tmp, 'var\s+?count\s*?=\s*?([0-9]+?);')[0]
            if int(count) < 15:
                GetIPTVSleep().Sleep(int(count))
        except Exception:
            printExc()
            return []
        
        header = dict(self.defaultParams['header'])
        params = dict(self.defaultParams)
        header['Referer'] = url
        header['Content-Type'] = "application/x-www-form-urlencoded"
        header['Accept-Encoding'] = 'gzip, deflate'
        params['header'] = header
        params['use_cookie'] = False
        
        sts, data = self.getPage('https://www.protect-stream.com/%s.php' % secure, params, {'k':k})
        if not sts: return []
        printDBG('==========================================')
        printDBG(data)
        printDBG('==========================================')
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''')[0]
        if not self.cm.isValidUrl(videoUrl):
            videoUrl = self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"]([^'^"]+?)['"]''')[0]
        return self.up.getVideoLinkExt(videoUrl)
        
    def getFavouriteData(self, cItem):
        printDBG('StreamingSeriesWatch.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('StreamingSeriesWatch.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('StreamingSeriesWatch.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def getArticleContent(self, cItem):
        printDBG("MoviesNight.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'resource_uri' not in cItem:
            return []
            
        if 0 == len(self.loginData['api_key']) and 0 == len(self.loginData['username']):
            self.requestLoginData()
        
        url = cItem['resource_uri']
        url += '?api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
        url = self.getFullUrl(url)
        
        sts, data = self.getPage(url)
        if not sts: return []
        
        title = cItem['title']
        desc  = cItem.get('desc', '')
        icon  = cItem.get('icon', '')
        otherInfo = {}
        try:
            data = byteify(json.loads(data))
            icon = self._viaProxy( self.getFullUrl(data['poster']) )
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
        elif category == 'sort':
            self.listSort(self.currItem, 'list_items')
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
        CHostBase.__init__(self, StreamingSeriesWatch(), True, [])
