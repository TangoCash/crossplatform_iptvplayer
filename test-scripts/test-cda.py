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

hostName='cdapl' #name of hostfile, without py
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
#Filmy wideo
myID=0
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#glowna
myID=0
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#krotkie
myID=1
ret= host.getListForItem(myID,0,ret.value[myID])
print ToItemsListTable(ret.value, "PYTHON")
#pierwsze na liscie
myID=0
retUrl= host.getLinksForVideo(myID,ret.value[myID])
print ToUrlsTable(retUrl.value, "PYTHON")
#resolveURL
if retUrl.value[myID].urlNeedsResolve == 1:
    #linksList = []
    myID=0
    linksList= host.getResolvedURL(retUrl.value[myID].url).value
    print retUrl.value[myID].url
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

#currID=0
#ret=host.getLinksForVideo(currID,ret.value[currID])
#print ToLuaUrlsTable(ret.value)

#####################################################################'Refresh'
#ret = None
#ret=host.getCurrentList()
#print ToItemsListTable(ret.value, "PYTHON")
#####################################################################'ForItem'
#ret= host.getListForItem(0,0,ret.value[0])
#print ToItemsListTable(ret.value, "PYTHON")

#ret= host.getListForItem(0,0,ret.value[0])
#print ToItemsListTable(ret.value, "PYTHON")

#ret= host.getListForItem(0,0,ret.value[4])
#currID=0
#ret=host.getLinksForVideo(currID,ret.value[currID])
#print ToLuaUrlsTable(ret.value)

#####################################################################'Previous'
#ret= host.getPrevList()
#print ToItemsListTable(ret.value, "PYTHON")
#'ForVideoLinks'
#asynccall.AsyncMethod(self.host.getLinksForVideo, self.selectHostVideoLinksCallback, True)(currSelIndex, selItem)

#####################################################################'ResolveURL':
#myURL=ret.value[0].url
#print myURL
#ret= host.getResolvedURL(myURL)
#
#####################################################################'ForSearch':
#asynccall.AsyncMethod(self.host.getSearchResults, boundFunction(self.callbackGetList, {}), True)(self.searchPattern, self.searchType)
#searchPattern = raw_input('Enter search pattern:')
#ret = host.getSearchResults(searchPattern)
#print ret.value

#currID=0
#ret=host.getLinksForVideo(currID,ret.value[currID])
#print ToLuaUrlsTable(ret.value)

#host configuration
#hostconfig = __import__('hosts.' + hostName, globals(), locals(), ['GetConfigList'], -1)
#ConfList = hostconfig.GetConfigList()
#index=0
#ConfList[1][1].value = True
#ConfigItems="HostConfig={\n"
#for item in ConfList:
#    luaItem = '\t{id=%d, name="%s", value="%s", ' % (index, item[0].strip(), item[1].value)
#    if 'choices' in vars(item[1]):
#        luaItem += 'type="ConfigSelection", '
#        selections=""
#        iindex2 =0
#        for choice in item[1].choices.choices:
#            selections += '\n\t\t{id=%d, name="%s", value="%s"},' %(iindex2, choice[1], choice[0])
#            iindex2 +=1
#        luaItem += "choices={\n%s\n\t},\n" % selections
#    elif 'descriptions' in vars(item[1]):
#        luaItem += ', type="ConfigYesNo"},\n'
#    elif 'text' in vars(item[1]) and 'fixed_size' in vars(item[1]):
#        luaItem += ', type="ConfigText"},\n'
#    else:
#        pprint (vars(item[1]))
    
#    index += 1
#    ConfigItems += luaItem
#ConfigItems +="\t}\n"
#print ConfigItems
#print ToLuaConfigTable(ConfList)