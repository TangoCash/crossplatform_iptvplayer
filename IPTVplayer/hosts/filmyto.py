# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify, rm, GetTmpDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import base64
try:    import json
except Exception: import simplejson as json
from datetime import datetime
from urlparse import urlparse, urljoin
from copy import deepcopy
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.icomponents.iptvmultipleinputbox import IPTVMultipleInputBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://filmy.to/'

class FilmyTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'FilmyTo.tv', 'cookie':'filmyto.cookie'})
        self.USER_AGENT = 'Mozilla/5.0'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://filmy.to/'
        self.DEFAULT_ICON_URL = self.MAIN_URL + 'static/frontend/img/logo.06ac9ed751db.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_items',        'title': _('Movies'),                       'url':self.getFullUrl('filmy/'),        },
                             {'category':'list_items',        'title': _('Series'),                       'url':self.getFullUrl('seriale/'),      },
                             {'category':'list_items',        'title': _('Dokumentalne'),                 'url':self.getFullUrl('dokumentalne/'), },
                             {'category':'list_items',        'title': _('Dla dzieci'),                   'url':self.getFullUrl('dzieci/'),       },
                             {'category':'search',            'title': _('Search'), 'search_item':True,                                           },
                             {'category':'search_history',    'title': _('Search history'),                                                       } 
                            ]
        
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.cacheSeries = {}
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
        if sts and 'id="captchaPage"' in data:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'id="captchaPage"', '</form>')[1]
            captchaTitle = self.cm.ph.getAllItemsBeetwenMarkers(data, '<p', '</p>')
            
            if len(captchaTitle):
                captchaTitle = self.cleanHtmlStr(captchaTitle[-1])
            
            # parse form data
            data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>')[1]
            
            imgUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            if imgUrl.startswith('/'):
                imgUrl = urljoin(baseUrl, imgUrl)
                
            actionUrl = self.cm.ph.getSearchGroups(data, 'action="([^"]+?)"')[0]
            if actionUrl.startswith('/'):
                actionUrl = urljoin(baseUrl, actionUrl)
                
            captcha_post_data = dict(re.findall(r'''<input[^>]+?name=["']([^"^']*)["'][^>]+?value=["']([^"^']*)["'][^>]*>''', data))
            
            if self.cm.isValidUrl(imgUrl):
                header = dict(self.HTTP_HEADER)
                header['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                params = dict(self.defaultParams)
                params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':header} )
                filePath = GetTmpDir('.iptvplayer_captcha.jpg')
                ret = self.cm.saveWebFile(filePath, imgUrl.replace('&amp;', '&'), params)
                if not ret.get('sts'):
                    SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                    return False

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
                    captcha_post_data['captcha_1'] = retArg[0][0]
                    params = deepcopy(addParams)
                    params['header']['Referer'] = baseUrl
                    sts, data = self.cm.getPage(actionUrl, self.defaultParams, captcha_post_data)
                
                if sts and 'id="captchaPage"' in data:
                    SetIPTVPlayerLastHostError(_('Wrong answer.'))
                    sts, data = False, None
                else:
                    sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def getStr(self, item, key):
        if key not in item: return ''
        if item[key] == None: return ''
        return str(item[key])
        
    def fillFilters(self, cItem):
        self.cacheFilters = {}
        sts, data = self.getPage(self.getFullUrl('filmy/1')) # it seems that series and movies have same filters
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
                
        # letters
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="letters">', '</div')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<button', '</button>', withMarkers=True)
        addFilter(tmpData, 'letters', True, '')
        
        # genres
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="gatunek"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'genres', False, '') #'Gatunek: '
        
        # production
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="produkcja"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'production', False, '') #'Produkcja: '
        
        # year
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="rok_od"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'year', False, '') #'Rok: '
        
        # min raiting
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="ocena_od"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option', '</option>', withMarkers=True)
        addFilter(tmpData, 'min_raiting', False, 'Ocena od: ')
        
        # sort
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, '<select name="sortowanie"', '</select>')[1]
        tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<option ', '</option>', withMarkers=True)
        addFilter(tmpData, 'sort', False, '')
        
        # add order to sort filter
        orderLen = len(self.cacheFilters['sort'])
        for idx in range(orderLen):
            item = deepcopy(self.cacheFilters['sort'][idx])
            # desc
            self.cacheFilters['sort'][idx].update({'title':'\xe2\x86\x93 ' + self.cacheFilters['sort'][idx]['title'], 'order':'0'}) #+ ' (%s)' % "Malejąco"
            # asc
            item.update({'title': '\xe2\x86\x91 ' + item['title'], 'order':'rosnaco'}) #+ ' (%s)' % "Rosnąco"
            self.cacheFilters['sort'].append(item)
        
    def listFilter(self, cItem, filters):
        params = dict(cItem)
        idx = params.get('f_idx', 0)
        params['f_idx'] = idx + 1
        
        if idx == 0:
            self.fillFilters(cItem)
        
        tab = self.cacheFilters.get(filters[idx], [])
        self.listsTab(tab, params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("FilmyTo.listItems")
        perPage = 18
        page = cItem.get('page', 1)
        baseUrl = cItem['url'] + '{0}?widok=galeria&'.format(page)
        
        if cItem.get('letters', '0') not in ['0', '-', '']:
            baseUrl += 'litera={0}&'.format(cItem['letters'])
        
        if cItem.get('genres', '0') not in ['0', '-', '']:
            baseUrl += 'gatunek={0}&'.format(cItem['genres'])
        
        if cItem.get('production', '0') not in ['0', '-', '']:
            baseUrl += 'produkcja={0}&'.format(cItem['production'])
        
        if cItem.get('year', '0') not in ['0', '-', '']:
            baseUrl += 'rok_od={0}&rok_do={1}&'.format(cItem['year'], cItem['year'])
        
        if cItem.get('min_raiting', '0') not in ['0', '-', '']:
            baseUrl += 'ocena_od={0}&'.format(cItem['min_raiting'])
        
        if cItem.get('sort', '0') not in ['0', '-', '']:
            baseUrl += 'sortowanie={0}&'.format(cItem['sort'])
            
        if cItem.get('order', '0') not in ['0', '-', '']:
            baseUrl += 'kolejnosc={0}&'.format(cItem['order'])
            
        sts, data = self.getPage(self.getFullUrl(baseUrl), self.defaultParams)
        if not sts: return
        
        if None != re.search('<a[^>]+?>&rarr;<', data):
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie clearfix">', '<div class="pull-right">', withMarkers=False)[1]
        data = data.split('<div class="sep">')
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip())
            desc   = self.cleanHtmlStr(item.split('<div class="details-top">')[-1].replace('</strong>', '[/br]'))
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            if '/film/' in url:
                self.addVideo(params)
            elif '/serial/' in url:
                params['category'] = nextCategory
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page + 1})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("FilmyTo.listSeasons")
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, ' <select name="sezon"', '</select>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(item)
            sNum   = self.cm.ph.getSearchGroups('|%s|' % title, '''[^0-9]?([0-9]+?)[^0-9]''')[0]
            params = dict(cItem)
            params.update({'good_for_fav': True, 'priv_snum':sNum, 'priv_stitle':cItem['title'], 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("FilmyTo.listEpisodes")
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        params  = dict(self.defaultParams)
        params['header'] = dict(params['header'])
        params['header']['Referer'] = cItem['url']
        
        data  = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post">', '</form>')[1]
        name  = self.cm.ph.getSearchGroups(data, '''name=['"]([^'^"]+?)['"]''')[0]
        value = self.cm.ph.getSearchGroups(data, '''value=['"]([^'^"]+?)['"]''')[0]
        post_data = {name:value, 'ukryj_bez_zrodel':'1', 'ukryj':'on'}
        sts, data = self.getPage(cItem['url'], params, post_data)
        
        #if not sts or '<aside>' not in data:
        sts, data = self.getPage(cItem['url'], params)
        if not sts: return
        
        sNum = cItem['priv_snum']
        data = self.cm.ph.getDataBeetwenMarkers(data, '<aside>', '</aside>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>', withMarkers=True)
        for item in data:
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<span class="ep_tyt[^>]+?>'), re.compile('</span>'))[1])
            eNum   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<span class="ep_nr[^>]+?>'), re.compile('</span>'))[1])
            eNum   = self.cm.ph.getSearchGroups('|%s|' % eNum, '''[^0-9]?([0-9]+?)[^0-9]''')[0]
            title  = cItem['priv_stitle'] + ': s{0}e{1} {2}'.format(sNum.zfill(2), eNum.zfill(2), title)
            params = dict(cItem)
            params.update({'good_for_fav': True, 'title':title, 'url':url})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FilmyTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        baseUrl = self.getFullUrl('szukaj?q=' + urllib.quote_plus(searchPattern))
        sts, data = self.getPage(baseUrl)
        if not sts: return

        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="movie clearfix">', '<div id="now_playing"', withMarkers=False)[1]
        data = data.split('clearfix">')
        if len(data): data[-1] = data[-1] + '<test test="'
        for item in data:
            item += 'clearfix">'
            tmpTab = []
            url    = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="title', '</a>')[1])
            icon   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0].strip().replace('thumbnails/', ''))
            desc   = self.cleanHtmlStr(item.split('</a>')[-1].replace('</p>', '[/br]'))
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            if '/film/' in url:
                self.addVideo(params)
            elif '/serial/' in url:
                params['category'] = 'list_seasons'
                self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("FilmyTo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        #rm(self.COOKIE_FILE)
        
        sts, data = self.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        provision = self.cm.ph.getSearchGroups(data, '<meta[^>]+?"provision"[^>]+?content="([^"]+?)"')[0]
        
        params = deepcopy(self.defaultParams)
        params['header']['Referer'] = cItem['url']
        
        try: url = 'http://auth.filmy.to/iframe?page=%s&src=%s' % (urlparse(cItem['url']).path, self.up.getDomain(cItem['url']))
        except Exception:
            printExc()
            return []
            
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        csrftoken = self.cm.getCookieItem(self.COOKIE_FILE, 'csrftoken')
        
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = cItem['url']
        params['header']['X-CSRFToken'] = csrftoken
        
        url = self.getFullUrl('/ajax/provision/' + provision)
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        #printDBG(data)
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="host-container', '</span>', withMarkers=True)
        for item in data:
            url = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''data-url="([^"]+?)"''')[0])
            if url == '': continue
            printDBG(url)
            url     = self.getFullUrl(self.cm.ph.getSearchGroups(url, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            quality = self.cm.ph.getSearchGroups(item, '''title="([^"]+?)"''')[0]
            lang    = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="label', '</span>')[1])
            name = '{0} {1} {2}'.format(lang, quality, self.up.getHostName(url) )
            urlTab.append({'name':name, 'url':url, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("FilmyTo.getVideoLinks [%s]" % videoUrl)
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
        printDBG('FilmyTo.getFavouriteData')
        return json.dumps(cItem)
        
    def getLinksForFavourite(self, fav_data):
        printDBG('FilmyTo.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('FilmyTo.setInitListFromFavouriteItem')
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

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif 'list_items' == category:
            filtersTab = ['letters', 'genres', 'production', 'year', 'min_raiting', 'sort']
            idx = self.currItem.get('f_idx', 0)
            if idx < len(filtersTab):
                self.listFilter(self.currItem, filtersTab)
            else:
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
        CHostBase.__init__(self, FilmyTo(), True, []) #[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]
    
