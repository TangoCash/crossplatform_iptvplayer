# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, GetDefaultLang, \
                                                          DaysInMonth, NextMonth, PrevMonth, NextDay, PrevDay
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
import datetime
from copy import deepcopy
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.icomponents.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
#config.plugins.iptvplayer.kinomanco_vip_only = ConfigYesNo(default=False)
config.plugins.iptvplayer.kinomanco_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.kinomanco_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry(_("VIP only"), config.plugins.iptvplayer.kinomanco_vip_only))
    optionList.append(getConfigListEntry(_("e-mail")+":", config.plugins.iptvplayer.kinomanco_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.kinomanco_password))
    return optionList
###################################################

def gettytul():
    return 'https://www.kinoman.co/'

class KinomanCO(CBaseHostClass):
    CAPTCHA_CHALLENGE=''
    CAPTCHA_HASHKEY=''
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'kinoman.co', 'cookie':'kinoman.co.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'http://i2.wp.com/vodnews.pl/wp-content/uploads/2016/12/film-1594734_1920.jpg?resize=780%2C405' #'http://g1.pcworld.pl/news/thumbnails/2/7/274244_adaptiveresize_370x208.jpg'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':'https://www.kinoman.co', 'Origin':'https://www.kinoman.co', 'x-captcha-challenge':KinomanCO.CAPTCHA_CHALLENGE, 'x-captcha-hashkey':KinomanCO.CAPTCHA_HASHKEY}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        self.MAIN_URL = 'https://www.kinoman.co/'
        self.API_URL = 'https://api.kinoman.co/'
        self.API_CACHE_URL = 'https://cache_api.kinoman.co/'
        
        self.translations = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.cacheLinks   = {}
        self.cacheSeasons = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_CAT_TAB = [{'category':'list_filters',          'title': 'Movies',              'f_filters':'f_is_vip,f_years,f_categories,f_rates,f_order', 'f_type':'movie'   },
                             {'category':'list_movies_premiere',  'title': 'Movies premiere',                                                                  'f_type':'movie'   },
                             {'category':'list_filters',          'title': 'Series',              'f_filters':'f_is_vip,f_q,f_years,f_rates,f_order',          'f_type':'series'  },
                             {'category':'list_series_premiere',  'title': 'Series premiere',                                                                  'f_type':'episode' },
                             {'category':'list_filters',          'title': 'Playlists',           'f_filters':'f_playlists',                                                      },
                             
                             {'category':'search',                'title': _('Search'),              'search_item':True,                                                             },
                             {'category':'search_history',        'title': _('Search history'),                                                                                      } 
                            ]
        #{'category':'list_filters',          'title': _('Episodes'),            'f_filters':'f_is_vip,f_years,f_categories,f_rates,f_order', 'f_type':'episode' },
        #{'category':'list_filters',          'title': _('Others'),              'f_filters':'f_is_vip,f_years,f_categories,f_rates,f_order', 'f_type':'other'   },
        #{'category':'list_actors',           'title': 'Actors',                                                                              'f_type':'person'  },
        #{'category':'list_filters',          'title': 'Episodes',               'f_filters':'f_years,f_categories,f_rates,f_order',          'f_type':'episode' },
        
        self.login = ''
        self.password = ''
        self.loggedIn = None
        self.logginInfo = '' 
        self.isVip = False
    
    def cleanHtmlStr(self, txt):
        txt = CBaseHostClass.cleanHtmlStr(txt)
        try: txt = txt.decode('string-escape')
        except Exception: pass
        return txt
    
    def getMainUrl(self):
        if self.urlType == 'api':
            return self.API_URL 
        elif self.urlType == 'api_cache':
            return self.API_CACHE_URL 
        else:
            return self.MAIN_URL 
            
    def getFullUrl(self, url, type=''):
        self.urlType = type
        return CBaseHostClass.getFullUrl(self, url)
        
    def _getStr(self, item, key, default=''):
        if key not in item: val = default
        if item[key] == None: val = default
        val = str(item[key])
        return self._(val)
        
    def _(self, txt):
        return self.translations.get(txt, _(txt))
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def listMainMenu(self, cItem):
        if self.translations == {} and 'pl' == GetDefaultLang():
            while True:
                url = self.getFullUrl('/api/translate?lang=1', 'api')
                sts, data = self.getPage(url)
                if not sts: break
                try:
                    data = byteify(json.loads(data), '',  baseTypesAsString=True)
                    for item in data:
                        self.translations[item['key']] = item['value']
                except Exception:
                    printExc()
                break
        
        if self.cacheFilters == {}:
            url = self.getFullUrl('/api/config?cache=3600', 'api_cache')
            sts, data = self.getPage(url)
            if not sts: return
            try:
                data = byteify(json.loads(data), noneReplacement='', baseTypesAsString=True)
                
                key = 'f_is_vip'
                tab = []
                for item in [('yes', self._('Only VIP') + ' -> ' + self._('Yes') ), ('no', self._('Only VIP') + ' -> ' + self._('No') )]:
                    tab.append({key:item[0], 'title':item[1]})
                if len(tab):
                    tab.insert(0, {'title':self._('All')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                
                key = 'f_type'
                tab = []
                for item in data['types']:
                    tab.append({key:item, 'title':self.translations.get(item, item)})
                if len(tab):
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                    
                key = 'f_years'
                tab = []
                for item in data['years']:
                    tab.append({key:item, 'title':item})
                if len(tab):
                    tab.insert(0, {'title':self._('All')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                
                key = 'f_categories'
                tab = []
                for item in data['categories']:
                    tab.append({key:item['slug'], 'title':item['name']})
                if len(tab):
                    tab.insert(0, {'title':self._('All')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                    
                key = 'f_rates'
                tab = []
                tmp = "9876543210"
                for idx in range(len(tmp)): #data['rates']:
                    tab.append({key:','.join(tmp[0:idx+1]), 'title':'%s.0 - 10.0' % tmp[idx]})
                if len(tab):
                    tab.insert(0, {'title':self._('All')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                
                key = 'f_order'
                tab = []
                for item in data['order']:
                    tab.append({key:item['display'], 'title':self._getStr(item, 'display')})
                if len(tab):
                    tab.insert(0, {'title':_('Default')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                    
                key = 'f_q'
                tab = []
                for item in 'ABCDEFGHIJKLMNOPQRSTUWZ':
                    tab.append({key:item.lower(), 'title':item})
                if len(tab):
                    tab.insert(0, {'title':_('Any')})
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                    
                key = 'f_playlists'
                tab = []
                for item in data['playlists']:
                    params = {'title':self._getStr(item, 'name')}
                    if len(item.get('related', [])):
                        subFilters = []
                        for subItem in item['related']:
                            subFilters.insert(0,{key:subItem['slug'], 'title':self._getStr(subItem, 'name')})
                        params.update({'f_sub':subFilters})
                    else:
                        params.update({key:item['slug']})
                    tab.append(params)
                    
                if len(tab):
                    self.cacheFilters[key] = tab
                    self.cacheFiltersKeys.append(key)
                
            except Exception:
                printExc()
                return
        
        for item in self.MAIN_CAT_TAB:
            params = dict(item)
            params['title'] = self._(params['title'])
            params.update({'name':'category', 'desc':self.logginInfo})
            self.addDir(params)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("KinomanCO.listFilters")
        cItem = dict(cItem)
        
        filters = cItem.get('f_filters', '').split(',')
        f_idx = cItem.get('f_idx', 0)
        
        if len(cItem.get('f_sub', [])):
            tab = cItem.pop('f_sub', [])
        else:
            if f_idx >= len(filters): return
            tab = self.cacheFilters.get(filters[f_idx], [])
            f_idx += 1
        
        cItem['f_idx'] = f_idx
        for item in tab:
            params = dict(cItem)
            params.update(item)
            if 0 == len(item.get('f_sub', [])) and f_idx >= len(filters):
                params['category'] = nextCategory
            self.addDir(params)
    
    def listSeriesPremiere(self, cItem, nextCategory):
        printDBG("KinomanCO.listSeriesPremiere [%s]" % cItem)
        dt = cItem.get('f_date', None)
        ITEMS_PER_PAGE = 3
        if dt == None:
            dt = PrevDay(datetime.date.today())
            spin = 1
            nextPage = False
        else:
            try:
                dt = datetime.datetime.strptime(dt, '%Y-%m-%d').date()
                spin = cItem['f_direction']
                nextPage = True
            except Exception:
                printExc()
                return
        
        dtIt = dt
        for m in range(ITEMS_PER_PAGE):
            premiere = []
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':dtIt.strftime("%d-%m-%Y"), 'f_premiere':dtIt.strftime("%Y-%m-%d")})
            self.addDir(params)
            dtIt = NextDay(dtIt) if spin == 1 else PrevDay(dtIt)
                
        if spin == -1: self.currList.reverse()
        
        if nextPage:
            if spin == -1: title = _('Older')
            else: title = _('Newer')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':title, 'f_date': dtIt.strftime('%Y-%m-%d')})
            self.addDir(params)
        else:
            dt = PrevDay(dt)
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Older'), 'f_direction':-1, 'f_date': dt.strftime('%Y-%m-%d')})
            self.addDir(params)
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Newer'), 'f_direction':1, 'f_date': dtIt.strftime('%Y-%m-%d')})
            self.addDir(params)
    
    def listMoviesPremiere(self, cItem, nextCategory):
        printDBG("KinomanCO.listMoviesPremiere [%s]" % cItem)
        dt = cItem.get('f_date', None)
        ITEMS_PER_PAGE = 3
        if dt == None:
            dt = PrevMonth(datetime.date.today())
            spin = 1
            nextPage = False
        else:
            try:
                dt = datetime.datetime.strptime(dt, '%Y-%m-%d').date()
                spin = cItem['f_direction']
                nextPage = True
            except Exception:
                printExc()
                return
        
        dtIt = dt
        for m in range(ITEMS_PER_PAGE):
            premiere = []
            base = dtIt.strftime("%Y-%m-")
            for d in range(1, DaysInMonth(dtIt)+1, 1):
                premiere.append(base + str(d).zfill(2))
            
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':dtIt.strftime("%m/%y"), 'f_premiere':','.join(premiere)})
            self.addDir(params)
            
            dtIt = NextMonth(dtIt) if spin == 1 else PrevMonth(dtIt)
                
        if spin == -1: self.currList.reverse()
        
        if nextPage:
            if spin == -1: title = _('Older')
            else: title = _('Newer')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':title, 'f_date': dtIt.strftime('%Y-%m-%d')})
            self.addDir(params)
        else:
            dt = PrevMonth(dt)
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Older'), 'f_direction':-1, 'f_date': dt.strftime('%Y-%m-%d')})
            self.addDir(params)
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_('Newer'), 'f_direction':1, 'f_date': dtIt.strftime('%Y-%m-%d')})
            self.addDir(params)
            
    def _addItem(self, item, cItem, nextCategory):
        title = item['name']
        try: icon  = item['main_image']['path']['cover_big']
        except Exception: icon = ''
        type = item['type']
        url  = item['slug']
        
        descTab = []
        tmp = item['is_new']
        if tmp == 'True': descTab.append('NEW')
        
        tmp = item['is_vip']
        if tmp == 'True': descTab.append('VIP')
        
        tmp = item['year']
        if tmp != '' and type == 'series': tmp += '-%s' % item.get('year_to', '')
        if tmp != '': descTab.append(tmp)
        
        tmp = self.cm.ph.getSearchGroups(item['duration'], '''PT([0-9]+?)M''')[0]
        if tmp != '': descTab.append(tmp + ' min')
        
        tmp = item['media_rate']['rate']
        if tmp != '': descTab.append(tmp+'/10')
        
        tmp = item.get('categories', '')
        tmp2 = []
        if tmp != '':
            for t in tmp: tmp2.append(t['name'])
        if len(tmp2): descTab.append(', '.join(tmp2))
        
        desc = [' | '.join(descTab), item['description']]
        desc = '[/br]'.join(desc)
        
        if type == 'episode': title = '%s - s%se%s %s' % (self.cleanHtmlStr(item['series']['name']), str(item['season_num']).zfill(2), str(item['episode_num']).zfill(2), title)
        
        params = dict(cItem)
        params.update({'good_for_fav':True, 'f_type':type, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
        if type == 'episode':
            self.addVideo(params)
        else:
            params['category'] = nextCategory
            self.addDir(params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("KinomanCO.listItems [%s]" % cItem)
        ITEMS_PER_PAGE = 30
        page = cItem.get('page', 0)
        
        query = {'cache':3600, 'page':page+1, 'limit':ITEMS_PER_PAGE, 'offset':page*ITEMS_PER_PAGE}
        
        type = cItem.get('f_type', '')
        if 'person' == type:
            url = '/api/person?' 
        else:
            url = '/api/search?'
            if type != '': query['types'] = type
        
        for key in ['is_vip', 'years', 'categories', 'rates', 'order', 'q', 'playlists', 'premiere']:
            val = cItem.get('f_%s' % key, '')
            if val != '': query[key] = val
        #if config.plugins.iptvplayer.kinomanco_vip_only.value:
        #    query['is_vip'] = 'yes'
        
        url = self.getFullUrl(url + urllib.urlencode(query), 'api_cache')
        sts, data = self.getPage(url)
        if not sts: return
        
        try:
            data = byteify(json.loads(data), noneReplacement='', baseTypesAsString=True)
            for item in data['objects']:
                self._addItem(item, cItem, nextCategory)
        except Exception:
            printExc()

        try:
            nextPage = False
            if int(data['pagination']['next_page']) > (page + 1):
                nextPage = True
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def listLangVersions(self, cItem, nextCategory):
        printDBG("KinomanCO.listLangVersions")
    
        try:
            imdbID = cItem['imdb_id']
            sts, data = self.getPage(self.getFullUrl('/request'), post_data={'mID':imdbID})
            if not sts: return
        
            # type: 0 == cinema, 2 == series, 1 == movies
            data = byteify(json.loads(data))[0]
            for item in data['languages']:
                icon = cItem.get('icon', '')
                cover = self._getStr(data, 'cover')
                if '/' in cover and not cover.endswith('/'): icon = self.getFullIconUrl(cover)
                title = self.cleanHtmlStr('%s (%s)' % (data['name'], item['text']))
                desc = []
                desc.append(self._getStr(data, 'year'))
                desc.append('~%s %s' % (self._getStr(data, 'duration'), _('min')))
                desc.append('%s/10' % (self._getStr(data, 'rating')))
                desc.append(', '.join(data.get('genres', [])))
                desc.append(', '.join(data.get('actors', []))[:3])
                desc.append(', '.join(data.get('directors', [])[:3]))
                desc = ' | '.join(desc) + '[/br]' + self.cleanHtmlStr(str(data['plot']))
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'icon':icon, 'desc':desc, 'title':title, 'item_type_id':data['type'], 'f_lang':item['symbol'].lower(), 'lang':{'id':item['ID'], 'symbol':item['symbol']}})
                self.addDir(params)
        except Exception:
            printExc()
            
    def exploreItem(self, cItem, nextCategory):
        printDBG("KinomanCO.exploreItem")
        
        try:
            type = cItem.get('f_type', '')
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> type[%s]' % type)
            url = self.getFullUrl('/api/media?slug=%s&cache=3600' % cItem['url'], 'api_cache')
            sts, data = self.getPage(url)
            if not sts: return
            data = byteify(json.loads(data), '', True)
            if "youtube" == data.get("trailer", {}).get("host", ""):
                url = 'https://www.youtube.com/watch?v=' +  data['trailer']['host_code']
                title = self.cleanHtmlStr(data['trailer']['name'])
                if type == 'episode': title = '%s (%s)' % (self.cleanHtmlStr(data['series']['name']), title)
                params = dict(cItem)
                params.pop('f_type')
                params.update({'good_for_fav':False, 'title':title, 'url':url, 'desc':_('Trailer')})
                self.addVideo(params)
            
            if type in ['movie']:
                params = dict(cItem)
                if data['is_vip'] == 'True':
                    params.update({'with_vip_link':True})
                self.addVideo(params)
            elif type == 'series':
                for item in data['series']['seasons']:
                    params = dict(cItem)
                    title = '%s %s (%s)' % (_('Season'), item['season'], self.cleanHtmlStr(item['episode_cnt']))
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 's_num':item['season']})
                    self.addDir(params)
        except Exception:
            printExc()
        
    def listEpisodes(self, cItem, nextCategory):
        printDBG("KinomanCO.listEpisodes")
        
        try:
            url = self.getFullUrl('/api/media/season?slug=%s&season=%s&cache=1800' % (cItem['url'], cItem['s_num']), 'api_cache')
            sts, data = self.getPage(url)
            if not sts: return
            data = byteify(json.loads(data), '', True)
            for item in data['episodes']:
                self._addItem(item['media'], cItem, nextCategory)
        except Exception:
            printExc()
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KinomanCO.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['f_q'] = searchPattern
        cItem['f_type'] = searchType
        
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("KinomanCO.getLinksForVideo [%s]" % cItem)
        retTab = []
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)

        cacheKey = cItem['url']
        cacheTab = self.cacheLinks.get(cacheKey, [])
        if len(cacheTab):
            return cacheTab
            
        try:
            url = self.getFullUrl('/api/link?media_slug=%s' % cItem['url'], 'api')
            sts, data = self.getPage(url)
            if not sts: return []
            data = byteify(json.loads(data), '', True)
            printDBG(data)
            
            vipItems = []
            for item in data:
                tmp = [item['site_name'], item['type'], item['quality'], item['rate']]
                if '' != item.get('file_info', ''): 
                    tmp.append('%sx%s' % (item['file_info']['width'], item['file_info']['height']))
                name = self.cleanHtmlStr(' | '.join(tmp))
                if 'True' == item['is_vip']:
                    vipItems.append({'name':name, 'url':item['code'], 'need_resolve':1})
                else:
                    retTab.append({'name':name, 'url':item['code'], 'need_resolve':1})
            #if cItem.get('with_vip_link', False):
            #    if True or self.isVip:
            #        vipItems.extend(retTab)
            #        retTab = vipItems
            #    else:
            #        retTab.extend(vipItems)
            vipItems.extend(retTab)
            retTab = vipItems
                    
        except Exception:
            printExc()
        
        if len(retTab):
            self.cacheLinks[cacheKey] = retTab
        
        return retTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("KinomanCO.getVideoLinks [%s]" % videoUrl)
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
                        
        url = self.getFullUrl('/api/link/embed?width=500&height=500', 'api')
        post_data = '{"code":"%s","secure": 1}' % (videoUrl)
        videoUrl = ''
        try:
            while True:
                httpParams = dict(self.defaultParams)
                httpParams.update({'raw_post_data':True, 'ignore_http_code_ranges':[(401,401), (500,500)]})
                httpParams['header'] = dict(httpParams['header'])
                httpParams['header']['Content-Type'] = 'application/json; charset=UTF-8'
                sts, data = self.getPage(url, httpParams, post_data)
                printDBG(data)
                if sts:
                    data = byteify(json.loads(data), '', True)
                    if not isinstance(data, str):
                        videoUrl = data['link']
                    elif 'captcha' in data.lower():
                        sts, data = self.getPage(self.getFullUrl('/api/captcha', 'api'))
                        if not sts:
                            SetIPTVPlayerLastHostError(_('Network connection failed.'))
                            break
                        data = byteify(json.loads(data), '', True)
                        captchaTitle = self._('Fill captcha')
                        imgUrl = data['image']
                        KinomanCO.CAPTCHA_HASHKEY = data['key']
                        self.defaultParams['header']['x-captcha-hashkey'] = KinomanCO.CAPTCHA_HASHKEY
                        
                        if self.cm.isValidUrl(imgUrl):
                            header = dict(self.HEADER)
                            header['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                            params = dict(self.defaultParams)
                            params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':header} )
                            filePath = GetTmpDir('.iptvplayer_captcha.jpg')
                            rm(filePath)
                            ret = self.cm.saveWebFile(filePath, imgUrl, params)
                            if not ret.get('sts'):
                                SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                                return []

                            params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
                            params['accep_label'] = _('Send')
                            params['title'] = _('Captcha')
                            params['status_text'] = captchaTitle
                            params['with_accept_button'] = True
                            params['list'] = []
                            item = deepcopy(IPTVMultipleInputBox.DEF_INPUT_PARAMS)
                            item['label_size'] = (160,75)
                            item['input_size'] = (480,25)
                            item['icon_path'] = filePath
                            item['title'] = _('Answer')
                            item['input']['text'] = ''
                            params['list'].append(item)
                
                            ret = 0
                            retArg = self.sessionEx.waitForFinishOpen(IPTVMultipleInputBox, params)
                            printDBG(retArg)
                            if retArg and len(retArg) and retArg[0]:
                                printDBG(retArg[0])
                                KinomanCO.CAPTCHA_CHALLENGE = retArg[0][0]
                                self.defaultParams['header']['x-captcha-challenge'] = KinomanCO.CAPTCHA_CHALLENGE
                                continue
                            break
                else:
                    SetIPTVPlayerLastHostError(_('Network connection failed.'))
                break
        except Exception:
            SetIPTVPlayerLastHostError(_('Unknown server response.'))
            printExc()
        
        directLink = False
        if self.cm.isValidUrl(videoUrl):
            if 0 == self.up.checkHostSupport(videoUrl):
                params = dict(self.defaultParams)
                params.update({'return_data':False})
                try:
                    sts, response = self.cm.getPage(videoUrl, params)
                    videoUrl = response.geturl()
                    type = response.info().type.lower()
                    printDBG("type [%s]" % type)
                    if 'video' in type:
                        directLink = True
                    response.close()
                except Exception:
                    printExc()
            if directLink:
                urlTab.append({'name':'direct_link', 'url':videoUrl})
            else:
                urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("KinomanCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        
        try:
            type = cItem.get('f_type', '')
            printDBG('> > > > type[%s]' % type)
            url = self.getFullUrl('/api/media?slug=%s&cache=3600' % cItem['url'], 'api_cache')
            sts, data = self.getPage(url)
            if not sts: return []
            data = byteify(json.loads(data), '', True)
            
            printDBG(data)
            
            title = self.cleanHtmlStr(data['name'])
            try: icon  = data['main_image']['path']['cover_big']
            except Exception: icon = ''
            desc = self.cleanHtmlStr(data.get('description', ''))
            
            tmp = data.get('year', '')
            if tmp != '': otherInfo['year'] = tmp
            
            tmp = data.get('premiere', '')
            if tmp != '': otherInfo['released'] = tmp
            
            tmp = self.cm.ph.getSearchGroups(data['duration'], '''PT([0-9]+?)M''')[0]
            if tmp != '': otherInfo['duration'] = tmp + ' min'
            
            tmp = data.get('categories', '')
            tmp2 = []
            if tmp != '':
                for item in tmp: tmp2.append(item['name'])
            if len(tmp2): otherInfo['categories'] = ', '.join(tmp2)
            
            tmp = data.get('original_name', '')
            if tmp != '': otherInfo['alternate_title'] = self.cleanHtmlStr(tmp)
            
            tmp = data['media_rate']['imdb_rate']
            if tmp != '': otherInfo['imdb_rating'] = '%s/10' % (data['media_rate']['imdb_rate'])
            
            if title == '': title = cItem['title']
            if desc == '':  desc = cItem.get('desc', '')
            if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        except Exception:
            printExc()
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def tryTologin(self):
        printDBG('tryTologin start')
        
        if self.login == config.plugins.iptvplayer.kinomanco_login.value and \
           self.password == config.plugins.iptvplayer.kinomanco_password.value:
           return 
        
        self.login = config.plugins.iptvplayer.kinomanco_login.value
        self.password = config.plugins.iptvplayer.kinomanco_password.value
        
        self.defaultParams.pop('x-user-token', None)
        self.logginInfo = ''
        self.isVip = False
        
        if '' == self.login.strip() or '' == self.password.strip():
            printDBG('tryTologin wrong login data')
            self.loggedIn = None
            return
            
        url = self.getFullUrl('/api/user/login', 'api')
        post_data = '{"password":"%s","login":"%s"}' % (self.password, self.login)
        httpParams = dict(self.defaultParams)
        httpParams.update({'raw_post_data':True, 'ignore_http_code_ranges':[(401,401)]})
        httpParams['header'] = dict(httpParams['header'])
        httpParams['header']['Content-Type'] = 'application/json; charset=UTF-8'
        
        sts, data = self.getPage(url, httpParams, post_data)
        printDBG(data)
        if sts:
            try:
                data = byteify(json.loads(data), '', True)
                if not isinstance(data, str):
                    self.defaultParams['x-user-token'] = data['token']
                    self.loggedIn = True
                    logginInfo = []
                    logginInfo.append(self._('Points') + '\t' + data['points'])
                    logginInfo.append(self._('Vip valid') + '\t' + data['vip_valid'])
                    logginInfo.append(self._('Vip level') + '\t' + data['vip_level'])
                    self.logginInfo = '[/br]'.join(logginInfo)
                    if data['vip_valid'] != '' and data['vip_level'] > 0:
                        self.isVip = True
                    return
                else:
                    msg = data
            except Exception:
                msg = _('Unknown server response.')
                printExc()
        else:
            msg = _('Network connection failed.')
        
        self.sessionEx.open(MessageBox, _('Login failed.') + '\n' + (_('Error message "%s".') % msg), type = MessageBox.TYPE_ERROR, timeout = 10)
        printDBG('tryTologin failed')
        self.loggedIn = False
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        self.tryTologin()
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_movies_premiere':
            self.listMoviesPremiere(self.currItem, 'list_items')
        elif category == 'list_series_premiere':
            self.listSeriesPremiere(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem, 'explore_item')
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
        CHostBase.__init__(self, KinomanCO(), True, [])
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Movies"),      "movie"))
        searchTypesOptions.append((_("Series"),     "series"))
        searchTypesOptions.append((_("Episodes"),  "episode"))
        return searchTypesOptions
        
    def withArticleContent(self, cItem):
        if cItem.get('f_type') in ['movie', 'series', 'episode'] and (cItem.get('category') in ['explore_item', 'list_episodes'] or cItem.get('type') in ['video']):
            return True
        return False
    
    