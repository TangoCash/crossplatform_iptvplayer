# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import re
try:    import json
except: import simplejson as json

IPTV_DEBUG=False
def printDBG(strDat):
    if IPTV_DEBUG:
        print("%s" % strDat)

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def getPage(url, params={}):
    printDBG('url [%s]' % url)
    sts = False
    try:
        resp = urllib2.urlopen(url)
        data = resp.read()
        sts = True
    except:
        printExc()
    return sts, data

def getDataBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
    if caseSensitive:
        idx1 = data.find(marker1)
    else:
        idx1 = data.lower().find(marker1.lower())
    if -1 == idx1: return False, ''
    if caseSensitive:
        idx2 = data.find(marker2, idx1 + len(marker1))
    else:
        idx2 = data.lower().find(marker2.lower(), idx1 + len(marker1))
    if -1 == idx2: return False, ''
    
    if withMarkers:
        idx2 = idx2 + len(marker2)
    else:
        idx1 = idx1 + len(marker1)
    return True, data[idx1:idx2]
    
def getAllItemsBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
    itemsTab = []
    if caseSensitive:
        sData = data
    else:
        sData = data.lower()
        marker1 = marker1.lower()
        marker2 = marker2.lower()
    idx1 = 0
    while True:
        idx1 = sData.find(marker1, idx1)
        if -1 == idx1: return itemsTab
        idx2 = sData.find(marker2, idx1 + len(marker1))
        if -1 == idx2: return itemsTab
        tmpIdx2 = idx2 + len(marker2) 
        if withMarkers:
            idx2 = tmpIdx2
        else:
            idx1 = idx1 + len(marker1)
        itemsTab.append(data[idx1:idx2])
        idx1 = tmpIdx2
    return itemsTab

def getSearchGroups(data, pattern, grupsNum=1, ignoreCase=False):
    tab = []
    if ignoreCase:
        match = re.search(pattern, data, re.IGNORECASE)
    else:
        match = re.search(pattern, data)
    
    for idx in range(grupsNum):
        try:    value = match.group(idx + 1)
        except: value = ''
        tab.append(value)
    return tab
    
def removeDoubles(data, pattern):
    while -1 < data.find(pattern+pattern) and '' != pattern:
        data = data.replace(pattern+pattern, pattern)
    return data 

def replaceHtmlTags(s, replacement=''):
    tag = False
    quote = False
    out = ""
    for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
                out += replacement
            elif (c == '"' or c == "'") and tag:
                quote = not quote
            elif not tag:
                out = out + c
    return re.sub('&\w+;', ' ',out)
    
def getEpisodes(imdbid, promSeason, promEpisode):
    printDBG('getEpisodes imdbid[%s]' % imdbid)
    promSeason = int(promSeason)
    promEpisode = int(promEpisode)
    # get all seasons
    sts, data = getPage("http://www.imdb.com/title/tt%s/episodes" % imdbid)
    if not sts: return False, ''
    data = getDataBeetwenMarkers(data, '<select id="bySeason"', '</select>', False)[1]
    seasons = re.compile('value="([0-9]+?)"').findall(data)
    
    list = []
    promotItem = {}
    # get episoded for all seasons
    for season in seasons:
        season = int(season)
        sts, data = getPage("http://www.imdb.com/title/tt%s/episodes/_ajax?season=%s" % (imdbid, season))
        if not sts: break
        data = getDataBeetwenMarkers(data, '<div class="list detail eplist">', '<hr>', False)[1]
        data = data.split('<div class="clear">')
        if len(data): del data[-1]
        for item in data:
            episodeTitle = getSearchGroups(item, 'title="([^"]+?)"')[0]
            eimdbid = getSearchGroups(item, 'data-const="tt([0-9]+?)"')[0]
            episode = int(getSearchGroups(item, 'content="([0-9]+?)"')[0])
            params = {"season": season, "episode_title":episodeTitle, "episode":episode, "id":imdbid, "eimdbid":eimdbid}
            #params = {"s": season, "et":episodeTitle, "e":episode, "i":eimdbid}
            title = 's{0}e{1} {2}'.format(str(season).zfill(2), str(episode).zfill(2), episodeTitle)
            if season == promSeason and episode == promEpisode and promotItem == {}:
                promotItem = {'title':title, 'private_data':params}
                #promotItem = {'t':title, 'p':params}
            else:
                list.append({'title':title, 'private_data':params})
                #list.append({'t':title, 'p':params})
    if promotItem != {}:
        list.insert(0, promotItem)
    data = {'list':list}
    data = json.dumps(data)
    return True, data
    
def findByTitle(title):
    sts, data = getPage("http://www.imdb.com/find?ref_=nv_sr_fn&q=%s&s=tt" % urllib.quote_plus(title))
    if not sts: return False, ''
    list = []
    
    data = getDataBeetwenMarkers(data, '<table class="findList">', '</table>', False)[1]
    data = data.split('</tr>')
    if len(data): del data[-1]
    for item in data:
        item = item.split('<a ')
        item = '<a ' + item[2]
        if '(Video Game)' in item: continue
        imdbid = getSearchGroups(item, '/tt([0-9]+?)/')[0]
        title = title.split('<br/>')[0]
        title = removeDoubles(replaceHtmlTags(item, ' '), ' ').strip()
        list.append({'title':title, 'imdbid':imdbid})
    data = {'list':list}
    data = json.dumps(data)
    return True, data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python pwget url file', file=sys.stderr)
        sys.exit(1)
    data = ''
    code = -1
    try:
        sts = False
        handler = sys.argv[1]
        if '_dbg' in handler:
            IPTV_DEBUG = True
        if 'episodes' in handler:
            sts, data = getEpisodes(sys.argv[2], sys.argv[3], sys.argv[4])
        elif 'find_title' in handler:
            sts, data = findByTitle(sys.argv[2])
        if sts: code = 0
    except:
        printExc()
    
    print(data, file=sys.stderr)
    sys.exit(code)
        

    
