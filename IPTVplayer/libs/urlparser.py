# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, CSelOneLink, GetCookieDir, byteify, formatBytes, GetPyScriptCmd, GetTmpDir, rm, GetDefaultLang, GetDukPath, CreateTmpFile
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.md5Hash import MD5

from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v2 import UnCaptchaReCaptcha
from Plugins.Extensions.IPTVPlayer.libs.gledajfilmDecrypter import gledajfilmDecrypter
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes  import AES
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.base import noPadding
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import unescapeHTML, clean_html, _unquote
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, unpackJS, \
                                                               getParamsTouple, JS_FromCharCode, \
                                                               JS_toString, \
                                                               VIDUPME_decryptPlayerParams,    \
                                                               VIDEOWEED_unpackJSPlayerParams, \
                                                               SAWLIVETV_decryptPlayerParams,  \
                                                               VIDEOMEGA_decryptPlayerParams, \
                                                               OPENLOADIO_decryptPlayerParams, \
                                                               TEAMCASTPL_decryptPlayerParams, \
                                                               VIDEOWEED_decryptPlayerParams, \
                                                               KINGFILESNET_decryptPlayerParams, \
                                                               captchaParser, \
                                                               getDirectM3U8Playlist, \
                                                               getMPDLinksWithMeta, \
                                                               getF4MLinksWithMeta, \
                                                               decorateUrl, \
                                                               MYOBFUSCATECOM_OIO, \
                                                               MYOBFUSCATECOM_0ll, \
                                                               int2base, drdX_fx, \
                                                               unicode_escape, JS_FromCharCode, pythonUnescape
from Plugins.Extensions.IPTVPlayer.libs.jjdecode import JJDecoder
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import iptv_execute, iptv_js_execute, MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
import socket
import string
import base64
import math

from xml.etree import cElementTree
from random import random, randint, randrange
from urlparse import urlparse, parse_qs
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config

try: import json
except Exception: import simplejson as json
    
import codecs
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.youtube import YoutubeIE
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.mtv import GametrailersIE
    
