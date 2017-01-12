# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
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
config.plugins.iptvplayer.filmy3deu_sortby   = ConfigSelection(default = "date", choices = [("date", _("Added date")), ("rating", _("Rating")), ("news_read", _("View count")), ("comm_num", _("Comment count")), ("title", _("Title"))]) 
config.plugins.iptvplayer.filmy3deu_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.filmy3deu_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.filmy3deu_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.filmy3deu_sortby))
    optionList.append(getConfigListEntry("Użytkownik Filmy3dEU?", config.plugins.iptvplayer.filmy3deu_premium))
    if config.plugins.iptvplayer.filmy3deu_premium.value:
        optionList.append(getConfigListEntry("  Filmy3dEU login:", config.plugins.iptvplayer.filmy3deu_login))
        optionList.append(getConfigListEntry("  Filmy3dEU hasło:", config.plugins.iptvplayer.filmy3deu_password))
    return optionList
###################################################


def gettytul():
    return 'filmy3d.eu'

class Filmy3dEU(CBaseHostClass):
    MAIN_URL    = 'http://filmy3d.eu/'
    SRCH_URL    = MAIN_URL + 'index.php?do=search'
    
    MAIN_CAT_TAB = [{'category':'list_movies',     'title':  'Najnowsze filmy', 'sort_type':'lastnews', 'icon':'', 'url':MAIN_URL+'lastnews/'},
                    {'category':'list_movies',     'title':  'Polecamy',        'sort_type':'cat',      'icon':'', 'url':MAIN_URL+'polecane/'},
                    {'category':'list_movies',     'title':  'Strona główna',   'sort_type':'main',     'icon':'', 'url':MAIN_URL},
                    {'category':'cat_movies',      'title':  'Kategorie',       'sort_type':'cat',      'icon':'', 'url':MAIN_URL},
                    {'category':'cat_az',          'title':  'Katalog A-Z',     'sort_type':'main',     'icon':'', 'url':MAIN_URL},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Filmy3dEU', 'cookie':'playtube.cookie'})

        #Login data
        self.loggedIn = None
        
        self.catCache = {'cat_az':[], 'cat_movies':[], 'filled':False}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def _addSortData(self, sortType, post_data={}):
        post_data['dlenewssortby'] = config.plugins.iptvplayer.filmy3deu_sortby.value
        post_data.update({'set_new_sort':'dle_sort_'+sortType, 'set_direction_sort':'dle_direction_'+sortType})
        if post_data['dlenewssortby'] == 'title':
            post_data['dledirection'] = 'asc'
        else:
            post_data['dledirection'] = 'desc'
        return post_data

    def listsTab(self, tab, cItem):
        printDBG("Filmy3dEU.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def listMovies(self, cItem):
        printDBG("Filmy3dEU.listMovies")
        
        page = cItem.get('page', 1)
        url = cItem['url']
        if page > 1 and '?' not in url: 
            if url.endswith('/'):
                url = url[:-1]
            url += '/page/%s/' % page
        
        post_data = cItem.get('post_data', {})
        if {} == post_data:
            sts, data = self.cm.getPage(url, {}, self._addSortData(cItem.get('sort_type', '')))
        else:
            sts, data = self.cm.getPage(cItem['url'], {'raw_post_data':True, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}, post_data)
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="short-film">', '<div class="gf-right">', False)[1]
        data = data.split('<div class="short-film">')
        
        if len(data) > 0 and '<span class="pnext">Poprzednia</span></a>' in data[-1]:
            nextPage = True
        else: nextPage = False
        
        for item in data:
            tmp = item.split('<h5')[-1]
            url    = self.cm.ph.getSearchGroups(tmp, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = CParsingHelper.getDataBeetwenMarkers(tmp, '>', '</h5>', False)[1]
            if '' == title: self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc = _("Rating") + ': {0}/100, '.format(self.cm.ph.getSearchGroups(item, 'width\:([0-9]+?)\%')[0]) 
            desc  += CParsingHelper.getDataBeetwenMarkers(item, '<p class="text">', '</p>', False)[1]

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Filmy3dEU.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        if True != self.loggedIn:
            SetIPTVPlayerLastHostError('Dostęp do wyszukiwarki dla użytkowników z rangą: "Goście" jest zablokowany.')
            return
        
        page = cItem.get('page', 1) - 1
        post_data = 'do=search&subaction=search&search_start={0}&full_search={1}&result_from=1&story={2}'.format(page+1, page*10 +1, urllib.quote_plus(searchPattern))
        cItem = dict(cItem)
        cItem.update({'post_data':post_data, 'url':Filmy3dEU.SRCH_URL})
        
        self.listMovies(cItem)
        
    def getArticleContent(self, cItem):
        printDBG("Filmy3dEU.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'url' not in cItem: return retTab
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, "<div id='dle-content'>", '<div class="gf-right">', False)
        title = CParsingHelper.getDataBeetwenMarkers(data, '<h1 class="title">', '</h1>', False)[1]
        icon = self.cm.ph.getSearchGroups(data, 'srct="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="comment-box-block" id="comment1">', '</div>', False)[1] )
        
        return [{'title':title, 'text':desc, 'images':[]}]
        
    def getLinksForVideo(self, cItem):
        printDBG("Filmy3dEU.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'], {'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        if not sts:
            # no cookie file?
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return urlTab
            
        match = re.search('<iframe[^>]+?src="([^"]+?)"', data, re.IGNORECASE)
        if match:
            url = match.group(1)
            urlTab.append({'name':'Main url [%s]' % self.up.getHostName(url), 'url':url, 'need_resolve':1})
        

        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<code>', '</code>', False)
        if not sts: return urlTab
        data = data.split('http&#58;')
        for item in data:
            item = item.strip()
            if not item.startswith('//'): continue
            url = 'http:' + item
            urlTab.append({'name':self.up.getHostName(url), 'url':url, 'need_resolve':1})
        return urlTab
        
    def _getCategoriesData(self, url):
        if self.catCache['filled']: return
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        reCatObj = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>')
        for catType in [{'type':'cat_movies', 'm1':'<span>Kategorie</span>'}, {'type':'cat_az', 'm1':'<span>Katalog A-Z</span>'}]:
            sts, catData = self.cm.ph.getDataBeetwenMarkers(data, catType['m1'], '</ul>', False)
            if not sts: return
            catData = reCatObj.findall(catData)
            dataTab = []
            for item in catData:
                dataTab.append({ 'title':item[1], 'url':self._getFullUrl(item[0]) })
            if 0 == len(catData): return
            self.catCache[catType['type']] = dataTab
        self.catCache['filled'] = True
        
    def listCategories(self, cItem, category):
        printDBG("Filmy3dEU.listCategories [%s]" % cItem)
        self._getCategoriesData(cItem['url'])
        
        dataTab = self.catCache[cItem['category']]
        params = dict(cItem)
        params['category'] = category
        
        self.listsTab(dataTab, params)
        
    def getVideoLinks(self, url):
        printDBG("Movie4kTO.getVideoLinks [%s]" % url)
        urlTab = []
        
        videoUrl = url
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def tryTologin(self):
        printDBG('tryTologin start')
        if '' == config.plugins.iptvplayer.filmy3deu_login.value.strip() or '' == config.plugins.iptvplayer.filmy3deu_password.value.strip():
            printDBG('tryTologin wrong login data')
            return False
        post_data = {'login_name':config.plugins.iptvplayer.filmy3deu_login.value, 'login_password':config.plugins.iptvplayer.filmy3deu_password.value, 'login_not_save':'1', 'login':'submit'}
        params = {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage( self.MAIN_URL, params, post_data)
        if not sts:
            printDBG('tryTologin problem with login')
            return False
            
        if '?action=logout' in data:
            printDBG('tryTologin user[%s] logged' % config.plugins.iptvplayer.filmy3deu_login.value)
            return True
     
        printDBG('tryTologin user[%s] failed' % config.plugins.iptvplayer.filmy3deu_login.value)
        return False

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn and config.plugins.iptvplayer.filmy3deu_premium.value:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % config.plugins.iptvplayer.filmy3deu_login.value, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})           
    #MOVIES LIST
        elif category == "list_movies":
            self.listMovies(self.currItem)
    #CATEGORIES
        elif category == "cat_movies" or category == "cat_az":
            self.listCategories(self.currItem, "list_movies")
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
        CHostBase.__init__(self, Filmy3dEU(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('filmy3deulogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

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
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "filmy"))
        #searchTypesOptions.append(("Seriale", "seriale"))
    
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

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except Exception:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
