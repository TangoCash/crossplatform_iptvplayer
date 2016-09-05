# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from datetime import datetime
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.exua_proxy_enable = ConfigYesNo(default = False)
config.plugins.iptvplayer.exua_language = ConfigSelection(default = "uk", choices = [("ru", "русский"),
                                                                                     ("uk", "українська"),
                                                                                     ("en", "english"),
                                                                                     ("es", "espanol"),
                                                                                     ("de", "deutsch"),
                                                                                     ("fr", "français"),
                                                                                     ("pl", "polski"),
                                                                                     ("ja", "日本語"),
                                                                                     ("kk", "қазақ") ])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Language:"), config.plugins.iptvplayer.exua_language))
    optionList.append(getConfigListEntry(_("Use ru proxy server:"), config.plugins.iptvplayer.exua_proxy_enable))
    return optionList
###################################################


def gettytul():
    return _("http://www.ex.ua/")

class ExUA(CBaseHostClass):
    MAIN_URL = 'http://www.ex.ua/'
    LANG_URL = MAIN_URL + 'language?lang='
    DEFAULT_ICON_URL = 'http://i.obozrevatel.ua/8/1290031/934016.jpg'
    
    MAIN_CAT_TAB = [
                    {'category':'search', 'title': _('Search'), 'search_type':_("Global"), 'original_id':'global', 'search_item':True}
                    #{'category':'search_history', 'title': _('Search history')} 
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'ExUA', 'cookie':'ExUA.cookie', 'cookie_type':'MozillaCookieJar', 'proxyURL': config.plugins.iptvplayer.russian_proxyurl.value, 'useProxy': config.plugins.iptvplayer.exua_proxy_enable.value})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':{'User-Agent': 'Mozilla/5.0'}}
        self.videoCatsCache = []
        
    def getVideoCats(self):
        return self.videoCatsCache
        
    def _getFullUrl(self, url, series=False):
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if url.startswith('/'):
            url = url[1:]
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("ExUA.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if '' == params.get('icon', ''):
                params['icon'] = self.DEFAULT_ICON_URL
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def getMainTab(self, cItem):
        printDBG("ExUA.getMainTab")
        url = self.LANG_URL + config.plugins.iptvplayer.exua_language.value
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<td class=menu_text>', '</td>', False)[1]
        data = re.compile('''<a[^>]*?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)</a>''').findall(data)
        haveAccess = False
        videoCatsUrl = ''
        for item in data:
            if 'video' in item[0] or 'audio' in item[0]:
                params = dict(cItem)
                url = self._getFullUrl(item[0])
                params.update({'name':'category', 'category':'list_items', 'title':item[1], 'url':url, 'icon':self.DEFAULT_ICON_URL})
                self.addDir(params)
                haveAccess = True
        if not haveAccess:
            msg = _("You probably have not access to this page due to geolocation restriction.")
            msg += '\n' + _("You can use Russian proxy server as a workaround.")
            self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 10 )
        return haveAccess
            
    def listItems(self, cItem, m1='class=include_0>'):
        printDBG("ExUA.listMovies")
        url = cItem['url']
        page = cItem.get('page', 0)
        if page > 0:
            if '?' not in url:
                url += '?'
            elif not url.endswith('&'):
                url += '&' 
            url += 'p=%d' % page
        
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return
        
        original_id = self.cm.ph.getSearchGroups(data, '''<input[^>]+?name=original_id[^>]+?value=['"]([0-9]+?)['"]>''', 1, True)[0]
        if original_id != '':
            if 0 == page:
                params = {'category':'search', 'title': _('Search'), 'search_type':cItem['title'], 'original_id':original_id, 'search_item':True}
                self.addDir(params)
        
        nextPage = False
        if 'id="browse_next"' in data:
            nextPage = True
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '</table>', False)[1]
        data = data.split('</td>')
        if len(data):
            del data[-1]
        
        hasItems = False
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)["']''')[0]
            icon   = self.cm.ph.getSearchGroups(item, '''src=["']([^"^']+?)["']''')[0]
            title  = self.cm.ph.getSearchGroups(item, '''alt=["']([^"^']+?)["']''')[0]
            if '' == title:
                title = self.cm.ph.getDataBeetwenMarkers(item, '<b>', '</b>', False)[1]
            title  = self.cleanHtmlStr(title) 
            title  = title.split('/')
            if len(title) > 1:
                try:
                    tmp = title[0].decode('utf-8').encode('ascii')
                except Exception:
                    del data[0]
            title  = '/'.join(title)
            if '/' in url:
                params = dict(cItem)
                params.update( {'title': title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item )} )
                icon = self._getFullUrl(icon)
                if icon.startswith('http'):
                    params['icon'] = icon
                self.addDir(params)
                hasItems = True
        
        if hasItems:
            if nextPage:
                params = dict(cItem)
                if 'rek' in params:
                    params.pop('rek', None)
                params.update( {'title':_('Next page'), 'page':page+1} )
                self.addDir(params)
        else:
            self.listPlayItems(cItem)
            
    def listPlayItems(self, cItem):
        printDBG("ExUA.listPlayItems")
        urlTab = self.getLinksForVideo(cItem)
            
        for item in urlTab:
            params = dict(cItem)
            params.update( item )
            params['title'] = item['name']
            params['fav_url'] = cItem['url']
            type = params.get('type', 'unknown')
            if 'picture' == type:
                self.addPicture(params)
            elif 'audio' == type:
                self.addAudio(params)
            else:
                self.addVideo(params)

    
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        if 0 == cItem.get('rek', 0):
            if 'global' != cItem.get('original_id', ''):
                try:
                    id  = int(cItem['original_id'])
                except Exception:
                    printExc()
                    return
                url = self.MAIN_URL + 'search?original_id={0}&s='.format( id )
            else:
                url = self.MAIN_URL + 'search?s='
            cItem['url'] = url + searchPattern
        cItem['rek'] = 1
        self.listItems(cItem, 'class=panel>')
        
    def getLinksForVideo(self, cItem, withPicture=True):
        printDBG("ExUA.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return urlTab

        meta = {}
        if config.plugins.iptvplayer.exua_proxy_enable.value:
            meta['http_proxy'] = config.plugins.iptvplayer.russian_proxyurl.value
            
        # download urls
        downloadUrls = []
        subTracks = []
        picturesTab = []
        downData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<td width=17>', '</tr>', False)
        for item in downData:
            printDBG(">>>>>>>>>>>>>>>>>>>> [%s]" % item)
            url    = self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)["']''')[0]
            title  = self.cm.ph.getSearchGroups(item, '''title=["']([^"^']+?)["']''')[0]
            if '/get/' not in url:
                continue
            title = self.cleanHtmlStr( title )
            # video
            if 'class="fox-play-btn"' in item: 
                downloadUrls.append({'name':title, 'url':url, 'need_resolve':0})
            elif title.lower().endswith('.srt'):
                subTracks.append({'title':title, 'url':self.up.decorateUrl(self._getFullUrl(url), meta), 'lang':'', 'format':'srt'})
            elif 'picture_0' in item:
                picturesTab.append({'name':title, 'url':self._getFullUrl(url)})
        
        if len (subTracks):
            meta['external_sub_tracks'] = subTracks
        
        # watch urls
        watchUrls   = self.cm.ph.getDataBeetwenMarkers(data, "player_list = '", "';", False)[1]
        watchTitles = self.cm.ph.getDataBeetwenMarkers(data, 'new Array(', ');', False)[1]
        tmpTypes = {}
        try:
            watchUrls   = byteify(json.loads('[%s]' % watchUrls))
            watchTitles = re.compile('''title[^'^"]*?['"]([^'^"]+?)['"]''').findall(watchTitles)
            printDBG(watchTitles)
            for idx in range(len(watchUrls)):
                type  = watchUrls[idx]['type']
                if type not in ['audio', 'video']:
                    type = 'unknown'
                tmpTypes[title] = type
                url   = watchUrls[idx]['url']
                title = watchTitles[idx][:-3] + url[-3:]
                urlTab.append({'name':_('%s [watch]') % title, 'url':self.up.decorateUrl(url, meta), 'need_resolve':0, 'type':type})
        except Exception:
            printExc()
            
        for item in downloadUrls:
            if item['name'].endswith('.mp3'):
                type = 'audio'
            else:
                type = 'unknown'
            item['type'] = tmpTypes.get(item['name'], type)
            item['name'] = _('%s [download]') % item['name']
            item['url'] = self.up.decorateUrl(self._getFullUrl(item['url']), meta)
            urlTab.append(item)
            
        for item in picturesTab:
            item['type'] = 'picture'
            item['need_resolve'] = 0
            urlTab.append(item)
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['fav_url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def getArticleContent(self, cItem):
        printDBG("ExUA.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getDataBeetwenMarkers(data, '</select>', '</div>', False)[1]
        desc  = self.cm.ph.getDataBeetwenMarkers(data, '<p class="description"', '</p>', True)[1]
        icon  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="coverImage">', '</div>', False)[1]
        icon  = self.cm.ph.getSearchGroups(icon, 'href="([^"]*?\.jpg)"')[0]
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="overViewBox">', '</div>', False)[1].split('</dl>')
        printDBG(descData)
        descTabMap = {"Directors":    "director",
                      "Cast":         "actors",
                      "Genres":       "genre",
                      "Country":      "country",
                      "Release Date": "released",
                      "Duration":     "duration"}
        
        otherInfo = {}
        for item in descData:
            item = item.split('</dt>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key in descTabMap:
                otherInfo[descTabMap[key]] = val
        
        imdbRating = self.cm.ph.getDataBeetwenMarkers(data, '<div class="imdbRating', '</p>', True)[1]
        solarRating = self.cm.ph.getDataBeetwenMarkers(data, '<div class="solarRating', '</p>', True)[1]
        
        otherInfo['rating'] = self.cleanHtmlStr( imdbRating )
        otherInfo['rated'] = self.cleanHtmlStr( solarRating )
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
        
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
            self.getMainTab({})
    #MOVIES
        elif category == 'list_items':
            self.listItems(self.currItem)
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
        CHostBase.__init__(self, ExUA(), False, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('exualogo.png')])
    
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
        
    #def getArticleContent(self, Index = 0):
    #    retCode = RetHost.ERROR
    #    retlist = []
    #    if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
    #    cItem = self.host.currList[Index]
    #    
    #    if cItem['type'] != 'video' and cItem['category'] != 'list_seasons':
    #        return RetHost(retCode, value=retlist)
    #    hList = self.host.getArticleContent(cItem)
    #    for item in hList:
    #        title      = item.get('title', '')
    #        text       = item.get('text', '')
    #        images     = item.get("images", [])
    #        othersInfo = item.get('other_info', '')
    #        retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
    #    return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        searchTypesOptions = [] # ustawione alfabetycznie
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
        elif 'picture' == cItem['type']:
            type = CDisplayListItem.TYPE_PICTURE
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_PICTURE]:
            url = cItem.get('url', '')
            need_resolve = cItem.get('need_resolve', 1)
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, need_resolve))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 0,
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