try:    from urlparse import urlsplit, urlunsplit
except Exception: printExc()
###################################################
class urlparser:
    def __init__(self):
        self.cm = common()
        self.pp = pageParser()
        self.setHostsMap()
        
    @staticmethod
    def getDomain(url, onlyDomain=True):
        parsed_uri = urlparse( url )
        if onlyDomain:
            domain = '{uri.netloc}'.format(uri=parsed_uri)
        else:
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain
    
    @staticmethod
    def decorateUrl(url, metaParams={}):
        return decorateUrl(url, metaParams)
        
    @staticmethod
    def decorateParamsFromUrl(baseUrl, overwrite=False):
        printDBG("urlparser.decorateParamsFromUrl >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + baseUrl)
        tmp        = baseUrl.split('|')
        baseUrl    = urlparser.decorateUrl(tmp[0].strip(), strwithmeta(baseUrl).meta)
        KEYS_TAB = list(DMHelper.HANDLED_HTTP_HEADER_PARAMS)
        KEYS_TAB.extend(["iptv_audio_url", "Host", "Accept", "MPEGTS-Live"])
        if 2 == len(tmp):
            baseParams = tmp[1].strip()
            try:
                params  = parse_qs(baseParams)
                for key in params.keys():
                    if key not in KEYS_TAB: continue
                    if not overwrite and key in baseUrl.meta: continue
                    try: baseUrl.meta[key] = params[key][0]
                    except Exception: printExc()
            except Exception: printExc()
        return baseUrl

    def preparHostForSelect(self, v, resolveLink = False):
        valTab = []
        i = 0
        if len(v) > 0:
            for url in (v.values() if type(v) is dict else v):
                if 1 == self.checkHostSupport(url):
                    hostName = self.getHostName(url, True)
                    i=i+1
                    if resolveLink:
                        url = self.getVideoLink( url )
                    if isinstance(url, basestring) and url.startswith('http'):
                        valTab.append({'name': (str(i) + '. ' + hostName), 'url': url})
        return valTab

    def getItemTitles(self, table):
        out = []
        for i in range(len(table)):
            value = table[i]
            out.append(value[0])
        return out

#anyfiles, bestreams, cda, cloudyvideos, flashx, neodrive, novamov, nowvideo, openload, played, realvid, streamin, streamplay, thevideo, video, videomega, videowood, vidgg, vidspot, 
#vidto, vidup, vidzer, vodlocker, vshare, vshareio, yourvideohost, youtube, youwatch
#    neodrive
    def setHostsMap(self):
        self.hostMap = {
                       'putlocker.com':        self.pp.parserFIREDRIVE     , 
                       'firedrive.com':        self.pp.parserFIREDRIVE     , 
                       'sockshare.com':        self.pp.parserSOCKSHARE     ,
                       'megustavid.com':       self.pp.parserMEGUSTAVID    ,
                       #'hd3d.cc':              self.pp.parserHD3D          ,
                       'sprocked.com':         self.pp.parserSPROCKED      ,
                       'wgrane.pl':            self.pp.parserWGRANE        ,
                       'cda.pl':               self.pp.parserCDA           ,
                       'ebd.cda.pl':           self.pp.parserCDA           ,
                       'video.anyfiles.pl':    self.pp.parserANYFILES      ,
                       'anyfiles.pl':          self.pp.parserANYFILES      ,
                       'videoweed.es':         self.pp.parserVIDEOWEED     ,
                       'videoweed.com':        self.pp.parserVIDEOWEED     ,
                       'bitvid.sx':            self.pp.parserVIDEOWEED     ,
                       'novamov.com':          self.pp.parserNOVAMOV       ,
                       'nowvideo.eu':          self.pp.parserNOWVIDEO      ,
                       'nowvideo.sx':          self.pp.parserNOWVIDEO      ,
                       'nowvideo.to':          self.pp.parserNOWVIDEO      ,
                       'nowvideo.co':          self.pp.parserNOWVIDEO      ,
                       'rapidvideo.com':       self.pp.parserRAPIDVIDEO    ,
                       'videoslasher.com':     self.pp.parserVIDEOSLASHER  ,
                       'dailymotion.com':      self.pp.parserDAILYMOTION   ,
                       'video.sibnet.ru':      self.pp.parserSIBNET        ,
                       'vk.com':               self.pp.parserVK            ,
                       'anime-shinden.info':   self.pp.parserANIMESHINDEN  ,
                       'content.peteava.ro':   self.pp.parserPETEAVA       ,
                       'i.vplay.ro':           self.pp.parserVPLAY         ,
                       'nonlimit.pl':          self.pp.parserIITV          ,
                       'streamo.tv':           self.pp.parserIITV          ,
                       'divxstage.eu':         self.pp.parserDIVXSTAGE     ,
                       'divxstage.to':         self.pp.parserDIVXSTAGE     ,
                       'movdivx.com':          self.pp.parserMODIVXCOM     ,
                       'movshare.net':         self.pp.parserWHOLECLOUD     ,
                       'wholecloud.net':       self.pp.parserWHOLECLOUD     ,
                       'wholecloud.net':       self.pp.parserWHOLECLOUD    ,
                       'tubecloud.net':        self.pp.parserTUBECLOUD     ,
                       'bestreams.net':        self.pp.parserBESTREAMS     ,
                       'freedisc.pl':          self.pp.parserFREEDISC      ,
                       'dwn.so':               self.pp.parserDWN           ,
                       'st.dwn.so':            self.pp.parserDWN           ,
                       'ginbig.com':           self.pp.parserGINBIG        ,
                       'qfer.net':             self.pp.parserQFER          ,
                       'streamcloud.eu':       self.pp.parserSTREAMCLOUD   ,
                       'limevideo.net':        self.pp.parserLIMEVIDEO     ,
                       'donevideo.com':        self.pp.parserLIMEVIDEO     ,
                       'scs.pl':               self.pp.parserSCS           ,
                       'youwatch.org':         self.pp.parserYOUWATCH      ,
                       'played.to':            self.pp.parserPLAYEDTO      ,
                       'playedto.me':          self.pp.parserPLAYEDTO      ,
                       'watchers.to':          self.pp.parserWATCHERSTO    ,
                       'streame.net':          self.pp.parserSTREAMENET    ,
                       'estream.to':           self.pp.parserESTREAMTO     ,
                       'videomega.tv':         self.pp.parserVIDEOMEGA     ,
                       'up2stream.com':        self.pp.parserVIDEOMEGA     ,
                       'vidto.me':             self.pp.parserVIDTO         ,
                       'vidstream.in':         self.pp.parserVIDSTREAM     ,
                       'faststream.in':        self.pp.parserVIDSTREAM     ,
                       'video.rutube.ru':      self.pp.parserRUTUBE        ,
                       'rutube.ru':            self.pp.parserRUTUBE        ,
                       'youtube.com':          self.pp.parserYOUTUBE       ,
                       'youtu.be':             self.pp.parserYOUTUBE       ,
                       'google.com':           self.pp.parserGOOGLE        ,
                       'tinymov.net':          self.pp.parserTINYMOV       ,
                       'topupload.tv':         self.pp.parserTOPUPLOAD     ,
                       'maxupload.tv':         self.pp.parserTOPUPLOAD     ,
                       'video.yandex.ru':      self.pp.parserYANDEX        ,
                       'seositer.com':         self.pp.parserYANDEX        ,
                       'liveleak.com':         self.pp.parserLIVELEAK      ,
                       'vidup.me':             self.pp.parserVIDUPME       ,
                       'embed.trilulilu.ro':   self.pp.parserTRILULILU     ,
                       'videa.hu':             self.pp.parserVIDEA         ,
                       'emb.aliez.tv':         self.pp.parserALIEZ         ,
                       'my.mail.ru':           self.pp.parserVIDEOMAIL     ,
                       'api.video.mail.ru':    self.pp.parserVIDEOMAIL     ,
                       'videoapi.my.mail.ru':  self.pp.parserVIDEOMAIL     ,
                       'cloud.mail.ru':        self.pp.parserCOUDMAILRU    ,
                       'wrzuta.pl':            self.pp.parserWRZUTA        ,
                       'goldvod.tv':           self.pp.parserGOLDVODTV     ,
                       'vidzer.net':           self.pp.parserVIDZER        ,
                       'nowvideo.ch':          self.pp.parserNOWVIDEOCH    ,
                       'streamin.to':          self.pp.parserSTREAMINTO    ,
                       'vidsso.com':           self.pp.parserVIDSSO        ,
                       'wat.tv':               self.pp.parseWATTV          ,
                       'tune.pk':              self.pp.parseTUNEPK         ,
                       'netu.tv':              self.pp.parseNETUTV         ,
                       'hqq.tv':               self.pp.parseNETUTV         ,
                       'waaw.tv':              self.pp.parseNETUTV         ,
                       'vshare.io':            self.pp.parseVSHAREIO       ,
                       'vidspot.net':          self.pp.parserVIDSPOT       ,
                       'video.tt':             self.pp.parserVIDEOTT       ,
                       'vodlocker.com':        self.pp.parserVODLOCKER     ,
                       'vshare.eu':            self.pp.parserVSHAREEU      ,
                       'vidbull.com':          self.pp.parserVIDBULL       ,
                       'divxpress.com':        self.pp.parserDIVEXPRESS    ,
                       'promptfile.com':       self.pp.parserPROMPTFILE    ,
                       'playreplay.net':       self.pp.parserPLAYEREPLAY   ,
                       'moevideo.net':         self.pp.parserPLAYEREPLAY   ,
                       'videowood.tv':         self.pp.parserVIDEOWOODTV   ,
                       'movreel.com':          self.pp.parserMOVRELLCOM    ,
                       'vidfile.net':          self.pp.parserVIDFILENET    ,
                       'mp4upload.com':        self.pp.parserMP4UPLOAD     ,
                       'yukons.net':           self.pp.parserYUKONS        ,
                       'ustream.tv':           self.pp.parserUSTREAMTV     ,
                       'privatestream.tv':     self.pp.parserPRIVATESTREAM ,
                       'aliez.me':             self.pp.parserALIEZME       ,
                       'abcast.biz':           self.pp.parserABCASTBIZ     ,
                       'abcast.net':           self.pp.parserABCASTBIZ     ,
                       'goodcast.co':          self.pp.parserGOODCASTCO    ,
                       'myvi.ru':              self.pp.parserMYVIRU        ,
                       'myvi.tv':              self.pp.parserMYVIRU        ,
                       'archive.org':          self.pp.parserARCHIVEORG    ,
                       'sawlive.tv':           self.pp.parserSAWLIVETV     ,
                       'shidurlive.com':       self.pp.parserSHIDURLIVECOM ,
                       'castalba.tv':          self.pp.parserCASTALBATV    ,
                       'fxstream.biz':         self.pp.parserFXSTREAMBIZ   ,
                       'webcamera.pl':         self.pp.parserWEBCAMERAPL   ,
                       'webcamera.mobi':       self.pp.parserWEBCAMERAPL   ,
                       'flashx.tv':            self.pp.parserFLASHXTV      ,
                       'flashx.pw':            self.pp.parserFLASHXTV      , 
                       'myvideo.de':           self.pp.parserMYVIDEODE     ,
                       'vidzi.tv':             self.pp.parserVIDZITV       ,
                       'tvp.pl':               self.pp.parserTVP           ,
                       'junkyvideo.com':       self.pp.parserJUNKYVIDEO    ,
                       'live.bvbtotal.de':     self.pp.parserLIVEBVBTOTALDE,
                       'partners.nettvplus.com': self.pp.parserNETTVPLUSCOM,
                       '7cast.net':            self.pp.parser7CASTNET      ,
                       'facebook.com':         self.pp.parserFACEBOOK      ,
                       'cloudyvideos.com':     self.pp.parserCLOUDYVIDEOS  ,
                       'thevideo.me':          self.pp.parserTHEVIDEOME    ,
                       'xage.pl':              self.pp.parserXAGEPL        ,
                       'castamp.com':          self.pp.parserCASTAMPCOM    ,
                       'crichd.tv':            self.pp.parserCRICHDTV      ,
                       'castto.me':            self.pp.parserCASTTOME      ,
                       'cast4u.tv':            self.pp.parserCAST4UTV      ,
                       'hdcast.info':          self.pp.parserHDCASTINFO    ,
                       'deltatv.pw':           self.pp.parserDELTATVPW     ,
                       'pxstream.tv':          self.pp.parserPXSTREAMTV    ,
                       'coolcast.eu':          self.pp.parserCOOLCASTEU    ,
                       'filenuke.com':         self.pp.parserFILENUKE      ,
                       'sharesix.com':         self.pp.parserFILENUKE      ,
                       'thefile.me':           self.pp.parserTHEFILEME     ,
                       'cloudtime.to':         self.pp.parserCLOUDTIME     ,
                       'nosvideo.com':         self.pp.parserNOSVIDEO      ,
                       'letwatch.us':          self.pp.parserLETWATCHUS    ,
                       'uploadc.com':          self.pp.parserUPLOADCCOM    ,
                       'mightyupload.com':     self.pp.parserMIGHTYUPLOAD  ,
                       'zalaa.com':            self.pp.parserZALAACOM      ,
                       'allmyvideos.net':      self.pp.parserALLMYVIDEOS   ,
                       'streamplay.cc':        self.pp.parserSTREAMPLAYCC  ,
                       'yourvideohost.com':    self.pp.parserYOURVIDEOHOST ,
                       'vidgg.to':             self.pp.parserVIDGGTO       ,
                       'vid.gg':               self.pp.parserVIDGGTO       ,
                       'tiny.cc':              self.pp.parserTINYCC        ,
                       'picasaweb.google.com': self.pp.parserPICASAWEB     ,
                       'stream4k.to':          self.pp.parserSTREAM4KTO    ,
                       'onet.pl':              self.pp.parserONETTV        ,
                       'onet.tv':              self.pp.parserONETTV        ,
                       'swirownia.com.usrfiles.com': self.pp.parserSWIROWNIA,
                       'byetv.org':            self.pp.paserBYETVORG       ,
                       'putlive.in':           self.pp.paserPUTLIVEIN      ,
                       'liveall.tv':           self.pp.paserLIVEALLTV      ,
                       'p2pcast.tv':           self.pp.paserP2PCASTTV      ,
                       'nowlive.pw':           self.pp.paserNOWLIVEPW      ,
                       'nowlive.xyz':          self.pp.paserNOWLIVEPW      ,
                       'streamlive.to':        self.pp.paserSTREAMLIVETO   ,
                       'megom.tv':             self.pp.paserMEGOMTV        ,
                       'openload.io':          self.pp.parserOPENLOADIO    ,
                       'openload.co':          self.pp.parserOPENLOADIO    ,
                       'oload.io':             self.pp.parserOPENLOADIO    ,
                       'oload.co':             self.pp.parserOPENLOADIO    ,
                       'oload.tv':             self.pp.parserOPENLOADIO    ,
                       'gametrailers.com':     self.pp.parserGAMETRAILERS  , 
                       'vevo.com':             self.pp.parserVEVO          ,
                       'bbc.co.uk':            self.pp.parserBBC           ,
                       'shared.sx':            self.pp.parserSHAREDSX      ,
                       'gorillavid.in':        self.pp.parserFASTVIDEOIN   , 
                       'daclips.in':           self.pp.parserFASTVIDEOIN   ,
                       'movpod.in':            self.pp.parserFASTVIDEOIN   ,
                       'fastvideo.in':         self.pp.parserFASTVIDEOIN   ,
                       'realvid.net':          self.pp.parserFASTVIDEOIN   ,
                       'rapidvideo.ws':        self.pp.parserRAPIDVIDEOWS  ,
                       'hdvid.tv':             self.pp.parserHDVIDTV       ,
                       'exashare.com':         self.pp.parserEXASHARECOM   ,
                       'bojem3a.info':         self.pp.parserEXASHARECOM   ,
                       'openload.info':        self.pp.parserEXASHARECOM   ,
                       'chefti.info':          self.pp.parserEXASHARECOM   ,
                       'allvid.ch':            self.pp.parserALLVIDCH      ,
                       'posiedze.pl':          self.pp.parserPOSIEDZEPL    ,
                       'neodrive.co':          self.pp.parserNEODRIVECO    ,
                       'cloudy.ec':            self.pp.parserCLOUDYEC      ,
                       'ideoraj.ch':           self.pp.parserCLOUDYEC      ,
                       'miplayer.net':         self.pp.parserMIPLAYERNET   ,
                       'yocast.tv':            self.pp.parserYOCASTTV      ,
                       'liveonlinetv247.info': self.pp.parserLIVEONLINE247 ,
                       'liveonlinetv247.net':  self.pp.parserLIVEONLINE247 ,
                       'filepup.net':          self.pp.parserFILEPUPNET    ,
                       'superfilm.pl':         self.pp.parserSUPERFILMPL   ,
                       'sendvid.com':          self.pp.parserSENDVIDCOM    ,
                       'filehoot.com':         self.pp.parserFILEHOOT      ,
                       'ssh101.com':           self.pp.parserSSH101COM     ,
                       'twitch.tv':            self.pp.parserTWITCHTV      ,
                       'sostart.org':          self.pp.parserSOSTARTORG    ,
                       'sostart.pw':           self.pp.parserSOSTARTPW     ,
                       'theactionlive.com':    self.pp.parserTHEACTIONLIVE ,
                       'biggestplayer.me':     self.pp.parserBIGGESTPLAYER ,
                       'goodrtmp.com':         self.pp.parserGOODRTMP      ,
                       'life-rtmp.com':        self.pp.parserLIFERTMP      ,
                       'openlive.org':         self.pp.parserOPENLIVEORG   ,
                       'moonwalk.cc':          self.pp.parserMOONWALKCC    ,
                       'serpens.nl':           self.pp.parserMOONWALKCC    ,
                       '37.220.36.15':         self.pp.parserMOONWALKCC    ,
                       'easyvid.org':          self.pp.parserEASYVIDORG    ,
                       'playvid.org':          self.pp.parserEASYVIDORG    ,
                       'mystream.la':          self.pp.parserMYSTREAMLA    ,
                       'ok.ru':                self.pp.parserOKRU          ,
                       'putstream.com':        self.pp.parserPUTSTREAM     ,
                       'live-stream.tv':       self.pp.parserLIVESTRAMTV   ,
                       'zerocast.tv':          self.pp.parserZEROCASTTV    ,
                       'vid.ag':               self.pp.parserVIDAG         ,
                       'albfilm.com':          self.pp.parserALBFILMCOM    ,
                       'hdfilmstreaming.com':  self.pp.parserHDFILMSTREAMING,
                       'allocine.fr':          self.pp.parserALLOCINEFR    ,
                       'video.meta.ua':        self.pp.parseMETAUA         ,
                       'xvidstage.com':        self.pp.parseXVIDSTAGECOM   ,
                       'speedvideo.net':       self.pp.parseSPEEDVICEONET  ,
                       'vid.me':               self.pp.parseVIDME          ,
                       'veehd.com':            self.pp.parseVEEHDCOM       ,
                       'sharerepo.com':        self.pp.parseSHAREREPOCOM   ,
                       'easyvideo.me':         self.pp.parseEASYVIDEOME    ,
                       'playbb.me':            self.pp.parseEASYVIDEOME    ,
                       'vimeo.com':            self.pp.parseVIMEOCOM       ,
                       'jacvideo.com':         self.pp.parseJACVIDEOCOM    ,
                       'caston.tv':            self.pp.parseCASTONTV       ,
                       'bro.adca.st':          self.pp.parseBROADCAST      ,
                       'bro.adcast.tech':      self.pp.parseBROADCAST      ,
                       'moshahda.net':         self.pp.parseMOSHAHDANET    ,
                       'stream.moe':           self.pp.parseSTREAMMOE      ,
                       'publicvideohost.org':  self.pp.parsePUBLICVIDEOHOST,
                       'castflash.pw':         self.pp.parseCASTFLASHPW    ,
                       'flashlive.pw':         self.pp.parseCASTFLASHPW    ,
                       'castasap.pw':          self.pp.parseCASTFLASHPW    ,
                       'fastflash.pw':         self.pp.parseCASTFLASHPW    ,
                       'flashcast.pw':         self.pp.parseCASTFLASHPW    ,
                       'dotstream.tv':         self.pp.parserDOTSTREAMTV   ,
                       'leton.tv':             self.pp.parserDOTSTREAMTV   ,
                       'tvope.com':            self.pp.parserTVOPECOM      ,
                       'fileone.tv':           self.pp.parserFILEONETV     ,
                       'userscloud.com':       self.pp.parserUSERSCLOUDCOM ,
                       'tusfiles.net':         self.pp.parserUSERSCLOUDCOM ,
                       'hdgo.cc':              self.pp.parserHDGOCC        ,
                       'liveonlinetv247.info': self.pp.parserLIVEONLINETV247,
                       'streamable.com':       self.pp.parserSTREAMABLECOM  ,
                       'auroravid.to':         self.pp.parserAURORAVIDTO    ,
                       'playpanda.net':        self.pp.parserPLAYPANDANET   ,
                       'easyvideo.me':         self.pp.parserEASYVIDEOME    ,
                       'vidlox.tv':            self.pp.parserVIDLOXTV       ,
                       'embeducaster.com':     self.pp.parserUCASTERCOM     ,
                       'darkomplayer.com':     self.pp.parserDARKOMPLAYER   ,
                       'vivo.sx':              self.pp.parserVIVOSX         ,
                       'zstream.to':           self.pp.parserZSTREAMTO      ,
                       'uploadz.co':           self.pp.parserUPLOAD         ,
                       'upload.af':            self.pp.parserUPLOAD         ,
                       'uploadx.org':          self.pp.parserUPLOAD         ,
                       'clicknupload.link':    self.pp.parserUPLOAD         ,
                       'kingfiles.net':        self.pp.parserKINGFILESNET   ,
                       'thevideobee.to':       self.pp.parserTHEVIDEOBEETO  ,
                       'vidabc.com':           self.pp.parserVIDABCCOM      ,
                       'uptobox.com':          self.pp.parserUPTOSTREAMCOM  ,
                       'uptostream.com':       self.pp.parserUPTOSTREAMCOM  ,
                       'fastplay.cc':          self.pp.parserFASTPLAYCC     ,
                       'spruto.tv':            self.pp.parserSPRUTOTV       ,
                       'raptu.com':            self.pp.parserRAPTUCOM       ,
                       'ovva.tv':              self.pp.parserOVVATV         ,
                       'streamplay.to':        self.pp.parserSTREAMPLAYTO   ,
                       'streamango.com':       self.pp.parserSTREAMANGOCOM  ,
                       #'billionuploads.com':   self.pp.parserBILLIONUPLOADS ,
                    }
        return
    
    def getHostName(self, url, nameOnly = False):
        hostName = ''
        match = re.search('https?://(?:www.)?(.+?)/', url)
        if match:
            hostName = match.group(1)
            if (nameOnly):
                n = hostName.split('.')
                try: hostName = n[-2]
                except Exception: printExc()
        hostName = hostName.lower()
        printDBG("_________________getHostName: [%s] -> [%s]" % (url, hostName))
        return hostName
        
        
    def getParser(self, url, host=None):
        if None == host:
            host = self.getHostName(url)
        parser = self.hostMap.get(host, None)
        if None == parser:
            host2 = host[host.find('.')+1:]
            printDBG('urlparser.getParser II try host[%s]->host2[%s]' % (host, host2))
            parser = self.hostMap.get(host2, None)
        return parser
    
    def checkHostSupport(self, url):
        # -1 - not supported
        #  0 - unknown
        #  1 - supported
        host  = self.getHostName(url)
        
        # quick fix
        if host == 'facebook.com' and 'likebox.php' in url:
            return 0
        
        ret = 0
        parser = self.getParser(url, host)
        if None != parser:
            return 1
        return ret

    def getVideoLinkExt(self, url):
        videoTab = []
        try:
            ret = self.getVideoLink(url, True)
            
            if isinstance(ret, basestring):
                if 0 < len(ret):
                    host = self.getHostName(url)
                    videoTab.append({'name': host, 'url': ret})
            elif isinstance(ret, list) or isinstance(ret, tuple):
                return ret
        except Exception:
            printExc()
            
        return videoTab
        
    def getVideoLink(self, url, acceptsList = False):
        try:
            url = self.decorateParamsFromUrl(url)
            nUrl=''
            parser = self.getParser(url)
            if None != parser:
                nUrl = parser(url)
    
            if isinstance(nUrl, list) or isinstance(nUrl, tuple):
                if True == acceptsList:
                    return nUrl
                else:
                    if len(nUrl) > 0:
                        return nUrl[0]['url']
                    else:
                        return False
            return nUrl
        except Exception:
            printExc()
        return False
        
    def getAutoDetectedStreamLink(self, baseUrl, data=None):
        printDBG("urlparser.getAutoDetectedStreamLink baseUrl[%s]" % baseUrl)
        url = baseUrl
        num = 0
        while True:
            num += 1
            if None == data:
                url = strwithmeta(url)
                HTTP_HEADER = dict(pageParser.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = url.meta.get('Referer', url)
                sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
                if not sts: return []
            data = re.sub("<!--[\s\S]*?-->", "", data)
            if 1 == num  and 'http://up4free.com/' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'^"]+?)['"];""")[0]
                tmpUrl = url
                url = 'http://embed.up4free.com/stream.php?id=' + id + '&amp;width=700&amp;height=450&amp;stretching='
                url = strwithmeta(url, {'Referer':tmpUrl})
                data = None
                continue
            elif 'hdfree.tv/live' in data and 'hdfree.tv' not in url:
                tmpUrl = url
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?hdfree.tv/live[^"^']+?)["']''', 1, True)[0]
                url = strwithmeta(url, {'Referer':tmpUrl})
                data = None
                continue
            elif 'dotstream.tv' in data:
                streampage = self.cm.ph.getSearchGroups(data, """streampage=([^&]+?)&""")[0]
                videoUrl = 'http://dotstream.tv/player.php?streampage={0}&height=490&width=730'.format(streampage)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'ucaster.js' in data:
                channel = self.cm.ph.getSearchGroups(data, """channel=['"]([^'^"]+?)['"]""")[0]
                g = self.cm.ph.getSearchGroups(data, """g=['"]([^'^"]+?)['"]""")[0]
                width = self.cm.ph.getSearchGroups(data, """width=([0-9]+?)[^0-9]""")[0]
                height = self.cm.ph.getSearchGroups(data, """height=([0-9]+?)[^0-9]""")[0]
                videoUrl = 'http://www.embeducaster.com/membedplayer/{0}/{1}/{2}/{3}'.format(channel, g, width, height)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'leton.tv' in data:
                streampage = self.cm.ph.getSearchGroups(data, """streampage=([^&]+?)&""")[0]
                videoUrl = 'http://leton.tv/player.php?streampage={0}&height=490&width=730'.format(streampage)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'tvope.com' in data:
                channel = self.cm.ph.getSearchGroups(data, """[^a-zA-Z0-9]c=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'http://tvope.com/emb/player.php?c={0}&w=600&h=400&d={1}'.format(channel, urlparser.getDomain(baseUrl))
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'nowlive.' in data:
                id = self.cm.ph.getSearchGroups(data, """[^a-zA-Z0-9]id=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://nowlive.pw/stream.php?id={0}&width=640&height=480&stretching=uniform&p=1'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'caston.tv/player.php' in data:
                id = self.cm.ph.getSearchGroups(data, """var\sid\s?=[^0-9]([0-9]+?)[^0-9]""")[0]
                if id == '': id = self.cm.ph.getSearchGroups(data, """id\s?=[^0-9]([0-9]+?)[^0-9]""")[0]
                videoUrl = 'http://www.caston.tv/player.php?width=1920&height=419&id={0}'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveonlinetv247' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://[^'^"]*?liveonlinetv247[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'ssh101.com/secure/' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?ssh101.com/secure/[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'twitch.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?twitch.tv[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'goodrtmp.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?goodrtmp.com[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'life-rtmp.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?life-rtmp.com[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'sostart.org' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://sostart.org/streamk.php?id={0}&width=640&height=390'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'bro.adca.' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adca\.[^'^"]+?stream\.php\?id=[^'^"]+?)['"]""")[0] 
                if videoUrl == '':
                    tmpUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adca\.[^'^"]+?)['"]""")[0] 
                    if '' == tmpUrl: tmpUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adcast\.[^'^"]+?)['"]""")[0] 
                    id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                    videoUrl = self.cm.getBaseUrl(tmpUrl) + 'stream.php?id={0}&width=600&height=400'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'sostart.pw' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://www.sostart.pw/jwplayer6.php?channel={0}&vw=710&vh=460'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'theactionlive.com' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://theactionlive.com/livegamecr2.php?id={0}&width=640&height=460&stretching='.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'biggestplayer.me' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://biggestplayer.me/streamcrjeje.php?id={0}&width=640&height=460'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'yocast.tv' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://www.yocast.tv/embed.php?live={0}&vw=620&vh=490'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'miplayer.net' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://miplayer.net[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'p2pcast' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://p2pcast.tv/stream.php?id={0}&live=0&p2p=0&stretching=uniform'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveall.tv' in data: 
                videoUrl = self.cm.ph.getSearchGroups(data, 'SRC="([^"]+?liveall.tv[^"]+?)"', 1, True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'putlive.in' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?putlive.in/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'streamlive.to' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?streamlive.to/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'megom.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?megom.tv/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'byetv.org' in data:
                file = self.cm.ph.getSearchGroups(data, "file=([0-9]+?)[^0-9]")[0]
                if '' == file: file = self.cm.ph.getSearchGroups(data, "a=([0-9]+?)[^0-9]")[0]
                videoUrl = "http://www.byetv.org/embed.php?a={0}&id=&width=710&height=460&autostart=true&strech=".format(file)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'castto.me' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://static.castto.me/embedlivepeer5.php?channel={0}&vw=710&vh=460'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'cast4u.tv' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'http://www.cast4u.tv/embed.php?v={0}&vw=700&vh=450'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'hdcast.info' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'http://www.hdcast.info/embed.php?live={0}&vw=700&vh=450'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'deltatv.pw' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                videoUrl = 'http://deltatv.pw/stream.php?id=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'pxstream.tv' in data:
                id = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                videoUrl = 'http://pxstream.tv/embed.php?file=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'coolcast.eu' in data:
                id = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                videoUrl = 'http://coolcast.eu/?name=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'goodcast.co' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                videoUrl = 'http://goodcast.co/stream.php?id=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif '7cast.net' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?7cast.net[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'partners.nettvplus.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://partners.nettvplus.com[^'^"]+?)['"]""")[0]
                return self.getVideoLinkExt(videoUrl)
            elif "yukons.net" in data:
                channel = self.cm.ph.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
                videoUrl = strwithmeta('http://yukons.net/watch/'+channel, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "castamp.com" in data:
                channel = self.cm.ph.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
                videoUrl = strwithmeta('http://www.castamp.com/embed.php?c='+channel, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveonlinetv247.info/embed/' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](https?://(?:www\.)?liveonlinetv247\.info/embed/[^'^"]+?)['"]""")[0]
                return self.getVideoLinkExt(videoUrl)
            elif "crichd.tv" in data:
                if baseUrl.startswith('http://crichd.tv'):
                    videoUrl = strwithmeta(baseUrl, {'Referer':baseUrl})
                else:
                    videoUrl = self.cm.ph.getSearchGroups(data, 'src="(http://crichd.tv[^"]+?)"')[0]
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "privatestream.tv" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://w*?privatestream.tv/[^"^']+?)['"]''')[0]
                if '' == videoUrl: videoUrl = self.cm.ph.getSearchGroups(data, '''=(https?://w*?privatestream.tv/[^"^'^>^<^\s]+?)['"><\s]''')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "aliez.me" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://[^'^"]*?aliez.me/[^"^']+?)['"]''')[0]
                if '' == videoUrl: videoUrl = self.cm.ph.getSearchGroups(data, '''=(https?://[^'^"]*?aliez.me/[^"^'^>^<^\s]+?)['"><\s]''')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "ustream.tv" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?ustream.tv[^"]+?)"')[0]
                if videoUrl.startswith('//'):
                    videoUrl = 'http:' + videoUrl
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'source=rtmp://' in data:
                tmp = self.cm.ph.getSearchGroups(data, """source=(rtmp://[^'^"]+?)['"]""")[0]
                tmp = tmp.split('&amp;')
                r = tmp[0]
                swfUrl='swf'
                r += ' swfUrl=%s pageUrl=%s live=1' % (swfUrl, url)
                return [{'name':'[rtmp]', 'url':r}]
            elif 'rtmp://' in data:
                tmp = self.cm.ph.getSearchGroups(data, """(rtmp://[^'^"]+?)['"]""")[0]
                tmp = tmp.split('&amp;')
                r = tmp[0]
                if 1 < len(tmp)and tmp[1].startswith('c='):
                    playpath = tmp[1][2:]
                else:
                    playpath = self.cm.ph.getSearchGroups(data, """['"]*url['"]*[ ]*?:[ ]*?['"]([^'^"]+?)['"]""")[0]
                if '' != playpath:
                    r += ' playpath=%s' % playpath.strip()
                swfUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?swf)['"]""")[0]
                r += ' swfUrl=%s pageUrl=%s' % (swfUrl, url)
                return [{'name':'team-cast', 'url':r}]
            elif 'abcast.biz' in data or 'abcast.net' in data :
                file = self.cm.ph.getSearchGroups(data, "file='([^']+?)'")[0]
                if '' != file:
                    if 'abcast.net' in data:
                        videoUrl = 'http://abcast.net/embed.php?file='
                    else:
                        videoUrl = 'http://abcast.biz/embed.php?file='
                    videoUrl += file+'&width=640&height=480'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            elif 'openlive.org' in data:
                file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                videoUrl = 'http://openlive.org/embed.php?file={0}&width=710&height=460'.format(file)
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'shidurlive.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?shidurlive.com[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            elif 'sawlive.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?sawlive.tv[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                    return self.getVideoLinkExt(videoUrl)
            elif "castalba.tv" in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                if '' != id:
                    videoUrl = 'http://castalba.tv/embed.php?cid='+id+'&wh=640&ht=400&r=team-cast.pl.cp-21.webhostbox.net'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            elif "fxstream.biz" in data:
                file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                if '' != file:
                    videoUrl = 'http://fxstream.biz/embed.php?file='+file+'&width=640&height=400'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            else:
                file = self.cm.ph.getSearchGroups(data, """['"]*(http[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0]
                if '' != file: 
                    file = file.split('&#038;')[0]
                    return getDirectM3U8Playlist(urllib.unquote(clean_html(file)), checkExt=False)
                if 'x-vlc-plugin' in data:
                    vlcUrl = self.cm.ph.getSearchGroups(data, """target=['"](http[^'^"]+?)['"]""")[0]
                    if '' != vlcUrl: return [{'name':'vlc', 'url':vlcUrl}]
                printDBG("=======================================================================")
                printDBG("No link extractor for url[%s]" % url)
                printDBG("=======================================================================")
            return []

class pageParser:
    HTTP_HEADER= {  'User-Agent'  : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                    'Accept'      :  'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Content-type': 'application/x-www-form-urlencoded' }
    def __init__(self):
        self.cm = common()
        self.captcha = captchaParser()
        self.ytParser = None
        self.moonwalkParser = None
        self.vevoIE = None
        self.bbcIE = None
        
        #config
        self.COOKIE_PATH = GetCookieDir('')
        #self.hd3d_login = config.plugins.iptvplayer.hd3d_login.value
        #self.hd3d_password = config.plugins.iptvplayer.hd3d_password.value
    
    def getYTParser(self):
        if self.ytParser == None:
            try:
                from youtubeparser import YouTubeParser
                self.ytParser = YouTubeParser()
            except Exception:
                printExc()
                self.ytParser = None
        return self.ytParser
        
    def getVevoIE(self):
        if self.vevoIE == None:
            try:
                from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.vevo import VevoIE
                self.vevoIE = VevoIE()
            except Exception:
                self.vevoIE = None
                printExc()
        return self.vevoIE
        
    def getBBCIE(self):
        if self.bbcIE == None:
            try:
                from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.bbc import BBCCoUkIE
                self.bbcIE = BBCCoUkIE()
            except Exception:
                self.bbcIE = None
                printExc()
        return self.bbcIE
        
    def getMoonwalkParser(self):
        if self.moonwalkParser == None:
            try:
                from moonwalkcc import MoonwalkParser
                self.moonwalkParser = MoonwalkParser()
            except Exception:
                printExc()
                self.moonwalkParser = None
        return self.moonwalkParser
        
    def _getSources(self, data):
        printDBG('>>>>>>>>>> _getSources')
        urlTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'sources', ']')[1]
        if tmp != '':
            tmp = tmp.replace('\\', '')
            tmp = tmp.split('}')
            urlAttrName = 'file'
            sp = ':'
        else:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', withMarkers=True)
            urlAttrName = 'src'
            sp = '='
        printDBG(tmp)
        for item in tmp:
            url  = self.cm.ph.getSearchGroups(item, r'''['"]?{0}['"]?\s*{1}\s*['"](https?://[^"^']+)['"]'''.format(urlAttrName, sp))[0]
            if not self.cm.isValidUrl(url): continue
            name = self.cm.ph.getSearchGroups(item, r'''['"]?label['"]?\s*''' + sp + r'''\s*['"]?([^"^'^\,^\{]+)['"\,\{]''')[0]
            
            printDBG('---------------------------')
            printDBG('url:  ' + url)
            printDBG('name: ' + name)
            printDBG('+++++++++++++++++++++++++++')
            printDBG(item)
            
            if 'mp4' in item:
                urlTab.append({'name':name, 'url':url})
        return urlTab
        
    def _findLinks(self, data, serverName='', linkMarker=r'''['"]?file['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='sources', m2=']', contain=''):
        linksTab = []
        
        def _isSmil(data):
            return data.split('?')[0].endswith('.smil')
        
        def _getSmilUrl(url):
            if _isSmil(url):
                SWF_URL=''
                # get stream link
                sts, data = self.cm.getPage(url)
                if sts:
                    base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
                    src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                    #if ':' in src:
                    #    src = src.split(':')[1]   
                    if base.startswith('rtmp'):
                        return base + '/' + src + ' swfUrl=%s pageUrl=%s' % (SWF_URL, url)
            return ''
        
        srcData = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1].split('},')
        for item in srcData:
            item += '},'
            if contain != '' and contain not in item: continue
            link = self.cm.ph.getSearchGroups(item, linkMarker)[0].replace('\/', '/')
            if '%3A%2F%2F' in link and '://' not in link:
                link = urllib.unquote(link)
            label = self.cm.ph.getSearchGroups(item, r'''['"]?label['"]?[ ]*:[ ]*['"]([^"^']+)['"]''')[0]
            if _isSmil(link):
                link = _getSmilUrl(link)
            if '://' in link:
                proto = 'mp4'
                if link.startswith('rtmp'):
                    proto = 'rtmp'
                if link.split('?')[0].endswith('m3u8'):
                    tmp = getDirectM3U8Playlist(link)
                    linksTab.extend(tmp)
                else:
                    linksTab.append({'name': '%s %s' % (proto + ' ' +serverName, label), 'url':link})
                printDBG('_findLinks A')
        
        if 0 == len(linksTab):
            printDBG('_findLinks B')
            link = self.cm.ph.getSearchGroups(data, linkMarker)[0].replace('\/', '/')
            if _isSmil(link):
                link = _getSmilUrl(link)
            if '://' in link:
                proto = 'mp4'
                if link.startswith('rtmp'):
                    proto = 'rtmp'
                linksTab.append({'name':proto + ' ' +serverName, 'url':link})
        return linksTab
        
    def _findLinks2(self, data, baseUrl):
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video/divx"src="(http[^"]+?)"')[0]
        if '' != videoUrl: return strwithmeta(videoUrl, {'Referer':baseUrl})
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*[:,][ ]*['"](http[^"^']+)['"][,}\)]''')[0]
        if '' != videoUrl: return strwithmeta(videoUrl, {'Referer':baseUrl})
        return False
        
    def _parserUNIVERSAL_A(self, baseUrl, embedUrl, _findLinks, _preProcessing=None, httpHeader={}, params={}):
        refUrl = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':refUrl }
        HTTP_HEADER.update(httpHeader)
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[/.]')[0]
            url = embedUrl.format(video_id)
        else:
            url = baseUrl
        params = dict(params)
        params.update({'header':HTTP_HEADER})
        post_data = None
        
        sts, data = self.cm.getPage(url, params, post_data)
        if not sts: sts, data = self.cm.getPageWithWget(url, params, post_data)
        if not sts: return False
        
        errMarkers = ['File was deleted', 'File Removed', 'File Deleted.', 'File Not Found']
        for errMarker in errMarkers:
            if errMarker in data:
                SetIPTVPlayerLastHostError(errMarker)
        
        if _preProcessing != None:
            data = _preProcessing(data)
        printDBG("Data: " + data)
        
        # get JS player script code from confirmation page
        mrk1 = ">eval("
        mrk2 = 'eval("'
        if mrk1  in data:
            m1 = mrk1
        elif mrk2 in data :
            m1 = mrk2
        else: m1 = "eval(" 
        tmpDataTab = self.cm.ph.getAllItemsBeetwenMarkers(data, m1, '</script>', False)
        for tmpData in tmpDataTab:
            data2 = tmpData
            tmpData = None
            # unpack and decode params from JS player script code
            tmpData = unpackJSPlayerParams(data2, VIDUPME_decryptPlayerParams)
            if tmpData == '':
                tmpData = unpackJSPlayerParams(data2, VIDUPME_decryptPlayerParams, 0)
            if None != tmpData:
                data = data + tmpData
        printDBG("Data: " + data)
        return _findLinks(data)
        
    def _parserUNIVERSAL_B(self, url, userAgent='Mozilla/5.0'):
        printDBG("_parserUNIVERSAL_B url[%s]" % url)
        
        sts, response = self.cm.getPage(url, {'return_data':False})
        url = response.geturl()
        response.close()
            
        post_data = None
        
        if '/embed' not in url: 
            sts, data = self.cm.getPage( url, {'header':{'User-Agent': userAgent}} )
            if not sts: return False
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)[1]
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            except Exception:
                printExc()
            try:
                tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                post_data.update(tmp)
            except Exception:
                printExc()
        videoTab = []
        params = {'header':{ 'User-Agent': userAgent, 'Content-Type':'application/x-www-form-urlencoded','Referer':url} }
        try:
            sts, data = self.cm.getPage(url, params, post_data)
            printDBG(data)
            
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player.ready', '}')[1]
            url = self.cm.ph.getSearchGroups(tmp, '''src['"\s]*?:\s['"]([^'^"]+?)['"]''')[0]
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url) and url.split('?')[0].endswith('.mpd'):
                url = strwithmeta(url, {'User-Agent':params['header']['User-Agent']})
                videoTab.extend(getMPDLinksWithMeta(url, False))
            
            filekey = re.search('flashvars.filekey="([^"]+?)";', data)
            if None == filekey: 
                filekey = re.search("flashvars.filekey=([^;]+?);", data)
                filekey = re.search('var {0}="([^"]+?)";'.format(filekey.group(1)), data)
            filekey = filekey.group(1)
            file    = re.search('flashvars.file="([^"]+?)";', data).group(1)
            domain  = re.search('flashvars.domain="(http[^"]+?)"', data).group(1)
            
            url = domain + '/api/player.api.php?cid2=undefined&cid3=undefined&cid=undefined&user=undefined&pass=undefined&numOfErrors=0'
            url = url + '&key=' + urllib.quote_plus(filekey) + '&file=' + urllib.quote_plus(file)
            sts, data = self.cm.getPage(url)
            videoUrl = re.search("url=([^&]+?)&", data).group(1)
            
            errUrl = domain + '/api/player.api.php?errorCode=404&cid=1&file=%s&cid2=undefined&cid3=undefined&key=%s&numOfErrors=1&user=undefined&errorUrl=%s&pass=undefined' % (urllib.quote_plus(file), urllib.quote_plus(filekey), urllib.quote_plus(videoUrl))
            sts, data = self.cm.getPage(errUrl)
            errUrl = re.search("url=([^&]+?)&", data).group(1)
            if '' != errUrl: url = errUrl
            if '' != url:
                videoTab.append({'name':'base', 'url':url})
        except Exception:
            printExc()
        return videoTab
        
    def __parseJWPLAYER_A(self, baseUrl, serverName='', customLinksFinder=None, folowIframe=False, sleep_time=None):
        printDBG("pageParser.__parseJWPLAYER_A serverName[%s], baseUrl[%r]" % (serverName, baseUrl))
        
        linkList = []
        tries = 3
        while tries > 0:
            tries -= 1
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})

            if sts:
                HTTP_HEADER = dict(self.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = baseUrl
                url = self.cm.ph.getSearchGroups(data, 'iframe[ ]+src="(https?://[^"]*?embed[^"]+?)"')[0]
                if '' != url and (serverName in url or folowIframe): 
                    sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}) 
                else:
                    url = baseUrl
            
            if sts and '' != data:
                try:
                    sts, data2 = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
                    if sts:
                        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data2))
                        try:
                            tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                            post_data.update(tmp)
                        except Exception:
                            printExc()
                        if tries == 0:
                            try:
                                sleep_time = self.cm.ph.getSearchGroups(data2, '>([0-9]+?)</span> seconds<')[0]
                                if '' != sleep_time: time.sleep(int(sleep_time))
                            except Exception:
                                if sleep_time != None:
                                    time.sleep(sleep_time)
                                printExc()
                        HTTP_HEADER['Referer'] = url
                        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
                        if sts:
                            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>')
                            for tmpItem in tmp:
                                try:
                                    tmpItem = unpackJSPlayerParams(tmpItem, VIDUPME_decryptPlayerParams)
                                    data = tmpItem + data
                                except Exception: printExc()
                    if None != customLinksFinder: linkList = customLinksFinder(data)
                    if 0 == len(linkList): linkList = self._findLinks(data, serverName)
                except Exception:
                    printExc()
            if len(linkList) > 0:
                break
        return linkList
            
    def parserFIREDRIVE(self,url):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        COOKIEFILE = self.COOKIE_PATH + "firedrive.cookie"
        url = url.replace('putlocker', 'firedrive').replace('file', 'embed')
        HTTP_HEADER['Referer'] = url
        
        sts, data = self.cm.getPage( url, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE} )
        if not sts: return False
        if not 'Continue to ' in data: return False
        data = re.search('name="confirm" value="([^"]+?)"', data)
        if not data: return False
        data = {'confirm' : data.group(1)}
        sts, data = self.cm.getPage( url, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE}, data)
        if not sts: return False
        sts, link_data = CParsingHelper.getDataBeetwenMarkers(data, "function getVideoUrl(){", 'return', False)
        if sts:       match = re.search("post\('(http[^']+?)'", link_data)
        else:         match = re.search("file: '(http[^']+?)'", data)
        if not match: match = re.search("file: loadURL\('(http[^']+?)'", data)

        if not match: return False
        url = match.group(1)
        printDBG('parserFIREDRIVE url[%s]' % url)
        return url


    def parserMEGUSTAVID(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        match = re.compile('value="config=(.+?)">').findall(link)
        if len(match) > 0:
            p = match[0].split('=')
            url = "http://megustavid.com/media/nuevo/player/playlist.php?id=" + p[1]
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
            link = self.cm.getURLRequestData(query_data)
            match = re.compile('<file>(.+?)</file>').findall(link)
            if len(match) > 0:
                return match[0]
            else:
                return False
        else:
            return False

    def parserSPROCKED(self,url):
        url = url.replace('embed', 'show')
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        match = re.search("""url: ['"](.+?)['"],.*\nprovider""",link)
        if match: return match.group(1)
        else: return False

    def parserWGRANE(self,url):
        # extract video hash from given url
        sts, data = self.cm.getPage(url)
        if not sts: return False
        agree = ''
        if 'controversial_content_agree' in data: agree = 'controversial_content_agree'
        elif 'adult_content_agree' in data: agree = 'adult_content_agree'
        if '' != agree:
            vidHash = re.search("([0-9a-fA-F]{32})$", url)
            if not vidHash: return False
            params = {'use_cookie': True, 'load_cookie':False, 'save_cookie':False} 
            url = "http://www.wgrane.pl/index.html?%s=%s" % (agree, vidHash.group(1))
            sts, data = self.cm.getPage(url, params)
            if not sts: return False

        tmp = re.search('''["'](http[^"^']+?/video/[^"^']+?\.mp4[^"^']*?)["']''', data)
        if tmp: return tmp.group(1)
        data = re.search("<meta itemprop='contentURL' content='([^']+?)'", data)
        if not data: return False
        url = clean_html(data.group(1))
        return url
        
    def parserCDA(self, inUrl):
        COOKIE_FILE = GetCookieDir('cdapl.cookie')
        HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        defaultParams = {'header': HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        def _decorateUrl(inUrl, host, referer):
            # prepare extended link
            retUrl = strwithmeta( inUrl )
            retUrl.meta['Host']              = host
            retUrl.meta['Referer']           = referer
            retUrl.meta['Cookie']            = self.cm.getCookieHeader(COOKIE_FILE) #"PHPSESSID=1"
            retUrl.meta['iptv_proto']        = 'http'
            retUrl.meta['iptv_urlwithlimit'] = False
            retUrl.meta['iptv_livestream']   = False
            return retUrl
            
        vidMarker = '/video/'
        videoUrls = []
        uniqUrls  = []
        tmpUrls = []
        if vidMarker not in inUrl:
            sts, data = self.cm.getPage(inUrl, defaultParams)
            if sts:
                sts,match = self.cm.ph.getDataBeetwenMarkers(data, "Link do tego video:", '</a>', False)
                if sts: match = self.cm.ph.getSearchGroups(match, 'href="([^"]+?)"')[0] 
                else: match = self.cm.ph.getSearchGroups(data, "link[ ]*?:[ ]*?'([^']+?/video/[^']+?)'")[0]
                if match.startswith('http'): inUrl = match
        if vidMarker in inUrl: 
            vid = self.cm.ph.getSearchGroups(inUrl + '/', "/video/([^/]+?)/")[0]
            inUrl = 'http://ebd.cda.pl/620x368/' + vid
        
        # extract qualities
        sts, data = self.cm.getPage(inUrl, defaultParams)
        if sts:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'Jakość:', '</div>', False)
            if sts:
                data = re.findall('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>', data)
                for urlItem in data:
                    tmpUrls.append({'name':'cda.pl ' + urlItem[1], 'url':urlItem[0]})
        
        if 0 == len(tmpUrls):
            tmpUrls.append({'name':'cda.pl', 'url':inUrl})
            
        def __appendVideoUrl(params):
            if params['url'] not in uniqUrls:
                videoUrls.append(params)
                uniqUrls.append(params['url'])
        
        def __ca(dat):
            def __replace(c):
                code = ord(c.group(1))
                if code <= ord('Z'):
                    tmp = 90
                else: 
                    tmp = 122
                c = code + 13
                if tmp < c:
                    c -= 26
                return chr(c)
            
            if not self.cm.isValidUrl(dat):
                try:
                    dat = re.sub('([a-zA-Z])', __replace, dat)
                    if not dat.endswith('.mp4'):
                        dat += '.mp4'
                    dat = dat.replace("adc.mp4", ".mp4")
                except Exception:
                    dat = ''
                    printExc()
            return str(dat)
        
        for urlItem in tmpUrls:
            if urlItem['url'].startswith('/'): inUrl = 'http://www.cda.pl/' + urlItem['url']
            else: inUrl = urlItem['url']
            sts, pageData = self.cm.getPage(inUrl, defaultParams)
            if not sts: continue
            
            #with open('/home/sulge/movie/test.txt', 'r') as cfile:
            #    pageData = cfile.read()
            
            tmpData = self.cm.ph.getDataBeetwenMarkers(pageData, "eval(", '</script>', False)[1]
            if tmpData != '':
                m1 = '$.get' 
                if m1 in tmpData:
                    tmpData = tmpData[:tmpData.find(m1)].strip() + '</script>'
                try: tmpData = unpackJSPlayerParams(tmpData, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                except Exception: pass
                #printDBG(tmpData)
            tmpData += pageData
            
            tmp = self.cm.ph.getDataBeetwenMarkers(tmpData, "player_data='", "'", False)[1].strip()
            #printDBG("===========================================")
            #printDBG(tmp)
            #printDBG("===========================================")
            try:
                if tmp != '':
                    tmp = byteify(json.loads(tmp))
                    tmp = __ca(tmp['video']['file'])
            except Exception:
                tmp = ''
                printExc()
                
            # confirm
            #def __getValue(dat):
            #    dat = dat.strip()
            #    if len(dat) < 2: return dat
            #    if dat[0] in ['"', "'"] and dat[-1] in ['"', "'"]:
            #        return dat[1:-1]
            #    return dat
            #        
            #confirmData = self.cm.ph.getDataBeetwenMarkers(tmpData, '$.get(', ');', False)[1]
            #_confirmData = self.cm.ph.getDataBeetwenMarkers(confirmData, '{', '}', False)[1]
            #url         = __getValue(confirmData.split('{')[0])
            #url = __getValue(confirmData.split(',')[0])
            #if url.startswith('/'):
            #    url = urlparser.getDomain(inUrl, False) + url[1:]
            #_confirmData = _confirmData.split(',')
            #confirmData = ''
            #printDBG(_confirmData)
            #for item in _confirmData:
            #    item = item.split(':')
            #    if len(item) != 2: continue
            #    confirmData += '%s=%s&' % (__getValue(item[0]), __getValue(item[1]))
            #
            #confirmParams = dict(defaultParams)
            #confirmParams['header'] = dict(confirmParams['header'])
            #confirmParams['Referer'] = inUrl
            #sts, confirmData = self.cm.getPage(url + '?' + confirmData, confirmParams)
            #printDBG("===========================================")
            #printDBG("confirmData: " + confirmData)
            #printDBG("===========================================")
            
            if tmp == '':
                data = self.cm.ph.getDataBeetwenReMarkers(tmpData, re.compile('''modes['"]?[\s]*:'''), re.compile(']'), False)[1]
                data = re.compile("""file:[\s]*['"]([^'^"]+?)['"]""").findall(data)
            else: data = [tmp]
            if 0 < len(data) and data[0].startswith('http'): __appendVideoUrl( {'name': urlItem['name'] + ' flv', 'url':_decorateUrl(data[0], 'cda.pl', urlItem['url']) } )
            if 1 < len(data) and data[1].startswith('http'): __appendVideoUrl( {'name': urlItem['name'] + ' mp4', 'url':_decorateUrl(data[1], 'cda.pl', urlItem['url']) } )
            if 0 == len(data):
                data = self.cm.ph.getDataBeetwenReMarkers(tmpData, re.compile('video:[\s]*{'), re.compile('}'), False)[1]
                data = self.cm.ph.getSearchGroups(data, "'(http[^']+?(:?\.mp4|\.flv)[^']*?)'")[0]
                if '' != data:
                    type = ' flv '
                    if '.mp4' in data:
                        type = ' mp4 '
                    __appendVideoUrl( {'name': urlItem['name'] + type, 'url':_decorateUrl(data, 'cda.pl', urlItem['url']) } )
    
        #if len(videoUrls):
        #    videoUrls = [videoUrls[0]]
        return videoUrls

    def parserDWN(self,url):
        if "play4.swf" in url:
            match = re.search("play4.swf([^']+?)',", url+"',")
        else:
            sts, url = self.cm.getPage(url)
            if not sts: return False
            match = re.search('src="([^"]+?)" width=', url)
            if match:
                sts, url = self.cm.getPage( match.group(1) )
                if not sts: return False
            match = re.search("play4.swf([^']+?)',", url)

        if match:
            url = 'http://st.dwn.so/xml/videolink.php' + match.group(1)
            sts, data = self.cm.getPage(url)
            if not sts: return False
            match = re.search('un="([^"]+?),0"', data)
            if match:
                linkvideo = 'http://' + match.group(1)
                printDBG("parserDWN directURL [%s]" % linkvideo)
                return linkvideo
        return False

    def parserANYFILES(self, url):
        from anyfilesapi import AnyFilesVideoUrlExtractor
        self.anyfiles = AnyFilesVideoUrlExtractor()
        
        id = self.cm.ph.getSearchGroups(url+'|', 'id=([0-9]+?)[^0-9]')[0]
        if id != '':
            url = 'http://video.anyfiles.pl/videos.jsp?id=' + id
        retVal = self.anyfiles.getVideoUrl(url)
        return retVal

    def parserWOOTLY(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        c = re.search("""c.value="(.+?)";""",link)
        if c:
            cval = c.group(1)
        else:
            return False
        match = re.compile("""<input type=['"]hidden['"] value=['"](.+?)['"].+?name=['"](.+?)['"]""").findall(link)
        if len(match) > 0:
            postdata = {};
            for i in range(len(match)):
                if (len(match[i][0])) > len(cval):
                    postdata[cval] = match[i][1]
                else:
                    postdata[match[i][0]] = match[i][1]
            self.COOKIEFILE = self.COOKIE_PATH + "wootly.cookie"
            query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.search("""<video.*\n.*src=['"](.+?)['"]""",link)
            if match:
                return match.group(1)
            else:
                return False
        else:
            return False

    def parserVIDEOWEED(self, url):
        return self._parserUNIVERSAL_B(url)
        
    def parserAURORAVIDTO(self, url):
        return self._parserUNIVERSAL_B(url)

    def parserNOVAMOV(self, url):
        return self._parserUNIVERSAL_B(url)

    def parserNOWVIDEO(self, baseUrl):
        urlTab = []

        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0" }
        
        COOKIE_FILE = GetCookieDir('nowvideo.sx')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        if 'embed' not in baseUrl:
            vidId = self.cm.ph.getSearchGroups(baseUrl + '/', '/video/([^/]+?)/')[0]
            if '' == vidId: vidId = self.cm.ph.getSearchGroups(baseUrl + '&', '[\?&]v=([^&]+?)&')[0]
            baseUrl = 'http://embed.nowvideo.sx/embed/?v=' + vidId
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
            
        tokenUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?/api/toker[^'^"]+?)['"]''')[0]
        if tokenUrl.startswith('/'):
            tokenUrl = 'http://embed.nowvideo.sx' + tokenUrl
        
        HTTP_HEADER['Referer'] = baseUrl
        sts, token = self.cm.getPage(tokenUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} )
        if not sts: return False
        token = self.cm.ph.getDataBeetwenMarkers(token, '=', ';', False)[1].strip()
         
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        
        tmp = self._parserUNIVERSAL_B(baseUrl)
        if isinstance(tmp, basestring) and 0 < len(tmp):
            tmp += '?client=FLASH'
        return tmp
        
    def parserSOCKSHARE(self,url):
        query_data = { 'url': url.replace('file', 'embed'), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        r = re.search('value="(.+?)" name="fuck_you"', link)
        if r:
            self.COOKIEFILE = self.COOKIE_PATH + "sockshare.cookie"
            postdata = {'fuck_you' : r.group(1), 'confirm' : 'Close Ad and Watch as Free User'}
            query_data = { 'url': url.replace('file', 'embed'), 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.compile("playlist: '(.+?)'").findall(link)
            if len(match) > 0:
                url = "http://www.sockshare.com" + match[0]
                query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True }
                link = self.cm.getURLRequestData(query_data)
                match = re.compile('</link><media:content url="(.+?)" type="video').findall(link)
                if len(match) > 0:
                    url = match[0].replace('&amp;','&')
                    return url
                else:
                    return False
            else:
                return False
        else:
            return False

    def parserRAPIDVIDEO(self, baseUrl):
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '(?:embed|view)[/-]([A-Za-z0-9]{8})')[0]
        sts, data = self.cm.getPage('http://www.rapidvideo.com/view/'+video_id)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1].strip()
        data = self.cm.ph.getDataBeetwenMarkers(data, '"sources":', ']', False)[1].strip()
        data = byteify(json.loads(data+']'))
        printDBG(data)
        retTab = []
        for item in data:
            try: retTab.append({'name':'rapidvideo.com ' + item.get('label', item.get('res', '')), 'url':item['file']})
            except Exception: pass
        return retTab
        
    def parserVIDEOSLASHER(self, url):
        self.COOKIEFILE = self.COOKIE_PATH + "videoslasher.cookie"
        query_data = { 'url': url.replace('embed', 'video'), 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True }
        postdata = {'confirm': 'Close Ad and Watch as Free User', 'foo': 'bar'}
        data = self.cm.getURLRequestData(query_data, postdata)

        match = re.compile("playlist: '/playlist/(.+?)'").findall(data)
        if len(match)>0:
            query_data = { 'url': 'http://www.videoslasher.com//playlist/' + match[0], 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIEFILE,  'use_post': True, 'return_data': True }
            data = self.cm.getURLRequestData(query_data)
            match = re.compile('<title>Video</title>.*?<media:content url="(.+?)"').findall(data)
            if len(match)>0:
                sid = self.cm.getCookieItem(self.COOKIEFILE,'authsid')
                if sid != '':
                    streamUrl = urlparser.decorateUrl(match[0], {'Cookie':"authsid=%s" % sid, 'iptv_buffering':'required'})
                    return streamUrl
                else:
                    return False
            else:
                return False
        else:
            return False

    def parserDAILYMOTION(self, baseUrl):
        # https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/dailymotion.py
        COOKIE_FILE = self.COOKIE_PATH + "dailymotion.cookie"
        _VALID_URL = r'(?i)(?:https?://)?(?:(www|touch)\.)?dailymotion\.[a-z]{2,3}/(?:(embed|swf|#)/)?video/(?P<id>[^/?_]+)'
        mobj = re.match(_VALID_URL, baseUrl)
        video_id = mobj.group('id')
        
        HTTP_HEADER= {'User-Agent': "Mozilla/5.0"}
        
        url = 'http://www.dailymotion.com/embed/video/' + video_id
        familyUrl = 'http://www.dailymotion.com/family_filter?enable=false&urlback=' + urllib.quote_plus('/embed/video/' + video_id)
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': False, 'cookiefile': COOKIE_FILE})
        if not sts or "player" not in data: 
            sts, data = self.cm.getPage(familyUrl, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': False, 'cookiefile': COOKIE_FILE})
            if not sts: return []
        
        vidTab = []
        playerConfig = None
        
        tmp = self.cm.ph.getSearchGroups(data, r'playerV5\s*=\s*dmp\.create\([^,]+?,\s*({.+?})\);')[0]
        try:
            playerConfig = byteify(json.loads(tmp))['metadata']['qualities']
        except Exception:
            pass
        if playerConfig == None:
            tmp = self.cm.ph.getSearchGroups(data, r'var\s+config\s*=\s*({.+?});')[0]
            try:
                playerConfig = byteify(json.loads(tmp))['metadata']['qualities']
            except Exception:
                pass
            
        if None != playerConfig:
            hlsTab = []
            for quality, media_list in playerConfig.items():
                for media in media_list:
                    media_url = media.get('url')
                    if not media_url:
                        continue
                    type_ = media.get('type')
                    if type_ == 'application/vnd.lumberjack.manifest':
                        continue
                    if type_ == 'application/x-mpegURL' or media_url.split('?')[-1].endswith('m3u8'):
                        hlsTab.append(media_url)
                    else:
                        vidTab.append({'name':'dailymotion.com: %sp' % quality, 'url':media_url, 'quality':quality})
            
            if len(hlsTab) and 0 == len(vidTab):
                for media_url in hlsTab:
                    tmpTab = getDirectM3U8Playlist(media_url, False, checkContent=True, cookieParams={'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True})
                    cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
                    for tmp in tmpTab:
                        redirectUrl =  strwithmeta(tmp['url'], {'iptv_proto':'m3u8', 'Cookie':cookieHeader, 'User-Agent': HTTP_HEADER['User-Agent']})
                        vidTab.append({'name':'dailymotion.com: %sp hls' % (tmp.get('heigth', '0')), 'url':redirectUrl, 'quality':tmp.get('heigth', '0')})
                        
        if 0 == len(vidTab):
            data = CParsingHelper.getDataBeetwenMarkers(data, 'id="player"', '</script>', False)[1].replace('\/', '/')
            match = re.compile('"stream_h264.+?url":"(http[^"]+?H264-)([^/]+?)(/[^"]+?)"').findall(data)
            for i in range(len(match)):
                url = match[i][0] + match[i][1] + match[i][2]
                name = match[i][1]
                try: vidTab.append({'name': 'dailymotion.com: ' + name, 'url':url})
                except Exception: pass
        try: vidTab = sorted(vidTab, key=lambda item: int(item.get('quality', '0')))
        except Exception: pass
        return vidTab[::-1]

    def parserSIBNET(self, baseUrl):
        printDBG("parserSIBNET url[%s]" % baseUrl)
        videoUrls = []
        
        videoid = self.cm.ph.getSearchGroups(baseUrl+'|', """videoid=([0-9]+?)[^0-9]""")[0]
        #baseUrl.split('?')[0].endswith('.swf') and
        if '' != videoid: configUrl = "http://video.sibnet.ru/shell_config_xml.php?videoid=%s&partner=null&playlist_position=null&playlist_size=0&related_albid=0&related_tagid=0&related_ids=null&repeat=null&nocache" % (videoid)
        else: configUrl = baseUrl
        # get video for android
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        sts, data = self.cm.getPage(configUrl, {'header':HTTP_HEADER})
        if sts:
            url = self.cm.ph.getSearchGroups(data, """<file>(http[^<]+?\.mp4)</file>""")[0]
            if '' == url: url = self.cm.ph.getSearchGroups(data, """(http[^"']+?\.mp4)""")[0]
            if '' != url: videoUrls.append({'name':'video.sibnet.ru: mp4', 'url':url})
        # get video for PC
        sts, data = self.cm.getPage(configUrl)
        if sts:
            url = self.cm.ph.getSearchGroups(data, """<file>(http[^<]+?)</file>""")[0]
            if '' == url: url = self.cm.ph.getSearchGroups(data, """['"]file['"][ ]*?:[ ]*?['"]([^"^']+?)['"]""")[0]
            if url.split('?')[0].endswith('.m3u8'):
                retTab = getDirectM3U8Playlist(url)
                for item in retTab:
                    videoUrls.append({'name':'video.sibnet.ru: ' + item['name'], 'url':item['url']})
            elif '' != url: videoUrls.append({'name':'video.sibnet.ru: ' + url.split('.')[-1], 'url':url})
        return videoUrls
        '''
        # Old code not used
        mid = re.search('videoid=(.+?)$',url)
        ourl = 'http://video.sibnet.ru'
        movie = 'http://video.sibnet.ru/v/qwerty/'+mid.group(1)+'.mp4?start=0'
        query_data = { 'url': ourl+'/video'+mid.group(1), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        match = re.search("'file':'(.+?)'",link)
        if match:
            sUrl = match.group(1)
            if not sUrl.startswith('http'):
                sUrl = ourl + sUrl
            return sUrl
        else:
            return False
        '''

    def parserVK(self, baseUrl):
        printDBG("parserVK url[%s]" % baseUrl)
        
        COOKIE_FILE = GetCookieDir('vkcom.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def _doLogin(login, password):
             
            loginSts = False
            rm(COOKIE_FILE)
            loginUrl = 'https://vk.com/login'
            sts, data = self.cm.getPage(loginUrl, params)
            if not sts: return False
            data = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post"', '</form>', False, False)[1]
            action = self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0]
            printDBG(data)
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            post_data.update({'email':login, 'pass':password})
            if not self.cm.isValidUrl(action):
                return False
            params['header']['Referr'] = loginUrl
            sts, data =  self.cm.getPage(action, params, post_data)
            if not sts: return False
            sts, data =  self.cm.getPage('https://vk.com/', params)
            if not sts: return False            
            if 'logout_link' not in data: return False
            return True
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        login    = config.plugins.iptvplayer.vkcom_login.value
        password = config.plugins.iptvplayer.vkcom_password.value
        try:
            vkcom_login = self.vkcom_login
            vkcom_pass  = self.vkcom_pass
        except:
            rm(COOKIE_FILE)
            vkcom_login = ''
            vkcom_pass  = ''
            self.vkcom_login = ''
            self.vkcom_pass  = ''
            
            printExc()
        if '<div id="video_ext_msg">' in data or vkcom_login != login or vkcom_pass != password:
            rm(COOKIE_FILE)
            self.vkcom_login = login
            self.vkcom_pass  = password
            
            if login.strip() == '' or password.strip() == '':
                sessionEx = MainSessionWrapper() 
                sessionEx.waitForFinishOpen(MessageBox, _('To watch videos from http://vk.com/ you need to login.\nPlease fill your login and password in the IPTVPlayer configuration.'), type = MessageBox.TYPE_INFO, timeout = 10 )
                return False
            elif not _doLogin(login, password):
                sessionEx = MainSessionWrapper() 
                sessionEx.waitForFinishOpen(MessageBox, _('Login user "%s" to http://vk.com/ failed!\nPlease check your login data in the IPTVPlayer configuration.' % login), type = MessageBox.TYPE_INFO, timeout = 10 )
                return False
            else:
                sts, data = self.cm.getPage(baseUrl, params)
                if not sts: return False
        
        #data = self.cm.ph.getDataBeetwenMarkers(data, 'var playerParams =', '};', False, False)[1]
        
        movieUrls = []
        item = self.cm.ph.getSearchGroups(data, '''['"]?cache([0-9]+?)['"]?[=:]['"]?(http[^"]+?\.mp4[^;^"^']*)[;"']''', 2)
        if '' != item[1]:
            cacheItem = { 'name': 'vk.com: ' + item[0] + 'p (cache)', 'url':item[1].replace('\\/', '/').encode('UTF-8') }
        else: cacheItem = None
        
        tmpTab = re.findall('''['"]?url([0-9]+?)['"]?[=:]['"]?(http[^"]+?\.mp4[^;^"^']*)[;"']''', data)
        ##prepare urls list without duplicates
        for item in tmpTab:
            item = list(item)
            if item[1].endswith('&amp'): item[1] = item[1][:-4]
            item[1] = item[1].replace('\\/', '/')
            found = False
            for urlItem in movieUrls:
                if item[1] == urlItem['url']:
                    found = True
                    break
            if not found:        
                movieUrls.append({ 'name': 'vk.com: ' + item[0] + 'p', 'url':item[1].encode('UTF-8') })
        ##move default format to first position in urls list
        ##default format should be a configurable
        DEFAULT_FORMAT = 'vk.com: 720p'
        defaultItem = None
        for idx in range(len(movieUrls)):
            if DEFAULT_FORMAT == movieUrls[idx]['name']:
                defaultItem = movieUrls[idx]
                del movieUrls[idx]
                break
        movieUrls = movieUrls[::-1]
        if None != defaultItem:
            movieUrls.insert(0, defaultItem)
        if None != cacheItem:
            movieUrls.insert(0, cacheItem)
        return movieUrls

    def parserPETEAVA(self, url):
        mid = re.search("hd_file=(.+?_high.mp4)&", url)
        movie = "http://content.peteava.ro/video/"+mid.group(1)+"?token=PETEAVARO"
        return movie

    def parserVPLAY(self, url):
        vid = re.search("key=(.+?)$", url)
        query_data = { 'url': 'http://www.vplay.ro/play/dinosaur.do', 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
        postdata = {'key':vid.group(1)}
        link = self.cm.getURLRequestData(query_data, postdata)
        movie = re.search("nqURL=(.+?)&", link)
        if movie:
            return movie.group(1)
        else:
            return False

    def parserIITV(self, url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        query_data_non = { 'url': url + '.html?i&e&m=iitv', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        if 'streamo' in url:
            match = re.compile("url: '(.+?)',").findall(self.cm.getURLRequestData(query_data))
        if 'nonlimit' in url:
            match = re.compile('url: "(.+?)",     provider:').findall(self.cm.getURLRequestData(query_data_non))
        if len(match) > 0:
            linkVideo = match[0]
            print ('linkVideo ' + linkVideo)
            return linkVideo
        else:
            print ('Przepraszamy','Obecnie zbyt dużo osób ogląda film za pomocą', 'darmowego playera premium.', 'Sproboj ponownie za jakis czas')
        return False

    def parserDIVXSTAGE(self,url):
        return self._parserUNIVERSAL_B(url)
            
    def parserBESTREAMS(self, baseUrl):
        printDBG("parserBESTREAMS baseUrl[%s]" % baseUrl)
        USER_AGENT = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[/-]([A-Za-z0-9]{12})[/-]')[0]
        
        url = 'http://bestreams.net/{0}'.format(video_id)
        
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = USER_AGENT
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        
        tries = 0
        while tries < 3:
            tries += 1

            try:
                sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]
                sleep_time = int(sleep_time)
                if sleep_time < 12: time.sleep(sleep_time)
            except Exception:
                printExc()
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: continue
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            HTTP_HEADER['Referer'] = url
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
            if not sts: continue
            #printDBG(data)
            
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, 'id="file_title"', '</a>', False)[1]
                videoUrl = self.cm.ph.getSearchGroups(tmp, 'href="(http[^"]+?)"')[0]
                if '' == videoUrl: continue
                return urlparser.decorateUrl(videoUrl, {'User-Agent':USER_AGENT})
            except Exception:
                printExc()
            
        return False

    def parserTUBECLOUD(self, url):
        self.COOKIEFILE = self.COOKIE_PATH + "tubecloud.cookie"
        query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        HASH = re.search('name="hash" value="(.+?)">', link)
        if ID and FNAME and HASH > 0:
            time.sleep(105)
            postdata = {'fname' : FNAME.group(1), 'hash' : HASH.group(1), 'id' : ID.group(1), 'imhuman' : 'Proceed to video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.compile('file: "(.+?)"').findall(link)
            if len(match) > 0:
                linkvideo = match[0]
                return linkvideo
            else:
                return self.parserPLAYEDTO(url)
        else:
            return self.parserPLAYEDTO(url)
            
    def parserPLAYEDTO(self, url):
        sts, data = self.cm.getPage(url)
        url = re.search('file: "(http[^"]+?)"', data)
        if url:
            return url.group(1)
        return False
        
    def parserFREEDISC(self, baseUrl):
        linksTab = []
        
        COOKIE_FILE = GetCookieDir('freedicpl.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':False}
        
        tmpUrls = []
        if '/embed/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return linksTab
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<script type="application/ld+json">', '</script>', False)[1]
                tmp = byteify(json.loads(tmp))
                tmp = tmp['embedUrl'].split('?file=')
                if tmp[1].startswith('http'):
                    linksTab.append({'name':'freedisc.pl', 'url': urlparser.decorateUrl(tmp[1], {'Referer':tmp[0], 'User-Agent':HTTP_HEADER['User-Agent']})})
                    tmpUrls.append(tmp[1])
            except Exception:
                printExc()
                
            videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?/embed/[^"^']+?)["']''', 1, True)[0]
        else:
            videoUrl = baseUrl
        
        if '' == videoUrl: return linksTab
        params['load_cookie'] = True
        params['header']['Referer'] = baseUrl
        
        sts, data = self.cm.getPage(videoUrl, params)
        if not sts: return linksTab
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''data-video-url=["'](http[^"^']+?)["']''', 1, True)[0]
        if videoUrl == '': videoUrl = self.cm.ph.getSearchGroups(data, '''player.swf\?file=(http[^"^']+?)["']''', 1, True)[0]
        if videoUrl.startswith('http') and  videoUrl not in tmpUrls:
            linksTab.append({'name':'freedisc.pl', 'url': urlparser.decorateUrl(videoUrl, {'Referer':'http://freedisc.pl/static/player/v612/jwplayer.flash.swf', 'User-Agent':HTTP_HEADER['User-Agent']})})
        
        return linksTab

    def parserGINBIG(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        if ID and FNAME > 0:
            postdata = { 'op': 'download1', 'id': ID.group(1), 'fname': FNAME.group(1), 'referer': url, 'method_free': 'Free Download', 'usr_login': '' }
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            data = link.replace('|', '<>')
            PL = re.search('<>player<>(.+?)<>flvplayer<>', data)
            HS = re.search('video<>(.+?)<>(.+?)<>file<>', data)
            if PL and HS > 0:
                linkVideo = 'http://' + PL.group(1) + '.ginbig.com:' + HS.group(2) + '/d/' + HS.group(1) + '/video.mp4?start=0'
                print ('linkVideo ' + linkVideo)
                return linkVideo
            else:
                return False
        else:
            return False

    def parserQFER(self, url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        match = re.compile('"PSST",url: "(.+?)"').findall(self.cm.getURLRequestData(query_data))
        if len(match) > 0:
            linkVideo = match[0]
            print ('linkVideo ' + linkVideo)
            return linkVideo
        else:
            return False

    def parserSTREAMCLOUD(self, baseUrl):
        printDBG("parserSTREAMCLOUD [%s]" % baseUrl)
        # code from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/streamcloud.py
    
        _VALID_URL = r'https?://streamcloud\.eu/(?P<id>[a-zA-Z0-9_-]+)(?:/(?P<fname>[^#?]*)\.html)?'
        mobj = re.match(_VALID_URL, baseUrl)
        video_id = mobj.group('id')
        url = 'http://streamcloud.eu/%s' % video_id
        
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        fields = re.findall(r'''(?x)<input\s+
            type="(?:hidden|submit)"\s+
            name="([^"]+)"\s+
            (?:id="[^"]+"\s+)?
            value="([^"]*)"
            ''', data)
            
        time.sleep(12)
        
        sts, data = self.cm.getPage(url, {}, fields)
        if not sts: return False
        
        file = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]        
        if file.startswith('http'): return file

        return False

    def parserLIMEVIDEO(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        if ID and FNAME > 0:
            time.sleep(205)
            postdata = {'fname' : FNAME.group(1), 'id' : ID.group(1), 'method_free' : 'Continue to Video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            ID = re.search('name="id" value="(.+?)">', link)
            RAND = re.search('name="rand" value="(.+?)">', link)
            table = self.captcha.textCaptcha(link)
            value = table[0][0] + table [1][0] + table [2][0] + table [3][0]
            code = self.cm.html_entity_decode(value)
            print ('captcha-code :' + code)
            if ID and RAND > 0:
                postdata = {'rand' : RAND.group(1), 'id' : ID.group(1), 'method_free' : 'Continue to Video', 'op' : 'download2', 'referer' : url, 'down_direct' : '1', 'code' : code, 'method_premium' : '' }
                query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
                link = self.cm.getURLRequestData(query_data, postdata)
                data = link.replace('|', '<>')
                PL = re.search('<>player<>video<>(.+?)<>(.+?)<>(.+?)<><>(.+?)<>flvplayer<>', data)
                HS = re.search('image<>(.+?)<>(.+?)<>(.+?)<>file<>', data)
                if PL and HS > 0:
                    linkVideo = 'http://' + PL.group(4) + '.' + PL.group(3) + '.' + PL.group(2) + '.' + PL.group(1) + ':' + HS.group(3) + '/d/' + HS.group(2) + '/video.' + HS.group(1)
                    print ('linkVideo :' + linkVideo)
                    return linkVideo
                else:
                    return False
            else:
                return False
        else:
            return False

    def parserSCS(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('"(.+?)"; ccc', link)
        if ID > 0:
            postdata = {'f' : ID.group(1) }
            query_data = { 'url': 'http://scs.pl/getVideo.html', 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.compile("url: '(.+?)',").findall(link)
            if len(match) > 0:
                linkVideo = match[0]
                print ('linkVideo ' + linkVideo)
                return linkVideo
            else:
                print ('Przepraszamy','Obecnie zbyt dużo osób ogląda film za pomocą', 'darmowego playera premium.', 'Sproboj ponownie za jakis czas')
                return False
        else:
            return False
        
    def parserYOUWATCH(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-') + '.html'
        COOKIE_FILE = GetCookieDir('youwatchorg.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        tries = 0
        while tries < 3:
            tries += 1
            sts, data = self.cm.getPage(url, params)
            if not sts: return False
            if 'sources:' in data:
                break
            else:
                params['header']['Referer'] = url
                url = self.cm.ph.getSearchGroups(data, '<iframe[^>]*?src="(http[^"]+?)"', 1, True)[0].replace('\n', '')
        try:       
            linksTab = self._findLinks(data)
            if len(linksTab):
                for idx in range(len(linksTab)):
                    linksTab[idx]['url'] = urlparser.decorateUrl(linksTab[idx]['url'], {'User-Agent':HTTP_HEADER['User-Agent'],'Referer': url})
                return linksTab
        except Exception:
            pass
        
        def rc4(e, code):
            d = base64.b64decode(base64.b64decode(base64.b64decode(code)))
            b = []
            for a in range(256):
                b.append(a)
            c = 0
            for a in range(256):
                c = (c + b[a] + ord(d[a % len(d)])) % 256
                f = b[a]
                b[a] = b[c]
                b[c] = f
            a = 0
            c = 0
            d = 0
            g = ""
            for d in range(len(e)): 
                a = (a + 1) % 256
                c = (c + b[a]) % 256
                f = b[a]
                b[a] = b[c]
                b[c] = f
                g += chr(ord(e[d]) ^ b[(b[a] + b[c]) % 256])
            return g
        
        def link(e, code):
            e = base64.b64decode(base64.b64decode(e))
            return rc4(e, code)
        
        jsUrl = self.cm.ph.getSearchGroups(data, '"(http[^"]+?==\.js)"', 1, True)[0]
        sts, data = self.cm.getPage(jsUrl, params)
        printDBG(data)
        code = self.cm.ph.getSearchGroups(data, 'code[ ]*?\=[ ]*?"([^"]+?)"')[0]
        direct_link = self.cm.ph.getSearchGroups(data, 'direct_link[ ]*?\=[^"]*?"([^"]+?)"')[0]    
        videoUrl = link(direct_link, code)
        if not videoUrl.strtswith("http"): return False
        videoUrl = urlparser.decorateUrl(videoUrl, {'User-Agent':HTTP_HEADER['User-Agent'],'Referer': url})
        return videoUrl
        
    def parserSTREAMENET(self, baseUrl):
        return self.parserWATCHERSTO(baseUrl)
        
    def parserESTREAMTO(self, baseUrl):
        return self.parserWATCHERSTO(baseUrl)
        
    def parserWATCHERSTO(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-').replace('me/', 'me/embed-').replace('.net/', '.net/embed-')
            if not url.endswith('.html'):
             url += '-640x360.html'

        sts, allData = self.cm.getPage(url)
        if not sts: return False
        
        errMsg = clean_html(CParsingHelper.getDataBeetwenMarkers(allData, '<div class="delete"', '</div>')[1]).strip()
        if errMsg != '': SetIPTVPlayerLastHostError(errMsg)
        
        # get JS player script code from confirmation page
        sts, tmpData = CParsingHelper.getDataBeetwenMarkers(allData, ">eval(", '</script>', False)
        if sts:
            data = tmpData
            tmpData = None
            # unpack and decode params from JS player script code
            data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0, r2=True) #YOUWATCH_decryptPlayerParams == VIDUPME_decryptPlayerParams

        printDBG(data)
        
        # get direct link to file from params
        linksTab = self._findLinks(data, serverName=urlparser.getDomain(baseUrl))
        if len(linksTab): return linksTab
        
        domain = urlparser.getDomain(url, False) 
        tmp = self.cm.ph.getDataBeetwenMarkers(allData, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0] 
            if 'video' not in type and 'x-mpeg' not in type: continue
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url):
                if 'video' in type:
                    linksTab.append({'name':'[%s]' % type, 'url':url})
                elif 'x-mpeg' in type:
                    linksTab.extend(getDirectM3U8Playlist(url, checkContent=True))
        return linksTab[::-1]

    def parserPLAYEDTO(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-').replace('me/', 'me/embed-')
            if not url.endswith('.html'):
             url += '-640x360.html'
             
        #HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'}
        #, {'header':HTTP_HEADER}
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        url = self.cm.ph.getSearchGroups(data, '<iframe[^>]*?src="(http[^"]+?)"', 1, True)[0]
        if url != '':
            sts, data = self.cm.getPage(url, {'header':{'Referer':url, 'User-Agent':'Mozilla/5.0'}})
            if not sts: return False
        
        # get JS player script code from confirmation page
        sts, tmpData = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
        if sts:
            data = tmpData
            tmpData = None
            # unpack and decode params from JS player script code
            data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0) #YOUWATCH_decryptPlayerParams == VIDUPME_decryptPlayerParams

        printDBG(data)
        return self._findLinks(data, serverName='played.to')
        
    '''
    def parserALLMYVIDEOS(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        if ID and FNAME > 0:
            time.sleep(105)
            postdata = {'fname' : FNAME.group(1), 'method_free' : '1', 'id' : ID.group(1), 'x' : '82', 'y' : '13', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.compile('"file" : "(.+?)",').findall(link)
            if len(match) > 0:
                linkVideo = match[0]
                print ('linkVideo ' + linkVideo)
                return linkVideo
            else:
                return False
        else:
            return False
    '''
            
    def parserVIDEOMEGA(self, baseUrl):
        baseUrl = strwithmeta(baseUrl)
        Referer = baseUrl.meta.get('Referer', 'http://nocnyseans.pl/film/chemia-2015/15471') 
        
        video_id  = self.cm.ph.getSearchGroups(baseUrl, 'https?://(?:www\.)?videomega\.tv/(?:iframe\.php|cdn\.php|view\.php)?\?ref=([A-Za-z0-9]+)')[0]
        if video_id == '': video_id = self.cm.ph.getSearchGroups(baseUrl + '&', 'ref=([A-Za-z0-9]+)[^A-Za-z0-9]')[0]
        COOKIE_FILE = GetCookieDir('videomegatv.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36',
                       'Accept-Encoding':  'gzip,deflate,sdch'} # (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10' }
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        #if 'iframe' in baseUrl:
        #    iframe_url = 'http://videomega.tv/iframe.php?ref=%s' % (video_id)
        #    url = 'http://videomega.tv/iframe.php?ref=%s' % (video_id)
        #else:
            
        for i in range(2):
        
            if i == 0:
                iframe_url = 'http://videomega.tv/?ref=%s' % (video_id)
                url = 'http://videomega.tv/cdn.php?ref=%s' % (video_id)
            else:
                url = 'http://videomega.tv/view.php?ref=%s&width=730&height=440&val=1' % (video_id)
                iframe_url = url
            
            HTTP_HEADER['Referer'] = Referer
            sts, data = self.cm.getPage(url, params)
            if not sts: 
                continue
            if 'dmca ' in data:
                DMCA = True
                SetIPTVPlayerLastHostError("'Digital Millennium Copyright Act' detected.")
                return False
            else: DMCA = False
            
            adUrl =self.cm.ph.getSearchGroups(data, '"([^"]+?/ad\.php[^"]+?)"')[0]
            if adUrl.startswith("/"): 
                adUrl = 'http://videomega.tv' + adUrl
            
            params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} 
            HTTP_HEADER['Referer'] = url
            if adUrl:
                sts, tmp = self.cm.getPage(adUrl, params)
            
            subTracksData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track ', '>', False, False)
            subTracks = []
            for track in subTracksData:
                if 'kind="captions"' not in track: continue
                subUrl = self.cm.ph.getSearchGroups(track, 'src="(http[^"]+?)"')[0]
                subLang = self.cm.ph.getSearchGroups(track, 'srclang="([^"]+?)"')[0]
                subLabel = self.cm.ph.getSearchGroups(track, 'label="([^"]+?)"')[0]
                subTracks.append({'title':subLabel + '_' + subLang, 'url':subUrl, 'lang':subLang, 'format':'srt'})
            
            linksTab = []
            fakeLinkVideo  = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"[^>]+?type="video')[0]
            
            # get JS player script code from confirmation page
            sts, data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>')
            if not sts: continue
            
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            printDBG(data)
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            
            # unpack and decode params from JS player script code
            decrypted = False
            for decryptor in [SAWLIVETV_decryptPlayerParams, VIDUPME_decryptPlayerParams]:
                try:
                    data = unpackJSPlayerParams(data, decryptor, 0)
                    if len(data):
                        decrypted = True
                    break
                except Exception:
                    continue
            if not decrypted: continue
            
            linkVideo  = self.cm.ph.getSearchGroups(data, '"(http[^"]+?\.mp4\?[^"]+?)"')[0]
            
            if fakeLinkVideo == linkVideo:
                SetIPTVPlayerLastHostError(_("Videomega has blocked your IP for some time.\nPlease retry this link after some time."))
                if i == 0: time.sleep(3)
                continue
            
            #printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            #printDBG("DMCA [%r]" % DMCA)

            if linkVideo.startswith('http'):
                linksTab.append({'name': 'videomega_2', 'url':urlparser.decorateUrl(linkVideo, {'external_sub_tracks':subTracks, "iptv_wget_continue":True, "iptv_wget_timeout":10, "Orgin": "http://videomega.tv/", 'Referer': url, 'User-Agent':HTTP_HEADER['User-Agent'], 'iptv_buffering':'required'})})
            #"Cookie": "__cfduid=1", "Range": "bytes=0-",
        return linksTab

    def parserVIDTO(self, baseUrl):
        printDBG('parserVIDTO baseUrl[%s]' % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[\./]')[0]
            url = 'http://vidto.me/embed-{0}-640x360.html'.format(video_id)
        else:
            url = baseUrl 
        params = {'header' : HTTP_HEADER}
        sts, data = self.cm.getPage(url, params)
        
        # get JS player script code from confirmation page
        tmp = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>')[1]
        if not sts: return False
        # unpack and decode params from JS player script code
        tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
        if tmp != None: data = tmp + data
        printDBG(tmp)
        subData = CParsingHelper.getDataBeetwenMarkers(data, "captions", '}')[1]
        subData = self.cm.ph.getSearchGroups(subData, '''['"](http[^'^"]+?)['"]''')[0]
        sub_tracks = []
        if (subData.startswith('https://') or subData.startswith('http://')) and (subData.endswith('.srt') or subData.endswith('.vtt')):
            sub_tracks.append({'title':'attached', 'url':subData, 'lang':'unk', 'format':'srt'})
        linksTab = []
        links = self._findLinks(data, 'vidto.me')
        for item in links:
            item['url'] = strwithmeta(item['url'], {'external_sub_tracks':sub_tracks})
            linksTab.append(item)
        return linksTab

    def parserVIDSTREAM(self,url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        link = self.cm.getURLRequestData(query_data)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        HASH = re.search('name="hash" value="(.+?)">', link)
        if ID and FNAME and HASH > 0:
            time.sleep(55)
            postdata = {'fname' : FNAME.group(1), 'id' : ID.group(1), 'hash' : HASH.group(1), 'imhuman' : 'Proceed to video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
            link = self.cm.getURLRequestData(query_data, postdata)
            match = re.compile('file: "(.+?)",').findall(link)
            if len(match) > 0:
                linkVideo = match[0]
                printDBG ('linkVideo :' + linkVideo)
                return linkVideo
            else:
                return False
        else:
            return False
        
    def parserYANDEX(self, url):
        #http://www.kreskoweczki.pl/kreskowka/71428/nawiedzeni_4-haunted-kids/
        #http://seositer.com/player10-loader.swf?login=eriica&storage_directory=xeacxjweav.5822/&is-hq=false
        #player10-loader.swf?login=eriica&storage_directory=xeacxjweav.5822/&is-hq=true
        DEFAULT_FORMAT = 'mpeg4_low'
        # authorization
        authData = ''
        urlElems = urlparse(url)
        urlParams = parse_qs(urlElems.query)
        if 0 < len(urlParams.get('file', [])):
            return urlParams['file'][0]
        elif 0 < len(urlParams.get('login', [])) and 0 < len(urlParams.get('storage_directory', [])):
            authData = urlParams['login'][0] + '/' + urlParams['storage_directory'][0]
        elif 'vkid=' in url:
            sts, data = self.cm.getPage(url)
            if not sts: return False
            data = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
            return urlparser().getVideoLink(data, True)
        else:
            # last chance
            r = re.compile('iframe/(.+?)\?|$').findall(url)
            if 0 <= len(r): return False
            authData = r[0]
        # consts
        playerUrlPrefix    = "http://flv.video.yandex.ru/"
        tokenUrlPrefix     = "http://static.video.yandex.ru/get-token/"
        serviceHostUrl     = "http://video.yandex.ru/"
        storageHostUrl     = "http://static.video.yandex.ru/"
        clipStorageHostUrl = "http://streaming.video.yandex.ru/"
        nameSpace          = "get"
        FORMATS_MAP = {}
        FORMATS_MAP["flv_low"]          = "0.flv"
        FORMATS_MAP["mpeg4_low"]        = "m450x334.mp4"
        FORMATS_MAP["mpeg4_med"]        = "medium.mp4"
        FORMATS_MAP["mpeg4_hd_720p"]    = "m1280x720.mp4"
        FORMATS_MAP["flv_h264_low"]     = "m450x334.flv"
        FORMATS_MAP["flv_h264_med"]     = "medium.flv"
        FORMATS_MAP["flv_h264_hd_720p"] = "m1FLV_SAME_QUALITY280x720.flv"
        FORMATS_MAP["flv_same_quality"] = "sq-medium.flv"
        
        # get all video formats info
        # http://static.video.yandex.ru/get/eriica/xeacxjweav.5822//0h.xml?nc=0.9776535825803876
        url = storageHostUrl + nameSpace + "/" + authData + "/0h.xml?nc=" + str(random())
        sts, data = self.cm.getPage(url)
        if not sts: return False
        try:
            formatsTab = []
            defaultItem = None
            for videoFormat in cElementTree.fromstring(data).find("formats_available").getiterator():
                fileName = FORMATS_MAP.get(videoFormat.tag, '')
                if '' != fileName:
                    bitrate  = int(videoFormat.get('bitrate', 0))
                    formatItem = { 'bitrate': bitrate, 'file':fileName, 'ext':fileName[-3:] }
                    if DEFAULT_FORMAT == videoFormat.tag:
                        defaultItem = formatItem
                    else:
                        formatsTab.append(formatItem)
            if None != defaultItem: formatsTab.insert(0, defaultItem)
            if 0 == len(formatsTab): return False
            # get token
            token = tokenUrlPrefix + authData + "?nc=" + str(random())
            sts, token = self.cm.getPage(token)
            sts, token = CParsingHelper.getDataBeetwenMarkers(token, "<token>", '</token>', False)
            if not sts:
                printDBG("parserYANDEX - get token problem")
                return False
            movieUrls = []
            for item in formatsTab:
                # get location
                location = clipStorageHostUrl + 'get-location/' + authData + '/' + item['file'] + '?token=' + token + '&ref=video.yandex.ru'
                sts, location = self.cm.getPage(location)
                sts, location = CParsingHelper.getDataBeetwenMarkers(location, "<video-location>", '</video-location>', False)
                if sts: movieUrls.append({ 'name': 'yandex.ru: ' + item['ext'] + ' bitrate: ' + str(item['bitrate']), 'url':location.replace('&amp;', '&') })
                else: printDBG("parserYANDEX - get location problem")
            return movieUrls
        except Exception:
            printDBG("parserYANDEX - formats xml problem")
            printExc()
            return False
        
    def parserANIMESHINDEN(self, url):
        query_data = { 'url': url, 'return_data': False }       
        response = self.cm.getURLRequestData(query_data)
        redirectUrl = response.geturl() 
        response.close()
        redirectUrl = redirectUrl.replace('https', 'http')
        return redirectUrl

    def parserRUTUBE(self, url):
        if '//rutube.ru/video/embed' in url or '//rutube.ru/play/embed/' in url:
            sts, data = self.cm.getPage(url)
            if not sts: return False
            data = re.search('href="([^"]+?)"', data)
            if not data: return False
            url = data.group(1)
        videoID = ''
        url += '/'

        # get videoID/hash
        match = re.search('video\.rutube\.ru/(\w+?)/', url)
        if match:
            videoID = match.group(1)
        else:
            match = re.search('/video/(\w+?)/', url)
            if match:
                videoID = match.group(1)
            else:
                match = re.search('hash=([^/]+?)/', url)
                if match:
                    videoID = match.group(1)
        if '' != videoID:
            printDBG('parserRUTUBE:                 videoID[%s]' % videoID)
            # get videoInfo:
            #vidInfoUrl = 'http://rutube.ru/api/play/trackinfo/%s/?format=json' % videoID
            vidInfoUrl = 'http://rutube.ru/api/play/options/%s/?format=json&referer=&no_404=true&sqr4374_compat=1' % videoID
            query_data = { 'url': vidInfoUrl, 'return_data': True }
            try:
                videoInfo = self.cm.getURLRequestData(query_data)
            except Exception:
                printDBG('parserRUTUBE problem with getting video info page')
                return []
            printDBG('---------------------------------------------------------')
            printDBG(videoInfo)
            printDBG('---------------------------------------------------------')
            # "m3u8": "http://bl.rutube.ru/ae8621ff85153a30c398746ed8d6cc03.m3u8"
            # "f4m": "http://bl.rutube.ru/ae8621ff85153a30c398746ed8d6cc03.f4m"
            videoUrls = []
            match = re.search('"m3u8":[ ]*?"(http://bl\.rutube\.ru/.+?)"', videoInfo)
            if match:
                printDBG('parserRUTUBE m3u8 link[%s]' % match.group(1))
                retTab = getDirectM3U8Playlist(match.group(1))
                videoUrls.extend(retTab)
            else:
                printDBG('parserRUTUBE there is no m3u8 link in videoInfo:')
                printDBG('---------------------------------------------------------')
                printDBG(videoInfo)
                printDBG('---------------------------------------------------------')
               
            match = re.search('"default":[ ]*?"(http://[^"]+?f4m[^"]*?)"', videoInfo)
            if match:
                printDBG('parserRUTUBE f4m link[%s]' % match.group(1))
                retTab = getF4MLinksWithMeta(match.group(1))
                videoUrls.extend(retTab)
            return videoUrls
        else:
            printDBG('parserRUTUBE ERROR cannot find videoID in link[%s]' % url)
            return []
    
    def parserYOUTUBE(self, url):
        if None != self.getYTParser():
            try:
                formats = config.plugins.iptvplayer.ytformat.value
                bitrate = config.plugins.iptvplayer.ytDefaultformat.value
                dash    = config.plugins.iptvplayer.ytShowDash.value
            except Exception:
                printDBG("parserYOUTUBE default ytformat or ytDefaultformat not available here")
                formats = "mp4"
                bitrate = "360"
                dash    = False
            
            tmpTab, dashTab = self.getYTParser().getDirectLinks(url, formats, dash, dashSepareteList = True)
            # move default URL to the TOP of list
            if 1 < len(tmpTab):
                def __getLinkQuality( itemLink ):
                    tab = itemLink['format'].split('x')
                    return int(tab[0])

                # get default item
                defItem = CSelOneLink(tmpTab, __getLinkQuality, int(bitrate)).getOneLink()[0]
                # remove default item
                tmpTab[:] = [x for x in tmpTab if x['url'] != defItem['url']]
                # add default item at top
                tmpTab.insert(0, defItem)
                    
            videoUrls = []
            for item in tmpTab:
                url = strwithmeta(item['url'], {'youtube_id':item.get('id', '')})
                videoUrls.append({ 'name': 'YouTube: ' + item['format'] + '\t' + item['ext'] , 'url':url})
            for item in dashTab:
                url = strwithmeta(item['url'], {'youtube_id':item.get('id', '')})
                videoUrls.append({'name': _("[For download only] ") + item['format'] + ' | dash', 'url':url})
            return videoUrls

        return False
        
    def parserTINYMOV(self, url):
        printDBG('parserTINYMOV url[%s]' % url)
        sts, data = self.cm.getPage(url)
        if sts:
            match = re.search("url: '([^']+?.mp4|[^']+?.flv)',", data)
            if match:
                linkVideo = match.group(1)
                printDBG ('parserTINYMOV linkVideo :' + linkVideo)
                return linkVideo
            
        return False
     
    def parserTOPUPLOAD(self, url):
        url = url.replace('topupload.tv', 'maxupload.tv')
        HTTP_HEADER = {'Referer':url}
        post_data = {'ok':'yes', 'confirm':'Close+Ad+and+Watch+as+Free+User', 'submited':'true'}        
        sts, data = self.cm.getPage(url=url, addParams={'header':HTTP_HEADER}, post_data = post_data)
        if sts:
            posibility = ["'file': '([^']+?)'", "file: '([^']+?)'", "'url': '(http[^']+?)'", "url: '(http[^']+?)'"]
            for posibe in posibility:
                match = re.search(posibe, data)  
                if match:
                    try:
                        header = {'Referer':'http://www.maxupload.tv/media/swf/player/player.swf'}
                        query_data = { 'url': match.group(1), 'return_data': False, 'header':header }
                        response = self.cm.getURLRequestData(query_data)
                        redirectUrl = response.geturl() 
                        response.close()
                        return redirectUrl
                    except Exception:
                        printExc()
            else:
                printDBG('parserTOPUPLOAD direct link not found in return data')
        else:
            printDBG('parserTOPUPLOAD error when getting page')
        return False
        
    def parserLIVELEAK(self, baseUrl):
        printDBG('parserLIVELEAK baseUrl[%s]' % baseUrl)
        urlTab = []
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            file_url    = urllib.unquote(self.cm.ph.getSearchGroups(data, 'file_url=(http[^&]+?)&')[0])
            hd_file_url = urllib.unquote(self.cm.ph.getSearchGroups(data, 'hd_file_url=(http[^&]+?)&')[0])
            if '' != file_url:
                urlTab.append({'name':'liveleak.com SD', 'url':file_url})
            if '' != hd_file_url:
                urlTab.append({'name':'liveleak.com HD', 'url':hd_file_url})
            if len(urlTab) == 0:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
                for item in tmp:
                    if 'video/mp4' in item or '.mp4' in item:
                        label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                        if label == '': label = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                        url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                        if url.startswith('//'): url = 'http:' + url
                        if not self.cm.isValidUrl(url): continue
                        urlTab.append({'name':label, 'url':strwithmeta(url, {'Referer':baseUrl})})
                
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % urlTab)
            if 0 == len(urlTab):
                data = re.compile('<iframe[^>]+?src="([^"]+?youtube[^"]+?)"').findall(data)
                for item in data:
                    url = item
                    if url.startswith('//'): url = 'http:' + url
                    if not self.cm.isValidUrl(url): continue
                    urlTab.extend(self.parserYOUTUBE(url))
        return urlTab
            
    def parserVIDUPME(self, baseUrl):
        printDBG("parserVIDUPME baseUrl[%r]" % baseUrl)
        # example video: http://beta.vidup.me/embed-p1ko9zqn5e4h-640x360.html
        #def _findLinks(data):
        #    return self._findLinks(data, 'vidup.me', m1='setup(', m2='image:')
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidup.me/embed-{0}-640x360.html', self._findLinks)
        
    def parserVIDLOXTV(self, baseUrl):
        printDBG("parserVIDLOXTV baseUrl[%r]" % baseUrl)
        # example video: http://vidlox.tv/embed-e9r0y7i65i1v.html
        def _findLinks(data):
            linksTab = []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
            data = re.compile('"(http[^"]+?)"').findall(data)
            for link in data:
                if link.split('?')[0].endswith('m3u8'):
                    linksTab.extend(getDirectM3U8Playlist(link, checkContent=True))
                elif link.split('?')[0].endswith('mp4'):
                    linksTab.append({'name':'mp4', 'url': link})
            return linksTab
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidlox.tv/embed-{0}.html', _findLinks)
        
    def parserVIDABCCOM(self, baseUrl):
        printDBG("parserVIDABCCOM baseUrl[%r]" % baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidabc.com/embed-{0}.html', self._findLinks)
        
    def parserFASTPLAYCC(self, baseUrl):
        printDBG("parserFASTPLAYCC baseUrl[%r]" % baseUrl)
        return self._parserUNIVERSAL_A(strwithmeta(baseUrl, {'Referer':''}), 'http://fastplay.cc/embed-{0}.html', self._findLinks)
    
    def parserSPRUTOTV(self, baseUrl):
        printDBG("parserSPRUTOTV baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        return self._findLinks(data, serverName='spruto.tv', linkMarker=r'''['"]?file['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='Uppod(', m2=')', contain='.mp4')
        
    def parserRAPTUCOM(self, baseUrl):
        printDBG("parserRAPTUCOM baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1].strip()
        data = self.cm.ph.getDataBeetwenMarkers(data, '"sources":', ']', False)[1].strip()
        data = byteify(json.loads(data+']'))
        printDBG(data)
        retTab = []
        for item in data:
            try: retTab.append({'name':'raptu.com ' + item.get('label', item.get('res', '')), 'url':item['file']})
            except Exception: pass
        return retTab[::-1]
        
    def parserOVVATV(self, baseUrl):
        printDBG("parserOVVATV baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'ovva(', ')', False)[1].strip()[1:-1]
        data = json.loads(base64.b64decode(data))
        url = data['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return False
        data = data.strip()
        if data.startswith('302='):
            url = data[4:]
        
        return getDirectM3U8Playlist(url, checkContent=True)[::-1]
            
    def parseMOSHAHDANET(self, baseUrl):
        printDBG("parseMOSHAHDANET baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False)[1]
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        try:
            sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9])</span>')[0])
            time.sleep(sleep_time)
        except Exception:
            printExc()
            
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
        if not sts: return False
        
        printDBG(data)
        return self._findLinks(data, 'moshahda.net')
        
        linksTab = []
        srcData = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', '],', False)[1].strip()
        srcData = byteify(json.loads(srcData+']')) 
        for link in srcData:
            if not self.cm.isValidUrl(link): continue
            if link.split('?')[0].endswith('m3u8'):
                tmp = getDirectM3U8Playlist(link)
                linksTab.extend(tmp)
            else:
                linksTab.append({'name': 'mp4', 'url':link})
        return linksTab
                
        #return self._findLinks(data, 'moshahda.net', linkMarker=r'''['"](http[^"^']+)['"]''')
        
    def parseSTREAMMOE(self, baseUrl):
        printDBG("parseSTREAMMOE baseUrl[%r]" % baseUrl)
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        url = baseUrl
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: sts, data = self.cm.getPageWithWget(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub('''atob\(["']([^"^']+?)['"]\)''', lambda m: base64.b64decode(m.group(1)), data)
        printDBG(data)
        tab = self._findLinks(data, 'stream.moe', linkMarker=r'''['"]?url['"]?[ ]*:[ ]*['"](http[^"^']+(?:\.mp4|\.flv)[^"^']*)['"][,}]''', m1='clip:')
        if len(tab) == 0:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
            for item in data:
                if 'video/mp4' in item:
                    url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                    tab.append({'name':'stream.moe', 'url':url})
            return tab
        
    def parseCASTFLASHPW(self, baseUrl):
        printDBG("parseCASTFLASHPW baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl) 
        aesKey = baseUrl.meta.get('aes_key', '') 
        
        def getUtf8Str(st):
            idx = 0
            st2 = ''
            while idx < len(st):
                st2 += '\\u0' + st[idx:idx + 3]
                idx += 3
            return st2.decode('unicode-escape').encode('UTF-8')
            
        def cryptoJS_AES_decrypt(encrypted, password, salt):
            def derive_key_and_iv(password, salt, key_length, iv_length):
                d = d_i = ''
                while len(d) < key_length + iv_length:
                    d_i = md5(d_i + password + salt).digest()
                    d += d_i
                return d[:key_length], d[key_length:key_length+iv_length]
            bs = 16
            key, iv = derive_key_and_iv(password, salt, 32, 16)
            cipher = AES_CBC(key=key, keySize=32)
            return cipher.decrypt(encrypted, iv)
        
        #['Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10']
        for agent in ['Mozilla/5.0 (iPhone; CPU iPhone OS 9_0_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13A452 Safari/601.1']: 
            HTTP_HEADER= { 'User-Agent':agent, 'Referer':Referer }
            COOKIE_FILE = GetCookieDir('sport365live.cookie') #('castflashpw.cookie')
            baseParams = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':False, 'save_cookie':True} 
            params = dict(baseParams)
            
            url = baseUrl
            sts, data = self.cm.getPage(url, params)
            if not sts: return False
            
            printDBG(data)
            
            post_data = self.cm.ph.getDataBeetwenMarkers(data, '<form ', '</form>', withMarkers=False, caseSensitive=False)[1]
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', post_data))
            params['header']['Referer'] = url
            params['load_cookie'] = True
            url = self.cm.ph.getSearchGroups(data, '''attr\([^<]*?['"]action["'][^<]*?\,[^<]*?["'](http[^'^"]+?)['"]''')[0]
            printDBG(url)
            
            sts, data = self.cm.getPage(url, params, post_data)
            printDBG(data)
            if not sts: return False
            
            linksData = []
            tmp = self.cm.ph.getSearchGroups(data, '''\(([^)]+?)\)''')[0].split(',')
            for t in tmp:
                linksData.append(t.replace('"', '').strip())
            printDBG(linksData)
            
            for idx in [1, 2]:
                try:
                    linkData = base64.b64decode(linksData[idx])
                except Exception:
                    pass
            linkData   = byteify(json.loads(linkData))
            
            ciphertext = base64.b64decode(linkData['ct'])
            iv         = a2b_hex(linkData['iv'])
            salt       = a2b_hex(linkData['s'])
            
            playerUrl = cryptoJS_AES_decrypt(ciphertext, aesKey, salt)
            playerUrl = byteify(json.loads(playerUrl))
            if playerUrl.startswith('#') and 3 < len(playerUrl): 
                playerUrl = getUtf8Str(playerUrl[1:])
            printDBG("[[[[[[[[[[[[[[[[[[[[[[%r]" % playerUrl)
            if playerUrl.startswith('http'):
                COOKIE_FILE_M3U8 = GetCookieDir('sport365live.cookie')
                params = {'cookiefile':COOKIE_FILE_M3U8, 'use_cookie': True, 'load_cookie':False, 'save_cookie':True} 
                playerUrl = urlparser.decorateUrl(playerUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':'http://h5.adshell.net/peer5', 'Origin':'http://h5.adshell.net', 'User-Agent':HTTP_HEADER['User-Agent']})
                try:
                    import uuid
                    playerUrl.meta['X-Playback-Session-Id'] = str(uuid.uuid1()).upper()
                except Exception:
                    printExc()
                
                urlsTab = getDirectM3U8Playlist(playerUrl, False, cookieParams=params)
                try:
                    PHPSESSID = self.cm.getCookieItem(COOKIE_FILE_M3U8, 'PHPSESSID')
                    newUrlsTab = []
                    for item in urlsTab:
                        if PHPSESSID != '': item['url'].meta['Cookie'] = 'PHPSESSID=%s' % PHPSESSID
                        newUrlsTab.append(item)
                    return newUrlsTab
                except Exception:
                    printExc()
                    return urlsTab
                    
                params = dict(baseParams)
                params['header']['Referer'] = 'http://www.sport365.live/en/main'
                sts, data = self.cm.getPage("http://www.sport365.live/en/sidebar", params)
                if not sts: return False
                
        return False
        
    def parserTRILULILU(self, baseUrl):
        def getTrack(userid, hash):
            hashLen = len(hash) / 2
            mixedStr = (hash[0:hashLen] + userid) + hash[hashLen:len(hash)]
            md5Obj = MD5()
            hashTab = md5Obj(mixedStr)
            return hexlify(hashTab)
        
        match = re.search("embed\.trilulilu\.ro/video/([^/]+?)/([^.]+?)\.swf", baseUrl)
        data = None
        if not match:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
            match = re.search('userid=([^"^<^>^&]+?)&hash=([^"^<^>^&]+?)&', data)
        if match:          
            userid = match.group(1)
            hash = match.group(2)
            refererUrl = "http://static.trilulilu.ro/flash/player/videoplayer2011.swf?userid=%s&hash=%s&referer=" % (userid, hash)
            fileUrl = "http://embed.trilulilu.ro/flv/" + userid + "/" + hash + "?t=" + getTrack(userid, hash) + "&referer=" + urllib.quote_plus( base64.b64encode(refererUrl) ) + "&format=mp4-360p"
            return fileUrl
        # new way to get video
        if sts:
            url = self.cm.ph.getSearchGroups(data, 'id="link" href="(http[^"]+?)"')[0]
            if '' != url:
                HTTP_HEADER = dict(self.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = baseUrl
                sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
                data = self.cm.ph.getSearchGroups(data, """["']*video["']*:[ ]*["']([^"']+?)["']""")[0]
                if '' != data:
                    if data.startswith('//'):
                        data = 'http:' + data
                    return data
        return False
        
    def parserVIDEA(self, url):
        sts, data = self.cm.getPage(url)
        if not sts: return False
        r = re.compile('v=(.+?)&eventHandler').findall(data)
        sts, data = self.cm.getPage('http://videa.hu/flvplayer_get_video_xml.php?v='+r[0])
        if not sts: return False
        r2 = re.compile('video_url="(.+?)"').findall(data)
        return r2[0]

    def parserALIEZ(self, url):
        sts, data = self.cm.getPage(url)
        if not sts: return False
        r = re.compile("file:.+?'(.+?)'").findall(data)
        return r[0]
    
    def parserCOUDMAILRU(self, baseUrl):
        printDBG("parserCOUDMAILRU baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        weblink  = self.cm.ph.getSearchGroups(data, '"weblink"\s*:\s*"([^"]+?)"')[0]
        videoUrl = self.cm.ph.getSearchGroups(data, '"weblink_video"\s*:[^\]]*?"url"\s*:\s*"(https?://[^"]+?)"')[0]
        videoUrl += '0p/%s.m3u8?double_encode=1' % (base64.b64encode(weblink))
        videoUrl = strwithmeta(videoUrl, {'User-Agent':HTTP_HEADER['User-Agent']})
        
        return getDirectM3U8Playlist(videoUrl, checkContent=True)
    
    def parserVIDEOMAIL(self, url):
        printDBG("parserVIDEOMAIL baseUrl[%s]" % url)
        #http://api.video.mail.ru/videos/embed/mail/etaszto/_myvideo/852.html
        #http://my.mail.ru/video/mail/etaszto/_myvideo/852.html#video=/mail/etaszto/_myvideo/852
        COOKIEFILE = self.COOKIE_PATH + "video.mail.ru.cookie"
        movieUrls = []
        try:
            sts, data = self.cm.getPage(url, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False})
            if 'This video is only available on Mail.Ru' in data:
                tmpUrl = self.cm.ph.getSearchGroups(data, 'href="([^"]+?)"')[0]
                sts, data = self.cm.getPage(tmpUrl)
            metadataUrl =  self.cm.ph.getSearchGroups(data, """["']*metadataUrl["']*[ ]*:[ ]*["'](http[^"']+?\.json[^"']*?)["']""")[0]
            if '' == metadataUrl:
                tmp =  self.cm.ph.getSearchGroups(data, """["']*metadataUrl["']*[ ]*:[ ]*["'][^0-9]*?([0-9]{19})[^0-9]*?["']""")[0]
                if '' == tmp:
                    tmp = self.cm.ph.getSearchGroups(data, '<link[^>]*?rel="image_src"[^>]*?href="([^"]+?)"')[0]
                    if '' == tmp: tmp = self.cm.ph.getSearchGroups(data, '<link[^>]*?href="([^"]+?)"[^>]*?rel="image_src"[^>]*?')[0]
                    tmp = self.cm.ph.getSearchGroups(urllib.unquote(tmp), '[^0-9]([0-9]{19})[^0-9]')[0]
                metadataUrl = 'http://videoapi.my.mail.ru/videos/{0}.json?ver=0.2.102'.format(tmp)
            sts, data = self.cm.getPage(metadataUrl, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True})
            video_key = self.cm.getCookieItem(COOKIEFILE,'video_key')
            if '' != video_key:
                data = json.loads(data)['videos']
                for item in data:
                    videoUrl = strwithmeta(item['url'].encode('utf-8'), {'Cookie':"video_key=%s" % video_key, 'iptv_buffering':'required'})
                    videoName = 'mail.ru: %s' % item['key'].encode('utf-8')
                    movieUrls.append({ 'name': videoName, 'url': videoUrl}) 
        except Exception:
            printExc()
        # Try old code extractor
        if 0 == len(movieUrls):
            idx = url.find(".html")
            if 1 > idx: return False
            authData = url[:idx].split('/')
            url = 'http://api.video.mail.ru/videos/' + authData[-4] + '/' + authData[-3] + '/' + authData[-2] + '/' + authData[-1] + '.json'
            sts, data = self.cm.getPage(url, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False})
            if not sts: return False
            video_key = self.cm.getCookieItem(COOKIEFILE,'video_key')
            if '' == video_key: return False
            data = re.search('"videos":{([^}]+?)}', data)
            if not data: return False
            formats = ['sd', 'hd']
            for item in formats:
                url = re.search('"%s":"([^"]+?)"' % item, data.group(1))
                if url:
                    movieUrls.append({ 'name': 'mail.ru: %s' % item, 'url':url.group(1) + '|Cookie="video_key=' + video_key + '"' })
        return movieUrls
        
        
    def parserWRZUTA(self, url):
        movieUrls = []
        
        # start algo from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/wrzuta.py
        _VALID_URL = r'https?://(?P<uploader>[0-9a-zA-Z]+)\.wrzuta\.pl/(?P<typ>film|audio)/(?P<id>[0-9a-zA-Z]+)'
        try:
            while True:
                mobj = re.match(_VALID_URL, url)
                video_id = mobj.group('id')
                typ = mobj.group('typ')
                uploader = mobj.group('uploader')
                
                #sts, data = self.cm.getPage(url)
                #if not sts: break
                quality = {'SD':240, 'MQ':360, 'HQ':480, 'HD':720}
                audio_table = {'flv': 'mp3', 'webm': 'ogg', '???': 'mp3'}
                sts, data = self.cm.getPage('http://www.wrzuta.pl/npp/embed/%s/%s' % (uploader, video_id))
                if not sts: break
                
                data = byteify( json.loads(data) )
                for media in data['url']:
                    fmt = media['type'].split('@')[0]
                    if typ == 'audio':
                        ext = audio_table.get(fmt, fmt)
                    else:
                        ext = fmt
                    if fmt in ['webm']: continue
                    movieUrls.append({'name': 'wrzuta.pl: ' + str(quality.get(media['quality'], 0)) + 'p', 'url':media['url']})                
                break;
        
        except Exception: 
            printExc()
        # end algo
        
        if len(movieUrls): return movieUrls
    
        def getShardUserFromKey(key):
            tab = ["w24", "w101", "w70", "w60", "w2", "w14", "w131", "w121", "w50", "w40", "w44", "w450", "w90", "w80", "w30", "w20", "w25", "w100", "w71", "w61", "w1", "w15", "w130", "w120", "w51", "w41", "w45", "w451", "w91", "w81", "w31", "w21"]
            abc = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            usr_idx = 0
            for i in range(11):
                tmp = key[i]
                usr_idx = (usr_idx * len(abc))
                usr_idx = (usr_idx + abc.find(tmp))
                usr_idx = (usr_idx & 0xFFFF)
            return tab[usr_idx]
            
        def getFileData(login, key, flagaXml, host, site, pltype): 
            url = "http://" + login + "." + host + "/xml/" + flagaXml + "/" + key + "/" + site + "/" + pltype + "/" + str(int(random() * 1000000 + 1))
            sts, data = self.cm.getPage(url)
            return data
        
        urlElems = urlparse(url)
        urlParams = parse_qs(urlElems.query)
        site     = urlParams.get('site', ["wrzuta.pl"])[0]
        host     = urlParams.get('host', ["wrzuta.pl"])[0]
        key      = urlParams.get('key', [None])[0]
        login    = urlParams.get('login', [None])[0]
        language = urlParams.get('login', ["pl"])[0]
        boolTab  = ["yes", "true", "t", "1"]
        embeded  = urlParams.get('embeded', ["false"])[0].lower() in boolTab
        inskin   = urlParams.get('inskin', ["false"])[0].lower() in boolTab
        
        if None == key: return False
        if None == login: login = getShardUserFromKey(key)
        if embeded: pltype = "eb"
        elif inskin: pltype = "is"
        else: pltype = "sa"

        data = getFileData(login, key, "kontent", host, site, pltype)
        formatsTab = [{'bitrate':360, 'file':'fileMQId_h5'},\
                      {'bitrate':480, 'file':'fileHQId_h5'},\
                      {'bitrate':720, 'file':'fileHDId_h5'},\
                      {'bitrate':240, 'file':'fileId_h5'}]
        
        for item in formatsTab:
            sts, url = CParsingHelper.getDataBeetwenMarkers(data, "<%s>" % item['file'], '</%s>' % item['file'], False)
            url = url.replace('<![CDATA[', '').replace(']]>', '')
            if sts: movieUrls.append({'name': 'wrzuta.pl: ' + str(item['bitrate']) + 'p', 'url':url.strip() + '/0'})
        return movieUrls
        
    def parserGOLDVODTV(self, baseUrl):
        COOKIE_FILE = GetCookieDir('goldvodtv.cookie')
        HTTP_HEADER = { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3' }
        SWF_URL = 'http://p.jwpcdn.com/6/9/jwplayer.flash.swf'
        
        url = strwithmeta(baseUrl)
        baseParams = url.meta.get('params', {})
        
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params.update(baseParams)
        sts, data = self.cm.getPage( baseUrl, params)
        
        msg = 'Dostęp wyłącznie dla użytkowników z kontem premium.' 
        if msg in data:
            SetIPTVPlayerLastHostError(msg)
        
        urlTab = []
        qualities = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, "box_quality", "</div>", False)[1]
        tmp = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)</a>''').findall(tmp)
        for item in tmp:
            qualities.append({'title':item[1], 'url':baseUrl+item[0]})
        
        if len(qualities):
            data2 = None
        else:
            data2 = data
            qualities.append({'title':'default', 'url':baseUrl})
        
        for item in qualities:
            if data2 == None:
                sts, data2 = self.cm.getPage( item['url'], params)
                if not sts:
                    data2 = None
                    continue
            data2 = self.cm.ph.getDataBeetwenMarkers(data2, '.setup(', '}', False)[1]
            #printDBG(data2)
            rtmpUrls = re.compile('''(rtmp[^"^']+?)["'&]''').findall(data2)
            for idx in range(len(rtmpUrls)):
                rtmpUrl = urllib.unquote(rtmpUrls[idx])
                if len(rtmpUrl):
                    rtmpUrl = rtmpUrl + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, baseUrl)
                    urlTab.append({'name':'{0}. '.format(idx+1) + item['title'], 'url':rtmpUrl})
            data2 = None
        
        if len(urlTab):
            printDBG(urlTab)
            return urlTab
        
        # get connector link
        data = self.cm.ph.getSearchGroups(data, "'(http://goldvod.tv/tv-connector/[^']+?\.smil[^']*?)'")[0]
        params['load_cookie'] = True
        params['header']['Referer'] = SWF_URL
        
        # get stream link
        sts, data = self.cm.getPage(data, params)
        if sts:
            base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
            src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            if ':' in src:
                src = src.split(':')[1]
                
            if base.startswith('rtmp'):
                return base + '/' + src + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, baseUrl)
        return False
        
    def parserVIDZER(self, baseUrl):
        printDBG("parserVIDZER baseUrl[%s]" % baseUrl)
        
        baseUrl = baseUrl.split('?')[0]
        
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        defaultParams = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('vidzernet.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def getPage(url, params={}, post_data=None):
            sts, data = False, None
            sts, data = self.cm.getPage(url, defaultParams, post_data)
            if sts:
                imgUrl = self.cm.ph.getSearchGroups(data, '"([^"]+?captcha-master[^"]+?)"')[0]
                if imgUrl.startswith('/'): imgUrl = 'http://www.vidzer.net' + imgUrl
                if imgUrl.startswith('http://') or imgUrl.startswith('https://'):
                    sessionEx = MainSessionWrapper() 
                    header = dict(HTTP_HEADER)
                    header['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                    params = dict(defaultParams)
                    params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':header} )
                    filePath = GetTmpDir('.iptvplayer_captcha.jpg')
                    #Accept=image/png,image/*;q=0.8,*/*;q=0.5
                    ret = self.cm.saveWebFile(filePath, imgUrl.replace('&amp;', '&'), params)
                    if not ret.get('sts'):
                        SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                        return False
                    from Plugins.Extensions.IPTVPlayer.icomponents.iptvmultipleinputbox import IPTVMultipleInputBox
                    from copy import deepcopy
                    params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
                    params['accep_label'] = _('Send')
                    params['title'] = _('Answer')
                    params['list'] = []
                    item = deepcopy(IPTVMultipleInputBox.DEF_INPUT_PARAMS)
                    item['label_size'] = (160,75)
                    item['input_size'] = (300,25)
                    item['icon_path'] = filePath
                    item['title'] = clean_html(CParsingHelper.getDataBeetwenMarkers(data, '<h1', '</h1>')[1]).strip()
                    item['input']['text'] = ''
                    params['list'].append(item)
        
                    ret = 0
                    retArg = sessionEx.waitForFinishOpen(IPTVMultipleInputBox, params)
                    printDBG(retArg)
                    if retArg and len(retArg) and retArg[0]:
                        printDBG(retArg[0])
                        sts, data = self.cm.getPage(url, defaultParams, {'captcha':retArg[0][0]})
                        return sts, data
                    else:
                        SetIPTVPlayerLastHostError(_('Wrong answer.'))
                    return False, None
            return sts, data
            
        ########################################################
                    

        sts, data = getPage(baseUrl)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, '<iframe src="(http[^"]+?)"')[0]
        if url != '':        
            sts, data = getPage(url)
            if not sts: return False
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="playerVidzer">', '</a>', False)[1]
        match = re.search('href="(http[^"]+?)"', data)
        if match:
            url = urllib.unquote( match.group(1) )
            return url
        
        r = re.search('value="(.+?)" name="fuck_you"', data)
        r2 = re.search('name="confirm" type="submit" value="(.+?)"', data)
        r3 = re.search('<a href="/file/([^"]+?)" target', data)
        if r:
            printDBG("r_1[%s]" % r.group(1))
            printDBG("r_2[%s]" % r2.group(1))
            data = 'http://www.vidzer.net/e/'+r3.group(1)+'?w=631&h=425'
            postdata = {'confirm' : r2.group(1), 'fuck_you' : r.group(1)}
            sts, data = getPage(data, {}, postdata)
            match = re.search("url: '([^']+?)'", data)
            if match:
                url = match.group(1) #+ '|Referer=http://www.vidzer.net/media/flowplayer/flowplayer.commercial-3.2.18.swf'
                return url
            else:
                return False
        else:
            return False
            
    def parserNOWVIDEOCH(self, url):
        printDBG("parserNOWVIDEOCH url[%s]" % url)
        return self._parserUNIVERSAL_B(url)
    
    def parserSTREAMINTO(self, baseUrl):
        printDBG("parserSTREAMINTO baseUrl[%s]" % baseUrl)
        # example video: http://streamin.to/okppigvwdk8w
        #                http://streamin.to/embed-rme4hyg6oiou-640x500.html
        #tmp =  self.__parseJWPLAYER_A(baseUrl, 'streamin.to')
        
        def getPageUrl(data):
            #printDBG("=======================================")
            #printDBG(data)
            #printDBG("=======================================")
            
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>')
            for tmp in tmpTab:
                tmp2 = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)
                data += tmp2
            
            vidTab = []
            sub_tracks = []
            subData = self.cm.ph.getDataBeetwenMarkers(data, 'tracks:', ']', False)[1].split('}')
            for item in subData:
                if '"captions"' in item:
                    label   = self.cm.ph.getSearchGroups(item, 'label:\s*?"([^"]+?)"')[0]
                    srclang = self.cm.ph.getSearchGroups(item, 'srclang:\s*?"([^"]+?)"')[0]
                    src     = self.cm.ph.getSearchGroups(item, 'file:\s*?"([^"]+?)"')[0]
                    if not src.startswith('http'): continue
                    sub_tracks.append({'title':label, 'url':src, 'lang':label, 'format':'srt'})
            data = re.sub("tracks:[^\]]+?\]", "", data)
            
            streamer = self.cm.ph.getSearchGroups(data, 'streamer: "(rtmp[^"]+?)"')[0]
            printDBG(streamer)
            data     = re.compile('file:[ ]*?"([^"]+?)"').findall(data)
            
            for item in data:
                if item.startswith('http://'):
                    vidTab.insert(0, {'name': 'http://streamin.to/ ', 'url':strwithmeta(item, {'external_sub_tracks':sub_tracks})})
                elif item.startswith('rtmp://') or '' != streamer:
                    try:
                        if item.startswith('rtmp://'):
                            item     = item.split('flv:')
                            r        = item[0]
                            playpath = item[1]
                        else:
                            r        = streamer
                            playpath = item 
                        swfUrl  = "http://streamin.to/player6/jwplayer.flash.swf"
                        rtmpUrl = r + ' playpath=%s' % playpath + ' swfUrl=%s' % swfUrl + ' pageUrl=%s' % baseUrl
                        vidTab.append({'name': 'rtmp://streamin.to/ ', 'url':urlparser.decorateUrl(rtmpUrl, {'external_sub_tracks':sub_tracks, 'iptv_livestream':False})})
                    except Exception:
                        printExc()
            return vidTab
        vidTab = []
        if 'embed' not in baseUrl:
            baseUrl = 'http://streamin.to/embed-%s-640x500.html' % baseUrl.split('/')[-1]
        
        HTTP_HEADER = {"User-Agent":"Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10"}
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        #printDBG(data)
        if sts:
            errMarkers = ['File was deleted', 'File Removed', 'File Deleted.']
            for errMarker in errMarkers:
                if errMarker in data:
                    SetIPTVPlayerLastHostError(errMarker)
            vidTab = getPageUrl(data)
            if 0 == len(vidTab):
                cookies_data = ''
                cookies = re.findall("cookie\('([^']*)', '([^']*)'", data)
                for item in cookies:
                    cookies_data += '%s=%s;' % (item[0], item[1])
                
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                HTTP_HEADER['Referer'] = baseUrl
                # get cookie for streamin.to
                if len(cookies_data):
                    HTTP_HEADER['Cookie'] = cookies_data[:-1]
                try:
                    sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9]+?)</span>')[0])
                    time.sleep(sleep_time)
                except Exception:
                    printExc()
                    
                sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
                if sts:
                    vidTab = getPageUrl(data)
        return vidTab
        
    def parseVSHAREIO(self, baseUrl):
        printDBG("parseVSHAREIO baseUrl[%s]" % baseUrl)
        # example video: 
        # http://vshare.io/v/72f9061/width-470/height-305/
        # http://vshare.io/v/72f9061/width-470/height-305/
        # http://vshare.io/d/72f9061/1
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/[dv]/([A-Za-z0-9]{7})/')[0]
        url = 'http://vshare.io/v/{0}/width-470/height-305/'.format(video_id)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0', 'Referer':baseUrl}
        
        vidTab = []
        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
        if not sts: return
        
        stream   = self.cm.ph.getSearchGroups(data, '''['"](http://[^"^']+?/stream\,[^"^']+?)['"]''')[0]
        if '' == stream: stream   = byteify(json.loads('"%s"' % self.cm.ph.getSearchGroups(data, '''['"](http://[^"^']+?\.flv)['"]''')[0]))
        if '' != stream:
            vidTab.append({'name': 'http://vshare.io/stream ', 'url':stream})
            
        if 0 == len(vidTab):
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'clip:', '}', False)[1]
            url = byteify(json.loads('"%s"' % self.cm.ph.getSearchGroups(tmp, '''['"](http[^"^']+?)['"]''')[0]))
            if url != '': vidTab.append({'name': 'http://vshare.io/ ', 'url':url})
        
        if 0 == len(vidTab):
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
            for item in tmp:
                if 'video/mp4' in item or '.mp4' in item:
                    label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                    res = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                    if label == '': label = res
                    url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                    if url.startswith('//'): url = 'http:' + url
                    if not self.cm.isValidUrl(url): continue
                    vidTab.append({'name':'vshare.io ' + label, 'url':strwithmeta(url, {'Referer':baseUrl})})
            
        return vidTab
            
    def parserVIDSSO(self, url):
        printDBG("parserVIDSSO url[%s]" % url)
        # example video: http://www.vidsso.com/video/hhbwr85FMGX
        try:
            sts, data = self.cm.getPage(url)
            try:
                confirm  = re.search('<input name="([^"]+?)" [^>]+?value="([^"]+?)"', data)
                vs       = re.search('<input type="hidden" value="([^"]+?)" name="([^"]+?)">', data)
                post = {confirm.group(1):confirm.group(2), vs.group(2):vs.group(1)}
                sts, data = self.cm.getPage(url, {'Referer':url}, post)
            except Exception:
                printExc()
            
            url = re.search("'file': '(http[^']+?)'", data).group(1)
            return url
        except Exception:
            printExc()
        return False
            
    def parseWATTV(self, url="http://www.wat.tv/images/v70/PlayerLite.swf?videoId=6owmd"):
        printDBG("parseWATTV url[%s]\n" % url)
        # example video: http://www.wat.tv/video/orages-en-dordogne-festival-6xxsn_2exyh_.html
        def getTS():
            #ts = math.floor( float(ts) / 1000 )
            url = "http://www.wat.tv/servertime?%d" % int(random() * 0x3D0900)
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
            ts = int(data.split('|')[0])
            return int2base(int(ts), 36)

        def computeToken(urlSuffixe, ts):
            tHex = int2base(int(ts, 36), 16)
            while len(tHex) < 8:
                tHex = "0" + tHex
            constToken = "9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba009l2564"
            hashAlg = MD5() 
            return hexlify( hashAlg(constToken + urlSuffixe + tHex) ) + "/" + tHex

        movieUrls = []
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        HTTP_HEADER['Referer'] = url
        match = re.search("videoId=([^']+?)'", url + "'")

        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
        if sts:
            real_id = re.search(r'xtpage = ".*-(.*?)";', data)
            if real_id:
                real_id = real_id.group(1)
                movieUrls.append({'name': 'wat.tv: Mobile', 'url':'http://wat.tv/get/android5/%s.mp4' % real_id})    
            if not match:
                match = re.search('videoId=([^"]+?)"', data)
        
        for item in ["webhd", "web"]:
            try:
                vidId = int(match.group(1), 36)
                url_0 = "/%s/%d" % (item, vidId)
                url_1 = computeToken(url_0, getTS())
                url_2 =  url_0 + "?token=" + url_1 + "&"
                url   = "http://www.wat.tv/get" + url_2 + "domain=www.wat.tv&refererURL=www.wat.tv&revision=04.00.388%0A&synd=0&helios=1&context=playerWat&pub=5&country=FR&sitepage=WAT%2Ftv%2Fu%2Fvideo&lieu=wat&playerContext=CONTEXT_WAT&getURL=1&version=WIN%2012,0,0,44"
                printDBG("====================================================: [%s]\n" % url)
                
                sts, url = self.cm.getPage(url, {'header' : HTTP_HEADER})
                if sts:
                    if url.split('?')[0].endswith('.f4m'):
                        url = urlparser.decorateUrl(url, HTTP_HEADER)
                        retTab = getF4MLinksWithMeta(url)
                        movieUrls.extend(retTab)
                    elif 'ism' not in url:
                        movieUrls.append({'name': 'wat.tv: ' + item, 'url':url})
            except Exception:
                printExc()
        movieUrls.reverse()
        return movieUrls
        
    def parserFILEONETV(self, baseUrl):
        printDBG("parserFILEONETV baseUrl[%s]\n" % baseUrl)
        url = baseUrl.replace('show/player', 'v')
        sts, data = self.cm.getPage(url)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        url  = self.cm.ph.getSearchGroups(data, '''file[^"^']+?["'](http[^"^']+?)['"]''')[0]
        if '://' in url:
            return url
        return False
        
    def parserHDGOCC(self, baseUrl):
        printDBG("parserHDGOCC url[%s]\n" % baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Referer' : Referer}
        
        vidTab = []
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        url = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return
        
        printDBG(data)
        
        unique = []
        urls = []
        
        tmpTab = re.compile('''var\s*url\s*=\s*['"]([,]*?http[^'^"]+?)['"]''').findall(data)
        for tmp in tmpTab:
            urls.extend(tmp.split(' or '))
        tmp = self.cm.ph.getSearchGroups(data, '''file\s*:\s*['"]([,]*?http[^'^"]+?)['"]''', 1, True)[0]
        urls.extend(tmp.split(' or '))
        
        urlsTab = []
        for item in urls:
            urlsTab.extend(item.split(','))
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'media:', ']', False)[1].split('}')
        for item in tmp:
            ok = False
            if 'video/mp4' in item:
                ok = True
            url = self.cm.ph.getSearchGroups(item,'''["'](http[^"^']+?)["']''', 1, True)[0]
            if ok or url.split('?')[0].endswith('.mp4'): 
                urlsTab.append(url)
        
        for url in urlsTab:
            url = url.strip()
            if not self.cm.isValidUrl(url): continue
            if url in unique: continue
            label = self.cm.ph.getSearchGroups(url, '''/([0-9]+?)\-''', 1, True)[0]
            if label == '':
                if '/3/' in url: label = '720p'
                elif '/2/' in url: label = '480p'
                else: label = '360p'
            if url.split('?')[0].endswith('.m3u8'):
                url = urlparser.decorateUrl(url, HTTP_HEADER)
                tmpTab = getDirectM3U8Playlist(url, checkContent=True)
                tmpTab.extend(vidTab)
                vidTab = tmpTab
            elif url.split('?')[0].endswith('.f4m'):
                url = urlparser.decorateUrl(url, HTTP_HEADER)
                tmpTab = getF4MLinksWithMeta(url)
                tmpTab.extend(vidTab)
                vidTab = tmpTab
            else:
                vidTab.append({'name':label, 'url':url})
        return vidTab
        
    def parserUSERSCLOUDCOM(self, url):
        printDBG("parserUSERSCLOUDCOM url[%s]\n" % url)
        sts, data = self.cm.getPage(url)
        
        errorTab = ['File Not Found', 'File was deleted']
        for errorItem in errorTab:
            if errorItem in data:
                SetIPTVPlayerLastHostError(_(errorItem))
                break
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)[1]
        tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')[1]
        # unpack and decode params from JS player script code
        tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
        if tmp != None: data = tmp + data
        # printDBG(data)
        # get direct link to file from params
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?["']video''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        
        return False
        
    def parseTUNEPK(self, url):
        printDBG("parseTUNEPK url[%s]\n" % url)
        # example video: http://tune.pk/video/4203444/top-10-infamous-mass-shootings-in-the-u
        for item in ['vid=', '/video/', '/play/']:
            vid = self.cm.ph.getSearchGroups(url+'&', item+'([0-9]+)[^0-9]')[0]
            if '' != vid: break
        if '' == vid: return []
        url = 'http://embed.tune.pk/play/%s?autoplay=no&ssl=no' % vid
        return self.__parseJWPLAYER_A(url, 'tune.pk')
    
    def parserVIDEOTT(self, url):
        printDBG("parserVIDEOTT url[%r]" % url)
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/videott.py
        # example video: http://www.video.tt/video/HRKwm3EhI
        linkList = []
        try:
            mobj = re.match(r'http://(?:www\.)?video\.tt/(?:video/|watch_video\.php\?v=|embed/)(?P<id>[\da-zA-Z]{9})', url)
            video_id = mobj.group('id')
        except Exception:
            printExc()
            return linkList
        url = 'http://www.video.tt/player_control/settings.php?v=%s' % video_id
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json.loads(data)['settings']
                linkList = [
                    {
                        'url': base64.b64decode(res['u'].encode('utf-8')),
                        'name': res['l'].encode('utf-8'),
                    } for res in data['res'] if res['u']
                ]
            except Exception:
                printExc()
        return linkList
        
    def parserEXASHARECOM(self, url):
        printDBG("parserEXASHARECOM url[%r]" % url)
        # example video: http://www.exashare.com/s4o73bc1kd8a
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':url }
        if 'exashare.com' in url:
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
            if not sts: return
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0].replace('\n', '').replace('\r', '')
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>> url[%s]\n" % url)
        def _findLinks(data):
            return self._findLinks(data, 'exashare.com', m1='setup(', m2=')')
        return self.__parseJWPLAYER_A(url, 'exashare.com', _findLinks, folowIframe=True)
        
    def parserALLVIDCH(self, baseUrl):
        printDBG("parserALLVIDCH baseUrl[%r]" % baseUrl)
        # example video: http://allvid.ch/embed-fhpd7sk5ac2o-830x500.html
        
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('allvidch.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def _findLinks(data):
            return self._findLinks(data, 'allvid.ch', m1='setup(', m2='image:')
        
        def _preProcessing(data):
            url2 = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http[^"^']+?)["']''', 1, True)[0]
            if url2.startswith('http'):
                sts, data2 = self.cm.getPage(url2, params)
                if sts:
                    return data2
            return data
        
        return self._parserUNIVERSAL_A(baseUrl, 'http://allvid.ch/embed-{0}-830x500.html', _findLinks, _preProcessing,  HTTP_HEADER, params)
        #return self.__parseJWPLAYER_A(baseUrl, 'allvid.ch', _findLinks)
        
    def parserALBFILMCOM(self, baseUrl):
        printDBG("parserALBFILMCOM baseUrl[%r]" % baseUrl)
        # www.albfilm.com/video/?m=endless_love_2014
        def _findLinks(data):
            videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0]
            if videoUrl == '': return []
            return [{'name':'albfilm.com', 'url':videoUrl}]
        url = baseUrl
        return self._parserUNIVERSAL_A(baseUrl, url, _findLinks)
        
    def parserVIDAG(self, baseUrl):
        printDBG("parserVIDAG baseUrl[%r]" % baseUrl)
        # example video: http://vid.ag/embed-24w6kstkr3zt-540x360.html
        def _findLinks(data):
            tab = []
            tmp = self._findLinks(data, 'vid.ag', m1='setup(', m2='image:')
            for item in tmp:
                if not item['url'].split('?')[0].endswith('.m3u8'):
                    tab.append(item)
            return tab
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':'http://www.streaming-series.xyz/', 'Cookie':'__test' }
        return self._parserUNIVERSAL_A(baseUrl, 'http://vid.ag/embed-{0}-540x360.html', _findLinks, None, HTTP_HEADER)
        
    def parserVODLOCKER(self, url):
        printDBG("parserVODLOCKER url[%r]" % url)
        # example video: http://vodlocker.com/txemekqfbopy
        return self.__parseJWPLAYER_A(url, 'vodlocker.com')
        
    def parserSTREAMABLECOM(self, baseUrl):
        printDBG("parserVSHAREEU baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if videoUrl.startswith('//'):
            videoUrl = 'http:' + videoUrl
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserPLAYPANDANET(self, baseUrl):
        printDBG("parserPLAYPANDANET baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl.replace('&amp;', '&'))
        if not sts: return False
        videoUrl = self.cm.ph.getSearchGroups(data, '''_url\s*=\s*['"]([^'^"]+?)['"]''')[0]
        if videoUrl.startswith('//'):
            videoUrl = 'http:' + videoUrl
        videoUrl = urllib.unquote(videoUrl)
        if self.cm.isValidUrl(videoUrl):
            return videoUrl        
        return False

    def parserEASYVIDEOME(self, baseUrl):
        printDBG("parserEASYVIDEOME baseUrl[%r]" % baseUrl)
        return self.parserPLAYPANDANET(baseUrl)
            
    def parserVSHAREEU(self, baseUrl):
        printDBG("parserVSHAREEU baseUrl[%r]" % baseUrl)
        # example video: http://vshare.eu/mvqdaea0m4z0.htm
        
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}
        
        if 'embed' not in baseUrl:
            COOKIE_FILE = GetCookieDir('vshareeu.cookie')
            rm(COOKIE_FILE)
            params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: return False
            
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            params['header']['Referer'] = baseUrl
            
            time.sleep(5)
            
            sts, data = self.cm.getPage(baseUrl, params, post_data)
            if not sts: return False
        else:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
        
        linksTab = self._findLinks(data, 'vshare.eu')
        for idx in range(len(linksTab)):
            linksTab[idx]['url'] = strwithmeta(linksTab[idx]['url'] + '?start=0', {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        return linksTab
        
        #X-Requested-With:ShockwaveFlash/23.0.0.205
        if 'embed' not in baseUrl:
            tmp = baseUrl.split('.')
            baseUrl = '.'.join(tmp[:-1])
            baseUrl = baseUrl.replace('.eu/', '.eu/embed-') + '-729x400.html'
        
    def parserVIDSPOT(self, url):
        printDBG("parserVIDSPOT url[%r]" % url)
        # example video: http://vidspot.net/2oeqp21cdsee
        return self.__parseJWPLAYER_A(url, 'vidspot.net')
            
    def parserVIDBULL(self, baseUrl):
        printDBG("parserVIDBULL baseUrl[%s]" % baseUrl)
        # example video: http://vidbull.com/zsi9kwq0eqm4.html
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = baseUrl
        
        # we will try three times if they tell us that we wait to short
        tries = 0
        while tries < 3:
            # get embedded video page and save returned cookie
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<input type="hidden" name="op" value="download2">', '</Form>', True)
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            
            try:
                sleep_time = int(self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]) 
                time.sleep(sleep_time)
            except Exception:
                printExc()
            if {} == post_data:
                post_data = None
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
            if not sts: return False
            if 'Skipped countdown' in data:
                tries += tries
                continue # we will try three times if they tell us that we wait to short
            # get JS player script code from confirmation page
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                printDBG(data)
                # get direct link to file from params
                src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                if src.startswith('http'):
                    return src
            # get direct link to file from params
            file = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
            if '' != file:
                if file.startswith('http'): return src
                else:
                    key = 'YTk0OTM3NmUzN2IzNjlmMTdiYzdkM2M3YTA0YzU3MjE='
                    bkey, knownCipherText = a2b_hex(base64.b64decode(key)), a2b_hex(file)
                    kSize = len(bkey)
                    alg = AES(bkey, keySize=kSize, padding=noPadding())
                    file = alg.decrypt(knownCipherText).split('\x00')[0]
                    if file.startswith('http'):
                        return file
            break
        return False
        
    def parserDIVEXPRESS(self, baseUrl):
        printDBG("parserDIVEXPRESS baseUrl[%s]" % baseUrl)
        # example video: http://divxpress.com/h87ygyutusp6/The.Last.Ship.S01E04.HDTV.x264-LOL_Napisy_PL.AVI.html
        return self.parserVIDBULL(baseUrl)
        
    def parserPROMPTFILE(self, baseUrl):
        printDBG("parserPROMPTFILE baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            if 'Continue to File' in data:
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                params = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('promptfile.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':False}
                sts, data = self.cm.getPage(baseUrl, params, post_data)
                if not sts:
                    return False
            data = self.cm.ph.getSearchGroups(data, """url: ["'](http[^"']+?)["'],""")[0]
            if '' != data:
                return data
        return False
        
    def parserPLAYEREPLAY(self, baseUrl):
        printDBG("parserPLAYEREPLAY baseUrl[%s]" % baseUrl)
        videoIDmarker = "((?:[0-9]){5}\.(?:[A-Za-z0-9]){28})"
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}

        COOKIE_FILE = GetCookieDir('playreplaynet.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage(baseUrl, params)
        if sts:
            data = self.cm.ph.getSearchGroups(data, videoIDmarker)[0]
        if data == '':
            data = self.cm.ph.getSearchGroups(baseUrl, videoIDmarker)[0]
        if '' != data: 
            HTTP_HEADER['Referer'] = baseUrl
            post_data = {'r':'[["file/flv_link2",{"uid":"%s","link":true}],["file/flv_image",{"uid":"%s","link":true}]]' % (data, data)}
            #
            params['header'] = HTTP_HEADER
            params['load_cookie'] = True
            sts, data = self.cm.getPage('http://playreplay.net/data', params, post_data)
            printDBG(data)
            if sts:
                data = byteify(json.loads(data))['data'][0]
                if 'flv' in data[0]:
                    return strwithmeta(data[0], {'Range':'0', 'iptv_buffering':'required'})
        return False
        
    def parserVIDEOWOODTV(self, baseUrl):
        printDBG("parserVIDEOWOODTV baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{4})/')[0]
            url = 'http://videowood.tv/embed/{0}'.format(video_id)
        else:
            url = baseUrl 
        
        params = {'header' : HTTP_HEADER}
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        while True:
            vidUrl = self.cm.ph.getSearchGroups(data, """["']*file["']*:[ ]*["'](http[^"']+?(?:\.mp4|\.flv)[^"']*?)["']""")[0]
            if '' != vidUrl:
                return vidUrl.replace('\\/', '/')
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(data, TEAMCASTPL_decryptPlayerParams)
                #data = self.cm.ph.getDataBeetwenMarkers(data, 'config=', ';',
                printDBG(data)
                continue
            break
        return False
        
    def parserMOVRELLCOM(self, baseUrl):
        printDBG("parserMOVRELLCOM baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            if 'Watch as Free User' in data:
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False, False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                params = {'header' : HTTP_HEADER}
                sts, data = self.cm.getPage(baseUrl, params, post_data)
                if not sts:
                    return False
            # get JS player script code from confirmation page
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                printDBG(data)
                # get direct link to file from params
                src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                if src.startswith('http'):
                    return src
        return False
        
    def parserVIDFILENET(self, baseUrl):
        printDBG("parserVIDFILENET baseUrl[%s]" % baseUrl)
        vidTab = []
        #COOKIE_FILE = GetCookieDir('vidfilenet.cookie')
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header':HTTP_HEADER} #, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        rm(HTTP_HEADER)
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: sts, data = self.cm.getPageWithWget(baseUrl, params)
        if not sts: return False
        
        #cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
        for item in data:
            if 'video/mp4' in item or '.mp4' in item:
                res = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                if url.startswith('//'): url = 'http:' + url
                if not self.cm.isValidUrl(url): continue
                vidTab.append({'name':'vidfile.net ' + res, 'url':strwithmeta(url, {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})}) #'Cookie':cookieHeader,
        vidTab.reverse()
        return vidTab
        
    def parserMP4UPLOAD(self, baseUrl):
        printDBG("parserMP4UPLOAD baseUrl[%s]" % baseUrl)
        videoUrls = []
        sts, data = self.cm.getPage(baseUrl)
        #printDBG(data)
        if sts:
            data = CParsingHelper.getDataBeetwenMarkers(data, "'modes':", ']', False)[1]
            data = re.compile("""['"]file['"]: ['"]([^'^"]+?)['"]""").findall(data)
            if 1 < len(data) and data[1].startswith('http'): videoUrls.append( {'name': 'mp4upload.com: html5',    'url':data[1] } )
            if 0 < len(data) and data[0].startswith('http'): videoUrls.append( {'name': 'mp4upload.com: download', 'url':data[0] } )
        return videoUrls
        
    def parserYUKONS(self, baseUrl):
        printDBG("parserYUKONS url[%s]" % baseUrl)
        #http://yukons.net/watch/willstream002?Referer=wp.pl
        def _resolveChannelID(channel):
            def _decToHex(a):
                b = hex(a)[2:]
                if 1 == len(b):
                    return '0'+b
                else:
                    return b
            
            def _resolve(a):
                b = ''
                for i in range(len(a)):
                    b += _decToHex(ord(a[i]))
                return b
                
            return _resolve( _resolve(channel) )
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        shortChannelId = baseUrl.split('?')[0].split('/')[-1]
        Referer = baseUrl.meta.get('Referer', '')
        
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Referer' : Referer}
        COOKIE_FILE = GetCookieDir('yukonsnet.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}

        longChannelId = _resolveChannelID(shortChannelId)
        url1 = 'http://yukons.net/yaem/' + longChannelId
        sts, data = self.cm.getPage(url1, params)
        if sts:
            kunja = re.search("'([^']+?)';", data).group(1)
            url2 = 'http://yukons.net/embed/' + longChannelId + '/' + kunja + '/680/400'
            params.update({'save_cookie' : False, 'load_cookie' : True}) 
            sts, data = self.cm.getPage(url2, params)
            if sts:
                data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>', False)[1]
                data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0)
                printDBG(data)
                id = CParsingHelper.getDataBeetwenMarkers(data, "id=", '&', False)[1]
                pid = CParsingHelper.getDataBeetwenMarkers(data, "pid=", '&', False)[1]
                data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>', False)[1]
                sts, data = self.cm.getPage("http://yukons.net/srvload/"+id, params)
                printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % data)
                if sts:
                    ip = data[4:].strip()
                    url = 'rtmp://%s:443/kuyo playpath=%s?id=%s&pid=%s  swfVfy=http://yukons.net/yplay2.swf pageUrl=%s conn=S:OK live=1' % (ip, shortChannelId, id, pid, url2)
                    return url
        return False
        
    def parserUSTREAMTV(self, linkUrl):
        printDBG("parserUSTREAMTV linkUrl[%s]" % linkUrl)
        #http://www.ustream.tv/channel/nasa-educational
        linksTab = []
        live = True
        # get PC streams
        while True:
            channelID = self.cm.ph.getSearchGroups(linkUrl+'|', "cid=([0-9]+?)[^0-9]")[0]
            if '' == channelID:            
                sts, data = self.cm.getPage(linkUrl)
                if not sts: break
                channelID = self.cm.ph.getSearchGroups(data, 'data-content-id="([0-9]+?)"')[0]
                if '' == channelID: channelID = self.cm.ph.getSearchGroups(data, 'ustream.vars.contentId=([0-9]+?)[^0-9]')[0]
                if '' == channelID: channelID = self.cm.ph.getSearchGroups(data, 'ustream.vars.cId=([0-9]+?)[^0-9]')[0]

            if '' == channelID: break
            #in linkUrl and 'ustream.vars.isLive=true' not in data and '/live/' not in linkUrl
            if '/recorded/' in linkUrl:
                videoUrl = 'https://www.ustream.tv/recorded/' + channelID
                live = False
            else:
                videoUrl = 'https://www.ustream.tv/embed/' + channelID
                live = True
            
            # get mobile streams
            if live:
                playlist_url = "http://iphone-streaming.ustream.tv/uhls/%s/streams/live/iphone/playlist.m3u8" % channelID
                try:
                    retTab = getDirectM3U8Playlist(playlist_url)
                    if len(retTab):
                        for item in retTab:
                            name = ('ustream.tv %s' % item.get('heigth', 0)) + '_mobile'
                            url = urlparser.decorateUrl(item['url'], {'iptv_livestream': True})
                            linksTab.append({'name':name, 'url':url})
                        break
                except Exception:
                    printExc()
                return linksTab
            else:
                sts, data = self.cm.getPage(videoUrl)
                if not sts: return
                data = self.cm.ph.getDataBeetwenMarkers(data, '"media_urls":{', '}', False)[1]
                data = byteify(json.loads('{%s}' % data))
                printDBG("++++++++++++++++++++++++++++++++++++++++++")
                printDBG(data)
                if self.cm.isValidUrl(data['flv']) and '/{0}?'.format(channelID) in data['flv']:
                    return urllib.unquote(data['flv'].replace('&amp;', '&'))
                return False
                
            
            baseWgetCmd = DMHelper.getBaseWgetCmd({})
            cmd = DMHelper.GET_F4M_PATH() + (" '%s'" % baseWgetCmd) + (' "%s"' % videoUrl) + ' 2>&1 > /dev/null'
            
            printDBG("parserUSTREAMTV cmd[%s" % cmd)
            data = iptv_execute()( cmd )
            printDBG(data)
            if not data['sts'] or 0 != data['code']:
                break
            try:
                data = json.loads(data['data'])
                for item in data['stream_info_list']:
                    if not live and item['chunk_name'].startswith('http'):
                        url = urlparser.decorateUrl(item['chunk_name'].encode('utf-8'))
                        linksTab.append({'name':'ustream.tv recorded', 'url': url})
                    else:
                        name     = 'ustream.tv ' + item['stream_name'].encode('utf-8')
                        chankUrl = (item['prov_url'] + item['chunk_name']).encode('utf-8')
                        url      = urlparser.decorateUrl(videoUrl, {'iptv_livestream': True, 'iptv_proto':'f4m', 'iptv_chank_url':chankUrl})
                        linksTab.append({'name':name, 'url':url})
            except Exception:
                printExc()
            break
        return linksTab
        
    def parserALIEZME(self, baseUrl):
        printDBG("parserALIEZME baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)

        if baseUrl.split('?')[0].endswith('.js'):
            sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
            if not sts: return []
            tr = 0
            while tr < 3:
                tr += 1
                videoUrl = self.cm.ph.getSearchGroups(data, '"(http://[^/]+?/player?[^"]+?)"')[0]
                if "" != videoUrl: break
                time.sleep(1)
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return []
        urlsTab = []
        videoUrl = self.cm.ph.getSearchGroups(data, """['"]*(http[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0]
        if self.cm.isValidUrl(videoUrl):
            videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
            urlsTab.extend(getDirectM3U8Playlist(videoUrl))
        #videoUrl = urllib.unquote(self.cm.ph.getSearchGroups(data, """['"]*(rtmp[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0])
        #if videoUrl.startswith('rtmp://'):
            
        return urlsTab
        
    def parserPRIVATESTREAM(self, linkUrl):
        printDBG("parserPRIVATESTREAM linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']

        if videoUrl.split('?')[0].endswith('.js'):
            sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
            if not sts: return False
            printDBG(data)
            tr = 0
            while tr < 3:
                tr += 1
                videoUrl = self.cm.ph.getSearchGroups(data, '"(http://privatestream.tv/player?[^"]+?)"')[0]
                if "" != videoUrl: break
                time.sleep(1)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        printDBG(data)
        if sts:
            try:
                a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
                b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
                c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
                d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
                f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
                v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
                
                url = ('rtmp://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) ) + v_part
                url += ' swfUrl=http://privatestream.tv/js/jwplayer.flash.swf pageUrl=%s' % (videoUrl)
                return url
            except Exception:
                printExc()
        return False
        
    def parserTVOPECOM(self, baseUrl):
        printDBG("parserTVOPECOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'clip:', '}', False)[1]
        live = self.cm.ph.getSearchGroups(tmp, '''live:\s*([^,]+?),''')[0]
        
        playpath = self.cm.ph.getSearchGroups(tmp, '''url:\s?['"]([^'^"]+?)['"]''')[0]
        if playpath == '': playpath = self.cm.ph.getSearchGroups(data, '''\(\s*['"]file['"]\s*\,\s*['"]([^'^"]+?)['"]''')[0]
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''src:\s?['"](http[^'^"]+?\.swf[^'^"]*?)['"]''')[0]
        if swfUrl == '': swfUrl = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]+?\.swf[^'^"]*?)['"]''')[0]
        
        rtmpUrl = self.cm.ph.getSearchGroups(data, '''['"](rtmp[^'^"]+?)['"]''')[0]
        
        return rtmpUrl + ' playpath=' + playpath + ' swfUrl=' + swfUrl +  ' pageUrl=' + baseUrl + ' live=1'
        
    def parserVIVOSX(self, baseUrl):
        printDBG("parserVIVOSX baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: sts, data = self.cm.getPageWithWget(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'InitializeStream', ';', False)[1]
        data = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]+?)['"]''')[0]
        data = byteify(json.loads(base64.b64decode(data)))
        urlTab = []
        for idx in range(len(data)):
            if not self.cm.isValidUrl(data[idx]): continue
            urlTab.append({'name':_('Source %s') % (idx+1), 'url':strwithmeta(data[idx], {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})})
        return urlTab
        
    def parserZSTREAMTO(self, baseUrl):
        printDBG("parserZSTREAMTO baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        return self._findLinks(data, 'zstream')
        
    def parserTHEVIDEOBEETO(self, baseUrl):
        printDBG("parserTHEVIDEOBEETO baseUrl[%r]" % baseUrl)
        
        if 'embed-' not in baseUrl: url = 'https://thevideobee.to/embed-%s.html' % baseUrl.split('/')[-1].replace('.html', '')
        else: url = baseUrl
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: sts, data = self.cm.getPageWithWget(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video[^>]*?src="([^"]+?)"')[0]
        if not self.cm.isValidUrl(videoUrl): videoUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"[^>]*?type="video')[0]
        if self.cm.isValidUrl(videoUrl): 
            return videoUrl
        return False
        
    def parserKINGFILESNET(self, baseUrl):
        printDBG("parserKINGFILESNET baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        COOKIE_FILE = GetCookieDir('kingfilesnet.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        post_data.pop('method_premium', None)
        params['header']['Referer'] = baseUrl
        
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return False
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')
        if sts:
            tmp = unpackJSPlayerParams(tmp, KINGFILESNET_decryptPlayerParams)
            printDBG(tmp)
            videoUrl = self.cm.ph.getSearchGroups(tmp, 'type="video/divx"[^>]*?src="([^"]+?)"')[0]
            if self.cm.isValidUrl(videoUrl): return videoUrl
            try:
                videoLinks = self._findLinks(tmp, 'kingfiles.net', m1='config:', m2=';')
                printDBG(videoLinks)
                if len(videoLinks): return videoLinks
            except Exception:
                printExc()
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        post_data.pop('method_premium', None)
        #params['return_data'] = False
        
        try:
            sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9]+?)</span> seconds<')[0]
            if '' != sleep_time: time.sleep(int(sleep_time))
        except Exception:
            printExc()
            
        
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '</tr>', '</table>', caseSensitive=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<span style', '</span>')
        
        def _cmpLinksBest(item1, item2):
            val1 = int(self.cm.ph.getSearchGroups(item1, '''left\:([0-9]+?)px''')[0])
            val2 = int(self.cm.ph.getSearchGroups(item2, '''left\:([0-9]+?)px''')[0])
            printDBG("%s %s" % (val1, val2))
            if val1 < val2:   ret = -1
            elif val1 > val2: ret = 1
            else:             ret = 0
            return ret
        
        data.sort(_cmpLinksBest)
        data = clean_html(''.join(data)).strip()
        if data != '': post_data['code'] = data
        
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return False
        
        # get JS player script code from confirmation page
        sts, tmp = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
        if sts:
            try:
                tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                data += tmp
            except Exception: printExc()
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video[^>]*?src="([^"]+?)"')[0]
        if videoUrl.startswith('http'):
            return videoUrl
        return False
    
    def parserUPLOAD(self, baseUrl):
        printDBG("parserUPLOAD baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        
        if baseUrl.startswith('http://'):
            baseUrl = 'https' + baseUrl[4:]
        
        def _getPage(url, params={}, post_data=None):
            return self.cm.getPageWithWget(url, params, post_data)

        sts, data = _getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        for marker in ['File Not Found', 'The file you were looking for could not be found, sorry for any inconvenience.']:
            if marker in data: SetIPTVPlayerLastHostError(_(marker))
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        HTTP_HEADER['Referer'] = baseUrl
        
        sts, data = _getPage(baseUrl, {'header':HTTP_HEADER}, post_data )
        if not sts: return False
        
        sitekey = self.cm.ph.getSearchGroups(data, 'data-sitekey="([^"]+?)"')[0]
        if sitekey != '': 
            token = UnCaptchaReCaptcha(lang=GetDefaultLang()).processCaptcha(sitekey)
            if token == '': return False
        else: token = ''
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        if '' != token: post_data['g-recaptcha-response'] = token
        
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = _getPage(baseUrl, {'header':HTTP_HEADER}, post_data )
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        videoData = self.cm.ph.rgetDataBeetwenMarkers2(data, '>download<', '<a ', caseSensitive=False)[1]
        printDBG('videoData[%s]' % videoData)
        videoUrl = self.cm.ph.getSearchGroups(videoData, 'href="([^"]+?)"')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<[^>]+?class="downloadbtn"[^>]+?['"](http[s]?://[^'^"]+?['"])''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl   
        
        return False
        
        #printDBG(data)
        #videoUrl = self.cm.ph.getSearchGroups(data, '''<[^>]+?'class="downloadbtn"[^>]+?['"](http[s]?://[^'^"]+?(?:\.avi|.mkv)['"])''')[0]
        videoUrl = self.cm.ph.getSearchGroups(data, '<a\s+class="btn"\s+href="([^"]+?)"')[0]
        if not self.cm.isValidUrl(videoUrl): videoUrl = self.cm.ph.getSearchGroups(data, '<a[^>]+?href="([^"]+?)"[^>]+?class="btn"')[0]
        if not self.cm.isValidUrl(videoUrl): videoUrl = self.cm.ph.getSearchGroups(data, '<a[^>]+?class="[^"]*?btn[^"]*?"[^>]+?href="([^"]+?)"[^>]')[0]
        if not self.cm.isValidUrl(videoUrl): videoUrl = self.cm.ph.getSearchGroups(data, '<a[^>]+?href="([^"]+?)"[^>]+?class="[^"]*?btn[^"]*?"')[0]
        return videoUrl
        
    def parserUCASTERCOM(self, baseUrl):
        printDBG("parserUCASTERCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta: HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        
        # get IP
        sts, data = self.cm.getPage('http://www.pubucaster.com:1935/loadbalancer', {'header': HTTP_HEADER})
        if not sts: return False
        ip = data.split('=')[-1].strip()
        
        streamsTab = []
        # m3u8 link
        url = videoUrl.replace('/embedplayer/', '/membedplayer/')
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if sts:
            streamUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]+?\.m3u8[^'^"]+?)['"]''')[0]
            if streamUrl != '':
                streamUrl = 'http://' + ip + streamUrl
                streamsTab.extend(getDirectM3U8Playlist(streamUrl))
        
        # rtmp does not work at now
        return streamsTab
        url = videoUrl.replace('/membedplayer/', '/embedplayer/')
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if not sts: return streamsTab
        try: 
            tmp = self.cm.ph.getSearchGroups(data, '''['"]FlashVars['"]\s*,\s*['"]([^'^"]+?)['"]''')[0]
            tmp = parse_qs(tmp)
            playpath = '{0}?id={1}&pk={2}'.format(tmp['s'][0], tmp['id'][0], tmp['pk'][0])
            rtmpUrl  = 'rtmp://{0}/live'.format(ip)
            swfUrl   = 'http://www.embeducaster.com/static/scripts/fplayer.swf'
            streamUrl = rtmpUrl + ' playpath=' + playpath +  ' tcUrl=' + rtmpUrl + ' swfUrl=' + swfUrl + ' pageUrl=' + baseUrl + ' app=live live=1 conn=S:OK'
            streamsTab.append({'name':'[rtmp] ucaster', 'url':streamUrl})
        except:
            printExc()
        return streamsTab
        
    def parserDOTSTREAMTV(self, linkUrl):
        printDBG("parserDOTSTREAMTV linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        #printDBG(data)
        if sts:
            try:
                a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
                b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
                c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
                d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
                f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
                v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
                
                url = ('://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) )
                if True:
                    url = 'rtmp' + url + v_part
                    url += ' swfUrl=%sjwp/jwplayer.flash.swf pageUrl=%s live=1 token=‪%s ' % (self.cm.getBaseUrl(videoUrl), videoUrl, '#atd%#$ZH')
                else:
                    tmp = v_part.split('?')
                    url = 'http' + url + tmp[0] + '/index.m3u8?' + tmp[1]
                    printDBG(url)
                    return getDirectM3U8Playlist(url)
                return url
            except Exception:
                printExc()
        return False
    
    def parserABCASTBIZ(self, linkUrl):
        printDBG("parserABCASTBIZ linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        swfUrl = "http://abcast.net/player.swf"
        file = self.cm.ph.getSearchGroups(data, 'file=([^&]+?)&')[0]
        if file.endswith(".flv"): file = file[0:-4]
        streamer = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        if '' != file:
            url    = "rtmpe://live.abcast.biz/redirect"
            url = streamer
            url += ' playpath=%s swfUrl=%s pageUrl=%s' % (file, swfUrl, linkUrl)
            printDBG(url)
            return url
        data = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        url    = self.cm.ph.getSearchGroups(data, 'streamer[^"]+?"(rtmp[^"]+?)"')[0]
        file   = self.cm.ph.getSearchGroups(data, 'file[^"]+?"([^"]+?)"')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s ' % (file, swfUrl, linkUrl)
            return url
        return False
        
    def parserOPENLIVEORG(self, linkUrl):
        printDBG("parserOPENLIVEORG linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
            
        file     = self.cm.ph.getSearchGroups(data, 'file=([^&]+?)&')[0]
        if file.endswith(".flv"): file = file[0:-4]
        streamer = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        swfUrl = "http://openlive.org/player.swf"
        if '' != file:
            url = streamer
            url += ' playpath=%s swfUrl=%s pageUrl=%s' % (file, swfUrl, linkUrl)
            printDBG(url)
            return url
        data = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        url    = self.cm.ph.getSearchGroups(data, 'streamer[^"]+?"(rtmp[^"]+?)"')[0]
        file   = self.cm.ph.getSearchGroups(data, 'file[^"]+?"([^"]+?)"')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s ' % (file, swfUrl, linkUrl)
            return url
        return False
        
    def parserGOODCASTCO(self, linkUrl):
        printDBG("parserGOODCASTCO linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        url  = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        file = self.cm.ph.getSearchGroups(data, 'file=([0-9]+?)&')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=http://abcast.biz/ab.swf pageUrl=%s token=Fo5_n0w?U.rA6l3-70w47ch' % (file, linkUrl)
            return url
        return False
        
    def paserLIVEALLTV(self, linkUrl):
        printDBG("paserLIVEALLTV linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
        b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
        c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
        d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
        f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
        v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
        
        url = ('rtmp://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) ) + v_part
        url += ' swfUrl=http://wds.liveall.tv/jwplayer.flash.swf pageUrl=%s' % (linkUrl)
        return url
        
    def paserP2PCASTTV(self, linkUrl):
        printDBG("paserP2PCASTTV linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0"
        COOKIE_FILE = GetCookieDir('p2pcasttv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(videoUrl, params)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'curl[^"]*?=[^"]*?"([^"]+?)"')[0]
        if '' == url: url = self.cm.ph.getSearchGroups(data, 'murl[^"]*?=[^"]*?"([^"]+?)"')[0]
        url = base64.b64decode(url)
        
        if url.endswith('token='):
            params['header']['Referer'] = linkUrl
            params['header']['X-Requested-With'] = 'XMLHttpRequest'
            params['load_cookie'] = True
            sts, data = self.cm.getPage('http://p2pcast.tech/getTok.php', params)
            if not sts: return False
            data = byteify(json.loads(data))
            url += data['token']
        return urlparser.decorateUrl(url, {'Referer':'http://cdn.webplayer.pw/jwplayer.flash.swf', "User-Agent": HTTP_HEADER['User-Agent']})
        
    def paserNOWLIVEPW(self, linkUrl):
        printDBG("paserNOWLIVEPW linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0"
        COOKIE_FILE = GetCookieDir('novelivepw.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(videoUrl, params)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'curl[^"]*?=[^"]*?"([^"]+?)"')[0]
        if '' == url: url = self.cm.ph.getSearchGroups(data, 'murl[^"]*?=[^"]*?"([^"]+?)"')[0]
        url = base64.b64decode(url)
        
        if url.endswith('token='):
            params['header']['Referer'] = linkUrl
            params['header']['X-Requested-With'] = 'XMLHttpRequest'
            params['load_cookie'] = True
            sts, data = self.cm.getPage(urlparser.getDomain(linkUrl, False) + 'getToken.php', params)
            if not sts: return False
            data = byteify(json.loads(data))
            url += data['token']
        return urlparser.decorateUrl(url, {'Referer':linkUrl, "User-Agent": HTTP_HEADER['User-Agent']})
    
    def parserGOOGLE(self, baseUrl):
        printDBG("parserGOOGLE baseUrl[%s]" % baseUrl)
        
        videoTab = []
        _VALID_URL = r'https?://(?:(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)|video\.google\.com/get_player\?.*?docid=)(?P<id>[a-zA-Z0-9_-]{28})'
        mobj = re.match(_VALID_URL, baseUrl)
        try:
            video_id = mobj.group('id')
            linkUrl = 'http://docs.google.com/file/d/' + video_id 
        except Exception:
            linkUrl = baseUrl
            
        _FORMATS_EXT = {
            '5': 'flv', '6': 'flv',
            '13': '3gp', '17': '3gp',
            '18': 'mp4', '22': 'mp4',
            '34': 'flv', '35': 'flv',
            '36': '3gp', '37': 'mp4',
            '38': 'mp4', '43': 'webm',
            '44': 'webm', '45': 'webm',
            '46': 'webm', '59': 'mp4',
        }
        
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
        HTTP_HEADER['Referer'] = linkUrl
        
        COOKIE_FILE = GetCookieDir('google.cookie')
        defaultParams = {'header': HTTP_HEADER, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(linkUrl, defaultParams)
        if not sts: return False 
        
        cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        fmtDict = {} 
        fmtList = self.cm.ph.getSearchGroups(data, '"fmt_list"[:,]"([^"]+?)"')[0]
        fmtList = fmtList.split(',')
        for item in fmtList:
            item = self.cm.ph.getSearchGroups(item, '([0-9]+?)/([0-9]+?x[0-9]+?)/', 2)
            if item[0] != '' and item[1] != '':
                fmtDict[item[0]] = item[1]
        data = self.cm.ph.getSearchGroups(data, '"fmt_stream_map"[:,]"([^"]+?)"')[0]
        data = data.split(',')
        for item in data:
            item = item.split('|')
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> type[%s]" % item[0])
            if 'mp4' in _FORMATS_EXT.get(item[0], ''):
                videoTab.append({'name':'google.com: %s' % fmtDict.get(item[0], '').split('x')[1] + 'p', 'url':strwithmeta(unicode_escape(item[1]), {'Cookie':cookieHeader, 'Referer':'https://youtube.googleapis.com/', 'User-Agent':HTTP_HEADER['User-Agent']})})
        return videoTab
        
    def parserPICASAWEB(self, baseUrl):
        printDBG("parserPICASAWEB baseUrl[%s]" % baseUrl)
        videoTab = []
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return videoTab
        data = re.compile('(\{"url"[^}]+?\})').findall(data)
        printDBG(data)
        for item in data:
            try:
                item = byteify(json.loads(item))
                if 'video' in item.get('type', ''):
                    videoTab.append({'name':'%sx%s' % (item.get('width', ''), item.get('height', '')), 'url':item['url']})
            except Exception:
                printExc()
        return videoTab
        
    def parserMYVIRU(self, linkUrl):
        printDBG("parserMYVIRU linkUrl[%s]" % linkUrl)
        COOKIE_FILE = GetCookieDir('myviru.cookie')
        params  = {'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        if linkUrl.startswith('https://'):
            linkUrl = 'http' + linkUrl[5:]
        videoTab = []
        if '/player/flash/' in linkUrl:
            videoId = linkUrl.split('/')[-1]
            sts, response = self.cm.getPage(linkUrl, {'return_data':False})
            if not sts: return videoTab
            preloaderUrl = response.geturl()
            response.close()
            flashApiUrl = "http://myvi.ru/player/api/video/getFlash/%s?ap=1&referer&sig&url=%s" % (videoId, urllib.quote(preloaderUrl))
            sts, data = self.cm.getPage(flashApiUrl)
            if not sts: return videoTab
            data = data.replace('\\', '')
            data = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            if not data.startswith("//"): return videoTab
            linkUrl = "http:" + data
        if '/embed/html/' in linkUrl: 
            sts, data = self.cm.getPage(linkUrl)
            if not sts: return videoTab
            data = self.cm.ph.getSearchGroups(data, """dataUrl[^'^"]*?:[^'^"]*?['"]([^'^"]+?)['"]""")[0]
            if data.startswith("//"): linkUrl = "http:" + data
            elif data.startswith("/"): linkUrl = "http://myvi.ru" + data
            elif data.startswith("http"): linkUrl = data
            else: return videoTab 
            if linkUrl.startswith('https://'):
                linkUrl = 'http' + linkUrl[5:]
            sts, data = self.cm.getPage(linkUrl, params)
            if not sts: return videoTab
            try:
                # get cookie data
                universalUserID = self.cm.getCookieItem(COOKIE_FILE,'UniversalUserID')
                data = json.loads(data)
                for item in data['sprutoData']['playlist']:
                    url = item['video'][0]['url'].encode('utf-8')
                    if url.startswith('http'):
                        videoTab.append({'name': 'myvi.ru: %s' % item['duration'], 'url':strwithmeta(url, {'Cookie':'UniversalUserID=%s; vp=0.33' % universalUserID})})
            except Exception: 
                printExc()
        return videoTab
        
    def parserARCHIVEORG(self, linkUrl):
        printDBG("parserARCHIVEORG linkUrl[%s]" % linkUrl)
        videoTab = []
        sts, data = self.cm.getPage(linkUrl)
        if sts: 
            data = self.cm.ph.getSearchGroups(data, '"sources":\[([^]]+?)]')[0]
            data = '[%s]' % data
            try:
                data = json.loads(data)
                for item in data:
                    if 'mp4' == item['type']:
                        videoTab.append({'name':'archive.org: ' + item['label'].encode('utf-8'), 'url':'https://archive.org' + item['file'].encode('utf-8')})
            except Exception:
                printExc()
        return videoTab
        
    def parserSAWLIVETV(self, baseUrl):
        printDBG("parserSAWLIVETV linkUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl)
        #HTTP_HEADER['Referer'] = Referer
        
        COOKIE_FILE = GetCookieDir('sawlive.tv')
        params = {'header' : HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        stdWay = False
        if 1:
            sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
            if not sts: return False
            
            if 'eval' in data:
                data  = data.strip()
                data = data[data.rfind('}(')+2:-2]
                
                data = unpackJS(data, SAWLIVETV_decryptPlayerParams)
                printDBG(">>>>>>>>>>>>>>>>>>>" + data)
                
                def jal(a):
                    b = ''
                    for c in a:
                        b += JS_toString(ord(c), 16)
                    return b
                
                linkUrl = self.cm.ph.getSearchGroups(data, '''src="([^"']+?)["']''')[0] + '/' + jal(urlparser().getHostName(Referer))
            else:
                stdWay = True
        if stdWay:
            params['header']['Referer'] = Referer
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return False
            
            vars = dict( re.compile("var ([^=]+?)='([^']+?)';").findall(data) )
            data = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            
            def fakeJSExec(dat):
                dat = dat.group(1)
                if dat.startswith('unescape'):
                    dat = self.cm.ph.getSearchGroups(dat, '\(([^)]+?)\)')[0]
                    if "'" == dat[0]:
                        dat = dat[1:-1]
                    else:
                        dat = vars[dat]
                    printDBG('dat: ' + dat)
                    return dat.replace('%', '\\u00').decode('unicode-escape').encode("utf-8")
                else:
                    return vars[dat]
            linkUrl = re.sub("'\+([^+]+?)\+'", fakeJSExec, data)
        
        sts, data = self.cm.getPage(linkUrl, params)
        if not sts: return False
        swfUrl = self.cm.ph.getSearchGroups(data, "'(http[^']+?swf)'")[0]
        url    = self.cm.ph.getSearchGroups(data, "streamer'[^']+?'(rtmp[^']+?)'")[0]
        file   = self.cm.ph.getSearchGroups(data, "file'[^']+?'([^']+?)'")[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s ' % (file, swfUrl, linkUrl)
            #printDBG(url)
            return url
        return False
        
    def parserSHIDURLIVECOM(self, baseUrl):
        printDBG("parserSHIDURLIVECOM linkUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        linkUrl = self.cm.ph.getSearchGroups(data, 'src="(http[^"]+?)"')[0].strip()
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'new SWFObject', '</script>', True)[1]
        printDBG(data)
        dataTab = data.split(';')
        data = ''
        for line in dataTab: 
            if not line.strip().startswith('//'): 
                data += line+';'
        swfUrl = self.cm.ph.getSearchGroups(data, "'(http[^']+?swf)'")[0]
        url    = self.cm.ph.getSearchGroups(data, "streamer'[^']+?'(rtmp[^']+?)'")[0]#.replace('rtmp://', 'rtmpe://')
        file   = urllib.unquote( self.cm.ph.getSearchGroups(data, "file'[^']+?'([^']+?)'")[0] )
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, linkUrl)
            printDBG(url)
            return url
        return False
        
    def parserCASTALBATV(self, baseUrl):
        printDBG("parserCASTALBATV baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        def _getParam(name):
            return self.cm.ph.getDataBeetwenMarkers(data, "'%s':" % name, ',', False)[1].strip() + ", '{0}'".format(name)
            #self.cm.ph.getSearchGroups(data, """['"]%s['"][^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        def _getParamVal(value, name):
            return value
        data = self.cm.ph.getDataBeetwenMarkers(data, '<script type="text/javascript">', '</script>', False)[1]
        vars = dict( re.compile('''var ([^=]+?)=[^']*?'([^']+?)['];''').findall(data) )
        printDBG("===================================")
        printDBG(vars)
        printDBG("===================================")
        addCode = ''
        for item in vars:
            addCode += '%s="%s"\n' % (item, vars[item])
            
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        pyCode = addCode
        for item in funData:
            funHeader = item[0]
            
            funBody = item[1]
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
            
        addCode = pyCode
        printDBG("===================================")
        printDBG(pyCode)
        printDBG("===================================")
            
        swfUrl = unpackJS(_getParam('flashplayer'), _getParamVal, addCode)
        url    = unpackJS(_getParam('streamer'), _getParamVal, addCode)
        file   = unpackJS(_getParam('file'), _getParamVal, addCode)
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserFXSTREAMBIZ(self, baseUrl):
        printDBG("parserFXSTREAMBIZ baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]*%s['"]*[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0]
        file   = _getParam('file')
        printDBG(data)
        return False
        
    def parserWEBCAMERAPL(self, baseUrl):
        printDBG("parserWEBCAMERAPL baseUrl[%s]" % baseUrl)
        
        def _getFullUrl(url):
            if url.startswith('//'):
                url = 'http:' + url
            return url
        
        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return urlsTab
        
        playerUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?player\.webcamera\.[^'^"]+?)['"]""")[0]
        if playerUrl.startswith('//'):
            playerUrl = 'http:' + playerUrl
        if self.cm.isValidUrl(playerUrl):
            sts, tmp = self.cm.getPage(playerUrl)
            tmp = re.compile("""['"]([^'^"]+?\.m3u8[^'^"]*?)['"]""").findall(tmp)
            if len(tmp) == 2:
                tmpList = getDirectM3U8Playlist(_getFullUrl(tmp[0]), checkContent=True)
                if len(tmpList):
                    urlsTab.extend(tmpList)
                else:
                    return getDirectM3U8Playlist(_getFullUrl(tmp[1]), checkContent=True)
            else:
                for playerUrl in tmp:
                    if self.cm.isValidUrl(_getFullUrl(playerUrl)):
                        urlsTab.extend(getDirectM3U8Playlist(playerUrl), checkContent=True)
        
        data = self.cm.ph.getSearchGroups(data, """<meta itemprop="embedURL" content=['"]([^'^"]+?)['"]""")[0]
        data = data.split('&')
        if 2 < len(data) and data[0].startswith('http') and data[1].startswith('streamer=') and data[2].startswith('file='):
            swfUrl = data[0]
            url    = urllib.unquote(data[1][len('streamer='):])
            file   = urllib.unquote(data[2][len('file='):])
            if '' != file and '' != url:
                url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
                urlsTab.append({'name':'rtmp', 'url':url})
        return urlsTab
        
    def parserFLASHXTV(self, baseUrl):
        printDBG("parserFLASHXTV baseUrl[%s]" % baseUrl)
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language':'pl,en-US;q=0.7,en;q=0.3',
                        'Accept-Encoding':'gzip, deflate',
                        'DNT':1,
                        'Connection':'keep-alive',
                      }
                      
        if '.tv/embed-' not in baseUrl:
            baseUrl = baseUrl.replace('.tv/', '.tv/embed-')
        if not baseUrl.endswith('.html'):
            baseUrl += '.html'
        HTTP_HEADER['Referer'] = baseUrl
        SWF_URL = 'http://static.flashx.tv/player6/jwplayer.flash.swf'
        
        COOKIE_FILE = GetCookieDir('flashxtv.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'return_data':False}
        
        id = self.cm.ph.getSearchGroups(baseUrl+'/', 'c=([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        if id == '': id = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        baseUrl = 'http://www.flashx.tv/embed.php?c=' + id
        
        sts, response = self.cm.getPage(baseUrl, params)
        redirectUrl = response.geturl() 
        response.close()
        
        id = self.cm.ph.getSearchGroups(redirectUrl+'/', 'c=([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        if id == '': id = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0] 
        baseUrl = 'http://www.flashx.tv/embed.php?c=' + id
        
        params['return_data'] = True
        sts, data = self.cm.getPage(baseUrl, params)
        params['header']['Referer'] = redirectUrl
        params['return_data'] = True
        params['load_cookie'] = True
        
        def _first_of_each(*sequences):
            return (next((x for x in sequence if x), '') for sequence in sequences)
        
        def _url_path_join(*parts):
            """Normalize url parts and join them with a slash."""
            schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
            scheme, netloc, query, fragment = _first_of_each(schemes, netlocs, queries, fragments)
            path = '/'.join(x.strip('/') for x in paths if x)
            return urlunsplit((scheme, netloc, path, query, fragment))
        
        vid = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        for item in ['playvid', 'playthis', 'playit']:
            if item+'-' in data:
                play = item
                break
        
        printDBG("vid[%s] play[%s]" % (vid, play))
        
        #tmpUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?counter[^'^"]+?)['"]""")[0]
        #if tmpUrl == '': tmpUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?jquery2[^'^"]+?)['"]""")[0]
        tmpUrls = re.compile("""['"]([^'^"]+?\.js[^'^"]+?)['"]""").findall(data)
        for tmpUrl in tmpUrls:
            if tmpUrl.startswith('.'):
                tmpUrl = tmpUrl[1:]
            if tmpUrl.startswith('//'):
                tmpUrl = 'http:' + tmpUrl
            if tmpUrl.startswith('/'):
                tmpUrl = 'http://www.flashx.tv' + tmpUrl
            if tmpUrl != '':
                printDBG('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                printDBG(tmpUrl)
                sts, tmp = self.cm.getPage(tmpUrl, params)
        #sts, tmp = self.cm.getPage(tmpUrl, params)
        
        sts, tmp = self.cm.getPage('https://www.flashx.tv/js/code.js', params)
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, 'function', ';');
        for tmpItem in tmp:
            tmpItem = tmpItem.replace(' ', '')
            if '!=null' in tmpItem:
                tmpItem   = self.cm.ph.getDataBeetwenMarkers(tmpItem, 'get(', ')')[1]
                tmpUrl    = self.cm.ph.getSearchGroups(tmpItem, """['"](https?://[^'^"]+?)['"]""")[0]
                if not self.cm.isValidUrl(tmpUrl): continue
                getParams = self.cm.ph.getDataBeetwenMarkers(tmpItem, '{', '}', False)[1]
                getParams = getParams.replace(':', '=').replace(',', '&').replace('"', '').replace("'", '')
                tmpUrl += '?' + getParams
                sts, tmp = self.cm.getPage(tmpUrl, params)
                break
        
        url = self.cm.ph.getSearchGroups(redirectUrl, """(https?://[^/]+?/)""")[0] + play + '-{0}.html?{1}'.format(vid, play)
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        printDBG(data)
            
        if 'fxplay' not in url and 'fxplay' in data:
            url = self.cm.ph.getSearchGroups(data, '"(http[^"]+?fxplay[^"]+?)"')[0]
            sts, data = self.cm.getPage(url)
            if not sts: return False
        
        try:
            printDBG(data)
            if 'Sorry, file was deleted!' in data:
                SetIPTVPlayerLastHostError(_('Sorry, file was deleted!'))
            
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>', False, False)
            for tmp in tmpTab:
                tmp2 = ''
                for type in [0, 1]:
                    for fun in [SAWLIVETV_decryptPlayerParams, VIDUPME_decryptPlayerParams]:
                        tmp2 = unpackJSPlayerParams(tmp, fun, type=type)
                        printDBG(tmp2)
                        data = tmp2 + data
                        if tmp2 != '': 
                            printDBG("+++++++++++++++++++++++++++++++++++++++")
                            printDBG(tmp2)
                            printDBG("+++++++++++++++++++++++++++++++++++++++")
                            break
                    if tmp2 != '': break
                        
        except Exception:
            printExc()
        
        data = self.cm.ph.getSearchGroups(data, """["']*file["']*[ ]*?:[ ]*?["']([^"^']+?)['"]""")[0]
        if data.startswith('http'):
            if data.split('?')[0].endswith('.smil'):
                # get stream link
                sts, data = self.cm.getPage(data)
                if sts:
                    base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
                    src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                    #if ':' in src:
                    #    src = src.split(':')[1]   
                    if base.startswith('rtmp'):
                        return base + '/' + src + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, redirectUrl)
            else:
                return data
        return False
        
    def parserMYVIDEODE(self, baseUrl):
        printDBG("parserMYVIDEODE baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0",
                       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
                       'Referer': baseUrl}
        baseUrl = strwithmeta(baseUrl)
        ################################################################################
        # Implementation based on:
        # https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/myvideo.py
        ################################################################################
        swfUrl = 'http://is5.myvideo.de/de/player/mingR14b/ming.swf'
        GK = b'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakptTW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3TnpsbA0KTVRkbU1tSTRNdz09'
        requestParams = {'http_proxy':baseUrl.meta.get('http_proxy', '')}
        requestParams['header'] = HTTP_HEADER
        baseUrl = strwithmeta(baseUrl+'/')
        
        videoTab = []
        
        # Original Code from: https://github.com/dersphere/plugin.video.myvideo_de.git
        # Released into the Public Domain by Tristan Fischer on 2013-05-19
        # https://github.com/rg3/youtube-dl/pull/842
        def __rc4crypt(data, key):
            x = 0
            box = list(range(256))
            for i in list(range(256)):
                x = (x + box[i] + ord(key[i % len(key)])) % 256
                box[i], box[x] = box[x], box[i]
            x = 0
            y = 0
            out = ''
            for char in data:
                x = (x + 1) % 256
                y = (y + box[x]) % 256
                box[x], box[y] = box[y], box[x]
                out += chr(ord(char) ^ box[(box[x] + box[y]) % 256])
            return out
        def __md5(s):
            return md5(s).hexdigest().encode()
            
        def _getRtmpLink(r, tcUrl, playpath, swfUrl, page):
            if '?token=' in r:
                tmp = r.split('?token=')
                r = tmp[0]
                token = tmp[1]
            else:
                token = ''
            if '' != tcUrl:    r += ' tcUrl='    + tcUrl
            if '' != playpath: r += ' playpath=' + playpath
            if '' != swfUrl:   r += ' swfUrl='   + swfUrl
            if '' != page:     r += ' pageUrl='  + page
            if '' != token:     r += ' token='    + token
            return urlparser.decorateUrl(r, {'iptv_livestream':False})
        # Get video ID
        video_id = baseUrl
        if '-m-' in video_id:
            video_id = self.cm.ph.getSearchGroups(video_id, """-m-([0-9]+?)[^0-9]""")[0]
        else:
            video_id = self.cm.ph.getSearchGroups(video_id, """/(?:[^/]+/)?watch/([0-9]+)/""")[0]
        if '' != video_id:
            try:
                xmldata_url = "http://www.myvideo.de/dynamic/get_player_video_xml.php?ID=%s&flash_playertype=D&autorun=yes" % video_id
                sts, enc_data = self.cm.getPage(xmldata_url, requestParams)
                enc_data = enc_data.split('=')[1]
                enc_data_b = unhexlify(enc_data)
                sk = __md5(base64.b64decode(base64.b64decode(GK)) + __md5(str(video_id).encode('utf-8')))
                dec_data = __rc4crypt(enc_data_b, sk)
                #printDBG("============================================================================")
                #printDBG(dec_data)
                #printDBG("============================================================================")

                # extracting infos
                connectionurl = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "connectionurl='([^']*?)'")[0] )
                source        = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "source='([^']*?)'")[0] )
                path          = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "path='([^']*?)'")[0] )
                
                if connectionurl.startswith('rtmp'):
                    connectionurl = connectionurl.replace('rtmpe://', 'rtmp://')
                
                    rtmpUrl = urlparser.decorateUrl(connectionurl)
                    if rtmpUrl.meta.get('iptv_proto', '') == 'rtmp':
                        if not source.endswith('f4m') :
                            playpath = source.split('.')
                            playpath = '%s:%s' % (playpath[1], playpath[0]) 
                        videoUrl = _getRtmpLink(rtmpUrl, rtmpUrl, playpath, swfUrl, baseUrl)
                        videoTab.append({'name':'myvideo.de: RTMP', 'url':videoUrl})
                else:
                    videoTab.append({'name':'myvideo.de: HTTP', 'url':path+source})
            except Exception:
                printExc()
                
        return videoTab
        
    def parserVIDZITV(self, baseUrl):
        printDBG("parserVIDZITV baseUrl[%s]" % baseUrl)
        videoTab = []
        if 'embed' not in baseUrl:
            vid = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
            baseUrl = 'http://vidzi.tv/embed-%s-682x500.html' % vid
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        # get JS player script code from confirmation page
        sts, tmp = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
        if sts:
            try:
                tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                data = tmp + data
            except Exception: printExc()
        
        data = CParsingHelper.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
        data = re.findall('file:[ ]*"([^"]+?)"', data)
        for item in data:
            if item.split('?')[0].endswith('m3u8'):
                tmp = getDirectM3U8Playlist(item)
                videoTab.extend(tmp)
            else:
                videoTab.append({'name':'vidzi.tv mp4', 'url':item})
        return videoTab
        
    def parserTVP(self, baseUrl):
        printDBG("parserTVP baseUrl[%s]" % baseUrl)
        vidTab = []
        try:
            sts, data = self.cm.getPage(baseUrl)
            if sts:
                
                object_id = self.cm.ph.getSearchGroups(data, 'data-video-id="([0-9]+?)"')[0]
                if '' == object_id:
                    object_id = self.cm.ph.getSearchGroups(data, "object_id:'([0-9]+?)'")[0]
                if '' == object_id:
                    object_id = self.cm.ph.getSearchGroups(data, 'object_id=([0-9]+?)[^0-9]')[0]
                if '' != object_id:
                    from Plugins.Extensions.IPTVPlayer.hosts.hosttvpvod import TvpVod
                    vidTab = TvpVod().getVideoLink(object_id)
        except Exception:
            printExc()
        return vidTab
        
    def parserJUNKYVIDEO(self, baseUrl):
        printDBG("parserJUNKYVIDEO baseUrl[%s]" % baseUrl)
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
        if url.startswith('http'):
            return [{'name':'junkyvideo.com', 'url':url}]
        return []
        
    def parserLIVEBVBTOTALDE(self, baseUrl):
        printDBG("parserJUNKYVIDEO baseUrl[%s]" % baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'<iframe[^>]+?src="([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'<iframe[^>]+?src="([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'url: "([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        printDBG(data)
        if 'statustext="success"' not in data: return []
        url   = self.cm.ph.getSearchGroups(data, r'url="([^"]+)"')[0]
        autch = self.cm.ph.getSearchGroups(data, r'auth="([^"]+)"')[0]
        url += '?' + autch
        linksTab = []
        retTab = getDirectM3U8Playlist(url)
        return retTab
        for item in retTab:
            name = ('live.bvbtotal.de %s' % item.get('heigth', 0))
            url = urlparser.decorateUrl(item['url'], {'iptv_livestream': True})
            linksTab.append({'name':name, 'url':url})
        return linksTab
        
    def parserNETTVPLUSCOM(self, baseUrl):
        printDBG("parserNETTVPLUSCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = baseUrl
        if baseUrl.endswith('/source.js'): url = baseUrl
        else: url = baseUrl[:baseUrl.rfind('/')] + '/source.js'
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?m3u8[^'^"]*?)["']''')[0]
        if '' != url: return getDirectM3U8Playlist(url, False)
        return []
        
    def parser7CASTNET(self, baseUrl):
        printDBG("parser7CASTNET baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateUrl(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = referer

        url = baseUrl
        if '/embed/' in url:
            sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
            if not sts: return []
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^'^"]+?)["']''')[0]
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if not sts: return False
        data = data[data.rfind('}(')+2:].split('{}))')[0] + '{}'
        data = unpackJS(data, SAWLIVETV_decryptPlayerParams)
        names  = []
        values = {}
        data = re.compile(";([^;]+?)\.push\('(.)'\)").findall(data)
        for item in data:
            if item[0] not in names:
                names.append(item[0])
                values[item[0]] = item[1]
            else: values[item[0]] += item[1]
        if urllib.unquote(values[names[1]]).startswith('rtmp'): names = names[::-1]
        r = urllib.unquote(values[names[0]]) + '/' + urllib.unquote(values[names[1]])
        printDBG("...............................[%s]" % r)
        if r.startswith('rtmp'):
            swfUrl  = "http://7cast.net/jplayer.swf"
            rtmpUrl = r + ' swfUrl=%s pageUrl=%s live=1 ' % (swfUrl, baseUrl)
            return [{'name': 'rtmp://7cast.com/ ', 'url':urlparser.decorateUrl(rtmpUrl, {'iptv_livestream':True})}]
        return []
        
    def parserFACEBOOK(self, baseUrl):
        printDBG("parserFACEBOOK baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return []
        
        urlsTab = []
        for item in ['hd_src_no_ratelimit', 'hd_src', 'sd_src_no_ratelimit', 'sd_src']:
            url = self.cm.ph.getSearchGroups(data, '''"%s"\s*?:\s*?"(http[^"]+?\.mp4[^"]*?)"''' % item)[0]
            url = url.replace('\\/', '/')
            if self.cm.isValidUrl(url):
                urlsTab.append({'name':'facebook %s' % item, 'url':url})
                
        return urlsTab
        
    def parserCLOUDYVIDEOS(self, baseUrl):
        printDBG("parserCLOUDYVIDEOS baseUrl[%s]" % baseUrl)
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[/-]([A-Za-z0-9]{12})[/-]')[0]
        url = 'http://cloudyvideos.com/{0}'.format(video_id)
        
        linkList = []
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})

        try:
            sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]
            if '' != sleep_time: time.sleep(int(sleep_time))
        except Exception:
            printExc()
        try:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: return False
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            HTTP_HEADER['Referer'] = url
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
            if not sts: return False
            #printDBG(data)
            linkList = self._findLinks(data, serverName='cloudyvideos.com', m1='setup({', m2='</script>')
            for item in linkList:
                item['url'] = urlparser.decorateUrl(item['url']+'?start=0', {'User-Agent':'Mozilla/5.0', 'Referer':'http://cloudyvideos.com/player510/player.swf'})
        except Exception:
            printExc()
        return linkList
        
    def parserFASTVIDEOIN(self, baseUrl):
        printDBG("parserFASTVIDEOIN baseUrl[%s]" % baseUrl)
        #http://fastvideo.in/nr4kzevlbuws
        host = self.cm.ph.getDataBeetwenMarkers(baseUrl, "://", '/', False)[1]
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[/-]([A-Za-z0-9]{12})[/-]')[0]
        
        url = 'http://%s/embed-%s-960x480.html' % (host, video_id)
        sts, data = self.cm.getPage(url)
        if not sts and data != None:
            #USER_AGENT = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'
            url = 'http://%s/%s' % (host, video_id)
            HTTP_HEADER = dict(self.HTTP_HEADER)
            #HTTP_HEADER['User-Agent'] = USER_AGENT
            HTTP_HEADER['Referer'] = url
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
            if not sts: return False
            
            try:
                sleep_time =  self.cm.ph.getDataBeetwenMarkers(data, '<div class="btn-box"', '</div>')[1]
                sleep_time = self.cm.ph.getSearchGroups(sleep_time, '>([0-9]+?)<')[0]
                time.sleep(int(sleep_time))
            except Exception:
                printExc()
                
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST" action', '</Form>', False, False)
            if sts:
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                post_data.pop('method_premium', None)
                HTTP_HEADER['Referer'] = url
                sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
            
            return self._findLinks(data, host,  m1='options', m2='}')
        else:
            return self._findLinks(data, host,  m1='setup(', m2=')')
        return False
        
    def parserTHEVIDEOME(self, baseUrl):
        printDBG("parserTHEVIDEOME baseUrl[%s]" % baseUrl)
        #http://thevideo.me/embed-l03p7if0va9a-682x500.html
        if 'embed' in baseUrl: url = baseUrl
        else: url = baseUrl.replace('.me/', '.me/embed-') + '-640x360.html'

        HTTP_HEADER = {'User-Agent':'Mozilla/5.0'}
        COOKIE_FILE = GetCookieDir('thvideome.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, pageData = self.cm.getPage(url, params)
        if not sts: return False
        
        authKey = self.cm.ph.getSearchGroups(pageData, r"""Key\s*=\s*['"]([^'^"]+?)['"]""")[0]
        try_again = self.cm.ph.getSearchGroups(pageData, r"""try_again\s*=\s*['"]([^'^"]+?)['"]""")[0]
        if len(try_again) > len(authKey): authKey = try_again
        
        params['header']['Referer'] = url
        sts, authKey = self.cm.getPage('http://thevideo.me/jwv/' + authKey, params)
        if not sts: return False
        authKey = self.cm.ph.getSearchGroups(authKey, r"""\|([a-z0-9]{40}[a-z0-9]+?)\|""")[0]
        
        def decorateUrls(urlsTab):
            for idx in range(len(urlsTab)):
                urlsTab[idx]['url'] = urlparser.decorateUrl(urlsTab[idx]['url'] + '?direct=false&ua=1&vt=' + authKey, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':'http://thevideo.me/player/jw/7/jwplayer.flash.swf'})
            return urlsTab
        
        videoLinks = self._findLinks(pageData, 'thevideo.me', r'''['"]?file['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,} ]''')
        if len(videoLinks): return decorateUrls(videoLinks)
        
        # get JS player script code from confirmation page
        sts, data = CParsingHelper.getDataBeetwenMarkers(pageData, ">eval(", '</script>', False)
        if sts:
            mark1 = "}("
            idx1 = data.find(mark1)
            if -1 == idx1: return False
            idx1 += len(mark1)
            # unpack and decode params from JS player script code
            pageData = unpackJS(data[idx1:-3], VIDUPME_decryptPlayerParams)
            return decorateUrls(self._findLinks(pageData, 'thevideo.me'))
        else:
            pageData = CParsingHelper.getDataBeetwenMarkers(pageData, 'setup(', '</script', False)[1]
            videoUrl = self.cm.ph.getSearchGroups(pageData, r"""['"]?file['"]?[ ]*?\:[ ]*?['"]([^"^']+?)['"]""")[0]
            if videoUrl.startswith('http'): return decorateUrls([{'name':'thevideo.me', 'url':videoUrl}])
        return False
    
    def parserMODIVXCOM(self, baseUrl):
        printDBG("parserMODIVXCOM baseUrl[%s]" % baseUrl)
        serverName='movdivx.com'
        def __customLinksFinder(pageData):
            #printDBG(pageData)
            sts, data = CParsingHelper.getDataBeetwenMarkers(pageData, ">eval(", '</script>', False)
            if sts:
                mark1 = "}("
                idx1 = data.find(mark1)
                if -1 == idx1: return False
                idx1 += len(mark1)
                pageData = unpackJS(data[idx1:-3], VIDUPME_decryptPlayerParams)
                return self._findLinks(pageData, serverName)
            else: return []
        return self.__parseJWPLAYER_A(baseUrl, serverName, customLinksFinder=__customLinksFinder)
            
    def parserXAGEPL(self, baseUrl):
        printDBG("parserXAGEPL baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        return urlparser().getVideoLinkExt(url)
        
        
    def parseCASTONTV(self, baseUrl):
        printDBG("parseCASTONTV baseUrl[%s]" % baseUrl)

        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict({'User-Agent':'Mozilla/5.0'}) 
        HTTP_HEADER['Referer'] = Referer
        
        COOKIE_FILE = GetCookieDir('castontv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        id = self.cm.ph.getSearchGroups(baseUrl + '|', 'id=([0-9]+?)[^0-9]')[0]
        linkUrl = 'http://www.caston.tv/player.php?width=1920&height=419&id={0}'.format(id)
        
        sts, data = self.cm.getPage(linkUrl, params)
        if not sts: return False
        
        data = re.sub('''unescape\(["']([^"^']+?)['"]\)''', lambda m: urllib.unquote(m.group(1)), data)
        #printDBG(data)
        
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>', True)[1]
        printDBG(tmpData)
        while 'eval' in tmpData:
            tmp = tmpData.split('eval(')
            if len(tmp): del tmp[0]
            tmpData = ''
            for item in tmp:
                for decFun in [VIDEOWEED_decryptPlayerParams, SAWLIVETV_decryptPlayerParams]:
                    tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                    if '' != tmpData:   
                        break
                printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                printDBG(tmpData)
                printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                if 'token' in tmpData and 'm3u8' in tmpData:
                    break
        token = self.cm.ph.getSearchGroups(tmpData, r"""['"]?token['"]?[\s]*?\:[\s]*?['"]([^"^']+?)['"]""")[0]
        url   = self.cm.ph.getSearchGroups(tmpData, r"""['"]?url['"]?[\s]*?\:[\s]*?['"]([^"^']+?)['"]""")[0]
        file  = self.cm.ph.getSearchGroups(tmpData, r"""['"]?file['"]?[\s]*?\:[\s]*?['"]([^}]+?)\}""")[0] 
        
        printDBG("token[%s]" % token)
        printDBG("url[%s]" % url)
        printDBG("file[%s]" % file)
        
        if url != '' and '://' not in url:
            if url.startswith('//'): url = 'http:' + url
            else: url = 'http://www.caston.tv/' + url

        params['load_cookie'] = True
        params['header'].update({'Referer':linkUrl, 'Accept':'application/json, text/javascript, */*', 'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With':'XMLHttpRequest' })
        sts, data = self.cm.getPage(url, params, {'token':token, 'is_ajax':1})
        if not sts: return False
        
        data = byteify(json.loads(data))
        printDBG(data)
        def _replace(item):
            idx = int(item.group(1))
            return str(data[idx])
            
        file = re.sub('"\+[^"]+?\[([0-9]+?)\]\+"', _replace, file+'+"')
        hlsUrl = urlparser.decorateUrl(file, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':'http://p.jwpcdn.com/6/12/jwplayer.flash.swf', 'User-Agent':'Mozilla/5.0'})
        return getDirectM3U8Playlist(hlsUrl)
        
    def parserCASTAMPCOMUnpackJS(self, code, name):
        printDBG(">>>>>>>>>>>>>>>> code start")
        printDBG(code)
        printDBG(">>>>>>>>>>>>>>>> code end")
        try:
            paramsAlgoObj = compile(code, '', 'exec')
        except Exception:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''

        try:
            vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote}
            vLocals = { name: None }
            exec( code, vGlobals, vLocals )
        except Exception:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except Exception:
            printExc('decryptPlayerParams EXCEPTION')
        return ''

    def parserCASTAMPCOM(self, baseUrl):
        printDBG("parserCASTAMPCOM baseUrl[%s]" % baseUrl)
        channel = self.cm.ph.getSearchGroups(baseUrl + '&', 'c=([^&]+?)&')[0]

        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        def _getDomainsa():
            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"
            string_length = 8
            randomstring = ''
            for i in range(string_length):
                rnum = randint(0, len(chars)-1)
                randomstring += chars[rnum]
            return randomstring 
        
        linkUrl = 'http://www.castamp.com/embed.php?c={0}&tk={1}&vwidth=710&vheight=460'.format(channel, _getDomainsa())
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="player">', '</script>', False)
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]%s['"][^'^"^,]+?['"]([^'^"^,]+?)['"]""" % name)[0] 
        swfUrl = _getParam('flashplayer')
        url    = self.cm.ph.getSearchGroups(data, """\|(rtmp[^'^"^\|]+?)['"\|]""")[0] 
        printDBG(">>>>>>>>>>>>>> url[%s]" % url)
        file   = _getParam('file')
        if file == '':
            file = self.cm.ph.getSearchGroups(data, """['"]file['"]\s*:([^,]+?),""")[0].strip() 
            tmp = re.compile('(%s\s*=[^;]+?);' % file).findall(data)
            code = ''
            for ins in tmp:
                code += ins.strip() + '\n'
            file = self.parserCASTAMPCOMUnpackJS(code, file)
        
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserCRICHDTV(self, baseUrl):
        printDBG("parserCRICHDTV baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        baseUrl.meta['Referer'] = baseUrl
        links = urlparser().getAutoDetectedStreamLink(baseUrl, data)
        return links
        
        
        channelId = self.cm.ph.getSearchGroups(data, "id='([0-9]+?)'")[0]
        linkUrl = 'http://popeoftheplayers.eu/crichd.php?id={0}&width=710&height=460'.format(channelId)
        HTTP_HEADER['Referer'] = baseUrl
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]%s['"][^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://popeoftheplayers.eu/atdedead.swf"#_getParam('flashplayer')
        url    = _getParam('streamer') #rtmp://89.248.172.159:443/liverepeater
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, '#atd%#$ZH', linkUrl)
            printDBG(url)
            return url
        return False
        
        
    def parserCASTTOME(self, baseUrl):
        printDBG("parserCASTTOME baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        #printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]?%s['"]?[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://www.castto.me/_.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, '#ed%h0#w@1', baseUrl)
            printDBG(url)
            return url
        else:
            data = re.compile('''["'](http[^'^"]+?\.m3u8[^'^"]*?)["']''').findall(data)
            data.reverse()
            printDBG(data)
            data.insert(0, file)
            data.reverse()
            for file in data:
                if file.startswith('http') and file.split('?')[0].endswith('.m3u8'):
                    tab = getDirectM3U8Playlist(file, checkContent=True)
                    if len(tab): return tab
        return False
        
    def saveGet(self, b, a):
        try: return b[a]
        except Exception: return 'pic'
        
    def justRet(self, data):
        return data
        
    def _unpackJS(self, data, name):
        data = data.replace('Math.min', 'min').replace(' + (', ' + str(').replace('String.fromCharCode', 'chr').replace('return b[a]', 'return saveGet(b, a)')
        try:
            paramsAlgoObj = compile(data, '', 'exec')
        except Exception:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''
        vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote, 'min':min, 'saveGet':self.saveGet, 'justRet':self.justRet}
        vLocals = { name: None }

        try:
            exec( data, vGlobals, vLocals )
        except Exception:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except Exception:
            printExc('decryptPlayerParams EXCEPTION')
        return ''
        
        
    def parserHDCASTINFO(self, baseUrl):
        printDBG("parserHDCASTINFO baseUrl[%s]" % baseUrl)
        return self.parserCAST4UTV(baseUrl, 'hdcast.info')
        
    def parserCAST4UTV(self, baseUrl, domain='cast4u.tv'):
        printDBG("parserCAST4UTV baseUrl[%s]" % baseUrl)
        
        def _getVariables(data):
            printDBG('_getVariables')
            varTabs = []
            tmp = re.compile('var([^;]+?)=[^;]*?(\[[^\]]+?\]);').findall(data)
            for item in tmp:
                var = item[0].strip()
                val = item[1].strip()
                if var == '': continue
                if val == '': continue
                varTabs.append('%s = %s' % (var, val))
            varTabs = '\n'.join( varTabs )
            return varTabs
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<span style', '</script>')[1]
        globalVars = _getVariables(data)
        file = self.cm.ph.getDataBeetwenMarkers(data, 'file:', '}', False)[1].strip()
        token = self.cm.ph.getSearchGroups(data, """securetoken\s*:\s*([^\s]+?)\s""")[0] 
        
        def _evalSimple(dat):
            return '"%s"' % self.cm.ph.getSearchGroups(data, """<[^>]+?id=['"]?%s['"]?[^>]*?>([^<]+?)<""" % dat.group(1))[0] 
        data = re.sub('document\.getElementById\("([^"]+?)"\)\.innerHTML', _evalSimple, data)
        
        def _evalJoin(dat):
            return " ''.join(%s) " % dat.group(1)
        
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        pyCode = ''
        for item in funData:
            funHeader = item[0]
            
            funBody = re.sub('(\[[^\]]+?\])\.join\(""\)', _evalJoin, item[1])
            funBody = re.sub(' ([^ ]+?)\.join\(""\)', _evalJoin, funBody)
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                if len(ins) and ins[-1] not in [')', ']', '"']:
                    ins += '()'
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
        
        pyCode = 'def retA():\n\t' + globalVars.replace('\n', '\n\t') + '\n\t' + pyCode.replace('\n', '\n\t') + '\n\treturn {0}\n'.format(file) + 'param = retA()'
        printDBG(pyCode)
        file = self._unpackJS(pyCode, 'param').replace('\\/', '/')
        
        swfUrl = 'http://%s/jwplayer/jwplayer.flash.swf' % domain
        token = '%XB00(nKH@#.' #http://stream-recorder.com/forum/rtmp-token-vlc-help-t20959.html?s=7c3a16e350bdc8bdf73c525163884654&amp;
        return file + ' swfUrl=%s token=%s pageUrl=%s live=1 ' % (swfUrl, token, baseUrl)
        
    def parserDELTATVPW(self, baseUrl):
        printDBG("parserDELTATVPW baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, "%s=([^&]+?)&" % name)[0] 
        swfUrl = "http://cdn.deltatv.pw/players.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, 'Fo5_n0w?U.rA6l3-70w47ch', baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserPXSTREAMTV(self, baseUrl):
        printDBG("parserPXSTREAMTV baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """%s:[^'^"]*?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://pxstream.tv/player510.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if file.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(file)
        elif '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
    
    def parserCOOLCASTEU(self, baseUrl):
        printDBG("parserCOOLCASTEU baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        printDBG(data)
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]%s['"]:[^'^"]*?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://coolcast.eu/file/1444766476/player.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfVfy=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
    
    def parserFILENUKE(self, baseUrl):
        printDBG("parserFILENUKE baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0' }
        
        COOKIE_FILE = GetCookieDir('filenuke.com')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        params_s['return_data'] =  False
        sts, response = self.cm.getPage(baseUrl, params_s)
        redirectUrl = response.geturl() 
        data = response.read()
        if not sts: return False
        
        if 'method_free' in data:
            sts, data = self.cm.getPage(baseUrl, params_l, {'method_free':'Free'})
            if not sts: return False
            
        if 'id="go-next"' in data:
            url = self.cm.ph.getSearchGroups(data, '<a[^>]+?id="go-next"[^>]+?href="([^"]+?)"')[0]
            baseUrl = self.cm.ph.getSearchGroups(redirectUrl, '(https?://[^/]+?)/')[0]
            if url.startswith('/'): url = baseUrl + url
            sts, data = self.cm.getPage(url, params_l)
            if not sts: return False
            
        data = self.cm.ph.getDataBeetwenMarkers(data, 'jwplayer', 'play(')[1]
        printDBG(data)
            
        videoMarker = self.cm.ph.getSearchGroups(data, r"""['"]?file['"]?[ ]*?:[ ]*?([^ ^,]+?),""")[0]
        videoUrl    = self.cm.ph.getSearchGroups(data, r"""['"]?%s['"]?[ ]*?\=[ ]*?['"](http[^'^"]+?)["']""" % videoMarker)[0]
        
        printDBG("parserFILENUKE videoMarker[%s] videoUrl[%s]" % (videoMarker, videoUrl))
        if '' == videoUrl: return False
        videoUrl = urlparser.decorateUrl(videoUrl, {'User-Agent':'Mozilla/5.0', 'Referer':'http://filenuke.com/a/jwplayer/jwplayer.flash.swf'})
        return videoUrl
        
    def parserTHEFILEME(self, baseUrl):
        printDBG("parserTHEFILEME baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30" }
        
        COOKIE_FILE = GetCookieDir('thefile.me')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="main-wrap">', '</script>', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?%s['"]?[ ]*?\=[ ]*?['"](http[^'^"]+?)["']""" % 'href')[0]
        seconds = self.cm.ph.getSearchGroups(data, r"""seconds[ ]*?\=[ ]*?([^;^ ]+?);""")[0]
        printDBG("parserFILENUKE seconds[%s] videoUrl[%s]" % (seconds, videoUrl))
        seconds = int(seconds)
        
        time.sleep(seconds+1) 
        
        params_l['header']['Referer'] = videoUrl
        sts, data = self.cm.getPage(videoUrl, params_l)
        if not sts: return False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, 'setup({', '}', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?file['"]?[ ]*?\:[ ]*?['"]([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserCLOUDTIME(self, baseUrl):
        printDBG("parserCLOUDTIME baseUrl[%s]" % baseUrl)
        try:
            url = self._parserUNIVERSAL_B(baseUrl)
            if len(url): return url
        except Exception:
            printExc()
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0" }
        
        COOKIE_FILE = GetCookieDir('cloudtime.to')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        if 'embed' not in baseUrl:
            vidId = self.cm.ph.getSearchGroups(baseUrl + '/', '/video/([^/]+?)/')[0]
            if '' == vidId: vidId = self.cm.ph.getSearchGroups(baseUrl + '&', '[\?&]v=([^&]+?)&')[0]
            baseUrl = 'http://www.cloudtime.to/embed.php?v=' + vidId
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
            
        tokenUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?/api/toker[^'^"]+?)['"]''')[0]
        if tokenUrl.startswith('/'):
            tokenUrl = 'http://www.cloudtime.to' + tokenUrl
        
        HTTP_HEADER['Referer'] = baseUrl
        sts, token = self.cm.getPage(tokenUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} )
        if not sts: return False
        token = self.cm.ph.getDataBeetwenMarkers(token, '=', ';', False)[1].strip()
         
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserNOSVIDEO(self, baseUrl):
        printDBG("parserNOSVIDEO baseUrl[%s]" % baseUrl)
        # code from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/nosvideo.py
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10", 'Referer':baseUrl }

        if 'embed' not in baseUrl:
            videoID = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
            videoUrl = 'http://nosvideo.com/embed/' + videoID
        else:
            videoUrl = baseUrl
        sts, data = self.cm.getPage(videoUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>', False)[1]
        mark1 = "}("
        idx1 = data.find(mark1)
        if -1 == idx1: return False
        idx1 += len(mark1)
        data = unpackJS(data[idx1:-3], VIDUPME_decryptPlayerParams)
        
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?playlist['"]?[ ]*?\:[ ]*?['"]([^"^']+?)['"]""")[0]
        sts, data = self.cm.getPage(videoUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        
        videoUrl = self.cm.ph.getDataBeetwenMarkers(data, '<file>', '</file>', False)[1]
        if not self.cm.isValidUrl(videoUrl):
            videoUrl = self.cm.ph.getSearchGroups(data, 'file="(http[^"]+?)"')[0]

        return videoUrl
        
    def parserPUTSTREAM(self, baseUrl):
        printDBG("parserPUTSTREAM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'putstream.com')
        return self._parserUNIVERSAL_A(baseUrl, 'http://putstream.com/embed-{0}-640x400.html', _findLinks)
        
    def parserLETWATCHUS(self, baseUrl):
        printDBG("parserLETWATCHUS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'letwatch.us')
        return self._parserUNIVERSAL_A(baseUrl, 'http://letwatch.us/embed-{0}-640x360.html', _findLinks)
        
    def parserUPLOADCCOM(self, baseUrl):
        printDBG("parserUPLOADCCOM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.uploadc.com/embed-{0}.html', _findLinks)
        
    def parserMIGHTYUPLOAD(self, baseUrl):
        printDBG("parserMIGHTYUPLOAD baseUrl[%s]" % baseUrl)
        def _preProcessing(data):
            return CParsingHelper.getDataBeetwenMarkers(data, '<div id="player_code">', '</div>', False)[1]
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.mightyupload.com/embed-{0}-645x353.html', _findLinks, _preProcessing)
        
    def parserZALAACOM(self, baseUrl):
        printDBG("parserZALAACOM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.zalaa.com/embed-{0}.html', _findLinks)
    
    def parserALLMYVIDEOS(self, baseUrl):
        printDBG("parserALLMYVIDEOS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'allmyvideos.net')
        return self._parserUNIVERSAL_A(baseUrl, 'http://allmyvideos.net/embed-{0}.html', _findLinks)
        
    def parserRAPIDVIDEOWS(self, baseUrl):
        printDBG("parserRAPIDVIDEOWS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://rapidvideo.ws/embed-{0}-720x420.html', _findLinks)
        
    def parserHDVIDTV(self, baseUrl):
        printDBG("parserHDVIDTV baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://hdvid.tv/embed-{0}-950x480.html', _findLinks)
        
    def parseVIDME(self, baseUrl):
        printDBG("parseVIDME baseUrl[%s]" % baseUrl)
        # from: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/vidme.py
        _VALID_URL = r'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]{,5})(?:[^\da-zA-Z]|$)'
        mobj = re.match(_VALID_URL, baseUrl)
        id = mobj.group('id')
        sts, data = self.cm.getPage('https://api.vid.me/videoByUrl/' + id)
        if not sts: return False
        data = byteify( json.loads(data) )['video']
        if 'formats' in data:
            urlTab = []
            for item in data['formats']:
                if '-clip' in item['type']: continue
                try: 
                    if item['type'] == 'dash': continue
                    elif item['type'] == 'hls':
                        continue
                        hlsTab = getDirectM3U8Playlist(item['uri'], False)
                        urlTab.extend(hlsTab)
                    else:
                        urlTab.append({'name':item['type'], 'url':item['uri']})
                except Exception: pass
            return urlTab
        else:
            return urlparser().getVideoLinkExt(data['source'])
        return False
        
    def parseVEEHDCOM(self, baseUrl):
        printDBG("parseVEEHDCOM baseUrl[%s]" % baseUrl)
        COOKIE_FILE = GetCookieDir('veehdcom.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36',
                       'Referer':baseUrl}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'playeriframe', ';', False)[1]
        url = self.cm.ph.getSearchGroups(data, '''src[ ]*?:[ ]*?['"]([^"^']+?)['"]''')[0]
        if not url.startswith('http'):
            if not url.startswith('/'):
                url = '/' + url 
            url = 'http://veehd.com' + url 
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        vidUrl = self.cm.ph.getSearchGroups(data, '''type=['"]video[^"^']*?["'][^>]+?src=["']([^'^"]+?)['"]''')[0]
        if vidUrl.startswith('http'):
            return vidUrl
        return False
        
    def parseSHAREREPOCOM(self, baseUrl):
        printDBG("parseSHAREREPOCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        tab = []
        tmp = self._findLinks(data, m1='setup', m2='</script>')
        for item in tmp:
            item['url'] = urlparser.decorateUrl(item['url'], {'Referer':baseUrl, 'User-Agent':'Mozilla/5.0'})
            tab.append(item)
        return tab
        
    def parseEASYVIDEOME(self, baseUrl):
        printDBG("parseEASYVIDEOME baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="flowplayer">', '</script>', False)[1]
        tab = self._findLinks(data, serverName='playlist', linkMarker=r'''['"]?url['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='playlist', m2=']')
        video_url = self.cm.ph.getSearchGroups(data, '_url = "(http[^"]+?)"')[0]
        if '' != video_url: 
            video_url = urllib.unquote(video_url)
            tab.insert(0, {'name':'main', 'url':video_url})
        return tab
        
    def parserUPTOSTREAMCOM(self, baseUrl):
        printDBG("parserUPTOSTREAMCOM baseUrl[%s]" % baseUrl)
        
        url = baseUrl
        domain = urlparser.getDomain(baseUrl) 
        if '/iframe/' not in url:
            url = 'https://' + domain + '/iframe/' + url.split('/')[-1]
            baseUrl = url
        else:
            url = baseUrl
        sts, data = self.cm.getPage(url)
        if not sts: return False
        subTracks = []
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track', '</track>', False, False)
        for item in tmp:
            if 'subtitles' not in item: continue
            type  = self.cm.ph.getSearchGroups(item, '''type=['"]([^"^']+?)['"]''')[0]
            lang  = self.cm.ph.getSearchGroups(item, '''lang=['"]([^"^']+?)['"]''')[0]
            label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
            url   = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            if url.startswith('//'):
                url = 'http:' + url
            if '://' not in url: continue
            subTracks.append({'title':label, 'url':url, 'lang':label, 'format':type})
        
        #'<font color="red">', '</font>'
        urlTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source ', '>', False, False)
        for item in data:
            if 'video/mp4' not in item: continue
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^"^']+?)['"]''')[0]
            res  = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
            lang = self.cm.ph.getSearchGroups(item, '''lang=['"]([^"^']+?)['"]''')[0]
            url  = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            if url.startswith('//'):
                url = 'http:' + url
            if url.startswith('http'):
                url = strwithmeta(url, {'Referer':baseUrl, 'external_sub_tracks':subTracks})
                urlTab.append({'name':domain + ' {0} {1}'.format(lang, res), 'url':url})
        urlTab.reverse()
        return urlTab
        
    def parseVIMEOCOM(self, baseUrl):
        printDBG("parseVIMEOCOM baseUrl[%s]" % baseUrl)
        
        if 'player' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([0-9]+?)[/.]')[0]
            url = 'https://player.vimeo.com/video/' + video_id
        else:
            url = baseUrl
        sts, data = self.cm.getPage(url)
        if not sts: return False

        urlTab = []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'progressive', ']', False)[1]
        tmp = tmp.split('}')
        printDBG(tmp)
        for item in tmp:
            if 'video/mp4' not in item: continue
            quality = self.cm.ph.getSearchGroups(item, '''quality['"]?:['"]([^"^']+?)['"]''')[0]
            url  = self.cm.ph.getSearchGroups(item, '''url['"]?:['"]([^"^']+?)['"]''')[0]
            if url.startswith('http'):
                urlTab.append({'name':'vimeo.com {0}'.format(quality), 'url':url})
                
        hlsUrl = self.cm.ph.getSearchGroups(data, '"hls"[^}]+?"url"\:"([^"]+?)"')[0]
        tab = getDirectM3U8Playlist(hlsUrl)
        urlTab.extend(tab)
        
        return urlTab
        
    def parserDARKOMPLAYER(self, baseUrl):
        printDBG("parserDARKOMPLAYER baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')[1]
        tmp = unpackJSPlayerParams(tmp, TEAMCASTPL_decryptPlayerParams, type=0)
        data += tmp
        
        urlTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source ', '>', False, False)
        for item in data:
            type  = self.cm.ph.getSearchGroups(item, '''type=['"]([^"^']+?)['"]''')[0]
            res   = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
            label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
            url   = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            if 'mp4' not in type: continue
            if url.startswith('//'):
                url = 'http:' + url
            if self.cm.isValidUrl(url):
                url = urlparser.decorateUrl(url, {'Referer':baseUrl, 'User-Agent':'Mozilla/5.0'})
                urlTab.append({'name':'darkomplayer {0}: {1}'.format(label, res), 'url':url})
        return urlTab
        
    def parseJACVIDEOCOM(self, baseUrl):
        printDBG("parseJACVIDEOCOM baseUrl[%s]" % baseUrl)
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('jacvideocom.cookie')}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'jacvideosys(', ');', False)[1]
        tmp = data.split(',')[-1]
        link = self.cm.ph.getSearchGroups(tmp, '''link['"]?:['"]([^"^']+?)['"]''')[0]
        if link != '':
            post_data = {'link':link}
            sts, data = self.cm.getPage('http://www.jacvideo.com/embed/plugins/jacvideosys.php', params, post_data)
            if not sts: return False
            try:
                data = byteify(json.loads(data))
                if 'error' in data:
                    SetIPTVPlayerLastHostError(data['error'])
                linksTab = []
                for item in data['link']:
                    if item['type'] != 'mp4': continue
                    url  = item['link']
                    name = item['label']
                    url = urlparser.decorateUrl(url, {'iptv_livestream':False, 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl})
                    linksTab.append({'name':name, 'url':url})
                return linksTab
            except Exception:
                printExc()
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http[^"^']+?)["']''', 1, True)[0]
        try:
            linksTab = urlparser().getVideoLinkExt(url)
            if len(linksTab): return linksTab
        except Exception:
            printExc()
            
        urlTab = self._getSources(data)
        if len(urlTab): return urlTab
        return self._findLinks(data, contain='mp4')
        
    def parseSPEEDVICEONET(self, baseUrl):
        printDBG("parseSPEEDVICEONET baseUrl[%s]" % baseUrl)
        
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[/.]')[0]
            url = 'http://speedvideo.net/embed-{0}-600x360.html'.format(video_id)
        else:
            url = baseUrl
        
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        urlTab = []
        tmp = []
        for item in [('linkfile', 'normal'), ('linkfileBackup', 'backup'), ('linkfileBackupLq', 'low')]:
            try:
                a = re.compile('var\s+linkfile *= *"(.+?)"').findall(data)[0]
                b = re.compile('var\s+linkfile *= *base64_decode\(.+?\s+(.+?)\)').findall(data)[0]
                c = re.compile('var\s+%s *= *(\d*)' % b).findall(data)[0]
                vidUrl = a[:int(c)] + a[(int(c) + 10):]
                vidUrl = base64.b64decode(vidUrl)
                if vidUrl not in tmp:
                    tmp.append(vidUrl)
                    if vidUrl.split('?')[0].endswith('.m3u8'):
                        tab = getDirectM3U8Playlist(vidUrl)
                        urlTab.extend(tab)
                    else:
                        urlTab.append({'name':item[1], 'url':vidUrl})
            except Exception:
                continue
        return urlTab
        
    def parseXVIDSTAGECOM(self, baseUrl):
        printDBG("parseXVIDSTAGECOM baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        def _first_of_each(*sequences):
            return (next((x for x in sequence if x), '') for sequence in sequences)
        
        def _url_path_join(*parts):
            """Normalize url parts and join them with a slash."""
            schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
            scheme, netloc, query, fragment = _first_of_each(schemes, netlocs, queries, fragments)
            path = '/'.join(x.strip('/') for x in paths if x)
            return urlunsplit((scheme, netloc, path, query, fragment))
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data.split('site_logo')[-1], '<Form method="POST"', '</Form>', True)
        action = self.cm.ph.getSearchGroups(data, "action='([^']+?)'")[0]
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        
        try:
            sleep_time = int(self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]) 
            time.sleep(sleep_time)
        except Exception:
            printExc()
        if {} == post_data:
            post_data = None
        if action.startswith('/'):
            url = _url_path_join(url[:url.rfind('/')+1], action[1:])
        else: url = action
        if url == '':
            url = baseUrl
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return False
        
        try:
            tmp = CParsingHelper.getDataBeetwenMarkers(data.split('player_code')[-1], ">eval(", '</script>')[1]
            tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
            data = tmp + data
        except Exception:
            pass
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<[^>]+?type="video[^>]+?src="([^"]+?)"')[0]
        if videoUrl.startswith('http'):
            return videoUrl
        return False
        
    def parserSTREAMPLAYCC(self, baseUrl):
        printDBG("parserSTREAMPLAYCC baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if '/embed/' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{16})/')[0]
            url = 'http://www.streamplay.cc/embed/{0}'.format(video_id)
        else:
            url = baseUrl
        post_data = None
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER}, post_data)
        if not sts: return False
        data = CParsingHelper.getDataBeetwenMarkers(data, 'id="playerStream"', '</a>', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, 'href="(http[^"]+?)"')[0]
        if '' != videoUrl: return videoUrl
        return False
        
    def parserYOURVIDEOHOST(self, baseUrl):
        printDBG("parserSTREAMPLAYCC baseUrl[%s]" % baseUrl)
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        url = 'http://yourvideohost.com/{0}'.format(video_id)
        return self.__parseJWPLAYER_A(url, 'yourvideohost.com')
        
    def parserVIDGGTO(self, baseUrl):
        printDBG("parserVIDGGTO baseUrl[%s]" % baseUrl)
        return self._parserUNIVERSAL_B(baseUrl)
        
    def parserTINYCC(self, baseUrl):
        printDBG("parserTINYCC baseUrl[%s]" % baseUrl)
        query_data = { 'url': baseUrl, 'return_data': False }       
        response = self.cm.getURLRequestData(query_data)
        redirectUrl = response.geturl() 
        response.close()
        if baseUrl != redirectUrl:
            return urlparser().getVideoLinkExt(redirectUrl)
        return False
    
    def parserWHOLECLOUD(self, baseUrl):
        printDBG("parserWHOLECLOUD baseUrl[%s]" % baseUrl)
        
        params = {'header': {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'}, 'return_data':False}
        sts, response = self.cm.getPage(baseUrl, params)
        url = response.geturl()
        response.close()
        
        #url = baseUrl.replace('movshare.net', 'wholecloud.net')
        mobj = re.search(r'/(?:file|video)/(?P<id>[a-z\d]{13})', baseUrl)
        video_id = mobj.group('id')
        onlyDomain = urlparser.getDomain(url, True) 
        domain = urlparser.getDomain(url, False) 
        url = domain + 'video/' + video_id

        params['return_data'] = True
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
            
        try:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)[1]
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            post_data.update(tmp)
        except Exception:
            printExc()
            
        params['header'].update({'Content-Type':'application/x-www-form-urlencoded','Referer':url})
        sts, data = self.cm.getPage(url, params, post_data)
        if not sts: return False
        
        videoTab = []
        url = self.cm.ph.getSearchGroups(data, '"([^"]*?/download[^"]+?)"')[0]
        if url.startswith('/'):
            url = domain + url[1:]
        if self.cm.isValidUrl(url):
            url = strwithmeta(url, {'User-Agent':params['header']})
            videoTab.append({'name':'[Download] %s' % onlyDomain, 'url':url})
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player.ready', '}')[1]
        url = self.cm.ph.getSearchGroups(tmp, '''src['"\s]*?:\s['"]([^'^"]+?)['"]''')[0]
        if url.startswith('/'):
            url = domain + url[1:]
        if self.cm.isValidUrl(url) and url.split('?')[0].endswith('.mpd'):
            url = strwithmeta(url, {'User-Agent':params['header']})
            videoTab.extend(getMPDLinksWithMeta(url, False))
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
        links = []
        for item in tmp:
            if 'video/' not in item: continue
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0] 
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url):
                if url in links: continue
                links.append(url)
                url = strwithmeta(url, {'User-Agent':params['header']})
                videoTab.append({'name':'[%s] %s' % (type, onlyDomain), 'url':url})
                
        printDBG(data)
        return videoTab
        
    def parserSTREAM4KTO(self, baseUrl):
        printDBG("parserSTREAM4KTO baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        mainData = data
        
        data = self.cm.ph.getSearchGroups(data, "drdX_fx\('([^']+?)'\)")[0]
        data = drdX_fx( data )
        data = self.cm.ph.getSearchGroups(data, 'proxy.link=linkcdn%2A([^"]+?)"')[0]
        printDBG(data)
        if data != '':
            x = gledajfilmDecrypter(198,128)
            Key = "VERTR05uak80NEpDajY1ejJjSjY="
            data = x.decrypt(data, Key.decode('base64', 'strict'), "ECB")
            if '' != data:
                return urlparser().getVideoLinkExt(data)
            
        data = unpackJSPlayerParams(mainData, SAWLIVETV_decryptPlayerParams, 0)
        printDBG(">>>>>>>>>>>>>>>>>>>" + data)
        return self._findLinks(data)
        
    def parserONETTV(self, baseUrl):
        printDBG("parserONETTV baseUrl[%r]" % baseUrl )
        
        videoUrls = []
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return videoUrls
        ckmId = self.cm.ph.getSearchGroups(data, 'data-params-mvp="([^"]+?)"')[0]
        if '' == ckmId: ckmId = self.cm.ph.getSearchGroups(data, 'id="mvp:([^"]+?)"')[0]
        if '' == ckmId: return videoUrls
        
        tm = str(int(time.time() * 1000))
        jQ = str(randrange(562674473039806,962674473039806))
        authKey = 'FDF9406DE81BE0B573142F380CFA6043'
        hostName = urlparser().getHostName(baseUrl)
        contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D={0}&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_='.format(hostName) + tm
        sts, data = self.cm.getPage(contentUrl)
        if sts:
            try:
                printDBG(data)
                data = byteify( json.loads(data[data.find("(")+1:-2]) )
                data = data['result']['0']['formats']['wideo']
                for type in data:
                    for vidItem in data[type]:
                        if None != vidItem.get('drm_key', None): continue
                        vidUrl = vidItem.get('url', '')
                        if '' == vidUrl: continue
                        if 'hls' == type:
                            tmpTab = getDirectM3U8Playlist(vidUrl)
                            for tmp in tmpTab:
                                videoUrls.append({'name':'ONET type:%s :%s' % (type, tmp.get('bitrate', '0')), 'url':tmp['url']})
                        elif None != vidItem.get('video_bitrate', None):
                            videoUrls.append({'name':'ONET type:%s :%s' % (type, vidItem.get('video_bitrate', '0')), 'url':vidUrl})
                        elif None != vidItem.get('audio_bitrate', None):
                            videoUrls.append({'name':'ONET type:%s :%s' % (type, vidItem.get('audio_bitrate', '0')), 'url':vidUrl})
            except Exception:
                printExc()
        return videoUrls
        
    def paserBYETVORG(self, baseUrl):
        printDBG("paserBYETVORG baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        file = self.cm.ph.getSearchGroups(baseUrl, "file=([0-9]+?)[^0-9]")[0]
        if '' == file: file = self.cm.ph.getSearchGroups(baseUrl, "a=([0-9]+?)[^0-9]")[0]
        linkUrl = "http://www.byetv.org/embed.php?a={0}&id=&width=710&height=460&autostart=true&strech=".format(file)
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '"jwplayer1"', '</script>', False)
        if not sts: return False 
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, "'%s',[ ]*?'([^']+?)'" % name)[0] 
        
        swfUrl  = "http://p.jwpcdn.com/6/8/jwplayer.flash.swf"
        streamer = _getParam('streamer')
        file     = _getParam('file')
        token    = _getParam('token')
        provider = _getParam('provider')
        rtmpUrl  = provider + streamer[streamer.find(':'):]
        if '' != file and '' != rtmpUrl:
            rtmpUrl += ' playpath=file:%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, token, linkUrl)
            printDBG(rtmpUrl)
            return rtmpUrl
        return False
        
    def paserPUTLIVEIN(self, baseUrl):
        printDBG("paserPUTLIVEIN baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        file = self.cm.ph.getSearchGroups(baseUrl, "file=([0-9]+?)[^0-9]")[0]
        if '' == file: file = self.cm.ph.getSearchGroups(baseUrl+'/', "/e/([^/]+?)/")[0]
        
        linkUrl = "http://www.putlive.in/e/{0}".format(file)
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        #printDBG("=======================================================")
        #printDBG(data)
        #printDBG("=======================================================")
        token =  self.cm.ph.getSearchGroups(data, "'key' : '([^']+?)'")[0]
        if token != "": token = ' token=%s ' % token
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'unescape("', '")', False)
        if not sts: return False 
        data = urllib.unquote(data)
        #printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, "%s=([^&]+?)&" % name)[0] 
        
        swfUrl  = "http://putlive.in/player59.swf"
        streamer = _getParam('streamer')
        file     = _getParam('file')
        provider = _getParam('provider')
        rtmpUrl  = provider + streamer[streamer.find(':'):]
        if '' != file and '' != rtmpUrl:
            rtmpUrl += ' playpath=%s swfUrl=%s %s pageUrl=%s live=1 ' % (file, swfUrl, token, linkUrl)
            printDBG(rtmpUrl)
            return rtmpUrl
        return False
        
    def paserSTREAMLIVETO(self, baseUrl):
        printDBG("paserSTREAMLIVETO baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        defaultParams = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('streamliveto.cookie')}
        
        _url_re = re.compile("http(s)?://(\w+\.)?(ilive.to|streamlive.to)/.*/(?P<channel>\d+)")
        channel = _url_re.match(baseUrl).group("channel")
        
        linksTab = []
        linkUrl ='http://www.streamlive.to/view/%s' % channel
        
        for idx in [0]:
            params = dict(defaultParams)
            params.update({'header':{'header':HTTP_HEADER}})
            sts, data = self.cm.getPage(linkUrl, params)
            if not sts: return False 
            
            if '<div id="loginbox">' in data:
                SetIPTVPlayerLastHostError(_("Only logged in user have access.\nPlease set login data in the host configuration under blue button."))
            
            if 'get_free_credits' in data:
                msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_container">', '</a>')[1])
                if msg != '':
                    SetIPTVPlayerLastHostError(msg)
                
            if 0 == idx:
                linkUrl = self.cm.ph.getSearchGroups(data, 'popup\s*=\s*window\.open\(\s*"([^"]+?)"')[0]
        
        # get token
        token = CParsingHelper.getDataBeetwenMarkers(data, 'var token', '});', False)[1]
        token = self.cm.ph.getSearchGroups(token, '"([^"]+?/server.php[^"]+?)"')[0]
        if token.startswith('//'): token = 'http:' + token
        
        params = dict(defaultParams)
        HTTP_HEADER = dict(HTTP_HEADER)
        HTTP_HEADER['Referer'] = linkUrl
        params.update({'header':{'header':HTTP_HEADER}})
        sts, token = self.cm.getPage(token, params)
        if not sts: return False 
        TOKEN = byteify(json.loads(token))['token']
        if token != "": token = ' token=%s ' % TOKEN
        sts, token = self.cm.getPage('http://textuploader.com/ddf5v')
        if not sts: return False 
        token = self.cm.ph.getSearchGroups(token, 'description"\s*content="([^"]+?)"')[0]
        token = base64.b64decode(token)

        # get others params
        data = CParsingHelper.getDataBeetwenMarkers(data, '.setup(', '</script>', False)[1]
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]?%s['"]?[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0].replace('\\/', '/')
        
        swfUrl  = "http://www.streamlive.to/player/Player.swf"
        streamer = _getParam('streamer')
        file     = _getParam('file').replace('.flv', '')
        provider = _getParam('provider')
        rtmpUrl  = provider + streamer[streamer.find(':'):]
        if rtmpUrl.startswith('video://'):
            linksTab.append({'name':'http', 'url': rtmpUrl.replace('video://', 'http://')})
        elif '' != file and '' != rtmpUrl:
            printDBG("streamer[%s]" % streamer)
            parsed_uri = urlparse( streamer )
            printDBG("parsed_uri[%r]" % [parsed_uri])
            rtmpUrl    = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            app        = '{uri.path}'.format(uri=parsed_uri)[1:]
            if '' != parsed_uri.query: app += '?' + '{uri.query}'.format(uri=parsed_uri)
            rtmpUrl += ' playpath=%s swfUrl=%s token=%s live=1 pageUrl=%s app=%s tcUrl=%s conn=S:OK' % (file, swfUrl, token, linkUrl, app, streamer)
            printDBG(rtmpUrl)
            linksTab.append({'name':'rtmp', 'url': rtmpUrl})
        return linksTab
        
    def paserMEGOMTV(self, baseUrl):
        printDBG("paserMEGOMTV baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        
        id = self.cm.ph.getSearchGroups(baseUrl, "id=([^&]+?)&")[0]
        linkUrl = "http://distro.megom.tv/player-inside.php?id={0}&width=100%&height=450".format(id)
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<head>', 'var ad_data;', False)
        if not sts: return False 
        swfUrl = 'http://lds.megom.tv/jwplayer.flash.swf'
        a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
        b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
        c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
        d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
        f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
        v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
        
        rtmpUrl = ('rtmp://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) ) + v_part
        rtmpUrl += ' swfUrl=%s pageUrl=%s live=1 ' % (swfUrl, linkUrl)
        printDBG(rtmpUrl)
        return rtmpUrl
        
    def openload_substring(self, tmp, *args):
        if 2 == len(args):
            return tmp[args[0]:args[1]]
        elif 1 == len(args):
            return tmp[args[0]:]
        return ERROR_WRONG_SUBSTRING_PARAMS
        
    def openload_slice(self, tmp, *args):
        if 2 == len(args):
            return ord(tmp[args[0]:args[1]][0])
        elif 1 == len(args):
            return ord(tmp[args[0]:][0])
        return ERROR_WRONG_SLICE_PARAMS
        
    def parserOPENLOADIOExtractJS(self, fullAlgoCode, outFunNum, res):
        num = ''
        try:
            vGlobals = {"__builtins__": None, 'substring':self.openload_substring, 'slice':self.openload_slice, 'chr':chr, 'len':len}
            vLocals = { outFunNum: None }
            exec( fullAlgoCode, vGlobals, vLocals )
            num = vLocals[outFunNum](res)
            printDBG('parserOPENLOADIOExtractJS num[%s]' % num)
        except Exception:
            printExc('parserOPENLOADIOExtractJS exec code EXCEPTION')
        return num
        
    def parserOPENLOADIO(self, baseUrl):
        printDBG("parserOPENLOADIO baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl}
        
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Referer':baseUrl} #'Connection': 'keep-alive'           

        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        orgData = data
        
        if 'content-blocked' in data:
            msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<img class="image-blocked"', '</div>')[1]).strip()
            if msg == '': msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<p class="lead"', '</p>')[1]).strip()
            if msg == '': msg = _("We can't find the file you are looking for. It maybe got deleted by the owner or was removed due a copyright violation.")
            SetIPTVPlayerLastHostError(msg)
        
        subTracksData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track ', '>', False, False)
        subTracks = []
        for track in subTracksData:
            if 'kind="captions"' not in track: continue
            subUrl = self.cm.ph.getSearchGroups(track, 'src="([^"]+?)"')[0]
            if subUrl.startswith('/'):
                subUrl = 'http://openload.co' + subUrl
            if subUrl.startswith('http'):
                subLang = self.cm.ph.getSearchGroups(track, 'srclang="([^"]+?)"')[0]
                subLabel = self.cm.ph.getSearchGroups(track, 'label="([^"]+?)"')[0]
                subTracks.append({'title':subLabel + '_' + subLang, 'url':subUrl, 'lang':subLang, 'format':'srt'})
        
        # If you want to use the code for openload please at least put the info from were you take it:
        # for example: "Code take from plugin IPTVPlayer: "https://gitlab.com/iptvplayer-for-e2/iptvplayer-for-e2/"
        # It will be very nice if you send also email to me samsamsam@o2.pl and inform were this code will be used
        
        # start https://github.com/whitecream01/WhiteCream-V0.0.1/blob/master/plugin.video.uwc/plugin.video.uwc-1.0.51.zip?raw=true
        def decode(encoded):
            tab = encoded.split('\\')
            ret = ''
            for item in tab:
                try: ret += chr(int(item, 8))
                except Exception: 
                    ret += item
            return ret
        
        def base10toN(num,n):
            num_rep={10:'a', 11:'b',12:'c',13:'d',14:'e',15:'f',16:'g',17:'h',18:'i',19:'j',20:'k',21:'l',22:'m',23:'n',24:'o',25:'p',26:'q',27:'r',28:'s',29:'t',30:'u',31:'v',32:'w',33:'x',34:'y',35:'z'}
            new_num_string=''
            current=num
            while current!=0:
                remainder=current%n
                if 36>remainder>9:
                    remainder_string=num_rep[remainder]
                elif remainder>=36:
                    remainder_string='('+str(remainder)+')'
                else:
                    remainder_string=str(remainder)
                new_num_string=remainder_string+new_num_string
                current=current/n
            return new_num_string
        
        def decodeOpenLoad(aastring):
            # decodeOpenLoad made by mortael, please leave this line for proper credit :)
            #aastring = re.search(r"<video(?:.|\s)*?<script\s[^>]*?>((?:.|\s)*?)</script", html, re.DOTALL | re.IGNORECASE).group(1)
    
            aastring = aastring.replace("(ﾟДﾟ)[ﾟεﾟ]+(oﾟｰﾟo)+ ((c^_^o)-(c^_^o))+ (-~0)+ (ﾟДﾟ) ['c']+ (-~-~1)+","")
            aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ) + (ﾟΘﾟ))", "9")
            aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ))","8")
            aastring = aastring.replace("((ﾟｰﾟ) + (o^_^o))","7")
            aastring = aastring.replace("((c^_^o)-(c^_^o))","0")
            aastring = aastring.replace("((ﾟｰﾟ) + (ﾟΘﾟ))","5")
            aastring = aastring.replace("(ﾟｰﾟ)","4")
            aastring = aastring.replace("((o^_^o) - (ﾟΘﾟ))","2")
            aastring = aastring.replace("(o^_^o)","3")
            aastring = aastring.replace("(ﾟΘﾟ)","1")
            aastring = aastring.replace("(+!+[])","1")
            aastring = aastring.replace("(c^_^o)","0")
            aastring = aastring.replace("(0+0)","0")
            aastring = aastring.replace("(ﾟДﾟ)[ﾟεﾟ]","\\")  
            aastring = aastring.replace("(3 +3 +0)","6")
            aastring = aastring.replace("(3 - 1 +0)","2")
            aastring = aastring.replace("(!+[]+!+[])","2")
            aastring = aastring.replace("(-~-~2)","4")
            aastring = aastring.replace("(-~-~1)","3")
            aastring = aastring.replace("(-~0)","1")
            aastring = aastring.replace("(-~1)","2")
            aastring = aastring.replace("(-~3)","4")
            aastring = aastring.replace("(0-0)","0")
            
            aastring = aastring.replace("(ﾟДﾟ).ﾟωﾟﾉ","10")
            aastring = aastring.replace("(ﾟДﾟ).ﾟΘﾟﾉ","11")
            aastring = aastring.replace("(ﾟДﾟ)[\'c\']","12")
            aastring = aastring.replace("(ﾟДﾟ).ﾟｰﾟﾉ","13")
            aastring = aastring.replace("(ﾟДﾟ).ﾟДﾟﾉ","14")
            aastring = aastring.replace("(ﾟДﾟ)[ﾟΘﾟ]","15")

            decodestring = re.search(r"\\\+([^(]+)", aastring, re.DOTALL | re.IGNORECASE).group(1)
            decodestring = "\\+"+ decodestring
            decodestring = decodestring.replace("+","")
            decodestring = decodestring.replace(" ","")

            decodestring = decode(decodestring)
            decodestring = decodestring.replace("\\/","/")
            
            if 'toString' in decodestring:
                base = re.compile(r"toString\(a\+(\d+)", re.DOTALL | re.IGNORECASE).findall(decodestring)[0]
                base = int(base)
                match = re.compile(r"(\(\d[^)]+\))", re.DOTALL | re.IGNORECASE).findall(decodestring)
                for repl in match:
                    match1 = re.compile(r"(\d+),(\d+)", re.DOTALL | re.IGNORECASE).findall(repl)
                    base2 = base + int(match1[0][0])
                    repl2 = base10toN(int(match1[0][1]),base2)
                    decodestring = decodestring.replace(repl,repl2)
                decodestring = decodestring.replace("+","")
                decodestring = decodestring.replace("\"","")
            return decodestring
        
        preDataTab = self.cm.ph.getAllItemsBeetwenMarkers(data, 'a="0%', '{}', withMarkers=True, caseSensitive=False)
        for item in preDataTab:
            try:
                dat = self.cm.ph.getSearchGroups(item, 'a\s*?=\s*?"([^"]+?)"', ignoreCase=True)[0]
                z = self.cm.ph.getSearchGroups(item, '\}\(([0-9]+?)\)', ignoreCase=True)[0]
                z = int(z)
                def checkA(c):
                    code = ord(c.group(1))
                    if code <= ord('Z'):
                        tmp = 90
                    else: 
                        tmp = 122
                    c = code + z
                    if tmp < c:
                        c -= 26
                    return chr(c)
                    
                dat = urllib.unquote( re.sub('([a-zA-Z])', checkA, dat) )
                dat = OPENLOADIO_decryptPlayerParams(dat, 4, 4, ['j', '_', '__', '___'], 0, {})
                data += dat
            except Exception:
                printExc()
        
        videoUrl = ''
        tmp = ''
        encodedData = self.cm.ph.getAllItemsBeetwenMarkers(data, 'ﾟωﾟ', '</script>', withMarkers=False, caseSensitive=False)
        for item in encodedData:
            tmpEncodedData = item.split('┻━┻')
            for tmpItem in tmpEncodedData:
                try:
                    tmp += decodeOpenLoad(tmpItem)
                except Exception:
                    printExc()
        
        tmp2 = ''
        encodedData = self.cm.ph.getAllItemsBeetwenMarkers(data, "j=~[];", "())();", withMarkers=True, caseSensitive=False)
        for item in encodedData:
            try:
                if '' != item:
                    tmp2 += JJDecoder(item).decode()
            except Exception:
                printExc()
        
        printDBG('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        printDBG(tmp)
        printDBG('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
        printDBG(tmp2)
        printDBG('CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC')
        
        ##########################################################
        # new algo 2016-12-04 ;)
        ##########################################################
        varName = self.cm.ph.getSearchGroups(tmp, '''window.r=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
        encTab = re.compile('''<span[^>]+?id="%s[^"]*?"[^>]*?>([^<]+?)<\/span>''' % varName).findall(data)
        printDBG(">>>>>>>>>>>> varName[%s] encTab[%s]" % (varName, encTab) )
        
        if varName == '':
            for e in encTab:
                if len(e) > 40:
                    encTab.insert(0, e)
                    break
        
        def __decode_k(enc, jscode):
            decoded = ''
            tmpPath = ''
            try:
                jscode = base64.b64decode('''ICAgICAgICAgICAgICAgICAgICB2YXIgaWQgPSAiJXMiDQogICAgICAgICAgICAgICAgICAgICAgLCBkZWNvZGVkDQogICAgICAgICAgICAgICAgICAgICAgLCBkb2N1bWVudCA9IHt9DQogICAgICAgICAgICAgICAgICAgICAgLCB3aW5kb3cgPSB0aGlzDQogICAgICAgICAgICAgICAgICAgICAgLCAkID0gZnVuY3Rpb24oKXsNCiAgICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIHsNCiAgICAgICAgICAgICAgICAgICAgICAgICAgICB0ZXh0OiBmdW5jdGlvbihhKXsNCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmKGEpDQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGRlY29kZWQgPSBhOw0KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZWxzZQ0KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gaWQ7DQogICAgICAgICAgICAgICAgICAgICAgICAgICAgfSwNCiAgICAgICAgICAgICAgICAgICAgICAgICAgICByZWFkeTogZnVuY3Rpb24oYSl7DQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBhKCkNCiAgICAgICAgICAgICAgICAgICAgICAgICAgICB9DQogICAgICAgICAgICAgICAgICAgICAgICAgIH0NCiAgICAgICAgICAgICAgICAgICAgICAgIH07DQogICAgICAgICAgICAgICAgICAgIChmdW5jdGlvbihkLCB3KXsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgZiA9IGZ1bmN0aW9uKCl7fTsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgcyA9ICcnOw0KICAgICAgICAgICAgICAgICAgICAgIHZhciBvID0gbnVsbDsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgYiA9IGZhbHNlOw0KICAgICAgICAgICAgICAgICAgICAgIHZhciBuID0gMDsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgZGYgPSBbJ2Nsb3NlJywnY3JlYXRlQXR0cmlidXRlJywnY3JlYXRlRG9jdW1lbnRGcmFnbWVudCcsJ2NyZWF0ZUVsZW1lbnQnLCdjcmVhdGVFbGVtZW50TlMnLCdjcmVhdGVFdmVudCcsJ2NyZWF0ZU5TUmVzb2x2ZXInLCdjcmVhdGVSYW5nZScsJ2NyZWF0ZVRleHROb2RlJywnY3JlYXRlVHJlZVdhbGtlcicsJ2V2YWx1YXRlJywnZXhlY0NvbW1hbmQnLCdnZXRFbGVtZW50QnlJZCcsJ2dldEVsZW1lbnRzQnlOYW1lJywnZ2V0RWxlbWVudHNCeVRhZ05hbWUnLCdpbXBvcnROb2RlJywnb3BlbicsJ3F1ZXJ5Q29tbWFuZEVuYWJsZWQnLCdxdWVyeUNvbW1hbmRJbmRldGVybScsJ3F1ZXJ5Q29tbWFuZFN0YXRlJywncXVlcnlDb21tYW5kVmFsdWUnLCd3cml0ZScsJ3dyaXRlbG4nXTsNCiAgICAgICAgICAgICAgICAgICAgICBkZi5mb3JFYWNoKGZ1bmN0aW9uKGUpe2RbZV09Zjt9KTsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgZG9fID0gWydhbmNob3JzJywnYXBwbGV0cycsJ2JvZHknLCdkZWZhdWx0VmlldycsJ2RvY3R5cGUnLCdkb2N1bWVudEVsZW1lbnQnLCdlbWJlZHMnLCdmaXJzdENoaWxkJywnZm9ybXMnLCdpbWFnZXMnLCdpbXBsZW1lbnRhdGlvbicsJ2xpbmtzJywnbG9jYXRpb24nLCdwbHVnaW5zJywnc3R5bGVTaGVldHMnXTsNCiAgICAgICAgICAgICAgICAgICAgICBkb18uZm9yRWFjaChmdW5jdGlvbihlKXtkW2VdPW87fSk7DQogICAgICAgICAgICAgICAgICAgICAgdmFyIGRzID0gWydVUkwnLCdjaGFyYWN0ZXJTZXQnLCdjb21wYXRNb2RlJywnY29udGVudFR5cGUnLCdjb29raWUnLCdkZXNpZ25Nb2RlJywnZG9tYWluJywnbGFzdE1vZGlmaWVkJywncmVmZXJyZXInLCd0aXRsZSddOw0KICAgICAgICAgICAgICAgICAgICAgIGRzLmZvckVhY2goZnVuY3Rpb24oZSl7ZFtlXT1zO30pOw0KICAgICAgICAgICAgICAgICAgICAgIHZhciB3YiA9IFsnY2xvc2VkJywnaXNTZWN1cmVDb250ZXh0J107DQogICAgICAgICAgICAgICAgICAgICAgd2IuZm9yRWFjaChmdW5jdGlvbihlKXt3W2VdPWI7fSk7DQogICAgICAgICAgICAgICAgICAgICAgdmFyIHdmID0gWydhZGRFdmVudExpc3RlbmVyJywnYWxlcnQnLCdhdG9iJywnYmx1cicsJ2J0b2EnLCdjYW5jZWxBbmltYXRpb25GcmFtZScsJ2NhcHR1cmVFdmVudHMnLCdjbGVhckludGVydmFsJywnY2xlYXJUaW1lb3V0JywnY2xvc2UnLCdjb25maXJtJywnY3JlYXRlSW1hZ2VCaXRtYXAnLCdkaXNwYXRjaEV2ZW50JywnZmV0Y2gnLCdmaW5kJywnZm9jdXMnLCdnZXRDb21wdXRlZFN0eWxlJywnZ2V0U2VsZWN0aW9uJywnbWF0Y2hNZWRpYScsJ21vdmVCeScsJ21vdmVUbycsJ29wZW4nLCdwb3N0TWVzc2FnZScsJ3Byb21wdCcsJ3JlbGVhc2VFdmVudHMnLCdyZW1vdmVFdmVudExpc3RlbmVyJywncmVxdWVzdEFuaW1hdGlvbkZyYW1lJywncmVzaXplQnknLCdyZXNpemVUbycsJ3Njcm9sbCcsJ3Njcm9sbEJ5Jywnc2Nyb2xsVG8nLCdzZXRJbnRlcnZhbCcsJ3NldFRpbWVvdXQnLCdzdG9wJ107DQogICAgICAgICAgICAgICAgICAgICAgd2YuZm9yRWFjaChmdW5jdGlvbihlKXt3W2VdPWY7fSk7DQogICAgICAgICAgICAgICAgICAgICAgdmFyIHduID0gWydkZXZpY2VQaXhlbFJhdGlvJywnaW5uZXJIZWlnaHQnLCdpbm5lcldpZHRoJywnbGVuZ3RoJywnb3V0ZXJIZWlnaHQnLCdvdXRlcldpZHRoJywncGFnZVhPZmZzZXQnLCdwYWdlWU9mZnNldCcsJ3NjcmVlblgnLCdzY3JlZW5ZJywnc2Nyb2xsWCcsJ3Njcm9sbFknXTsNCiAgICAgICAgICAgICAgICAgICAgICB3bi5mb3JFYWNoKGZ1bmN0aW9uKGUpe3dbZV09bjt9KTsNCiAgICAgICAgICAgICAgICAgICAgICB2YXIgd28gPSBbJ2FwcGxpY2F0aW9uQ2FjaGUnLCdjYWNoZXMnLCdjcnlwdG8nLCdleHRlcm5hbCcsJ2ZyYW1lRWxlbWVudCcsJ2ZyYW1lcycsJ2hpc3RvcnknLCdpbmRleGVkREInLCdsb2NhbFN0b3JhZ2UnLCdsb2NhdGlvbicsJ2xvY2F0aW9uYmFyJywnbWVudWJhcicsJ25hdmlnYXRvcicsJ29uYWJvcnQnLCdvbmFuaW1hdGlvbmVuZCcsJ29uYW5pbWF0aW9uaXRlcmF0aW9uJywnb25hbmltYXRpb25zdGFydCcsJ29uYmVmb3JldW5sb2FkJywnb25ibHVyJywnb25jYW5wbGF5Jywnb25jYW5wbGF5dGhyb3VnaCcsJ29uY2hhbmdlJywnb25jbGljaycsJ29uY29udGV4dG1lbnUnLCdvbmRibGNsaWNrJywnb25kZXZpY2Vtb3Rpb24nLCdvbmRldmljZW9yaWVudGF0aW9uJywnb25kcmFnJywnb25kcmFnZW5kJywnb25kcmFnZW50ZXInLCdvbmRyYWdsZWF2ZScsJ29uZHJhZ292ZXInLCdvbmRyYWdzdGFydCcsJ29uZHJvcCcsJ29uZHVyYXRpb25jaGFuZ2UnLCdvbmVtcHRpZWQnLCdvbmVuZGVkJywnb25lcnJvcicsJ29uZm9jdXMnLCdvbmhhc2hjaGFuZ2UnLCdvbmlucHV0Jywnb25pbnZhbGlkJywnb25rZXlkb3duJywnb25rZXlwcmVzcycsJ29ua2V5dXAnLCdvbmxhbmd1YWdlY2hhbmdlJywnb25sb2FkJywnb25sb2FkZWRkYXRhJywnb25sb2FkZWRtZXRhZGF0YScsJ29ubG9hZHN0YXJ0Jywnb25tZXNzYWdlJywnb25tb3VzZWRvd24nLCdvbm1vdXNlZW50ZXInLCdvbm1vdXNlbGVhdmUnLCdvbm1vdXNlbW92ZScsJ29ubW91c2VvdXQnLCdvbm1vdXNlb3ZlcicsJ29ubW91c2V1cCcsJ29ub2ZmbGluZScsJ29ub25saW5lJywnb25wYWdlaGlkZScsJ29ucGFnZXNob3cnLCdvbnBhdXNlJywnb25wbGF5Jywnb25wbGF5aW5nJywnb25wb3BzdGF0ZScsJ29ucHJvZ3Jlc3MnLCdvbnJhdGVjaGFuZ2UnLCdvbnJlc2V0Jywnb25yZXNpemUnLCdvbnNjcm9sbCcsJ29uc2Vla2VkJywnb25zZWVraW5nJywnb25zZWxlY3QnLCdvbnNob3cnLCdvbnN0YWxsZWQnLCdvbnN0b3JhZ2UnLCdvbnN1Ym1pdCcsJ29uc3VzcGVuZCcsJ29udGltZXVwZGF0ZScsJ29udG9nZ2xlJywnb250cmFuc2l0aW9uZW5kJywnb251bmxvYWQnLCdvbnZvbHVtZWNoYW5nZScsJ29ud2FpdGluZycsJ29ud2Via2l0YW5pbWF0aW9uZW5kJywnb253ZWJraXRhbmltYXRpb25pdGVyYXRpb24nLCdvbndlYmtpdGFuaW1hdGlvbnN0YXJ0Jywnb253ZWJraXR0cmFuc2l0aW9uZW5kJywnb253aGVlbCcsJ29wZW5lcicsJ3BhcmVudCcsJ3BlcmZvcm1hbmNlJywncGVyc29uYWxiYXInLCdzY3JlZW4nLCdzY3JvbGxiYXJzJywnc2VsZicsJ3Nlc3Npb25TdG9yYWdlJywnc3BlZWNoU3ludGhlc2lzJywnc3RhdHVzYmFyJywndG9vbGJhcicsJ3RvcCddOw0KICAgICAgICAgICAgICAgICAgICAgIHdvLmZvckVhY2goZnVuY3Rpb24oZSl7d1tlXT1vO30pOw0KICAgICAgICAgICAgICAgICAgICAgIHZhciB3cyA9IFsnbmFtZSddOw0KICAgICAgICAgICAgICAgICAgICAgIHdzLmZvckVhY2goZnVuY3Rpb24oZSl7d1tlXT1zO30pOw0KICAgICAgICAgICAgICAgICAgICB9KShkb2N1bWVudCwgd2luZG93KTsNCiAgICAgICAgICAgICAgICAgICAgJXM7DQogICAgICAgICAgICAgICAgICAgIHByaW50KGRlY29kZWQpOw==''') % (enc, jscode)                     
                printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
                printDBG(jscode)
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                ret = iptv_js_execute( jscode )
                if ret['sts'] and 0 == ret['code']:
                    decoded = ret['data'].strip()
                    printDBG('DECODED DATA -> [%s]' % decoded)
            except Exception:
                printExc()
            #rm(tmpPath)
            return decoded
        
        marker = 'ﾟωﾟﾉ= /｀ｍ´）ﾉ'
        orgData = marker + self.cm.ph.getDataBeetwenMarkers(orgData, marker, marker, False)[1]
        orgData = re.sub('''if\s*\([^\}]+?typeof[^\}]+?\}''', '', orgData)
        orgData = re.sub('''if\s*\([^\}]+?document[^\}]+?\}''', '', orgData)
        dec = __decode_k(encTab[0], orgData)
        
        videoUrl = 'https://openload.co/stream/{0}?mime=true'.format(dec)
        params = dict(HTTP_HEADER)
        params['external_sub_tracks'] = subTracks
        return urlparser.decorateUrl(videoUrl, params)
        ##########################################################
        # new algo 2016-12-04 end ;)
        ##########################################################
        
        # new algo
        varName = self.cm.ph.getSearchGroups(tmp2+tmp, '''=\s*([^.^;^{^}]+)\s*\.charCodeAt''', ignoreCase=True)[0]
        printDBG('varName: [%s]' % varName)
        hiddenUrlName = self.cm.ph.getSearchGroups(tmp2+tmp, '''var\s*%s\s*=[^"^;]+?"\#([^"]+?)"\)\.text\(\)''' % varName, ignoreCase=True)[0]
        linkData = self.cm.ph.getSearchGroups(data, '''<span[^>]+?id="%s"[^>]*?>([^<]+?)<\/span>''' % hiddenUrlName, ignoreCase=True)[0].strip()
        printDBG("=======================linkData=============================")
        printDBG(linkData)
        printDBG("============================================================")
        linkData = clean_html(linkData).strip()
        res = ""
        magic = ord(linkData[-1])
        for item in linkData:
            c = ord(item)
            if c >= 33 and c <= 126:
                c = ((c + 14) % 94) + 33
            res += chr(c)
        
        tmp = tmp2+tmp
        
        # get function names
        pyCode = ''
        functionNamesTab = re.compile('function\s+([^\(]+?)\s*\(\)').findall(tmp)
        for item in functionNamesTab:
            funBody = self.cm.ph.getDataBeetwenMarkers(tmp, 'function ' + item.strip(), '}', False)[1]
            funBody = self.cm.ph.getDataBeetwenMarkers(funBody, 'return', ';', False)[1].strip()
            
            pyCode += '\ndef %s():\n' % item
            pyCode += '\treturn ' + funBody
        
        num = self.cm.ph.getSearchGroups(tmp, 'var\s*str\s*=([^;]+?;)', ignoreCase=True)[0].strip()
        num = num.replace('String.fromCharCode', 'chr')
        num = num.replace('.charCodeAt(0)', '')
        num = num.replace('tmp.slice(', 'slice(tmp,')
        num = num.replace('tmp.length', 'len(tmp)')
        num = num.replace('tmp.substring(', 'substring(tmp, ')
        
        algoLines = pyCode.split('\n')
        for i in range(len(algoLines)):
            algoLines[i] = '\t' + algoLines[i]
        fullAlgoCode  = 'def openload_get_num(tmp):'
        fullAlgoCode += '\n'.join(algoLines)
        fullAlgoCode += '\n\treturn %s' % num
        fullAlgoCode += '\noutGetNum = openload_get_num\n'
        
        printDBG("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
        printDBG(fullAlgoCode)
        printDBG("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
        
        res = self.parserOPENLOADIOExtractJS(fullAlgoCode, 'outGetNum', res)
        if res == '': return False
        
        videoUrl = 'https://openload.co/stream/{0}?mime=true'.format(res)
        if '' == videoUrl: return False
        params = dict(HTTP_HEADER)
        params['external_sub_tracks'] = subTracks
        return urlparser.decorateUrl(videoUrl, params)
        
    def parserGAMETRAILERS(self, baseUrl):
        printDBG("parserGAMETRAILERS baseUrl[%r]" % baseUrl )
        list = GametrailersIE()._real_extract(baseUrl)[0]['formats']
        
        for idx in range(len(list)):
            width   = int(list[idx].get('width', 0))
            height  = int(list[idx].get('height', 0))
            bitrate = int(list[idx].get('bitrate', 0))
            if 0 != width or 0 != height:
                name = '%sx%s' % (width, height)
            elif 0 != bitrate:
                name = 'bitrate %s' % (bitrate)
            else:
                name = '%s.' % (idx + 1)
            list[idx]['name'] = name
        return list
        
    def parserVEVO(self, baseUrl):
        printDBG("parserVEVO baseUrl[%r]" % baseUrl )
        videoUrls = self.getVevoIE()._real_extract(baseUrl)['formats']
        
        for idx in range(len(videoUrls)):
            width   = int(videoUrls[idx].get('width', 0))
            height  = int(videoUrls[idx].get('height', 0))
            bitrate = int(videoUrls[idx].get('bitrate', 0)) / 8
            name = ''
            if 0 != bitrate:
                name = 'bitrate %s' % (formatBytes(bitrate, 0).replace('.0', '')+'/s')
            if 0 != width or 0 != height:
                name += ' %sx%s' % (width, height)
            if '' == name:
                name = '%s.' % (idx + 1)
            videoUrls[idx]['name'] = name
        if 0 < len(videoUrls):
            max_bitrate = int(config.plugins.iptvplayer.vevo_default_quality.value)
            def __getLinkQuality( itemLink ):
                return int(itemLink['bitrate'])
            videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.vevo_use_default_quality.value:
                videoUrls = [videoUrls[0]]
        return videoUrls
        
    def parserBBC(self, baseUrl):
        printDBG("parserBBC baseUrl[%r]" % baseUrl )
        
        vpid = self.cm.ph.getSearchGroups(baseUrl, '/vpid/([^/]+?)/')[0]
        
        if vpid == '':
            data = self.getBBCIE()._real_extract(baseUrl)
        else:
            formats, subtitles = self.getBBCIE()._download_media_selector(vpid)
            data = {'formats':formats, 'subtitles':subtitles}
        
        subtitlesTab = []
        for sub in data.get('subtitles', []):
            if self.cm.isValidUrl(sub.get('url', '')):
                subtitlesTab.append({'title':_(sub['lang']), 'url':sub['url'], 'lang':sub['lang'], 'format':sub['ext']})
        
        videoUrls = []
        hlsLinks = []
        mpdLinks = []
        for vidItem in data['formats']:
            url = self.getBBCIE().getFullUrl(vidItem['url'].replace('&amp;', '&'))
            if vidItem['ext'] == 'hls' and 0 == len(hlsLinks):
                hlsLinks.extend(getDirectM3U8Playlist(url, False, checkContent=True))
            elif vidItem['ext'] == 'mpd' and 0 == len(mpdLinks):
                mpdLinks.extend(getMPDLinksWithMeta(url, False))
        
        tmpTab = [hlsLinks, mpdLinks]
        
        if config.plugins.iptvplayer.bbc_prefered_format.value == 'dash':
            tmpTab.reverse()
        
        max_bitrate = int(config.plugins.iptvplayer.bbc_default_quality.value)
        for item in tmpTab:
            def __getLinkQuality( itemLink ):
                try: return int(itemLink['height'])
                except Exception: return 0
            item = CSelOneLink(item, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.bbc_use_default_quality.value:
                videoUrls.append(item[0])
                break
            videoUrls.extend(item)
        
        if len(subtitlesTab):
            for idx in range(len(videoUrls)):
                videoUrls[idx]['url'] = strwithmeta(videoUrls[idx]['url'], {'external_sub_tracks':subtitlesTab})
        
        return videoUrls
        
    def parserSHAREDSX(self, baseUrl):
        printDBG("parserSHAREDSX baseUrl[%r]" % baseUrl )
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/shared.py
        sts, data = self.cm.getPage(baseUrl)

        if '>File does not exist<' in data:
            SetIPTVPlayerLastHostError('Video %s does not exist' % baseUrl)
            return False

        data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False)[1]
        data = re.compile('name="([^"]+?)"[^>]*?value="([^"]+?)"').findall(data)
        post_data = dict(data)
        sts, data = self.cm.getPage(baseUrl, {'header':self.HTTP_HEADER}, post_data)
        if not sts: return False        
            
        videoUrl = self.cm.ph.getSearchGroups(data, 'data-url="([^"]+)"')[0]
        if videoUrl.startswith('http'): return videoUrl
        return False
        
    def parserPOSIEDZEPL(self, baseUrl):
        printDBG("parserPOSIEDZEPL baseUrl[%r]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if '/e.' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{10})[/.?]')[0]
            url = 'http://e.posiedze.pl/' + video_id
        else:
            url = baseUrl
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, """["']*file["']*[ ]*?:[ ]*?["']([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserNEODRIVECO(self, baseUrl):
        printDBG("parserNEODRIVECO baseUrl[%r]" % baseUrl)
        #http://neodrive.co/embed/EG0F2UYFNR2CN1CUDNT2I5OPN/
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, """["']*vurl["']*[ ]*?=[ ]*?["']([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserMIPLAYERNET(self, baseUrl):
        printDBG("parserMIPLAYERNET baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        url2 = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http://miplayer.net[^"^']+?)["']''', 1, True)[0]
        if url2 != '':
            sts, data = self.cm.getPage(url2, {'header':HTTP_HEADER})
            if not sts: return False
        
        curl = self.cm.ph.getSearchGroups(data, '''curl[ ]*?=[ ]*?["']([^"^']+?)["']''', 1, True)[0]
        curl = base64.b64decode(curl)
        if curl.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(curl, checkExt=False)
        elif curl.startswith('rtmp'):
            swfUrl = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
            curl += ' swfUrl=%s pageUrl=%s token=OOG17t.x#K9Vh#| ' % (swfUrl, url2)
            #curl += ' token=OOG17t.x#K9Vh#| '
            return curl
        return False
        
    def parserYOCASTTV(self, baseUrl):
        printDBG("parserYOCASTTV baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?swf)['"]''')[0]
        url    = self.cm.ph.getSearchGroups(data, '''streamer[^'^"]*?['"](rtmp[^'^"]+?)['"]''')[0]
        file   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0].replace('.flv', '')
        if '' != file and '' != url:
            url += ' playpath=%s swfVfy=%s pageUrl=%s ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserSOSTARTORG(self, baseUrl):
        printDBG("parserSOSTARTORG baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = 'http://sostart.org/jw/jwplayer.flash.swf'
        url    = ''
        file   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        url += file
        if '' != file and '' != url:
            url += ' swfVfy=%s pageUrl=%s ' % (swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserSOSTARTPW(self, baseUrl):
        printDBG("parserSOSTARTPW baseUrl[%r]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        jsonUrl = self.cm.ph.getSearchGroups(data, '''getJSON\([^"^']*?['"]([^"^']+?)['"]''')[0]
        if not jsonUrl.startswith('http'): return False
        
        if 'chunklist.m3u8' in data:
            hlsStream = True
        sts, data = self.cm.getPage(jsonUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        data = byteify(json.loads(data))
        if hlsStream:
            Referer = 'http://api.peer5.com/jwplayer6/assets/jwplayer.flash.swf'
            hlsUrl = data['rtmp']+"/"+data['streamname']+"/chunklist.m3u8"
            hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':Referer})
            return getDirectM3U8Playlist(hlsUrl)
        return False
        
    def parserLIVEONLINETV247(self, baseUrl):
        printDBG("parserLIVEONLINETV247 baseUrl[%r]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        hlsUrl = self.cm.ph.getSearchGroups(data, '''<source\s+?type="application/x-mpegurl"\s+?src=["'](http[^'^"]+?)["']''')[0]
        if hlsUrl == '': return False
        return getDirectM3U8Playlist(hlsUrl)
        return False
        
    def parseBROADCAST(self, baseUrl):
        printDBG("parseBROADCAST baseUrl[%r]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('broadcast.cookie')}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        curl = self.cm.ph.getSearchGroups(data, '''curl[^"^']*?=[^"^']*?['"]([^"^']+?)['"]''')[0]
        curl = base64.b64decode(curl)
        if not curl.startswith('http'): return False
        
        params['header']['Referer'] = baseUrl
        params['header']['X-Requested-With'] = 'XMLHttpRequest'
        sts, data = self.cm.getPage(self.cm.getBaseUrl(baseUrl) + 'getToken.php', params)
        if not sts: return False
        printDBG(data)
        data = byteify(json.loads(data))
        Referer = 'http://cdn.allofme.site/jw/jwplayer.flash.swf'
        hlsUrl = curl + data['token']
        hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':Referer})
        return getDirectM3U8Playlist(hlsUrl)
    
    def parserGOODRTMP(self, baseUrl):
        printDBG("parserGOODRTMP baseUrl[%r]" % baseUrl)
        SetIPTVPlayerLastHostError('Links from "goodrtmp.com" not supported.')
        return False
        
    def parserLIFERTMP(self, baseUrl):
        printDBG("parserGOODRTMP baseUrl[%r]" % baseUrl)
        SetIPTVPlayerLastHostError('Links from "life-rtmp.com" not supported.')
        return False
    
    def parserTHEACTIONLIVE(self, baseUrl):
        printDBG("parserTHEACTIONLIVE baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        baseUrl = strwithmeta(baseUrl, {'Referer':baseUrl})
        return urlparser().getAutoDetectedStreamLink(baseUrl, data)
        
    def parserBIGGESTPLAYER(self, baseUrl):
        printDBG("parserBIGGESTPLAYER baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', '}', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        return getDirectM3U8Playlist(url)
        
    def parserLIVEONLINE247(self, baseUrl):
        printDBG("parserLIVEONLINE247 baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?swf)['"]''')[0]
        if swfUrl == '':
            swfUrl = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
        url   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        if url.startswith('rtmp'):
            url += ' swfVfy=%s pageUrl=%s ' % (swfUrl, baseUrl)
            printDBG(url)
            return url
        else:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'source:', '}', False)[1]
            url = self.cm.ph.getSearchGroups(data, '''hls[^'^"]*?['"]([^'^"]+?)['"]''')[0]
            return getDirectM3U8Playlist(url)
        return False
        
    def parserFILEPUPNET(self, baseUrl):
        printDBG("parserFILEPUPNET baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'window.onload', '</script>', False)[1]
        qualities = self.cm.ph.getSearchGroups(data, 'qualities:[ ]*?\[([^\]]+?)\]')[0]
        qualities = self.cm.ph.getAllItemsBeetwenMarkers(qualities, '"', '"', False)
        defaultQuality = self.cm.ph.getSearchGroups(data, 'defaultQuality:[ ]*?"([^"]+?)"')[0]
        qualities.remove(defaultQuality)
        
        sub_tracks = []
        subData = self.cm.ph.getDataBeetwenMarkers(data, 'subtitles:', ']', False)[1].split('}')
        for item in subData:
            if '"subtitles"' in item:
                label   = self.cm.ph.getSearchGroups(item, 'label:[ ]*?"([^"]+?)"')[0]
                srclang = self.cm.ph.getSearchGroups(item, 'srclang:[ ]*?"([^"]+?)"')[0]
                src     = self.cm.ph.getSearchGroups(item, 'src:[ ]*?"([^"]+?)"')[0]
                if not src.startswith('http'): continue
                sub_tracks.append({'title':label, 'url':src, 'lang':srclang, 'format':'srt'})
        
        printDBG(">>>>>>>>>>>>>>>>> sub_tracks[%s]\n[%s]" % (sub_tracks, subData))
        
        linksTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
        defaultUrl = self.cm.ph.getSearchGroups(data, '"(http[^"]+?)"')[0]
        linksTab.append({'name':defaultQuality, 'url': strwithmeta(defaultUrl, {'Referer':'baseUrl', 'external_sub_tracks':sub_tracks})})
        for item in qualities:
            if '.mp4' in defaultUrl:
                url = defaultUrl.replace('.mp4', '-%s.mp4' % item)
                linksTab.append({'name':item, 'url': strwithmeta(url, {'Referer':'baseUrl', 'external_sub_tracks':sub_tracks})})
        return linksTab
        
    def parserHDFILMSTREAMING(self, baseUrl):
        printDBG("parserHDFILMSTREAMING baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        sub_tracks = []
        subData = self.cm.ph.getDataBeetwenMarkers(data, 'tracks:', ']', False)[1].split('}')
        for item in subData:
            if '"captions"' in item:
                label   = self.cm.ph.getSearchGroups(item, 'label:[ ]*?"([^"]+?)"')[0]
                src     = self.cm.ph.getSearchGroups(item, 'file:[ ]*?"([^"]+?)"')[0]
                if not src.startswith('http'): continue
                sub_tracks.append({'title':label, 'url':src, 'lang':'unk', 'format':'srt'})
        
        linksTab = self._findLinks(data, serverName='hdfilmstreaming.com')
        for idx in range(len(linksTab)):
            linksTab[idx]['url'] = urlparser.decorateUrl(linksTab[idx]['url'], {'external_sub_tracks':sub_tracks})
        
        return linksTab
        
    def parsePUBLICVIDEOHOST(self, baseUrl):
        printDBG("parsePUBLICVIDEOHOST baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        linksTab = self._findLinks(data, serverName='publicvideohost.org', m1='setup(', m2=')', contain='.mp4')
        return linksTab
                    
    def parserSUPERFILMPL(self, baseUrl):
        printDBG("parserSUPERFILMPL baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video ', '</video>', False)[1]
        linkUrl = self.cm.ph.getSearchGroups(data, '<source[^>]+?src="(http[^"]+?)"')[0]
        return linkUrl
        
    def parserSENDVIDCOM(self, baseUrl):
        printDBG("parserSENDVIDCOM baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video ', '</video>', False)[1]
        linkUrl = self.cm.ph.getSearchGroups(data, '<source[^>]+?src="([^"]+?)"')[0]
        if linkUrl.startswith('//'): linkUrl = 'http:' + linkUrl
        return linkUrl
        
    def parserFILEHOOT(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        
        if 'embed-' not in baseUrl:
            baseUrl = 'http://filehoot.com/embed-%s-1046x562.html' % baseUrl.split('/')[-1].replace('.html', '')
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = re.search('file:[ ]*?"([^"]+?)"', data)
        if data:
            linkVideo = data.group(1)
            printDBG('parserFILEHOOT direct link: ' + linkVideo)
            return linkVideo
        return False
        
    def parserSSH101COM(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'file:[ ]*?"([^"]+?)"', 1, ignoreCase=True)[0]
        if not videoUrl.split('?')[0].endswith('.m3u8'): videoUrl = self.cm.ph.getSearchGroups(data, '<source[^>]*?src="([^"]+?)"', 1, ignoreCase=True)[0]
        
        if videoUrl.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(videoUrl)
        return False
        
    def parserTWITCHTV(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        if 'channel'  in baseUrl:
            data = baseUrl + '&'
        else:
            sts, data = self.cm.getPage(baseUrl)
        
        channel = self.cm.ph.getSearchGroups(data, '''channel=([^&^'^"]+?)[&'"]''')[0]
        MAIN_URLS = 'https://api.twitch.tv/'
        CHANNEL_TOKEN_URL = MAIN_URLS + 'api/channels/%s/access_token'
        LIVE_URL = 'http://usher.justin.tv/api/channel/hls/%s.m3u8?token=%s&sig=%s&allow_source=true'
        if '' != channel:
            url = CHANNEL_TOKEN_URL % channel
            sts, data = self.cm.getPage(url)
            urlTab = []
            if sts:
                try:
                    data = byteify( json.loads(data) )
                    url = LIVE_URL % (channel, urllib.quote(data['token']), data['sig'])
                    data = getDirectM3U8Playlist(url, checkExt=False)
                    for item in data:
                        item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True}) 
                        urlTab.append(item)
                except Exception: printExc()
            return urlTab
        return False
        
    def parserMOONWALKCC(self, baseUrl):
        printDBG("parserMOONWALKCC baseUrl[%r]" % baseUrl)
        return self.getMoonwalkParser().getDirectLinks(baseUrl)
        
    def parserEASYVIDORG(self, baseUrl):
        printDBG("parserEASYVIDORG baseUrl[%r]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'easyvid.org')
        return self._parserUNIVERSAL_A(baseUrl, 'http://easyvid.org/embed-{0}-640x360.html', _findLinks)
    
    def parserMYSTREAMLA(self, baseUrl):
        printDBG("parserMYSTREAMLA baseUrl[%r]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'mystream.la')
        return self._parserUNIVERSAL_A(baseUrl, 'http://mystream.la/external/{0}', _findLinks)
        
    def parserOKRU(self, baseUrl):
        printDBG("parserOKRU baseUrl[%r]" % baseUrl)
        if 'videoPlayerMetadata' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([0-9]+)/')[0]
            if video_id == '': return False
            url = 'http://ok.ru/dk?cmd=videoPlayerMetadata&mid=%s' % video_id
        else:
            url = baseUrl
        
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer':baseUrl,
                       'Cookie':'_flashVersion=18',
                       'X-Requested-With':'XMLHttpRequest'}
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        data = byteify(json.loads(data))
        urlsTab = []
        for item in data['videos']:
            url = item['url'].replace('&ct=4&', '&ct=0&') + '&bytes'#=0-7078'
            url = strwithmeta(url, {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            urlsTab.append({'name':item['name'], 'url':url})
        return urlsTab[::-1]
        
    def parserALLOCINEFR(self, baseUrl):
        printDBG("parserOKRU baseUrl[%r]" % baseUrl)
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/allocine.py
        _VALID_URL = r'https?://(?:www\.)?allocine\.fr/_?(?P<typ>article|video|film|video|film)/(iblogvision.aspx\?cmedia=|fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\.html)?'
        mobj = re.match(_VALID_URL, baseUrl)
        typ = mobj.group('typ')
        display_id = mobj.group('id')

        sts, webpage = self.cm.getPage(baseUrl)
        if not sts: return False

        if 'film' == type:
            video_id = self.cm.ph.getSearchGroups(webpage, r'href="/video/player_gen_cmedia=([0-9]+).+"')[0]
        else:
            player = self.cm.ph.getSearchGroups(webpage, r'data-player=\'([^\']+)\'>')[0]
            if player != '':
                player_data = byteify(json.loads(player))
                video_id = player_data['refMedia']
            else:
                model = self.cm.ph.getSearchGroups(webpage, r'data-model="([^"]+)">')[0] 
                model_data = byteify(json.loads(unescapeHTML(model)))
                video_id = model_data['id']

        sts, data = self.cm.getPage('http://www.allocine.fr/ws/AcVisiondataV5.ashx?media=%s' % video_id)
        if not sts: return False
        
        data = byteify(json.loads(data))
        quality = ['hd', 'md', 'ld']
        urlsTab = []
        for item in quality:
            url = data['video'].get(item + 'Path', '')
            if not url.startswith('http'):
                continue
            urlsTab.append({'name':item, 'url':url})
        return urlsTab
        
    def parserLIVESTRAMTV(self, baseUrl):
        printDBG("parserLIVESTRAMTV baseUrl[%r]" % baseUrl)
        url = 'http://www.live-stream.tv/'
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer':baseUrl}
                       
        COOKIEFILE = self.COOKIE_PATH + "live-stream.tv.cookie"
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE}
        
        def updateStreamStatistics(channel, quality, statserver):
            upBaseUrl = 'http://'+statserver+'.ucount.in/stats/update/custom/lstv/'+channel+'/'+quality
            tm = str(int(time.time() * 1000))
            upUrl = upBaseUrl + "&_="+tm+"&callback=?"
            std, data = self.cm.getPage(upUrl, params)
            return upBaseUrl
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0]
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        
        def _getUpData(dat):
            upData = self.cm.ph.getDataBeetwenMarkers(dat, 'updateStreamStatistics', ';', False)[1]
            upData = re.compile('''['"]([^'^"]+?)['"]''').findall(upData)
            return upData
            
        def _getVidUrl(dat):
            vidUrl = self.cm.ph.getSearchGroups(dat, r'''movie=['"](http[^'^"]+?hls[^'^"]+?)['"]''')[0]
            if vidUrl == '': vidUrl = self.cm.ph.getSearchGroups(dat, r'''movie=['"](http[^'^"]+?\.m3u8[^'^"]*?)['"]''')[0]
            return vidUrl
        
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>', True)[1]
        printDBG(tmpData)
        upData = None
        vidUrl = None
        while 'eval' in tmpData and (upData == None or vidUrl == None):
            tmp = tmpData.split('eval(')
            if len(tmp): del tmp[0]
            tmpData = ''
            for item in tmp:
                for decFun in [VIDEOWEED_decryptPlayerParams, SAWLIVETV_decryptPlayerParams]:
                    tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                    if '' != tmpData: break
                printDBG(tmpData)
                if 'updateStreamStatistics' in tmpData:
                    upData = _getUpData(tmpData)
                    if 0 == len(upData): upData = None
                if 'movie' in tmpData and ('hls' in tmpData or '.m3u8' in tmpData):
                    vidUrl = _getVidUrl(tmpData)
                    if '' == vidUrl: vidUrl = None
        
        if None == upData:
            upData = _getUpData(data)
            
        if None == vidUrl:
            vidUrl = _getVidUrl(data)
        
        marker = '.m3u8'
        if marker in vidUrl:
            vidUrl = strwithmeta(vidUrl, {'iptv_proto':'m3u8', 'iptv_m3u8_skip_seg':2, 'Referer':'http://static.live-stream.tv/player/player.swf', 'User-Agent':HTTP_HEADER['User-Agent']})
            tab = getDirectM3U8Playlist(vidUrl, False)
            tab.reverse()
            return tab
        return False
        
    def parserZEROCASTTV(self, baseUrl):
        printDBG("parserZEROCASTTV baseUrl[%r]" % baseUrl)
        if 'embed.php' in baseUrl:
            url = baseUrl
        elif 'chan.php?' in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
            data = self.cm.ph.getDataBeetwenMarkers(data, '<body ', '</body>', False)[1]
            url = self.cm.ph.getSearchGroups(data, r'''src=['"](http[^"^']+)['"]''')[0]
            
        if 'embed.php' not in url:
            sts, data = self.cm.getPage(url)
            if not sts: return False
            url = self.cm.ph.getSearchGroups(data, r'''var [^=]+?=[^'^"]*?['"](http[^'^"]+?)['"];''')[0]
            
        if url == '': return False
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        channelData = self.cm.ph.getSearchGroups(data, r'''unescape\(['"]([^'^"]+?)['"]\)''')[0]
        channelData = urllib.unquote(channelData)
        
        if channelData == '':
            data = self.cm.ph.getSearchGroups(data, '<h1[^>]*?>([^<]+?)<')[0]
            SetIPTVPlayerLastHostError(data)
        
        if channelData.startswith('rtmp'):
            channelData += ' live=1 '
            return channelData
        return False
        
    def parserCLOUDYEC(self, baseUrl):
        printDBG("parserCLOUDYEC baseUrl[%r]" % baseUrl)
        #based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/cloudy.py
        
        _VALID_URL = r'''(?x)
            https?://(?:www\.)?(?P<host>cloudy\.ec|videoraj\.ch)/
            (?:v/|embed\.php\?id=)
            (?P<id>[A-Za-z0-9]+)
            '''
        _EMBED_URL = 'http://www.%s/embed.php?id=%s'
        _API_URL = 'http://www.%s/api/player.api.php?%s'
        _MAX_TRIES = 2
        
        mobj = re.match(_VALID_URL, baseUrl)
        video_host = mobj.group('host')
        video_id = mobj.group('id')

        url = _EMBED_URL % (video_host, video_id)
        sts, data = self.cm.getPage(url)
        if not sts: return False

        file_key = self.cm.ph.getSearchGroups(data, r'key\s*:\s*"([^"]+)"')[0]
        if '' == file_key:
            file_key = self.cm.ph.getSearchGroups(data, r'filekey\s*=\s*"([^"]+)"')[0]

        def _extract_video(video_host, video_id, file_key, error_url=None, try_num=0):

            if try_num > _MAX_TRIES - 1:
                return False

            form = {'file': video_id, 'key': file_key}
            if error_url:
                form.update({'numOfErrors': try_num, 'errorCode': '404', 'errorUrl': error_url})

            data_url = _API_URL % (video_host, urllib.urlencode(form))
            sts, player_data = self.cm.getPage(data_url)
            if not sts: return sts

            data = parse_qs(player_data)
            try_num += 1
            if 'error' in data:
                return False
            title = data.get('title', [None])[0]
            if title:
                title = title.replace('&asdasdas', '').strip()
            video_url = data.get('url', [None])[0]
            if video_url:
                sts, data = self.cm.getPage(video_url, {'return_data':False})
                data.close()
                if not sts:
                    return self._extract_video(video_host, video_id, file_key, video_url, try_num)
            return [{'id': video_id, 'url': video_url, 'name': title}]
        return _extract_video(video_host, video_id, file_key)
    
    def parserSWIROWNIA(self, baseUrl):
        printDBG("Ekstraklasa.parserSWIROWNIA baseUrl[%r]" % baseUrl)
        def fun1(x):
            o = ""
            l = len(x)
            i = l - 1;
            while i >= 0:
                try:
                    o += x[i]
                except Exception:
                    pass
                i -= 1
            return o
        def fun2(x):
            o = ""
            ol = len(x)
            l = ol
            while ord(x[l/13]) != 48:
                try:
                    x += x
                    l += l
                except Exception:
                    pass
            i = l - 1
            while i >= 0:
                try:
                    o += x[i]
                except Exception:
                    pass
                i -= 1
            return o[:ol]
        def fun3(x, y, a=1):
            o = ""
            i = 0
            l = len(x)
            while i<l:
                if i<y:
                    y += a
                y %= 127
                o += JS_FromCharCode(ord(x[i]) ^ y)
                y += 1
                i += 1
            return o
              
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = data[data.find('x="')+2 : data.rfind('"')+1]
        dataTab = data.split('+\n')
        data = ""
        for line in dataTab:
            line = line.strip()
            if '"' != line[0] or '"' != line[-1]:
                raise Exception("parserSWIROWNIA parsing ERROR")
            data += line[1:-1]


        def backslashUnEscaped(data):
            #return pythonUnescape(data)
            #return codecs.decode(data, "unicode_escape").replace('\\,', ',')
            #return re.sub(r'\\(.)', r'\1', data)
            #try:
            #    return data.decode('unicode-escape')
            #except Exception:
            #    printExc()
                #return re.sub(r'\\(.)', r'\1', data)
            tmp = ''
            idx = 0
            while idx < len(data):
                if data[idx] == '\\':
                    tmp += data[idx+1]
                    idx += 2
                else:
                    tmp += data[idx]
                    idx += 1
            return tmp
            
        def printDBG2(data):
            printDBG("================================================================")
            printDBG( data )
            printDBG("================================================================")
        data = backslashUnEscaped(data)
        
        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun1( data )
        printDBG2(data)
        data = backslashUnEscaped(data)
        
        printDBG2(data)
        
        data = data[data.find('f("')+3:data.rfind('"')]
        printDBG2(data)
        data = data.decode('string_escape')
        data = fun3( data, 50, 0)
        data = backslashUnEscaped(data)
        
        printDBG2(data)
        
        return
        
        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun2( data )
        data = data.decode('string-escape')

        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun3( data, 23, 1)
        data = backslashUnEscaped(data)
        
        printDBG(data)
        printDBG("------------------------------------------------------------------------------------")
        return
        #data = data.decode('string_escape')
        #printDBG(data)
        data = fun3( data, 23, 1)
        #data = data.decode('string_escape')
        data = backslashUnEscaped(data)
        
        printDBG("------------------------------------------------------------------------------------")
        printDBG(data)
        printDBG("------------------------------------------------------------------------------------")

    def parseMETAUA(self, baseUrl):
        printDBG("parseMETAUA baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', #'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        if not sts: return False
        file_url = self.cm.ph.getSearchGroups(data, '''st_html5=['"]([^'^"]+?)['"]''')[0]
        
        def getUtf8Str(st):
            idx = 0
            st2 = ''
            while idx < len(st):
                st2 += '\\u0' + st[idx:idx + 3]
                idx += 3
            return st2.decode('unicode-escape').encode('UTF-8')
        
        if file_url.startswith('#') and 3 < len(file_url):
            file_url = getUtf8Str(file_url[1:])
            file_url = byteify(json.loads(file_url))['file']
        
        if file_url.startswith('http'): 
            return urlparser.decorateUrl(file_url, {'iptv_livestream':False, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        return False 
        
    def parseNETUTV(self, url):
        printDBG("parseNETUTV url[%s]" % url)
        # example video: http://netu.tv/watch_video.php?v=WO4OAYA4K758
    
        printDBG("parseNETUTV url[%s]\n" % url)
        
        #http://netu.tv/watch_video.php?v=ODM4R872W3S9
        match = re.search("=([0-9a-zA-Z]+?)[^0-9^a-z^A-Z]", url + '|' )
        vid = match.group(1)
        
        # User-Agent - is important!!!
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', #'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Referer': 'http://hqq.tv/'
                      }
        
        COOKIE_FILE = self.COOKIE_PATH + "netu.tv.cookie"
        # remove old cookie file
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        sts, ipData = self.cm.getPage('http://hqq.tv/player/ip.php?type=json', params)
        ipData = byteify(json.loads(ipData)) #{"ip":"MTc4LjIzNS40My4zNw==","ip_blacklist":0}

        printDBG("=================================================================")
        printDBG(ipData)
        printDBG("=================================================================")
        
        #http://hqq.tv/player/hash.php?hash=229221213221211228239245206208212229194271217271255
        if 'hash.php?hash' in url:
            sts, data = self.cm.getPage(url, params)
            if not sts: return False
            data = re.sub('document\.write\(unescape\("([^"]+?)"\)', lambda m: urllib.unquote(m.group(1)), data)
            vid = re.search('''var[ ]+%s[ ]*=[ ]*["']([^"]*?)["']''' % 'vid', data).group(1)
        
        playerUrl = "http://hqq.tv/player/embed_player.php?vid=%s&autoplay=no" % vid
        referer = strwithmeta(url).meta.get('Referer', playerUrl)
        
        #HTTP_HEADER['Referer'] = url
        sts, data = self.cm.getPage(playerUrl, params)
        
        def _getEvalData(data):
            tmpData = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>', True)[1]
            printDBG(tmpData)
            while 'eval' in tmpData:
                tmp = tmpData.split('eval(')
                if len(tmp): del tmp[0]
                tmpData = ''
                for item in tmp:
                    for decFun in [VIDEOWEED_decryptPlayerParams, SAWLIVETV_decryptPlayerParams]:
                        tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                        if '' != tmpData:   
                            break
            return tmpData
            
        tmpData = _getEvalData(data)
                
        iss = '' #ipData['ip']
        need_captcha = '0' #str(ipData['ip_blacklist'])
        
        def _getVar(tmp, varName):
            val = self.cm.ph.getSearchGroups(tmp, 'var\s*%s\s*=([^;]+?);' % varName, ignoreCase=True)[0].strip()
            return val.replace('"', '').replace("'", '')
        vid          = _getVar(tmpData, 'vid')
        at           = _getVar(tmpData, 'at')
        autoplayed   = _getVar(tmpData, 'autoplayed')
        referer      = _getVar(tmpData, 'referer')
        passwd       = _getVar(tmpData, 'pass')
        embed_from   = _getVar(tmpData, 'embed_from')
        http_referer = _getVar(tmpData, 'http_referer')
                
        secPlayerUrl = "http://hqq.tv/sec/player/embed_player.php?iss="+iss+"&vid="+vid+"&at="+at+"&autoplayed="+autoplayed+"&referer="+referer+"&http_referer="+http_referer+"&pass="+passwd+"&embed_from="+embed_from+"&need_captcha="+need_captcha
        HTTP_HEADER['Referer'] = referer
        sts, data = self.cm.getPage(secPlayerUrl, params)
        
        data = re.sub('document\.write\(unescape\("([^"]+?)"\)', lambda m: urllib.unquote(m.group(1)), data)
        data += str(_getEvalData(data))
        
        def getUtf8Str(st):
            idx = 0
            st2 = ''
            while idx < len(st):
                st2 += '\\u0' + st[idx:idx + 3]
                idx += 3
            return st2.decode('unicode-escape').encode('UTF-8')
        
        data += str(tmpData)
        #self.cm.ph.writeToFile('/mnt/new2/test.html', data)
        
        playerData = self.cm.ph.getDataBeetwenMarkers(data, 'get_md5.php', '})')[1]
        playerData = self.cm.ph.getDataBeetwenMarkers(playerData, '{', '}', False)[1]
        playerData = playerData.split(',')
        getParams = {}
        for p in playerData:
            tmp = p.split(':')
            printDBG(tmp)
            key = tmp[0].replace('"', '').strip()
            val = tmp[1].strip()
            if len(val) and val[0] not in ['"', "'"]:
                printDBG("MY VAL: " + val)
                v = re.search('''var[ ]+%s[ ]*=[ ]*["']([^"]*?)["']''' % val, data).group(1)
                if '' != val: val = v
            if key == 'adb':
                val = val.replace('1', '0')
            getParams[key] = val.replace('"', '').strip()
        playerUrl = 'http://hqq.tv/player/get_md5.php?' + urllib.urlencode(getParams)
        #params.pop('use_cookie')
        #strTime = re.search('''var[ ]+%s[ ]*=[ ]*["']([^"]*?)["']''' % 'time', data).group(1)
        #params['header']['Cookie'] = self.cm.getCookieHeader(COOKIE_FILE) + 'adc1=opened; user_ad=1; user_ad_time={0}; '.format(strTime)
        params['header']['X-Requested-With'] = 'XMLHttpRequest'
        params['header']['Referer'] = secPlayerUrl
        sts, data = self.cm.getPage(playerUrl, params)
        
        printDBG(data)
        if not sts: return False
        data = byteify( json.loads(data) )
        file_url = data['html5_file']
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(data['file'])
        if file_url.startswith('#') and 3 < len(file_url): file_url = getUtf8Str(file_url[1:])
        if self.cm.isValidUrl(file_url): 
            file_url = urlparser.decorateUrl(file_url, {'iptv_livestream':False, 'User-Agent':HTTP_HEADER['User-Agent']})
            if file_url.split('?')[0].endswith('.m3u8'):
                return getDirectM3U8Playlist(file_url, False)
        return file_url
        
    def parserSTREAMPLAYTO(self, url):
        printDBG("parserSTREAMPLAYTO url[%s]\n" % url)
        sts, data = self.cm.getPage(url)
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>')
        if sts:
            # unpack and decode params from JS player script code
            data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0, r2=True)
            printDBG(data)
            # get direct link to file from params
            file = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
            if self.cm.isValidUrl(file):
                return file
        return False
        
    def parserSTREAMANGOCOM(self, baseUrl):
        printDBG("parserSTREAMANGOCOM url[%s]\n" % baseUrl)
        videoTab = []
        if '/embed/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return videoTab
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?/embed/[^"^']+?)["']''', 1, True)[0]
        else:
            url = baseUrl
        
        sts, data = self.cm.getPage(url)
        if not sts: return videoTab
        
        dashTab = []
        hlsTab = []
        mp4Tab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'srces.push(', ')', False)
        printDBG(data)
        for item in data:
            url = self.cm.ph.getSearchGroups(item, r'''['"]?src['"]?\s*:\s*['"]([^"^']+)['"]''')[0]
            if url.startswith('//'): url = 'http:' + url
            type = self.cm.ph.getSearchGroups(item, r'''['"]?type['"]?\s*:\s*['"]([^"^']+)['"]''')[0]
            if not self.cm.isValidUrl(url): continue
        
            #url = strwithmeta(url, {'User-Agent':params['header']})
            if '/dash' in type:
                dashTab.extend(getMPDLinksWithMeta(url, False))
            elif 'hls' in type:
                hlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True))
            elif '/mp4' in type:
                name = self.cm.ph.getSearchGroups(item, '''height\s*\:\s*([^\,]+?)[\,]''')[0]
                mp4Tab.append({'name':'[%s] %sp' % (type, name), 'url':url})

        videoTab.extend(mp4Tab)
        videoTab.extend(hlsTab)
        videoTab.extend(dashTab)
        return videoTab
        
        
