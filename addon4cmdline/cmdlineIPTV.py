#!/usr/bin/env python
# -*- coding: utf-8 -*-
# execfile('cmdlineIPTV.py')
import os, sys, time

myRootPath = os.path.dirname(os.path.realpath(sys.argv[0])).replace("/Plugins/Extensions/IPTVPlayer","")
if myRootPath not in sys.path:
    sys.path.append(myRootPath)
if '/usr/share/E2emulator' not in sys.path and os.path.exists('/usr/share/E2emulator'):
    sys.path.append('/usr/share/E2emulator')
    
from Components.config import config
from Components.SetupDevices import InitSetupDevices #inits correct language based on neutrino settings
from Plugins.Extensions.IPTVPlayer.dToolsSet.DaemonTools import *

os.system('mkdir -p %s/.IPTVdaemon;rm -f %s/neutrinoIPTV.log;rm -f %s/cmdlineIPTV.log' %(config.misc.sysTempPath.value,
                                                                                         config.misc.sysTempPath.value,
                                                                                         config.misc.sysTempPath.value))
	
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
#from Plugins.Extensions.IPTVPlayer.dToolsSet.itools import *
import Plugins.Extensions.IPTVPlayer.icomponents.iptvconfigmenu
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem

def myLog( text = ''):
    try:
        f = open(config.misc.sysTempPath.value +'/cmdlineIPTV.log', 'a')
        f.write(text + '\n')
        f.close
    except:
        pass

