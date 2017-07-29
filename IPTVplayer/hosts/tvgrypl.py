# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import urlparse
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
config.plugins.iptvplayer.tvgrypl_default_quality = ConfigSelection(default = "SD", choices = [("MOB", "MOB: niska"),("SD", "SD: standardowa"),("HD", "HD: wysoka")]) #, ("FHD", "FHD: bardzo wysoka")
config.plugins.iptvplayer.tvgrypl_use_dq          = ConfigYesNo(default = True)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Domyślna jakość wideo:"), config.plugins.iptvplayer.tvgrypl_default_quality))
    optionList.append(getConfigListEntry(_("Używaj domyślnej jakości wideo:"), config.plugins.iptvplayer.tvgrypl_use_dq))
    return optionList
###################################################

def gettytul():
    return 'tvgry.pl'

class TvGryPL(CBaseHostClass):

    def __init__(self):
        printDBG("TvGryPL.__init__")
        CBaseHostClass.__init__(self, {'history':'TvGryPL.tv'})
        self.DEFAULT_ICON_URL = 'http://www.gry-online.pl/apple-touch-icon-120x120.png'
        self.MAIN_URL = 'http://tvgry.pl/'
        self.SEARCH_URL = self.getFullUrl('wyszukiwanie.asp')
        self.MAIN_CAT_TAB = [{'category':'list_tabs',          'title':'Materiały',            'url': self.getFullUrl('/wideo-tvgry.asp')},
                             {'category':'list_items',         'title':'Tematy',               'url': self.getFullUrl('/tematy.asp')},
                             {'category':'list_tabs',          'title':'Zwiastuny gier',       'url': self.getFullUrl('/trailery-z-gier.asp')},
                             {'category':'list_tabs',          'title':'Zwiastuny filmów',     'url': self.getFullUrl('/trailery-filmowe.asp')},
                             {'category':'search',         'title':_('Search'), 'search_item':True},
                             {'category':'search_history', 'title':_('Search history')} ]
        
    def _decodeData(self, data):
        try: return data.decode('cp1250').encode('utf-8')
        except Exception: return data

    def getPage(self, url, params={}, post_data=None):
        sts,data = self.cm.getPage(url, params, post_data)
        if sts: data = self._decodeData(data)
        return sts,data
    
    def listTabs(self, cItem, post_data=None):
        printDBG("TvGryPL.listTabs")
        tabIdx = cItem.get('tab_idx', 0)
        sts, data = self.getPage(cItem['url'], {}, post_data)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tvgry-lista-menu', '</div>')[1]
        data = data.split('<br>')
        if tabIdx < len(data):
            data = self.cm.ph.getAllItemsBeetwenMarkers(data[tabIdx], '<a ', '</a>')
            for item in data:
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(item)
                if self.cm.isValidUrl(url):
                    params = dict(cItem)
                    params.update({'tab_idx':tabIdx+1, 'title':title, 'url':url})
                    self.addDir(params)
                
        if 0 == len(self.currList):
            self.listItems(cItem, post_data)
    
    def listItems(self, cItem, post_data=None):
        printDBG("TvGryPL.listItems")
        page = cItem.get('page', 1)
        url  = cItem['url']
        if 1 < page:
            if '?' in url: url += '&'
            else: url += '?'
            url += 'STR=%d' % page
        
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '-wide">', '<div class="clr">', False)[1]
        data = data.split('<div class="next-prev')
        
        if len(data) == 2 and '' != self.cm.ph.getSearchGroups(data[1], '''STR=(%s)[^0-9]''' % (page + 1))[0]:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data[0], '<a ', '</a>')
        for item in data:
            url  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p class="tv-box-title"', '</p>')[1])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p class="title"', '</p>')[1])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            
            descTab = []
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="tv-box-time"', '</div>')[1])
            if tmp != '': descTab.append(tmp)
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="tv-box-thumb-c"', '</div>')[1])
            if tmp != '': descTab.append(tmp.replace(' ', '/'))
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p class="tv-box-desc"', '</p>')[1])
            if tmp != '': descTab.append(tmp)
            
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':' | '.join(descTab)}
            if '/wideo.asp' in url:
                self.addVideo(params)
            elif '/temat.asp' in url:
                params.update({'name':'category', 'category':'list_tabs'})
                self.addDir(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'name':'category', 'category':'list_items', 'title':_('Next page'), 'page':page + 1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TvGryPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        baseUrl = 'https://tvgry.pl/wyszukiwanie.asp'
        post_data = {'search':searchPattern}
        
        cItem = dict(cItem)
        cItem.update({'url':baseUrl})
        self.listItems(cItem, post_data)
    
    def getLinksForVideo(self, cItem):
        printDBG("TvGryPL.getLinksForVideo [%s]" % cItem)
        allLinksTab = []
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        if self.cm.isValidUrl(url):
            allLinksTab = self.up.getVideoLinkExt(url)
        
        urlIDS = []
        urlTemplate = ''
        data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '{', '}')
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''['"]?file['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
            name = self.cm.ph.getSearchGroups(item, '''['"]?label['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
            if self.cm.isValidUrl(url):
                id = self.cm.ph.getSearchGroups(url, '''(/[0-9]+_)[0-9]+''')[0]
                if id != '' and id not in urlIDS:
                    urlIDS.append(id)
                    if urlTemplate == '': urlTemplate = url.replace(id, '{0}')
                    
                q = ""
                if '/500_' in url or "Mobile" in url:
                    q = 'MOB'
                elif '/750_' in url or "SD" in url:
                    q = 'SD'
                elif '/1280_' in url or "720p" in url:
                    q = 'HD'
                if q != '': urlTab.append({'name':name, 'url':url, 'q':q, 'need_resolve':0})
        
        if urlTemplate != '':
            for item in [('/500_', 'MOB'), ('/750_', 'SD'), ('/1280_', 'HD')]:
                if item[0] in urlIDS: continue
                try:
                    url = urlTemplate.format(item[0])
                    sts, response = self.cm.getPage(url, {'return_data':False})
                    if 'mp4' in response.info().get('Content-Type', '').lower():
                        urlTab.append({'name':item[1], 'url':url, 'q':item[1], 'need_resolve':0})
                    response.close()
                except Exception:
                    printExc()
        
        if 1 < len(urlTab):
            map = {'MOB':0, 'SD':1, 'HD':2, 'FHD':3}
            oneLink = CSelOneLink(urlTab, lambda x: map[x['q']], map[config.plugins.iptvplayer.tvgrypl_default_quality.value])
            if config.plugins.iptvplayer.tvgrypl_use_dq.value: urlTab = oneLink.getOneLink()
            else: urlTab = oneLink.getSortedLinks()
        
        if 0 == len(urlTab):
            return allLinksTab
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('TvGryPL.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('TvGryPL.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('TvGryPL.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('TvGryPL.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = [] 

        if None == name:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #ITEMS
        elif 'list_tabs' == category:
            self.listTabs(self.currItem)
        elif 'list_items' == category:
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
        CHostBase.__init__(self, TvGryPL(), True)
