# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, rm, GetTmpDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
from copy import deepcopy
import base64
from Components.config import config, ConfigText, getConfigListEntry
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
config.plugins.iptvplayer.naszekinotv_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.naszekinotv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":",   config.plugins.iptvplayer.naszekinotv_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.naszekinotv_password))
    return optionList
###################################################

def gettytul():
    return 'https://nasze-kino.tv/'

class NaszeKinoTv(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'nasze-kino.tv.com', 'cookie':'nasze-kino.tv.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'https://www.nasze-kino.tv/'
        self.DEFAULT_ICON_URL = 'https://raw.githubusercontent.com/podpis/kodi/master/zips/plugin.video.naszekinotv/icon.png'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.cacheLinks    = {}
        self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.cacheSeriesLetter = []
        self.cacheSetiesByLetter = {}
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def getFullIconUrl(self, url, currUrl=None):
        url = CBaseHostClass.getFullIconUrl(self, url.strip(), currUrl)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE, ['PHPSESSID', "cf_clearance"])
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
    
    def listMainMenu(self, cItem):
        printDBG("NaszeKinoTv.listMainMenu")
        
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        MAIN_CAT_TAB = [{'category':'sections',       'title': 'Strona Główna',    'url':self.getMainUrl()}, 
                        {'category':'movies',         'title': 'Filmy Online',     'url':self.getFullUrl('/filmy-online/')}, 
                        {'category':'series',         'title': 'Seriale Online',   'url':self.getFullUrl('/seriale-online/')}, 
                        {'category':'sections',       'title': 'Dla Dzieci',       'url':self.getFullUrl('/dla-dzieci/')}, 
                        {'category':'raiting',        'title': 'Ranking',          'url':self.getFullUrl('/ranking')}, 
                        {'category':'search',         'title': _('Search'),        'search_item':True}, 
                        {'category':'search_history', 'title': _('Search history')},]
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def _parseSectionItems(self, nextCategory, data):
        printDBG("NaszeKinoTv._parseSectionItems")
        retItems = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0])
            if '/serial' not in url and '/film' not in url: continue
            icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0])
            title = ''
            desc = ''
            tab = []
            for m in ['title', 'view', 'year', 'info', 'description']:
                t = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', m), ('</div', '>'), False)[1])
                if t == '': continue
                if m == 'title': title = t
                elif m == 'description': desc = t
                else: tab.insert(0, t)
            if title == '': continue
            desc = [desc]
            if len(tab): desc.insert(0, ' | '.join(tab))
            retItems.append({'name':'category', 'type':'category', 'good_for_fav':True, 'category':nextCategory, 'url':url, 'title':title, 'desc':'[/br]'.join(desc), 'icon':icon})
        return retItems
        
    def listSections(self, cItem, nextCategory1, nextCategory2, skipSubSections=False):
        printDBG("NaszeKinoTv.exploreItem [%s]" % cItem)
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        curl = data.meta['url']
        self.setMainUrl(curl)
        
        data = data.split('</footer>', 1)[0]
        
        # main section
        sTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'headline'), ('</div', '>'), False)[1])
        if sTitle != '':
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'item-list'), ('<div', '>', 'row'), False)[1]
            tmp = self._parseSectionItems(nextCategory2, tmp)
            if len(tmp):
                nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'pagination'), ('</ul', '>'), False)[1]
                nextPage = self.cm.ph.getSearchGroups(nextPage, '''(<a[^>]+?pagenumber=['"]%s['"][^>]*?>)''' % (page + 1))[0]
                nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^"^']+?)['"]''')[0], curl)
                if nextPage != '':  tmp.append({'name':'category', 'type':'category', 'category':cItem['category'], 'url':nextPage, 'title':_('Next page'), 'page':page+1})
                self.addDir({'name':'category', 'category':nextCategory1, 'title':sTitle, 'sub_items':tmp})
        
        if page == 1 and not skipSubSections:
            data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'col-md'), ('<div', '>', '"row"'), False)
            for tmp in data:
                sTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<h3', '</h3>')[1])
                tmp = self._parseSectionItems(nextCategory2, tmp)
                if len(tmp): self.addDir({'name':'category', 'category':nextCategory1, 'title':sTitle, 'sub_items':tmp})
            
    def listSubItems(self, cItem):
        printDBG("NaszeKinoTv.listSubItems")
        self.currList = cItem['sub_items']
        
    def listMovies(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listMovies [%s]" % cItem)
        cItem = dict(cItem)
        cItem['category'] = 'sections'
        self.listSections(cItem, 'list_sub_items', 'explore_item')
        self.addDir({'name':'category', 'type':'category', 'category':nextCategory, 'url':cItem['url'], 'title':_('Filters')})
        
    def listSeries(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listSeries [%s]" % cItem)
        self.listSections(cItem, 'list_sub_items', 'explore_item')
        if 1 == len(self.currList): self.currList[0]['title'] = 'Ostatnio dodane seriale'
        self.addDir({'name':'category', 'type':'category', 'category':nextCategory, 'url':cItem['url'], 'title':_('A-Z')})
    
    def listAZ(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listAZ")
        self._listLetters(cItem, nextCategory, self.cacheSeriesLetter, self.cacheSetiesByLetter)
        
    def listByLetter(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listByLetter")
        self._listByLetter(cItem, nextCategory, self.cacheSetiesByLetter)
        
    def _listLetters(self, cItem, nextCategory, cacheLetter, cacheByLetter):
        printDBG("NaszeKinoTv._listLetters")
        
        if 0 == len(cacheLetter):
            del cacheLetter[:]
            cacheByLetter.clear()
            
            sts, data = self.getPage(cItem['url'])
            if not sts: return

            data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'series-list'), ('</ul', '>'))[1]
            data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>'), ('</a', '>'))
            for item in data:
                url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
                if url == '': continue
                title = self.cleanHtmlStr( item )
                if title == '': continue
                letter = url.split('/')[-1]
                if letter == '': letter = title[0]
                else: letter = letter[0]
                letter = letter.decode('utf-8').upper().encode('utf-8')
                if not letter.decode('utf-8').isalpha(): letter = '#'
                
                if letter not in cacheLetter:
                    cacheLetter.append(letter)
                    cacheByLetter[letter] = []
                cacheByLetter[letter].append({'title':title, 'url':url, 'desc':'', 'icon':url + '?fake=need_resolve.jpeg'})
            
        for letter in cacheLetter:
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':letter, 'desc':'', 'f_letter':letter})
            self.addDir(params)
    
    def _listByLetter(self, cItem, nextCategory, cacheByLetter):
        printDBG("NaszeKinoTv._listByLetter")
        letter = cItem['f_letter']
        tab = cacheByLetter[letter]
        cItem = dict(cItem)
        cItem.update({'good_for_fav':True, 'category':nextCategory, 'desc':''})
        self.listsTab(tab, cItem)
        
    def _fillCacheFilters(self, cItem):
        printDBG("NaszeKinoTv._fillCacheFilters")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                value = self.cm.ph.getSearchGroups(item, marker + '''=['"]([^"^']+?)['"]''')[0]
                title = self.cleanHtmlStr(item)
                self.cacheFilters[key].append({'title':title, key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('--All--')})
                self.cacheFiltersKeys.append(key)
        
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<ul', '>', 'multiple-select'), ('</ul', '>'))
        for item in tmp:
            key = self.cm.ph.getSearchGroups(item, '''id=['"]filter\-([^'^"]+?)['"]''')[0]
            item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')
            addFilter(item, 'data\-id', key, True)
            
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<ul', '>', 'single-select'), ('</ul', '>'))
        for item in tmp:
            key = self.cm.ph.getSearchGroups(item, '''id=['"]filter\-([^'^"]+?)['"]''')[0]
            item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')
            addFilter(item, 'data\-sort', key, False)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listFilters")
        cItem = dict(cItem)
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self._fillCacheFilters(cItem)
        if f_idx >= len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listItems [%s]" % cItem)
        if 1 == cItem.get('page', 1):
            filters = []
            for key in self.cacheFiltersKeys:
                baseKey = key[2:] # "f_"
                if key not in cItem: continue
                if cItem[key].startswith(baseKey): value = cItem[key]
                else: value = baseKey + ':' + cItem[key]
                filters.append(value)
            url = cItem['url']
            if not url.startswith('/'): url += '/'
            cItem['url'] = url + '/'.join(filters) + '/'
        
        self.listSections(cItem, 'list_sub_items', nextCategory, True)
        if 1 == len(self.currList): self.listSubItems(self.currList[0])
        
    def listRaitingItems(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.listRaitingItems")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '"ranking" '), ('<footer', '>'))[1]
        self.currList = self._parseSectionItems(nextCategory, data)

    def exploreItem(self, cItem, nextCategory):
        printDBG("NaszeKinoTv.exploreItem [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<p', '>', 'description'), ('</p', '>'))[1])
        posterData = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'single-poster'), ('<img', '>'))[1]
        icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(posterData, '<img[^>]+?src="([^"]+?\.(:?jpe?g|png)(:?\?[^"]+?)?)"')[0], cUrl)
        
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'trailer'), ('</div', '>'))[1]
        url = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
        if url != '':
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':'%s - %s' % (cItem['title'], _('trailer')), 'url':url, 'icon':icon, 'desc':desc})
            self.addVideo(params)
            
        if '/film/' in cUrl:
            params = dict(cItem)
            params.update({'type':'video', 'icon':icon, 'desc':desc})
            self.currList.insert(0, params)
        else:
            if 'episode-list' not in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(posterData, '''href=['"]([^'^"]*?serial\-online[^'^"]+?)['"]''')[0])
                if url != '':
                    sts, data = self.getPage(url)
                    if not sts: return
                elif 'link-to-video' in data:
                    params = dict(cItem)
                    params.update({'icon':icon, 'desc':desc})
                    self.addVideo(params)
                    return
            seriesTitle = self.cleanHtmlStr(self.cm.ph.getSearchGroups(data, '''<meta[^>]+?property=['"]og\:title['"][^>]+?content=['"]([^"^']+?)['"]''')[0])
            if seriesTitle == '': seriesTitle = cItem['title']
            data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'episode-list'), ('<', '>', '/dodaj-odcinek/'), False)[1]
            data = data.split('</ul>')
            sId = 0
            for sItem in data:
                sTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(sItem, '<span', '</span>')[1])
                sItem = self.cm.ph.getAllItemsBeetwenMarkers(sItem.split('<ul', 1)[-1], '<li', '</li>')
                episodesTab = []
                for item in sItem:
                    title = self.cleanHtmlStr(item)
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    episodesTab.append({'good_for_fav':True, 'type':'video', 'title':'%s - %s' % (seriesTitle, title), 'url':url, 'icon':icon})
                sId += 1
                if len(episodesTab):
                    self.addDir({'good_for_fav':False, 'name':'category', 'type':'category', 'category':nextCategory, 'sub_items':episodesTab, 'title':sTitle, 'icon':icon, 'desc':desc})
        
            if 1 == len(self.currList):
                self.listSubItems(self.currList[0])
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("NaszeKinoTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = self.getFullUrl('/wyszukiwarka?phrase=') + urllib.quote_plus(searchPattern)
        sts, data = self.getPage(url)
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'advanced-search'), ('<footer', '>'))[1]
        if searchType == 'movie': m1 = '<h3>Filmy</h3>'
        else: m1 = '<h3>Seriale</h3>'
        data = re.compile('''<div[^>]+?class=['"]row['"][^>]*?>''').split(data)
        for idx in range(len(data)):
            if m1 in data[idx] and (idx+1) < len(data):
                self.currList = self._parseSectionItems('explore_item', data[idx+1])
                break
        
    def getLinksForVideo(self, cItem):
        printDBG("NaszeKinoTv.getLinksForVideo [%s]" % cItem)
        self.tryTologin()
        
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        
        cacheKey = cItem['url']
        cacheTab = self.cacheLinks.get(cacheKey, [])
        if len(cacheTab): return cacheTab
        
        self.cacheLinks = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        paramsUrl = dict(self.defaultParams)
        paramsUrl['header'] = dict(paramsUrl['header'])
        
        ##############################################################################################
        while sts and 'captcha-info' in data:
            # parse form data
            data = self.cm.ph.getDataBeetwenMarkers(data, 'captcha-info', '</form>')[1]
            
            captchaTitle = self.cm.ph.getAllItemsBeetwenMarkers(data, '<p', '</p>')
            if len(captchaTitle): captchaTitle = self.cleanHtmlStr(captchaTitle[-1])
            else: captchaTitle = ''
            
            sendLabel = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<button', '</button>')[1])
            captchaLabel = self.cleanHtmlStr(self.cm.ph.getSearchGroups(data, '''\splaceholder=['"]([^'^"]+?)['"]''')[0])
            captchaLabel = '%s %s' % (sendLabel, captchaLabel)
            
            if captchaLabel.strip() == '': captchaLabel = _('Captcha')
            if captchaTitle == '': captchaTitle = captchaLabel
            sendLabel = _('Send')
            
            imgUrl = self.getFullIconUrl(self.cm.ph.getSearchGroups(data, '<img[^>]+?src="([^"]+?\.(:?jpe?g|png)(:?\?[^"]+?)?)"')[0], cUrl)
            
            actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, 'action="([^"]+?)"')[0], cUrl)
            if actionUrl == '': actionUrl = cUrl
            tmp = re.compile('''<input[^>]+?>''').findall(data)
            printDBG(tmp)
            captcha_post_data = {}
            for it in tmp:
                val = self.cm.ph.getSearchGroups(it, '''\svalue=['"]?([^'^"^\s]+?)['"\s]''')[0].strip()
                name = self.cm.ph.getSearchGroups(it, '''\sname=['"]([^'^"]+?)['"]''')[0]
                captcha_post_data[name] = val
            
            header = dict(self.HTTP_HEADER)
            header['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
            params = dict(self.defaultParams)
            params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':header} )
            filePath = GetTmpDir('.iptvplayer_captcha.jpg')
            rm(filePath)
            ret = self.cm.saveWebFile(filePath, imgUrl.replace('&amp;', '&'), params)
            if not ret.get('sts'):
                SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                return []
            params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
            params['accep_label'] = sendLabel
            params['title'] = captchaLabel
            params['status_text'] = captchaTitle
            params['status_text_hight'] = 200
            params['with_accept_button'] = True
            params['list'] = []
            item = deepcopy(IPTVMultipleInputBox.DEF_INPUT_PARAMS)
            item['label_size'] = (660,110)
            item['input_size'] = (680,25)
            item['icon_path'] = filePath
            item['title'] = _('Answer')
            item['input']['text'] = ''
            params['list'].append(item)
            params['vk_params'] = {'invert_letters_case':True}

            ret = 0
            retArg = self.sessionEx.waitForFinishOpen(IPTVMultipleInputBox, params)
            printDBG(retArg)
            if retArg and len(retArg) and retArg[0]:
                printDBG(retArg[0])
                captcha_post_data['captcha'] = retArg[0][0]
                paramsUrl['header']['Referer'] = cUrl
                sts, data = self.cm.getPage(actionUrl, paramsUrl, captcha_post_data)
                if sts: cUrl = data.meta['url'] 
                else: return []
            else:
                return []
        ##############################################################################################
        
        msg = self.cm.ph.getDataBeetwenNodes(data, ('', '>', 'alert-info'), ('</div', '>'), False)[1]
        SetIPTVPlayerLastHostError(msg)
        
        retTab = []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<tbody', '>'), ('</tbody', '>'), False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr', '</tr>', False)
        for item in data:
            url = ''
            tmp = ph.getattr(item, 'data-iframe')
            try:
                tmp = json_loads(base64.b64decode(tmp))['src']
                url = self.getFullUrl(tmp)
            except Exception:
                printExc()
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0])
            if url == '': continue
            item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>')
            name = []
            for t in item:
                t = self.cleanHtmlStr(t)
                if t != '': name.append(t)
            name = ' | '.join(name)
            retTab.append({'name':name, 'url':strwithmeta(url, {'Referer':cUrl}), 'need_resolve':1})
        
        if len(retTab):
            self.cacheLinks[cacheKey] = retTab
        return retTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("NaszeKinoTv.getVideoLinks [%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if baseUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name'] + '*'
                        break
                        
        if 1 == self.up.checkHostSupport(baseUrl):
            return self.up.getVideoLinkExt(baseUrl)
                        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(urlParams['header'])
        urlParams['header']['Referer'] = baseUrl.meta.get('Referer', self.getMainUrl())
        
        sts, data = self.getPage(baseUrl, urlParams)
        if not sts: return
        
        videoUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
        videoUrl = strwithmeta(videoUrl, {'Referer':urlParams['header']['Referer']})
        return self.up.getVideoLinkExt(videoUrl)
        
    def getArticleContent(self, cItem, data=None, cUrl=''):
        printDBG("NaszeKinoTv.getArticleContent [%s]" % cItem)
        
        retTab = []
        
        otherInfo = {}
        
        if data == None:
            sts, data = self.getPage(cItem['url'])
            if not sts: return []
            cUrl = data.meta['url']
            self.setMainUrl(cUrl)
            
        if '/odcinek' in cUrl and cItem['type'] == 'category':
            posterData = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'single-poster'), ('<img', '>'))[1]
            url = self.getFullUrl(self.cm.ph.getSearchGroups(posterData, '''href=['"]([^'^"]*?serial\-online[^'^"]+?)['"]''')[0])
            
            sts, data = self.getPage(url)
            if not sts: return []
            cUrl = data.meta['url']
            self.setMainUrl(cUrl)
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'item-headline'), ('<footer', '>'))[1] #, 'clearfix'
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<p', '>', 'description'), ('</p', '>'))[1])
        icon = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'single-poster'), ('<img', '>'))[1]
        icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(icon, '<img[^>]+?src="([^"]+?\.(:?jpe?g|png)(:?\?[^"]+?)?)"')[0], cUrl)
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'item-headline'), ('</div', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenNodes(tmp, ('<h', '>'), ('</h', ''), False)
        title = []
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': title.append(t)
        title = ' '.join(title)
        
        keysMap = {'Odsłony:':          'views',
                   'Kategoria:':        'genre',
                   'Kraj:':             'country',
                   'Dodał:':            'added',
                   'director':          'director',
                   'productionCompany': 'writer',
                   'actors':            'actors',}
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'info'), ('</div', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<ul', '</ul>')
        for item in tmp:
            item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')
            tab = []
            for it in item:
                it = self.cleanHtmlStr(it)
                tab.append(it)
            if len(tab) > 1:
                key = keysMap.get(tab[0], '')
                otherInfo[key] = ', '.join(tab[1:])
        
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data.split('</p>', 1)[-1], ('<h4', '</h4>'), ('</ul', '>'))
        for item in tmp:
            key = self.cm.ph.getSearchGroups(item, '''itemprop=['"]([^'^"]+?)['"]''')[0]
            key = keysMap.get(key, '')
            if key == '': continue
            item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<li', '</li>')
            tab = []
            for it in item:
                it = self.cleanHtmlStr(it)
                tab.append(it)
            if len(tab): otherInfo[key] = ', '.join(tab)
        
        item = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<', '>', 'ratingValue'), ('</div', '>'))[1])
        if item != '': otherInfo['rating'] = item
        item = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<sup', '</sup>')[1])
        if item != '': otherInfo['year'] = item
        
        if title == '': title = cItem['title']
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        #if desc == '':  desc = cItem.get('desc', '')
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def tryTologin(self):
        printDBG('tryTologin start')
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.naszekinotv_login.value or\
            self.password != config.plugins.iptvplayer.naszekinotv_password.value:
        
            self.login = config.plugins.iptvplayer.naszekinotv_login.value
            self.password = config.plugins.iptvplayer.naszekinotv_password.value
            
            sts, data = self.getPage(self.getFullUrl('/profil'))
            if not sts: return False
            
            login = self.cm.ph.getSearchGroups(data, '''alogowany jako:([^<]+?)<''')[0].strip()

            self.loggedIn = False
            if '' == self.login.strip() or '' == self.password.strip():
                if login != '':
                    rm(self.COOKIE_FILE)
                return False
            elif self.login.strip() == login:
                self.loggedIn = True
                return True
            
            rm(self.COOKIE_FILE)
            
            url = self.getFullUrl('/logowanie')
            sts, data = self.getPage(url)
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'post'), ('</form', '>'))
            if not sts: return False
            
            actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
            if actionUrl == '': actionUrl = url
            
            post_data = {}
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
            tmp.extend(self.cm.ph.getAllItemsBeetwenMarkers(data, '<button', '>'))
            for item in tmp:
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                post_data[name] = value
            
            post_data.update({'login':self.login, 'password':self.password, 'remember':'on'})
            
            httpParams = dict(self.defaultParams)
            httpParams['header'] = dict(httpParams['header'])
            httpParams['header']['Referer'] = url
            sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
            printDBG(data)
            if sts and '/wylogowanie' in data:
                printDBG('tryTologin OK')
                self.loggedIn = True
            else:
                if sts:
                    errMsg = []
                    tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'alert-danger'), ('</div', '>'), False)
                    for it in tmp:
                        errMsg.append(self.cleanHtmlStr(it))
                else:
                    errMsg = [_('Connection error.')]
                self.sessionEx.open(MessageBox, _('Login failed.') + '\n' + '\n'.join(errMsg), type = MessageBox.TYPE_ERROR, timeout = 10)
                printDBG('tryTologin failed')
        return self.loggedIn
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||| name[%s], category[%s] " % (name, category) )
        self.cacheLinks = {}
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
    #SECTIONS
        elif category == 'sections':
            self.listSections(self.currItem, 'list_sub_items', 'explore_item')
            if 1 == len(self.currList): self.listSubItems(self.currList[0])
        elif category == 'list_sub_items':
            self.listSubItems(self.currItem)
    #MOVIES
        elif category == 'movies':
            self.listMovies(self.currItem, 'list_filters')
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
    #SERIES
        elif category == 'series':
            self.listSeries(self.currItem, 'a_z')
        elif category == 'a_z':
            self.listAZ(self.currItem, 'list_by_letter')
        elif category == 'list_by_letter':
            self.listByLetter(self.currItem, 'explore_item')
    #RAITING
        elif category == 'raiting':
            self.listRaitingItems(self.currItem, 'explore_item')
        
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_sub_items')
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
        CHostBase.__init__(self, NaszeKinoTv(), True, [])
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Movies"), "movie"))
        searchTypesOptions.append((_("Series"), "serie"))
        return searchTypesOptions
        
    def withArticleContent(self, cItem):
        if '.nasze-kino.' in cItem.get('url', '') and \
           ('video' == cItem.get('type', '') or \
            'explore_item' == cItem.get('category', '')):
            return True
        else: return False
    