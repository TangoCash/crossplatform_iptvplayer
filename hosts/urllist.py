# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.iptvcomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvfilehost import IPTVFileHost
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigDirectory, getConfigListEntry
import re
import codecs
import time
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.Sciezkaurllist = ConfigDirectory(default = "/hdd/")
config.plugins.iptvplayer.grupujurllist  = ConfigYesNo(default = True)
config.plugins.iptvplayer.sortuj         = ConfigYesNo(default = True)
config.plugins.iptvplayer.urllist_showrafalcool1 = ConfigYesNo(default = True)

def GetConfigList():
    optionList = [] 
    optionList.append(getConfigListEntry(_('Text files ytlist and urllist are in:'), config.plugins.iptvplayer.Sciezkaurllist))    
    optionList.append(getConfigListEntry(_('Show recommended by Rafalcool1:'), config.plugins.iptvplayer.urllist_showrafalcool1))
    optionList.append(getConfigListEntry(_('Sort the list:'), config.plugins.iptvplayer.sortuj))
    optionList.append(getConfigListEntry(_('Group links into categories: '), config.plugins.iptvplayer.grupujurllist))
    return optionList
###################################################

def gettytul():
    return (_('Urllists player'))

class Urllist(CBaseHostClass):
    RAFALCOOL1_FILE  = 'urllist.rafalcool1'
    URLLIST_FILE     = 'urllist.txt'
    URRLIST_STREAMS  = 'urllist.stream'
    URRLIST_USER     = 'urllist.user'
    
    def __init__(self):
        printDBG("Urllist.__init__")
        
        self.MAIN_GROUPED_TAB = [{'category': 'all', 'title': (_("All in one")), 'desc': (_("Links are videos and messages, without division into categories")), 'icon':'http://osvita.mediasapiens.ua/content/news/001000-002000/shyfrovanie_dannyh_1415.jpg'}]
        if config.plugins.iptvplayer.urllist_showrafalcool1.value:
            self.MAIN_GROUPED_TAB.append({'category': Urllist.RAFALCOOL1_FILE,  'title': (_("Recommended by Rafalcool1")), 'desc': (_("List of movies prepared by Rafalcool1")),                     'icon':'http://s1.bild.me/bilder/030315/3925071iconFilm.jpg'})        
        self.MAIN_GROUPED_TAB.extend( [{'category': Urllist.URLLIST_FILE,       'title': (_("Videos")),                    'desc': (_("Links to the video files from the file urllist.txt")),        'icon':'http://mohov.h15.ru/logotip_kino.jpg'}, \
                                       {'category': Urllist.URRLIST_STREAMS,    'title': (_("live transfers")),            'desc': (_("Live broadcasts from the file urllist.stream")),              'icon':'http://asiamh.ru.images.1c-bitrix-cdn.ru/images/media_logo.jpg?136879146733721'}, \
                                       {'category': Urllist.URRLIST_USER,       'title': (_("User files")),                'desc': (_("Favorite addresses are stored under the file urllist.user")), 'icon':'http://kinovesti.ru/uploads/posts/2014-12/1419918660_1404722920_02.jpg'}])
        CBaseHostClass.__init__(self)               
        self.currFileHost = None 
    
    def _cleanHtmlStr(self, str):
            str = self.cm.ph.replaceHtmlTags(str, ' ').replace('\n', ' ')
            return clean_html(self.cm.ph.removeDoubles(str, ' ').replace(' )', ')').strip())
            
    def _getHostingName(self, url):
        if 0 != self.up.checkHostSupport(url):
            return self.up.getHostName(url)
        elif self._uriIsValid(url):
            return (_('direct link'))
        else:
            return (_('unknown'))
    
    def _uriIsValid(self, url):
        if '://' in url:
            return True
        return False
        
    def updateRafalcoolFile(self, filePath, encoding):
        printDBG("Urllist.updateRafalcoolFile filePath[%s]" % filePath)
        remoteVersion = -1
        localVersion = -1
        # get version from file
        try:
            with codecs.open(filePath, 'r', encoding, 'replace') as fp:
                # version should be in first line
                line = fp.readline()
                localVersion = int(self.cm.ph.getSearchGroups(line + '|', '#file_version=([0-9]+?)[^0-9]')[0])
        except Exception:
            printExc()
        
        # generate timestamp to add to url to skip possible cacheing
        timestamp = str(time.time())
        
        # if we have loacal version get remote version for comparison
        if localVersion != '':
            sts, data = self.cm.getPage("http://hybrid.xunil.pl/IPTVPlayer_resources/UsersFiles/urllist.txt.version?t=" + timestamp)
            if sts:
                try:
                    remoteVersion = int(data.strip())
                except Exception:
                    printExc()
        # uaktualnij versje
        printDBG('Urllist.updateRafalcoolFile localVersion[%d] remoteVersion[%d]' % (localVersion, remoteVersion))
        if remoteVersion > -1 and localVersion < remoteVersion:
            sts, data = self.cm.getPage("http://hybrid.xunil.pl/IPTVPlayer_resources/UsersFiles/urllist.txt?t=" + timestamp)
            if sts:
                # confirm version
                line = data[0:data.find('\n')]
                try:
                    newVersion = int(self.cm.ph.getSearchGroups(line + '|', '#file_version=([0-9]+?)[^0-9]')[0])
                    if newVersion != remoteVersion:
                        printDBG("Version mismatches localVersion[%d], remoteVersion[%d], newVersion[%d]" % (localVersion, remoteVersion, newVersion) )
                    file = open(filePath, 'wb')
                    file.write(data)
                    file.close()
                except Exception:
                    printExc()
        
    def listCategory(self, cItem, searchMode=False):
        printDBG("Urllist.listCategory cItem[%s]" % cItem)
        
        sortList = config.plugins.iptvplayer.sortuj.value
        filespath = config.plugins.iptvplayer.Sciezkaurllist.value
        groupList = config.plugins.iptvplayer.grupujurllist.value
        if cItem['category'] in ['all', Urllist.URLLIST_FILE, Urllist.URRLIST_STREAMS, Urllist.URRLIST_USER, Urllist.RAFALCOOL1_FILE]:
            self.currFileHost = IPTVFileHost()
            if cItem['category'] in ['all', Urllist.RAFALCOOL1_FILE] and config.plugins.iptvplayer.urllist_showrafalcool1.value:
                self.updateRafalcoolFile(filespath + Urllist.RAFALCOOL1_FILE, encoding='utf-8')
                self.currFileHost.addFile(filespath + Urllist.RAFALCOOL1_FILE, encoding='utf-8')
            
            if cItem['category'] in ['all', Urllist.URLLIST_FILE]: 
                self.currFileHost.addFile(filespath + Urllist.URLLIST_FILE, encoding='utf-8')
            if cItem['category'] in ['all', Urllist.URRLIST_STREAMS]: 
                self.currFileHost.addFile(filespath + Urllist.URRLIST_STREAMS, encoding='utf-8')
            if cItem['category'] in ['all', Urllist.URRLIST_USER]:
                self.currFileHost.addFile(filespath + Urllist.URRLIST_USER, encoding='utf-8')
            
            if 'all' != cItem['category'] and groupList:
                tmpList = self.currFileHost.getGroups(sortList)
                for item in tmpList:
                    if '' == item: title = (_("Other"))
                    else:          title = item
                    params = {'name': 'category', 'category':'group', 'title':title, 'group':item}
                    self.addDir(params)
            else:
                tmpList = self.currFileHost.getAllItems(sortList)
                for item in tmpList:
                    desc = (_("Hosting: %s, %s")) % (self._getHostingName(item['url']), item['url'])
                    if item['desc'] != '':
                        desc = item['desc']
                    params = {'title':item['full_title'], 'url':item['url'], 'desc':desc, 'icon':item['icon']}
                    self.addVideo(params)
        elif 'group' in cItem:
            tmpList = self.currFileHost.getItemsInGroup(cItem['group'], sortList)
            for item in tmpList:
                if '' == item['title_in_group']:
                    title = item['full_title']
                else:
                    title = item['title_in_group']
                desc = (_("Hosting: %s, %s")) % (self._getHostingName(item['url']), item['url'])
                if item.get('desc', '') != '':
                    desc = item['desc']
                params = {'title':title, 'url':item['url'], 'desc': desc, 'icon':item.get('icon', '')}
                self.addVideo(params)
                
    def getLinksForVideo(self, cItem):
        printDBG("Urllist.getLinksForVideo url[%s]" % cItem['url'])
        videoUrls = []
        uri, params   = DMHelper.getDownloaderParamFromUrl(cItem['url'])
        printDBG(params)
        uri = urlparser.decorateUrl(uri, params)
        uri = urlparser.decorateParamsFromUrl(uri)
        
        urlSupport = self.up.checkHostSupport( uri )
        if 1 == urlSupport:
            retTab = self.up.getVideoLinkExt( uri )
            videoUrls.extend(retTab)
        elif 0 == urlSupport and self._uriIsValid(uri):
            if uri.split('?')[0].endswith('.m3u8'):
                retTab = getDirectM3U8Playlist(uri)
                videoUrls.extend(retTab)
            elif uri.split('?')[0].endswith('.f4m'):
                retTab = getF4MLinksWithMeta(uri)
                videoUrls.extend(retTab)
            else:
                videoUrls.append({'name':'direct link', 'url':uri})
        return videoUrls
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Urllist.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Urllist.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if None == name:
            self.listsTab(self.MAIN_GROUPED_TAB, self.currItem)
        else:
            self.listCategory(self.currItem)
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Urllist(), True)
        
    def _isPicture(self, url):
        def _checkExtension(url): 
            return url.endswith(".jpeg") or url.endswith(".jpg") or url.endswith(".png")
        if _checkExtension(url): return True
        if _checkExtension(url.split('|')[0]): return True
        if _checkExtension(url.split('?')[0]): return True
        return False

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('urllistlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        uri = self.host.currList[Index].get('url', '')
        if not self._isPicture(uri):
            urlList = self.host.getLinksForVideo(self.host.currList[Index])
            for item in urlList:
                retlist.append(CUrlItem(item["name"], item["url"], 0))
        else: retlist.append(CUrlItem('picture link', urlparser.decorateParamsFromUrl(uri, True), 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Filmy", "filmy"))
        #searchTypesOptions.append(("Seriale", "seriale"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if self._isPicture(url):
                    type = CDisplayListItem.TYPE_PICTURE
                else:
                    type = CDisplayListItem.TYPE_VIDEO
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  clean_html(cItem.get('desc', ''))
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

    def getSearchItemInx(self):
        # Find 'Wyszukaj' item
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'Wyszukaj':
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