# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetLogoDir, FreeSpace as iptvtools_FreeSpace, GetIconDirBaseName, GetNewIconsDirName, mkdirs
from Plugins.Extensions.IPTVPlayer.tools.iptvfilehost import IPTVFileHost
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.md5Hash import MD5
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigPassword, ConfigDirectory, getConfigListEntry, NoSave
import re
import codecs
import time
from binascii import hexlify
from os import path, system, remove
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.Sciezkaurllist = ConfigDirectory(default = "/tmp/")
config.plugins.iptvplayer.grupujurllist  = ConfigYesNo(default = True)
config.plugins.iptvplayer.sortuj         = ConfigYesNo(default = True)
config.plugins.iptvplayer.urllist_showrafalcool1 = ConfigYesNo(default = True)
config.plugins.iptvplayer.useTMDB = ConfigYesNo(default = False)
config.plugins.iptvplayer.showXXXlinks = ConfigYesNo(default = True)
config.plugins.iptvplayer.protectHostWithPin = ConfigSelection(default = 'none', choices = [("host", "hosta"),("xxx", "kategorii dla dorosłych"),("none", "nie wymagaj")])
config.plugins.iptvplayer.XXXlinksPinEntered = NoSave(ConfigPassword(default = ' :P ', fixed_size = True))
config.plugins.iptvplayer.excludeFromList = ConfigSelection(default = '', choices = [("", "wyświetlaj wszystko"),("zwiastun", "zwiastunów")])

def GetConfigList():
    optionList = [] 
    optionList.append(getConfigListEntry('Pobierz listę do:', config.plugins.iptvplayer.Sciezkaurllist))    
    optionList.append(getConfigListEntry('Pobierz brakującą okładkę i opis z web:', config.plugins.iptvplayer.useTMDB))    
    optionList.append(getConfigListEntry('Nie wyświetlaj:', config.plugins.iptvplayer.excludeFromList))    
    optionList.append(getConfigListEntry('Wyświetl listę dla dorosłych:', config.plugins.iptvplayer.showXXXlinks))
    optionList.append(getConfigListEntry('Wymagaj pin przy wejściu do:', config.plugins.iptvplayer.protectHostWithPin))    
    optionList.append(getConfigListEntry('Podaj pin wtyczki:', config.plugins.iptvplayer.XXXlinksPinEntered))    
    #optionList.append(getConfigListEntry(_('Show recommended by Rafalcool1:'), config.plugins.iptvplayer.urllist_showrafalcool1))
    #optionList.append(getConfigListEntry(_('Sort the list:'), config.plugins.iptvplayer.sortuj))
    #optionList.append(getConfigListEntry(_('Group links into categories: '), config.plugins.iptvplayer.grupujurllist))
    return optionList
###################################################

def gettytul():
    return ('Rafalcoo1 proponuje')

class Urllist(CBaseHostClass):
    RAFALCOOL1_FILE  = 'urllist_hostrafalcool1.txt'
    URLLIST_FILE     = 'urllist_hostrafalcool1.pin'
    URRLIST_STREAMS  = 'urllist_hostrafalcool1.stream'
    URRLIST_ADULT     = 'urllist_hostrafalcool1.XXX'
    
    def __init__(self):
        printDBG("Urllist.__init__")
        
        self.MAIN_GROUPED_TAB = [{'category': self.RAFALCOOL1_FILE,    'title': ("Propozycje Rafalcool1"),        'desc': ("Lista filmów wybranych przez kolegę Rafalcool1")}]
        if config.plugins.iptvplayer.showXXXlinks.value == True:
            self.MAIN_GROUPED_TAB.append( {'category': self.URRLIST_ADULT,    'title': ("Propozycje dla dorosłych..."),        'desc': ("Musisz podać prawidłowy PIN w konfiguracji hosta")})
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
        
    def updateRafalcoolFile(self, fileName, filePath, encoding):
        printDBG("Urllist.updateRafalcoolFile filePath[%s]" % filePath)
        remoteVersion = -1
        localVersion = -1
        # get version from file
        if path.exists(filePath):
            try:
                with codecs.open(filePath, 'r', encoding, 'replace') as fp:
                    # version should be in first line
                    line = fp.readline()
                    localVersion = int(self.cm.ph.getSearchGroups(line + '|', '#file_version=([0-9]+?)[^0-9]')[0])
            except:
                printExc()
        
        # generate timestamp to add to url to skip possible cacheing
        timestamp = str(time.time())
        
        # if we have loacal version get remote version for comparison
        if localVersion != '':
            sts, data = self.cm.getPage("http://hybrid.xunil.pl/IPTVPlayer_resources/UsersFiles/urllist_hostrafalcool1.version")
            if sts:
                try:
                    remoteVersion = int(data.strip())
                except:
                    printExc()
        # uaktualnij versje
        printDBG('Urllist.updateRafalcoolFile localVersion[%d] remoteVersion[%d]' % (localVersion, remoteVersion))
        if remoteVersion > -1 and localVersion < remoteVersion:
            sts, data = self.cm.getPage("http://hybrid.xunil.pl/IPTVPlayer_resources/UsersFiles/" + fileName + "?t=" + timestamp)
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
                except:
                    printExc()
        
    def listCategory(self, cItem, searchMode=False):
        printDBG("Urllist.listCategory cItem[%s]" % cItem)
        
        sortList = config.plugins.iptvplayer.sortuj.value
        filespath = config.plugins.iptvplayer.Sciezkaurllist.value
        groupList = config.plugins.iptvplayer.grupujurllist.value
        if cItem['category'] in ['all', Urllist.URLLIST_FILE, Urllist.URRLIST_STREAMS, Urllist.URRLIST_ADULT, Urllist.RAFALCOOL1_FILE]:
            self.currFileHost = IPTVFileHost()
            if cItem['category'] in ['all', Urllist.RAFALCOOL1_FILE] and config.plugins.iptvplayer.urllist_showrafalcool1.value:
                self.updateRafalcoolFile(self.RAFALCOOL1_FILE, filespath + Urllist.RAFALCOOL1_FILE, encoding='utf-8')
                self.currFileHost.addFile(filespath + Urllist.RAFALCOOL1_FILE, encoding='utf-8')
            
            #if cItem['category'] in ['all', Urllist.URLLIST_FILE]: 
            #    self.currFileHost.addFile(filespath + Urllist.URLLIST_FILE, encoding='utf-8')
            #if cItem['category'] in ['all', Urllist.URRLIST_STREAMS]: 
            #    self.currFileHost.addFile(filespath + Urllist.URRLIST_STREAMS, encoding='utf-8')
                
            if cItem['category'] in ['all', Urllist.URRLIST_ADULT]:
                if config.plugins.iptvplayer.protectHostWithPin.value != 'xxx' or config.plugins.iptvplayer.XXXlinksPinEntered.value == config.plugins.iptvplayer.pin.value:
                    self.updateRafalcoolFile(self.URRLIST_ADULT, filespath + Urllist.URRLIST_ADULT, encoding='utf-8')
                    self.currFileHost.addFile(filespath + Urllist.URRLIST_ADULT, encoding='utf-8')
            
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
            if iptvtools_FreeSpace(config.plugins.iptvplayer.SciezkaCache.value, 10):
                downloadPath = config.plugins.iptvplayer.SciezkaCache.value
                cacheTMDB = True
            else:
                downloadPath = config.plugins.iptvplayer.NaszaTMP.value
                cacheTMDB = False
            for item in tmpList:
                if '' == item['title_in_group']:
                    title = item['full_title']
                else:
                    title = item['title_in_group']
                    
                #desc = (_("Hosting: %s, %s")) % (self._getHostingName(item['url']), item['url'])
                #if item.get('desc', '') != '':
                #    desc = item['desc']
                if config.plugins.iptvplayer.excludeFromList.value == '' or not re.search(config.plugins.iptvplayer.excludeFromList.value, title, flags=re.I):
                    if item.get('desc', '') == '' and item.get('icon', '') == '' and config.plugins.iptvplayer.useTMDB.value == True:
                        desc, cover = downloadData(item['url'], title, config.plugins.iptvplayer.wgetpath.value, downloadPath, cacheTMDB )
                    else:
                        desc = item.get('desc', '')
                        cover = item.get('icon', '')
                    params = {'title':title, 'url':item['url'], 'desc': desc, 'icon': cover}
                    
                    self.addVideo(params)
                
    def getLinksForVideo(self, cItem):
        printDBG("Urllist.getLinksForVideo url[%s]" % cItem['url'])
        videoUrls = []
        uri, params   = DMHelper.getDownloaderParamFromUrl(cItem['url'])
        printDBG(params)
        uri = urlparser.decorateUrl(uri, params)
        
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
        
    def isProtectedByPinCode(self):
        if config.plugins.iptvplayer.protectHostWithPin.value == "host":
            return True
        else:
            return False
        
    def _isPicture(self, url):
        def _checkExtension(url): 
            return url.endswith(".jpeg") or url.endswith(".jpg") or url.endswith(".png")
        if _checkExtension(url): return True
        if _checkExtension(url.split('|')[0]): return True
        if _checkExtension(url.split('?')[0]): return True
        return False

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('rafalcool1logo.png')])

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
        except:
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
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
        
        
#####################################################################################################
def ClearMemory(): #avoid GS running os.* (e.g. os.system) on tuners with small RAM
    with open("/proc/sys/vm/drop_caches", "w") as f: f.write("1\n")

