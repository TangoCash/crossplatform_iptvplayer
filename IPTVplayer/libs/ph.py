﻿# -*- coding: utf-8 -*-

import re

START_E=1
START_S=2
END_E=4
END_S=8
IGNORECASE=16

# pre-compiled regular expressions
IMAGE_SRC_URI_RE = re.compile(r'''<img[^>]+?src=(['"])([^\1]+?\.(?:jpe?g|png)(?:\?[^\1]*?)?)(?:\1)''', re.I)
A_HREF_URI_RE = re.compile(r'''<a[^>]+?href=(['"])([^\1]+?)(?:\1)''', re.I)

def getattr(data, attrmame, flags=0):
    if flags & IGNORECASE:
        sData = data.lower() 
        m = '%s=' % attrmame.lower() 
    else:
        sData = data
        m = '%s=' % attrmame
    sidx = 0
    while True:
        sidx = sData.find(m, sidx)
        if sidx == -1:
            return ''
        if data[sidx - 1] in ('\t', ' ', '\n', '\r'):
            break
        sidx += len(m)
    sidx += len(m)
    z = data[sidx]
    if z not in ('"', "'"):
        return ''
    eidx = sidx + 1
    while eidx < len(data):
        if data[eidx] == z:
            return data[sidx+1:eidx]
        eidx += 1
    return ''

def search(data, pattern, flags=0, limits=-1):
    tab = []
    if isinstance(pattern, basestring):
        reObj = re.compile(pattern, re.IGNORECASE if flags & IGNORECASE else 0)
    else:
        reObj = pattern
    if limits == -1:
        limits = reObj.groups
    match = reObj.search(data)
    for idx in range(limits):
        try:    value = match.group(idx + 1)
        except Exception: value = ''
        tab.append(value)
    return tab

def all(tab, data, start, end):
    for it in tab:
        if data.find(it, start, end) == -1:
            return False
    return True

def any(tab, data, start, end):
    for it in tab:
        if data.find(it, start, end) != -1:
            return True
    return False

def check(arg1, arg2=None):
    if arg2 == None and isinstance(arg1, basestring):
        return lambda data, ldata, s, e: ldata.find(arg1, s, e) != -1
    
    return lambda data, ldata, s, e: arg1(arg2, ldata, s, e)

def findall(data, start, end=('',), flags=START_E|END_E, limits=-1):

    start = start if isinstance(start, tuple) or isinstance(start, list) else (start,)
    end = end if isinstance(end, tuple) or isinstance(end, list) else (end,)

    if len(start) < 1 or len(end) < 1:
        return []

    itemsTab = []

    n1S = start[0]
    n1E = start[1] if len(start) > 1 else ''
    match1P = start[2] if len(start) > 2 else None
    match1P = check(match1P) if isinstance(match1P, basestring) else match1P

    n2S = end[0]
    n2E = end[1] if len(end) > 1 else ''
    match2P = end[2] if len(end) > 2 else None
    match2P = check(match2P) if isinstance(match2P, basestring) else match2P

    lastIdx = 0
    search = 1
    
    if not (flags & IGNORECASE):
        sData = data
    else:
        sData = data.lower()
        n1S = n1S.lower()
        n1E = n1E.lower()
        n2S = n2S.lower()
        n2E = n2E.lower()

    while True:
        if search == 1:
            # node 1 - start
            idx1 = sData.find(n1S, lastIdx)
            if -1 == idx1: return itemsTab
            lastIdx = idx1 + len(n1S)
            idx2 = sData.find(n1E, lastIdx)
            if -1 == idx2: return itemsTab
            lastIdx = idx2 + len(n1E)

            if match1P and not  match1P(data, sData, idx1 + len(n1S), idx2):
                continue

            search = 2
        else:
            # node 2 - end
            tIdx1 = sData.find(n2S, lastIdx)
            if -1 == tIdx1: return itemsTab
            lastIdx = tIdx1 + len(n2S)
            tIdx2 = sData.find(n2E, lastIdx)
            if -1 == tIdx2: return itemsTab
            lastIdx = tIdx2 + len(n2E)

            if match2P and not  match2P(data, sData, tIdx1 + len(n2S), tIdx2):
                continue

            if flags & START_S:
                itemsTab.append(data[idx1:idx2 + len(n1E)])

            idx1 = idx1 if flags & START_E else idx2 + len(n1E)
            idx2 = tIdx2 + len(n2E) if flags & END_E else tIdx1

            itemsTab.append(data[idx1:idx2])

            if flags & END_S:
                itemsTab.append(data[tIdx1:tIdx2 + len(n2E)])

            search = 1

        if limits > 0 and len(itemsTab) == limits:
            break
    return itemsTab

def rfindall(data, start, end=('',), flags=START_E|END_E, limits=-1):

    start = start if isinstance(start, tuple) or isinstance(start, list) else (start,)
    end = end if isinstance(end, tuple) or isinstance(end, list) else (end,)

    if len(start) < 1 or len(end) < 1:
        return []

    itemsTab = []

    n1S = start[0]
    n1E = start[1] if len(start) > 1 else ''
    match1P = start[2] if len(start) > 2 else None
    match1P = check(match1P) if isinstance(match1P, basestring) else match1P

    n2S = end[0]
    n2E = end[1] if len(end) > 1 else ''
    match2P = end[2] if len(end) > 2 else None
    match2P = check(match2P) if isinstance(match2P, basestring) else match2P

    lastIdx = len(data)
    search = 1
    
    if not (flags & IGNORECASE):
        sData = data
    else:
        sData = data.lower()
        n1S = n1S.lower()
        n1E = n1E.lower()
        n2S = n2S.lower()
        n2E = n2E.lower()

    while True:
        if search == 1:
            # node 1 - end
            idx1 = sData.rfind(n1S, 0, lastIdx)
            if -1 == idx1: return itemsTab
            lastIdx = idx1
            idx2 = sData.find(n1E, idx1+len(n1S))
            if -1 == idx2: return itemsTab

            if match1P and not  match1P(data, sData, idx1 + len(n1S), idx2):
                continue

            search = 2
        else:
            # node 2 - start
            tIdx1 = sData.rfind(n2S, 0, lastIdx)
            if -1 == tIdx1: return itemsTab
            lastIdx = tIdx1
            tIdx2 = sData.find(n2E, tIdx1+len(n2S), idx1)
            if -1 == tIdx2: return itemsTab

            if match2P and not  match2P(data, sData, tIdx1 + len(n2S), tIdx2):
                continue

            if flags & START_S:
                itemsTab.insert(0, data[idx1:idx2 + len(n1E)])

            s1 = tIdx1 if flags & START_E else tIdx2 + len(n2E)
            s2 = idx2 + len(n1E) if flags & END_E else idx1

            itemsTab.insert(0, data[s1:s2])

            if flags & END_S:
                itemsTab.insert(0, data[tIdx1:tIdx2 + len(n2E)])

            search = 1

        if limits > 0 and len(itemsTab) == limits:
            break
    return itemsTab


def find(data, start, end=('',), flags=START_E|END_E):
    ret = findall(data, start, end, flags, 1)
    if len(ret): return True, ret[0]
    else: return False, ''

def rfind(data, start, end=('',), flags=START_E|END_E):
    ret = rfindall(data, start, end, flags, 1)
    if len(ret): return True, ret[0]
    else: return False, ''