class aqq():
    def decodeUTF8(self,UTFtext):
        text = removeSpecialChars(UTFtext) #definition in DaemonTools
        text= text.replace("ó",'o').replace("ś",'s').replace("ć",'c').replace("ą",'a').replace("ł",'l').replace("ę",'e').replace("ń",'n').replace("ż",'z').replace("ź",'z')
        text= text.replace("Ó",'O').replace("Ś",'S').replace("Ć",'C').replace("Ą",'A').replace('Ł','L').replace("Ę",'E').replace("Ń",'N').replace("Ż",'Z').replace("Ź",'Z')
        return text

    def enterInt(self, text, specialChars = ['q']):
        while True:
            data = raw_input(text)
            if (data.isdigit() and int(data) <= self.index) or data in specialChars:
                break
        if data == 'q':
            sys.exit()
        return data

    def SelectHost(self):
        from Plugins.Extensions.IPTVPlayer.dToolsSet.hostslist import HostsList
        ListaTerm=''
        self.index = 0
        kolumna=1
        for host in HostsList:
            tmp = self.decodeUTF8(host[1].replace("https:",'').replace("http:",'').replace("/",'').replace("www.",''))
            if kolumna <3: tmp += " " * 20
            if len(tmp) > 21: tmp = tmp[:20]
            ListaTerm += "%d-%s" % (self.index, tmp)
            self.index += 1
            if kolumna <3:
                ListaTerm += "\t"
                kolumna += 1
            else:
                kolumna = 1
                ListaTerm += '\n'
        sys.stderr.write("\x1b[2J\x1b[H")
        print "Keys:\n\tq-quit\n\tp-previous list\n\tr-reload list\n\ti-initial categories list\n\th-list of hosts\n\n"
        print ListaTerm
        data = int(self.enterInt("Enter ID (q-exit): "))
        return HostsList[data][0]

    def SelectItem(self,retval):
        Podkr="-" * (len(self.hostTitle) + 1)
        ListaTerm='%s:\n%s\n' % (self.hostTitle,Podkr)
        self.index=0
        for item in retval:
            iname = self.decodeUTF8(item.name)
            idescr = self.decodeUTF8(item.description)
            if idescr == '':
                iitem = "%d-%s" %(self.index, iname)
            else:
                iitem = "%d-%s, %s" %(self.index, iname, idescr)
            if len(iitem) > 78: iitem = iitem[:78]
            ListaTerm += iitem + '\n'
            self.index += 1
        sys.stderr.write("\x1b[2J\x1b[H")
        daemonLog(ToItemsListTable(retval, "PYTHON"))
        print ListaTerm
        data = self.enterInt("Enter ID or [Q]uit/[P]revious/[R]eload/[I]nitlist/[H]ostslist: ", ['q','p','r','i','h'])
        if data == 'q':
            sys.exit()
        return data

    def SelectMovieLink(self,retval):
        Podkr="-" * (len(self.movieTitle[:78]) + 1)
        ListaTerm='%s:\n%s\n' % (self.movieTitle[:78],Podkr)
        self.index=0
        for item in retval:
            iname = self.decodeUTF8(item.name)
            iitem = "%d-%s" %(self.index, iname)
            if len(iitem) > 78: iitem = iitem[:78]
            ListaTerm += iitem + '\n'
            self.index += 1
        sys.stderr.write("\x1b[2J\x1b[H")
        daemonLog(ToUrlsTable(retval, 'PYTHON'))
        print ListaTerm
        data = self.enterInt("Enter ID to start downloading (q/p): ", ['q','p'])
        if data == 'p':
            return
        elif data == 'q':
            sys.exit()
        elif data.isdigit:
            if int(retval[int(data)].urlNeedsResolve) == 1:
                daemonLog('ResolveURL=%s' % retval[int(data)].url)
                url = "NOVALIDURLS"
                try:
                    #czasami jest zwracana lista linkow wiec trzeba ja sparsowac
                    linksList = []
                    linksList = self.host.getResolvedURL(retval[int(data)].url).value
                    if len(linksList) == 0: #There is no free links for current video
                        url = "NOVALIDURLS"
                    elif len(linksList) >1:
                        daemonLog('WARNING: more than one link returned, selecting first')
                        print "Warning more than one link returned, selecting first"
                        time.sleep(10)
                    if isinstance(linksList[0], CUrlItem):
                        if int(linksList[0].urlNeedsResolve) == 1:
                            daemonLog('ERROR: url should be already resolved. :(')
                            url = "NOVALIDURLS"
                        else:
                            url = linksList[0].url
                    elif isinstance(linksList[0], basestring):
                            url = linksList[0]
                    elif isinstance(linksList, (list, tuple)):
                            url = linksList[0] 
                except:
                    url = "NOVALIDURLS"
                daemonLog('ResolvedURL=%s' % url)
            else:
                url = retval[int(data)].url
        #print url
        #time.sleep(2)
        self.DownloadMovieLink(url)

    def DownloadMovieLink(self,url):   
        from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import IsUrlDownloadable, DownloaderCreator
        if IsUrlDownloadable(url):
            from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
            url, downloaderParams = DMHelper.getDownloaderParamFromUrl(url)
            currentDownloader = DownloaderCreator(url) #correct downloader is assigned (eg wget
            MovieRecordFileName = config.plugins.iptvplayer.NaszaSciezka.value + self.movieTitle.replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-')
            MovieRecordFileNameExt = MovieRecordFileName[-4:]
            if not MovieRecordFileNameExt in ('.mpg', '.flv', '.mp4'):
                MovieRecordFileName += ".mp4"
            currentDownloader.start(url, MovieRecordFileName, downloaderParams)
            print "Downloading in background...\n   %s\n" % MovieRecordFileName
            time.sleep(5)
        else:
            print "\n" + _("No valid links available.")
            time.sleep(10)
        time.sleep(20)
        return
    
    def MainLoop(self):
        #select Host
        hostName = self.SelectHost()
        _temp = __import__('hosts.' + hostName, globals(), locals(), ['IPTVHost'], -1)
        self.hostTitle = _temp.gettytul()
        self.movieTitle=''
        self.host = _temp.IPTVHost()
        sys.stderr.write("\x1b[2J\x1b[H")
        myLog("cmdlineIPTV:Selected:\n\t%s (%s),\n\tsupports %s,\n" %(self.hostTitle, hostName, self.host.getSupportedFavoritesTypes().value))
        #download initial catalog
        ret = self.host.getInitList() # this gest list of IHost items
        while True:
            retID = self.SelectItem(ret.value)
            if retID == 'p':
                ret= self.host.getPrevList()
            elif retID == 'i':
                ret= self.host.getInitList()
            elif retID == 'h':
                hostName = self.SelectHost()
                _temp = __import__('hosts.' + hostName, globals(), locals(), ['IPTVHost'], -1)
                self.hostTitle = _temp.gettytul()
                self.host = _temp.IPTVHost()
                sys.stderr.write("\x1b[2J\x1b[H")
                ret = self.host.getInitList() # this gest list of IHost items
            elif retID.isdigit():
                myID = int(retID)
                if ret.value[myID].type == "CATEGORY":
                    myLog("cmdlineIPTV:CATEGORY id=%d" % myID)
                    ret = self.host.getListForItem(myID,0,ret.value[myID])
                elif ret.value[myID].type == "VIDEO":
                    myLog("cmdlineIPTV:VIDEO id=%d" % myID)
                    self.movieTitle = self.decodeUTF8(ret.value[myID].name)
                    try:
                        ret = self.host.getLinksForVideo(myID,ret.value[myID])
                        self.SelectMovieLink(ret.value)
                        myLog("Link for video found")
                    except:
                        myLog("exception getting links")
                        links = ret.value[myID].urlItems
                        #index = 0
                        myLink=''
                        for link in links:
                            #print 'id=%d, name="%s", url="%s", urlNeedsResolve=%d}\n' % (index,link.name,link.url,link.urlNeedsResolve)
                            #index += 1
                            myLink=link.url
                            break
                        self.DownloadMovieLink(myLink)
                        time.sleep(30)
                    ret = self.host.getCurrentList()
                elif ret.value[myID].type == "SEARCH":
                    myLog("cmdlineIPTV:SEARCH id=%d" % myID)
                    self.searchPattern = raw_input('Enter search pattern: ')
                    ret = self.host.getSearchResults(self.searchPattern)
                else:
                    sys.stderr.write("\x1b[2J\x1b[H")
                    print "%s not implemented :(" %ret.value[myID].type
                    time.sleep(10)
            else: # Reload list
                ret= self.host.getCurrentList()
            
n=aqq()
n.MainLoop()