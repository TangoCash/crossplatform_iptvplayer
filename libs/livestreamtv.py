# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
try: import json
except Exception: import simplejson
############################################


class LiveStreamTvApi:
    def __init__(self):
        self.MAIN_URL = 'http://live-stream.tv/'
        self.cm = common()
        self.up = urlparser()

    def getChannelsList(self, cItem):
        printDBG("LiveStreamTvApi.getChannelsList cItem[%s]" % cItem )
        channelsList = []
        sts,data = self.cm.getPage(self.MAIN_URL)
        if not sts: return channelsList
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry">', '<footer id="footer">', False)[1]
        data = data.split('</a>')
        desc = ''
        for item in data:
            tmpDsc = self.cm.ph.getDataBeetwenMarkers(item, '<div class="fp_country">', '</div>', False)[1]
            if '' != tmpDsc: desc = tmpDsc
            title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if url.startswith('/'):
                url = self.MAIN_URL + url[1:]
            if url != '' and icon != '':
                channelsList.append({'name':'live-stream.tv', 'title':title, 'url':url, 'desc':desc, 'icon':icon})
        return channelsList
    
    def getVideoLink(self, cItem):
        printDBG("LiveStreamTvApi.getVideoLink cItem[%s]" % cItem)
        return self.up.getVideoLinkExt(cItem.get('url', ''))