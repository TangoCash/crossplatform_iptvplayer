# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
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
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.iptvcomponents.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################)
config.plugins.iptvplayer.kinoman_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.kinoman_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.kinoman_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Użytkownik KinomanTV?", config.plugins.iptvplayer.kinoman_premium))
    if config.plugins.iptvplayer.kinoman_premium.value:
        optionList.append(getConfigListEntry("  KinomanTV login:", config.plugins.iptvplayer.kinoman_login))
        optionList.append(getConfigListEntry("  KinomanTV hasło:", config.plugins.iptvplayer.kinoman_password))

    return optionList
def gettytul():
    return 'http://kinoman.tv/'

class KinomanTV(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'KinomanTV.tv', 'cookie':'kinomantv.cookie', 'cookie_type':'MozillaCookieJar'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.apiHost = "http://api.lajt.kinoman.tv/api/"
        self.apiCacheHost = "http://cache.lajt.kinoman.tv/api/"
        
        self.DEFAULT_ICON_URL = 'http://www.userlogos.org/files/logos/8596_famecky/kinoman.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_filter_genres', 'title': 'Filmy',   'url':self.apiCacheHost+'movie',  'icon':self.DEFAULT_ICON_URL},
                             {'category':'list_series_abc',    'title': 'Seriale', 'url':self.apiCacheHost+'series', 'icon':self.DEFAULT_ICON_URL},
                             {'category':'search',             'title': _('Search'), 'search_item':True,             'icon':self.DEFAULT_ICON_URL},
                             {'category':'search_history',     'title': _('Search history'),                         'icon':self.DEFAULT_ICON_URL}]
        self.MOVIES_TAB = [{'category':'list_filter_genres',   'title': 'Kategorie'}]
        self.SERIES_TAB = [{'category':'list_series_abc',      'title': 'Lista'}]
        
        qualities = [ {'title': "--Wszystkie--"     }, 
                      {'fquality': "3", 'title': "Wysoka HD" },
                      {'fquality': "2", 'title': "Średnia"   },
                      {'fquality': "1", 'title': "Niska"     }]

        rates = [ {'title': "--Wszystkie--"     }, 
                  {'frate': "9", 'title': "9.0 - 10.0"}, 
                  {'frate': "8", 'title': "8.0 - 9.0" },
                  {'frate': "7", 'title': "7.0 - 8.0" },
                  {'frate': "6", 'title': "6.0 - 7.0" },
                  {'frate': "5", 'title': "5.0 - 6.0" },
                  {'frate': "4", 'title': "4.0 - 5.0" },
                  {'frate': "3", 'title': "3.0 - 4.0" },
                  {'frate': "2", 'title': "2.0 - 3.0" },
                  {'frate': "1", 'title': "1.0 - 2.0" }]
                    
        years = [ {'title': "--Wszystkie--"     }, 
                  {'fyear': "2016", 'title': "2016"        }, 
                  {'fyear': "2015", 'title': "2015"        }, 
                  {'fyear': "2014", 'title': "2014"        }, 
                  {'fyear': "2013", 'title': "2013"        }, 
                  {'fyear': "2012", 'title': "2012"        }, 
                  {'fyear': "2011", 'title': "2011"        }, 
                  {'fyear': "2010", 'title': "2010"        }, 
                  {'fyear': "2005", 'title': "2005 - 2009" }, 
                  {'fyear': "2000", 'title': "2000 - 2004" }, 
                  {'fyear': "1990", 'title': "1990 - 1999" }, 
                  {'fyear': "1980", 'title': "1980 - 1989" }, 
                  {'fyear': "1970", 'title': "1970 - 1979" }, 
                  {'fyear': "1960", 'title': "1960 - 1969" }, 
                  {'fyear': "1950", 'title': "1950 - 1959" }]
                  
        sort_by = [{'forder': "year",     'title': "Data premiery"    },
                   {'forder': "rate",     'title': "Ocena"            }, 
                   {'forder': "rate_cnt", 'title': "Ilość głowsów"    },
                   {'forder': "views",    'title': "Ilość odsłon"     },
                   {'forder': "fav_cnt",  'title': "Ilość ulubionych" }]
         
        self.cacheFilters = {'qualities':qualities, 'rates':rates, 'years':years, 'sort_by':sort_by}
        self.genresByKey = {}
        self.cacheLinks = {}
        self.cacheSeries = {}
        self.loggedIn = None
        self.token = ''
        self.isPremium = None
        
    def getIconUrl(self, hash):
        # .../o.jpg - big, .../m.jpg - small
        return 'http://static.kinoman.tv/s/c/%s/%s/%s/o.jpg' % (hash[0:4], hash[4:6], hash[6:8])
    
    def fillCacheFilters(self):
        self.cacheFilters.update({'types':[], 'genres':[]})
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.cm.getPage(self.apiCacheHost + 'movie_filter', params)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))
            self.genresByKey = data['genres_byKey']
            for item in data['types']:
                self.cacheFilters['types'].append({'ftype':str(item['id']), 'title':item['name']})
            self.cacheFilters['types'].insert(0, {'title':'--Wszystkie--'})
            for item in data['genres']:
                if '' != item['name'].strip():
                    self.cacheFilters['genres'].append({'fgenre':str(item['id']), 'title':'%s (%s)' % (item['name'], item['cnt'])})
            self.cacheFilters['genres'].insert(0, {'title':'--Wszystkie--'})
        except Exception:
            printExc()
        
    def listFilters(self, cItem, filter, nextCategory):
        printDBG("KinomanTV.listFilters")
        if {} == self.cacheFilters:
            self.fillCacheFilters()
        
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listMovieItems(self, cItem):
        printDBG("KinomanTV.listMovieItems")
        page = cItem.get('page', 0)
        
        queryTab = []
        
        if 'forder' in cItem:
            queryTab.append('order%5Bcol%5D={0}'.format(cItem['forder']))
            queryTab.append('order%5Bdir%5D=desc')
        
        queryTab.append('limit=20')
        queryTab.append('offset={0}'.format(page*20))
        
        for key in ['fgenre', 'fquality', 'frate', 'ftype', 'fyear', 'frate']:
            if key in cItem:
                queryTab.append('{0}%5B%5D={1}'.format(key[1:], cItem[key]))
        
        for key in ['name_like']:
            if key in cItem:
                queryTab.append('{0}={1}'.format(key, cItem[key]))
        
        url = cItem['url'] + '?' + '&'.join(queryTab)
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        
        nextPage = False
        try:
            data = byteify(json.loads(data))
            if data.get('cnt', 0) > ((page+1) * 20):
                nextPage = True
            
            for item in data['rows']:
                title = item['name']
                if "" != item.get("orginal_name", ""): title += ' / %s' % item["orginal_name"]
                if "" != item.get("year", ""): title += ' (%s)' % item["year"]
                if "" != item.get("type_short", ""): title += ' [%s]' % item["type_short"]
                icon = self.getIconUrl(item['hash'])
                
                desc = ''
                try:
                    genresIds = item.get("genre_ids", "").split(',')
                    genres = []
                    for id in genresIds:
                        genres.append(self.genresByKey[id]['name'])
                    desc = ', '.join(genres)
                    if desc != '': desc += ' | '
                except Exception: printExc()
                
                try: desc += 'Ocena: %s/%s | Odsłon: %s | Komentarzy: %s | Ulubionych: %s' % (item.get('rate', 0), item.get('rate_cnt', 0), item.get('views', 0), item.get('comment_cnt', 0), item.get('fav_cnt', 0))
                except Exception: printExc()
                if desc != '': desc += '[/br]'
                desc += str(item.get('description', ''))
                
                params = dict(cItem)
                params.update({'good_for_fav': True, 'hash':item['hash'], 'movie_id':item['id'], 'uri':item['uri'], 'title':self.cleanHtmlStr(title), 'icon':icon, 'desc':self.cleanHtmlStr(desc)})
                self.addVideo(params)
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def fillSeriesCache(self, url):
        self.cacheSeries = {'series_list':[], 'by_letters':{}, 'letters_list':[]}
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            self.cacheSeries['series_list'] = data['rows']
            for idx in range(len(self.cacheSeries['series_list'])):
                item = self.cacheSeries['series_list'][idx]
                letter = self.cleanHtmlStr( item['name'] ).decode('utf-8')[0].encode('utf-8').upper()
                if letter.isdigit(): letter = '0-9'
                if letter not in self.cacheSeries['letters_list']: 
                    self.cacheSeries['letters_list'].append(letter)
                    self.cacheSeries['by_letters'][letter] = [idx]
                else: self.cacheSeries['by_letters'][letter].append( idx ) 
        except Exception:
            printExc()
            
    def listSeriesABC(self, cItem, nextCategory):
        printDBG("KinomanTV.listSeriesABC")
        if 0 == len(self.cacheSeries.get('letters_list', [])):
            self.fillSeriesCache(cItem['url'])
                
        for item in self.cacheSeries.get('letters_list', []):
            params = dict(cItem)
            params.update({'title':item, 'letter':item, 'category':nextCategory})
            self.addDir(params)
            
    def listSeriesByLetter(self, cItem, nextCategory):
        printDBG("KinomanTV.listSeriesByLetter")
        
        tab = self.cacheSeries.get('by_letters', {}).get(cItem.get('letter', ''), [])
        for idx in tab:
            self.addSeriesItem(cItem, nextCategory, self.cacheSeries['series_list'][idx])
            
    def addSeriesItem(self, cItem, nextCategory, item):
            title = item['name']
            if "" != item.get("orginal_name", ""): title += ' / %s' % item["orginal_name"]
            if "" != item.get("year", ""): title += ' (%s)' % item["year"]
            if "" != item.get("type_short", ""): title += ' [%s]' % item["type_short"]
            icon = self.getIconUrl(item['hash'])
            
            desc = ''
            try:
                genresIds = item.get("genre_ids", "").split(',')
                genres = []
                for id in genresIds:
                    genres.append(self.genresByKey[id]['name'])
                desc = ', '.join(genres)
                if desc != '': desc += ' | '
            except Exception: printExc()
            
            try: desc += 'Ocena: %s/%s | Odsłon: %s | Komentarzy: %s | Ulubionych: %s' % (item['rate'], item['rate_cnt'], item['views'], item['comment_cnt'], item['fav_cnt'])
            except Exception: printExc()
            if desc != '': desc += '[/br]'
            desc += str(item.get('description', ''))
            
            params = dict(cItem)
            params.update({'category':nextCategory, 'good_for_fav': True, 'hash':item['hash'], 'series_id':item['id'], 'uri':item['uri'], 'title':self.cleanHtmlStr(title), 'icon':icon, 'desc':self.cleanHtmlStr(desc)})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("KinomanTV.listEpisodes")
        page = cItem.get('page', 0)
        
        queryTab = []
        
        queryTab.append('limit=200')
        queryTab.append('offset={0}'.format(page*200))
        
        for key in ['series_id']:
            if key in cItem:
                queryTab.append('{0}={1}'.format(key, cItem[key]))
        
        url = self.apiCacheHost + 'episodes' + '?' + '&'.join(queryTab)
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        
        nextPage = False
        try:
            data = byteify(json.loads(data))
            if data.get('cnt', 0) > ((page+1) * 200):
                nextPage = True
            
            for item in data['rows']:
                title = item['series_name'] + ': s%se%s '% (item['season'].zfill(2), item['episode'].zfill(2)) + item['name']
                icon = self.getIconUrl(item['hash'])
                params = dict(cItem)
                params.update({'good_for_fav': True, 'hash':item['hash'], 'episode_id':item['id'], 'uri':item['uri'], 'title':self.cleanHtmlStr(title), 'icon':icon})
                self.addVideo(params)
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KinomanTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        if 'movie' == searchType:
            cItem = dict(cItem)
            cItem['url'] = self.apiCacheHost+'movie'
            cItem['name_like'] = urllib.quote_plus(searchPattern)
            self.listMovieItems(cItem)
        else:
            cItem = dict(cItem)
            cItem['url'] = self.apiCacheHost+'series'
            if 0 == len(self.cacheSeries.get('series_list', [])):
                self.fillSeriesCache(cItem['url'])
            for item in self.cacheSeries.get('series_list', []):
                if self.cleanHtmlStr(searchPattern).upper() in self.cleanHtmlStr(item['name']).upper():
                    self.addSeriesItem(cItem, 'list_episodes', item)
    
    def getLinksForVideo(self, cItem, forEpisodes=False):
        printDBG("KinomanTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'movie_id' in cItem: post_data = {"movie_id":cItem['movie_id']}
        elif 'episode_id' in cItem: post_data = {"episode_id":cItem['episode_id']}
        else: return []
        
        url = self.apiHost + 'link'
        
        if '' != self.token: 
            post_data['token'] = self.token
            url += '?userToken=' + self.token
        
        params = dict(self.defaultParams)
        params.update({'header':self.AJAX_HEADER, 'raw_post_data':True})
        sts, data = self.cm.getPage(url, params, json.dumps(post_data))
        if not sts: return urlTab
        
        try:
            data = byteify(json.loads(data))
            printDBG(data)
            for item in data:
                name = '%s | %s' % (item['type_name'], item['quality_name'])
                urlTab.append({'name':name, 'url':item['code'], 'need_resolve':1})
        except Exception:
            printExc()
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("KinomanTV.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        code    = videoUrl
        baseUrl = self.apiHost + 'player/get'
        
        params = dict(self.defaultParams)
        params.update({'header':self.AJAX_HEADER, 'raw_post_data':True})
        
        players = []
        if '' != self.token and self.isPremium:
            players.append('vip')
        players.append('free')
        
        for player in players:
            if player == 'free':
                post_data = {"action":"getFreePlayer", "code":code}
                url = baseUrl
            else:
                url = baseUrl + '?userToken=' + self.token
                post_data = {"action":"getHash","code":code,"token":self.token}
                
                sts, data = self.cm.getPage(url, params, json.dumps(post_data))
                if not sts: continue
                
                try:
                    hash = byteify(json.loads(data))
                except Exception:
                    printExc()
                    continue
                post_data = {"action":"getPlayerByHash","hash":hash,"token":self.token}
            
            sts, data = self.cm.getPage(url, params, json.dumps(post_data))
            if not sts: continue
            
            try:
                data = byteify(json.loads(data))
                printDBG(data)
                if 'iframe' in data: 
                    videoUrl = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0] ).replace(' ', '%20')
                    if videoUrl.startswith('http://') or url.startswith('https://'):
                        urlTab.extend( self.up.getVideoLinkExt(videoUrl) )
                elif data.startswith('http://') or data.startswith('https://'): 
                    urlTab.append({'name':'Premium link', 'url':data})
            except Exception:
                printExc()
            
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("KinomanTV.getArticleContent [%s]" % cItem)
        retItem = {}
        
        params = dict(self.defaultParams)
        params['header'] = self.AJAX_HEADER
        if 'movie_id' in cItem: type = 'movie'
        else: type = 'series'
        
        sts, data = self.cm.getPage(self.apiCacheHost + type + '/get?uri=' + cItem['uri'], params)
        if not sts: return []
        
        try:
            data  = byteify(json.loads(data))
            printDBG(data)
            retItem['images']  = [{'title':'', 'url':self.getIconUrl(data['hash'])}]
            retItem['title'] = self.cleanHtmlStr(data['name'])
            retItem['text']  = self.cleanHtmlStr(data['description'])
            
            retItem['other_info'] = {}
            if '' != data.get('orginal_name', ''): retItem['other_info']['alternate_title'] = str(data['orginal_name'])
            if '' != data.get('views', ''):        retItem['other_info']['views']           = str(data['views'])
            if '' != data.get('year', ''):         retItem['other_info']['year']            = str(data['year'])
            if '' != data.get('rate', ''):         retItem['other_info']['rating']          = str(data['rate'])
            if '' != data.get('rate_cnt', ''):     retItem['other_info']['rated']           = str(data['rate_cnt'])
            try:
                genre = data.get("genre_ids", "").split(',')
                genres = []
                for id in genre:
                    genres.append(self.genresByKey[id]['name'])
                genre = ', '.join(genres)
                if '' != genre: retItem['other_info']['genre'] = genre
            except Exception:
                printExc()
            
            try:
                sts, data = self.cm.getPage(self.apiCacheHost + 'actor?limit=100&movie_id=' + data['id'], params)
                data  = byteify(json.loads(data))
                actors     = []
                production = []
                director   = []
                for item in data['rows']:
                    if 'aktorzy' == item['value']: actors.append(item['name'])
                    if 'produkcja' == item['value']: production.append(item['name'])
                    if 'reżyserzy' == item['value']: director.append(item['name'])
                if len(actors):     retItem['other_info']['actors'] = ', '.join(actors)
                if len(production): retItem['other_info']['production'] = ', '.join(production)
                if len(director):   retItem['other_info']['director'] = ', '.join(director)
            except Exception:
                printExc()
                return []
        except Exception:
            printExc()
            return []
        return [retItem]
    
    def getFavouriteData(self, cItem):
        printDBG('KinomanTV.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
       
        if 'movie_id' in cItem:
            params['movie_id'] = cItem['movie_id']
        elif 'episode_id' in cItem:
            params['episode_id'] = cItem['episode_id']
        elif 'series_id' in cItem:
            params['series_id'] = cItem['series_id']
        else:
            params = {}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('KinomanTV.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('KinomanTV.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def tryTologin(self, login, password):
        printDBG('tryTologin start')
        
        post_data = {"username":login,"password":password}
        params = dict(self.defaultParams)
        params.update({'header':self.AJAX_HEADER, 'raw_post_data':True})
        sts, data = self.cm.getPage(self.apiHost + 'user/login', params, json.dumps(post_data))
        if not sts: return False, _('Connection to server failed!')
        
        try:
            data = byteify(json.loads(data))
            printDBG(data)
            self.token = data['token']
        except Exception:
            printExc()
            return False, 'Błędne dane do logowania.'
            
        # sprawdzenie
        post_data = {"token":self.token}
        params = dict(self.defaultParams)
        params.update({'header':self.AJAX_HEADER, 'raw_post_data':True})
        sts, data = self.cm.getPage(self.apiHost + 'user/getUser?userToken=' + self.token, params, json.dumps(post_data))
        if not sts: return False, _('Connection to server failed!')
        
        msg = ''
        try:
            data = byteify(json.loads(data))
            printDBG(data)
            msg = ''
            if None != data.get('premium_valid', None):
                self.isPremium = True
                msg = 'Premium ważne do: %s\n' % data['premium_valid']
            else:
                self.isPremium = False
            msg += 'Punktów: %s\n' % data['points']
        except Exception:
            printExc()
            return False, 'Błędne dane do logowania.'
        return True, msg
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn and config.plugins.iptvplayer.kinoman_premium.value:
            self.loggedIn, msg = self.tryTologin(config.plugins.iptvplayer.kinoman_login.value, config.plugins.iptvplayer.kinoman_password.value)
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % config.plugins.iptvplayer.kinoman_login.value, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.\n' + msg, type = MessageBox.TYPE_INFO, timeout = 10 )
                
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.fillCacheFilters()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'movies':
            self.listsTab(self.MOVIES_TAB, self.currItem)
        elif category == 'series':
            self.listsTab(self.SERIES_TAB, self.currItem)
        elif category.startswith('list_filter_'):
            filter = category.replace('list_filter_', '')
            if filter == 'genres':         self.listFilters(self.currItem, filter, 'list_filter_types')
            elif filter == 'types':        self.listFilters(self.currItem, filter, 'list_filter_years')
            elif filter == 'years':        self.listFilters(self.currItem, filter, 'list_filter_qualities')
            elif filter == 'qualities':    self.listFilters(self.currItem, filter, 'list_filter_rates')
            elif filter == 'rates':        self.listFilters(self.currItem, filter, 'list_filter_sort_by')
            elif filter == 'sort_by':      self.listFilters(self.currItem, filter, 'list_items')
            else: category = 'list_items'
        if category == 'list_items':
            self.listMovieItems(self.currItem)
        elif category == 'list_series_abc':
            self.listSeriesABC(self.currItem, 'list_series_by_letter')
        elif category == 'list_series_by_letter':
            self.listSeriesByLetter(self.currItem, 'list_episodes')
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
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, KinomanTV(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        
        if 'uri' not in cItem:
            return RetHost(retCode, value=retlist)
        hList = self.host.getArticleContent(cItem)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        if len(hList): retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
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
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Movies"),   "movie"))
        searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
        isGoodForFavourites = cItem.get('good_for_fav', False)
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem

