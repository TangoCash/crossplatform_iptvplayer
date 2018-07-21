# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import time
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
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'https://andrija-i-andjelka.com/'

class AndrijaIAndjelka(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'andrija-i-andjelka.com', 'cookie':'andrija-i-andjelka.com.cookie', 'min_py_ver':(2,7,9)})
        
        self.USER_AGENT = 'Mozilla/5.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'} )
        
        self.MAIN_URL = 'https://andrija-i-andjelka.com/'
        #https://previews.123rf.com/images/yusufsangdes89/yusufsangdes891507/yusufsangdes89150700042/42557652-cinema-camera-icon-movie-lover-series-icon.jpg
        self.DEFAULT_ICON_URL = 'https://img00.deviantart.net/972b/i/2010/241/0/4/tv_series_icon_set_by_silentbang-d2xl0kj.jpg'
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
    
    def listMainMenu(self, cItem):
        printDBG("AndrijaIAndjelka.listMainMenu")

        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        categories = []
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<li', '>', 'has-children'), ('</ul', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        for item in tmp:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'name':'category', 'category':'list_items', 'title':title, 'url':url})
            categories.append(params)

        if len(categories):
            title = categories[0]['title']
            categories[0]['title'] = _('--All--')
            params = dict(cItem)
            params.update({'category':'sub_items',  'title':title, 'sub_items':categories})
            self.addDir(params)

        MAIN_CAT_TAB = [{'category':'list_items',      'title':'NAJNOVIJE', 'url':self.getMainUrl()          },
                        {'category':'list_series',     'title':'SERIJE',    'url':self.getFullUrl('serije/') },
                        {'category':'search',          'title': _('Search'), 'search_item':True},
                        {'category':'search_history',  'title': _('Search history')} ]
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def listItems(self, cItem):
        printDBG("AndrijaIAndjelka.listItems")
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])
        
        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<nav', '>', 'pagination'), ('</nav', '>'), False)[1]
        nextPage = self.cm.ph.getSearchGroups(nextPage, '''<a[^>]+?href=['"]([^'^"]+?/%s[^0-9][^'^"]*?)['"]''' % (page + 1))[0]

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<article', '>', 'post-'), ('</article', '>'), False)
        for item in data:
            icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''<img[^>]+?src=['"]([^"^']+?)['"]''')[0] )
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<h', '>', 'title'), ('</h', '>'), False)[1] )

            params = dict(cItem)
            params.update({'good_for_fav': True, 'title':title, 'url':url, 'icon':icon})
            self.addVideo(params)

        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'url':nextPage, 'page':page+1})
            self.addDir(params)
            
    def listSeries(self, cItem, nextCategory):
        printDBG("AndrijaIAndjelka.listSeries")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<article', '>', 'post-'), ('</article', '>'), False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<td', '</td>')
        for item in data:
            icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''<img[^>]+?src=['"]([^"^']+?)['"]''')[0] )
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr( item )

            params = dict(cItem)
            params.update({'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AndrijaIAndjelka.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/?s=') + urllib.quote_plus(searchPattern)
        cItem['category'] = 'list_items'
        self.listItems(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("AndrijaIAndjelka.getLinksForVideo [%s]" % cItem)
        urlTab = []

        sts, data = self.getPage(cItem['url'])
        if not sts: return urlTab

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', caseSensitive=False)
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0])
            if 1 == self.up.checkHostSupport(url): 
                name = self.up.getHostName(url) #, nameOnly=True)
                url = strwithmeta(url, {'Referer':cItem['url']})
                urlTab.append({'name':name, 'url':url, 'need_resolve':1})

        return urlTab

    def getVideoLinks(self, videoUrl):
        printDBG("AndrijaIAndjelka.getVideoLinks [%s]" % videoUrl)
        return  self.up.getVideoLinkExt(videoUrl)

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: || name[%s], category[%s] " % (name, category) )
        self.currList = []
        self.currItem = dict(self.currItem)
        self.currItem.pop('good_for_fav', None)
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category', 'type':'category'})
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_items')
        elif category == 'sub_items':
            self.currList = self.currItem.get('sub_items', [])
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
        CHostBase.__init__(self, AndrijaIAndjelka(), True, favouriteTypes=[]) 

