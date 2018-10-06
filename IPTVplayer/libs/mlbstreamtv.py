# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify, MergeDicts, GetPyScriptCmd
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CBaseHostClass
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, getConfigListEntry, ConfigInteger
import re
import urllib
import base64
from datetime import datetime, timedelta
############################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.mlbstreamtv_port = ConfigInteger(8193, (1024,65535))

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('PORT') + ": ", config.plugins.iptvplayer.mlbstreamtv_port))
    return optionList
    
###################################################

class MLBStreamTVApi(CBaseHostClass):
    def __init__(self):
        CBaseHostClass.__init__(self, {'cookie':'mlbstream.tv.cookie'})
        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        self.AJAX_HEADER = MergeDicts(self.HTTP_HEADER, {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HTTP_HEADER, 'ignore_http_code_ranges':[], 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_URL = 'http://mlbstream.tv/'
        self.DEFAULT_ICON_URL = self.getFullUrl('/wp-content/uploads/2018/03/mlb-network-291x300.png')
        
        OFFSET = datetime.now() - datetime.utcnow()
        seconds = OFFSET.seconds + OFFSET.days * 24 * 3600
        if ((seconds + 1) % 10) == 0: seconds += 1
        elif ((seconds - 1) % 10) == 0: seconds -= 1
        if seconds > 0: GMTOffset = '+' + str(timedelta(seconds=seconds))
        elif seconds < 0: GMTOffset = '-' + str(timedelta(seconds=seconds*-1))
        else: GMTOffset = ''

        while GMTOffset.endswith(':00'):
            GMTOffset = GMTOffset.rsplit(':', 1)[0]
        self.GMTOffset = GMTOffset
        self.offset = timedelta(seconds=seconds)
        
        self.gameSchedule = {}
        
    def _str2date(self, txt):
        txt = self.cm.ph.getSearchGroups(txt, '([0-9]+\-[0-9]+\-[0-9]+T[0-9]+\:[0-9]+:[0-9]+)')[0]
        return datetime.strptime(txt, '%Y-%m-%dT%H:%M:%S') + self.offset
    
    def getList(self, cItem):
        printDBG("MLBStreamTVApi.getList cItem[%s]" % cItem )
        channelsList = []
        
        category = cItem.get('priv_cat')
        if category == None:
            if not self.gameSchedule:
                try:
                    sts, data = self.cm.getPage('https://statsapi.mlb.com/api/v1/schedule?sportId=1')
                    data = json_loads(data)
                    for item in data['dates']:
                        for gameItem in item['games']:
                            key = (gameItem['teams']['home']['team']['name'].replace(' ', ''), gameItem['teams']['away']['team']['name'].replace(' ', ''))
                            self.gameSchedule[key] = self._str2date(gameItem['gameDate'])
                except Exception:
                    printExc()
        
            sts, data = self.cm.getPage(self.getMainUrl(), self.defaultParams)
            if not sts: return []
            self.setMainUrl(self.cm.meta['url'])
            
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'menu-menu'), ('</ul', '>'), False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
            if len(tmp):
                url = self.getFullUrl( self.cm.ph.getSearchGroups(tmp[-1], '''href=['"]([^'^"]+?)['"]''')[0] )
                title = self.cleanHtmlStr(tmp[-1])
                sts, tmp = self.cm.getPage(url, self.defaultParams)
                if sts and '<iframe' in tmp:
                    title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<title', '</title>')[1])
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
                    channelsList.append({'name':'mlbstream.tv', 'type':'video', 'url':url, 'title':title, 'Referer':self.cm.meta['url'], 'icon':self.DEFAULT_ICON_URL})
            
            sDesc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'entry-content'), ('</', '>'), False)[1] )
            data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s+?timezoneJSON\s*?=\s*?\['), re.compile('\];'), False)[1]
            try:
                data = json_loads('[%s]' % data)
                for sData in data:
                    subItems = []
                    sTitle = ''
                    sData = self.cm.ph.getAllItemsBeetwenMarkers(sData, '<tr', '</tr>')
                    for item in sData:
                        if 'colspan' in item:
                            if len(subItems):
                                channelsList.append({'name':'mlbstream.tv', 'type':'dir', 'priv_cat':'sub_items', 'title':sTitle, 'sub_items':subItems, 'desc':sDesc, 'icon':self.DEFAULT_ICON_URL})
                            subItems = []
                            sTitle = self.cleanHtmlStr(item)
                            continue
                        
                        date = self.cm.ph.getSearchGroups(item, '''data\-token=['"]([^'^"]+?)['"]''')[0]
                        date = datetime.fromtimestamp(int(date))
                        
                        home = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'team-name'), ('</span', '>'), False)[1]).decode('utf-8').replace(' ', '')
                        away = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'away-name'), ('</span', '>'), False)[1]).decode('utf-8').replace(' ', '')
                        if (home, away) in self.gameSchedule:
                            key = (home, away)
                        elif (away, home) in self.gameSchedule:
                            key = (away, home)
                        else:
                            key = None
                        url = self.cm.ph.getSearchGroups(item, '''\sdata\-link=['"]([^'^"]+?)['"]''')[0]
                        
                        item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>')
                        title = self.cleanHtmlStr(''.join(item[3:]))
                        icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item[3], '''<img[^>]+?src=['"]([^'^"]+?)['"]''')[0])
                        desc = self.cleanHtmlStr(item[2])
                        if key != None: desc += '[/br]www.mlb.com: ' + self.gameSchedule[key].strftime('%A, %-d %B %H:%M')
                        desc += '[/br]mlbstream.tv: ' + date.strftime('%A, %-d %B %H:%M')
                        
                        subItems.append({'name':'mlbstream.tv', 'type':'dir', 'priv_cat':'links', 'title':title, 'url':self.getFullUrl(url), 'desc':desc, 'icon':icon})
                    if len(subItems):
                        channelsList.append({'name':'mlbstream.tv', 'type':'dir', 'priv_cat':'sub_items', 'title':sTitle, 'sub_items':subItems, 'desc':sDesc, 'icon':self.DEFAULT_ICON_URL})
            except Exception:
                printExc()
        elif category == 'sub_items':
            channelsList = cItem['sub_items']
        else:
            urlParams = dict(self.defaultParams)
            urlParams['header'] = dict(urlParams['header'])
            urlParams['header']['Referer'] = self.getMainUrl()
            sts, data = self.cm.getPage(cItem['url'], urlParams)
            if not sts: return []
            
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'custom-related-links'), ('</div', '>'))[1]
            tmp = self.cm.ph.getAllItemsBeetwenNodes(tmp, ('<a', '>'), ('</a', '>'))
            for item in tmp:
                url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
                title = '%s - %s' % (cItem['title'], self.cleanHtmlStr(item))
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'Referer':self.cm.meta['url'], 'get_iframe':True})
                channelsList.append(params)
            
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            params = dict(cItem)
            params.update({'type':'video', 'url':url, 'Referer':self.cm.meta['url']})
            channelsList.insert(0, params)

        return channelsList
    
    def getVideoLink(self, cItem):
        printDBG("MLBStreamTVApi.getVideoLink")
        urlsTab = []
        
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(urlParams['header'])
        urlParams['header']['Referer'] = cItem.get('Referer', self.getMainUrl())
        
        sts, data = self.cm.getPage(cItem['url'], urlParams)
        if not sts: return []
        
        if cItem.get('get_iframe', False):
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
            if url != '':
                urlParams['header']['Referer'] = self.cm.meta['url']
                sts, data = self.cm.getPage(url, urlParams)
                if not sts: return urlsTab
        
        cUrl = self.cm.meta['url']
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'unescape(', ')', False)[1].strip()
        data = urllib.unquote(data[1:-1]) + data
        
        printDBG("+++")
        printDBG(data)
        printDBG("+++")
        
        source  = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?source['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        replace = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?replace['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        keyurl  = self.cm.ph.getSearchGroups(data, '''[\s\{\,]['"]?keyurl['"]?\s*:\s*['"](https?://[^'^"]+?)['"]''', 1, True)[0]
        rewrittenUrl = self.cm.ph.getSearchGroups(data, '''\=\s*?['"]([^'^"]+?)['"]\s*?\+\s*?btoa''', 1, True)[0]
        
        replaceTab = self.cm.ph.getDataBeetwenMarkers(data, 'prototype.open', '};', False)[1]
        printDBG(replaceTab)
        replaceTab = re.compile('''\.replace\(['"](\s*[^'^"]+?)['"]\s*\,\s*['"]([^'^"]+?)['"]''').findall(replaceTab)
        printDBG(replaceTab)
        scriptUrl = ''
        hlsTab = getDirectM3U8Playlist(source, checkContent=True, sortWithMaxBitrate=9000000)
        if keyurl == '' and 1 == len(replaceTab):
            replace = replaceTab[0][0]
            keyurl = replaceTab[0][1]
        
        if replace != '' and keyurl != '':
            for idx in range(len(hlsTab)):
                hlsTab[idx]['url'] = strwithmeta(hlsTab[idx]['url'], {'iptv_m3u8_key_uri_replace_old':replace, 'iptv_m3u8_key_uri_replace_new':keyurl})
        elif len(replaceTab):
            scriptUrl = '|' + base64.b64encode(json_loads(replaceTab))
        elif rewrittenUrl != '':
            scriptUrl = '<proxy>' + rewrittenUrl
        elif '/js/nhl.js' in data:
            scriptUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^"^']*?js/nhl\.js)['"]''', 1, True)[0])
        
        if scriptUrl != '':
            for idx in range(len(hlsTab)):
                hlsTab[idx]['need_resolve'] = 1
                hlsTab[idx]['url'] = strwithmeta(hlsTab[idx]['url'], {'name':cItem['name'], 'Referer':cUrl, 'priv_script_url':scriptUrl})
        
        urlsTab = hlsTab
        
        return urlsTab

    def getResolvedVideoLink(self, videoUrl):
        printDBG("MLBStreamTVApi.getResolvedVideoLink [%s]" % videoUrl)
        urlsTab = []
        
        
        baseUrl = self.cm.getBaseUrl(videoUrl.meta.get('Referer', ''))
        scriptUrl = videoUrl.meta.get('priv_script_url', '')
        
        sts, data = self.cm.getPage(videoUrl)
        if not sts or '#EXTM3U' not in data: return urlsTab
        
        meta = {}
        keyUrl = set(re.compile('''#EXT\-X\-KEY.*?URI=['"](https?://[^"]+?)['"]''').findall(data))
        if len(keyUrl):
            keyUrl = keyUrl.pop()
            proto = keyUrl.split('://', 1)[0]
            pyCmd = GetPyScriptCmd('livesports') + ' "%s" "%s" "%s" "%s" "%s" ' % (config.plugins.iptvplayer.mlbstreamtv_port.value, videoUrl, baseUrl, scriptUrl, self.HTTP_HEADER['User-Agent'])
            meta = {'iptv_proto':'em3u8'}
            meta['iptv_m3u8_key_uri_replace_old'] = '%s://' % proto 
            meta['iptv_m3u8_key_uri_replace_new'] = 'http://127.0.0.1:{0}/{1}/'.format(config.plugins.iptvplayer.mlbstreamtv_port.value, proto)
            meta['iptv_refresh_cmd'] = pyCmd
        
        videoUrl = self.up.decorateUrl("ext://url/" + videoUrl, meta)
        
        return [{'name':'direct', 'url':videoUrl}]