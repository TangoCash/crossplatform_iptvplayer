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
    
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        params.update({'header':HTTP_HEADER})
        
        proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote_plus(url))
        params['header']['Referer'] = proxy
        url = proxy
        #sts, data = self.cm.getPage(url, params, post_data)
        #printDBG(data)
        return self.cm.getPage(url, params, post_data)
            
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
        url = baseUrl + '?' + '&'.join(getArgs)
        
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
                item['desc']  = self.cleanHtmlStr(item['post_content'])
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
        
    def __saveGet(self, b, a):
        try:
            return b[a]
        except Exception:
            return 'pic'
            
    def unpackJS(self, data, name):
        data = data.replace('Math.min', 'min').replace(' + (', ' + str(').replace('String.fromCharCode', 'chr').replace('return b[a]', 'return saveGet(b, a)')
        printDBG(data)
        
        def justRet(data):
            return data
        
        try:
            paramsAlgoObj = compile(data, '', 'exec')
        except Exception:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''

        try:
            vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote, 'min':min, 'saveGet':self.__saveGet, 'justRet':justRet}
            vLocals = { name: None }
            exec( data, vGlobals, vLocals )
        except Exception:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except Exception:
            printExc('decryptPlayerParams EXCEPTION')
        return ''
        
    def getPyCode(self, data):
        printDBG('getPyCode')
        self.pyCode = ''
        globalTabCode = []
        data = data.replace('"]"', '"--zz--"')
        tmp = re.compile('var([^;]+?)=[^;]*?(\[[^\]]+?\]);').findall(data)
        for item in tmp:
            var = item[0].strip()
            val = item[1].strip()
            if var == '': continue
            if val == '': continue
            globalTabCode.append('%s = %s' % (var, val))
        globalTabCode = '\n'.join( globalTabCode )
        globalTabCode = globalTabCode.replace('"--zz--"', '"]"')
        data = data.replace('"--zz--"', '"]"')
        
        self.evalNum = 0
        def evalSimple(data):
            dat = data.group(0)
            funName = 'eval%d()' % self.evalNum
            funData = 'def %s:' % funName
            self.evalNum += 1
            #printDBG("----------------------\n%s\n------------------" % dat)
            cond   = self.cm.ph.getDataBeetwenMarkers(dat, 'if', '{', False)[1]
            body   = self.cm.ph.getAllItemsBeetwenMarkers(dat, 'return', ';', False)
            funData += '\n\tif %s:' % cond.strip()
            funData += '\n\t\treturn str(%s)' % body[0]
            funData += '\n\telse:'
            funData += '\n\t\treturn str(%s)' % body[1]          
            funData += '\n'
            
            self.pyCode += funData
            #printDBG("====================\n%s\n====================" % funData)
            return funName
        
        data = re.sub('\(eval\("[^"]+?"\)\)', evalSimple, data)
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, 'eval(', ");", False)
        if sts:
            funName = 'eval%d()' % self.evalNum
            funData = 'def justRet%s:' % funName
            self.evalNum += 1
            funData += '\n\treturn ' + tmp.strip()
            funData += '\n'
            self.pyCode += funData
            args = funName
        else:
            args = self.cm.ph.getDataBeetwenMarkers(data, 'parseRes2', ";})", False)[1]
        
        data2 = data.split('\n')
        data = []
        for item in data2:
            if 'try{' in item: continue
            if '}catch' in item: continue
            data.append(item)
        data = '\n'.join(data)
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        
        pyCode = self.pyCode
        for item in funData:
            funHeader = item[0]
            
            funBody = item[1]
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                if len(ins) and ins[-1] not in [')', ']', '"']:
                    ins += '()'
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
        return globalTabCode, pyCode, args
    
    def getLinksForVideo(self, cItem):
        printDBG("YifyTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
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
                url = strwithmeta(tmp[1], {'external_sub_tracks':sub_tracks})
                url.meta['Referer'] = cItem['url']
                url.meta['sou'] = tmp[0]
                urlTab.append({'name':_('Mirror') + ' %s' % idx, 'url':url, 'need_resolve':1})
                idx += 1
        return urlTab
        
    def _evalJscode(self, data):
        try:
            data = byteify(json.loads(data))
            code = data[0]['jscode']
            tmpData = ''
            for decFun in [VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2, SAWLIVETV_decryptPlayerParams]:
                tmpData = unpackJSPlayerParams(code, decFun, 0)
                if '' != tmpData:
                    printDBG(tmpData)
                    return tmpData
            m1 = '(function (){'
            code = code[len(m1):]
            globalTabCode, pyCode, args = self.getPyCode(code)
            pyCode = 'def retA():\n\t' + globalTabCode.replace('\n', '\n\t') + '\n\t' + pyCode.replace('\n', '\n\t') + ('\n\treturn justRet%s\n' % args) + 'param = retA()'
            printDBG(pyCode)
            data = self.unpackJS(pyCode, 'param')
            printDBG(data)
        except Exception:
            printExc()
        return data
        
    def getVideoLinks(self, baseUrl):
        printDBG("YifyTV.getVideoLinks [%s]" % baseUrl)
        
        urlTab = []
        sub_tracks = strwithmeta(baseUrl).meta.get('external_sub_tracks', [])
        
        header = dict(self.AJAX_HEADER)
        header['Referer'] = baseUrl.meta['Referer']
        
        souTab = [baseUrl.meta.get('sou', '')]
        if souTab[0] == 'pic':
            souTab.append('adr')
        if souTab[0] == 'adr':
            souTab.append('pic')
        for sou in souTab:
            post_data = {'fv':'18', 'url':baseUrl, 'sou':sou}
            url = 'http://yify.bz/playerlite/pk/pk/plugins/player_p2.php'
            sts, data = self.cm.getPage(url, {'header':header}, post_data)
            if not sts: return []
            #printDBG('>>>>>>>>>>>>>>>>>>>>>>>\n%s\n<<<<<<<<<<<<<<<' % data)
            try:
                printDBG(data)
                if 'jscode' in data:
                    #printDBG("+++++++++++++++++++++++++++++++++++++++++")
                    #printDBG(data)
                    #printDBG("+++++++++++++++++++++++++++++++++++++++++")
                    #return []
                    data = self._evalJscode(data)
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
            if len(urlTab): break;
        
        if False: 
            videoUrl = url
            if url.startswith('//'):
                videoUrl = 'http:' + videoUrl
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(urlTab)
        
        for idx in range(len(urlTab)):
            subs = strwithmeta(urlTab[idx]['url']).meta.get('external_sub_tracks', [])
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

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('yifytvlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

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

    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): 
            return RetHost(retCode, value=retlist)

        cItem = self.host.currList[Index]
        if cItem.get('type') == 'video':
            hList = self.host.getArticleContent(cItem)
            for item in hList:
                title      = item.get('title', '')
                text       = item.get('text', '')
                images     = item.get("images", [])
                othersInfo = item.get('other_info', '')
                retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
                retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
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
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem
