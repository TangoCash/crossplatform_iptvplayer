# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm, GetIPTVPlayerComitStamp
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.configbase import COLORS_DEFINITONS
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import time
import re
import urllib
import string
import random
import base64
from copy import deepcopy
from hashlib import md5
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.iptvplayerinfo_currversion_color = ConfigSelection(default = "#008000", choices = COLORS_DEFINITONS)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("The color of the current version"), config.plugins.iptvplayer.iptvplayerinfo_currversion_color))
    return optionList
###################################################

def gettytul():
    return 'IPTVPlayer Info'

class IPTVPlayerInfo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'iptvplayer.pl', 'cookie':'iptvplayer.pl.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://bectechnologies.net/wordpress/wp-content/uploads/2015/10/iptv_icon.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding':'gzip, deflate'} )
        self.defaultParams = {'header':self.AJAX_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_URL = 'https://gitlab.com/'
        self.MAIN_CAT_TAB = [
                             {'category':'commits',        'title': _('Commits'),       },
                             {'category':'tutorial',       'title': _('Tutorials'),     } 
                            ]
                            
        self.TUTORIALS_TAB = [
                             {'title': _('http://rte.ie/player serivce overview'),              'url':'https://www.youtube.com/watch?v=IhC8m8K1jkg'},
                             {'title': _('[en] External subtitles download - how to'),          'url':'https://www.youtube.com/watch?v=ZO6w6Pr5z_4'},
                             {'title': _('[pl] External subtitles download - how to'),          'url':'https://www.youtube.com/watch?v=3onH5vxlDcg'},
                             {'title': _('http://prijevodi-online.org/ subtitles provider'),    'url':'https://www.youtube.com/watch?v=lb8QvViUYq4'},
                            ]
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)
    
    def listCommits(self, cItem, nextCategory):
        printDBG("listCommits [%s]" % cItem)
        
        ITEMS_PER_PAGE = 40
        
        page = cItem.get('page', 0)
        url  = self.getFullUrl('/iptvplayer-for-e2/iptvplayer-for-e2/commits/master?limit=%d&offset=%d' % (ITEMS_PER_PAGE, page * ITEMS_PER_PAGE))
        
        if page > 1:
            if '?' in url: url += '&'
            else: url += '?'
            url += 'page=%s' % page
        
        sts, data = self.getPage(url)
        if not sts: return
        
        try:
            nextPage = False
            currCommitStamp = GetIPTVPlayerComitStamp()
            
            printDBG(">>>> currCommitStamp[%s]" % currCommitStamp)
            
            data = byteify(json.loads(data))
            if data['count'] >= ITEMS_PER_PAGE: nextPage = True
            
            splitReObj = re.compile('''<span[^>]+?class=['"]commit-row-message[^>]+?>''')
            
            data = self.cm.ph.rgetAllItemsBeetwenNodes(data['html'], ('</li', '>'), ('<li', '>', 'commit-header'))
            for item in data:
                item = item.split('</li>', 1)
                title = self.cm.ph.getSearchGroups(item[0], '''data-day=['"]([^'^"]+?)['"]''')[0].replace('-', '.')
                desc  = self.cleanHtmlStr(item[0]) 
                self.addMarker({'title':title, 'desc':desc})
                
                item = self.cm.ph.getAllItemsBeetwenMarkers(item[1], '<li', '</li>')
                for it in item:
                    stamp = self.cm.ph.getSearchGroups(it, '''data-clipboard-text=['"]([^'^"]+?)['"]''')[0]
                    it = self.cm.ph.getAllItemsBeetwenMarkers(it, '<div', '</div>')
                    icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(it[0], '''data-src=['"]([^'^"]+?)['"]''')[0].replace('&amp;', '&'))
                    url   = self.getFullUrl(self.cm.ph.getSearchGroups(it[1], '''href=['"]([^'^"]+?)['"]''')[0])
                    it    = splitReObj.split(it[1])
                    title = self.cleanHtmlStr(it[0])
                    desc  = self.cleanHtmlStr(it[1])
                    
                    params = {'title':title, 'url':url, 'desc':desc, 'icon':icon}
                    if currCommitStamp != '' and currCommitStamp == stamp:
                        params['text_color'] = config.plugins.iptvplayer.iptvplayerinfo_currversion_color.value
                    self.addArticle(params)
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("getLinksForVideo [%s]" % cItem)
        return self.up.getVideoLinkExt(cItem['url'])
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'commits':
            self.listCommits(self.currItem, 'list_items')
        elif category == 'tutorial':
            self.listsTab(self.TUTORIALS_TAB, self.currItem, 'video')
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, IPTVPlayerInfo(), True, [])
    