# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, RetHost, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
import random
import base64
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

def gettytul():
    return 'http://salvetv.pl/'

class SalvetvPL(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'telewizjarepublika.pl', 'cookie':'telewizjarepublika.pl.cookie', 'cookie_type':'MozillaCookieJar'})
        self.MAIN_URL = 'http://www.salvetv.pl/'
        self.DEFAULT_ICON_URL = self.getFullIconUrl('/content/medium/pieczatka.jpg')
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'with_metadata':True, 'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        return self.cm.getPage(url, addParams, post_data)
        
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [{'category':'list_items', 'title': 'Start',    'url':self.getMainUrl()           },
                        {'category':'categories', 'title': 'Programy', 'url':self.getFullUrl('/programy')},]
        self.listsTab(MAIN_CAT_TAB, cItem)
    
    def listItems(self, cItem, nextCategory):
        printDBG("SalvetvPL.listItems")

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        categories = []
        cache = {}
        
        data = data.split('"archive"', 1)[0]

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>', 'multimedia/'), ('</li', '>'))
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''\shref=['"]([^"^']+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue

            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
            if title == '': title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''\stitle=['"]([^"^']+?)['"]''')[0] )

            desc = []
            tmp = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'duration'), ('</div', '>'))[1])
            if tmp != '': desc.append(tmp)
            tmp = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'description'), ('</div', '>'))[1])
            if tmp != '': desc.append(tmp)

            tmp = self.cm.ph.getDataBeetwenMarkers(item, 'url(', ')', False)[1].strip()
            if len(tmp) > 2 and tmp[0] in ['"', "'"]: icon = self.getFullIconUrl(tmp[1:-1])
            else: icon = self.getFullIconUrl(tmp)

            category = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'category'), ('</div', '>'))[1])

            params = dict(cItem)
            params = {'good_for_fav': True, 'type':'video', 'title':title, 'url':url, 'icon':icon, 'desc':'[/br]'.join(desc)}
            if category not in categories:
                categories.append(category)
                cache[category] = []
            cache[category].append(params)

        if len(categories) == 1:
            self.currList = cache[categories[0]]
        else:
            for item in categories:
                params = dict(cItem)
                params = {'good_for_fav': False, 'category':nextCategory, 'title':item, 'sub_items':cache[item]}
                self.addDir(params)
        
    def listSubItems(self, cItem):
        printDBG("SalvetvPL.listSubItems")
        self.currList = cItem['sub_items']
        
    def listCategories(self, cItem, nextCategory):
        printDBG("SalvetvPL.listCategories")

        sts, data = self.getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getDataBeetwenNodes(data, ('<select', '>'), ('</select', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>')
        for item in data:
            url = self.getFullUrl('/programy/' + self.cm.ph.getSearchGroups(item, '''\svalue=['"]([^"^']+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url}
            self.addDir(params)
        
    def listPrograms(self, cItem, nextCategory):
        printDBG("SalvetvPL.listPrograms")

        sts, data = self.getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getDataBeetwenNodes(data, ('</select', '>'), ('<div', '>', 'gpg-black'))[1]
        data = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</div', '>'), ('<div', '>', 'embed'))
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''\shref=['"]([^"^']+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue

            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1] )
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1])

            tmp = self.cm.ph.getDataBeetwenMarkers(item, 'url(', ')', False)[1].strip()
            if len(tmp) > 2 and tmp[0] in ['"', "'"]: icon = self.getFullIconUrl(tmp[1:-1])
            else: icon = self.getFullIconUrl(tmp)

            params = dict(cItem)
            params = {'good_for_fav': True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("SalvetvPL.getLinksForVideo [%s]" % cItem)
        urlTab = []

        sts, data = self.getPage(cItem['url'])
        if not sts: return

        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<iframe', '>'), ('</div', '>'))
        for item in tmp:
            url  = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            name = '%s. %s' % (str(len(urlTab)+1), self.up.getHostName(url))
            urlTab.append({'name':name, 'url':url, 'need_resolve':1})

        return urlTab
    
    def getVideoLinks(self, videoUrl):
        printDBG("SalvetvPL.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if 1 == self.up.checkHostSupport(videoUrl): 
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: >> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_programs')
        elif category == 'list_programs':
            self.listPrograms(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'sub_items')
        elif category == 'sub_items':
            self.listSubItems(self.currItem)
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SalvetvPL(), True, [])
    