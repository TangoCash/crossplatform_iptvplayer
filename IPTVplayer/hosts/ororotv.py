# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import time
import re
import urllib
import string
import random
import base64
import datetime
from copy import deepcopy
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
    return 'https://ororo.tv/'

class OroroTV(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'ororo.tv', 'cookie':'ororo.tv.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'http://www.yourkodi.com/wp-content/uploads/2016/02/ororo.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'https://ororo.tv/'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.cacheFilters  = {}
        self.cacheLinks   = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [
                             {'category':'list_channels',         'title': _('Channels'),            'url':self.getFullUrl('/channels')},
                             {'category':'search',                'title': _('Search'),              'search_item':True, },
                             {'category':'search_history',        'title': _('Search history'),                          } 
                            ]
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
    
    def listChannels(self, cItem, nextCategory):
        printDBG("OroroTV.listChannels")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        sp = re.compile('''<div[^>]+?class=['"]channel['"][^>]*?>''')
        data = self.cm.ph.getDataBeetwenReMarkers(data, sp, re.compile('''<div[^>]+?class=['"]site\-footer['"][^>]*?>'''), False)[1]
        
        data = sp.split(data)
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span', '</span>')[1] ) 
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1] )
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'desc':desc, 'url':url, 'icon':icon})
            self.addDir(params)
        
    def listItems(self, cItem):
        printDBG("OroroTV.listItems [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''<div[^>]+?class=['"]desc['"][^>]*?>'''), re.compile('</div>'))[1])
        
        sp = re.compile('''<div[^>]+?class=['"]video\s[^>]*?>''')
        data = self.cm.ph.getDataBeetwenReMarkers(data, sp, re.compile('''<div[^>]+?class=['"]site\-footer['"][^>]*?>'''), False)[1]
        data = sp.split(data)
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''original=['"]([^'^"]+?)['"]''')[0] )
            title = self.cleanHtmlStr( item ) 
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("OroroTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = self.getFullUrl('/api/frontend/search?query=') + urllib.quote_plus(searchPattern)
        
        sts, data = self.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0] )
            tmp   = self.cm.ph.getAllItemsBeetwenMarkers(item, '<p', '</p>')
            title = self.cleanHtmlStr( tmp[0] )
            desc  = self.cleanHtmlStr( tmp[1] )
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            if '/channels/' in url and '/videos/' not in url: 
                params['category'] = 'list_items'
                self.addDir(params)
            else:
                self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("OroroTV.getLinksForVideo [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<source', '>')[1]
        videoUrl = self.cm.ph.getSearchGroups(tmp, '''src=['"](https?://[^'^"]+?)['"]''')[0]
        type = self.cm.ph.getSearchGroups(tmp, '''type=['"]([^'^"]+?)['"]''')[0]
        
        retTab = self.up.getVideoLinkExt(videoUrl)
        if 0 == len(retTab): return []
        
        subTracks = []
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track', '>')
        for item in tmp:
            if 'subtitles' not in item: continue
            
            url = self.cm.ph.getSearchGroups(item, '''src=['"](https?://[^'^"]+?)['"]''')[0]
            lang = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0]
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            
            if url != '': subTracks.append({'title':title, 'url':url, 'lang':lang, 'format':url[-3:]})
        
        if len(subTracks):
            for idx in range(len(retTab)):
                tmp = list(subTracks)
                tmp.extend(retTab[idx]['url'].meta.get('external_sub_tracks', []))
                retTab[idx]['url'] = strwithmeta(retTab[idx]['url'], {'external_sub_tracks':list(tmp)})
        
        return retTab
    
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
        elif category == 'list_channels':
            self.listChannels(self.currItem, 'list_items')
        elif category == 'list_items':
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
        CHostBase.__init__(self, OroroTV(), True, [])
    
    