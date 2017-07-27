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
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.playmaxmx_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.playmaxmx_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":", config.plugins.iptvplayer.playmaxmx_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.playmaxmx_password))
    return optionList
###################################################

def gettytul():
    return 'https://playmax.mx/'

class PlayMaxMX(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'playmax.mx', 'cookie':'playmax.mx.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'https://pbs.twimg.com/profile_images/616338669209821184/5YKYgRtW.png'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://playmax.mx/'
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.cacheSeasons = {}
        self.loggedIn = None
        self.login = ''
        self.password = ''
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': _('Catalog'),             'url':self.getFullUrl('catalogo.php')   },
                             
                             {'category':'search',            'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',    'title': _('Search history'),            } 
                            ]
                            
    def getFullIconUrl(self, url):
        url = url.replace('&amp;', '&')
        return CBaseHostClass.getFullIconUrl(self, url)
        
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
        printDBG("PlayMaxMX.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                #if value == '': continue
                title = self.cleanHtmlStr(item)
                if title in ['Todo']:
                    addAll = False
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('All')})
                self.cacheFiltersKeys.append(key)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<form class="ct_form"', '</form>')[1]
        data = data.split('<div class="oh')
        if len(data): del data[0]
        for tmp in data:
            tmp = tmp.replace('name="reverse_order"', '')
            sts, tmp = self.cm.ph.getDataBeetwenReMarkers(tmp, re.compile('>'), re.compile('<input[^>]+?name=[^>]+?>', re.IGNORECASE))
            if not sts: continue
            key = self.cm.ph.getSearchGroups(tmp, '''<input[^>]+?name="([^"]+?)"''')[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div class="sel', '</div>')
            addFilter(tmp, 'value', key, False)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("PlayMaxMX.listFilters")
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
        printDBG("PlayMaxMX.listItems")
        url = cItem['url']
        page = cItem.get('page', 0)
        
        query = {}
        if page > 0: query['start'] = page * 60
        
        for key in self.cacheFiltersKeys:
            baseKey = key[2:] # "f_"
            if key in cItem: query[baseKey] = urllib.quote(cItem[key])
        
        query = urllib.urlencode(query)
        if '?' in url: url += '&' + query
        else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if  'class="next"' in data: nextPage = True
        else: nextPage = False
        
        sp = '<div class="c_fichas '
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, 'ficha_cheack_visible()', False)[1].split(sp) 
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src-data="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="c_fichas_title">', '</div>')[1] )
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '</a>', '<div class="c_fichas_title">')[1])
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'desc':desc, 'icon':icon}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("PlayMaxMX.listEpisodes")
        seasonId = cItem.get('f_season', '')
        tab = self.cacheSeasons.get(seasonId, [])
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.addVideo(params)
            
    def exploreItem(self, cItem, nextCategory):
        printDBG("PlayMaxMX.exploreItem")
        
        url = cItem['url']
        sts, data = self.getPage(url)
        if not sts: return
        
        tabTmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_b_r">', '<cb')[1]
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'load_trailers()', '}')[1]
        trailerUriBase = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''['"]?url["']?\s*:\s*['"]([^'^"]+?)['"]''')[0])
        trailerUriParams = self.cm.ph.getSearchGroups(tmp, '''['"]?data["']?\s*:\s*['"]([^'^"]+?)['"]''')[0]
        if trailerUriBase != '' and trailerUriParams != '':
            trailerUrl = trailerUriBase + '?' + trailerUriParams
            trailerTitle = self.cm.ph.getDataBeetwenReMarkers(tabTmp, re.compile('load_trailers\(\);[^>]+?>'), re.compile('</div>'), False)[1]
            if trailerTitle != '':
                params = dict(cItem)
                params.update({'good_for_fav': False, 'url':trailerUrl, 'title':trailerTitle, 'category':'list_trailers'})
                self.addDir(params)
        
        if '<div class="f_cl_t">' not in data:
            link = self.cm.ph.getSearchGroups(tabTmp, '''onclick="load_f_links\(\s*([0-9]+)\s*\,\s*([0-9]+)\s*\,''', 2)
            if '' not in link:
                url = self.getFullUrl('/c_enlaces_n.php?ficha=%s&c_id=%s' % (link[1], link[0]))       
                params = dict(cItem)
                params.update({'good_for_fav': False, 'url':url})
                self.addVideo(params)
            return
        
        self.cacheSeasons = {}
        seasonTitles = {}
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_cl_t">', '<div class="f_cl_l">')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div', '</div>')
        for item in tmp:
            seasonId = self.cm.ph.getSearchGroups(item, '''f_c_temporada\(\s*([0-9]+)\s*\)''')[0]
            if seasonId == '': continue
            title    = self.cleanHtmlStr(item)
            seasonTitles[seasonId] = title
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_cl_l">', '<div class="f_cl_p_vc">', False)[1]
        tmp = re.split('<div class="f_cl_l_t([0-9]+)"', tmp)
        if len(tmp): del tmp[0]
        if 0 != (len(tmp) % 2):
            printExc("Error occurs")
            return
        
        for idx in xrange(0, len(tmp), 2):
            seasonId = tmp[idx]
            
            item  = self.cm.ph.getAllItemsBeetwenMarkers(tmp[idx+1], '<div class="f_cl_l_c', '</div>')
            for it in item:
                num = self.cm.ph.getSearchGroups(it, '''c_num=['"]([0-9]+)[Xx]([0-9]+)['"]''', 2)
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(it, '''c_name=['"]([^'^"]+?)['"]''')[0])
                link  = self.cm.ph.getSearchGroups(it, '''load_f_links\(\s*([0-9]+)\s*\,\s*([0-9]+)\s*\,''', 2)
                url   = self.getFullUrl('/c_enlaces_n.php?ficha=%s&c_id=%s' % (link[1], link[0]))
                
                if seasonId not in self.cacheSeasons:
                    self.cacheSeasons[seasonId] = []
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':seasonTitles.get(seasonId, seasonId), 'f_season':seasonId})
                    self.addDir(params)
                title = '%s s%se%s %s' % (cItem['title'], num[0].zfill(2), num[1].zfill(2), title)
                self.cacheSeasons[seasonId].append({'good_for_fav':False, 'title':title, 'url':url})
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("PlayMaxMX.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 0)
        url = self.getFullUrl('/buscar.php?buscar=%s&mode=fichas&mode=fichas&start=%s' % (urllib.quote_plus(searchPattern), page * 20))
        sts, data = self.getPage(url)
        if not sts: return
        
        if  'class="next"' in data: nextPage = True
        else: nextPage = False
        
        sp = '<div class="bus">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div class="usuarios tbs dis-non">', False)[1].split(sp) 
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="bus_s">', '</div>', False)[1])
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'desc':desc, 'icon':icon}
            params['category'] = 'explore_item'
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def listTrailers(self, cItem):
        printDBG("PlayMaxMX.listTrailers cItem[%s]" % cItem)
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<divd class="ttrailer"', '</a>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'url\((https?://[^\)]+?\.jpg)\)')[0].strip() )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<divd class="ttrailer"', '</divd>')[1] )
            desc = self.cleanHtmlStr( item.split('</divd>')[-1] )
            
            params = dict(cItem)
            params = {'good_for_fav': False, 'title':title, 'url':url, 'desc':desc, 'icon':icon}
            self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("PlayMaxMX.getLinksForVideo [%s]" % cItem)
        linksTab = []
        
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)

        linksTab = self.cacheLinks.get(cItem['url'], [])
        if len(linksTab) > 0: return linksTab
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<divd class="tipodeenlaces" id="online1">', '<divd class="tipodeenlaces" id="descarga1">')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<divdd', '</divdd>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue
            
            # hostings
            titles = [self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0].split('/')[-1].replace('.png', '')]
            # version
            titles.append(self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<divd class="version', '</divd>')[1]))
            # quality
            titles.append(self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<divd class="calidad"', '</divd>')[1]))
            # language
            titles.append(self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''<divd\s+class="idioma"\s+title=['"]([^"^']+?)['"]''')[0]))
            # subtitles
            titles.append(self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''<divd\s+class="subtitulos"\s+title=['"]([^"^']+?)['"]''')[0]))
            # audio
            titles.append(self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<divd class="calidadaudio"', '</divd>')[1]))
            
            linksTab.append({'name':' | '.join(titles), 'url':strwithmeta(url, {'Referer':cItem['url']}), 'need_resolve':1})
        
        if len(linksTab):
            self.cacheLinks[cItem['url']] = linksTab
        
        return linksTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("PlayMaxMX.getVideoLinks [%s]" % videoUrl)
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
                        
        try:
            httpParams = dict(self.defaultParams)
            httpParams['return_data'] = False
            
            sts, response = self.cm.getPage(videoUrl, httpParams)
            videoUrl = response.geturl()
            response.close()
        except Exception:
            printExc()
            return []
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('FilmPalastTo.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('PlayMaxMX.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('PlayMaxMX.setInitListFromFavouriteItem')
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
        printDBG("PlayMaxMX.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_t"', '<div class="f_c_tab2"')[1]
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_t_b">', '</div>')[1])
        icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+?\.jpe?g[^"^']*?)["']''')[0] )
        desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'inopsis</div>', '</span>', False)[1])
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'original</div>', '</span>', False)[1])
        if tmp != '': otherInfo['alternate_title'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Año</div>', '</span>', False)[1])
        if tmp != '': otherInfo['year'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'uración</div>', '</span>', False)[1])
        if tmp != '': otherInfo['duration'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'aís</div>', '</span>', False)[1])
        if tmp != '': otherInfo['country'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'title_h="', '"', False)[1])
        if tmp != '': otherInfo['rating'] = tmp
        
        tmpTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'eparto</h5>', '<div class="opdlf">', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': tmpTab.append(t)
        if len(tmpTab): otherInfo['actors'] = ', '.join(tmpTab)
        
        tmpTab = []
        tmp = self.cm.ph.rgetAllItemsBeetwenMarkers(data, '<div class="acxenf">Director</div>', '<div class="palidlp">', False)
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': tmpTab.append(t)
        if len(tmpTab): otherInfo['directors'] = ', '.join(tmpTab)
        
        tmpTab = []
        tmp = self.cm.ph.rgetAllItemsBeetwenMarkers(data, '<div class="acxenf">Guión</div>', '<div class="palidlp">', False)
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': tmpTab.append(t)
        if len(tmpTab): otherInfo['writers'] = ', '.join(tmpTab)
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def tryTologin(self):
        printDBG('tryTologin start')
        
        rm(self.COOKIE_FILE)
        
        self.login = config.plugins.iptvplayer.playmaxmx_login.value
        self.password = config.plugins.iptvplayer.playmaxmx_password.value
        
        if '' == self.login.strip() or '' == self.password.strip():
            printDBG('tryTologin wrong login data')
            self.sessionEx.open(MessageBox, _('The host %s requires registration. \nPlease fill your login and password in the host configuration. Available under blue button.' % self.getMainUrl()), type = MessageBox.TYPE_ERROR, timeout = 10 )
            return False
            
        url = self.getFullUrl('/ucp.php?mode=login')
        
        sts, data = self.getPage(url)
        if not sts: return False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<form ', '</form>', False)
        if not sts: return False
        actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
        post_data = {}
        for item in data:
            name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
            post_data[name] = value
        
        post_data.update({'username':self.login, 'password':self.password, 'redirect':self.getFullUrl('/index.php')})
        
        httpParams = dict(self.defaultParams)
        httpParams['header'] = dict(httpParams['header'])
        httpParams['header']['Referer'] = url
        sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
        if sts and 'mode=logout' in data:
            printDBG('tryTologin OK')
            return True
     
        self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
        printDBG('tryTologin failed')
        return False
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.playmaxmx_login.value or\
            self.password != config.plugins.iptvplayer.playmaxmx_password.value:
            self.loggedIn = self.tryTologin()
        
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
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
        elif 'list_episodes' == category:
            self.listEpisodes(self.currItem)
        elif 'list_trailers' == category:
            self.listTrailers(self.currItem)
            
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
        CHostBase.__init__(self, PlayMaxMX(), True, [])
        
    def withArticleContent(self, cItem):
        if cItem['category'] != 'explore_item':
            return False
        return True
    
    