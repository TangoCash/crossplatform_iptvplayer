# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import base64
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from datetime import datetime
from copy import deepcopy
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

config.plugins.iptvplayer.naszekino_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.naszekino_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Login:", config.plugins.iptvplayer.naszekino_login))
    optionList.append(getConfigListEntry("Hasło:", config.plugins.iptvplayer.naszekino_password))
    return optionList
###################################################


def gettytul():
    return 'http://nasze-kino.online/'

class NaszeKinoOnline(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'NaszeKinoOnline.tv', 'cookie':'naszekinoonline.cookie'})
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.defaultParams = {'header': self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL = 'http://nasze-kino.online/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'images/robored/misc/logo.png'
        
        self.MAIN_CAT_TAB = [{'category':'search',            'title': _('Search'), 'search_item':True,         'icon':self.DEFAULT_ICON_URL},
                             {'category':'search_history',    'title': _('Search history'),                     'icon':self.DEFAULT_ICON_URL}]
        self.login    = ''
        self.password = ''
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.cacheSeries = {}
        
    def getStr(self, item, key):
        if key not in item: return ''
        if item[key] == None: return ''
        return str(item[key])
    
    def fillFilters(self, cItem):
        self.cacheFilters = {}
        sts, data = self.cm.getPage(self.getFullUrl('forumdisplay.php/57-Filmy-Online')) # it seems that all sub-forums have same filters
        if not sts: return
        
        def addFilter(data, key, addAny, titleBase):
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                self.cacheFilters[key].append({'title':titleBase + title, key:value})
            if addAny and len(self.cacheFilters[key]):
                self.cacheFilters[key].insert(0, {'title':'Wszystkie'})
                
        # daysprune
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'name="daysprune"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        tmpData.reverse()
        addFilter(tmpData, 'daysprune', False, '')
        
        # prefixid
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'name="prefixid"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'prefixid', False, '')
        
        # sort
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, 'name="sort"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'sort', False, '')
        
        # add order to sort filter
        orderLen = len(self.cacheFilters['sort'])
        for idx in range(orderLen):
            item = deepcopy(self.cacheFilters['sort'][idx])
            # desc
            self.cacheFilters['sort'][idx].update({'title':'\xe2\x86\x93 ' + self.cacheFilters['sort'][idx]['title'], 'order':'desc'})
            # asc
            item.update({'title': '\xe2\x86\x91 ' + item['title'], 'order':'asc'})
            self.cacheFilters['sort'].append(item)
        
    def listFilter(self, cItem, filters):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        
        if idx == 0:
            self.fillFilters(cItem)
        
        tab = self.cacheFilters.get(filters[idx], [])
        self.listsTab(tab, params)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("NaszeKinoOnline.listCategories")
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<table class="vbs_forumrow table">', '</table>', withMarkers=True)
        for item in data:
            tmp    = self.cm.ph.getDataBeetwenMarkers(item, '<h2 ', '</h2>')[1]
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''href=['"]([^'^"]+?)['"]''')[0])
            if 'Powitalnia' in url:
                break
            
            if 'forum_link-48.png' in item:
                category = 'list_threads2'
            else: category = nextCategory
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''src=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(tmp)
            desc   = self.cleanHtmlStr(item.replace('</td>', '[/br]').replace('<br />', '[/br]'))
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
    
    def listThreads(self, cItem, nextCategory):
        printDBG("NaszeKinoOnline.listThreads")
        perPage = 30
        page = cItem.get('page', 1)
        
        baseUrl = cItem['url']
        if page > 1: baseUrl += '/page{0}'.format(page)
        baseUrl += '?s=&pp={0}&'.format(perPage)
        
        if 'daysprune' in cItem:
            baseUrl += 'daysprune={0}&'.format(cItem['daysprune'])
        
        if 'prefixid' in cItem:
            baseUrl += 'prefixid={0}&'.format(cItem['prefixid'])
            
        if 'sort' in cItem:
            baseUrl += 'sort={0}&'.format(cItem['sort'])
        
        if 'order' in cItem:
            baseUrl += 'order={0}&'.format(cItem['order'])
        
        sts, data = self.cm.getPage(baseUrl, self.defaultParams)
        if not sts: return
        
        if None != re.search('<a[^>]+rel="next"', data):
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<table class="vbs_forumrow threadbit', '</table>', withMarkers=True)
        for item in data:
            item = '<table ' + item
            if page > 1 and 'sticky.gif' in item: continue
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''<img\s*class="preview"\s*src=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            desc   = self.cleanHtmlStr(item.replace('</td>', '[/br]').replace('<br />', '[/br]'))
            params = dict(cItem)
            params.update({'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page + 1})
            self.addDir(params)
    
    def listThreads2(self, cItem, nextCategory):
        printDBG("NaszeKinoOnline.listThreads2")
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="blockrow"', '</div>', withMarkers=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            params = dict(cItem)
            params.update({'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon})
            self.addDir(params)
        
    def listPosts(self, cItem):
        printDBG("NaszeKinoOnline.listPosts")
        
        page = cItem.get('page', 1)
        
        baseUrl = cItem['url']
        if page > 1: baseUrl += '/page{0}'.format(page)
        
        sts, data = self.cm.getPage(baseUrl, self.defaultParams)
        if not sts: return
       
        if None != re.search('<a[^>]+rel="next"', data):
            nextPage = True
        else: nextPage = False
        
        allLinks = []
        ret = {'names':[], 'links':{}}
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="bbcode_quote_container"></div>', '</div>', withMarkers=False)[1].replace('<br />', '[/br]'))       
        mainIcon = self.cm.ph.getDataBeetwenMarkers(data, '<meta name="description"', '>')[1]
        printDBG('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
        printDBG(mainIcon)
        printDBG('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
        mainIcon = self.cm.ph.getSearchGroups(mainIcon, '''(https?://[^\s^"^'^<^>^:]+\.(?:jpg|png|jpeg))''')[0]
        
        tmpTab0 = self.cm.ph.getAllItemsBeetwenMarkers(data, '<blockquote', '</blockquote>', withMarkers=True, caseSensitive=False)
        for tmpItem0 in tmpTab0:
            tmpTab = tmpItem0.split('<font size="4">')
            for tmpItem in tmpTab:
                tmpItem = '<font size="4">' + tmpItem
                linksName = self.cleanHtmlStr( self.cm.ph.rgetDataBeetwenMarkers(tmpItem, '<font', '</font>',  withMarkers=True)[1] )
                linksTab  = self.cm.ph.getAllItemsBeetwenMarkers(tmpItem, '<a', '</a>', withMarkers=True, caseSensitive=False) 
                newLinksTab = []
                for item in linksTab:
                    link     = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    linkNameBase = self.cleanHtmlStr(item)
                    
                    if link in allLinks: continue
                    if 'facebook' in link: continue
                    if 1 != self.up.checkHostSupport(link): continue
                    url  = link
                    name = self.up.getHostName(url, True)
                    if name != self.up.getHostName(linkNameBase, True):
                        name = linkNameBase + ' ' + name
                    
                    if linksName not in ret['names']:
                        ret['names'].append(linksName)
                        ret['links'][linksName] = []
                    newLinksTab.append({'name':name, 'url':url})
                    allLinks.append(url)
                if len(newLinksTab):
                    ret['links'][linksName] = newLinksTab + ret['links'][linksName]
        
        mainTitle = cItem.get('main_title', cItem['title'])
        params = dict(cItem)
        if desc != '': params['desc'] = desc
        
        if '' == params.get('icon', ''):
            params['icon'] = mainIcon
        
        sNum = self.cm.ph.getSearchGroups(baseUrl.lower() + '|', '''sezon-([0-9]+?)[^0-9]''')[0]
        for item in ret['names']:
            title = item
            if sNum != '':
                eNum = self.cm.ph.getSearchGroups(title + '|', '''[^0-9]([0-9]+?)[^0-9]''')[0]
                title = mainTitle + ': s%se%s ' % (sNum.zfill(2), eNum.zfill(2)) + self.cleanHtmlStr( title )
            elif 'opis' not in title.lower():
                title = mainTitle + ' ' + title
            else:
                title = mainTitle
            params = dict(params)
            params.update({'good_for_fav': False, 'title':title, 'url':item, 'urls':ret['links'][item]})
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_('Next page'), 'main_title':mainTitle, 'page':page + 1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("NaszeKinoOnline.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        params = dict(self.defaultParams)
        params.update({'return_data':False})
        
        baseUrl = self.getFullUrl('search.php?do=process')
        post_data = {'do':'process', 'query': searchPattern, 'titleonly':'1'}
        sts, response = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return
        try:
            newUrl = response.geturl()
            response.close()
        except Exception:
            printExc()
            return
        
        sts, data = self.cm.getPage(newUrl, self.defaultParams)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ol id="searchbits"', '</ol>', withMarkers=False)[1]
        data = data.split('<li class="imodselector')
        if len(data): del data[0]
        for item in data:
            item = '<li ' + item
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0].split('?')[0])
            if not self.cm.isValidUrl(url): continue
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''<img\s*class="preview"\s*src=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            desc   = self.cleanHtmlStr(item.replace('</td>', '[/br]').replace('<br />', '[/br]'))
            params = dict(cItem)
            params.update({'good_for_fav': True, 'category':'list_posts', 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("NaszeKinoOnline.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        urlTab = cItem.get('urls', [])
        for idx in range(len(urlTab)):
            urlTab[idx]['need_resolve'] = 1
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("NaszeKinoOnline.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            key = self.cacheLinks.keys()[0]
            for idx in range(len(self.cacheLinks[key])):
                if videoUrl in self.cacheLinks[key][idx]['url']:
                    if not self.cacheLinks[key][idx]['name'].startswith('*'):
                        self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                    break
        
        if self.cm.isValidUrl(videoUrl):
            return self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        printDBG('NaszeKinoOnline.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('NaszeKinoOnline.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('NaszeKinoOnline.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def tryTologin(self, login, password):
        printDBG('tryTologin start')
        connFailed = _('Connection to server failed!')
        
        rm(self.COOKIE_FILE)
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return False, connFailed 
        
        md5Password = md5(password).hexdigest()
        post_data = {"vb_login_username":login, "vb_login_password_hint":"Hasło", "vb_login_password":"", "do":"login", "s":"", "securitytoken":"guest", "cookieuser":"1", "vb_login_md5password":md5Password, "vb_login_md5password_utf8":md5Password}
        params = dict(self.defaultParams)
        params.update({'header':self.AJAX_HEADER}) #, 'raw_post_data':True
        
        # login
        sts, data = self.cm.getPage(self.getFullUrl('login.php?s=&do=login'), params, post_data)
        if not sts: return False, connFailed
        
        # check if logged
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return False, connFailed 
        
        if 'do=logout' in data:
            return True, 'OK'
        else:
            return False, 'NOT OK'
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if self.login != config.plugins.iptvplayer.naszekino_login.value and \
           self.password != config.plugins.iptvplayer.naszekino_password.value and \
           '' != config.plugins.iptvplayer.naszekino_login.value.strip() and \
           '' != config.plugins.iptvplayer.naszekino_password.value.strip():
            loggedIn, msg = self.tryTologin(config.plugins.iptvplayer.naszekino_login.value, config.plugins.iptvplayer.naszekino_password.value)
            if not loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % config.plugins.iptvplayer.naszekino_login.value, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.login    = config.plugins.iptvplayer.naszekino_login.value
                self.password = config.plugins.iptvplayer.naszekino_password.value
                #self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.\n' + msg, type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listCategories({'name':'category'}, 'list_threads')
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif 'list_threads' == category:
            filtersTab = ['daysprune', 'prefixid', 'sort']
            idx = self.currItem.get('f_idx', 0)
            if idx < len(filtersTab):
                self.listFilter(self.currItem, filtersTab)
            else:
                self.listThreads(self.currItem, 'list_posts')
        elif 'list_threads2' == category:
            self.listThreads2(self.currItem, 'list_posts')
        elif category == 'list_posts':
            self.listPosts(self.currItem)
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
        CHostBase.__init__(self, NaszeKinoOnline(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item.get('need_resolve', False)))

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
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "series"))
        
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
        if icon == '':  icon = self.host.DEFAULT_ICON_URL
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

