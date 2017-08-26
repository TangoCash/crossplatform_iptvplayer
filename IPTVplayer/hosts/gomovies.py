# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import urllib
import string
import random
import base64
from urlparse import urlparse
from hashlib import md5
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
config.plugins.iptvplayer.gomovies_proxy = ConfigSelection(default = "None", choices = [("None",         _("None")),
                                                                                        ("proxy_1",  _("Alternative proxy server (1)")),
                                                                                        ("proxy_2",  _("Alternative proxy server (2)"))])
config.plugins.iptvplayer.gomovies_alt_domain = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use proxy server:"), config.plugins.iptvplayer.gomovies_proxy))
    if config.plugins.iptvplayer.gomovies_proxy.value == 'None':
        optionList.append(getConfigListEntry(_("Alternative domain:"), config.plugins.iptvplayer.gomovies_alt_domain))
    return optionList
###################################################


def gettytul():
    return 'https://gostream.is/'

class GoMovies(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'GoMovies.tv', 'cookie':'gomovies.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'https://cdn.unlonecdn.ru/images/gomovies-logo-light.png'
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = None
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
            
        proxy = config.plugins.iptvplayer.gomovies_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            addParams = dict(addParams)
            addParams.update({'http_proxy':proxy})
        
        return self.cm.getPage(url, addParams, post_data)
        
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        proxy = config.plugins.iptvplayer.gomovies_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            url = strwithmeta(url, {'iptv_http_proxy':proxy})
        return url
        
    def selectDomain(self):
        domains = ['https://gostream.is/', 'https://gomovies.is/', 'https://gomovies.to/', 'https://gomovies.pet/'] #, 'https://123movieshd.to/', 'http://123movies.moscow/', 'https://123movies.ru/', 'https://123movies.is/'
        domain = config.plugins.iptvplayer.gomovies_alt_domain.value.strip()
        if self.cm.isValidUrl(domain):
            if domain[-1] != '/': domain += '/'
            domains.insert(0, domain)
        
        for domain in domains:
            for i in range(2):
                sts, data = self.getPage(domain)
                if sts:
                    if 'genre/action/' in data:
                        self.MAIN_URL = domain
                        break
                    else: 
                        continue
                break
            
            if self.MAIN_URL != None:
                break
                
        if self.MAIN_URL == None:
            self.MAIN_URL = 'https://gostream.is/' # first domain is default one
            
        try:
            urlParams = dict(self.defaultParams)
            urlParams['return_data'] = False
            sts, response = self.getPage(self.MAIN_URL, urlParams)
            url = response.geturl()
            response.close()
        except Exception:
            printExc()
        
        self.SEARCH_URL = self.MAIN_URL + 'movie/search'
        #self.DEFAULT_ICON_URL = self.MAIN_URL + 'assets/images/logo-light.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_filter_genre', 'title': 'Movies',    'url':self.MAIN_URL+'movie/filter/movie' },
                             {'category':'list_filter_genre', 'title': 'TV-Series', 'url':self.MAIN_URL+'movie/filter/series'},
                             {'category':'search',          'title': _('Search'), 'search_item':True,                        },
                             {'category':'search_history',  'title': _('Search history'),                                    } 
                            ]
        
    def fillCacheFilters(self):
        self.cacheFilters = {}
        
        sts, data = self.getPage(self.getFullUrl('movie/filter/all'), self.defaultParams)
        if not sts: return
        
        # get sort by
        self.cacheFilters['sort_by'] = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Sort by</span>', '</ul>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
        for item in tmp:
            value = self.cm.ph.getSearchGroups(item, 'href="[^"]+?/filter/all/([^"^/]+?)/')[0]
            self.cacheFilters['sort_by'].append({'sort_by':value, 'title':self.cleanHtmlStr(item)})
            
        for filter in [{'key':'quality', 'marker':'Quality</span>'},
                       {'key':'genre',   'marker':'Genre</span>'  },
                       {'key':'country', 'marker':'Country</span>'},
                       {'key':'year',    'marker':'Release</span>'}]:
            self.cacheFilters[filter['key']] = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, filter['marker'], '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
            allItemAdded = False
            for item in tmp:
                value = self.cm.ph.getSearchGroups(item, 'value="([^"]+?)"')[0]
                self.cacheFilters[filter['key']].append({filter['key']:value, 'title':self.cleanHtmlStr(item)})
                if value == 'all': allItemAdded = True
            if not allItemAdded:
                self.cacheFilters[filter['key']].insert(0, {filter['key']:'all', 'title':'All'})
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, filter, nextCategory):
        printDBG("GoMovies.listFilters")
        if {} == self.cacheFilters:
            self.fillCacheFilters()
        
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory=None):
        printDBG("GoMovies.listItems")
        url = cItem['url']
        page = cItem.get('page', 1)
        if '/search' not in url:
            # var url = 'http://123movies.to/movie/filter/' + type + '/' + 'view' + '/' + genres + '/' + countries + '/' + year + '/' + 'all' + '/' + quality;
            url += '/{0}/{1}/{2}/{3}/all/{4}'.format(cItem['sort_by'], cItem['genre'], cItem['country'], cItem['year'], cItem['quality'])
        
        if page > 1: url = url + '/{0}'.format(page)
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination">', '</ul>', False)[1]
        if '>Next &rarr;<' in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div data-movie-id=', '</a>', withMarkers=True)
        for item in data:
            url  = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-original="([^"]+?)"')[0] )
            movieId = self.cm.ph.getSearchGroups(item, 'data-movie-id="([^"]+?)"')[0]
            if icon == '': icon = cItem.get('icon', '')
            desc = self.cleanHtmlStr( item )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0] )
            if url.startswith('http'):
                params = {'good_for_fav': True, 'title':title, 'url':url, 'movie_id':movieId, 'desc':desc, 'info_url':url, 'icon':icon}
                if '-season-' not in url and 'class="mli-eps"' not in item: #and '/series' not in cItem['url']
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    params2 = dict(cItem)
                    params2.update(params)
                    self.addDir(params2)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def listEpisodes(self, cItem):
        printDBG("GoMovies.listEpisodes")
        
        tab = self.getLinksForVideo(cItem, True)
        episodeKeys = []
        episodeLinks = {}
        
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(tab)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        for item in tab:
            title = item['title'].replace(' 0', ' ')
            if title not in episodeKeys:
                episodeLinks[title] = []
                episodeKeys.append(title)
            item['name'] = item['server_title']
            episodeLinks[title].append(item)
        
        seasonNum = self.cm.ph.getSearchGroups(cItem['url']+'|', '''-season-([0-9]+?)[^0-9]''', 1, True)[0]
        for item in episodeKeys:
            episodeNum = self.cm.ph.getSearchGroups(item + '|', '''Episode\s+?([0-9]+?)[^0-9]''', 1, True)[0]
            if '' != episodeNum and '' != seasonNum:
                title = 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2)) + ' ' + item.replace('Episode %s' % episodeNum, '')
            else: title = item
            baseTitle = re.sub('Season\s[0-9]+?[^0-9]', '', cItem['title'] + ' ')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':self.cleanHtmlStr(baseTitle + ' ' + title), 'urls':episodeLinks[item]})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("GoMovies.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + '/' + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'list_episodes')
    
    def getLinksForVideo(self, cItem, forEpisodes=False):
        printDBG("GoMovies.getLinksForVideo [%s]" % cItem)
        
        if 'urls' in cItem:
            return cItem['urls']
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        #rm(self.COOKIE_FILE)
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        # get trailer
        trailer = self.cm.ph.getDataBeetwenMarkers(data, '''$('#pop-trailer')''', '</script>', False)[1]
        trailer = self.cm.ph.getSearchGroups(trailer, '''['"](http[^"^']+?)['"]''')[0]
        
        movieId = cItem.get('movie_id', '')
        if '' == movieId:
            try: movieId = str(int(cItem['url'].split('-')[-1]))
            except Exception:
                printExc()
        
        if '' == movieId: return []
        url = 'ajax/v2_get_episodes/' + movieId
        url = self.getFullUrl( url )
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="server', '<div class="clearfix">', withMarkers=True)
        for item in data:
            serverTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div id="server', '</div>', withMarkers=True)[1] )
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a', '</a>', withMarkers=True)
            for eItem in tmp:
                tmp = self.cm.ph.getDataBeetwenMarkers(eItem, 'loadEpisode(', ')', False)[1].split(',')
                if len(tmp) != 2: continue
                serverId = tmp[0].strip()
                episodeId = tmp[1].strip()
                title = self.cleanHtmlStr( eItem )
                if not forEpisodes:
                    name = serverTitle + ': ' + title
                else:
                    name = ''
                urlTab.append({'name':name, 'title':title, 'server_title':serverTitle, 'url':serverId + '|' + episodeId + '|' + cItem['url'], 'server_id':serverId, 'episode_id':episodeId, 'need_resolve':1})
            
        if len(urlTab) and self.cm.isValidUrl(trailer) and len(trailer) > 10:
            urlTab.insert(0, {'name':'Trailer', 'title':'Trailer', 'server_title':'Trailer', 'url':trailer, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab

    def uncensored1(self, data):    
        xx = ''
        xy = ''
        try:
            data = 'var location="https://gomovies.to/";String.prototype.italics=function(){return "<i></i>";};String.prototype.link=function(){return "<a href=\\"undefined\\"></a>";};String.prototype.fontcolor=function(){return "<font color=\\"undefined\\"></font>";};\n' + data + '\nfor (n in this){print(n+"="+this[n]+";");}'
            ret = iptv_js_execute( data )
            xx = data = self.cm.ph.getSearchGroups(ret['data'], '''x=([^;]+?);''')[0]
            xy = data = self.cm.ph.getSearchGroups(ret['data'], '''y=([^;]+?);''')[0]
        except Exception:
            printExc()
        return xx, xy
        
    def getVideoLinks(self, videoUrl):
        printDBG("GoMovies.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if self.cm.isValidUrl(videoUrl):
            return self.up.getVideoLinkExt(videoUrl)
        
        tmp = videoUrl.split('|')
        if len(tmp) != 3: return []
        serverId  = tmp[0]
        episodeId = tmp[1]
        referer   = tmp[2]
        
        if referer.endswith('/'):
            referer += 'watching.html'
        
        sts, data = self.getPage(referer, self.defaultParams)
        if not sts: return []
        
        #rm(self.COOKIE_FILE)
        #cookie = self.cm.getCookieHeader(self.COOKIE_FILE)
        
        if serverId in ['12', '13', '14', '15']:
            url = 'ajax/load_embed/' + episodeId
            url = self.getFullUrl( url )
            sts, data = self.getPage(url)
            if not sts: return []
            try:
                data = byteify(json.loads(data))
                if data['status']:
                    urlTab = self.up.getVideoLinkExt(data['embed_url'])
            except Exception:
                printExc()
                return []
        else:
            try: mid = urlparse(referer).path.split('/')[2].split('-')[-1]
            except Exception:
                mid = ''
                printExc()
            url = self.getFullUrl( 'https://gomovies.to/ajax/movie_token?eid=%s&mid=%s&_=%s' % (episodeId, mid, int(time.time() * 10000)))
            if not self.cm.isValidUrl(url): return []
            
            params = dict(self.defaultParams)
            params['header'] = dict(self.HEADER)
            params['header']['Referer'] = referer
            
            tries = 0
            while tries < 10:
                sts, data = self.getPage(url, params)
                if not sts: return []
                
                xx, xy = self.uncensored1(data)
                if xx != '' and xy != '':
                    break
                tries += 1
            
            url = 'ajax/movie_sources/%s?x=%s&y=%s' % (episodeId, xx, xy)
            url = self.getFullUrl( url )

            params = {}
            params['header'] = dict(self.AJAX_HEADER)
            sts, data = self.getPage(url, params)
            if not sts: return []
            
            subTracks = []
            if False:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<jwplayer', '>', withMarkers=True)
                printDBG("------------------------------------------------\n%s+++++++++++++++++++++++++++++++++++++++++++++\n" % tmp)
                for item in tmp:
                    url  = self.cm.ph.getSearchGroups(item, 'file="(http[^"]+?)"')[0].replace('&amp;', '&')
                    name = self.cm.ph.getSearchGroups(item, 'label="([^"]+?)"')[0]
                    if 'type="mp4"' in item:
                        urlTab.append({'name':name, 'url':url})
                    elif 'type="m3u8"' in item:
                        url = strwithmeta(url, {'Referer':referer, 'User-Agent':params['header']['User-Agent']})
                        urlTab.extend(getDirectM3U8Playlist(url, checkContent=True))
                    elif 'kind="captions"' in item:
                        format = url[-3:]
                        if format in ['srt', 'vtt']:
                            subTracks.append({'title':name, 'url':self.getFullIconUrl(url), 'lang':name, 'format':format})
            else:
                try:
                    tmp = byteify(json.loads(data))
                    printDBG("------------------------------------------------\n%s+++++++++++++++++++++++++++++++++++++++++++++\n" % tmp)
                    for item in tmp['playlist'][0]['sources']:
                        if "mp4" == item['type']:
                            urlTab.append({'name':str(item.get('label', 'default')), 'url':item['file']})
                        elif "m3u8" == item['type']:
                            url = strwithmeta(item['file'], {'Referer':referer, 'User-Agent':params['header']['User-Agent']})
                            urlTab.extend(getDirectM3U8Playlist(url, checkContent=True))
                    for item in tmp['playlist'][0]['tracks']:
                        format = item['file'][-3:]
                        if format in ['srt', 'vtt'] and "captions" == item['kind']:
                            subTracks.append({'title':str(item['label']), 'url':self.getFullIconUrl(item['file']), 'lang':item['label'], 'format':format})
                except Exception:
                    printExc()
            printDBG(subTracks)
            urlParams = {'Referer':referer, 'User-Agent':params['header']['User-Agent']}
            if len(subTracks):
                urlParams.update({'external_sub_tracks':subTracks})
            
            for idx in range(len(urlTab)):
                urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], urlParams)
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("GoMovies.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem.get('url', ''))
        if not sts: return retTab
        
        title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:title"[^>]+?content="([^"]+?)"')[0] )
        desc  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:description"[^>]+?content="([^"]+?)"')[0] )
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<meta property="og:image"[^>]+?content="([^"]+?)"')[0] )
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', '')
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="mvic-info">', '<div class="clearfix">', False)[1]
        descData = self.cm.ph.getAllItemsBeetwenMarkers(descData, '<p', '</p>')
        descTabMap = {"Director":     "director",
                      "Actor":        "actors",
                      "Genre":        "genre",
                      "Country":      "country",
                      "Release":      "released",
                      "Duration":     "duration",
                      "Quality":      "quality",
                      "IMDb":         "rated"}
        
        otherInfo = {}
        for item in descData:
            item = item.split('</strong>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key == 'IMDb': val += ' IMDb' 
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = val
                except Exception: continue
        
        if '' != cItem.get('movie_id', ''):
            rating = ''
            sts, data = self.getPage(self.getFullUrl('ajax/movie_rate_info/' + cItem['movie_id']))
            if sts: rating = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div id="movie-mark"', '</label>', True)[1] )
            if rating != '': otherInfo['rating'] = self.cleanHtmlStr( rating )
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        if self.MAIN_URL == None:
            #rm(self.COOKIE_FILE)
            self.selectDomain()

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.fillCacheFilters()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category.startswith('list_filter_'):
            filter = category.replace('list_filter_', '')
            if filter == 'genre':     self.listFilters(self.currItem, filter, 'list_filter_country')
            elif filter == 'country': self.listFilters(self.currItem, filter, 'list_filter_year')
            elif filter == 'year':    self.listFilters(self.currItem, filter, 'list_filter_quality')
            elif filter == 'quality': self.listFilters(self.currItem, filter, 'list_filter_sort_by')
            elif filter == 'sort_by': self.listFilters(self.currItem, filter, 'list_items')
        if category == 'list_items':
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
        CHostBase.__init__(self, GoMovies(), True, [])
    
    def withArticleContent(self, cItem):
        if cItem.get('type', 'video') != 'video' and cItem.get('category', 'unk') != 'list_episodes':
            return False
        return True
    