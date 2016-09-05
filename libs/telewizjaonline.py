# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
try:    import simplejson as json
except: import json
from os import path as os_path
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.telewizjaonline_sort = ConfigSelection(default = "date", choices = [("date", "Date"), ("ostatnio-ogladane", "ostatnio ogl¹dane"), ("title", "Title"), ("view", "Views"), ("like", "Likes"), ("comment", "Comments")])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Sortuj kana³y wed³ug:", config.plugins.iptvplayer.telewizjaonline_sort))
    return optionList
###################################################


class TelewizjaOnline:
    MAINURL      = 'http://telewizja-online.pl/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()

    def getCategoriesList(self):
        printDBG("TelewizjaOnline.getCategoriesList")
        catsList = []
        sts,data = self.cm.getPage(TelewizjaOnline.MAINURL) 
        if not sts: return catsList
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Kategorie Stacji TV', '</ul>', False)[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            catsList.append({'url':item[0], 'title':item[1]})
        return catsList

    def getChannelsList(self, baseUrl):
        printDBG("TelewizjaOnline.getChannelsList baseUrl[%s]" % baseUrl )
        channelsList = []
        url = baseUrl + '?orderby=' + config.plugins.iptvplayer.telewizjaonline_sort.value
        sts,data = self.cm.getPage(url)
        if not sts: return channelsList
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-md-3', '<center>', False)[1]
        data = data.split('<div class="col-md-3')
        for item in data:
            title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon  = self.cm.ph.getSearchGroups(item, 'src="(http[^"]+?)"')[0]
            channelsList.append({'title':title, 'url':url, 'icon':icon})
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("TelewizjaOnline.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player-embed">', '<div class="player-button">', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if '' != url:
            data = None
        return self.up.getAutoDetectedStreamLink(url, data)
