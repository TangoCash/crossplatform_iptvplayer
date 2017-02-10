# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

#ToDo
#    Błąd przy wyszukiwaniu filmów z polskimi znakami

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.libs.anyfilesapi import AnyFilesVideoUrlExtractor
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, rm
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################
# FOREIGN import
###################################################
import re, string
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
config.plugins.iptvplayer.anyfilespl_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.anyfilespl_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Anyfiles.pl " + _('login:'), config.plugins.iptvplayer.anyfilespl_login))
    optionList.append(getConfigListEntry("Anyfiles.pl " + _('password:'), config.plugins.iptvplayer.anyfilespl_password))
    return optionList
###################################################

def gettytul():
    return 'AnyFiles'

class AnyFiles(CBaseHostClass):
    MAIN_URL = 'http://anyfiles.pl'
    SEARCH_URL = MAIN_URL + '/search.jsp'
    DEFAULT_ICON_URL = 'http://anyfiles.pl/css/images/logo.png'
    MAIN_CAT_TAB = [{'category':'list_movies',        'title': _('Most Popular'), 'url':MAIN_URL + '/all.jsp'},
                    {'category':'genres',             'title': _('Genres'),       'url':MAIN_URL + '/pageloading/index-categories-loader.jsp'},
                    {'category':'list_movies',        'title': _('Most Popular'), 'url':MAIN_URL + '/all.jsp'},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AnyFiles', 'cookie':'anyfiles.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.anyfiles = AnyFilesVideoUrlExtractor()

    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("AnyFiles.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listGenres(self, cItem, category):
        printDBG("AnyFiles.listGenres")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return 
        data = data.split('<div class="thumbnail"')
        if len(data): del data[0]
        
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            title = self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1]
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', 1)[0]
            params = dict(cItem)
            params.update( {'category':category, 'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon)} )
            self.addDir(params)
            
    def listMovies(self, cItem, m1='<div  class="kat-box-div">', m2='<script type="text/javascript">', reTitle='class="kat-box-name">([^<]+?)<'):
        printDBG("AnyFiles.listMovies")
        
        cItem = dict(cItem)
        
        page = cItem.get('page', 1)
        if 1 == page: 
            if 'priv_search' not in cItem:
                sts, data = self.cm.getPage(self._getFullUrl('/all.jsp?reset_f=true'), self.defaultParams)
                if not sts: return 
            url = cItem['url']
        else: url = cItem['url'] + str(page * cItem['page_size'])
            
        post_data = cItem.get('post_data', None)
        httpParams = dict(self.defaultParams)
        ContentType =  cItem.get('Content-Type', None)
        Referer = cItem.get('Referer', None)
        if None != Referer: httpParams['header'] =  {'DNT': '1', 'Referer':Referer, 'User-Agent':self.cm.HOST}
        else: {'DNT':'1', 'User-Agent':self.cm.HOST}
        
        
        sts, data = self.cm.getPage(url, httpParams, post_data)
        if not sts: return
        #printDBG(data)
        tmp = self.cm.ph.getSearchGroups(data, 'new Paginator\("paginator0",[^,]*?([0-9]+?)\,[^,]*?[0-9]+?\,[^,]*?[0-9]+?\,[^"]*?"([^"]+?)"\,[^,]*?([0-9]+?)[^0-9]', 3)
        if '' == tmp[1]:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '.paginator(', ');', False)[1]
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> %s" % tmp)
            tmpTab = []
            tmpTab.append( self.cm.ph.getSearchGroups(tmp, 'pagesTotal:[^0-9]([0-9]+?)[^0-9]', 1)[0])
            if 'priv_search' in cItem:
                tmpTab.append( '/search.jsp?st=')
            else:
                tmpTab.append( '/all.jsp?st=')
            tmpTab.append( self.cm.ph.getSearchGroups(tmp, 'numberObjects:[^0-9]([0-9]+?)[^0-9]', 1)[0])
            tmp = tmpTab
        
        try: cItem['num_of_pages'] = int(tmp[0])
        except Exception: cItem['num_of_pages'] = 1
        try: cItem['url'] = self._getFullUrl(tmp[1])
        except Exception: pass
        try: cItem['page_size'] = int(tmp[2])
        except Exception: cItem['page_size'] = 1
        
        if 'priv_search' in cItem:
            pageloadUrl = '/pageloading/search-media-loader.jsp'
        else:
            pageloadUrl = '/pageloading/all-loader.jsp'
            
        if pageloadUrl in data:
            httpParams['header'] =  {'DNT': '1', 'Referer':url, 'User-Agent':self.cm.HOST}
            url = self._getFullUrl(pageloadUrl + '?ads=false')
            sts, data = self.cm.getPage(url, httpParams, None)
            if not sts: return
            #printDBG(data)
            m1 = '<div class="thumbnail"'
            m2 = '</li>'
            newhandle = True
        else:
            newhandle = False
        
        #printDBG(data)
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(m1)
        #if len(data): del data[0]
        
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', 1)[0]
            if newhandle:
                title = self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1]
                try: desc = self.cleanHtmlStr(item.split('</div>')[1])
                except Exception: desc = ''
            else:
                title = self.cm.ph.getSearchGroups(item, reTitle, 1)[0]
                try: desc = self.cleanHtmlStr(item.split('</tr>')[1])
                except Exception: desc = ''
            if title != '' and url != '':
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon), 'desc':desc} )
                self.addVideo(params)
            
        if page < cItem['num_of_pages']:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnyFiles.searchTab")
        
        page = cItem.get('page', 1)
        if 1 == page:
            sts, data = self.cm.getPage(self._getFullUrl('/all.jsp?reset_f=true'), self.defaultParams) #self.MAIN_URL
            if not sts: return
            data = self.cm.ph.getDataBeetwenMarkers(data, 'POST', ';', False)[1]
            data = re.compile('[ ]*?se:[ ]*?"([^"]+?)"').findall(data)
            post_data = {}
            for item in data:
                post_data['se'] = item
            post_data['q'] = searchPattern
            cItem = dict(cItem)
            #cItem['post_data'] = post_data
            cItem['url'] = self.SEARCH_URL
            cItem['Referer'] = self.SEARCH_URL
            cItem['priv_search'] = True
            sts, data = self.cm.getPage(self.SEARCH_URL, self.defaultParams, post_data)
            if not sts: return 
        
        self.listMovies(cItem, m1='<div class="u-hr-div" >', reTitle='<a [^>]+?>([^<]+?)</a>')
        
    def getLinksForVideo(self, cItem):
        return self.getLinksForFavourite(cItem['url'])
                
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        printDBG("AnyFiles.getLinksForFavourite [%s]" % fav_data)
        data = self.anyfiles.getVideoUrl(fav_data)
        for item in data:
            item['need_resolve'] = 0
        return data
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            rm(self.COOKIE_FILE)
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #MOVIES
        elif category == 'genres':
            self.listGenres(self.currItem, 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
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
        CHostBase.__init__(self, AnyFiles(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('anyfileslogo.png')])
    
