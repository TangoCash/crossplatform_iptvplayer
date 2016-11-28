# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
###################################################

def ParseM3u(data):
    printDBG('ParseM3u')
    list = []
    data = data.replace("\r","\n").replace('\n\n', '\n').split('\n')
    printDBG(">>>>>>>>>>>>> data0[%s]" % data[0])
    if '#EXTM3U' not in data[0]:
        return list
    
    params = {'title':'', 'length':'', 'uri':''}
    for line in data:
        line = line.strip()
        printDBG(line)
        if line.startswith('#EXTINF:'):
            try:
                length, title = line.split('#EXTINF:')[1].split(',', 1)
                params = {'title':title, 'length':length, 'uri':''}
            except Exception:
                printExc()
                params = {'title':'', 'length':'', 'uri':''}
        else:
            if '' != params['title']:
                line = line.replace('rtmp://$OPT:rtmp-raw=', '')
                cTitle = re.sub('\[[^\]]*?\]', '', params['title'])
                if len(cTitle): params['title'] = cTitle
                params['uri'] = urlparser.decorateParamsFromUrl(line)
                list.append(params)
            params = {'title':'', 'length':'', 'uri':''}
    return list