# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import urlparse
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
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://watchwrestling.uno/'

class WatchwrestlingUNO(CBaseHostClass):
    MAIN_URL    = 'http://watchwrestling.uno/'
    SRCH_URL    = MAIN_URL + 'index.php?s='
    DEFAULT_ICON_URL = 'http://watchwrestling.uno/wp-content/uploads/2016/03/wwunologo2.png'
    
    MAIN_CAT_TAB = [{'category':'categories',  'title': _('Categories'), 'url':MAIN_URL,                                      'm1':'Categories</h3>'},
                    {'category':'categories', 'title': _('Monthly'),     'url':MAIN_URL + 'video/watch-wwe-raw-101915/',      'm1':'Monthly Posts</h3>'},
                    {'category':'live',       'title': _('LIVE 24/7'),   'url':MAIN_URL + 'watch-wwe-network-247-live-free/'},
                    {'category':'search',             'title': _('Search'),       'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} 
                   ]
    
    SORT_TAB = [{'sort':'date',     'title':_('DATE')},
                {'sort':'views',    'title':_('VIEWS')},
                {'sort':'likes',    'title':_('LIKES')},
                {'sort':'comments', 'title':_('COMMENTS')}
               ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'watchwrestling.uno', 'cookie':'watchwrestling.uno.cookie'})
        self.serversCache = []

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("WatchwrestlingUNO.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem, category):
        printDBG("WatchwrestlingUNO.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, cItem['m1'], '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''')[0]
            if url == '': continue
            title  = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'title':title, 'url':self.getFullUrl(url), 'category':category})
            self.addDir(params)
            
    def listFilters(self, cItem, category):
        printDBG("WatchwrestlingUNO.listFilters")
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.SORT_TAB, cItem)
            
    def listMovies(self, cItem, category):
        printDBG("WatchwrestlingUNO.listMovies")
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%d/' % page
        if '?' in url:
            url += '&'
        else: url += '?'
        url += 'orderby=%s' % cItem['sort']
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        if '<div class="loop-nav pag-nav">' in data:
            m2 = '<div class="loop-nav pag-nav">'
        else:
            m2 = '<div id="sidebar"'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="nag cf">', m2, False)[1]
        
        data = data.split('<div id="post-')
        if len(data): del data[0]
        
        for item in data:
            tmp    = item.split('<p class="stats">')
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            desc   = tmp[-1]
            params = dict(cItem)
            params.update( {'category':category, 'title': self.cleanHtmlStr( title ), 'url':self.getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self.getFullIconUrl(icon)} )
            self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listServers(self, cItem, category):
        printDBG("WatchwrestlingUNO.listServers [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        self.serversCache = []
        matchObj = re.compile('href="([^"]+?)"[^>]*?>([^>]+?)</a>')
        sp = '<div style="text-align: center;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="extras">', False)[1]
        data = data.split(sp)
        if len(data): del data[0]
        for item in data:
            sts, serverName = self.cm.ph.getDataBeetwenMarkers(item, 'geneva;">', '</span>', False)
            if not sts: continue
            parts = matchObj.findall(item)
            partsTab = []
            for part in parts:
                partsTab.append({'title':cItem['title'] + '[%s]' % part[1], 'url':part[0], 'Referer':cItem['url']})
            if len(partsTab):
                params = dict(cItem)
                params.update( {'category':category, 'title':serverName, 'part_idx':len(self.serversCache)} )
                self.addDir(params)
                self.serversCache.append(partsTab)
        
    def listParts(self, cItem):
        printDBG("WatchwrestlingUNO.listServers [%s]" % cItem)
        partIdx = cItem['part_idx']
        self.listsTab(self.serversCache[partIdx], cItem, 'video')
        
    def listLiveStreams(self, cItem):
        printDBG("WatchwrestlingUNO.listLiveStreams [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        baseUrl = self.cm.ph.getSearchGroups(data, '''<base[^>]+?href=["'](https?://[^"^']+?)['"]''')[0]
        sp = '<div style="text-align: center;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<p style="text-align: center;"><a', '</p>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>', True)
        for item in data:
            title  = self.cleanHtmlStr(item)
            url    = urlparse.urljoin(baseUrl, self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)['"]''')[0])
            params = dict(cItem)
            params.update({'title':title, 'url':strwithmeta(url, {'live':True, 'Referer':cItem['url']}), 'live':True})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url']  = self.SRCH_URL + searchPattern
        cItem['sort'] = searchType
        self.listMovies(cItem, 'list_server')
        
    def _clearData(self, data):
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        return data
        
    def getLinksForVideo(self, cItem):
        printDBG("WatchwrestlingUNO.getLinksForVideo [%s]" % cItem)
        urlTab = []
        live = cItem.get('live', False)
        if live: return [{'name':cItem['title'], 'url':cItem['url'], 'need_resolve':1}]
        
        url = strwithmeta(cItem['url'])
        referer =  url.meta.get('Referer', '')
        if 1 != self.up.checkHostSupport(url):  
            tries = 0
            while tries < 3:
                sts, data = self.cm.getPage(url, {'header':{'Referer':referer, 'User-Agent':'Mozilla/5.0'}})
                if not sts: return urlTab
                data = data.replace('// -->', '')
                data = self._clearData(data)
                #printDBG(data)
                if 'eval(unescape' in data:
                    data = urllib.unquote(self.cm.ph.getSearchGroups(data, '''eval\(unescape\(['"]([^"^']+?)['"]''')[0])
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=['"]([^"^']+?)['"]''', 1, True)[0]
                if '/cgi-bin/' in url:
                    referer = cItem['url']
                else:
                    break
                tries += 1
        url = strwithmeta(url)
        url.meta['Referer'] = referer
        url.meta['live'] = cItem.get('live', False)
        
        urlTab.append({'name':cItem['title'], 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("WatchwrestlingUNO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        url = strwithmeta(baseUrl)
        if url.meta.get('live'):
            urlTab = self.up.getAutoDetectedStreamLink(url)
        else:
            urlTab = self.up.getVideoLinkExt(url)
        return urlTab

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
            self.listCategories(self.currItem, 'list_filters')
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_movies')
    #MOVIES
        elif category == 'list_movies':
            self.listMovies(self.currItem, 'list_server')
        elif category == 'list_server':
            self.listServers(self.currItem, 'list_parts')
        elif category == 'list_parts':
            self.listParts(self.currItem)
    #LIVE
        elif category == 'live':
            self.listLiveStreams(self.currItem)
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
        CHostBase.__init__(self, WatchwrestlingUNO(), True, []) #CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO