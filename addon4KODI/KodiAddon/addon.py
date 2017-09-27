# -*- coding: utf-8 -*-
# Module: main loop for IPTVdaemon
# Author: j00zek
# Created on: 15.01.2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
fileExists = os.path.exists
buildPath = os.path.join

import sys
from urllib import urlencode
from urlparse import parse_qsl
try:    import json
except: import simplejson as json
import time
import tempfile


import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# assure we have correct paths defined
ADDON = xbmcaddon.Addon(id='plugin.video.IPTVplayer')
# Get the plugin handle as an integer number.
ADDON_handle = int(sys.argv[1])
# Get the plugin url in plugin:// notation.
ADDON_url = sys.argv[0]
sys.path.insert(0, buildPath(ADDON.getAddonInfo("path"), 'resources', 'E2emulator'))

def _(data):
    if isinstance(data, (int, long)):
        return ADDON.getLocalizedString(data)
    else:
        return data
      
def myLog( text = '' , clearFile = False):
    myLogFile = buildPath(ADDON.getSetting("config.misc.sysTempPath"),'IPTVplayerGUI.log')
    if int(ADDON.getSetting("LogOptions")) > 1: #0-none, 1-only KODIservice:
        if clearFile == True:
            f = open(myLogFile, 'w')
        else:
            f = open(myLogFile, 'a')
        if isinstance(text, (tuple, list, set, dict)):
            f.write("\t %s" % json.dumps(text))
        else:
            f.write(text + '\n')
        f.close
    else:
        if fileExists(myLogFile):
            os.remove(myLogFile)
    return

class StatusLine(xbmcgui.WindowDialog):
    def __init__(self, line=''):
        self.addControl(xbmcgui.ControlLabel(x=390, y=5, width=500, height=25, label=line, textColor='0xFFFFFF00'))

def showDialog(HeaderText, Message):
    d = xbmcgui.Dialog()
    d.ok(HeaderText, Message)
    return

def selectionDialog(HeaderText, listOfOptions):
    d = xbmcgui.Dialog()
    ret = d.select(HeaderText, listOfOptions)
    return ret

try:
    from Plugins.Extensions.IPTVPlayer.dToolsSet.hostslist import HostsList
except ImportError, error:
    showDialog(str(error), 'Error loading list of hosts.')
    raise

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(ADDON_url, urlencode(kwargs))

