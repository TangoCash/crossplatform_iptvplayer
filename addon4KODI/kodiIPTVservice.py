# -*- coding: utf-8 -*-
import sys
import os
import time
myTime = time.time

import xbmc
import xbmcgui
import xbmcaddon
try:    import json
except: import simplejson as json

#get paths
myAddon=xbmcaddon.Addon('plugin.video.IPTVplayer')
addonTempFolder = myAddon.getSetting('config.misc.sysTempPath')
kodiIPTVpath = myAddon.getSetting('kodiIPTVpath')
E2root = kodiIPTVpath
if os.path.basename(E2root) == 'IPTVPlayer':
    E2root = os.path.dirname(E2root)
    if os.path.basename(E2root) == 'Extensions':
        E2root = os.path.dirname(E2root)
        if os.path.basename(E2root) == 'Plugins':
            E2root = os.path.dirname(E2root)

#set constants
logFile = os.path.join(addonTempFolder,'kodiIPTVservice.log')

#update cpython search paths
if kodiIPTVpath not in sys.path:
    sys.path.append(kodiIPTVpath)
if E2root not in sys.path:
    sys.path.append(E2root)
if not os.path.exists(os.path.join(E2root,'config')):
    os.system('mkdir -p %s/config' % E2root)

from Components.config import config, configfile
from Components.SetupDevices import InitSetupDevices #inits correct language based on neutrino settings

import Plugins.Extensions.IPTVPlayer.icomponents.iptvconfigmenu
from Plugins.Extensions.IPTVPlayer.dToolsSet.DaemonTools import *
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem

def logState(myText, append=True ):
    if append == False:
        with open(logFile, "w") as f:
            f.write(myText)
            f.close()
    else:
        with open(logFile, "a") as f:
            f.write(myText)
            f.close()
daemonLog = logState

def getCMD():
    cmd = xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.CMD').strip()
    xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.CMD', '')
    IPTVdaemonRET=os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','ret')
    if cmd != '':
        xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.RET', '')
        daemonLog("getCMD>%s\n" % cmd)
    return cmd
    
def myAnswer(text = ''):
    xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.RET', text)
    daemonLog("<%s\n" % text)
    return

