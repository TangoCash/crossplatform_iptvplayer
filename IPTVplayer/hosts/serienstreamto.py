# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
import urllib2
import string
import base64
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
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.serienstreamto_langpreference = ConfigSelection(default = "de,de_sub,en", choices = [("de,de_sub,en", "de,sub,en"), \
                                                                                                               ("de,en,de_sub", "de,en,sub"), \
                                                                                                               ("de_sub,de,en", "sub,de,en"), \
                                                                                                               ("de_sub,en,de", "sub,en,de"), \
                                                                                                               ("en,de_sub,de", "en,sub,de"), \
                                                                                                               ("en,de,de_sub", "en,de,sub")]) 
config.plugins.iptvplayer.serienstreamto_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.serienstreamto_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( _("Your language preference:"), config.plugins.iptvplayer.serienstreamto_langpreference ) )
    
    optionList.append(getConfigListEntry(_("e-mail")+":", config.plugins.iptvplayer.serienstreamto_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.serienstreamto_password))
    return optionList
###################################################

def gettytul():
    return 'https://serienstream.to/'

class SerienStreamTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SerienStreamTo.tv', 'cookie':'serienstreamto.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        self.HEADER = {'User-Agent':self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'https://serienstream.to/'
        self.DEFAULT_ICON_URL = 'https://serienstream.to/public/img/facebook.jpg'
        
        self.MAIN_CAT_TAB = [{'category':'list_abc',          'title': _('A-Z'),                          'url':self.MAIN_URL                       },
                             {'category':'list_genres',       'title': _('Genres'),                       'url':self.MAIN_URL                       },
                             {'category':'list_items',        'title': _('New'),                          'url':self.getFullUrl('/neu')             },
                             {'category':'list_items',        'title': _('Popular'),                      'url':self.getFullUrl('/beliebte-serien') },
                             {'category':'search',            'title': _('Search'),                       'search_item':True,                       },
                             {'category':'search_history',    'title': _('Search history'),                                                         } 
                            ]
        
        self.cacheLinks = {}
        self.cacheFilters = {}
        self.cookieHeader = ''
        self.login = ''
        self.password = ''
        self.loggedIn = None
        
