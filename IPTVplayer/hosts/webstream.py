# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetLogoDir, GetCookieDir, byteify, SaveHostsOrderList, GetHostsOrderList
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, MYOBFUSCATECOM_OIO, MYOBFUSCATECOM_0ll, \
                                                               unpackJS, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils  import clean_html, compat_parse_qs
from Plugins.Extensions.IPTVPlayer.libs.teledunet         import  TeledunetParser
from Plugins.Extensions.IPTVPlayer.libs.urlparser         import urlparser
from Plugins.Extensions.IPTVPlayer.libs.filmonapi         import FilmOnComApi, GetConfigList as FilmOn_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.videostar         import VideoStarApi, GetConfigList as VideoStar_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.weebtv            import WeebTvApi, GetConfigList as WeebTv_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.wagasworld        import WagasWorldApi, GetConfigList as WagasWorld_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.ustvnow           import UstvnowApi, GetConfigList as Ustvnow_GetConfigList
#from Plugins.Extensions.IPTVPlayer.libs.telewizjadanet    import TelewizjadaNetApi, GetConfigList as TelewizjadaNet_GetConfigList
#from Plugins.Extensions.IPTVPlayer.libs.iklubnet          import IKlubNetApi, GetConfigList as IKlubNet_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.telewizjacom      import TeleWizjaComApi
from Plugins.Extensions.IPTVPlayer.libs.meteopl           import MeteoPLApi, GetConfigList as MeteoPL_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.edemtv            import EdemTvApi, GetConfigList as EdemTv_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.livestreamtv      import LiveStreamTvApi 
from Plugins.Extensions.IPTVPlayer.libs.skylinewebcamscom import WkylinewebcamsComApi, GetConfigList as WkylinewebcamsCom_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.livespottingtv    import LivespottingTvApi
from Plugins.Extensions.IPTVPlayer.libs.goldvodtv         import GoldVodTVApi, GetConfigList as GoldVodTV_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.showsporttvcom    import ShowsportTVApi
from Plugins.Extensions.IPTVPlayer.libs.sport365live      import Sport365LiveApi
from Plugins.Extensions.IPTVPlayer.libs.pierwszatv        import PierwszaTVApi, GetConfigList as PierwszaTV_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.yooanimecom       import YooanimeComApi
from Plugins.Extensions.IPTVPlayer.libs.livetvhdnet       import LivetvhdNetApi
from Plugins.Extensions.IPTVPlayer.libs.karwantv          import KarwanTvApi
from Plugins.Extensions.IPTVPlayer.libs.wizjatv           import WizjaTvApi, GetConfigList as WizjaTV_GetConfigList
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes        import strwithmeta



###################################################

###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
try:    import simplejson as json
except Exception: import json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry

try:    from urlparse import urlsplit, urlunsplit
except Exception: pass
from hashlib import md5
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.SortowanieWebstream              = ConfigYesNo(default = False)
config.plugins.iptvplayer.weatherbymatzgprohibitbuffering  = ConfigYesNo(default = True)
config.plugins.iptvplayer.weather_useproxy                 = ConfigYesNo(default = False)
config.plugins.iptvplayer.fake_separator = ConfigSelection(default = " ", choices = [(" ", " ")])

