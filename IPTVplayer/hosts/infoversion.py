# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, GetLogoDir, GetTmpDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser 
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import decorateUrl, getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html 
###################################################
# FOREIGN import
###################################################
import re, urllib, base64, urllib2
try:
    import simplejson
except:
    import json as simplejson 
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry
from os import remove as os_remove, path as os_path, system as os_system
###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.numerwersji = ConfigYesNo(default = True)
config.plugins.iptvplayer.ilepozycji = ConfigInteger(8, (1, 99))  
config.plugins.iptvplayer.religia = ConfigYesNo(default = True)  

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Pokaz numer wersji:", config.plugins.iptvplayer.numerwersji) )
    optionList.append( getConfigListEntry( "Ile pozycji:", config.plugins.iptvplayer.ilepozycji) )
    optionList.append( getConfigListEntry( "Transmisje religijne:", config.plugins.iptvplayer.religia) )
    return optionList
###################################################
###################################################
# Title of HOST
###################################################
def gettytul():
    return 'Info version'


class IPTVHost(IHost):
    LOGO_NAME = 'infologo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        printDBG( "init end" )
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir(self.LOGO_NAME) ])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.prevList = []
        printDBG( "getInitList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( "getListForItem begin" )
        self.prevIndex.append(Index)
        self.prevList.append(self.currList)
        self.currList = self.host.getListForItem(Index, refresh, selItem)
        printDBG( "getListForItem end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getPrevList(self, refresh = 0):
        printDBG( "getPrevList begin" )
        if(len(self.prevList) > 0):
            self.prevIndex.pop()
            self.currList = self.prevList.pop()
            self.host.setCurrList(self.currList)
            printDBG( "getPrevList end OK" )
            return RetHost(RetHost.OK, value = self.currList)
        else:
            printDBG( "getPrevList end ERROR" )
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        printDBG( "getCurrentList begin" )
        #if refresh == 1
        #self.prevIndex[-1] #ostatni element prevIndex
        #self.prevList[-1]  #ostatni element prevList
        #tu pobranie listy dla dla elementu self.prevIndex[-1] z listy self.prevList[-1]  
        printDBG( "getCurrentList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getLinksForVideo(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getResolvedURL(self, url):
        printDBG( "getResolvedURL begin" )
        if url != None and url != '':        
            ret = self.host.getResolvedURL(url)
            if ret != None and ret != '':        
               printDBG( "getResolvedURL ret: "+str(ret))
               list = []
               list.append(ret)
               printDBG( "getResolvedURL end OK" )
               return RetHost(RetHost.OK, value = list)
            else:
               printDBG( "getResolvedURL end" )
               return RetHost(RetHost.NOT_IMPLEMENTED, value = [])                
        else:
            printDBG( "getResolvedURL end" )
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = []) 
    ###################################################
    # Additional functions on class IPTVHost
    ###################################################

class Host:
    infoversion = "2017.10.01"
    inforemote  = "0.0.0"
    currList = []

    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.cm = pCommon.common()
        self.up = urlparser() 
        self.currList = []
        _url = 'https://gitlab.com/mosz_nowy/infoversion/raw/master/hosts/hostinfoversion.py'
        query_data = { 'url': _url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
           data = self.cm.getURLRequestData(query_data)
           #printDBG( 'Host init data: '+data )
           r = self.cm.ph.getSearchGroups(data, '''infoversion\s=\s['"]([^"^']+?)['"]''')[0] 
           if r:
              printDBG( 'r: '+r)
              self.inforemote=r
        except:
           printDBG( 'Host init query error' )
        printDBG( 'Host __init__ begin' )
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList end' )
        return 
    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        self.currList = self.listsItems(-1, '', 'main-menu')
        printDBG( 'Host getInitList end' )
        return self.currList

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( 'Host getListForItem begin' )
        valTab = []
        if len(self.currList[Index].urlItems) == 0:
           return valTab
        valTab = self.listsItems(Index, self.currList[Index].urlItems[0], self.currList[Index].urlSeparateRequest)
        self.currList = valTab
        printDBG( 'Host getListForItem end' )
        return self.currList

    def getLinksForVideo(self, url):
        printDBG("Urllist.getLinksForVideo url[%s]" % url)
        videoUrls = []
        uri, params   = DMHelper.getDownloaderParamFromUrl(url)
        printDBG(params)
        uri = urlparser.decorateUrl(uri, params)
       
        urlSupport = self.up.checkHostSupport( uri )
        if 1 == urlSupport:
            retTab = self.up.getVideoLinkExt( uri )
            videoUrls.extend(retTab)
            printDBG("Video url[%s]" % videoUrls)
            return videoUrls

    def _cleanHtmlStr(self, str):
            str = self.cm.ph.replaceHtmlTags(str, ' ').replace('\n', ' ')
            return clean_html(self.cm.ph.removeDoubles(str, ' ').replace(' )', ')').strip()) 

    def getPage(self, baseUrl, cookie_domain, cloud_domain, params={}, post_data=None):
        COOKIEFILE = os_path.join(GetCookieDir(), cookie_domain)
#        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
        self.USER_AGENT = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'
#        self.USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        params['cloudflare_params'] = {'domain':cloud_domain, 'cookie_file':COOKIEFILE, 'User-Agent':self.USER_AGENT}
        return self.cm.getPageCFProtection(baseUrl, params, post_data)

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        valTab = []

        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           valTab.append(CDisplayListItem('Toya', 'http://tvtoya.pl/live', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://tvtoya.pl/live', 1)], 'Toya', 'http://ocdn.eu/images/program-tv/ZmE7MDA_/cd36db78536d606386fcea91f3a5d88c.png', None)) 
           valTab.append(CDisplayListItem('Asta TV', 'http://www.tvasta.pl', CDisplayListItem.TYPE_CATEGORY, ['http://www.tvasta.pl/home/'], 'asta', 'http://www.tvasta.pl/resources/images/logo_tvasta.png', None)) 
           valTab.append(CDisplayListItem('Dami 24', 'http://dami24.pl', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UCL1u3cY7_nPjbZmKljCy_Cw/live'], 'dami', 'http://dami24.pl/images/headers/logo.png', None)) 
           valTab.append(CDisplayListItem('Echo24', 'http://www.echo24.tv', CDisplayListItem.TYPE_CATEGORY, ['http://www.echo24.tv/live'], 'echo', 'http://www.pro-run.pl/images/stories/2016/echo24.jpg', None)) 
           valTab.append(CDisplayListItem('Sudecka TV', 'http://www.tvsudecka.pl', CDisplayListItem.TYPE_CATEGORY, ['http://www.tvsudecka.pl/streams/single/1'], 'tvsudecka', 'https://pbs.twimg.com/profile_images/585880676693454849/2eAO2_hC.jpg', None)) 
           valTab.append(CDisplayListItem('Kłodzka TV', 'http://www.tvklodzka.pl', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UCOBLslh96FyyppmaYaJDwyQ/live'], 'klodzka', 'https://d-nm.ppstatic.pl/k/r/46/d7/4c227342bda20_o.jpg', None)) 
           #valTab.append(CDisplayListItem('Teletop Sudety TV', 'http://www.tvts.pl', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UC6jExnerSegVwurjdxHe2wg/live'], 'teletop', 'http://www.tvts.pl/wp-content/uploads/2015/03/1.jpg', None)) 
           valTab.append(CDisplayListItem('Zgorzelec TVT', 'http://www.tvtzgorzelec.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.tvtzgorzelec.pl/index.php/live', 1)], 'tvt', 'http://www.tvtzgorzelec.pl/images/TVT-mini.png', None)) 
           valTab.append(CDisplayListItem('Gorlice TV', 'http://gorlice.tv', CDisplayListItem.TYPE_CATEGORY, ['http://gorlice.tv/%C2%A0'], 'gorlice', 'http://gorlice.tv/static/gfx/service/gorlicetv/logo.png?96eb5', None)) 
           valTab.append(CDisplayListItem('Stella TVK', 'http://www.tvkstella.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.tvkstella.pl/live_tv', 1)], 'stella', 'http://www.tvkstella.pl/img/logo.png', None)) 
           valTab.append(CDisplayListItem('Narew TV', 'http://www.narew.info', CDisplayListItem.TYPE_CATEGORY, ['http://www.narew.info/streams/single/1'], 'narew', 'https://pbs.twimg.com/profile_images/684831832307810306/M9KmKBse_400x400.jpg', None)) 
           #valTab.append(CDisplayListItem('Pomorska TV', 'http://www.pomorska.tv/livestream', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.pomorska.tv/livestream', 1)], 'pomorska', 'http://www.pomorska.tv/templates/pomorskatv/img/pomorska-tv-logo.png', None)) 
           valTab.append(CDisplayListItem('WP1 TV', 'WP1 TV', CDisplayListItem.TYPE_CATEGORY, ['https://av-cdn-2.wpimg.pl/tv24/ngrp:wp1/chunklist_.m3u8'], 'wp1', 'http://telewizja-cyfrowa.com/wp-content/uploads/2016/09/wp1-logo.png', None)) 
           valTab.append(CDisplayListItem('Master TV', 'http://www.tv.master.pl', CDisplayListItem.TYPE_CATEGORY, ['http://www.tv.master.pl/tv_online.php'], 'master', 'http://www.tv.master.pl/grafika/TV_Master2.png', None))
           valTab.append(CDisplayListItem('Opoka TV', 'http://opoka.tv', CDisplayListItem.TYPE_CATEGORY, ['http://www.popler.tv/embed/player.php?user=Opokatv&popler=1&kody_code='], 'opoka', 'http://opoka.tv/wp-content/uploads/2016/10/OPTV2016weblgtp1bc.png', None)) 
           valTab.append(CDisplayListItem('Sfera TV', 'http://www.sferatv.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://stream.sferatv.pl/sferalive/_definst_/mp4:live3', 0)], 'sfera', 'http://www.sferatv.pl/images/logo_www.png', None)) 
           valTab.append(CDisplayListItem('EO TV', 'http://eotv.de/', CDisplayListItem.TYPE_CATEGORY, ['http://eotv.de/'], 'eotv', 'http://eotv.de/wp-content/uploads/2015/12/Cranberry-Logo.png', None))
           #valTab.append(CDisplayListItem('Kamery Ptaki w gniazdach na żywo', 'Ptaki w gniazdach na żywo', CDisplayListItem.TYPE_CATEGORY, [''], 'ptaki', 'http://dinoanimals.pl/wp-content/uploads/2013/05/Bocian-DinoAnimals.pl-5.jpg', None))
           valTab.append(CDisplayListItem('Kamery Toya GO', 'https://go.toya.net.pl/25', CDisplayListItem.TYPE_CATEGORY, ['https://go.toya.net.pl/25'], 'toyago', 'https://go.toya.net.pl/public/images/top_menu/logo-4.png?t=1494325022', None)) 
           valTab.append(CDisplayListItem('Podkarpacie TV', 'http://podkarpacielive.tv', CDisplayListItem.TYPE_CATEGORY, ['http://podkarpacielive.tv'], 'podkarpacie', 'http://podkarpacielive.tv/wp-content/themes/podkarpackielivetv/images/logo.png', None)) 
           valTab.append(CDisplayListItem('Żary TV', 'http://www.telewizjazary.pl', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UC29dc_mBUWW4mz5h754v88w/live'], 'zary', 'http://www.telewizjazary.pl/assets/wysiwig/images/logo/TVR_logo.png', None))
           valTab.append(CDisplayListItem('TRT PL', 'http://www.trt.pl/', CDisplayListItem.TYPE_CATEGORY, ['http://www.trt.pl/'], 'trt', 'http://www.trt.pl/images/logo-new.png', None))
           valTab.append(CDisplayListItem('Toruń TV', 'http://www.tvtorun.net/', CDisplayListItem.TYPE_CATEGORY, ['http://www.tvtorun.net/'], 'toruntv', 'http://www.tvtorun.net/public/img/new/logo.png', None))
           valTab.append(CDisplayListItem('Stream - Nadajemy TV', 'http://nadajemy.tv', CDisplayListItem.TYPE_CATEGORY, ['http://nadajemy.tv/api/api.php?method=getChannels'], 'nadajemy', 'http://www.tetex.com/wp-content/uploads/2015/11/Fotolia_92836261_Subscription_Monthly_M.jpg', None))
           valTab.append(CDisplayListItem('Stream - POLAND', 'http://civeci.com/POLAND.txt', CDisplayListItem.TYPE_CATEGORY, ['http://civeci.com/POLAND.txt'], 'POLAND-STREAMS', 'http://www.gizycko.pl/data/multimedia2/jpg/6733.jpg', None))
           valTab.append(CDisplayListItem('Stream - EUROPA', 'http://civeci.com/EUROPA.txt', CDisplayListItem.TYPE_CATEGORY, ['http://civeci.com/EUROPA.txt'], 'POLAND-STREAMS', 'http://www.gizycko.pl/data/multimedia2/jpg/6733.jpg', None))
           valTab.append(CDisplayListItem('Kamery Ośrodek Górnik - Łeba', 'http://gornik.pl/kamery.php', CDisplayListItem.TYPE_CATEGORY, ['http://gornik.pl/kamery.php'], 'gornik', 'http://gornik.pl/grafika/naglowek.png', None))
           valTab.append(CDisplayListItem('WTK Play - Poznań', 'http://wtkplay.pl/live', CDisplayListItem.TYPE_CATEGORY, ['http://wtkplay.pl/live'], 'wtk', 'http://wtkplay.pl/graphic/header/wtkplay_logo.png', None))
           valTab.append(CDisplayListItem('Lech TV', 'http://lech.tv/live', CDisplayListItem.TYPE_CATEGORY, ['http://lech.tv/program'], 'lechtv', 'http://lech.tv/graphics_new/all/lechtv_logo_top.png', None))
           valTab.append(CDisplayListItem('Euronews DE', 'http://de.euronews.com/live', CDisplayListItem.TYPE_CATEGORY, ['http://de.euronews.com/api/watchlive.json'], 'euronewsde', 'http://www.euronews.com/images/fallback.jpg', None))
           valTab.append(CDisplayListItem('Kamery WLKP24', 'http://wlkp24.info/kamery/', CDisplayListItem.TYPE_CATEGORY, ['http://wlkp24.info/kamery/'], 'wlkp24', 'http://archiwum.wlkp24.info/static/img/squarelogo400.jpg', None)) 
           valTab.append(CDisplayListItem('BG-Gledai TV', 'http://www.bg-gledai.tv', CDisplayListItem.TYPE_CATEGORY, ['http://www.bg-gledai.tv'], 'gledai', 'http://www.bg-gledai.tv/img/newlogo.png', None)) 
           valTab.append(CDisplayListItem('Stream - Goldvod', 'Goldvod', CDisplayListItem.TYPE_CATEGORY, ['http://api.j.pl/goldvod'], 'goldvod', 'http://goldvod.tv/assets/images/logo.png', None))
           valTab.append(CDisplayListItem('Zabrze TV', 'Zabrze TV', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UCyQL0IjtptnQ9PxmAfH3fKQ/live'], 'zabrze', 'http://tvzabrze.pl/assets/images/logo.png', None))
           valTab.append(CDisplayListItem('Kamery Lookcam', 'https://lookcam.com', CDisplayListItem.TYPE_CATEGORY, ['https://lookcam.com/kamerki/'], 'lookcam', 'https://r.cdn.cloudbitly.com/lookcam/static/images/logo_lookcam_oognet.png', None)) 
           valTab.append(CDisplayListItem('Fokus TV', 'http://www.fokus.tv', CDisplayListItem.TYPE_CATEGORY, ['http://www.fokus.tv'], 'fokus', 'http://www.fokus.tv/assets/gfx/logo-new.png', None)) 
           valTab.append(CDisplayListItem('News12 Long Island', 'http://longisland.news12.com/category/324508/live-streaming', CDisplayListItem.TYPE_CATEGORY, ['http://longisland.news12.com/category/324508/live-streaming'], 'n12', 'http://ftpcontent.worldnow.com/professionalservices/clients/news12/news12li/images/news12li-logo.png', None)) 

           valTab.sort(key=lambda poz: poz.name)
           valTab.insert(0,CDisplayListItem('Pobierz info o IPTV Player', 'Wersja hostinfoversion: '+self.infoversion, CDisplayListItem.TYPE_CATEGORY, ['https://gitlab.com/iptvplayer-for-e2/iptvplayer-for-e2/commits/master'], 'info', 'http://www.cam-sats.com/images/forumicons/ip.png', None)) 
           if self.infoversion <> self.inforemote and self.inforemote <> "0.0.0":
              valTab.insert(0,CDisplayListItem('---UPDATE---','UPDATE MENU',        CDisplayListItem.TYPE_CATEGORY,           [''], 'UPDATE',  '', None)) 
           if config.plugins.iptvplayer.religia.value:     
              valTab.append(CDisplayListItem('Piotr Natanek Ogłoszenia bieżące', 'http://www.christusvincit-tv.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.christusvincit-tv.pl/articles.php?article_id=120', 1)], 'religia', 'http://img.youtube.com/vi/JRHdinMsXmA/hqdefault.jpg', None)) 
              valTab.append(CDisplayListItem('Piotr Natanek Live', 'http://www.christusvincit-tv.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://185.48.128.148/hls playpath=test swfUrl=http://mediaserwer3.christusvincit-tv.pl/p/100/sp/10000/flash/kdp3/v3.9.9/kdp3.swf pageUrl=http://christusvincit-tv.pl/viewpage.php?page_id=1 live=1', 0)], 'religia', 'http://img.youtube.com/vi/JRHdinMsXmA/hqdefault.jpg', None)) 
              valTab.append(CDisplayListItem('Piotr Natanek Kazanie', 'http://christusvincit-tv.pl', CDisplayListItem.TYPE_CATEGORY, ['http://christusvincit-tv.pl/viewpage.php?page_id=1'], 'religia', 'http://img.youtube.com/vi/JRHdinMsXmA/hqdefault.jpg', None)) 
              valTab.append(CDisplayListItem('Sanktuarium Kraków-Łagiewniki', 'https://www.faustyna.pl', CDisplayListItem.TYPE_CATEGORY, ['https://www.faustyna.pl/zmbm/transmisja-on-line/'], 'faustyna', 'http://milosierdzie.pl/images/menu-obrazki/obraz.png', None)) 
              valTab.append(CDisplayListItem('Jasna Góra', 'http://www.jasnagora.pl', CDisplayListItem.TYPE_CATEGORY, ['http://www.jasnagora.pl/612,372,artykul,Kaplica_Matki_Bozej.aspx'], 'jasna', 'http://cdn19.se.smcloud.net/t/photos/280918/cudowny-wizerunek-matki-boskiej-czestochowskiej.jpg', None)) 
              valTab.append(CDisplayListItem('Parafia Skoczów   (exteplayer3)', 'http://www.kamera.parafiaskoczow.ox.pl/', CDisplayListItem.TYPE_CATEGORY, ['rtmp://80.51.121.254:5119/live/pip_video1'], 'skoczow', 'http://www.parafiaskoczow.ox.pl/templates/img/logo.png', None)) 
              valTab.append(CDisplayListItem('Parafia Skoczów 2   (exteplayer3)', 'http://www.kamera2.parafiaskoczow.ox.pl/', CDisplayListItem.TYPE_CATEGORY, ['rtmp://80.51.121.254:5119/live/pip_video2'], 'skoczow', 'http://www.parafiaskoczow.ox.pl/templates/img/logo.png', None)) 
              valTab.append(CDisplayListItem('Kaplicówka - Sanktuarium Św. Jana Sarkandra', 'http://kamera.pompejanska.pl/', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://80.51.121.254:5119/live/kaplicowka', 0)], 'kaplicowka', 'http://www.polskaniezwykla.pl/pictures/original/278033.jpg', None))               #valTab.append(CDisplayListItem('Parafia Górny Bor', 'http://parafiagornybor.pl/kamera-online', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://parafiagornybor.pl/kamera-online', 1)], 'gornybor', 'http://www.parafiagornybor.ox.pl/images/slider/slide_02.jpg', None)) 
              valTab.append(CDisplayListItem('Cieszyn - Parafia Św. Marii Magdaleny', 'http://parafiamagdaleny.pl', CDisplayListItem.TYPE_CATEGORY, ['http://parafiamagdaleny.pl/parafia/transmisja-wideo'], 'magdalena', 'http://www.polskiekrajobrazy.pl/images/stories/big/50261.jpg', None)) 
              valTab.append(CDisplayListItem('Parafia pw Narodzenia Najświętszej Maryi Panny w Piwnicznej - Zdrój', 'http://www.parafia.piwniczna.com', CDisplayListItem.TYPE_CATEGORY, ['http://www.parafia.piwniczna.com/s48-tv---online.html'], 'piwniczna', 'http://www.parafia.piwniczna.com/images/panel_boczny.jpg', None)) 
              valTab.append(CDisplayListItem('Dąbrowa Tarnowska Ołtarz', 'Parafia Najświętszej Maryi Panny Szkaplerznej', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://149.202.72.222:1936/live playpath=c2 swfUrl=http://www.alarmserwis.eu/components/com_hdflvplayer/hdflvplayer/hdplayer.swf pageUrl=http://alarmserwis.eu/dt/oltarz.html', 0)], '', 'http://www.dt.diecezja.tarnow.pl/wp-content/gallery/kosciol/dsc_0305.jpg', None)) 
              valTab.append(CDisplayListItem('Dąbrowa Tarnowska Adoracja', 'Parafia Najświętszej Maryi Panny Szkaplerznej', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://149.202.72.222:1936/live playpath=c3 swfUrl=http://alarmserwis.eu/components/com_hdflvplayer/hdflvplayer/hdplayer.swf pageUrl=http://alarmserwis.eu/dt/adoracja.html', 0)], '', 'http://www.dt.diecezja.tarnow.pl/wp-content/gallery/kosciol/dsc_0305.jpg', None)) 
              valTab.append(CDisplayListItem('Dąbrowa Tarnowska Nawa', 'Parafia Najświętszej Maryi Panny Szkaplerznej', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://149.202.72.222:1936/live playpath=c4 swfUrl=http://alarmserwis.eu/components/com_hdflvplayer/hdflvplayer/hdplayer.swf pageUrl=http://alarmserwis.eu/dt/nawa.html', 0)], '', 'http://www.dt.diecezja.tarnow.pl/wp-content/gallery/kosciol/dsc_0305.jpg', None)) 
              valTab.append(CDisplayListItem('Dąbrowa Tarnowska Chór', 'Parafia Najświętszej Maryi Panny Szkaplerznej', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://149.202.72.222:1936/live playpath=c5 swfUrl=http://alarmserwis.eu/components/com_hdflvplayer/hdflvplayer/hdplayer.swf pageUrl=http://alarmserwis.eu/dt/chor.htm', 0)], '', 'http://www.dt.diecezja.tarnow.pl/wp-content/gallery/kosciol/dsc_0305.jpg', None)) 
              valTab.append(CDisplayListItem('Maków Podhalański Ołtarz', 'Maków Podhalański Ołtarz', CDisplayListItem.TYPE_CATEGORY, ['http://www.parafiamakowska.pl/kamera-online/kamera-na-oltarz/'], 'makow', 'http://www.parafia.pixpro.pl/img/obraz_top.png', None)) 
              valTab.append(CDisplayListItem('Maków Podhalański Kaplica', 'Maków Podhalański Kaplica', CDisplayListItem.TYPE_CATEGORY, ['http://www.parafiamakowska.pl/kamera-online/kamera-w-kaplicy/'], 'makow', 'http://www.parafia.pixpro.pl/img/obraz_top.png', None)) 
              valTab.append(CDisplayListItem('Pogórze - Parafia NMP Królowej Polski', 'http://www.pogorze.katolik.bielsko.pl', CDisplayListItem.TYPE_CATEGORY, ['http://80.51.121.254/pogorze.m3u8'], 'pogorze', 'http://www.pogorze.info.pl/files/kosciol1.jpg', None)) 
              valTab.append(CDisplayListItem('Fatima', 'http://www.fatima.pt', CDisplayListItem.TYPE_CATEGORY, ['http://www.fatima.pt/pt/pages/transmissoes-online'], 'fatima', 'http://usti.reckokat.cz/images/fatima-2017.jpg', None)) 
              valTab.append(CDisplayListItem('TV Lourdes', 'https://www.lourdes-france.org', CDisplayListItem.TYPE_CATEGORY, ['https://www.lourdes-france.org/en/tv-lourdes'], 'lourdes', 'http://www.fronda.pl/site_media/media/uploads/maryja_lourdes.jpg', None)) 
              valTab.append(CDisplayListItem('CTV Watykan', 'http://www.ctv.va', CDisplayListItem.TYPE_CATEGORY, ['http://www.ctv.va/content/ctv/it/livetv.html'], 'ctv', 'http://www.ctv.va/content/ctv/it/_jcr_content/logo.img.png/1383824514179.png', None)) 
              valTab.append(CDisplayListItem('Basilica of St. Francis in Assisi', 'Basilica of St. Francis in Assisi', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.skylinewebcams.com/en/webcam/italia/umbria/perugia/basilica-san-francesco-assisi.html', 1)], '', 'https://ladybudd.files.wordpress.com/2012/08/basilica-of-st-francis-of-assisi.jpg', None)) 
              #valTab.append(CDisplayListItem('Chicago - Parafia św. Brunona', 'http://mass-online.org', CDisplayListItem.TYPE_CATEGORY, ['http://mass-online.org/st-brunos-church-chicago-il-usa/'], 'brunon', 'http://www.mszaswieta.com/UserContent/Church-Full-Size/parafia-swietego-brunona-chicago.jpg', None)) 
              valTab.append(CDisplayListItem('Wilno - Sanktuarium Miłosierdzia Bożego', 'http://msza-online.net/sanktuarium-milosierdzia-bozego-wilno-litwa/', CDisplayListItem.TYPE_CATEGORY, ['http://msza-online.net/sanktuarium-milosierdzia-bozego-wilno-litwa/'], 'wilno', 'http://www.faustyna.eu/IMG_1919aa.jpg', None)) 
              valTab.append(CDisplayListItem('Edmonton, Kanada - Parafia Różańca Świętego', 'http://msza-online.net', CDisplayListItem.TYPE_CATEGORY, ['http://msza-online.net/parafia-rozanca-swietego-edmonton-kanada/'], 'edmonton', 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Holy_Rosary_Church_Edmonton_Alberta_Canada_01A.jpg/1200px-Holy_Rosary_Church_Edmonton_Alberta_Canada_01A.jpg', None)) 
              valTab.append(CDisplayListItem('TV Medziugorje', 'http://www.centrummedjugorje.pl', CDisplayListItem.TYPE_CATEGORY, ['http://www.centrummedjugorje.pl/PL-H516/video.html'], 'medju', 'http://www.medjugorje.org.pl/images/medjugorje-2.jpg', None)) 
              valTab.append(CDisplayListItem('Heroldsbach - Gnadenkapelle', 'http://heroldsbach.esgibtmehr.net', CDisplayListItem.TYPE_CATEGORY, ['http://heroldsbach.esgibtmehr.net/doku.php?id=gnadenkapelle'], 'Heroldsbach', 'http://static.panoramio.com/photos/original/130564119.jpg', None)) 
              valTab.append(CDisplayListItem('Heroldsbach - Rosenkranzkapelle', 'http://heroldsbach.esgibtmehr.net', CDisplayListItem.TYPE_CATEGORY, ['http://heroldsbach.esgibtmehr.net/doku.php?id=rosenkranzkapelle'], 'Heroldsbach', 'https://image.jimcdn.com/app/cms/image/transf/none/path/sfb302df63f1bb549/image/id6c593d789b741f4/version/1391965689/image.jpg', None)) 
              valTab.append(CDisplayListItem('Heroldsbach - Krypta', 'http://heroldsbach.esgibtmehr.net', CDisplayListItem.TYPE_CATEGORY, ['http://heroldsbach.esgibtmehr.net/doku.php?id=krypta'], 'Heroldsbach', 'http://www.gebetsstaette-heroldsbach.de/bilder/PICT0068_1.jpg', None)) 
              valTab.append(CDisplayListItem('Heroldsbach - Marienkirche', 'http://heroldsbach.esgibtmehr.net', CDisplayListItem.TYPE_CATEGORY, ['http://heroldsbach.esgibtmehr.net/doku.php?id=marienkirche#marienkirche_-_24h_livestream'], 'Heroldsbach', 'http://www.heroldsbach-pilgerverein.de/bilder/rundgang_5_g.jpg', None)) 
              valTab.append(CDisplayListItem('Domradio.de', 'domradio.de', CDisplayListItem.TYPE_CATEGORY, ['https://www.youtube.com/channel/UCgX-WrCB5ALQOILWx-b6gUg/live'], 'domradio', 'https://www.domradio.de/sites/all/themes/domradio/images/logo.png', None)) 
              valTab.append(CDisplayListItem('TV Trwam', 'http://www.tv-trwam.pl', CDisplayListItem.TYPE_CATEGORY, ['http://trwamtv.live.e55-po.insyscd.net/trwamtv.smil/playlist.m3u8'], 'trwam', 'http://www.tv-trwam.pl/Content/images/trwam-2/logo.png', None)) 
              valTab.append(CDisplayListItem('Kluczbork - Parafia Najświętszego Serca Pana Jezusa', 'http://nspjkluczbork.pl/uncategorized/kamera/', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://nspjkluczbork.pl/uncategorized/kamera/', 1)], 'kluczbork', 'http://nspjkluczbork.pl/wp-content/uploads/2016/11/33_-1200x675.jpg', None)) 
              valTab.append(CDisplayListItem('Tomaszów Lubelski - Kościół pw. Zwiastowania Najświętszej Marii Panny', 'http://www.tomaszow-sanktuarium.pl', CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://www.tomaszow-sanktuarium.pl/niedzielna-transmisja-wideo/', 1)], 'tomaszow', 'http://lubelskie.regiopedia.pl/sites/default/files/imagecache/width630px/photos/foto07.jpg', None)) 
              valTab.append(CDisplayListItem('Kodeń - Sanktuarium Matki Bożej', 'http://www.koden.com.pl/', CDisplayListItem.TYPE_CATEGORY, ['https://worldcam.live/pl/webcam/koden'], 'koden', 'http://img2.garnek.pl/a.garnek.pl/017/153/17153628_800.0.jpg/koden-sanktuarium-maryjne.jpg', None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        if 'trwam' == name:
            printDBG( 'Host listsItems begin name='+name )
            if self.cm.isValidUrl(url): 
                tmp = getDirectM3U8Playlist(url)
                for item in tmp:
                    #printDBG( 'Host listsItems valtab: '  +str(item) )
                    valTab.append(CDisplayListItem(item['name'], item['url'],  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://www.tv-trwam.pl/Content/images/trwam-2/logo.png', None))
            return valTab
        if 'wp1' == name:
            printDBG( 'Host listsItems begin name='+name )
            if self.cm.isValidUrl(url): 
                tmp = getDirectM3U8Playlist(url)
                for item in tmp:
                    #printDBG( 'Host listsItems valtab: '  +str(item) )
                    valTab.append(CDisplayListItem(item['name'], item['url'],  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, '', None))
            return valTab
        if 'pogorze' == name:
            printDBG( 'Host listsItems begin name='+name )
            if self.cm.isValidUrl(url): 
                tmp = getDirectM3U8Playlist(url)
                for item in tmp:
                    #printDBG( 'Host listsItems valtab: '  +str(item) )
                    valTab.append(CDisplayListItem('Pogórze - Parafia NMP Królowej Polski', item['url'],  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://www.pogorze.info.pl/files/kosciol1.jpg', None))
            return valTab
        if 'skoczow' == name:
            printDBG( 'Host listsItems begin name='+name )
            Aurl = 'rtmp://80.51.121.254:5119/live/pip_sound'
            Vurl = url
            mergeurl = decorateUrl("merge://audio_url|video_url", {'audio_url':Aurl, 'video_url':Vurl, 'prefered_merger':'MP4box'}) 
            printDBG( 'Host mergeurl:  '+mergeurl )
            valTab.append(CDisplayListItem('Parafia Skoczów ', Vurl+'|'+Aurl,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', mergeurl, 0)], 0, '', None))
            return valTab 

        if 'gledai' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'gledai.cookie')
            host = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
            header = {'Referer':url, 'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}   
            try: data = self.cm.getURLRequestData({ 'url': url, 'header': header, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            printDBG( 'Host listsItems data1: '+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="menu-item', '</li>')
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url: Title = Url.split('/')[-1]
                if not 'premium' in Title and not 'gledai' in Title:
                    valTab.append(CDisplayListItem(Title,Title,CDisplayListItem.TYPE_CATEGORY, [Url],'gledai-clips', '', None)) 
            return valTab  
        if 'gledai-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'gledai.cookie')
            host = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
            header = {'Referer':url, 'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}   
            try: data = self.cm.getURLRequestData({ 'url': url, 'header': header, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            printDBG( 'Host listsItems data1: '+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<h2 class="post', '</h2>')
            for item in data:
                #Title = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''', 1, True)[0]
                #Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Title = self._cleanHtmlStr(item) 
                valTab.append(CDisplayListItem(Title, Title,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, '', None))
            return valTab  

        if 'lookcam' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'lookcam.cookie')
            self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIEFILE}
            sts, data = self.getPage(url, 'lookcam.cookie', 'lookcam.com', self.defaultParams)
            if not sts: return ''
            printDBG( 'Host listsItems data1: '+str(data) )
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="cam-category">', '</div>', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li>', '</li>')
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Title = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'https://lookcam.com' + Url 
                valTab.append(CDisplayListItem(Title,Title,CDisplayListItem.TYPE_CATEGORY, [Url],'lookcam-clips', '', None)) 
            valTab.insert(0,CDisplayListItem("--- Live TV ---",     "Live TV",     CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'https://lookcam.com/livetv/player/', 1)], 0, '',None))
            return valTab  
        if 'lookcam-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'lookcam.cookie')
            self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIEFILE}
            sts, data = self.getPage(url, 'lookcam.cookie', 'lookcam.com', self.defaultParams)
            if not sts: return ''
            printDBG( 'Host listsItems data1: '+str(data) )
            next_page = self.cm.ph.getDataBeetwenMarkers(data, 'title="Current Page">', 'Next', False)[1]
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="cam-box', 'class="pagination">', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li>', '</li>')
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Title = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''', 1, True)[0] 
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'https://lookcam.com' + Url 
                if Url:
                    valTab.append(CDisplayListItem(Title, Title,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, Image, None))
            if next_page: 
                match = re.compile('href="(.*?)"').findall(next_page)
                if match:
                    next_page = 'https://lookcam.com'+match[-1]
                    valTab.append(CDisplayListItem('Next', next_page, CDisplayListItem.TYPE_CATEGORY, [next_page], name, '', None))
            return valTab 

        if 'fokus' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'fokus.cookie')
            try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            printDBG( 'Host listsItems data1: '+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="slide"', '</a>')
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'http://www.fokus.tv' + Url 
                Title = self._cleanHtmlStr(item) 
                valTab.append(CDisplayListItem(Title,Title,CDisplayListItem.TYPE_CATEGORY, [Url],'fokus-groups', '', None)) 
            valTab.insert(0,CDisplayListItem("--- Nasze programy ---",     "Nasze programy",     CDisplayListItem.TYPE_CATEGORY,["http://www.fokus.tv/program-api-v1/programs-block"], 'fokus-nasze', '',None))
            valTab.insert(0,CDisplayListItem("--- Fokus TV na żywo ---",     "Fokus TV na żywo",     CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://stream.cdn.smcloud.net/fokustv-p/stream1', 0)], 0, 'http://www.lumi.net.pl/img/all/channel_logo_137_large.png',None))
            return valTab 
        if 'fokus-groups' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'fokus.cookie')
            try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            printDBG( 'Host listsItems data1: '+data )
            next = self.cm.ph.getSearchGroups(data, '''<a class="next_ftv" href=['"]([^"^']+?)['"]''', 1, True)[0]
            data = self.cm.ph.getDataBeetwenMarkers(data, 'class="small_video vod">', 'div class="zpr_red', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="box_small_video', '</div>')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''', 1, True)[0]
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'http://www.fokus.tv' + Url 
                valTab.append(CDisplayListItem(Title,Title,CDisplayListItem.TYPE_CATEGORY, [Url],'fokus-clips', Image, None)) 
            if next:
                if next.startswith('/'): next = 'http://www.fokus.tv' + next
                #valTab.append(CDisplayListItem('Next', 'Page: '+next, CDisplayListItem.TYPE_CATEGORY, [next], name, '', None))
            return valTab
        if 'fokus-nasze' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'fokus.cookie')
            try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            #printDBG( 'Host listsItems data1: '+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="box_small_video', '</div>')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''', 1, True)[0]
                if not Title: Title = self._cleanHtmlStr(item) 
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'http://www.fokus.tv' + Url 
                printDBG( 'Host Title: '+Title )
                printDBG( 'Host Url: '+Url )
                if Url == 'http://www.fokus.tv/wszystko-o/piec-lat-po-upadku-hitlera-1': Url = 'http://www.fokus.tv/programy/piec-lat-po-upadku-hitlera-czesc-ii/196-30907'
                if Title:
                    valTab.append(CDisplayListItem(Title,Title,CDisplayListItem.TYPE_CATEGORY, [Url],'fokus-clips', Image, None)) 
            return valTab
        if 'fokus-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            COOKIEFILE = os_path.join(GetCookieDir(), 'fokus.cookie')
            try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return valTab
            printDBG( 'Host listsItems data1: '+data )
            Title =''
            data2 = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="box_small_video', '</div>')
            for item in data2:
                Title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''', 1, True)[0]
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                if Url.startswith('/'): Url = 'http://www.fokus.tv' + Url 
                valTab.append(CDisplayListItem(Title, Title,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, Image, None))
            data2 = None
            Url = self.cm.ph.getSearchGroups(data, '''<source src=['"]([^"^']+?)['"]''', 1, True)[0]
            if Url and Title=='': valTab.append(CDisplayListItem('Link', '',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', url, 1)], 0, '', None))
            if not Url: 
                data2 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="hiper-descript">', '</div>', False)[1]
                nazwa = self.cm.ph.getSearchGroups(data2, '''alt=['"]([^"^']+?)['"]''', 1, True)[0]
                image = self.cm.ph.getSearchGroups(data2, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                desc = self.cm.ph.getSearchGroups(data2, '''"p-descript">([^>]+?)<''', 1, True)[0]
                if nazwa:
                    valTab.append(CDisplayListItem(nazwa, desc,  CDisplayListItem.TYPE_ARTICLE, [CUrlItem('', url, 0)], 0, image, None))
                if data2=='': 
                    data2 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="box_art_news">', '</div>', False)[1]
                    nazwa = self.cm.ph.getSearchGroups(data2, '''alt=['"]([^"^']+?)['"]''', 1, True)[0]
                    image = self.cm.ph.getSearchGroups(data2, '''src=['"]([^"^']+?)['"]''', 1, True)[0]
                    desc = self.cm.ph.getSearchGroups(data2, '''<p>([^>]+?)<''', 1, True)[0]
                    valTab.append(CDisplayListItem(nazwa, desc,  CDisplayListItem.TYPE_ARTICLE, [CUrlItem('', url, 0)], 0, image, None))
            return valTab  
#############################################
        if len(url)>8:
           query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
           try:
               printDBG( 'Host listsItems begin query' )
               data = self.cm.getURLRequestData(query_data)
           except:
               printDBG( 'Host listsItems ERROR '+url )
               return valTab
           printDBG( 'Host listsItems data'+data )

        if 'info' == name:
            tags_re = re.compile('(<(\S+?)>|<(\S+)\s.*?>)')
            x = 0
            Commit = re.findall('id="commit-(.*?)".*?commit-content">(.*?)</span>.*?class="commit-author.*?href.*?>(.*?)</a>.*?datetime="(.*?)"', data, re.S)
            if Commit:
               for (ID, Title, phName, phUpdated) in Commit:
                   phTitle = tags_re.sub(' ', Title)
                   phTitle = phTitle.strip()
                   phTitle = phTitle.strip(ID)
                   phTitle = re.sub(r'        (.*?) ', '', phTitle)
                   phTitle = decodeHtml(phTitle)
                   phUpdated = phUpdated.replace('T', '   ').replace('Z', '   ')
                   if config.plugins.iptvplayer.numerwersji.value:
                       parse = re.search('commit-row-message item.*?href="(.*?)"', Title, re.S)
                       if parse:
                           url = 'https://gitlab.com'+parse.group(1).replace('commit','raw')+'/IPTVPlayer/version.py'
                           query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                           try:
                               printDBG( 'Host listsItems begin query' )
                               data = self.cm.getURLRequestData(query_data)
                           except:
                               printDBG( 'Host listsItems ERROR' )
                           #printDBG( 'Host listsItems data'+data )
                           ver = self.cm.ph.getSearchGroups(data, '''IPTV_VERSION=['"]([^"^']+?)['"]''')[0] 
                           printDBG( 'Host listsItems ver: '+ver )
                           if ver:   
                               phName = ver

                   if x == config.plugins.iptvplayer.ilepozycji.value : return valTab
                   printDBG( 'Host listsItems ID: '+ID )
                   printDBG( 'Host listsItems phUpdated: '+phUpdated )
                   printDBG( 'Host listsItems phName: '+phName )
                   printDBG( 'Host listsItems phTitle: '+phTitle )
                   x += 1
                   valTab.append(CDisplayListItem(phUpdated+' '+phName+'  >>  '+phTitle,phTitle,CDisplayListItem.TYPE_CATEGORY, [''],'', '', None)) 
            printDBG( 'Host listsItems end' )
            return valTab

        if 'jasna' == name:
            printDBG( 'Host listsItems begin name='+name )
            Url = self.cm.ph.getSearchGroups(data, '''href=['"](https://www.youtube.com/channel/[^"^']+?)['"]''')[0]+'/live'
            videoUrls = self.getLinksForVideo(Url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Jasna Góra    '+Name, 'Jasna Góra    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.jasnagora.com/zdjecia/galerie_nowe/1755.jpg', None))
            return valTab 

        if 'echo' == name:
            printDBG( 'Host listsItems begin name='+name )
            try: data = self.cm.getURLRequestData({'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            printDBG( 'Host listsItems data youtube '+data )
            #data = self.cm.ph.getDataBeetwenMarkers(data, 'transmisja', 'transmisja', False)[1]
            Url = self.cm.ph.getSearchGroups(data, '''src: ['"]([^"^']+?m3u8)['"]''')[0] 
            if Url:
                Name = ''
                valTab.append(CDisplayListItem('Echo24    '+Name, 'Echo24    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.pro-run.pl/images/stories/2016/echo24.jpg', None))
                return valTab 
            Url = 'https://www.youtube.com/TelewizjaEcho24/live'
            videoUrls = self.getLinksForVideo(Url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Echo24    '+Name, 'Echo24    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.pro-run.pl/images/stories/2016/echo24.jpg', None))
            return valTab 

        if 'zabrze' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Zabrze TV    '+Name, 'Zabrze TV    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://tvzabrze.pl/assets/images/logo.png', None))
            return valTab 

        if 'tvsudecka' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('<iframe\ssrc="(http[s]?://www.youtube.com.*?)"', data, re.S|re.I)
            if link:
                pageUrl = link.group(1)
                query_data = {'url': pageUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                try:
                   data = self.cm.getURLRequestData(query_data)
                except:
                   printDBG( 'Host listsItems ERROR' )
                   return valTab
                #printDBG( 'Host listsItems data : '+data )
                link = re.search('href="(http[s]?://www.youtube.com.*?)"', data, re.S|re.I)
                videoUrls = self.getLinksForVideo(link.group(1))
                if videoUrls:
                   for item in videoUrls:
                      Url = item['url']
                      Name = item['name']
                      printDBG( 'Host Url:  '+Url )
                      printDBG( 'Host name:  '+Name )
                      valTab.append(CDisplayListItem('TV Sudecka   '+Name, 'TV Sudecka   '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://pbs.twimg.com/profile_images/585880676693454849/2eAO2_hC.jpg', None))
            return valTab 

        if 'klodzka' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('TV Kłodzka  '+Name, 'TV Kłodzka  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://d-nm.ppstatic.pl/k/r/46/d7/4c227342bda20_o.jpg', None))
            return valTab 

        if 'teletop' == name:
            printDBG( 'Host listsItems begin name='+name )
            #youtube_url = self.cm.ph.getSearchGroups(data, '''og:video:url" content=['"](https://www.youtube.com/embed[^"^']+?)['"]''')[0] 
            #try: data = self.cm.getURLRequestData({'url': youtube_url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
            #except:
            #    printDBG( 'Host listsItems ERROR' )
            #    return valTab
            #printDBG( 'Host listsItems data youtube '+data )
            #youtube_url = self.cm.ph.getSearchGroups(data, '''href=['"](http://www.youtube.com/watch[^"^']+?)['"]''')[0] 
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host Url:  '+Url )
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Teletop Sudety    '+Name, 'Teletop Sudety    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.tvts.pl/wp-content/uploads/2015/03/1.jpg', None))
            return valTab 

        if 'gorlice' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('src="(http://www.gorlice.tv/embed/.*?)"', data, re.S|re.I)
            if link:
                Url = link.group(1)
                query_data = {'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                try:
                   data = self.cm.getURLRequestData(query_data)
                except:
                   printDBG( 'Host listsItems ERROR' )
                   return valTab
                #printDBG( 'Host listsItems data youtube '+data )
                youtube_url = self.cm.ph.getSearchGroups(data, '''(//[www.]?youtu[^"^']+?)['"?]''')[0] 
                if youtube_url.startswith('//'): youtube_url = 'https:' + youtube_url 
                if not youtube_url:
                   youtube_url = self.cm.ph.getSearchGroups(data, '''(https://www.youtube.com[^"^']+?)['"]''')[0] 
                printDBG( 'Host listsItems data youtube_url '+youtube_url )
                videoUrls = self.getLinksForVideo(youtube_url)
                if videoUrls:
                   for item in videoUrls:
                      Url = item['url']
                      Name = item['name']
                      printDBG( 'Host name:  '+Name )
                      valTab.append(CDisplayListItem('TV Gorlice    '+Name, 'TV Gorlice    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://gorlice.tv/static/gfx/service/gorlicetv/logo.png?96eb5', None))
            return valTab 

        if 'narew' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('src="(http[s]?://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
                Url = link.group(1).replace('embed/','watch?v=')
                videoUrls = self.getLinksForVideo(Url)
                if videoUrls:
                   for item in videoUrls:
                      Url = item['url']
                      Name = item['name']
                      printDBG( 'Host Url:  '+Url )
                      printDBG( 'Host name:  '+Name )
                      valTab.append(CDisplayListItem('TV Narew  '+Name, 'TV Narew  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://pbs.twimg.com/profile_images/684831832307810306/M9KmKBse_400x400.jpg', None))
            return valTab 

        if 'lourdes' == name:
            printDBG( 'Host listsItems begin name='+name )
            youtube_link = self.cm.ph.getSearchGroups(data, '''href=['"](https://www.youtube.com[^"^']+?)['"]''')[0] 
            try: data = self.cm.getURLRequestData({'url': youtube_link, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            printDBG( 'Host listsItems data youtube '+data )
            youtube_link = self.cm.ph.getSearchGroups(data, '''data-context-item-id=['"]([^"^']+?)['"]''')[0] 
            videoUrls = self.getLinksForVideo('https://www.youtube.com/watch?v='+youtube_link)
            if videoUrls:
               for item in videoUrls:
                  Url = item['url']
                  Name = item['name']
                  printDBG( 'Host Url:  '+Url )
                  printDBG( 'Host name:  '+Name )
                  valTab.append(CDisplayListItem('TV Lourdes  '+Name, 'TV Lourdes  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://mozecoswiecej.pl/wp-content/uploads/2017/02/VirgendeLourdes.jpg', None))
            link = re.search('source: "(.*?)"', data, re.S|re.I)
            if link:
               valTab.append(CDisplayListItem('TV Lourdes  '+'Clappr', 'TV Lourdes  '+'Clappr',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', link.group(1), 0)], 0, 'http://mozecoswiecej.pl/wp-content/uploads/2017/02/VirgendeLourdes.jpg', None))
            Url = 'http://bsbdr-apple-live.adaptive.level3.net/apple/bstream/bsbdr/bdrhlslive1_Layer2.m3u8'
            valTab.append(CDisplayListItem('TV Lourdes  '+'(m3u8)', 'TV Lourdes  '+'(m3u8)',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://mozecoswiecej.pl/wp-content/uploads/2017/02/VirgendeLourdes.jpg', None))
            return valTab 

        if 'ctv' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('(https://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
               videoUrls = self.getLinksForVideo(link.group(1))
               if videoUrls:
                  for item in videoUrls:
                     Url = item['url']
                     Name = item['name']
                     printDBG( 'Host Url:  '+Url )
                     printDBG( 'Host name:  '+Name )
                     valTab.append(CDisplayListItem('CTV Watykan  '+Name, 'CTV Watykan  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.ctv.va/content/ctv/it/_jcr_content/logo.img.png/1383824514179.png', None))
            return valTab 

        if 'koden' == name:
            printDBG( 'Host listsItems begin name='+name )
            host = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
            header = {'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'} 
            query_data = { 'url': url, 'header': header, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                return valTab
            #printDBG( 'Host listsItems data '+data )
            m3u8_src = self.cm.ph.getSearchGroups(data, '''source: ['"](http[^"^']+?)['"]''')[0] 
            if m3u8_src:
                if self.cm.isValidUrl(m3u8_src): 
                    tmp = getDirectM3U8Playlist(m3u8_src)
                    for item in tmp:
                        valTab.append(CDisplayListItem('Kodeń    '+str(item['name']), 'Kodeń',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'https://upload.wikimedia.org/wikipedia/commons/5/50/Matka-boza-kodenska.jpg', None))
            return valTab 

        if 'eotv' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('<iframe src="(.*?)"', data, re.S|re.I)
            if link:
                Url = 'http://eotv.de'+link.group(1)
                query_data = {'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                try:
                   data = self.cm.getURLRequestData(query_data)
                except:
                   printDBG( 'Host listsItems ERROR' )
                   return valTab
                #printDBG( 'Host listsItems data '+data )
                link = re.findall('<script type.*?src="(.*?)"', data, re.S|re.I)
                if link:
                   Url = 'http://eotv.de'+link[-1]
                   query_data = {'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                   try:
                      data = self.cm.getURLRequestData(query_data)
                   except:
                      printDBG( 'Host listsItems ERROR' )
                      return valTab
                   #printDBG( 'Host listsItems data '+data )
                   http = re.search("http = '(.*?)'", data, re.S|re.I)
                   if http:
                      url = http.group(1)
                      if self.cm.isValidUrl(url): 
                          tmp = getDirectM3U8Playlist(url)
                          for item in tmp:
                                valTab.append(CDisplayListItem('EO TV   '+str(item['name']), 'EO TV',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'http://eotv.de/wp-content/uploads/2015/12/Cranberry-Logo.png', None))
                   rtmp = re.search("rtmp = '(.*?)'", data, re.S|re.I)
                   if rtmp:
                      rtmp = rtmp.group(1)+' live=1'
                      valTab.append(CDisplayListItem('EO TV   (rtmp)', 'EO TV',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', rtmp, 0)], 0, 'http://eotv.de/wp-content/uploads/2015/12/Cranberry-Logo.png', None))
            return valTab 

        if 'asta' == name:
            printDBG( 'Host listsItems begin name='+name )
            url = self.cm.ph.getSearchGroups(data, '''file:['"]([^"^']+?m3u8)['"]''', 1, True)[0]
            if self.cm.isValidUrl(url): 
                tmp = getDirectM3U8Playlist(url)
                for item in tmp:
                    valTab.append(CDisplayListItem(str(item['name']), str(item['url']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'http://www.tvasta.pl/resources/images/logo_tvasta.png', None))
            return valTab

        if 'toruntv' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>')
            for item in data:
               phUrl = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0] 
               if phUrl.startswith('//'): phUrl = 'http:' + phUrl
               printDBG( 'Host listsItems phUrl: '  +phUrl )
               phTitle = phUrl.split('.')[-1]
               if 'mpd' in phUrl:
                  valTab.append(CDisplayListItem(phTitle, phTitle,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 0)], 0, 'http://www.tvtorun.net/public/img/new/logo.png', None))
               if 'm3u8' in phUrl:
                  if self.cm.isValidUrl(phUrl): 
                     tmp = getDirectM3U8Playlist(phUrl)
                     for item in tmp:
                        #printDBG( 'Host listsItems valtab: '  +str(item) )
                        valTab.append(CDisplayListItem(item['name'], item['url'],  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://www.tvtorun.net/public/img/new/logo.png', None))
            return valTab

        if 'gornik' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>')
            x = 0
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''src=['"](http://player.webcamera.pl[^"^']+?)['"]''', 1, True)[0].strip() 
                if Url:
                    x += 1
                    try: data = self.cm.getURLRequestData({'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
                    except:
                        printDBG( 'Host listsItems ERROR' )
                        return valTab
                    printDBG( 'Host data '+data )
                    Url = self.cm.ph.getSearchGroups(data, '''<video id="video" src=['"]([^"^']+?)['"]''', 1, True)[0]
                    if Url.startswith('//'): Url = 'http:' + Url
                    if self.cm.isValidUrl(Url): 
                        tmp = getDirectM3U8Playlist(Url)
                        for item in tmp:
                            valTab.append(CDisplayListItem('Ośrodek Górnik - Łeba  '+str(x), str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, '', None))

            return valTab 

        if 'fatima' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = self.cm.ph.getSearchGroups(data, '''src=['"](https?://www.youtube.com[^"^']+?)['"]''')[0] 
            if not link:
                link = self.cm.ph.getSearchGroups(data, '''src=['"](https?://youtu[^"^']+?)['"]''')[0] 
            if link:
                videoUrls = self.getLinksForVideo(link)
                if videoUrls:
                    for item in videoUrls:
                        Url = item['url']
                        Name = item['name']
                        printDBG( 'Host Url:  '+Url )
                        printDBG( 'Host name:  '+Name )
                        valTab.append(CDisplayListItem('Fatima  '+Name, 'Fatima  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://science-info.pl/wp-content/uploads/2011/12/maria.jpg', None))
            link = re.search('(http://rd3.videos.sapo.pt.*?)"', data, re.S|re.I)
            if link:
                stream = 'rtmp://213.13.26.13/live/ playpath=santuario.stream swfUrl=http://js.sapo.pt/Projects/SAPOPlayer/20170410R1/jwplayer.flash.swf pageUrl=http://videos.sapo.pt/v6Lza88afnReWzVdAQap'
                valTab.append(CDisplayListItem('Fatima  '+'sapo', 'Fatima  '+'sapo',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', stream, 0)], 0, '', None))
            return valTab 

        if 'makow' == name:
            printDBG( 'Host listsItems begin name='+name )
            Url = self.cm.ph.getSearchGroups(data, '''<iframe src=['"]([^"^']+?)['"]''')[0] 
            if Url.startswith('//'): Url = 'http:' + Url
            if Url:
                try: data = self.cm.getURLRequestData({'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
                except:
                    printDBG( 'Host listsItems ERROR' )
                    return valTab
                printDBG( 'Host data '+data )
                Url = self.cm.ph.getSearchGroups(data, '''<video id="video" src=['"]([^"^']+?)['"]''', 1, True)[0]
                if Url.startswith('//'): Url = 'http:' + Url
                if self.cm.isValidUrl(Url): 
                    tmp = getDirectM3U8Playlist(Url)
                    for item in tmp:
                        valTab.append(CDisplayListItem('Maków', 'Maków',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, '', None))
            return valTab

        if 'magdalena' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('<iframe.*?src="(.*?)"', data, re.S|re.I)
            if link: 
                query_data = {'url': link.group(1), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                try:
                   data = self.cm.getURLRequestData(query_data)
                except:
                   printDBG( 'Host listsItems ERROR' )
                   return valTab
                #printDBG( 'Host listsItems data '+data )
                streamName = self.cm.ph.getSearchGroups(data, '''"streamName":['"]([^"^']+?)['"]''')[0] 
                rtmpPort = self.cm.ph.getSearchGroups(data, '''"rtmpPort":([^"^']+?),''')[0] 
                rtmp_app = self.cm.ph.getSearchGroups(data, '''rtmp_app = ['"]([^"^']+?)['"]''')[0] 
                rtmp_host = self.cm.ph.getSearchGroups(link.group(1), '''//([^"^']+?):''')[0] 
                printDBG( 'Host listsItems streamName: '+streamName )
                printDBG( 'Host listsItems rtmpPort: '+rtmpPort )
                printDBG( 'Host listsItems rtmp_app: '+rtmp_app )
                printDBG( 'Host listsItems rtmp_host: '+rtmp_host )
                hls_url = link.group(1).replace('embed.html?dvr=false','index.m3u8')
                if self.cm.isValidUrl(hls_url): 
                    tmp = getDirectM3U8Playlist(hls_url)
                    for item in tmp:
                        valTab.append(CDisplayListItem('Cieszyn  m3u8', str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg/240px-Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg', None))
                if rtmp_app:
                    rtmp_url = 'rtmp://'+rtmp_host+':'+rtmpPort+'/'+rtmp_app+'/'+streamName+' live=1'
                    valTab.append(CDisplayListItem('Cieszyn  rtmp', 'Cieszyn  rtmp',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', rtmp_url, 0)], 0, 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg/240px-Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg', None))
                f4m_url = link.group(1).replace('embed.html?dvr=false','manifest.f4m')
                valTab.append(CDisplayListItem('Cieszyn  f4m', 'Cieszyn  f4m',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', f4m_url, 0)], 0, 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg/240px-Cieszyn_sw_Marii_Magdaleny_od_pd_wsch.jpg', None))
            return valTab 

        if 'brunon' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('(https://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
                videoUrls = self.getLinksForVideo(link.group(1))
                if videoUrls:
                    for item in videoUrls:
                        Url = item['url']
                        Name = item['name']
                        printDBG( 'Host Url:  '+Url )
                        printDBG( 'Host name:  '+Name )
                        valTab.append(CDisplayListItem('Parafia św. Brunona  '+Name, 'Parafia św. Brunona  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.polishnews.com/art_pics/A_Brunona.jpg', None))
            return valTab 

        if 'wilno' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('(https://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
                videoUrls = self.getLinksForVideo(link.group(1))
                if videoUrls:
                    for item in videoUrls:
                        Url = item['url']
                        Name = item['name']
                        printDBG( 'Host Url:  '+Url )
                        printDBG( 'Host name:  '+Name )
                        valTab.append(CDisplayListItem('Wilno  '+Name, 'Wilno  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://zgromadzenie.faustyna.org/wp-content/uploads/2016/03/DSCF7213.jpg', None))
            return valTab 

        if 'edmonton' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('(https://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
                videoUrls = self.getLinksForVideo(link.group(1))
                if videoUrls:
                    for item in videoUrls:
                        Url = item['url']
                        Name = item['name']
                        printDBG( 'Host Url:  '+Url )
                        printDBG( 'Host name:  '+Name )
                        valTab.append(CDisplayListItem('Edmonton, Kanada  '+Name, 'Edmonton, Kanada  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Holy_Rosary_Church_Edmonton_Alberta_Canada_01A.jpg/1200px-Holy_Rosary_Church_Edmonton_Alberta_Canada_01A.jpg', None))
            return valTab 

        if 'medju' == name:
            printDBG( 'Host listsItems begin name='+name )
            source_m3u8 = self.cm.ph.getSearchGroups(data, '''<source src=['"]([^"^']+?)['"]''')[0] 
            if source_m3u8:
               if self.cm.isValidUrl(source_m3u8): 
                  tmp = getDirectM3U8Playlist(source_m3u8)
                  for item in tmp:
                     valTab.append(CDisplayListItem('TV Medziugorje   (m3u8)', 'TV Medziugorje   '+ str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'http://www.churchmilitant.com//images/social_images/2015-06-10-niles-a.jpg', None))
            source_rtmp = self.cm.ph.getSearchGroups(data, '''file:['"]([^"^']+?)['"]''')[0] 
            if source_rtmp:
               playpath = source_rtmp.split('/')[-1]
               rtmp = source_rtmp.replace('/'+playpath,'')
               Url = '%s playpath=%s swfUrl=http://p.jwpcdn.com/6/12/jwplayer.flash.swf pageUrl=http://www.centrummedjugorje.pl/PL-H516/video.html live=1' % (rtmp, playpath)
               valTab.append(CDisplayListItem('TV Medziugorje   (rtmp)', 'TV Medziugorje',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.churchmilitant.com//images/social_images/2015-06-10-niles-a.jpg', None))
            return valTab

        if 'trt' == name:
            printDBG( 'Host listsItems begin name='+name )
            menu = self.cm.ph.getDataBeetwenMarkers(data, 'Strona główna', 'class="fa fa-music"', False)[1]
            printDBG( 'Host listsItems menu='+str(menu) )
            menu = self.cm.ph.getAllItemsBeetwenMarkers(menu, '<a', '</a>')
            printDBG( 'Host listsItems trt='+str(menu) )
            for item in menu:
                phUrl = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                phTitle = self.cm.ph.getSearchGroups(item, '''</i>([^"^']+?)<''', 1, True)[0] 
                #phTitle = phUrl.split('/')[-1]
                if phUrl.startswith('/'): phUrl = 'http://www.trt.pl' + phUrl
                phTitle = phTitle.replace('&nbsp;','').replace('<strong>','')
                printDBG( 'Host listsItems phUrl: '  +phUrl )
                printDBG( 'Host listsItems phTitle: '+phTitle )
                valTab.append(CDisplayListItem(phTitle,phTitle,CDisplayListItem.TYPE_CATEGORY, [phUrl],'trt-clips', '', None)) 
            menu = None
            return valTab
        if 'trt-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            next = self.cm.ph.getDataBeetwenMarkers(data, 'class="container"', '&raquo;', False)[1]
            next = self.cm.ph.getSearchGroups(next, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="tile-video">', 'class="info-block"')
            printDBG( 'Host listsItems trt='+str(data) )
            for item in data:
                phTitle = self.cm.ph.getSearchGroups(item, '"tile-title"([^>]+?)href="([^"]+?)"')[0] 
                phUrl = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                phImage = self.cm.ph.getSearchGroups(item, '''img src=['"]([^"^']+?)['"]''', 1, True)[0] 
                phTime = self.cm.ph.getSearchGroups(item, '''time">([^"^']+?)<''', 1, True)[0] 
                phTitle = phUrl.split('/')[-1]
                phTitle = phTitle.replace('quot-','').replace('-',' ')

                if phUrl.startswith('/'): phUrl = 'http://www.trt.pl' + phUrl
                printDBG( 'Host listsItems phUrl: '  +phUrl )
                printDBG( 'Host listsItems phTitle: '+phTitle )
                valTab.append(CDisplayListItem(phTitle, '['+phTime+'] '+phTitle,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, phImage, None))
            if next:
                if next.startswith('/'): next = 'http://www.trt.pl' + next
                next = next.replace('&amp;','&')
                valTab.append(CDisplayListItem('Next', 'Page: '+next.split('/')[-1], CDisplayListItem.TYPE_CATEGORY, [next], name, '', None))
            return valTab

        if 'Heroldsbach' == name:
            printDBG( 'Host listsItems begin name='+name )
            source_m3u8 = self.cm.ph.getSearchGroups(data, '''file['"]: ['"]([^"^']+?m3u8)['"]''')[0] 
            if source_m3u8:
               if self.cm.isValidUrl(source_m3u8): 
                  tmp = getDirectM3U8Playlist(source_m3u8)
                  for item in tmp:
                     valTab.append(CDisplayListItem('Heroldsbach   (m3u8)', 'Heroldsbach  '+str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, '', None))
            source_rtmp = self.cm.ph.getSearchGroups(data, '''file['"]: ['"](rtmp[^"^']+?)['"]''')[0] 
            if source_rtmp:
               valTab.append(CDisplayListItem('Heroldsbach   (rtmp)', 'Heroldsbach',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', source_rtmp, 0)], 0, '', None))
            return valTab

        if 'domradio' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Domradio.de    '+Name, 'Domradio.de    '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://www.domradio.de/sites/all/themes/domradio/images/logo.png', None))
            return valTab 

        if 'piwniczna' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo('https://www.youtube.com/channel/UCLdNRt-R-qnTTd6zSWXHZVQ/live')
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host Url:  '+Url )
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Piwniczna - Zdrój  '+Name, 'Piwniczna - Zdrój  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.parafia.piwniczna.com/images/panel_boczny.jpg', None))
            return valTab 

        if 'opoka' == name:
            printDBG( 'Host listsItems begin name='+name )
            if 'sources:' in data:
                data2 = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
                videoUrl = self.cm.ph.getSearchGroups(data2, '''src[^'"]*?['"]([^'"]+?)['"]''')[0]
                videoUrl2 = self.cm.ph.getSearchGroups(data2, '''src[^'"]*?['"](rtmp[^'"]+?)['"]''')[0]
                data2 = None
                printDBG( 'Host videoUrl='+videoUrl )
                printDBG( 'Host videoUrl2='+videoUrl2 )
                if videoUrl:
                    if videoUrl.startswith('//'): url = 'http:'+videoUrl
                    if self.cm.isValidUrl(url): 
                        tmp = getDirectM3U8Playlist(url)
                        for item in tmp:
                            valTab.append(CDisplayListItem('Opoka TV   '+str(item['name']), 'Opoka TV',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, 'http://itvmedia.pl/uploaded/loga_itv_ok/opoka%20TV.png', None))
                if videoUrl2:
                    valTab.append(CDisplayListItem('Opoka TV   (rtmp)', 'Opoka TV',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', videoUrl2, 0)], 0, 'http://itvmedia.pl/uploaded/loga_itv_ok/opoka%20TV.png', None))
            return valTab

        if 'master' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = re.search('(https://www.youtube.com/embed/.*?)"', data, re.S|re.I)
            if link:
                videoUrls = self.getLinksForVideo(link.group(1))
                if videoUrls:
                    for item in videoUrls:
                        Url = item['url']
                        Name = item['name']
                        printDBG( 'Host Url:  '+Url )
                        printDBG( 'Host name:  '+Name )
                        valTab.append(CDisplayListItem('TV Master  '+Name, 'TV Master  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.tv.master.pl/grafika/TV_Master2.png', None))
            return valTab 

        if 'dami' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Dami 24  '+Name, 'Dami 24  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://dami24.pl/images/headers/logo.png', None))
            return valTab

        if 'zary' == name:
            printDBG( 'Host listsItems begin name='+name )
            videoUrls = self.getLinksForVideo(url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Żary TV  '+Name, 'Żary TV   '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'http://www.telewizjazary.pl/assets/wysiwig/images/logo/TVR_logo.png', None))
            return valTab

        if 'toyago' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<ul class="active">', '</a>')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''">([^"^']+?)</a>''', 1, True)[0] 
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Url = 'https://go.toya.net.pl'+Url
                Title = Title.replace('&nbsp;',' ').replace('</span>',' ')
                printDBG( 'Host listsItems Title:'+Title )
                if Title <> 'Kamery':
                    valTab.append(CDisplayListItem(Title, Title, CDisplayListItem.TYPE_CATEGORY, [Url], 'toyago-clips', '', None)) 
            return valTab
        if 'toyago-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            #printDBG( 'Host listsItems data toyago: '+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="item isotope-item --locked search-item"', '<time datetime')
            printDBG( 'Host listsItems data toyago2: '+str(data) )

            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^"^']+?)['"]''', 1, True)[0] 
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0] 
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Url = 'https://go.toya.net.pl'+Url
                valTab.append(CDisplayListItem(Title, Title,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, Image, None))
            return valTab

        if 'wlkp24' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<h4 class="vc_tta-panel-title">', '</div></div></div></div>')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''title-text">([^"^']+?)<''', 1, True)[0] 
                Url = self.cm.ph.getSearchGroups(item, '''<div id=['"]([^"^']+?)['"]''', 1, True)[0] 
                valTab.append(CDisplayListItem(Title, Title, CDisplayListItem.TYPE_CATEGORY, [Url], 'wlkp24-clips', '', None)) 
            return valTab
        if 'wlkp24-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            source = '"#'+url+'"'
            query_data = {'url': 'http://wlkp24.info/kamery/', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            data = self.cm.ph.getDataBeetwenMarkers(data, source, '</script>', False)[1]
            url_m3u8 = self.cm.ph.getSearchGroups(data, '''src:  ['"]([^"^']+?)['"]''', 1, True)[0] 
            url_rtmp = self.cm.ph.getSearchGroups(data, '''rtmp: ['"]([^"^']+?)['"]''', 1, True)[0] 
            if url_m3u8:
                if self.cm.isValidUrl(url_m3u8): 
                    tmp = getDirectM3U8Playlist(url_m3u8)
                    for item in tmp:
                        valTab.append(CDisplayListItem(str(item['name']), str(item['url']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, '', None))
            if url_rtmp:
                valTab.append(CDisplayListItem('rtmp', url_rtmp,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', url_rtmp, 0)], 0, '', None))
            return valTab

        if 'faustyna' == name:
            printDBG( 'Host listsItems begin name='+name )
            Url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
            if Url:
               printDBG( 'Host faustyna Url'+Url )
               if Url[:2] == "//": Url = "https:" + Url
               query_data = {'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
               try:
                  data = self.cm.getURLRequestData(query_data)
               except:
                   printDBG( 'Host listsItems ERROR: '+Url )
                   proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=2e1'.format(urllib.quote(Url, ''))
                   try:
                      query_data = {'url': proxy, 'header': {'Referer': proxy, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'}, 'return_data': True}
                      data = self.cm.getURLRequestData(query_data)
                      #printDBG( 'Host faustyna data'+data )
                   except: 
                      return valTab
               #printDBG( 'Host faustyna data'+data )
               live=''
               link = re.findall('"m3u8_url":"(.*?)"', data, re.S|re.I)
               if link: 
                  for (Url) in link:
                     if 'broadcasts' in Url: 
                        if self.cm.isValidUrl(Url): 
                            tmp = getDirectM3U8Playlist(Url)
                            printDBG( 'Host faustyna tmp'+str(tmp) )
                            for item in tmp:
                               valTab.append(CDisplayListItem(str(item['name']), str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', str(item['url']), 0)], 0, '', None))
            return valTab

        if 'religia' == name:
            printDBG( 'Host listsItems begin name='+name )
            link = self.cm.ph.getSearchGroups(data, '''iframe\ssrc=['"]([^"^']+?)['"]''')[0] 
            try: data = self.cm.getURLRequestData({'url': link, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
            except:
                printDBG( 'Host listsItems ERROR' )
                return ''
            #printDBG( 'Host listsItems data2'+data )
            link = re.search('"items":(.*?),"messages":', data, re.S|re.I)
            if link: 
                baza = link.group(1)
                printDBG( 'Host listsItems baza: '+baza )
                data = self.cm.ph.getAllItemsBeetwenMarkers(baza, '{', '}')
                for item in data:
                    phTitle = self.cm.ph.getSearchGroups(item, '''"name":['"]([^"^']+?)['"]''', 1, True)[0].encode("utf-8")  
                    phUrl = self.cm.ph.getSearchGroups(item, '''"downloadUrl":['"]([^"^']+?)['"]''', 1, True)[0].replace('\/','/') 
                    id = self.cm.ph.getSearchGroups(item, ''',"id":['"]([^"^']+?)['"]''', 1, True)[0] 
                    api = urllib.unquote('http://mediaserwer3.christusvincit-tv.pl/api_v3/index.php?service=multirequest&apiVersion=3.1&expiry=86400&clientTag=kwidget%3Av2.41&format=1&ignoreNull=1&action=null&1:service=session&1:action=startWidgetSession&1:widgetId=_100&2:ks=%7B1%3Aresult%3Aks%7D&2:service=baseentry&2:action=list&2:filter:objectType=KalturaBaseEntryFilter&2:filter:redirectFromEntryId=idididid&3:ks=%7B1%3Aresult%3Aks%7D&3:contextDataParams:referrer=http%3A%2F%2Fchristusvincit-tv.pl&3:contextDataParams:objectType=KalturaEntryContextDataParams&3:contextDataParams:flavorTags=all&3:contextDataParams:streamerType=auto&3:service=baseentry&3:entryId=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&3:action=getContextData&4:ks=%7B1%3Aresult%3Aks%7D&4:service=metadata_metadata&4:action=list&4:version=-1&4:filter:metadataObjectTypeEqual=1&4:filter:orderBy=%2BcreatedAt&4:filter:objectIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&4:pager:pageSize=1&5:ks=%7B1%3Aresult%3Aks%7D&5:service=cuepoint_cuepoint&5:action=list&5:filter:objectType=KalturaCuePointFilter&5:filter:orderBy=%2BstartTime&5:filter:statusEqual=1&5:filter:entryIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&kalsig=d575e4c088a57621d47fe2f48db13675')
                    api = api.replace('idididid', id)
                    try: data = self.cm.getURLRequestData({'url': api, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
                    except:
                        printDBG( 'Host listsItems ERROR' )
                        return ''
                    printDBG( 'Host listsItems data3'+data )
                    id = self.cm.ph.getSearchGroups(data, '''"videoCodecId":"avc1","status":2,"id":['"]([^"^']+?)['"]''', 1, True)[0] 
                    phUrl = phUrl.replace('raw/entry_id','serveFlavor/entryId').replace('version/0','v/2/flavorId/')
                    phUrl = phUrl+id+'/fileName/'+decodeHtml(phTitle).replace(' ','_')+'.mp4/forceproxy/true/name/a.mp4'
                    if phTitle <>'' and phTitle <> 'czo\u0142\u00f3wka':
                        printDBG( 'Host listsItems downloadUrl: '  +phUrl )
                        printDBG( 'Host listsItems name: '+phTitle ) 
                        printDBG( 'Host listsItems id: '+id ) 
                        valTab.append(CDisplayListItem(decodeNat2(phTitle), decodeNat2(phTitle),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 0)], 0, '', None))
        if 'podkarpacie' == name:
            printDBG( 'Host listsItems begin name='+name )
            image = 'http://podkarpacielive.tv/wp-content/themes/podkarpackielivetv/images/logo.png'
            valTab.insert(0,CDisplayListItem("--- Inne sporty ---", "Inne sporty", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/inne-sporty/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Różności ---", "Różności", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/roznosci/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Wywiady/komentarze ---", "Wywiady/komentarze", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/wywiady-komentarze/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Kraj/Świat ---", "Kraj/Świat", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/kraj-swiat/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Kibice ---", "Kibice", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/kibice/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Transmisje online ---", "Transmisje online", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/transmisje-online/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Bramki ---", "Bramki", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/bramki/'], 'podkarpacie-kategorie', image,None))
            valTab.insert(0,CDisplayListItem("--- Skróty wideo ---", "Skróty wideo", CDisplayListItem.TYPE_CATEGORY,['http://podkarpacielive.tv/kategoria/skroty-wideo/'], 'podkarpacie-kategorie', image,None))
            return valTab
        if 'podkarpacie-kategorie' == name:
            printDBG( 'Host listsItems begin name='+name )
            next = self.cm.ph.getSearchGroups(data, '''next page-numbers" href=['"]([^"^']+?)['"]''', 1, True)[0]

            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="videos">', 'footer', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<img', '</article>')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, '''<h3>([^"^']+?)</h3>''', 1, True)[0] 
                Url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0] 
                Time = self.cm.ph.getSearchGroups(item, '''<time>([^"^']+?)</time>''', 1, True)[0] 
                Image = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''', 1, True)[0] 
                Title = Title.replace('&#8211;','-')
                printDBG( 'Host listsItems Title: '  +Title )
                printDBG( 'Host listsItems Url: '  +Url )
                valTab.append(CDisplayListItem(Title, '['+Time+'] '+Title, CDisplayListItem.TYPE_CATEGORY, [Url], 'podkarpacie-clips', Image, None)) 
            if next:
               if next.startswith('/'): next = 'http://podkarpacielive.tv' + next
               next = next.replace('&amp;','&')
               valTab.append(CDisplayListItem('Next', 'Page: '+next, CDisplayListItem.TYPE_CATEGORY, [next], name, '', None))
            printDBG( 'Host listsItems end' )
            return valTab
        if 'podkarpacie-clips' == name:
            printDBG( 'Host listsItems begin name='+name )
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            #printDBG( 'Host listsItems data podkarpacie: '+data )
            Url = self.cm.ph.getSearchGroups(data, '''<iframe src=['"]([^"^']+?)['"]''', 1, True)[0] 
            if Url.startswith('//'): Url = 'https:' + Url 
            videoUrls = self.getLinksForVideo(Url)
            if videoUrls:
                for item in videoUrls:
                    Url = item['url']
                    Name = item['name']
                    printDBG( 'Host Url:  '+Url )
                    printDBG( 'Host name:  '+Name )
                    valTab.append(CDisplayListItem('Transmisja  '+Name, 'Transmisja  '+Name,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, '', None))
            return valTab

        if 'nadajemy' == name:
            printDBG( 'Host listsItems begin name='+name )
            result = simplejson.loads(data)
            if result:
                for item in result:
                    phUrl = str(item["url"].replace('\/','/'))  
                    phTitle = str(item["id"]) 
                    phImage = str(item["image"]) 
                    phUrl = phUrl+' live=1'  # flashVer=WIN 12,0,0,44'
                    phUrl = urlparser.decorateUrl(phUrl, {'Referer': url})
                    valTab.append(CDisplayListItem(phTitle,phUrl,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 0)], 0, phImage, None))
                valTab.sort(key=lambda poz: poz.name)
            return valTab

        if 'goldvod' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'EXTINF', '#')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, ''',([^,]+?)\n''', 1, True)[0].strip()
                Url = self.cm.ph.getSearchGroups(item, '''(rtmp[^>]+?)\n''', 1, True)[0]
                if not Url: Url = self.cm.ph.getSearchGroups(item, '''(http[^>]+?)\n''', 1, True)[0]
                printDBG( 'Host Title:  '+Title )
                printDBG( 'Host Url:  '+Url )
                valTab.append(CDisplayListItem(Title,Url,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'goldvod'+Title, 1)], 0, '', None))
                #valTab.sort(key=lambda poz: poz.name)
            return valTab

        if 'POLAND-STREAMS' == name:
            printDBG( 'Host listsItems begin name='+name )
            import codecs
            tmpDir = GetTmpDir() 
            source = os_path.join(tmpDir, 'POLAND.txt') 
            dest = os_path.join(tmpDir , '') 
            output = open(source,'wb')
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
            try:
                output.write(self.cm.getURLRequestData(query_data))
                output.close()
                printDBG( 'pobieranie' )
            except:
                printDBG( 'Blad pobierania' )
                return valTab
            try:
                with codecs.open(source, 'r') as fp:
                    lineNum = 0
                    while True:
                        line = fp.readline()
                        line = line.strip()
                        Name = str(line.split(',')[-2]).strip()
                        Url = str(line.split(',')[-1])
                        if 'mp4' in Url: Name = Name+'   (mp4)'
                        if 'm3u8' in Url: Name = Name+'   (m3u8)'
                        if '/udp/' in Url: Name = Name+'   (udp)'
                        if 'wmv' in Url: Name = Name+'   (wmv)'
                        if '.ts' in Url: 
                            Name = Name+'   (ts -> m3u8)'
                            Url = Url.replace('.ts','.m3u8')
                        printDBG( 'Host name:  '+Name )
                        printDBG( 'Host Url:  '+Url )
                        if Url:
                            if 'pvr.rete.netforms.cz' in Url: Url =''
                            if 'gogo.jksw.cz' in Url: Url =''
                            if 'fms.zulu.mk' in Url: Url =''
                            if 'clientportalpro.com' in Url: Url =''
                            if 'redcdn.pl' in Url: Url =''


                            if 'PART' in Name: Url =''
                        if Url:
                            if Url.startswith('http'):
                                valTab.append(CDisplayListItem(Name, Url,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://previews.123rf.com/images/sarahdesign/sarahdesign1403/sarahdesign140302179/26994295-live-stream-icon-Stock-Vector.jpg', None))
                            elif Url.startswith('rtmp://'):
                                valTab.append(CDisplayListItem(Name, Url,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://previews.123rf.com/images/sarahdesign/sarahdesign1403/sarahdesign140302179/26994295-live-stream-icon-Stock-Vector.jpg', None))
                            elif Url.startswith('rtps://'):
                                valTab.append(CDisplayListItem(Name, Url,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, 'https://previews.123rf.com/images/sarahdesign/sarahdesign1403/sarahdesign140302179/26994295-live-stream-icon-Stock-Vector.jpg', None))
                            lineNum += 1
                fp.close()
            except:
                printDBG( 'Koniec' )
                if os_path.exists(source):
                    printDBG( 'remove '+source )
                    os_remove(source)
                valTab.sort(key=lambda poz: poz.name)
                valTab.insert(0,CDisplayListItem("--- info:   Load "+str(lineNum)+" lines ---", url, CDisplayListItem.TYPE_CATEGORY,[], '', '',None))
            return valTab 

        if 'wtk' == name:
            printDBG( 'Host listsItems begin name='+name )
            url = self.cm.ph.getSearchGroups(data, ''';var player_src = ['"]([^"^']+?)['"]''', 1, True)[0]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="program_data_left">', '</tr>')
            programTV = ''
            for item in data:
                time = self.cm.ph.getSearchGroups(item, '''<div class="program_time">([^>]+?)</div>''', 1, True)[0]
                name = self.cm.ph.getSearchGroups(item, '''<div class="program_name">([^>]+?)</div>''', 1, True)[0]
                desc = self.cm.ph.getSearchGroups(item, '''<div class="program_description">([^>]+?)</div>''', 1, True)[0]
                programTV = programTV + time+'   '+name+'   '+desc+'\n'
            if url.startswith('//'): url = 'http:' + url
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            printDBG( 'Host listsItems data : '+data )
            m3u8_url = self.cm.ph.getSearchGroups(data, '''src: ['"]([^"^']+?m3u8)['"]''', 1, True)[0]
            if m3u8_url.startswith('//'): m3u8_url = 'http:' + m3u8_url
            if self.cm.isValidUrl(m3u8_url): 
               tmp = getDirectM3U8Playlist(m3u8_url)
               for item in tmp:
                  #printDBG( 'Host listsItems valtab: '  +str(item) )
                  valTab.append(CDisplayListItem(item['name'], programTV,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://wtkplay.pl/graphic/header/wtkplay_logo.png', None))
            return valTab

        if 'lechtv' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="program_lechtv_time">', '</div>')
            programTV = ''
            for item in data:
                time = self.cm.ph.getSearchGroups(item, '''"program_lechtv_time">([^>]+?)<''', 1, True)[0]
                name = self.cm.ph.getSearchGroups(item, '''program_lechtv_name.*?>([^>]+?)<''', 1, True)[0]
                desc = self.cm.ph.getSearchGroups(item, '''program_lechtv_desc.*?>([^>]+?)<''', 1, True)[0]
                programTV = programTV + time+'   '+name+'   '+desc+'\n'
            printDBG( 'Host listsItems programTV: '  +programTV)
            m3u8_url = 'https://redir.cache.orange.pl/jupiterecdn/o1-cl3//live/wtk-b-lechtv/live.m3u8'
            if self.cm.isValidUrl(m3u8_url): 
               tmp = getDirectM3U8Playlist(m3u8_url)
               for item in tmp:
                  #printDBG( 'Host listsItems valtab: '  +str(item) )
                  valTab.append(CDisplayListItem(item['name'], programTV,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://lech.tv/graphics_new/all/lechtv_logo_top.png', None))
            return valTab

        if 'euronewsde' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = '['+data+']'
            try:
                result = simplejson.loads(data)
                if result:
                    for item in result:
                        url = str(item["url"])  
            except:
                printDBG( 'Host listsItems ERROR JSON' )
                return valTab
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            printDBG( 'Host listsItems data : '+data )
            data = '['+data+']'
            try:
                result = simplejson.loads(data)
                if result:
                    for item in result:
                        primary = str(item["primary"])  
                        #backup = str(item["backup"])  
            except:
                printDBG( 'Host listsItems ERROR JSON' )
                return valTab
            m3u8_url = primary
            if m3u8_url.startswith('//'): m3u8_url = 'http:' + m3u8_url
            if self.cm.isValidUrl(m3u8_url): 
               tmp = getDirectM3U8Playlist(m3u8_url)
               for item in tmp:
                  #printDBG( 'Host listsItems valtab: '  +str(item) )
                  valTab.append(CDisplayListItem('Euronews DE  '+item['name'], 'Euronews DE',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['url'], 0)], 0, 'http://www.euronews.com/images/fallback.jpg', None))
            return valTab

        if 'czeskie' == name:
            printDBG( 'Host listsItems begin name='+name )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a href="./tv.php', '</a>')
            for item in data:
                Url = self.cm.ph.getSearchGroups(item, '''href=['"].([^"^']+?)['"]''', 1, True)[0]
                Title = self._cleanHtmlStr(item) 
                Image = self.cm.ph.getSearchGroups(item, '''img src=['"].([^"^']+?)['"]''', 1, True)[0]
                if Url.startswith('/'): Url = 'http://www.mojatv.info' + Url
                if Image.startswith('/'): Image = 'http://www.mojatv.info' + Image
                std = ''
                if 'webm' in Url: std = '   (webm)'
                valTab.append(CDisplayListItem(Title+std, Title,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, Image, None))
            return valTab

        if 'n12' == name:
            printDBG( 'Host listsItems begin name='+name )
            Url = self.cm.ph.getSearchGroups(data, '''src=['"](http://adx.news12.com[^"^']+?)['"]''', 1, True)[0]
            query_data = {'url': Url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try: data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            #printDBG( 'Host listsItems data1 '+data )
            url_m3u8 = self.cm.ph.getSearchGroups(data, '''var stream_url = ['"]([^"^']+?)['"]''', 1, True)[0]+'N12LI_WEST'
            printDBG( 'Host listsItems url_m3u8 '+url_m3u8 )
            query_data = {'url': url_m3u8, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try: data = self.cm.getURLRequestData(query_data)
            except:
                printDBG( 'Host listsItems ERROR' )
                return valTab
            #printDBG( 'Host listsItems data2 '+data )
            Aurl = self.cm.ph.getSearchGroups(data, '''URI=['"]([^"^']+?)['"]''', 1, True)[0]
            if self.cm.isValidUrl(url_m3u8): 
                tmp = getDirectM3U8Playlist(url_m3u8)
                for item in tmp:
                    printDBG( 'Host listsItems valtab: '  +str(item) )
                    Vurl = item['url']
                    mergeurl = decorateUrl("merge://audio_url|video_url", {'audio_url':Aurl, 'video_url':Vurl, 'prefered_merger':'MP4box'}) 
                    valTab.append(CDisplayListItem('News12    (exteplayer3)   '+str(item['name']), 'News12   '+str(item['name']),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', mergeurl, 0)], 0, 'http://ftpcontent.worldnow.com/professionalservices/clients/news12/news12li/images/news12li-logo.png', None))
                valTab.append(CDisplayListItem('News12 only video', Vurl,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Vurl, 0)], 0, 'http://ftpcontent.worldnow.com/professionalservices/clients/news12/news12li/images/news12li-logo.png', None))
                valTab.append(CDisplayListItem('News12 only audio', Aurl,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Aurl, 0)], 0, 'http://ftpcontent.worldnow.com/professionalservices/clients/news12/news12li/images/news12li-logo.png', None))
            return valTab 

        #http://www.peregrinus.pl/pl/podglad-gniazd-na-zywo
        if 'ptaki' == name:
            printDBG( 'Host listsItems begin name='+name )
            #valTab.append(CDisplayListItem('Rybołów Nadleśnictwo Lipka (m3u8)', 'Rybołów',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://91.225.157.3/mstream/lp_r/rybolowyonline.stream/index.m3u8', 0)], 0, 'http://portal.dobresciagi.pl/wp-content/uploads/2013/04/Rybo%C5%82%C3%B3w.jpg', None))
            valTab.append(CDisplayListItem('Rybołów Estonia (m3u8)', 'Rybołów',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://tv.eenet.ee/hls/kalakotkas2.m3u8', 0)], 0, 'http://portal.dobresciagi.pl/wp-content/uploads/2013/04/Rybo%C5%82%C3%B3w.jpg', None))
            valTab.append(CDisplayListItem('Sokół wędrowny Płock ORLEN (rtmp)', 'Sokół wędrowny Płock ORLEN',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'rtmp://stream.orlen.pl:1935/sokol playpath=gniazdo.stream swfUrl=http://webcam.peregrinus.pl/plugins/hwdvs-videoplayer/jwflv/mediaplayer.swf pageUrl=http://webcam.peregrinus.pl/pl/plock-orlen-podglad', 0)], 0, 'http://postis.pl/wp-content/uploads/sok%C3%B3%C5%82-w%C4%99drowny.jpeg', None))

            url = 'http://webcam.peregrinus.pl/pl/gdansk-lotos-podglad'
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
               data = self.cm.getURLRequestData(query_data)
            except:
               printDBG( 'Host listsItems ERROR' )
               return valTab
            #printDBG( 'Host listsItems data '+data )
            Url = self.cm.ph.getSearchGroups(data, '''['"](https://www.youtube.com/embed/[^"^']+?)['"]''')[0] 
            valTab.append(CDisplayListItem('Sokół wędrowny LOTOS Gdańsk (youtube)', 'Sokół wędrowny LOTOS Gdańsk',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, '', None))

            url = 'http://www.peregrinus.pl/pl/police'
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
               data = self.cm.getURLRequestData(query_data)
            except:
               printDBG( 'Host listsItems ERROR' )
               return valTab
            #printDBG( 'Host listsItems data '+data )
            Url = self.cm.ph.getSearchGroups(data, '''['"](https://www.youtube.com/embed/[^"^']+?)['"&]''')[0]
            if Url:
               valTab.append(CDisplayListItem('Sokół wędrowny Police Zakłady Chemiczne (youtube)', 'Sokół wędrowny Police Zakłady Chemiczne',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, '', None))

            url ='https://www.sokolka.tv/index.php/kamery-online/gniazdo-bocianie'
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
               data = self.cm.getURLRequestData(query_data)
            except:
               printDBG( 'Host listsItems ERROR' )
               return valTab
            #printDBG( 'Host listsItems data '+data )
            Url = self.cm.ph.getSearchGroups(data, '''(//www.youtube.com[^"^']+?)['"?]''')[0] 
            if Url:
               if Url.startswith('//'): Url = 'https:' + Url 
               valTab.append(CDisplayListItem('Kamera na bocianim gnieździe Sokółka (youtube)', 'Kamera na bocianim gnieździe Sokółka (youtube)',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 1)], 0, '', None))

            url ='http://www.bociany.ec.pl/'
            query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
               data = self.cm.getURLRequestData(query_data)
            except:
               printDBG( 'Host listsItems ERROR')
               return valTab
            #printDBG( 'Host listsItems data '+data )
            Url = self.cm.ph.getSearchGroups(data, '''file: ['"]([^"^']+?)['"]''')[0] 
            if Url:
               if Url.startswith('//'): Url = 'http:' + Url 
               valTab.append(CDisplayListItem('Kamera na bocianim gnieździe Przygodzice (Dolina Baryczy)', 'Kamera na bocianim gnieździe Przygodzice (Dolina Baryczy)',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', Url, 0)], 0, '', None))

            #valTab.append(CDisplayListItem('Czarny bocian Łódź (m3u8)', 'Czarny bocian dąb',  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', 'http://91.225.157.3/mstream2/lp_bocian2/bocianczarny2.stream/index.m3u8', 0)], 0, '', None))


            return valTab 

        if 'UPDATE' == name:
               printDBG( 'Host listsItems begin name='+name )
               valTab.append(CDisplayListItem(self.infoversion+' - Local version',   'Local  infoversion', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
               valTab.append(CDisplayListItem(self.inforemote+ ' - Remote version',  'Remote infoversion', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
               valTab.append(CDisplayListItem('ZMIANY W WERSJI',                    'ZMIANY W WERSJI',   CDisplayListItem.TYPE_CATEGORY, ['https://gitlab.com/mosz_nowy/infoversion/commits/master.atom'], 'UPDATE-ZMIANY', '', None)) 
               valTab.append(CDisplayListItem('Update Now',                         'Update Now',        CDisplayListItem.TYPE_CATEGORY, [''], 'UPDATE-NOW',    '', None)) 
               valTab.append(CDisplayListItem('Update Now & Restart Enigma2',       'Update Now & Restart Enigma2',        CDisplayListItem.TYPE_CATEGORY, ['restart'], 'UPDATE-NOW',    '', None)) 
               printDBG( 'Host listsItems end' )
               return valTab
        if 'UPDATE-ZMIANY' == name:
           printDBG( 'Host listsItems begin name='+name )
           try:
              data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phCats = re.findall("<entry>.*?<title>(.*?)</title>.*?<updated>(.*?)</updated>.*?<name>(.*?)</name>", data, re.S)
           if phCats:
              for (phTitle, phUpdated, phName ) in phCats:
                  phUpdated = phUpdated.replace('T', '   ')
                  phUpdated = phUpdated.replace('Z', '   ')
                  phUpdated = phUpdated.replace('+01:00', '   ')
                  phUpdated = phUpdated.replace('+02:00', '   ')
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  printDBG( 'Host listsItems phUpdated: '+phUpdated )
                  printDBG( 'Host listsItems phName: '+phName )
                  valTab.append(CDisplayListItem(phUpdated+' '+phName+'  >>  '+phTitle,phTitle,CDisplayListItem.TYPE_CATEGORY, [''],'', '', None)) 
           printDBG( 'Host listsItems end' )
           return valTab
        if 'UPDATE-NOW' == name:
           printDBG( 'Hostinfo listsItems begin name='+name )
           tmpDir = GetTmpDir() 
           import os
           source = os.path.join(tmpDir, 'iptv-host-info.tar.gz') 
           dest = os.path.join(tmpDir , '') 
           _url = 'https://gitlab.com/mosz_nowy/infoversion/repository/archive.tar.gz?ref=master'              
           output = open(source,'wb')
           query_data = { 'url': _url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
           try:
              output.write(self.cm.getURLRequestData(query_data))
              output.close()
              os.system ('sync')
              printDBG( 'Hostinfo pobieranie iptv-host-info.tar.gz' )
           except:
              if os.path.exists(source):
                 os.remove(source)
              printDBG( 'Hostinfo Błąd pobierania master.tar.gz' )
              valTab.append(CDisplayListItem('ERROR - Blad pobierania: '+_url,   'ERROR', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
              return valTab
           if os.path.exists(source):
              printDBG( 'Hostinfo Jest plik '+source )
           else:
              printDBG( 'Hostinfo Brak pliku '+source )
           cmd = 'tar -xzf "%s" -C "%s" 2>&1' % ( source, dest )  
           try: 
              os.system (cmd)
              os.system ('sync')
              printDBG( 'Hostinfo rozpakowanie  ' + cmd )
           except:
              printDBG( 'Hostinfo Błąd rozpakowania iptv-host-info.tar.gz' )
              os.system ('rm -f %s' % source)
              os.system ('rm -rf %siptv-host-info*' % dest)
              valTab.append(CDisplayListItem('ERROR - Blad rozpakowania %s' % source,   'ERROR', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
              return valTab
           printDBG( 'Hostinfo sleep' )
           try:
              import commands
              cmd = 'ls '+dest+' | grep infoversion-master*'
              katalog = commands.getoutput(cmd)
              printDBG( 'Hostinfo katalog list > '+ cmd )
              filepath = '%s%s' % (dest, katalog)
              if os.path.exists(filepath):
                 printDBG( 'Hostinfo Jest rozpakowany katalog '+filepath )
              else:
                 printDBG( 'Hostinfo Brak katalogu '+filepath )
           except:
              printDBG( 'Hostinfo error commands.getoutput ' )

           try:
              os.system ('cp -rf %sinfoversion-master*/* /usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/' % dest)
              os.system ('sync')
              printDBG( 'Hostinfo kopiowanie hostinfo do IPTVPlayer' )
           except:
              printDBG( 'Hostinfo blad kopiowania' )
              os.system ('rm -f %s' % source)
              os.system ('rm -rf %sinfoversion*' % dest)
              valTab.append(CDisplayListItem('ERROR - blad kopiowania',   'ERROR', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
              return valTab
           try:
              cmd = '/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/hosts/hostinfoversion.py'
              with open(cmd, 'r') as f:  
                 data = f.read()
                 f.close() 
                 wersja = re.search('infoversion = "(.*?)"', data, re.S)
                 aktualna = wersja.group(1)
                 printDBG( 'Hostinfo aktualna wersja wtyczki '+aktualna )
           except:
              printDBG( 'Hostinfo error openfile ' )
           printDBG( 'Hostinfo usuwanie plikow tymczasowych' )
           os.system ('rm -f %s' % source)
           os.system ('rm -rf %sinfoversion*' % dest)
           if url:
              try:
                 from enigma import quitMainloop
                 quitMainloop(3)
              except: pass
           valTab.append(CDisplayListItem('Update End. Please manual restart enigma2',   'Restart', CDisplayListItem.TYPE_CATEGORY, [''], '', '', None)) 
           printDBG( 'Hostinfo listsItems end' )
           return valTab
        return valTab 

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL begin' )
        printDBG( 'Host getResolvedURL url: '+url )
        videoUrl = ''
        valTab = []

        if url.startswith('https://lookcam.com'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            COOKIEFILE = os_path.join(GetCookieDir(), 'lookcam.cookie')
            self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIEFILE}
            sts, data = self.getPage(url, 'lookcam.cookie', 'lookcam.com', self.defaultParams)
            if not sts: return ''
            #printDBG( 'Host listsItems data1: '+str(data) )
            Url = self.cm.ph.getSearchGroups(data, '''source src=['"]([^"^']+?)['"]''')[0] 
            if Url.startswith('//'): Url = 'https:' + Url 
            if self.cm.isValidUrl(Url): 
                tmp = getDirectM3U8Playlist(Url)
                for item in tmp:
                    return item['url']
            return ''

        if url.startswith('goldvod'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            query_data = {'url': 'http://api.j.pl/goldvod', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except:
                return ''
            #printDBG( 'Host listsItems data2'+data )
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'EXTINF', '#')
            for item in data:
                Title = self.cm.ph.getSearchGroups(item, ''',([^,]+?)\n''', 1, True)[0].strip()
                Url = self.cm.ph.getSearchGroups(item, '''(rtmp[^>]+?)\n''', 1, True)[0]
                if not Url: Url = self.cm.ph.getSearchGroups(item, '''(http[^>]+?)\n''', 1, True)[0]
                printDBG( 'Host Title:  '+Title )
                printDBG( 'Host Url:  '+Url )
                if url == 'goldvod'+Title: return Url

        if url.startswith('http://www.bg-gledai.tv'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            COOKIEFILE = os_path.join(GetCookieDir(), 'gledai.cookie')
            host = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
            header = {'Referer':url, 'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}   
            try: data = self.cm.getURLRequestData({ 'url': url, 'header': header, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host getResolvedURL query error url: '+url )
                return ''
            #printDBG( 'Host listsItems data1: '+data )
            data = self.cm.ph.getDataBeetwenMarkers(data, '<iframe', '</iframe>', False)[1]
            Url = self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+?)['"]''', 1, True)[0] 
            if Url:
                try: data = self.cm.getURLRequestData({ 'url': Url, 'header': header, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
                except:
                    printDBG( 'Host getResolvedURL query error url: '+Url )
                    return ''
                #printDBG( 'Host listsItems data2: '+data )
                data = re.sub("document\.write\(unescape\('([^']+?)'\)", lambda m: urllib.unquote(m.group(1)), data) 
                #printDBG( 'Host listsItems data3: '+data )
                Url = self.cm.ph.getSearchGroups(data, '''playlist:  unescape\(['"]([^"^']+?)['"]''', 1, True)[0]
                if Url:
                    Url = urllib2.unquote(Url)
                    try: data = self.cm.getURLRequestData({ 'url': Url, 'header': header, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
                    except:
                        printDBG( 'Host getResolvedURL query error url: '+Url )
                        return ''
                    #printDBG( 'Host listsItems data4: '+data )
                    Url = self.cm.ph.getSearchGroups(data, '''file>([^"^']+?)<''', 1, True)[0].replace('&amp;','&')
                    return urlparser.decorateUrl(Url, {'User-Agent': host})
            return ''

        videoUrls = self.getLinksForVideo(url)
        if videoUrls:
           for item in videoUrls:
              Url = item['url']
              Name = item['name']
              printDBG( 'Host Url:  '+Url )
              printDBG( 'Host name:  '+Name )
              if len(Url)>8: return Url

        if 'assisi' in url:
            printDBG( 'Host getResolvedURL mainurl: '+url )
            COOKIEFILE = os_path.join(GetCookieDir(), 'skylinewebcams.cookie')
            try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True })
            except:
                printDBG( 'Host listsItems query error cookie' )
                return ''
            #printDBG( 'Host listsItems data: '+data )
            return self.cm.ph.getSearchGroups(data, '''url:['"]([^"^']+?)['"]''', 1, True)[0]

        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            printDBG( 'Host listsItems begin query' )
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG( 'Host listsItems ERROR' )
            return videoUrl
        printDBG( 'Host getResolvedURL data'+data )

        if url == 'http://tvtoya.pl/live':
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.search('data-stream="(.*?)"', data, re.S|re.I)
           if link: 
              videoUrl = link.group(1).replace("index","03")
              printDBG( 'Host link: '+videoUrl )
              return videoUrl

        if url.startswith('https://go.toya.net.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           videoUrl = self.cm.ph.getSearchGroups(data, '''data-stream=['"]([^"^']+?)['"]''', 1, True)[0]
           if videoUrl: 
              printDBG( 'Host link: '+videoUrl )
              return urlparser.decorateUrl(videoUrl, {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36'})

        if url.startswith('http://www.christusvincit-tv.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.findall('iframe src="(.*?)"', data, re.S)
           if link: 
              videoUrl = link[0]
              printDBG( 'Host link: '+videoUrl )
              query_data = {'url': videoUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
              try:
                  printDBG( 'Host listsItems begin query' )
                  data = self.cm.getURLRequestData(query_data)
              except:
                  printDBG( 'Host listsItems ERROR' )
                  return ''
              #printDBG( 'Host listsItems data2'+data )
              idparse = re.search('"avc1","status":2,"id":"(.*?)"', data, re.S|re.I)
              if idparse : 
                  id = idparse.group(1)
                  link = re.search('"items":(.*?),{"mediaType":1', data, re.S|re.I)
                  if link: 
                      baza = link.group(1)+']'
                      result = simplejson.loads(baza)
                      if result:
                          for item in result:
                             phUrl = str(item["downloadUrl"].replace('\/','/'))  
                             phTitle = str(item["name"]) 
                             phUrl = phUrl.replace('raw/entry_id','serveFlavor/entryId').replace('version/0','v/2/flavorId/')
                             phUrl = phUrl+id+'/fileName/'+phTitle+'.mp4/forceproxy/true/name/a.mp4'
                             printDBG( 'Host listsItems downloadUrl: '  +phUrl )
                             printDBG( 'Host listsItems name: '+phTitle ) 
                             printDBG( 'Host listsItems id: '+id ) 
                             return phUrl

        if url.startswith('http://christusvincit-tv.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.findall('iframe src="(.*?)"', data, re.S)
           if link: 
              videoUrl = link[0]
              printDBG( 'Host link: '+videoUrl )
              query_data = {'url': videoUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
              try:
                  printDBG( 'Host listsItems begin query' )
                  data = self.cm.getURLRequestData(query_data)
              except:
                  printDBG( 'Host listsItems ERROR' )
                  return ''
              #printDBG( 'Host listsItems data2'+data )
              idparse = re.search('"avc1","status":2,"id":"(.*?)"', data, re.S|re.I)
              if idparse : 
                  id = idparse.group(1)
                  link = re.search('"items":(.*?),{"mediaType":1', data, re.S|re.I)
                  if link: 
                      baza = link.group(1)+']'
                      result = simplejson.loads(baza)
                      if result:
                          for item in result:
                             phUrl = str(item["downloadUrl"].replace('\/','/'))  
                             phTitle = str(item["name"]) 
                             phUrl = phUrl.replace('raw/entry_id','serveFlavor/entryId').replace('version/0','v/2/flavorId/')
                             phUrl = phUrl+id+'/fileName/'+phTitle+'.mp4/forceproxy/true/name/a.mp4'
                             printDBG( 'Host listsItems downloadUrl: '  +phUrl )
                             printDBG( 'Host listsItems name: '+phTitle ) 
                             printDBG( 'Host listsItems id: '+id ) 
                             return phUrl

        if url.startswith('http://www.tvtzgorzelec.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           parse = re.search("sources:(.*?)image", data, re.S)
           if parse:
              link = re.findall('file: "(.*?)"', parse.group(1), re.S)
              if link:
                 for item in link: 
                    printDBG( 'Host listsItems tvt: '+item ) 
                    m3u8 = self.cm.ph.getSearchGroups(item, '(http.*?m3u8)')[0]
                    if m3u8: return m3u8 

        if url.startswith('http://www.tvkstella.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.search("netConnectionUrl: '(.*?)'", data, re.S|re.I)
           if link: 
              rtmp = link.group(1)
              swfUrl = 'http://www.tvkstella.pl/flowplayer-3.2.7.swf'
              playpatch ='StellaLive'
              videoUrl = '%s playpath=%s swfUrl=%s pageUrl=%s live=1' % (rtmp, playpatch, swfUrl, url)
              return videoUrl

        if url.startswith('http://www.pomorska.tv'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.search('file: "(.*?)"', data, re.S|re.I)
           if link: 
              videoUrl = 'http://www.pomorska.tv'+link.group(1)
              query_data = {'url': videoUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
              try:
                  data = self.cm.getURLRequestData(query_data)
              except:
                  return ''
              #printDBG( 'Host listsItems data2'+data )
              link = re.search('base="(.*?)"', data, re.S|re.I)
              if link:
                 return link.group(1)+' playpath=livestream_1 live=1 swfUrl=http://www.pomorska.tv/player/jwplayer.flash.swf pageUrl=http://www.pomorska.tv/livestream '

        if url.startswith('http://nspjkluczbork.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.search('data-rtmp="(.*?)"', data, re.S|re.I)
           link2 = re.search('source src="(.*?)"', data, re.S|re.I)
           if link: 
              return '%s playpath=%s swfUrl=http://nspjkluczbork.pl/wp-content/plugins/fv-wordpress-flowplayer/flowplayer/flowplayer.swf?ver=6.0.5.12 pageUrl=http://nspjkluczbork.pl/uncategorized/kamera/ live=1' % (link.group(1), link2.group(1))
           return ''

        if url.startswith('http://parafiagornybor.pl'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           link = re.search("rtmp'.*?(rtmp.*?)'", data, re.S|re.I)
           if link: 
              playpath = link.group(1).split('/')[-1]
              rtmp = link.group(1).replace('/'+playpath,'')
              return '%s playpath=%s swfUrl=http://kamera.parafiaskoczow.ox.pl/FlashPlayer/player-glow.swf pageUrl=http://www.parafiagornybor.ox.pl/index.php/kamera-online.html live=1' % (rtmp, playpath)
           return ''

        if url.startswith('http://www.tomaszow-sanktuarium.pl'):
           return 'rtmp://159.255.185.248:1936/streamHD/ playpath=kosciol_HD swfUrl=http://p.jwpcdn.com/6/12/jwplayer.flash.swf pageUrl=http://www.tomaszow-sanktuarium.pl/niedzielna-transmisja-wideo/ live=1'

        if url.startswith('http://www.trt.pl'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            youtube_link = self.cm.ph.getSearchGroups(data, '''(https://www.youtu[^"^']+?)[<'"]''', 1, True)[0]
            if youtube_link: return self.getResolvedURL(youtube_link)
            return self.cm.ph.getSearchGroups(data, '''<video\ssrc=['"]([^"^']+?)['"]''', 1, True)[0]

        if url.startswith('http://player.webcamera.pl'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            m3u8_link = self.cm.ph.getSearchGroups(data, '''<video id="video" src=['"]([^"^']+?)['"]''', 1, True)[0]
            if m3u8_link.startswith('//'): m3u8_link = 'http:' + m3u8_link
            return self.getResolvedURL(m3u8_link)

        if url.startswith('http://www.fokus.tv'):
            printDBG( 'Host getResolvedURL mainurl: '+url )
            link = self.cm.ph.getSearchGroups(data, '''<source src=['"]([^"^']+?mp4)['"]''', 1, True)[0]
            if not link:
                link = self.cm.ph.getSearchGroups(data, '''<source src=['"]([^"^']+?)['"]''', 1, True)[0].replace('&amp;','&')
                if self.cm.isValidUrl(link): 
                    tmp = getDirectM3U8Playlist(link)
                    for item in tmp:
                        return item['url']
            return link

        if url.startswith('https://www.youtube.com/embed'):
           printDBG( 'Host getResolvedURL mainurl: '+url )
           Url = self.cm.ph.getSearchGroups(data, '''['"](http://www.youtube.com/watch[^"^']+?)['"]''')[0] 
           return self.getResolvedURL(Url)

        printDBG( 'Host getResolvedURL end' )
        return videoUrl 

def decodeHtml(text):
	text = text.replace(chr(10), '')
	text = text.replace('&#x000A;', ' ')
	text = text.replace('  by', '')
	text = text.replace('-&gt;', 'and')
	text = text.replace('…  ...    …', '')
	text = text.replace('  ...  ', '')
	text = text.replace('&middot;', '')
	return text	
def decodeNat1(text):
	text = text.replace('\u015a', '_')
	text = text.replace('\u0119', '_')
	text = text.replace('\u015b', '_')
	text = text.replace('\u0142a', '_')
	return text	
def decodeNat2(text):
	text = text.replace('\u015a', 'Ś')
	text = text.replace('\u0119', 'ę')
	text = text.replace('\u015b', 'ś')
	text = text.replace('\u0142', 'ł')
	text = text.replace('\u00f3', 'ó')
	text = text.replace('\u017c', 'ż')
	text = text.replace('\u0107', 'ć')
	text = text.replace('\u0144', 'ń')
	return text	
