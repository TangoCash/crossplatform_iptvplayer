# -*- coding: utf-8 -*-
#
#-*- Coded  by gorr
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, \
    CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, \
    GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
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


def gettytul():
    return 'http://sovdub.ru/'


class Sovdub(CBaseHostClass):
    MAIN_URL = 'http://sovdub.ru/'
    DEFAULT_ICON_URL = 'http://sovdub.ru/templates/simplefilms/images/logo.png'
    SRCH_URL = MAIN_URL + '?do=search&mode=advanced&subaction=search&story='

    MAIN_CAT_TAB = [{'category': 'genres', 'title': _('Genres'), 'url': MAIN_URL, 'icon': DEFAULT_ICON_URL},
                    {'category': 'countries', 'title': _('Countries'), 'url': MAIN_URL, 'icon': DEFAULT_ICON_URL},
                    {'category': 'search', 'title': _('Search'), 'icon': DEFAULT_ICON_URL, 'search_item': True},
                    {'category': 'search_history', 'title': _('Search history'), 'icon': DEFAULT_ICON_URL}]

    def __init__(self):
        CBaseHostClass.__init__(self, {'history': 'Sovdub', 'cookie': 'Sovdub.cookie'})

    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('/'):
                url = url[1:]
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def getPage(self, url, params={}, post_data=None):
        sts, data = self.cm.getPage(url, params, post_data)
        if sts: data = data.decode('windows-1251').encode('utf-8')
        return sts, data

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Sovdub.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name'] = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)

    def listGenres(self, cItem, category):
        printDBG("Sovdub.listGenres")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        catData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="right-menu">', '</div>', False)[1]
        catData = re.compile('href="([^"]+?)">([^<]+?)</a>').findall(catData)
        for item in catData:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': item[0]})
            self.addDir(params)

    def listCountries(self, cItem, category):
        printDBG("Sovdub.listCountries")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        canData = self.cm.ph.getDataBeetwenMarkers(data, '()\n//-->', '</div>', False)[1]
        canData = re.compile('href="([^"]+?)">([^<]+?)</a>').findall(canData)
        for item in canData:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': item[0]})
            self.addDir(params)

    def listItems(self, cItem, category):
        printDBG("Sovdub.listItems")

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

        post_data = cItem.get('post_data', None)
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return

        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False

        m1 = '</div></div>'
        if ('<div class="navigation">') in data:
            m1 = '<div class="navigation">'
        data = self.cm.ph.getDataBeetwenMarkers(data, "<div id='dle-content'>", m1, False)[1]
        data = re.compile('src="(.*jpg)".*alt="(.*)" />*\s.*<a href="(.*?)"></a></div>').findall(data)
        for item in data:
            title = item[1]
            icon = item[0]
            url = item[2]
            printDBG(icon)
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'icon': item[0], 'desc': item[1], 'url': item[2]})
            self.addDir(params)

        if nextPage:
            params = dict(cItem)
            params.update({'title': _('Next page'), 'page': cItem.get('page', 1)+1})
            self.addDir(params)

    def listContent(self, cItem):
        printDBG("Sovdub.listContent")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<div class="full-news-content">', '</a></div>', False)[1]
        desc = self.cleanHtmlStr(desc).replace('  ', '')
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["']([^"^']+?)['"]''', 1, True)[0]
        url = url.replace('amp;', '')
        url = self.getFullUrl(url)
        if self.cm.isValidUrl(url):
            params = dict(cItem)
            params['desc'] = desc
            params['url'] = url
            params.update({'desc': desc, 'url': url})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        try: searchPattern = searchPattern.decode('utf-8').encode('cp1251', 'ignore')
        except Exception: searchPattern = ''
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + urllib.quote_plus(searchPattern)
        cItem['post_data'] = {'do': 'search', 'subaction': 'search', 'x': 0, 'y': 0, 'story': searchPattern}
        self.listItems(cItem, 'list_items')

    def getLinksForVideo(self, cItem):
        printDBG("Sovdub.getLinksForVideo [%s]" % cItem)
        urlTab = []
        urlTab.append({'name': 'Main url', 'url': cItem['url'], 'need_resolve': 1})
        return urlTab

    def getVideoLinks(self, videoUrl):
        printDBG("Sovdub.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if 'publicvideohost.org' in videoUrl:
            sts, data = self.getPage(videoUrl)
            if not sts: return []
            url = self.cm.ph.getSearchGroups(data, 'file: "(.*?)"')[0]
            urlTab.append({'name': 'Main url', 'url': url, 'need_resolve': 0})
        else: 
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab

    def getFavouriteData(self, cItem):
        return cItem['url']

    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url': fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG("handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category))
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name': 'category'})
        elif category == 'genres':
            self.listGenres(self.currItem, 'list_items')
        elif category == 'countries':
            self.listCountries(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_content')
        elif category == 'list_content':
            self.listContent(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item': False, 'name': 'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Sovdub(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('sovdublogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))
        return RetHost(RetHost.OK, value = retlist)

    def getResolvedURL(self, url):
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))
        return RetHost(RetHost.OK, value = retlist)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = []

        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if cItem['type'] == 'category':
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif cItem['type'] == 'more':
            type = CDisplayListItem.TYPE_MORE
        elif cItem['type'] == 'audio':
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

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range(len(list)):
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
                self.host.history.addHistoryItem(pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
