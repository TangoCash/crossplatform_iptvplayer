# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
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
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
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
    return 'http://neokino.net/'

class NeoKinoNet(CBaseHostClass):
    MAIN_URL    = 'http://neokino.net/'
    SRCH_URL    = MAIN_URL + 'index.php?s='
    DEFAULT_ICON_URL = 'https://b.thumbs.redditmedia.com/KipKPDYiM2_jtUczTpyJKUYUpXqOhw3RxKuZPDDMmws.jpg'
    
    MAIN_CAT_TAB = [{'category':'list_movies',    'title': _('Main'),       'url':MAIN_URL,     'icon':DEFAULT_ICON_URL, 'm1':'Categories</h3>'},
                    {'category':'filter',         'title': _('Genres'),     'url':MAIN_URL,     'icon':DEFAULT_ICON_URL, 'filter_id':0},
                    {'category':'filter',         'title': _('Year'),       'url':MAIN_URL,     'icon':DEFAULT_ICON_URL, 'filter_id':1},
                    {'category':'filter',         'title': _('Resolution'), 'url':MAIN_URL,     'icon':DEFAULT_ICON_URL, 'filter_id':2},
                    #{'category':'filter',         'title': _('Sort by'),    'url':MAIN_URL,     'icon':DEFAULT_ICON_URL, 'filter_id':3},
                    {'category':'search',         'title': _('Search'),     'search_item':True, 'icon':DEFAULT_ICON_URL},
                    {'category':'search_history', 'title': _('Search history'),                 'icon':DEFAULT_ICON_URL} 
                   ]
    
    CAT_TAB = [{'sort':'date',      'title':_('DATE')},
                {'sort':'views',    'title':_('VIEWS')},
                {'sort':'likes',    'title':_('LIKES')},
                {'sort':'comments', 'title':_('COMMENTS')}
               ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'NeoKinoNet', 'cookie':'NeoKinoNet.cookie'})
        self.filterCache = {} 
        
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
        
    def fillFilters(self, url):
        printDBG("NeoKinoNet.fillFilters")
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="categorias">', '<div id="footer"', False)[1]
        data = data.split('<div class="filtro_y">')
        self.filterCache = {0:[], 1:[], 2:[], 3:[]} 
        idx = 0
        for item in data:
            item = item.split('</li>')
            #printDBG(item)
            if len(item): del item[-1]
            for it in item: 
                url    = self.cm.ph.getSearchGroups(it, '''href=['"]([^"^']+?)["']''', 1, True)[0]
                if url == '': continue
                title  = self.cleanHtmlStr(it)
                self.filterCache[idx].append({'title':title, 'url':self._getFullUrl(url)})
            idx += 1

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("NeoKinoNet.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listFilters(self, cItem, category):
        printDBG("NeoKinoNet.listFilters")
        if self.filterCache == {}:
            self.fillFilters(cItem['url'])
        tab = self.filterCache.get(cItem['filter_id'], [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
            
    def listMovies(self, cItem):
        printDBG("NeoKinoNet.listMovies")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%d/' % page
        if post != '': 
            url += '?' + post
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'items">', '<div class="lateral">', False)[1]
        data = re.split('<div[^>]+?class="item">', data)
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = item.split('<div id="paginador">')[0]
            title  = self.cleanHtmlStr( title )
            url    = self._getFullUrl(url)
            if title != '' and url.startswith('http'):
                params = dict(cItem)
                params.update( {'title': title, 'url':url, 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url']  = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listMovies(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("NeoKinoNet.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        url = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http\://mp4load\.com/[^"]+?)"')[0]
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        sourcesData = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
        tracksData  = self.cm.ph.getDataBeetwenMarkers(data, 'tracks:', ']', False)[1]
        tracksData = re.compile('''['"](http[^"^']+?\.srt)['"]''').findall(tracksData)
        idx = 0
        sub_tracks = []
        for item in tracksData:
            sub_tracks.append({'title':'sub %d' % idx, 'url':item, 'lang':'defaul'})
            idx += 1
            
        try:
            for item in ['type', 'file', 'label']:
                if '"{0}"'.format(item) not in sourcesData:
                    sourcesData = sourcesData.replace(item, '"{0}"'.format(item))
            sourcesData = byteify(json.loads(sourcesData.strip() + ']'))
            for item in sourcesData:
                url = strwithmeta(item['file'], {'external_sub_tracks':sub_tracks})
                urlTab.append({'name':item['label'], 'url':url, 'type':item['type'], 'need_resolve':0})
        except Exception:
            printExc()
            
        url = self.cm.ph.getSearchGroups(data, '''<embed[^>]+?src=['"](http[^"^']+?)['"]''')[0]
        if url.startswith('http'):
            url = strwithmeta(url, {'external_sub_tracks':sub_tracks})
            urlTab.append({'name':'google.com', 'url':url, 'need_resolve':1})
            
        data = re.compile('''\('display'\)\.src=['"]([^'^"]+?)['"]''').findall(data)
        for url in data:
            url = strwithmeta(url, {'external_sub_tracks':sub_tracks})
            urlTab.append({'name':self.up.getHostName(url), 'url':url, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("NeoKinoNet.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        videoUrl = strwithmeta(baseUrl)
        sub_tracks = videoUrl.meta['external_sub_tracks']
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
            if len(sub_tracks):
                for idx in range(len(urlTab)):
                    urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], {'external_sub_tracks':sub_tracks})
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getDataBeetwenMarkers(data, '"og:title" content="', '"', False)[1]
        desc  = self.cm.ph.getDataBeetwenMarkers(data, '"og:description" content="', '"', False)[1]
        icon  = self.cm.ph.getDataBeetwenMarkers(data, '"og:image" content="', '"', False)[1]
        
        rating   = self.cm.ph.getDataBeetwenMarkers(data, 'IMDB:', '</b>', False)[1]
        duration = self.cm.ph.getDataBeetwenMarkers(data, 'class="icon-time">', '</span>', False)[1]
        genre    = self.cm.ph.getDataBeetwenMarkers(data, '<i class="limpiar">', '</i>', False)[1]
        released = self.cm.ph.getSearchGroups(data, 'release-year[^>]*?>([^<]+?)<')[0]
        director = self.cm.ph.getDataBeetwenMarkers(data, '<b class="icon-megaphone">', '</p>', False)[1]
        stars    = self.cm.ph.getDataBeetwenMarkers(data, '<p class="meta_dd limpiar">', '</p>', False)[1]
        
        otherInfo = {'director': self.cleanHtmlStr( director ),
                     'rating':self.cleanHtmlStr( rating ), 
                     'duration':self.cleanHtmlStr( duration ), 
                     'genre':self.cleanHtmlStr( genre ), 
                     'released':self.cleanHtmlStr( released ),
                     'stars': self.cleanHtmlStr( stars ),
                     }
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
        
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
        elif category == 'filter':
            self.listFilters(self.currItem, 'list_movies')
    #MOVIES
        elif category == 'list_movies':
            self.listMovies(self.currItem)
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
        CHostBase.__init__(self, NeoKinoNet(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('neokinologo.png')])
    
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

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        return RetHost(RetHost.OK, value = retlist)
    
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
