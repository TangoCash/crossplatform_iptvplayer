# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, unpackJS, VIDEOMEGA_decryptPlayerParams
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
import hashlib
from binascii import hexlify, unhexlify
from urlparse import urlparse, urljoin
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
    return 'http://skstream.info/'

class SKStream(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'skstream.co', 'cookie':'skstream.co.cookie', 'cookie_type':'MozillaCookieJar'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.DEFAULT_ICON_URL = 'http://www.skstream.info/apple-touch-icon.png'
        self.MAIN_URL = None
        self.cacheCategories = []
        self.episodesCache = []
        self.cacheLinks = {}
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self._getHeaders = None
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urljoin(baseUrl, url)
        
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def getFullUrl(self, url):
        url = CBaseHostClass.getFullUrl(self, url)
        try: url.encode('ascii')
        except Exception: url = urllib.quote(url, safe="/:&?%@[]()*$!+-=|<>;")
        url = url.replace(' ', '%20')
        return url
        
    def selectDomain(self):
        self.MAIN_URL = 'http://www.skstream.info/'
        params = dict(self.defaultParams)
        params['return_data'] = False
        try:
            sts, response = self.getPage(self.MAIN_URL, params)
            self.MAIN_URL = response.geturl()
            response.close()
        except Exception:
            printExc()
        printDBG("selectDomain [%s]" % self.MAIN_URL)
        
    def listMainMenu(self, cItem):
        if self.MAIN_URL == None: return
        MAIN_CAT_TAB = [{'category':'list_categories',         'title': 'Films',                    'url':self.getFullUrl('/films')},
                        {'category':'list_categories',         'title': 'Séries',                   'url':self.getFullUrl('/series')},
                        {'category':'list_categories',         'title': 'Mangas',                   'url':self.getFullUrl('/mangas')},
                        
                        {'category':'search',          'title': _('Search'), 'search_item':True, },
                        {'category':'search_history',  'title': _('Search history'),             } 
                       ]
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("SKStream.listCategories")
        self.cacheCategories = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        params = dict(cItem)
        params.update({'good_for_fav':False, 'category':'list_items', 'title':_('--All--')})
        self.addDir(params)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<nav ', '</nav>')[1]
        data = data.split('<div class="panel panel-default">')
        if len(data) > 2: data = data[2:]
        for section in data:
            sectionTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(section, '<div class="panel-heading">', '</div>')[1])
            
            groupsTitles  = self.cm.ph.getAllItemsBeetwenMarkers(section, '<span data-target="md-tab', '</span>')
            groupsDataTab = self.cm.ph.getAllItemsBeetwenMarkers(section, '<div class="list-group', '</div>')
            for idx in range(len(groupsDataTab)):
                groupTitle = sectionTitle + ' '
                if idx < len(groupsTitles): groupTitle += self.cleanHtmlStr(groupsTitles[idx])
                tmp   = self.cm.ph.getAllItemsBeetwenMarkers(groupsDataTab[idx], '<a', '</a>')
                tab = []
                for item in tmp:
                    title = self.cleanHtmlStr(item)
                    url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    if not self.cm.isValidUrl(url): continue
                    tab.append({'title':title, 'url':url})
                if len(tab):
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':groupTitle, 'c_idx':len(self.cacheCategories)})
                    self.addDir(params)
                    self.cacheCategories.append(tab)

    def listCatsItems(self, cItem, nextCategory):
        printDBG("SKStream.listCatsItems")
        cIdx = cItem.get('c_idx', 0)
        if cIdx < len(self.cacheCategories):
            tab = self.cacheCategories[cIdx]
            for item in tab:
                params = dict(cItem)
                params.update(item)
                params.update({'good_for_fav':False, 'category':nextCategory})
                self.addDir(params)
            
    def listItems(self, cItem, nextCategory):
        printDBG("SKStream.listItems")
        
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"]([^"^']+?)['"][^>]*?>Suivant''', ignoreCase=True)[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="panel-body">', '<div class="text-center">')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        printDBG(data)
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''', ignoreCase=True)[0])
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(item)
            icon  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''<img[^>]+?src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon})
            self.addDir(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Next page'), 'url':nextPage, 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem, nextCategory):
        printDBG("SKStream.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="more-info">', '</div>')[1])
        
        if 'data-embedlien' in data:
            params = dict(cItem)
            params.update({'desc':desc})
            self.addVideo(params)
        elif 'class="episode-' in data:
            self.episodesCache = []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'season-block"', '<div class="jumbotron">')[1]
            data = data.split('<div class="panel-heading">')
            for season in data:
                seasonTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(season, '<h4', '</h4>')[1])
                season = self.cm.ph.getAllItemsBeetwenMarkers(season, '<a', '</a>')
                tab = []
                for item in season:
                    title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                    url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    if not self.cm.isValidUrl(url): continue
                    tab.append({'title':title, 'url':url})
                if len(tab):
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':seasonTitle, 'desc':desc, 's_idx':len(self.episodesCache)})
                    self.addDir(params)
                    self.episodesCache.append(tab)
    
    def listEpisodes(self, cItem):
        printDBG("SKStream.listEpisodes")
        cIdx = cItem.get('s_idx', 0)
        if cIdx < len(self.episodesCache):
            tab = self.episodesCache[cIdx]
            for item in tab:
                params = dict(cItem)
                params.update(item)
                params.update({'good_for_fav':True})
                self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SKStream.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 1)
        
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('recherche?s=%s' % urllib.quote_plus(searchPattern))
        self.listItems(cItem, 'explore_item')
    
    def getLinksForVideo(self, cItem):
        printDBG("SKStream.getLinksForVideo [%s]" % cItem)
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
            
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        urlTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>')
        for item in data:
            linksTab = []
            playerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data-embedlien=['"]([^'^"]+?)['"]''')[0])
            if self.cm.isValidUrl(playerUrl):
                linksTab.append(playerUrl)
            playerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data-basicurl=['"]([^'^"]+?)['"]''')[0])
            if self.cm.isValidUrl(playerUrl):
                linksTab.append(playerUrl)
            
            if 0 == len(linksTab): continue
            
            nameTab = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>')
            for n in tmp:
                n = self.cleanHtmlStr(n)
                if n != '': nameTab.append(n)
            
            url = strwithmeta('|><|'.join(linksTab), {'Referer':cItem['url']})
            urlTab.append({'name':' | '.join(nameTab), 'url':url, 'need_resolve':1})
            
        if len(urlTab):
            self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def _generatePass(self, nb):
        chars = 'azertyupqsdfghjkmwxcvbn23456789AZERTYUPQSDFGHJKMWXCVBN_-#@'
        password = ''
        for idx in range(nb):
            wpos = random.randrange(0, len(chars))
            password += chars[wpos]
        return password
        
    def getVideoLinks(self, videoUrl):
        printDBG("SKStream.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
                        
        linksTab = videoUrl.split('|><|')
        for url in linksTab:
            printDBG("> url[%s]" % url)
            if not self.cm.isValidUrl(url):
                continue
            
            if 1 != self.up.checkHostSupport(url):
                params = dict(self.defaultParams)
                try:
                    maxAttempt = 3
                    attempt = 0
                    params['header'] = dict(params['header'])
                    params['header']['Referer'] = videoUrl.meta['Referer']
                    params['return_data'] = False
                    post_data = None
                    while attempt < maxAttempt:
                        attempt += 1
                        sts, response = self.getPage(url, params, post_data)
                        url = response.geturl()
                        if 'dl-protect.co' in self.up.getDomain(url):
                            data = response.read(1024*1024*1024)
                            response.close()
                            
                            # get JS player script code from confirmation page
                            sts, tmpData = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
                            if sts: data += unpackJSPlayerParams(tmpData, VIDEOMEGA_decryptPlayerParams, 0, r2=True) #YOUWATCH_decryptPlayerParams == VIDUPME_decryptPlayerParams
                            
                            printDBG(data)
                            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
                            if url == '': url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''iframe.src\s*=\s*['"]([^"^']+?)['"]''', 1, True)[0])
                            if not self.cm.isValidUrl(url):
                                data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', '],', False)[1] + ']'
                                data = byteify(json.loads(data))
                                for item in data:
                                    if "mp4" == item['type']:
                                        urlTab.append({'name':str(item.get('label', 'default')), 'url':item['file']})
                            break
                        else:
                            if 1 != self.up.checkHostSupport(url):
                                data = response.read(1024*1024*1024)
                                response.close()
                                
                                scriptUrl = self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^"^']*?QapTcha.jquery[^"^']*?\.js)['"]''', 1, True)[0]
                                if scriptUrl != '' and not self.cm.isValidUrl(scriptUrl):
                                    scriptUrl = self.getFullUrl('/dl/' + scriptUrl)
                                if not self.cm.isValidUrl(scriptUrl):
                                    printDBG(">> scriptUrl not valid")
                                    break
                                
                                sts, data = self.getPage(scriptUrl)
                                if not sts:
                                    break
                                
                                formUrl = self.cm.ph.getSearchGroups(data, '''['"]([^"^']*?QapTcha.jquery[^"^']*?\.php)['"]''', 1, True)[0]
                                if formUrl != '' and not self.cm.isValidUrl(formUrl):
                                    formUrl = self.getFullUrl('/dl/' + formUrl)
                                if not self.cm.isValidUrl(formUrl):
                                    printDBG(">> formUrl not valid")
                                    break
                                
                                qaptchaKey = self._generatePass(37)
                                post_data2 = {'action':'qaptcha', 'qaptcha_key':qaptchaKey}
                                params2 = dict(self.defaultParams)
                                params2['header'] = dict(self.AJAX_HEADER)
                                params2['header']['Referer'] = url
                                sts, data = self.getPage(formUrl, params2, post_data2)
                                if not sts:
                                    break
                                printDBG(">>>>>>\n%s\n<<<<<<" % data)
                                
                                post_data2 = {'submit':'Valider', qaptchaKey:''}
                                sts, data = self.getPage(url, params2, post_data2)
                                if not sts:
                                    break
                                printDBG(">>>>>>\n%s\n<<<<<<" % data)
                                
                                url = self.cm.ph.getSearchGroups(data, '''['"](https?://[^"^"]*?dl\-protect\.co[^'^"]+?)['"]''', 1, True)[0]
                                if self.cm.isValidUrl(url):
                                    continue
                                break
                            else:
                                response.close()
                                break                            
                except Exception:
                    printExc()
                    continue
            
            if len(urlTab):
                break
            
            urlTab = self.up.getVideoLinkExt(url)
            if len(urlTab):
                break
            
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('SKStream.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('SKStream.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('SKStream.setInitListFromFavouriteItem')
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
            self.listMainMenu({'name':'category'})
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_cats_items')
        elif category == 'list_cats_items':
            self.listCatsItems(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, SKStream(), True, [])
    