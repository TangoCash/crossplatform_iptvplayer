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
#config.plugins.iptvplayer.alltubetv_premium  = ConfigYesNo(default = False)
#config.plugins.iptvplayer.alltubetv_login    = ConfigText(default = "", fixed_size = False)
#config.plugins.iptvplayer.alltubetv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #if config.plugins.iptvplayer.alltubetv_premium.value:
    #    optionList.append(getConfigListEntry("  alltubetv login:", config.plugins.iptvplayer.alltubetv_login))
    #    optionList.append(getConfigListEntry("  alltubetv hasło:", config.plugins.iptvplayer.alltubetv_password))
    return optionList
###################################################


def gettytul():
    return 'http://watchwrestling.tc/'

class Watchwrestling(CBaseHostClass):
    MAIN_URL    = 'http://watchwrestling.tc/'
    SRCH_URL    = MAIN_URL + 'index.php?s='
    DEFAULT_ICON_URL = 'http://watchwrestling.to/wp-content/uploads/2014/11/ww_fb.png'
    
    MAIN_CAT_TAB = [{'category':'categories',  'title': _('Categories'), 'url':MAIN_URL,                                 'icon':DEFAULT_ICON_URL, 'm1':'Categories</h3>'},
                    {'category':'categories', 'title': _('Monthly'),     'url':MAIN_URL + 'video/watch-wwe-raw-101915/', 'icon':DEFAULT_ICON_URL, 'm1':'Monthly Posts</h3>'},
                    {'category':'live',       'title': _('LIVE 24/7'),   'url':MAIN_URL + 'watch-wwe-network-live/',     'icon':DEFAULT_ICON_URL, 'm1':'Monthly Posts</h3>'},
                    {'category':'search',             'title': _('Search'),       'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} 
                   ]
    
    SORT_TAB = [{'sort':'date',     'title':_('DATE')},
                {'sort':'views',    'title':_('VIEWS')},
                {'sort':'likes',    'title':_('LIKES')},
                {'sort':'comments', 'title':_('COMMENTS')}
               ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Watchwrestling', 'cookie':'Watchwrestling.cookie'})
        self.serversCache = []
        
    def _getFullUrl(self, url, series=False):
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Watchwrestling.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem, category):
        printDBG("Watchwrestling.listCategories")
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
            params.update({'title':title, 'url':self._getFullUrl(url), 'category':category})
            self.addDir(params)
            
    def listFilters(self, cItem, category):
        printDBG("Watchwrestling.listFilters")
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.SORT_TAB, cItem)
            
    def listMovies(self, cItem, category):
        printDBG("Watchwrestling.listMovies")
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
            params.update( {'category':category, 'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listServers(self, cItem, category):
        printDBG("Watchwrestling.listServers [%s]" % cItem)
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
        printDBG("Watchwrestling.listServers [%s]" % cItem)
        partIdx = cItem['part_idx']
        self.listsTab(self.serversCache[partIdx], cItem, 'video')
        
    def listLiveStreams(self, cItem):
        printDBG("Watchwrestling.listLiveStreams [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        sp = '<div style="text-align: center;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '</div>', False)[1]
        data = re.compile('href="([^"]+?)"[^>]*?>([^>]+?)</a>').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'title':item[1], 'url':item[0], 'Referer':cItem['url'], 'live':True})
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
        printDBG("Watchwrestling.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        Referer =  cItem.get('Referer', '')
        if 1 != self.up.checkHostSupport(url):  
            tries = 0
            while tries < 3:
                sts, data = self.cm.getPage(url, {'header':{'Referer':Referer, 'User-Agent':'Mozilla/5.0'}})
                if not sts: return urlTab
                data = data.replace('// -->', '')
                data = self._clearData(data)
                #printDBG(data)
                if 'eval(unescape' in data:
                    data = urllib.unquote(self.cm.ph.getSearchGroups(data, '''eval\(unescape\(['"]([^"^']+?)['"]''')[0])
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=['"]([^"^']+?)['"]''', 1, True)[0]
                if 'protect.cgi' in url:
                    Referer = cItem['url']
                else:
                    break
                tries += 1
        url = strwithmeta(url)
        url.meta['Referer'] = Referer
        url.meta['live'] = cItem.get('live', False)
        
        urlTab.append({'name':cItem['title'], 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Watchwrestling.getVideoLinks [%s]" % baseUrl)
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
        CHostBase.__init__(self, Watchwrestling(), True, []) #CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('watchwrestlinglogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie  
        searchTypesOptions.append((_("DATE"),         "date"))
        searchTypesOptions.append((_("VIEWS"),       "views"))
        searchTypesOptions.append((_("LIKES"),       "likes"))
        searchTypesOptions.append((_("COMMENTS"), "comments"))
        
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except Exception:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
