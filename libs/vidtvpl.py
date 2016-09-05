# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import string
############################################


class VidTvApi:
    MAINURL      = 'http://vidtv.pl/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
    
    def getChannelsList(self, url):
        channelList = []
        sts, data = self.cm.getPage(VidTvApi.MAINURL + 'index.php')
        if not sts: return channelList
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="sixths_team">', '</div>', False)
        
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title = self.cm.ph.getDataBeetwenMarkers(icon, '/', '.png', False)[1].replace('img/', '').title()
            if not url.startswith('http'):
                channelList.append({'title':title, 'url':VidTvApi.MAINURL[:-1] + url, 'icon': VidTvApi.MAINURL + icon})
        return channelList
        
    def unpackJS(self, data, name):
        try:
            paramsAlgoObj = compile(data, '', 'exec')
        except:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''
        vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote}
        vLocals = { name: None }

        try:
            exec( data, vGlobals, vLocals )
        except:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except:
            printExc('decryptPlayerParams EXCEPTION')
        return ''
        
    def _clearData(self, data):
        # get all vars
        pyCode = ''
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, 'var ', ';', False)
        for item in tmp:
            pyCode = item.strip() + '\n'
            
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(pyCode)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        def evalSimple(data):
            code = pyCode
            code += 'retVal = unescape(%s)' % data.group(1)
            dat = self.unpackJS(code, 'retVal')
            if 'unescape' in dat:
                return self._clearData(dat)
            return dat
        return re.sub('''document\.write\([ ]*?unescape\(([^)]+?)\)''', evalSimple, data)
    
    def getVideoLink(self, baseUrl):
        printDBG("NettvPw.getVideoLink url[%s]" % baseUrl)
        urlsTab = []
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return urlsTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Oglądasz', 'Lista ', False)[1]
        data = self._clearData(data)
       
        printDBG(data)
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'value="src=', '"', False)[1]
        if 'plugin_hls=http' in tmp:
            urlsTab = getDirectM3U8Playlist(tmp.split('&amp;')[0], checkExt=False)
        
        if '.setup(' in tmp:
            tmp = self.cm.ph.getSearchGroups(data, "file[^']*?:[^']*?'([^']+?'")[0]
            if '.m3u8' in tmp:
                urlsTab.extend(getDirectM3U8Playlist(tmp, checkExt=False))
                
        if 'play.php?f=http' in data:
            tmp = self.cm.ph.getSearchGroups(data, '''play\.php\?f=(http[^'^"]+?)["']''')[0]
            if '.m3u8' in tmp:
                urlsTab.extend(getDirectM3U8Playlist(tmp.split('&amp;')[0], checkExt=False))
                
        if 'type=rtmp' in data:
            video = self.cm.ph.getDataBeetwenMarkers(data, 'video=', '&#038;', False)[1]
            streamer = self.cm.ph.getDataBeetwenMarkers(data, 'streamer=', '&#038;', False)[1]
            urlsTab.append({'name':'rtmp', 'url':streamer + video})
        
        if 0 == len(urlsTab):
            tmp = self.up.getAutoDetectedStreamLink(baseUrl, data)
            urlsTab.extend(tmp)
            
        if 0 == len(urlsTab):
            tmp = self.cm.ph.getSearchGroups(data, 'SRC="([^"]+?)"', 1, True)[0]
            tmp = self.up.getAutoDetectedStreamLink(tmp)
            urlsTab.extend(tmp)
            
        if 0 == len(urlsTab):
            if 'Microsoft Silverlight' in data or 'x-silverlight' in data:
                SetIPTVPlayerLastHostError('Silverlight stream not supported.')

        return urlsTab
