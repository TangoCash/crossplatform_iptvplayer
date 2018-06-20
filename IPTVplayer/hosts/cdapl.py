# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify, rm
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json


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
config.plugins.iptvplayer.cda_searchsort = ConfigSelection(default = "best", choices = [("best", _("Najtrafniejsze")), ("date", _("Najnowsze")), ("rate", _("Najlepiej oceniane")), ("alf", _("Alfabetycznie"))])
config.plugins.iptvplayer.cda_login      = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.cda_password   = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Login:", config.plugins.iptvplayer.cda_login))
    optionList.append(getConfigListEntry("Hasło:", config.plugins.iptvplayer.cda_password))
    optionList.append( getConfigListEntry( _("Sortuj wyniki wyszukiwania po:"), config.plugins.iptvplayer.cda_searchsort ) )
    return optionList
###################################################

def gettytul():
    return 'https://cda.pl/'

class cda(CBaseHostClass):
    
    def __init__(self):
        printDBG("cda.__init__")
        CBaseHostClass.__init__(self, {'history':'cda.pl', 'cookie':'cdapl.cookie'})
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.defaultParams = {'header': self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.MAIN_URL = 'https://www.cda.pl/'
        self.SEARCH_URL = self.getFullUrl('video/show/%s/p%d?s=%s')
        self.DEFAULT_ICON_URL = 'http://www.download.net.pl/upload/NewsSeptember2015/CDA-Filmy/cdalogo.jpg'
        
        self.MAIN_TAB = [{'category':'video',             'title': 'Filmy wideo',  'url':''},
                         {'category':'premium',           'title': 'CDA Premium',  'url':self.getFullUrl('premium')},
                         {'category':'channels_cats',     'title': 'Kanały',       'url':''},
                         {'category':'search',            'title': _('Search'), 'search_item':True},
                         {'category':'search_history',    'title': _('Search history')}]
        
        self.VIDEO_TAB = [{'category':'categories',       'title': 'Główna',       'base_url':'video'},
                          {'category':'categories',       'title': 'Poczekalnia',  'base_url':'video/poczekalnia'}]

        self.CATEGORIES_TAB = [{'url' : '',       'category':'category', 'title' : '--Wszystkie--'}, 
                               {'url' : '/kat26', 'category':'category', 'title' : 'Krótkie filmy i animacje'}, 
                               {'url' : '/kat24', 'category':'category', 'title' : 'Filmy Extremalne'}, 
                               {'url' : '/kat27', 'category':'category', 'title' : 'Motoryzacja, wypadki'}, 
                               {'url' : '/kat28', 'category':'category', 'title' : 'Muzyka'}, 
                               {'url' : '/kat29', 'category':'category', 'title' : 'Prosto z Polski'}, 
                               {'url' : '/kat30', 'category':'category', 'title' : 'Rozrywka'}, 
                               {'url' : '/kat31', 'category':'category', 'title' : 'Sport'}, 
                               {'url' : '/kat32', 'category':'category', 'title' : 'Śmieszne filmy'}, 
                               {'url' : '/kat33', 'category':'category', 'title' : 'Różności'}, 
                               {'url' : '/kat34', 'category':'category', 'title' : 'Życie studenckie'} ]
        self.cacheFilters = {}
        self.filtersTab = []
        self.login    = ''
        self.password = ''
    
    # premium filters
    def fillFilters(self, cItem):
        printDBG("cda.fillFilters")
        self.cacheFilters = {}
        self.filtersTab = []
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
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
        
        # premium categories
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<ul class="kat-kino">', '</ul>', withMarkers=True)
        if len(tmp) >= 1:
            self.cacheFilters['premium_cat'] = []
            tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmp[0], '<li', '</li>', withMarkers=True)
            for item in tmpData:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(item)
                self.cacheFilters['premium_cat'].append({'title':title, 'url':url})
        if len(self.cacheFilters.get('premium_cat', [])):
            self.filtersTab.append('premium_cat')
        
        # premium quality
        if len(tmp) >= 2:
            tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmp[1], '<li', '</li>', withMarkers=True)
            tmpData.reverse()
            addFilter(tmpData, 'premium_quality', True, '')
        if len(self.cacheFilters.get('premium_quality', [])):
            self.filtersTab.append('premium_quality')
        
        # premium movie type
        if len(tmp) >= 3:
            tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmp[2], '<li', '</li>', withMarkers=True)
            tmpData.reverse()
            addFilter(tmpData, 'premium_type', True, '')
        if len(self.cacheFilters.get('premium_type', [])):
            self.filtersTab.append('premium_type')
            
        # premium sort
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="s"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'premium_sort', False, '')
        if len(self.cacheFilters.get('premium_sort', [])):
            self.filtersTab.append('premium_sort')
            
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(self.filtersTab)
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
    def listFilter(self, cItem, filters):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        
        tab = self.cacheFilters.get(filters[idx], [])
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(tab)
        printDBG(params)
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        self.listsTab(tab, params)
        
    def listPremiumItems(self, cItem):
        printDBG("cda.listPremiumItems cItem[%s]" % cItem)
        page = cItem.get('page', 1)
        
        baseUrl = cItem['url'] + '?'
        if 'premium_sort' in cItem:
            baseUrl += 'sort={0}&'.format(cItem['premium_sort'])
        if cItem.get('premium_quality', '') != '':
            baseUrl += 'q={0}&'.format(cItem['premium_quality'])
        if cItem.get('premium_type', '') != '':
            baseUrl += 'd={0}&'.format(cItem['premium_type'])
        
        nextPage = False
        nextPageData = {}
        
        if page == 1:
            sts, data = self.cm.getPage(baseUrl, self.defaultParams)
            if not sts: return
            tmp = self.cm.ph.getSearchGroups(data, '''katalogLoadMore\([^\,]+?\,\s*"([^"]+?)"\s*,\s*"([^"]+?)"''', 2)
            nextPageData = {'cat':tmp[0], 'sort':tmp[1]}
            nextPage = True
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="covers-container">', '<div id="loadMore">', False)[1]
        else:
            HEADER = dict(self.AJAX_HEADER)
            HEADER['Referer'] = baseUrl
            params = dict(self.defaultParams)
            params['header'] = HEADER
            nextPageData = cItem.get('next_page_data', {})
            post_data = '{"jsonrpc":"2.0","method":"katalogLoadMore","params":[%s,"%s","%s",{}],"id":%s}' % (page, nextPageData.get('cat', 'all'), nextPageData.get('sort', 'new'), nextPageData.get('id', page-1))
            params['raw_post_data'] = True
            sts, data = self.cm.getPage(self.getFullUrl('premium'), params, post_data)
            if not sts: return
            try:
                data = byteify(json.loads(data))
                if data['result']['status'] == 'continue' and int(data['id']) < page:
                    nextPage = True
                    nextPageData['id'] = data['id']
                data = data['result']['html']
            except Exception:
                printExc()
                return
        
        data = self.cm.ph.rgetAllItemsBeetwenMarkers(data, '</span>', '</style>', withMarkers=True)
        for item in data:
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            desc = self.cleanHtmlStr(item.replace('<br />', '[/br]').replace('</a>', '[/br]'))
            
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
            self.addVideo(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1, 'next_page_data':nextPageData})
            self.addDir(params)
        
    def listCategory(self, cItem):
        printDBG("cda.listCategory cItem[%s]" % cItem)
        page = cItem.get('page', 1)
        url = self.getFullUrl( cItem['base_url'] + cItem['url'] + ('/p%d' % page))
        self.listItems(cItem, url, page)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("cda.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchsort = config.plugins.iptvplayer.cda_searchsort.value
        page = cItem.get('page', 1)
        url  = self.SEARCH_URL % (urllib.quote_plus(searchPattern), page, searchsort)
        tmpItem = dict(cItem)
        tmpItem.update({'category' : 'search_next_page', 'search_pattern':searchPattern})
        self.listItems(tmpItem, url, page, True)
        
    def listItems(self, cItem, url, page, search=False):
        sts, data = self.cm.getPage(url)
        if sts:
            if 'Następna strona' in data:
                nextPage = True
            else:
                nextPage = False
            
            if search:
                data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'video-clip-wrapper'), ('</label', '>'))
            elif 'poczekalnia' in url:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="videoInfo">', '<span class="next-wrapper">', False)[1]
                data = data.split('<div class="videoInfo">')                
            else:
                data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'video-clip-wrapper'), ('</label', '>'))
                
            for item in data:
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                printDBG(item)
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                
                descTab = []
                desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(item, re.compile('''<span class=["']timeElem[^>]*?>'''), re.compile('</span>'), False)[1])
                if '' != desc: descTab.append(desc)
                desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="text text-video">' , '</div>', False)[1])
                if '' != desc: descTab.append(desc)
                desc  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''<label[^>]+title=['"]([^"^']+?)["']''', 1, True)[0] )
                if '' == desc: 
                    desc = self.cm.ph.getDataBeetwenMarkers(item, '<div class="text"' , '</div>')[1]
                    desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)["']''', 1, True)[0] )
                if '' != desc: descTab.append(desc)
                desc = self.cleanHtmlStr('[/br]'.join(descTab))
                if desc == '': desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<', '>', 'count-files'), ('</a', '>'))[1])  
                
                title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="text">', '</div>', False)[1] )
                if '' == title: title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span style="color: #B82D2D; font-size: 14px">', '</a>', False)[1] )
                if '' == title: title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'alt="', '"', False)[1] )
                if '' == title: title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<a', '>', 'link-title'), ('</a', '>'))[1])
                
                url    = self.getFullUrl(self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'href="', '"', False)[1] ))
                icon   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'src="', '"', False)[1] )
                params = {'good_for_fav':True, 'title':self.cleanHtmlStr(title), 'url':url, 'icon':icon, 'desc':desc}
                if '/video' in url:
                    self.addVideo(params)
                elif '/folder/' in url:
                    params.update({'name':'dir', 'category':'list_folder_sort'})
                    self.addDir(params)
                
            if nextPage:
                nextPage = dict(cItem)
                nextPage.update({'good_for_fav':False, 'title':'Następna strona', 'page':page+1})
                self.addDir(nextPage)
    
    def listChannelsCategories(self, cItem, nextCategory):
        printDBG("cda.listChannelsCategories [%s]" % cItem['url'])
        
        url = self.getFullUrl('/partial/polecanekanaly_paski')
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        cats = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s*?polecani_partnerzy\s*?='), re.compile(';'), False)[1].strip()
        counts = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s*?polecani_video_count\s*?='), re.compile(';'), False)[1].strip()
        maps = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s*?mapping \s*?='), re.compile(';'), False)[1].strip()
        try:
            tmp = re.compile('''"([^"]+?)"\s*?\:\s*?\[''').findall(cats) # we use this trick to get valid order of cats
            data = []
            for item in tmp: data.append('"%s"' % item)
            data = '[%s]' % ','.join(data)
            data   = byteify(json.loads(data), '')
            cats   = byteify(json.loads(cats), '')
            counts = byteify(json.loads(counts), '')
            maps   = byteify(json.loads(maps), '')
            for item in data:
                url = self.getFullUrl('/video/' + maps.get(item, item.lower()))
                printDBG("+++++++++++++++++++++++++++++++++")
                printDBG(cats[item][0])
                kid = cats[item][0]['kid']
                title = item
                desc = counts.get(kid, '')
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'desc':desc, 'url':url})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listChannels(self, cItem, nextCategory):
        printDBG("cda.listChannels [%s]" % cItem['url'])
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>', 'tube-wrap'), ('</a', '>'))
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<', '>', 'tube-name'), ('</span', '>'), False)[1])
            desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<', '>', 'tube-count'), ('</span', '>'), False)[1])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            self.addDir(params)
            
    def listFolders(self, cItem, nextCategory):
        printDBG("cda.listFolders [%s]" % cItem['url'])
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'navigation_foldery'), ('<div', '>', 'panel-footer'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'desc':''})
            self.addDir(params)
            
    def listFolderSort(self, cItem, nextCategory):
        printDBG("cda.listFolderSort [%s]" % cItem['url'])
        
        items = [('od Z do A', 'sortby=name&order=desc'), ('od A do Z', ''), ('najnowsze', 'sortby=created&order=desc'), ('najstarsze', 'sortby=created&order=asc')]
        for item in items:
            url = cItem['url']
            if item[1] != '': url += '?' + item[1]
            title = item[0]
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def listFolderItems(self, cItem):
        printDBG("cda.listFolderItems [%s]" % cItem['url'])
        url = cItem['url']
        if '?' in url: url += '&'
        else: url += '?'
        url += 'type=pliki'
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'list-when-small'), ('</div', '>'))
        for item in data:
            tmp = self.cm.ph.getDataBeetwenNodes(item, ('<a', '>', 'link-title'), ('</a', '>'))[1]
            url = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''\shref=['"]([^'^"]+?)['"]''')[0])
            if '/video/' not in url: continue
            icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''\ssrc=['"]([^'^"]+?)['"]''')[0])
            desc = [self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<', '>', 'time-inline'), ('<', '>'), False)[1])]
            desc.append(self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''\salt=['"]([^'^"]+?)['"]''')[0]))
            
            title = self.cleanHtmlStr(tmp)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':'[/br]'.join(desc)})
            self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        if 'url' not in cItem: return []
        printDBG("cda.getLinksForVideo [%s]" % cItem['url'])
        return self.up.getVideoLinkExt(cItem['url'])
        
    def getFavouriteData(self, cItem):
        try:
            return json.dumps(cItem)
        except Exception: 
            printExc()
        return ''
        
    def getLinksForFavourite(self, fav_data):
        url = fav_data
        try:
            cItem = byteify(json.loads(fav_data))
            url = cItem['url']
        except Exception:
            printExc()
        return self.up.getVideoLinkExt(url)
        
    def tryTologin(self, login, password):
        printDBG('tryTologin start')
        connFailed = _('Connection to server failed!')
        
        loginUrl = 'https://www.cda.pl/login'
        rm(self.COOKIE_FILE)
        sts, data = self.cm.getPage(loginUrl, self.defaultParams)
        if not sts: return False, connFailed 
        
        r = self.cm.ph.getSearchGroups(data, '''name=['"]r['"][^>]+?value=['"]([^'^"]+?)['"]''', 1, True)[0]
        
        post_data = {"r":r, "username":login, "password":password, "login":"zaloguj"}
        params = dict(self.defaultParams)
        HEADER = dict(self.AJAX_HEADER)
        HEADER['Referer'] = self.MAIN_URL
        params.update({'header':HEADER})
        
        # login
        sts, data = self.cm.getPage(loginUrl, params, post_data)
        if not sts: return False, connFailed
        
        # check if logged
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return False, connFailed 
        
        if '/logout' in data:
            return True, 'OK'
        else:
            return False, 'NOT OK'
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('cda.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        if self.login != config.plugins.iptvplayer.cda_login.value and \
           self.password != config.plugins.iptvplayer.cda_password.value and \
           '' != config.plugins.iptvplayer.cda_login.value.strip() and \
           '' != config.plugins.iptvplayer.cda_password.value.strip():
            loggedIn, msg = self.tryTologin(config.plugins.iptvplayer.cda_login.value, config.plugins.iptvplayer.cda_password.value)
            if not loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % config.plugins.iptvplayer.cda_login.value, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.login    = config.plugins.iptvplayer.cda_login.value
                self.password = config.plugins.iptvplayer.cda_password.value
        
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "cda.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(self.MAIN_TAB, {'name':'category'})
        elif 'premium' == category:
            idx = self.currItem.get('f_idx', 0)
            if idx == 0: self.fillFilters({'name':'category', 'url':self.getFullUrl('premium')})
            if idx < len(self.filtersTab): self.listFilter(self.currItem, self.filtersTab)
            else: self.listPremiumItems(self.currItem)
        elif 'video' == category:
            self.listsTab(self.VIDEO_TAB, self.currItem)
        elif 'categories' == category:
            self.listsTab(self.CATEGORIES_TAB, self.currItem)
        elif 'category' == category:
            self.listCategory(self.currItem)
    # CHANNELS
        elif 'channels_cats' == category:
            self.listChannelsCategories(self.currItem, 'list_channels')
        elif 'list_channels' == category:
            self.listChannels(self.currItem, 'list_folders')
        elif 'list_folders' == category:
            self.listFolders(self.currItem, 'list_folder_sort')
        elif 'list_folder_sort' == category:
            self.listFolderSort(self.currItem, 'list_folder_items')
        elif 'list_folder_items' == category:
            self.listFolderItems(self.currItem)
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
        CHostBase.__init__(self, cda(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

