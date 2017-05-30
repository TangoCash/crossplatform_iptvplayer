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
config.plugins.iptvplayer.movies123_proxy = ConfigSelection(default = "None", choices = [("None",     _("None")),
                                                                                         ("proxy_1",  _("Alternative proxy server (1)")),
                                                                                         ("proxy_2",  _("Alternative proxy server (2)"))])
config.plugins.iptvplayer.moviesto123_alt_domain = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use proxy server:"), config.plugins.iptvplayer.movies123_proxy))
    if config.plugins.iptvplayer.movies123_proxy.value == 'None':
        optionList.append(getConfigListEntry(_("Alternative domain:"), config.plugins.iptvplayer.moviesto123_alt_domain))
    return optionList
###################################################


def gettytul():
    return 'https://123movies.st/'

class T123Movies(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'T123Movies.tv', 'cookie':'123moviesto.cookie', 'cookie_type':'MozillaCookieJar'})
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.DEFAULT_ICON_URL = 'https://123movies.st/assets/movie/frontend/images/123movies.png'
        self.MAIN_URL = None
        self.cacheFiltersKeys = []
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self._myFun = None
        
    def uncensored(self, data):    
        cookieItems = {}
        try:
            jscode = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQp2YXIgd2luZG93ID0gdGhpczsNCnZhciBsb2NhdGlvbiA9ICJodHRwczovLzlhbmltZS50by8iOw0KU3RyaW5nLnByb3RvdHlwZS5pdGFsaWNzPWZ1bmN0aW9uKCl7cmV0dXJuICI8aT48L2k+Ijt9Ow0KU3RyaW5nLnByb3RvdHlwZS5saW5rPWZ1bmN0aW9uKCl7cmV0dXJuICI8YSBocmVmPVwidW5kZWZpbmVkXCI+PC9hPiI7fTsNClN0cmluZy5wcm90b3R5cGUuZm9udGNvbG9yPWZ1bmN0aW9uKCl7cmV0dXJuICI8Zm9udCBjb2xvcj1cInVuZGVmaW5lZFwiPjwvZm9udD4iO307DQpBcnJheS5wcm90b3R5cGUuZmluZD0iZnVuY3Rpb24gZmluZCgpIHsgW25hdGl2ZSBjb2RlXSB9IjsNCkFycmF5LnByb3RvdHlwZS5maWxsPSJmdW5jdGlvbiBmaWxsKCkgeyBbbmF0aXZlIGNvZGVdIH0iOw0KZnVuY3Rpb24gZmlsdGVyKCkNCnsNCiAgICBmdW4gPSBhcmd1bWVudHNbMF07DQogICAgdmFyIGxlbiA9IHRoaXMubGVuZ3RoOw0KICAgIGlmICh0eXBlb2YgZnVuICE9ICJmdW5jdGlvbiIpDQogICAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoKTsNCiAgICB2YXIgcmVzID0gbmV3IEFycmF5KCk7DQogICAgdmFyIHRoaXNwID0gYXJndW1lbnRzWzFdOw0KICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbGVuOyBpKyspDQogICAgew0KICAgICAgICBpZiAoaSBpbiB0aGlzKQ0KICAgICAgICB7DQogICAgICAgICAgICB2YXIgdmFsID0gdGhpc1tpXTsNCiAgICAgICAgICAgIGlmIChmdW4uY2FsbCh0aGlzcCwgdmFsLCBpLCB0aGlzKSkNCiAgICAgICAgICAgICAgICByZXMucHVzaCh2YWwpOw0KICAgICAgICB9DQogICAgfQ0KICAgIHJldHVybiByZXM7DQp9Ow0KT2JqZWN0LmRlZmluZVByb3BlcnR5KGRvY3VtZW50LCAiY29va2llIiwgew0KICAgIGdldCA6IGZ1bmN0aW9uICgpIHsNCiAgICAgICAgcmV0dXJuIHRoaXMuX2Nvb2tpZTsNCiAgICB9LA0KICAgIHNldCA6IGZ1bmN0aW9uICh2YWwpIHsNCiAgICAgICAgcHJpbnQodmFsKTsNCiAgICAgICAgdGhpcy5fY29va2llID0gdmFsOw0KICAgIH0NCn0pOw0KQXJyYXkucHJvdG90eXBlLmZpbHRlciA9IGZpbHRlcjsNCiVzDQoNCg==''') % (data)                     
            ret = iptv_js_execute( jscode )
            if ret['sts'] and 0 == ret['code']:
                printDBG(ret['data'])
                data = ret['data'].split('\n')
                for line in data:
                    line = line.strip()
                    if not line.endswith('=/'): continue
                    line = line.split(';')[0]
                    line = line.replace(' ', '').split('=')
                    if 2 != len(line): continue
                    cookieItems[line[0]] = line[1].split(';')[0]
        except Exception:
            printExc()
        return cookieItems
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
            
        proxy = config.plugins.iptvplayer.seriesonlineio_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            addParams = dict(addParams)
            addParams.update({'http_proxy':proxy})
            
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        if sts:
            try:
                tmpUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<script src=['"]([^'^"]*?/token[^'^"]*?)['"]''')[0])
                if self.cm.isValidUrl(tmpUrl):
                    tmpSts, tmpData = self.cm.getPageCFProtection(tmpUrl, addParams)
                    cookieItems = self.uncensored(tmpData);
                    self.defaultParams['cookie_items'] = cookieItems
            except Exception:
                printExc()
        return sts, data
            
        
    def getFullIconUrl(self, url):
        m1 = 'amp;url='
        if m1 in url: url = url.split(m1)[-1]
        url = self.getFullUrl(url)
        proxy = config.plugins.iptvplayer.seriesonlineio_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            url = strwithmeta(url, {'iptv_http_proxy':proxy})
            
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def selectDomain(self):
        domains = ['https://123movies.st/']
        domain = config.plugins.iptvplayer.moviesto123_alt_domain.value.strip()
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
            self.MAIN_URL = domains[0]
        
        self.SEARCH_URL = self.MAIN_URL + 'search'
        
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': 'Movies',     'url':self.MAIN_URL+'movies',    'f_type':{'name':'type[]', 'value':'movie'} },
                             {'category':'list_filters',    'title': 'TV-Series',  'url':self.MAIN_URL+'tv-series', 'f_type':{'name':'type[]', 'value':'series'}},
                             {'category':'search',          'title': _('Search'), 'search_item':True, },
                             {'category':'search_history',  'title': _('Search history'),             } 
                            ]
        
    def fillCacheFilters(self, cItem):
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(self.getFullUrl('movies'), self.defaultParams)
        if not sts: return
        
        for filter in [{'key':'f_quality',  'marker':'Quality</span>'},
                       {'key':'f_genre',    'marker':'Genre</span>'  },
                       {'key':'f_country',  'marker':'Country</span>'},
                       {'key':'f_year',     'marker':'Release</span>'},
                       {'key':'f_subtitle', 'marker':'Subtitle</span', 'title':_('Subtitle: '), 'all_label':_('any')}]:
            key    = filter['key']
            marker = filter['marker']
            title  = filter.get('title', '')
            allLabel = filter.get('all_label', _('All'))
            self.cacheFilters[key] = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, marker, '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
            allItemAdded = False
            for item in tmp:
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
                self.cacheFilters[key].append({key:{'name':name, 'value':value}, 'title':title + self.cleanHtmlStr(item)})
                if value == 'all': allItemAdded = True
            if len(self.cacheFilters[key]):
                self.cacheFiltersKeys.append(key)
                if not allItemAdded:
                    self.cacheFilters[key].insert(0, {'title':allLabel})
        
        # fix problem with GENRE and 'COUNTRY' filter
        for fixItem in [('f_genre', 'GENRE'), ('f_country', 'COUNTRY')]:
            key = fixItem[0]
            tmp = self.cm.ph.getDataBeetwenMarkers(data, fixItem[1], '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
            for item in tmp:
                url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                title = self.cleanHtmlStr(item)
                for idx in range(len(self.cacheFilters[key])):
                    if self.cacheFilters[key][idx]['title'] == title:
                        self.cacheFilters[key][idx][key]['url'] = url
                        break
        
        # get sort by
        key = 'f_sort'
        self.cacheFilters[key] = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Sort by</span>', '</ul>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
        for item in tmp:
            value = self.cm.ph.getSearchGroups(item, '''data-value=['"]([^'^"]+?)['"]''')[0]
            self.cacheFilters[key].append({'f_sort':{'name':'sort', 'value':value}, 'title':self.cleanHtmlStr(item)})
        self.cacheFiltersKeys.append(key)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("AnimeTo.listFilters")
        cItem = dict(cItem)
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if f_idx >= len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory=None, searchPattern=''):
        printDBG("T123Movies.listItems")
        url = cItem['url']
        getParams = {}
        
        page = cItem.get('page', 1)
        if page > 1:
            getParams['page'] = page
        
        if '/search' in url:
            getParams['keyword'] = searchPattern
        else:
            newUrl = ''
            for key in cItem:
                if key.startswith('f_') and key not in ['f_idx']:
                    filter = cItem[key]
                    if newUrl == '' and 'url' in filter:
                        newUrl = filter['url']
                    else:
                        getParams[filter['name']] = filter['value']
            if newUrl != '':
                url = newUrl
            
        url += '?' + urllib.urlencode(getParams)
        sts, data = self.getPage(self.getFullUrl(url))
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination">', '</ul>', False)[1]
        if '>&raquo;</a>' in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="ml-item"', '</a>', withMarkers=True)
        for item in data:
            url  = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            dataTip = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-tip="([^"]+?)"')[0] )
            desc = self.cleanHtmlStr( item )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0] )
            if url.startswith('http'):
                params = {'good_for_fav': True, 'title':title, 'url':url, 'desc':desc, 'info_url':dataTip, 'icon':icon}
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
        printDBG("T123Movies.listEpisodes")
        
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
        printDBG("seasonNum[%s]" % (seasonNum))
        if seasonNum == '': seasonNum = self.cm.ph.getSearchGroups(cItem['url']+'|', '''\-([0-9]+?)\.[A-Za-z0-9]+?\|''', 1, True)[0]
        printDBG("seasonNum[%s]" % (seasonNum))
        for item in episodeKeys:
            episodeNum = self.cm.ph.getSearchGroups(item + '|', '''Episode\s+?([0-9]+?)[^0-9]''', 1, True)[0]
            if episodeNum == '':
                try: episodeNum = str(int(item))
                except Exception: pass
            if '' != episodeNum and '' != seasonNum:
                title = 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2)) #+ ' ' + item.replace('Episode %s' % episodeNum, '')
            else: title = item
            baseTitle = re.sub('Season\s[0-9]+?[^0-9]', '', cItem['title'] + ' ')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':self.cleanHtmlStr(baseTitle + ' ' + title), 'urls':episodeLinks[item]})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("T123Movies.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 0)
        if page == 0: self.getPage(self.getMainUrl())
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL
        self.listItems(cItem, 'list_episodes', searchPattern)
    
    def getLinksForVideo(self, cItem, forEpisodes=False):
        printDBG("T123Movies.getLinksForVideo [%s]" % cItem)
        
        if 'urls' in cItem:
            return cItem['urls']
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        # get trailer
        trailer = self.cm.ph.getDataBeetwenMarkers(data, '''$('#pop-trailer')''', '</script>', False)[1]
        trailer = self.cm.ph.getSearchGroups(trailer, '''['"](http[^"^']+?)['"]''')[0]

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="server"', '<div class="clearfix">', withMarkers=True)
        for item in data:
            serverTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<label', '</label>', withMarkers=True)[1] )
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>', withMarkers=True)
            printDBG(tmp)
            for eItem in tmp:
                url = self.getFullUrl( self.cm.ph.getSearchGroups(eItem, '''href=['"]([^"^']+?)['"]''')[0] )
                if not self.cm.isValidUrl(url): continue
                dataId = self.cm.ph.getSearchGroups(eItem, '''data-id=['"]([^"^']+?)['"]''')[0]
                title = self.cleanHtmlStr( eItem )
                if not forEpisodes:
                    name = serverTitle + ': ' + title
                else:
                    name = ''
                url = strwithmeta(url, {'data_id':dataId})
                urlTab.append({'name':name, 'title':title, 'server_title':serverTitle, 'url':url, 'need_resolve':1})
            
        if len(urlTab) and self.cm.isValidUrl(trailer) and len(trailer) > 10:
            urlTab.insert(0, {'name':'Trailer', 'title':'Trailer', 'server_title':'Trailer', 'url':trailer, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab

    def _updateParams(self, params):
        if self._myFun == None:
            try:
                tmp = 'ZGVmIHphcmF6YShpbl9hYmMpOg0KICAgIGRlZiByaGV4KGEpOg0KICAgICAgICBoZXhfY2hyID0gJzAxMjM0NTY3ODlhYmNkZWYnDQogICAgICABiID0gZmYoYiwgYywgZCwgYSwgdGFiQlszXSwgMjIsIC0xMDQ0NTI1MzMwKTsN\rZGVmIHphcmF6YShwYXJhbXMpOg0KICAgIGRlZiBuKHQsIGUpOg0KICAgICAgICBuID0gMA0KICAgICAgICByID0gMA0KICAgICAgICBpID0gW10NCiAgICAgICAgZm9yIHMgaW4gcmFuZ2UoMCwgMjU2KToNCiAgICAgICAgICAgIGkuYXBwZW5kKHMpDQogICAgICAgIGZvciBzIGluIHJhbmdlKDAsIDI1Nik6DQogICAgICAgICAgICBuID0gKG4gKyBpW3NdICsgb3JkKHRbcyAlIGxlbih0KV0pKSAlIDI1Ng0KICAgICAgICAgICAgYSA9IGlbc10NCiAgICAgICAgICAgIGlbc10gPSBpW25dDQogICAgICAgICAgICBpW25dID0gYQ0KICAgICAgICBzID0gMA0KICAgICAgICBuID0gMCANCiAgICAgICAgZm9yIG8gaW4gcmFuZ2UobGVuKGUpKToNCiAgICAgICAgICAgIHMgPSAocysxKSAlIDI1Ng0KICAgICAgICAgICAgbiA9IChuICsgaVtzXSkgJSAyNTYNCiAgICAgICAgICAgIGEgPSBpW3NdDQogICAgICAgICAgICBpW3NdID0gaVtuXQ0KICAgICAgICAgICAgaVtuXSA9IGENCiAgICAgICAgICAgIHIgKz0gb3JkKGVbb10pIF4gaVsoaVtzXSArIGlbbl0pICUgMjU2XSAqIG8gKyBvDQogICAgICAgIHJldHVybiByDQogICAgaGFzaCA9IDANCiAgICBmb3Iga2V5IGluIHBhcmFtczoNCiAgICAgICAgaGFzaCArPSBuKHN0cihrZXkpLCBzdHIocGFyYW1zW2tleV0pKQ0KICAgIHBhcmFtcyA9IGRpY3QocGFyYW1zKQ0KICAgIHBhcmFtc1snXyddID0gaGFzaA0KICAgIHJldHVybiBwYXJhbXMNCg=='
                tmp = base64.b64decode(tmp.split('\r')[-1]).replace('\r', '')
                _myFun = compile(tmp, '', 'exec')
                vGlobals = {"__builtins__": None, 'len': len, 'dict':dict, 'list': list, 'ord':ord, 'range':range, 'str':str}
                vLocals = { 'zaraza': '' }
                exec _myFun in vGlobals, vLocals
                self._myFun = vLocals['zaraza']
            except Exception:
                printExc()
        try: params = self._myFun(params)
        except Exception: printExc()
        return params
        
    def getVideoLinks(self, videoUrl):
        printDBG("T123Movies.getVideoLinks [%s]" % videoUrl)
        metaData = strwithmeta(videoUrl).meta
        urlTab = []
        subTracks = []
        
        if 'data_id' not in metaData:
            return self.up.getVideoLinkExt(videoUrl)
            
        sts, data = self.getPage(videoUrl)
        if not sts: return []
        
        timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([0-9]+?)['"]''')[0]

        getParams = {'ts':timestamp, 'id':metaData['data_id'], 'W':'1'}
        getParams = self._updateParams(getParams)
        url = self.getFullUrl('/ajax/film/update-views?' + urllib.urlencode(getParams))
        sts, data = self.getPage(url)
        if not sts: return []
        
        m = "++++++++++++++++++++++++++++++++"
        printDBG('%s\n%s\n%s' % (m, data, m))
        
        getParams = {'ts':timestamp, 'id':metaData['data_id'], 'update':'0'}
        getParams = self._updateParams(getParams)
        
        url = self.getFullUrl('/ajax/episode/info?' + urllib.urlencode(getParams))
        
        sts, data = self.getPage(url)
        if not sts: return []
        
        try:
            serverData = byteify(json.loads(data))
            printDBG('%s\n%s\n%s' % (m, serverData, m))
            
            subUrl = serverData.get('subtitle', '')
            if self.cm.isValidUrl(subUrl):
                subTracks
                format = subUrl.split('?')[0][-3:]
                if format in ['srt', 'vtt']:
                    subTracks.append({'title':_('English'), 'url':subUrl, 'lang':'en', 'format':format})
            
            if serverData['type'] == 'direct':
                url = serverData['grabber']
                getParams.update(serverData['params'])
                getParams = self._updateParams(getParams)
                sts, data = self.getPage(url + '?' + urllib.urlencode(getParams))
                if not sts: return []
                data = byteify(json.loads(data))
                printDBG('%s\n%s\n%s' % (m, data, m))
                error = data.get('error', None)
                if error != None: SetIPTVPlayerLastHostError(str(error))
                for item in data['data']:
                    if 'mp4' in item['type']:
                        urlTab.append({'name':item['label'], 'url':item['file']})
                urlTab = urlTab[::-1]
            else:
                urlTab = self.up.getVideoLinkExt(serverData['target'])
        except Exception:
            printExc()
        
        printDBG(subTracks)
        if len(subTracks):
            for idx in range(len(urlTab)):
                itemSubTracks = strwithmeta(urlTab[idx]['url']).meta.get('external_sub_tracks', [])
                itemSubTracks.extend(subTracks)
                urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], {'external_sub_tracks':itemSubTracks})
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("SeriesOnlineIO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem.get('url', ''))
        if not sts: return retTab
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h1', '</h1>')[1])
        desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="desc">', '</div>')[1])
        icon = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<meta property="og:image"[^>]+?content="([^"]+?)"')[0] )
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="mvic-desc">', '<div class="clearfix">')[1]
        
        if title == '': title = cItem['title']
        if desc == '':  desc  = cItem.get('desc', '')
        if icon == '':  icon  = cItem.get('icon', '')
        
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
            item = item.split('</b>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key == 'IMDb': val += ' IMDb' 
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = val
                except Exception: continue
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullIconUrl(icon)}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('T123Movies.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('T123Movies.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('T123Movies.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
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
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
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
        CHostBase.__init__(self, T123Movies(), True, [])
    
    def withArticleContent(self, cItem):
        if cItem['type'] != 'video' and cItem['category'] != 'list_episodes':
            return False
        return True
    