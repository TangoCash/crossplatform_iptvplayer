## @file  ihost.py
#

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSearchHistoryHelper, GetCookieDir, printDBG, printExc, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

class CUrlItem:
    def __init__(self, name = "", url = "", urlNeedsResolve = 0):
        if isinstance(name, basestring): self.name = name
        else: self.name = str(name)
        
        # used only for TYPE_VIDEO item 
        if isinstance(url, basestring): self.url = url
        else: self.url = str(url)
        
        self.urlNeedsResolve = urlNeedsResolve #  additional request to host is needed to resolv this url (url is not direct link)
## class CDisplayListItem
# define attribiutes for item of diplay list
# communicate display layer with host
#
class CDisplayListItem:
    TYPE_CATEGORY  = "CATEGORY"
    TYPE_VIDEO     = "VIDEO"
    TYPE_AUDIO     = "AUDIO"
    TYPE_SEARCH    = "SEARCH"
    TYPE_ARTICLE   = "ARTICLE"
    TYPE_PICTURE   = "PICTURE"
    TYPE_MORE      = "MORE"
    
    TYPE_SUBTITLE      = "SUBTITLE"
    TYPE_SUB_PROVIDER  = "SUB_PROVIDER"
    TYPE_UNKNOWN       = "UNKNOWN"
    
    def __init__(self, name = "", \
                description = "", \
                type = TYPE_UNKNOWN, \
                urlItems = [], \
                urlSeparateRequest = 0, \
                iconimage = '', \
                possibleTypesOfSearch = None, \
                pinLocked = False, \
                isGoodForFavourites = False, \
                isWatched = False):
                
        if isinstance(name, basestring): self.name = name
        else: self.name = str(name)
        
        if isinstance(description, basestring): self.description = description
        else: self.description = str(description)
        
        if isinstance(type, basestring): self.type = type
        else: self.type = str(type)
        
        if isinstance(iconimage, basestring): self.iconimage = iconimage
        else: self.iconimage = str(iconimage)
        
        if pinLocked: self.pinLocked = True
        else: self.pinLocked = False
            
        if isGoodForFavourites: self.isGoodForFavourites = True
        else: self.isGoodForFavourites = False
        
        if isWatched: self.isWatched = True
        else: self.isWatched = False
        
        # used only for TYPE_VIDEO item
        self.urlItems = urlItems # url to VIDEO
        # links are not available the separate request is needed to get links
        self.urlSeparateRequest = urlSeparateRequest
        # used only for TYPE_SEARCH item
        self.possibleTypesOfSearch = possibleTypesOfSearch
        self.privateData = None
        self.itemIdx = -1

class ArticleContent:
    VISUALIZER_DEFAULT = 'DEFAULT'
    # Posible args and values for richDescParams:
    RICH_DESC_PARAMS        = ["alternate_title", "views", "status", "country", "language", "quality", "subtitles", "year", "imdb_rating", \
                               "released", "broadcast", "remaining", "rating", "rated", "duration", "genre", "production", "director", "directors", "writer", "writers", \
                               "creator", "creators", "actors", "stars", "awards", "budget" ]
    # labels here must be in english language 
    # translation should be done before presentation using "locals" mechanism
    RICH_DESC_LABELS = {"alternate_title":   "Alternate Title:",
                        "status":            "Status:",
                        "quality":           "Quality:",
                        "subtitles":         "Subtitles:",
                        "country":           "Country:", 
                        "language":          "Language",
                        "year":              "Year:", 
                        "released":          "Released:",
                        "broadcast":         "Broadcast:",
                        "remaining":         "Remaining:",
                        "imdb_rating":       "IMDb Rating:",
                        "rating":            "Rating:", 
                        "rated":             "Rated:",
                        "duration":          "Duration:", 
                        "genre":             "Genre:", 
                        "production":        "Production:",
                        "director":          "Director:",
                        "directors":         "Directors:",
                        "writer":            "Writer:",
                        "writers":           "Writers:",
                        "creator":           "Creator:",
                        "creators":          "Creators:",
                        "actors":            "Actors:", 
                        "stars":             "Stars:",
                        "awards":            "Awards:",
                        "views":             "Views:",
                        "budget":            "Budget:",}
    def __init__(self, title = '', text = '', images = [], trailers = [], richDescParams = {}, visualizer=None):
        self.title    = title
        self.text     = text
        self.images   = images
        self.trailers = trailers
        self.richDescParams = richDescParams
        if None == visualizer: 
            self.visualizer = ArticleContent.VISUALIZER_DEFAULT
        else:
            self.visualizer = visualizer
        
