# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetDefaultLang, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
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
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'pl.wwe.com'

class PLWWECOM(CBaseHostClass):
    HTTP_HEADER= {  'User-Agent'  : 'Mozilla/5.0' }
    MAIN_URL    = 'http://pl.wwe.com/'
    BASE_URL    = MAIN_URL +'_hn:component-rendering%7C'
    SEARCH_URL  = MAIN_URL + '?q='
    LOGO_URL    = 'http://pl.wwe.com/img/xwweLogo.pl.png.pagespeed.ic.YaFxrVdW4A.png'
    MAIN_CAT_TAB = [{'category':'vid_pho',    'title': 'Główna',          'base':'r31_r1_r2_r3', 'url':BASE_URL+'{base}?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                    {'category':'list_cats',  'title': 'Filmy',           'base':'r41_r1_r2_r1', 'url':BASE_URL+'{base}/{ltype}{cat}?{base}:offset={page}&{base}', 'ltype':'videos', 'icon':LOGO_URL},
                    {'category':'list_cats',  'title': 'Zdjęcia',         'base':'r29_r1_r2_r1', 'url':BASE_URL+'{base}/{ltype}{cat}?{base}:offset={page}&{base}', 'ltype':'photos', 'icon':LOGO_URL},
                    {'category':'vid_pho',    'title': 'Raw',             'base':'r28_r1_r2_r3', 'url':BASE_URL+'{base}/broadcasts/raw?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                    {'category':'vid_pho',    'title': 'SmackDown',       'base':'r28_r1_r2_r3', 'url':BASE_URL+'{base}/broadcasts/smackdown?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                    {'category':'vid_pho',    'title': 'WWE Main Event',  'base':'r28_r1_r2_r3', 'url':BASE_URL+'{base}/broadcasts/wwe_main_event?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                    {'category':'vid_pho',    'title': 'WWE NXT',         'base':'r28_r1_r2_r3', 'url':BASE_URL+'{base}/broadcasts/wwe_nxt?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                    {'category':'vid_pho',    'title': 'Total Divas',     'base':'r28_r1_r2_r3', 'url':BASE_URL+'{base}/broadcasts/total_divas?{base}:offset={page}&{base}:type={ltype}&{base}', 'icon':LOGO_URL},
                   ]
    #{'category':'search',                          'title': _('Search'), 'search_item':True, 'icon':LOGO_URL},
    #{'category':'search_history',                  'title': _('Search history'), 'icon':LOGO_URL}
    
    VIDEO_PHOTO_TAB = [{'category':'list_items', 'title':'Filmy',   'ltype':'videos'},
                       {'category':'list_items', 'title':'Zdjęcia', 'ltype':'photos'}]
                       
    CATS_TAB = [{'category':'list_items', 'title':'Wszystkie',   'cat':''},
                {'category':'list_items', 'title':'Raw',         'cat':'/raw'},
                {'category':'list_items', 'title':'SmackDown',   'cat':'/smackdown'},
                {'category':'list_items', 'title':'Main Event',  'cat':'/wwe_main_event'},
                {'category':'list_items', 'title':'NXT',         'cat':'/wwe_nxt'},
                {'category':'list_items', 'title':'PPV',         'cat':'/ppv'},
                {'category':'list_items', 'title':'Total Divas', 'cat':'/total_divas'},
                {'category':'list_items', 'title':'Extra',       'cat':'/extra'}]
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'PLWWECOM', 'cookie':'PLWWECOM.cookie'})
        self.countryCode = ''
        self.proxy_gateway = 'http://darmowe-proxy.pl/browse.php?u={0}&b=28&f=norefer'
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
    
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("PLWWECOM.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def addNextPage(self, cItem, nextPage, page):
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':str(int(cItem.get('page', '0'))+page)})
            self.addDir(params)
    
    def listItems(self, cItem, category):
        printDBG("PLWWECOM.listItems [%s]" % cItem)
        url = cItem['url']
        for item in ['base', 'cat', 'ltype', 'page']:
            url = url.replace('{%s}' % item, cItem.get(item, ''))
        url += ':dataOnly=true'
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        type = cItem['ltype']
        if type == 'photos':
            type = 'picture'
        else: 
            type = 'video'
        data = data.split('<li class="%s">' % type)
        if len(data): del data[0]
        
        offset = 0
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon  = self.cm.ph.getSearchGroups(item, 'itemprop="url" content="([^"]+?\.jpg)"')[0]
            title = self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1]
            
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon)})
            if type == 'video':
                self.addVideo(params)
            else:
                params['category'] = category
                self.addDir(params)
            offset += 1
        self.addNextPage(cItem, offset, offset)
        
    def listPcturesItems(self, cItem):
        printDBG("PLWWECOM.listPcturesItems [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = re.compile('<meta[^>]+?content="(http[^"]+?\.jpg)"').findall(data)
        nr = 1
        for item in data:
            title = '%d. %s' % (nr, cItem['title'])
            url   = item
            icon  = item
            self.addPicture({'title':title, 'url':url, 'icon':icon})
            nr += 1
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("PLWWECOM.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = self.SEARCH_URL + urllib.quote(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = url
        self.listItems(cItem, 'list_episodes')
        
    def getLinksForVideo(self, cItem):
        printDBG("PLWWECOM.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if '' == self.countryCode:
            self.countryCode = self.cm.getCountryCode()
            
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        if 'pl' != self.countryCode:
            HTTP_HEADER['Referer'] = self.proxy_gateway
            params =  {'header' : HTTP_HEADER, 'proxy_gateway':self.proxy_gateway}
        else:
            params =  {}
            
        sts, data = self.cm.getPage(cItem['url'], params)
        if not sts: return urlTab
        
        hlsUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?\.m3u8[^'^"]*?)['"]''')[0].replace('\\/', '/')
        if hlsUrl.startswith('//'):
            hlsUrl = 'http:' + hlsUrl
        if self.cm.isValidUrl(hlsUrl):
            return getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=False)
        
        baseUrl     = 'http://c.brightcove.com/services/viewer/htmlFederated?playerID={0}&playerKey={1}&purl={2}&%40videoPlayer={3}&flashID={4}'
        data        = self.cm.ph.getDataBeetwenMarkers(data, '<object id=', '</object>', True)[1]
        playerID    = self.cm.ph.getSearchGroups(data, ' name="playerID"[^>]+?value="([^"]+?)"')[0]
        playerKey   = self.cm.ph.getSearchGroups(data, ' name="playerKey"[^>]+?value="([^"]+?)"')[0]
        videoPlayer = self.cm.ph.getSearchGroups(data, ' name="@videoPlayer"[^>]+?value="([^"]+?)"')[0]
        flashID     = self.cm.ph.getSearchGroups(data, ' id="([^"]+?)"')[0]
        url = baseUrl.format(playerID, playerKey, urllib.quote(cItem['url']), videoPlayer, flashID)
        
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        if 'pl' != self.countryCode:
            HTTP_HEADER['Referer'] = self.proxy_gateway
            params =  {'header' : HTTP_HEADER, 'proxy_gateway':self.proxy_gateway}
        else:
            params =  {}
            
        sts, data = self.cm.getPage(url, params)
        if not sts: return urlTab
        data = self.cm.ph.getDataBeetwenMarkers(data, 'var experienceJSON = {', '};', False)[1]
        data = '{%s}' % data
        try:
            data = byteify(json.loads(data))
            if data['success']:
                for item in data['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']:
                    item['need_resolve'] = 0
                    item['name'] = '%sx%s' % (item['frameWidth'], item['frameHeight'])
                    item['url']  = item['defaultURL']
                    urlTab.append(item)
        except Exception:
            printExc()
            
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG("NaszeKino.getFavouriteData")
        data = {'url':cItem['url'], 'type':cItem['type']}
        try:
            data = json.dumps(data).encode('utf-8')
        except Exception:
            printExc()
            data = ''
        return data
        
    def getLinksForFavourite(self, fav_data):
        printDBG("NaszeKino.getLinksForFavourite")
        try:
            cItem = byteify(json.loads(fav_data))
            if cItem['type'] == 'picture':
                return[{'name':'url', 'url':cItem['url'], 'need_resolve':0}]
        except Exception:
            printExc()
            return []
        return self.getLinksForVideo(cItem)
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #SELECT VIDEO OR PTHOTO
        elif category == 'vid_pho':
            self.listsTab(self.VIDEO_PHOTO_TAB, self.currItem)
    #LIST CATS  
        elif category == 'list_cats':
            self.listsTab(self.CATS_TAB, self.currItem)
    #LIST ITEMS
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_pictures')
    #LIST PICTURES
        elif category == 'list_pictures':
            self.listPcturesItems(self.currItem)
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
        CHostBase.__init__(self, PLWWECOM(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_PICTURE])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('plwwecomlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item.get('need_resolve', False)))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
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
