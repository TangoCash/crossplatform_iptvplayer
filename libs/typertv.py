# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


class TyperTV:
    MAINURL      = 'http://www.typertv.com.pl/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        self.catsCache = {}
        
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()

    def getCategoriesList(self):
        printDBG("TyperTV.getCategoriesList")
        self.catsCache = {}
        catsList = []
        
        sts,data = self.cm.getPage(TyperTV.MAINURL) 
        if not sts: return catsList
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="droppy" class="droppyOne">', '<script>', False)[1]
        data = data.split('</ul>')
        if len(data): del data[-1]
        
        for item in data:
            tmp = item.split('<ul>')
            if 2 != len(tmp):
                printDBG("TyperTV.getCategoriesList - parsing problem")
            else:
                category = self.cm.ph.getSearchGroups(tmp[0], 'href="http://www.typertv.com.pl/([^"]+?)"[^>]*?>([^<]+?)<', 2)
                channels = re.compile('href="(http://www.typertv.com.pl/[^"]+?)"[^>]*?>([^<]+?)<').findall(tmp[1])
                catsList.append({'url':category[0], 'title':category[1]})
                self.catsCache[category[0]] = channels
        return catsList

    def getChannelsList(self, baseUrl):
        printDBG("TyperTV.getChannelsList baseUrl[%s]" % baseUrl )
        channelsList = []

        data = self.catsCache.get(baseUrl, [])
        for item in data:
            icon  = ''
            channelsList.append({'title':item[1], 'url':item[0], 'icon':icon})
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("TyperTV.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="okno-ogladania-place', '</div>', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if '' != url:
            data = None
        return self.up.getAutoDetectedStreamLink(url, data)
