#!/usr/bin/python
import os, sys, time, json

import __init__
   
from Components.config import config, configfile
from Components.SetupDevices import InitSetupDevices #inits correct language based on neutrino settings

from Plugins.Extensions.IPTVPlayer.dToolsSet.DaemonTools import *
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _

from daemon import Daemon

import Plugins.Extensions.IPTVPlayer.icomponents.iptvconfigmenu
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem

class MyDaemon(Daemon):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', hostName='', clientType='LUA'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.hostName = hostName
        self.clientType = clientType
        self.myCommand = ''
        self.host = ''
        self.title = ''

    def run(self):
        _temp = __import__('hosts.' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
        self.title = _temp.gettytul()
        print self.title
        self.host = _temp.IPTVHost()
        self.SelectedLink = ''
        try:
            if not isinstance(self.host, IHost):
                print("Host [%r] does not inherit from IHost" % self.hostName)
                self.stop()
        except:
            print( 'Cannot import class IPTVHost for host [%r]' %  self.hostName)
            self.stop()

        print("Host [%r] inherited from IHost properly" % self.hostName)
        hostconfig = __import__('hosts.' + self.hostName, globals(), locals(), ['GetConfigList'], -1)
        ConfList = hostconfig.GetConfigList()
        #main loop
        while True:
            time.sleep(1)
            self.myCommand = getCMD()
            if self.myCommand == '':
                continue
            elif self.myCommand == 'Title':
                myAnswer(self.title)
            elif self.myCommand == 'LogoPath':
                myAnswer(self.host.getLogoPath().value)
            elif self.myCommand == 'SupportedTypes':
                myAnswer(self.host.getSupportedFavoritesTypes().value)
            elif self.myCommand == 'InitList':
                ret = self.host.getInitList()
                if len(ConfList) > 0:
                    #### TBC    myAnswer(ToItemsListTable(ret.value, self.clientType) + ToConfigTable(ConfList, clientType)) #if host hasconfig, return it too
                    myAnswer(ToItemsListTable(ret.value, self.clientType)) #if host hasconfig, return it too
                else:
                    myAnswer(ToItemsListTable(ret.value, self.clientType))
            elif self.myCommand == 'RefreshList':
                ret = self.host.getCurrentList()
                myAnswer(ToItemsListTable(ret.value, self.clientType))
            elif self.myCommand == 'PreviousList':
                ret= self.host.getPrevList()
                myAnswer(ToItemsListTable(ret.value, self.clientType))
                
            elif self.myCommand.startswith('ListForItem='): #Param: item ID
                myID = self.myCommand.split('=')[1]
                if myID.isdigit():
                    myID = int(myID)
                    ret= self.host.getListForItem(myID,0,ret.value[myID])
                    myAnswer(ToItemsListTable(ret.value, self.clientType))
                else:
                    myAnswer('ERROR: wrong index')
                
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
                    MovieRecordFileName = config.plugins.iptvplayer.NaszaSciezka.value + self.movieTitle.replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-')
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
                    myAnswer( 'ERROR')
            elif self.myCommand.startswith('doUnsafeCommand='): #Param: selected quality link ID
                execCMD = self.myCommand.replace('doUnsafeCommand=','')
                exec(execCMD)
                myAnswer( 'OK' )
            else:
                daemonLog("Unknown command:'%s'\n" % self.myCommand)

if __name__ == "__main__":
    if len(sys.argv) == 2 and 'stop' == sys.argv[1]:
        daemon = MyDaemon( config.misc.sysTempPath.value +'/.IPTVdaemon/pid' )
        daemon.stop()
    elif len(sys.argv) >= 3:
        #default init values
        arg_clientType = 'LUA'
        try:
            arg_clientType = sys.argv[3]
        except:
            pass
        try:
            config.misc.sysTempPath.value = sys.argv[4]
            config.misc.sysTempPath.save()
            configfile.save()
        except:
            pass
        clearLogsPaths(config.misc.sysTempPath.value +'/.IPTVdaemon')
        daemon = MyDaemon( pidfile = config.misc.sysTempPath.value +'/.IPTVdaemon/pid',
                          hostName=sys.argv[2],
                          clientType=arg_clientType,
                          stderr=config.misc.sysTempPath.value +'/.IPTVdaemon/errors')
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s stop|restart|start hostname [LUA|PYTHON [TEMP_PATH]]" % sys.argv[0]
        sys.exit(2)
