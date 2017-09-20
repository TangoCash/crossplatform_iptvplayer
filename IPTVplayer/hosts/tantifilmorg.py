# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
import string
import base64
import random
try:    import json
except Exception: import simplejson as json
from datetime import datetime
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
    return 'http://www.tantifilm.top/'
    
    

class TantiFilmOrg(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'TantiFilmOrg.tv', 'cookie':'tantifilmorg.cookie'})
        self.USER_AGENT = 'Mozilla/5.0'
        self.HEADER = {'User-Agent':self.USER_AGENT, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.cm.HEADER = self.HEADER # default header
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://www.tantifilm.top/'
        self.DEFAULT_ICON_URL = 'https://raw.githubusercontent.com/Zanzibar82/images/master/posters/tantifilm.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_categories',    'title': _('Categories'),                           'url':self.MAIN_URL  },
                             {'category':'search',             'title': _('Search'), 'search_item':True,         },
                             {'category':'search_history',     'title': _('Search history'),                     } 
                            ]
        
        self.cacheCollections = {}
        self.cookieHeader = ''
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.cacheSeries = {}
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def refreshCookieHeader(self):
        self.cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        
    def getFullIconUrl(self, url, refreshCookieHeader=True):
        url = CBaseHostClass.getFullIconUrl(self, url)
        if url == '': return ''
        if refreshCookieHeader: self.refreshCookieHeader()
        return strwithmeta(url, {'Cookie':self.cookieHeader, 'User-Agent':self.USER_AGENT})

    def listMainMenu(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listMainMenu")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<nav id="ddmenu">', '</ul>', withMarkers=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<li", '</li>', withMarkers=True)
        for item in data:
            title = self.cleanHtmlStr(item)
            if title.upper() == 'HOME': continue # not items on home page
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            params = dict(cItem)
            if 'elenco-saghe' not in url:
                params.update({'category':nextCategory, 'title':title, 'url':self.getFullUrl(url)})
                self.addDir(params)
            else:
                params.update({'category':'list_collections', 'title':title, 'url':self.getFullUrl(url)})
                self.addDir(params)
                break
                
    def listCategories(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listCategories")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="table-list">', '</ul>', withMarkers=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<li", '</li>', withMarkers=True)
        for item in data:
            title = self.cleanHtmlStr(item)
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':self.getFullUrl(url)})
            self.addDir(params)
            
    def listCollections(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listCollections")
        self.cacheCollections = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        sp = '<img class="alignnone'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="footer"', withMarkers=False)[1]
        data = data.split(sp)
        for item in data:
            icon = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if icon == '': continue
            tmpTab = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, "<a", '</a>', withMarkers=True)
            for tmpItem in tmp:
                url   = self.cm.ph.getSearchGroups(tmpItem, '''href=['"]([^'^"]+?)['"]''')[0]
                title = self.cleanHtmlStr(tmpItem)
                params= {'good_for_fav': True, 'title':title, 'url':self.getFullUrl(url), 'icon':self.getFullIconUrl(icon)}
                tmpTab.append(params)
            
            if len(tmpTab):
                self.cacheCollections[icon] = tmpTab
                title = icon.split('/')[-1].replace('png-', '').replace('.png', '').replace('-', ' ').title()
                params = dict(cItem)
                params.update({'category':nextCategory, 'title':title, 'icon':self.getFullIconUrl(icon)})
                self.addDir(params)
            
    def listColectionItems(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listColectionItems")
        tab = self.cacheCollections.get(cItem.get('icon', ''), [])
        self.listsTab(tab, {'category':nextCategory})
    
    def listItems(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listItems")
        
        url  = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            tmp = url.split('?')
            url = tmp[0]
            if not url.endswith('/'): url += '/'
            url += 'page/%s/' % (page)
            if len(tmp) == 2: url += '?' + tmp[1]
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if 'page/{0}/'.format(page+1) in data:
            nextPage = True
        else:
            nextPage = False
        
        if '?s=' in url:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="film film-2">', '<!-- search_post -->', withMarkers=True)
        else:
            if page == 1:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<h1 class="page-title">', '</body>', withMarkers=False)[1]
            else:
                tmp = self.cm.ph.rgetDataBeetwenMarkers2(data, '</body>', '<h1 class="page-title">', withMarkers=False)[1]
            if tmp == '':
                tmp = data
            data = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div class="mediaWrap', '</span>', withMarkers=True)
        for item in data:
            idx = item.find('</h2>')
            if idx > 0: item = item[:idx]
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if '/film-di-natale-streaming/' in url: continue
            if 'saghe/' in url: continue
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="title-film', '</a>')[1])
            if title.endswith('streaming'): title = title[:-9].strip()
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            desc  = self.cleanHtmlStr(item.replace('</p>', '[/br]'))
            
            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':self.getFullUrl(url), 'icon':self.getFullIconUrl(icon), 'desc':desc}
            self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
            
    def listContent(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listContent")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        # trailer
        trailerUrls = []
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="trailer"', '</div>')
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            if self.cm.isValidUrl(url) and url not in trailerUrls:
                params = dict(cItem)
                params.pop('category', None)
                trailerUrls.append(url)
                title = cItem['title'] + ' - ' + self.cleanHtmlStr(item)
                self.addVideo({'good_for_fav': True, 'title':title, 'url':url, 'video_type':'trailer', 'icon':cItem.get('icon', '')})
        
        # desc
        desc = []
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="keywords-film-left">', '</p>')[1])
        if tmp != '': desc.append(tmp)
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="content-left-film">', '</p>')[1])
        if tmp != '': desc.append(tmp)
        desc = '[/br][/br]'.join(desc)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="wpwm-movie-links">', '<div class="film-left">', False)[1]
        tmp = re.compile('''<iframe[^>]+?src=['"]([^'^"]+?)['"]''', re.IGNORECASE).findall(tmp)
        if len(tmp) == 1 and '/serietv/' in tmp[0] and self.cm.isValidUrl(tmp[0]): 
            # series
            cItem = dict(cItem)
            cItem['url'] = tmp[0]
            cItem['desc'] = desc
            self.listSeasons(cItem, nextCategory)
        elif len(tmp) > 0:
            # movie
            # add this item as video item
            params = dict(cItem)
            params.pop('category', None)
            params.update({'good_for_fav': True, 'video_type':'movie', 'desc':desc})
            self.addVideo(params)
            
    def listSeasons(self, cItem, nextCategory):
        printDBG("TantiFilmOrg.listSeasons")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<nav class="', '</select>')
        if len(data) < 2: 
            printDBG("!!!!!!!!!!!! wrong makers for series TV -> url[%s]" % cItem['url'])
            return
        
        # get seasons
        data = data[0]
        seasonName = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data.split('<ul')[0], '<a', '</a>')[1])
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>')
        printDBG(data)
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if not self.cm.isValidUrl(url): continue
            seasonTitle = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title': '%s %s' % (seasonName, seasonTitle), 'season_id':seasonTitle, 'series_title':cItem['title'], 'url':url})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("TantiFilmOrg.listEpisodes")
        
        seriesTitle = cItem['series_title']
        try: seasonNum = str(int(cItem['season_id']))
        except Exception: seasonNum = ''
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<nav class="', '</select>')
        if len(data) < 2: 
            printDBG("!!!!!!!!!!!! wrong makers for series TV -> url[%s]" % cItem['url'])
            return
        
        # get seasons
        data = data[1]
        episodeName = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data.split('<ul')[0], '<a', '</a>')[1])
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>')
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if not self.cm.isValidUrl(url): continue
            episodeTitle = self.cleanHtmlStr(item)
            try: episodeNum = str(int(episodeTitle))
            except Exception: episodeNum = ''
            
            if '' != episodeNum and '' != seasonNum:
                title = seriesTitle + ' - ' + 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2))
            else: 
                title = seriesTitle + ' - ' +  cItem['title'] + ' ' + '%s %s' % (episodeName, episodeTitle)
           
            params = {'good_for_fav': False, 'title': title, 'video_type':'episode', 'url':url, 'icon':cItem.get('icon', ''), 'desc':cItem.get('desc', '')}
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TantiFilmOrg.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        baseUrl = self.getFullUrl('?s=' + urllib.quote_plus(searchPattern))
        cItem = dict(cItem)
        cItem['url'] = baseUrl
        self.listItems(cItem, 'list_content')

    
    def getLinksForVideo(self, cItem):
        printDBG("TantiFilmOrg.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if len(self.cacheLinks.get(cItem['url'], [])):
            return self.cacheLinks[cItem['url']]
            
        type = cItem['video_type']
        if type == 'trailer':
            return self.up.getVideoLinkExt(cItem['url'])
        else:
            sts, data = self.getPage(cItem['url'])
            if not sts: return []
        
        urlTab = []
        if type == 'movie':
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="wpwm-movie-links">', '<div class="film-left">', False)[1]
            tmp = tmp.split('</ul>')
            printDBG(tmp)
            for item in tmp:
                url = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                if not self.cm.isValidUrl(url): continue
                id = self.cm.ph.getSearchGroups(item, '''id=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                title = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''<a[^>]+?href=['"]\#%s['"][^>]*?>''' % re.escape(id)), re.compile('</a>'))[1]
                title = self.cleanHtmlStr(title)
                if title == '': title = self.up.getDomain(url)
                urlTab.append({'name':title, 'url':strwithmeta(url, {'url':cItem['url']}), 'need_resolve':1})
        elif type == 'episode':
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<nav class="', '</select>')
            if len(data) < 3: 
                printDBG("!!!!!!!!!!!! wrong makers for links TV series -> url[%s]" % cItem['url'])
                return []
            
            data = data[2]
            seasonName = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data.split('<ul')[0], '<a', '</a>')[1])
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>')
            printDBG(data)
            for item in data:
                url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(item)
                if title == '': continue
                urlTab.append({'name':title, 'url':strwithmeta(url, {'url':cItem['url']}), 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("TantiFilmOrg.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            key = self.cacheLinks.keys()[0]
            for idx in range(len(self.cacheLinks[key])):
                if videoUrl in self.cacheLinks[key][idx]['url']:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                    break
                    
        if 'hostvid.xyz' == self.up.getDomain(videoUrl):
            sts, data = self.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
        
        if self.cm.isValidUrl(videoUrl):
            return self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('TantiFilmOrg.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('TantiFilmOrg.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('TantiFilmOrg.setInitListFromFavouriteItem')
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
            self.listMainMenu({'name':'category', 'url':self.MAIN_URL}, 'list_items')
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif 'list_categories' == category:
            self.listCategories(self.currItem, 'list_items')
        elif 'list_collections' == category:
            self.listCollections(self.currItem, 'list_colection_items')
        elif 'list_colection_items' == category:
            self.listColectionItems(self.currItem, 'list_content')
        elif 'list_items' == category:
            self.listItems(self.currItem, 'list_content')
        elif 'list_content' == category:
            self.listContent(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, TantiFilmOrg(), True, [])

    