def GetConfigList():
    optionList = []
    
    optionList.append(getConfigListEntry("-----------------VideoStar------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( VideoStar_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("----------------Pierwsza.TV-----------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( PierwszaTV_GetConfigList() )
    except Exception: printExc()
    
    #optionList.append(getConfigListEntry("-----------------iklub.net------------------", config.plugins.iptvplayer.fake_separator))
    #try:    optionList.extend( IKlubNet_GetConfigList() )
    #except Exception: printExc()
    
    optionList.append(getConfigListEntry("------------------meteo.pl------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( MeteoPL_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("-------------------WeebTV-------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( WeebTv_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("-----------------FilmOn TV------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( FilmOn_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("----------------ustvnow.com-----------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( Ustvnow_GetConfigList() )
    except Exception: printExc()
    
    #optionList.append(getConfigListEntry("--------------telewizjada.net---------------", config.plugins.iptvplayer.fake_separator))
    #try:    optionList.extend( TelewizjadaNet_GetConfigList() )
    #except Exception: printExc()
   
    optionList.append(getConfigListEntry("-------------------edem.tv------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( EdemTv_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("-------------SkyLineWebCams.com-------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( WkylinewebcamsCom_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry(_("----------Other----------"), config.plugins.iptvplayer.fake_separator))
    optionList.append(getConfigListEntry(_("Turn off buffering for http://prognoza.pogody.tv/"), config.plugins.iptvplayer.weatherbymatzgprohibitbuffering))
    optionList.append(getConfigListEntry(_("Use Polish proxy for http://prognoza.pogody.tv/"), config.plugins.iptvplayer.weather_useproxy))
    
    optionList.append(getConfigListEntry("----------------GoldVod.TV------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( GoldVodTV_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("-----------------Wizja.TV------------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( WizjaTV_GetConfigList() )
    except Exception: printExc()
    
    optionList.append(getConfigListEntry("--------------wagasworld.com---------------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( WagasWorld_GetConfigList() )
    except Exception: printExc()
    
    
    return optionList

###################################################
# "HasBahCa"
def gettytul():
    return (_('"Web" streams player'))

class HasBahCa(CBaseHostClass):
    HTTP_HEADER= { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3' }
    MAIN_GROUPED_TAB = [{'alias_id':'weeb.tv',                 'name': 'weeb.tv',             'title': 'WeebTV',                            'url': '',                                                                   'icon': 'http://xmtvplayer.com/wp-content/uploads/2014/07/weebtv.png'}, \
                        {'alias_id':'videostar.pl',            'name': 'videostar.pl',        'title': 'VideoStar',                         'url': '',                                                                   'icon': 'https://static-videostar1.4vod.tv/assets/images/logo.png'}, \
                        #{'alias_id':'iklub.net',               'name': 'iklub.net',           'title': 'iKlub.net',                         'url': '',                                                                   'icon': 'http://iklub.net/wp-content/uploads/2015/11/klub2.png'}, \
                        {'alias_id':'tele-wizja.com',          'name': 'tele-wizja.com',      'title': 'tele-wizja.com',                    'url': '',                                                                   'icon': 'http://htk.net.pl/wp-content/uploads/2016/07/cache_2422349465.jpg'}, \
                        {'alias_id':'pierwsza.tv',             'name': 'pierwsza.tv',         'title': 'Pierwsza.TV',                       'url': '',                                                                   'icon': 'http://pierwsza.tv/img/logo.png'}, \
                        #{'alias_id':'telewizja-live.com',      'name': 'telewizja-live.com',  'title': 'Telewizja-Live.com',                'url': '',                                                                   'icon': 'http://mksolimpia.com/wp-content/uploads/2015/12/LIVE.png'}, \
                        #{'alias_id':'telewizjada.net',         'name': 'telewizjada.net',     'title': 'Telewizjada.net',                   'url': '',                                                                   'icon': 'http://www.btv.co/newdev/images/rokquickcart/samples/internet-tv.png'}, \
                        {'alias_id':'iptv_matzgpl',            'name': 'm3u',                 'title': 'Kanały IPTV_matzgPL',               'url': 'http://matzg2.prv.pl/Lista_matzgPL.m3u',                             'icon': 'http://matzg2.prv.pl/Iptv_matzgPL.png'}, \
                        {'alias_id':'prognoza.pogody.tv',      'name': 'prognoza.pogody.tv',  'title': 'prognoza.pogody.tv',                'url': 'http://prognoza.pogody.tv',                                          'icon': 'http://s2.manifo.com/usr/a/A17f/37/manager/pogoda-w-chorwacji-2013.png'}, \
                        {'alias_id':'meteo.pl',                'name': 'meteo.pl',            'title': 'Pogoda PL - meteorogramy',          'url': 'http://meteo.pl/',                                                   'icon': 'http://matzg2.prv.pl/pogoda_logo.png'}, \
                        {'alias_id':'webcamera.pl',            'name': 'webcamera.pl',        'title': 'WebCamera PL',                      'url': 'http://www.webcamera.pl/',                                           'icon': 'http://www.webcamera.pl/img/logo80x80.png'}, \
                        {'alias_id':'skylinewebcams.com',      'name': 'skylinewebcams.com',  'title': 'SkyLineWebCams.com',                'url': 'https://www.skylinewebcams.com/',                                    'icon': 'https://cdn.skylinewebcams.com/skylinewebcams.png'}, \
                        {'alias_id':'livespotting.tv',         'name': 'livespotting.tv',     'title': 'Livespotting.tv',                   'url': 'http://livespotting.tv/',                                            'icon': 'http://livespotting.tv/img/ls_logo.png'}, \
                        {'alias_id':'inne_matzg',              'name': 'm3u',                 'title': 'Różne Kanały IPTV_matzg',           'url': 'http://matzg2.prv.pl/inne_matzg.m3u',                                'icon': 'http://matzg2.prv.pl/iptv.png'}, \
                        {'alias_id':'filmon.com',              'name': 'filmon_groups',       'title': 'FilmOn TV',                         'url': 'http://www.filmon.com/',                                             'icon': 'http://static.filmon.com/theme/img/filmon_tv_logo_white.png'}, \
                        {'alias_id':'ustvnow.com',             'name': 'ustvnow',             'title': 'ustvnow.com',                       'url': 'https://www.ustvnow.com/',                                           'icon': 'http://2.bp.blogspot.com/-SVJ4uZ2-zPc/UBAZGxREYRI/AAAAAAAAAKo/lpbo8OFLISU/s1600/ustvnow.png'}, \
                        {'alias_id':'showsport-tv.com',        'name': 'showsport-tv.com',    'title': 'showsport-tv.com',                  'url': 'http://showsport-tv.com/',                                           'icon': 'http://showsport-tv.com/img/logo1-white-inverse.png'}, \
                        {'alias_id':'sport365.live',           'name': 'sport365.live',       'title': 'sport365.live',                     'url': 'http://www.sport365.live/',                                          'icon': 'http://s1.medianetworkinternational.com/images/icons/48x48px.png'}, \
                        {'alias_id':'yooanime.com',            'name': 'yooanime.com',        'title': 'yooanime.com',                      'url': 'http://yooanime.com/',                                               'icon': 'https://socialtvplayground.files.wordpress.com/2012/11/logo-technicolor2.png?w=960'}, \
                        {'alias_id':'livetvhd.net',            'name': 'livetvhd.net',        'title': 'livetvhd.net',                      'url': 'https://livetvhd.net/',                                              'icon': 'https://livetvhd.net/images/logo.png'}, \
                        {'alias_id':'karwan.tv',               'name': 'karwan.tv',           'title': 'karwan.tv',                         'url': 'http://karwan.tv/',                                                  'icon': 'http://karwan.tv/images/KARWAN_TV_LOGO/www.karwan.tv.png'}, \
                        #{'alias_id':'hasbahca',                'name': 'HasBahCa',            'title': 'HasBahCa',                          'url': 'http://hasbahcaiptv.com/m3u/HasBahCa/index.php?dir=',                'icon': 'http://hasbahcaiptv.com/xml/iptv.png'}, \
                        #{'alias_id':'wownet.ro',               'name': 'm3u',                 'title': 'Deutsch-Fernseher',                 'url': 'http://wownet.ro/iptv/',                                             'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/1000px-Flag_of_Germany.svg.png'}, \
                        #{'alias_id':'iptv.ink',                'name': 'm3u',                 'title': 'Free Iptv Project',                 'url': 'http://tv.iptv.ink/iptv.ink',                                        'icon': ''}, \
                        {'alias_id':'wagasworld',              'name': 'wagasworld.com',      'title': 'WagasWorld',                        'url': 'http://www.wagasworld.com/channels.php',                              'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/1000px-Flag_of_Germany.svg.png'}, \
                        #{'alias_id':'live_stream_tv',          'name': 'live-stream.tv',      'title': 'Live-Stream.tv',                    'url': 'http://www.live-stream.tv/',                                          'icon': 'http://www.live-stream.tv/images/lstv-logo.png'}, \
                        {'alias_id':'edem_tv',                 'name': 'edem.tv',             'title': 'Edem TV',                           'url': 'https://edem.tv/',                                                    'icon': 'https://edem.tv/public/images/logo_edem.png'}, \
                        #{'alias_id':'freetuxtv_programmes_en', 'name': 'm3u',                 'title': 'Angielska TV',                      'url': 'http://database.freetuxtv.net/playlists/playlist_programmes_en.m3u'}, \
                        {'alias_id':'matzg2_radio',            'name': 'm3u',                 'title': 'Radio-OPEN FM i inne',              'url':'http://matzg2.prv.pl/radio.m3u',                                      'icon': 'http://matzg2.prv.pl/openfm.png'}, \
                        {'alias_id':'goldvod.tv',              'name': 'goldvod.tv',          'title': 'http://goldvod.tv/',                'url': '',                                                                   'icon': 'http://goldvod.tv/assets/images/logo.png'}, \
                        {'alias_id':'wizja.tv',                'name': 'wizja.tv',            'title': 'wizja.tv',                          'url': 'http://wizja.tv/',                                                   'icon': 'http://wizja.tv/logo.png'}, \
                       ] 
    #http://play.tvip.ga/iptvde.m3u
    
    def __init__(self):
        CBaseHostClass.__init__(self)
        
        # temporary data
        self.currList = []
        self.currItem = {}
        
        #Login data
        self.sort = config.plugins.iptvplayer.SortowanieWebstream.value
        self.sessionEx = MainSessionWrapper()
        self.filmOnApi    = None
        self.videoStarApi = None
        self.wagasWorldApi= None
        self.ustvnowApi   = None
        self.telewizjadaNetApi = None
        #self.iKlubNetApi       = None
        self.yooanimeComApi    = None
        self.livetvhdNetApi    = None
        self.teleWizjaComApi   = None
        self.telewizjaLiveComApi = None
        self.meteoPLApi        = None
        self.liveStreamTvApi   = None
        self.pierwszaTvApi     = None
        self.goldvodTvApi      = None
        self.showsportTvApi    = None
        self.sport365LiveApi   = None
        self.edemTvApi            = None
        self.wkylinewebcamsComApi = None
        self.livespottingTvApi    = None
        self.karwanTvApi          = None
        self.wizjaTvApi           = None
        
        self.weebTvApi    = None
        self.hasbahcaiptv = {}
        
    def getPage(self, url, params={}, post_data=None):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        params.update({'header':HTTP_HEADER})
        
        if False and 'hasbahcaiptv.com' in url:
            printDBG(url)
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e5'.format(urllib.quote_plus(url))
            params['header']['Referer'] = proxy
            url = proxy
        #sts, data = self.cm.getPage(url, params, post_data)
        #printDBG(data)
        return self.cm.getPage(url, params, post_data)
        
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def _getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return clean_html(u'%s' % v).encode('utf-8')
  
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
        
    def playVideo(self, params):
        params['type'] = 'video'
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
        
    def addItem(self, params):
        self.currList.append(params)
        return

    def listsMainMenu(self, tab, forceParams={}):
        # sort tab if needed
        orderList = GetHostsOrderList('iptvplayerwebstreamorder')
        addedAlias = []
        
        # add in order from order file
        for alias in orderList:
            for item in tab:
                if item['alias_id'] == alias.strip():
                    params = dict(item)
                    params.update(forceParams)
                    self.addDir(params)
                    addedAlias.append(item['alias_id'])
                elif ('!' + item['alias_id']) == alias.strip():
                    addedAlias.append(item['alias_id'])
        
        # add other streams not listed at order file
        for item in tab:
            if item['alias_id'] not in addedAlias:
                params = dict(item)
                params.update(forceParams)
                self.addDir(params)
            
    def listHasBahCa(self, item):
        url = item.get('url', '')
        if 'proxy-german.de' in url:
            url = urllib.unquote(url.split('?q=')[-1])
        
        printDBG("listHasBahCa url[%s]" % url)
        BASE_URL = 'http://hasbahcaiptv.com/'
        
        if '?' in url and '/' == url[-1]:
            url = url[:-1]
        
        def _url_path_join(*parts):
            """Normalize url parts and join them with a slash."""
            schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
            scheme, netloc, query, fragment = _first_of_each(schemes, netlocs, queries, fragments)
            path = '/'.join(x.strip('/') for x in paths if x)
            return urlunsplit((scheme, netloc, path, query, fragment))

        def _first_of_each(*sequences):
            return (next((x for x in sequence if x), '') for sequence in sequences)
        
        login    = self.hasbahcaiptv.get('login', '')
        password = self.hasbahcaiptv.get('password', '')
        
        if login == '' and password == '':
            sts, data = self.getPage('http://hasbahcaiptv.com/page.php?seite=Passwort.html')
            if sts:
                login    = self._cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Downloads Login', '</h3>', False)[1])
                password = self._cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Downloads Pass', '</h3>', False)[1])
                self.hasbahcaiptv['login']    = login.replace('&nbsp;','').replace('\xc2\xa0','').strip() 
                self.hasbahcaiptv['password'] = password.replace('&nbsp;','').replace('\xc2\xa0', '').strip()
            
        sts, data = self.getPage( url, {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('hasbahcaiptv')}, {'username':self.hasbahcaiptv.get('login', 'downloader'), 'password':self.hasbahcaiptv.get('password', 'hasbahcaiptv.com')} )
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<table class="autoindex_table">', '</table>', False)[1]    
        data = data.split('</tr>')
        for item in data:
            printDBG(item)
            if 'text.png' in item:  name = 'm3u' 
            elif 'dir.png' in item: name = 'HasBahCa' 
            else: continue
            desc    = self.cm.ph.removeDoubles(clean_html(item.replace('>', '> ')).replace('\t', ' '), ' ')
            new_url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title   = new_url
            printDBG("listHasBahCa new_url[%s]" % new_url)
            if title[-1] != '/':  title = title.split('/')[-1]
            title   = self._cleanHtmlStr(item) #title.split('dir=')[-1]

            if new_url.startswith('.'): 
                if 'm3u' == name: new_url = BASE_URL + new_url[2:]
                else: new_url = _url_path_join(url[:url.rfind('/')+1], new_url[1:])
            if not new_url.startswith('http'): new_url = BASE_URL + new_url
            new_url = new_url.replace("&amp;", "&")

            new_url = strwithmeta(new_url, {'cookiefile':'hasbahcaiptv'})
            params = {'name':name, 'title':title.strip(), 'url':new_url, 'desc':desc}
            self.addDir(params)
            
    def getDirectVideoHasBahCa(self, name, url):
        printDBG("getDirectVideoHasBahCa name[%s], url[%s]" % (name, url))
        videoTabs = []
        url = strwithmeta(url)
        if 'cookiefile' in url.meta:
            sts, data = self.cm.getPage( url, {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir(url.meta['cookiefile'])} )
        else:
            sts, data = self.cm.getPage( url )
        if sts:
            data = data.strip()
            if data.startswith('http'):
                videoTabs.append({'name':name, 'url':data})
        return videoTabs
            
    def __getFilmOnIconUrl(self, item):
        icon = u''
        try:
            icon = item.get('big_logo', '')
            if '' == icon: icon = item.get('logo_148x148_uri', '')
            if '' == icon: icon = item.get('logo', '')
            if '' == icon: icon = item.get('logo_uri', '')
        except Exception:
            printExc()
        return icon.encode('utf-8')

    def __setFilmOn(self):
        if None == self.filmOnApi:
            self.filmOnApi = FilmOnComApi()
            
    def getFilmOnLink(self, channelID):
        self.__setFilmOn()
        return self.filmOnApi.getUrlForChannel(channelID)

    def getFilmOnGroups(self):
        self.__setFilmOn()
        tmpList = self.filmOnApi.getGroupList()
        for item in tmpList:
            try:
                params = { 'name'     : 'filmon_channels', 
                           'title'    : item['title'].encode('utf-8'), 
                           'desc'     : item['description'].encode('utf-8'), 
                           'group_id' : item['group_id'],
                           'icon'     : self.__getFilmOnIconUrl(item)
                           }
                self.addDir(params)
            except Exception:
                printExc()

    def getFilmOnChannels(self):        
        self.__setFilmOn()
        tmpList = self.filmOnApi.getChannelsListByGroupID(self.currItem['group_id'])
        for item in tmpList:
            try:
                params = { 'name'     : 'filmon_channel', 
                           'title'    : item['title'].encode('utf-8'), 
                           'url'      : item['id'], 
                           'desc'     : item['group'].encode('utf-8'), 
                           'seekable' : item['seekable'],
                           'icon'     : self.__getFilmOnIconUrl(item)
                           }
                self.addVideo(params)
            except Exception:
                printExc()
    
    def m3uList(self, listURL):
        printDBG('m3uList entry')
        params = {'header': self.HTTP_HEADER}
        
        listURL = strwithmeta(listURL)
        meta = listURL.meta
        if 'proxy-german.de' in listURL:
            listURL = urllib.unquote(listURL.split('?q=')[-1])
        
        listURL = strwithmeta(listURL, meta)
        if 'cookiefile' in listURL.meta:
            params.update({'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir(listURL.meta['cookiefile'])} )
            
        sts, data = self.getPage(listURL, params)
        if not sts:
            printDBG("getHTMLlist ERROR geting [%s]" % listURL)
            return
        data = data.replace("\r","\n").replace('\n\n', '\n').split('\n')
        printDBG("[\n%s\n]" % data)
        title    = ''
        nr       = ''
        catTitle = ''
        icon     = ''
        for item in data:
            if item.startswith('#EXTINF:'):
                try:    
                    nr       = self.cm.ph.getDataBeetwenMarkers(item, 'tvg-id="', '"', False)[1]
                    catTitle = self.cm.ph.getDataBeetwenMarkers(item, 'group-title="', '"', False)[1]
                    icon     = self.cm.ph.getDataBeetwenMarkers(item, 'tvg-logo="', '"', False)[1]
                    title    = item.split(',')[1]
                except Exception: 
                    title = item
            else:
                if 0 < len(title):
                    if 'Lista_matzgPL' in listURL and title.startswith('TVP '):
                        continue
                    item = item.replace('rtmp://$OPT:rtmp-raw=', '')
                    cTitle = re.sub('\[[^\]]*?\]', '', title)
                    if len(cTitle): title = cTitle
                    itemUrl = self.up.decorateParamsFromUrl(item)
                    if 'http://wownet.ro/' in itemUrl:
                        icon = 'http://wownet.ro/logo/' + icon
                    else: icon = ''
                    if '' != catTitle:
                        desc = catTitle + ', '
                    else: desc = ''
                    desc += (_("Protocol: ")) + itemUrl.meta.get('iptv_proto', '')
                    
                    if 'headers=' in itemUrl:
                        headers = self.cm.ph.getSearchGroups(itemUrl, 'headers\=(\{[^\}]+?\})')[0]
                        try:
                            headers = byteify(json.loads(headers))
                            itemUrl = itemUrl.split('headers=')[0].strip()
                            itemUrl = urlparser.decorateUrl(itemUrl, headers)
                        except Exception:
                            printExc()
                    params = {'title': title, 'url': itemUrl, 'icon':icon, 'desc':desc}
                    
                    self.addVideo(params)
                    title = ''
        
    def getWagasWorldList(self, cItem):
        if None == self.wagasWorldApi: 
            self.wagasWorldApi = WagasWorldApi()

        tmpList = self.wagasWorldApi.getChannelsList(cItem)
        for item in tmpList: 
            params = dict(item)
            params.update({'name':'wagasworld.com'})
            if 'video' == item['type']:
                self.addVideo(params)
            elif 'more' == item['type']:
                self.addMore(params)
            else:
                self.addDir(params)
            
    def getWagasWorldLink(self, cItem):
        return self.wagasWorldApi.getVideoLink(cItem)
        
    def getOthersList(self, cItem):
        sts, data = self.cm.getPage("http://www.elevensports.pl/")
        if not sts: return
        channels = {0:"ELEVEN", 1:"ELEVEN SPORTS"}
        data = re.compile('''stream=(http[^"']+?)["']''').findall(data)
        for idx in range(len(data)):
            params = dict(cItem)
            params.update({'title':channels.get(idx, 'Unknown'), 'provider':'elevensports', 'url':data[idx].replace('~', '=')})
            self.addVideo(params)
    
    def getOthersLinks(self, cItem):
        urlTab = []
        url = cItem.get('url', '')
        if url != '':
            urlTab = getDirectM3U8Playlist(url, False)
        return urlTab
    
    def getWeebTvList(self, url):
        printDBG('getWeebTvList start')
        if None == self.weebTvApi:
            self.weebTvApi = WeebTvApi()
        if '' == url:
            tmpList = self.weebTvApi.getCategoriesList()
            for item in tmpList:
                params = dict(item)
                params.update({'name':'weeb.tv'})
                self.addDir(params)
        else:
            tmpList = self.weebTvApi.getChannelsList(url)
            for item in tmpList: 
                item.update({'name':'weeb.tv'})
                self.addVideo(item)
            
    def getWeebTvLink(self, url):
        printDBG("getWeebTvLink url[%s]" % url)
        return self.weebTvApi.getVideoLink(url)
        
    def getWebCamera(self, cItem):
        printDBG("getWebCamera start")
        baseMobileUrl = 'http://www.webcamera.mobi/'
        baseUrl = 'http://www.webcamera.pl/'
        
        def _getFullUrl(url, mobile=False):
            if mobile: 
                base = baseMobileUrl
            else:
                base = baseUrl
            
            if self.cm.isValidUrl(url):
                if mobile:
                    url = url.replace(self.up.getDomain(baseUrl), self.up.getDomain(baseMobileUrl))
                else:
                    url = url.replace(self.up.getDomain(baseMobileUrl), self.up.getDomain(baseUrl))
                return url
            if url.startswith('//'):
                return 'http:' + url
            elif url.startswith('/'):
                return base[:-1] + url
            elif len(url):
                return base + url
            return url
        
        catKey = 'webcamera_category'
        category = cItem.get(catKey, '')
            
        if category == '':
            sts, data = self.cm.getPage(baseMobileUrl)
            if not sts: return

            params = dict(cItem)
            params.update({'title':'TV', 'url':strwithmeta(_getFullUrl('tv'), {'iframe':True})})
            self.addVideo(params)
            params = dict(cItem)
            params.update({'title':'Polecane kamery', 'url':baseUrl, catKey:'list_videos'})
            self.addDir(params)
            params = dict(cItem)
            params.update({'title':'Ostatnio dodane', catKey:'list_videos', 'url':_getFullUrl('ostatniododane')})
            self.addDir(params)
            
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="inlinecam inlinecamv2"', '</div>')
            for item in data:
                catUrl = self.cm.ph.getSearchGroups(item, """href=['"]([^'^"]+?)['"]""")[0]
                icon   = self.cm.ph.getSearchGroups(item, """src=['"]([^'^"]+?)['"]""")[0] 
                params = dict(cItem)
                params.update({'title':self._cleanHtmlStr(item), 'url':_getFullUrl(catUrl, True), 'icon':_getFullUrl(icon, True), catKey:'sub_cat'})
                self.addDir(params)
        elif category == 'sub_cat':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
            
            hasSubCats = False
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="inlinecam inlinecamv2"', '</div>')
            for item in data:
                catUrl = self.cm.ph.getSearchGroups(item, """href=['"]([^'^"]+?)['"]""")[0].replace('?cat=', 'kategoria,')
                icon   = self.cm.ph.getSearchGroups(item, """src=['"]([^'^"]+?)['"]""")[0] 
                params = dict(cItem)
                params.update({'title':self._cleanHtmlStr(item), 'url':_getFullUrl(catUrl), 'icon':_getFullUrl(icon, True), catKey:'list_videos'})
                self.addDir(params)
                hasSubCats = True
            if hasSubCats:
                params = dict(cItem)
                params.update({'type':'category', 'title':'Wszystkie', 'url':_getFullUrl(params['url']).replace('?cat=', 'kategoria,')})
                self.currList.insert(0, params)
            else:
                cItem = dict(cItem)
                cItem['url'] = _getFullUrl(cItem['url']).replace('?cat=', 'kategoria,')
                category = 'list_videos'
        
        if category == 'list_videos':
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="inlinecam', '</div>')
            for item in data:
                url = self.cm.ph.getSearchGroups(item, """href=['"]([^'^"]+?)['"]""")[0]
                if '' != url:
                    title = self._cleanHtmlStr(item)
                    icon  = self.cm.ph.getSearchGroups(item, """src=['"]([^'^"]+?\.jpg[^'^"]*?)['"]""")[0]
                    params = dict(cItem)
                    params.update({'title':title, 'url':_getFullUrl(url), 'icon':_getFullUrl(icon)})
                    self.addVideo(params)
                       
    def getWebCameraLink(self, videoUrl):
        printDBG("getWebCameraLink start")
        videoUrl = strwithmeta(videoUrl)
        if videoUrl.meta.get('iframe', False):
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?embed[^"^']+?)['"]''', 1, True)[0]
        
        return self.up.getVideoLinkExt(videoUrl)
    
    def getVideostarList(self):
        printDBG("getVideostarList start")
        if None == self.videoStarApi:
            self.videoStarApi = VideoStarApi()
            
        tmpList = self.videoStarApi.getChannelsList(True)
        for item in tmpList:
            try:
                descTab = []
                if item.get('geoblocked', False):
                    descTab.append('Kanał zablokowany dla Twojego IP.')
                    descTab.append('Spróbuj włączyć bramkę proxy w konfiguracji hosta (klawisz niebieski na pilocie) i odświeżyć.')
                descTab.append(_('Access status: ') + _(item['access_status']))
                params = { 'name'       : 'videostar_channels', 
                           'title'      : item['name'], 
                           'desc'       :  '[/br]'.join(descTab), 
                           'url'        : item['id'],
                           'icon'       : item['thumbnail'],
                           }
                self.addVideo(params)
            except Exception:
                printExc()
        
    def getVideostarLink(self, channelID):
        urlsTab = self.videoStarApi.getVideoLink(channelID)
        if 0 < len(urlsTab):
            if 'hls' == urlsTab[0]['type']:
                tmpList = getDirectM3U8Playlist(urlsTab[0]['url'], checkExt=False)
            else:
                tmpList = urlsTab
            try:
                for item in tmpList:
                    if self.videoStarApi.getDefaultQuality() == item['bitrate']:
                        return [dict(item)]
                return [dict(tmpList[0])]
            except Exception:
                printExc()
                urlsTab = []
        return urlsTab
        
        
    #############################################################
    def getUstvnowList(self, cItem):
        printDBG("getUstvnowList start")
        if None == self.ustvnowApi:
            self.ustvnowApi = UstvnowApi()
        tmpList = self.ustvnowApi.getChannelsList(cItem)
        for item in tmpList:
            self.addVideo(item)
        
    def getUstvnowLink(self, cItem):
        printDBG("getUstvnowLink start")
        urlsTab = self.ustvnowApi.getVideoLink(cItem)
        return urlsTab
    #############################################################
    
    def getTelewizjadaNetList(self, cItem):
        printDBG("getTelewizjadaNetList start")
        if None == self.telewizjadaNetApi:
            self.telewizjadaNetApi = TelewizjadaNetApi()
        tmpList = self.telewizjadaNetApi.getChannelsList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getTelewizjadaNetLink(self, cItem):
        printDBG("getTelewizjadaNetLink start")
        urlsTab = self.telewizjadaNetApi.getVideoLink(cItem)
        return urlsTab
        
    #def getIKlubNetList(self, cItem):
    #    printDBG("getIKlubNetList start")
    #    if None == self.iKlubNetApi:
    #        self.iKlubNetApi = IKlubNetApi()
    #    tmpList = self.iKlubNetApi.getList(cItem)
    #    for item in tmpList:
    #        if 'video' == item['type']:
    #            self.addVideo(item) 
    #        else:
    #            self.addDir(item)
        
    #def getIKlubNetLink(self, cItem):
    #    printDBG("getIKlubNetLink start")
    #    urlsTab = self.iKlubNetApi.getVideoLink(cItem)
    #    return urlsTab
        
    def getYooanimeComtList(self, cItem):
        printDBG("getYooanimeComtList start")
        if None == self.yooanimeComApi:
            self.yooanimeComApi = YooanimeComApi()
        tmpList = self.yooanimeComApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getYooanimeComLink(self, cItem):
        printDBG("getYooanimeComLink start")
        urlsTab = self.yooanimeComApi.getVideoLink(cItem)
        return urlsTab
        
    def geLivetvhdNetList(self, cItem):
        printDBG("geLivetvhdNetList start")
        if None == self.livetvhdNetApi:
            self.livetvhdNetApi = LivetvhdNetApi()
        tmpList = self.livetvhdNetApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getLivetvhdNetLink(self, cItem):
        printDBG("getLivetvhdNetLink start")
        urlsTab = self.livetvhdNetApi.getVideoLink(cItem)
        return urlsTab
        
    def getKarwanTvList(self, cItem):
        printDBG("getKarwanTvList start")
        if None == self.karwanTvApi:
            self.karwanTvApi = KarwanTvApi()
        tmpList = self.karwanTvApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            elif 'audio' == item['type']:
                self.addAudio(item) 
            else:
                self.addDir(item)
        
    def getKarwanTvLink(self, cItem):
        printDBG("getKarwanTvLink start")
        urlsTab = self.karwanTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getWizjaTvList(self, cItem):
        printDBG("getWizjaTvList start")
        if None == self.wizjaTvApi:
            self.wizjaTvApi = WizjaTvApi()
        tmpList = self.wizjaTvApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            elif 'audio' == item['type']:
                self.addAudio(item) 
            else:
                self.addDir(item)
        
    def getWizjaTvLink(self, cItem):
        printDBG("getWizjaTvLink start")
        urlsTab = self.wizjaTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getTelewizjaLiveComList(self, cItem):
        printDBG("getTelewizjaLiveComList start")
        if None == self.telewizjaLiveComApi:
            from Plugins.Extensions.IPTVPlayer.libs.telewizjalivecom  import TelewizjaLiveComApi
            self.telewizjaLiveComApi = TelewizjaLiveComApi()
        tmpList = self.telewizjaLiveComApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getTelewizjaLiveComLink(self, cItem):
        printDBG("getTelewizjaLiveComLink start")
        urlsTab = self.telewizjaLiveComApi.getVideoLink(cItem)
        return urlsTab
    
    def getTeleWizjaComList(self, cItem):
        printDBG("getTeleWizjaComList start")
        if None == self.teleWizjaComApi:
            self.teleWizjaComApi = TeleWizjaComApi()
        tmpList = self.teleWizjaComApi.getList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getTeleWizjaComLink(self, cItem):
        printDBG("getTeleWizjaComLink start")
        urlsTab = self.teleWizjaComApi.getVideoLink(cItem)
        return urlsTab
        
    def getMeteoPLList(self, cItem):
        printDBG("getMeteoPLApiList start")
        if None == self.meteoPLApi:
            self.meteoPLApi = MeteoPLApi()
        tmpList = self.meteoPLApi.getList(cItem)
        for item in tmpList:
            self.addItem(item) 
        
    def getMeteoPLLink(self, cItem):
        printDBG("getMeteoPLLink start")
        urlsTab = self.meteoPLApi.getVideoLink(cItem)
        return urlsTab
        
    def getEdemTvList(self, cItem):
        printDBG("getEdemTvList start")
        if None == self.edemTvApi:
            self.edemTvApi = EdemTvApi()
        tmpList = self.edemTvApi.getChannelsList(cItem)
        for item in tmpList:
            if 'video' == item['type']:
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getEdemTvLink(self, cItem):
        printDBG("getEdemTvLink start")
        urlsTab = self.edemTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getWkylinewebcamsComList(self, cItem):
        printDBG("getWkylinewebcamsComList start")
        if None == self.wkylinewebcamsComApi:
            self.wkylinewebcamsComApi = WkylinewebcamsComApi()
        tmpList = self.wkylinewebcamsComApi.getChannelsList(cItem)
        for item in tmpList:
            if 'video' == item.get('type', ''):
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getWkylinewebcamsComLink(self, cItem):
        printDBG("getWkylinewebcamsComLink start")
        urlsTab = self.wkylinewebcamsComApi.getVideoLink(cItem)
        return urlsTab
        
    def getLivespottingTvList(self, cItem):
        printDBG("getLivespottingTvList start")
        if None == self.livespottingTvApi:
            self.livespottingTvApi = LivespottingTvApi()
        tmpList = self.livespottingTvApi.getChannelsList(cItem)
        for item in tmpList:
            self.addVideo(item) 
        
    def getLiveStreamTvList(self, cItem):
        printDBG("getLiveStreamTvList start")
        if None == self.liveStreamTvApi:
            self.liveStreamTvApi = LiveStreamTvApi()
        tmpList = self.liveStreamTvApi.getChannelsList(cItem)
        for item in tmpList:
            self.addVideo(item) 
        
    def getLiveStreamTvLink(self, cItem):
        printDBG("getLiveStreamTvLink start")
        urlsTab = self.liveStreamTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getPierwszaTvList(self, cItem):
        printDBG("getPierwszaTvList start")
        if None == self.pierwszaTvApi:
            self.pierwszaTvApi = PierwszaTVApi()
        tmpList = self.pierwszaTvApi.getChannelsList(cItem)
        for item in tmpList:
            self.playVideo(item) 
        
    def getPierwszaTvLink(self, cItem):
        printDBG("getPierwszaTvLink start")
        urlsTab = self.pierwszaTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getGoldVodTvList(self, cItem):
        printDBG("getGoldVodTvList start")
        if None == self.goldvodTvApi:
            self.goldvodTvApi = GoldVodTVApi()
        tmpList = self.goldvodTvApi.getChannelsList(cItem)
        for item in tmpList:
            self.addVideo(item) 
        
    def getGoldVodTvLink(self, cItem):
        printDBG("getGoldVodTvLink start")
        urlsTab = self.goldvodTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getShowsportTvList(self, cItem):
        printDBG("getShowsportTvList start")
        if None == self.showsportTvApi:
            self.showsportTvApi = ShowsportTVApi()
        tmpList = self.showsportTvApi.getChannelsList(cItem)
        for item in tmpList:
            if 'video' == item.get('type', ''):
                self.addVideo(item) 
            else:
                self.addDir(item)
        
    def getShowsportTvLink(self, cItem):
        printDBG("getShowsportTvLink start")
        urlsTab = self.showsportTvApi.getVideoLink(cItem)
        return urlsTab
        
    def getSport365LiveList(self, cItem):
        printDBG("getSport365LiveList start")
        if None == self.sport365LiveApi:
            self.sport365LiveApi = Sport365LiveApi()
        tmpList = self.sport365LiveApi.getChannelsList(cItem)
        for item in tmpList:
            self.currList.append(item) 
        
    def getSport365LiveLink(self, cItem):
        printDBG("getSport365LiveLink start")
        urlsTab = self.sport365LiveApi.getVideoLink(cItem)
        return urlsTab
        
    def prognozaPogodyList(self, url):
        printDBG("prognozaPogodyList start")
        if config.plugins.iptvplayer.weather_useproxy.value: params = {'http_proxy':config.plugins.iptvplayer.proxyurl.value}
        else: params = {}
        sts,data = self.cm.getPage(url, params)
        if not sts: return
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="items">', '</div>', False)[1]    
        data = data.split('</a>')
        if len(data): del data[-1]
        for item in data:
            params = {'name':"prognoza.pogody.tv"}
            params['url'] = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            params['icon'] = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            params['title'] = self.cleanHtmlStr(item)
            if len(params['icon']) and not params['icon'].startswith('http'): params['icon'] = 'http://prognoza.pogody.tv/'+params['icon']
            if len(params['url']) and not params['url'].startswith('http'): params['url'] = 'http://prognoza.pogody.tv/'+params['url']
            self.addVideo(params)
            
    def prognozaPogodyLink(self, url):
        printDBG("prognozaPogodyLink url[%r]" % url)
        if config.plugins.iptvplayer.weather_useproxy.value: params = {'http_proxy':config.plugins.iptvplayer.proxyurl.value}
        else: params = {}
        sts,data = self.cm.getPage(url, params)
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?\.mp4[^"]*?)"')[0]
        
        urlMeta = {}
        if config.plugins.iptvplayer.weatherbymatzgprohibitbuffering.value:
            urlMeta['iptv_buffering'] = 'forbidden'
        if config.plugins.iptvplayer.weather_useproxy.value:
            urlMeta['http_proxy'] = config.plugins.iptvplayer.proxyurl.value
            
        url = self.up.decorateUrl(url, urlMeta)
        return [{'name':'prognoza.pogody.tv', 'url':url}]

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s]" % (name) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.MAIN_GROUPED_TAB)
    #HasBahCa list
        elif name == "HasBahCa":
            self.listHasBahCa(self.currItem)
    #m3u items
        elif name == "m3u":
            self.m3uList(url)
    #prognoza.pogody.tv items
        elif name == "prognoza.pogody.tv":
            self.prognozaPogodyList(url)
    #pierwsza.tv items
        elif name == 'pierwsza.tv':
            self.getPierwszaTvList(self.currItem)
    #goldvod.tv items
        elif name == "goldvod.tv":
            self.getGoldVodTvList(url)
        elif name == "showsport-tv.com":
            self.getShowsportTvList(self.currItem)
        elif name == "sport365.live":
            self.getSport365LiveList(self.currItem)
    #videostar.pl items
        elif name == "videostar.pl":
            self.getVideostarList()
    #ustvnow.com items
        elif name == 'ustvnow':
            self.getUstvnowList(self.currItem)
    #telewizjada.net items
        elif name == 'telewizjada.net':
            self.getTelewizjadaNetList(self.currItem)
    #iklub.net items
    #    elif name == 'iklub.net':
    #        self.getIKlubNetList(self.currItem)
    #yooanime.com items
        elif name == 'yooanime.com':
            self.getYooanimeComtList(self.currItem)
    #livetvhd.net items
        elif name == 'livetvhd.net':
            self.geLivetvhdNetList(self.currItem)
    #karwan.tv items
        elif name == 'karwan.tv':
            self.getKarwanTvList(self.currItem)
    #wizja.tv items
        elif name == 'wizja.tv':
            self.getWizjaTvList(self.currItem)
    #telewizja-live.com items
        elif name == 'telewizja-live.com':
            self.getTelewizjaLiveComList(self.currItem)
    #tele-wizja.com items
        elif name == 'tele-wizja.com':
            self.getTeleWizjaComList(self.currItem)
    #meteo.pl items
        elif name == 'meteo.pl':
            self.getMeteoPLList(self.currItem)
    #edem.tv items
        elif name == 'edem.tv':
            self.getEdemTvList(self.currItem)
    #skylinewebcams.com items
        elif name == 'skylinewebcams.com':
            self.getWkylinewebcamsComList(self.currItem)
    #livespotting.tv items
        elif name == 'livespotting.tv':
            self.getLivespottingTvList(self.currItem)
    #live-stream.tv items
        elif name == 'live-stream.tv':
            self.getLiveStreamTvList(self.currItem)
    #wagasworld.com items
        elif name == "wagasworld.com":
            self.getWagasWorldList(self.currItem)
    #weeb.tv items
        elif name == 'weeb.tv':
            self.getWeebTvList(url)
    #webcamera.pl items
        elif name == "webcamera.pl":
            self.getWebCamera(self.currItem)
    # filmon.com groups
        elif name == "filmon_groups":
            self.getFilmOnGroups()
    # filmon.com channels
        elif name == "filmon_channels":
            self.getFilmOnChannels()
    # others
        elif name == 'others':
            self.getOthersList(self.currItem)
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, HasBahCa(), withSearchHistrory = False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('webstreamslogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen <= Index or Index < 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['video', 'audio', 'picture']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        cItem = self.host.currList[Index]
        url   = self.host.currList[Index].get("url", '')
        name  = self.host.currList[Index].get("name", '')
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s] [%s]" % (name, url))
        urlList = None
        
        if -1 != url.find('teledunet'):
            new_url = TeledunetParser().get_rtmp_params(url)
            if 0 < len(url): retlist.append(CUrlItem("Własny link", new_url))
        elif url.startswith('http://goldvod.tv/'):
            urlList = self.host.getGoldVodTvLink(cItem)
        elif name == 'pierwsza.tv':
            urlList = self.host.getPierwszaTvLink(cItem)
        elif "showsport-tv.com" == name:
            urlList = self.host.getShowsportTvLink(cItem)
        elif "sport365.live" == name:
            urlList = self.host.getSport365LiveLink(cItem)
        elif 'wagasworld.com' == name:
            urlList = self.host.getWagasWorldLink(cItem)
        elif 'others' == name:
            urlList = self.host.getOthersLinks(cItem)
        elif 'weeb.tv' in name:
            url = self.host.getWeebTvLink(url)
        elif "filmon_channel" == name:
            urlList = self.host.getFilmOnLink(channelID=url)
        elif "videostar_channels" == name:
            urlList = self.host.getVideostarLink(channelID=url)
            #if 1 < len(tmpList):
            #    for item in tmpList:
            #        retlist.append(CUrlItem(item['name'], item['url']))
            #elif 1 == len(tmpList):
            #    url =  tmpList[0]['url']
        elif name == 'ustvnow':
            urlList = self.host.getUstvnowLink(cItem)
        elif name == 'telewizjada.net':
            urlList = self.host.getTelewizjadaNetLink(cItem)
        #elif name == 'iklub.net':
        #    urlList = self.host.getIKlubNetLink(cItem)
        elif name == 'yooanime.com':
            urlList = self.host.getYooanimeComLink(cItem)
        elif name == 'livetvhd.net':
            urlList = self.host.getLivetvhdNetLink(cItem)
        elif name == 'karwan.tv':
            urlList = self.host.getKarwanTvLink(cItem)
        elif name == 'wizja.tv':
            urlList = self.host.getWizjaTvLink(cItem)
        elif name == 'telewizja-live.com':
            urlList = self.host.getTelewizjaLiveComLink(cItem)
        elif name == 'tele-wizja.com':
            urlList = self.host.getTeleWizjaComLink(cItem)
        elif name == 'meteo.pl':
            urlList = self.host.getMeteoPLLink(cItem)
        elif name == 'edem.tv':
            urlList = self.host.getEdemTvLink(cItem)
        elif name == 'skylinewebcams.com':
            urlList = self.host.getWkylinewebcamsComLink(cItem)
        elif name == 'live-stream.tv':
            urlList = self.host.getLiveStreamTvLink(cItem)
        elif name == "webcamera.pl":
            urlList = self.host.getWebCameraLink(url)
        elif name == "prognoza.pogody.tv":
            urlList = self.host.prognozaPogodyLink(url)
            
        if isinstance(urlList, list):
            for item in urlList:
                retlist.append(CUrlItem(item['name'], item['url']))
        elif isinstance(url, basestring):
            if url.endswith('.m3u'):
                tmpList = self.host.getDirectVideoHasBahCa(name, url)
                for item in tmpList:
                    retlist.append(CUrlItem(item['name'], item['url']))
            else:
                url = urlparser.decorateUrl(url)
                iptv_proto = url.meta.get('iptv_proto', '')
                if 'm3u8' == iptv_proto:
                    if '84.114.88.26' == url.meta.get('X-Forwarded-For', ''):
                        url.meta['iptv_m3u8_custom_base_link'] = '' + url
                        url.meta['iptv_proxy_gateway'] = 'http://webproxy.at/surf/printer.php?u={0}&b=192&f=norefer'
                        url.meta['Referer'] =  url.meta['iptv_proxy_gateway'].format(urllib.quote_plus(url))
                        meta = url.meta
                        tmpList = getDirectM3U8Playlist(url, checkExt=False)
                        if 1 == len(tmpList):
                            url = urlparser.decorateUrl(tmpList[0]['url'], meta)
                            
                    tmpList = getDirectM3U8Playlist(url, checkExt=False)
                    for item in tmpList:
                        retlist.append(CUrlItem(item['name'], item['url']))
                elif 'f4m' == iptv_proto:
                    tmpList = getF4MLinksWithMeta(url, checkExt=False)
                    for item in tmpList:
                        retlist.append(CUrlItem(item['name'], item['url']))
                else:
                    if '://' in url:
                        ua  = strwithmeta(url).meta.get('User-Agent', '')
                        if 'balkanstream.com' in url:
                            if '' == ua: url.meta['User-Agent'] = 'Mozilla/5.0'
                                
                        retlist.append(CUrlItem("Link", url))
            
        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo