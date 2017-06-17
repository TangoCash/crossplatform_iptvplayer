# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.vevo import VevoIE
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Components.config import config, ConfigSelection, getConfigListEntry
###################################################


###################################################
# Config options for HOST
###################################################
   
def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Default video quality:"), config.plugins.iptvplayer.vevo_default_quality))
    optionList.append(getConfigListEntry(_("Use default video quality:"), config.plugins.iptvplayer.vevo_use_default_quality))
    optionList.append(getConfigListEntry(_("Allow hls format"), config.plugins.iptvplayer.vevo_allow_hls))
    return optionList
###################################################

def gettytul():
    return 'vevo.com'

class Vevo(CBaseHostClass):
    MAIN_URL     = 'http://www.vevo.com/'
    API2_URL     = 'https://apiv2.vevo.com/'
    PLAYLIST_URL = MAIN_URL + 'watch/playlist/'
    ARTIST_URL   = MAIN_URL + 'artist/'
    VIDEO_URL    = MAIN_URL + 'watch/'
    SEARCH_URL   = API2_URL + 'search?query={0}&sortBy=MostViewedLastMonth&videosLimit=18&skippedVideos=0&artistsLimit=6&includecategories='
    DEFAULT_LOGO = 'http://1.bp.blogspot.com/-pSTjDlSgahQ/VVsbLaM40NI/AAAAAAAAHvU/wr8F9v9gPoE/s1600/Vevo.png'

    BASE_IMAGE = MAIN_URL + 'public/images/'
    
    MAIN_CAT_TAB = [{'category':'apiv2',  'keys':['nowPosts'], 'url': API2_URL + 'now?size=20', 'title': _("Main"),     'icon':DEFAULT_LOGO},
                    {'category':'browse_videos',            'title': "Browse",     'icon':DEFAULT_LOGO},
                    {'category':'browse_artists',           'title': "Popular Artists",     'icon':DEFAULT_LOGO},
                    #{'category':'browse_shows',             'title': "Shows",     'icon':DEFAULT_LOGO},
                    {'category':'search',                   'title':_('Search'), 'search_item':True, 'icon':DEFAULT_LOGO},
                    {'category':'search_history',           'title':_('Search history'), 'icon':DEFAULT_LOGO} ]
                    
                    
    VIDEO_SORT_TAB = [ {'title':"Most Viewed Today",      'sort':"MostViewedLastDay"},
                       {'title':"Most Viewed This Week",  'sort':"MostViewedLastWeek"},
                       {'title':"Most Viewed This Month", 'sort':"MostViewedLastMonth"},
                       {'title':"Most Viewed All Time",   'sort':"MostViewedAllTime"},
                       {'title':"Recently Added",         'sort':"MostRecent"} ]
                       
    GROUP_TAB = [ {'title':"Videos",     'group':"videos"},
                  {'title':"Tour Dates", 'group':"tour"} ]

    
    def __init__(self):
        printDBG("Vevo.__init__")
        CBaseHostClass.__init__(self, {'history':'vevo.com', 'cookie':'vevocom.cookie'})
        self.vevoIE = None
        self.translations = {}
        self.webDataCache = []
        self.browseCategoryList = []
        self.cacheShows = []
        self.language = []
        
    def getStr(self, item, key):
        if key not in item: return ''
        if item[key] == None: return ''
        return str(item[key])
        
    def _getFullUrl(self, url):
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def apiv2PrepareUrl(self, url, page=None, session=None):
        oauth_token = ''
        #sts, data = self.cm.getPage('http://www.vevo.com/auth', {}, b'')
        #if sts:
        #    try: oauth_token = byteify(json.loads(data))['access_token']
        #    except Exception: printExc()
        sts, data = self.cm.getPage('http://www.vevo.com/')
        if sts:
            oauth_token = self.cm.ph.getSearchGroups(data, '''"access_token":"([^"]+?)"''')[0]
        
        if '?' in url:
            url += '&'
        else: url += '?'
        url += '&token=%s' % oauth_token
        if None != page:
            url += '&page=%s' % page
        if None != session:
            url += '&session=%s' % session
        return url

    def listsTab(self, tab, cItem, translate=True):
        printDBG("Vevo.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if translate:
                params['title'] = self.translations.get(params['title'], params['title'])
            self.addDir(params)
            
    def fillBrowse2(self):
        if self.translations == {} or self.webDataCache == []:
            sts, data = self.cm.getPage(self.MAIN_URL)
            if not sts: return
            
            data = self.cm.ph.getDataBeetwenMarkers(data, 'window.__INITIAL_STORE__ = ', '</script>', False)[1]
            try:
                data = byteify(json.loads(data.strip()[:-1]))
                language = list(data['default']['localeData'].keys())[0]
                self.language = language.split('-')
                self.translations = data['default']['localeData'][language]['translation']
                self.webDataCache = data
            except Exception:
                printExc()
                return
                
    def fillBrowse(self):
        if self.translations == {} or self.browseCategoryList == []:
            sts, data = self.cm.getPage(self.MAIN_URL + 'auth')
            if not sts: return
            translations = self.cm.ph.getDataBeetwenMarkers(data, 'translations:', 'config:', False)[1]
            translations = '{"translations":%s}' % translations.strip()[:-2]
            #printDBG(translations)
            browseCategoryList = self.cm.ph.getDataBeetwenMarkers(data, '"browseCategoryList":', ']', True)[1]
            browseCategoryList = '{%s}' % browseCategoryList
            self.language = self.cm.ph.getSearchGroups(data, 'language:[^"]*?"([^"]+?)"')[0].split('-')
            try:
                self.translations = byteify(json.loads(translations))['translations']
                self.browseCategoryList = byteify(json.loads(browseCategoryList))['browseCategoryList']
            except Exception:
                printExc()
                return
            
    def listBrowseCategory(self, cItem, category):
        printDBG("Vevo.listBrowseCategory")
        try:
            for item in self.browseCategoryList:
                params = dict(cItem)
                title = self.translations.get(item['loc'], item['loc'])
                params.update({'title':title, 'category':category, 'genre':item['id']})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listBrowseArtists(self, cItem):
        printDBG("Vevo.listBrowseArtists")
        url = self.API2_URL + 'artists?size=30&sort=MostViewedThisWeek'
        if cItem['genre'] != 'all':
            url += '&genre={0}'.format(cItem['genre'])
        cItem = dict(cItem)
        cItem.update({'url':url, 'keys':['artists']})
        self.listApiv2(cItem)
        
    def listBrowseShows(self, cItem, category):
        printDBG("Vevo.listBrowseShows")
        if [] == self.cacheShows:
            if 2 != len(self.language): return
            url = self.MAIN_URL + 'c/{0}/{1}/shows.json?platform=web'.format(self.language[0], self.language[1])
            sts, data = self.cm.getPage(url)
            if not sts: return
            try:
                data = byteify(json.loads(data))
                if data['success']:
                   self.cacheShows = data['result']
            except Exception:
                printExc()
                return
        
        for idx in range(len(self.cacheShows)):
            params = dict(cItem)
            item = self.cacheShows[idx]
            
            icon = item.get('header_image_url', '')
            if '' == icon: icon = item.get('mobile_image_url', '')
            if '' == icon: icon = item.get('thumbnail_image_url', '')
            
            if 1 <= len(item.get('seasons', [])):
                category = 'list_show_videos'
            params.update({'category':category, 'title':item['title'], 'icon':icon, 'desc':item['description'], 'show_id':idx, 'season_id':0})
            self.addDir(params)
            
    def listShowSeasons(self, cItem, category):
        printDBG("Vevo.listShowSeasons")
        show_id = cItem.get('show_id', 0)
        if show_id >= len(self.cacheShows): return
        for idx in range(len(self.cacheShows[show_id]["seasons"])):
            params = dict(cItem)
            item = self.cacheShows[show_id]["seasons"][idx]
            params.update({'category':category, 'title':item['title'], 'season_id':idx})
            self.addDir(params)
            
    def listShowVideos(self, cItem):
        printDBG("Vevo.listShowVideos")
        show_id = cItem.get('show_id', 0)
        if show_id >= len(self.cacheShows): return
        season_id = cItem.get('season_id', 0)
        if season_id >= len(self.cacheShows[show_id]["seasons"]): return
        
        for item in self.cacheShows[show_id]["seasons"][season_id]["episodes"]:
            params = dict(cItem)
            icon = item.get('header_image_url', '')
            if '' == icon: icon = item.get('mobile_image_url', '')
            if '' == icon: icon = item.get('thumbnail_image_url', '')
            if '' == icon: icon = cItem.get('icon', '')
            if None != item.get('isrc'):
                params.update({'title':item['title'], 'icon':icon, 'isrc':item['isrc']})
                self.addVideo(params)
                
            if None != item.get('playlist'):
                if '-' not in item['playlist']: # bug in VEVO?
                    params.update({'title':item['title'], 'icon':icon, 'isrc':item['playlist']})
                    self.addVideo(params)
                else:
                    params.update({'category':'playlist', 'title':item['title'], 'icon':icon, 'url':self.PLAYLIST_URL + item['playlist']})
                    self.addDir(params)
            
    def addVideoItem(self, cItem, item):
        params = dict(cItem)
        icon = self.getStr(item, 'image') 
        if '' == icon: icon = self.getStr(item, 'thumbnailUrl')
        if '' == icon: icon = cItem.get('icon', '')
        
        desc = item.get('description', '')
        if '' == desc: 
            desc = []
            if 'artistName' in item: desc.append( item['artistName'] )
            if 'duration' in item: desc.append( _('%ss') % item['duration'] )
            if 'viewCount' in item: desc.append( _('view count: %s') % item['viewCount'] )
            if 'copyright' in item: desc.append( item['copyright'] )
            desc = ', '.join(desc)
        params.update({'title':item['title'], 'icon':self.getFullUrl(icon), 'desc':desc, 'isrc':item['isrc']})
        self.addVideo(params)
        
    def addPlaylistItem(self, cItem, item):
        params = dict(cItem)
        try: icon = item['images'][0]['image']
        except Exception: icon = ''
        params.update({'category':'playlist', 'title':item['name'], 'icon':icon, 'desc':item['description'], 'url':self.PLAYLIST_URL + item['playlistId']})
        self.addDir(params)
        
    def addArtistItem(self, cItem, item):
        params = dict(cItem)
        try: icon = item['thumbnailUrl']
        except Exception: icon = ''
        params.update({'category':'artist', 'title':item['name'], 'icon':icon, 'desc':_('video count: %s') % item.get('totalVideos', ''), 'url': self.ARTIST_URL + item['urlSafeName']})
        self.addDir(params)
        
    def listApiv2(self, cItem):
        printDBG("Vevo.listVideos")
        page = cItem.get('page', 1)
        
        url = self.apiv2PrepareUrl(cItem['url'], page, cItem.get('session', None))
        sts, data = self.cm.getPage(url)
        if not url: return
        try:
            data = byteify(json.loads(data))
            for key in cItem['keys']:
                for item in data[key]:
                    if key == 'videos' or item.get('type') == 'video':
                        self.addVideoItem(cItem, item)
                    elif key == 'artists' or item.get('type') == 'artist':
                        self.addArtistItem(cItem, item)
                    elif item.get('type') == 'playlist':
                        self.addPlaylistItem(cItem, item)

            if page < data['paging']['pages']:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':page+1, 'session':data.get('session')})
                self.addDir(params)
        except Exception:
            printExc()
    
    def listVideosFromPage(self, cItem):
        printDBG("Vevo.listVideosFromPage")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('window\.__INITIAL_STORE__\s*=\s*'), re.compile('</script>'), False)[1]
        try:
            data = byteify(json.loads(data.strip()[:-1]))
            if cItem['category'] == 'artist':
                data = data['apollo']['data']
                for key in data.keys():
                    if key.endswith('.videos'):
                        tmp = data[key]['data']
                        for item in tmp:
                            videoKey = "$%s.basicMeta" % item['id']
                            self.addVideoItem(cItem, data[videoKey])
            elif cItem['category'] == 'playlist':
                playlistId = data['routing']['locationBeforeTransitions']['pathname'].split('/')[-1]
                data = data['apollo']['data']
                for key in data[playlistId].keys():
                    if key.startswith('videos('):
                        for item in data[data[playlistId][key]['id']]['items']:
                            videoKey = "$%s.basicMetaV3" % data[item['id']]['isrc']
                            if 1 == len(data[videoKey].get('artists', [])):
                                artistKey = '$%s.basicMeta' % data[videoKey]['artists'][0]['id']
                                data[videoKey]['title'] = data[artistKey]['name'] + ' ' + data[videoKey]['title']
                            self.addVideoItem(cItem, data[videoKey])
                        break
        except Exception:
            printExc()
        return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '"key"', ']}}', True)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '"videos":[', ']}}', False)[1]
        idx = data.find('],"paging"')
        if idx >= 0: data = data[:idx] 
        data = '{ "videos":[' + data + ']}'
        #printDBG(data)
        try:
            data = byteify(json.loads(data))
            for item in data['videos']:
                self.addVideoItem(cItem, item)
        except Exception:
            printExc()
        
    def listBrowseVideos(self, cItem):
        printDBG("Vevo.listBrowseVideos")
        url = self.API2_URL + 'videos?sort={0}'.format(cItem['sort'])
        if cItem['genre'] != 'all':
            url += '&genre={0}'.format(cItem['genre'])
        if 'tour' == cItem['group']:
            url += '&islive=true'
        cItem = dict(cItem)
        cItem.update({'url':url, 'keys':['videos']})
        self.listApiv2(cItem)
        
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Vevo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        url = self.SEARCH_URL.format(searchPattern)
        cItem = dict(cItem)
        cItem.update({'url':url, 'keys':['artists', 'videos']})
        self.listApiv2(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("Vevo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'isrc' in cItem:
            videoUrl = self.VIDEO_URL + cItem['isrc']
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            url = self.cm.ph.getSearchGroups(data, '''<link href=['"](http[^'^"]+?)['"]''')[0]
            if url != '': videoUrl = url
            
            urlTab = self.up.getVideoLinkExt( videoUrl )
            for idx in range(len(urlTab)):
                urlTab[idx]['need_resolve'] = 0
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['isrc']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'isrc':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Vevo.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        if self.vevoIE == None:
            self.vevoIE = VevoIE()
            self.fillBrowse()
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Vevo.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            self.listsTab(Vevo.MAIN_CAT_TAB, {'name':'category'})
    #APIV2
        elif 'apiv2' == category:
            self.listApiv2(self.currItem)
        elif category in ['playlist', 'artist']:
            self.listVideosFromPage(self.currItem)
    #BROWSE VIDEOS
        elif 'browse_videos' == category:
            self.listBrowseCategory(self.currItem, 'groups')
    #BROWSE ARTISTS
        elif 'browse_artists' == category:
            self.listBrowseCategory(self.currItem, 'list_artists')
        elif 'list_artists' == category:
            self.listBrowseArtists(self.currItem)
    #BROWSE SHOWS
        elif 'browse_shows' == category:
            self.listBrowseShows(self.currItem, 'list_show_seasons')
        elif 'list_show_seasons' == category:
            self.listShowSeasons(self.currItem, 'list_show_videos')
        elif 'list_show_videos' == category:
            self.listShowVideos(self.currItem)
    #GROUPS
        elif 'groups' == category:
            cItem = dict(self.currItem)
            cItem['category'] = 'sort'
            self.listsTab(Vevo.GROUP_TAB, cItem)
    #SORT
        elif 'sort' == category:
            cItem = dict(self.currItem)
            cItem['category'] = 'list_browse_videos'
            self.listsTab(Vevo.VIDEO_SORT_TAB, cItem)
    #LIST BROWSE VIDEOS
        elif 'list_browse_videos' == category:
            self.listBrowseVideos(self.currItem)
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)
        
        
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Vevo(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('vevologo.png')])
    
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
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
