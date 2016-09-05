# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetLogoDir, byteify, CSelOneLink
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################
# FOREIGN import
###################################################
import re, urllib, urllib2, base64, math 
try:    import json
except Exception: import simplejson as json
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigYesNo
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.vimeo_default_quality = ConfigSelection(default = "360", choices = [
("0", _("the worst")),
("270",  "270p"), 
("360",  "360p"), 
("720",  "720p"), 
("1080",  "1080p"), 
("99999999", _("the best"))
])
config.plugins.iptvplayer.vimeo_use_default_quality = ConfigYesNo(default = False)
#config.plugins.iptvplayer.vimeo_allow_hls           = ConfigYesNo(default = True)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Default video quality:"), config.plugins.iptvplayer.vimeo_default_quality))
    optionList.append(getConfigListEntry(_("Use default video quality:"), config.plugins.iptvplayer.vimeo_use_default_quality))
    #optionList.append(getConfigListEntry(_("Allow hls format"), config.plugins.iptvplayer.vimeo_allow_hls))
    return optionList
###################################################

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'Dancetrippin'

class IPTVHost(IHost):
    LOGO_NAME = 'dancetrippinlogo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        printDBG( "init end" )
        
    def isProtectedByPinCode(self):
        return False
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir(self.LOGO_NAME)])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.host.setCurrList(self.currList)
        self.prevList = []
        printDBG( "getInitList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( "getListForItem begin" )
        self.prevIndex.append(Index)
        self.prevList.append(self.currList)
        self.currList = self.host.getListForItem(Index, refresh, selItem)
        #self.currList = [ self.prevList[-1][Index] ]
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
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getResolvedURL(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))
        return RetHost(RetHost.OK, value = retlist)

    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    ###################################################
    # Additional functions on class IPTVHost
    ###################################################

class Host:
    currList = []
    MAIN_URL = ''
    
    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.cm = pCommon.common()
        self.currList = []
        printDBG( 'Host __init__ end' )
        
    def getStr(self, v, default=''):
        if None == v:
            return default
        elif isinstance(v, int):
            return str(v)
        return str(v)
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList end' )
        return 

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        #self.currList = self.MAIN_MENU
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

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        printDBG( 'Host listsItems url[%r] '% url )
        valTab = []
        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           valTab.append(CDisplayListItem('Episodes',     'http://player.dancetrippin.tv/#dj',    CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/dj/'],    'episodes', '', None)) 
           valTab.append(CDisplayListItem('Sol sessions', 'http://player.dancetrippin.tv/#sol',   CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/sol/'],   'episodes', '', None)) 
           valTab.append(CDisplayListItem('Other videos', 'http://player.dancetrippin.tv/#other', CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/other/'], 'episodes', '', None)) 
           valTab.append(CDisplayListItem('Ibiza Global Radio', 'http://player.dancetrippin.tv/#igr', CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/igr/'], 'episodes', '', None))
           return valTab

        # ########## #
        if 'episodes' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://player.dancetrippin.tv' 
           try:
                data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
                result = byteify(json.loads(data))
           except Exception:
              printExc( 'Host listsItems query error url[%r]' % url )
              return valTab
           if result:
              for item in result:
                  if self.getStr(item["image"]) <> "":
                     phImage = 'http://www.dancetrippin.tv/media/'+self.getStr(item["image"])
                  else:
                     phImage = "http://player.dancetrippin.tv/media/static/img/system/default_video.png"
                  phUrl = self.MAIN_URL+'/video/'+self.getStr(item["slug"])+'/'   
                  desc = '['+self.getStr(item["venue"])+']['+self.getStr(item["dj"])+']['+self.getStr(item["location"])+']['+self.getStr(item["party"])+']['+self.getStr(item["description"])
                  desc = clean_html(desc)
                  valTab.append(CDisplayListItem(self.getStr(item["number"])+' '+self.getStr(item["title"]),desc,CDisplayListItem.TYPE_VIDEO, [CUrlItem('link', phUrl, 1)], 0, phImage, None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        return valTab

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL url[%r] ' % url )
        videoUrls = []
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"', 1, True)[0]
        
        sts, data = self.cm.getPage(videoUrl)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'var t={', '};', False)[1]
        printDBG(data)
        
        try:
            data = byteify( json.loads('{%s}' % data) )
            for item in data['request']['files']['progressive']:
                videoUrls.append({'name':item['quality'], 'url':item['url'], 'height':item['height']})
        except Exception:
            printExc()
            
        if 0 < len(videoUrls):
            max_bitrate = int(config.plugins.iptvplayer.vimeo_default_quality.value)
            def __getLinkQuality( itemLink ):
                return int(itemLink['height'])
            videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.vimeo_use_default_quality.value:
                videoUrls = [videoUrls[0]]
            
        return videoUrls