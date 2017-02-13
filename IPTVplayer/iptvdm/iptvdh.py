# -*- coding: utf-8 -*-
#
#  IPTV download helper
#
#  $Id$
#
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetPluginDir
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import enum
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Directories import fileExists
import datetime
import os
import re
###################################################

class DMItemBase:
    def __init__(self, url, fileName):
        self.url = url
        
        self.fileName       = fileName
        self.tmpFileName    = ""

        self.fileSize = -1 
        self.downloadedSize = 0
        self.downloadedProcent = -1
        self.downloadedSpeed = 0
        self.totalFileDuration = -1
        self.downloadedFileDuration = -1
        
        self.status = DMHelper.STS.WAITING
        self.tries = DMHelper.DOWNLOAD_TYPE.INITIAL
        
        # instance of downloader
        self.downloader = None
        self.callback = None
    def __del__(self):
        printDBG("DMItemBase.__del__  ---------------------")

class DMHelper:
    STATUS_FILE_PATH = '/tmp/iptvdownload'
    STATUS_FILE_EXT = '.txt'
    
    STS = enum( WAITING     = 'STS_WAITING',
                DOWNLOADING = 'STS_DOWNLOADING',
                DOWNLOADED  = 'STS_DOWNLOADED',
                INTERRUPTED = 'STS_INTERRUPTED',
                ERROR       = 'STS_ERROR',
                POSTPROCESSING = 'STS_POSTPROCESSING')
    DOWNLOAD_TYPE = enum( INITIAL  = 'INIT_DOWNLOAD',
                          CONTINUE = 'CONTINUE_DOWNLOAD',
                          RETRY    = 'RETRY_DOWNLOAD' )
    #
    DOWNLOADER_TYPE = enum( WGET = 'WGET_DOWNLOADER',
                            F4F  = 'F4F_DOWNLOADER' )
                            
    HEADER_PARAMS = [{'marker':'Host=',             'name':'Host'},
                     {'marker':'Accept=',           'name':'Accept'},
                     {'marker':'Cookie=',           'name':'Cookie'},
                     {'marker':'Referer=',          'name':'Referer'},
                     {'marker':'User-Agent=',       'name':'User-Agent'},
                     {'marker':'Range=',            'name':'Range'},
                     {'marker':'Orgin=',            'name':'Orgin'},
                     {'marker':'Origin=',           'name':'Origin'},
                     {'marker':'X-Playback-Session-Id=',           'name':'X-Playback-Session-Id'},
                     {'marker':'If-Modified-Since=','name':'If-Modified-Since'},
                     {'marker':'If-None-Match=',    'name':'If-None-Match'},
                     {'marker':'X-Forwarded-For=',  'name':'X-Forwarded-For'}]
                     
    HANDLED_HTTP_HEADER_PARAMS = ['Host', 'Accept', 'Cookie', 'Referer', 'User-Agent', 'Range', 'Orgin', 'Origin', 'X-Playback-Session-Id', 'If-Modified-Since', 'If-None-Match', 'X-Forwarded-For']
    IPTV_DOWNLOADER_PARAMS = ['iptv_wget_continue', 'iptv_wget_timeout', 'iptv_wget_waitretry']
    
    @staticmethod
    def GET_PWGET_PATH():
        return GetPluginDir('iptvdm/pwget.py')
    
    @staticmethod
    def GET_WGET_PATH():
        return config.plugins.iptvplayer.wgetpath.value
    
    @staticmethod
    def GET_F4M_PATH():
        return config.plugins.iptvplayer.f4mdumppath.value
        
    @staticmethod
    def GET_HLSDL_PATH():
        return config.plugins.iptvplayer.hlsdlpath.value
    
    @staticmethod
    def GET_RTMPDUMP_PATH():
        return config.plugins.iptvplayer.rtmpdumppath.value

    @staticmethod
    def getDownloaderType(url):
        if url.endswith(".f4m"):
            return DMHelper.DOWNLOADER_TYPE.F4F
        else:
            return DMHelper.DOWNLOADER_TYPE.WGET
        
    @staticmethod
    def getDownloaderCMD(downItem):
        if downItem.downloaderType == DMHelper.DOWNLOADER_TYPE.F4F:
            return DMHelper.getF4fCMD(downItem)
        else:
            return DMHelper.getWgetCMD(downItem)
        
    @staticmethod
    def makeUnikalFileName(fileName, withTmpFileName = True, addDateToFileName=False):
        # if this function is called
        # no more than once per second
        # date and time (with second)
        # is sufficient to provide a unique name
        from time import gmtime, strftime
        date = strftime("%Y-%m-%d_%H:%M:%S_", gmtime())
        
        if not addDateToFileName:
            tries = 10
            for idx in range(tries):
                if idx > 0:
                    uniqueID = str(idx+1) + '. '
                else: uniqueID = ''
                newFileName = os.path.dirname(fileName) + os.sep + uniqueID + os.path.basename(fileName)
                if fileExists(newFileName): continue
                if withTmpFileName: 
                    tmpFileName = os.path.dirname(fileName) + os.sep + "." + uniqueID + os.path.basename(fileName)
                    if fileExists(tmpFileName): continue
                    return newFileName, tmpFileName
                else:
                    return newFileName
                
        newFileName = os.path.dirname(fileName) + os.sep + date.replace(':', '.') + os.path.basename(fileName)
        if withTmpFileName:
            tmpFileName = os.path.dirname(fileName) + os.sep + "." + date.replace(':', '.') + os.path.basename(fileName)
            return newFileName, tmpFileName
        else:
            return newFileName
    
    @staticmethod
    def getProgressFromF4fSTSFile(file):
        ret = 0
        try:
            fo = open(file, "r")
            lines = fo.readlines()
            fo.close()
        except Exception:
            return ret
        if 0 < len(lines):
            match = re.search("|PROGRESS|([0-9]+?)/([0-9]+?)|" , lines[1])
            if match:
                ret = 100 * int(match.group(1)) / int(match.group(2))
        return ret
    
    @staticmethod
    def getFileSize(filename):
        try:
            st = os.stat(filename)
            ret = st.st_size
        except Exception:
            ret = -1
        return ret
        
    @staticmethod
    def getRemoteContentInfoByUrllib(url, addParams = {}):
        remoteContentInfo = {}
        addParams = DMHelper.downloaderParams2UrllibParams(addParams)
        addParams['return_data'] = False
        
        cm = common()
        # only request
        sts,response = cm.getPage(url, addParams)
        if sts:
            tmpInfo = response.info()
            remoteContentInfo = {'Content-Length': tmpInfo.get('Content-Length', -1), 'Content-Type': tmpInfo.get('Content-Type', '')}
        if response:
            try: response.close()
            except Exception: pass

        printDBG("getRemoteContentInfoByUrllib: [%r]" % remoteContentInfo)
        return sts,remoteContentInfo

    @staticmethod  
    def downloaderParams2UrllibParams(params):
        tmpParams = {}
        userAgent = params.get('User-Agent', '')
        if '' != userAgent: tmpParams['User-Agent'] = userAgent
        cookie = params.get('Cookie', '')
        if '' != cookie: tmpParams['Cookie'] = cookie
        
        if len(tmpParams) > 0:
            return {'header': tmpParams}
        else:
            return {}
            
    @staticmethod
    def getDownloaderParamFromUrlWithMeta(url, httpHeadersOnly=False):
        printDBG("DMHelper.getDownloaderParamFromUrlWithMeta url[%s], url.meta[%r]" % (url, url.meta))
        downloaderParams = {}
        for key in url.meta:
            if key in DMHelper.HANDLED_HTTP_HEADER_PARAMS:
                downloaderParams[key] = url.meta[key]
            elif key == 'http_proxy':
                downloaderParams[key] = url.meta[key]
        if not httpHeadersOnly:
            for key in DMHelper.IPTV_DOWNLOADER_PARAMS:
                if key in url.meta:
                    downloaderParams[key] = url.meta[key]
        return url, downloaderParams
    
    @staticmethod
    def getDownloaderParamFromUrl(url):
        if isinstance(url, strwithmeta):
            return DMHelper.getDownloaderParamFromUrlWithMeta(url)

        downloaderParams = {}
        paramsTab = url.split('|')
        url = paramsTab[0]
        del paramsTab[0]
        
        for param in DMHelper.HEADER_PARAMS:
            for item in paramsTab:
                if item.startswith(param['marker']):
                    downloaderParams[param['name']] = item[len(param['marker']):]

        # ugly workaround the User-Agent param should be passed in url
        if -1 < url.find('apple.com'):
            downloaderParams['User-Agent'] = 'QuickTime/7.6.2'
        
        return url,downloaderParams
        
    @staticmethod
    def getBaseWgetCmd(downloaderParams = {}):
        printDBG("getBaseWgetCmd downloaderParams[%r]" % downloaderParams)
        headerOptions = ''
        proxyOptions = ''
        
        defaultHeader = ' --header "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0" '
        for key, value in downloaderParams.items():
            if value != '':
                if key in DMHelper.HANDLED_HTTP_HEADER_PARAMS:
                    if 'Cookie' == key: headerOptions += ' --cookies=off '
                    headerOptions += ' --header "%s: %s" ' % (key, value)
                    if key == 'User-Agent': defaultHeader = ''
                elif key == 'http_proxy':
                    proxyOptions += ' -e use_proxy=yes -e http_proxy="%s" -e https_proxy="%s" ' % (value, value)
        
        wgetContinue = ''
        if downloaderParams.get('iptv_wget_continue', False):
            wgetContinue = ' -c --timeout=%s --waitretry=%s ' % (downloaderParams.get('iptv_wget_timeout', 30), downloaderParams.get('iptv_wget_waitretry', 1))
            
        cmd = DMHelper.GET_WGET_PATH() + wgetContinue + defaultHeader + ' --no-check-certificate ' + headerOptions + proxyOptions
        printDBG("getBaseWgetCmd return cmd[%s]" % cmd)
        return cmd
        
    @staticmethod
    def getBaseHLSDLCmd(downloaderParams = {}):
        printDBG("getBaseWgetCmd downloaderParams[%r]" % downloaderParams)
        headerOptions = ''
        proxyOptions = ''
        
        userAgent = ' -u "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0" '
        for key, value in downloaderParams.items():
            if value != '':
                if key in DMHelper.HANDLED_HTTP_HEADER_PARAMS:
                    if key == 'User-Agent':
                        userAgent = ' -u "%s" ' % value
                    else:
                        headerOptions += ' -h "%s: %s" ' % (key, value)
                elif key == 'http_proxy':
                    proxyOptions += ' -e use_proxy=yes -e http_proxy="%s" -e https_proxy="%s" ' % (value, value)
        
        cmd = DMHelper.GET_HLSDL_PATH() + ' -q -f -b ' + userAgent + headerOptions + proxyOptions
        printDBG("getBaseHLSDLCmd return cmd[%s]" % cmd)
        return cmd
