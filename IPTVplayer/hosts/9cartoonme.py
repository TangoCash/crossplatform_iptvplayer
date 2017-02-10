# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import urlparse
import unicodedata
import string
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
#config.plugins.iptvplayer.CartoonME_language = ConfigSelection(default = "en", choices = [("en", _("English")), ("es", _("Spanish"))])

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry(_("Language:"), config.plugins.iptvplayer.CartoonME_language))
    return optionList
###################################################


def gettytul():
    return 'http://9cartoon.me/'

class CartoonME(CBaseHostClass):
    USER_AGENT = 'curl/7'

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'9cartoon.me', 'cookie':'CartoonME.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://9cartoon.me/'
        self.SEARCH_URL = self.MAIN_URL +'Search?s='
        
        self.DEFAULT_ICON  = "http://www.siwallpaperhd.com/wp-content/uploads/2015/07/spongebob_squarepants_face_wallpaper_hd_8_cartoon-724x453.png"
        self.MAIN_CAT_TAB = [{'category':'list_types',  'title': _('Cartoon list'),   'url':self.MAIN_URL+'CartoonList', 'icon':self.DEFAULT_ICON},
                             {'category':'categories',  'title': _('Genres'),         'url':self.MAIN_URL, 'icon':self.DEFAULT_ICON},
                             {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':self.DEFAULT_ICON},
                             {'category':'search_history',  'title': _('Search history'),             'icon':self.DEFAULT_ICON} ]
        
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':'9cartoon.me', 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
        
    def getIconUrl(self, url):
        url = self.getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def listCategories(self, cItem, nextCategory):
        printDBG("CartoonME.listCategories")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'genre right">', '</ul>', False)[1]
        data = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            title = self.cleanHtmlStr(item[1])
            url   = self.getFullUrl(item[0])
            tab.append({'title':title, 'url':url})
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
        
    def listCartoonListTypes(self, cItem, nextCategory):
        printDBG("CartoonME.listCartoonListTypes")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="list_search">', '</ul>', False)[1]
        data = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            title = self.cleanHtmlStr(item[1])
            url   = self.getFullUrl(item[0])
            tab.append({'title':title, 'url':url})
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
        
    def listLetters(self, cItem, nextCategory):
        printDBG("CartoonME.listLetters")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tab = []
        data = self.cm.ph.rgetDataBeetwenMarkers(data, '<div class="list_search">', '<div class="anime_list_body">', False)[1]
        data = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            title = self.cleanHtmlStr(item[1])
            url   = self.getFullUrl(item[0])
            tab.append({'title':title, 'url':url})
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
        
    def listItems1(self, cItem, nextCategory):
        printDBG("CartoonME.listItems1")
        
        page = cItem.get('page', 1)
        url = cItem['url']
        tmp = url.split('?')
        url = tmp[0]
        if len(tmp)>1: query = tmp[1]
        else: query = ''
        
        if not url.endswith('/'): url += '/'
        if page > 1: url += '?page=%d&' % page
        else: url += '?'
        if query != '': url += query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="pagination">', '<!-- end pager -->', False)[1]
        if ('>%d<' % (page+1)) in nextPage: nextPage = True
        else: nextPage = False
        
        m1 = '<div class="anime_movies_items">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '</section>', False)[1]
        data = data.split(m1)
        for item in data:
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<p class="name">', '</p>', True)[1] )
            if title == '': title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0] )
            
            if url.startswith('http'):
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon})
                if '/WATCH/' in url.upper():
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def listItems2(self, cItem, nextCategory):
        printDBG("CartoonME.listItems2")
        
        page = cItem.get('page', 1)
        url = cItem['url']
        tmp = url.split('?')
        url = tmp[0]
        if len(tmp)>1: query = tmp[1]
        else: query = ''
        
        if not url.endswith('/'): url += '/'
        if page > 1: url += '?page=%d&' % page
        else: url += '?'
        if query != '': url += query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="pagination">', '<!-- end pager -->', False)[1]
        if ('>%d<' % (page+1)) in nextPage: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="anime_list_body">', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            tmp   = self.cm.ph.rgetDataBeetwenMarkers(item, '<a', '</a>')[1]
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(tmp, '''href=['"]([^'^"]+?)['"]''')[0] )
            title = self.cleanHtmlStr( tmp )
            desc  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''title=[']([^']+?)[']''')[0] )
            
            if url.startswith('http'):
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
                if '/WATCH/' in url.upper():
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("CartoonME.listEpisodes")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="anime_info_body">', '</ul>', False)[1]
        data = data.split('<ul id="episode_related">')
        if len(data) < 2: return
        
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data[0], '''src=['"]([^"^']+?)['"]''')[0] )
        if icon == '': icon = cItem.get('icon', '')
        title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data[0], '<h1', '</h1>', True)[1] )
        if title == '': icon = cItem['title']
        desc = self.cleanHtmlStr( data[0].split('</h1>')[-1] )
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data[1], '<li', '</li>')
        for item in data:
            eTitle = self.cleanHtmlStr(self.cleanHtmlStr(item))
            videoUrl = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] )
            if not videoUrl.startswith('http'): continue
            params = dict(cItem)
            params.update({'title':title + ' ' + eTitle, 'url':videoUrl, 'icon':icon, 'desc':desc})
            self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("CartoonME.getLinksForVideo [%s]" % cItem)
        urlTab = [] 
        
        if self.up.getDomain(self.MAIN_URL) not in cItem['url']:
            return [{'name':'', 'url':cItem['url'], 'need_resolve':1}]
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        if '#player_load' not in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            sts, data = self.getPage(url)
            if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '#player_load', 'success', False)[1]
        url       = self.cm.ph.getSearchGroups(data, '''url: ['"]([^'^"]+?)['"]''')[0]
        post_data = self.cm.ph.getSearchGroups(data, '''data: ['"]([^"^']+?)['"]''')[0]
        
        sts, data = self.getPage(url, {'raw_post_data':True, 'header':{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'}}, post_data)
        if not sts: return []
        
        printDBG(data)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '>Download', '<script ', False)[1]
        tmp = re.compile('''<a[^>]+?href=['"](http[^"^']+?)['"][^>]*?>([^<]+?)<''').findall(tmp)
        for item in tmp:
            urlTab.append({'name':item[1], 'url':item[0], 'need_resolve':1})
            
        if 0 == len(urlTab):
            titles = re.compile('selectquality[^>]*?>([^<]+?)<').findall(data)
            urls   = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s+part\s+='), re.compile('\]'), False)[1]
            urls   = re.compile('"(https?://[^"]+?)"').findall(urls)
            printDBG(titles)
            printDBG(urls)
            if len(urls) == len(titles):
                for idx in range(len(titles)):
                    urlTab.append({'name':titles[idx], 'url':urls[idx], 'need_resolve':1})
                
        if 0 == len(urlTab):
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player', '</script>', False)[1]
            if 'docid=' in tmp:
                docid = self.cm.ph.getSearchGroups(tmp, '''['"]([a-zA-Z0-9_-]{28})['"]''')[0]
                if docid != '':
                    url = 'https://video.google.com/get_player?docid=%s&authuser=&eurl=%s' % (docid, urllib.quote(cItem['url']))
                    urlTab.append({'name':'video.google.com', 'url':url, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("CartoonME.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if '/vload/' in videoUrl or 'redirector.googlevideo.com' in videoUrl or ('9cartoon.me' in videoUrl and 'token' in videoUrl):
            header = {'Referer':videoUrl, 'User-Agent':self.USER_AGENT, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
            params= {'return_data':False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':header}
            try:
                sts, response = self.cm.getPage(videoUrl, params)
                url = response.geturl()
                response.close()
                urlTab.append({'name':'', 'url':url, 'need_resolve':0})
            except Exception:
                printExc()
        elif videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("CartoonME.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 1)
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + urllib.quote_plus(searchPattern)
        
        self.listItems1(cItem, 'list_episodes')
        
        if 0 == len(self.currList):
            self.listEpisodes(cItem)
        
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
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items_1')
        if category == 'list_items_1':
            self.listItems1(self.currItem, 'list_episodes')
        elif category == 'list_types':
            self.listCartoonListTypes(self.currItem, 'list_letters')
        elif category == 'list_letters':
            self.listLetters(self.currItem, 'list_items_2')
        if category == 'list_items_2':
            self.listItems2(self.currItem, 'list_episodes')
        if category == 'list_episodes':
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
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, CartoonME(), True, favouriteTypes=[]) #, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
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
        
    #def getArticleContent(self, Index = 0):
    #    retCode = RetHost.ERROR
    #    retlist = []
    #    if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
    #
    #    hList = self.host.getArticleContent(self.host.currList[Index])
    #    for item in hList:
    #        title      = item.get('title', '')
    #        text       = item.get('text', '')
    #        images     = item.get("images", [])
    #        othersInfo = item.get('other_info', '')
    #        retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
    #    return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
        icon        =  self.host.getIconUrl( cItem.get('icon', '') )
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem
