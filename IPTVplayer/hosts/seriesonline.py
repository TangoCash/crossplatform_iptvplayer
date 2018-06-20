# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify, rm, GetDefaultLang
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
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from copy import deepcopy
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper, iptv_js_execute
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.seriesonlineio_proxy = ConfigSelection(default = "None", choices = [("None",     _("None")),
                                                                                              ("proxy_1",  _("Alternative proxy server (1)")),
                                                                                              ("proxy_2",  _("Alternative proxy server (2)"))])
config.plugins.iptvplayer.seriesonlineio_alt_domain = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use proxy server:"), config.plugins.iptvplayer.seriesonlineio_proxy))
    if config.plugins.iptvplayer.seriesonlineio_proxy.value == 'None':
        optionList.append(getConfigListEntry(_("Alternative domain:"), config.plugins.iptvplayer.seriesonlineio_alt_domain))
    return optionList
###################################################


def gettytul():
    return 'https://series9.co/'

class SeriesOnlineIO(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SeriesOnlineIO.tv', 'cookie':'seriesonlineio.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'https://series9.io/images/gomovies-logo-light.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
        
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = None
        self.cacheFilters = {}
        self.cacheLinks = {}
        self.defaultParams = {'header':self.HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_CAT_TAB = []
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
            
        proxy = config.plugins.iptvplayer.seriesonlineio_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            addParams = dict(addParams)
            addParams.update({'http_proxy':proxy})
            
        def _getFullUrl(url):
            if url == '': return ''
            
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        
        url = baseUrl
        urlParams = deepcopy(addParams)
        urlData = deepcopy(post_data)
        unloadUrl = None #
        tries = 0
        removeCookieItems = False
        while tries < 20:
            tries += 1
            sts, data = self.cm.getPageCFProtection(url, urlParams, urlData)
            if not sts: return sts, data
            
            if unloadUrl != None:
                self.cm.getPageCFProtection(unloadUrl, urlParams)
                unloadUrl = None
            
            if '_Incapsula_Resource' in data and None != re.compile('NAME="ROBOTS"', re.IGNORECASE).search(data):
                errorMSG = _('Bypass the Incapsula protection failed.')
                if 'eval' not in data:
                    if tries == 1:
                        rm(self.COOKIE_FILE)
                        printDBG("try %s: >>> re-try after cookie remove" % tries)
                        continue
                    elif tries < 5:
                        if tries == 10: t = 10
                        else: t = random.randint(1, 10)
                        
                        printDBG("try %s: >>> re-try after sleep [%s]" % (tries, t))
                        time.sleep(t)
                        continue
                    else:
                        self.sessionEx.waitForFinishOpen(MessageBox, errorMSG + '\n' + _('Google ReCAPTCHA not supported.'), type = MessageBox.TYPE_ERROR, timeout = 10)
                        break
                
                printDBG("try %s: >>> ReCAPTCHA less check" % tries)
                printDBG("========================================================================")
                printDBG(data)
                printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>', withMarkers=True, caseSensitive=False)
                jscode = ''
                for item in data:
                    src = _getFullUrl(self.cm.ph.getSearchGroups(item, '''<script[^>]+?src=['"]([^"^"]+?)['"]''')[0])
                    if self.cm.isValidUrl(src):
                        tmpParams = deepcopy(urlParams)
                        tmpParams['header']['Referer'] = baseUrl
                        tmpParams['return_data'] = True
                        sts, tmp = self.cm.getPageCFProtection(src, urlParams)
                        
                    else:
                        sts, tmp = self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<script[^>]*?>', re.IGNORECASE), re.compile('</script>', re.IGNORECASE), withMarkers=False)
                    if sts: jscode += '\n' + tmp
                
                printDBG("try %s: >>> ReCAPTCHA less check js code" % tries)
                printDBG("========================================================================")
                printDBG(jscode)
                printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE).replace('; ', ';')
                printDBG("try %s: >>> ReCAPTCHA less check cookies" % tries)
                printDBG("========================================================================")
                printDBG(cookieHeader)
                printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                
                try:
                    alljscode = base64.b64decode('''dmFyIHdpbmRvdyA9IHRoaXM7DQp2YXIgZG9jdW1lbnQgPSB7fTsNCnZhciBwYXJlbnQgPSB7bG9jYXRpb24gOiB7IHJlbG9hZCA6IGZ1bmN0aW9uICgpew0KICAgIGlwdHZVbmxvYWQgPSB0cnVlOw0KICAgIHRyeSB7DQogICAgICAgIHdpbmRvdy5vbnVubG9hZCgpOw0KICAgIH0gY2F0Y2ggKGMpIHsNCiAgICAgICAgcHJpbnQoYyk7DQogICAgfQ0KICAgIH0NCn0NCn07DQoNCnZhciBpcHR2VW5sb2FkID0gZmFsc2U7DQoNCnZhciBfaXB0dkxvZyA9IHsNCiAgICBlbGVtcyA6IFtdDQp9Ow0KDQp2YXIgWE1MSHR0cFJlcXVlc3QgPSBmdW5jdGlvbiAoKXsNCiAgICB0aGlzLm9wZW4gPSBmdW5jdGlvbiAobWV0aG9kLCB1cmwsIGFzeW5jLCB1c2VyLCBwYXNzd29yZCl7DQogICAgICAgIHRoaXMucGFyYW1zID0ge3R5cGUgOiAneGhyJywgbWV0aG9kIDogbWV0aG9kLCB1cmwgOiB1cmwsIGFzeW5jIDogYXN5bmMsIHVzZXIgOiB1c2VyLCBwYXNzd29yZCA6IHBhc3N3b3JkLCBjb29raWUgOiBkb2N1bWVudC5jb29raWV9Ow0KICAgIH07DQogICAgdGhpcy5zZW5kID0gZnVuY3Rpb24gKHBvc3Qpew0KICAgICAgICB0aGlzLnBhcmFtc1sncG9zdCddID0gcG9zdDsNCiAgICAgICAgdGhpcy5wYXJhbXNbJ3VubG9hZCddID0gaXB0dlVubG9hZDsNCiAgICAgICAgX2lwdHZMb2cuZWxlbXNbX2lwdHZMb2cuZWxlbXMubGVuZ3RoXSA9IHRoaXMucGFyYW1zOw0KICAgICAgICB0cnkgew0KICAgICAgICAgICAgdGhpcy5zdGF0dXMgPSAyMDA7DQogICAgICAgICAgICB0aGlzLnJlYWR5U3RhdGUgPSA0Ow0KICAgICAgICAgICAgdGhpcy5vbnJlYWR5c3RhdGVjaGFuZ2UoKTsNCiAgICAgICAgfSBjYXRjaCAoYykgew0KICAgICAgICAgICAgcHJpbnQoYyk7DQogICAgICAgIH0NCiAgICB9Ow0KfTsNCg0KdmFyIGVsZW1lbnQgPSBmdW5jdGlvbiAodHlwZSkNCnsNCiAgICB0aGlzLl90eXBlID0gdHlwZTsNCiAgICANCiAgICBPYmplY3QuZGVmaW5lUHJvcGVydHkodGhpcywgInNyYyIsIHsNCiAgICAgICAgZ2V0IDogZnVuY3Rpb24gKCkgew0KICAgICAgICAgICAgcmV0dXJuIHRoaXMuX3NyYzsNCiAgICAgICAgfSwNCiAgICAgICAgc2V0IDogZnVuY3Rpb24gKHZhbCkgew0KICAgICAgICAgICAgdGhpcy5fc3JjID0gdmFsOw0KICAgICAgICAgICAgX2lwdHZMb2cuZWxlbXNbX2lwdHZMb2cuZWxlbXMubGVuZ3RoXSA9IHt0eXBlIDogdGhpcy5fdHlwZSwgIHNyYyA6IHRoaXMuX3NyYywgdW5sb2FkIDogaXB0dlVubG9hZCwgY29va2llIDogZG9jdW1lbnQuY29va2llfQ0KICAgICAgICB9DQogICAgfSk7DQp9Ow0KDQpkb2N1bWVudC5jcmVhdGVFbGVtZW50ID0gZnVuY3Rpb24gKHR5cGUpIHsNCiAgICByZXR1cm4gbmV3IGVsZW1lbnQodHlwZSk7IA0KfTsNCg0KdmFyIG5hdmlnYXRvciA9IHt9Ow0KdmFyIGNocm9tZSA9IHt9Ow0KdmFyIHdlYmtpdFVSTCA9IHt9Ow0KDQpuYXZpZ2F0b3IudmVuZG9yID0gIkdvb2dsZSBJbmMuIjsNCm5hdmlnYXRvci5hcHBOYW1lID0gIk5ldHNjYXBlIjsNCm5hdmlnYXRvci5wbHVnaW5zID0gW107DQpuYXZpZ2F0b3IucGxhdGZvcm0gPSAiTGludXggeDg2XzY0IjsNCndpbmRvdy5XZWJHTFJlbmRlcmluZ0NvbnRleHQgPSB7fTsNCg0K''')
                    alljscode += '\ndocument.cookie = "%s";\n%s\nprint(JSON.stringify(_iptvLog));' % (cookieHeader, jscode)
                    printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
                    printDBG(alljscode)
                    printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    ret = iptv_js_execute( alljscode )
                    if ret['sts'] and 0 == ret['code']:
                        decoded = ret['data'].strip()
                        printDBG('DECODED DATA -> \n[%s]\n' % decoded)
                    decoded = byteify(json.loads(decoded))
                    for item in decoded['elems']:
                        cookie = item['cookie'].split(';')[0].split('=', 1)
                        cookie = {cookie[0]:urllib.unquote(cookie[1])}
                        urlParams['cookie_items'] = cookie
                        addParams['cookie_items'] = cookie
                        removeCookieItems = True
                        if not item.get('unload', False):
                            tmpParams = deepcopy(urlParams)
                            tmpParams['header']['Referer'] = baseUrl
                            tmpParams['return_data'] = True
                            
                            if item['type'] == 'img':
                                tmpParams['header']['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                                sts, tmp = self.cm.getPage(_getFullUrl(item['src']), tmpParams)
                            elif item['type'] == 'xhr':
                                tmpParams['header']['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                                sts, tmp = self.cm.getPage(_getFullUrl(item['url']), tmpParams)
                        else:
                            printDBG(item)
                            tmpParams['header']['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                            sts, tmp = self.cm.getPage(_getFullUrl(item['src']), tmpParams)
                            unloadUrl = _getFullUrl(item['src'])
                    continue
                except Exception as e:
                    self.sessionEx.waitForFinishOpen(MessageBox, errorMSG + '\n' + str(e), type = MessageBox.TYPE_ERROR, timeout = 10)
                    printExc()
                
                return False, None
            elif 'sucuri_cloudproxy' in data:
                cookieItems = {}
                jscode = self.cm.ph.getDataBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)[1]
                if 'eval' in jscode:
                    jscode = '%s\n%s' % (base64.b64decode('''dmFyIGlwdHZfY29va2llcz1bXSxkb2N1bWVudD17fTtPYmplY3QuZGVmaW5lUHJvcGVydHkoZG9jdW1lbnQsImNvb2tpZSIse2dldDpmdW5jdGlvbigpe3JldHVybiIifSxzZXQ6ZnVuY3Rpb24obyl7bz1vLnNwbGl0KCI7IiwxKVswXS5zcGxpdCgiPSIsMiksb2JqPXt9LG9ialtvWzBdXT1vWzFdLGlwdHZfY29va2llcy5wdXNoKG9iail9fSk7dmFyIHdpbmRvdz10aGlzLGxvY2F0aW9uPXt9O2xvY2F0aW9uLnJlbG9hZD1mdW5jdGlvbigpe3ByaW50KEpTT04uc3RyaW5naWZ5KGlwdHZfY29va2llcykpfTs='''), jscode)
                    ret = iptv_js_execute( jscode )
                    if ret['sts'] and 0 == ret['code']:
                        cookies = byteify(json.loads(ret['data'].strip()))
                        for cookie in cookies: cookieItems.update(cookie)
                self.defaultParams['cookie_items'] = cookieItems
                urlParams['cookie_items'] = cookieItems
                removeCookieItems = False
                sts, data = self.cm.getPageCFProtection(url, urlParams, urlData)
            
            # remove not needed used cookie
            if removeCookieItems:
                self.defaultParams.pop('cookie_items', None)
            self.cm.clearCookie(self.COOKIE_FILE, removeNames=['___utmvc'])
            printDBG(data)
            return sts, data
        
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
        
    def getDefaulIcon(self, cItem):
        return self.getFullIconUrl(self.DEFAULT_ICON_URL)
    
    def getFullUrl(self, url):
        if url.startswith('//'): return 'https:' + url
        return CBaseHostClass.getFullUrl(self, url)
    
    def getFullIconUrl(self, url):
        url = self.getFullUrl(url)
        
        proxy = config.plugins.iptvplayer.seriesonlineio_proxy.value
        
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            url = strwithmeta(url, {'iptv_http_proxy':proxy})
            
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def selectDomain(self):
        domains = ['https://series9.co/'] #'http://123movieshd.us/'
        domain = config.plugins.iptvplayer.seriesonlineio_alt_domain.value.strip()
        if self.cm.isValidUrl(domain):
            if domain[-1] != '/': domain += '/'
            domains.insert(0, domain)
        
        confirmedDomain = None
        for domain in domains:
            self.MAIN_URL = domain
            for i in range(2):
                sts, data = self.getPage(domain)
                if sts:
                    cUrl = data.meta['url']
                    self.setMainUrl(cUrl)
                    if 'genre/action/' in data:
                        confirmedDomain = self.MAIN_URL
                        break
                    else: 
                        continue
                break
            
            if confirmedDomain != None:
                break
        
        if confirmedDomain == None:
            self.MAIN_URL = 'https://series9.co/'
        
        self.SEARCH_URL = self.MAIN_URL + 'movie/search'
        #self.DEFAULT_ICON_URL = self.MAIN_URL + 'assets/images/logo-light.png'
        
        self.MAIN_CAT_TAB = [{'category':'list_filter_genre', 'title': 'Movies',    'url':self.MAIN_URL+'movie/filter/movie' },
                             {'category':'list_filter_genre', 'title': 'TV-Series', 'url':self.MAIN_URL+'movie/filter/series'},
                             {'category':'list_filter_genre', 'title': 'Cinema',    'url':self.MAIN_URL+'movie/filter/cinema'},
                             {'category':'search',          'title': _('Search'), 'search_item':True,                        },
                             {'category':'search_history',  'title': _('Search history'),                                    } 
                            ]
        
    def fillCacheFilters(self):
        self.cacheFilters = {}
        
        sts, data = self.getPage(self.getFullUrl('movie/filter/series/all/all/all/all/latest/'), self.defaultParams)
        if not sts: return
        
        # get sort by
        self.cacheFilters['sort_by'] = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Sort by</span>', '</ul>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
        for item in tmp:
            value = self.cm.ph.getSearchGroups(item, 'href="[^"]+?/filter/all/all/all/all/all/([^"^/]+?)/')[0]
            self.cacheFilters['sort_by'].append({'sort_by':value, 'title':self.cleanHtmlStr(item)})
            
        for filter in [{'key':'quality', 'marker':'Quality</span>'},
                       {'key':'genre',   'marker':'Genre</span>'  },
                       {'key':'country', 'marker':'Country</span>'},
                       {'key':'year',    'marker':'Release</span>'}]:
            self.cacheFilters[filter['key']] = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, filter['marker'], '</ul>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>', withMarkers=True, caseSensitive=False)
            allItemAdded = False
            for item in tmp:
                value = self.cm.ph.getSearchGroups(item, 'value="([^"]+?)"')[0]
                self.cacheFilters[filter['key']].append({filter['key']:value, 'title':self.cleanHtmlStr(item)})
                if value == 'all': allItemAdded = True
            if not allItemAdded:
                self.cacheFilters[filter['key']].insert(0, {filter['key']:'all', 'title':'All'})
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, filter, nextCategory):
        printDBG("SeriesOnlineIO.listFilters")
        if {} == self.cacheFilters:
            self.fillCacheFilters()
        
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory=None):
        printDBG("SeriesOnlineIO.listItems")
        url = cItem['url']
        page = cItem.get('page', 1)
        if '/search' not in url:
            url += '/{0}/{1}/{2}/{3}/{4}/'.format(cItem['quality'], cItem['genre'], cItem['country'], cItem['year'], cItem['sort_by'])
        
        if page > 1: url = url + '?page={0}'.format(page)
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>', False)[1]
        if '' != self.cm.ph.getSearchGroups(nextPage, 'page=(%s)[^0-9]' % (page+1))[0]:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="ml-item">', '</a>', withMarkers=True)
        for item in data:
            url  = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-original="([^"]+?)"')[0] )
            dataUrl = self.cm.ph.getSearchGroups(item, 'data-url="([^"]+?)"')[0]
            if icon == '': icon = cItem.get('icon', '')
            desc = self.cleanHtmlStr( item )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0] )
            if title == '': title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0] )
            if url.startswith('http'):
                params = {'good_for_fav': True, 'title':title, 'url':url, 'data_url':dataUrl, 'desc':desc, 'info_url':url, 'icon':icon}
                if '-season-' not in url and 'class="mli-eps"' not in item:
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    params2 = dict(cItem)
                    params2.update(params)
                    self.addDir(params2)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def listEpisodes(self, cItem):
        printDBG("SeriesOnlineIO.listEpisodes")
        
        tab = self.getLinksForVideo(cItem, True)
        episodeKeys = []
        episodeLinks = {}
        
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(tab)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        for item in tab:
            title = item['title'].upper()
            title = title.replace('EPISODE', ' ')
            title = title.replace(' 0', ' ')
            if 'TRAILER' not in title: title = 'Episode ' + title
            title = self.cm.ph.removeDoubles(title, ' ')
            if title not in episodeKeys:
                episodeLinks[title] = []
                episodeKeys.append(title)
            item['name'] = item['server_title']
            try: key = int(title)
            except Exception: key = title
            printDBG("key [%s]" % key)
            episodeLinks[key].append(item)
        
        seasonNum = self.cm.ph.getSearchGroups(cItem['url']+'|', '''-season-([0-9]+?)[^0-9]''', 1, True)[0]
        for item in episodeKeys:
            episodeNum = self.cm.ph.getSearchGroups(item + '|', '''Episode\s+?([0-9]+?)[^0-9]''', 1, True)[0]
            if '' != episodeNum and '' != seasonNum:
                title = 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2)) + ' ' + item.replace('Episode %s' % episodeNum, '')
            else: title = item
            baseTitle = re.sub('Season\s[0-9]+?[^0-9]', '', cItem['title'] + ' ')
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':self.cleanHtmlStr(baseTitle + ' ' + title), 'urls':episodeLinks[item]})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SeriesOnlineIO.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        if self.MAIN_URL == None:
            self.selectDomain()
        
        url = self.SEARCH_URL + '/' + urllib.quote_plus(searchPattern).replace('+', '-')
        sts, data = self.getPage(url)
        if not sts: return
        cUrl = data.meta['url']
        tmp = ''
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script>', '</script>', False)
        for item in data:
            if '$.ajax(' in item:
                tmp = item
                break
        if tmp == '': return
        ret = iptv_js_execute( '$={}; $.ajax=function(setup){print(JSON.stringify(setup));}\n' + tmp)
        if ret['sts'] and 0 == ret['code']:
            decoded = ret['data'].strip()
            printDBG('DECODED DATA -> \n[%s]\n' % decoded)
            try:
                decoded = byteify(json.loads(decoded))
                searchUrl = self.getFullUrl(decoded.get('url', cUrl))
                if '?' not in searchUrl: searchUrl += '?'
                if 'data' in decoded:
                    searchUrl += urllib.urlencode(decoded['data'])
                printDBG('searchUrl [%s]\n' % searchUrl)
                cItem = dict(cItem)
                cItem['url'] = searchUrl
                self.listItems(cItem, 'list_episodes')
            except Exception:
                printExc()
        
    def getLinksForVideo(self, cItem, forEpisodes=False):
        printDBG("SeriesOnlineIO.getLinksForVideo [%s]" % cItem)
        
        if 'urls' in cItem:
            return cItem['urls']
        
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        url = cItem['url']        
        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return []
        
        # get trailer
        trailer = self.cm.ph.getDataBeetwenMarkers(data, '''$('#pop-trailer')''', '</script>', False)[1]
        trailer = self.cm.ph.getSearchGroups(trailer, '''['"](http[^"^']+?)['"]''')[0]
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'id="mv-info"', '</a>')[1]
        url  = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]+?)['"]''')[0])
        
        params = dict(self.defaultParams)
        params['header'] = dict(params['header'])
        params['header']['Referer'] = cItem['url']
        
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="server', '<div class="clearfix">', withMarkers=True)
        for item in data:
            serverTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div id="server', '</div>', withMarkers=True)[1] )
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a', '</a>', withMarkers=True)
            for eItem in tmp:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(eItem, '''player-data=['"]([^'^"]+?)['"]''')[0])
                title = self.cleanHtmlStr( eItem )
                if not forEpisodes:
                    name = serverTitle + ': ' + title
                else:
                    name = ''
                urlTab.append({'name':name, 'title':title, 'server_title':serverTitle, 'url':url, 'need_resolve':1})
            
        if len(urlTab) and self.cm.isValidUrl(trailer) and len(trailer) > 10:
            urlTab.insert(0, {'name':'Trailer', 'title':'Trailer', 'server_title':'Trailer', 'url':trailer, 'need_resolve':1})
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("SeriesOnlineIO.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if not self.cm.isValidUrl(videoUrl):
            return []
        
        params = dict(self.defaultParams)
        params['return_data'] = False
        try:
            sts, response = self.getPage(videoUrl, params)
            maintype = response.info().maintype.lower()
            response.close()
            if maintype != 'text':
                if maintype != 'video': return [{'name':self.up.getDomain(videoUrl), 'url':videoUrl}]
                else: return []
        except Exception:
            printExc()
            return []
        
        tab = self.up.getVideoLinkExt(videoUrl)
        if len(tab): return tab
        
        sts, data = self.getPage(videoUrl, self.defaultParams)
        if not sts: return []
        
        tmpVideoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        if self.cm.isValidUrl(tmpVideoUrl):
            tab = self.up.getVideoLinkExt(tmpVideoUrl)
            if len(tab): return tab
        
        
        subTracks = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'sources', ']')[1]
        if tmp != '':
            tmp = data.split('}')
            urlAttrName = 'file'
            sp = ':'
        else:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', withMarkers=True)
            urlAttrName = 'src'
            sp = '='
        
        for item in tmp:
            url  = self.cm.ph.getSearchGroups(item, r'''['"]?{0}['"]?\s*{1}\s*['"]((:?https?:)?//[^"^']+)['"]'''.format(urlAttrName, sp))[0]
            name = self.cm.ph.getSearchGroups(item, r'''['"]?label['"]?\s*{0}\s*['"]([^"^']+)['"]'''.format(sp))[0]
            if url == '' or 'error.com' in url: continue
            if url.startswith('//'): url = 'https:' + url
                
            printDBG('---------------------------')
            printDBG('url:  ' + url)
            printDBG('name: ' + name)
            printDBG('+++++++++++++++++++++++++++')
            printDBG(item)
            
            if 'mp4' in item:
                urlTab.append({'name':self.up.getDomain(url) + ' ' + name, 'url':url})
            elif 'captions' in item:
                format = url[-3:]
                if format in ['srt', 'vtt']:
                    subTracks.append({'title':name, 'url':self.getFullIconUrl(url), 'lang':name, 'format':format})
            
        printDBG(subTracks)
        if len(subTracks):
            for idx in range(len(urlTab)):
                urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], {'external_sub_tracks':subTracks})
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("SeriesOnlineIO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem.get('url', ''))
        if not sts: return retTab
        
        title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:title"[^>]+?content="([^"]+?)"')[0] )
        desc  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:description"[^>]+?content="([^"]+?)"')[0] )
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<meta property="og:image"[^>]+?content="([^"]+?)"')[0] )
        
        if title == '': title = cItem['title']
        if desc == '':  title = cItem['desc']
        if icon == '':  title = cItem['icon']
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="mvic-info">', '<div class="clearfix">', False)[1]
        descData = self.cm.ph.getAllItemsBeetwenMarkers(descData, '<p', '</p>')
        descTabMap = {"Director":     "director",
                      "Actor":        "actors",
                      "Genre":        "genre",
                      "Country":      "country",
                      "Release":      "released",
                      "Duration":     "duration",
                      "Quality":      "quality",
                      "IMDb":         "rated"}
        
        otherInfo = {}
        for item in descData:
            item = item.split('</strong>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key == 'IMDb': val += ' IMDb' 
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = val
                except Exception: continue
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def getFavouriteData(self, cItem):
        printDBG('SeriesOnlineIO.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'data_url':cItem['data_url'], 'desc':cItem['desc'], 'info_url':cItem['info_url'], 'icon':cItem['icon']}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('SeriesOnlineIO.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('SeriesOnlineIO.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
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
        if self.MAIN_URL == None:
            #rm(self.COOKIE_FILE)
            self.selectDomain()

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.fillCacheFilters()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category.startswith('list_filter_'):
            filter = category.replace('list_filter_', '')
            if filter == 'genre':     self.listFilters(self.currItem, filter, 'list_filter_country')
            elif filter == 'country': self.listFilters(self.currItem, filter, 'list_filter_year')
            elif filter == 'year':    self.listFilters(self.currItem, filter, 'list_filter_quality')
            elif filter == 'quality': self.listFilters(self.currItem, filter, 'list_filter_sort_by')
            elif filter == 'sort_by': self.listFilters(self.currItem, filter, 'list_items')
        if category == 'list_items':
            self.listItems(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, SeriesOnlineIO(), True, [])
    
    def withArticleContent(self, cItem):
        if cItem['type'] != 'video' and cItem['category'] != 'list_episodes':
            return False
        return True
    