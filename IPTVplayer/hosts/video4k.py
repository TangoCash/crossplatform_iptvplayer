# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm
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
# Config options for HOST
###################################################
config.plugins.iptvplayer.video4k_proxy_gateway = ConfigYesNo(default = False)
config.plugins.iptvplayer.video4k_proxy = ConfigSelection(default = "None", choices = [("None",     _("None")),
                                                                                       ("proxy_1",  _("Alternative proxy server (1)")),
                                                                                       ("proxy_2",  _("Alternative proxy server (2)"))])
config.plugins.iptvplayer.video4k_alt_domain = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use free proxy gateway:"), config.plugins.iptvplayer.video4k_proxy_gateway))
    if not config.plugins.iptvplayer.video4k_proxy_gateway.value:
        optionList.append(getConfigListEntry(_("Use proxy server:"), config.plugins.iptvplayer.video4k_proxy))
        if config.plugins.iptvplayer.video4k_proxy.value == 'None':
            optionList.append(getConfigListEntry(_("Alternative domain:"), config.plugins.iptvplayer.video4k_alt_domain))
    return optionList
###################################################


def gettytul():
    return 'http://video4k.to/'

class Video4K(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'kinox.to', 'cookie':'kinox.to.com.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://static.video4k.to/images/logo.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        self.MAIN_URL = None
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        
        self.cacheLinks   = {}
        self.cacheSeasons = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getStr(self, item, key, default=''):
        if key not in item: return default
        if item[key] == None: return default
        return str(item[key])
        
    def selectDomain(self):
        domains = ['http://video4k.to/']
        domain = config.plugins.iptvplayer.video4k_alt_domain.value.strip()
        if self.cm.isValidUrl(domain):
            if domain[-1] != '/': domain += '/'
            domains.insert(0, domain)
        
        confirmedDomain = None
        for domain in domains:
            self.MAIN_URL = domain
            for i in range(2):
                sts, data = self.getPage(domain)
                if sts:
                    if 'table-filter' in data:
                        confirmedDomain = domain
                        break
                    else: 
                        continue
                break
            
            if confirmedDomain != None:
                break
        
        if confirmedDomain == None:
            self.MAIN_URL = 'http://video4k.to/'
        
        self.MAIN_CAT_TAB = [{'category':'list_filters',      'title': _('Cinema'),              'f_type':'cinema' },
                             {'category':'list_filters',      'title': _('Movies'),              'f_type':'movies' },
                             {'category':'list_filters',      'title': _('Series'),              'f_type':'series' },
                             {'category':'list_sort_filter',  'title': _('Latest Updates'),      'f_type':'updates'},
                             
                             {'category':'search',             'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',     'title': _('Search history'),            } 
                            ]
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        
        if config.plugins.iptvplayer.video4k_proxy_gateway.value:
            addParams = deepcopy(addParams)
            proxy = 'https://www.sslgate.co.uk/index.php?q={0}&hl=2c8'.format(base64.b64encode(baseUrl))
            if 'header' not in addParams: addParams['header'] = dict(self.AJAX_HEADER)
            addParams['header']['Referer'] = proxy
            #params['header']['Cookie'] = 'flags=2e5;'
            url = proxy
            sts, data = self.cm.getPage(url, addParams, post_data)
        else:
            proxy = config.plugins.iptvplayer.video4k_proxy.value
            if proxy != 'None':
                if proxy == 'proxy_1':
                    proxy = config.plugins.iptvplayer.alternative_proxy1.value
                else:
                    proxy = config.plugins.iptvplayer.alternative_proxy2.value
                addParams = dict(addParams)
                addParams.update({'http_proxy':proxy})
            
            def _getFullUrl(url):
                if self.cm.isValidUrl(url):
                    return url
                else:
                    return urlparse.urljoin(baseUrl, url)
                
            addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
            sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
        return sts, data
        
    def fillCacheFilters(self, cItem):
        printDBG("Video4K.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        
        # add letter 
        key = 'f_letter'
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'alphabet', 'table')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<span', '</span>')
        tab = []
        for item in tmp:
            letter = self.cleanHtmlStr(item)
            params = {'title':letter}
            if len(letter) == 1: params[key] = letter
            tab.append(params)
        
        if len(tab):
            self.cacheFilters[key] = tab
            self.cacheFiltersKeys.append(key)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("Video4K.listFilters")
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
        
    def listsSortFilter(self, cItem, nextCategory):
        printDBG("Video4K.listsSortFilter [%s]" % cItem)
        
        titleMap = {'0':_('Default'), '1':_('Title'), '4':_('IMDB Rating')}
        
        sortTab = [('0', 'asc'), ('1', 'asc'), ('4', 'desc'), ('0', 'desc'), ('1', 'desc'), ('4', 'asc')]
        for item in sortTab:
            if item[1] == 'desc': title = '\xe2\x86\x93 '
            else: title = '\xe2\x86\x91 '
            title += titleMap.get(item[0], _('Unknown'))
        
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'f_sort_by':item[0], 'f_sort_order':item[1]})
            self.addDir(params)
        
    def listItems(self, cItem, nextCategory):
        printDBG("Video4K.listItems [%s]" % cItem)
        ITEMS_PER_PAGE = 50
        page = cItem.get('page', 0)
        
        post_data = {'sEcho'          : '1',
                     'iColumns'       : '5',
                     'sColumns'       : '',
                     'iDisplayStart'  : '0',
                     'iDisplayLength' : ITEMS_PER_PAGE,
                     'mDataProp_0'    : '0',
                     'mDataProp_1'    : '1',
                     'mDataProp_2'    : '2',
                     'mDataProp_3'    : '3',
                     'mDataProp_4'    : '4',
                     'sSearch'        : '',
                     'bRegex'         : 'false',
                     'sSearch_0'      : '',
                     'bRegex_0'       : 'false',
                     'bSearchable_0'  : 'true',
                     'sSearch_1'      : '',
                     'bRegex_1'       : 'false',
                     'bSearchable_1'  : 'true',
                     'sSearch_2'      : '',
                     'bRegex_2'       : 'false',
                     'bSearchable_2'  : 'true',
                     'sSearch_3'      : '',
                     'bRegex_3'       : 'false',
                     'bSearchable_3'  : 'true',
                     'sSearch_4'      : '',
                     'bRegex_4'       : 'false',
                     'bSearchable_4'  : 'true',
                     'iSortCol_0'     : '0',
                     'sSortDir_0'     : 'asc',
                     'iSortingCols'   : '1',
                     'bSortable_0'    : 'false',
                     'bSortable_1'    : 'true',
                     'bSortable_2'    : 'false',
                     'bSortable_3'    : 'false',
                     'bSortable_4'    : 'true',
                     'type'           : '',
                     'filter'         : '',
                    }
        
        post_data.update({"iDisplayStart":page * ITEMS_PER_PAGE,"iDisplayLength":ITEMS_PER_PAGE})
        if 'f_type'       in cItem: post_data['type']        = cItem['f_type']
        if 'f_letter'     in cItem: post_data['filter']      = cItem['f_letter']
        if 'f_sort_by'    in cItem: post_data['iSortCol_0']  = cItem['f_sort_by']
        if 'f_sort_order' in cItem: post_data['sSortDir_0']  = cItem['f_sort_order']
        if 'f_pattern'    in cItem: post_data['sSearch']     = cItem['f_pattern']
        
        sts, data = self.getPage(self.getFullUrl('/request'), post_data=post_data)
        if not sts: return
        
        if config.plugins.iptvplayer.video4k_proxy_gateway.value:
            # try to fix this json 
            def _repl(m):
                try:
                    tmp = m.group(1).replace(' /', '/').replace(' ', '.')
                    tmp = re.search('(/images/[^"]+?\.png)', tmp).group(1)
                    return '<img src=\\"%s\\" >' % tmp
                except Exception:
                    return ''
            data = re.sub(r"(<img[^>]+?>)", _repl, data).replace('="', '=\\"')
        
        printDBG(data)
        
        nextPage = False
        try:
            data = byteify(json.loads(data))
            if ((page + 1) * ITEMS_PER_PAGE) < data['iTotalDisplayRecords']:
               nextPage =  True
            for item in data['aaData']:
                itemType = self.cm.ph.getSearchGroups(item[0], '''src=['"][^'^"]*?/images/([^'^"]+?)\.png['"]''')[0]
                title    = self.cleanHtmlStr(item[1].split('<small>', 1)[0])
                imdbId   = self.cm.ph.getSearchGroups(item[1], '''rel=['"]#tt([0-9]+?)['"]''')[0] 
                icon     = 'http://www.imdb.com/title/tt%s/?fake=need_resolve.jpeg' % imdbId
                desc = []
                flags = []
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(item[2], '<img', '>')
                for t in tmp:
                    if '0.' in t: continue
                    t = self.cm.ph.getSearchGroups(t, '''src=['"][^'^"]*?/flags/([^'^"]+?)\.png['"]''')[0]
                    flags.append(t)
                desc.append(_('Type') + ': ' + itemType)
                if not config.plugins.iptvplayer.video4k_proxy_gateway.value or 1 == len(flags):
                    desc.append(_('Language') + ': ' + ' | '.join(flags))
                desc.append(_('Genre') + ': ' + self.cleanHtmlStr(item[3]))
                desc.append(self.cleanHtmlStr(self.cm.ph.getSearchGroups(item[4], '''alt=['"]([^'^"]+?)['"]''')[0]))
                
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'item_type':itemType, 'imdb_id':imdbId, 'title':title, 'icon':icon, 'desc':'[/br]'.join(desc)})
                
                addEpisode = False
                if itemType == 'series':
                    sNum = self.cm.ph.getSearchGroups(item[1], '''data-season=['"]([0-9]+?)['"]''')[0] 
                    eNum = self.cm.ph.getSearchGroups(item[1], '''data-episode=['"]([0-9]+?)['"]''')[0] 
                    if sNum != '' and eNum != '' :
                        title = '%s s%se%s' % (title, sNum.zfill(2), eNum.zfill(2))
                        addEpisode = True
                        params.update({'title':title, 's_num':sNum, 'e_num':eNum})
                        if len(flags): params['f_lang'] = flags[0]
                
                if addEpisode:
                    self.addVideo(params)
                else:
                    self.addDir(params)
                
        except Exception:
            printExc()
            return
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def listLangVersions(self, cItem, nextCategory):
        printDBG("Video4K.listLangVersions")
    
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
        printDBG("Video4K.exploreItem")
        
        try:
            imdbID = cItem['imdb_id']
            sts, data = self.getPage(self.getFullUrl('/request'), post_data={'mID':imdbID})
            if not sts: return
            
            data = byteify(json.loads(data))[0]
            
            # trailer
            lang = cItem['f_lang']
            trailer = 'trailer_%s' % lang
            trailer = self._getStr(data, trailer)
            if self.cm.isValidUrl(trailer):
                params = dict(cItem)
                params.update({'title':'%s - %s' % (cItem['title'], _('trailer')), 'url':trailer})
                self.addVideo(params)
            
            seasons = []
            # type: 0 == cinema, 2 == series, 1 == movies
            if data['type'] == 2:
                # list seasons
                for key in data['seasons']:
                    sNum = str(int(key)) 
                    episodesList = []
                    for item in data['seasons'][key]:
                        eNum = str(int(item))
                        title = '%s s%se%s' % (cItem['title'], sNum.zfill(2), eNum.zfill(2))
                        params = {'title':title, 's_num':sNum, 'e_num':eNum}
                        episodesList.append(params)
                    if len(episodesList):
                        self.cacheSeasons[int(key)] = episodesList
                        seasons.append(sNum)
                
                seasons.sort(key=lambda x: int(x))
                for key in seasons:
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':'%s %s' % (_('Season'), key), 's_key':int(key)})
                    self.addDir(params)
            else:
                params = dict(cItem)
                # params.update({'title':'[%s] %s' % (lang, self._getStr(data, 'name'))})
                self.addVideo(params)
        except Exception:
            printExc()
        
    def listEpisodes(self, cItem):
        printDBG("Video4K.listEpisodes")
        
        sKey = cItem.get('s_key', -1)
        episodesList = self.cacheSeasons.get(sKey, [])
        
        for item in episodesList:
            params = dict(cItem)
            params.update(item)
            params.update({'good_for_fav': False})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Video4K.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['f_pattern'] = searchPattern
        self.listItems(cItem, 'list_lang_ver')
        
    def getLinksForVideo(self, cItem):
        printDBG("Video4K.getLinksForVideo [%s]" % cItem)
        retTab = []
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        
        imdbID = cItem['imdb_id']
        lang   = cItem['f_lang']
        sNum = cItem.get('s_num', '')
        eNum = cItem.get('e_num', '')
        
        post_data = {'mID':imdbID, 'raw':'true', 'language':lang}
        if '' not in [sNum, eNum]:
            post_data.update({'season':sNum, 'episode':eNum})
        
        cacheKey = '%s|%s|%s|%s' % (imdbID, lang, sNum, eNum)
        
        cacheTab = self.cacheLinks.get(cacheKey, [])
        if len(cacheTab):
            return cacheTab
            
            
        try:
            sts, data = self.getPage(self.getFullUrl('/request'), post_data=post_data)
            if not sts: return []
            
            data = byteify(json.loads(data))
            printDBG(data)
            for tab in data:
                for key in tab:
                    name = self._getStr(tab[key], 'name')
                    for item in tab[key]['links']:
                        url = self._getStr(item, 'URL')
                        if self.cm.isValidUrl(url) and 1 == self.up.checkHostSupport(url):
                            retTab.append({'name':name, 'url':url, 'need_resolve':1})
        except Exception:
            printExc()
        
        if len(retTab):
            self.cacheLinks[cacheKey] = retTab
        
        return retTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("Video4K.getVideoLinks [%s]" % videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        orginUrl = str(videoUrl)
        
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
        
    def getArticleContent(self, cItem):
        printDBG("Video4K.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        
        try:
            lang = cItem.get('f_lang', '')
            imdbID = cItem['imdb_id']
            sts, data = self.getPage(self.getFullUrl('/request'), post_data={'mID':imdbID})
            if not sts: return
            
            data = byteify(json.loads(data))[0]
            
            printDBG(data)
            
            title = self._getStr(data, 'name')
            icon  = self.getFullIconUrl(self._getStr(data, 'cover'))
            printDBG("%s -> %s" % (data['cover'], icon))
            if icon.endswith('/'): icon = ''
            desc = self.cleanHtmlStr(str(self._getStr(data, 'plot')))
            
            otherInfo['year']        = self._getStr(data, 'year')
            tmp = self._getStr(data, 'released')
            if tmp.lower() != 'unknown':  otherInfo['released'] = tmp
            otherInfo['duration']    = '~%s %s' % (self._getStr(data, 'duration'), _('min'))
            otherInfo['imdb_rating'] = '%s/10' % (self._getStr(data, 'rating'))
            
            tmp = data.get('genres', [])
            if len(tmp): otherInfo['genres']  = ', '.join(tmp)
            
            tmp = data.get('actors', [])
            if len(tmp): otherInfo['actors']  = ', '.join(tmp)
            
            tmp = data.get('directors', [])
            if len(tmp): otherInfo['directors']  = ', '.join(tmp)
            
            tmp = []
            for item in data['languages']:
                l = self._getStr(item, 'symbol').lower()
                if lang == '' or l == lang: 
                    tmp.append(self._getStr(item, 'text'))
            if len(tmp): otherInfo['language'] = ', '.join(tmp)
            
            if title == '': title = cItem['title']
            if desc == '':  desc = cItem.get('desc', '')
            if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        except Exception:
            printExc()
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
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
            self.selectDomain()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_sort_filter')
        elif category == 'list_sort_filter':
            self.listsSortFilter(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_lang_ver')
        elif category == 'list_lang_ver':
            self.listLangVersions(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, Video4K(), True, [])
        
    def withArticleContent(self, cItem):
        if 'imdb_id' in cItem:
            return True
        return False
    
    