def cleanFile(text):
    #text=getNameWithoutExtension(text)
    cutlist = ['x264','h264','720p','1080p','1080i','PAL','GERMAN','ENGLiSH','ENG', 'RUS', 'WS','DVDRiP','UNRATED','RETAIL','Web-DL','DL','LD','MiC','MD','DVDR','BDRiP','BLURAY','DTS','UNCUT',
                'ANiME','AC3MD','AC3','AC3D','TS','DVDSCR','COMPLETE','INTERNAL','DTSD','XViD','DIVX','DUBBED','LINE.DUBBED','DD51','DVDR9','DVDR5','AVC','WEBHDTVRiP','WEBHDRiP','WEBRiP',
                'WEBHDTV','WebHD','HDTVRiP','HDRiP','HDTV','ITUNESHD','REPACK','SYNC','REAL','PL']
    
    for word in cutlist:
        #text = re.sub('(\_|\-|\.|\+)'+word+'(\_|\-|\.|\+)','+', text, flags=re.I)
        text = re.sub('(\_|\-|\.|\+)'+word+'.*','.', text, flags=re.I) #assumtion is everything after garbage is garbadge too. ;)
    #text = re.sub('(\_|\-|\.|\+)[12][0-9][0-9][0-9]\+.*','', text, flags=re.I) #if there is plus sign after date, date is most probably the garbage, so removing it ;)
    
    #let's take a year, if exists
    try:
        movieYear=re.sub('(\_|\-|\.|\+|\()','', re.search('(\_|\-|\.|\+|\()[12][09][0-9][0-9]', text, flags=re.I).group() ) #for future use
    except:
        movieYear=''
    
    #removing exact character combinations
    ExactCutList = ['(\_|\-|\.|\+|\()[12][09][0-9][0-9](\_|\-|\.|\+|\))','^psig-','^[12][09][0-9]* [0-9][0-9]* - .* - ', '-[ ]*zwiastun']
    for word in ExactCutList:
        text = re.sub(word,'', text, flags=re.I) #assumtion is everything after garbage is garbadge too. ;)
        
    text = re.sub('(\_|\-|\.|\+)',' ', text, flags=re.I) #cleaning
    text = re.sub('(  [ ]*)',' ', text, flags=re.I) #merge multiple (2+) spaces into one

    return text, movieYear
    
