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
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import time
import re
import urllib
import string
import random
import base64
from copy import deepcopy
from hashlib import md5
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
    return 'http://paczamy.pl/'

class PaczamyPl(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'paczamy.pl', 'cookie':'paczamypl.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://i.imgur.com/qVbTKH4.png'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'http://paczamy.pl/'
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',   'title': _('Movies'),     'f_type':'movie',  'url':self.getFullUrl('filmy-online')           },
                             {'category':'list_filters',   'title': _('Series'),     'f_type':'series', 'url':self.getFullUrl('seriale-online')         },
                             {'category':'list_top',       'title': _('Top movies'), 'f_type':'movie',  'url':self.getFullUrl('top-100-filmy-online')   },
                             {'category':'list_top',       'title': _('Top series'), 'f_type':'series', 'url':self.getFullUrl('top-50-seriale-online')  },

                             {'category':'search',         'title': _('Search'), 'search_item':True,},
                             {'category':'search_history', 'title': _('Search history'),            } 
                            ]
                            
    def getStr(self, item, key):
        if key not in item: return ''
        if item[key] == None: return ''
        return str(item[key])
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def fillCacheFilters(self, cItem):
        printDBG("PaczamyPl.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        self.cacheFilters['token'] = self.cm.ph.getSearchGroups(data, '''token\s*:\s*['"]([^'^"]+?)['"]''')[0]
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('All')})
                self.cacheFiltersKeys.append(key)
        # genres
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="genre-box">', '<div class="form-group">')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<label', '</label>')
        addFilter(tmp, 'value', 'genres', True)
        
        # year
        if cItem['f_type'] == 'movie':
            self.cacheFilters['f_year'] = []
            year = datetime.now().year
            while year >= 1978:
                self.cacheFilters['f_year'].append({'title': str(year), 'f_year': year})
                year -= 1
            self.cacheFilters['f_year'].insert(0, {'title':_('Any')})
            self.cacheFiltersKeys.append('f_year')
            
        # order 
        self.cacheFilters['f_order'] = []
        for desc in [True, False]:
            for item in [('release_date', 'Data wydania'), ('created_at', 'Data dodania'), ('views', 'Liczba wyświetleń'), ('mc_user_score', 'Ocena'), ('mc_num_of_votes', 'Liczba głosów'), ('title', 'Alfabetycznie')]:
                value = item[0]
                if desc: 
                    title = '\xe2\x86\x93 '
                    value += 'Desc'
                else: 
                    title = '\xe2\x86\x91 '
                    value += 'Asc'
                title += item[1]
                self.cacheFilters['f_order'].append({'title':title, 'f_order': value})
        self.cacheFiltersKeys.append('f_order')
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("PaczamyPl.listFilters")
        cItem = dict(cItem)
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if 0 == len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("PaczamyPl.listItems")
        perPage = 20
        page = cItem.get('page', 1)
        baseUrl = 'titles/paginate?_token=' + self.cacheFilters['token'] + '&perPage={0}'.format(perPage) + '&type={0}'.format(cItem['f_type']) + '&availToStream=true' + '&page={0}'.format(page)
        if 'f_genres' in cItem:
            baseUrl += '&genres%5B%5D={0}'.format(urllib.quote(cItem['f_genres']))
        if 'f_order' in cItem:
            baseUrl += '&order={0}'.format(cItem['f_order'])
        if 'f_year' in cItem:
            baseUrl += '&after={0}-12-31'.format(cItem['f_year']-1)
            baseUrl += '&before={0}-1-1'.format(cItem['f_year']+1)
        if 'f_min_rating' in cItem:
            baseUrl += '&minRating={0}'.format(cItem['f_min_rating'])
        if 'f_query' in cItem:
            baseUrl += '&query={0}'.format(cItem['f_query'])
            
        sts, data = self.getPage(self.getFullUrl(baseUrl), {'header':self.AJAX_HEADER})
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data['items']:
                try:
                    if item['type'] == 'movie': url = 'filmy-online'
                    else: url = 'seriale-online'
                    url   = self.getFullUrl(url + '/'  + str(item['id']))
                    title = self.getStr(item, 'title')
                    if title.strip() == '': title = self.getStr(item, 'original_title')
                    title = '{0} ({1})'.format(title, self.getStr(item, 'year'))
                    desc  = '{0}/10 | {1}[/br]{2}'.format(self.getStr(item, 'imdb_rating'), self.getStr(item, 'genre'), self.getStr(item, 'plot'))
                    params = dict(cItem)
                    params.update({'good_for_fav': True, 'priv_title':self.getStr(item, 'title'), 'priv_alt_title':self.getStr(item, 'original_title'), 'title':title, 'url':url, 'f_type':self.getStr(item, 'type'), 'priv_id':self.getStr(item, 'id'), 'icon':self.getFullIconUrl(self.getStr(item, 'poster')), 'desc':desc})
                    if item['type'] == 'movie':
                        self.addVideo(params)
                    else:
                        params['category'] = nextCategory
                        self.addDir(params)
                except Exception:
                    printExc()
            if data['totalItems'] > page * perPage:
                params = dict(cItem)
                params.update({'title':_('Next page'), 'page':page+1})
                self.addDir(params)
        except Exception:
            printExc()
        
    def listTop(self, cItem, nextCategory):
        printDBG("PaczamyPl.listItems2")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<p style="text-align:center">', '<footer id="footer">')[1]        
        #data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<p', '</p>')
        #for idx in range(0, len(data), 2):
        #    try:
        #        item = ''.join(data[idx:idx+2])
        #    except Exception:
        #        printExc()
        #        continue
        data = data.split('.jpg" style')
        for item in data:
            item += '.jpg"'
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            desc = ''
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            title = title.replace('Online PL', '')
            
            params = dict(cItem)
            params.update({'good_for_fav': True, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            if cItem['f_type'] == 'movie':
                self.addVideo(params)
            else:
                params['category'] = nextCategory
                self.addDir(params)
            
    def listSeasons(self, cItem, nextCategory):
        printDBG("PaczamyPl.listSeasons")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'vars.title =', '};', False)[1].strip() + '}'
        
        try:
            trailerUrl = self.cm.ph.getSearchGroups(data, '''"trailer"\s*:\s*(['"]http[^'^"]+?['"])''')[0] 
            trailerUrl = byteify(json.loads(trailerUrl))
            if self.cm.isValidUrl(trailerUrl):
                params = dict(cItem)
                params.update({'good_for_fav': True, 'title':cItem['title'] + ' - ' + _('trailer'), 'f_type':'trailer', 'url':trailerUrl})
                self.addVideo(params)
        except Exception:
            printExc()
                
        try:
            data = byteify(json.loads(data))
            for item in data['season']:
                title = self.getStr(item, 'title')
                if '' == title: title = _('Season {0}'.format(item['number']))
                url   = self.getFullUrl(cItem['url'] + '/seasons/'  + str(item['number']))
                overview = self.getStr(item, 'overview')
                if overview == '':
                    desc = cItem['desc']
                else:
                    desc  = '{0}[/br]{1}'.format(self.getStr(item, 'release_date'), overview)
                params = {'good_for_fav': True, 'category':nextCategory, 'f_type':cItem['f_type'], 'title':title, 'url':url, 'priv_stitle':cItem['title'], 'priv_snum':self.getStr(item, 'number'), 'priv_id':self.getStr(item, 'id'), 'icon':self.getStr(item, 'poster'), 'desc':desc}
                self.addDir(params)
        except Exception:
            printExc()
        
    def listEpisodes(self, cItem):
        printDBG("PaczamyPl.listEpisodes")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        sNum = cItem['priv_snum']
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="media">', '</li>', withMarkers=True)
        for item in data:
            #if '<div class="status"' not in item: continue
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            status = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<a', '</a>')[1])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1])
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            desc   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<strong', '</div>')[1].replace('</strong>', '[/br]'))
            eNum   = url.split('/')[-1]
            title  = cItem['priv_stitle'] + ': s{0}e{1} {2}'.format(sNum.zfill(2), eNum.zfill(2), title)
            params = {'good_for_fav': True, 'f_type':cItem['f_type'], 'title':title, 'url':url, 'icon':icon, 'desc':status + '[/br]' + desc}
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("PaczamyPl.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        if 'token' not in self.cacheFilters:
            sts, data = self.getPage(self.MAIN_URL)
            if not sts: return
            self.cacheFilters['token'] = self.cm.ph.getSearchGroups(data, '''token\s*:\s*['"]([^'^"]+?)['"]''')[0]
        cItem = dict(cItem)
        cItem.update({'f_type':'', 'f_query':urllib.quote_plus(searchPattern)})
        self.listItems(cItem, 'list_seasons')
        
    def getLinksForVideo(self, cItem):
        printDBG("PaczamyPl.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'trailer' == cItem['f_type']:
            return self.up.getVideoLinkExt(cItem['url'])
            
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        jsonData = self.cm.ph.getDataBeetwenMarkers(data, 'vars.title =', '};', False)[1].strip() + '}'
        if 'movie' == cItem['f_type']:
            try:
                trailerUrl = self.cm.ph.getSearchGroups(jsonData, '''"trailer"\s*:\s*(['"]http[^'^"]+?['"])''')[0] 
                trailerUrl = byteify(json.loads(trailerUrl))
                if self.cm.isValidUrl(trailerUrl):
                    urlTab.append({'name':_('Trailer'), 'url':trailerUrl, 'need_resolve':1})
            except Exception:
                printExc()
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr data-id=', '</tr>', withMarkers=True)
        for item in data:
            name = item.replace('<div class="vote-positive"', '\xe2\x86\x91<div ')
            name = name.replace('<div class="vote-negative"', '\xe2\x86\x93<div ')
            name = self.cleanHtmlStr(name).replace('KLIKNIJ TUTAJ I OGLĄDAJ ', '').replace('Zgłoś niedziałający link', '')
            url  = self.cm.ph.getSearchGroups(item, '''playVideo[^'^"]+?['"](http[^'^"]+?)['"]''')[0].strip()
            urlTab.append({'name':name, 'url':url, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("PaczamyPl.getVideoLinks [%s]" % videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('PaczamyPl.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('PaczamyPl.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('PaczamyPl.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def getArticleContent(self, cItem):
        printDBG("PaczamyPl.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return retTab
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, 'id="content"', '<div class="col-sm-4')[1]
        
        title = cItem.get('priv_title', '')
        altTitle = cItem.get('priv_alt_title', '')
        
        if title == '': title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(descData, '<h1', '</h1>')[1] )
        if altTitle == '': altTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(descData, '<h2', '</h2>')[1] )
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(descData, '<p class="plot"', '</p>')[1])
        icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(descData, '<img[^>]+?src="([^"]+?)"')[0] )
        
        if title == '': title = cItem['title']
        if desc == '':  title = cItem['desc']
        if icon == '':  title = cItem['icon']
        
        otherInfo = {}
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(descData, '<div class="details-block">', '</ul>')
        for item in tmp:
            value = ', '.join([self.cleanHtmlStr(x) for x in self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')])
            if value == '': continue
            if 'Scenariusz:' in item:
                otherInfo['writer'] = value
            elif 'Reżyseria:' in item:
                otherInfo['director'] = value
            elif 'Gwiazdy:' in item:
                otherInfo['stars'] = value
                
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li><strong>', '</li>')
        for item in tmp:
            value = self.cleanHtmlStr(item.split('</strong>')[-1])
            if value == '': continue
            if 'Premiera:' in item:
                otherInfo['released'] = value
            elif 'Kraj ' in item:
                otherInfo['country'] = value
        
        rating = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(descData, '<div class="rating">', '</div>', False)[1])
        if rating != '': otherInfo['rating'] = rating
        
        if altTitle != '': otherInfo['alternate_title'] = altTitle
        
        ret = [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(ret)
        return ret
        
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
            self.cacheLinks = {}
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_top':
            self.listTop(self.currItem, 'list_seasons')
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
        CHostBase.__init__(self, PaczamyPl(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] not in ['list_seasons', 'list_episodes']):
            return False
        return True
    