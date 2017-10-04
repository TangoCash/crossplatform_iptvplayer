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
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
###################################################

###################################################
# FOREIGN import
###################################################
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
    return 'http://vumoo.li/'

class Vumoo(CBaseHostClass):
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
    MAIN_URL    = 'http://vumoo.li/'
    SRCH_URL    = MAIN_URL + 'videos/vsearch/?search='
    DEFAULT_ICON_URL = 'http://www.matrixable.org/wp-content/uploads/2016/02/vumoo.jpg'
    
    MAIN_CAT_TAB = [{'category':'movies',         'title': _('Movies'),       'url':MAIN_URL                                          },
                    {'category':'list_items',     'title': _('TV Shows'),     'url':MAIN_URL + 'videos/category/trending-television'  },
                    {'category':'search',         'title': _('Search'),       'search_item':True},
                    {'category':'search_history', 'title': _('Search history')} 
                   ]
    MOVIES_TAB = [{'category':'genres',          'title':_('Genres')},
                  {'category':'list_items',      'title':_('Currently Watching'),      'url':MAIN_URL + 'videos/category/currently-watching'},
                  {'category':'list_items',      'title':_('Popular this Week'),       'url':MAIN_URL + 'videos/category/popular-this-week'},
                  {'category':'list_items',      'title':_('IMDB Top Rated'),          'url':MAIN_URL + 'videos/category/top-rated-imdb'},
                  {'category':'list_items',      'title':_('IMDB Top Rated'),          'url':MAIN_URL + 'videos/category/top-rated-imdb'},
                  {'category':'list_items',      'title':_('New Releases'),            'url':MAIN_URL + 'videos/category/new-releases'},
                  {'category':'list_items',      'title':_('Recently Added'),          'url':MAIN_URL + 'videos/category/recently-added'},
                 ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Vumoo', 'cookie':'Vumoo.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.genresCache = []
        self.linksCache = {}
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':'vumoo.at', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
        
    def listGenres(self, cItem, category):
        printDBG("Vumoo.listGenres")

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="multi-column-dropdown">', '<button', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            params = dict(cItem)
            if title != '' and url != '':
                params.update({'category':category, 'title':title, 'url':url})
                self.addDir(params)
        
    def fillTvShowFilters(self, url):
        printDBG("Vumoo.fillTvShowFilters")
        self.tvshowGenresCache = []
        sts, data = self.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Subgenres', '<section', False)[1]
        data = data.split('<li>')
        if len(data): del data[0]
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            if url.startswith('http'):
                self.tvshowGenresCache.append({'title':title, 'url':url})
        
    def listTvShowsGenres(self, cItem, category):
        printDBG("Vumoo.listTvShowsGenres")
        if 0 == len(self.tvshowGenresCache):
            self.fillTvShowFilters(cItem['url'])
        
        if len(self.tvshowGenresCache):
            tab = [{'title':_('--All--'), 'url':cItem['url']}]
            cItem = dict(cItem)
            cItem['category'] = category
            tab.extend(self.tvshowGenresCache)
            self.listsTab(tab, cItem)
            
    def listItems(self, cItem, category='explore_item', post_data=None):
        printDBG("Vumoo.listItems")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        url += '?'
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page=%d&' % page
        if post != '': 
            url += post
        
        sts, data = self.getPage(url, post_data=post_data)
        if not sts: return
        
        nextPage = False
        
        num = 0
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<article', '</article>')       
        for item in data:
            num += 1
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            if icon == '': icon = self.cm.ph.getDataBeetwenMarkers(item, 'url(', ')', False)[1].strip()
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            if title == '': title = self.cm.ph.getSearchGroups(item, 'data-title="([^"]+?)"')[0]
            
            if url != '' and title != '': 
                params = dict(cItem)
                params.update( {'title': self.cleanHtmlStr( title ), 'url':self.getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self.getFullUrl(icon)} )
                params['category'] = category
                self.addDir(params)
        
        if nextPage or num >= 20:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def exploreItem(self, cItem, category):
        printDBG("Vumoo.exploreItem")
        self.linksCache = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        if 'tv-details-seasons' in data: type = 'tv'
        else: type = 'movie'
            
        if type == 'movie':
            printDBG('Vumoo.exploreItem - MOVIE')
            mov_id = self.cm.ph.getSearchGroups(data, '''mov_id[\s]*=[\s]*["']([0-9]+?)["']''')[0]
            t_id   = self.cm.ph.getSearchGroups(data, '''t_id[\s]*=[\s]*["']([0-9]+?)["']''')[0]
            openloadLink  = self.cm.ph.getSearchGroups(data, 'openloadLink[\s]*=[\s]*"(http[^"]+?)"')[0].replace('\\/', '/')
            self.linksCache[mov_id] = []
            if self.cm.isValidUrl(openloadLink):
                self.linksCache[mov_id].append({'type':'openload', 'url':openloadLink})
            
            data = self.cm.ph.getDataBeetwenMarkers(data, 'var fileId', '$.get')[1]
            try:
                jscode = data[:data.rfind(';')+1]
                try:
                    jscode = 'function setInterval() {};\nvar APP_PATH="%s";\n%s\nprint(url);' % (self.getMainUrl(), jscode)
                    printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
                    printDBG(jscode)
                    printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    ret = iptv_js_execute( jscode )
                    if ret['sts'] and 0 == ret['code']:
                        decoded = ret['data'].strip()
                        printDBG('DECODED DATA -> [%s]' % decoded)
                    sts, data = self.getPage(decoded)
                    data = byteify(json.loads(data))
                    for item in data:
                        printDBG(item)
                        if 'mp4' not in item.get('type', ''): continue
                        self.linksCache[mov_id].append({'type':item.get('label', str(item.get('res'))), 'url':self.getFullUrl(item['src'])})
                except Exception:
                    printExc()
            except Exception:
                printExc()
            
            params = dict(cItem)
            params.update({'links_id':mov_id, 't_id':t_id})
            self.addVideo(params)
        elif type == 'tv':
            printDBG('Vumoo.exploreItem - TV SERIES')
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tv-details-episodes synopsis-container">', '</ol>')[1]
            sp = '<li id=season'
            data = data.split(sp)
            if len(data): del data[0]
            num = 0 
            for item in data:
                num += 1
                item = sp + item
                tmp = self.cm.ph.getSearchGroups(item, 'season([0-9]+?)-([0-9]+?)[^0-9]', 2)
                sNum = tmp[0]
                eNum = tmp[1]
                title = ''
                if '' != eNum and '' != sNum: title = 's%se%s ' % (sNum.zfill(2), eNum.zfill(2))
                title += self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
                
                links_id = title + str(num)
                self.linksCache[links_id] = []
                tmp = re.compile('<[^>]+?id="([^"]+?)"[^>]+?data-click="([^"]+?)"').findall(item)
                for tmpItem in tmp:
                    link = tmpItem[1].strip()
                    name = tmpItem[0].strip()
                    if 'main-' in name: name = 'Main ' + name.split('main-', 1)[-1]
                    else: name = self.up.getHostName(link)
                    
                    if link.startswith('http') and '://' in link and 'ubershared.co' not in link:
                        self.linksCache[links_id].append({'type':name, 'url':link})
                    elif '/plink' in link:
                        link = self.getFullUrl(link)
                        self.linksCache[links_id].append({'type':name, 'url':link})
                        
                if len(self.linksCache[links_id]):
                    params = dict(cItem)
                    params.update({'title':'{0}: {1}'.format(cItem['title'], title), 'links_id':links_id, 'desc': self.cleanHtmlStr( item ) }) #, 'icon':self.getFullUrl(icon)})
                    self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        post_data = None
        
        params = dict(self.defaultParams)
        params['header'] = {'User-Agent':self.USER_AGENT, 'Referer':self.getMainUrl()}
        
        url  = self.SRCH_URL + urllib.quote_plus(searchPattern)
        sts, data = self.getPage(url, params)
        if not sts: return 
        
        printDBG(data)
        
        if 'window.location' in data: 
            url = self.cm.ph.getSearchGroups(data, '''window\.location[^'^"]+?['"]([^'^"]+?)['"]''')[0]
            params['header']['Referer'] = url
            
            sts, data = self.getPage(url, params)
            if not sts: return 
            
            printDBG(data)
            
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False, False)[1]
            post_data = dict(re.findall('''<input[^>]*name=['"]([^"^']*)['"][^>]*value=['"]([^"^']*)['"][^>]*>''', tmp))
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p', '</p>', False, False)[1])
            post_data['action'] = self.cm.ph.getSearchGroups(tmp, '[^0-9]([0-9]+?)[^0-9]')[0]
        cItem['url'] = url
        self.listItems(cItem, 'explore_item', post_data)
        
    def getLinksForVideo(self, cItem):
        printDBG("Vumoo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        linksID = cItem.get('links_id', 'none')
        if linksID in self.linksCache:
            for item in self.linksCache[linksID]:
                params = {'name':item['type'], 'url':strwithmeta(item['url'], {'Referer':cItem['url']}), 'need_resolve':1}
                if '/plink' in item['url']: params['need_resolve'] = 0
                urlTab.append(params)
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Vumoo.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        urlTab = self.up.getVideoLinkExt(baseUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
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
    #ITEMS
        elif category == 'movies':
            self.listsTab(self.MOVIES_TAB, self.currItem)
        elif category == 'genres':
            self.listGenres(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
    #EXPLORE
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
            
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
        CHostBase.__init__(self, Vumoo(), True, [])#[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])