def DecodeNationalLetters(text):
    #polskie litery
    text = text.replace('ą','a').replace('ę','e').replace('ś','s').replace('ć','c').replace('ż','z').replace('ź','z').replace('ł','l').replace('ń','n')
    text = text.replace('Ą','A').replace('Ę','E').replace('Ś','S').replace('Ć','C').replace('Ż','Z').replace('Ź','Z').replace('Ł','L').replace('Ń','N')
    return text.strip()

def ConvertChars(text):
    CharsTable={ '\xC2\xB1': '\xC4\x85','\xC2\xB6': '\xC5\x9b','\xC4\xBD': '\xC5\xba'}
    for i, j in CharsTable.iteritems():
        text = text.replace(i, j)
    return text

def downloadData(movieUrl, movieTitle, wgetpath, downloadPath, cacheTMDB = False ):
    if cacheTMDB == False:
        cachedDataFileName = '%s/rafalcool1.tmdb' % downloadPath
    else:
        hashAlg = MD5()
        fullPath= '%s/%s1444444441.144441/'.replace('//','/') % (downloadPath, GetIconDirBaseName() )
        cachedDataFileName = fullPath + hexlify(hashAlg(movieUrl[7:])) + '.jpg'
        if not path.exists(fullPath):
            mkdirs(fullPath)
        
    descr = ''
    coverUrl = ''
    ClearMemory()
    Webmovie, movieYear =cleanFile(movieTitle)
    Webmovie=DecodeNationalLetters(Webmovie)
    Webmovie=ConvertChars(Webmovie)
    url = "http://api.themoviedb.org/3/search/movie?api_key=8789cfd3fbab7dccf1269c3d7d867aff&query=%s&language=pl" % Webmovie
    if cacheTMDB == False:
        system('rm -f %s;%s "%s" -O %s' % (cachedDataFileName, wgetpath, url, cachedDataFileName))
    else:
        if not path.exists(cachedDataFileName):
            system('%s "%s" -O %s' % (wgetpath, url, cachedDataFileName))
    if path.exists(cachedDataFileName):
        with open(cachedDataFileName,'r') as tmdbDATA: myData = tmdbDATA.read()
        list = re.findall('"poster_path":"(.*?)".*?"overview":"(.*?)".*?"release_date":"(.*?)".*?"id":(.*?),.*?"original_title":"(.*?)".*?"original_language":"(.*?)".*?"title":"(.*?)".*?"popularity":([\.0-9]*).*?"vote_average":([\.0-9]*).*?', myData, re.S)

        myData=None # some cleanup, just in case
        if list is None or len(list) == 0:
            remove(cachedDataFileName) # kasujemy z cache pliki nie zawierajace danych
        else:
            if movieYear != '':
                printDBG("filtering movies list by release year %s" % movieYear)
                for coverPath,overview,release_date,id,otitle,original_language,title,popularity,vote_average in list:
                    if movieYear in release_date:
                        coverUrl = "http://image.tmdb.org/t/p/w185%s" % coverPath
                        coverUrl = coverUrl.replace('\/','/')
                        #print "[CoverFind] " + title, coverUrl
                        descr=overview + '<br/>' + 'Premiera: ' + release_date + '<br/>' + 'Popularność: ' + popularity + '<br/>' + 'Ocena: ' + vote_average
                        return descr, coverUrl
                            
            coverPath,overview,release_date,id,otitle,original_language,title,popularity,vote_average = list[0]
            coverUrl = "http://image.tmdb.org/t/p/w185%s" % coverPath
            coverUrl = coverUrl.replace('\/','/')
            #print "[CoverFind] " + title, coverUrl
            descr=overview + '<br/>' + 'Premiera: ' + release_date + '<br/>' + 'Popularność: ' + popularity + '<br/>' + 'Ocena: ' + vote_average

    return descr, coverUrl