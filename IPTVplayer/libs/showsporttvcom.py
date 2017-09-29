# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, GetPyScriptCmd
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
import base64
import datetime
try:    import json
except Exception: import simplejson as json

############################################

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

class ShowsportTVApi(CBaseHostClass):
    
    def __init__(self):
        self.MAIN_URL   = 'http://showsport-tv.com/'
        self.HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': self.MAIN_URL }
        self.COOKIE_FILE = GetCookieDir('showsporttvcom.cookie')
        self.sessionEx = MainSessionWrapper()
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        
    def _getChannelsList(self, cItem):
        printDBG("ShowsportTVApi._getChannelsList")
        channelsTab = []
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="magenta"', '</a>')
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''', 1, True)[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src="([^"]+?)"''', 1, True)[0] )
            title = self.cm.ph.getDataBeetwenMarkers(url, 'watch-', '-online.html', False)[1].replace('-', ' ').title()
            if 'Offline' in item:
                desc  = _('Off Air')
            else:
                desc  = _('On Air')
            if title == '': continue
            if not url.startswith('http'): continue
            params = dict(cItem)
            params.update({'type':'video', 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            channelsTab.append(params)
        return channelsTab
        
    def _getScheduleList(self, cItem):
        printDBG("ShowsportTVApi._getScheduleList")
        channelsTab = []
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="listmatch">', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li ', '</li>')
        for item in data:
            titleTab = []
            item = item.replace('<div class="versus column">', ' vs ')
            if '/images/live.gif' in item:
                titleTab.append(_('[LIVE]'))
            timestamp = self.cm.ph.getSearchGroups(item, '''class="starttime time"[^>]+?rel="([0-9]+?)"''', 1, True)[0]
            if timestamp == '': timestamp = self.cm.ph.getSearchGroups(item, '''class="startdate date"[^>]+?rel="([0-9]+?)"''', 1, True)[0]
            if timestamp != '':
                titleTab.append('[%s]' % datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S') )
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''', 1, True)[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src="([^"]+?)"''', 1, True)[0] )
            titleTab.append( self.cleanHtmlStr( item ) )
            desc  = ''
            if not url.startswith('http'): continue
            params = dict(cItem)
            params.update({'type':'video', 'title':' '.join(titleTab), 'url':url, 'icon':icon, 'desc':desc})
            channelsTab.append(params)
        return channelsTab
        
    def getChannelsList(self, cItem):
        printDBG("ShowsportTVApi.getChannelsList")
        return self._getChannelsList(cItem)
        
        channelsTab = []
        
        category = cItem.get('abc_cat', None)
        if category == None:
            for item in [{'title':_('Schedule'), 'abc_cat':'schedule'}, {'title':_('Channels'), 'abc_cat':'channels'}]:
                params = dict(cItem)
                params.update(item)
                channelsTab.append(params)
        elif category == 'channels':
            channelsTab = self._getChannelsList(cItem)
        elif category == 'schedule':
            channelsTab = self._getScheduleList(cItem)

        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("ShowsportTVApi.getVideoLink")
        urlsTab = []
        params    = {'header' : self.HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        sts, data = self.cm.getPage(cItem['url'], params)
        if not sts: return []
        #data = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^'^"]*?/embedplayer\.php[^'^"]+?)['"]''', 1, True)[0]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, 'setURL(', '<')
        checkedLinksTab = []
        for item in tmp:
            serverName = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '>', '<', False)[1] )
            playerUrl  = self.cm.ph.getSearchGroups(item, '''['"]([^'^"]*?/embedplayer\.php[^'^"]+?)['"]''', 1, True)[0]
            playerUrl = self.getFullUrl(playerUrl)
            if self.cm.isValidUrl(playerUrl) and playerUrl not in checkedLinksTab:
                checkedLinksTab.append(playerUrl)
                sts,item = self.cm.getPage(playerUrl)
                if not sts: continue
                links = self.up.getAutoDetectedStreamLink(playerUrl, item)
                for link in links:
                    link['name'] = '%s %s' % (serverName, link['name'])
                    urlsTab.append( link )
        return urlsTab
