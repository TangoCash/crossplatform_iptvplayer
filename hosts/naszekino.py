# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetDefaultLang, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'nasze-kino.eu'

class NaszeKino(CBaseHostClass):
    MAIN_URL    = 'http://nasze-kino.eu/'
    SEARCH_URL  = MAIN_URL + '?q='
    LOGO_URL    = 'http://img.cda.pl/obr/thumbs/7ef1c4fac63c2d77e0193183cb7a34bb.png_oooooooooo_186x.png'
    MAIN_CAT_TAB = [{'category':'recommended',                     'title': 'Polecane', 'icon':LOGO_URL},
                    {'category':'category', 'filtr':'genres',      'title': 'Gatunek',   'icon':LOGO_URL  },
                    {'category':'category', 'filtr':'quality',     'title': 'Jakość',    'icon':LOGO_URL   },
                    {'category':'category', 'filtr':'version',     'title': 'Wersja',    'icon':LOGO_URL   },
                    {'category':'search',                          'title': _('Search'), 'search_item':True, 'icon':LOGO_URL},
                    {'category':'search_history',                  'title': _('Search history'), 'icon':LOGO_URL} ]
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'NaszeKino', 'cookie':'naszekino.cookie'})
        self.categories = {}
            
    def addNextPage(self, cItem, nextPage, page):
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listFilters(self, cItem, category):
        printDBG("NaszeKino.listFilters [%s]" % cItem)
        if self.categories == {}:
            sts, data = self.cm.getPage(self.MAIN_URL)
            if not sts: return
            tab =[{'m1':'<li><span>Gatunek</span>', 'filtr':'genres' },
                  {'m1':'<li><span>Jakość</span>',  'filtr':'quality'},
                  {'m1':'<li><span>Wersja</span>',  'filtr':'version'}]
            for item in tab:
                self.categories[item['filtr']] = []
                tmp = self.cm.ph.getDataBeetwenMarkers(data, item['m1'], item.get('m2', '</ul>'), False)[1]
                tmp = re.compile('<a [^>]*?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(tmp)
                for el in tmp:
                    self.categories[item['filtr']].append({'url':self.getFullUrl(el[0]), 'title':el[1]})
                    
        tab = self.categories.get(cItem['filtr'], [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['category'] = category
            self.addDir(params)
            
    def getBase(self, item):
        url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
        icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
        title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
        return {'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon':self.getFullUrl(icon)}
            
    def listRecommended(self, cItem):
        printDBG("NaszeKino.listRecommended [%s]" % cItem)
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="span12 slider">', '</div>', False)[1]
        data = data.split('</a>')
        if len(data): del data[-1]
        for item in data:
            base = self.getBase(item)
            params = dict(cItem)
            params.update(base)
            self.addVideo(params)
    
    def listItems(self, cItem, category):
        printDBG("NaszeKino.listItems [%s]" % cItem)
        page = cItem.get('page', 1)
        url = cItem['url']
        if url.endswith('/'):
            url += '{0}'.format(page)
        elif '?' in url: url += '&p={0}'.format(page)
        else: url += '?p={0}'.format(page)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        nextPage = False
        if '"strona: {0}"'.format(page+1) in data:
            nextPage = True
        
        sp = '<div class="movie relative">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div class="clear">', False)[1]
        data = data.split(sp)
        for item in data:
            base = self.getBase(item)
            if '' == base['title']: continue
            if '' == base['url']: continue
            if '</h2>' in item:
                desc  = item.split('</h2>')[-1]
            else: desc = ''
            params = dict(cItem)
            params.update({'desc':self.cleanHtmlStr(desc)})
            params.update(base)
            if '-serial-' in base['url'] or '-sezon-' in base['url']:
                params['category'] = category
                self.addDir(params)
            else:
                self.addVideo(params)
        self.addNextPage(cItem, nextPage, page)
        
    def getLinkTab(self, cItem):
        printDBG("NaszeKino.getLinkTab [%s]" % cItem)
        ret = {'episodes':[], 'links':{}}
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return ret
        data = self.cm.ph.getDataBeetwenMarkers(data, "panel-container", "nothing", False)[1]
        data = re.compile('<a [^>]*?href="([^>]+?)"[^>]*?>([^<]+?)</a>').findall(data)
        for item in data:
            if 1 != self.up.checkHostSupport(item[0]): continue
            url  = item[0]
            name = self.up.getHostName(url, True)
            
            if item[1] not in ret['episodes']:
                ret['episodes'].append(item[1])
                ret['links'][item[1]] = []
            ret['links'][item[1]].append({'name':name, 'url':url})
        return ret
        
    def listEpisodes(self, cItem):
        printDBG("NaszeKino.listEpisodes [%s]" % cItem)
        ret = self.getLinkTab(cItem)
        for item in ret['episodes']:
            params = dict(cItem)
            params.update({'title':cItem['title'] + ': ' + self.cleanHtmlStr(item), 'episode':item, 'links':ret['links'][item]})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("NaszeKino.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = self.SEARCH_URL + urllib.quote(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = url
        self.listItems(cItem, 'list_episodes')
        
    def getLinksForVideo(self, cItem):
        printDBG("NaszeKino.getLinksForVideo [%s]" % cItem)
        urlTab = []
        if 'links' in cItem:
            for item in cItem['links']:
                item['need_resolve'] = 1
                urlTab.append(item)
        else:
            ret = self.getLinkTab(cItem)
            if 'episode' in cItem:
                ret['episodes'] = [cItem['episode']]
            
            for episode in ret['episodes']:
                for item in ret['links'][episode]:
                    item['need_resolve'] = 1
                    urlTab.append(item)
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("NaszeKino.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        if '' != baseUrl: 
            videoUrl = baseUrl
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG("NaszeKino.getFavouriteData")
        data = {'url':cItem['url']}
        if 'episode' in cItem:
            data['episode'] = cItem['episode']
        try:
            data = json.dumps(data).encode('utf-8')
        except Exception:
            data = ''
            printExc()
        return data
        
    def getLinksForFavourite(self, fav_data):
        printDBG("NaszeKino.getLinksForFavourite")
        try:
            cItem = byteify(json.loads(fav_data))
        except Exception:
            printExc()
            return []
        return self.getLinksForVideo(cItem)
    
    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem.get('url', ''))
        if not sts: return retTab
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="movie_big relative">', '<div class="report">', False)
        if not sts: return retTab
        icon  = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        desc  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie_desc">', '<div class="clear">', False)[1]
        title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<h1>', '</h1>', False)[1] )
        if '' == title:
            title = cItem['title']
        otherInfo = {}
        return [{'title': title, 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        

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
    #RECOMMENDED 
        elif category == 'recommended':
            self.listRecommended(self.currItem)
    #CATEGORIEs
        elif category == 'category':
            self.listFilters(self.currItem, 'list_items')
    #LIST ITEMS
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_episodes')
    #LIST EPISODES
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
        CHostBase.__init__(self, NaszeKino(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
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
        if 0 == len(hList): return RetHost(retCode, value=retlist)
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
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
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
