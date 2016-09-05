# -*- coding: utf-8 -*-
#
# Host prepared by 
#

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
from Plugins.Extensions.IPTVPlayer.libs.moonwalkcc import MoonwalkParser
###################################################

###################################################
# FOREIGN import
###################################################
import copy
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
    return 'http://online-kinopokaz.ru/'


class Kinopokaz(CBaseHostClass):
    MAIN_URL = 'http://online-kinopokaz.ru/'
    DEFAULT_ICON_URL = "http://ipic.su/img/img7/fs/logi.1456142273.png"

    MAIN_CAT_TAB = [{'category':'categories',     'title':_('Movie categories'),     'url':MAIN_URL, 'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title':_('Search'),         'icon':DEFAULT_ICON_URL, 'search_item':True},
                    {'category':'search_history', 'title':_('Search history'), 'icon':DEFAULT_ICON_URL}]

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Kinopokaz', 'cookie':'Kinopokaz.cookie'})
        self.catCache = []
        self.moonwalkParser = MoonwalkParser()

    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('/'):
                url = url[1:]
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, str):
        return self.cm.ph.removeDoubles(CBaseHostClass.cleanHtmlStr(str), '&nbsp;').replace('&nbsp;', ' ').strip()

    def getPage(self, url, params={}, post_data=None):
        sts,data = self.cm.getPage(url, params, post_data)
        return sts,data

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Kinopokaz.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)

    def listMainMenu(self, cItem, category):
        printDBG("Kinopokaz.listCategories")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        if 0 == len(self.catCache):
            catData = self.cm.ph.getDataBeetwenMarkers(data, 'class="catsTable">', '</table>', False)[1]
            catData = re.compile('href="(/[^"]+?)"[^>]*?>([^<]+?)<').findall(catData)
            for item in catData:
                if item[0] in ['/load/serialy/12','/load/multiplikacionnye/13','/load/anime/24','/load/tv_onlajn/23','/load/trillery/10']:
                    continue
                params = dict(cItem)
                params.update({'category':category, 'title':item[1], 'url':self._getFullUrl(item[0])})
                self.catCache.append(params)

        mainMenuData = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="uMenuRoot">', '</ul>', False)[1]
        mainMenuData = re.compile('href="/([^"]+?)"><span>([^<]+?)</span>').findall(mainMenuData)
        for item in mainMenuData:
            if item[0] in ['/load/tv_onlajn/tv_onlajn_prjamoj_ehfir/23-1-0-4951','index/pomoshh/0-2', 'index/stol_zakazov/0-5','index/ne_rabotaet_film/0-6']: 
                continue
            params = dict(cItem)
            params.update({'category':category, 'title':item[1], 'url':self._getFullUrl(item[0])})
            self.addDir(params)

        self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})

    def listContent(self, cItem, category):
        printDBG("Kinopokaz.listContent")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        desc=''
        title = cItem['title']
        seriesData = self.cm.ph.getDataBeetwenMarkers(data, '<h2 style=', '<div id=', False)[1]#
        if len(seriesData) == 0:
            url = cItem['url']
        else:
            desc  = self.cm.ph.getDataBeetwenMarkers(data, 'colspan="2">', '<h2 style="text-align:', False)[1]
            desc  = self.cleanHtmlStr(desc)
            tranData = re.compile('<div align="center">(.*)</div>\n.*\s.+?src="(http:[^"]+?)"').findall(seriesData)
            if tranData !=[]:
                params = dict(cItem)
                params['desc'] = desc
                for item in tranData:
                    param = dict(params)
                    param.update({'category':'tran', 'title':item[0], 'url':item[1]})
                    self.addDir(param)
                return
            else:
                url = self.cm.ph.getSearchGroups(seriesData, 'src="htt.*(//.*?)"')[0]
                if url.startswith('//'):
                    url = 'http:' + url

        params = dict(cItem)
        params['desc'] = desc
        params['url'] = url
        hostName = self.up.getHostName(url)
        if hostName in ['serpens.nl', '37.220.36.15']:
            hostName = 'moonwalk.cc'
        if hostName == 'moonwalk.cc' and '/serial/' in url:
            params.update({'category':category, 'serie_title':title})
            season = self.moonwalkParser.getSeasonsList(url)
            for item in season:
                param = dict(params)
                param.update({'host_name':'moonwalk', 'title':item['title'], 'season_id':item['id'], 'url':item['url']})
                self.addDir(param)
            return
        if self.up.checkHostSupport(url) == 1:
            self.addVideo(params)

    def listEpisodes(self, cItem):
        printDBG("Kinopokaz.listEpisodes")
        hostName = cItem['host_name']
        if hostName == 'moonwalk':
            title = cItem['serie_title']
            id    = cItem['season_id']
            episodes = self.moonwalkParser.getEpiodesList(cItem['url'], id)
            for item in episodes:
                params = dict(cItem)
                params.update({'title':'{0} - s{1}e{2} {3}'.format(title, id, item['id'], item['title']), 'url':item['url']})
                self.addVideo(params)

    def listItems(self, cItem, category):
        printDBG("Kinopokaz.listItems")
        tmp2 = cItem['url'].split('?')
        url= tmp2[0]
        tmp = cItem['url'].replace(self.MAIN_URL,'').split('/')
        if 1 == len(tmp):
            args = cItem.get('title', None)
            url = '{0}search/?q={1}'.format(self.MAIN_URL, args)
            tmp1 = 1
        else:
            arg = tmp[-1].split('-')
            page = cItem.get('page', 1)
            if 1 == page:
                if 2 == len(tmp):
                    tmp1 = arg[0]+'-'+str(page+1)
                else:
                    tmp1 = tmp[1]+'/'+arg[0]+'-'+str(page+1)
            if 1 < page:
                if 2 == len(tmp):
                    tmp1 = arg[0]+'-'+str(page+1)
                    url = self.MAIN_URL+tmp[0]+'/'+arg[0]+'-'+str(page)
                else:
                    tmp1 = tmp[1]+'/'+arg[0]+'-'+str(page+1)
                    url = self.MAIN_URL+tmp[0]+'/'+tmp[1]+'/'+arg[0]+'-'+str(page)
        post_data = cItem.get('post_data', None)
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return

        nextPage = False
        if ('/load/%s' % tmp1) in data:
            nextPage = True

        m1 = '<div class="eTitle"'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div id="rightcol">', False)[1]
        data = data.split(m1)
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            if title == '':
                title = self.cm.ph.getSearchGroups(item, 'href="[^"]+?">(.*?)</a>')[0]
            title = self.cleanHtmlStr(title)
            if title == '': continue
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            data = self.cm.ph.getDataBeetwenMarkers(item, '<div class="eMessage" style=','</p><br>', True)[1]
            if data == '':
                data = self.cm.ph.getDataBeetwenMarkers(item, '<div class="eMessage" style=','<br />', True)[1]
            desc = data.replace('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', '')
            desc = self.cleanHtmlStr(desc)
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'icon':self._getFullUrl(icon), 'desc':desc, 'url':self._getFullUrl(url)})
            self.addDir(params)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = searchPattern
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL
        cItem['post_data'] = {'do':'search', 'subaction':'search', 'x':0, 'y':0, 'story':searchPattern}
        self.listItems(cItem, 'list_content')

    def getLinksForVideo(self, cItem):
        printDBG("Kinopokaz.getLinksForVideo [%s]" % cItem)
        urlTab = []
        urlTab.append({'name':'Main url', 'url':cItem['url'], 'need_resolve':1})
        return urlTab

    def getVideoLinks(self, videoUrl):
        printDBG("Kinopokaz.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
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
            self.listMainMenu({'name':'category', 'icon':self.DEFAULT_ICON_URL, 'url':self.MAIN_URL},'list_items')
        elif category == 'categories':
            self.listsTab(self.catCache, self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_content')
        elif category == 'list_content':
            self.listContent(self.currItem, 'tran')
        elif category == 'tran':
            self.listContent(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, Kinopokaz(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('kinopokazlogo.png')])

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

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif 'video' == cItem['type']:
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
