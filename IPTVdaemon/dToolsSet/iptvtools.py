# -*- coding: utf-8 -*-
#
#  IPTV Tools
#
#  $Id$
#
# 
###################################################
# LOCAL import
###################################################

###################################################
 
###################################################
# FOREIGN import
###################################################
from Components.config import config
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS, SCOPE_CONFIG
from enigma import eConsoleAppContainer
from Components.Language import language
from time import sleep as time_sleep, time
from urllib2 import Request, urlopen, URLError, HTTPError
from datetime import datetime
import urllib
import urllib2
import traceback
import re
import sys
import os
import stat
import codecs
try:    import json
except Exception: import simplejson as json
import datetime

###################################################
def DaysInMonth(dt):
    return (datetime.date(dt.year+(dt.month / 12), (dt.month % 12) + 1, 1) - dt).days + dt.day - 1
    
def NextMonth(dt):
    return (dt.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    
def PrevMonth(dt):
    return (dt.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    
def NextDay(dt):
    return (dt + datetime.timedelta(days=1))
    
def PrevDay(dt):
    return (dt - datetime.timedelta(days=1))

###################################################
def UsePyCurl():
    return config.plugins.iptvplayer.usepycurl.value

def GetIconsHash():
    iconsHashFile = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/PlayerSelector/hash.txt')
    sts, data = ReadTextFile(iconsHashFile)
    if sts: return data.strip()
    else: return ''

def SetIconsHash(value):
    iconsHashFile = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/PlayerSelector/hash.txt')
    return WriteTextFile(iconsHashFile, value)

def GetGraphicsHash():
    graphicsHashFile = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/hash.txt')
    sts, data = ReadTextFile(graphicsHashFile)
    if sts: return data.strip()
    else: return ''

def SetGraphicsHash(value):
    graphicsHashFile = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/hash.txt')
    return WriteTextFile(graphicsHashFile, value)

###################################################
def GetNice(pid=None):
    nice = 0
    if None == pid:
        pid = 'self'
    filePath = '/proc/%s/stat' % pid
    try:
        with open(filePath, 'r') as f:
            data = f.read()
            data = data.split(' ')[19]
            nice = int(data)
    except Exception:
        printExc()
    return nice
    
def E2PrioFix(cmd):
    if '/duk' not in cmd and config.plugins.iptvplayer.plarform.value in ('mipsel', 'armv7', 'armv5t'):
        return 'nice -n %d %s' % (GetNice()+2, cmd)
    else:
        return cmd
    
def GetDefaultLang(full=False):
    if full:
        try: defaultLanguage = language.getActiveLanguage()
        except Exception:
            printExc()
            defaultLanguage = 'en_EN' 
    else:
        try: defaultLanguage = language.getActiveLanguage().split('_')[0]
        except Exception:
            printExc()
            defaultLanguage = 'en'
    return defaultLanguage
    
def GetPolishSubEncoding(filePath):
    encoding = 'utf-8'
    # Method provided by @areq: http://forum.dvhk.to/showpost.php?p=5367956&postcount=5331
    try:
        f = open(filePath)
        sub = f.read()
        f.close()
        iso = 0
        for i in (161, 166, 172, 177, 182, 188):
            iso += sub.count(chr(i))
        win = 0
        for i in (140, 143, 156, 159, 165, 185):
            win += sub.count(chr(i))
        utf = 0
        for i in (195, 196, 197):
            utf += sub.count(chr(i))
        if win > utf and win > iso:
            encoding = "CP1250"
        elif utf > iso and utf > win:
            encoding = "utf-8"
        else:
            encoding = "iso-8859-2"
        printDBG("IPTVExtMoviePlayer _getEncoding iso[%d] win[%d ] utf[%d] -> [%s]" % (iso, win, utf, encoding))
    except Exception:
        printExc()
    return encoding
    
def MapUcharEncoding(encoding):
    ENCODING_MAP = {'X-MAC-CYRILLIC':"MAC-CYRILLIC"}
    printDBG("MapUcharEncoding in encoding[%s]" % encoding)
    try: encoding = ENCODING_MAP.get(encoding.strip().upper(), encoding.strip())
    except Exception: printExc()
    printDBG("MapUcharEncoding out encoding[%s]" % encoding)
    return encoding

class eConnectCallbackObj:
    OBJ_ID = 0
    OBJ_NUM = 0
    def __init__(self, obj=None, connectHandler=None):
        #eConnectCallbackObj.OBJ_ID += 1
        #eConnectCallbackObj.OBJ_NUM += 1
        self.objID = eConnectCallbackObj.OBJ_ID
        #printDBG("eConnectCallbackObj.__init__ objID[%d] OBJ_NUM[%d]" % (self.objID, eConnectCallbackObj.OBJ_NUM))
        self.connectHandler = None #connectHandler
        self.obj = None #obj
    
    def __del__(self):
        eConnectCallbackObj.OBJ_NUM -= 1
        printDBG("eConnectCallbackObj.__del__ objID[%d] OBJ_NUM[%d] " % (self.objID, eConnectCallbackObj.OBJ_NUM))
        try:
            if 'connect' not in dir(self.obj):
                if 'get' in dir(self.obj):
                    self.obj.get().remove(self.connectHandler)
                else:
                    self.obj.remove(self.connectHandler)
            else:
                del self.connectHandler
        except Exception:
            printExc()
        self.connectHandler = None
        self.obj = None

def eConnectCallback(obj, callbackFun, withExcept=False):
    return None
    try:
        if 'connect' in dir(obj):
            return eConnectCallbackObj(obj, obj.connect(callbackFun))
        else:
            if 'get' in dir(obj):
                obj.get().append(callbackFun)
            else:
                obj.append(callbackFun)
            return eConnectCallbackObj(obj, callbackFun)
    except Exception:
        printExc("eConnectCallback")
    return eConnectCallbackObj()
    
class iptv_system:
    '''
    Calling os.system is not recommended, it may fail due to lack of memory,
    please use iptv_system instead, this should be used as follow:
    self.handle = iptv_system("cmd", callBackFun)
    there is need to have reference to the obj created by iptv_system, 
    other ways behaviour is undefined
    
    iptv_system must be used only inside MainThread context, please see 
    iptv_execute class from asynccall module which is dedicated to be
    used inside other threads
    '''
    def __init__(self, cmd, callBackFun=None):
        printDBG("iptv_system.__init__ ---------------------------------")
        self.outData = popen(cmd)
        callBackFun(0, self.outData)
        
    def terminate(self, doCallBackFun=False):
        pass
        
    def kill(self, doCallBackFun=False):
        pass

    def _dataAvail(self, data):
        pass

    def _cmdFinished(self, code):
        pass

    def __del__(self):
        printDBG("iptv_system.__del__ ---------------------------------")

def IsHttpsCertValidationEnabled():
    return config.plugins.iptvplayer.httpssslcertvalidation.value
    
def IsWebInterfaceModuleAvailable(chekInit=False):
    if chekInit:
        file = '__init__'
    else:
        file = 'initiator'
    if (fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/Web/%s.py'  % file)) or
        fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/Web/%s.pyo' % file)) or
        fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/Web/%s.pyc' % file))):
        return True
    else:
        return False
    
def GetAvailableIconSize(checkAll=True):
    return 0
    
#############################################################
# returns the directory path where specified resources are
# stored, in the future, it can be changed in the config
#############################################################
def GetLogoDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/') + file
    
def GetPyScriptCmd(name):
    cmd = ''
    baseName = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/scripts/') + name
    if fileExists(baseName + '.py'):
        baseName += '.py'
    elif fileExists(baseName + '.pyo'):
        baseName += '.pyo'
    if baseName != '':
        for item in ['python', 'python2.7', 'python2.6']:
            pyPath = Which(item)
            if '' != pyPath:
                cmd = '%s %s' % (pyPath, baseName)
                break
    return cmd

def GetJSScriptFile(file):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/jsscripts/') + file

def GetUchardetPath():
    return config.plugins.iptvplayer.uchardetpath.value
    
def GetCmdwrapPath():
    return config.plugins.iptvplayer.cmdwrappath.value
    
def GetDukPath():
    return config.plugins.iptvplayer.dukpath.value

gIPTVPlayerTempCookieDir = None
def SetTmpCookieDir():
    global gIPTVPlayerTempCookieDir
    for cookiePath in ['/tmp', '/storage/emulated/o/Android/data/org.xbmc.kodi/files/.kodi/temp']:
        if os.path.isdir(cookiePath):
            gIPTVPlayerTempCookieDir = cookiePath + '/iptvplayer_cookies/'
            break
    mkdirs(gIPTVPlayerTempCookieDir)
    
def ClearTmpCookieDir():
    global gIPTVPlayerTempCookieDir
    if gIPTVPlayerTempCookieDir != None:
        try:
            for file in os.listdir( gIPTVPlayerTempCookieDir ):
                rm(gIPTVPlayerTempCookieDir + '/' + file)
        except Exception:
            printExc()
    
    gIPTVPlayerTempCookieDir = None
    
def GetCookieDir(file = ''):
    global gIPTVPlayerTempCookieDir
    if gIPTVPlayerTempCookieDir == None: cookieDir = config.plugins.iptvplayer.SciezkaCache.value + '/cookies/'
    else: cookieDir = gIPTVPlayerTempCookieDir
    try:
        if not os.path.isdir(cookieDir):
            mkdirs(cookieDir)
    except Exception: printExc()
    return cookieDir + file

###########################
gE2iPlayerTempJSCache = None
def SetTmpJSCacheDir():
    global gE2iPlayerTempJSCache
    gE2iPlayerTempJSCache = '/tmp/e2iplayer_js_cache/'
    mkdirs(gE2iPlayerTempJSCache)

def ClearTmpJSCacheDir():
    global gE2iPlayerTempJSCache
    if gE2iPlayerTempJSCache != None:
        try:
            for file in os.listdir( gE2iPlayerTempJSCache ):
                rm(gE2iPlayerTempJSCache + '/' + file)
        except Exception:
            printExc()
    gE2iPlayerTempJSCache = None

def TestTmpJSCacheDir():
    path = GetJSCacheDir(forceFromConfig=True)
    if not os.path.isdir(path):
        mkdirs(path, True)
    with open(path + ".rw_test", 'w') as f:
        f.write("test")

def GetJSCacheDir(file = '', forceFromConfig=False):
    global gE2iPlayerTempJSCache
    if gE2iPlayerTempJSCache == None or forceFromConfig: cookieDir = config.plugins.iptvplayer.SciezkaCache.value + '/JSCache/'
    else: cookieDir = gE2iPlayerTempJSCache
    try:
        if not os.path.isdir(cookieDir):
            mkdirs(cookieDir)
    except Exception: printExc()
    return cookieDir + file
##############################

def GetTmpDir(file = ''):
    path = config.plugins.iptvplayer.NaszaTMP.value
    path = path.replace('//', '/')
    try: mkdirs(path)
    except Exception: printExc()
    return path + '/' + file
    
def CreateTmpFile(filename, data=''):
    sts = False
    filePath = GetTmpDir(filename)
    try:
        with open(filePath, 'w') as f:
            f.write(data)
            sts = True
    except Exception:
        printExc()
    return sts, filePath
    
def GetCacheSubDir(dir, file = ''):
    path = config.plugins.iptvplayer.SciezkaCache.value + "/" + dir
    path = path.replace('//', '/')
    try: mkdirs(path)
    except Exception: printExc()
    return path + '/' + file

def GetSearchHistoryDir(file = ''):
    return GetCacheSubDir('SearchHistory', file)
    
def GetFavouritesDir(file = ''):
    return GetCacheSubDir('IPTVFavourites', file)
    
def GetSubtitlesDir(file = ''):
    return GetCacheSubDir('Subtitles', file)
    
def GetMovieMetaDataDir(file = ''):
    return GetCacheSubDir('MovieMetaData', file)

def GetIPTVDMImgDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/') + file
def GetIconDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/') + file
def GetBinDir(file = '', platform=None):
    if None == platform: platform = config.plugins.iptvplayer.plarform.value
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/bin/') + platform + '/' + file
def GetPluginDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/') + file
def GetSkinsDir(path = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/skins/') + path
def GetConfigDir(path = ''):
    return resolveFilename(SCOPE_CONFIG, path)
def IsExecutable(fpath):
    try:
        if '' != Which(fpath): return True
    except Exception: printExc()
    return False
    
def Which(program):
    try:
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
    except Exception: printExc()
    return ''
#############################################################
# class used to auto-select one link when video has several 
# links with different qualities
#############################################################
class CSelOneLink():

    def __init__(self, listOfLinks, getQualiyFun, maxRes):
       self.listOfLinks = listOfLinks
       self.getQualiyFun = getQualiyFun
       self.maxRes = maxRes
       
    def _cmpLinks(self, item1, item2):
        val1 = self.getQualiyFun(item1)
        val2 = self.getQualiyFun(item2)
        if val1 < val2:   ret = -1
        elif val1 > val2: ret = 1
        else:             ret = 0
        return ret
        
    def _cmpLinksBest(self, item1, item2):
        return -1 * self._cmpLinks(item1, item2)
        
    def getBestSortedList(self):
        printDBG('getBestSortedList')
        sortList = self.listOfLinks[::-1]
        sortList.sort( self._cmpLinksBest )
        retList = []
        tmpList = []
        for item in sortList:
            linkRes = self.getQualiyFun( item )
            if linkRes <= self.maxRes:
                retList.append(item)
            else:
                tmpList.insert(0, item)
        retList.extend(tmpList)
        return retList
        
    def getSortedLinks(self, defaultFirst=True):
        printDBG('getSortedLinks defaultFirst[%r]' % defaultFirst)
        sortList = self.listOfLinks[::-1]
        sortList.sort( self._cmpLinks )
        if len(self.listOfLinks) < 2 or None == self.maxRes:
            return self.listOfLinks
        
        if defaultFirst:
            # split links to two groups 
            # first gorup will meet maxRes
            # second group not
            group1 = []
            group2 = []
            for idx in range(len(self.listOfLinks)):
                if  self.getQualiyFun( self.listOfLinks[idx] ) <= self.maxRes:
                    group1.append(self.listOfLinks[idx])
                else:
                    group2.append(self.listOfLinks[idx])
            group1.sort( self._cmpLinks )
            group1.reverse()
            group2.sort( self._cmpLinks )
            group1.extend(group2)
            return group1
        
        defIdx = -1
        for idx in range(len(sortList)):
            linkRes = self.getQualiyFun( sortList[idx] )
            printDBG("=============== getOneLink [%r] res[%r] maxRes[%r]" % (sortList[idx], linkRes, self.maxRes))
            if linkRes <= self.maxRes:
                defIdx = idx
                printDBG('getOneLink use format %d/%d' % (linkRes, self.maxRes) )
                
        if defaultFirst and -1 < defIdx:
            item = sortList[defIdx]
            del sortList[defIdx]
            sortList.insert(0, item)
        return sortList
            
    def getOneLink(self):
        printDBG('getOneLink start')
        tab = self.getSortedLinks()
        if len(tab) == 0:
            return tab
        return [ tab[0] ]
# end CSelOneLink

#############################################################
# processing daemon commands
#############################################################
def getCMD(cmdFileName):
    cmd = ''
    if os.path.exists(cmdFileName):
	try:
	    f = open(cmdFileName, 'r')
	    cmd = f.readline().strip()
	    f.close
	    os.remove(cmdFileName)
	except Exception:
	    pass
    return cmd

#############################################################
# prints logs to the file(s)
#############################################################
# debugs
def clearLogsPaths():
    currTime   = datetime.now()
    if os.access('/media/hdd', os.W_OK):
        logPath='/media/hdd'
    else:
        logPath='/tmp'
    try:
        with open('%s/IPTVdaemon.log' % logPath, 'w') as f:
            f.write('=== IPTV daemon starts %s ===\n' % datetime.now() )
            f.close
        with open('%s/neutrinoIPTV.log' % logPath, 'w') as f:
            f.write('=== neutrinoIPTV starts %s ===\n' %datetime.now() )
            f.close
        with open('%s/neutrinoIPTV.err' % logPath, 'w') as f:
            f.write('=== neutrinoIPTV starts %s ===\n' %datetime.now() )
            f.close
    except Exception:
        pass

def logDaemon( text = ''):
    try:
        f = open(os.path.join(config.plugins.iptvplayer.NaszaTMP.value,'IPTVdaemon.log'), 'a')
        f.write(text + '\n')
        f.close
    except Exception:
        pass
  

def dumpclean(obj):
    tmptext=""
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                tmptext += k + ", "
                dumpclean(v)
            else:
                tmptext += "%s : %s\n" % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                tmptext += v + ", "
    else:
        tmptext += obj
    return "dumpclean:[" + tmptext + "]\n"

def getDebugMode():
    DBG=''
    try:
        from Components.config import config
        DBG = config.plugins.iptvplayer.debugprint.value
    except Exception:
        file = open(resolveFilename(SCOPE_CONFIG, "settings"))
        for line in file:
            if line.startswith('config.plugins.iptvplayer.debugprint=' ) :
                DBG=line.split("=")[1].strip()
                break
    return DBG

def printDBG( DBGtxt ):
    try:
        f = open(os.path.join(config.plugins.iptvplayer.NaszaTMP.value,'iptv.dbg'), 'a')
        f.write( dumpclean(DBGtxt) )
        f.close
    except Exception:
        try:
            msg = '%s' % traceback.format_exc()
            f = open(os.path.join(config.plugins.iptvplayer.NaszaTMP.value,'iptv.dbg'), 'a')
            f.write(msg + '\n')
            f.close
        except Exception:
            pass

#####################################################
# get host list based on files in /hosts folder
#####################################################
def GetHostsList(fromList=True, fromHostFolder=True):
    #j00zek we always build the list based on folder, so functions options are just for compatibility :)
    printDBG('getHostsList begin')
    HOST_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/hosts/')
    BLOCKED_MARKER = '_blocked_'  
    lhosts = [] 
    
    def __isHostNameValid(hostName):
        if len(hostName) > 4 and BLOCKED_MARKER not in hostName and hostName.startswith("host"):
            return True
        return False
    
    try:
        fileList = os.listdir( HOST_PATH )
        for wholeFileName in fileList:
            # separate file name and file extension
            fileName, fileExt = os.path.splitext(wholeFileName)
            nameLen = len( fileName )
            if fileExt in ['.pyo', '.pyc', '.py'] and nameLen >  4 and __isHostNameValid(fileName):
                if fileName[4:] not in lhosts:
                    lhosts.append( fileName[4:] )
                    printDBG('getHostsList add host with fileName: "%s"' % fileName[4:])
        printDBG('getHostsList end')
        lhosts.sort()
    except Exception:
        printDBG('GetHostsList EXCEPTION')
    return lhosts
    
def GetHostsAliases():
    ret = {}
    try:
        HOST_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/hosts/')
        sts, data = ReadTextFile(HOST_PATH + '/aliases.txt')
        if sts:
            data = byteify(json.loads(data), '', True)
            ret = dict(data)
    except Exception:
        printExc()
    return ret

def GetEnabledHostsList():
    hostsList = GetHostsList(fromList=True, fromHostFolder=True)
    enabledHostsList = []
    for hostName in hostsList:
        if IsHostEnabled(hostName):
            enabledHostsList.append(hostName)
    return enabledHostsList
    
def SortHostsList(hostsList):
    hostsList = list(hostsList)
    hostsOrderList = GetHostsOrderList()
    sortedList = []
    for item in hostsOrderList:
        if item in hostsList: 
            sortedList.append(item)
            hostsList.remove(item)
    sortedList.extend(hostsList)
    return sortedList

def SaveHostsOrderList(list, fileName="iptvplayerhostsorder"):
    printDBG('SaveHostsOrderList begin')
    fname = GetConfigDir(fileName)
    try:
        f = open(fname, 'w')
        for item in list:
            f.write(item + '\n')
        f.close()
    except Exception:
        pass #printExc()
    
def GetHostsOrderList(fileName="iptvplayerhostsorder"):
    printDBG('GetHostsOrderList begin')
    fname = GetConfigDir(fileName)
    list = []
    try:
        if fileExists(fname):
            with open(fname, 'r') as f:
                content = f.readlines()
            for item in content:
                item = item.strip()
                if len(item): list.append(item)
        else:
            printDBG('GetHostsOrderList file[%s] not exists' % fname)
    except Exception:
        pass #printExc()
    return list

def GetSkinsList():
    skins = []
    skins.insert(0,("Default", "Default"))
    return skins
    
def IsHostEnabled( hostName ):
    hostEnabled  = False
    try:
        exec('if config.plugins.iptvplayer.host' + hostName + '.value: hostEnabled = True')
    except Exception:
        hostEnabled = False
    return hostEnabled

##############################################################
# check if we have enough free space
# if required == None return free space instead of comparing
# default unit = MB
##############################################################
def FreeSpace(katalog, requiredSpace, unitDiv=1024*1024):
    try:
        s = os.statvfs(katalog)
        freeSpace = s.f_bfree * s.f_frsize # all free space
        if 512 > (freeSpace / (1024 * 1024)):
            freeSpace = s.f_bavail * s.f_frsize
        freeSpace = freeSpace / unitDiv
    except Exception:
        printExc()
        freeSpace = -1
    printDBG("FreeSpace freeSpace[%s] requiredSpace[%s] unitDiv[%s]" % (freeSpace, requiredSpace, unitDiv))
    if None == requiredSpace:
        return freeSpace
    else:    
        if freeSpace >= requiredSpace:
            return True
        else:
            return False

def IsValidFileName(name, NAME_MAX=255):
    prohibited_characters = ['/', "\000", '\\', ':', '*', '<', '>', '|', '"']
    if isinstance(name, basestring) and (1 <= len(name) <= NAME_MAX):
        for it in name:
            if it in prohibited_characters:
                return False
        return True
    return False
    
def RemoveDisallowedFilenameChars(name, replacment='.'):
    prohibited_characters = ['/', "\000", '\\', ':', '*', '<', '>', '|', '"']
    for item in prohibited_characters:
        name = name.replace(item, replacment).replace(replacment+replacment, replacment)
    return name
        
def touch(fname, times=None):
    try:
        with open(fname, 'a'):
            os.utime(fname, times)
        return True
    except Exception:
        printExc()
        return False
        
        
def mkdir(newdir):
    """ Wrapper for the os.mkdir function
        returns status instead of raising exception
    """
    try:
        os.mkdir(newdir)
        sts = True
        msg = 'Katalog "%s" został utworzony poprawnie.' % newdir
    except Exception:
        sts = False
        msg = 'Katalog "%s" nie może zostać utworzony.' % newdir
        printExc()
    return sts,msg

def mkdirs(newdir):
    """ Create a directory and all parent folders.
        Features:
        - parent directories will be created
        - if directory already exists, then do nothing
        - if there is another filsystem object with the same name, raise an exception
    """
    printDBG('mkdirs: "%s"' % newdir)
    try:
        if os.path.isdir(newdir):
            pass
        elif os.path.isfile(newdir):
            raise OSError("cannot create directory, file already exists: '%s'" % newdir)
        else:
            head, tail = os.path.split(newdir)
            if head and not os.path.isdir(head) and not os.path.ismount(head) and not os.path.islink(head):
                mkdirs(head)
            if tail:
                os.mkdir(newdir)
        return True
    except Exception:
        printExc('!!!!!!!!!! EXCEPTION mkdirs["%s"]' % newdir)
        return False
        
def rm(fullname):
    try:
        os.remove(fullname)
        return True
    except Exception: printExc()
    return False

def rmtree(path, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree.
    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info(). If ignore_errors
    is false and onerror is None, an exception is raised.
    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    try:
        if os.path.islink(path):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call rmtree on a symbolic link")
    except OSError:
        onerror(os.path.islink, path)
        # can't continue even if onerror hook returns
        return
    names = []
    try:
        names = os.listdir(path)
    except os.error, err:
        onerror(os.listdir, path)
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error, err:
                onerror(os.remove, fullname)
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path) 
       
def GetFileSize(filepath):
    try:
        return os.stat(filepath).st_size
    except Exception:
        return -1
       
def DownloadFile(url, filePath):
    printDBG('DownloadFile [%s] from [%s]' % (filePath, url) )
    try:
        downloadFile = urllib2.urlopen(url)
        output = open(filePath, 'wb')
        output.write(downloadFile.read())
        output.close()
        try:
            iptv_system('sync')
        except Exception:
            printExc('DownloadFile sync exception')
        return True
    except Exception:
        try:
            if os.path.exists(filePath):
                os.remove(filePath)
            return False
        except Exception:
            printExc()
            return False

########################################################
#                     For icon manager
########################################################  
def GetLastDirNameFromPath(path):
    path = os.path.normcase(path)
    if path[-1] == '/':
        path = path[:-1]
    dirName = path.split('/')[-1]
    return dirName

def GetIconDirBaseName():
    return '.iptvplayer_icons_'
    
def CheckIconName(name):
    #check if name is correct 
    if 36 == len(name) and '.jpg' == name[-4:]:
        try:
            tmp = int(name[:-4], 16)
            return True
        except Exception:
            pass
    return False

def GetNewIconsDirName():
    return "%s%f" % (GetIconDirBaseName(), float(time()))

def CheckIconsDirName(path):
    dirName = GetLastDirNameFromPath(path)
    baseName = GetIconDirBaseName()
    if dirName.startswith(baseName):
        try:
            test = float(dirName[len(baseName):])
            return True
        except Exception:
            pass
    return False
    
def GetIconsDirs(basePath):
    iconsDirs = []
    try:
        list = os.listdir(basePath)
        for item in list:
            currPath = os.path.join(basePath, item)
            if os.path.isdir(currPath) and not os.path.islink(currPath) and CheckIconsDirName(item):
                iconsDirs.append(item)
    except Exception:
        printExc()
    return iconsDirs
    
def GetIconsFilesFromDir(basePath):
    iconsFiles = []
    if CheckIconsDirName(basePath):
        try:
            list = os.listdir(basePath)
            for item in list:
                currPath = os.path.join(basePath, item)
                if os.path.isfile(currPath) and not os.path.islink(currPath) and CheckIconName(item):
                    iconsFiles.append(item)
        except Exception:
            printExc()
    
    return iconsFiles
    
def GetCreationIconsDirTime(fullPath):
    try:
        dirName    = GetLastDirNameFromPath(fullPath)
        baseName   = GetIconDirBaseName()
        return float(dirName[len(baseName):])
    except Exception:
        return None
        
def GetCreateIconsDirDeltaDateInDays(fullPath):
    ret = -1
    createTime = GetCreationIconsDirTime(fullPath)
    if None != createTime:
        try:
            currTime   = datetime.now()
            modTime    = datetime.fromtimestamp(createTime)
            deltaTime  = currTime - modTime
            ret = deltaTime.days
        except Exception:
            printExc()
    return ret
    
def RemoveIconsDirByPath(path):
    printDBG("RemoveIconsDirByPath[%s]" % path)
    RemoveAllFilesIconsFromPath(path)
    try:
        os.rmdir(path)
    except Exception:
        printExc('RemoveIconsDirByPath dir[%s] is not empty' % path) 
    
def RemoveOldDirsIcons(path, deltaInDays='7'):
    deltaInDays = int(deltaInDays)
    try:
        iconsDirs = GetIconsDirs(path)
        for item in iconsDirs:
            currDir = os.path.join(path, item)
            delta = GetCreateIconsDirDeltaDateInDays(currDir) # we will check only directory date
            if delta >= 0 and deltaInDays >= 0 and delta >= deltaInDays:
                RemoveIconsDirByPath(currDir)
    except Exception:
        printExc()

def RemoveAllFilesIconsFromPath(path):
    printDBG( "RemoveAllFilesIconsFromPath" )
    try:
        list = os.listdir(path)
        for item in list:
            filePath = os.path.join(path, item)
            if CheckIconName(item) and os.path.isfile(filePath):
                printDBG( 'RemoveAllFilesIconsFromPath img: ' + filePath )
                try:
                    os.remove(filePath)
                except Exception:
                    printDBG( "ERROR while removing file %s" % filePath )
    except Exception:
        printExc('ERROR: in RemoveAllFilesIconsFromPath')
        
def RemoveAllDirsIconsFromPath(path, old=False):
    if old:
        RemoveAllFilesIconsFromPath(path)
    else:
        try:
            iconsDirs = GetIconsDirs(path)
            for item in iconsDirs:
                currDir = os.path.join(path, item)
                RemoveIconsDirByPath(currDir)
        except Exception:
            printExc()
    
def formatBytes(bytes, precision = 2):
    import math
    units = ['B', 'KB', 'MB', 'GB', 'TB'] 
    bytes = max(bytes, 0); 
    if bytes:
        pow = math.log(bytes)
    else:
        pow = 0
    pow = math.floor(pow / math.log(1024)) 
    pow = min(pow, len(units) - 1) 
    bytes /= math.pow(1024, pow);
    return ("%s%s" % (str(round(bytes, precision)),units[int(pow)])) 
    
def remove_html_markup(s, replacement=''):
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

class CSearchHistoryHelper():
    TYPE_SEP = '|--TYPE--|'
    def __init__(self, name, storeTypes=False):
        printDBG('CSearchHistoryHelper.__init__')
        self.storeTypes = storeTypes
        try:
            printDBG('CSearchHistoryHelper.__init__ name = "%s"' % name)
            self.PATH_FILE = GetSearchHistoryDir(name + ".txt")
        except Exception:
            printExc('CSearchHistoryHelper.__init__ EXCEPTION')

    def getHistoryList(self):
        printDBG('CSearchHistoryHelper.getHistoryList from file = "%s"' % self.PATH_FILE)
        historyList = []
    
        try:
            file = codecs.open(self.PATH_FILE, 'r', 'utf-8', 'ignore')
            for line in file:
                value = line.replace('\n', '').strip()
                if len(value) > 0:
                    try: historyList.insert(0, value.encode('utf-8', 'ignore'))
                    except Exception: printExc()
            file.close()
        except Exception:
            printExc()
            return []
        
        orgLen = len(historyList)
        # remove duplicates
        # last 50 searches patterns are stored
        historyList = historyList[:config.plugins.iptvplayer.search_history_size.value]
        uniqHistoryList = []
        for i in historyList:
            if i not in uniqHistoryList:
                uniqHistoryList.append(i)
        historyList = uniqHistoryList

        # save file without duplicates
        if orgLen > len(historyList):
            self._saveHistoryList(historyList)
        
        # now type also can be stored
        #################################
        newList = []
        for histItem in historyList:
            fields = histItem.split(self.TYPE_SEP)
            if 2 == len(fields):
                newList.append({'pattern':fields[0], 'type':fields[1]})
            elif self.storeTypes:
                newList.append({'pattern':fields[0]})
        
        if len(newList) > 0:
            return newList
        #################################
            
        return historyList
    
    def addHistoryItem(self, itemValue, itemType = None):
        printDBG('CSearchHistoryHelper.addHistoryItem to file = "%s"' % self.PATH_FILE)
        try:
            if config.plugins.iptvplayer.search_history_size.value > 0:
                file = codecs.open(self.PATH_FILE, 'a', 'utf-8', 'replace')
                value = itemValue
                if None != itemType:
                    value = value + self.TYPE_SEP + itemType
                file.write(value + '\n')
                printDBG('Added pattern: "%s"' % itemValue) 
                file.close
        except Exception:
            printExc('CSearchHistoryHelper.addHistoryItem EXCEPTION')


    def _saveHistoryList(self, list):
        printDBG('CSearchHistoryHelper._saveHistoryList to file = "%s"' % self.PATH_FILE)
        try:
            file = open( self.PATH_FILE, 'w' )
            l = len(list)
            for i in range( l ):
                file.write( list[l - 1 -i] + '\n' )
            file.close
        except Exception:
            printExc('CSearchHistoryHelper._saveHistoryList EXCEPTION')
    
    @staticmethod
    def saveLastPattern(pattern):
        filePath = GetSearchHistoryDir("pattern")
        sts = False
        try:
            file = codecs.open(filePath, 'w', 'utf-8', 'replace')
            file.write(pattern)
            file.close
            sts = True
        except Exception:
            printExc()
        return sts
        
    @staticmethod
    def loadLastPattern():
        filePath = GetSearchHistoryDir("pattern")
        return ReadTextFile(filePath)
# end CSearchHistoryHelper

def ReadTextFile(filePath, encode='utf-8', errors='ignore'):
    sts, ret = False, ''
    try:
        file = codecs.open(filePath, 'r', encode, errors)
        ret = file.read().encode(encode, errors)
        file.close()
        if ret.startswith(codecs.BOM_UTF8):
            ret = ret[3:]
        sts = True
    except Exception:
        printExc()
    return sts, ret
    
def WriteTextFile(filePath, text, encode='utf-8', errors='ignore'):
    sts = False
    try:
        file = codecs.open(filePath, 'w', encode, errors)
        file.write(text)
        file.close()
        sts = True
    except Exception:
        printExc()
    return sts

class CFakeMoviePlayerOption():
    def __init__(self, value, text):
        self.value = value
        self.text  = text
    def getText(self):
        return self.text

class CMoviePlayerPerHost():
    def __init__(self, hostName):
        self.filePath = GetCacheSubDir('MoviePlayer', hostName + '.json')
        self.activePlayer = {} # {buffering:True/False, 'player':''}
        self.load()
        
    def __del__(self):
        self.save()
        
    def load(self):
        sts, ret = False, ''
        try:
            if not os.path.isfile(self.filePath):
                sts = True
            else:
                file = codecs.open(self.filePath, 'r', 'utf-8', 'ignore')
                ret = file.read().encode('utf-8', 'ignore')
                file.close()
                activePlayer = {}
                ret = json.loads(ret)
                activePlayer['buffering'] = ret['buffering']
                activePlayer['player'] = CFakeMoviePlayerOption(ret['player']['value'].encode('utf-8'), ret['player']['text'].encode('utf-8'))
                self.activePlayer  = activePlayer
                sts = True
        except Exception: printExc()
        return sts, ret
        
    def save(self):
        sts = False
        try:
            if {} == self.activePlayer and os.path.isfile(self.filePath):
                os.remove(self.filePath)
            else:
                data = {}
                data['buffering'] = self.activePlayer['buffering']
                data['player']    = {'value':self.activePlayer['player'].value, 'text':self.activePlayer['player'].getText()}
                data = json.dumps(data).encode('utf-8')
                file = codecs.open(self.filePath, 'w', 'utf-8', 'replace')
                file.write(data)
                file.close
                sts = True
        except Exception: printExc()
        return sts
    
    def get(self, key, defval):
        return self.activePlayer.get(key, defval)
        
    def set(self, activePlayer):
        self.activePlayer = activePlayer
        
def byteify(input, noneReplacement=None, baseTypesAsString=False):
    if isinstance(input, dict):
        return dict([(byteify(key, noneReplacement, baseTypesAsString), byteify(value, noneReplacement, baseTypesAsString)) for key, value in input.iteritems()])
    elif isinstance(input, list):
        return [byteify(element, noneReplacement, baseTypesAsString) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    elif input == None and noneReplacement != None:
        return noneReplacement
    elif baseTypesAsString:
        return str(input)
    else:
        return input

def printExc(msg=''):
    printDBG("================== EXCEPTION ==================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def GetIPTVPlayerVerstion():
    try: from neutrinoIPTV.version import IPTV_VERSION
    except Exception: IPTV_VERSION="XX.YY.ZZ"
    return IPTV_VERSION

def GetIPTVPlayerComitStamp():
    try: from Plugins.Extensions.IPTVPlayer.version import COMMIT_STAMP
    except Exception: COMMIT_STAMP=""
    return COMMIT_STAMP

def GetShortPythonVersion():
    return "%d.%d" % (sys.version_info[0], sys.version_info[1])
    
def GetVersionNum(ver):
    try:
        if None == re.match("[0-9]+\.[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]", ver): raise Exception("Wrong version!")
        return int(ver.replace('.', ''))
    except Exception:
        printExc('Version[%r]' % ver)
        return 0
        
def IsFPUAvailable():
    try:
        if None == IsFPUAvailable.available:
            with open('/proc/cpuinfo', 'r') as f:
                data = f.read().strip().upper()
            if ' FPU ' in data:
                IsFPUAvailable.available = True
            else:
                IsFPUAvailable.available = False
        if IsFPUAvailable.available == False and config.plugins.iptvplayer.plarformfpuabi.value == 'hard_float':
            return True
    except Exception:
        printExc()
    return IsFPUAvailable.available
IsFPUAvailable.available = None

def IsSubtitlesParserExtensionCanBeUsed():
    try:
        if config.plugins.iptvplayer.useSubtitlesParserExtension.value:
            from Plugins.Extensions.IPTVPlayer.libs.iptvsubparser import _subparser as subparser
            if '' != subparser.version():
                return True
    except Exception:
        printExc()
    return False
    
def IsBrokenDriver(filePath):
    # workaround for broken DVB driver mbtwinplus:
    # root@mbtwinplus:~# cat /proc/stb/video/policy2
    # Segmentation fault
    try:
        return 'video/policy' in filePath and not fileExists('/proc/stb/video/aspect_choices')
    except Exception:
        printExc()
    return False
        
def GetE2OptionsFromFile(filePath):
    options = []
    if IsBrokenDriver(filePath): return []
    try:
        if fileExists(filePath):
            with open(filePath, 'r') as f:
                data = f.read().strip()
                data = data.split(' ')
                for item in data:
                    opt = item.strip()
                    if '' != opt:
                        options.append(opt)
        else:
            printDBG('GetE2OptionsFromFile file[%s] not exists' % filePath)
    except Exception:
        printExc()
    return options

def SetE2OptionByFile(filePath, value):
    if IsBrokenDriver(filePath): return False
    sts = False
    try:
        with open(filePath, 'w') as f:
            data = f.write(value)
            sts = True
    except Exception:
        printExc()
    return sts

def GetE2VideoAspectChoices():
    tab = GetE2OptionsFromFile('/proc/stb/video/aspect_choices')
    # workaround for some STB
    # reported here: https://gitlab.com/iptvplayer-for-e2/iptvplayer-for-e2/issues/30
    staticTab = ["4:3", "16:9", "any"]
    if len(tab) < 2 and GetE2VideoAspect() in staticTab:
        tab = staticTab
    return tab

def GetE2VideoAspect():
    options = GetE2OptionsFromFile('/proc/stb/video/aspect')
    if 1 == len(options): return options[0]
    return None
    
def SetE2VideoAspect(value):
    return SetE2OptionByFile('/proc/stb/video/aspect', value)
    
def GetE2VideoPolicyChoices(num=''):
    return GetE2OptionsFromFile('/proc/stb/video/policy%s_choices' % num)
    
def GetE2VideoPolicy(num=''):
    options = GetE2OptionsFromFile('/proc/stb/video/policy'+num)
    if 1 == len(options): return options[0]
    return None
    
def SetE2VideoPolicy(value, num=''):
    return SetE2OptionByFile('/proc/stb/video/policy'+num, value)
    
def GetE2AudioCodecMixChoices(codec):
    return GetE2OptionsFromFile('/proc/stb/audio/%s_choices' % codec)
    
def GetE2AudioCodecMixOption(codec):
    options = GetE2OptionsFromFile('/proc/stb/audio/%s' % codec)
    if 1 == len(options): return options[0]
    return None
    
def SetE2AudioCodecMixOption(codec, value):
    return SetE2OptionByFile('/proc/stb/audio/%s' % codec, value)

# videomode
def GetE2VideoModeChoices():
    # return 'pal ntsc 480i 576i 480p 576p 720p50 720p 1080i50 1080i 1080p24 1080p25 1080p30 720p24 720p25 720p30 1080p50 1080p'.split(' ')
    return GetE2OptionsFromFile('/proc/stb/video/videomode_choices')
    
def GetE2VideoMode():
    # return '1080p50'
    options = GetE2OptionsFromFile('/proc/stb/video/videomode')
    if 1 == len(options): return options[0]
    return None
    
def SetE2VideoMode(value):
    return SetE2OptionByFile('/proc/stb/video/videomode', value)

def MergeDicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
