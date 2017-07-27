# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import datetime, timedelta, date
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except Exception: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################
config.plugins.iptvplayer.tvpvod_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.tvpvod_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.tvpvod_password = ConfigText(default = "", fixed_size = False)

config.plugins.iptvplayer.tvpVodProxyEnable = ConfigYesNo(default = False)
config.plugins.iptvplayer.tvpVodDefaultformat = ConfigSelection(default = "590000", choices = [("360000",  "320x180"),
                                                                                               ("590000",  "398x224"),
                                                                                               ("820000",  "480x270"),
                                                                                               ("1250000", "640x360"),
                                                                                               ("1750000", "800x450"),
                                                                                               ("2850000", "960x540"),
                                                                                               ("5420000", "1280x720"),
                                                                                               ("6500000", "1600x900"),
                                                                                               ("9100000", "1920x1080") ])
config.plugins.iptvplayer.tvpVodUseDF    = ConfigYesNo(default = True)
config.plugins.iptvplayer.tvpVodNextPage = ConfigYesNo(default = True)
config.plugins.iptvplayer.tvpVodPreferedformat = ConfigSelection(default = "mp4", choices = [("mp4",  "MP4"), ("m3u8",  "HLS/m3u8")])

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Strefa Widza", config.plugins.iptvplayer.tvpvod_premium))
    if config.plugins.iptvplayer.tvpvod_premium.value:
        optionList.append(getConfigListEntry("  email:", config.plugins.iptvplayer.tvpvod_login))
        optionList.append(getConfigListEntry("  hasło:", config.plugins.iptvplayer.tvpvod_password))
    optionList.append(getConfigListEntry("Peferowany format wideo",               config.plugins.iptvplayer.tvpVodPreferedformat))
    optionList.append(getConfigListEntry("Domyślna jakość wideo",           config.plugins.iptvplayer.tvpVodDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnej jakości wideo:", config.plugins.iptvplayer.tvpVodUseDF))
    optionList.append(getConfigListEntry("Korzystaj z proxy?",              config.plugins.iptvplayer.tvpVodProxyEnable))
    #optionList.append(getConfigListEntry("Więcej jako następna strona",     config.plugins.iptvplayer.tvpVodNextPage))
    return optionList
###################################################

def gettytul():
    return 'vod.tvp.pl'

class TvpVod(CBaseHostClass):
    DEFAULT_ICON_URL = 'https://s.tvp.pl/files/vod.tvp.pl/img/menu/logo_vod.png' #'http://sd-xbmc.org/repository/xbmc-addons/tvpvod.png'
    PAGE_SIZE = 12
    ALL_FORMATS = [{"video/mp4":"mp4"}, {"application/x-mpegurl":"m3u8"}, {"video/x-ms-wmv":"wmv"}] 
    REAL_FORMATS = {'m3u8':'ts', 'mp4':'mp4', 'wmv':'wmv'}
    MAIN_VOD_URL = "https://vod.tvp.pl/"
    LOGIN_URL = "https://www.tvp.pl/sess/ssologin.php"
    STREAMS_URL_TEMPLATE = 'http://www.api.v3.tvp.pl/shared/tvpstream/listing.php?parent_id=13010508&type=epg_item&direct=false&filter={%22release_date_dt%22:%22[iptv_date]%22,%22epg_play_mode%22:{%22$in%22:[0,1,3]}}&count=-1&dump=json'
    SEARCH_VOD_URL = MAIN_VOD_URL + 'szukaj?query=%s'
    IMAGE_URL = 'http://s.v3.tvp.pl/images/%s/%s/%s/uid_%s_width_500_gs_0.%s'
    HTTP_HEADERS = {}
    
    
    VOD_CAT_TAB  = [{'category':'tvp_sport',           'title':'TVP Sport',                 'url':'http://sport.tvp.pl/wideo'},
                    {'category':'streams',             'title':'TVP na żywo',               'url':'http://tvpstream.tvp.pl/'},
                    {'category':'vods_explore_item',   'title':'Przegapiłeś w TV?',         'url':MAIN_VOD_URL + 'przegapiles-w-tv'},
                    {'category':'vods_list_cats',      'title':'Katalog',                   'url':MAIN_VOD_URL},
                    #{'category':'vods_explore_item',   'title':'Programy',                  'url':MAIN_VOD_URL + 'category/programy,4934948'},
                    
                    #{'category':'vods_list_items1',    'title':'Polecamy',                  'url':MAIN_VOD_URL},
                    #{'category':'vods_sub_categories', 'title':'Polecane',                  'marker':'Polecane'},
                    #{'category':'vods_sub_categories', 'title':'VOD',                       'marker':'VOD'},
                    #{'category':'vods_sub_categories', 'title':'Programy',                  'marker':'Programy'},
                    #{'category':'vods_sub_categories', 'title':'Informacje i publicystyka', 'marker':'Informacje i publicystyka'},
                    {'category':'search',          'title':_('Search'), 'search_item':True},
                    {'category':'search_history',  'title':_('Search history')} ]
                    
    STREAMS_CAT_TAB = [{'icon':DEFAULT_ICON_URL, 'category':'tvp3_streams', 'title':'TVP 3',     'url':'http://tvpstream.tvp.pl/', 'icon':'http://ncplus.pl/~/media/n/npl/kanaly/logo%20na%20strony%20kanalow/tvp3.png?bc=white&w=480'},
                       {'icon':DEFAULT_ICON_URL, 'category':'week_epg',     'title':'TVP SPORT', 'url':STREAMS_URL_TEMPLATE,       'icon':'https://upload.wikimedia.org/wikipedia/commons/9/9d/TVP_Sport_HD_Logo.png'},
                      ]
    
    def __init__(self):
        printDBG("TvpVod.__init__")
        CBaseHostClass.__init__(self, {'history':'TvpVod', 'cookie':'tvpvod.cookie', 'cookie_type':'MozillaCookieJar', 'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.tvpVodProxyEnable.value})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':TvpVod.HTTP_HEADERS}
        self.loggedIn = None
        self.fixUrlMap = {'nadobre.tvp.pl':        'http://vod.tvp.pl/8514270/na-dobre-i-na-zle',
                          'mjakmilosc.tvp.pl':     'http://vod.tvp.pl/1654521/m-jak-milosc',
                          'barwyszczescia.tvp.pl': 'http://vod.tvp.pl/8514286/barwy-szczescia',
                          'nasygnale.tvp.pl':      'http://vod.tvp.pl/13883615/na-sygnale'}
        self.FormatBitrateMap = [ ("360000",  "320x180"), ("590000",  "398x224"), ("820000",  "480x270"), ("1250000", "640x360"),
                                  ("1750000", "800x450"), ("2850000", "960x540"), ("5420000", "1280x720"), ("6500000", "1600x900"), ("9100000", "1920x1080") ]
    
    def getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return str(v)
    
    def getImageUrl(self, item):
        keys = ['logo_4x3', 'image_16x9', 'image_4x3', 'image_ns954', 'image_ns644', 'image']
        iconFile = ""
        for key in keys:
            if None != item.get(key, None):
                iconFile = self.getJItemStr( item[key][0], 'file_name')
            if len(iconFile):
                tmp = iconFile.split('.')
                return self.IMAGE_URL % (iconFile[0], iconFile[1], iconFile[2], tmp[0], tmp[1])
        return ''
        
    def _getPage(self, url, addParams = {}, post_data = None):
        
        try:
            import httplib
            def patch_http_response_read(func):
                def inner(*args):
                    try:
                        return func(*args)
                    except httplib.IncompleteRead, e:
                        return e.partial
                return inner
            prev_read = httplib.HTTPResponse.read
            httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)
        except Exception: printExc()
        sts, data = self.cm.getPage(url, addParams, post_data)
        try: httplib.HTTPResponse.read = prev_read
        except Exception: printExc()
        return sts, data
        
    def _getStr(self, v, default=''):
        return self.cleanHtmlStr(self._encodeStr(v, default))
        
    def _encodeStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        else: return default
        
    def _getNum(self, v, default=0):
        try: return int(v)
        except Exception:
            try: return float(v)
            except Exception: return default
            
    def _getFullUrl(self, url, baseUrl=None):
        if None == baseUrl: baseUrl = TvpVod.MAIN_VOD_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('//'):
                url = 'http:' + url
            else:
                if not baseUrl.endswith('/'):
                    baseUrl += '/'
                if url.startswith('/'):
                    url = url[1:]
                url =  baseUrl + url
        return url
        
    def getFormatFromBitrate(self, bitrate):
        ret = ''
        for item in self.FormatBitrateMap:
            if int(bitrate) == int(item[0]):
                ret = item[1]
        if '' == ret: ret = 'Bitrate[%s]' % bitrate
        return ret
        
    def getBitrateFromFormat(self, format):
        ret = 0
        for item in self.FormatBitrateMap:
            if format == item[1]:
                ret = int(item[0])
        return ret
     
    def tryTologin(self):
        email = config.plugins.iptvplayer.tvpvod_login.value
        password = config.plugins.iptvplayer.tvpvod_password.value
        msg = 'Wystąpił problem z zalogowaniem użytkownika "%s"!' % email
        params = dict(self.defaultParams)
        params.update({'load_cookie': False})
        sts, data = self._getPage(TvpVod.LOGIN_URL, params)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<fieldset>', '</fieldset>', False)[1]
            ref = self.cm.ph.getSearchGroups(data, 'name="ref".+?value="([^"]+?)"')[0]
            login = self.cm.ph.getSearchGroups(data, 'name="login".+?value="([^"]+?)"')[0]
            post_data = {'ref':ref, 'email':email, 'password':password, 'login':login, 'action':'login'}
            sts, data = self._getPage(TvpVod.LOGIN_URL, self.defaultParams, post_data)
            if sts and '"/sess/passwordreset.php"' not in data:
                if "Strefa Widza nieaktywna" in data:
                    msg = "Strefa Widza nieaktywna."
                    sts = False
                else:
                    msg = 'Użytkownik "%s" zalogowany poprawnie!' % email
            else: sts = False
        return sts, msg
       
    def listsTab(self, tab, cItem):
        printDBG("TvpVod.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _addNavCategories(self, data, cItem, category):
        data = re.findall('href="([^"]+?)"[^>]*?>([^<]+?)<', data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'title':self.cleanHtmlStr(item[1]), 'url':item[0]})
            self.addDir(params)
            
    def _getAjaxUrl(self, parent_id, location):
        if location == 'directory_series':
            order='';
            type='website'
            template ='listing_series.html'
            direct='&direct=false'
        elif location == 'directory_stats':
            order=''
            type='video'
            template ='listing_stats.html'
            direct='&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        elif location == 'directory_video':
            order='&order=position,1'
            type='video'
            template ='listing.html'
            direct='&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        elif location == 'website':
            order='&order=release_date_long,-1'
            type='video'
            template ='listing.html'
            direct='&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        else:
            order='&order=release_date_long,-1'
            type='video'
            template ='listing.html'
            direct='&filter=%7B%22playable%22%3Atrue%7D&direct=true'
            
        url = '/shared/listing.php?parent_id=' + parent_id + '&type=' + type + order + direct + '&template=directory/' + template + '&count=' + str(TvpVod.PAGE_SIZE) 
                    
        return self._getFullUrl(url)
        
    def listTVP3Streams(self, cItem):
        printDBG("TvpVod.listTVP3Streams")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts: return
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="button', '</div>', withMarkers=True, caseSensitive=False)
        for item in data:
            id    = self.cm.ph.getSearchGroups(item, 'data-video_id="([0-9]+?)"')[0]
            if id != '':
                desc  = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, 'titlte="([^"]+?)"')[0])
                icon  = self.cm.ph.getSearchGroups(item, 'src="(http[^"]+?)"')[0]
                title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0].replace('-', ' ').title()
                params = dict(cItem)
                params.update({'title':title, 'url':'http://tvpstream.tvp.pl/sess/tvplayer.php?object_id=%s&autoplay=true' % id, 'icon':icon, 'desc':desc})
                self.addVideo(params)
                
    def listWeekEPG(self, cItem, nextCategory):
        printDBG("TvpVod.listWeekEPG")
        urlTemplate = cItem['url']
        
        d = datetime.today()
        for i in range(7):
            url    = urlTemplate.replace('[iptv_date]', d.strftime('%Y-%m-%d'))
            title  = d.strftime('%a %d.%m.%Y')
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            d += timedelta(days=1)
            
    def listEPGItems(self, cItem):
        printDBG("TvpVod.listEPGItems")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts: return
        try:
            #date.fromtimestamp(item['release_date']['sec']).strftime('%H:%M')
            data = byteify(json.loads(data))
            data['items'].sort(key=lambda item: item['release_date_hour'])
            for item in data['items']:
                if not item.get('is_live', False): continue 
                title = str(item['title'])
                desc  = str(item['lead'])
                asset_id  = str(item['asset_id'])
                asset_id  = str(item['video_id'])
                icon  = self.getImageUrl(item)
                desc  = item['release_date_hour'] + ' - ' + item['broadcast_end_date_hour'] + '[/br]' + desc 
                self.addVideo({'title':title, 'url':'', 'object_id':asset_id, 'icon':icon, 'desc':desc})
            printDBG(data)
        except Exception:
            printExc()
        
    def listTVPSportCategories(self, cItem, nextCategory):
        printDBG("TvpVod.listTVPSportCategories")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="vod-select">', '<div class="vod-items">', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="option" ', '</div>', withMarkers=True, caseSensitive=False)
        for item in data:
            mode  = self.cm.ph.getSearchGroups(item, 'data-type="([^"]+?)"')[0]
            id    = self.cm.ph.getSearchGroups(item, 'data-id="([0-9]+?)"')[0]
            title = self.cleanHtmlStr(item)
            if id != '':
                if mode == 'popular':
                    copy   = 'true'
                    direct = 'true'
                    order  = 'position,1'
                    filter = '{"types.1":"video","play_mode":1}'
                else:
                    copy   = 'false'
                    direct = 'false'
                    order  = 'release_date_long,-1'
                    if mode == 'newest': filter = '{"types.1":"video","parents":{"$in":[432801,434339,548368]},"copy":false,"play_mode":1}'
                    else: filter = '{"types.1":"video","copy":false,"play_mode":1}'
                    
                url = 'http://sport.tvp.pl/shared/listing.php?parent_id=' + id + '&type=v_listing_typical_a&direct=' + direct +'&order=' + order + '&copy=' + copy + '&mode=' + mode + '&filter=' + urllib.quote(filter) + '&template=vod/items-listing.html&count=' + str(self.PAGE_SIZE)
                params = dict(cItem)
                params.update({'category':nextCategory, 'good_for_fav':True, 'title':title, 'url':url})
                self.addDir(params)
              
    def listTVPSportVideos(self, cItem):
        printDBG("TvpVod.listTVPSportVideos")
        
        page = cItem.get('page', 1)
        videosNum = 0
        
        url  = cItem['url']
        url += '&page=%d' %(page)
        
        sts, data = self._getPage(url, self.defaultParams)
        if not sts: return
        data = data.split('<div class="item')
        if len(data): del data[0]
        
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'data-url="([^"]+?)"')[0]
            if url.startswith('/'):
                url = 'http://sport.tvp.pl/' + url
            
            item  = item.split('class="item-data">')[-1]
            desc  = self.cleanHtmlStr(item)
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1] )
            if url.startswith('http'):
                videosNum += 1
                params = dict(cItem)
                params.update({'title':title, 'icon':icon, 'url':url, 'desc':desc})
                self.addVideo(params)
                
        if videosNum >= self.PAGE_SIZE:
            params = dict(cItem)
            params.update({'page':page+1})
            if config.plugins.iptvplayer.tvpVodNextPage.value:
                params['title'] = _("Następna strona")
                self.addDir(params)
            else:
                params['title'] = _('More')
                self.addMore(params)
                
    def listCatalog(self, cItem, nextCategory):
        printDBG("TvpVod.listCatalog")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts: return []

        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="subMenu">', '</ul>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':self.cleanHtmlStr(item).title(), 'url':url, 'desc':''})
            self.addDir(params)
            
    def mapHoeverItem(self, cItem, item, nextCategory):
        try:
            item = byteify(json.loads(item))
            title = self.getJItemStr(item, 'title')
            icon = self._getFullUrl(self.getJItemStr(item, 'image'))
            tmp = []
            for key in ['transmision', 'antena', 'age']:
                val = self.getJItemStr(item, key)
                if val != '': tmp.append(val)
            desc = ' | '.join(tmp)
            desc += '[/br]' + self.getJItemStr(item, 'description')
            
            params = {'good_for_fav': True, 'icon':icon, 'desc':self.cleanHtmlStr(desc)}
            seriesLink = self._getFullUrl(self.getJItemStr(item, 'seriesLink'))
            episodeUrl = self._getFullUrl(self.getJItemStr(item, 'episodeLink'))
            
            if self.cm.isValidUrl(episodeUrl) and  '/video/' in episodeUrl:
                title += ' ' + self.getJItemStr(item, 'episodeCount')
                params.update({'title':title, 'url':episodeUrl})
                self.addVideo(params)
            else:
                params.update({'category':nextCategory, 'title':title, 'url':seriesLink})
                self.addDir(params)
            
            printDBG("======================")
            printDBG(item)
        except Exception:
            printExc()
                
    def exploreVODItem(self, cItem, nextCategory):
        printDBG("TvpVod.exploreVODItem")
        
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        if '/szukaj?query=' in cItem['url']:
            isSearch = True
        else:
            isSearch = False
            
        printDBG(">>>>>>>>>>>>. isSearch [%s]" % isSearch)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<section class="episodes"', '</h1>')[1]
        if self.cleanHtmlStr(tmp) == "Odcinki":
            url = self._getFullUrl(self.cm.ph.getSearchGroups(tmp, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
            if self.cm.isValidUrl(url):
                cItem = dict(cItem)
                cItem['url'] = url
                sts, data = self._getPage(cItem['url'], self.defaultParams)
                if not sts: return []
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        
        page = cItem.get('page', 1)
        lastPage = self.cm.ph.getDataBeetwenMarkers(data, '<li class="lastItem"', '</li>')[1]
        lastPage = self.cm.ph.getSearchGroups(lastPage, '''<a[^>]+?href\s*=\s*['"][^'^"]*?page=([0-9]+?)[^0-9]''')[0]
        if lastPage != '' and page < int(lastPage):
            nextPageUrl = self.cm.ph.getDataBeetwenMarkers(data, '<li class="next"', '</li>')[1]
            nextPageUrl = self._getFullUrl(self.cm.ph.getSearchGroups(nextPageUrl, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
        else: nextPageUrl = ''
        
        sectionsData = self.cm.ph.getDataBeetwenMarkers(data, '<section', '<footer>')[1]
        sectionsData = sectionsData.split('<section')
        if len(sectionsData): del sectionsData[0]
        
        subFiltersData = self.cm.ph.getAllItemsBeetwenMarkers(data, '"dropdown-menu"', '</ul>')
        #subFiltersData.reverse()
        allSubFiltersTab = []
        for idx in range(len(subFiltersData)):
            subFilterData = self.cm.ph.getAllItemsBeetwenMarkers(subFiltersData[idx], '<li', '</li>')
            subFiltersTab = []
            for item in subFilterData:
                url = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                params = dict(cItem)
                params.update({'good_for_fav': False, 'category':nextCategory, 'title':self.cleanHtmlStr(item), 'url':url, 'desc':''})
                subFiltersTab.append(params)
            if len(subFiltersTab):
                allSubFiltersTab.append(subFiltersTab)
        
        subFiltersTab = []
        subFiltersNames = []
        for subFiltersTab in allSubFiltersTab:
            subFiltersNames = list(cItem.get('sub_filters_names', []))
            for params in subFiltersTab:
                if params['title'] in subFiltersNames:
                    subFiltersTab = []
                    break
                subFiltersNames.append(params['title'])
            if len(subFiltersTab):
                break
            
        for params in subFiltersTab:
            params['sub_filters_names'] = subFiltersNames
            self.addDir(params)
        
        if len(self.currList):
            return
                
        if isSearch:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'serachContent', '</section>')[1]
        else:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="contentList', '</section>')[1]
        if data != '':
            if isSearch:
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="item', '</a>')
            else:
                data = data.split('<div class="subCategoryMobile">')[0]
                data = data.split('<div class="col-md') #re.split('<div class="col-md[^>]+?>', data)
                if len(data): del data[0]
            for item in data:
                item = clean_html(self.cm.ph.getSearchGroups(item, '''data-hover\s*=\s*['"]([^'^"]+?)['"]''')[0])
                self.mapHoeverItem(cItem, item, nextCategory)
        else:
            for section in sectionsData:
                sectionHeader = self.cm.ph.getDataBeetwenMarkers(section, '<h1', '</h1>')[1]
                if sectionHeader == '': sectionHeader = self.cm.ph.getDataBeetwenMarkers(section, '<h2>', '</h2>')[1]
                sectionUrl    = self._getFullUrl(self.cm.ph.getSearchGroups(sectionHeader, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
                sectionIcon   = self._getFullUrl(self.cm.ph.getSearchGroups(section, '''<img[^>]+?data-lazy\s*=\s*['"]([^'^"]+?)['"]''')[0])
                sectionTitle  = self.cleanHtmlStr(sectionHeader)
                
                if self.cm.isValidUrl(sectionUrl):
                    if '>Oglądaj<' in section: continue
                    if sectionTitle.startswith('Zobacz także:'): continue
                    params = dict(cItem)
                    params.update({'good_for_fav': False, 'category':nextCategory, 'title':sectionTitle, 'url':sectionUrl, 'icon':sectionIcon, 'desc':''})
                    self.addDir(params)
                elif (len(self.currList) == 0 and sectionTitle in ['Przeglądaj', 'Wideo', 'Oglądaj']) or isSearch:
                    tmp = self.cm.ph.getAllItemsBeetwenMarkers(section, '<div class="item', '</a>')
                    for item in tmp:
                        icon = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''<img[^>]+?data-lazy\s*=\s*['"]([^'^"]+?)['"]''')[0])
                        if icon == '': icon = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''<img[^>]+?src\s*=\s*['"]([^'^"]+?\.jpg)['"]''')[0])
                        url  = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''<a[^>]+?href\s*=\s*['"]([^'^"]+?)['"]''')[0])
                        
                        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h3>')[1])
                        if title == '': title = self.cleanHtmlStr(item)
                        if self.cm.isValidUrl(url):
                            params = dict(cItem)
                            params.update({'good_for_fav': False, 'title':title, 'url':url, 'icon':icon, 'desc':''})
                            if '/video/' in url:
                                params['good_for_fav'] = True
                                self.addVideo(params)
                            else:
                                params.update({'category':nextCategory,})
                                self.addDir(params)
                    if len(self.currList) and not isSearch:
                        break
        
        if self.cm.isValidUrl(nextPageUrl):
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'title':_("Next page"), 'url':nextPageUrl, 'page':page+1})
            self.addDir(params)
            
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TvpVod.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        url = TvpVod.SEARCH_VOD_URL % urllib.quote(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = url
        
        self.exploreVODItem(cItem, 'vods_explore_item')
        
    def listsMenuGroups(self, cItem, category):
        printDBG("TvpVod.listsGroupsType1")
        url = self._getFullUrl(cItem['url'])
        sts, data = self._getPage(url, self.defaultParams)
        if sts:
            # check if 
            data = self.cm.ph.getDataBeetwenMarkers(data, '<section id="menu"', '</section>', False)[1]
            self._addNavCategories(data, cItem, category)
        
                
    def listItems2(self, cItem, category, data):
        printDBG("TvpVod.listItems2")
        itemMarker = '<div class="'
        sectionMarker = '<section id="emisje">'

        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'class="siteNewscast">', '</section>', False)[1]
        icon = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?)"')[0]
        desc = self.cm.ph.getDataBeetwenMarkers(tmp, '<p>', '</div>', False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, sectionMarker, '</section>', True)[1]
        
        printDBG("TvpVod.listItems2 start parse")
        data = data.split(itemMarker)
        if len(data): del data[0]
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cleanHtmlStr('<' + item)
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url, 'icon':icon, 'desc':desc, 'page':0})
            self.addVideo(params)
            
    def getObjectID(self, url):
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts: return ''
        asset_id = self.cm.ph.getSearchGroups(data, 'object_id=([0-9]+?)[^0-9]')[0]
        if asset_id == '': asset_id = self.cm.ph.getSearchGroups(data, 'class="playerContainer"[^>]+?data-id="([0-9]+?)"')[0]
        return asset_id
                
    def getLinksForVideo(self, cItem):
        asset_id = str(cItem.get('object_id', ''))
        url = self._getFullUrl(cItem.get('url', ''))
        
        if 'tvpstream.tvp.pl' in url:
            sts, data = self.cm.getPage(url)
            if not sts: return []
            
            hlsUrl = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]*?\.m3u8[^'^"]*?)['"]''')[0]
            if '' != hlsUrl:
                videoTab = getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=False)
                if 1 < len(videoTab):
                    max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)
                    def __getLinkQuality( itemLink ):
                        if 'with' in itemLink and 'heigth' in itemLink:
                            bitrate = self.getBitrateFromFormat('%sx%s' % (itemLink['with'], itemLink['heigth']))
                            if bitrate != 0: return bitrate
                        return int(itemLink['bitrate'])
                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
                if 1 <= len(videoTab):
                    return videoTab
            
        if '' == asset_id:
            asset_id = self.getObjectID(url)

        return self.getVideoLink(asset_id)
        
    def isVideoData(self, asset_id):
        sts, data = self.cm.getPage( 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?mime_type=video%2Fmp4&object_id=' + asset_id, self.defaultParams)
        if not sts:
            return False
        return not 'NOT_FOUND' in data
        
    def getVideoLink(self, asset_id):
        printDBG("getVideoLink asset_id [%s]" % asset_id)
        sts, data = self.cm.getPage( 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?mime_type=video%2Fmp4&object_id=' + asset_id, self.defaultParams)
        if False == sts:
            printDBG("getVideoLink problem")
        
        videoTab = []
        try:
            data = json.loads( data )
            
            def _getVideoLink(data, FORMATS):
                videoTab = []
                for item in data['formats']:
                    if item['mimeType'] in FORMATS.keys():
                        formatType = FORMATS[item['mimeType']].encode('utf-8')
                        format = self.REAL_FORMATS.get(formatType, '')
                        name = self.getFormatFromBitrate( str(item['totalBitrate']) ) + '\t ' + formatType
                        url = item['url'].encode('utf-8')
                        if 'm3u8' == formatType:
                            videoTab.extend( getDirectM3U8Playlist(url, checkExt=False, variantCheck=False) )
                        else:
                            meta = {'iptv_format':format}
                            if config.plugins.iptvplayer.tvpVodProxyEnable.value:
                                meta['http_proxy'] = config.plugins.iptvplayer.proxyurl.value
                            videoTab.append( {'name' : name, 'bitrate': str(item['totalBitrate']), 'url' : self.up.decorateUrl(url, meta) })
                if 1 < len(videoTab):
                    max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)
                    def __getLinkQuality( itemLink ):
                        if 'with' in itemLink and 'heigth' in itemLink:
                            bitrate = self.getBitrateFromFormat('%sx%s' % (itemLink['with'], itemLink['heigth']))
                            if bitrate != 0: return bitrate
                        return int(itemLink['bitrate'])
                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
                return videoTab
            
            preferedFormats  = []
            if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'm3u8':
                preferedFormats = [TvpVod.ALL_FORMATS[1], TvpVod.ALL_FORMATS[0], TvpVod.ALL_FORMATS[2]]
            else:
                preferedFormats = TvpVod.ALL_FORMATS
            for item in preferedFormats:
                videoTab = _getVideoLink(data, item )
                if len(videoTab):
                    break
        except Exception:
            printExc("getVideoLink exception") 
        return videoTab
        
    def getLinksForFavourite(self, fav_data):
        if None == self.loggedIn:
            premium = config.plugins.iptvplayer.tvpvod_premium.value
            if premium: self.loggedIn, msg = self.tryTologin()
        
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception:
            cItem = {'url':fav_data}
            try:
                ok = int(cItem['url'])
                if ok: return self.getVideoLink(cItem['url'])
            except Exception: pass
        return self.getLinksForVideo(cItem)
        
    def getFavouriteData(self, cItem):
        printDBG('TvpVod.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem.get('desc', ''), 'icon':cItem['icon']}
        if 'list_episodes' in cItem:
            params['list_episodes'] = cItem['list_episodes']
        return json.dumps(params) 
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('TvpVod.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('TvpVod.handleService start')
        if None == self.loggedIn:
            premium = config.plugins.iptvplayer.tvpvod_premium.value
            if premium:
                self.loggedIn, msg = self.tryTologin()
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 10 )

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "TvpVod.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 
        self.currItem.pop('good_for_fav', None)

        if None == name:
            self.listsTab(TvpVod.VOD_CAT_TAB, {'name':'category'})
    # STREAMS
        elif category == 'streams':
            self.listsTab(TvpVod.STREAMS_CAT_TAB, self.currItem)
        elif category == 'tvp3_streams':
            self.listTVP3Streams(self.currItem)
        elif category == 'week_epg':
            self.listWeekEPG(self.currItem, 'epg_items')
        elif category == 'epg_items':
            self.listEPGItems(self.currItem)
    # TVP SPORT
        elif category == 'tvp_sport':    
            self.listTVPSportCategories(self.currItem, 'tvp_sport_list_items')
    # LIST TVP SPORT VIDEOS
        elif category == 'tvp_sport_list_items':
            self.listTVPSportVideos(self.currItem)
        elif category == 'vods_list_cats':
            self.listCatalog(self.currItem, 'vods_explore_item')
        elif category == 'vods_explore_item':
            self.exploreVODItem(self.currItem, 'vods_explore_item')
    #WYSZUKAJ
        elif category == "search":
            cItem = dict(self.currItem)
            cItem.update({'category':'list_search', 'searchPattern':searchPattern, 'searchType':searchType, 'search_item':False})            
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "list_search":
            cItem = dict(self.currItem)
            searchPattern = cItem.get('searchPattern', '')
            searchType    = cItem.get('searchType', '')
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvpVod(), True, [])