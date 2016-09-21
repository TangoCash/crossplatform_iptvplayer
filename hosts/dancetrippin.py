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
from hashlib import md5
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
###################################################)

def GetConfigList():
    optionList = []
    return optionList
def gettytul():
    return 'http://dancetrippin.tv/'

class DancetrippinTV(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'DancetrippinTV.tv', 'cookie':'kinomantv.cookie', 'cookie_type':'MozillaCookieJar'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL = "http://www.dancetrippin.tv/"
        self.DEFAULT_ICON_URL = 'https://frenezy.files.wordpress.com/2010/10/dancetrippin.jpg'
        
        self.MAIN_CAT_TAB = [{'category':'latest',             'title': _('Latest'),   'icon':self.DEFAULT_ICON_URL, 'url':self.MAIN_URL},
                             {'category':'videos',             'title': _('Videos'),    'icon':self.DEFAULT_ICON_URL},
                             {'category':'artists',            'title': _('Artists'),   'icon':self.DEFAULT_ICON_URL, 'url':self.MAIN_URL+'artists'},
                             {'category':'playlists',          'title': _('Playlists'), 'icon':self.DEFAULT_ICON_URL, 'url':self.MAIN_URL+'playlists'}]
        
        
        self.VIDEOS_TAB = [{'category':'list_videos',          'title': _('DJ SETS'),   'url':self.MAIN_URL+'ajax.cfm?datatype=videos&cat=-12&templatetype=grid'},
                           {'category':'list_videos',          'title': _('MORE VIDS'), 'url':self.MAIN_URL+'ajax.cfm?datatype=videos&cat=12&templatetype=grid'}]
    
    def listsVideos(self, cItem):
        printDBG("DancetrippinTV.listsVideos")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data:
                url   = self.getFullUrl( item['videourl'] )
                icon  = self.getFullUrl( item['image'] )
                title = self.cleanHtmlStr( item['title'] )
                descTab = []
                for descItem in ['date', 'genre', 'event', 'location']:
                    if descItem in item:
                        descTab.append(item[descItem])
                desc = '| '.join(descTab)
                params = dict(cItem)
                params.update({'url':url, 'title':title, 'icon':icon, 'desc':desc, 'good_for_fav':True})
                self.addVideo(params)
        except:
            printExc()
            
    def listVideos2(self, cItem):
        printDBG("DancetrippinTV.listVideos2")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="grid-content">', '<footer> ', False)[1]
        data = data.split('<div class="single"')
        if len(data): del data[0]
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''url\(([^\(]+?)\)''')[0].replace('"', '').replace("'", "") )
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            params = dict(cItem)
            params.update({'url':url, 'title':title, 'icon':icon, 'good_for_fav':True})
            self.addVideo(params)
            
    def listLatests(self, cItem):
        printDBG("DancetrippinTV.listLatests")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="single videos"', '<div class="gradient">', True)
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''url\(([^\(]+?)\)''')[0].replace('"', '').replace("'", "") )
            title = self.cleanHtmlStr( item )
            params = dict(cItem)
            params.update({'url':url, 'title':title, 'icon':icon, 'good_for_fav':True})
            self.addVideo(params)
    
    def listArtists(self, cItem, nextCategory):
        printDBG("DancetrippinTV.listArtists")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="grid-content">', '<div class="show-more show-all">', False)[1]
        data = data.split('div class="single artist"')
        if len(data): del data[0]
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''url\(([^\(]+?)\)''')[0].replace('"', '').replace("'", "") )
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            params = dict(cItem)
            params.update({'category':nextCategory, 'url':url, 'title':title, 'icon':icon, 'good_for_fav':True})
            self.addDir(params)
            
    def listPlaylists(self, cItem, nextCategory):
        printDBG("DancetrippinTV.listPlaylists")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<h2 class="playlistheader"', '</h2>', True)
        for item in data:
            url    = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            if 'user/playlists' in url: continue
            title  = self.cleanHtmlStr( item )
            params = dict(cItem)
            params.update({'category':nextCategory, 'url':url, 'title':title, 'good_for_fav':True})
            self.addDir(params)
    
    def getLinksForVideo(self, cItem, forEpisodes=False):
        printDBG("DancetrippinTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video ', '</video>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>')
        for item in data:
            if 'video/mp4' not in item: continue 
            name = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0]
            url  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            urlTab.append({'name':name, 'url':self.getFullUrl(url), 'need_resolve':0})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("DancetrippinTV.getVideoLinks [%s]" % videoUrl)
        urlTab = []
            
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('DancetrippinTV.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem.get('desc', ''), 'icon':cItem.get('desc', '')}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('DancetrippinTV.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('DancetrippinTV.setInitListFromFavouriteItem')
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

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'videos':
            self.listsTab(self.VIDEOS_TAB, self.currItem)
        elif category == 'list_videos':
            self.listsVideos(self.currItem)
        elif category == 'artists':
            self.listArtists(self.currItem, 'list_videos2')
        elif category == 'playlists':
            self.listPlaylists(self.currItem, 'list_videos2')
        elif category == 'list_videos2':
            self.listVideos2(self.currItem)
        elif category == 'latest':
            self.listLatests(self.currItem)
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, DancetrippinTV(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]
    
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
        searchTypesOptions.append((_("Movies"),   "movie"))
        searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
        isGoodForFavourites = cItem.get('good_for_fav', False)
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem

