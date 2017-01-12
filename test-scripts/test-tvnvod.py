#!/usr/bin/env python
# cd /usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/
# execfile('testcmdline.py')
import sys


if '/usr/share/E2emulator' not in sys.path:
    sys.path.append('/usr/share/E2emulator')
    
import time, os
from Plugins.Extensions.IPTVPlayer.dToolsSet.DaemonTools import *
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Components.config import config
from Components.SetupDevices import InitSetupDevices #inits correct language based on neutrino settings
import Plugins.Extensions.IPTVPlayer.icomponents.iptvconfigmenu

hostName='tvnvod' #name of hostfile, without py
TopList = []
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem
_temp = __import__('hosts.' + hostName, globals(), locals(), ['IPTVHost'], -1)
print ('Tytul=', _temp.gettytul())
host = _temp.IPTVHost()
print 'LogoPath=',host.getLogoPath().value #zwraca sciezke do logo
print 'Supports=',host.getSupportedFavoritesTypes().value
#CDisplayListItem values:name|description|type|urlItems=[]|urlSeparateRequest = 0|iconimage|possibleTypesOfSearch
#CUrlItem values:name|url|urlNeedsResolve (additional request needed to resolve url

#####################################################################'Initial'
ret=host.getInitList() # this gest list of IHost items
print ToItemsListTable(ret.value, "PYTHON")
#Kategorie
myID=0
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#programy
myID=10
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#newsy
myID=8
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#fakty
myID=0
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#pierwsze na liscie
myID=0
ret= host.getLinksForVideo(myID,ret.value[myID])
print ToUrlsTable(ret.value, "PYTHON")
#resolveURL
if ret.value[myID].urlNeedsResolve == 1:
    #linksList = []
    myID=0
    linksList= host.getResolvedURL(ret.value[myID].url).value
    print ret.value[myID].url
    print linksList
    print "Liczba linkow:", len(linksList)
    #pobieranie url-a
    if isinstance(linksList[0], CUrlItem):
        print "CUrlItem:", linksList[0].url
    elif isinstance(linksList, basestring):
        print "basestring:", linksList[0]
    elif isinstance(linksList, basestring):
        print "basestring:", linksList[0]
    elif isinstance(linksList, (list, tuple)):
        print "list, tuple:", linksList[0]
    else:
        print "unknown"
