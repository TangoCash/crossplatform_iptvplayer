# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://iitv.pl/'

class IITVPL(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'IITVPL.tv', 'cookie':'iitvpl.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL = 'http://iitv.pl/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'assets/img/logo.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_abc',           'title': 'Lista ABC',                       'url':self.MAIN_URL,  'icon':self.DEFAULT_ICON_URL},
                             {'category':'list_series2',       'title': 'Popularne seriale',               'url':self.MAIN_URL,  'icon':self.DEFAULT_ICON_URL},
                             {'category':'list_series1',       'title': 'Wszystkie seriale',               'url':self.MAIN_URL,  'icon':self.DEFAULT_ICON_URL},
                             
                             #{'category':'search',            'title': _('Search'), 'search_item':True,         'icon':self.DEFAULT_ICON_URL},
                             #{'category':'search_history',    'title': _('Search history'),                     'icon':self.DEFAULT_ICON_URL} 
                            ]
        
        self.cacheLinks = {}
        self.cacheSeries = {}
        
    def getSeriesInfo(self, data):
        printDBG("IITVPL.getSeriesInfo")
        info = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="group series-info"', '</div>')[1]
        info['title'] = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h1', '</h1>')[1])
        info['icon']  = self.getFullUrl( self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0] )
        info['desc']  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p class="description"', '</p>')[1].split('</strong>')[-1])
        info['full_desc']  = self.cleanHtmlStr(data.split('</h1>')[-1])
        keysMap = {'Gatunek:':'genre'}
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<strong>', '<br/>', withMarkers=True)
        for item in data:
            tmp   = item.split('</strong>')
            key   = self.cleanHtmlStr(tmp[0])
            value = self.cleanHtmlStr(tmp[-1])
            if key in keysMap:
                info[keysMap[key]] = value
        return info
        
    def listABC(self, cItem, nextCategory):
        printDBG("IITVPL.listABC")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="list">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            title = self.cleanHtmlStr(item)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            
            if url.startswith('http://') or url.startswith('https://'):
                letter = title.decode('utf-8')[0].encode('utf-8').upper()
                if letter.isdigit(): letter = '0-9'
                if letter not in self.cacheSeries:
                    self.cacheSeries[letter] = []
                    params = dict(cItem)
                    params.update({'category':nextCategory, 'title':letter, 'letter':letter, 'url':url})
                    self.addDir(params)
                self.cacheSeries[letter].append( {'title':title, 'url':url} )
        
    def listSeriesByLetter(self, cItem, nextCategory):
        printDBG("IITVPL.listSeriesByLetter")
        tab = self.cacheSeries.get(cItem.get('letter'), [])
        params = dict(cItem)
        params.update({'category':nextCategory, 'good_for_fav': True})
        self.listsTab(tab, params)
                
    def listSeries(self, cItem, nextCategory, m1):
        printDBG("IITVPL.listSeries")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>', withMarkers=True)
        for item in data:
            title = self.cleanHtmlStr(item)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if url.startswith('http://') or url.startswith('https://'):
                params = dict(cItem)
                params.update({'category':nextCategory, 'good_for_fav': True, 'title':title, 'url':url})
                self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("IITVPL.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        info = self.getSeriesInfo(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="episodes-list">', '<footer>')[1]
        data = data.split('</ul>')
        if len(data): del data[-1]
        
        for sItem in data:
            season   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(sItem, '<h2', '</h2>')[1] )
            eDataTab = self.cm.ph.getAllItemsBeetwenMarkers(sItem, '<li', '</li>', withMarkers=True)
            for item in eDataTab:
                title = info['title'] + ': ' + self.cleanHtmlStr(item)
                url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                if url.startswith('http://') or url.startswith('https://'):
                    params = dict(cItem)
                    params.update({'good_for_fav': True, 'title':title, 'url':url, 'desc':info['full_desc'], 'icon':info['icon']})
                    self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("IITVPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + '/' + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'list_episodes')
    
    def getLinksForVideo(self, cItem):
        printDBG("IITVPL.getLinksForVideo [%s]" % cItem)
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="tab-selector', '</ul>', withMarkers=True)
        tabs = []
        links = {}
        for tItem in data:
            tabTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(tItem, '<a class="tab-selector', '</a>')[1] )
            links[tabTitle] = []
            tabs.append(tabTitle)
            lData = self.cm.ph.getAllItemsBeetwenMarkers(tItem, '<li', '</li>', withMarkers=True)
            for item in lData:
                tmp   = self.cm.ph.getSearchGroups(item, '<a[^>]+?class="_?video-link"[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<', 2)
                if tmp[0].startswith('http://') or tmp[0].startswith('https://'):
                    links[tabTitle].append({'name':'[{0}] '.format(tabTitle) + self.cleanHtmlStr(tmp[1]), 'url':tmp[0], 'need_resolve':1})
        
        keys = ['Lektor', 'Napisy PL', 'Orygina³']
        keys.extend(links.keys())
        for key in keys:
            for item in links.get(key, []):
                urlTab.append(item)
            links.pop(key, None)
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("IITVPL.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            key = self.cacheLinks.keys()[0]
            for idx in range(len(self.cacheLinks[key])):
                if videoUrl in self.cacheLinks[key][idx]['url']:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                    break
        
        url = self.getFullUrl('ajax/getLinkInfo')
        if 'link=' in videoUrl:
            linkID = videoUrl.split('link=')[-1].strip()
            post_data = {'link_id':linkID}
            HEADER = dict(self.AJAX_HEADER)
            HEADER['Referer'] = videoUrl
            sts, data = self.cm.getPage(url, {'header':HEADER}, post_data)
            if not sts: return []
            try:
                data = byteify(json.loads(data))
                data = data['results']
                printDBG(data)
                if 'embed_code' in data:
                    videoUrl = self.cm.ph.getSearchGroups(data['embed_code'], 'src="([^"]+?)"')[0]
                elif 'link' in data:
                    videoUrl = str(data['link'])
            except Exception:
                printExc()
        
        if 1 != self.up.checkHostSupport(videoUrl):
            try:
                sts, response = self.cm.getPage(videoUrl, {'return_data':False})
                videoUrl = response.geturl()
                response.close()
            except Exception:
                printExc()
        
        if videoUrl.startswith('http://') or videoUrl.startswith('https://'):
            return self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("IITVPL.getArticleContent [%s]" % cItem)
        retTab = []
        url = cItem.get('url', '')
        
        if cItem['type'] == 'video':
            url = '/'.join( url.split('/')[:-1])
            
        sts, data = self.cm.getPage(url)
        if not sts: return retTab
        
        info  = self.getSeriesInfo(data)
        
        otherInfo = {}
        if 'genre' in info:
            otherInfo['genre'] = info['genre']
        
        return [{'title':self.cleanHtmlStr( info['title'] ), 'text': self.cleanHtmlStr( info['desc'] ), 'images':[{'title':'', 'url':info['icon']}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('IITVPL.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem.get('desc', ''), 'icon':cItem['icon']}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('IITVPL.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('IITVPL.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
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
        elif category == 'list_abc':
            self.listABC(self.currItem, 'list_by_letter')
        elif category == 'list_by_letter':
            self.listSeriesByLetter(self.currItem, 'list_episodes')
        elif category == 'list_series1':
            self.listSeries(self.currItem, 'list_episodes', '<ul id="list">')
        if category == 'list_series2':
            self.listSeries(self.currItem, 'list_episodes', '<ul id="popular-list">')
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
        CHostBase.__init__(self, IITVPL(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        
        if cItem['type'] != 'video' and cItem['category'] != 'list_episodes':
            return RetHost(retCode, value=retlist)
        hList = self.host.getArticleContent(cItem)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        if len(hList): retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
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
        icon        =  cItem.get('icon', '')
        isGoodForFavourites = cItem.get('good_for_fav', False)
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem

