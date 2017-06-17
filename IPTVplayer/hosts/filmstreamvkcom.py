# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import _unquote
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_execute
###################################################

###################################################
# FOREIGN import
###################################################
import time
import datetime
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://filmstreamvk.ws/'

class FilmstreamvkCom(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    MAIN_URL = 'http://filmstreamvk.ws/'
    DEFAULT_ICON_URL = 'http://filmstreamvk.ws/wp-content/themes/keremiyav4/logo/logo.png'
    MAIN_CAT_TAB = [{'category':'main',            'title':_('Main'),         'url':MAIN_URL,         },
                    {'category':'categories',      'title':_('Categories'),   'url':MAIN_URL,         },
                    {'category':'list_items',      'title':_('Series'),       'url':MAIN_URL+'serie', },
                    {'category':'list_items',      'title':_('Manga'),        'url':MAIN_URL+'manga', },
                    {'category':'search',          'title': _('Search'), 'search_item':True,          },
                    {'category':'search_history',  'title': _('Search history'),                      } ]
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmstreamvk.com', 'cookie':'filmstreamvkcom.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url, api=True):
        baseUrl = self.MAIN_URL
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  baseUrl + url
        if not baseUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("FilmstreamvkCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listMainCategories(self, cItem, category):
        printDBG("FilmstreamvkCom.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        self._listCategory(cItem, category, '<div class="tam"', '</ul>', data)
        self._listCategory(cItem, category, 'Accueil', '<ul class="sub-menu">', data)
        self._listCategory(cItem, category, '</ul>', 'CONTACT', data)
        
    
    def listCategories(self, cItem, category):
        printDBG("FilmstreamvkCom.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        self._listCategory(cItem, category, '<li class="cat-item cat', '</ul>', data)
        
    def _listCategory(self, cItem, category, m1, m2, data):
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2)[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'url':item[0], 'title':item[1]})
            self.addDir(params)
    
    def listItems(self, cItem, category):
        printDBG("FilmstreamvkCom.listItems")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '''rel=["']next["'][^>]+?href=['"]([^'^"]+?)['"]''')[0]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="moviefilm">', '<div class="filmcontent">')[1]
        data = data.split('<div class="moviefilm">')
        if len(data): del data[0]
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            title = self.cm.ph.getSearchGroups(item, '<a[^<]+?>([^<]+?)</a>')[0]
            desc  = self.cleanHtmlStr(item.replace(title, '').replace('</div>', '[/br]'))
            
            params = dict(cItem)
            params.update({'category':category, 'url':url, 'title':self.cleanHtmlStr(title), 'icon':icon, 'desc':desc})
            if 'saison-' in url or '/manga/' in url or '/serie/' in url:
                season = self.cm.ph.getSearchGroups(url+'-', 'aison-([0-9]+?)-' )[0]
                params['season'] = season
                self.addDir(params)
            else:
                self.addVideo(params)
            
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'url':nextPage})
            self.addDir(params)
    
    def listEpisodes(self, cItem, nextCategory):
        printDBG("FilmstreamvkCom.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'liste_episode', '</tr>')
        for idx in range(len(data)):
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data[idx], '>', '<', False)[1])
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 's_title':cItem['title'], 'erow_idx':idx})
            self.addDir(params)
            
    def listEpisodesByLanguage(self, cItem):
        printDBG("FilmstreamvkCom.listEpisodesByLanguage")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        descData  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filmalti">', '<div class="filmborder">')[1]
        desc = self.cleanHtmlStr(descData)
        icon = self.cm.ph.getSearchGroups(descData, '''src=['"]([^'^"]+?)['"]''')[0]
        titleSeason = self.cleanHtmlStr(cItem.get('s_title', '').split('Saison')[0])
        
        idx = cItem.get('erow_idx', 0)
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'liste_episode', '</tr>')
        if idx < len(data): data = data[idx]
        else: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if self.cm.isValidUrl(url):
                title = self.cleanHtmlStr(item)
                fullTitle = titleSeason + ' '
                if cItem['season'] != '':
                    fullTitle += 's%s' % str(cItem['season']).zfill(2)
                try:
                    title = int(title)
                    fullTitle += 'e%s' % str(title).zfill(2)
                except Exception:
                    fullTitle += ' %s' % str(title).zfill(2)
                
                urlName = url.split('-')[-1]
                if urlName != '': fullTitle += ' [%s]' %  urlName
                
                params = dict(cItem)
                params.update({'url':url, 'title':fullTitle, 'icon':icon, 'desc':desc})
                self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FilmstreamvkCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL + '?s=' + urllib.quote(searchPattern)
        self.listItems(cItem, 'episodes')
        
    def _getBaseVideoLink(self, wholeData):
        videoUrlParams = []
        tmpUrls = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(wholeData, '<iframe ', '</iframe>', withMarkers=True, caseSensitive=False)
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''',  grupsNum=1, ignoreCase=True)[0]
            if url in tmpUrls: continue
            tmpUrls.append(url)
            if url.startswith('http') and 'facebook.com' not in url and 1 == self.up.checkHostSupport(url):
                videoUrlParams.append({'name': self.up.getHostName(url), 'url':url, 'need_resolve':1})
                
        data = re.compile('''onclick=[^>]*?['"](http[^'^"]+?)['"]''').findall(wholeData)
        for url in data:
            if url in tmpUrls: continue
            tmpUrls.append(url)
            if 'facebook.com' not in url and 1 == self.up.checkHostSupport(url):
                videoUrlParams.append({'name': self.up.getHostName(url), 'url':url, 'need_resolve':1})
        return videoUrlParams
    
    def getLinksForVideo(self, cItem):
        printDBG("FilmstreamvkCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
            
        urlTab = self._getBaseVideoLink(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="keremiya_part">', '</div>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            name = self.cleanHtmlStr(item)
            if url.startswith('http'):
                urlTab.append({'name': name, 'url':url, 'need_resolve':1})
        
        if 1 == len(urlTab) and 'filmstreamvk' in self.up.getDomain(urlTab[0]['url']):
            sts, data = self.cm.getPage(urlTab[0]['url'])
            if not sts: return urlTab
            mainName = urlTab[0]['name']
            urlTab = self._getBaseVideoLink(data)
            for idx in range(len(urlTab)):
                urlTab[idx]['name'] = mainName + ' ' + urlTab[idx]['name']
            
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("FilmstreamvkCom.getVideoLinks [%s]" % url)
        urlTab = []
        
        videoUrl = ''
        if 'filmstreamvk' in self.up.getDomain(url):
            sts, data = self.cm.getPage(url)
            if not sts: return []
            tmoUrlTab = self._getBaseVideoLink(data)
            if len(tmoUrlTab):
                videoUrl = tmoUrlTab[0].get('url', '')
        else:
            videoUrl = url
        
        if videoUrl.startswith('http'):
            return self.up.getVideoLinkExt(videoUrl)
        return []
        
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
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'main':
            self.listMainCategories(self.currItem, 'list_items')
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'episodes')
        elif category == 'episodes':
            self.listEpisodes(self.currItem, 'episodes_by_language')
        elif category == 'episodes_by_language':
            self.listEpisodesByLanguage(self.currItem)
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
        CHostBase.__init__(self, FilmstreamvkCom(), True, [])
    