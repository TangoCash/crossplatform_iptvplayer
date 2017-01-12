# -*- coding: utf-8 -*-

from __future__ import print_function
import urllib
import urllib2
import sys
import traceback
import time
import json
import threading
import urlparse

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)

def printDBG(strDat):
    if 1:
        print("%s" % strDat)

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def getPage(url, params={}, post_data=None):
    printDBG('url [%s]' % url)
    sts = False
    data = None
    return_data = params.get('return_data', True)
    try:
        req = urllib2.Request(url, post_data, params)
        if 0:
            if 'Referer' in params:
                req.add_header('Referer', params['Referer'])
            if 'User-Agent' in params:
                req.add_header('User-Agent', params['User-Agent'])
            if 'Cookie' in params:
                req.add_header('Cookie', params['Cookie'])
        resp = urllib2.urlopen(req)
        if return_data:
            data = resp.read()
            resp.close()
        else:
            data = resp
        sts = True
    except Exception:
        printExc()
    return sts, data
    
def checkAndReportUrl(vidUrl, userAgent):
    timeout = 20
    start_time = time.time()
    try:
        while True: 
            
            sts, data = getPage(vidUrl, {'User-Agent':userAgent})
            #printDBG(data)
            testResult = False
            data = data.split('\n')
            for item in reversed(data):
                item = item.strip()
                if item.endswith('.ts'):
                    url = urlparse.urljoin(vidUrl, item)
                    try:
                        sts, resp = getPage(url, {'return_data':False, 'User-Agent':userAgent})
                        if resp.headers['content-length'] > 0:
                            printDBG(resp.headers['content-length'])
                            testResult = True
                        resp.close()
                    except Exception:
                        printExc()
                    break
            if testResult:
                break
            time.sleep(2)
            dt = time.time() - start_time
            if dt >= timeout:
                break
    except Exception:
        printExc()
    print('\n%s\n' % vidUrl, file=sys.stderr)
 
    
def getTimestamp(t, s=64):
    a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    e = ""
    t = int(t)
    while t > 0:
        e = a[t % s] + e
        t = int(t / s)
    return e

if __name__ == "__main__":
    if len(sys.argv) < 9:
        print('User-Agent, BaseUrl, two refresh urls, stoken, streamId and libsPath are needed', file=sys.stderr)
        sys.exit(1)
    try:
        timeout = 20 # 20s
        userAgent   = sys.argv[1]
        baseUrl     = sys.argv[2]
        refreshUrl1 = sys.argv[3]
        refreshUrl2 = sys.argv[4]
        stoken      = sys.argv[5]
        streamId    = sys.argv[6]
        libsPath    = sys.argv[7]
        sid         = sys.argv[8]
        
        sys.path.insert(1, libsPath)
        import websocket
        
        ws1 = websocket.create_connection(refreshUrl1)
        try: ws2 = websocket.create_connection(refreshUrl2)
        except Exception: pass
        
        ws1.send('2probe')
        try: ws2.send('2probe')
        except Exception: pass
        
        result = ws1.recv()
        try: result = ws2.recv()
        except Exception: pass
        
        ws1.send('5')
        try: ws2.send('5')
        except Exception: pass
        
        if 0:
            t2 = getTimestamp(time.time()*1000)
            url = baseUrl.replace(":8000",":8004") + '/socket.io/?EIO=3&transport=polling&t={0}&sid={1}'.format(t2, sid)
            sts, data = getPage(url, {'User-Agent':userAgent, 'Cookie':sid}, '84:42["subscribe","%s"]' % streamId)
            print(data)

        ws1.send('42["subscribe","%s"]' % streamId)
        result = ws1.recv()
        printDBG(result)
        result = json.loads(result[result.find('42')+2:])
        if "ERR_PROC_EXIT" == result[1].get('error', None):
            sys.exit(-1)
        vidUrl = baseUrl.replace(":8000",":%s" % result[1].get('port', '8000')) + '/' + result[1]['url'] + '?token=' + stoken
       
       #print('\n%s\n' % vidUrl, file=sys.stderr)        
        t1 = FuncThread(checkAndReportUrl, vidUrl, userAgent)
        t1.start()
        #t1.join()
        
        start_time = time.time()
        result = ['', '']
        while True:
            printDBG("Refreshing....")
            
            dt = time.time() - start_time
            if dt >= 0 and dt < 20:
                time.sleep(20 - dt)
            
            ws1.send('2')
            try: ws2.send('2')
            except Exception: pass
            result[0] = ws1.recv()
            try: result[1] = ws2.recv()
            except Exception: pass
            print(result, file=sys.stderr)
            
            if 0:
                #42["stream_restart",{"event":"stream_restart","server":"http://109.236.84.53:8000","streamId":"219532349db1cc6aa31971dc4d593e68896bdd2a90fff4d659812c54f1f6928094"}]
                for item in result:
                    if 'stream_restart' in item:
                        item = json.loads(item[item.find('42')+2:])
                        vidUrl = baseUrl + '/' + item[1]['url'] + '?token=' + stoken
                        print('\n%s\n' % vidUrl, file=sys.stderr)
            
            start_time = time.time()
                    

        ws1.close()
        try: ws2.close()
        except Exception: pass
    except Exception:
        printExc()
    sys.exit(0)

