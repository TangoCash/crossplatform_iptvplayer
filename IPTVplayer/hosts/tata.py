# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetPluginDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta

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
from binascii import hexlify, unhexlify
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from urlparse import urlparse, urljoin
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
    return 'https://tata.to/'

class Tata(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'tata.to', 'cookie':'tata.to.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'https://image.ibb.co/hBrDXk/logo.png'
        self.MAIN_URL = None
        self.cacheFilters = []
        self.cacheFiltersNames = []
        
    def selectDomain(self):
        
        self.MAIN_URL = 'https://www.tata.to/'
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': 'FILME',       'url':self.getFullUrl('/filme')},
                             {'category':'list_channels',   'title': 'TV SENDER',   'url':self.getFullUrl('/channels')},
                             
                             {'category':'search',          'title': _('Search'), 'search_item':True, },
                             {'category':'search_history',  'title': _('Search history'),             } 
                            ]
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urljoin(baseUrl, url)
        
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
    
    def _addFilter(self, data, cacheTab, cacheNames, anyTitle='', titleBase=''):
        filtersTab = []
        for item in data:
            key   = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
            title = self.cleanHtmlStr(item)
            if key not in cacheNames:   
                cacheNames.append(key)
            filtersTab.append({'title':titleBase + title, 'f_'+key:value})
        if anyTitle != '' and len(filtersTab):
            filtersTab.insert(0, {'title':anyTitle})
        if len(filtersTab):
            cacheTab.append(filtersTab)
            return True
        return False
    
    def _fillFilters(self, cItem):
        self.cacheFilters = []
        self.cacheFiltersNames = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filter-row"', '</form>', False)[1]
        data = data.split('<div class="filter-row"')
        for tmp in data:
            anyTitle =  _('--Any--')
            filterTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<span', '</span>')[1])
            printDBG("filterTitle    [%s]" % filterTitle)
            if 'Type' in filterTitle: continue
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<label', '</label>')
            if 'Veröffentlichung' in filterTitle: tmp = tmp[::-1]
            if 'Sortieren' in filterTitle:
                tmp = tmp[::-1]
                anyTitle = ''
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>> filterTitle[%s] [%d]" % (filterTitle, len(tmp)))
            self._addFilter(tmp, self.cacheFilters, self.cacheFiltersNames, anyTitle)
    
    def listFilters(self, cItem, cacheTab):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        if idx < len(cacheTab):
            self.listsTab(cacheTab[idx], params)
    
    def listChannels(self, cItem):
        printDBG("Tata.listChannels")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="ml-list', '<nav')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="ml-item', '</div>')
        for item in data:
            url  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+)['"]''')[0] )
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+)['"]''')[0] )
            title = url.split('/')[-1].replace('-', ' ').title()
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon})
            self.addVideo(params)
            
    def listItems(self, cItem, nextCategory='', searchPattern=''):
        printDBG("Tata.listItems |%s|" % cItem)
        
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1: url += '/%s' % page
        
        query = {'type':'filme'}
        if searchPattern != '': query['suche'] = searchPattern
        for key in self.cacheFiltersNames:
            if 'f_'+key in cItem: 
                query[key] = cItem['f_'+key]
        
        query = urllib.urlencode(query)
        if '?' in url: url += '&' + query
        else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if 'rel="next"' in data: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<section', '</section')[1]
        data = data.split('<div class="ml-item">')
        if len(data): del data[0]
        for item in data:
            url  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+)['"]''')[0] )
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+)['"]''')[0] )
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h6', '</h6>')[1])
            
            descTab = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': descTab.append(t)
            desc = ' | '.join(descTab)
            desc += '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="caption-description"', '</div>')[1])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            self.addVideo(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('filme?suche=%s' % urllib.quote_plus(searchPattern))
        self.listItems(cItem, searchPattern=searchPattern)
        
    def getLinksForVideo(self, cItem):
        printDBG("Tata.getLinksForVideo [%s]" % cItem)
        linksTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        tmp = self.cm.ph.getSearchGroups(data, '''(<a[^>]+?show-trailer[^>]+>)''')[0]
        trailerUrl = self.cm.ph.getSearchGroups(tmp, '''href=['"](https?://[^'^"]+)['"]''')[0]
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'class="video-embed', '</div>')[1]
        videoUrl = self.cm.ph.getSearchGroups(data, '''data-src=['"](https?://[^'^"]+)['"]''')[0].strip()
        if '' == videoUrl:
            try:
                getParams = dict(self.defaultParams)
                getParams['header'] = dict(getParams['header'])
                getParams['header']['Referer'] = cItem['url']
                
                url = self.cm.ph.getSearchGroups(data, '''data-url=['"](https?://[^'^"]+)['"]''')[0]
                sts, data = self.getPage(url, getParams)
                if not sts: return []
                printDBG("+++++++++++++++++++++++++++++++++++++++")
                printDBG(data)
                printDBG("+++++++++++++++++++++++++++++++++++++++")
                
                data = base64.b64decode(data)
                data = byteify(json.loads(data))
                videoUrl = data['playinfo'].replace('\\/', '/').strip()
            except Exception:
                printExc()
        
        if self.cm.isValidUrl(videoUrl):
            #videoUrl = videoUrl.replace('://s6.', '://s4.')
            getParams = dict(self.defaultParams)
            getParams['header'] = dict(getParams['header'])
            getParams['header']['Referer'] = cItem['url']
            
            sts, data = self.getPage(videoUrl, getParams)
            if not sts: return []
            
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            try:
                data = base64.b64decode(data)
                data = byteify(json.loads(data))
                videoUrl = data['playinfo'].replace('\\/', '/').strip()
                
                sts, data = self.getPage(videoUrl, getParams)
                if not sts: return []
                
                printDBG("+++++++++++++++++++++++++++++++++++++++")
                printDBG(data)
                printDBG("+++++++++++++++++++++++++++++++++++++++")
            except Exception:
                printExc()
            
            hlsUrl = videoUrl.replace('/embed.html', '/index.m3u8')
            hlsUrl = strwithmeta(hlsUrl, {'Referer':videoUrl, 'User-Agent':self.USER_AGENT})
            
            linksTab = getDirectM3U8Playlist(hlsUrl, checkContent=True)
            #for idx in range(len(linksTab)):
            #    if linksTab[idx]['url'].startswith('https:'):
            #        linksTab[idx]['url'] = strwithmeta('http' + linksTab[idx]['url'][5:], linksTab[idx]['url'].meta)
            
        if len(linksTab) and self.cm.isValidUrl(trailerUrl):
            linksTab.append({'name':'Trailer', 'url':trailerUrl, 'need_resolve':1})
        
        return linksTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("Tata.getVideoLinks [%s]" % videoUrl)
        return self.up.getVideoLinkExt(videoUrl)
    
    def getArticleContent(self, cItem):
        printDBG("Tata.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        title = ''
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie-info">', 'share-list')[1]
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie-description">', '</div>')[1])
        icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+\.jpe?g)['"]''')[0] )
        
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in tmp:
            t = self.cm.ph.getDataBeetwenMarkers(item, '<span', '</span>')[1]
            value  = self.cleanHtmlStr(item.split('</span>')[-1])
            if value == '': continue
            if t == '': t = self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1]
            
            printDBG("-------------")
            printDBG(t)
            printDBG(value)
            
            for m in [{'m':'Land', 'k':'country'}, {'m':'Genre', 'k':'genre'}, {'m':'Schauspieler', 'k':'actors'}, \
                      {'m':'time"', 'k':'duration'}, {'m':'calendar"', 'k':'released'}, {'m':'eye-open"', 'k':'views'}, \
                      {'m':'IMDb', 'k':'imdb_rating'}, {'m':'quality', 'k':'quality'}]:
                if m['m'] in t:
                    otherInfo[m['k']] = value.replace(' ,', ',')
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<span class="quality', '</span>')[1])
        if tmp != '': otherInfo['quality'] = tmp
            
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('Tata.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('Tata.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('Tata.setInitListFromFavouriteItem')
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
        elif category == 'list_channels':
            self.listChannels(self.currItem)
        elif 'list_filters' == category:
            idx = self.currItem.get('f_idx', 0)
            if idx == 0: self._fillFilters(self.currItem)
            if idx < len(self.cacheFilters):
                self.listFilters(self.currItem, self.cacheFilters)
            else:
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
        CHostBase.__init__(self, Tata(), True, [])
    
    def withArticleContent(self, cItem):
        if 'video' != cItem.get('type', '') or '/film/' not in cItem.get('url', ''):
            return False
        return True
    