# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getF4MLinksWithMeta, getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, _unquote
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
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
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://series-en-streaming.com/'

class SeriesEnStreamingCom(CBaseHostClass):
    USER_AGENT = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'
    HEADER = {'User-Agent': USER_AGENT, 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = 'http://www.series-en-streaming.com/'
    DEFAULT_ICON = "http://www.series-en-streaming.com/templates/YStarter/images/logo.png"
    
    MAIN_CAT_TAB = [{'category':'list_cats',       'title': _('Series'),              'url':MAIN_URL,    'icon':DEFAULT_ICON, 'cat':'series'},
                    {'category':'list_cats',       'title': _('Movies'),              'url':MAIN_URL,    'icon':DEFAULT_ICON, 'cat':'movies'},
                    {'category':'list_cats',       'title': _('Mangas'),              'url':MAIN_URL ,   'icon':DEFAULT_ICON, 'cat':'mangas'},
                    {'category':'search',          'title': _('Search'), 'search_item':True,             'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),                         'icon':DEFAULT_ICON} ]
    SORT_BY_TAB = [{'title':_('Sort by alphabet')},
                   {'title':_('Sort by popularity'), 'sort_by':'MostPopular'},
                   {'title':_('Latest update'),      'sort_by':'LatestUpdate'},
                   {'title':_('New cartoon'),        'sort_by':'Newest'}]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'series-en-streaming.com', 'cookie':'seriesenstreamingcom.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = {}
    
    def _getFullUrl(self, url):
        if url == '':
            return url
            
        if url.startswith('.'):
            url = url[1:]
        
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if url.startswith('/'):
                url = url[1:]
            if not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)
        newUrl = ''
        idx = 0
        while idx < len(url):
            if 128 < ord(url[idx]):
                newUrl += urllib.quote(url[idx])
            else:
                newUrl += url[idx]
            idx += 1
        return newUrl #.replace('ยก', '%C2%A1')
        
    def _urlWithCookie(self, url):
        url = self._getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data).strip()
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("SeriesEnStreamingCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir' and 'video' != item.get('category', ''):
                self.addDir(params)
            else: self.addVideo(params)
            
    def _fillCache(self, cItem):
        printDBG("SeriesEnStreamingCom._fillCache [%s]" % cItem)
        self.cache = {}
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        for item in [('series','fa-television', '/liste-'), \
                     ('movies', 'fa-film', '/liste-'), \
                     ('mangas', 'fa-youtube-play', '/streaming-')]:
            key = item[0]
            self.cache[key] = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, item[1], '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li>', '</li>')
            for item2 in tmp:
                url = self.cm.ph.getSearchGroups(item2, '''href="([^"]+?)"''')[0]
                title = self.cleanHtmlStr(item2)
                if item[2] in url:
                    category = 'list_abc'
                else:
                    category = 'list_items'
                self.cache[key].append({'category':category, 'title':title, 'url':self._getFullUrl(url)})
        
        for item in [('series_genre','Séries par genre'), \
                     ('series_date','Séries par Année'), \
                     ('movies_genre','Films par genre'), \
                     ('movies_date','Films par Année')]:
            key = item[0]
            self.cache[key] = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, item[1], '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li>', '</li>')
            tab = []
            for item2 in tmp:
                url = self.cm.ph.getSearchGroups(item2, '''href="([^"]+?)"''')[0]
                title = self.cleanHtmlStr(item2)
                tab.append({'title':title, 'url':self._getFullUrl(url)})
            self.cache[key] = tab
        
    def listCats(self, cItem):
        printDBG("SeriesEnStreamingCom.listCats [%s]" % cItem)
        cat = cItem['cat']
        tab = self.cache.get(cat, [])
        if 0 == len(tab): self._fillCache(cItem)
        tab = self.cache.get(cat, [])
        
        self.listsTab(tab, cItem)
        
        for item in [(cat+'_genre', _('Genres')), (cat+'_date', _('By Year'))]:
            if len(self.cache.get(item[0], [])):
                params = dict(cItem)
                params.update({'title':item[1], 'category':'list_sub_cats', 'cache_key':item[0]})
                self.addDir(params)
        
    def listSubCats(self, cItem, category):
        printDBG("SeriesEnStreamingCom.listSubCats [%s]" % cItem)
        tab = self.cache[cItem['cache_key']]
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
        
    def listABC(self, cItem, category):
        printDBG("SeriesEnStreamingCom.listABC [%s]" % cItem)
        
        baseUrlTab = {'series':'/liste-streaming-serie/%s.html', 
                      'movies':'/liste-des-films-en-streaming-gratuit/%s.html', 
                      'mangas':'/streaming-manga-vostfr/%s.html' }
        if not cItem.get('cat', '') in baseUrlTab:
            return
        baseUrl = baseUrlTab[cItem['cat']]
        tab = []
        for i in range(8):
            tab.append(str(i+1))
        tab = self.cm.makeABCList(tab)
        for item in tab:
            params = dict(cItem)
            params.update({'title':item, 'category':category, 'url':self._getFullUrl(baseUrl % item)})
            self.addDir(params)
            
    def listABCItems(self, cItem, category):
        printDBG("SeriesEnStreamingCom.listABCItems [%s]" % cItem)
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="newslist">', '</div>', False)[1].split('</span>')[-1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''')[0]
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':self._getFullUrl(url)})
            if cItem.get('cat', '') == 'movies' or '/films-' in url:
                self.addVideo(params)
            else:
                self.addDir(params)
            
    def _urlAppendPage(self, url, page, sortBy, keyword=''):
        post_data = None
        if '' != keyword:
            post_data = {'do':'search', 'subaction':'search', 'search_start':page, 'full_search':0, 'result_from':(page-1)*20+1, 'story':keyword}
        else:
            if sortBy != '':
                if not url.endswith('/'):
                    url += '/'
                url += sortBy+'/'
            if page > 1:
                if not url.startswith('/'):
                    url += '/'
                url += 'page/%d/' % page
        return post_data, url
        
    def listItems(self, cItem, category):
        printDBG("SeriesEnStreamingCom.listItems [%s]" % cItem)
        page = cItem.get('page', 1)
        sort_by   = cItem.get('sort_by', '')
        post_data, url = self._urlAppendPage(cItem['url'], page, sort_by, cItem.get('keyword', ''))
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return
        
        nextPage = False
        if ('/page/%d/' % (page+1)) in data or 'nextlink' in data:
            nextPage = True
            
        if 'keyword' in cItem:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="sres-wrap', '</a>')
            for item in data:
                url   = self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)["']''')[0]
                title = self.cm.ph.getSearchGroups(item, '''alt=["']([^"^']+?)["']''')[0]
                if '' == title: title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>', True)[1] )
                icon  = self.cm.ph.getSearchGroups(item, '''src=["']([^"^']+?\.jpg)["']''')[0]
                desc  = self.cleanHtmlStr(item)
            
                params = dict(cItem)
                params.update({'category':category, 'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon), 'desc':desc})
                if cItem.get('cat', '') == 'movies' or '/films-' in url:
                    self.addVideo(params)
                else:
                    self.addDir(params)
        else:
            sp = '<div class="movie-item'
            data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div class="cl', False)[1] #'<div class="clr">'
            #printDBG(data)
            data = data.split(sp)
            for item in data:
                #item  = '<div ' + item 
                tmp   = self.cm.ph.getDataBeetwenMarkers(item, '<a ', '</a>', True)[1]
                url   = self.cm.ph.getSearchGroups(tmp, '''href=["']([^"^']+?)["']''')[0]
                title = self.cleanHtmlStr( tmp )
                icon  = self.cm.ph.getSearchGroups(item, '''src=["']([^"^']+?\.jpg)["']''')[0]
                
                descTab = []
                tmp = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="movie-series">', '</span>', True)[1])
                if '' != tmp: descTab.append(tmp)
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<div class="movie-director"', '</div>')
                for t in tmp: 
                    t = self.cleanHtmlStr( t )
                    if '' != t: descTab.append(t)
                tmp = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="movie-text"', '</div>', True)[1])
                if '' != tmp: descTab.append(tmp)
                
                desc  = '[/br]'.join(descTab)
            
                params = dict(cItem)
                params.update({'category':category, 'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon), 'desc':desc})
                if cItem.get('cat', '') == 'movies' or '/films-' in url:
                    self.addVideo(params)
                else:
                    self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("SeriesEnStreamingCom.listEpisodes [%s]" % cItem)
        
        sts, data = self.cm.getPage(cItem['url']) 
        if not sts: return
        
        saison = self.cm.ph.getSearchGroups(cItem['url']+'|', '''saison-([0-9]+?)[^0-9]''')[0]
        
        tmpTab = []
        dat = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div style="text-align:left;">', '</div>', False)
        for tmp in dat:
            tmpTab.extend( tmp.split('</br>') )
        
        for tmp in tmpTab:
            tab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>')
            marker = tmp.split('<a ')[0]
            urlTab = []
            for item in tab:
                name = self.cleanHtmlStr(item)
                url  = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''')[0]
                if 'links-secure' not in url: continue
                urlTab.append({'name':name, 'url':url, 'need_resolve':1})
            if len(urlTab):
                params  = dict(cItem)
                title   = self.cleanHtmlStr(marker)
                episode = self.cm.ph.getSearchGroups(title+'|', '''[^0-9]([0-9]+?)[^0-9]''')[0]
                if '' != episode and '' != saison:
                    title = ' s%se%s ' % (saison, episode)
                
                params.update({'title':cItem['title'] +': '+ title, 'marker':marker})
                self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("SeriesEnStreamingCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url']) 
        if not sts: return urlTab
        
        marker = cItem.get('marker', '')
        
        tmpTab = []
        dat = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div style="text-align:left;">', '</div>', False)
        for tmp in dat:
            tmpTab.extend( tmp.split('</br>') )
        
        for dat in [(tmpTab, marker), ([data], '')]:
            for tmp in dat[0]:
                if dat[1] not in tmp: continue
                tab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>')
                for item in tab:
                    name = self.cleanHtmlStr(item)
                    url  = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''')[0]
                    if 'links-secure' not in url: continue
                    urlTab.append({'name':name, 'url':url, 'need_resolve':1})
            if len(urlTab): break
            
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("SeriesEnStreamingCom.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        videoUrl = baseUrl
        if 'links-secure' in videoUrl:  
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '''<a[^>]*?id="go_next"[^>]*?href="([^"]+?)"''')[0]
            if not videoUrl.startswith('http'):
                videoUrl = urlparse.urljoin(baseUrl, videoUrl)
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '''<a[^>]*?id="download"[^>]*?href="([^"]+?)"''')[0]
        
        if videoUrl.startswith('http'):
            urlTab.extend(self.up.getVideoLinkExt(videoUrl))
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SeriesEnStreamingCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'keyword':searchPattern, 'url':self._getFullUrl('/index.php?do=search')})
        self.listItems(cItem, 'list_episodes')
        
    def getArticleContent(self, cItem):
        printDBG("SeriesEnStreamingCom.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        mainData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="m-header">', '<div class="m-desc full-text', False)[1]
        
        rank = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(mainData, '<div class="rip">', '</div>', False)[1] )
        icon = self.cm.ph.getSearchGroups(mainData, '''background:url\((http[^)]+?\.jpg)\)''')[0].strip()
        if icon == '': icon = cItem.get('icon', '')
        title = cItem['title']
        
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="mr-item">', '<div class="m-info clearfix">')[1])
        
        keysTab = [{'m1':'Titre de la série',               'key':'alternate_title'},
                   {'m1':'fa-calendar',  'm2':'',           'key':'year'},
                   {'m1':'Réalisateur',                     'key':'director'},
                   {'m1':'Genre',                           'key':'genre'},
                   {'m1':'Langue',                          'key':'language'},
                   {'m1':'Lanague',                         'key':'language'},
                   {'m1':'fa-clock-o',                      'key':'duration'},
                   {'m1':'Statut',                          'key':'status'},
                   {'m1':'Acteurs',                         'key':'actors'},
                   {'m1':'Qualité',                         'key':'quality'},
                   {'m1':'Nationalité',                     'key':'country'},
                   {'m1':'Crée par',                        'key':'production'}, 
                   {'m1':'Production',                      'key':'production'},
                   {'m1':'fa-users',                        'key':'actors'},
                   {'m1':'Durée',                           'key':'duration'},
                   {'m1':'Date',                            'key':'released'}
                   ]

        otherInfo = {}
        data = self.cm.ph.getAllItemsBeetwenMarkers(mainData, '<div class="mi-item clearfix">', '<div class="mi-item clearfix">')
        for item in data:
            for keyItem in keysTab:
                if keyItem['m1'] in item and keyItem.get('m2', '') in item:
                    val = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="mi-desc">', '</div>', False)[1] )
                    if '' != val:
                        otherInfo[keyItem['key'] ] =  val
                        break
        rating = self.cm.ph.getDataBeetwenMarkers(mainData, '<i class="fa fa-star">', '</div>', False)[1]
        m1 = 'Allociné:'
        if m1 in rating:
            otherInfo['rating'] = self.cleanHtmlStr( rating.replace(m1, ''))
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]

    def getFavouriteData(self, cItem):
        params = {'url':cItem['url']}
        if '' != cItem.get('marker', ''):
            params['marker'] = cItem['marker']
        data = ''
        try:
            data = json.dumps(params).encode('utf-8')
        except Exception:
            printExc()
        return data
        
    def getLinksForFavourite(self, fav_data):
        try:
            return self.getLinksForVideo(byteify(json.loads(fav_data)))
        except Exception:
            printExc()
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
        elif category == 'list_cached_items':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_episodes'
            self.listsTab(self.cacheHome.get(cItem.get('tab_id'), []), cItem)
        elif category == 'list_cats':
            self.listCats(self.currItem)
        elif category == 'list_sub_cats':
            self.listSubCats(self.currItem, 'list_items')
        elif category == 'list_abc':
            self.listABC(self.currItem, 'list_abc_items')
        elif category == 'list_abc_items':
            self.listABCItems(self.currItem, 'list_episodes')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
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
        CHostBase.__init__(self, SeriesEnStreamingCom(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('seriesenstreamingcomlogo.png')])
    
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
        
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        cItem = self.host.currList[Index]
        if 'video' == cItem.get('type', '') or cItem.get('category', 'list_episodes'):
            hList = self.host.getArticleContent(cItem)
            for item in hList:
                title      = item.get('title', '')
                text       = item.get('text', '')
                images     = item.get("images", [])
                othersInfo = item.get('other_info', '')
                retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
            retCode = RetHost.OK
        return RetHost(retCode, value=retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
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