def configureE2():
    logState('Configuring E2 settings..\n')
    with open(xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/settings.xml'), 'r') as settingsFile:
        for line in settingsFile:
            if line.find('id="config.') > 0:
                mySetting = line.split('id="')[1].split('"')[0]
                mySettingValue = myAddon.getSetting(mySetting).replace('\\','/') #to avoid issues on Windows
                if mySettingValue != '' and mySettingValue[-1] == '/':
                    mySettingValue = mySettingValue[:-1]
                logState('\t%s=%s\n' % (mySetting,mySettingValue))
                exec("%s.value='%s';%s.save()" %(mySetting, mySettingValue, mySetting))
    SaveE2ConfFile(os.path.join(E2root, 'config', 'E2settings.conf'))
    return

def configureHOST(hostname):
    logState('Configuring HOST %s settings..\n' % hostname)
    with open(xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/settings.xml'), 'r') as settingsFile:
        for line in settingsFile:
            if line.find('id="%s.config.' % hostname ) > 0:
                mySetting = line.split('id="')[1].split('"')[0][len(hostname)+1:]
                mySettingValue = myAddon.getSetting(mySetting).replace('\\','/') #to avoid issues on Windows
                if mySettingValue != '' and mySettingValue[-1] == '/':
                    mySettingValue = mySettingValue[:-1]
                logState('\t%s=%s\n' % (mySetting,mySettingValue))
                exec("%s.value='%s';%s.save()" %(mySetting, mySettingValue, mySetting))
    SaveE2ConfFile(os.path.join(E2root, 'config', 'E2settings.conf'))
    return

class MyDaemon():
    def __init__(self, pidfile='/dev/null', stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', hostName='', clientType='PYTHON'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.hostName = hostName
        self.clientType = clientType
        self.myCommand = ''
        self.host = ''
        self.title = ''
        self.logo = ''

    def run(self):
        ret=None
        _temp = __import__('hosts.' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
        self.title = _temp.gettytul()
        logState("Host title: %s\n" % self.title)
        self.host = _temp.IPTVHost()
        self.SelectedLink = ''
        try:
            if not isinstance(self.host, IHost):
                logState("Host [%r] inherits from IHost :)\n" % (self.hostName))
        except:
            logState( 'Cannot import class IPTVHost for host [%r]\n' %  self.hostName)
            self.stop()
            return

        hostconfig = __import__('hosts.' + self.hostName, globals(), locals(), ['GetConfigList'], -1)
        ConfList = hostconfig.GetConfigList()
        configureHOST(self.hostName)

        monitor = xbmc.Monitor()
        while not monitor.abortRequested() or xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.HOST') == self.hostName:
            #logState("plugin.video.IPTVplayer.HOST=%s self.hostName=%s\n" %(xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.HOST'),self.hostName))
            timestamp = long(myTime())
            xbmcgui.Window(10000).setProperty("kodiIPTVserviceHeartBeat", str(timestamp))
            # Sleep/wait for abort for 10 seconds
            if monitor.waitForAbort(1):
                break # Abort was requested while waiting. We should exit
            self.myCommand = getCMD()
            if self.myCommand == '':
                continue
            elif self.myCommand == 'STOPservice':
                self.stop()
                return
            elif self.myCommand == 'Title':
                myAnswer(self.title)
                continue
            elif self.myCommand == 'LogoPath':
                myAnswer(self.host.getLogoPath().value)
                continue
            elif self.myCommand == 'SupportedTypes':
                myAnswer(self.host.getSupportedFavoritesTypes().value)
                continue
            elif self.myCommand == 'InitList':
                ret = self.host.getInitList()
                if len(ConfList) > 0:
                    #### TBC    myAnswer(ToItemsListTable(ret.value, self.clientType) + ToConfigTable(ConfList, clientType)) #if host hasconfig, return it too
                    myAnswer(ToItemsListTable(ret.value, self.clientType)) #if host hasconfig, return it too
                else:
                    myAnswer(ToItemsListTable(ret.value, self.clientType))
                continue
            elif self.myCommand == 'RefreshList':
                ret = self.host.getCurrentList()
                myAnswer(ToItemsListTable(ret.value, self.clientType))
                continue
            elif self.myCommand == 'PreviousList':
                ret= self.host.getPrevList()
                myAnswer(ToItemsListTable(ret.value, self.clientType))
                continue
            elif self.myCommand.startswith('ListForItem='): #Param: item ID
                myID = self.myCommand.split('=')[1]
                if myID.isdigit():
                    myID = int(myID)
                    ret= self.host.getListForItem(myID,0,ret.value[myID])
                    myAnswer(ToItemsListTable(ret.value, self.clientType))
                else:
                    myAnswer('ERROR: wrong index')
                continue
            elif self.myCommand.startswith('getVideoLinks='): #Param: link ID
                myID = self.myCommand.split('=')[1]
                daemonLog("daemon:getVideoLinks=%s" % myID)
                if myID.isdigit():
                    myID = int(myID)
                    self.movieTitle = ret.value[myID].name.replace('"', "'")
                    try:
                        links = ret.value[myID].urlItems
                    except:
                        links='NOVALIDURLS'
                    try:
                        retUrl= self.host.getLinksForVideo(myID,ret.value[myID]) #returns "NOT_IMPLEMENTED" when host is using curlitem
                        myAnswer(ToUrlsTable(retUrl.value, self.clientType))
                        daemonLog("retUrl found")
                    except:
                        daemonLog("Exception running getLinksForVideo (means not implemented), using CUrlItem")
                        retUrl = RetHost(RetHost.NOT_IMPLEMENTED, value = [])
                    if retUrl.status == "NOT_IMPLEMENTED" and links != 'NOVALIDURLS': 
                        daemonLog("getLinksForVideo not implemented, using CUrlItem")
                        tempUrls=[]
                        daemonLog("Iterating links...")
                        iindex=1
                        for link in links:
                            if link.name == '':
                                tempUrls.append(CUrlItem('link %d' % iindex, link.url, link.urlNeedsResolve))
                            else:
                                tempUrls.append(CUrlItem(link.name, link.url, link.urlNeedsResolve))
                            iindex += 1
                        retUrl = RetHost(RetHost.OK, value = tempUrls)
                        myAnswer(ToUrlsTable(tempUrls, self.clientType))
                else:
                    myAnswer('ERROR: wrong index')
                continue
            #### ResolveURL ####
            elif self.myCommand.startswith('ResolveURL='): #Param: selected quality link ID
                myParm = self.myCommand.split('=')[1]
                url = "NOVALIDURLS"
                linksList = []
                if myParm.isdigit():
                    myID = int(myParm)
                    #czasami jest zwracana lista linkow wiec trzeba ja sparsowac
                    linksList = self.host.getResolvedURL(retUrl.value[myID].url).value
                    daemonLog("myParm.isdigit and points to:%s" % retUrl.value[myID].url)
                else:
                    linksList = self.host.getResolvedURL(myParm).value
                if len(linksList) == 0: #There is no free links for current video
                    daemonLog("linksList has no items :(")
                elif len(linksList) >1:
                    daemonLog('WARNING: more than one link returned, selecting first')
                if isinstance(linksList[0], CUrlItem):
                    if int(linksList[0].urlNeedsResolve) == 1:
                        daemonLog('ERROR: url should be already resolved. :(')
                    else:
                        url = linksList[0].url
                        daemonLog("CUrlItem url:%s" %url)
                elif isinstance(linksList[0], basestring):
                        url = linksList[0]
                        daemonLog("basestring url:%s" %url)
                elif isinstance(linksList, (list, tuple)):
                        url = linksList[0] 
                        daemonLog("list/tuple url:%s" %url)
                myAnswer( url )
            #### Download movie ####
            elif self.myCommand.startswith('DownloadURL='):  #Param: full download url
                url = self.myCommand[len('DownloadURL='):]   #using split results in wrong links
                from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import IsUrlDownloadable, DownloaderCreator
                if IsUrlDownloadable(url):
                    from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
                    url, downloaderParams = DMHelper.getDownloaderParamFromUrl(url)
                    currentDownloader = DownloaderCreator(url) #correct downloader is assigned e.g. wget
                    MovieRecordFileName = os.path.join(config.plugins.iptvplayer.NaszaSciezka.value , self.movieTitle.replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-'))
                    MovieRecordFileNameExt = MovieRecordFileName[-4:]
                    if not MovieRecordFileNameExt in ('.mpg', '.flv', '.mp4'):
                        MovieRecordFileName += ".mp4"
                    currentDownloader.start(url, MovieRecordFileName, downloaderParams)
                    myAnswer(MovieRecordFileName)
                else:
                    myAnswer( 'ERROR:wrong url' )
            #### buffer movie ####
            elif self.myCommand.startswith('BufferURL='):  #Param: full download url
                url = self.myCommand[len('BufferURL='):]   #using split results in wrong links
                from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import IsUrlDownloadable, DownloaderCreator
                if IsUrlDownloadable(url):
                    from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
                    url, downloaderParams = DMHelper.getDownloaderParamFromUrl(url)
                    currentDownloader = DownloaderCreator(url) #correct downloader is assigned e.g. wget
                    MovieRecordFileName = config.plugins.iptvplayer.NaszaSciezka.value + "iptv_buffering.mp4"
                    currentDownloader.start(url, MovieRecordFileName, downloaderParams)
                    myAnswer(MovieRecordFileName)
                else:
                    myAnswer( 'ERROR:wrong url' )
            #### Search items ####
            elif self.myCommand.startswith('Search='):  #Param: search pattern
                self.searchPattern = self.myCommand[len('Search='):] #param can contain '='. Using split function would brake everything ;)
                ret = self.host.getSearchResults(self.searchPattern)
                myAnswer(ToItemsListTable(ret.value, self.clientType))

            #### doCommand - not finished####
            elif self.myCommand.startswith('doCommand='): #Param: selected quality link ID
                execCMD = self.myCommand.replace('doCommand=','')
                try:
                    exec(execCMD)
                    myAnswer( 'OK' )
                except Exception:
                    myAnswer( 'ERROR executing command.')
            elif self.myCommand.startswith('doUnsafeCommand='): #Param: selected quality link ID
                execCMD = self.myCommand.replace('doUnsafeCommand=','')
                exec(execCMD)
                myAnswer( 'OK' )
            else:
                daemonLog("Unknown command:'%s'\n" % self.myCommand)
                myAnswer("ERROR: Unknown command:'%s'\n" % self.myCommand)
        self.stop()
        return

    def stop(self):
        xbmcgui.Window(10000).clearProperty("kodiIPTVserviceHeartBeat")
        return
    
if __name__ == '__main__':
    startHost = xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.HOST')
    if xbmcgui.Window(10000).getProperty('kodiIPTVserviceHeartBeat').isdigit():
        logState('KODI service already running, exiting\n')
    else:        
        logState("[%d]init KODI service for host %s\n" % (myTime(),startHost), False)
        logState("E2root:%s\n" % E2root)
        logState("kodiIPTVpath:%s\n" % kodiIPTVpath)
        logState("addonTempFolder:%s\n" % addonTempFolder)
        # set proper path for e2
        LoadE2ConfFile(os.path.join(E2root, 'config', 'E2settings.conf'))
        configureE2()
        #clearLogsPaths(os.path.join(addonTempFolder,'.IPTVdaemon'))
        #start main loop
        daemon = MyDaemon(hostName=startHost)
        daemon.run()
        logState("Stop KODI service\n")
