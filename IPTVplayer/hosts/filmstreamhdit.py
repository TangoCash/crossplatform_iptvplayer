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
import copy
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from datetime import datetime
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
    return 'http://filmstreamhd.it/'

class FilmStreamHD(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmstreamhd.it', 'cookie_type':'MozillaCookieJar', 'cookie':'filmstreamhd.it.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'http://filmstreamhd.it/'
        self.DEFAULT_ICON_URL = self.getFullIconUrl('/wp-content/themes/BLU/logo/logo.png')
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'home',           'title': _('Home')      },
                             {'category':'categories',     'title': _('Categories')},
                             {'category':'search',         'title': _('Search'), 'search_item':True},
                             {'category':'search_history', 'title': _('Search history'), } 
                            ]

    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
    
    def listCategories(self, cItem, category, m1):
        printDBG("FilmStreamHD.listCategories")
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', m1), ('</ul', '>'), False)[1]
        data = re.compile('''<a[^>]+?href=['"]([^"^']+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'title':self.cleanHtmlStr(item[1]), 'url':self.getFullUrl(item[0])})
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("FilmStreamHD.listItems")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'nextpostslink'), ('</a', '>'))[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^"^']+?)['"]''')[0])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'moviefilm'), ('<div', '>', 'filmborder'))[1]
        data = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</div', '>'), ('<div', '>', 'moviefilm'))
        for item in data:
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0])
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''')[0])
            
            desc = []
            item = self.cm.ph.getAllItemsBeetwenMarkers(item.split('</a>')[-1], '<div', '</div>')
            for t in item:
                t = self.cleanHtmlStr(t)
                if t != '': desc.append(t)
                
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':icon, 'desc':' | '.join(desc)})
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'url':nextPage, 'page':cItem.get('page', 1)+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/?s=') + urllib.quote_plus(searchPattern)
        cItem['category'] = 'list_items'
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("FilmStreamHD.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '-player-'), ('</script', '>'), False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '"source"', ']')[1]
        data = re.compile('''['"]url['"]\s*?:\s*?['"]([^'^"]+?)['"]''').findall(data)
        for item in data:
            url = self.getFullUrl(item.replace('\\/', '/'))
            urlTab.append({'name':self.up.getHostName(url), 'url':strwithmeta(url, {'Referer':cUrl, 'User-Agent':self.USER_AGENT}), 'need_resolve':0})

        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("FilmStreamHD.getArticleContent [%s]" % cItem)
        
        retTab = []
        
        otherInfo = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'filmaltiaciklama'), ('<div', '>', 'filmborder'))[1]
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'konuozet'), ('</div', '>'))[1])
        icon = ''
        title = ''
        
        keysMap = {'Genere':        'genre',
                   'IMDB':          'imdb_rating',
                   'Anno':          'year',
                   'Scrittori':     'writers',
                   'Attori':        'actors',
                   'votes':         'views'}
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<p', '>'), ('</p', '>'))
        for item in data:
            item = item.split('</span>', 1)
            if len(item) != 2: continue
            val = self.cleanHtmlStr(item[-1].replace('</a>', ', ')).replace(', ,', ',')
            if val.endswith(','): val = val[:-1]
            key = self.cleanHtmlStr(item[0])
            if key not in keysMap: continue
            otherInfo[keysMap[key]] = val
        
        if title == '': title = cItem['title']
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
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
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items', 'sidebar-right')
        elif category == 'home':
            self.listCategories(self.currItem, 'list_items', 'leftC')
    #ITEMS
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
        CHostBase.__init__(self, FilmStreamHD(), True)
        
    def withArticleContent(self, cItem):
        if 'video' == cItem.get('type', ''):
            return True
        else: return False
