# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, DownloadFile, eConnectCallback
###################################################
# FOREIGN import
###################################################
from enigma import eConsoleAppContainer
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from Components.config import config, configfile
from Components.Language import language
import gettext
import os, sys
###################################################

###################################################
# Globals
###################################################
gInitIPTVPlayer = True # is initialization of IPTVPlayer is needed
PluginLanguageDomain = "IPTVPlayer"
PluginLanguagePath = "Extensions/IPTVPlayer/locale"
gSetIPTVPlayerLastHostError = ""
###################################################
def localeInit():
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    printDBG(PluginLanguageDomain + " set language to " + lang)
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def TranslateTXT(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)

def IPTVPlayerNeedInit(value=None):
    global gInitIPTVPlayer
    if value in [True, False]: gInitIPTVPlayer = value
    return gInitIPTVPlayer
    
def SetIPTVPlayerLastHostError(value=""):
    global gSetIPTVPlayerLastHostError
    gSetIPTVPlayerLastHostError = value

def GetIPTVPlayerLastHostError(clear=True):
    global gSetIPTVPlayerLastHostError
    tmp = gSetIPTVPlayerLastHostError
    if clear: gSetIPTVPlayerLastHostError = ""
    return tmp


