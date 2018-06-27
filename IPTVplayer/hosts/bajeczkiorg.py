# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, RetHost, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import random
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

def gettytul():
    return 'http://bajeczki.org/'

class BajeczkiOrg(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'bajeczki.org', 'cookie':'bajeczki.org.cookie', 'cookie_type':'MozillaCookieJar'})
        self.MAIN_URL = 'http://bajeczki.org/'
        self.DEFAULT_ICON_URL = self.getFullIconUrl('/wp-content/uploads/1397134512_5b47d5c61cb3523b0ff67e3168ded910-1-640x360.jpg')
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'with_metadata':True, 'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheLinks = {}
    
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        return self.cm.getPage(url, addParams, post_data)
        
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [{'category':'categories',      'title': 'Wszystkie bajki',    'url':self.getFullUrl('/all-categories/')},
                        {'category':'search',          'title': _('Search'), 'search_item':True, },
                        {'category':'search_history',  'title': _('Search history'),             }]
        self.listsTab(MAIN_CAT_TAB, cItem)
    
    def listCategories(self, cItem, nextCategory):
        printDBG("BajeczkiOrg.listCategories")

        sts, data = self.getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'category-bar'), ('</div', '>'))
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''\shref=['"]([^"^']+?)['"]''')[0])
            if url == '': continue
            item = item.split('</span>', 1)
            title = self.cleanHtmlStr(item[0])
            desc  = self.cleanHtmlStr(item[-1])
            icon = url + '?fake=need_resolve.jpeg'
            params = dict(cItem)
            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("BajeczkiOrg.listItems")

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        descObj = re.compile('''<span[^>]+?>''')
        data = self.cm.ph.getDataBeetwenMarkers(data, '<main', '</main>', False)[1]
        printDBG(data)
        data = re.compile('<(?:div|article)[^>]+?hentry[^>]+?>').split(data)
        for idx in range(1, len(data), 1):
            item = data[idx]
            
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''\shref=['"]([^"^']+?)['"]''')[0] )
            if url == '': continue
            icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''<img[^>]+?src=['"]([^"^']+?\.(:?jpe?g|png)(?:\?[^"^']+?)?)['"]''')[0])
            item = item.split('</h2>', 1)
            title = self.cleanHtmlStr( item[0] )

            desc = []
            tmp = descObj.split(item[-1])
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': desc.append(t)
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':'[/br]'.join(desc)}
            self.addVideo(params)
    
    def listSubItems(self, cItem):
        printDBG("BajeczkiOrg.listSubItems")
        self.currList = cItem['sub_items']
        
    def getLinksForVideo(self, cItem):
        printDBG("BajeczkiOrg.getLinksForVideo [%s]" % cItem)
        urlTab = self.cacheLinks.get(cItem['url'], [])
        if len(urlTab): return urlTab
        
        self.cacheLinks = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'entry-content'), ('<button', '>'))[1]
        data = re.sub("<!--[\s\S]*?-->", "", data)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>', caseSensitive=False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', caseSensitive=False)
        for item in tmp:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0])
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''', ignoreCase=True)[0].lower()
            if 'mp4' in type:
                name = self.up.getDomain(url)
                urlTab.append({'name':name, 'url':strwithmeta(url, {'direct_link':True, 'Referer':cItem['url']}), 'need_resolve':1})
                
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '>', caseSensitive=False)
        for item in tmp:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0])
            if 1 == self.up.checkHostSupport(url):
                name = self.up.getDomain(url)
                urlTab.append({'name':name, 'url':strwithmeta(url, {'Referer':cItem['url']}), 'need_resolve':1})
        if len(urlTab):
            self.cacheLinks[cItem['url']] = urlTab
            
        return urlTab
    
    def getVideoLinks(self, videoUrl):
        printDBG("BajeczkiOrg.getVideoLinks [%s]" % videoUrl)
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
        if videoUrl.meta.get('direct_link'):
            return [{'name':'direct', 'url':videoUrl}]
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FilmeHD.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'category':'list_items', 'url':self.getFullUrl('/?s=') + urllib.quote_plus(searchPattern)})
        self.listItems(cItem)
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: >> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items')
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
        CHostBase.__init__(self, BajeczkiOrg(), True, [])
    