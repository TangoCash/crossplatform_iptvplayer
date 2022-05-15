# -*- coding: utf-8 -*-
###################################################
# 2021-12-30 by Blindspot - modified Filmezz
###################################################
HOST_VERSION = "2.5"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, rm, GetTmpDir, GetIPTVPlayerVerstion, MergeDicts
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
import random
import os
import datetime
import time
import zlib
import cookielib
import base64
import traceback
from copy import deepcopy
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from datetime import datetime
from hashlib import sha1
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.filmezzeu_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.filmezzeu_password = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.filmezzeu_id = ConfigYesNo(default = False)
config.plugins.iptvplayer.boxtipus = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.boxrendszer = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":", config.plugins.iptvplayer.filmezzeu_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.filmezzeu_password))
    optionList.append(getConfigListEntry("id:", config.plugins.iptvplayer.filmezzeu_id))
    return optionList
###################################################

def gettytul():
    return 'https://filmezz.club/'

class FilmezzEU(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmezz.club', 'cookie':'filmezzeu.cookie'})
        self.DEFAULT_ICON_URL = 'http://plugins.movian.tv/data/3c3f8bf962820103af9e474604a0c83ca3b470f3'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://filmezz.club/'
        self.vivn = GetIPTVPlayerVerstion()
        self.porv = self.gits()
        self.pbtp = '-'
        self.btps = config.plugins.iptvplayer.boxtipus.value
        self.brdr = config.plugins.iptvplayer.boxrendszer.value
        self.aid = config.plugins.iptvplayer.filmezzeu_id.value
        self.aid_ki = ''
        self.ilk = False
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.loggedIn = None
        self.login = ''
        self.password = ''
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}        

    def getFullIconUrl(self, url):
        return CBaseHostClass.getFullIconUrl(self, url.replace('&amp;', '&'))

    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def listMainMenu(self, cItem):
        try:
            self.cacheLinks = {}
            if not self.ebbtit(): return
            if self.btps != '' and self.brdr != '': self.pbtp = self.btps.strip() + ' - ' + self.brdr.strip()
            tab_home = 'filmezz_fooldal'
            desc_home = self.getdvdsz(tab_home, 'Főoldali felvételek megjelenítése')
            tab_movies = 'filmezz_filmek'
            desc_movies = self.getdvdsz(tab_movies, 'Filmek megjelenítése')
            tab_series = 'filmezz_sorozatok'
            desc_series = self.getdvdsz(tab_series, 'Sorozatok megjelenítése')
            tab_top_movies = 'filmezz_csucs_filmek'
            desc_top_movies = self.getdvdsz(tab_top_movies, 'Csúcsmozik megjelenítése')
            tab_top_series = 'filmezz_csucs_sorozatok'
            desc_top_series = self.getdvdsz(tab_top_series, 'Legjobb sorozatok megjelenítése')
            tab_latest_add = 'filmezz_utoljara_hozzaadva'
            desc_latest_add = self.getdvdsz(tab_latest_add, 'Legutóbb feltöltött felvételek megjelenítése')
            tab_ajanlott = 'filmezz_ajanlott'
            desc_ajanlott = self.getdvdsz(tab_ajanlott, 'Ajánlott, nézett tartalmak megjelenítése')
            tab_keresett = 'filmezz_keresett_tartalom'
            desc_keresett = self.getdvdsz(tab_keresett, 'Keresett tartalmak megjelenítése')
            tab_search = 'filmezz_kereses'
            desc_search = self.getdvdsz(tab_search, 'Keresés')
            tab_search_hist = 'filmezz_kereses_elozmeny'
            desc_search_hist = self.getdvdsz(tab_search_hist, 'Keresés az előzmények között')
            MAIN_CAT_TAB = [
                            #{'category':'list_filters', 'title': _('Home'), 'url':self.getFullUrl('kereses.php'), 'tps':'0', 'tab_id':tab_home, 'desc':desc_home   },
                            {'category':'list_items', 'title': _('Movies'), 'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=1&h=0&o=feltoltve'), 'tps':'1', 'tab_id':tab_movies, 'desc':desc_movies  },
                            {'category':'list_items', 'title': _('Series'), 'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=2&h=0&o=feltoltve'), 'tps':'2', 'tab_id':tab_series, 'desc':desc_series  },
                            {'category':'list_items', 'title': _('Top movies'), 'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=1&h=0&o=nezettseg'), 'tps':'1', 'tab_id':tab_top_movies, 'desc':desc_top_movies  },
                            {'category':'list_items', 'title': _('Top series'), 'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=2&h=0&o=nezettseg'), 'tps':'2', 'tab_id':tab_top_series, 'desc':desc_top_series  },
                            {'category':'list_items', 'title': _('Latest added'), 'url':self.getFullUrl('kereses.php?q=0&l=0&e=0&c=0&t=0&h=0&o=feltoltve'), 'tps':'0', 'tab_id':tab_latest_add, 'desc':desc_latest_add  },
                            {'category':'list_main', 'title': 'Ajánlott, nézett tartalmak', 'tab_id':tab_ajanlott, 'desc':desc_ajanlott},
                            {'category':'list_main', 'title': 'Keresett tartalmak', 'tab_id':tab_keresett, 'desc':desc_keresett},
                            {'category':'search', 'title': _('Search'), 'search_item':True, 'tps':'0', 'tab_id':tab_search, 'desc':desc_search },
                            {'category':'search_history', 'title': _('Search history'), 'tps':'0', 'tab_id':tab_search_hist, 'desc':desc_search_hist } 
                           ]
            self.listsTab(MAIN_CAT_TAB, {'name':'category'})
            vtb = self.malvadnav(cItem, '7', '2', '0', '11')
            if len(vtb) > 0:
                for item in vtb:
                    item['category'] = 'list_third'
                    self.addVideo(item)
            self.ilk = True
        except Exception:
            return

    def fillCacheFilters(self, cItem):
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                if title in ['Összes']:
                    addAll = False
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('All')})
                self.cacheFiltersKeys.append(key)
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="row form-group">', '</select>')
        for tmp in data:
            key = self.cm.ph.getSearchGroups(tmp, '''name="([^"]+?)"''')[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')
            addFilter(tmp, 'value', key, False)
        
    def listMainItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'filmezz_ajanlott':
                self.Fzkttm(cItem, tabID)
            elif tabID == 'filmezz_keresett_tartalom':
                self.Vdakstmk({'name':'history', 'category': 'search', 'tab_id':''}, 'desc', _("Type: "), tabID)
            else:
                return
        except Exception:
            return
            
    def Fzkttm(self, cItem, tabID):
        try:
            self.susn('2', '2', tabID)
            tab_ams = 'filmezz_ajnlt_musor'
            desc_ams = self.getdvdsz(tab_ams, 'Ajánlott, nézett tartalmak megjelenítése műsorok szerint')
            tab_adt = 'filmezz_ajnlt_datum'
            desc_adt = self.getdvdsz(tab_adt, 'Ajánlott, nézett tartalmak megjelenítése dátum szerint')
            tab_anzt = 'filmezz_ajnlt_nezettseg'
            desc_anzt = self.getdvdsz(tab_anzt, 'Ajánlott, nézett tartalmak megjelenítése nézettség szerint')
            A_CAT_TAB = [{'category':'list_third', 'title': 'Dátum szerint', 'tab_id':tab_adt, 'desc':desc_adt},
                         {'category':'list_third', 'title': 'Nézettség szerint', 'tab_id':tab_anzt, 'desc':desc_anzt},
                         {'category':'list_third', 'title': 'Műsorok szerint', 'tab_id':tab_ams, 'desc':desc_ams} 
                        ]
            self.listsTab(A_CAT_TAB, cItem)
        except Exception:
            return
        
    def listFilters(self, cItem, nextCategory):
        if self.ilk:
            self.susn('2', '2', 'filmezz_fooldal')
            self.ilk = False
        cItem = dict(cItem)
        cItem['desc'] = ''
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if 0 == len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listThirdItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'filmezz_ajnlt_musor':
                self.Vajnltmsr(cItem)
            elif tabID == 'filmezz_ajnlt_datum':
                self.Vajnltdtm(cItem)
            elif tabID == 'filmezz_ajnlt_nezettseg':
                self.Vajnltnztsg(cItem)
            else:
                return
        except Exception:
            return
            
    def Vajnltmsr(self,cItem):
        try:
            self.susn('2', '2', 'filmezz_ajnlt_musor')
            vtb = self.malvadnav(cItem, '3', '2', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltdtm(self,cItem):
        vtb = []
        try:
            self.susn('2', '2', 'filmezz_ajnlt_datum')
            vtb = self.malvadnav(cItem, '4', '2', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltnztsg(self,cItem):
        try:
            self.susn('2', '2', 'filmezz_ajnlt_nezettseg')
            vtb = self.malvadnav(cItem, '5', '2', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
        
    def listItems(self, cItem, nextCategory):
        try:
            tabID = cItem['tab_id']
            if tabID != '' and tabID not in ['filmezz_fooldal','filmezz_kereses','filmezz_kereses_elozmeny']:
                self.susn('2', '2', tabID)
            url = cItem['url']
            page = cItem.get('page', 0)
            
            query = {}
            if page > 0: query['p'] = page
            
            for key in self.cacheFiltersKeys:
                baseKey = key[2:] # "f_"
                if key in cItem: query[baseKey] = urllib.quote(cItem[key])
            
            query = urllib.urlencode(query)
            if '?' in url: url += '&' + query
            else: url += '?' + query
            
            sts, data = self.getPage(url)
            if not sts: return
            
            nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>')[1]
            if  '' != self.cm.ph.getSearchGroups(nextPage, 'p=(%s)[^0-9]' % (page+1))[0]: nextPage = True
            else: nextPage = False
            
            data = self.cm.ph.getDataBeetwenMarkers(data, 'movie-list', '<footer class="footer">')[1]        
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</a>')
            reDescObj = re.compile('title="([^"]+?)"')
            for item in data:
                url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
                if not self.cm.isValidUrl(url): continue
                if 'kereses.php' in url: continue
                
                icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
                title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="title">', '</span>')[1] )
                if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
                if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                
                # desc start
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li>', '</li>')
                descTab = []
                for t in tmp:
                    t = self.cleanHtmlStr(t)
                    if t == '': continue
                    descTab.append(t)
                tmp = self.cm.ph.getDataBeetwenMarkers(item, 'movie-icons">', '</ul>', False)[1]
                t = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="cover-element imdb"', '</span>')[1])
                tmp = reDescObj.findall(tmp)
                if t != '': tmp.insert(0, t)
                descTab.insert(0, ' | '.join(tmp))
                ######
                
                params = MergeDicts(cItem, {'good_for_fav': True, 'category':nextCategory , 'title':title, 'url':url, 'desc':'[/br]'.join(descTab), 'icon':icon})
                self.addDir(params)
            
            if nextPage and len(self.currList) > 0:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':page+1, 'desc':'Nyugi...\nVan még további tartalom, lapozz tovább!!!'})
                self.addDir(params)
        except Exception:
            return
            
    def exploreItem(self, cItem):
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        if len(data) == 0: return
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text"', '</div>')[1])
        desc = re.sub(r'^(.{1000}).*$', '\g<1>...', desc)
        # trailer 
        tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<a[^>]+?class="venobox"'), re.compile('>'))[1]
        url = self.cm.ph.getSearchGroups(tmp, '''href=['"]([^'^"]+?)['"]''')[0]
        title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(tmp, '''title=['"]([^'^"]+?)['"]''')[0])
        if 1 == self.up.checkHostSupport(url):
            params = dict(cItem)
            params.update({'good_for_fav': True, 'title':title, 'prev_title':cItem['title'], 'url':url, 'prev_url':cItem['url'], 'prev_desc':cItem.get('desc', ''), 'desc':desc})
            self.addVideo(params)
        reDescObj = re.compile('title="([^"]+?)"')
        titlesTab = []
        self.cacheLinks  = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-md-6 col-sm-12', '</div>')[1]
        tmp_url = self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]+?)['"]''')[0]
        sts, data = self.getPage(tmp_url)
        if not sts: return
        if len(data) == 0: return
        data = self.cm.ph.getDataBeetwenMarkers(data, 'url-list', '</body>')[1]
        data = data.split('<div class="col-sm-4 col-xs-12 host">')
        if len(data): del data[0]
        for tmp in data:
            dTab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div', '</div>')
            if len(dTab) < 2: continue 
            title = self.cleanHtmlStr(dTab[1])
            
            # serverName
            t = self.cm.ph.getDataBeetwenMarkers(tmp, 'movie-icons">', '<div', False)[1]
            serverName = reDescObj.findall(t)
            if t != '': serverName.append(self.cleanHtmlStr(t))
            serverName = ' | '.join(serverName)
            #if 'letöltés' in serverName: continue
            
            url = self.getFullUrl(urllib.unquote(self.cm.ph.getSearchGroups(tmp, '''(link_to\.php[^'^"]+?)['"]''')[0]))
            if not url:
                url = ph.find(tmp, ('<a ', '>', 'url-btn play'), '</a>')[1]
                url = self.getFullUrl(ph.search(url, ph.A)[1])
            if url == '': continue

            if url.startswith('https://adf.ly/'):
                url = urllib.unquote(url.rpartition('/')[2])
                if url == '': continue

            if title not in titlesTab:
                titlesTab.append(title)
                self.cacheLinks[title] = []
            self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        
        for item in titlesTab:
            params = dict(cItem)
            title = cItem['title']
            if item != '': title += ' :: ' + item
            params.update({'good_for_fav': True, 'title':title, 'links_key':item, 'prev_desc':cItem.get('desc', ''), 'desc':desc})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        try:
            self.suskrbt('2', '2', searchPattern)
            cItem = dict(cItem)
            cItem['url'] = self.getFullUrl('kereses.php?s=' + urllib.quote_plus(searchPattern))
            self.listItems(cItem, 'explore_item')
        except Exception:
            return
            
    def flzchim(self, i_u=''):
        try:
            if i_u != '':
                sts, data = self.getPage(i_u)
                if not sts: return
                if len(data) == 0: return
                tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<a[^>]+?class="venobox"'), re.compile('>'))[1]
                title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(tmp, '''title=['"]([^'^"]+?)['"]''')[0])
                reDescObj = re.compile('title="([^"]+?)"')
                titlesTab = []
                self.cacheLinks  = {}
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-md-6 col-sm-12', '</div>')[1]
                tmp_url = self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]+?)['"]''')[0]
                sts, data = self.getPage(tmp_url)
                if not sts: return
                if len(data) == 0: return
                data = self.cm.ph.getDataBeetwenMarkers(data, 'url-list', '</body>')[1]
                data = data.split('<div class="col-sm-4 col-xs-12 host">')
                if len(data): del data[0]
                for tmp in data:
                    dTab = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div', '</div>')
                    if len(dTab) < 2: continue 
                    title = self.cleanHtmlStr(dTab[1])
                    t = self.cm.ph.getDataBeetwenMarkers(tmp, 'movie-icons">', '<div', False)[1]
                    serverName = reDescObj.findall(t)
                    if t != '': serverName.append(self.cleanHtmlStr(t))
                    serverName = ' | '.join(serverName)
                    url = self.getFullUrl(urllib.unquote(self.cm.ph.getSearchGroups(tmp, '''(link_to\.php[^'^"]+?)['"]''')[0]))
                    if not url:
                        url = ph.find(tmp, ('<a ', '>', 'url-btn play'), '</a>')[1]
                        url = self.getFullUrl(ph.search(url, ph.A)[1])
                    if url == '': continue
                    if url.startswith('https://adf.ly/'):
                        url = urllib.unquote(url.rpartition('/')[2])
                        if url == '': continue
                    if title not in titlesTab:
                        titlesTab.append(title)
                        self.cacheLinks[title] = []
                    self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        except Exception:
            return
        
    def getLinksForVideo(self, cItem):
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        if cItem['category'] != 'list_third':
            self.susmrgts('2', '2', cItem['tps'], cItem['url'], cItem['title'], cItem['icon'], cItem['desc'], 'mnez')
            key = cItem.get('links_key', '')
        else:
            key = ''
            idx1 = cItem['title'].rfind('::')
            if -1 < idx1:
                key = cItem['title'][idx1+2:].strip()
            self.flzchim(cItem['url'])
        return self.cacheLinks.get(key, [])
        
    def getVideoLinks(self, videoUrl):
        global x
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
                        
        url = videoUrl
        printDBG(url)		
        post_data = None
        while True:
            httpParams = dict(self.defaultParams)
            httpParams['max_data_size'] = 0
            self.cm.getPage(url, httpParams, post_data)
            if 'url' in self.cm.meta: videoUrl = self.cm.meta['url']
            else: return []
            
            if self.up.getDomain(self.getMainUrl()) in videoUrl:
                sts, data = self.getPage(videoUrl)
                if not sts: return []
                
                if 'captcha' in data: data = re.sub("<!--[\s\S]*?-->", "", data)
                
                if 'google.com/recaptcha/' in data and 'sitekey' in data:
                    message = _('Link protected with google recaptcha v2.')
                    if True != self.loggedIn:
                        message += '\n' + _('Please fill your login and password in the host configuration (available under blue button) and try again.')
                    SetIPTVPlayerLastHostError(message)
                    break
                elif '<input name="captcha"' in data:
                    data = self.cm.ph.getDataBeetwenMarkers(data, '<div align="center">', '</form>')[1]
                    captchaTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h3', '</h3>')[1])
                    captchaDesc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '</h3>', '</span>')[1])
                    
                    # parse form data
                    data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>')[1]
                    
                    imgUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                    if imgUrl != '': imgUrl = '/' + imgUrl
                    if imgUrl.startswith('/'): imgUrl = urlparse.urljoin(videoUrl, imgUrl)
                    
                    printDBG("img URL [%s]" % imgUrl)
                        
                    actionUrl = self.cm.ph.getSearchGroups(data, 'action="([^"]+?)"')[0]
                    if actionUrl != '': actionUrl = '/' + actionUrl
                    if actionUrl.startswith('/'): actionUrl = urlparse.urljoin(videoUrl, actionUrl)
                    elif actionUrl == '': actionUrl = videoUrl
                        
                    captcha_post_data = dict(re.findall(r'''<input[^>]+?name=["']([^"^']*)["'][^>]+?value=["']([^"^']*)["'][^>]*>''', data))
                    
                    if self.cm.isValidUrl(imgUrl):
                        params = dict(self.defaultParams)
                        params['header'] = dict(params['header'] )
                        params['header']['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                        params = dict(self.defaultParams)
                        params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':params['header']} )
                        filePath = GetTmpDir('.iptvplayer_captcha.jpg')
                        ret = self.cm.saveWebFile(filePath, imgUrl.replace('&amp;', '&'), params)
                        if not ret.get('sts'):
                            SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                            return urlTab

                        params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
                        params['accep_label'] = _('Send')
                        params['title'] = captchaTitle
                        params['status_text'] = captchaDesc
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
                            captcha_post_data['captcha'] = retArg[0][0]
                            post_data = captcha_post_data
                            url = actionUrl
                        
                        if not sts:
                            return urlTab
                        else:
                            continue
                
                tmp = ph.IFRAME.findall(data)
                for urlItem in tmp:
                    url = self.cm.getFullUrl(urlItem[1])
                    if 1 == self.up.checkHostSupport(url):
                        videoUrl = url
                        break
            break

        if not self.up.checkHostSupport(videoUrl):
            sts, data = self.getPage(videoUrl)
            if not sts: return []
            tmp = ph.IFRAME.findall(data)
            tmp.extend(ph.A.findall(data))
            for item in tmp:
                url = self.cm.getFullUrl(item[1])
                if 1 == self.up.checkHostSupport(url):
                    videoUrl = url
                    break

        if self.up.checkHostSupport(videoUrl):
            return self.up.getVideoLinkExt(videoUrl)

        return urlTab

    def getFavouriteData(self, cItem):
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
        return json_dumps(params) 

    def getArticleContent(self, cItem):
        retTab = []
        url = cItem.get('prev_url', '')
        if url == '': url = cItem.get('url', '')
        sts, data = self.getPage(url)
        if not sts: return retTab
        if len(data) == 0: return retTab
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="text"', '</div>')[1])
        if desc == '': desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta[^>]+?name="description"[^>]+?content="([^"]+?)"')[0] )
        titleData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="title"', '</div>')[1]
        title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(titleData, '<h1', '</h1>')[1] )
        altTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(titleData, '<h2', '</h2>')[1] )
        if title != '': title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta[^>]+?name="title"[^>]+?content="([^"]+?)"')[0] )
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<link[^>]+?rel="image_src"[^>]+?href="([^"]+?)"')[0] )
        if title == '': title = cItem['title']
        if desc == '':  title = cItem['desc']
        if icon == '':  title = cItem['icon']
        
        descTabMap = {"Kategória":    "genre",
                      "Rendező":      "director",
                      "Hossz":        "duration"}
        otherInfo = {}
        descData = cItem.get('prev_desc', '')
        if descData == '': descData = cItem.get('desc', '')
        descData = descData.split('[/br]')
        for item in descData:
            item = item.split(':')
            key = item[0]
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = self.cleanHtmlStr(item[-1])
                except Exception: continue
        imdb_rating = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<span class="score">', '</span>', False)[1])
        if imdb_rating != '': otherInfo['imdb_rating'] = imdb_rating
        if altTitle != '': otherInfo['alternate_title'] = altTitle
        year = self.cm.ph.getSearchGroups(cItem.get('prev_title', ''), '\(([0-9]{4})\)')[0]
        if year == '': year = self.cm.ph.getSearchGroups(cItem['title'], '\(([0-9]{4})\)')[0]
        if year != '': otherInfo['year'] = year
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def suskrbt(self, i_md='', i_hgk='', i_mpsz=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_mpsz != '' and len(i_mpsz) > 1:
                if len(i_mpsz) > 80:
                    i_mpsz = i_mpsz[:78]
                i_mpsz = base64.b64encode(i_mpsz).replace('\n', '').strip()
                if i_hgk != '':
                    i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                    pstd = {'md':i_md, 'hgk':i_hgk, 'mpsz':i_mpsz}
                    if i_md != '' and i_hgk != '' and i_mpsz != '':
                        sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
            
    def susmrgts(self, i_md='', i_hgk='', i_mptip='', i_mpu='', i_mpt='', i_mpi='', i_mpdl='', i_mpnzs=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        try:
            if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
            if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
            if i_mpu != '': i_mpu = base64.b64encode(i_mpu).replace('\n', '').strip()
            if i_mpt != '': i_mpt = base64.b64encode(i_mpt).replace('\n', '').strip()
            if i_mpi == '':
                i_mpi = base64.b64encode('-')
            else:
                i_mpi = base64.b64encode(i_mpi).replace('\n', '').strip()
            if i_mpdl == '':
                i_mpdl = base64.b64encode('-')
            else:
                i_mpdl = base64.b64encode(i_mpdl).replace('\n', '').strip()
            if i_mpnzs != '': i_mpnzs = base64.b64encode(i_mpnzs).replace('\n', '').strip()
            pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpu':i_mpu, 'mpt':i_mpt, 'mpi':i_mpi, 'mpdl':i_mpdl, 'mpnzs':i_mpnzs}
            if i_md != '' and i_hgk != '' and i_mptip != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def getdvdsz(self, pu='', psz=''):
        bv = ''
        if pu != '' and psz != '':
            n_atnav = self.malvadst('1', '2', pu)
            if n_atnav != '' and self.aid:
                if pu == 'filmezz_filmek':
                    self.aid_ki = 'ID: ' + n_atnav + '  |  Filmezz  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = 'ID: ' + n_atnav + '\n'
            else:
                if pu == 'filmezz_filmek':
                    self.aid_ki = 'Filmezz  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = ''
            bv = self.aid_ki + psz
        return bv
        
    def malvadst(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu}
        t_s = ''
        temp_vn = ''
        temp_vni = ''
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a_div', '</div>')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '/>')
                if len(data) == 0: return t_s
                for item in data:
                    t_i = self.cm.ph.getSearchGroups(item, 'id=[\'"]([^"^\']+?)[\'"]')[0]
                    if t_i == 'vn':
                        temp_vn = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                    elif t_i == 'vni':
                        temp_vni = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                if temp_vn != '':
                    t_s = temp_vn
            return t_s
        except Exception:
            return t_s
            
    def malvadnav(self, cItem, i_md='', i_hgk='', i_mptip='', i_mpdb=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        t_s = []
        try:
            if i_md != '' and i_hgk != '' and i_mptip != '':
                if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
                if i_mpdb != '': i_mpdb = base64.b64encode(i_mpdb).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpdb':i_mpdb}
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a1_div"', '<div id="div_a2_div"')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="d_sor_d"', '</div>')
                if len(data) == 0: return t_s
                for temp_item in data:
                    temp_data = self.cm.ph.getAllItemsBeetwenMarkers(temp_item, '<span', '</span>')
                    if len(temp_data) == 0: return t_s
                    for item in temp_data:
                        t_vp = self.cm.ph.getSearchGroups(item, 'class=[\'"]([^"^\']+?)[\'"]')[0]
                        if t_vp == 'c_sor_u':
                            temp_u = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_u">', '</span>', False)[1]
                            if temp_u != '': temp_u = base64.b64decode(temp_u)
                        if t_vp == 'c_sor_t':
                            temp_t = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_t">', '</span>', False)[1]
                            if temp_t != '': temp_t = base64.b64decode(temp_t)
                        if t_vp == 'c_sor_i':
                            temp_i = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_i">', '</span>', False)[1]
                            if temp_i != '': temp_i = base64.b64decode(temp_i)
                        if t_vp == 'c_sor_l':
                            temp_l = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_l">', '</span>', False)[1]
                            if temp_l != '': temp_l = base64.b64decode(temp_l)
                        if t_vp == 'c_sor_n':
                            temp_n = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_n">', '</span>', False)[1]
                            if temp_n != '': temp_n = base64.b64decode(temp_n)
                        if t_vp == 'c_sor_tip':
                            temp_tp = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_tip">', '</span>', False)[1]
                            if temp_tp != '': temp_tp = base64.b64decode(temp_tp)
                    if temp_u == '' and temp_t =='': continue
                    if temp_n == '': temp_n = '1'
                    params = MergeDicts(cItem, {'good_for_fav': True, 'url':temp_u, 'title':temp_t, 'icon':temp_i, 'desc':temp_l, 'nztsg':temp_n, 'tps':temp_tp})
                    t_s.append(params)       
            return t_s
        except Exception:
            return []
            
    def susn(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu, 'hv':self.vivn, 'orv':self.porv, 'bts':self.pbtp}
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def ebbtit(self):
        try:
            if '' == self.btps.strip() or '' == self.brdr.strip():
                msg = 'A Set-top-Box típusát és a használt rendszer (image) nevét egyszer meg kell adni!\n\nA kompatibilitás és a megfelelő használat miatt kellenek ezek az adatok a programnak.\nKérlek, a helyes működéshez a valóságnak megfelelően írd be azokat.\n\nA "HU Telepítő" keretrendszerben tudod ezt megtenni.\n\nKilépek és megyek azt beállítani?'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                return False
            else:
                return True
        except Exception:
            return False
    
    def gits(self):
        bv = '-'
        tt = []
        try:
            if fileExists(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE'))):
                fr = open(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE')),'r')
                for ln in fr:
                    ln = ln.rstrip('\n')
                    if ln != '':
                        tt.append(ln)
                fr.close()
                if len(tt) == 1:
                    bv = tt[0].strip()[:-6].capitalize()
                if len(tt) == 2:
                    bv = tt[1].strip()[:-6].capitalize()
            return bv
        except:
            return '-'
            
    def malvadkrttmk(self, i_md='', i_hgk=''):
        bv = []
        ukszrz = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_md != '' and i_hgk != '':
                i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk}
                sts, data = self.cm.getPage(ukszrz, self.defaultParams, pstd)
                if not sts: return []
                if len(data) == 0: return []
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div>', '</div>', False)
                if len(data) == 0: return []
                for item in data:
                    if item != '':
                        bv.append(base64.b64decode(item))
            return bv
        except Exception:
            return []
    
    def tryTologin(self):
        rm(self.COOKIE_FILE)
        self.login = config.plugins.iptvplayer.filmezzeu_login.value
        self.password = config.plugins.iptvplayer.filmezzeu_password.value
        if '' == self.login.strip() or '' == self.password.strip():
            #self.sessionEx.open(MessageBox, _('The host %s requires registration. \nPlease fill your login and password in the host configuration. Available under blue button.' % self.getMainUrl()), type = MessageBox.TYPE_ERROR, timeout = 10 )
            return False
        url = self.getFullUrl('/bejelentkezes.php')
        post_data = {'logname':self.login, 'logpass':self.password, 'ref':self.getFullUrl('/index.php')}
        httpParams = dict(self.defaultParams)
        httpParams['header'] = dict(httpParams['header'])
        httpParams['header']['Referer'] = url
        sts, data = self.cm.getPage(url, httpParams, post_data)
        if sts and 'kijelentkezes.php' in data:
            printDBG('tryTologin OK')
            return True
        self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
        return False
        
    def Vdakstmk(self, baseItem={'name': 'history', 'category': 'search'}, desc_key='plot', desc_base=(_("Type: ")), tabID='' ):
        if tabID != '':
            self.susn('2', '2', tabID)
            
        def _vdakstmk(data,lnp=50):
            ln = 0
            for histItem in data:
                plot = ''
                try:
                    ln += 1
                    if type(histItem) == type({}):
                        pattern = histItem.get('pattern', '')
                        search_type = histItem.get('type', '')
                        if '' != search_type: plot = desc_base + _(search_type)
                    else:
                        pattern = histItem
                        search_type = None
                    params = dict(baseItem)
                    params.update({'title': pattern, 'search_type': search_type,  desc_key: plot, 'tps':'0'})
                    self.addDir(params)
                    if ln >= lnp:
                        break
                except Exception:
                    return
            
        try:
            list = self.malvadkrttmk('1','2')
            if len(list) > 0:
                _vdakstmk(list,2)
            if len(list) > 0:
                list = list[2:]
                random.shuffle(list)
                _vdakstmk(list,48)
        except Exception:
            return
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.filmezzeu_login.value or\
            self.password != config.plugins.iptvplayer.filmezzeu_password.value:
            self.loggedIn = self.tryTologin()
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )        
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
        elif category == 'list_main':
            self.listMainItems(self.currItem)
        elif category == 'list_third':
            self.listThirdItems(self.currItem)
        elif category in ["search", "search_next_page"]:
            if self.currItem['tab_id'] == 'filmezz_kereses':
                self.susn('2', '2', 'filmezz_kereses')
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            if self.currItem['tab_id'] == 'filmezz_kereses_elozmeny':
                self.susn('2', '2', 'filmezz_kereses_elozmeny')
            self.listsHistory({'name':'history', 'category': 'search', 'tab_id':'', 'tps':'0'}, 'desc', _("Type: "))
        else:
            return
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, FilmezzEU(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] != 'explore_item'):
            return False
        return True
    
    