def sendCMD(mycmd):
    if ADDON.getSetting("daemonType") == "1": #= kodi service
        xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.RET', '')
        xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.CMD', mycmd)
    else:
        if fileExists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','ret')):
            os.system('rm -f %s' % buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','ret')) 
        with open(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','cmd'), "w") as fp:
            fp.write(mycmd)
            fp.close()
################################################################################################################### DAEMON SUBS >>>
def startDaemon(hostName):
    TempFiles=['cmd','log','pid','errors','kodiIPTVservice.log']
    for Tempfile in TempFiles:
        #just cleaning before start
        if fileExists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon',Tempfile)):
            os.remove(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon',Tempfile))
        if fileExists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),Tempfile)):
            os.remove(buildPath(ADDON.getSetting("config.misc.sysTempPath"),Tempfile))
    if ADDON.getSetting("daemonType") == "1": #= kodi service
        xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.HOST', hostName)
        #xbmcgui.Window(10000).setProperty("kodiIPTVserviceHeartBeat", str(long(time.time())))
        xbmc.executescript(buildPath(ADDON.getSetting("kodiIPTVpath"),'kodiIPTVservice.py')) # no parameters, we use main window property
        WaitTime = 10 #maximum 5 seconds wait for init.
        while WaitTime >= 1:
            myLog("initializing host %ds" % WaitTime)
            WaitTime = WaitTime - 1
            time.sleep(1)
            if xbmcgui.Window(10000).getProperty("kodiIPTVserviceHeartBeat").isdigit():
                break
    else:
        os.system("%s/IPTVdaemon.py restart %s PYTHON %s" %(ADDON.getSetting("kodiIPTVpath"), hostName, ADDON.getSetting("config.misc.sysTempPath")))
        WaitTime = 5 #maximum 5 seconds wait for init.
        while WaitTime >= 1:
            myLog("initializing host %ds" % WaitTime)
            WaitTime = WaitTime - 1
            time.sleep(1)
            if fileExists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','ret')):
                break
        if fileExists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','pid')):
            with open(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','pid'), 'r') as f:
                ADDON.setSetting("daemonPID", f.read().strip())
                f.close
    return

def stopDaemon():
    if ADDON.getSetting("daemonType") == "1": #= kodi service
        xbmcgui.Window(10000).setProperty('plugin.video.IPTVplayer.HOST', '-')
        xbmcgui.Window(10000).clearProperty("plugin.video.IPTVplayer.HOST")
        xbmcgui.Window(10000).clearProperty("kodiIPTVserviceHeartBeat")
        ADDON.setSetting("daemonPID", "-1")
        sendCMD('STOPservice')
    else:
        os.system("kill `ps -ef|grep -v grep|grep 'plugin.video.IPTVplayer'|awk '{print $2}'` 2>/dev/null")
        ADDON.setSetting("daemonPID", "-1")
    return

def restartDaemon(hostName):
    stopDaemon()
    time.sleep(1)
    startDaemon(hostName)
    return

def isDeamonWorking():
    if ADDON.getSetting("daemonPID") != "-1" and ADDON.getSetting("daemonPID") != "" and ADDON.getSetting("daemonType") == "0": #0-we use separate IPTVdaemon
        if fileExists("/proc/%s" % ADDON.getSetting("daemonPID")):
            return True
    elif ADDON.getSetting("daemonType") == "1" and xbmcgui.Window(10000).getProperty("kodiIPTVserviceHeartBeat").isdigit():
        currTime = int(time.time())
        timestamp = int(xbmcgui.Window(10000).getProperty("kodiIPTVserviceHeartBeat"))
        xbmcgui.Window(10000).setProperty("kodiIPTVserviceHeartBeat", str(long(time.time())))
        if currTime - timestamp < 2:
            return True
    return False
###################################################################################################################  DAEMON SUBS <<<

def doCMD( myCommand , commandPart1 = '' , commandPart2 = ''):
    try:
        commandDescr= commandPart1.decode('utf-8', errors='ignore') + commandPart2.decode('utf-8', errors='ignore')
    except Exception:
        commandDescr=''
    myLog("doCMD('%s')" % myCommand)
    IPTVdaemonRET = buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon','ret')
    if myCommand == None or myCommand == '':
        return ''
    elif not isDeamonWorking():
        showDialog('Error', _(30428))
        return ''
    if commandDescr == '':
        SL = StatusLine(_(30429))
    else:
        SL = StatusLine(commandDescr)
    SL.show()
    retVal= ''
    if fileExists(IPTVdaemonRET):
        os.system('rm -f %s' % IPTVdaemonRET) 
                
    sendCMD(myCommand)
    # waiting for a response, max 30 seconds
    WaitTime = 30
    while WaitTime >= 1:
        if fileExists(IPTVdaemonRET) or xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.RET') != '':
            break
        time.sleep(1)
        WaitTime = WaitTime - 1
        myLog("doCMD Waiting %ds" % WaitTime)
        
    if not fileExists(IPTVdaemonRET) and xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.RET') == '':
        retVal="Timeout"
    elif xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.RET') != '':
        retVal = xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.RET')
    elif fileExists(IPTVdaemonRET):
        with open(IPTVdaemonRET, "r") as fp:
            retVal = fp.read()
            fp.close()
    myLog("doCMD returned: %s" % retVal)
    SL.close()
    return retVal

def isERROR(myAnswer):
    if myAnswer.lower().startswith('timeout'):
        showDialog(_(30403), myAnswer)
        return True
    elif myAnswer.lower().startswith('ERROR'):
        showDialog(_(30403), myAnswer)
        return True
    elif myAnswer == 'wrongindex':
        showDialog(_(30403), 'Wrong index!')
        return True
    elif myAnswer == 'novalidurls':
        showDialog(_(30403), 'No valid urls')
        return True
    return False
#################################################################################################################################################
def showTopOptions():
    #EXIT
    if ADDON.getSetting("showExitOption") == "true":
        list_item = xbmcgui.ListItem(label = _(30425))
        url = get_url(action='exitPlugin')
        is_folder = False
        list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/exit.png')})
        xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    #HOSTS LIST
    if ADDON.getSetting("showHostListOption") == "true":
        list_item = xbmcgui.ListItem(label = _(30426))
        url = get_url(action='reloadHostsList')
        is_folder = False
        list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/home.png')})
        xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    #INITIAL LIST
    if ADDON.getSetting("showInitialListOption") == "true":
        list_item = xbmcgui.ListItem(label = _(30427))
        url = get_url(action='InitialList')
        is_folder = False
        list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/initlist.png')})
        xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    return
    
def showDownloaderItem():
    for filename in os.listdir(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka")):
        if filename.endswith('.wget'):
            myLog('Found at least one wget status file, displaying menut then ;)')
            list_item = xbmcgui.ListItem(label = _(30424))
            url = get_url(action='wgetStatus')
            is_folder = True
            list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/download.png')})
            xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
            break
    return

def getDownloaderStatus():
    for filename in os.listdir(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka")):
        if filename.endswith('.wget'):
            myLog('Found: [%s]' % filename)
            list_item = xbmcgui.ListItem(label = filename[:-5])
            url = get_url(action='wgetRead', fileName=filename)
            is_folder = False
            last_Lines = ''
            with open(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka") , filename)) as f:
                last_Lines = f.readlines()[-5:]
                f.close()
            if ''.join(last_Lines).find('100%') > 0:
                list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/done.png')})
            else:
                list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/progress.png')})
            xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    #last but not least delete all status files        
    list_item = xbmcgui.ListItem(label = '> Delete all status files <')
    url = get_url(action='wgetDelete')
    is_folder = False
    list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/delete.png')})
    xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    #closing directory
    xbmcplugin.endOfDirectory(ADDON_handle)
    return

def SelectHost():
    for host in HostsList:
            if ADDON.getSetting(host[0]) == 'true':
                hostName = host[1].replace("https:",'').replace("http:",'').replace("/",'').replace("www.",'')
                hostImage = '%s/icons/%s.png' % (ADDON.getSetting("kodiIPTVpath"), host[0])
                list_item = xbmcgui.ListItem(label = hostName)
                list_item.setArt({'thumb': hostImage,})
                list_item.setInfo('video', {'title': hostName, 'genre': hostName})
                url = get_url(action='startHost', host=host[0])
                myLog(url)
                is_folder = True
                # Add our item to the Kodi virtual folder listing.
                xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(ADDON_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(ADDON_handle)
    return

def ContextMenu():
    liz=xbmcgui.ListItem('You directory label', iconImage="DefaultFolder.png", thumbnailImage='your icon')
    contextMenuItems = []
    contextMenuItems.append(('This is a context menu entry', 'XBMC.RunPlugin(Your_path_goes_here)',))
    liz.addContextMenuItems(contextMenuItems, replaceItems=True)
    myUrl = get_url(action='wgetStatus')
    xbmcplugin.addDirectoryItem(handle=ADDON_handle,url=myUrl,listitem=liz,isFolder=False)
#    commands = []
#    #commands.append(( 'Jump to page', 'XBMC.Container.Update(%s/%s/jump)' % (plugin.root, obj['board']), ))
#    commands.append(( 'Exit plugin', 'XBMC.ActivateWindow(Home)', ))
#    list_item = xbmcgui.ListItem(label = 'aqq', iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
#    list_item.addContextMenuItems(commands)
#    xbmcplugin.addDirectoryItem(ADDON_handle, get_url(action='exitPlugin'), list_item, True)
    
def playVideo(path, videoName):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :type path: str
    """
    play_item = xbmcgui.ListItem(path=path) # Create a playable item with a path to play.
    xbmcplugin.setResolvedUrl(ADDON_handle, True, listitem=play_item) # Pass the item to the Kodi player.

def prepareKODIitemsList(itemsList):
    exec(itemsList)
    for item in ItemsList:
        myAction = 'NOACTION'
        list_item = xbmcgui.ListItem(label = item['name'], label2 = item['descr'])
        list_item.setInfo('video', {'title': item['name'], 'genre': item['name']})
        myID = item['id']
        myLevel = ADDON.getSetting("currenLevel")
        if item['type'] == 'VIDEO':
            is_folder = True
            myAction = 'playMovie'
            list_item.setArt({'thumb': item['icon'],
                  #'icon': item['icon'],
                  #'fanart': VIDEOS[category][0]['thumb']
                  })
        elif item['type'] == 'CATEGORY':
            is_folder = True
            if not item['name'].lower() in ['search history',]:
                myAction = 'getList'
        elif item['type'] == 'SEARCH':
            is_folder = True
            myAction = 'SEARCH'
            list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/SearchItem.png')})
        if myAction != 'NOACTION':
            url = get_url(action = myAction, id = myID, level = myLevel, name = item['name'])
            xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
            myLog('action=%s id=%s level=%s' % (myAction,myID,myLevel))
    return

def prepareKODIurlsList(urlsList, videoName):
    exec(urlsList)
    for item in UrlsList:
        list_item = xbmcgui.ListItem(label = item['name'])
        #list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
        #          'icon': VIDEOS[category][0]['thumb'],
        #          'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        list_item.setInfo('video', {'title': videoName}) # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setProperty('IsPlayable', 'true')
        myID = item['id']
        myUrl = item['url']
        myLevel = ADDON.getSetting("currenLevel")
        is_folder = False
        url = get_url(action = 'playUrl',
                      id = myID,
                      level = myLevel,
                      urlNeedsResolve=item['urlNeedsResolve'],
                      url=myUrl,
                      name=videoName) # Create a URL for a plugin recursive call.
        if ADDON.getSetting("PlayerMode") == "2":
            list_item.setArt({'thumb': xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/icons/download.png')})
        xbmcplugin.addDirectoryItem(ADDON_handle, url, list_item, is_folder)
        myLog('action=playUrl id=%s level=%s' % (myID,myLevel))
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        #xbmcplugin.addSortMethod(ADDON_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        # Finish creating a virtual folder.

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### MAIN FUNCTION ###
def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### uruchomienie hosta i pobieranie listy inicjalnej ###
        if params['action'] == 'startHost':
            SL = StatusLine(_(30401) % params['host'])
            SL.show()
            restartDaemon(params['host'])
            SL.close()
            if not isDeamonWorking():
                myLog('Error starting daemon for host %s' % (params['host']))
                showDialog(_(30403), _(30404) % (params['host']))
            else:
                myLog('>startHost %s, pid:%s' % (params['host'],ADDON.getSetting("daemonPID")))
                ADDON.setSetting("selectedHost", doCMD("Title", _(30402)))
                ANSWER = doCMD("InitList", _(30405))
                if not isERROR(ANSWER) and ANSWER.startswith( 'ItemsList=' ):
                    ADDON.setSetting("currenLevel", "1")
                    prepareKODIitemsList(ANSWER)
                elif isinstance(ANSWER, (str, unicode)):
                    showDialog(_(30403), ANSWER)
            xbmcplugin.endOfDirectory(ADDON_handle)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### pobieranie kategorii
        elif params['action'] == 'getList':
            showTopOptions()
            while int(params['level']) < int(ADDON.getSetting("currenLevel")):
                ANSWER = doCMD("PreviousList", "..")
                ADDON.setSetting("currenLevel", "%d" % (int(ADDON.getSetting("currenLevel")) - 1) )
            ANSWER = doCMD("ListForItem=%s" % params['id'], _(30406), params['name'])
            if not isERROR(ANSWER) and ANSWER.startswith( 'ItemsList=' ):
                ADDON.setSetting("currenLevel", "%d" % (int(ADDON.getSetting("currenLevel")) + 1) )
                prepareKODIitemsList(ANSWER)
            xbmcplugin.endOfDirectory(ADDON_handle)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### pobieranie linkow do filmu
        elif params['action'] == 'playMovie':
            ANSWER = doCMD("getVideoLinks=%s" % params['id'], _(30407) , params['name'])
            if not isERROR(ANSWER) and ANSWER.startswith( 'UrlsList=' ):
                prepareKODIurlsList(ANSWER,params['name'])
            xbmcplugin.endOfDirectory(ADDON_handle)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### Downloader status
        elif params['action'] == 'wgetStatus':
            getDownloaderStatus()
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### read status
        elif params['action'] == 'wgetRead':
            if not fileExists(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName'])):
                showDialog("Info", _(30408))
                return
            selRet=selectionDialog(_(30409), [_(30410),_(30411),_(30412)])
            if selRet < 0: #user pressed cancel
                return
            elif selRet == 0:
                DocFile = ''
                iindex=0
                lastline=''
                for line in open(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName']), 'r').readlines():
                    if line.find('..........') > 0 and not line.find('100%') > 0:
                        iindex += 1
                        if iindex < 3:
                            DocFile += line.replace('..........','.').strip() + '[CR]'
                        elif iindex == 3:
                            DocFile += '~~~skip lines~~~[CR]'
                        else:
                            lastline = line.replace('..........','.').strip() + '[CR]'
                    elif line.find('100%') > 0:
                        DocFile += lastline + line.replace('..........','.').strip() + '[CR]'
                    else:
                        DocFile += line.replace('..........','.').strip() + '[CR]'
                showDialog("Status", DocFile)
            elif selRet == 1:
                os.remove(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName']))
                showDialog("Status", _(30413))
            elif selRet == 2:
                os.remove(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName']))
                if fileExists(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName'][:-5])):
                    os.remove(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName'][:-5]))
                showDialog("Status", _(30414) + os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),params['fileName'][:-5]))
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### read status
        elif params['action'] == 'wgetDelete':
            iindex=0
            for filename in os.listdir(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka")):
                if filename.endswith('.wget'):
                    os.remove(os.path.join(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"),filename))
                    iindex += 1
            if iindex ==1:
                showDialog("Info", _(30415))
            elif iindex >1:
                showDialog("Info", _(30416) % iindex)
            else:
                showDialog("Info", _(30417))
            return
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### odtwarzanie filmu
        elif params['action'] == 'playUrl':
            myLog('>playUrl[mode:%s] urlNeedsResolve:%s, %s' % (ADDON.getSetting("PlayerMode"),params['urlNeedsResolve'],params['url']))
            if params['urlNeedsResolve'] == '1':
                #myUrl = doCMD("ResolveURL=%s" % params['url'])
                myUrl = doCMD("ResolveURL=%s" % params['id'])
                if isERROR(myUrl):
                    myUrl = ''
            else:
                myUrl = params['url']
            if myUrl != '':
                if ADDON.getSetting("PlayerMode") == "1": # 1-player with buffering
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Info', _(30418))
                    ANSWER = doCMD("DownloadURL=%s" % myUrl, _(30419))
                    waitTime=10
                    ScaleMultiplier=100/waitTime
                    while waitTime >0:
                        pDialog.update(100 - waitTime * ScaleMultiplier, _(30420))
                        time.sleep(1)
                        waitTime = waitTime -1
                    pDialog.close()
                    if fileExists(ANSWER):
                        playVideo(ANSWER, params['name'])
                    else:
                        showDialog(_(30403), _(30421))
                elif ADDON.getSetting("PlayerMode") == "2": #2-recorder
                    ANSWER = doCMD("DownloadURL=%s" % myUrl, _(30422))
                    if os.path.exists(ANSWER):
                        showDialog("Info", _(30423) % ANSWER)
                else: #  0-player 
                    playVideo(myUrl, params['name'])
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### SZUKANIE
        elif params['action'] == 'SEARCH':
            kb = xbmc.Keyboard(xbmcgui.Window(10000).getProperty('plugin.video.IPTVplayer.SEARCH'), 'Search for', False)
            kb.doModal()
            if (kb.isConfirmed()):
                retText = kb.getText()
                xbmcgui.Window(10000).setProperty("plugin.video.IPTVplayer.SEARCH", retText)
                ANSWER = doCMD("Search=%s" % retText)
                if not isERROR(ANSWER) and ANSWER.startswith( 'ItemsList=' ):
                    ADDON.setSetting("currenLevel", "%d" % (int(ADDON.getSetting("currenLevel")) + 1) )
                    prepareKODIitemsList(ANSWER)
            xbmcplugin.endOfDirectory(ADDON_handle)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### NA POCZATEK
        elif params['action'] == 'InitialList':
            xbmc.executebuiltin('XBMC.Container.Update("%s", "replace")' % 'plugin://plugin.video.IPTVplayer/?action=startHost&host=cdapl')
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### DO LISTY SERWISOW
        elif params['action'] == 'reloadHostsList':
            stopDaemon()
            xbmc.executebuiltin('XBMC.Container.Update("%s", "replace")' % ADDON_url)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### KONIEC
        elif params['action'] == 'exitPlugin':
            EXIT()
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ### 
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of hosts
        if not fileExists(ADDON.getSetting("config.plugins.iptvplayer.SciezkaCache")):
            showDialog(_(30403), _(30430))
            ADDON.openSettings()
        elif not os.access(ADDON.getSetting("config.plugins.iptvplayer.NaszaSciezka"), os.W_OK):
            showDialog(_(30403), _(30431))
            ADDON.openSettings()
        elif not os.access(ADDON.getSetting("config.plugins.iptvplayer.NaszaTMP"), os.W_OK):
            showDialog(_(30403), _(30432))
            ADDON.openSettings()
        else:
            #ustawienie krytycznych ścieżek
            if ADDON.getSetting("kodiIPTVpath") == '-' or not os.access(ADDON.getSetting("kodiIPTVpath"), os.W_OK):
                ADDON.setSetting("kodiIPTVpath", xbmc.translatePath('special://home/addons/plugin.video.IPTVplayer/resources/E2emulator/Plugins/Extensions/IPTVPlayer'))
            if ADDON.getSetting("config.misc.sysTempPath") == '-' or not os.access(ADDON.getSetting("config.misc.sysTempPath"), os.W_OK):
                ADDON.setSetting("config.misc.sysTempPath",xbmc.translatePath( "special://temp" ))
            if not os.path.exists(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon')):
                os.makedirs(buildPath(ADDON.getSetting("config.misc.sysTempPath"),'.IPTVdaemon'))
            if ADDON.getSetting("config.misc.sysTempPath") != ADDON.getSetting("addonTempFolder"):
                if os.path.exists(ADDON.getSetting("addonTempFolder")) and os.access(ADDON.getSetting("addonTempFolder"), os.W_OK):
                    ADDON.setSetting("config.misc.sysTempPath",ADDON.getSetting("addonTempFolder"))
                else:
                    ADDON.setSetting("addonTempFolder",ADDON.getSetting("config.misc.sysTempPath"))
            # czyszczenie ewentualnych smieci
            ADDON.setSetting("currenLevel", "0")
            ADDON.setSetting("selectedID", "-1")
            
            if ADDON.getSetting("selectedHost") != "-":
                ADDON.setSetting("selectedHost", "-")
                ADDON.setSetting("updateE2settings", "0") # jesli juz bylismy w jakims hoscie to nie ma potrzeby konfigurowac e2 jeszcze raz
            else:
                ADDON.setSetting("updateE2settings", "1")
                
            if isDeamonWorking():
                myLog("Deamon is Working, stopping it")
                stopDaemon()
            myLog("[%s:kodiIPTV] >initial list of hosts" % os.name)
            #jesli sa pliki downloadera, wyswietlamy link do niego w glownym menu
            showDownloaderItem()
            #wyswietlamy liste hostow
            ContextMenu()
            SelectHost()

def EXIT():
    myLog('exit')
    stopDaemon()
    xbmc.executebuiltin("XBMC.Container.Update(addons://sources/video,replace)")
    xbmc.executebuiltin("XBMC.ActivateWindow(Home)")

def patchAndroid():
    if os.path.exists('/storage/external_storage/') or os.path.exists('/storage/emulated/'): #patch for Android only
        zopePath=xbmc.translatePath('special://home/addons/script.module.zope.interface/lib/zope/')
        myLog('patchAndroid > found common Android paths, patching %s' % zopePath)
        if not os.path.exists(zopePath + "__init__.py.org") and os.path.exists(zopePath + "__init__.py"):
            os.rename(zopePath + "__init__.py", zopePath + "__init__.py.org")
            with open(zopePath + "__init__.py", 'w') as f:
                f.write("""# this is a namespace package patched by j00zek
try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
""")
                f.close()
                if os.path.exists(zopePath + "__init__.pyo"):
                    os.remove(zopePath + "__init__.pyo")
    else:
        myLog('patchAndroid > common Android paths not found, is it Android?')

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    patchAndroid()
    router(sys.argv[2][1:])
