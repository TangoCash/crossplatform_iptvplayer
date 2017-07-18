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
    return 'https://hd-streams.org/'

class HDStreams(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'hd-streams.org', 'cookie':'hd-streams.org.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.USER_AGENT = 'Mozilla/5.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'http://s-media-cache-ak0.pinimg.com/originals/82/63/59/826359efee44e19824912cdf45b3bd59.jpg'
        self.MAIN_URL = None
        
    def selectDomain(self):
        
        self.MAIN_URL = 'https://hd-streams.org/'
        self.MAIN_CAT_TAB = [{'category':'list_sort',       'title': _('MOVIES'),      'url':self.getFullUrl('/category/movie/'), 'f_category':'2'},
                             {'category':'list_sort',       'title': _('TV SERIES'),   'url':self.getFullUrl('/category/serie/'), 'f_category':'3'},
                             {'category':'list_categories', 'title': _('CATEGORIES'),  'url':self.getMainUrl()}, 
                             
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
        
    def cryptoJS_AES_decrypt(self, encrypted, password, salt):
        def derive_key_and_iv(password, salt, key_length, iv_length):
            d = d_i = ''
            while len(d) < key_length + iv_length:
                d_i = md5(d_i + password + salt).digest()
                d += d_i
            return d[:key_length], d[key_length:key_length+iv_length]
        bs = 16
        key, iv = derive_key_and_iv(password, salt, 32, 16)
        cipher = AES_CBC(key=key, keySize=32)
        return cipher.decrypt(encrypted, iv)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("HDStreams.listCategories")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tagcloud"', '</li>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+)['"]''')[0] )
            title = self.cleanHtmlStr(item)
            tag   = self.cm.ph.getSearchGroups(url+'/', '''/tag/([^/]+)/''')[0]
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':title, 'url':url, 'f_tag':tag})
            self.addDir(params)
            
    def listSort(self, cItem, nextCategory):
        printDBG("HDStreams.listSort")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="dropdown-menu', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+)['"]''')[0] + '&'
            title = self.cleanHtmlStr(item)
            orderby = self.cm.ph.getSearchGroups(url, '''orderby=([^&]+)&''')[0]
            order   = self.cm.ph.getSearchGroups(url, '''order=([^&]+)&''')[0]
            last    = self.cm.ph.getSearchGroups(url, '''last=([^&]+)&''')[0]
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':title, 'f_orderby':orderby, 'f_order':order, 'f_last':last})
            self.addDir(params)
        
    def listItems(self, cItem, nextCategory='', searchPattern=''):
        printDBG("HDStreams.listItems |%s|" % cItem)
        NUM = 48
        url = self.getFullUrl('/wp-admin/admin-ajax.php')
        page = cItem.get('page', 1)
        
        if '/?s=' in cItem['url']:
            isSarchMode = True
        else: isSarchMode = False
        
        if page == 1:
            sts, data = self.getPage(cItem['url'])
            if not sts: return
            printDBG(data)
            nonce = self.cm.ph.getSearchGroups(data, '''"nonce"\s*:\s*"([^"]+)"''')[0]
            cItem = dict(cItem)
            cItem['f_nonce'] = nonce
        
        query = {}
        keys = ['nonce', 'category', 'orderby', 'order', 'last', 'tag']
        query.update({'site':page, 'c':NUM, 'action':'load_categories', 'initialLoad':False})
        
        for key in keys:
            if 'f_'+key in cItem: 
                val = cItem['f_'+key]
            else:
                val = ''
            query[key] = val
        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(self.AJAX_HEADER)
        urlParams['header']['Referer'] = cItem['url']
        
        sts, data = self.getPage(url, urlParams, query)
        if not sts: return
        
        nextPage = False
        try:
            data = byteify(json.loads(data))
            for item in data['data'][0]:
                url  = self.getFullUrl(item['url'])
                icon = self.getFullIconUrl(item.get('image', ''))
                title = self.cleanHtmlStr(item.get('title',''))
                descTab = []
                if '' != item.get('hd',''):
                    descTab.append('HD')
                if '' != item.get('views',''):
                    descTab.append(_('%s views') % item['views'])
                descTab.append(self.cleanHtmlStr(item.get('content','')))
                
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'desc':'[/br]'.join(descTab), 'icon':icon})
                self.addDir(params)
            if data.get('eps', 0) == NUM:
                nextPage = True
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("HDStreams.exploreItem")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        mainTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text-left title">', '</div>')[1])
        
        sNum = self.cm.ph.getSearchGroups(data, 'staffel\-([0-9]+)\-')[0]
        
        m1 = '<div class="episode">'
        tmp = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div class="row">', False)[1]
        if tmp == '':
            urls = []
            langsData = re.compile('<a[^>]+?href="#lang\-([^"]+)"').findall(data)
            for lang in langsData:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, 'id="lang-%s"' % lang, '</ul>', False)[1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
                for q in tmp:
                    quality = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(q, '<div class="quality-wrapper"', '</div>')[1])
                    linksData = self.cm.ph.getAllItemsBeetwenMarkers(q, '<a', '</a>')
                    for t in linksData:
                        name = self.cleanHtmlStr(t)
                        embed = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-embed=['"]([^"^']+)['"]''')[0])
                        server = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-server=['"]([^"^']+)['"]''')[0])
                        episode = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-episode=['"]([^"^']+)['"]''')[0])
                        if server != "" and episode != "":
                            urls.append({'name':'[%s][%s] %s' %(lang, quality, name), 'embed':embed, 'server':server, 'episode':episode})
            
            params = dict(cItem)
            params.update({'good_for_fav':False, 'urls':urls})
            self.addVideo(params)
        else:
            data = tmp.split(m1)
            for item in data:
                icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''url\(\s*['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''data-title=['"]([^"^']+)['"]''')[0])
                tmp  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="number">', '</div>')[1])
                eNum = self.cm.ph.getSearchGroups(tmp, '''([0-9]+)''')[0]
                
                if sNum != '' and eNum != '': key = 's%se%s'% (sNum.zfill(2), eNum.zfill(2))
                else: key = ''
                
                if title != '': title = '%s: %s %s' % (mainTitle, key, title)
                else: title = mainTitle
                
                if icon == '': icon = cItem['icon']
                
                urls = []
                tmp = item.split('</button>')[-1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
                for t in tmp:
                    name = self.cleanHtmlStr(t)
                    embed = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-embed=['"]([^"^']+)['"]''')[0])
                    server = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-server=['"]([^"^']+)['"]''')[0])
                    episode = self.cleanHtmlStr(self.cm.ph.getSearchGroups(t, '''data-episode=['"]([^"^']+)['"]''')[0])
                    if server != "" and episode != "":
                        urls.append({'name':name, 'embed':embed, 'server':server, 'episode':episode})
                params = dict(cItem)
                params.update({'good_for_fav':False, 'title':title, 'urls':urls, 'icon':icon})
                self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("HDStreams.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'f_action':'ajax_search', 'f_query':searchPattern})
        url = self.getFullUrl('/?s=' + urllib.quote_plus(searchPattern))
        sts, data = self.getPage(url)
        if not sts: return
        nonce = self.cm.ph.getSearchGroups(data, '''"snonce"\s*:\s*"([^"]+)"''')[0]
        query = {'action':'ajax_search', 'nonce':nonce,  'query':searchPattern, 'form':'main', 'cat':'2,3,'}
        
        if 'movie' == searchType:
            query['cat'] = '2,'
        else:
            query['cat'] = '3,'
        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(self.AJAX_HEADER)
        urlParams['header']['Referer'] = url
        url = self.getFullUrl('/wp-admin/admin-ajax.php')
        
        sts, data = self.getPage(url, urlParams, query)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))['data']
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="search-card', '</a>')
            for item in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''url\(\s*['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':'explore_item', 'title':title, 'url':url, 'icon':icon})
                self.addDir(params)
        except Exception:
            printExc()
        
    def getLinksForVideo(self, cItem):
        printDBG("HDStreams.getLinksForVideo [%s]" % cItem)
        linksTab = []
        
        if 'urls' in cItem:
            sts, data = self.getPage(cItem['url'])
            if not sts: return []
            
            nonce  = self.cm.ph.getSearchGroups(data, '''"nonce"\s*:\s*"([^"]+)"''')[0]
            postid = self.cm.ph.getSearchGroups(data, '''"postid"\s*:\s*"([^"]+)"''')[0]
            b      = self.cm.ph.getSearchGroups(data, '''data-img=['"]([^'^"]+?)['"]''')[0]
            
            for item in cItem['urls']:
                post_data = dict(item)
                post_data.pop('name')
                post_data.update({'action':'load_episodes', 'b':b, 'nonce':nonce, 'pid':postid})
                url = self.getFullUrl('/wp-admin/admin-ajax.php')
                url = strwithmeta(url, {'Referer':cItem['url'], 'post_data':post_data})
                linksTab.append({'name':item['name'], 'url':url, 'need_resolve':1})
        
        return linksTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDStreams.getVideoLinks [%s]" % videoUrl)
        meta = strwithmeta(videoUrl).meta
        post_data = meta.get('post_data', {})
        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(self.AJAX_HEADER)
        urlParams['header']['Referer'] = meta.get('Referer', '')
        
        sts, data = self.getPage(videoUrl, urlParams, post_data)
        if not sts: return []
        
        try:
            data = byteify(json.loads(data))
            tmp = base64.b64decode(data['u'])
            tmp = byteify(json.loads(tmp))
            
            ciphertext = base64.b64decode(tmp['ct'])
            iv = unhexlify(tmp['iv'])
            salt = unhexlify(tmp['s'])
            tmp = self.cryptoJS_AES_decrypt(ciphertext, base64.b64decode(post_data['b']), salt)
            tmp = byteify(json.loads(tmp))
            videoUrl = tmp
        except Exception:
            printExc()
        
        return self.up.getVideoLinkExt(videoUrl)
    
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
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_sort')
        elif category == 'list_channels':
            self.listChannels(self.currItem)
        elif 'list_sort' == category:
            self.listSort(self.currItem, 'list_items')
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
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Movies"),   "movie"))
        searchTypesOptions.append((_("TV Shows"), "series"))
        return searchTypesOptions
    
    def withArticleContent(self, cItem):
        if 'video' == cItem.get('type', '') or 'explore_item' == cItem.get('category', ''):
            return True
        return False
    