# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import base64
try:    import json
except Exception: import simplejson as json
from random import randint
from datetime import datetime
from time import sleep
from copy import deepcopy
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
    return 'http://www.eskago.pl/'

class EskaGo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'eskaGO.pl', 'cookie':'eskagopl.cookie'})
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://www.eskago.pl/'
        self.MAIN_ESKAPL_URL = 'http://www.eska.pl/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'html/img/fb.jpg'
        
        self.MAIN_CAT_TAB = [{'category':'list_tv_items',           'title': 'TV',                       'url':self.getFullUrl('tv')      },
                             {'category':'list_radio_cats',         'title': 'Radio Eska Go',            'url':self.getFullUrl('radio')   },
                             {'category':'list_radio_eskapl',       'title': 'Radio Eska PL',            'url':self.MAIN_ESKAPL_URL,       'icon':self.MAIN_ESKAPL_URL + 'html/v6/images/logo_eska_pl.png'},
                             ]
                            # {'category':'search',                  'title': _('Search'),                'search_item':True,              },
                            # {'category':'search_history',          'title': _('Search history'),                                         } 
                            #]
        
        self.cacheItems = {}
        
    def listRadioCats(self, cItem, nextCategory):
        printDBG('listRadioCats')
        self.cacheItems = {}
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        ###########################
        listDataTab = self.cm.ph.getDataBeetwenMarkers(data, '<div class="channel-list-box"', '<script>', False)[1]
        listDataTab = listDataTab.split('<div class="channel-list-box"')
        for listData in listDataTab:
            listId = self.cm.ph.getSearchGroups(listData, '''channel\-list\-([^"^']+?)["']''')[0]
            self.cacheItems[listId] = []
            
            headMarker = '<div class="head-title">'
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(listData, headMarker, '</ul>')
            for tmp in tmpTab:
                desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(tmp, headMarker, '</div>', False)[1] )
                tmp  = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li>', '</li>')
                for item in tmp:
                    if 'play_icon' not in item: continue
                    url   = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    title = self.cleanHtmlStr(item)
                    self.cacheItems[listId].append({'good_for_fav':True, 'type':'audio', 'title':title, 'url':url, 'desc':desc})
        printDBG('#########################################')
        printDBG(self.cacheItems)
        printDBG('#########################################')
        ###########################
            
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="new-radio-box">', '<div class="row radio-list">', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        for item in tmp:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''color[^>]+?src=['"]([^'^"]+?)['"]''')[0] )
            if url != '#': url = self.getFullUrl(url)
            if self.cm.isValidUrl(url):
                title = url.split('/')[-1].replace('-', ' ').title()
                params = {'good_for_fav':True, 'title':title, 'url':url, 'icon':icon}
                self.addAudio(params)
            else:
                listId = self.cm.ph.getSearchGroups(item, '''data-list-id=['"]([^'^"]+?)['"]''')[0]
                if 0 == len(self.cacheItems.get(listId, [])): continue
                params = {'good_for_fav':False, 'category':nextCategory, 'title':self.cacheItems[listId][0]['desc'], 'url':listId, 'icon':icon}
                self.addDir(params)
                
    def listCacheItems(self, cItem):
        printDBG('listCacheItems')
        listId = cItem.get('url', '')
        tab = self.cacheItems.get(listId, [])
        
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.currList.append(params)
        
    def listTvItems(self, cItem):
        printDBG("EskaGo.listTvItems")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="tv-online">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon   = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip())
            title  = self.cleanHtmlStr(item)
            desc   = '' # ?? maybe EPG for channel
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addVideo(params)
            
    def listRadioEskaPL(self, cItem):
        printDBG("EskaGo.listRadioEskaPL")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="r_station_list">', '<script')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, '''data-link=['"]([^'^"]+?)['"]''')[0]
            if url == '': continue
            if not self.cm.isValidUrl(url):
                url = self.MAIN_ESKAPL_URL + url
            icon   = cItem.get('icon', '')
            title  = self.cleanHtmlStr(item)
            desc   = '' # ?? maybe EPG for channel
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EskaGo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        # TODO: implement me
    
    def getLinksForItem(self, cItem):
        printDBG("EskaGo.getLinksForItem [%s]" % cItem)
        urlTab = []
        
        url = cItem['url']
        
        if self.up.getDomain(self.MAIN_ESKAPL_URL , onlyDomain=True) in url:
            sts, data = self.cm.getPage(url, self.defaultParams)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="play_player">', '</div>')[1]
            url = self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]+?)['"]''')[0]
            if not self.cm.isValidUrl(url): return []
        
        sts, data = self.cm.getPage(url)
        if not sts: data = ''
        
        printDBG('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        
        if '/radio/' in  url:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'input[name="data-radio-url"]', ';', withMarkers=False)[1]
            url  =  self.cm.ph.getSearchGroups(tmp, '''(https?://[^'^"]+?)['"]''')[0]
            if url != '' and url.endswith('.pls'):
                sts, tmp = self.cm.getPage(url)
                if not sts: return []
                printDBG(tmp)
                tmp = tmp.split('File')
                if len(tmp): del tmp[0]
                for item in tmp:
                    printDBG('ITEM [%s]' % item)
                    url  = self.cm.ph.getSearchGroups(item, '''(https?://[^\s]+?)\s''')[0]
                    name = self.cm.ph.getSearchGroups(item, '''Title[^=]*?=([^\s]+?)\s''')[0].strip()
                    urlTab.append({'name':name, 'url':url})
            else:
                tmp1 = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
                for tmp in tmp1:
                    tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '{', '}')
                    for item in tmp:
                        if 'streamUrl' in item:
                            streamUrl  = self.cm.ph.getSearchGroups(item, '''streamUrl\s*=\s*['"](https?://[^'^"]+?)['"]''')[0]
                            streamType = self.cm.ph.getSearchGroups(item, '''streamType\s*=\s*['"]([^'^"]+?)['"]''')[0]
                            if 'aac' in streamType:
                                streamUrl = streamUrl.replace('.mp3', '.aac')
                            elif 'mp3' in streamType:
                                streamUrl = streamUrl.replace('.aac', '.mp3')
                            urlTab.append({'name':streamType, 'url':streamUrl})
                        
        elif '/tv/' in url or url.endswith('/player'):
            streamUriMap = {'eska-tv':['eskatv-t/eskatv_720p', 'eskatv-t/eskatv_360p'],
                            'polo-tv':['polotv-p/stream1'],
                            'eska-best-music-tv':['best-t/best_720p', 'best-t/best_360p'],
                            'eska-party-tv':['eska_party-t/eska_party_720p', 'eska_party-t/eska_party_360p'],
                            'music-vox-tv':['vox2-p/stream1'],
                            'vox-olds-cool-tv':['vox-t/vox_720p', 'vox-t/vox_360p'],
                            'eska-rock-tv':['eska_rock-t/eska_rock_720p', 'eska_rock-t/eska_rock_360p'],
                            'wawa-tv':['wawa-t/wawa_720p', 'wawa-t/wawa_360p'],
                            'polo-party-tv':['polo_party-t/polo_party_720p', 'polo_party-t/polo_party_360p'],
                            'player':['fokustv-p/stream1'],
                            'hip-hop-tv':['hiphoptv-p/stream1'],}
                            
            marker = cItem['url'].split('/')[-1]
            printDBG(">>>>>>>>>>>>>>> marker [%s]" % marker)
            tab = streamUriMap.get(marker, [])
            data = self.cm.ph.getDataBeetwenMarkers(data, '$.post(', 'function', withMarkers=False)[1]
            printDBG(data)
            secureUri =  self.cm.ph.getSearchGroups(data, '''(https?://[^'^"]+?)['"]''')[0]
            streamUri = self.cm.ph.getSearchGroups(data, '''streamUri['"\s]*?:\s*?['"]([^'^"]+?)['"]''')[0]
            
            if secureUri == '': secureUri = 'https://api.stream.smcdn.pl/api/secureToken.php'
            elif streamUri not in tab: tab.insert(0, streamUri)
            
            printDBG(">>>>>>>>>>>>>>> tab %s" % tab)
            for streamUri in tab:
                sts, url = self.cm.getPage(secureUri, post_data={'streamUri':streamUri})
                if not sts: continue
                
                printDBG('++++++++++++++++++++++++++')
                printDBG(url)
                printDBG('++++++++++++++++++++++++++')
                
                if self.cm.isValidUrl(url):
                    data = getDirectM3U8Playlist(url, checkExt=True, checkContent=True)
                    for item in data:
                        item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True})
                        urlTab.append(item)
                
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("EskaGo.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('EskaGo.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('EskaGo.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForItem(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('EskaGo.setInitListFromFavouriteItem')
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
        elif 'list_radio_cats' == category:
            self.listRadioCats(self.currItem, 'list_cache_items')
        elif 'list_cache_items' == category:
            self.listCacheItems(self.currItem)
        elif 'list_tv_items' == category:
            self.listTvItems(self.currItem)
        elif 'list_radio_eskapl' == category:
            self.listRadioEskaPL(self.currItem)
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
        CHostBase.__init__(self, EskaGo(), True, [])


