# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
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
try:    import json
except Exception: import simplejson as json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.twitch_iconssize = ConfigSelection(default = "medium", choices = [ ("large", _("large")), ("medium", _("medium")), ("small", _("small")) ])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Device ID"), config.plugins.iptvplayer.Twitch_deviceid))
    return optionList
###################################################

def gettytul():
    return 'twitch.tv'

class Twitch(CBaseHostClass):
    NUM_OF_ITEMS = '20'
    MAIN_URL = 'https://api.twitch.tv/'
    MAIN_URLS = 'https://api.twitch.tv/'
    GAMES_URL = MAIN_URL + 'kraken/games/top?offset=0&on_site=1&limit=' + NUM_OF_ITEMS
    GAME_LIVE_CHANNELS_URL = MAIN_URL + 'kraken/streams?offset=0&game=%s&broadcaster_language=&on_site=1&limit=' + NUM_OF_ITEMS
    SEARCH_URL = MAIN_URL + 'kraken/search/%s?query=%s&type=suggest&offset=0&on_site=1&limit=' + NUM_OF_ITEMS
    
    CHANNEL_TOKEN_URL = MAIN_URLS + 'api/channels/%s/access_token'
    LIVE_URL = 'http://usher.justin.tv/api/channel/hls/%s.m3u8?token=%s&sig=%s&allow_source=true'
    
    VOD_TOKEN_URL = MAIN_URLS + 'api/vods/%s/access_token'
    VOD_URL = 'https://usher.ttvnw.net/vod/%s.m3u8?token=%s&sig=%s&allow_source=true'
    
    VIDEOS_CATS_URL = MAIN_URL + 'kraken/videos/top?offset=0&game=%s&period=%s&on_site=1&limit=' + NUM_OF_ITEMS
    
    MAIN_CAT_TAB = [{'category':'games',          'title':_('Games'), 'url': GAMES_URL},
                    {'category':'channels',       'title':_('Channels'), },
                    {'category':'videos_period',  'title':_('Videos')},
                    {'category':'games',          'title':_('Promoted games'), 'url': MAIN_URL+'kraken/games/featured?offset=0&platform=android&on_site=1&limit='+ NUM_OF_ITEMS},
                    {'category':'streams',        'title':_('Promoted channels'), 'url': MAIN_URL+'kraken/streams/featured?offset=0&on_site=1&limit='+ NUM_OF_ITEMS},
                    {'category':'search',         'title':_('Search'), 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
    GAME_CAT_TAB = [{'category':'streams',        'title':_('Live Channels')},
                    {'category':'videos_period',  'title':_('Videos')} ]
    VIDEOS_PERIOD_TAB = [{'category':'videos', 'title':_('Week'),     'period':'week'},
                         {'category':'videos', 'title':_('Month'),    'period':'month'} ]
    
     
    
    def __init__(self):
        printDBG("Twitch.__init__")
        CBaseHostClass.__init__(self, {'history':'Twitch.tv'})
        self.cm.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Client-ID':'jzkbprff40iqj646a697cyrvl0zt2m6'}
        self.DEFAULT_ICON_URL = 'http://s.jtvnw.net/jtv_user_pictures/hosted_images/GlitchIcon_WhiteonPurple.png'
    
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def _getStr(self, v, default=''):
        return clean_html(self._encodeStr(v, default))
        
    def _encodeStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        else: return default
        
    def _getNum(self, v, default=0):
        try: return int(v)
        except Exception:
            try: return float(v)
            except Exception: return default
            
    def _checkNexPage(self, url, key):
        if 'limit=' not in url: return False
        try:
            url = re.sub('(limit=[0-9]*?)[^0-9]', '', url)
            sts, data = self.cm.getPage(url)
            data = json.loads(data)
            if len(data[key]): return True
        except Exception:
            printExc()
        return False
            
    def listChannelCategories(self, cItem, category):
        printDBG("Twitch.listChannelCategories")
        
        params = dict(cItem)
        params.update({'category':category, 'title':_('Random'), 'url':self.MAIN_URL+'kraken/beta/streams/random?offset=0&on_site=1&limit='+self.NUM_OF_ITEMS})
        self.addDir(params)
        
        baseChannelUrl = self.MAIN_URL+'kraken/streams?offset=0&broadcaster_language=%s&sce_platform=%s&on_site=1&limit='+ self.NUM_OF_ITEMS
        tmpTab = [(_('Top'), '', '')]
        
        userLang = GetDefaultLang()
        promoteItem = None
        # list language
        sts, data = self.cm.getPage('https://www.twitch.tv/directory/all')
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'header_language_dropmenu', '</div>', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True, caseSensitive=False)
            for item in data:
                title = self.cleanHtmlStr(item)
                lang  = self.cm.ph.getDataBeetwenMarkers(item, 'setByAsyncPut(', ')', False)[1].replace('"', '').replace("'", '')
                if lang != '':
                    if lang != userLang:
                        tmpTab.append((title, lang, ''))
                    else:
                        promoteItem = (title, lang, '')
                
        if promoteItem != None:
            tmpTab.insert(1, promoteItem)
                
        for item in tmpTab:
            params = dict(cItem)
            params.update({'category':category, 'title':item[0], 'url':baseChannelUrl % (item[1], item[2])})
            self.addDir(params)
            
    def listGames(self, cItem, category):
        printDBG("Twitch.listGames")
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            try:
                data = json.loads(data)
                if 'featured' in data:
                    main_key = 'featured'
                else:
                    main_key = 'top'
                for item in data[main_key]:
                    params = dict(cItem)
                    if 'viewers' in item and 'channels' in item:
                        desc  = _('%s viewers, %s channels') % (item['viewers'], item['channels'])
                    else: desc = ''
                    item  = item['game']
                    icon  = config.plugins.iptvplayer.twitch_iconssize.value
                    params.update({'title':self._getStr(item['name']), 'url':'', 'game':self._getStr(item['name']), 'category':self._getStr(category), 'desc':self._getStr(desc), 'icon':self._getStr(item['box'][icon])})
                    self.addDir(params)
                if len(data[main_key]):
                    nextPage = data['_links']['next']
                    params = dict(cItem)
                    params.update({'title':_('Next page'), 'url':nextPage+'&on_site=1', 'desc':''})
                    self.addDir(params)
            except Exception: printExc()
            
    def listSearchGames(self, cItem, category):
        printDBG("Twitch.listSearchGames")
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            try:
                data = json.loads(data)
                for item in data['games']:
                    params = dict(cItem)
                    desc  = ''
                    icon  = config.plugins.iptvplayer.twitch_iconssize.value
                    params.update({'title':self._getStr(item['name']), 'url':'', 'game':self._getStr(item['name']), 'category':category, 'desc':self._getStr(desc), 'icon':self._getStr(item['box'][icon])})
                    self.addDir(params)
                
                nextPage = data['_links']['next']+'&on_site=1'
                if self._checkNexPage(nextPage, 'games'):
                    params = dict(cItem)
                    params.update({'title':_('Next page'), 'url':nextPage, 'desc':''})
                    self.addDir(params)
            except Exception: printExc()
            
    def listLiveChannels(self, cItem):
        printDBG("Twitch.listLiveChannels")
        url = cItem['url']
        if '' == url:
            if 'game' in cItem:
                url = Twitch.GAME_LIVE_CHANNELS_URL % urllib.quote_plus(cItem['game'])
        if '' != url:
            sts, data = self.cm.getPage(url)
            if sts:
                try:
                    data = json.loads(data)
                    if 'featured' in data:
                        main_key = 'featured'
                    else:
                        main_key = 'streams'
                    for item in data[main_key]:
                        if 'featured' == main_key: item = item["stream"]
                        icon = item['preview'][config.plugins.iptvplayer.twitch_iconssize.value]
                        item  = item['channel']
                        title = '%s, %s, %s' % (item['display_name'], item.get('game', ''), item.get('broadcaster_language', ''))
                        desc  = item.get('status', '')
                        params = {'title':self._getStr(title), 'url':'', 'channel':self._getStr(item['name']), 'desc':self._getStr(desc), 'icon':self._getStr(icon) }
                        self.addVideo(params)
                    nextPage = data['_links']['next']+'&on_site=1'
                    if self._checkNexPage(nextPage, main_key):
                        params = dict(cItem)
                        params.update({'title':_('Next page'), 'url':nextPage, 'desc':''})
                        self.addDir(params)
                except Exception: printExc()
                
    def listsVideos(self, cItem):
        printDBG("Twitch.listsVideos")
        url = Twitch.VIDEOS_CATS_URL % (urllib.quote_plus(cItem.get('game', '')), cItem['period'])
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json.loads(data)
                for item in data['videos']:
                    params = dict(cItem)
                    desc  = item.get('recorded_at', '') + ', ' + item.get('description', '')
                    icon  = item.get('preview', '')
                    params.update({'title':self._getStr(item['title']), 'url':'', 'vod_id': self._getStr(item['_id']), 'desc':self._getStr(desc), 'icon':self._getStr(icon)})
                    self.addVideo(params)                
                nextPage = data['_links']['next']+'&on_site=1'
                if self._checkNexPage(nextPage, 'videos'):
                    params = dict(cItem)
                    params.update({'title':_('Next page'), 'url':nextPage, 'desc':''})
                    self.addDir(params)
            except Exception: printExc()

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Twitch.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        url = Twitch.SEARCH_URL % (searchType, searchPattern)
        item = dict(cItem)
        item['url'] = url
        if 'streams' == searchType:
            item['category'] = 'streams'
            self.listLiveChannels(item)
        elif 'games' == searchType:
            item['category'] = 'search_games'
            self.listSearchGames(item, 'game')
    
    def getLinksForVideo(self, cItem):
        printDBG("Twitch.getLinksForVideo [%s]" % cItem)
        urlTab = []
        if 'vod_id' in cItem:
            id = cItem['vod_id'][1:]
            tokenUrl = Twitch.VOD_TOKEN_URL
            vidUrl   = Twitch.VOD_URL
            liveStream = False
        elif 'channel' in cItem:
            id = cItem['channel']
            tokenUrl = Twitch.CHANNEL_TOKEN_URL
            vidUrl   = Twitch.LIVE_URL
            liveStream = True
        
        if id != '':
            url = tokenUrl % id
            sts, data = self.cm.getPage(url)
            if sts:
                try:
                    data = json.loads(data)
                    url =  vidUrl % (id, urllib.quote(self._getStr(data['token'])), self._getStr(data['sig']))
                    data = getDirectM3U8Playlist(url, checkExt=False)
                    for item in data:
                        item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':liveStream})
                        urlTab.append(item)
                except Exception: printExc()
        elif '' != cItem['url']:
            urlTab.append({'name':cItem['title'], 'url':cItem['url']})
    
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Twitch.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Twitch.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(Twitch.MAIN_CAT_TAB, {'name':'category'})
    #GAMES
        elif 'games' == category:
            self.listGames(self.currItem, 'game')
        elif 'search_games' == category:
            self.listSearchGames(self.currItem, 'game')
    #GAME
        elif 'game' == category:
            self.listsTab(Twitch.GAME_CAT_TAB, self.currItem)
    #CHANNELS CAT
        elif 'channels' == category:
            self.listChannelCategories(self.currItem, 'streams')
    #LIVE CHANNELS
        elif 'streams' == category:
            self.listLiveChannels(self.currItem)
    #VIDEOS PERIOD
        elif 'videos_period' == category:
            self.listsTab(Twitch.VIDEOS_PERIOD_TAB, self.currItem)
    #VIDEOS CATS
        elif 'videos' == category:
            self.listsVideos(self.currItem)
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
        CHostBase.__init__(self, Twitch(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('twitchtvlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen <= Index or Index < 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host._getStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Games"), "games"))
        searchTypesOptions.append((_("Channles"), "streams"))
    
        for cItem in cList:
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
                
            title       =  self.host._getStr( cItem.get('title', '') )
            description =  self.host._getStr( cItem.get('desc', '') ).strip()
            icon        =  self.host._getStr( cItem.get('icon', '') )
            if '' == icon:
                icon = self.host.DEFAULT_ICON_URL
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList
