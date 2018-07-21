# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 419 - Wersja 605

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, GetIPTVNotify, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, IsHttpsCertValidationEnabled, byteify, GetDefaultLang, SetTmpCookieDir, rm, UsePyCurl
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_js_execute, IsMainThread, IsThreadTerminated, SetThreadKillable
###################################################
# FOREIGN import
###################################################
import urllib
import urllib2
import base64
try: import ssl
except Exception: pass
import re
import string
import time
import htmlentitydefs
import cookielib
import unicodedata
#import urllib2_ssl
try:    import json
except Exception: import simplejson as json
try:
    try: from cStringIO import StringIO
    except Exception: from StringIO import StringIO 
    import gzip
except Exception: pass
from Tools.Directories import fileExists
from urlparse import urljoin, urlparse, urlunparse
###################################################

def DecodeGzipped(data):
    buf = StringIO(data)
    f = gzip.GzipFile(fileobj=buf)
    return f.read()

def EncodeGzipped(data):
    f = StringIO()
    gzf = gzip.GzipFile(mode="wb", fileobj=f, compresslevel=1)
    gzf.write(data)
    gzf.close()
    encoded = f.getvalue()
    f.close()
    return encoded

class NoRedirection(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302

class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10

    def http_request(self, request):
        data = request.get_data()
        if data is not None and type(data) != str:
            content_type, data = self.encode_multipart_formdata( data )
            request.add_unredirected_header('Content-Type', content_type)
            request.add_data(data)
        return request
        
    def encode_multipart_formdata(self, fields):
        LIMIT = '-----------------------------14312495924498'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body
    
    https_request = http_request

class CParsingHelper:
    @staticmethod
    def listToDir(cList, idx):
        cTree = {'dat':''}
        deep = 0 
        while (idx+1) < len(cList):
            if cList[idx].startswith('<ul') or cList[idx].startswith('<li'):
                deep += 1
                nTree, idx, nDeep = CParsingHelper.listToDir(cList, idx+1)
                if 'list' not in cTree: cTree['list'] = []
                cTree['list'].append(nTree)
                deep += nDeep
            elif cList[idx].startswith('</ul>') or cList[idx].startswith('</li>'):
                deep -= 1
                idx += 1
            else:
                cTree['dat'] += cList[idx]
                idx += 1
            if deep < 0:
                break
        return cTree, idx, deep
    
    @staticmethod
    def getSearchGroups(data, pattern, grupsNum=1, ignoreCase=False):
        tab = []
        if ignoreCase:
            match = re.search(pattern, data, re.IGNORECASE)
        else:
            match = re.search(pattern, data)
        
        for idx in range(grupsNum):
            try:    value = match.group(idx + 1)
            except Exception: value = ''
            tab.append(value)
        return tab
        
    @staticmethod
    def getDataBeetwenReMarkers(data, pattern1, pattern2, withMarkers=True):
        match1 = pattern1.search(data)
        if None == match1 or -1 == match1.start(0): return False, ''
        match2 = pattern2.search(data[match1.end(0):])
        if None == match2 or -1 == match2.start(0): return False, ''
        
        if withMarkers:
            return True, data[match1.start(0): (match1.end(0) + match2.end(0)) ]
        else:
            return True, data[match1.end(0): (match1.end(0) + match2.start(0)) ]

        
    @staticmethod
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
        
    @staticmethod
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
        
    @staticmethod
    def rgetAllItemsBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
        itemsTab = []
        if caseSensitive:
            sData = data
        else:
            sData = data.lower()
            marker1 = marker1.lower()
            marker2 = marker2.lower()
        idx1 = len(data)
        while True:
            idx1 = sData.rfind(marker1, 0, idx1)
            if -1 == idx1: return itemsTab
            idx2 = sData.rfind(marker2, 0, idx1)
            if -1 == idx2: return itemsTab
            
            if withMarkers:
                itemsTab.insert(0, data[idx2:idx1+len(marker1)])
            else:
                itemsTab.insert(0, data[idx2+len(marker2):idx1])
            idx1 = idx2
        return itemsTab
        
    @staticmethod
    def rgetDataBeetwenMarkers2(data, marker1, marker2, withMarkers=True, caseSensitive=True):
        if caseSensitive:
            sData = data
        else:
            sData = data.lower()
            marker1 = marker1.lower()
            marker2 = marker2.lower()
        idx1 = len(data)
        
        idx1 = sData.rfind(marker1, 0, idx1)
        if -1 == idx1: return False, ''
        idx2 = sData.rfind(marker2, 0, idx1)
        if -1 == idx2: return False, ''
        
        if withMarkers:
            return True, data[idx2:idx1+len(marker1)]
        else:
            return True, data[idx2+len(marker2):idx1]
        
    @staticmethod
    def rgetDataBeetwenMarkers(data, marker1, marker2, withMarkers = True):
        # this methods is not working as expected, but is is used in many places
        # so I will leave at it is, please use rgetDataBeetwenMarkers2
        idx1 = data.rfind(marker1)
        if -1 == idx1: return False, ''
        idx2 = data.rfind(marker2, idx1 + len(marker1))
        if -1 == idx2: return False, ''
        
        if withMarkers:
            idx2 = idx2 + len(marker2)
        else:
            idx1 = idx1 + len(marker1)
        return True, data[idx1:idx2]
        
    @staticmethod
    def getDataBeetwenNodes(data, node1, node2, withNodes=True, caseSensitive=True):
        ret = CParsingHelper.getAllItemsBeetwenNodes(data, node1, node2, withNodes, 1, caseSensitive)
        if len(ret): return True, ret[0]
        else: return False, ''
    
    @staticmethod
    def getAllItemsBeetwenNodes(data, node1, node2, withNodes=True, numNodes=-1, caseSensitive=True):
        if len(node1) < 2 or len(node2) < 2:
            return []
        itemsTab = []
        n1S = node1[0]
        n1E = node1[1]
        if len(node1) > 2: n1P = node1[2]
        else: n1P = None
        n2S = node2[0]
        n2E = node2[1]
        if len(node2) > 2: n2P = node2[2]
        else: n2P = None
        lastIdx = 0
        search = 1
        
        if caseSensitive:
            sData = data
        else:
            sData = data.lower()
            n1S = n1S.lower()
            n1E = n1E.lower()
            if n1P != None: n1P = n1P.lower()
            n2S = n2S.lower()
            n2E = n2E.lower()
            if n2P != None: n2P = n2P.lower()
            
        while True:
            if search == 1:
                # node 1 - start
                idx1 = sData.find(n1S, lastIdx)
                if -1 == idx1: return itemsTab
                lastIdx = idx1 + len(n1S)
                idx2 = sData.find(n1E, lastIdx)
                if -1 == idx2: return itemsTab
                lastIdx = idx2 + len(n1E)
                if n1P != None and sData.find(n1P, idx1 + len(n1S), idx2) == -1:
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

                if n2P != None and sData.find(n2P, tIdx1 + len(n2S), tIdx2) == -1:
                    continue

                if withNodes:
                    idx2 = tIdx2 + len(n2E)
                else:
                    idx1 = idx2 + len(n1E)
                    idx2 = tIdx1
                search = 1
                itemsTab.append(data[idx1:idx2])
            if numNodes > 0 and len(itemsTab) == numNodes:
                break
        return itemsTab
        
    @staticmethod
    def rgetDataBeetwenNodes(data, node1, node2, withNodes=True, caseSensitive=True):
        ret = CParsingHelper.rgetAllItemsBeetwenNodes(data, node1, node2, withNodes, 1, caseSensitive)
        if len(ret): return True, ret[0]
        else: return False, ''
        
    @staticmethod
    def rgetAllItemsBeetwenNodes(data, node1, node2, withNodes=True, numNodes=-1, caseSensitive=True):
        if len(node1) < 2 or len(node2) < 2:
            return []
        itemsTab = []
        n1S = node1[0]
        n1E = node1[1]
        if len(node1) > 2: n1P = node1[2]
        else: n1P = None
        n2S = node2[0]
        n2E = node2[1]
        if len(node2) > 2: n2P = node2[2]
        else: n2P = None
        lastIdx = len(data)
        search = 1
        if caseSensitive:
            sData = data
        else:
            sData = data.lower()
            n1S = n1S.lower()
            n1E = n1E.lower()
            if n1P != None: n1P = n1P.lower()
            n2S = n2S.lower()
            n2E = n2E.lower()
            if n2P != None: n2P = n2P.lower()
        while True:
            if search == 1:
                # node 1 - end
                idx1 = sData.rfind(n1S, 0, lastIdx)
                if -1 == idx1: return itemsTab
                lastIdx = idx1
                idx2 = sData.find(n1E, idx1+len(n1S))
                if -1 == idx2: return itemsTab
                if n1P != None and sData.find(n1P, idx1 + len(n1S), idx2) == -1:
                    continue
                search = 2
            else:
                # node 2 - start
                tIdx1 = sData.rfind(n2S, 0, lastIdx)
                if -1 == tIdx1: return itemsTab
                lastIdx = tIdx1
                tIdx2 = sData.find(n2E, tIdx1+len(n2S), idx1)
                if -1 == tIdx2: return itemsTab
                if n2P != None and sData.find(n2P, tIdx1 + len(n2S), tIdx2) == -1:
                    continue
                if withNodes:
                    s1 = tIdx1
                    s2 = idx2 + len(n1E)
                else:
                    s1 = tIdx2 + len(n2E)
                    s2 = idx1
                search = 1
                itemsTab.insert(0, data[s1:s2])
            if numNodes > 0 and len(itemsTab) == numNodes:
                break
        return itemsTab

    @staticmethod
    def removeDoubles(data, pattern):
        while -1 < data.find(pattern+pattern) and '' != pattern:
            data = data.replace(pattern+pattern, pattern)
        return data 

    @staticmethod
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
        
    # this method is useful only for developers 
    # to dump page code to the file
    @staticmethod
    def writeToFile(file, data, mode = "w"):
        #helper to see html returned by ajax
        file_path = file
        text_file = open(file_path, mode)
        text_file.write(data)
        text_file.close()
    
    @staticmethod
    def getNormalizeStr(txt, idx=None):
        POLISH_CHARACTERS = {u'ą':u'a', u'ć':u'c', u'ę':u'ę', u'ł':u'l', u'ń':u'n', u'ó':u'o', u'ś':u's', u'ż':u'z', u'ź':u'z',
                             u'Ą':u'A', u'Ć':u'C', u'Ę':u'E', u'Ł':u'L', u'Ń':u'N', u'Ó':u'O', u'Ś':u'S', u'Ż':u'Z', u'Ź':u'Z',
                             u'á':u'a', u'é':u'e', u'í':u'i', u'ñ':u'n', u'ó':u'o', u'ú':u'u', u'ü':u'u',
                             u'Á':u'A', u'É':u'E', u'Í':u'I', u'Ñ':u'N', u'Ó':u'O', u'Ú':u'U', u'Ü':u'U',
                            }
        txt = txt.decode('utf-8')
        if None != idx: txt = txt[idx]
        nrmtxt = unicodedata.normalize('NFC', txt)
        ret_str = []
        for item in nrmtxt:
            if ord(item) > 128:
                item = POLISH_CHARACTERS.get(item)
                if item: ret_str.append(item)
            else: # pure ASCII character
                ret_str.append(item)
        return ''.join(ret_str).encode('utf-8')
        
    @staticmethod
    def isalpha(txt, idx=None):
        return CParsingHelper.getNormalizeStr(txt, idx).isalpha()

class common:
    HOST   = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
    HEADER = None
    ph = CParsingHelper
    
    @staticmethod
    def getParamsFromUrlWithMeta(url, baseHeaderOutParams=None):
        from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
        HANDLED_HTTP_HEADER_PARAMS = DMHelper.HANDLED_HTTP_HEADER_PARAMS #['Host', 'User-Agent', 'Referer', 'Cookie', 'Accept',  'Range']
        outParams = {}
        tmpParams = {}
        postData = None
        if isinstance(url, strwithmeta):
            if None != baseHeaderOutParams: tmpParams['header'] = baseHeaderOutParams
            else: tmpParams['header'] = {}
            for key in url.meta:
                if key in HANDLED_HTTP_HEADER_PARAMS:
                    tmpParams['header'][key] = url.meta[key]
            if 0 < len(tmpParams['header']):
                outParams = tmpParams
            if 'iptv_proxy_gateway' in url.meta:
                outParams['proxy_gateway'] = url.meta['iptv_proxy_gateway']
            if 'iptv_http_proxy' in url.meta:
                outParams['http_proxy'] = url.meta['iptv_http_proxy']
        return outParams, postData
        
    @staticmethod
    def getBaseUrl(url, domainOnly=False):
        parsed_uri = urlparse( url )
        if domainOnly:
            domain = '{uri.netloc}'.format(uri=parsed_uri)
        else:
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain
        
    @staticmethod
    def getFullUrl(url, mainUrl='http://fake'):
        if url.startswith('//'):
            proto = mainUrl.split('://', 1)[0]
            url = proto + ':' + url
        elif url.startswith('://'):
            proto = mainUrl.split('://', 1)[0]
            url = proto + url
        elif url.startswith('/'):
            url = mainUrl + url[1:]
        elif 0 < len(url) and not common.isValidUrl(url):
            url = urljoin(mainUrl, url)
        return url
        
    @staticmethod
    def isValidUrl(url):
        return url.startswith('http://') or url.startswith('https://')
    
    def __init__(self, proxyURL= '', useProxy = False, useMozillaCookieJar=True):
        self.proxyURL = proxyURL
        self.useProxy = useProxy
        self.geolocation = {}
        self.useMozillaCookieJar = useMozillaCookieJar
        self.metadataFromLastRequest = {}
        
        self.curlSession = None
        self.pyCurlAvailable = None
        self.pyCurl = None
    
    @property
    def meta(self):
        return self.metadataFromLastRequest
    
    def usePyCurl(self):
        bRet = False
        if UsePyCurl():
            if self.pyCurlAvailable == None:
                try:
                    import pycurl
                    #test = pycurl.SSLVERSION_TLSv1_3
                    verInfo = pycurl.version_info()
                    printDBG("usePyCurl VERSION: %s" % [verInfo])
                    # #define CURL_VERSION_ASYNCHDNS    (1<<7)
                    # we need to have ASYNC DNS to be able "cancel"
                    # request
                    if verInfo[4] & (1<<7):
                        self.pyCurlAvailable = True
                        self.pyCurl = pycurl
                    else:
                        self.pyCurlAvailable = False
                except Exception:
                    self.pyCurlAvailable = False
                    printExc()
            bRet = self.pyCurlAvailable
        return bRet
        
    def getCountryCode(self, lower=True):
        if 'countryCode' not in self.geolocation:
            sts, data = self.getPage('http://ip-api.com/json')
            if sts:
                try:
                    self.geolocation['countryCode'] = byteify(json.loads(data))['countryCode']
                except Exception:
                    printExc()
        return self.geolocation.get('countryCode', '').lower()
        
    def _pyCurlLoadCookie(self, cookiefile, ignoreDiscard=True, ignoreExpires=False):
        cj = cookielib.MozillaCookieJar()
        f = open(cookiefile)
        lines = f.readlines()
        f.close()
        for idx in range(len(lines)):
            lineNeedFix = False
            fields = lines[idx].split('\t')
            if len(fields) < 5: continue
            if fields[0].startswith('#HttpOnly_'):
                fields[0] = fields[0][10:]
                lineNeedFix = True
            if fields[4] == '0':
                fields[4] = ''
                lineNeedFix = True
            if lineNeedFix: 
                lines[idx] = '\t'.join(fields)
        cj._really_load(StringIO(''.join(lines)), cookiefile, ignore_discard=ignoreDiscard, ignore_expires=ignoreExpires)
        return cj
        
    def clearCookie(self, cookiefile, leaveNames=[], removeNames=None, ignore_discard = True):
        try:
            toRemove = []
            if self.usePyCurl():
                cj = self._pyCurlLoadCookie(cookiefile, ignoreDiscard, ignoreExpires)
            elif not self.useMozillaCookieJar:
                cj = cookielib.LWPCookieJar()
            else:
                cj = cookielib.MozillaCookieJar()
            cj.load(cookiefile, ignore_discard = ignore_discard)
            for cookie in cj:
                if cookie.name not in leaveNames and (None == removeNames or cookie.name in removeNames):
                    toRemove.append(cookie)
            for cookie in toRemove:
                cj.clear(cookie.domain, cookie.path, cookie.name)
            cj.save(cookiefile, ignore_discard = ignore_discard)
        except Exception:
            printExc()
            return False
        return True
        
    def getCookieItem(self, cookiefile, item):
        cookiesDict = self.getCookieItems(cookiefile)
        return cookiesDict.get(item, '')
        
    def getCookieItems(self, cookiefile, ignoreDiscard=True, ignoreExpires=False):
        cookiesDict = {}
        try:
            if self.usePyCurl():
                cj = self._pyCurlLoadCookie(cookiefile, ignoreDiscard, ignoreExpires)
            elif not self.useMozillaCookieJar:
                cj = cookielib.LWPCookieJar()
                cj.load(cookiefile, ignore_discard = ignoreDiscard)
            else:
                cj = cookielib.MozillaCookieJar()
                cj.load(cookiefile, ignore_discard = ignoreDiscard)
            for cookie in cj:
                cookiesDict[cookie.name] = cookie.value
        except Exception:
            printExc()
        return cookiesDict
        
    def getCookieHeader(self, cookiefile, allowedNames=[], unquote=True, ignoreDiscard=True, ignoreExpires=False):
        ret = ''
        try:
            cookiesDict = self.getCookieItems(cookiefile, ignoreDiscard, ignoreExpires)
            for name in cookiesDict:
                if 0 < len(allowedNames) and name not in allowedNames: continue
                value = cookiesDict[name]
                if unquote: value = urllib.unquote(value)
                ret += '%s=%s; ' % (name, value)
        except Exception:
            printExc()
        return ret

    def getPageWithPyCurl(self, url, params = {}, post_data = None):
        if IsMainThread():
            msg1 = _('It is not allowed to call getURLRequestData from main thread.')
            msg2 = _('You should never perform block I/O operations in the __init__.')
            GetIPTVNotify().push('\s'.join([msg1, msg2]), 'error', 40)
            raise Exception("Wrong usage!")
        
        pycurl = self.pyCurl
        # by default we will work in return_data mode
        if 'return_data' not in params:
            params['return_data'] = True
        
        self.metadataFromLastRequest = {}
        metadata = self.metadataFromLastRequest
        out_data = None
        sts = False
        
        buffer = StringIO()
        checkFromFirstBytes = params.get('check_first_bytes', [])
        fileHandler = None
        firstAttempt = [True]
        
        responseHeaders = {}
        def _headerFunction(headerLine):
            if ':' not in headerLine:
                return

            name, value = headerLine.split(':', 1)

            name = name.strip()
            value = value.strip()

            name = name.lower()
            responseHeaders[name] = value

        def _bodyFunction(toWriteData):
            # we started receiving body data so all headers are available
            # so we can check it if needed
            if firstAttempt[0]:
                firstAttempt[0] = False
                if 'check_maintype' in params and \
                    params['check_maintype'] != responseHeaders.get('content-type', '').split('/', 1)[0]:
                    printDBG('wrong maintype: %s' % responseHeaders.get('content-type', ''))
                    return 0
                
                if 'check_subtypes' in params:
                    contentSubType = responseHeaders.get('content-type', '').split('/', 1)[-1]
                    try:
                        valid = False
                        for subType in params['check_subtypes']:
                            if subType == contentSubType:
                                valid = True
                                break
                        if not valid:
                            printDBG('wrong type: %s' % responseHeaders.get('content-type', ''))
                            return 0
                    except Exception:
                        printExc()
                        return 0 # wrong params?
 
            # if we should check start body data 
            if len(checkFromFirstBytes):
                buffer.write(toWriteData)
                toWriteData = None
                valid = False
                value = buffer.getvalue()
                for toCheck in checkFromFirstBytes:
                    if len(toCheck) <= len(value):
                        if value.startswith(toCheck):
                            valid = True
                            # valid no need to check anymore
                            del checkFromFirstBytes[:]
                            break
                    elif toCheck.startswith(value):
                        # it could be valid - we need to wait for more data
                        valid = True
                if not valid:
                    printDBG('wrong body')
                    return 0
            
            if fileHandler != None and 0 == len(checkFromFirstBytes):
                # all check were done so, we can start write data to file
                try:
                    if fileHandler.tell() == 0 and buffer.tell() > 0:
                        fileHandler.write(buffer.getvalue())
                    
                    if toWriteData != None:
                        fileHandler.write(toWriteData)
                except Exception:
                    printExc()
                    return 0 # wrong file handle
                
            if  toWriteData != None and params['return_data']:
                buffer.write(toWriteData)
            
        def _terminateFunction(download_t, download_d, upload_t, upload_d):
            if IsThreadTerminated():
                printDBG(">> _terminateFunction")
                return True # anything else then None will cause pycurl perform cancel
        
        try:
            timeout = params.get('timeout', None)
            
            if 'host' in params:
                host = params['host']
            else:
                host = self.HOST

            if 'header' in params:
                headers = params['header']
            elif None != self.HEADER:
                headers = self.HEADER
            else:
                headers = { 'User-Agent' : host }
                
            if 'User-Agent' not in headers:
                headers['User-Agent'] = host
            
            printDBG('pCommon - getPageWithPyCurl() -> params: ' + str(params))
            printDBG('pCommon - getPageWithPyCurl() -> headers: ' + str(headers)) 
            
            if 'save_to_file' in params:
                fileHandler = file(params['save_to_file'], "wb")
            
            # we can not kill thread when we are in any function of pycurl
            SetThreadKillable(False)
            
            if None == self.curlSession:
                curlSession = pycurl.Curl()
            else:
                # use previous session to be able to reuse connection
                curlSession = self.curlSession
                self.curlSession = None
                curlSession.reset()
            
            customHeaders = []
            for key in headers:
                lKey = key.lower()
                if lKey == 'user-agent': curlSession.setopt(pycurl.USERAGENT, headers[key])
                elif lKey == 'cookie': curlSession.setopt(pycurl.COOKIE, headers[key])
                elif lKey == 'referer': curlSession.setopt(pycurl.REFERER, headers[key])
                else: customHeaders.append('%s: %s' % (key, headers[key]))
            if len(customHeaders):
                curlSession.setopt(pycurl.HTTPHEADER, customHeaders)
            
            curlSession.setopt(pycurl.ACCEPT_ENCODING, "") # enable all supported built-in compressions
            #sslProto = params.get('ssl_protocol', None)
            #ssl.PROTOCOL_TLSv1_2
            #curlSession.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_TLSv1_0) # TLS v1.0 or later 
            
            if 'use_cookie' not in params and 'cookiefile' in params and ('load_cookie' in params or 'save_cookie' in params):
                params['use_cookie'] = True
                
            if params.get('use_cookie', False):
                cookiesStr = ''
                for cookieKey in params.get('cookie_items', {}).keys():
                    printDBG("cookie_item[%s=%s]" % (cookieKey, params['cookie_items'][cookieKey]))
                    cookiesStr += '%s=%s; ' % (cookieKey, params['cookie_items'][cookieKey])
                
                if cookiesStr != '':
                    curlSession.setopt(pycurl.COOKIE, cookiesStr) #'Set-Cookie: foo=baar') #
            
                if params.get('load_cookie', False):
                    curlSession.setopt(pycurl.COOKIEFILE, params.get('cookiefile', ''))
                
                if params.get('save_cookie', False):
                    curlSession.setopt(pycurl.COOKIEJAR, params.get('cookiefile', ''))
                    
            if timeout != None:
                curlSession.setopt(pycurl.CONNECTTIMEOUT, timeout) # in seconds - connection timeout
                curlSession.setopt(pycurl.LOW_SPEED_TIME, timeout) # in seconds
                curlSession.setopt(pycurl.LOW_SPEED_LIMIT, 10) # in bytes
                # set maximum time the request is allowed to take
                #curlSession.setopt(pycurl.TIMEOUT, 300) # in seconds
            
            if not params.get('no_redirection', False):
                curlSession.setopt(pycurl.FOLLOWLOCATION, 1)
                curlSession.setopt(pycurl.UNRESTRICTED_AUTH, 1)
                curlSession.setopt(pycurl.MAXREDIRS, 5)
            
            # debug 
            #curlSession.setopt(pycurl.VERBOSE, 1)
            #curlSession.setopt(pycurl.DEBUGFUNCTION, debug_fun)
            
            if not IsHttpsCertValidationEnabled():
                curlSession.setopt(pycurl.SSL_VERIFYHOST, 0)
                curlSession.setopt(pycurl.SSL_VERIFYPEER, 0)
            
            #proxy support
            if self.useProxy:
                http_proxy = self.proxyURL
            else:
                http_proxy = ''
            #proxy from parameters (if available) overwrite default one
            if 'http_proxy' in params:
                http_proxy = params['http_proxy']
            if '' != http_proxy:
                printDBG('getPageWithPyCurl USE PROXY')
                curlSession.setopt(pycurl.PROXY, http_proxy)
            
            pageUrl = url
            proxy_gateway = params.get('proxy_gateway', '')
            if proxy_gateway != '':
                pageUrl = proxy_gateway.format(urllib.quote_plus(pageUrl, ''))
            printDBG("pageUrl: [%s]" % pageUrl)
            
            curlSession.setopt(pycurl.URL, pageUrl)
            
            if None != post_data:
                printDBG('pCommon - getPageWithPyCurl() -> post data: ' + str(post_data))
                if params.get('raw_post_data', False):
                    curlSession.setopt(pycurl.POSTFIELDS, post_data)
                elif params.get('multipart_post_data', False):
                    printDBG("multipart_post_data NOT SUPPORTED")
                    dataPost = post_data
                    curlSession.setopt(pycurl.HTTPPOST, post_data)
                    #curlSession.setopt(pycurl.CUSTOMREQUEST, "PUT")
                else:
                    curlSession.setopt(pycurl.POSTFIELDS, urllib.urlencode(post_data))
            
            curlSession.setopt(pycurl.WRITEDATA, buffer)
            curlSession.setopt(pycurl.HEADERFUNCTION, _headerFunction)
            if fileHandler:
                curlSession.setopt(pycurl.WRITEFUNCTION, _bodyFunction)

            curlSession.setopt(pycurl.NOPROGRESS, False)
            curlSession.setopt(pycurl.PROGRESSFUNCTION, _terminateFunction)
            curlSession.setopt(pycurl.NOSIGNAL, 1)

            if not IsThreadTerminated():
                curlSession.perform()
                
                metadata['url'] = curlSession.getinfo(pycurl.EFFECTIVE_URL)
                metadata['status_code'] = curlSession.getinfo(pycurl.HTTP_CODE)
                metadata['size_download'] = curlSession.getinfo(pycurl.SIZE_DOWNLOAD)
                
                # reset will cause lost all cookies, so we force to saved them in the file
                if params.get('use_cookie', False) and params.get('save_cookie', False):
                    curlSession.setopt(pycurl.COOKIELIST , 'FLUSH')
                
                curlSession.reset()
                # to be re-used in next request
                self.curlSession = curlSession 
                
                # we should not use pycurl anymore
                SetThreadKillable(True)
                
                if 'content-type' in responseHeaders:
                    metadata['content-type'] = responseHeaders['content-type']
                
                if params['return_data']:
                    out_data = buffer.getvalue()
                else:
                    out_data = ""
                
                out_data, metadata = self.handleCharset(params, out_data, metadata)
                if metadata['status_code'] != 200:
                    ignoreCodeRanges = params.get('ignore_http_code_ranges', [(404, 404), (500, 500)])
                    for ignoreCodeRange in ignoreCodeRanges:
                        if metadata['status_code'] >= ignoreCodeRange[0] and metadata['status_code'] <= ignoreCodeRange[1]:
                            sts = True
                            break
                else:
                    sts = True

            if fileHandler:
                fileHandler.close()
        except Exception:
            printExc()
        
        SetThreadKillable(True)
        
        printDBG('pCommon - getPageWithPyCurl() return -> \nsts: %s\nmetadata: %s\n' % (sts, metadata))
        if params.get('with_metadata', False):
            out_data = strwithmeta(out_data, metadata)
            
        return sts, out_data
    
    def getPage(self, url, addParams = {}, post_data = None):
        ''' wraps getURLRequestData '''
        
        # if curl should be used and can be used
        if addParams.get('return_data', True) and self.usePyCurl():
            return self.getPageWithPyCurl(url, addParams, post_data)
        
        try:
            addParams['url'] = url
            if 'return_data' not in addParams:
                addParams['return_data'] = True
            response = self.getURLRequestData(addParams, post_data)
            status = True
        except urllib2.HTTPError, e:
            try:
                printExc()
                status = False
                response = e
                if addParams.get('return_data', False):
                    self.metadataFromLastRequest = {}
                    metadata = self.metadataFromLastRequest
                    metadata['url'] = e.fp.geturl()
                    metadata['status_code'] = e.code
                    if 'Content-Type' in e.fp.info():
                        metadata['content-type'] = e.fp.info()['Content-Type']
                    
                    data = e.fp.read()
                    if e.fp.info().get('Content-Encoding', '') == 'gzip':
                        data = DecodeGzipped(data)
                    
                    data, metadata = self.handleCharset(addParams, data, metadata)
                    response = strwithmeta(data, metadata)
                    e.fp.close()
            except Exception:
                printExc()
        except urllib2.URLError, e:
            if 'TLSV1_ALERT_PROTOCOL_VERSION' in str(e) and 'ssl_protocol' not in addParams:
                try:
                    newParams = dict(addParams)
                    newParams['ssl_protocol'] = ssl.PROTOCOL_TLSv1_2
                    return self.getPage(url, newParams, post_data)
                except Exception: 
                    pass
            printExc()
            response = None
            status = False
                
        except Exception:
            printExc()
            response = None
            status = False
        
        if addParams['return_data'] and status and not isinstance(response, basestring):
            status = False
            
        return (status, response)
        
    def getPageWithWget(self, url, params={}, post_data=None):
        from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
        cmd = DMHelper.getBaseWgetCmd(params.get('header', {})) +  (" --timeout=20 --tries=1 '%s' " % url)
        if post_data != None:
            if params.get('raw_post_data', False):
                post_data_str = post_data
            else:
                post_data_str = urllib.urlencode(post_data)
            cmd += " --post-data '{0}' ".format(post_data_str)
        
        if params.get('use_cookie', False):
            cmd += " --keep-session-cookies "
            cookieFile = str(params.get('cookiefile', ''))
            if params.get('load_cookie', False) and fileExists(cookieFile):
                cmd += "  --load-cookies '%s' " %  cookieFile
            if params.get('save_cookie', False):
                cmd += "  --save-cookies '%s' " %  cookieFile
        cmd += ' -O - 2> /dev/null'
        
        printDBG('_getPageWget request: [%s]' % cmd)
        from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_execute
        
        data = iptv_execute()( cmd )
        
        if params.get('use_cookie', False) and params.get('save_cookie', False) and fileExists(cookieFile):
            # fix cookie 
            
            try:
                f = open(cookieFile, "r")
                cookieStr = f.read()
                f.close()
                
                marker = '# HTTP cookie file.'
                if cookieStr.startswith(marker):
                    cookieStr = cookieStr.replace(marker, '# HTTP Cookie File.')
                    f = open(cookieFile, "w")
                    f.write(cookieStr)
                    f.close()
            except Exception:
                printExc()
        
        if not data['sts'] or 0 != data['code']: 
            return False, None
        else:
            return True, data['data']
        
    def getPageCFProtection(self, baseUrl, params={}, post_data=None):
        cfParams = params.get('cloudflare_params', {})
        
        def _getFullUrlEmpty(url):
            return url
        _getFullUrl  = cfParams.get('full_url_handle', _getFullUrlEmpty)
        _getFullUrl2 = cfParams.get('full_url_handle2', _getFullUrlEmpty)
        
        url = baseUrl
        header = {'Referer':url, 'User-Agent':cfParams.get('User-Agent', ''), 'Accept-Encoding':'text'}
        header.update(params.get('header', {}))
        params.update({'with_metadata':True, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': cfParams.get('cookie_file', ''), 'header':header})
        sts, data = self.getPage(url, params, post_data)
        
        current = 0
        while current < 5:
            #if True:
            if not sts and None != data:
                start_time = time.time()
                current += 1
                doRefresh = False
                try:
                    domain = self.getBaseUrl(data.meta['url'])
                    verData = data
                    printDBG("------------------")
                    printDBG(verData)
                    printDBG("------------------")
                    if 'sitekey' not in verData and 'challenge' not in verData: break
                    
                    printDBG(">>")
                    printDBG(verData)
                    printDBG("<<")
                    
                    sitekey = self.ph.getSearchGroups(verData, 'data-sitekey="([^"]+?)"')[0]
                    id = self.ph.getSearchGroups(verData, 'data-ray="([^"]+?)"')[0]
                    if sitekey != '':
                        from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v2 import UnCaptchaReCaptcha
                        # google captcha
                        recaptcha = UnCaptchaReCaptcha(lang=GetDefaultLang())
                        recaptcha.HTTP_HEADER['Referer'] = baseUrl
                        if '' != cfParams.get('User-Agent', ''): recaptcha.HTTP_HEADER['User-Agent'] = cfParams['User-Agent']
                        token = recaptcha.processCaptcha(sitekey)
                        if token == '': return False, None
                        
                        sts, tmp = self.ph.getDataBeetwenMarkers(verData, '<form', '</form>', caseSensitive=False)
                        if not sts: return False, None
                        
                        url = self.ph.getSearchGroups(tmp, 'action="([^"]+?)"')[0]
                        if url != '': url = _getFullUrl( url )
                        else: url = data.meta['url']
                        actionType = self.ph.getSearchGroups(tmp, 'method="([^"]+?)"', 1, True)[0].lower()
                        post_data2 = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                        #post_data2['id'] = id
                        if '' != token:
                            post_data2['g-recaptcha-response'] = token
                        else:
                            continue
                        params2 = dict(params)
                        params2['header']= dict(params['header'])
                        params2['header']['Referer'] = baseUrl
                        if actionType == 'get':
                            if '?' in url:
                                url += '&'
                            else:
                                url += '?'
                            url += urllib.urlencode(post_data2)
                            post_data2 = None
                            
                        sts, data = self.getPage(url, params2, post_data2)
                        printDBG("+++++++++++++")
                        printDBG(sts)
                        printDBG("-------------")
                        printDBG(data)
                        printDBG("++++++++++++++")
                    else:
                        dat = self.ph.getAllItemsBeetwenNodes(verData, ('<script', '>'), ('</script', '>'), False)
                        for item in dat:
                            if 'setTimeout' in item and 'submit()' in item:
                                dat = item
                                break
                        decoded = ''
                        jscode = base64.b64decode('''ZnVuY3Rpb24gc2V0VGltZW91dCh0LGUpe2lwdHZfcmV0LnRpbWVvdXQ9ZSx0KCl9dmFyIGlwdHZfcmV0PXt9LGlwdHZfZnVuPW51bGwsZG9jdW1lbnQ9e30sd2luZG93PXRoaXMsZWxlbWVudD1mdW5jdGlvbih0KXt0aGlzLl9uYW1lPXQsdGhpcy5fc3JjPSIiLHRoaXMuX2lubmVySFRNTD0iIix0aGlzLl9wYXJlbnRFbGVtZW50PSIiLHRoaXMuc2hvdz1mdW5jdGlvbigpe30sdGhpcy5hdHRyPWZ1bmN0aW9uKHQsZSl7cmV0dXJuInNyYyI9PXQmJiIjdmlkZW8iPT10aGlzLl9uYW1lJiZpcHR2X3NyY2VzLnB1c2goZSksdGhpc30sdGhpcy5maXJzdENoaWxkPXtocmVmOmlwdHZfZG9tYWlufSx0aGlzLnN0eWxlPXtkaXNwbGF5OiIifSx0aGlzLnN1Ym1pdD1mdW5jdGlvbigpe3ByaW50KEpTT04uc3RyaW5naWZ5KGlwdHZfcmV0KSl9LE9iamVjdC5kZWZpbmVQcm9wZXJ0eSh0aGlzLCJzcmMiLHtnZXQ6ZnVuY3Rpb24oKXtyZXR1cm4gdGhpcy5fc3JjfSxzZXQ6ZnVuY3Rpb24odCl7dGhpcy5fc3JjPXR9fSksT2JqZWN0LmRlZmluZVByb3BlcnR5KHRoaXMsImlubmVySFRNTCIse2dldDpmdW5jdGlvbigpe3JldHVybiB0aGlzLl9pbm5lckhUTUx9LHNldDpmdW5jdGlvbih0KXt0aGlzLl9pbm5lckhUTUw9dH19KSxPYmplY3QuZGVmaW5lUHJvcGVydHkodGhpcywidmFsdWUiLHtnZXQ6ZnVuY3Rpb24oKXtyZXR1cm4iIn0sc2V0OmZ1bmN0aW9uKHQpe2lwdHZfcmV0LmFuc3dlcj10fX0pfSwkPWZ1bmN0aW9uKHQpe3JldHVybiBuZXcgZWxlbWVudCh0KX07ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQ9ZnVuY3Rpb24odCl7cmV0dXJuIG5ldyBlbGVtZW50KHQpfSxkb2N1bWVudC5jcmVhdGVFbGVtZW50PWZ1bmN0aW9uKHQpe3JldHVybiBuZXcgZWxlbWVudCh0KX0sZG9jdW1lbnQuYXR0YWNoRXZlbnQ9ZnVuY3Rpb24oKXtpcHR2X2Z1bj1hcmd1bWVudHNbMV19Ow==''')
                        jscode = "var location = {hash:''}; var iptv_domain='%s';\n%s\n%s\niptv_fun();" % (domain, jscode, dat) #cfParams['domain']
                        printDBG("+ CODE +")
                        printDBG(jscode)
                        printDBG("++++++++")
                        ret = iptv_js_execute( jscode )
                        decoded = byteify(json.loads(ret['data'].strip()))
                        
                        verData = self.ph.getDataBeetwenReMarkers(verData, re.compile('<form[^>]+?id="challenge-form"'), re.compile('</form>'), False)[1]
                        printDBG(">>")
                        printDBG(verData)
                        printDBG("<<")
                        verUrl =  _getFullUrl( self.ph.getSearchGroups(verData, 'action="([^"]+?)"')[0] )
                        get_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', verData))
                        get_data['jschl_answer'] = decoded['answer']
                        verUrl += '?'
                        for key in get_data:
                            verUrl += '%s=%s&' % (key, get_data[key])
                        verUrl = _getFullUrl( self.ph.getSearchGroups(verData, 'action="([^"]+?)"')[0] ) + '?jschl_vc=%s&pass=%s&jschl_answer=%s' % (get_data['jschl_vc'], get_data['pass'], get_data['jschl_answer'])
                        verUrl = _getFullUrl2( verUrl )
                        params2 = dict(params)
                        params2['load_cookie'] = True
                        params2['save_cookie'] = True
                        params2['header'] = dict(params.get('header', {}))
                        params2['header'].update({'Referer':url, 'User-Agent':cfParams.get('User-Agent', ''), 'Accept-Encoding':'text'})
                        printDBG("Time spent: [%s]" % (time.time() - start_time))
                        if current == 1:
                            GetIPTVSleep().Sleep(1 + (decoded['timeout'] / 1000.0)-(time.time() - start_time))
                        else:
                            GetIPTVSleep().Sleep((decoded['timeout'] / 1000.0))
                        printDBG("Time spent: [%s]" % (time.time() - start_time))
                        printDBG("Timeout: [%s]" % decoded['timeout'])
                        sts, data = self.getPage(verUrl, params2, post_data)
                except Exception:
                    printExc()
                    break
            else:
                break
        return sts, data
    
    def saveWebFileWithPyCurl(self, file_path, url, add_params = {}, post_data = None):
        bRet = False
        downDataSize = 0
        
        add_params['with_metadata'] = True
        add_params['save_to_file'] = file_path
        if 'maintype' in add_params:
            add_params['check_maintype'] = add_params.pop('maintype')
        if 'subtypes' in add_params:
            add_params['check_subtypes'] = add_params.pop('subtypes')
        
        sts, data = self.getPageWithPyCurl(url, add_params, post_data)
        if sts:
            downDataSize = data.meta['size_download']
        else:
            rm(file_path)
        return {'sts': sts, 'fsize': downDataSize}
    
    def saveWebFile(self, file_path, url, addParams = {}, post_data = None):
        addParams = dict(addParams)
        
        outParams, postData = self.getParamsFromUrlWithMeta(url)
        addParams.update(outParams)
        if 'header' not in addParams and 'host' not in addParams:
            host = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
            header = {'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
            addParams['header'] = header
        addParams['return_data'] = False
        
        # if curl should and can be used
        if self.usePyCurl():
            return self.saveWebFileWithPyCurl(file_path, url, addParams, post_data)
    
        bRet = False
        downDataSize = 0
        dictRet = {}
        try:
            sts, downHandler = self.getPage(url, addParams, post_data)

            if addParams.get('ignore_content_length', False):
                meta = downHandler.info()
                contentLength = int(meta.getheaders("Content-Length")[0])
            else:
                contentLength = None
            
            checkFromFirstBytes = addParams.get('check_first_bytes', [])
            OK = True
            if 'maintype' in addParams and addParams['maintype'] != downHandler.headers.maintype:
                printDBG("common.getFile wrong maintype! requested[%r], retrieved[%r]" % (addParams['maintype'], downHandler.headers.maintype))
                if 0 == len(checkFromFirstBytes):
                    downHandler.close()
                OK = False
            
            if OK and 'subtypes' in addParams:
                OK = False
                for item in addParams['subtypes']:
                    if item == downHandler.headers.subtype:
                        OK = True
                        break
            
            if OK or len(checkFromFirstBytes):
                blockSize = addParams.get('block_size', 8192)
                fileHandler = None
                while True:
                    buffer = downHandler.read(blockSize)
                    
                    if len(checkFromFirstBytes):
                        OK = False
                        for item in checkFromFirstBytes:
                            if buffer.startswith(item):
                                OK = True
                                break
                        if not OK:
                            break
                        else:
                            checkFromFirstBytes = []
                    
                    if not buffer:
                        break
                    downDataSize += len(buffer)
                    if len(buffer):
                        if fileHandler == None:
                            fileHandler = file(file_path, "wb")
                        fileHandler.write(buffer)
                if fileHandler != None:
                    fileHandler.close()
                downHandler.close()
                if None != contentLength:
                    if contentLength == downDataSize:
                        bRet = True
                elif downDataSize > 0:
                    bRet = True
        except Exception:
            printExc("common.getFile download file exception")
        dictRet.update( {'sts': bRet, 'fsize': downDataSize} )
        return dictRet
    
    def getURLRequestData(self, params = {}, post_data = None):
        
        def urlOpen(req, customOpeners, timeout):
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                if timeout != None:
                    response = opener.open(req, timeout=timeout)
                else:
                    response = opener.open(req)
            else:
                if timeout != None:
                    response = urllib2.urlopen(req, timeout=timeout)
                else:
                    response = urllib2.urlopen(req)
            return response
        
        if IsMainThread():
            msg1 = _('It is not allowed to call getURLRequestData from main thread.')
            msg2 = _('You should never perform block I/O operations in the __init__.')
            GetIPTVNotify().push('\s'.join([msg1, msg2]), 'error', 40)
            raise Exception("Wrong usage!")
        
        if not self.useMozillaCookieJar:
            cj = cookielib.LWPCookieJar()
        else:
            cj = cookielib.MozillaCookieJar()
        response = None
        req      = None
        out_data = None
        opener   = None
        self.metadataFromLastRequest = {}
        metadata = self.metadataFromLastRequest
        
        timeout = params.get('timeout', None)
        
        if 'host' in params:
            host = params['host']
        else:
            host = self.HOST

        if 'header' in params:
            headers = params['header']
        elif None != self.HEADER:
            headers = self.HEADER
        else:
            headers = { 'User-Agent' : host }
            
        if 'User-Agent' not in headers:
            headers['User-Agent'] = host
        
        printDBG('pCommon - getURLRequestData() -> params: ' + str(params))
        printDBG('pCommon - getURLRequestData() -> headers: ' + str(headers)) 

        customOpeners = []
        #cookie support
        if 'use_cookie' not in params and 'cookiefile' in params and ('load_cookie' in params or 'save_cookie' in params):
            params['use_cookie'] = True 
        
        if params.get('use_cookie', False):
            if params.get('load_cookie', False):
                try:
                    cj.load(params['cookiefile'], ignore_discard = True)
                except IOError:
                    printDBG('Cookie file [%s] not exists' % params['cookiefile'])
                except Exception:
                    printExc()
            try:
                for cookieKey in params.get('cookie_items', {}).keys():
                    printDBG("cookie_item[%s=%s]" % (cookieKey, params['cookie_items'][cookieKey]))
                    cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=params['cookie_items'][cookieKey], port=None, port_specified=False, domain='', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                    cj.set_cookie(cookieItem)
            except Exception:
                printExc()
            customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
            
        if params.get('no_redirection', False):
            customOpeners.append( NoRedirection() )
        
        # debug 
        #customOpeners.append(urllib2.HTTPSHandler(debuglevel=1))
        #customOpeners.append(urllib2.HTTPHandler(debuglevel=1))
        if not IsHttpsCertValidationEnabled():
            try:
                if params.get('ssl_protocol', None) != None:
                    ctx = ssl._create_unverified_context(params['ssl_protocol'])
                else:
                    ctx = ssl._create_unverified_context()
                customOpeners.append(urllib2.HTTPSHandler(context=ctx))
            except Exception: pass
        elif params.get('ssl_protocol', None) != None:
            ctx = ssl.SSLContext(params['ssl_protocol'])
            customOpeners.append(urllib2.HTTPSHandler(context=ctx))
        
        #proxy support
        if self.useProxy:
            http_proxy = self.proxyURL
        else:
            http_proxy = ''
        #proxy from parameters (if available) overwrite default one
        if 'http_proxy' in params:
            http_proxy = params['http_proxy']
        if '' != http_proxy:
            printDBG('getURLRequestData USE PROXY')
            customOpeners.append( urllib2.ProxyHandler({"http":http_proxy}) )
            customOpeners.append( urllib2.ProxyHandler({"https":http_proxy}) )
        
        pageUrl = params['url']
        proxy_gateway = params.get('proxy_gateway', '')
        if proxy_gateway != '':
            pageUrl = proxy_gateway.format(urllib.quote_plus(pageUrl, ''))
        printDBG("pageUrl: [%s]" % pageUrl)

        if None != post_data:
            printDBG('pCommon - getURLRequestData() -> post data: ' + str(post_data))
            if params.get('raw_post_data', False):
                dataPost = post_data
            elif params.get('multipart_post_data', False):
                customOpeners.append( MultipartPostHandler() )
                dataPost = post_data
            else:
                dataPost = urllib.urlencode(post_data)
            req = urllib2.Request(pageUrl, dataPost, headers)
        else:
            req = urllib2.Request(pageUrl, None, headers)

        if not params.get('return_data', False):
            out_data = urlOpen(req, customOpeners, timeout)
        else:
            gzip_encoding = False
            try:
                response = urlOpen(req, customOpeners, timeout)
                if response.info().get('Content-Encoding') == 'gzip':
                    gzip_encoding = True
                try: 
                    metadata['url'] = response.geturl()
                    metadata['status_code'] = response.getcode()
                    if 'Content-Type' in response.info(): metadata['content-type'] = response.info()['Content-Type']
                except Exception: pass
                
                data = response.read()
                response.close()
            except urllib2.HTTPError, e:
                ignoreCodeRanges = params.get('ignore_http_code_ranges', [(404, 404), (500, 500)])
                ignoreCode = False
                metadata['status_code'] = e.code
                for ignoreCodeRange in ignoreCodeRanges:
                    if e.code >= ignoreCodeRange[0] and e.code <= ignoreCodeRange[1]:
                        ignoreCode = True
                        break
                
                if ignoreCode:
                    printDBG('!!!!!!!! %s: getURLRequestData - handled' % e.code)
                    if e.fp.info().get('Content-Encoding', '') == 'gzip':
                        gzip_encoding = True
                    try: 
                        metadata['url'] = e.fp.geturl()
                        if 'Content-Type' in e.fp.info(): metadata['content-type'] = e.fp.info()['Content-Type']
                    except Exception: pass
                    data = e.fp.read()
                    #e.msg
                    #e.headers
                elif e.code == 503:
                    if params.get('use_cookie', False):
                        new_cookie = e.fp.info().get('Set-Cookie', '')
                        printDBG("> new_cookie[%s]" % new_cookie)
                        cj.save(params['cookiefile'], ignore_discard = True)
                    raise e
                else:
                    if e.code in [300, 302, 303, 307] and params.get('use_cookie', False) and params.get('save_cookie', False):
                        new_cookie = e.fp.info().get('Set-Cookie', '')
                        printDBG("> new_cookie[%s]" % new_cookie)
                        #for cookieKey in params.get('cookie_items', {}).keys():
                        #    cj.clear('', '/', cookieKey)
                        cj.save(params['cookiefile'], ignore_discard = True)
                    raise e
            try:
                if gzip_encoding:
                    printDBG('Content-Encoding == gzip')
                    buf = StringIO(data)
                    f = gzip.GzipFile(fileobj=buf)
                    out_data = f.read()
                else:
                    out_data = data
            except Exception as e:
                printExc()
                msg1 = _("Critical Error – Content-Encoding gzip cannot be handled!")
                msg2 = _("Last error:\n%s" % str(e))
                GetIPTVNotify().push('%s\n\n%s' % (msg1, msg2), 'error', 20)
                out_data = data
 
        if params.get('use_cookie', False) and params.get('save_cookie', False):
            try:
                cj.save(params['cookiefile'], ignore_discard = True)
            except Exception as e:
                printExc()
                msg1 = _("Critical Error – cookie can't be saved!")
                msg2 = _("Last error:\n%s" % str(e))
                msg3 = _("Please make sure that the folder for cache data (set in the configuration) is writable.")
                GetIPTVNotify().push('%s\n\n%s\n\n%s' % (msg1, msg2, msg3), 'error', 20)
                SetTmpCookieDir()
                raise e
        
        out_data, metadata = self.handleCharset(params, out_data, metadata)
        if params.get('with_metadata', False) and params.get('return_data', False):
            out_data = strwithmeta(out_data, metadata)
        
        return out_data 
        
    def handleCharset(self, params, data, metadata):
        try:
            if params.get('return_data', False) and params.get('convert_charset', True) :
                encoding = ''
                if 'content-type' in metadata:
                    encoding = self.ph.getSearchGroups(metadata['content-type'], '''charset=([A-Za-z0-9\-]+)''', 1, True)[0].strip().upper()
                
                if encoding == '' and params.get('search_charset', False):
                    encoding = self.ph.getSearchGroups(data, '''(<meta[^>]+?Content-Type[^>]+?>)''', ignoreCase=True)[0]
                    encoding = self.ph.getSearchGroups(encoding, '''charset=([A-Za-z0-9\-]+)''', 1, True)[0].strip().upper()
                if encoding not in ['', 'UTF-8']:
                    printDBG(">> encoding[%s]" % encoding)
                    try:
                        data = data.decode(encoding).encode('UTF-8')
                    except Exception:
                        printExc()
                    metadata['orig_charset'] = encoding
        except Exception:
            printExc()
        return data, metadata

    def urlEncodeNonAscii(self, b):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

    def iriToUri(self, iri):
        try:
            parts = urlparse(iri.decode('utf-8'))
            encodedParts = []
            for parti, part in enumerate(parts):
                newPart = part
                try:
                    if parti == 1: newPart = part.encode('idna')
                    else: newPart = self.urlEncodeNonAscii(part.encode('utf-8'))
                except Exception:
                    printExc()
                encodedParts.append(newPart)
            return urlunparse(encodedParts)
        except Exception:
            printExc()
        return iri

    def makeABCList(self, tab = ['0 - 9']):
        strTab = list(tab)
        for i in range(65,91):
            strTab.append(str(unichr(i)))    
        return strTab