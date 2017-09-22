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
# FOREIGN import
###################################################
from Components.config import config, ConfigText
#from Tools.Directories import resolveFilename, fileExists
#from urllib2 import Request, urlopen, URLError, HTTPError
from datetime import datetime
#import urllib
#import urllib2
#import traceback
#import re
#import sys
import os
#import stat
#import time
#import codecs
#try:    import json
#except: import simplejson as json
from tempfile import gettempdir

try:
    config.misc.sysTempPath = ConfigText(default = gettempdir() , fixed_size = False)
except Exception, e:
    print "Exception getting tempdir occured is it sheety Android?... (%s)" % str(e)
    for TP in ['/storage/sdcard1', '/storage/sda1/', '/data/local/tmp/', '/tmp' ]:
        if os.path.exists(TP) and os.access(TP, os.W_OK):
            config.misc.sysTempPath = ConfigText(default = TP , fixed_size = False)
            break
    
#############################################################
# e2 support functions
#############################################################
def LoadE2ConfFile(filename):
    try:
        config.loadFromFile(filename, True)
    except IOError, e:
        print "unable to load config (%s), assuming defaults..." % str(e)
    
def SaveE2ConfFile(filename):
    config.saveToFile(filename)
    
#############################################################
# processing daemon commands
#############################################################
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
    return "[" + tmptext + "]\n"

def printDBG( text ):
    logFile = os.path.join(config.misc.sysTempPath.value,'IPTVdaemon.log')
    try:
        f = open(logFile, 'a')
        f.write( dumpclean(text) )
        f.close
    except:
        try:
            msg = '%s' % traceback.format_exc()
            f = open(logFile, 'a')
            f.write(msg + '\n')
            f.close
        except:
            pass

