# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import datetime, timedelta
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
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.zdfmediathek_iconssize = ConfigSelection(default = "medium", choices = [ ("large", _("large")), ("medium", _("medium")), ("small", _("small")) ])
config.plugins.iptvplayer.zdfmediathek_prefformat = ConfigSelection(default = "mp4,m3u8", choices = [\
("mp4,m3u8", "mp4,m3u8"),("m3u8,mp4", "m3u8,mp4")])
config.plugins.iptvplayer.zdfmediathek_prefquality = ConfigSelection(default = "4", choices = [("0", _("low")), ("1", _("medium")), ("2", _("high")), ("3", _("very high")), ("4", _("hd"))])
config.plugins.iptvplayer.zdfmediathek_prefmoreimportant = ConfigSelection(default = "quality", choices = [("quality", _("quality")), ("format", _("format"))])
config.plugins.iptvplayer.zdfmediathek_onelinkmode = ConfigYesNo(default=True)


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Icons size"), config.plugins.iptvplayer.zdfmediathek_iconssize))
    optionList.append(getConfigListEntry(_("Prefered format"), config.plugins.iptvplayer.zdfmediathek_prefformat))
    optionList.append(getConfigListEntry(_("Prefered quality"), config.plugins.iptvplayer.zdfmediathek_prefquality))
    optionList.append(getConfigListEntry(_("More important"), config.plugins.iptvplayer.zdfmediathek_prefmoreimportant))
    optionList.append(getConfigListEntry(_("One link mode"), config.plugins.iptvplayer.zdfmediathek_onelinkmode))
    return optionList
###################################################

def gettytul():
    return 'ZDFmediathek'