    def getPage(self, baseUrl, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        params['cloudflare_params'] = {'domain':self.up.getDomain(self.MAIN_URL), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':self.getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)
       
    def refreshCookieHeader(self):
        self.cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        
    def getIconUrl(self, url, refreshCookieHeader=True):
        url = self.getFullUrl(url)
        if url == '': return ''
        if refreshCookieHeader: self.refreshCookieHeader()
        return strwithmeta(url, {'Cookie':self.cookieHeader, 'User-Agent':self.USER_AGENT})
    
    def fillFilters(self, url):
        printDBG("SerienStreamTo.listABC")
        
        self.cacheFilters = {'abc':[], 'genres':[]}
        
        sts, data = self.getPage(url)
        if not sts: return
        
        for filter in [('abc', '<ul class="catalogNav"', '<li class="'), ('genres', '<ul class="homeContentGenresList"', '</ul>')]:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, filter[1], filter[2], withMarkers=False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>', withMarkers=True)
            for item in tmp:
                url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title  = self.cleanHtmlStr(item)
                if title == '': title  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
                params = {'good_for_fav': True, 'title':title, 'url':url}
                self.cacheFilters[filter[0]].append(params)
        
    def listFilter(self, cItem, nextCategory, filter):
        printDBG("SerienStreamTo.listFilter")
        
        tab = self.cacheFilters.get(filter, [])
        
        if 0 == len(tab):
            self.fillFilters(cItem['url'])
            tab = self.cacheFilters.get(filter, [])
        
        params = dict(cItem)
        params['category'] = nextCategory
        self.listsTab(tab, params)
    
    def listItems(self, cItem, nextCategory):
        printDBG("SerienStreamTo.listItems")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="seriesListContainer', '<div class="cf">', withMarkers=True)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', withMarkers=False)[1])
            if title == '': title  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            desc   = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
            
    def listSeasons(self, cItem, nextCategory):
        printDBG("SerienStreamTo.listSeasons")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tmp  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="seriesContentBox"', '<div class="series-add')[1]
        icon = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''src=['"]([^'^"]+?)['"]''')[0])
        if '' == icon: icon = cItem.get('series_title', '')
        desc = self.cleanHtmlStr(self.cm.ph.getSearchGroups(tmp, '''description=['"]([^'^"]+?)['"]''')[0])
        
        trailerUrl = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''href=['"]([^'^"]+?)['"][^>]+?itemprop=['"]trailer['"]''')[0])
        if self.cm.isValidUrl(trailerUrl):
            params = {'good_for_fav':True, 'title':_('Trailer'), 'url':trailerUrl, 'icon':icon, 'desc':desc}
            self.addVideo(params)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Staffeln:', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(item)
            try:
                seasonNum = str(int(title))
                title  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            except Exception:
                seasonNum = ''
            params = dict(cItem)
            params.update({'category':nextCategory, 'good_for_fav':True, 'season_num':seasonNum, 'series_title':cItem['title'], 'title':cItem['title'] + ': ' + title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("SerienStreamTo.listEpisodes")
        
        seasonNum   = cItem.get('season_num', '')
        seriesTitle = cItem.get('series_title', '')
        cItem = dict(cItem)
        cItem.pop('season_num', None)
        cItem.pop('series_title', None)
        
        #seriesTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="series-title">', '<div', withMarkers=False)[1])
        #if seriesTitle == '': seriesTitle = cItem.get('series_title', '')
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody ', '</tbody>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr ', '</tr>')
        for item in data:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td ', '</td>')
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            title  = self.cleanHtmlStr(tmp[1])
            try: episodeNum = str(int(self.cm.ph.getSearchGroups(item, '''episode\-([0-9]+?)[^0-9]''')[0]))
            except Exception: episodeNum = ''
            if '' != episodeNum and '' != seasonNum: title = 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2)) + ' - ' + title
            
            langs = re.compile('/public/img/([a-z]+?)\.png').findall(item)
            desc = '[{0}]'.format(' | '.join(langs)) + '[/br]' + cItem.get('desc', '')
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':'{0}: {1}'.format(seriesTitle, title), 'url':url, 'desc':desc})
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SerienStreamTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        baseUrl = self.getFullUrl('ajax/search')
        post_data = {'keyword':searchPattern}
        sts, data = self.getPage(baseUrl, {}, post_data)
        if not sts: return
        
        printDBG(data)

        try:
            data = byteify(json.loads(data))
            for item in data:
                title = self.cleanHtmlStr(item['title'])
                desc  = self.cleanHtmlStr(item['description'])
                url   = self.getFullUrl(item['link'])
                params = {'name':'category', 'category':'list_seasons', 'good_for_fav':True, 'title':title, 'url':url, 'desc':desc}
                self.addDir(params)
        except Exception:
            printExc()
    
