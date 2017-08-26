# -*- coding: utf-8 -*-
#
# Host prepared by 
#

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
from Plugins.Extensions.IPTVPlayer.libs.moonwalkcc import MoonwalkParser
from Plugins.Extensions.IPTVPlayer.libs.hdgocc import HdgoccParser
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
    return 'http://online-kinopokaz.ru/'

class Kinopokaz(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Kinopokaz', 'cookie':'Kinopokaz.cookie'})
        self.catCache = []
        self.moonwalkParser = MoonwalkParser()
        self.hdgocc = HdgoccParser()
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL = 'http://online-kinopokaz.ru/'
        self.DEFAULT_ICON_URL = "http://ipic.su/img/img7/fs/logi.1456142273.png"

        self.MAIN_CAT_TAB = [{'category':'categories',         'title':_('Movie categories'),     'url':self.getMainUrl()},
                             {'category':'search',              'title':_('Search'),          'search_item':True          },
                             {'category':'search_history',      'title':_('Search history'),                              }
                            ]
    
    def getPage(self, url, params={}, post_data=None):
        sts,data = self.cm.getPage(url, params, post_data)
        return sts,data
    
    def getFullUrl(self, url):
        url = url.replace('&amp;', '&')
        return CBaseHostClass.getFullUrl(self, url)

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
                params.update({'category':category, 'title':item[1], 'url':self.getFullUrl(item[0])})
                self.catCache.append(params)

        mainMenuData = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="uMenuRoot">', '</ul>', False)[1]
        mainMenuData = re.compile('href="/([^"]+?)"><span>([^<]+?)</span>').findall(mainMenuData)
        for item in mainMenuData:
            if item[0] in ['/load/tv_onlajn/tv_onlajn_prjamoj_ehfir/23-1-0-4951','index/pomoshh/0-2', 'index/stol_zakazov/0-5','index/ne_rabotaet_film/0-6']: 
                continue
            params = dict(cItem)
            params.update({'category':category, 'title':item[1], 'url':self.getFullUrl(item[0])})
            self.addDir(params)

        self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})

    def listContent(self, cItem, category):
        printDBG("Kinopokaz.listContent")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        desc = ''
        title = cItem['title']
        url = cItem['url']
        
        seriesData = self.cm.ph.getDataBeetwenMarkers(data, '<h2 style=', '<div id=', False)[1]#
        if len(seriesData):
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
        
        if self.up.getDomain(url) in self.getMainUrl():
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '>')
            for item in tmp:
                url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                if 1 == self.up.checkHostSupport(url):
                    break
        
        params = dict(cItem)
        params['desc'] = desc
        params['url'] = strwithmeta(url, {'Referer':cItem['url']})
        hostName = self.up.getHostName(url)
        if hostName in ['serpens.nl', '37.220.36.15']:
            hostName = 'moonwalk.cc'
        
        params.update({'category':category, 'serie_title':title})
        if hostName == 'moonwalk.cc' and '/serial/' in url:
            params.update({'category':category, 'serie_title':title})
            season = self.moonwalkParser.getSeasonsList(url)
            for item in season:
                param = dict(params)
                param.update({'host_name':'moonwalk', 'title':item['title'], 'season_id':item['id'], 'url':item['url']})
                self.addDir(param)
            return
        elif hostName == 'hdgo.cc':
            url = strwithmeta(url, {'Referer':cItem['url']})
            seasons = self.hdgocc.getSeasonsList(url)
            for item in seasons:
                param = dict(params)
                param.update(
                    {'host_name': 'hdgo.cc', 'title': item['title'], 'season_id': item['id'], 'url': item['url']})
                self.addDir(param)
            
            if 0 != len(seasons):
                return
            
            seasonUrl = url
            episodes = self.hdgocc.getEpiodesList(seasonUrl, -1)
            for item in episodes:
                param = dict(params)
                param.update(
                    {'title': '{0} - {1} - s01e{2} '.format(title, item['title'], item['id']), 'url': item['url']})
                self.addVideo(param)
            
            if 0 != len(episodes):
                return
        
        if self.up.checkHostSupport(url) == 1:
            self.addVideo(params)

    def listEpisodes(self, cItem):
        printDBG("Kinopokaz.listEpisodes")
        title = cItem['serie_title']
        id = cItem['season_id']
        hostName = cItem['host_name']
        episodes = []
        if hostName == 'moonwalk':
            episodes = self.moonwalkParser.getEpiodesList(cItem['url'], id)
        elif hostName == 'hdgo.cc':
            episodes = self.hdgocc.getEpiodesList(cItem['url'], id)
        
        for item in episodes:
            params = dict(cItem)
            params.update( {'title': '{0} - s{1}e{2} {3}'.format(title, id, item['id'], item['title']), 'url': item['url']})
            self.addVideo(params)

    def listItems(self, cItem, category):
        printDBG("Kinopokaz.listItems")
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            url += '-' + str(page)
        
        post_data = cItem.get('post_data', None)
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return

        nextPage = False
        if '' != self.cm.ph.getSearchGroups(data, '''spages\(\s*['"](%s)['"]''' % (page+1))[0]:
            nextPage = True

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="eTitle"', '</table>')
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
            params.update({'category':category, 'title':title, 'icon':self.getFullUrl(icon), 'desc':desc, 'url':self.getFullUrl(url)})
            self.addDir(params)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        #searchPattern = 'Колонна'
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('search/?q=%s&m=site&m=load&t=0' % urllib.quote_plus(searchPattern))
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
