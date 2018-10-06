# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
try:    import json
except Exception: import simplejson as json
###################################################


def gettytul():
    return 'http://bajkipopolsku.com/'

class BajkiPoPolskuCOM(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'bajkipopolsku.com', 'cookie':'bajkipopolsku.com.cookie'})
        self.DEFAULT_ICON_URL = 'http://bajkipopolsku.com/wp-content/uploads/2015/04/bajkipopolsku-logo2.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'http://bajkipopolsku.com/'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'list_items',     'title': 'START',             'url':self.getMainUrl()},
                             {'category':'list_categories','title': 'SPIS ALFABETYCZNY', 'url':self.getMainUrl()},
                             {'category':'list_items',     'title': 'FILMY',             'url':self.getFullUrl('/category/fimly')},
                             
                             {'category':'search',         'title': _('Search'),          'search_item':True}, 
                             {'category':'search_history', 'title': _('Search history')},
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
    
    def listMainMenu(self, cItem, nextCategory):
        printDBG("BajkiPoPolskuCOM.listMainMenu")
        self.listsTab(self.MAIN_CAT_TAB, cItem)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("BajkiPoPolskuCOM.listCategories [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'categories'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            desc  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'desc':desc})
            self.addDir(params)
    
    def listItems(self, cItem, nextCategory):
        printDBG("BajkiPoPolskuCOM.listItems [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<link', '>', 'next'), ('<', '>'))[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0])
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<section', '>'), ('</section', '>'))
        items = []
        for dataItem in data:
            items.extend(self.cm.ph.getAllItemsBeetwenNodes(dataItem, ('<div', '>', 'post-'), ('<div', '>', 'clearfix')))
        
        self._listItems(cItem, nextCategory, items, nextPage)
            
    def _listItems(self, cItem, nextCategory, data, nextPage):
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''[\s\-]src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            desc  = [self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1])]
            
            tmp = self.cm.ph.getAllItemsBeetwenNodes(item, ('<i', '>', 'fa-'), ('</span', '>'))
            for t in tmp:
                if 'fa-eye' in t: label = 'Obejrzeń'
                elif 'fa-comment' in t: label = 'Kometarzy'
                elif 'fa-thumbs' in t: label = 'Polubień'
                else: continue
                t = self.cleanHtmlStr(t)
                if t != '': desc.insert(0, '%s: %s' % (label, t))
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':'[/br]'.join(desc)})
            if 'video' == nextCategory or 'video-item' in item:
                self.addVideo(params)
            else:
                params['category'] = nextCategory
                self.addDir(params)

        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'url':nextPage, 'page':cItem.get('page', 1)+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("BajkiPoPolskuCOM.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 1)
        
        if 1 == page: url = self.getFullUrl('?s=') + urllib.quote_plus(searchPattern)
        else: url = cItem['url']
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '''['"]nextLink['"]\s*:\s*['"](https?:[^'^"]+?)['"]''')[0].replace('\\/', '/')
        
        reObj = re.compile('<div[^>]+?post\-[^>]+?>')
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<section', '>'), ('</section', '>'))
        items = []
        for dataItem in data:
            tmp = reObj.split(dataItem)
            if len(tmp): del tmp[0]
            items.extend(tmp)
        
        self._listItems(cItem, 'video', items, nextPage)
        
    def getLinksForVideo(self, cItem):
        printDBG("BajkiPoPolskuCOM.getLinksForVideo [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'video-player'), ('<div', '>', 'clearfix'))[1]
        videoUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]).replace('&#038;', '&')
        return self.up.getVideoLinkExt(videoUrl)
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( ">> handleService: name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'}, 'list_genres')
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_items')
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
        CHostBase.__init__(self, BajkiPoPolskuCOM(), True, [])
    
    