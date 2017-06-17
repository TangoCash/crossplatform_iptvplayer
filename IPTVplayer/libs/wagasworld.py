# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
try: import json
except Exception: import simplejson as json
############################################


class WagasWorldApi:
    MAIN_URL      = 'http://www.wagasworld.com/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAIN_URL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url.replace('&amp;', '&')
        
    def getMainCategories(self, cItem):
        printDBG("WagasWorldApi.getMainCategories")
        list = []
        list.append({'type':'waga_cat', 'waga_cat':'groups', 'title':_('Channel'), 'url':self.MAIN_URL + 'channel'})
        list.append({'type':'waga_cat', 'waga_cat':'groups', 'title':_('LiveTv'),  'url':self.MAIN_URL + 'LiveTv' })
        return list
        
    def getGroups(self, cItem):
        printDBG("WagasWorldApi.getGroups")
        list = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return list
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="form-item">', '<select', True)[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(data)
        for item in data:
            list.append({'type':'waga_cat', 'waga_cat':'items', 'title':item[1], 'url':self._getFullUrl(item[0])})
        return list
        
    def getItems(self, cItem):
        printDBG("WagasWorldApi.getItems")
        list = []
        page = cItem.get('page', 0)
        url  = cItem['url']
        if page > 0:
            if '?' in url: url += '&'
            else: url += '?'
            url += 'page={0}'.format(page)
        sts, data = self.cm.getPage(url)
        if not sts: return list
        
        nextPage = False
        if '&amp;page={0}"'.format(page+1) in data:
            nextPage = True
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="view-content">', '</section>', True)[1]
        data = data.split('</span>')
        if len(data): del data[-1]
        for item in data:
            title = self.cm.ph.getSearchGroups(item, '>([^<]+?)</a>')[0]
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if '' != url and '' != title:
                list.append( {'type':'video', 'title':title, 'icon':icon, 'url':url} )
        if nextPage:
            list.append({'type':'waga_cat', 'waga_cat':'items', 'title':_('Next page'), 'url':cItem['url'], 'page':page+1})
        return list
        
    def getChannelsList(self, cItem):
        printDBG("WagasWorldApi.getChannelsList waga_cat[%s]" % cItem.get('waga_cat',  '') )
        list = []
        waga_cat = cItem.get('waga_cat',  '')
        if '' == waga_cat:
            list = self.getGroups({'url':self.MAIN_URL + 'channel'})
            #list = self.getMainCategories(cItem)
        elif 'groups' == waga_cat:
            list = self.getGroups(cItem)
        elif 'items' == waga_cat:
            list = self.getItems(cItem)
        return list

    
    def getVideoLink(self, baseUrl):
        printDBG("WagasWorldApi.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="videoWrapper">', ' </section>', False)[1]
        return self.up.getAutoDetectedStreamLink(baseUrl, data)