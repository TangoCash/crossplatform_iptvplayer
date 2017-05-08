# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
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
    return 'http://filmezz.eu/'

class AnimeTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmezz.eu', 'cookie':'filmezzeu.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://plugins.movian.tv/data/3c3f8bf962820103af9e474604a0c83ca3b470f3'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'http://filmezz.eu/'
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': _('Home'),               'url':self.getFullUrl('kereses.php')   },
                             {'category':'list_items',      'title': _('Movies'),             'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=1&h=0&o=feltoltve')  },
                             {'category':'list_items',      'title': _('Series'),             'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=2&h=0&o=feltoltve')  },
                             {'category':'list_items',      'title': _('Top movies'),         'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=1&h=0&o=nezettseg')  },
                             {'category':'list_items',      'title': _('Top series'),         'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=2&h=0&o=nezettseg')  },
                             {'category':'list_items',      'title': _('Latest added'),       'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=0&h=0&o=feltoltve')  },
                             
                             {'category':'search',            'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',    'title': _('Search history'),            } 
                            ]
                            
    def getFullIconUrl(self, url):
        url = url.replace('&amp;', '&')
        return CBaseHostClass.getFullIconUrl(self, url)
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def fillCacheFilters(self, cItem):
        printDBG("AnimeTo.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                if title in ['Összes']:
                    addAll = False
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('All')})
                self.cacheFiltersKeys.append(key)
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="row form-group">', '</select>')
        for tmp in data:
            key = self.cm.ph.getSearchGroups(tmp, '''name="([^"]+?)"''')[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')
            addFilter(tmp, 'value', key, False)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("AnimeTo.listFilters")
        cItem = dict(cItem)
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if 0 == len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("AnimeTo.listItems")
        url = cItem['url']
        page = cItem.get('page', 0)
        
        query = {}
        if page > 0: query['p'] = page
        
        for key in self.cacheFiltersKeys:
            baseKey = key[2:] # "f_"
            if key in cItem: query[baseKey] = urllib.quote(cItem[key])
        
        query = urllib.urlencode(query)
        if '?' in url: url += '&' + query
        else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>')[1]
        if  '' != self.cm.ph.getSearchGroups(nextPage, 'p=(%s)[^0-9]' % (page+1))[0]: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'movie-list', '<footer class="footer">')[1]        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</a>')
        reDescObj = re.compile('title="([^"]+?)"')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            if 'kereses.php' in url: continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="title">', '</span>')[1] )
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            
            # desc start
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li>', '</li>')
            descTab = []
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t == '': continue
                descTab.append(t)
            tmp = self.cm.ph.getDataBeetwenMarkers(item, 'movie-icons">', '</ul>', False)[1]
            t = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="cover-element imdb"', '</span>')[1])
            tmp = reDescObj.findall(tmp)
            if t != '': tmp.insert(0, t)
            descTab.insert(0, ' | '.join(tmp))
            ######
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'desc':'[/br]'.join(descTab), 'icon':icon}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("AnimeTo.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text"', '</div>')[1])
        
        # trailer 
        tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<a[^>]+?class="venobox"'), re.compile('>'))[1]
        url = self.cm.ph.getSearchGroups(tmp, '''href=['"]([^'^"]+?)['"]''')[0]
        title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(tmp, '''title=['"]([^'^"]+?)['"]''')[0])
        if 1 == self.up.checkHostSupport(url):
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':title, 'prev_title':cItem['title'], 'url':url, 'prev_url':cItem['url'], 'prev_desc':cItem.get('desc', ''), 'desc':desc})
            self.addVideo(params)
        
        reDescObj = re.compile('title="([^"]+?)"')
        titlesTab = []
        self.cacheLinks  = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, 'url-list', '</section>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="col-sm-4 col-xs-12 host">', '</a>')
        for tmp in data:
            dTab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div', '</div>')
            if len(dTab) < 2: continue 
            title = self.cleanHtmlStr(dTab[1])
            
            # serverName
            t = self.cm.ph.getDataBeetwenMarkers(tmp, 'movie-icons">', '<div', False)[1]
            serverName = reDescObj.findall(t)
            if t != '': serverName.append(self.cleanHtmlStr(t))
            serverName = ' | '.join(serverName)
            #if 'letöltés' in serverName: continue
            
            url = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''(/link_to\.php\?id=[^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            
            if title not in titlesTab:
                titlesTab.append(title)
                self.cacheLinks[title] = []
            self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        
        for item in titlesTab:
            params = dict(cItem)
            title = cItem['title']
            if item != '': title += ' : ' + item
            params.update({'good_for_fav': False, 'title':title, 'links_key':item, 'prev_desc':cItem.get('desc', ''), 'desc':desc})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('kereses.php?s=' + urllib.quote_plus(searchPattern))
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("AnimeTo.getLinksForVideo [%s]" % cItem)
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        
        key = cItem.get('links_key', '')
        return self.cacheLinks.get(key, [])
        
    def getVideoLinks(self, videoUrl):
        printDBG("AnimeTo.getVideoLinks [%s]" % videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
                        
        try:         
            sts, response = self.cm.getPage(videoUrl, {'return_data':False})
            videoUrl = response.geturl()
            response.close()
        except Exception:
            printExc()
            return []
        
        if self.up.getDomain(self.getMainUrl()) in videoUrl:
            sts, data = self.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('AnimeTo.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('AnimeTo.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('AnimeTo.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def getArticleContent(self, cItem):
        printDBG("AnimeTo.getArticleContent [%s]" % cItem)
        retTab = []
        
        url = cItem.get('prev_url', '')
        if url == '': url = cItem.get('url', '')
        
        sts, data = self.getPage(url)
        if not sts: return retTab
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text"', '</div>')[1])
        if desc == '': desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta[^>]+?name="description"[^>]+?content="([^"]+?)"')[0] )
        titleData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="title"', '</div>')[1]
        
        title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(titleData, '<h1', '</h1>')[1] )
        altTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(titleData, '<h2', '</h2>')[1] )
        if title != '': title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta[^>]+?name="title"[^>]+?content="([^"]+?)"')[0] )
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<link[^>]+?rel="image_src"[^>]+?href="([^"]+?)"')[0] )
        
        if title == '': title = cItem['title']
        if desc == '':  title = cItem['desc']
        if icon == '':  title = cItem['icon']
        
        descTabMap = {"Kategória":    "genre",
                      "Rendező":      "director",
                      "Hossz":        "duration"}
        
        otherInfo = {}
        descData = cItem.get('prev_desc', '')
        if descData == '': descData = cItem.get('desc', '')
        descData = descData.split('[/br]')
        for item in descData:
            item = item.split(':')
            key = item[0]
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = self.cleanHtmlStr(item[-1])
                except Exception: continue
        
        imdb_rating = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<span class="score">', '</span>', False)[1])
        if imdb_rating != '': otherInfo['imdb_rating'] = imdb_rating
        
        if altTitle != '': otherInfo['alternate_title'] = altTitle
        year = self.cm.ph.getSearchGroups(cItem.get('prev_title', ''), '\(([0-9]{4})\)')[0]
        if year == '': year = self.cm.ph.getSearchGroups(cItem['title'], '\(([0-9]{4})\)')[0]
        if year != '': otherInfo['year'] = year
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        
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
            self.cacheLinks = {}
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
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
        CHostBase.__init__(self, AnimeTo(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] != 'explore_item'):
            return False
        return True
    
    