class CFavItem:
    RESOLVER_DIRECT_LINK = 'DIRECT_LINK'
    RESOLVER_SELF        = 'SELF'
    RESOLVER_URLLPARSER  = 'URLLPARSER'
    TYPE_UNKNOWN = CDisplayListItem.TYPE_UNKNOWN
    def __init__( self, name         = '', \
                  description        = '', \
                  type               = TYPE_UNKNOWN, \
                  iconimage          = '', \
                  data               = '', \
                  resolver           = RESOLVER_SELF ):
        self.name        = name
        self.description = description
        self.type        = type
        self.iconimage   = iconimage 
        self.data        = data
        self.resolver    = resolver
        self.hostName    = ''
        
    def fromDisplayListItem(self, dispItem):
        self.name        = dispItem.name
        self.description = dispItem.description
        self.type        = dispItem.type
        self.iconimage   = dispItem.iconimage
        return self
    
    def setFromDict(self, data):
        for key in data:
            setattr(self, key, data[key])
        return self
        
    def getAsDict(self):
        return vars(self)
       
class RetHost:
    OK = "OK"
    ERROR = "ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    def __init__(self, status , value, message = ''):
        self.status = status
        self.value = value  
        self.message = message

## class IHost
# interface base class with method used to
# communicate display layer with host
#
class IHost:

    def isProtectedByPinCode(self):
        return False
    
    # return list of types which can be added as favourite
    def getSupportedFavoritesTypes(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # get favourite item CFavItem for item with given index
    def getFavouriteItem(self, Index=0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # similar as getLinksForItem, returns links 
    # for given CFavItem
    def getLinksForFavourite(self, favItem):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    def setInitFavouriteItem(self, favItem):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    # return firs available list of item category or video or link
    def getInitList(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    # item - object of CDisplayListItem for selected item
    def getListForItem(self, Index = 0, refresh = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    def getMoreForItem(self, Index=0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getLinksForVideo(self, Index = 0, item = None):
        return self.getLinksForItem(Index, item)
        
    # return list of links for AUDIO, VIDEO, PICTURE
    # for given Index, 
    # item - object of CDisplayListItem for selected item
    def getLinksForItem(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getArticleContent(self, Index = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return full path to player logo
    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir(getattr(self, '__module__').split('.')[-1][4:] + 'logo.png')])
        
    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    # return list of custom actions 
    # for given Index,  
    # this function is called directly from main theread
    # it should be very quick and can not perform long actions,
    # like reading file, download web page etc.
    def getCustomActions(self, Index = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def performCustomAction(self, privateData):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
'''
CHostBase implements some typical methods
          from IHost interface
'''
class CHostBase(IHost):
    def __init__( self, host, withSearchHistrory, favouriteTypes=[] ):
        self.host = host
        self.withSearchHistrory = withSearchHistrory
        self.favouriteTypes     = favouriteTypes

        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = [] 
        
        self.searchPattern = ''
        self.searchType = ''
        
    def getSupportedFavoritesTypes(self):
        return RetHost(RetHost.OK, value = self.favouriteTypes)
        
    def isValidIndex(self, Index, validTypes=None):
        listLen = len(self.host.currList)
        if listLen <= Index or Index < 0:
            printDBG( "ERROR isValidIndex - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return False
        if None != validTypes and self.converItem(self.host.currList[Index]).type not in validTypes:
            printDBG( "ERROR isValidIndex - current item has wrong type" )
            return False
        return True
        
    def withArticleContent(self, cItem):
        return False
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        
        if not self.withArticleContent(cItem):
            return RetHost(retCode, value=retlist)
        hList = self.host.getArticleContent(cItem)
        if None == hList:
            return RetHost(retCode, value=retlist)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        if len(hList): retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    # end getArticleContent
    
    def getLinksForItem(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForItem(self.host.currList[Index])
        for item in urlList:
            need_resolve = item.get("need_resolve", 0)
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
    # end getResolvedURL
        
    def getFavouriteItem(self, Index=0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index, self.favouriteTypes): RetHost(retCode, value=retlist)
        
        cItem = self.host.currList[Index]
        data = self.host.getFavouriteData(cItem)
        if None != data:
            favItem = CFavItem(data=data)
            favItem.fromDisplayListItem(self.converItem(cItem))
            
            retlist = [favItem]
            retCode = RetHost.OK

        return RetHost(retCode, value=retlist)
    # end getFavouriteItem
    
    def getLinksForFavourite(self, favItem):
        retlist = []
        urlList = self.host.getLinksForFavourite(favItem.data)
        for item in urlList:
            need_resolve = item.get("need_resolve", 0)
            name = self.host.cleanHtmlStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))
        return RetHost(RetHost.OK, value = retlist)
        
    def setInitFavouriteItem(self, favItem):
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = []
        
        self.host.setCurrList([])
        self.host.setCurrItem({})
        
        if self.host.setInitListFromFavouriteItem(favItem.data):
            return RetHost(RetHost.OK, value = None)
        return RetHost(RetHost.ERROR, value = None)
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = []
        
        self.host.handleService(self.currIndex)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        self.listOfprevItems.append(self.host.getCurrItem())
        
        self.currIndex = Index
        if self.withSearchHistrory:
            self.setSearchPattern()
            try:
                if len(self.searchPattern):
                    sts, prevPattern = CSearchHistoryHelper.loadLastPattern()
                    if sts and prevPattern != self.searchPattern:
                        CSearchHistoryHelper.saveLastPattern(self.searchPattern)
            except Exception:
                printExc()
        
        self.host.handleService(Index, refresh, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)

    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            hostCurrItem = self.listOfprevItems.pop()
            self.host.setCurrList(hostList)
            self.host.setCurrItem(hostCurrItem)
            
            convList = self.convertList(hostList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        if refresh == 1:
            self.host.handleService(self.currIndex, refresh, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    def getMoreForItem(self, Index=0):
        self.host.handleService(Index, 2, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)

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
    
    def convertList(self, cList):
        hostList = []
        for cItem in cList:
            hostItem = self.converItem(cItem)
            if None != hostItem: hostList.append(hostItem)
        return hostList
    # end convertList
    
    def getSearchTypes(self):
        searchTypesOptions = []
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "series"))
        return searchTypesOptions
        
    def getDefaulIcon(self, cItem):
        return self.host.getDefaulIcon(cItem)
        
    def getFullIconUrl(self, cItem):
        return self.host.getFullIconUrl(cItem)
    
    def converItem(self, cItem):
        hostList = []
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = self.getSearchTypes()
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
        elif 'picture' == cItem['type']:
            type = CDisplayListItem.TYPE_PICTURE
        elif 'article' == cItem['type']:
            type = CDisplayListItem.TYPE_ARTICLE
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO, \
                    CDisplayListItem.TYPE_PICTURE, CDisplayListItem.TYPE_ARTICLE]:
            url = cItem.get('url', '')
            if '' != url: hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  self.getFullIconUrl( cItem.get('icon', '') )
        if icon == '': icon = self.getDefaulIcon(cItem)
        isGoodForFavourites = cItem.get('good_for_fav', False)
        pinLocked = cItem.get('pin_locked', False)
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch,
                                    pinLocked = pinLocked,
                                    isGoodForFavourites = isGoodForFavourites)
    # end converItem

    def getSearchResults(self, searchpattern, searchType = None):
        retList = []
        if self.withSearchHistrory:
            self.host.history.addHistoryItem( searchpattern, searchType )

        self.searchPattern = searchpattern
        self.searchType = searchType
        
        # Find 'Wyszukaj' item
        list = self.host.getCurrList()
        
        searchItemIdx = self.getSearchItemInx()
        if searchItemIdx > -1:
            return self.getListForItem( searchItemIdx )
        else:
            return RetHost(RetHost.ERROR, value = [])
            
    # end getSearchResults
    

class CBaseHostClass:
    def __init__(self, params={}):
        self.sessionEx = MainSessionWrapper() 
        self.up = urlparser()
        
        proxyURL = params.get('proxyURL', '')
        useProxy = params.get('useProxy', False)
        if 'MozillaCookieJar' == params.get('cookie_type', ''):
            self.cm = common(proxyURL, useProxy, True)
        else:
            self.cm = common(proxyURL, useProxy)

        self.currList = []
        self.currItem = {}
        if '' != params.get('history', ''):
            self.history = CSearchHistoryHelper(params['history'], params.get('history_store_type', False))
        if '' != params.get('cookie', ''):
            self.COOKIE_FILE = GetCookieDir(params['cookie'])
        self.moreMode = False
        self.minPyVer = params.get('min_py_ver', 0)
        
    def checkPythonVersion(self, pyVer):
        try:
            from Screens.MessageBox import MessageBox
            import sys
            if sys.version_info < pyVer:
                hasSNI = False
                try:
                    from ssl import wrap_socket
                    from inspect import getargspec
                    if 'server_hostname' in '%s' % [getargspec(wrap_socket)]:
                        hasSNI = True
                except Exception:
                    pass
                if not hasSNI:
                    message = _('This service requires a new Enigma2 image with a Python version %s or later.') % ('.'.join(str(x) for x in pyVer))
                    message += '\n' + _('You can also install SNI patch for you python if available.')
                    self.sessionEx.waitForFinishOpen(MessageBox, message, type = MessageBox.TYPE_INFO, timeout = 10)
        except Exception:
            printExc()
    
    def listsTab(self, tab, cItem, type='dir'):
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
    
    def getMainUrl(self):
        return self.MAIN_URL
    
    def getFullUrl(self, url):
        if url.startswith('./'):
            url = url[1:]
        if url.startswith('//'):
            url = 'http:' + url
        elif url.startswith('://'):
            url = 'http' + url
        elif url.startswith('/'):
            url = self.getMainUrl() + url[1:]
        elif 0 < len(url) and '://' not in url:
            url =  self.getMainUrl() + url
        return url
        
    def getFullIconUrl(self, url):
        return self.getFullUrl(url)
        
    def getDefaulIcon(self, cItem=None):
        try: return self.DEFAULT_ICON_URL
        except Exception:
            pass
        return ''
    
    @staticmethod 
    def cleanHtmlStr(str):
        str = str.replace('<', ' <')
        str = str.replace('&nbsp;', ' ')
        str = str.replace('&nbsp', ' ')
        str = clean_html(str)
        str = str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return CParsingHelper.removeDoubles(str, ' ').strip()

    @staticmethod 
    def getStr(v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''):  return v
        return default
            
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def addMore(self, params):
        params['type'] = 'more'
        self.currList.append(params)
        return
        
    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return
        
    def addAudio(self, params):
        params['type'] = 'audio'
        self.currList.append(params)
        return
    
    def addPicture(self, params):
        params['type'] = 'picture'
        self.currList.append(params)
        return
  
    def addArticle(self, params):
        params['type'] = 'article'
        self.currList.append(params)
        return
    
    def listsHistory(self, baseItem={'name': 'history', 'category': 'Wyszukaj'}, desc_key='plot', desc_base=(_("Type: ")) ):
        list = self.history.getHistoryList()
        for histItem in list:
            plot = ''
            try:
                if type(histItem) == type({}):
                    pattern     = histItem.get('pattern', '')
                    search_type = histItem.get('type', '')
                    if '' != search_type: plot = desc_base + _(search_type)
                else:
                    pattern     = histItem
                    search_type = None
                params = dict(baseItem)
                params.update({'title': pattern, 'search_type': search_type,  desc_key: plot})
                self.addDir(params)
            except Exception: printExc()
            
    def setInitListFromFavouriteItem(self, fav_data):
        return False
        
    def getLinksForItem(self, cItem):
        return self.getLinksForVideo(cItem)
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        if self.minPyVer > 0:
            self.checkPythonVersion(self.minPyVer)
            self.minPyVer = 0 # inform only once
        
        self.moreMode = False
        if 0 == refresh:
            if len(self.currList) <= index:
                return
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
        if 2 == refresh: # refresh for more items
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> endHandleService index[%s]" % index)
            # remove item more and store items before and after item more
            self.beforeMoreItemList = self.currList[0:index]
            self.afterMoreItemList = self.currList[index+1:]
            self.moreMode = True
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
    
    def endHandleService(self, index, refresh):
        if 2 == refresh: # refresh for more items
            currList = self.currList
            self.currList = self.beforeMoreItemList
            for item in currList:
                if 'more' == item['type'] or (item not in self.beforeMoreItemList and item not in self.afterMoreItemList):
                    self.currList.append(item)
            self.currList.extend(self.afterMoreItemList)
            self.beforeMoreItemList = []
            self.afterMoreItemList  = []
        self.moreMode = False
    