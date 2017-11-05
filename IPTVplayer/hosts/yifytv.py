# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.base import noPadding
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import datetime
import string
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from binascii import hexlify, unhexlify, a2b_hex
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://yify.bz/'

class YifyTV(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    MAIN_URL    = 'http://yify.bz/'
    SRCH_URL    = MAIN_URL + '?s='
    DEFAULT_ICON= MAIN_URL + 'wp-content/themes/yifybootstrap3/img/logo3s.png'
    
    MAIN_CAT_TAB = [{'category':'list_items',            'title': _('Releases'),          'icon':DEFAULT_ICON, 'url':MAIN_URL+'files/releases/'                                                 },
                    {'category':'list_popular',          'title': _('Popular'),           'icon':DEFAULT_ICON, 'url':MAIN_URL+'wp-admin/admin-ajax.php?action=noprivate_movies_loop&asec=get_pop&needcap=1'                                                        },
                    {'category':'list_items',            'title': _('Top +250'),          'icon':DEFAULT_ICON, 'url':MAIN_URL+'files/movies/?meta_key=imdbRating&orderby=meta_value&order=desc' },
                    {'category':'list_genres_filter',    'title': _('Genres'),            'icon':DEFAULT_ICON, 'url':MAIN_URL+'files/movies/'                                                   },
                    {'category':'list_languages_filter', 'title': _('Languages'),         'icon':DEFAULT_ICON, 'url':MAIN_URL+'languages/'                                                      },
                    {'category':'list_countries_filter', 'title': _('Countries'),         'icon':DEFAULT_ICON, 'url':MAIN_URL+'countries/'                                                      },
                    {'category':'search',                'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON },
                    {'category':'search_history',        'title': _('Search history'),             'icon':DEFAULT_ICON } ]
                    
    POPULAR_TAB = [{'category':'list_items2', 'title': _('All'),        'url':MAIN_URL+'wp-admin/admin-ajax.php?action=noprivate_movies_loop&asec=get_pop&needcap=1'       },
                   {'category':'list_items2', 'title': _('Comedies'),   'url':MAIN_URL+'wp-admin/admin-ajax.php?action=noprivate_movies_loop&asec=get_pop&genre=comedy'    },
                   {'category':'list_items2', 'title': _('Animations'), 'url':MAIN_URL+'wp-admin/admin-ajax.php?action=noprivate_movies_loop&asec=get_pop&genre=animation' },
                   {'category':'list_items2', 'title': _('Dramas'),     'url':MAIN_URL+'wp-admin/admin-ajax.php?action=noprivate_movies_loop&asec=get_pop&genre=drama'     }]
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'YifyTV', 'cookie':'alltubetv.cookie'})
        self.filterCache = {}
        
        self.VIDEO_HOSTINGS_MAP = {"rpd":"https://www.rapidvideo.com/embed/{0}", "vza":"https://vidoza.net/embed-{0}.html", "akv":"https://akvideo.stream/embed-{0}.html", "rpt":"https://www.raptu.com/e/{0}", "lox":"https://vidlox.tv/embed-{0}.html", "vsh":"http://vshare.eu/embed-{0}.html"}
        
    def fillFiltersCache(self):
        printDBG("YifyTV.fillFiltersCache")
        # Fill genres, years, orderby
        if 0 == len(self.filterCache.get('genres', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'files/movies/')
            if sts:
                # genres
                genres = self.cm.ph.getDataBeetwenMarkers(data, '<select name="genre', '</select>', False)[1]
                genres = re.compile('<option[^>]+?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(genres)
                self.filterCache['genres'] = []
                for item in genres:
                    value = item[0]
                    if value == 'Genre':
                        value = ''
                    self.filterCache['genres'].append({'title': self.cleanHtmlStr(item[1]), 'genre':value})
               
                # orderby
                orderby = self.cm.ph.getDataBeetwenMarkers(data, '<select id="orderby"', '</select>', False)[1]
                orderby = re.compile('<option[^>]+?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(orderby)
                self.filterCache['orderby'] = []
                for item in orderby:
                    for val in [(_('descending'), '&order=desc'), (_('ascending'), '&order=asc')]:
                        self.filterCache['orderby'].append({'title': self.cleanHtmlStr(item[1]) + ' [%s]' % val[0], 'orderby':item[0]+val[1]})
                
                # years
                self.filterCache['years'] = [{'title': _('Any')}]
                year = datetime.now().year
                while year >= 1920:
                    self.filterCache['years'].append({'title': str(year), 'year':year})
                    year -= 1
                    
        if 0 == len(self.filterCache.get('languages', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'languages/')
            if sts:
                #languages
                languages = self.cm.ph.getDataBeetwenMarkers(data, '<!-- start content container -->', '</section>', False)[1]
                languages = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(languages)
                self.filterCache['languages'] = []
                for item in languages:
                    self.filterCache['languages'].append({'title': self.cleanHtmlStr(item[1]), 'url':self.getFullUrl(item[0])})
                    
        if 0 == len(self.filterCache.get('countries', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'countries/')
            if sts:
                #countries
                countries = self.cm.ph.getDataBeetwenMarkers(data, '<!-- start content container -->', '</section>', False)[1]
                countries = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(countries)
                self.filterCache['countries'] = []
                for item in countries:
                    self.filterCache['countries'].append({'title': self.cleanHtmlStr(item[1]), 'url':self.getFullUrl(item[0])})
                    
    def listFilters(self, cItem, filter, category):
        printDBG("YifyTV.listFilters")
        tab = self.filterCache.get(filter, [])
        if 0 == len(tab):
            self.fillFiltersCache()
            tab = self.filterCache.get(filter, [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
                    
    def listItems(self, cItem):
        printDBG("YifyTV.listItems")
        
        tmp     = cItem['url'].split('?')
        baseUrl = tmp[0]
        getArgs = []
        if 2 == len(tmp):
            getArgs.append(tmp[1])
        # page
        page = cItem.get('page', 1)
        if page > 1:
            baseUrl += 'page/%s/' % page
        # year
        if '' != cItem.get('year', ''):
            getArgs.append('years=%s' % cItem['year'])
        # genre
        if '' != cItem.get('genre', ''):
            getArgs.append('genre=%s' % cItem['genre'])
        # orderby
        if '' != cItem.get('orderby', ''):
            getArgs.append(cItem['orderby'])
            
        if len(getArgs):
            url = baseUrl + '?' + '&'.join(getArgs)
        else:
            url = baseUrl
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%s/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'var posts = {', '};', False)[1]
        data = '{' + data + '}'
        self._listItems(cItem, data, nextPage)
        
    def listItems2(self, cItem):
        printDBG("YifyTV.listItems2")
        
        url = cItem['url'] + '&num=%s' % cItem.get('page', 1)
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        self._listItems(cItem, data, True)
        
    def _listItems(self, cItem, data, nextPage):
        printDBG("YifyTV.listItems")
        try:
            data = byteify(json.loads(data))
            for item in data['posts']:
                item['url']   = self.getFullUrl(item['link'])
                item['title'] = self.cleanHtmlStr(item['title'])
                desc = ' | '.join([item['year'], item['runtime'], item['genre']])
                desc += '[/br]' + self.cleanHtmlStr(item['post_content'])
                item['desc']  = desc
                item['icon']  = self.getFullUrl(item['image'])
                self.addVideo(item)
        except Exception:
            printExc()
        
        if nextPage:
            page = cItem.get('page', 1)
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("YifyTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        currItem = dict(cItem)
        currItem['url'] = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(currItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("YifyTV.getLinksForVideo [%s]" % cItem)
        
        urlTab = self.cacheLinks.get(cItem['url'], [])
        if len(urlTab): return urlTab
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        trailer = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''<a[^>]+?class=['"]video'''), re.compile('''</a>'''))[1]
        trailerUrl  = self.cm.ph.getSearchGroups(trailer, '''href=['"](https?://[^'^"]+?)['"]''')[0]
        
        imdbid = self.cm.ph.getSearchGroups(data, '''var\s+imdbid\s*=\s*['"]([^'^"]+?)['"]''')[0]
        
        jscode = self.cm.ph.getDataBeetwenMarkers(data, 'jQuery.noConflict();', '</script>', False)[1]
        try:
            jscode = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQp2YXIgd2luZG93ID0gdGhpczsNCnZhciBsb2NhdGlvbiA9IHt9Ow0KbG9jYXRpb24uaG9zdG5hbWUgPSAiJXMiOw0KbG9jYXRpb24udG9TdHJpbmcgPSBmdW5jdGlvbigpew0KICAgICAgICAgICAgICAgICAgICAgIHJldHVybiAiJXMiOw0KICAgICAgICAgICAgICAgICAgICB9Ow0KJXM7DQoNCnByaW50KHdpbmRvdy5wYXJhbWV0cm9zKQ==''') % (self.up.getDomain(self.getMainUrl()), self.getMainUrl(), jscode)                   
            printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
            printDBG(jscode)
            printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            ret = iptv_js_execute( jscode )
            if ret['sts'] and 0 == ret['code']:
                decoded = ret['data'].strip()
                printDBG('DECODED DATA -> [%s]' % decoded)
            data = decoded
        except Exception:
            printExc()
        
        sub_tracks = []
        subLangs = self.cm.ph.getSearchGroups(data, '&sub=([^&]+?)&')[0]
        if subLangs == '':
            tmp = re.compile("\=([^&]*?)&").findall(data)
            for it in tmp:
                for e in ['PT2', 'EN', 'FR', 'ES']:
                    if e in it:
                        subLangs = it
                        break
                if '' != subLangs:
                    break
        
        if subLangs != '':
            subID    = self.cm.ph.getSearchGroups(data, '&id=(tt[^&]+?)&')[0]
            if subID == '':
                subID    = self.cm.ph.getSearchGroups(data, '&pic=(tt[^&]+?)&')[0]
            subLangs = subLangs.split(',')
            for lang in subLangs:
                if subID != '':
                    sub_tracks.append({'title':lang, 'url':'http://yify.bz/player/bajarsub.php?%s_%s' % (subID, lang), 'lang':lang, 'format':'srt'})
        
        data = data.split('&')
        idx = 1
        for item in data:
            tmp = item.split('=')
            if len(tmp)!= 2: continue
            if tmp[1].endswith('enc'):
                url = strwithmeta(tmp[1], {'Referer': cItem['url'], 'sou':tmp[0], 'imdbid':imdbid, 'external_sub_tracks':sub_tracks})
                urlTab.append({'name':_('Mirror') + ' %s' % idx, 'url':url, 'need_resolve':1})
            elif '' != self.VIDEO_HOSTINGS_MAP.get(tmp[0], ''):
                url = self.VIDEO_HOSTINGS_MAP[tmp[0]].format(tmp[1])
                url = strwithmeta(url, {'Referer': cItem['url'], 'imdbid':imdbid, 'external_sub_tracks':sub_tracks})
                urlTab.append({'name':_('Mirror') + ' %s [%s]' % (idx, self.up.getHostName(url)), 'url':url, 'need_resolve':1})
            idx += 1
        
        if len(urlTab):
            self.cacheLinks[cItem['url']] = urlTab
        
        if self.cm.isValidUrl(trailerUrl) and 1 == self.up.checkHostSupport(trailerUrl):
            urlTab.insert(0, {'name':self.cleanHtmlStr(trailer), 'url':trailerUrl, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("YifyTV.getVideoLinks [%s]" % baseUrl)
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if baseUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
        
        urlTab = []
        
        baseUrl = strwithmeta(baseUrl)
        imdbid  = baseUrl.meta.get('imdbid', '')
        sub_tracks = baseUrl.meta.get('external_sub_tracks', [])
        
        header = dict(self.AJAX_HEADER)
        #header['Referer'] = baseUrl.meta['Referer']
        
        if 'sou' in baseUrl.meta:
            souTab = [baseUrl.meta['sou']]
            if souTab[0] == 'pic':
                souTab.append('adr')
            if souTab[0] == 'adr':
                souTab.append('pic')
            
            for sou in souTab:
                post_data = {'fv':'27', 'url':baseUrl, 'sou':sou}
                url = 'https://yify.bz/playerlite/pk/pk/plugins/player_p2.php'
                sts, data = self.cm.getPage(url, {'header':header}, post_data)
                if not sts: return []
                
                try:
                    printDBG(data)
                    if 'jscode' in data:
                        try:
                            data = byteify(json.loads(data))[0]['jscode'][1:-1]#.replace('eval(', 'print(')
                            jscode = '''var iptv_href="%s"; var iptv_domain="%s"; var iptv_video_id="%s"; var iptv_jwpath="%s";\n''' % (self.getMainUrl(), self.up.getDomain(self.getMainUrl()), imdbid, url)
                            jscode += base64.b64decode('''ZnVuY3Rpb24gU2hvd0Rpdigpe31mdW5jdGlvbiBzaG93aUZyYW1lKCl7cHJpbnQoYXJndW1lbnRzWzBdKX1mdW5jdGlvbiBnZXRKd1BhdGgoKXtyZXR1cm4gaXB0dl9qd3BhdGh9ZnVuY3Rpb24gZ2V0X3BhcmFtc19ub19zb3JjZXMoKXtyZXR1cm4gaXB0dl92aWRlb19pZH1mdW5jdGlvbiBzZXRUaW1lb3V0KHQsbil7dGhpcy50cnl1cCgpfXZhciBkb2N1bWVudD17fSx3aW5kb3c9dGhpcyxsb2NhdGlvbj17fTtsb2NhdGlvbi5ocmVmPWlwdHZfaHJlZixsb2NhdGlvbi5ob3N0bmFtZT1pcHR2X2RvbWFpbixsb2NhdGlvbi50b1N0cmluZz1mdW5jdGlvbigpe3JldHVybiBpcHR2X2hyZWZ9LGRvY3VtZW50LmxvY2F0aW9uPWxvY2F0aW9uO3ZhciBlbGVtZW50PWZ1bmN0aW9uKHQpe3RoaXMudGV4dD1mdW5jdGlvbigpe3JldHVybiJub25lIn0sdGhpcy5maXJzdD1mdW5jdGlvbigpe3JldHVybiBuZXcgZWxlbWVudH19LCQ9ZnVuY3Rpb24odCl7cmV0dXJuIG5ldyBlbGVtZW50KHQpfSxwbGF5ZXJtb2RlPSIiLHNvdXJjZVNlbGVjdGVkPTAsc291cmNlcz1be3N1Yl9kZWxheTowLHN1Yl9mYWN0b3I6MX1dOyQuZ2V0PWZ1bmN0aW9uKCl7cmV0dXJuIHByaW50KGFyZ3VtZW50c1swXSkse2RvbmU6U2hvd0RpdixlcnJvcjpTaG93RGl2fX07''')               
                            jscode += 'var iptv_fun = %s; iptv_fun();' % data
                            printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
                            printDBG(jscode)
                            printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                            ret = iptv_js_execute( jscode )
                            if not ret['sts'] or  0 != ret['code']:
                                ret = iptv_js_execute( jscode.replace('eval(', 'print(') )
                            if ret['sts'] and 0 == ret['code']:
                                decoded = ret['data'].strip()
                                printDBG('DECODED DATA -> [%s]' % decoded)
                            data = decoded
                        except Exception:
                            printExc()
                        
                        g3 = self.cm.ph.getSearchGroups(data+'&', '''[&\?]g3=([^&]+?)&''')[0]
                        emb = self.cm.ph.getSearchGroups(data+'&', '''[&\?]emb=([^&^\*]+?)[&\*]''')[0]
                        if emb != '': data = urllib.unquote(emb)
                        if g3 != '':
                            post_data = {'fv':'0', 'g3':urllib.unquote(g3)}
                            url = 'https://yify.bz/playerlite/pk/pk/plugins/player_g3.php'
                            sts, data = self.cm.getPage(url, {'header':header}, post_data)
                            if not sts: return []
                            printDBG(data)
                        elif self.cm.isValidUrl(data) and 1 == self.up.checkHostSupport(data):
                            urlTab = self.up.getVideoLinkExt(data)
                            break                            
                        else:
                            if 'showiFrame(' in data:
                                url = urllib.unquote(self.cm.ph.getDataBeetwenMarkers(data, "emb='+'", "'", False)[1])
                                tmp = url.split('sub.file')
                                url = tmp[0]
                                subTrack = urllib.unquote(tmp[1])
                                if url.startswith('//'):
                                    url = 'http:' + url
                                if subTrack.startswith('//'):
                                    subTrack = 'http:' + subTrack
                                tmpUrlTab = self.up.getVideoLinkExt(url)
                                if self.cm.isValidUrl(subTrack):
                                    format = subTrack[-3:]
                                    for idx in range(len(tmpUrlTab)):
                                        tmpUrlTab[idx]['url'] = strwithmeta(tmpUrlTab[idx]['url'], {'external_sub_tracks':[{'title':'', 'url':subTrack, 'lang':'en', 'format':format}]})
                                urlTab.extend(tmpUrlTab)
                                printDBG(urlTab)
                                break
                                
                            if 'sources[sourceSelected]["paramId"]' in data:
                                data = data.replace('"+"', '').replace(' ', '')
                                paramSite = self.cm.ph.getSearchGroups(data, 'sources\[sourceSelected\]\["paramSite"\]="([^"]+?)"')[0]
                                data = self.cm.ph.getSearchGroups(data, 'sources\[sourceSelected\]\["paramId"\]="([^"]+?)"')[0]
                                printDBG('data ------------------------- [%s]' % data)
                                if data.startswith('enc'):
                                    encrypted = base64.b64decode(data[3:])
                                    key = unhexlify(base64.b64decode('MzAzOTM4NzMzOTM3MzU0MTMxMzIzMzczMzEzMzM1NjQ2NDY2Njc3NzQ4MzczODM0MzczNTMzMzQzNjcyNjQ3Nw=='))
                                    iv = unhexlify(base64.b64decode('NWE0MTRlMzEzNjMzNjk2NDZhNGM1MzUxMzU0YzY0MzU='))
                                    cipher = AES_CBC(key=key, padding=noPadding(), keySize=32)
                                    data = cipher.decrypt(encrypted, iv).split('\x00')[0]
                                    if 'ucl' == paramSite:
                                        urlTab.extend( self.up.getVideoLinkExt("https://userscloud.com/embed-" + data + "-1280x534.html") )
                                    elif 'tus' == paramSite:
                                        urlTab.extend( self.up.getVideoLinkExt("https://tusfiles.net/embed-" + data + "-1280x534.html?v=34") )
                                    elif 'up' == paramSite:
                                        urlTab.extend( self.up.getVideoLinkExt("http://uptobox.com/" + data) )
                                    break
                        
                    data = byteify(json.loads(data))
                    for item in data:
                        #printDBG('++++++++++++++++++++++\n%s\n++++++++++++++++++++++' % item)
                        if (item.get('type', '').startswith('video/') or item.get('type', '').startswith('application/x-shockwave-flash')) and self.cm.isValidUrl(item.get('url', '')):
                            urlTab.append({'name':'{0}x{1}'.format(item.get('height', ''), item.get('width', '')), 'url':item['url'], 'need_resolve':0})
                except Exception:
                    SetIPTVPlayerLastHostError('The Mirror is broken.\nIf available you can choose other source.')
                    printExc()
                    return []
                
                if len(urlTab): break;
            
        elif self.cm.isValidUrl(baseUrl):
            urlTab = self.up.getVideoLinkExt(baseUrl)
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(urlTab)
        
        for idx in range(len(urlTab)):
            subs = list(strwithmeta(urlTab[idx]['url']).meta.get('external_sub_tracks', []))
            subs.extend(sub_tracks)
            urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], {'external_sub_tracks':subs})
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(urlTab)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        
        title = cItem['title']
        icon  = cItem['image']
        desc  = cItem['post_content']
        otherInfo = {}
        otherInfo['year']     = cItem['year']
        otherInfo['duration'] = cItem['runtime']
        otherInfo['genre']    = cItem['genre']
        otherInfo['director'] = cItem['director']
        otherInfo['actors']   = cItem['actors']
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        self.cacheLinks = {}
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_popular':
            self.listsTab(self.POPULAR_TAB, self.currItem)
    #MOVIES
        elif category == 'list_countries_filter':
            self.listFilters(self.currItem, 'countries', 'list_genres_filter')
        elif category == 'list_languages_filter':
            self.listFilters(self.currItem, 'languages', 'list_genres_filter')
        elif category == 'list_genres_filter':
            self.listFilters(self.currItem, 'genres', 'list_year_filter')
        elif category == 'list_year_filter':
            self.listFilters(self.currItem, 'years', 'list_orderby_filter')
        elif category == 'list_orderby_filter':
            self.listFilters(self.currItem, 'orderby', 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'list_items2':
            self.listItems2(self.currItem)
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
        CHostBase.__init__(self, YifyTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def withArticleContent(self, cItem):
        if cItem['type'] != 'video':
            return False
        return True

