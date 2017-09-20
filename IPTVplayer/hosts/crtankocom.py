# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import base64
try:    import json
except Exception: import simplejson as json
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
    return 'http://www.crtanko.com/'

class CrtankoCom(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  CrtankoCom.tv', 'cookie':'crtankocom.cookie'})
        
        self.MAIN_URL      = 'http://www.crtanko.com/'
        self.SEARCH_URL    = self.MAIN_URL
        self.DEFAULT_ICON_URL  = "http://www.crtanko.com/wp-content/uploads/2015/04/logo5.png"
        
        self.MAIN_CAT_TAB = [{'category':'search',          'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',  'title': _('Search history'),            } ]
                        
        self.BY_LETTER_TAB = [{'title':_('All')},
                              {'title':'#', 'letter':'numeric'}, {'title':'', 'letter':'A'},
                              {'title':'', 'letter':'B'},        {'title':'', 'letter':'C'},
                              {'title':'', 'letter':'Č'},        {'title':'', 'letter':'D'},
                              {'title':'', 'letter':'E'},        {'title':'', 'letter':'F'},
                              {'title':'', 'letter':'G'},        {'title':'', 'letter':'H'},
                              {'title':'', 'letter':'I'},        {'title':'', 'letter':'J'},
                              {'title':'', 'letter':'K'},        {'title':'', 'letter':'L'},
                              {'title':'', 'letter':'LJ'},       {'title':'', 'letter':'M'},
                              {'title':'', 'letter':'N'},        {'title':'', 'letter':'O'},
                              {'title':'', 'letter':'P'},        {'title':'', 'letter':'R'},
                              {'title':'', 'letter':'S'},        {'title':'', 'letter':'Š'},
                              {'title':'', 'letter':'T'},        {'title':'', 'letter':'U'},
                              {'title':'', 'letter':'V'},        {'title':'', 'letter':'W'},
                              {'title':'', 'letter':'Y'},        {'title':'', 'letter':'Z'},
                              {'title':'', 'letter':'Ž'} ]
        
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheSubCategory = []
        self.cacheLinks = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if 0 < len(url) and not url.startswith('http'):
                url =  self.MAIN_URL + url
            if not self.MAIN_URL.startswith('https://'):
                url = url.replace('https://', 'http://')
                
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)

        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)
            
    def listsMainMenu(self, cItem, category1, category2):
        printDBG("CrtankoCom.listsMainMenu")
        self.cacheSubCategory = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        subCatMarker = '<ul class="dropdown-menu">'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="menu-meni-container">', subCatMarker)[1]
        data = re.split('<a[^>]+?href="#"[^>]*?>', data)
        
        for part in data:
            subCatDataIdx = part.find(subCatMarker)
        
            idx = 0
            if subCatDataIdx > 0:
                subCatName = self.cleanHtmlStr( part[0:subCatDataIdx] )
                idx  = subCatDataIdx
            
            part = self.cm.ph.getAllItemsBeetwenMarkers(part[idx:], '<li ', '</li>')
            
            tab = []
            for item in part:
                url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
                title = self.cleanHtmlStr( item )
                if not url.startswith('http'):
                    continue
                tab.append({'title':title, 'url':url})
            
            if subCatDataIdx > 0:
                params = dict(cItem)
                if len(tab):
                    params.update({'category':category1,'title':subCatName, 'sub_cat_idx':len(self.cacheSubCategory)})
                    self.addDir(params)
                    self.cacheSubCategory.append(tab)
            else:
                params = dict(cItem)
                params['category'] = category2
                self.listsTab(tab, params)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("CrtankoCom.listCategories")
        if 'sub_cat_idx' not in cItem: return
        idx = cItem['sub_cat_idx']
        if idx > -1 and idx < len(self.cacheSubCategory):
            cItem = dict(cItem)
            cItem['category'] = nextCategory
            self.listsTab(self.cacheSubCategory[idx], cItem)
            
    def listLetters(self, cItem, nextCategory):
        printDBG("CrtankoCom.listCategories")
        tab = []
        for item in self.BY_LETTER_TAB:
            params = dict(cItem)
            params.update(item)
            params['category'] = nextCategory
            if item['title'] == '':
                params['title'] = item['letter']
            self.addDir(params)
            
    def listItems(self, cItem, nextCategory='explore_item'):
        printDBG("CrtankoCom.listItems")
        page   = cItem.get('page', 1)
        search = cItem.get('search', '') 
        letter = cItem.get('letter', '') 
        url    = cItem['url'] 
        
        if page > 1:
            url += 'page/%s/' % page
        if letter != '':
            url += '?ap=%s' % letter
        elif search != '':
            url += '?s=%s' % search
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'rel="next"', '>', False)[1]
        if '/page/{0}/'.format(page+1) in nextPage:
            nextPage = True
        else:
            nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<article ', '</article>')
        for item in data:
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''')[0]
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''data-src=['"]([^"^']+?)['"]''')[0])
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            if self.cm.isValidUrl(url):
                params = dict(cItem)
                params.update({'good_for_fav': True, 'category':nextCategory, 'title':self.cleanHtmlStr(title), 'url':url, 'icon':icon, 'desc':self.cleanHtmlStr(item.split('</noscript>')[-1])})
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem, category):
        printDBG("CrtankoCom.exploreItem")
        page = cItem.get('page', 1)
        url  = cItem['url']
        
        if page > 1:
            url += '%s/' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'Pages:', '</section>', False)[1]
        if '>{0}<'.format(page+1) in nextPage:
            nextPage = True
        else:
            nextPage = False
        
        tmp1 = self.cm.ph.getDataBeetwenMarkers(data, '<section', '</section', False)[1]
        tmp1 = self.cm.ph.getAllItemsBeetwenMarkers(tmp1, '<p', '</div>')
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="youtube">', '</div>')
        searchMore = True
        for tmp in [tmp1, data]:
            for item in tmp:
                linkData = self.cm.ph.getDataBeetwenMarkers(item, '<div class="youtube">', '</div', False)[1]
                if linkData == '':
                    continue
                titles = self.cm.ph.getAllItemsBeetwenMarkers(item, '<p', '</p>')
                if len(titles) and titles[-1] != '':
                    title = self.cleanHtmlStr(titles[-1])
                else:
                    title = self.cleanHtmlStr(item)
                t1 = cItem['title'].strip().upper()
                t2 = title.strip().upper()
                if t1 != t2 and t2 != '' and not t1 in t2:
                    title = '{0} - {1}'.format(cItem['title'], title)
                if title == '': title = cItem['title']
                params = dict(cItem)
                params.update({'good_for_fav': False, 'title':title, 'url_data':linkData})
                self.addVideo(params)
                searchMore = False
            if not searchMore:
                break
            
        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_('Next page'), 'page':page+1})
            self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("CrtankoCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'url_data' in cItem:
            data = cItem['url_data']
        else:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return []
        
        vidUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
        if vidUrl == '': vidUrl = self.cm.ph.getSearchGroups(data, '<script[^>]+?src="([^"]+?)"', 1, True)[0]
        if vidUrl == '': vidUrl = self.cm.ph.getDataBeetwenMarkers(data, 'data-rocketsrc="', '"', False, True)[1]

        if vidUrl.startswith('//'):
            vidUrl = 'http:' + vidUrl
        
        vidUrl = self._getFullUrl(vidUrl)
        validatehash = ''
        for hashName in ['up2stream.com', 'videomega.tv']:
            if hashName + '/validatehash.php?' in vidUrl:
                validatehash = hashName
        if validatehash != '':
            sts, dat = self.cm.getPage(vidUrl, {'header':{'Referer':cItem['url'], 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'}})
            if not sts: return urlTab
            dat = self.cm.ph.getSearchGroups(dat, 'ref="([^"]+?)"')[0]
            if '' == dat: return urlTab
            vidUrl = 'http://{0}/view.php?ref={1}&width=700&height=460&val=1'.format(validatehash, dat)
            
        if '' != vidUrl:
            title = self.up.getHostName(vidUrl)
            urlTab.append({'name':title, 'url':vidUrl, 'need_resolve':1})
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("CrtankoCom.getVideoLinks [%s]" % videoUrl)
        
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("CrtankoCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL
        cItem['search'] = urllib.quote(searchPattern)
        self.listItems(cItem)

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % self.currItem )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu({'url':self.MAIN_URL}, 'categories', 'list_letters')
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_letters')
        elif category == 'list_letters':
            self.listLetters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
    #EXPLORE ITEM
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_videos')
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
        CHostBase.__init__(self, CrtankoCom(), True, favouriteTypes=[])

