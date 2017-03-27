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
from random import randint
from datetime import datetime
from time import sleep
from copy import deepcopy
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
    return 'http://hdpopcorns.com/'

class HDPopcornsCom(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'HDPopcornsCom.tv', 'cookie':'HDPopcornsCom.cookie'})
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://hdpopcorns.com/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'wp-content/uploads/2016/08/large-logo.png' 
        
        self.MAIN_CAT_TAB = [{'category':'list_items',        'title': _('Categories'),           'url':self.getMainUrl()           },
                             {'category':'search',            'title': _('Search'),               'search_item':True,               },
                             {'category':'search_history',    'title': _('Search history'),                                         } 
                            ]
        
        self.cacheFilters = {}
        self.cacheSeasons = {}
        
    def fillFilters(self, cItem):
        self.cacheFilters = {}
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        def addFilter(data, key, addAny, titleBase, marker):
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, '''%s=['"]([^'^"]+?)['"]''' % marker)[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                if titleBase == '':
                    title = title.title()
                self.cacheFilters[key].append({'title':titleBase + title, key:value})
            if addAny and len(self.cacheFilters[key]):
                self.cacheFilters[key].insert(0, {'title':'Wszystkie'})
        
        # category
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'ofcategory', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'ofcategory', False, '', 'value') 
        if 0 == len(self.cacheFilters['ofcategory']):
            for item in [("46","Action"),("24","Adventure"),("25","Animation"),("26","Biography"),("27","Comedy"),("28","Crime"),("29","Documentary"),("30","Drama"),("31","Family"),("32","Fantasy"),("33","Film-Noir"),("35","History"),("36","Horror"),("37","Music"),("38","Musical"),("39","Mystery"),("40","Romance"),("41","Sci-Fi"),("42","Sports"),("43","Thriller")]:
                self.cacheFilters['ofcategory'].append({'title':item[1], 'ofcategory':item[0]})
        
        # rating
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'ofrating', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'ofrating', False, '', 'value') 
        if 0 == len(self.cacheFilters['ofrating']):
            for i in range(10):
                i = str(i)
                if i == '0': title = 'All Ratings'
                else: title = i
                self.cacheFilters['ofrating'].append({'title':title, 'ofrating':i})
        
        
        # quality
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'ofquality', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'ofquality', False, '', 'value') 
        if 0 == len(self.cacheFilters['ofquality']):
            for item in [("0","All Qualities"),("47","1080p"),("48","720p")]:
                self.cacheFilters['ofquality'].append({'title':item[1], 'ofquality':item[0]})
        
        printDBG(self.cacheFilters)
        
    def listFilter(self, cItem, filters):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        
        if idx == 0:
            self.fillFilters(cItem)
        
        tab = self.cacheFilters.get(filters[idx], [])
        self.listsTab(tab, params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("HDPopcornsCom.listItems")
        baseUrl = cItem['url']
        post_data = None
        page = cItem.get('page', 1)
        if page == 1 and '/?s=' not in baseUrl:
            post_data = 'ofsearch=&'
            for key in ['ofcategory', 'ofrating', 'ofquality']:
                if cItem.get(key, '') not in ['-', '']:
                    post_data += key + '={0}&ofcategory_operator=and&'.format(cItem[key])
            post_data += 'ofsubmitted=1'
        
        params = dict(self.defaultParams)
        params['header'] = dict(params['header'])
        params['raw_post_data'] = True
        
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, 'var\s+?mts_ajax_loadposts\s*=\s*([^;]+?);')[0].strip()
        try:
            nextPage = str(byteify(json.loads(nextPage)).get('nextLink', ''))
        except Exception:
            nextPage = ''
            ptineExc()
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<article', '</article>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon   = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip())
            desc  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if desc == '': desc = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addVideo(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page + 1, 'url':nextPage})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("HDPopcornsCom.listSeasons")
        
        self.cacheSeasons = {'keys':[], 'dict':{}}
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = data.split('<div id="episodes">')
        if 2 != len(data): return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data[0], '<div id="seasons_list">', '<div class="clear">')[1]
        tmp = re.compile('<[^>]+?num\="([0-9]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            self.cacheSeasons['keys'].append({'key':item[0], 'title':self.cleanHtmlStr(item[1])})
        
        del data[0]
        
        # fill episodes
        for season in self.cacheSeasons['keys']:
            tmp = self.cm.ph.getDataBeetwenMarkers(data[0], 'data-season-num="%s"' % season['key'], '</ul>')[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True)
            self.cacheSeasons['dict'][season['key']] = []
            for item in tmp:
                url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<a class="episodeName"', '</a>')[1])
                es     = self.cm.ph.getSearchGroups(url, '''/(s[0-9]+?e[0-9]+?)/''')[0]
                self.cacheSeasons['dict'][season['key']].append({'good_for_fav': True, 'title': '%s: %s %s' % (cItem['title'], es, title), 'url':url})
                
        for season in self.cacheSeasons['keys']:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':season['title'], 's_key':season['key']})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("HDPopcornsCom.listEpisodes")
        
        tab = self.cacheSeasons.get('dict', {}).get(cItem['s_key'], [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("HDPopcornsCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('?s=' + urllib.quote_plus(searchPattern))
        
        self.listItems(cItem, 'list_seasons')
    
    def getLinksForVideo(self, cItem):
        printDBG("HDPopcornsCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        trailerUrl = self.cm.ph.getSearchGroups(data, '''href=['"](https?://[^'^"]+?)['"][^>]+?id=['"]playTrailer['"]''')[0]
        if '' == trailerUrl: trailerUrl = self.cm.ph.getSearchGroups(data, '''id=['"]playTrailer['"][^>]+?href=['"](https?://[^'^"]+?)['"][^>]''')[0]
        
        if self.cm.isValidUrl(trailerUrl) and 1 == self.up.checkHostSupport(trailerUrl):
            urlTab.append({'name':_('Trailer'), 'url':trailerUrl, 'need_resolve':1})
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<form action', '</form>')[1]
        try:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0] )
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            
            params = dict(self.defaultParams)
            params['header'] = dict(params['header'])
            params['header']['Referer'] = cItem['url']
            
            sts, data = self.cm.getPage(url, params, post_data)
            if not sts: return []
            
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="subtitles">', '</form>')[1]
            popcornsubtitlesUrl = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''action=['"]([^'^"]+?)['"]''')[0])
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="btn', '</a>', withMarkers=True)
            for item in data:
                url  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                name = self.cleanHtmlStr(item)
                url = strwithmeta(url.replace('&#038;', '&'), {'popcornsubtitles_url':popcornsubtitlesUrl})
                urlTab.append({'name':name, 'url':url, 'need_resolve':0})
        except Exception:
            printExc()
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("HDPopcornsCom.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('HDPopcornsCom.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('HDPopcornsCom.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('HDPopcornsCom.setInitListFromFavouriteItem')
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
        elif 'list_items' == category:
            filtersTab = ['ofcategory', 'ofrating', 'ofquality']
            idx = self.currItem.get('f_idx', 0)
            if idx < len(filtersTab):
                self.listFilter(self.currItem, filtersTab)
            else:
                self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, HDPopcornsCom(), True, [])