class ZDFmediathek(CBaseHostClass):
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache'} )
    
    DEFAULT_ICON = 'http://www.zdf.de/ZDFmediathek/img/fallback/236x133.jpg'
    MAIN_URL     = 'https://www.zdf.de/'
    MAIN_API_URL = 'https://zdf-cdn.live.cellular.de/'
    ZDF_API_URL  = 'https://api.zdf.de/'
    DOCUMENT_API_URL            = MAIN_API_URL + 'mediathekV2/document/%s'
    BROADSCAST_MISSED_API_URL   = MAIN_API_URL + 'mediathekV2/broadcast-missed/%s'
    LIVE_TV_API_URL             = MAIN_API_URL + 'mediathekV2/live-tv/%s"'
    BRANDS_ALPHABETICAL_API_URL = MAIN_API_URL + 'mediathekV2/brands-alphabetical'
    TYPEAHEAD_API_URL           = MAIN_API_URL + 'mediathekV2/search/typeahead?q=%s&context=%s'
    SEARCH_API_URL              = MAIN_API_URL + 'mediathekV2/search?q=%s&contentTypes=%s'
    START_PAGE_API_URL          = MAIN_API_URL + 'mediathekV2/start-page'
    IMPRINT_PAGE_API_URL        = MAIN_API_URL + 'mediathekV2/page/imprint'
    CONTACT_PAGE_API_URL        = MAIN_API_URL + 'mediathekV2/page/contact'
    PRIVACY_PAGE_API_URL        = MAIN_API_URL + 'mediathekV2/page/privacy'
    CATEGORIES_PAGE_API_URL     = MAIN_API_URL + 'mediathekV2/categories'
    MYZDF_API_URL               = MAIN_API_URL + 'mediathekV2/user/my-zdf'
    CLIP_GROUP_API_URL          = MAIN_API_URL + 'mediathek/champions-league/match/%s/clip-group/%s'
    LOGIN_URL                   = ZDF_API_URL  + 'identity/login'
    LOGIN_FACEBOOK_URL          = ZDF_API_URL  + 'identity/thirdparty/facebook/login'
    LOGIN_GOOGLE_URL            = ZDF_API_URL  + 'identity/thirdparty/google/login'
    REGISTER_URL                = MAIN_URL     + 'mein-zdf#start'
    SUBSCRIPTIONS_API_URL       = MAIN_API_URL + 'mediathekV2/user/subscriptions'
    PUSH_SUBSCRIBE_URL           = 'http://push.live.cellular.de/api/device/'
    BOOKMARKS_API_URL           = MAIN_API_URL + 'mediathekV2/user/bookmarks'
    AUTH_TOKEN_API_URL          = MAIN_API_URL + 'mediathekV2/token'
    AKAMAI_TOKEN_API_URL        = 'https://tg2cl15.zdf.de/generate'
    
    MAIN_CAT_TAB = [{'category':'list_start',      'title':_('Home page'), 'url': START_PAGE_API_URL},
                    {'category':'missed_date',     'title':_('Missed the show?')},
                    {'category':'list_cluster',    'title':_('Program A-Z'), 'simplify':False, 'url': BRANDS_ALPHABETICAL_API_URL},
                    {'category':'list_cluster',    'title':_('Categories'), 'url': CATEGORIES_PAGE_API_URL},
                    #{'category':'themen',         'title':_('Topics'), 'url': NEWS_API_URL},
                    {'category':'search',          'title':_('Search'), 'search_item':True},
                    {'category':'search_history',  'title':_('Search history')} ]
                       
    QUALITY_MAP = {'hd':4, 'veryhigh':3, 'high':2, 'med':1, 'low':0 }
    
    def __init__(self):
        printDBG("ZDFmediathek.__init__")
        CBaseHostClass.__init__(self, {'history':'ZDFmediathek.tv', 'cookie':'zdfde.cookie'})
        self.DEFAULT_ICON_URL = 'http://www.supportnet.de/articleimage/2384046/01-ZDF-Mediathek-App-Startbildschirm-200.png'
    
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= dict(self.HEADER)
        params.update({'header':HTTP_HEADER})
        
        if 'zdf-cdn.live.cellular.de' in url:
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e1'.format(urllib.quote(url, ''))
            params['header']['Referer'] = proxy
            #params['header']['Cookie'] = 'flags=2e5;'
            url = proxy
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and None == data:
            sts = False
        if sts and 'Duze obciazenie!' in data:
            SetIPTVPlayerLastHostError(self.cleanHtmlStr(data))
        return sts, data
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if  'zdf-cdn.live.cellular.de' in url:
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e1'.format(urllib.quote(url, ''))
            params = {}
            params['User-Agent'] = self.HEADER['User-Agent'],
            params['Referer'] = proxy
            params['Cookie'] = 'flags=2e5;'
            url = strwithmeta(proxy, params) 
        elif url.startswith('https://'):
            url = 'http' + url[5:]
            
        return url
        
    def getFullUrl(self, url):
        if 'proxy-german.de' in url:
            url = urllib.unquote( self.cm.ph.getSearchGroups(url+'&', '''\?q=(http[^&]+?)&''')[0] )
        return CBaseHostClass.getFullUrl(self, url)
        
    def _getNum(self, v, default=0):
        try: return int(v)
        except Exception:
            try: return float(v)
            except Exception: return default
            
    def _getList(self, data, key, default=[]):
        try: 
            if isinstance(data[key], list):
                return data[key]
        except Exception:
            printExc()
        return default
            
    def _getIcon(self, iconsItem):
        iconssize = config.plugins.iptvplayer.zdfmediathek_iconssize.value
        iconsTab = []
        for item in iconsItem.keys():
            item = iconsItem[item]
            if "/assets/" in item["url"]:
                iconsTab.append({'size':item["width"], 'url':item["url"]})
        idx = len(iconsTab)
        if idx:
            iconsTab.sort(key=lambda k: k['size'])
            if 'large' == iconssize:    idx -= 1
            elif 'medium' == iconssize: idx /=  2
            elif 'small' == iconssize:  idx = 0
            return iconsTab[idx]['url']
        return ''
        
    def listStart(self, cItem):
        printDBG('listStart')
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data['stage']:
                self._addItem(cItem, item)
            self._listCluster(cItem, data['cluster'])
        except Exception:
            printExc()
        
    def listSendungverpasst(self, cItem):
        printDBG('listSendungverpasst')
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        try:
            data = byteify(json.loads(data)['broadcastCluster'])
            self._listCluster(cItem, data)
        except Exception:
            printExc()
        
    def listCluster(self, cItem):
        printDBG('listCluster')
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        try:
            data = byteify(json.loads(data)['cluster'])
            self._listCluster(cItem, data)
        except Exception:
            printExc()
    
    def _listCluster(self, cItem, data):
        for item in data:
            
            if 'teaser' in item['type']:
                tab = self._getList(item, 'teaser')
                if 0 == len(tab): continue
                if 1 == len(tab) and cItem.get('simplify', True):
                    self._addItem(cItem, tab[0])
                    continue
                title = self.cleanHtmlStr(item['type'])
                if 'name' in item: title = self.cleanHtmlStr(item['name'])
                elif 'teaserLivevideo' == item['type']: title = _('Live')
                params = dict(cItem)
                params.update({'category':'list_content', 'title':title, 'content':tab})
                self.addDir(params)
                
    def listContent(self, cItem):
        printDBG('listCluster')
        contentTab = cItem.get('content', [])
        for item in contentTab:
            self._addItem(cItem, item)
        
    def _addItem(self, cItem, item):
        printDBG('_addItem')
        try:
            icon = self._getIcon(item.get("teaserBild", {}))
            if icon == '': icon = cItem['icon']
            title = self.cleanHtmlStr(item["titel"])
            if item['type'] in ['brand', 'category']:
                descTab = []
                descTab.append(self.cleanHtmlStr(item['headline']))
                descTab.append(self.cleanHtmlStr(item['channel']))
                descTab.append(self.cleanHtmlStr(item['beschreibung']))
                params = {'name':'category', 'category':'list_cluster', 'title':title, 'url':self.getFullUrl(item['url']), 'desc':' | '.join(descTab), 'icon':self.getIconUrl(icon), 'id':item['id'], 'sharing_url':item['sharingUrl'], 'good_for_fav': True}
                self.addDir(params)
            elif item['type'] in ["video", "livevideo"]:    
                descTab = []
                descTab.append(self.cleanHtmlStr(item['headline']))
                descTab.append(self.cleanHtmlStr(item['channel']))
                if 'length' in item: descTab.append(str(timedelta(seconds=int(item["length"]))))
                descTab.append(self.cleanHtmlStr(item['beschreibung']))
                params = {'title':title, 'url':self.getFullUrl(item['url']), 'desc':'| '.join(descTab), 'icon':self.getIconUrl(icon), 'id':item['id'], 'sharing_url':item['sharingUrl'], 'good_for_fav': True}
                self.addVideo(params)
        except Exception:
            printExc()
    
    def listMissedDate(self, cItem):
        printDBG("listMissedDate")
        # convert to timestamp
        now = int(time.time())
        for item in range(7):
            date =  datetime.fromtimestamp(now - item * 24 * 3600).strftime('%Y-%m-%d')
            params = dict(cItem)
            params.update({'category':'list_missed', 'title':date, 'url':self.BROADSCAST_MISSED_API_URL % date})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("ZDFmediathek.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 0)
        if page == 0:
            url = self.SEARCH_API_URL % (searchPattern, 'episode')
        else:
            url = cItem['url']
        
        sts, data = self.getPage(url)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data['results']:
                self._addItem(cItem, item)
            if data['nextPage']:
                params = dict(cItem)
                params.update({'title':_('Next page'), 'url':self.getFullUrl(data['nextPageUrl']), 'page':page+1})
                self.addDir(params)
        except Exception:
            printExc()
    
    def getLinksForVideo(self, cItem):
        printDBG("ZDFmediathek.getLinksForVideo id[%s]" % cItem['id'])
        
        sts, data = self.getPage(self.DOCUMENT_API_URL % cItem['id'])
        if not sts: return []
        
        preferedQuality = int(config.plugins.iptvplayer.zdfmediathek_prefquality.value)
        preferedFormat  = config.plugins.iptvplayer.zdfmediathek_prefformat.value
        tmp = preferedFormat.split(',')
        formatMap = {}
        for i in range(len(tmp)):
            formatMap[tmp[i]] = i
        
        try:
            urlTab = []
            tmpUrlTab = []
            data = byteify(json.loads(data)['document'])
            live = data['type']
            try:
                data = data['formitaeten']
                for item in data:
                    quality = item['quality']
                    url = item['url']
                    if url.startswith('https://'):
                        url = 'http' + url[5:]
                    for type in [{'pattern':'http_m3u8_http', 'name':'m3u8'}, {'pattern':'mp4_http', 'name':'mp4'}]:
                        if type['pattern'] not in item['type']: continue
                        if type['name'] == 'mp4':
                            if item['hd']:
                                quality = 'hd'
                            qualityVal = ZDFmediathek.QUALITY_MAP.get(quality, 10)
                            qualityPref = abs(qualityVal - preferedQuality)
                            formatPref  = formatMap.get(type['name'], 10)
                            tmpUrlTab.append({'url':url, 'quality_name':quality, 'quality':qualityVal, 'quality_pref':qualityPref, 'format_name':type['name'], 'format_pref':formatPref})
                        elif type['name'] == 'm3u8':
                            tmpList = getDirectM3U8Playlist(url, checkExt=False)
                            for tmpItem in tmpList:
                                res = tmpItem['with']
                                if res == 0: continue
                                if res > 300: quality = 'low'
                                if res > 600: quality = 'med'
                                if res > 800: quality = 'high'
                                if res > 1000: quality = 'veryhigh'
                                if res > 1200: quality = 'hd'
                                qualityVal = ZDFmediathek.QUALITY_MAP.get(quality, 10)
                                qualityPref = abs(qualityVal - preferedQuality)
                                formatPref  = formatMap.get(type['name'], 10)
                                tmpUrlTab.append({'url':tmpItem['url'], 'quality_name':quality, 'quality':qualityVal, 'quality_pref':qualityPref, 'format_name':type['name'], 'format_pref':formatPref})
            except Exception:
                printExc()
            def _cmpLinks(it1, it2):
                prefmoreimportantly = config.plugins.iptvplayer.zdfmediathek_prefmoreimportant.value
                if 'quality' == prefmoreimportantly:
                    if it1['quality_pref'] < it2['quality_pref'] :   return -1
                    elif it1['quality_pref']  > it2['quality_pref'] : return 1
                    else:
                        if it1['quality'] < it2['quality'] :   return -1
                        elif it1['quality']  > it2['quality'] : return 1
                        else:
                            if it1['format_pref'] < it2['format_pref'] :   return -1
                            elif it1['format_pref']  > it2['format_pref'] : return 1
                            else: return 0
                else:
                    if it1['format_pref'] < it2['format_pref'] :   return -1
                    elif it1['format_pref']  > it2['format_pref'] : return 1
                    else:
                        if it1['quality_pref'] < it2['quality_pref'] :   return -1
                        elif it1['quality_pref']  > it2['quality_pref'] : return 1
                        else:
                            if it1['quality'] < it2['quality'] :   return -1
                            elif it1['quality']  > it2['quality'] : return 1
                            else: return 0
            tmpUrlTab.sort(_cmpLinks)
            onelinkmode = config.plugins.iptvplayer.zdfmediathek_onelinkmode.value
            for item in tmpUrlTab:
                url = item['url']
                name = item['quality_name'] + ' ' + item['format_name']
                if '' != url:
                    if 'live' in str(live):
                        live = True
                    else: 
                        live = False
                    urlTab.append({'need_resolve':0, 'name':name, 'url':self.up.decorateUrl(url, {'iptv_livestream':live})})
                    if onelinkmode: break
            printDBG(tmpUrlTab)
        except Exception:
            printExc()
            
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('ZDFmediathek.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "ZDFmediathek.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(ZDFmediathek.MAIN_CAT_TAB, {'name':'category'})
        elif 'list_start' == category:
            self.listStart(self.currItem)
        elif 'missed_date' == category:
            self.listMissedDate(self.currItem)
        elif 'list_missed' == category:
            self.listSendungverpasst(self.currItem)
        elif 'list_cluster' == category:
            self.listCluster(self.currItem)
        elif 'list_content' == category:
            self.listContent(self.currItem)
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category', 'category':'search_next_page'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, ZDFmediathek(), True)

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
        isGoodForFavourites = cItem.get('good_for_fav', False)
        if icon == '': icon = self.host.DEFAULT_ICON_URL
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem
