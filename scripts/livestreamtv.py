# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import time

def printDBG(strDat):
    if 0:
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
        req = urllib2.Request(url)
        if 'Referer' in params:
            req.add_header('Referer', params['Referer'])
        resp = urllib2.urlopen(req)
        data = resp.read()
        sts = True
    except:
        printExc()
    return sts, data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Refresh and referer urls are needed', file=sys.stderr)
        sys.exit(1)
    try:
        timeout = 20 # 20s
        refreshUrl = sys.argv[1]
        referer    = sys.argv[2]
        
        while True:
            printDBG("Refreshing....")
            start_time = time.time()
            tm = str(int(start_time * 1000))
            url = refreshUrl + "&_="+tm+"&callback=?"
            getPage(url, {'Referer':referer})
            dt = time.time() - start_time
            if dt > 0 and dt < 20:
                time.sleep(20 - dt)
    except:
        printExc()
    sys.exit(0)

