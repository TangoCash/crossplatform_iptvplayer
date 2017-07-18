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
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from urlparse import urlparse, urljoin

from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
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
    return 'http://mythewatchseries.com/'

class HDStreams(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'mythewatchseries', 'cookie':'mythewatchseries.cookie', 'cookie_type':'MozillaCookieJar'}) #, 'min_py_ver':(2,7,9)
        self.USER_AGENT = 'Mozilla/5.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'http://mythewatchseries.com/img/icon/logo.png'
        self.MAIN_URL = None
        self.cacheLinks = {}
        
    def selectDomain(self):
        self.MAIN_URL = 'http://mythewatchseries.com/'
        self.MAIN_CAT_TAB = [{'category':'list_items',       'title': _("MOVIES"),                     'url':self.getFullUrl('/movies')},
                             {'category':'list_items',       'title': _("CINEMA MOVIES"),              'url':self.getFullUrl('/cinema-movies')},
                             {'category':'list_items',       'title': _("THIS WEEK'S SERIES POPULAR"), 'url':self.getFullUrl('/recommended-series')},
                             {'category':'list_items',       'title': _("NEW RELEASE LIST"),           'url':self.getFullUrl('/new-release')},
                             
                             #{'category':'list_categories', 'title': _('CATEGORIES'),  'url':self.getMainUrl()}, 
                             
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
        
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def listItems(self, cItem, nextCategory='', searchPattern=''):
        printDBG("HDStreams.listItems |%s|" % cItem)
        
        url  = cItem['url']
        page = cItem.get('page', 1)
        
        query = {}
        if searchPattern != '':
            query['keyword'] = searchPattern
        if page > 1: query['page'] = page
        query = urllib.urlencode(query)
        if query != '':
            if url[-1] in ['&', '?']: sep = ''
            elif '?' in url: sep = '&'
            else: sep = '?'
            url += sep + query
        
        sts, data = self.getPage(url)
        if not sts: return []
        
        if '>Next<' in data: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="listing items"', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="name"', '</div>')[1])
            if title != '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+)['"]''')[0])
            
            # prepare desc
            descTab = []
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(item, '<div class="season"', '</div>')
            tmpTab.extend(self.cm.ph.getAllItemsBeetwenMarkers(item, '<div class="date"', '</div>'))
            for tmp in tmpTab:
                tmp = self.cleanHtmlStr(tmp)
                if tmp != '': descTab.append(tmp)
            desc = ' | '.join(descTab) + '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="des"', '</div>')[1])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("HDStreams.exploreItem")
        
        self.cacheLinks = {}
        
        url = cItem['url']
        if '/info/' not in url:
            sts, data = self.getPage(url)
            if sts:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content">', '</div>')[1]
                data = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]*?/info/[^'^"]+?)['"]''')[0])
                if self.cm.isValidUrl(data):
                    url = data
        
        sts, data = self.getPage(url)
        if not sts: return
        
        tmp = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?id=['"]iframe-trailer['"][^>]+?>''')[0]
        trailerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''['"](https?://[^'^"]+?)['"]''')[0])
        if not self.cm.isValidUrl(trailerUrl):
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '#iframe-trailer', ';')[1]
            trailerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''['"](https?://[^'^"]+?)['"]''')[0])
        
        # prepare desc
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="info_movies"', '<div class="clr">')[1]
        descTab = []
        tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
        for d in tmpTab:
            if 'Latest Episode' in d: continue
            d = self.cleanHtmlStr(d)
            if d != '': descTab.append(d)
        mainDesc = '[/br]'.join(descTab) + '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<div class="des"', '</div>')[1])
        
        icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(tmp, '''src=['"]([^'^"]+?)['"]''')[0])
        if icon == '': icon = cItem.get('icon', '')
        if mainDesc == '': mainDesc = cItem.get('desc', '')
        
        # add trailer item
        if self.cm.isValidUrl(trailerUrl):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'is_trailer':True, 'title':_('%s - trailer') % cItem['title'], 'url':trailerUrl, 'icon':icon, 'desc':mainDesc})
            self.addVideo(params)
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="child_episode"', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item.split('<span')[0])
            if title != '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+)['"]''')[0])
            
            # prepare desc
            descTab = []
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(item, '<span class="date"', '</span>')
            for tmp in tmpTab:
                tmp = self.cleanHtmlStr(tmp)
                if tmp != '': descTab.append(tmp)
            desc = ' | '.join(descTab) + '[/br]' + mainDesc
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("HDStreams.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/search.html')
        self.listItems(cItem, 'explore_item', searchPattern)
        
    def getLinksForVideo(self, cItem):
        printDBG("HDStreams.getLinksForVideo [%s]" % cItem)
        linksTab = []
        if cItem.get('is_trailer'):
            linksTab.append({'name':'trailer', 'url':cItem['url'], 'need_resolve':1})
        else:
            linksTab = self.cacheLinks.get(cItem['url'], [])
            if len(linksTab) > 0: return linksTab
            
            sts, data = self.getPage(cItem['url'], self.defaultParams)
            if not sts: return []
            
            data = self.cm.ph.getDataBeetwenMarkers(data, 'muti_link', '</ul>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
            for item in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data-video=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<a', '</span>')[1])
                if title == '': title = self.cleanHtmlStr(item)
                
                linksTab.append({'name':title, 'url':strwithmeta(url, {'links_key':cItem['url']}), 'need_resolve':1})
        
        if len(linksTab):
            self.cacheLinks[cItem['url']] = linksTab
        
        return linksTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDStreams.getVideoLinks [%s]" % videoUrl)
        linksTab = []
        
        videoUrl = strwithmeta(videoUrl)
        
        key = videoUrl.meta.get('links_key', '')
        if key != '':
            if key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if self.cacheLinks[key][idx]['url'] == videoUrl and not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(urlParams['header'])
        urlParams['header']['Referer'] = videoUrl.meta.get('Referer', key)
        
        if self.up.getDomain(self.getMainUrl()) in videoUrl:
            sts, data = self.getPage(videoUrl, urlParams)
            printDBG(data)
            if sts:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>')
                for item in tmp:
                    printDBG(item)
                    label = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0]
                    type  = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0]
                    url   = self.cm.ph.getSearchGroups(item, '''src=['"](https?://[^'^"]+?)['"]''')[0]
                    if self.cm.isValidUrl(url) and 'mp4' in type:
                        linksTab.append({'name':label, 'url':url})
                videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^"]+?)['"]''', 1, True)[0]
        
        if 0 == len(linksTab):
            videoUrl = strwithmeta(videoUrl, {'Referer':self.getMainUrl()})
            linksTab = self.up.getVideoLinkExt(videoUrl)
        
        return linksTab
    
    def getArticleContent(self, cItem):
        printDBG("HDStreams.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="post', '<div class="row">')[1]
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text-left title">', '</div>')[1])
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="summary-wrapper">', '</div>')[1])
        icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+\.jpe?g)['"]''')[0] )
        
        tmpTab = []
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<span class="mdl-chip">', '</a>')
        for t in tmp:
            tmpTab.append(self.cleanHtmlStr(t))
        otherInfo['genre'] = ', '.join(tmpTab)
        
        tmpTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="cast">', '<div class="text-left')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<span class="mdl-chip__text">', '</a>')
        for t in tmp:
            tmpTab.append(self.cleanHtmlStr(t))
        otherInfo['actors'] = ', '.join(tmpTab)
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<div[^>]+?year"[^>]*?>'), re.compile('</div>'))[1])
        if tmp != '': otherInfo['released'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="rating-votes">', '</div>')[1])
        if tmp != '': otherInfo['rating'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Original Titel:', '</div>', False, False)[1])
        if tmp != '': otherInfo['alternate_title'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Laufzeit:', '</div>', False, False)[1])
        if tmp != '': otherInfo['duration'] = tmp
            
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('HDStreams.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('HDStreams.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('HDStreams.setInitListFromFavouriteItem')
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
        elif 'list_items' == category:
            self.listItems(self.currItem, 'explore_item')
        elif 'explore_item' == category:
            self.exploreItem(self.currItem)
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
        CHostBase.__init__(self, HDStreams(), True, [])
    
    #def withArticleContent(self, cItem):
    #    if 'video' == cItem.get('type', '') or 'explore_item' == cItem.get('category', ''):
    #        return True
    #    return False
    