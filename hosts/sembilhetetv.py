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
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.sembilhetetv_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.sembilhetetv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login"), config.plugins.iptvplayer.sembilhetetv_login))
    optionList.append(getConfigListEntry(_("password"), config.plugins.iptvplayer.sembilhetetv_password))
    return optionList
###################################################


def gettytul():
    return 'SemBilhete.tv'

class SemBilheteTV(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    LIMIT = 13
    MAIN_URL = 'http://sembilhete.tv/'
    API_URL = MAIN_URL + 'api/v1/'
    DEFAULT_ICON = 'http://kodiportugal.pt/wp-content/uploads/2016/01/icon-4-150x150.png'
    MAIN_CAT_TAB = [{'category':'movies',          'title':_('Movies'),   'url':MAIN_URL+'index.php/listing', 'icon':DEFAULT_ICON},
                    {'category':'series',          'title':_('TV series'), 'url':MAIN_URL+'index.php/listing', 'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]

    ORDER_BY_TAB = [{'category':'list_movies',     'title':_('--All--') },
                    {'category':'list_movies',     'title':_('Newest added'), 'order_by':'newest-added' },
                    {'category':'list_movies',     'title':_('Oldest added'), 'order_by':'oldest-added' },
                    {'category':'list_movies',     'title':_('Newest year'),  'order_by':'newest-year' },
                    {'category':'list_movies',     'title':_('Oldest year'),  'order_by':'oldest-year' },
                    {'category':'list_movies',     'title':_('Best rating'),  'order_by':'best-rating' },
                    {'category':'list_movies',     'title':_('Worse rating'), 'order_by':'worse-rating' },
                    {'category':'list_movies',     'title':_('Most viewed'),  'order_by':'most-viewed' },
                    {'category':'list_movies',     'title':_('Less viewed'),  'order_by':'less-viewed' }]

 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SemBilheteTV.com', 'cookie':'veetlecom.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.loginData = {"api_key": "", "username":""}
        self.cache = {}
        
    def _getFullUrl(self, url, api=True):
        if str(url) == 'None':
            return ''
        if api:
            baseUrl = self.API_URL
        else:
            baseUrl = self.MAIN_URL
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  baseUrl + url
        if not baseUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def _viaProxy(self, url):
        if url.startswith('http'):
            baseProxy = 'http://www.proxy-german.de/'
            proxy = baseProxy + 'index.php?q={0}&hl=240'.format(urllib.quote_plus(url))
            return strwithmeta(proxy, {'Referer':baseProxy, 'Cookie':'flags=240'})
        else:
            return ''
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("SemBilheteTV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
    
    def listItems(self, cItem, key='movie', category=None):
        printDBG("SemBilheteTV.listItems")
        if 'next' in cItem:
            url = cItem['next']
            url = self._getFullUrl(url, False)
        else:
            url = key + '/?'
            if 'query' in cItem:
                url += 'query=%s&' % cItem['query']
            url += 'limit=%s' % self.LIMIT
            if 'order_by' in cItem:
                url += '&order_by=%s' % cItem['order_by']
            url += '&api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
            url = self._getFullUrl(url)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        next = ''
        try:
            data = byteify(json.loads(data))
            for item in data['objects']:
                params = dict(cItem)
                icon = self._viaProxy( self._getFullUrl(item['poster'], False) )
                title = self.cleanHtmlStr(item['title'])
                
                if 'date' in item:
                    date = item['date']
                elif 'year' in item:
                    date = item['year']
                else:
                    date = item['start_year'] + '-' + item['end_year']
                desc = '%s | %s' % (date, item['imdb_rating'])
                params.update({'title':title, 'desc':desc, 'icon':icon, 'imdb_id':item['imdb_id'], 'resource_uri':item['resource_uri']})
                type = item.get('type', key)
                if type == 'movie':
                    self.addVideo(params)
                else:
                    params.update({'category':category})
                    self.addDir(params)
            
            if len(data['meta']['next']):
                params = dict(cItem)
                params.update({'title':_("Next page"), 'next':str(data['meta']['next'])})
                self.addDir(params)
        except Exception:
            printExc()
        
    def listSeasons(self, cItem, category):
        printDBG("SemBilheteTV.listSeasons")
        url = 'serie/%s/?' % cItem.get('imdb_id', '')
        url += '&api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
        url = self._getFullUrl(url)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            icon = self._viaProxy( self._getFullUrl(data['poster'], False) )
            desc = data['overview']
            imdbID = data['imdb_id']
            for item in data['seasons']:
                params = dict(cItem)
                title = _('Season') + ' %s' % item['season_number']
                params.update({'category':category, 'serie_title':cItem['title'], 'title':title, 'season': item['season_number'], 'desc':desc, 'icon':icon, 'imdb_id':imdbID, 'resource_uri':item['resource_uri']})
                self.addDir(params)
        except Exception:
            printExc()
        
    def listEpisodes(self, cItem):
        printDBG("SemBilheteTV.listEpisodes")
        url = 'serie/{0}/season/{1}/?'.format(cItem.get('imdb_id', ''), cItem.get('season', 1))
        url += '&api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
        url = self._getFullUrl(url)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data['episodes']:
                params = dict(cItem)
                title = '%s s%se%s %s' % (cItem['serie_title'], cItem['season'], item['episode_number'], item['name'] )
                icon = self._getFullUrl(str(item['still']), False)
                if icon.startswith('http'):
                    icon = self._viaProxy( icon )
                else:
                    icon = cItem['icon']
                imdbID = item['imdb_id']
                desc = '%s | %s |[/br]%s' % (item['air_date'], item['imdb_rating'], item['overview'])
                params.update({'title':title, 'desc':desc, 'icon':icon, 'imdb_id':imdbID})
                self.addVideo(params)
        except Exception:
            printExc()
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SemBilheteTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['query'] = urllib.quote(searchPattern)
        self.listItems(cItem, 'search', 'seasons')
    
    def getLinksForVideo(self, cItem):
        printDBG("SemBilheteTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        if 0 == len(self.loginData['api_key']) and 0 == len(self.loginData['username']):
            self.requestLoginData()
        
        if 'imdb_id' in cItem:
            url = 'content/request/%s/?api_key=%s&username=%s' % (cItem['imdb_id'], self.loginData['api_key'], self.loginData['username'])
            url = self._getFullUrl(url)
            sts, data = self.cm.getPage(url)
            if not sts: return []
            try:
                printDBG(data)
                data = byteify(json.loads(data))
                linkVideo = data['url']
                if not linkVideo.startswith('http'):
                    SetIPTVPlayerLastHostError(self.cleanHtmlStr(url))
                    return []
                subTracks = []
                for track in data.get('subtitles', []):
                    subUrl = self._getFullUrl(track['url'], False)
                    subLang = track['language']
                    subTracks.append({'title':subLang, 'url':subUrl, 'lang':subLang, 'format':'srt'})
                
                urlTab.append({'name': 'main', 'url':urlparser.decorateUrl(linkVideo, {'external_sub_tracks':subTracks}), 'need_resolve':1})
            except Exception:
                printExc()
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("SemBilheteTV.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = strwithmeta(baseUrl)
        if url.startswith('http'): 
            subTracks = url.meta.get('external_sub_tracks', [])
            tmp = self.up.getVideoLinkExt(url)
            if len(subTracks):
                for item in tmp:
                    item['url'] = urlparser.decorateUrl(item['url'], {'external_sub_tracks':subTracks})
                    urlTab.append(item)
            else:
                urlTab = tmp
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['imdb_id']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'imdb_id':fav_data})
        
    def getArticleContent(self, cItem):
        printDBG("SemBilheteTV.getArticleContent [%s]" % cItem)
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
        
    def requestLoginData(self):
        login    = config.plugins.iptvplayer.sembilhetetv_login.value
        password = config.plugins.iptvplayer.sembilhetetv_password.value
        url      = "login/?login=%s&password=%s" % (urllib.quote(login), urllib.quote(password))
        
        sts = False
        if '' == login.strip() or '' == password.strip():
            self.sessionEx.open(MessageBox, _('This host requires registration. \nPlease fill your login and password in the host configuration. Available under blue button.'), type = MessageBox.TYPE_ERROR, timeout = 10 )
        else:
            sts, data = self.cm.getPage(self._getFullUrl(url))
            try:
                data = byteify(json.loads(data))
                self.loginData.update(data)
                sts = True
            except Exception:
                sts = False
            if not sts or 0 == len(self.loginData['api_key']) or 0 == len(self.loginData['username']):
                sts = False
            if not sts:
                self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
        return sts
        
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
            if not self.requestLoginData(): return
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'movies':
            self.listsTab(self.ORDER_BY_TAB, self.currItem)
        elif category == 'list_movies':
            self.listItems(self.currItem)
        elif category == 'series':
            self.listItems(self.currItem, 'serie', 'seasons')
        elif category == 'seasons':
            self.listSeasons(self.currItem, 'episodes')
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
        CHostBase.__init__(self, SemBilheteTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('sembilhetetvlogo.png')])
    
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
