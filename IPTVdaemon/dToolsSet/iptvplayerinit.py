# -*- coding: utf-8 -*-
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.Language import language
import gettext
import os
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