    def getLinksForVideo(self, cItem):
        printDBG("SerienStreamTo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        # 1 - de, 2 - en, 3 - de_sub
        langPreference = config.plugins.iptvplayer.serienstreamto_langpreference.value.replace('de_sub', '3').replace('de', '1').replace('en', '2').split(',')
        printDBG(langPreference)
        def compare(itemX, itemY):
            x = itemX['lang_id']
            if x in langPreference: x = len(langPreference) - langPreference.index(x)
            else: x = 0
            y = itemY['lang_id']
            if y in langPreference: y = len(langPreference) - langPreference.index(y)
            else: y = 0
            return int(y) - int(x)
        
        if self.up.getDomain(self.MAIN_URL) in cItem['url']:
            if len(self.cacheLinks.get(cItem['url'], [])):
                urlTab = self.cacheLinks[cItem['url']]
            else:
                sts, data = self.getPage(cItem['url'])
                if not sts: return []
                # fill data lang map
                langMap = {}
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="changeLanguageBox"', '</div>')[1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<img ', '>')
                for item in tmp:
                    key   = self.cm.ph.getSearchGroups(item, '''data-lang-key=['"]([^'^"]+?)['"]''')[0]
                    title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0] #self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].split('/')[-1].repace('.png', '')
                    langMap[key] = title
                    
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="changeLanguageBox"', '</ul>')[1]
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
                for item in data:
                    langId = self.cm.ph.getSearchGroups(item, '''data-lang-key=['"]([^'^"]+?)['"]''')[0]
                    title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h4>', '</h4>', withMarkers=False)[1])
                    url    = strwithmeta(self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]), {'base_url':cItem['url']})
                    urlTab.append({'name': '[{0}] {1}'.format(langMap.get(langId, _('Unknown')), title), 'lang_id':langId, 'url':url, 'need_resolve':1})
                
                if len(urlTab):
                    self.cacheLinks[cItem['url']] = urlTab
                
            urlTab = sorted(urlTab, cmp=compare)
        else:
            urlTab = self.up.getVideoLinkExt(cItem['url'])
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("SerienStreamTo.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        videoUrl = strwithmeta(videoUrl)
        key = videoUrl.meta.get('base_url', '')
        if key != '' and key in self.cacheLinks:
            for idx in range(len(self.cacheLinks[key])):
                if self.cacheLinks[key][idx]['url'] == videoUrl:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'): 
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
        
        if self.cm.isValidUrl(videoUrl):
            if 1 != self.up.checkHostSupport(videoUrl):
                params = dict(self.defaultParams)
                try:
                    params['return_data'] = False
                    params['no_redirection'] = True
                    tries = 0
                    tmpUrl = videoUrl
                    while tries < 3:
                        sts, response = self.getPage(videoUrl, params)
                        printDBG("+++++++++++")
                        printDBG(response.info())
                        printDBG("+++++++++++")
                        url = ''
                        for key in response.info():
                            if key.upper() == 'LOCATION':
                                url = response.info()[key]
                        response.close()
                        if not self.cm.isValidUrl(url):
                            break
                        videoUrl = url
                        tries += 1
                except Exception:
                    printExc()
            
            if 1 != self.up.checkHostSupport(videoUrl):
                sts, data = self.getPage(videoUrl)
                if sts and 'google.com/recaptcha/' in data and 'sitekey' in data:
                    message = _('Link protected with google recaptcha v2.')
                    if True != self.loggedIn:
                        message += '\n' + _('Please fill your login and password in the host configuration (available under blue button) and try again.')
                    else:
                        message += '\n' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<small', '</small>')[1])
                        message += '\n' + _('Please retry later.')
                    SetIPTVPlayerLastHostError(message)
            
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def tryTologin(self):
        printDBG('tryTologin start')
        
        if self.login == config.plugins.iptvplayer.serienstreamto_login.value and \
           self.password == config.plugins.iptvplayer.serienstreamto_password.value:
           return 
        
        self.cm.clearCookie(self.COOKIE_FILE, ['__cfduid', 'cf_clearance'])
        self.login = config.plugins.iptvplayer.serienstreamto_login.value
        self.password = config.plugins.iptvplayer.serienstreamto_password.value
        
        if '' == self.login.strip() or '' == self.password.strip():
            printDBG('tryTologin wrong login data')
            self.loggedIn = None
            return
            
        url = self.getFullUrl('/login')
        
        post_data = {'email':self.login, 'password':self.password, 'autoLogin':'on'}

        httpParams = dict(self.defaultParams)
        httpParams['header'] = dict(httpParams['header'])
        httpParams['header']['Referer'] = url
        sts, data = self.getPage(url, httpParams, post_data)
        printDBG(data)
        sts, data = self.getPage(url)
        if sts and '/home/logout' in data:
            printDBG('tryTologin OK')
            self.loggedIn = True
            return
     
        self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
        printDBG('tryTologin failed')
        self.loggedIn = False
        return
        
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
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif 'list_abc' == category:
            self.listFilter(self.currItem, 'list_items', 'abc')
        elif 'list_genres' == category:
            self.listFilter(self.currItem, 'list_items', 'genres')
        elif 'list_items' == category:
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
        CHostBase.__init__(self, SerienStreamTo(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]

