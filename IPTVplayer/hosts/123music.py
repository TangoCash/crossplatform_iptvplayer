# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import urllib
import string
import random
import base64
from urlparse import urlparse
from hashlib import md5
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
    return 'https://123music.to/'

class Music123(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'123music.to', 'cookie':'123musicto.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'https://123music.to/assets/images/logo.png'
        self.HEADER = {'User-Agent': 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = None
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheTopItems = {}
        
    def getPage(self, url, addParams = {}, post_data = None):
        return self.cm.getPage(url, addParams, post_data)
        
    def selectDomain(self):
        self.MAIN_URL = 'https://123music.to/'
        
        self.SEARCH_URL = self.MAIN_URL + 'search'
        
        self.MAIN_CAT_TAB = [{'category':'list_song_genres',      'title': _('Genres'),   'url':self.getMainUrl()                },
                             {'category':'list_albums_tab',       'title': _('Albums')                                           },
                             {'category':'list_artists_genres',   'title': _('Artists'),  'url':self.getFullUrl('/artists.html') },
                             {'category':'list_top_genres',       'title': _('Billboard'),'url':self.getMainUrl()                },
                             
                             {'category':'search',          'title': _('Search'), 'search_item':True},
                             {'category':'search_history',  'title': _('Search history'),           },
                            ]
        
        self.ALBUMS_TAB = [{'category':'list_albums_genres', 'title': _('LATEST ALBUMS'),  'url':self.getFullUrl('/albums.html')     },
                           {'category':'list_albums_genres', 'title': _('HOT ALBUMS'),     'url':self.getFullUrl('/albums/hot.html') },
                          ]
        
    def listGenres(self, cItem, nextCategory, m1, m2, addAll=False):
        printDBG("Music123.listGenres")
        
        if addAll:
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':_("--All--")})
            self.addDir(params)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
    
    def exploreArtistItem(self, cItem):
        printDBG("Music123.exploreArtistItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="artist-menu">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if '/songs.html' in url:
                nextCategory = 'list_songs_items'
            elif '/albums.html' in url:
                nextCategory = 'list_albums_items'
            else:
                continue
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def exploreTopItem(self, cItem, nextCategory):
        printDBG("Music123.exploreTopItem")
        
        self.cacheTopItems = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        
        filtersTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="mbb-tabs">', '</div>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        for item in tmp:
            title = self.cleanHtmlStr(item)
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url.startswith('#'):
                filtersTab.append({'title':title, 'f_key':url[1:]})
        
        printDBG(filtersTab)
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab-content">', 'list-->')[1]
        data = data.split('<div id="')
        if len(data): del data[0]
        
        for dataItem in data:
            filterItem = None
            for filter in filtersTab:
                if dataItem.startswith(filter['f_key']):
                    filterItem = filter
                    break
            if filterItem == None: continue
            
            itemsTab = []
            dataItem = self.cm.ph.getAllItemsBeetwenMarkers(dataItem, '<div class="item', '<div class="clearfix">')
            for item in dataItem:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(item.replace('<span class="singer">', ' - '))
                songId = self.cm.ph.getSearchGroups(item, '''data-song-id=['"]([^'^"]+?)['"]''')[0]
                icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                if icon == '': icon = cItem.get('icon', '')
                
                params = {'title':title, 'url':url, 'icon':icon}
                if songId != '':
                    params.update({'type':'audio', 'song_id':songId})
                elif '/album/' in url:
                    params.update({'category':'list_songs_items'})
                elif '/artist/' in url:
                    params.update({'category':'explore_artist'})
                else:
                    continue
                itemsTab.append(params)
             
            if len(itemsTab):
                self.cacheTopItems[filterItem['f_key']] = itemsTab
                params = dict(cItem)
                params.update(filterItem)
                params.update({'good_for_fav':False, 'category':nextCategory})
                self.addDir(params)
                
    def listTopItems(self, cItem):
        printDBG("Music123.listTopItems")
        key = cItem.get('f_key', '')
        tab = self.cacheTopItems.get(key, [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            if item.get('type', '') == 'audio':
                self.addAudio(params)
            else:
                self.addDir(params)
    
    def listItems(self, cItem, nextCategory='audio', m2='<div class="clearfix">'):
        printDBG("Music123.listItems")
        
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<li class="next">', '</li>')[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0])
        
        if nextCategory == 'audio':
            data = self.cm.ph.getDataBeetwenMarkers(data, 'song-cate-list', 'list-->')[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="item', 'list-->')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="item', m2)
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item.replace('<span class="singer">', ' - '))
            
            icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            if icon == '': icon = cItem.get('icon', '')
            
            params = dict(cItem)
            params.update({'good_for_fav':True,'title':title, 'url':url, 'icon':icon})
            if nextCategory == 'audio':
                songId = self.cm.ph.getSearchGroups(item, '''data-song-id=['"]([^'^"]+?)['"]''')[0]
                params.update({'song_id':songId})
                self.addAudio(params)
            else:
                params.update({'category':nextCategory})
                self.addDir(params)
        
        if nextPage != '':
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'url':nextPage, 'page':page+1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Music123.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        page = cItem.get('page', 1)
        if page == 1:
            cItem['url'] = self.SEARCH_URL + '/' + searchType + '/' + urllib.quote_plus(searchPattern) + '.html'
        
        if searchType == 'songs':
            nextCategory = 'audio'
        elif searchType == 'albums':
            nextCategory = 'list_songs_items'
        else:
            nextCategory = 'explore_artist'
            self.listItems(cItem, 'explore_artist', '</div>')
            return
        self.listItems(cItem, nextCategory)
        
    def getLinksForVideo(self, cItem):
        printDBG("Music123.getLinksForVideo [%s]" % cItem)
        urlTab = []
        songId = cItem.get('song_id', '')
        if songId != '':
            url = self.getFullUrl('/ajax/song/download/' + songId)
            sts, data = self.getPage(url)
            try:
                data = byteify(json.loads(data))['html']
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
                for item in data:
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    if not self.cm.isValidUrl(url): continue
                    name = self.cleanHtmlStr(item)
                    urlTab.append({'name':name, 'url':url, 'need_resolve':0})
            except Exception:
                printExc()
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("Music123.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("Music123.getArticleContent [%s]" % cItem)
        retTab = []
        
        url = self.getFullUrl('/ajax/song/sources/' + cItem.get('song_id', ''))
        sts, data = self.getPage(url)
        if not sts: return retTab
        
        title = ''
        desc  = ''
        icon  = ''
        try:
            data = byteify(json.loads(data))
            title = self.cleanHtmlStr(data['name'])
            desc  = self.cleanHtmlStr(data['lyrics'].replace('\n', '[/br]'))
        except Exception:
            printExc()
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return retTab
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', '')
        if icon == '':  icon = self.DEFAULT_ICON_URL
        
        otherInfo = {} #{'released':'2015'}
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('Music123.getFavouriteData')
        params = dict(cItem)
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('Music123.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('Music123.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        if self.MAIN_URL == None:
            #rm(self.COOKIE_FILE)
            self.selectDomain()

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #ALBUMS
        elif category == 'list_albums_tab':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_albums_genres'
            self.listsTab(self.ALBUMS_TAB, cItem)
        elif category == 'list_albums_genres':
            self.listGenres(self.currItem, 'list_albums_items', '<ul class="cfc-genre">', '</ul>', True)
        elif category == 'list_albums_items':
            self.listItems(self.currItem, 'list_songs_items')
    #ARTISTS
        elif category == 'list_artists_genres':
            self.listGenres(self.currItem, 'list_artists_items', '<div class="artist-letter">', '</div>')
        elif category == 'list_artists_items':
            self.listItems(self.currItem, 'explore_artist', '</div>')
        elif category == 'explore_artist':
            self.exploreArtistItem(self.currItem)
    #TOP
        elif category == 'list_top_genres':
            self.listGenres(self.currItem, 'explore_top', 'Billboard', '</ul>')
        elif category == 'explore_top':
            self.exploreTopItem(self.currItem, 'list_top_items')
        elif category == 'list_top_items':
            self.listTopItems(self.currItem)
    #SONGS
        elif category == 'list_song_genres':
            self.listGenres(self.currItem, 'list_songs_items', '<ul class="sub-menu">', '</ul>')
        elif category == 'list_songs_items':
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
        CHostBase.__init__(self, Music123(), True, [])
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Songs"),   "songs"))
        searchTypesOptions.append((_("Albums"), "albums"))
        searchTypesOptions.append((_("Artists"), "artists"))
        return searchTypesOptions
    
    def withArticleContent(self, cItem):
        if cItem['type'] != 'audio'  or '' == cItem.get('song_id', ''):
            return False
        return True
    