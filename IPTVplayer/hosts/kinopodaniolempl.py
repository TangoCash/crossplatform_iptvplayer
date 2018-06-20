# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, GetDefaultLang, WriteTextFile, ReadTextFile
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
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
from datetime import datetime
from hashlib import md5
from copy import deepcopy
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
config.plugins.iptvplayer.kinopodaniolempl_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.kinopodaniolempl_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":",    config.plugins.iptvplayer.kinopodaniolempl_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.kinopodaniolempl_password))
    return optionList
###################################################

def gettytul():
    return 'http://kinopodaniolem.pl/'

class KinoPodAniolemPL(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'kinopodaniolem.pl', 'cookie':'kinopodaniolem.pl.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://kinopodaniolem.pl/Content/gloria-dark/images/kino-pod-aniolem__logo_n.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'http://kinopodaniolem.pl/'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.cacheLinks  = []
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'list_categories',   'title': 'Repertuar', 'url':self.getFullUrl('/filmy')},
                             
                             {'category':'search',            'title': _('Search'),          'search_item':True}, 
                             {'category':'search_history',    'title': _('Search history')},
                            ]
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        self.konto = ''
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def getFullUrl(self, url):
        url = CBaseHostClass.getFullUrl(self, url)
        return url.replace('&amp;', '&')
        
    def listMainMenu(self, cItem, nextCategory):
        printDBG("KinoPodAniolemPL.listMainMenu")
        if self.loggedIn:
            params = dict(cItem)
            params.update({'category':'list_user_movies', 'title':self.konto, 'url':self.getFullUrl('/konto')})
            self.addDir(params)
        
        self.listsTab(self.MAIN_CAT_TAB, cItem)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("KinoPodAniolemPL.listCategories [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'catalog-filter__list'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
        
    def listSort(self, cItem, nextCategory):
        printDBG("KinoPodAniolemPL.listSort [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'sort-list'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def _listItems(self, cItem, nextCategory, data):
        printDBG("KinoPodAniolemPL._listItems")
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<article', '>', 'movie-box'), ('</article', '>'))
        for item in data:
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h1', '</h1>')[1])
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            price    = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<a', '>', 'btn--buy'), ('</a', '>'))[1])
            duration = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'duration'), ('</span', '>'))[1])
            release  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'release'), ('</span', '>'))[1])
            publish  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'publish'), ('</span', '>'))[1])
            categories = []
            tmp = self.cm.ph.getAllItemsBeetwenNodes(item, ('<span', '>', 'categories'), ('</span', '>'))
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': categories.append(t)
            categories = ', '.join(categories)
            desc = []
            for t in [release, duration, publish, categories, price]:
                if t != '': desc.append(t)
            desc = ' | '.join(desc) + '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'description'), ('</div', '>'))[1])
            otherInfo = {'i_title':title, 'i_price':price, 'i_duration':duration, 'i_release':release, 'i_publish':publish, 'i_categories':categories}
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc, 'other_info':otherInfo})
            self.addDir(params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("KinoPodAniolemPL.listItems [%s]" % cItem)
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<li', '>', 'next'), ('</li', '>'))[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0])
        
        self._listItems(cItem, nextCategory, data)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'url':nextPage, 'page':page+1})
            self.addDir(params)
    
    def listUserMovies(self, cItem, nextCategory):
        printDBG("KinoPodAniolemPL.listUserMovies [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = re.compile('''<section[^>]+?usermovieslist[^>]+?>''').split(data)
        if len(data): del data[0]
        for item in data:
            sectionTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<h2', '>', 'section__title'), ('</h2', '>'))[1])
            self.addMarker({'title':sectionTitle})
            self._listItems(cItem, nextCategory, item)
        
    def exploreItem(self, cItem):
        printDBG("KinoPodAniolemPL.exploreItem")
        
        self.cacheLinks = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        if 'player-trailer' in data: trailer = True
        else: trailer = False
        
        hlsTab  = []
        dashTab = []
        mp4Tab  = []
        
        getDirectM3U8Playlist, getMPDLinksWithMeta
        
        data = self.cm.ph.getSearchGroups(data, '''data\-opts=[']([^']+?)[']''')[0]
        try:
            data = byteify(json.loads(data), '', True)
            for playlist in data['playlist']:
                for item in playlist['sources']:
                    vidUrl = item['file']
                    format = vidUrl.split('?', 1)[0].split('.')[-1].lower()
                    if format == 'm3u8': hlsTab.extend(getDirectM3U8Playlist(vidUrl, checkExt=False, checkContent=True, cookieParams=self.defaultParams, sortWithMaxBitrate=999999999))
                    elif format == 'mpd': dashTab.extend(getMPDLinksWithMeta(vidUrl, checkExt=False, cookieParams=self.defaultParams, sortWithMaxBandwidth=999999999))
                    elif format == 'mp4':   mp4Tab.append({'name':'mp4', 'url':vidUrl})
        except Exception:
            printExc()
        
        self.cacheLinks.extend(hlsTab)
        self.cacheLinks.extend(dashTab)
        self.cacheLinks.extend(mp4Tab)
        
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        for idx in range(len(self.cacheLinks)):
            self.cacheLinks[idx]['url'] = strwithmeta(self.cacheLinks[idx]['url'], {'User-Agent':self.USER_AGENT, 'Referer':cItem['url'], 'Cookie':cookieHeader})
        
        if len(self.cacheLinks):
            title = cItem['title']
            if trailer:
                title += ' - ' + _('TRAILER')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':title})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KinoPodAniolemPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        page = cItem.get('page', 1)
        if page == 1:
            cItem = dict(cItem)
            cItem['url'] = self.getFullUrl('/filmy?Filter.Query=') + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("KinoPodAniolemPL.getLinksForVideo [%s]" % cItem)
        
        self.tryTologin()
        return self.cacheLinks
    
    def getArticleContent(self, cItem):
        printDBG("KinoPodAniolemPL.getArticleContent [%s]" % cItem)
        
        self.tryTologin()
        
        infoObj = cItem.get('other_info', {})
        
        otherInfo = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        title = infoObj.get('i_title', '')
        desc = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'movie-meta__description'), ('</section', '>'))[1]
        desc = re.compile('''<[/\s]*br[/\s]*>''').sub('[/br]', desc)
        desc = self.cleanHtmlStr(desc)
        icon  = cItem.get('icon', '')
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<span', '>', 'meta__duration'), ('</span', '>'))[1])
        if tmp == '': tmp = infoObj.get('i_duration', '')
        if tmp != '': otherInfo['duration'] =  tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<span', '>', 'meta__year'), ('</span', '>'))[1])
        if tmp == '': tmp = infoObj.get('i_release', '')
        if tmp != '': otherInfo['released'] =  tmp
        
        tmp = infoObj.get('i_price', '')
        if tmp != '': otherInfo['price'] =  tmp
        
        categories = []
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<', '>', 'elem-gatunek'), ('</ul', '>'), False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': categories.append(t)
        tmp = ', '.join(categories)
        if tmp == '': tmp = infoObj.get('i_categories', '')
        if tmp != '': otherInfo['genres'] =  tmp
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def tryTologin(self):
        printDBG('KinoPodAniolemPL.tryTologin start')
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.kinopodaniolempl_login.value or\
            self.password != config.plugins.iptvplayer.kinopodaniolempl_password.value:
        
            self.login = config.plugins.iptvplayer.kinopodaniolempl_login.value
            self.password = config.plugins.iptvplayer.kinopodaniolempl_password.value
            
            rm(self.COOKIE_FILE)
            
            self.loggedIn = False
            
            if '' == self.login.strip() or '' == self.password.strip():
                return False
            
            sts, data = self.getPage(self.getFullUrl('/logowanie'))
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'logowanie'), ('</form', '>'))
            if not sts: return False
            actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
            tmp.extend(self.cm.ph.getAllItemsBeetwenMarkers(data, '<button', '>'))
            post_data = {}
            for item in tmp:
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                post_data[name] = value
            
            post_data.update({'Login':self.login, 'Password':self.password})
            
            httpParams = dict(self.defaultParams)
            httpParams['header'] = dict(httpParams['header'])
            httpParams['header']['Referer'] = self.getMainUrl()
            sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
            if sts and '/Logout' in data:
                printDBG('tryTologin OK')
                self.loggedIn = True
                self.konto = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', '/konto'), ('</a', '>'))[1])
            else:
                errorMsg = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'errorList'), ('</ul', '>'))[1])
                self.sessionEx.open(MessageBox, _('Login failed.') + '\n' + errorMsg, type = MessageBox.TYPE_ERROR, timeout = 10)
                printDBG('tryTologin failed')
        return self.loggedIn
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'}, 'list_genres')
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_sort')
        elif category == 'list_sort':
            self.listSort(self.currItem, 'list_items')
        elif category == 'list_user_movies':
            self.listUserMovies(self.currItem, 'explore_item')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
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
        CHostBase.__init__(self, KinoPodAniolemPL(), True, [])
        
    def withArticleContent(self, cItem):
        if  cItem.get('good_for_fav', False) or 'explore_item' == cItem.get('category', ''):
            return True
        return False
        
    