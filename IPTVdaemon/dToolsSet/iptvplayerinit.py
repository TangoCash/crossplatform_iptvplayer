# -*- coding: utf-8 -*-
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.Language import language
import gettext
import os
import threading
###################################################
# Globals
###################################################
gInitIPTVPlayer = True # is initialization of IPTVPlayer is needed
PluginLanguageDomain = "IPTVPlayer"
PluginLanguagePath = "Extensions/IPTVPlayer/locale"
gSetIPTVPlayerLastHostError = ""

def localeInit():
    lang = 'pl' #TO DO language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    print(PluginLanguageDomain + " set language to " + lang)
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def TranslateTXT(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

localeInit()

def TranslateTXT(txt):
    return txt

def IPTVPlayerNeedInit(value=None):
    return False
    
def SetIPTVPlayerLastHostError(value=""):
    pass

def GetIPTVPlayerLastHostError(clear=True):
    return ""

class IPTVPlayerNotificationList(object):
    
    def __init__(self):
        self.notificationsList = []
        self.mainLock = threading.Lock()
        # this flag will be checked with mutex taken 
        # to less lock check
        self.empty = True
        
    def clearQueue(self):
        self.mainLock.acquire()
        self.notificationsList = []
        self.empty = True
        self.mainLock.release()
        
    def isEmpty(self):
        try:
            if self.empty:
                return True
        except Exception:
            pass
        return False
    
    def push(self, message, type="message", timeout=5): #, allowDuplicates=True
        ret = False
        self.mainLock.acquire()
        try:
            notification = IPTVPlayerNotification('IPTVPlayer', message, type, timeout)
            self.notificationsList.append(notification)
            self.empty = False
            ret = True
        except Exception:
            print(str(e))

        self.mainLock.release()
        return ret

    def pop(self, popAllSameNotificationsAtOnce=True):
        notification = None
        self.mainLock.acquire()
        try:
            notification = self.notificationsList.pop()
            if popAllSameNotificationsAtOnce:
                newList = []
                for item in self.notificationsList:
                    if item != notification:
                        newList.append(item)
                self.notificationsList = newList
        except Exception as e:
            print(str(e))
            
        if 0 == len(self.notificationsList):
            self.empty = True
        
        self.mainLock.release()
        return notification

gIPTVPlayerNotificationList = IPTVPlayerNotificationList()

def GetIPTVNotify():
    global gIPTVPlayerNotificationList
    return gIPTVPlayerNotificationList