def daemonLog(text):
    with open(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','log'), 'a') as f:
        f.write('%s\n' % text )
        f.close
    printDBG(text)

def myAnswer(text = ''):
    daemonLog("<%s" % text)
    with open(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','ret'), 'w') as f:
        f.write(text)
        f.close

def getCMD():
    cmd = ''
    IPTVdaemonCMD=os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','cmd')
    IPTVdaemonRET=os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','ret')
    if os.path.exists(IPTVdaemonCMD):
        if os.path.exists(IPTVdaemonRET):
            os.remove(IPTVdaemonRET)
        with open(IPTVdaemonCMD, 'r') as f:
            cmd = f.readline().strip()
            f.close
            os.remove(IPTVdaemonCMD)
        daemonLog("getCMD>%s" % cmd)
    return cmd

#############################################################
# prints logs to the file(s)
#############################################################
# debugs
def clearLogsPaths(folderName):
    currTime   = datetime.now()
    if not os.path.exists(folderName):
        os.makedirs(folderName)
    try:
        with open(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','log'), 'w') as f:
            f.write('=== IPTV daemon starts %s ===\n' % datetime.now() )
            f.close
        with open(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','errors'), 'w') as f:
            f.close
        if os.path.exists(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','pid')):
            os.remove(os.path.join(config.misc.sysTempPath.value,'.IPTVdaemon','pid'))
    except:
        pass
    try:
        with open(os.path.join(config.misc.sysTempPath.value,'IPTVplayer.log'), 'w') as f:
            f.write('=== IPTVplayer 4 Neutrino/Kodi starts %s ===\n' %datetime.now() )
            f.close

    except:
        pass

def logToFile( FileName, text = ''):
    try:
        f = open(FileName, 'a')
        f.write(text + '\n')
        f.close
    except:
        pass
  
#############################################################
# converts data to lua list
#############################################################
def removeSpecialChars(text):
    text = text.replace('\n', ' ').replace('\r', '').replace('\t', ' ').replace('"', "'").replace('  ', " ").strip()
    text = text.replace('&oacute;', 'ó').replace('&Oacute;', 'Ó')
    text = text.replace('&quot;', "'").replace('&#34;', "'").replace('&nbsp;', ' ').replace('&#160;', " ")
    
    return text.strip()

def ToUrlsTable(retval, clientType):
    index=0
    if clientType == 'LUA': urlsTable="UrlsList={\n"
    elif clientType == 'PYTHON': urlsTable = "UrlsList=[\n"
    for item in retval:
        try:
            iname= removeSpecialChars(item.name)
            iurl= item.url.replace("ext://url/","") #to chyba sss zrobil do wymuszenia extplayera przyklad pierwszatv
            iurlNeedsResolve= int(item.urlNeedsResolve)
            if clientType == 'LUA': urlsTable += '\t{id=%d, name="%s", url="%s", urlNeedsResolve=%d},\n' % (index,iname,iurl,iurlNeedsResolve)
            elif clientType == 'PYTHON': urlsTable += "\t{'id':%d, 'name':\"%s\", 'url':'%s', 'urlNeedsResolve':%d},\n" % (index,iname,iurl,iurlNeedsResolve)
            index += 1
        except:
            printDBG("ToUrlsTable exception") #pass
    if clientType == 'LUA': urlsTable += "}\n"
    elif clientType == 'PYTHON': urlsTable += "]\n"
    return urlsTable

def ToConfigTable(ConfList, clientType):
    index=0
    ConfigItems="HostConfig={\n"
    for item in ConfList:
        luaValue = item[1].value
        luaItem = '\t{id=%d, name="%s", value="%s", ' % (index, item[0].strip(), item[1].value)
        if 'choices' in vars(item[1]):
            luaItem += 'type="ConfigSelection", '
            selections=""
            chNames=''
            chValues=''
            iindex2 =0
            for choice in item[1].choices.choices:
                selections += '\n\t\t\t{id=%d, name="%s", value="%s"},' %(iindex2, choice[1], choice[0])
                chNames += '"%s",\n\t\t\t' % str(choice[1])
                chValues += '"%s",\n\t\t\t ' % str(choice[0])
                iindex2 +=1
            #luaItem += "\n\t\tchoices={\n%s\n\t\t},\n\tchNames={%s},\t\nchValues={%s},\n},\n" % (selections,chNames,chValues)
            iindex2 =0
            for choice in item[1].choices.choices:
                if luaValue == choice[0]:
                    luaValName = str(choice[1])
            luaItem += 'valName="%s", ' % luaValName
            luaItem += "\n\t\tchNames={%s},\n\t\tchValues={%s},\n},\n" % (chNames,chValues)
        elif 'descriptions' in vars(item[1]):
            luaItem += 'type="ConfigYesNo"},\n'
        elif 'text' in vars(item[1]) and 'fixed_size' in vars(item[1]):
            luaItem += 'type="ConfigText"},\n'
        else:
            pprint (vars(item[1]))
    
        index += 1
        ConfigItems += luaItem
    ConfigItems +="}\n"
    return ConfigItems

def ToItemsListTable(retval, clientType):
    index=0
    if clientType == 'LUA': itemsTable="ItemsList={\n"
    elif clientType == 'PYTHON': itemsTable="ItemsList=[\n"
    for item in retval:
        try:
            iname= removeSpecialChars(item.name)
            itype=item.type
            idescr= removeSpecialChars(item.description)
            if itype == "CATEGORY":
                icon = 'folder'
            elif itype == "SEARCH":
                icon = 'question'
            elif itype == "VIDEO":
                icon = item.iconimage #'video'
            elif itype == "AUDIO":
                icon = 'mp3'
            else:
                icon = ''
            if clientType == 'LUA': itemsTable += '\t{id=%d, name="%s", descr="%s", type="%s", icon="%s", },\n' %(index,iname,idescr,itype,icon)
            elif clientType == 'PYTHON': itemsTable += "\t{'id':%d, 'name':\"%s\", 'descr':\"%s\", 'type':'%s', 'icon':'%s'},\n" %(index,iname,idescr,itype,icon)
            index += 1
        except:
            pass
    if clientType == 'LUA': itemsTable += "}\n"
    elif clientType == 'PYTHON': itemsTable += "]\n"
    return itemsTable
