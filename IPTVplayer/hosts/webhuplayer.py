# -*- coding: utf-8 -*-
###################################################
# 2022-03-26 - Web HU Player
###################################################
HOST_VERSION = "3.2"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, GetLogoDir, GetIPTVPlayerVerstion, rm, rmtree, mkdirs, DownloadFile, GetFileSize, GetConfigDir, Which, MergeDicts
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigText, ConfigYesNo, ConfigDirectory, getConfigListEntry
from os.path import normpath
import urlparse
import os
import re
import random
import datetime
import time
import zlib
import cookielib
import base64
import codecs
import traceback
try:
    import subprocess
    FOUND_SUB = True
except Exception:
    FOUND_SUB = False
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from Screens.MessageBox import MessageBox
from hashlib import sha1
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.webhuplayer_dir = ConfigText(default = "/hdd/webhuplayer", fixed_size = False)
config.plugins.iptvplayer.webmedia_dir = ConfigText(default = "/hdd/webmedia", fixed_size = False)
config.plugins.iptvplayer.ytmedia_dir = ConfigText(default = "/hdd/ytmedia", fixed_size = False)
config.plugins.iptvplayer.webhuplayer_nezettseg = ConfigYesNo(default = False)
config.plugins.iptvplayer.boxtipus = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.boxrendszer = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Web HU Player könyvtára:", config.plugins.iptvplayer.webhuplayer_dir))
    optionList.append(getConfigListEntry("Web média könyvtára:", config.plugins.iptvplayer.webmedia_dir))
    optionList.append(getConfigListEntry("YouTube média könyvtára:", config.plugins.iptvplayer.ytmedia_dir))
    optionList.append(getConfigListEntry("Nézettség kijelzés:", config.plugins.iptvplayer.webhuplayer_nezettseg))
    return optionList
###################################################

def gettytul():
    return 'Web HU Player'

class webhuplayer(CBaseHostClass):

    def __init__(self):
        printDBG("webhuplayer.__init__")
        CBaseHostClass.__init__(self, {'history':'webhuplayer', 'cookie':'webhuplayer.cookie'})
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = self.cm.getDefaultHeader()
        self.DEFAULT_ICON_URL = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1S9PTcooLchJrEwtis/JT8/XyypIBwDbUhM+'))
        self.ICON_YT = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1S9PTcooLchJrEwtis/JT8+PryzRyypIBwAYgRSK'))
        self.ICON_IDOJARAS = zlib.decompress(base64.b64decode('eNpdikEOgzAMwH7DsWlY6MoktMv+EbE0DDTRVlDE92Ec55NleSwlrw+A3bxT+kqIRtIMu/Zl1AXyJGVbFIjRW9cyMp7a4KCe0VkeLvh2wdaT969z+svsTI6f5yopaIc1VSHNU+jI1VUfhX9K96Y9AGfgK44='))
        self.ICON_INFO = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1S9PTcooLchJrEwtis/JT8+Pz9TLKkgHAANGFAY='))
        self.ICON_FRISSIT = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1S9PTcooLchJrEwtis/JT8+PTyvSyypIBwAYBRR1'))
        self.WHPL = zlib.decompress(base64.b64decode('eJwrT03KKC3ISaxMLdLLySwuAQA4XgaT'))
        self.WHYTPL = zlib.decompress(base64.b64decode('eJyrLMkoLchJrEwt0svJLC4BADMVBkI='))
        self.WAFL = zlib.decompress(base64.b64decode('eJxLzC4pTczJLNYrLilKTcwFADECBhk='))
        self.path_wh = config.plugins.iptvplayer.webmedia_dir.value + '/'
        self.path_yt = config.plugins.iptvplayer.ytmedia_dir.value + '/'
        self.fwuln = normpath(self.path_wh + self.WHPL)
        self.fwuytln = normpath(self.path_yt + self.WHYTPL)
        self.fwan = normpath(self.path_wh + self.WAFL)
        self.vivn = GetIPTVPlayerVerstion()
        self.porv = self.gits()
        self.pbtp = '-'
        self.btps = config.plugins.iptvplayer.boxtipus.value
        self.brdr = config.plugins.iptvplayer.boxrendszer.value
        self.whuunz = config.plugins.iptvplayer.webhuplayer_dir.value + zlib.decompress(base64.b64decode('eJzTLykozSupKtEryS0AAB7TBNg='))
        self.whutv = config.plugins.iptvplayer.webhuplayer_dir.value + zlib.decompress(base64.b64decode('eJzTLykozygtKdMryS0AAB6iBNE='))
        self.WUSG = self.path_wh + zlib.decompress(base64.b64decode('eJwrKS8tTtcryS0AABMbA7o='))
        self.YUSG = self.path_yt + zlib.decompress(base64.b64decode('eJwrqSwtTtcryS0AABMrA7w='))
        self.IH = resolveFilename(SCOPE_PLUGINS, zlib.decompress(base64.b64decode('eJxzrShJzSvOzM8r1vcMCAkLyEmsTC0CAFlVCBA=')))
        self.TEMP = zlib.decompress(base64.b64decode('eJzTL8ktAAADZgGB'))
        self.aid = config.plugins.iptvplayer.webhuplayer_nezettseg.value
        self.aid_ki = ''
        self.wupt = []
        self.yupt = []
        self.whuav = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': False, 'load_cookie': False, 'save_cookie': False, 'cookiefile': self.COOKIE_FILE}
        
    def _uriIsValid(self, url):
        return '://' in url
        
    def listMainMenu(self, cItem):
        try:
            if not self.ebbtit(): return
            if self.btps != '' and self.brdr != '': self.pbtp = self.btps.strip() + ' - ' + self.brdr.strip()
            n_wt = self.malvadst('1', '10', 'hu_webes_tartalom')
            if n_wt != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_wt + '\n\n'
            else:
                self.aid_ki = '\n'
            msg_webes_tartalom = 'Web HU Player - v' + HOST_VERSION + '\n' + self.aid_ki + 'Webes tartalmak megjelenítése...'
            n_yt = self.malvadst('1', '10', 'hu_yt_tartalom')
            if n_yt != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_yt + '\n\n'
            else:
                self.aid_ki = ''
            msg_yt_tartalom = self.aid_ki + 'YouTube tartalmak megjelenítése'
            n_utso = self.malvadst('1', '10', 'hu_utso_tartalom')
            if n_utso != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_utso + '\n\n'
            else:
                self.aid_ki = ''
            msg_utnez_tartalom = self.aid_ki + 'Utoljára nézett tartalmak megjelenítése'
            n_antrt = self.malvadst('1', '10', 'hu_ajltt_tartalom')
            if n_antrt != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_antrt + '\n\n'
            else:
                self.aid_ki = ''
            msg_wh_ajlt_tart = self.aid_ki + 'Ajánlott, nézett tartalmak megjelenítése'
            n_if = self.malvadst('1', '10', 'hu_informacio')
            if n_if != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_if + '\n\n'
            else:
                self.aid_ki = ''
            msg_info = self.aid_ki + 'Információk megjelenítése'
            n_fr = self.malvadst('1', '10', 'hu_fofrissites')
            if n_fr != '' and self.aid:
                self.aid_ki = 'Megnézve: ' + n_fr + '\n\n'
            else:
                self.aid_ki = ''
            msg_frissites = self.aid_ki + 'A meglévő tartalmak frissítése, újak telepítése...\nOK gomb megnyomása után láthatod, hogy kell-e frissítened, illetve telepítened a média tartalmakat!\nAz ellenőrzés időigényes lehet, akár 1-2 percig is eltarthat...  Légy türelmes!'
            MAIN_CAT_TAB = [{'category': 'list_main', 'title': 'Webes tartalmak', 'tab_id': 'webes', 'desc': msg_webes_tartalom, 'icon':self.ICON_IDOJARAS},
                            {'category': 'list_main', 'title': 'YouTube tartalmak', 'tab_id': 'youtartalom', 'desc': msg_yt_tartalom, 'icon':self.ICON_IDOJARAS},
                            {'category': 'list_main', 'title': 'Utoljára nézett tartalmak', 'tab_id': 'ut_nez_tart', 'desc': msg_utnez_tartalom, 'icon':self.DEFAULT_ICON_URL},
                            {'category': 'list_main', 'title': 'Ajánlott, nézett tartalmak', 'tab_id': 'wh_ajlt_tart', 'desc': msg_wh_ajlt_tart, 'icon':self.DEFAULT_ICON_URL},
                            {'category': 'list_main', 'title': 'Tartalom frissítés, telepítés', 'tab_id': 'fofrissites', 'desc': msg_frissites, 'icon':self.ICON_FRISSIT}
                           ]
            self.listsTab(MAIN_CAT_TAB, cItem)
            params = dict(cItem)
            params = {'good_for_fav': False, 'title':'Információ', 'icon':self.ICON_INFO, 'desc':msg_info, 'art_id':'foinformacio', 'type':'article'}
            self.addArticle(params)
        except Exception:
            return
            
    def listMainItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'webes':
                self.wstrtlmk(cItem)
            elif tabID == 'ut_nez_tart':
                self.unttrlmk(cItem)
            elif tabID == 'wh_ajlt_tart':
                self.whajnztrt(cItem, tabID)
            elif tabID == 'youtartalom':
                self.yttrtmkk(cItem)
            elif tabID == 'fofrissites':
                self.ffts(cItem)
            else:
                return
        except Exception:
            return
            
    def dtcffn(self):
        encoding = 'utf-8'
        self.whuav = {}
        try:
            if fileExists(self.whutv):
                with codecs.open(self.whutv, 'r', encoding, 'replace') as fpr:
                    for line in fpr:
                        if type(line) == type(u''): line = line.encode('utf-8', 'replace')
                        line = line.replace('\n', '').strip()
                        if len(line) > 0:
                            tt = line.split('|')
                            if len(tt) == 2:
                                self.whuav[tt[0].strip()] = tt[1].strip()
        except Exception:
            self.whuav = {}
            return
            
    def frtrlv(self):
        kkl = False
        lwh = config.plugins.iptvplayer.webhuplayer_dir.value
        lwm = config.plugins.iptvplayer.webmedia_dir.value
        lym = config.plugins.iptvplayer.ytmedia_dir.value
        encoding = 'utf-8'
        ltfn = self.whutv + '.writing'
        try:
            if os.path.isdir(lwh):
                fpw = codecs.open(ltfn, 'w', encoding, 'replace')
            else:
                if mkdirs(lwh): 
                    fpw = codecs.open(ltfn, 'w', encoding, 'replace')
                else:
                    msg = 'A Web HU Player könyvtára nem hozható létre!\nA kék gomb, majd az Oldal beállításai segítségével megadhatod a kért adatokat.\nHa megfelelőek az előre beállított értékek, akkor ZÖLD gomb (Mentés) megnyomása!'
                    self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
                    return
            if os.path.isdir(lwm):
                for root, dirs, files in os.walk(lwm):
                    dirs.sort()
                    for filename in sorted(files):
                        fname_with_path = os.path.join(root, filename)
                        fext = os.path.splitext(fname_with_path)[1]
                        if fext in ['.stream','.kstream']:
                            if '.kstream' in fname_with_path:
                                kkl = True
                            else:
                                kkl = False
                            data, elso = self.tkn_dt(fname_with_path)
                            if len(data) == 0: continue
                            for item in data:
                                tov, prdt = self.tkn_it(item, kkl)
                                if tov or len(prdt) == 0:
                                    continue
                                va = prdt['azn']
                                vv = prdt['verzio']
                                fpw.write("%s | %s\n" % (va,vv))
            if os.path.isdir(lym):
                for root, dirs, files in os.walk(lym):
                    dirs.sort()
                    for filename in sorted(files):
                        fname_with_path = os.path.join(root, filename)
                        fext = os.path.splitext(fname_with_path)[1]
                        if fext in ['.stream','.kstream']:
                            if '.kstream' in fname_with_path:
                                kkl = True
                            else:
                                kkl = False
                            data, elso = self.tkn_dt(fname_with_path)
                            if len(data) == 0: continue
                            for item in data:
                                tov, prdt = self.tkn_it(item, kkl)
                                if tov or len(prdt) == 0:
                                    continue
                                va = prdt['azn']
                                vv = prdt['verzio']
                                fpw.write("%s | %s\n" % (va,vv))
            fpw.flush()
            os.fsync(fpw.fileno())
            fpw.close()
            os.rename(ltfn, self.whutv)
            if fileExists(ltfn):
                rm(ltfn)
        except Exception:
            if fileExists(ltfn):
                rm(ltfn)        

    def wstrtlmk(self, cItem):
        vlrs = ''
        avrzl = ''
        try:
            if fileExists(self.fwuln):
                self.susn('2', '10', 'hu_webes_tartalom')
                n_aktt = self.malvadst('1', '10', 'hu_aktualis_tartalom')
                if n_aktt != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_aktt + '\n\n'
                else:
                    self.aid_ki = ''
                msg_webes_meglevo = self.aid_ki + 'Aktuális webes tartalmak'
                n_akttu = self.malvadst('1', '10', 'hu_webes_uj_tartalom')
                if n_akttu != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_akttu + '\n\n'
                else:
                    self.aid_ki = ''
                msg_webes_uj = self.aid_ki + 'Új tartalmak megjelenítése a legutolsó frissítés óta'
                vrz, dtm = self.gvsn(self.fwan)
                n_aktv = self.malvadst('1', '10', 'hu_aktualis_verzio')
                if n_aktv != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_aktv + '\n\n'
                else:
                    self.aid_ki = ''
                if vrz > 0 and dtm != '':
                    vlrs = 'Verzió:  ' + vrz + '  |  Dátuma:  ' + dtm
                    avrzl = '  -  v' + vrz
                msg_webes_akt = self.aid_ki + 'Aktuális verzió leírása, új és frissített tartalmak bemutatása\n' + vlrs
                akt_vrz_l = 'Aktuális verzió leírása' + avrzl
                n_akk = self.malvadst('1', '10', 'hu_webes_kereses')
                if n_akk != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_akk + '\n\n'
                else:
                    self.aid_ki = ''
                msg_webes_kereses = self.aid_ki + 'Keresés az aktuális webes tartalmak megnevezéseiben\nA folyamat időigényes lehet, akár 1-2 percig is eltarthat...  Légy türelmes!'                
                WEBES_CAT_TAB = [{'category': 'list_second', 'title': 'Aktuális tartalmak', 'tab_id': 'meg_webes', 'desc': msg_webes_meglevo},
                                 {'category': 'list_second', 'title': 'Újdonságok, új tartalmak', 'tab_id': 'meg_webes_u', 'desc': msg_webes_uj},
                                 {'category': 'list_second', 'title': akt_vrz_l, 'tab_id': 'akt_webes', 'desc': msg_webes_akt},
                                 {'category': 'search', 'title': 'Keresés', 'search_item': True, 'tab_id': 's_webes', 'desc': msg_webes_kereses}                        
                                ]
                self.listsTab(WEBES_CAT_TAB, cItem)
            else:
                msg = 'Hiba: 1\nHiányzó Web média tartalom (Telepítés szükséges)\nvagy Nem megfelelő a beállítás (KÉK gomb, Oldal beállítasai)!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )    
        except Exception:
            return
            
    def whajnztrt(self, cItem, tabID):
        try:
            self.susn('2', '10', 'hu_ajltt_tartalom')
            tab_ams = 'whu_ajnlt_musor'
            desc_ams = self.getdvdsz(tab_ams, 'Ajánlott, nézett tartalmak megjelenítése műsorok szerint')
            tab_adt = 'whu_ajnlt_datum'
            desc_adt = self.getdvdsz(tab_adt, 'Ajánlott, nézett tartalmak megjelenítése dátum szerint')
            tab_anzt = 'whu_ajnlt_nezettseg'
            desc_anzt = self.getdvdsz(tab_anzt, 'Ajánlott, nézett tartalmak megjelenítése nézettség szerint')
            A_CAT_TAB = [{'category':'list_six', 'title': 'Dátum szerint', 'tab_id':tab_adt, 'desc':desc_adt},
                         {'category':'list_six', 'title': 'Nézettség szerint', 'tab_id':tab_anzt, 'desc':desc_anzt},
                         {'category':'list_six', 'title': 'Műsorok szerint', 'tab_id':tab_ams, 'desc':desc_ams},
                        ]
            self.listsTab(A_CAT_TAB, cItem)
        except Exception:
            return
            
    def yttrtmkk(self, cItem):        
        try:
            if fileExists(self.fwuytln):
                self.susn('2', '10', 'hu_yt_tartalom')
                n_ytt = self.malvadst('1', '10', 'hu_yt_akt_tartalom')
                if n_ytt != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_ytt + '\n\n'
                else:
                    self.aid_ki = ''
                msg_yt_meglevo = self.aid_ki + 'YouTube tartalmak megjelenítése'
                n_yttu = self.malvadst('1', '10', 'hu_yt_uj_tartalom')
                if n_yttu != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_yttu + '\n\n'
                else:
                    self.aid_ki = ''
                msg_yt_uj = self.aid_ki + 'Új tartalmak megjelenítése a legutolsó frissítés óta'
                n_ytk = self.malvadst('1', '10', 'hu_yt_kereses')
                if n_ytk != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_ytk + '\n\n'
                else:
                    self.aid_ki = ''
                msg_yt_kereses = self.aid_ki + 'Keresés az aktuális YouTube tartalmak megnevezéseiben\nA folyamat időigényes lehet, akár 1-2 percig is eltarthat...  Légy türelmes!'
                YT_CAT_TAB = [{'category': 'list_second', 'title': 'Aktuális YouTube tartalmak', 'tab_id': 'meg_yt', 'desc': msg_yt_meglevo},
                              {'category': 'list_second', 'title': 'Újdonságok, új tartalmak', 'tab_id': 'meg_ytu', 'desc': msg_yt_uj},
                              {'category': 'search', 'title': 'Keresés', 'search_item': True, 'tab_id': 's_yt', 'desc': msg_yt_kereses}                        
                             ]
                self.listsTab(YT_CAT_TAB, cItem)
            else:
                msg = 'Hiba: 1\nHiányzó YouTube média tartalom (Telepítés szükséges)\nvagy Nem megfelelő a beállítás (KÉK gomb, Oldal beállítasai)!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
        except Exception:
            return

    def unttrlmk(self, cItem):
        encoding = 'utf-8'
        ln = 0
        try:
            self.susn('2', '10', 'hu_utso_tartalom')
            if fileExists(self.whuunz):
                with codecs.open(self.whuunz, 'r', encoding, 'replace') as fpr:
                    for line in fpr:
                        ln += 1
                        line = line.replace('\n', '').strip()
                        if len(line) > 0:
                            d1 = self.cm.ph.getAllItemsBeetwenMarkers(line, '{', '}', False)
                            if len(d1) == 0: return
                            for i1 in d1:
                                d2 = i1.split("',")
                                if len(d2) == 0: return
                                for i2 in d2:
                                    d3 = i2.split(': ')
                                    if len(d3) != 2: return
                                    tv1 = d3[0].strip().replace("'","")
                                    if tv1 == 'azn':
                                        pa = self.esklsz('5',d3[1].strip().replace("'",""))
                                    if tv1 == 'url':
                                        pu = self.esklsz('5',d3[1].strip().replace("'",""))
                                    if tv1 == 'desc':
                                        pd = self.esklsz('5',d3[1].strip().replace("'",""))
                                        try:
                                            tdsc = pd.split('\n')
                                            if len(tdsc) > 0:
                                                tmpsz = re.sub(r'^(.{600}).*$', '\g<1>...', tdsc[0]) + '\n\n'
                                                if len(tdsc) >= 4:
                                                    if tdsc[2] != '' and tdsc[3] != '':
                                                        tmpsz = tmpsz + tdsc[2] + '\n' + tdsc[3]
                                            else:
                                                tmpsz = pd
                                        except Exception:
                                            tmpsz = pd
                                    if tv1 == 'icon':
                                        pi = self.esklsz('5',d3[1].strip().replace("'",""))
                                    if tv1 == 'title':
                                        pt = self.esklsz('5',d3[1].strip().replace("'",""))
                                    if tv1 == 'mkt':
                                        pmk = self.esklsz('5',d3[1].strip().replace("'",""))
                                    if tv1 == 'md':
                                        pmd = self.esklsz('5',d3[1].strip().replace("'",""))
                            if pt != '' and pu != '' and pd != '' and pi != '' and pa != '' and pmk != '' and pmd != '':
                                tdpt = {'title':pt, 'url':pu, 'desc':tmpsz, 'icon':pi, 'azn':pa, 'mkt':pmk, 'md':pmd, 'mjnts':False}
                                fext = os.path.splitext(pu)[1]
                                if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in tmpsz:
                                    self.addAudio(tdpt)
                                else:
                                    self.addVideo(tdpt)
                                if ln > 50:
                                    break
        except Exception:
            return
        
    def ffts(self, cItem): 
        try:
            self.susn('2', '10', 'hu_fofrissites')
            valasz, msg = self._usable()
            if valasz:
                n_wfr = self.malvadst('1', '10', 'hu_webes_frissit')
                if n_wfr != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_wfr + '\n\n'
                else:
                    self.aid_ki = ''
                msg_webes_frissit = self.aid_ki + 'Webes tartalom frissítése'
                n_yfr = self.malvadst('1', '10', 'hu_yt_frissites')
                if n_yfr != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_yfr + '\n\n'
                else:
                    self.aid_ki = ''
                msg_yt_frissit = self.aid_ki + 'YouTube tartalom frissítése'
                self.wupt = []
                self.yupt = []
                self.dtcffn()
                FR_CAT_TAB = []
                FR_CAT_TAB.append(self.mtem('1','Webes tartalom frissítése','web_tr_frissit',msg_webes_frissit))
                FR_CAT_TAB.append(self.mtem('2','YouTube tartalom frissítése','yt_tr_frissit',msg_yt_frissit))
                self.whuav = {}
                self.listsTab(FR_CAT_TAB, cItem)
            else:
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
        except Exception:
            return        
        
    def listSecondItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'meg_webes':
                self.wsmvtrmk(cItem)
            elif tabID == 'meg_webes_u':
                self.wsutrtmk(cItem)
            elif tabID == 'akt_webes':
                self.wsattk(cItem)
            elif tabID == 'meg_yt':
                self.ymltrmk(cItem)
            elif tabID == 'meg_ytu':
                self.yutrmk(cItem)
            elif tabID == 'web_tr_frissit':
                self.wstmft(cItem)
            elif tabID == 'yt_tr_frissit':
                self.ytmfs(cItem)
            else:
                return
        except Exception:
            return
        
    def wsmvtrmk(self, cItem):
        try:
            self.susn('2', '10', 'hu_aktualis_tartalom')
            self.tfkn('1', self.fwuln, self.path_wh)    
        except Exception:
            return
            
    def wsutrtmk(self, cItem):
        encoding = 'utf-8'
        ln = 0
        mlt = []
        try:
            if fileExists(self.WUSG):
                if GetFileSize(self.WUSG) > 0:
                    self.susn('2', '10', 'hu_webes_uj_tartalom')
                    with codecs.open(self.WUSG, 'r', encoding, 'replace') as fpr:
                        esdt = fpr.read()
                    if len(esdt) == 0: return
                    if type(esdt) == type(u''): esdt = esdt.encode('utf-8', 'replace')
                    esdt = esdt.replace('[','').strip()
                    esdt = esdt.replace(']','').strip()
                    d1 = self.cm.ph.getAllItemsBeetwenMarkers(esdt, '{', '}', False)
                    if len(d1) == 0: return
                    for i1 in d1:
                        ln += 1
                        d2 = i1.split("',")
                        if len(d2) == 0: return
                        for i2 in d2:
                            d3 = i2.split(': ')
                            if len(d3) != 2: return
                            tv1 = d3[0].strip().replace("'","")
                            if tv1 == 'url':
                                pu = d3[1].strip().replace("'","")
                            if tv1 == 'desc':
                                pd = d3[1].strip().replace("'","")
                            if tv1 == 'azn':
                                pa = d3[1].strip().replace("'","")
                            if tv1 == 'icon':
                                pi = d3[1].strip().replace("'","")
                            if tv1 == 'title':
                                pt = d3[1].strip().replace("'","")
                            if tv1 == 'mkt':
                                pmk = d3[1].strip().replace("'","")
                            if tv1 == 'md':
                                pmd = d3[1].strip().replace("'","")
                        if ln > 50:
                            break
                        if pt == '' or pu == '' or pd == '' or pi == '' or pa == '' and pmk == '' and pmd == '':
                            return
                        else:
                            try:
                                tdsc = self.esklsz('5',pd).split('\n')
                                if len(tdsc) > 0:
                                    tmpsz = re.sub(r'^(.{600}).*$', '\g<1>...', tdsc[0]) + '\n\n'
                                    if len(tdsc) >= 4:
                                        if tdsc[2] != '' and tdsc[3] != '':
                                            tmpsz = tmpsz + tdsc[2] + '\n' + tdsc[3]
                                else:
                                    tmpsz = self.esklsz('5',pd)
                            except Exception:
                                tmpsz = self.esklsz('5',pd)
                            params = {'title':self.esklsz('5',pt), 'url':self.esklsz('5',pu), 'desc':tmpsz, 'icon':self.esklsz('5',pi), 'azn':self.esklsz('5',pa), 'mkt':self.esklsz('5',pmk), 'md':self.esklsz('5',pmd), 'mjnts':True}
                            mlt.append(params)
                    if len(mlt) > 0:
                        random.shuffle(mlt)
                        for ipv in mlt:
                            fext = os.path.splitext(ipv['url'])[1]
                            if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in ipv['desc']:
                                self.addAudio(ipv)
                            else:
                                self.addVideo(ipv)
            else:
                msg = 'Nincs új tartalom a legutolsó frissítés óta!\nÚjdonságokért menj a Tartalom frissítéshez!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 15 )
        except Exception:
            return
            
    def wsattk(self, cItem):
        try:
            if fileExists(self.fwan):
                self.susn('2', '10', 'hu_aktualis_verzio')
                self.tkn(self.fwan,False)    
            else:
                fwank = self.fwan.replace('.stream', '.kstream')
                if fileExists(fwank):
                    self.susn('2', '10', 'hu_aktualis_verzio')
                    self.tkn(fwank,True)    
                else:
                    msg = 'Hiba: 2 - Nem megfelelő tartalom!'
                    self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )            
        except Exception:
            return
            
    def ymltrmk(self, cItem):
        try:
            self.susn('2', '10', 'hu_yt_akt_tartalom')
            self.tfkn('2', self.fwuytln, self.path_yt)    
        except Exception:
            return
            
    def yutrmk(self, cItem):
        encoding = 'utf-8'
        ln = 0
        mlt = []
        try:
            if fileExists(self.YUSG):
                if GetFileSize(self.YUSG) > 0:
                    self.susn('2', '10', 'hu_yt_uj_tartalom')
                    with codecs.open(self.YUSG, 'r', encoding, 'replace') as fpr:
                        esdt = fpr.read()
                    if len(esdt) == 0: return
                    if type(esdt) == type(u''): esdt = esdt.encode('utf-8', 'replace')
                    esdt = esdt.replace('[','').strip()
                    esdt = esdt.replace(']','').strip()
                    d1 = self.cm.ph.getAllItemsBeetwenMarkers(esdt, '{', '}', False)
                    if len(d1) == 0: return
                    for i1 in d1:
                        ln += 1
                        d2 = i1.split("',")
                        if len(d2) == 0: return
                        for i2 in d2:
                            d3 = i2.split(': ')
                            if len(d3) != 2: return
                            tv1 = d3[0].strip().replace("'","")
                            if tv1 == 'url':
                                pu = d3[1].strip().replace("'","")
                            if tv1 == 'desc':
                                pd = d3[1].strip().replace("'","")
                            if tv1 == 'azn':
                                pa = d3[1].strip().replace("'","")
                            if tv1 == 'icon':
                                pi = d3[1].strip().replace("'","")
                            if tv1 == 'title':
                                pt = d3[1].strip().replace("'","")
                            if tv1 == 'mkt':
                                pmk = d3[1].strip().replace("'","")
                            if tv1 == 'md':
                                pmd = d3[1].strip().replace("'","")
                        if ln > 50:
                            break
                        if pt == '' or pu == '' or pd == '' or pi == '' or pa == '' and pmk == '' and pmd == '':
                            return
                        else:
                            try:
                                tdsc = self.esklsz('5',pd).split('\n')
                                if len(tdsc) > 0:
                                    tmpsz = re.sub(r'^(.{600}).*$', '\g<1>...', tdsc[0]) + '\n\n'
                                    if len(tdsc) >= 4:
                                        if tdsc[2] != '' and tdsc[3] != '':
                                            tmpsz = tmpsz + tdsc[2] + '\n' + tdsc[3]
                                else:
                                    tmpsz = self.esklsz('5',pd)
                            except Exception:
                                tmpsz = self.esklsz('5',pd)
                            params = {'title':self.esklsz('5',pt), 'url':self.esklsz('5',pu), 'desc':tmpsz, 'icon':self.esklsz('5',pi), 'azn':self.esklsz('5',pa), 'mkt':self.esklsz('5',pmk), 'md':self.esklsz('5',pmd), 'mjnts':True}
                            mlt.append(params)
                    if len(mlt) > 0:
                        random.shuffle(mlt)
                        for ipv in mlt:
                            fext = os.path.splitext(ipv['url'])[1]
                            if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in ipv['desc']:
                                self.addAudio(ipv)
                            else:
                                self.addVideo(ipv)
            else:
                msg = 'Nincs új tartalom a legutolsó frissítés óta!\nÚjdonságokért menj a Tartalom frissítéshez!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 15 )
        except Exception:
            return        
            
    def wstmft(self, cItem):
        try:
            if self.cpve(config.plugins.iptvplayer.webmedia_dir.value):
                msg = 'A telepítés, frissítés helye:  ' + config.plugins.iptvplayer.webmedia_dir.value.replace('/',' / ').strip() + '\nFolytathatom?'
                msg += '\n\nHa máshova szeretnéd, akkor itt nem - utána KÉK gomb, majd az Oldal beállításai.\nOtt az adatok megadása, s utána a ZÖLD gomb (Mentés) megnyomása!'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                if ret[0]:
                    self.susn('2', '10', 'hu_webes_frissit')
                    self.wstmts(cItem)
                    self.wmpfkr()
                    self.frtrlv()
            else:
                msg = 'A kék gomb, majd az Oldal beállításai segítségével megadhatod a kért adatokat.\nHa megfelelőek az előre beállított értékek, akkor ZÖLD gomb (Mentés) megnyomása!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
        except Exception:
            return
            
    def ytmfs(self, cItem):
        try:            
            if self.cpve(config.plugins.iptvplayer.ytmedia_dir.value):
                msg = 'A telepítés, frissítés helye:  ' + config.plugins.iptvplayer.ytmedia_dir.value.replace('/',' / ').strip() + '\nFolytathatom?'
                msg += '\n\nHa máshova szeretnéd, akkor itt nem - utána KÉK gomb, majd az Oldal beállításai.\nOtt az adatok megadása, s utána a ZÖLD gomb (Mentés) megnyomása!'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                if ret[0]:
                    self.susn('2', '10', 'hu_yt_frissites')
                    self.ytmtps(cItem)
                    self.ytmpfkr()
                    self.frtrlv()
            else:
                msg = 'A kék gomb, majd az Oldal beállításai segítségével megadhatod a kért adatokat.\nHa megfelelőek az előre beállított értékek, akkor ZÖLD gomb (Mentés) megnyomása!'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
        except Exception:
            return
            
    def listThirdItems(self, cItem):
        azn = cItem['azn']
        try:
            fPM = cItem.get('f_pn', '')
            fNM = cItem.get('f_nm', '')
            fin = cItem.get('icon', '')
            if fin == '': self.DEFAULT_ICON_URL
            fan = fPM + '/' + fNM
            if fileExists(fan):
                self.susn('2', '10', azn)
                with open(fan, 'r') as f:
                    for line in f:
                        values = line.split('|')
                        if len(values) == 4:
                            mn = values[0].strip()
                            fn = values[1].strip()
                            ls = values[2].strip()
                            ak = values[3].strip()
                            if '.list' in fn:
                                fpn = fPM + '/' + fn.replace('.list','').strip()
                                n_st = self.malvadst('1', '10', ak)
                                if n_st  != '' and self.aid:
                                    self.aid_ki = 'Megnézve: ' + n_st  + '\n\n'
                                else:
                                    self.aid_ki = ''
                                desc = self.aid_ki + ls
                                params = dict()
                                params.update({'good_for_fav': False, 'category': 'list_fourth', 'title': mn, 'f_pn': fpn, 'f_nm': fn, 'desc': desc, 'icon': fin, 'azn': ak})
                                self.addDir(params)
                            if '.kstream' in fn:
                                self.tkn(fPM + '/' + fn,True)
                            if '.stream' in fn:
                                self.tkn(fPM + '/' + fn,False)
        except Exception:
            return
            
    def listFourthItems(self, cItem):
        azn = cItem['azn']
        try:
            fPM = cItem.get('f_pn', '')
            fNM = cItem.get('f_nm', '')
            fin = cItem.get('icon', '')
            if fin == '': self.DEFAULT_ICON_URL
            fan = fPM + '/' + fNM
            if fileExists(fan):
                self.susn('2', '10', azn)
                with open(fan, 'r') as f:
                    for line in f:
                        values = line.split('|')
                        if len(values) == 4:
                            mn = values[0].strip()
                            fn = values[1].strip()
                            ls = values[2].strip()
                            ak = values[3].strip()
                            if '.list' in fn:
                                fpn = fPM + '/' + fn.replace('.list','').strip()
                                n_st = self.malvadst('1', '10', ak)
                                if n_st  != '' and self.aid:
                                    self.aid_ki = 'Megnézve: ' + n_st  + '\n\n'
                                else:
                                    self.aid_ki = ''
                                desc = self.aid_ki + ls
                                params = dict()
                                params.update({'good_for_fav': False, 'category': 'list_fifth', 'title': mn, 'f_pn': fpn, 'f_nm': fn, 'desc': desc, 'icon': fin, 'azn': ak})
                                self.addDir(params)
                            if '.kstream' in fn:
                                self.tkn(fPM + '/' + fn,True)
                            if '.stream' in fn:
                                self.tkn(fPM + '/' + fn,False)
        except Exception:
            return
            
    def listFifthItems(self, cItem):
        azn = cItem['azn']
        try:
            fPM = cItem.get('f_pn', '')
            fNM = cItem.get('f_nm', '')
            fan = fPM + '/' + fNM
            if fileExists(fan):
                self.susn('2', '10', azn)
                with open(fan, 'r') as f:
                    for line in f:
                        values = line.split('|')
                        if len(values) == 4:
                            mn = values[0].strip()
                            fn = values[1].strip()
                            ls = values[2].strip()
                            ak = values[3].strip()
                            if '.kstream' in fn:
                                self.tkn(fPM + '/' + fn,True)
                            if '.stream' in fn:
                                self.tkn(fPM + '/' + fn,False)
        except Exception:
            return
            
    def listSixItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'whu_ajnlt_musor':
                self.Vajnltmsr(cItem)
            elif tabID == 'whu_ajnlt_datum':
                self.Vajnltdtm(cItem)
            elif tabID == 'whu_ajnlt_nezettseg':
                self.Vajnltnztsg(cItem)
            else:
                return
        except Exception:
            return
            
    def Vajnltmsr(self,cItem):
        try:
            self.susn('2', '10', 'whu_ajnlt_musor')
            vtb = self.malvadnav(cItem, '3', '10', '0')
            if len(vtb) > 0:
                for item in vtb:
                    if item['desc'] > 0:
                        if item['md'] == 'wm': kszv = 'Webes tartalmak:'
                        if item['md'] == 'ym': kszv = 'YouTube tartalmak:'
                        tmp_d = item['desc'].replace('\n','').strip()
                        tid = re.sub(r'^(.{600}).*$', '\g<1>...', tmp_d)
                        item['desc'] = tid + '\n\n' + kszv + '\n' + item['mkt']
                        item['mjnts'] = False
                    fext = os.path.splitext(item['url'])[1]
                    if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in item['mkt']:
                        self.addAudio(item)
                    else:
                        self.addVideo(item)
        except Exception:
            return
            
    def Vajnltdtm(self,cItem):
        vtb = []
        kszv = ''
        try:
            self.susn('2', '10', 'whu_ajnlt_datum')
            vtb = self.malvadnav(cItem, '4', '10', '0')
            if len(vtb) > 0:
                for item in vtb:
                    if item['desc'] > 0:
                        if item['md'] == 'wm': kszv = 'Webes tartalmak:'
                        if item['md'] == 'ym': kszv = 'YouTube tartalmak:'
                        tmp_d = item['desc'].replace('\n','').strip()
                        tid = re.sub(r'^(.{600}).*$', '\g<1>...', tmp_d)
                        item['desc'] = tid + '\n\n' + kszv + '\n' + item['mkt']
                        item['mjnts'] = False
                    fext = os.path.splitext(item['url'])[1]
                    if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in item['mkt']:
                        self.addAudio(item)
                    else:
                        self.addVideo(item)
        except Exception:
            return
            
    def Vajnltnztsg(self,cItem):
        try:
            self.susn('2', '10', 'whu_ajnlt_nezettseg')
            vtb = self.malvadnav(cItem, '5', '10', '0')
            if len(vtb) > 0:
                for item in vtb:
                    if item['desc'] > 0:
                        if item['md'] == 'wm': kszv = 'Webes tartalmak:'
                        if item['md'] == 'ym': kszv = 'YouTube tartalmak:'
                        tmp_d = item['desc'].replace('\n','').strip()
                        tid = re.sub(r'^(.{600}).*$', '\g<1>...', tmp_d)
                        item['desc'] = tid + '\n\n' + kszv + '\n' + item['mkt']
                        item['mjnts'] = False
                    fext = os.path.splitext(item['url'])[1]
                    if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in item['mkt']:
                        self.addAudio(item)
                    else:
                        self.addVideo(item)
        except Exception:
            return
            
    def wstmts(self, cItem):
        hiba = False
        msg = ''
        lyt = config.plugins.iptvplayer.webmedia_dir.value
        url = zlib.decompress(base64.b64decode('eJwFwWEKgDAIBtAbTehnt3HbRwrJRK2o0/eeVHnuRIeWXL2NZYRN/eQXISsr6UE3TGXiGKI3yDgL0T71H8yHF2M='))
        fname = zlib.decompress(base64.b64decode('eJwrT03KTU3JTNSryiwAAB9HBMA='))
        destination = self.TEMP + '/' + fname
        destination_dir = self.TEMP + zlib.decompress(base64.b64decode('eJzTL09Nyk1NyUzUzU0sLkktAgAynwYn'))
        destination_fo = self.TEMP + zlib.decompress(base64.b64decode('eJzTL09Nyk1NyUwEABCLA24='))
        fname_zip = destination_dir + '/' + fname
        unzip_command = ['unzip', '-q', '-o', destination, '-d', self.TEMP]
        unzip_command_zip = ['unzip', '-q', '-o', fname_zip, '-d', self.TEMP]
        if fileExists(destination):
            rm(destination)
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        try:        
            if self.dflt(url,destination):
                if fileExists(destination):
                    if GetFileSize(destination) > 0:
                        if self._mycall(unzip_command) == 0:
                            if fileExists(fname_zip):
                                if GetFileSize(fname_zip) > 0:
                                    if self._mycall(unzip_command_zip) == 0:
                                        if mkdirs(lyt):
                                            if self._mycopy_o(destination_fo + '/*',lyt):
                                                hiba = False
                                            else:
                                                hiba = True
                                                msg = 'Hiba: 401 - Nem sikerült a frissítés, telepítés!'
                                        else:
                                            hiba = True
                                            msg = 'Hiba: 402 - Nem sikerült a frissítés, telepítés!'
                                    else:
                                        hiba = True
                                        msg = 'Hiba: 403 - Nem sikerült a frissítés, telepítés!'
                                else:
                                    hiba = True
                                    msg = 'Hiba: 404 - Nem sikerült a frissítés, telepítés!'
                            else:
                                hiba = True
                                msg = 'Hiba: 405 - Nem sikerült a frissítés, telepítés!'
                        else:
                            hiba = True
                            msg = 'Hiba: 406 - Nem sikerült a frissítés, telepítés!'
                    else:
                        hiba = True
                        msg = 'Hiba: 407 - Nem sikerült a frissítés, telepítés!'
                else:
                    hiba = True
                    msg = 'Hiba: 408 - Nem sikerült a frissítés, telepítés!'
            else:
                hiba = True
                msg = 'Hiba: 409 - Nem sikerült a frissítés, telepítés!'
            if hiba:
                if msg == '':
                    msg = 'Hiba: 410 - Nem sikerült a Webes tartalom telepítése, frissítése!'
                title = 'A Webes tartalom frissítése nemsikerült!'
                desc = 'Indítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
            else:
                title = 'Webes tartalom frissítése - végrehajtva'
                desc = 'Sikerült a Webes tartalom frissítése, telepítése!\n\nIndítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'               
        except Exception:
            title = 'Webes tartalom frissítése nemsikerült!'
            desc = 'Indítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'
        params = dict(cItem)
        params.update({'good_for_fav': False, 'category': 'list_second', 'title': title, 'tab_id': 'web_tr_frissit', 'desc': desc})
        self.addDir(params)            
        if fileExists(destination):
            rm(destination) 
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)            
        return
            
    def ytmtps(self, cItem):
        hiba = False
        msg = ''
        lyt = config.plugins.iptvplayer.ytmedia_dir.value
        url = zlib.decompress(base64.b64decode('eJwFwUEKgDAMBMAfdcGjv4k1mIClIVmF+npnjIzagctpz9H6HNDN45alabNYWBx6ukCym7+KIUXN9nn8tuwXEg=='))
        fname = zlib.decompress(base64.b64decode('eJyrLMlNTclM1KvKLAAAG0IEbw=='))
        destination = self.TEMP + '/' + fname
        destination_dir = self.TEMP + zlib.decompress(base64.b64decode('eJzTryzJTU3JTNTNTSwuSS0CAC14BdY='))
        destination_fo = self.TEMP + zlib.decompress(base64.b64decode('eJzTryzJTU3JTAQADZsDHQ=='))
        fname_zip = destination_dir + '/' + fname
        unzip_command = ['unzip', '-q', '-o', destination, '-d', self.TEMP]
        unzip_command_zip = ['unzip', '-q', '-o', fname_zip, '-d', self.TEMP]
        if fileExists(destination):
            rm(destination)
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        try:        
            if self.dflt(url,destination):
                if fileExists(destination):
                    if GetFileSize(destination) > 0:
                        if self._mycall(unzip_command) == 0:
                            if fileExists(fname_zip):
                                if GetFileSize(fname_zip) > 0:
                                    if self._mycall(unzip_command_zip) == 0:
                                        if mkdirs(lyt):
                                            if self._mycopy_o(destination_fo + '/*',lyt):
                                                hiba = False
                                            else:
                                                hiba = True
                                                msg = 'Hiba: 301 - Nem sikerült a frissítés, telepítés!'
                                        else:
                                            hiba = True
                                            msg = 'Hiba: 302 - Nem sikerült a frissítés, telepítés!'
                                    else:
                                        hiba = True
                                        msg = 'Hiba: 303 - Nem sikerült a frissítés, telepítés!'
                                else:
                                    hiba = True
                                    msg = 'Hiba: 304 - Nem sikerült a frissítés, telepítés!'
                            else:
                                hiba = True
                                msg = 'Hiba: 305 - Nem sikerült a frissítés, telepítés!'
                        else:
                            hiba = True
                            msg = 'Hiba: 306 - Nem sikerült a frissítés, telepítés!'
                    else:
                        hiba = True
                        msg = 'Hiba: 307 - Nem sikerült a frissítés, telepítés!'
                else:
                    hiba = True
                    msg = 'Hiba: 308 - Nem sikerült a frissítés, telepítés!'
            else:
                hiba = True
                msg = 'Hiba: 309 - Nem sikerült a frissítés, telepítés!'
            if hiba:
                if msg == '':
                    msg = 'Hiba: 310 - Nem sikerült a YouTube tartalom telepítése, frissítése!'
                title = 'A YouTube tartalom frissítése nemsikerült!'
                desc = 'Indítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'
                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
            else:
                title = 'YouTube tartalom frissítése - végrehajtva'
                desc = 'Sikerült a YouTube tartalom frissítése, telepítése!\n\nIndítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'               
        except Exception:
            title = 'YouTube tartalom frissítése nemsikerült!'
            desc = 'Indítsd újra a programot!\nNyomd meg a Kilépés gombot!  -  PIROS gomb a távirányítón'
        params = dict(cItem)
        params.update({'good_for_fav': False, 'category': 'list_second', 'title': title, 'tab_id': 'yt_tr_frissit', 'desc': desc})
        self.addDir(params)            
        if fileExists(destination):
            rm(destination) 
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)            
        return
        
    def tfkn(self, mod, fan, pfan):
        fin = self.DEFAULT_ICON_URL
        try:
            if mod != '' and fan != '' and pfan != '':
                if mod == '2': fin = self.ICON_YT
                if fileExists(fan):
                    with open(fan, 'r') as f:
                        for line in f:
                            values = line.split('|')
                            if len(values) == 4:
                                mn = values[0].strip()
                                fn = values[1].strip()
                                ls = values[2].strip()
                                ak = values[3].strip()
                                if '.list' in fn:
                                    fpn = pfan + fn.replace('.list','').strip()
                                    n_st = self.malvadst('1', '10', ak)
                                    if n_st  != '' and self.aid:
                                        self.aid_ki = 'Megnézve: ' + n_st  + '\n\n'
                                    else:
                                        self.aid_ki = ''
                                    desc = self.aid_ki + ls
                                    params = dict()
                                    params.update({'good_for_fav': False, 'category': 'list_third', 'title': mn, 'f_pn': fpn, 'f_nm': fn, 'desc': desc, 'icon': fin, 'azn': ak})
                                    self.addDir(params)
        except Exception:
            return        
        
    def tkn(self, fan, kkl=False):
        hnn = 'nn'
        try:
            if config.plugins.iptvplayer.webmedia_dir.value in fan:
                hnn = 'wm'
            if config.plugins.iptvplayer.ytmedia_dir.value in fan:
                hnn = 'ym'
            data, elso = self.tkn_dt(fan)
            if len(data) == 0: return
            for item in data:
                tov, prdt = self.tkn_it(item, kkl)
                if tov or len(prdt) == 0:
                    continue
                n_st = self.malvadst('1', '10', prdt['azn'])
                if n_st  != '' and self.aid:
                    self.aid_ki = 'Megnézve: ' + n_st
                else:
                    self.aid_ki = ''
                tdsc = re.sub(r'^(.{600}).*$', '\g<1>...', prdt['desc'])
                desc = tdsc + '\n\n' + self.aid_ki
                params = {'title':prdt['title'], 'url':prdt['url'], 'desc':desc, 'icon':prdt['icon'], 'azn':prdt['azn'], 'mkt': elso, 'md':hnn, 'mjnts':True}
                fext = os.path.splitext(prdt['url'])[1]
                if fext in ['.mp3','.acc'] or 'MAGYAR RÁDIÓK' in elso:
                    self.addAudio(params)
                else:
                    self.addVideo(params)
        except Exception:
            return
        
    def tkn_dt(self, fan):
        encoding = 'utf-8'
        data = []
        elso = ''
        try:
            if fan != '':
                if fileExists(fan):
                    with codecs.open(fan, 'r', encoding, 'replace') as fpr:
                        data = fpr.read()
                    if type(data) == type(u''): data = data.encode('utf-8', 'replace')
                    elso = self.cm.ph.getDataBeetwenMarkers(data, '#', '---', False)[1]
                    if len(elso) > 0:
                        elso = elso.replace('\n','').strip()
                    data = self.cm.ph.getAllItemsBeetwenMarkers(data, '', '---\n', False)
        except Exception:
            return [], ''
        return data, elso
        
    def tkn_it(self, it, kkl=False):
        tov = True
        vn = ''
        vu = ''
        vi = ''
        vl = ''
        va = '' 
        vdv = ''
        params = {}
        try:
            stmb = self.cm.ph.getAllItemsBeetwenMarkers(it, '', '\n', False)
            if len(stmb) == 0 or len(stmb) != 6: return tov, params
            if kkl:
                vn = zlib.decompress(base64.b64decode(stmb[0].strip()))
            else:
                vn = stmb[0].strip()
            if len(vn) == 0: return tov, params
            if kkl:
                vu = zlib.decompress(base64.b64decode(stmb[1].strip()))
            else:
                vu = stmb[1].strip()
            if len(vu) == 0: return tov, params
            if kkl:
                vi = zlib.decompress(base64.b64decode(stmb[2].strip()))
            else:
                vi = stmb[2].strip()
            if len(vi) == 0: vi = self.DEFAULT_ICON_URL
            if kkl:
                vl = zlib.decompress(base64.b64decode(stmb[3].strip()))
            else:
                vl = stmb[3].strip()
            if len(vl) == 0: vl = ' '
            if kkl:
                va = zlib.decompress(base64.b64decode(stmb[4].strip()))
            else:
                va = stmb[4].strip()
            if len(va) == 0: return tov, params
            if kkl:
                vdv = zlib.decompress(base64.b64decode(stmb[5].strip()))
            else:
                vdv = stmb[5].strip()
            if len(vdv) == 0: return tov, params
            values = vdv.split('|')
            if len(values) == 2:
                vdvd = values[0].strip()
                vdvv = values[1].strip()
            else:
                return tov, params
            params = {'title':vn, 'url':vu, 'desc':vl, 'icon':vi, 'azn':va, 'datum':vdvd, 'verzio':vdvv}
            return False, params
        except Exception:
            return True, params
            
    def wmpfkr(self):
        encoding = 'utf-8'
        lyt = config.plugins.iptvplayer.webmedia_dir.value
        try:
            if len(self.wupt) > 0 and os.path.isdir(lyt):
                try:
                    with codecs.open(self.WUSG, 'w', encoding, 'replace') as fpw:
                        fpw.write("%s" % self.wupt)
                finally:
                    self.wupt = []
        except Exception:
            return
        
    def ytmpfkr(self):
        encoding = 'utf-8'
        lyt = config.plugins.iptvplayer.ytmedia_dir.value
        try:
            if len(self.yupt) > 0 and os.path.isdir(lyt):
                try:
                    with codecs.open(self.YUSG, 'w', encoding, 'replace') as fpw:
                        fpw.write("%s" % self.yupt)
                finally:
                    self.yupt = []
        except Exception:
            return
    
    def cpve(self, cfpv=''):
        vissza = False
        try:
            if cfpv != '':
                mk = cfpv
                if mk != '':
                    vissza = True
        except Exception:
            return False
        return vissza
        
    def _usable(self):
        msg = ''
        valasz = False
        try:
            if Which('python2') == '':
                msg = 'Hiba: 100 - Python 2.7 kell a használathoz!'
            elif Which('unzip') == '':
                msg = 'Hiba: 101 - unzip kell a használathoz, kérjük telepítsd!'
            elif Which('cp') == '':
                msg = 'Hiba: 102 - cp kell a használathoz, kérjük telepítsd!'
            elif not os.path.isdir(self.IH):
                msg = 'Hiba: 103 - Nem megfelelő E2iPlayer könyvtár!'
            elif FOUND_SUB == False:
                msg = 'Hiba: 104 - Sajnos nem kompatibilis a set-top-box rendszered a használathoz!\nsubprocess modul kell a használathoz, telepítsd!'
            else:
                valasz = True
        except Exception:
            return False, ''
        return valasz, msg
        
    def _mycall(self, cmd):
        command = cmd
        back_state = -1
        try:
            back_state = subprocess.call(command)
        except Exception:
            return -1
        return back_state
        
    def _mycopy(self, filename, dest_dir):
        sikerult = False
        try:
            if filename != '' and dest_dir != '':
                if fileExists(filename):
                    copy_command = ['cp', '-f', filename, dest_dir]
                    if self._mycall(copy_command) == 0:
                        sikerult = True
        except Exception:
            return False
        return sikerult
        
    def _mycopy_o(self, filename, dest_dir):
        sikerult = False
        try:
            if filename != '' and dest_dir != '':
                copy_command = 'cp -rf ' + filename + ' ' + dest_dir
                if subprocess.call(copy_command, shell=True) == 0:
                    sikerult = True
        except Exception:
            return False
        return sikerult
        
    def dflt(self, url, fnm, hsz=2, ved=3):
        vissza = False
        try:
            if url == '' or fnm == '' or type(hsz) != int or type(ved) != int:
                return vissza
            for i in range(hsz):
                tmp = DownloadFile(url,fnm)
                if tmp:
                    vissza = True
                    break
                else:
                    sleep(ved)
        except Exception:
            return False
        return vissza
        
    def malvadst(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu}
        t_s = ''
        temp_vn = ''
        temp_vni = ''
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a_div', '</div>')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '/>')
                if len(data) == 0: return t_s
                for item in data:
                    t_i = self.cm.ph.getSearchGroups(item, 'id=[\'"]([^"^\']+?)[\'"]')[0]
                    if t_i == 'vn':
                        temp_vn = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                    elif t_i == 'vni':
                        temp_vni = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                if temp_vn != '':
                    t_s = temp_vn
            return t_s
        except Exception:
            return t_s
        
    def susn(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu, 'hv':self.vivn, 'orv':self.porv, 'bts':self.pbtp}
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
            
    def gits(self):
        bv = '-'
        tt = []
        try:
            if fileExists(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE'))):
                fr = open(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE')),'r')
                for ln in fr:
                    ln = ln.rstrip('\n')
                    if ln != '':
                        tt.append(ln)
                fr.close()
                if len(tt) == 1:
                    bv = tt[0].strip()[:-6].capitalize()
                if len(tt) == 2:
                    bv = tt[1].strip()[:-6].capitalize()
            return bv
        except:
            return '-'
        
    def getArticleContent(self, cItem):
        try:
            artID = cItem.get('art_id', '')
            if artID == 'foinformacio':
                return self.fgtac(cItem)
            else:
                return []
        except Exception:
            return
            
    def bladt(self, wtt='', ktt= True):
        szv = ''
        sztv = ''
        try:
            if ktt:
                sztv = wtt
            if wtt != '' and sztv != '':
                szv = zlib.compress(sztv)
        except Exception:
            return ''
        return szv
            
    def fgtac(self, cItem):
        try:
            self.susn('2', '10', 'hu_informacio')
            title_citem = cItem['title']
            icon_citem = cItem['icon']
            desc = 'Észrevételeidet, javaslataidat a következő címre küldheted el:\n' + zlib.decompress(base64.b64decode('eJwrT03KKC3ISaxMLXJIz03MzNFLzs8FAF5sCGA=')) + '\n\nFelhívjuk figyelmedet, hogy egyes csatornák online adásai átmenetileg szünetelhetnek. Mielőtt hibát jelzel, ellenőrizd az adott csatorna internetes oldalán az adás működését.\n\nA rádiócsatornák zökkenőmentes hallgatásához javasoljuk az exteplayer3 használatát pufferelés nélküli módban!\n\nKellemes szórakozást kívánunk!\n(Alec, Blindspot)'            
            retList = {'title':title_citem, 'text': desc, 'images':[{'title':'', 'url':icon_citem}]}
            return [retList]
        except Exception:
            return
                
    def getLinksForVideo(self, cItem):
        try:
            azn = cItem['azn']
            self.susn('2', '10', azn)
            self.ulsnztt(cItem)
            videoUrls = []
            if 'picture' == cItem['type']:
                uri = urlparser.decorateParamsFromUrl(cItem['url'], True)
                videoUrls.append({'name':'picture link', 'url':uri})
            else:
                if cItem['url'] == "https://archivum.mtva.hu/m3/stream?target=live":
                    sts, data = self.cm.getPage(cItem['url'])
                    if not sts:
                        return
                    data = self.cm.ph.getDataBeetwenMarkers(data, '"url":"', '","', False)[1]
                    data = data.replace('\/', '/')
                    cItem['url'] = data
                if "https://onlinestream.live/" in cItem['url']:
                    sts, data = self.cm.getPage(cItem['url'])
                    if not sts:
                        return
                    dat = self.cm.ph.getDataBeetwenMarkers(data, '</li><li><a target="_blank" href="', '"><span>', False) [1]
                    cItem['url'] = dat
                uri = urlparser.decorateParamsFromUrl(cItem['url'])
                protocol = uri.meta.get('iptv_proto', '')
                urlSupport = self.up.checkHostSupport( uri )
                if 1 == urlSupport:
                    retTab = self.up.getVideoLinkExt( uri )
                    videoUrls.extend(retTab)
                elif 0 == urlSupport and self._uriIsValid(uri):
                    if protocol == 'm3u8':
                        retTab = getDirectM3U8Playlist(uri, checkExt=False, checkContent=True)
                        videoUrls.extend(retTab)
                    elif protocol == 'f4m':
                        retTab = getF4MLinksWithMeta(uri)
                        videoUrls.extend(retTab)
                    elif protocol == 'mpd':
                        retTab = getMPDLinksWithMeta(uri, False)
                        videoUrls.extend(retTab)
                    else:
                        videoUrls.append({'name':'direct link', 'url':uri})
            if cItem['mjnts']:
                tid = ''
                if len(cItem['desc']) > 0:
                    dsct = cItem['desc']
                    idx1 = dsct.find('\n\n')
                    if -1 < idx1:
                        tid = dsct[0:idx1].strip()
                        tid = re.sub(r'^(.{600}).*$', '\g<1>...', tid)
                self.susmrgts('2', '10', '0', cItem['url'], cItem['title'], cItem['icon'], tid, cItem['azn'], cItem['mkt'], cItem['md'], 'mnez')
            return videoUrls
        except Exception:
            return
            
    def getVideoLinks(self, videoUrl):
        urlTab = []
        urlTab = [{'name':'direct link', 'url':videoUrl}]
        return urlTab
            
    def mtem(self, pi, pt, pti, pd):
        params = dict()
        if pi != '' and pt != '' and pti != '' and pd != '':
            if pi == '1':
                tsz, dsz = self.wsvoes()
                tt = pt + tsz
                dd = pd + '\n' + dsz 
            if pi == '2':
                tsz, dsz = self.yvoes()
                tt = pt + tsz
                dd = pd + '\n' + dsz
            params = {'category': 'list_second', 'title': tt, 'tab_id': pti, 'desc': dd}
        return params
        
    def getdvdsz(self, pu='', psz=''):
        bv = ''
        if pu != '' and psz != '':
            n_atnav = self.malvadst('1', '10', pu)
            if n_atnav != '' and self.aid:
                if pu == 'hu_webes_tartalom':
                    self.aid_ki = 'Web HU Player  v' + HOST_VERSION + '\nMegnézve: ' + n_atnav + '\n\n'
                else:
                    self.aid_ki = 'Megnézve: ' + n_atnav + '\n\n'
            else:
                if pu == 'hu_webes_tartalom':
                    self.aid_ki = 'Web HU Player  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = ''
            bv = self.aid_ki + psz
        return bv
        
    def wsvoes(self):
        vsz = ''
        dsz = ''
        evo = 0
        uvo = 0
        kkl = False
        lyt = config.plugins.iptvplayer.webmedia_dir.value
        url = zlib.decompress(base64.b64decode('eJwFwWEKgDAIBtAbTehnt3HbRwrJRK2o0/eeVHnuRIeWXL2NZYRN/eQXISsr6UE3TGXiGKI3yDgL0T71H8yHF2M='))
        fname = zlib.decompress(base64.b64decode('eJwrT03KTU3JTNSryiwAAB9HBMA='))
        destination = self.TEMP + '/' + fname
        destination_dir = self.TEMP + zlib.decompress(base64.b64decode('eJzTL09Nyk1NyUzUzU0sLkktAgAynwYn'))
        destination_fo = self.TEMP + zlib.decompress(base64.b64decode('eJzTL09Nyk1NyUwEABCLA24='))
        fname_zip = destination_dir + '/' + fname
        unzip_command = ['unzip', '-q', '-o', destination, '-d', self.TEMP]
        unzip_command_zip = ['unzip', '-q', '-o', fname_zip, '-d', self.TEMP]
        if not os.path.isdir(lyt) or len(self.whuav) == 0:
            vsz = '  -  Telepítés szükséges'
            dsz = 'Telepíteni kell a Web média tartalmat!  OK gomb megnyomása után a tartalom települ. A telepítés időigényes lehet...'
            return vsz, dsz
        if fileExists(destination):
            rm(destination)
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        try:        
            if self.dflt(url,destination):
                if fileExists(destination):
                    if GetFileSize(destination) > 0:
                        if self._mycall(unzip_command) == 0:
                            if fileExists(fname_zip):
                                if GetFileSize(fname_zip) > 0:
                                    if self._mycall(unzip_command_zip) == 0:
                                        if os.path.isdir(destination_fo):
                                            for root, dirs, files in os.walk(destination_fo):
                                                dirs.sort()
                                                for filename in sorted(files):
                                                    fname_with_path = os.path.join(root, filename)
                                                    fext = os.path.splitext(fname_with_path)[1]
                                                    if fext in ['.stream','.kstream']:
                                                        if '.kstream' in fname_with_path: kkl = True
                                                        fn = fname_with_path.replace(destination_fo, '')
                                                        if not fileExists(lyt + fn):
                                                            uv = self.rstredb('1', fname_with_path, kkl)
                                                            uvo += uv
                                                        else:
                                                            ev, uv = self.rstre('1', lyt + fn, fname_with_path, kkl)
                                                            evo += ev
                                                            uvo += uv
                                            if evo == 0 and uvo == 0:
                                                dsz = 'Nincs semmi teendő!  A Web média tartalom megfelelő.'
                                            else:
                                                vsz = '  -  Frissítés szükséges'
                                                if uvo > 0:
                                                    if evo > 0:
                                                        dsz = str(uvo) + ' új műsor és ' + str(evo) + ' módosult műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
                                                    else:
                                                        dsz = str(uvo) + ' új műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
                                                else:
                                                    dsz = str(evo) + ' módosult műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
        except Exception:
            if fileExists(destination):
                rm(destination) 
                rmtree(destination_dir, ignore_errors=True)
                rmtree(destination_fo, ignore_errors=True)            
            return vsz, dsz
        if fileExists(destination):
            rm(destination) 
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        return vsz, dsz
        
    def ebbtit(self):
        try:
            if '' == self.btps.strip() or '' == self.brdr.strip():
                msg = 'A Set-top-Box típusát és a használt rendszer (image) nevét egyszer meg kell adni!\n\nA kompatibilitás és a megfelelő használat miatt kellenek ezek az adatok a programnak.\nKérlek, a helyes működéshez a valóságnak megfelelően írd be azokat.\n\nA "HU Telepítő" keretrendszerben tudod ezt megtenni.\n\nKilépek és megyek azt beállítani?'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                return False
            else:
                return True
        except Exception:
            return False
        
    def yvoes(self):
        vsz = ''
        dsz = ''
        evo = 0
        uvo = 0
        kkl = False
        lyt = config.plugins.iptvplayer.ytmedia_dir.value
        url = zlib.decompress(base64.b64decode('eJwFwUEKgDAMBMAfdcGjv4k1mIClIVmF+npnjIzagctpz9H6HNDN45alabNYWBx6ukCym7+KIUXN9nn8tuwXEg=='))
        fname = zlib.decompress(base64.b64decode('eJyrLMlNTclM1KvKLAAAG0IEbw=='))
        destination = self.TEMP + '/' + fname
        destination_dir = self.TEMP + zlib.decompress(base64.b64decode('eJzTryzJTU3JTNTNTSwuSS0CAC14BdY='))
        destination_fo = self.TEMP + zlib.decompress(base64.b64decode('eJzTryzJTU3JTAQADZsDHQ=='))
        fname_zip = destination_dir + '/' + fname
        unzip_command = ['unzip', '-q', '-o', destination, '-d', self.TEMP]
        unzip_command_zip = ['unzip', '-q', '-o', fname_zip, '-d', self.TEMP]
        if not os.path.isdir(lyt) or len(self.whuav) == 0:
            vsz = '  -  Telepítés szükséges'
            dsz = 'Telepíteni kell a YouTube média tartalmat!  OK gomb megnyomása után a tartalom települ. A telepítés időigényes lehet...'
            return vsz, dsz
        if fileExists(destination):
            rm(destination)
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        try:        
            if self.dflt(url,destination):
                if fileExists(destination):
                    if GetFileSize(destination) > 0:
                        if self._mycall(unzip_command) == 0:
                            if fileExists(fname_zip):
                                if GetFileSize(fname_zip) > 0:
                                    if self._mycall(unzip_command_zip) == 0:
                                        if os.path.isdir(destination_fo):
                                            for root, dirs, files in os.walk(destination_fo):
                                                dirs.sort()
                                                for filename in sorted(files):
                                                    fname_with_path = os.path.join(root, filename)
                                                    fext = os.path.splitext(fname_with_path)[1]
                                                    if fext in ['.stream','.kstream']:
                                                        if '.kstream' in fname_with_path: kkl = True
                                                        fn = fname_with_path.replace(destination_fo, '')
                                                        if not fileExists(lyt + fn):
                                                            uv = self.rstredb('2', fname_with_path, kkl)
                                                            uvo += uv
                                                        else:
                                                            ev, uv = self.rstre('2', lyt + fn, fname_with_path, kkl)
                                                            evo += ev
                                                            uvo += uv
                                            if evo == 0 and uvo == 0:
                                                dsz = 'Nincs semmi teendő!  A YouTube média tartalom megfelelő.'
                                            else:
                                                vsz = '  -  Frissítés szükséges'
                                                if uvo > 0:
                                                    if evo > 0:
                                                        dsz = str(uvo) + ' új műsor és ' + str(evo) + ' módosult műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
                                                    else:
                                                        dsz = str(uvo) + ' új műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
                                                else:
                                                    dsz = str(evo) + ' módosult műsor található!  OK gomb megnyomása után a tartalom frissíthető.'
        except Exception:
            if fileExists(destination):
                rm(destination) 
                rmtree(destination_dir, ignore_errors=True)
                rmtree(destination_fo, ignore_errors=True)            
            return vsz, dsz
        if fileExists(destination):
            rm(destination) 
            rmtree(destination_dir, ignore_errors=True)
            rmtree(destination_fo, ignore_errors=True)
        return vsz, dsz
        
    def ulsnztt(self, cItem):
        encoding = 'utf-8'
        tfn = self.whuunz + '.writing'
        ln = 0
        kszv = ''
        tp = []
        dpt = {}
        lyt = config.plugins.iptvplayer.webhuplayer_dir.value
        try:
            if len(cItem) > 0:
                dsct = cItem['desc']
                mdt = cItem['md']
                if mdt == 'wm': kszv = 'A tartalom elérhetősége a megnézésekor:\nWebes tartalmak -> ' + cItem['mkt']
                if mdt == 'ym': kszv = 'A tartalom elérhetősége a megnézésekor:\nYouTube tartalmak -> ' + cItem['mkt']
                idx1 = dsct.find('\n\n')
                if -1 < idx1:
                    desc = dsct[0:idx1].strip()
                    desc += '\n\n' + kszv
                dpt = {'title':self.esklsz('3',cItem['title']), 'url':self.esklsz('3',cItem['url']), 'desc':self.esklsz('3',desc), 'icon':self.esklsz('3',cItem['icon']), 'azn':self.esklsz('3',cItem['azn']), 'mkt':self.esklsz('3',cItem['mkt']), 'md':self.esklsz('3',cItem['md'])}
                if fileExists(self.whuunz):
                    try:
                        fpw = codecs.open(tfn, 'w', encoding, 'replace')
                        fpw.write("%s\n" % dpt)
                        tp.append(self.esklsz('3',cItem['azn']))
                        with codecs.open(self.whuunz, 'r', encoding, 'replace') as fpr:
                            for line in fpr:
                                ln += 1
                                if type(line) == type(u''): line = line.encode('utf-8', 'replace')
                                line = line.replace('\n', '').strip()
                                if len(line) > 0:
                                    d1 = self.cm.ph.getAllItemsBeetwenMarkers(line, '{', '}', False)
                                    if len(d1) == 0: return
                                    for i1 in d1:
                                        d2 = i1.split("',")
                                        if len(d2) == 0: return
                                        for i2 in d2:
                                            d3 = i2.split(': ')
                                            if len(d3) != 2: return
                                            tv1 = d3[0].strip().replace("'","")
                                            if tv1 == 'azn':
                                                pa = d3[1].strip().replace("'","")
                                            if tv1 == 'url':
                                                pu = d3[1].strip().replace("'","")
                                            if tv1 == 'desc':
                                                pd = d3[1].strip().replace("'","")
                                            if tv1 == 'icon':
                                                pi = d3[1].strip().replace("'","")
                                            if tv1 == 'title':
                                                pt = d3[1].strip().replace("'","")
                                            if tv1 == 'mkt':
                                                pmt = d3[1].strip().replace("'","")
                                            if tv1 == 'md':
                                                pmd = d3[1].strip().replace("'","")
                                    if pa in tp:
                                        continue
                                    else:
                                        if pt != '' and pu != '' and pd != '' and pi != '' and pa != '' and pmt != '' and  pmd != '':
                                            tp.append(pa)
                                            tdpt = {'title':pt, 'url':pu, 'desc':pd, 'icon':pi, 'azn':pa, 'mkt':pmt, 'md':pmd}
                                            fpw.write("%s\n" % tdpt)
                                            if ln > 30:
                                                break
                        fpw.flush()
                        os.fsync(fpw.fileno())
                        fpw.close()
                        os.rename(tfn, self.whuunz)
                    except Exception:
                        if fileExists(tfn):
                            rm(tfn)
                else:
                    if len(dpt) > 0:
                        if os.path.isdir(lyt):
                            with codecs.open(self.whuunz, 'w', encoding, 'replace') as fpw:
                                fpw.write("%s\n" % dpt)
                        else:
                            if mkdirs(lyt): 
                                with codecs.open(self.whuunz, 'w', encoding, 'replace') as fpw:
                                    fpw.write("%s\n" % dpt)
                            else:
                                msg = 'A Web HU Player könyvtára nem hozható létre!\nA kék gomb, majd az Oldal beállításai segítségével megadhatod a kért adatokat.\nHa megfelelőek az előre beállított értékek, akkor ZÖLD gomb (Mentés) megnyomása!'
                                self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 20 )
                                
            if fileExists(tfn):
                rm(tfn)
        except Exception:
            return        

    def rstredb(self, mi='1', rfn='', kkl=False):
        uv = 0
        try:
            if rfn != '':
                data, elso = self.tkn_dt(rfn)
                if len(data) == 0: return 0
                for item in data:
                    tov, prdt = self.tkn_it(item, kkl)
                    if tov or len(prdt) == 0:
                        continue
                    else:
                        uv += 1
                        if mi == '1':
                            desc = prdt['desc'] + '\n\nWebes tartalmak:\n' + elso
                            params = {'title':self.esklsz('3',prdt['title']), 'url':self.esklsz('3',prdt['url']), 'desc':self.esklsz('3',desc), 'icon':self.esklsz('3',prdt['icon']), 'azn':self.esklsz('3',prdt['azn']), 'mkt':self.esklsz('3',elso), 'md':self.esklsz('3','wm')}
                            self.wupt.append(params)
                        if mi == '2':
                            desc = prdt['desc'] + '\n\nYouTube tartalmak:\n' + elso
                            params = {'title':self.esklsz('3',prdt['title']), 'url':self.esklsz('3',prdt['url']), 'desc':self.esklsz('3',desc), 'icon':self.esklsz('3',prdt['icon']), 'azn':self.esklsz('3',prdt['azn']), 'mkt':self.esklsz('3',elso), 'md':self.esklsz('3','ym')}
                            self.yupt.append(params)
        except Exception:
            return 0
        return uv
        
    def rstre(self, mi='1', lfn='', rfn='', kkl=False):
        ev = 0
        uv = 0
        try:
            if lfn != '' and rfn != '':
                data, elso = self.tkn_dt(rfn)
                if len(data) == 0: return 0, 0
                for item in data:
                    tov, prdt = self.tkn_it(item, kkl)
                    if tov or len(prdt) == 0:
                        continue
                    bvv, bvnv = self.lwhuv(prdt['azn'], prdt['verzio'])
                    if bvv:
                        if bvnv:
                            ev += 1
                    else:
                        uv += 1
                        if mi == '1':
                            desc = prdt['desc'] + '\n\nWebes tartalmak:\n' + elso
                            params = {'title':self.esklsz('3',prdt['title']), 'url':self.esklsz('3',prdt['url']), 'desc':self.esklsz('3',desc), 'icon':self.esklsz('3',prdt['icon']), 'azn':self.esklsz('3',prdt['azn']), 'mkt':self.esklsz('3',elso), 'md':self.esklsz('3','wm')}
                            self.wupt.append(params)
                        if mi == '2':
                            desc = prdt['desc'] + '\n\nYouTube tartalmak:\n' + elso
                            params = {'title':self.esklsz('3',prdt['title']), 'url':self.esklsz('3',prdt['url']), 'desc':self.esklsz('3',desc), 'icon':self.esklsz('3',prdt['icon']), 'azn':self.esklsz('3',prdt['azn']), 'mkt':self.esklsz('3',elso), 'md':self.esklsz('3','ym')}
                            self.yupt.append(params)
        except Exception:
            return 0, 0
        return ev, uv
        
    def susmrgts(self, i_md='', i_hgk='', i_mptip='', i_mpu='', i_mpt='', i_mpi='', i_mpdl='', i_mpaz='', i_mput='', i_mpmd='', i_mpnzs=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        try:
            if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
            if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
            if i_mpu != '': i_mpu = base64.b64encode(i_mpu).replace('\n', '').strip()
            if i_mpt != '': i_mpt = base64.b64encode(i_mpt).replace('\n', '').strip()
            if i_mpi == '':
                i_mpi = base64.b64encode('-')
            else:
                i_mpi = base64.b64encode(i_mpi).replace('\n', '').strip()
            if i_mpdl == '':
                i_mpdl = base64.b64encode('-')
            else:
                i_mpdl = base64.b64encode(i_mpdl).replace('\n', '').strip()
            if i_mpaz == '':
                i_mpaz = base64.b64encode('-')
            else:
                i_mpaz = base64.b64encode(i_mpaz).replace('\n', '').strip()
            if i_mput == '':
                i_mput = base64.b64encode('-')
            else:
                i_mput = base64.b64encode(i_mput).replace('\n', '').strip()
            if i_mpmd == '':
                i_mpmd = base64.b64encode('-')
            else:
                i_mpmd = base64.b64encode(i_mpmd).replace('\n', '').strip()
            if i_mpnzs != '': i_mpnzs = base64.b64encode(i_mpnzs).replace('\n', '').strip()
            pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpu':i_mpu, 'mpt':i_mpt, 'mpi':i_mpi, 'mpdl':i_mpdl, 'mpaz':i_mpaz, 'mput':i_mput, 'mpmd':i_mpmd, 'mpnzs':i_mpnzs}
            if i_md != '' and i_hgk != '' and i_mptip != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
        
    def lwhuv(self, azn='', pv=''):
        bvv = False
        bvnv = False
        try:
            if azn != '' and pv != '':
                if len(self.whuav) > 0:
                    for key, val in self.whuav.items():
                        if key == azn:
                            if val != pv:
                                bvnv = True
                            bvv = True
                            break
        except Exception:
            return False, False
        return bvv, bvnv
        
    def esklsz(self, bk='3', gste='', beert=True):
        kszvdrtk = ''
        tts = ''
        ttsk = ''
        try:
            i = 0
            if gste != '':
                if bk == '3':
                    tts = 'yes'
            egylszt = True
            if gste != '':
                if bk == '5':
                    ttsk = 'no'                
            if beert:
                egylszt = False
            if beert and gste != '' and bk == '3':
                kszvdrtk = base64.encodestring(zlib.compress(gste)).replace('\n', '').strip()
                if bk == '2':
                    i = 2
            else:
                i += 1
            if bk == '5':
                i = 3
                if gste != '':
                    kszvdrtk = zlib.decompress(base64.b64decode(gste))
        except Exception:
            return ''
        return kszvdrtk
        
    def malvadnav(self, cItem, i_md='', i_hgk='', i_mptip=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        t_s = []
        try:
            if i_md != '' and i_hgk != '' and i_mptip != '':
                if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip}
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a1_div"', '<div id="div_a2_div"')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="d_sor_d"', '</div>')
                if len(data) == 0: return t_s
                for temp_item in data:
                    temp_data = self.cm.ph.getAllItemsBeetwenMarkers(temp_item, '<span', '</span>')
                    if len(temp_data) == 0: return t_s
                    for item in temp_data:
                        t_vp = self.cm.ph.getSearchGroups(item, 'class=[\'"]([^"^\']+?)[\'"]')[0]
                        if t_vp == 'c_sor_u':
                            temp_u = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_u">', '</span>', False)[1]
                            if temp_u != '': temp_u = base64.b64decode(temp_u)
                        if t_vp == 'c_sor_t':
                            temp_t = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_t">', '</span>', False)[1]
                            if temp_t != '': temp_t = base64.b64decode(temp_t)
                        if t_vp == 'c_sor_i':
                            temp_i = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_i">', '</span>', False)[1]
                            if temp_i != '': temp_i = base64.b64decode(temp_i)
                        if t_vp == 'c_sor_l':
                            temp_l = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_l">', '</span>', False)[1]
                            if temp_l != '': temp_l = base64.b64decode(temp_l)
                        if t_vp == 'c_sor_n':
                            temp_n = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_n">', '</span>', False)[1]
                            if temp_n != '': temp_n = base64.b64decode(temp_n)
                        if t_vp == 'c_sor_tip':
                            temp_tp = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_tip">', '</span>', False)[1]
                            if temp_tp != '': temp_tp = base64.b64decode(temp_tp)
                        if t_vp == 'c_sor_ut':
                            temp_tut = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_ut">', '</span>', False)[1]
                            if temp_tut != '': temp_tut = base64.b64decode(temp_tut)
                        if t_vp == 'c_sor_az':
                            temp_az = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_az">', '</span>', False)[1]
                            if temp_az != '': temp_az = base64.b64decode(temp_az)
                        if t_vp == 'c_sor_md':
                            temp_md = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_md">', '</span>', False)[1]
                            if temp_md != '': temp_md = base64.b64decode(temp_md)
                    if temp_u == '' and temp_t =='': continue
                    if temp_n == '': temp_n = '1'
                    params = MergeDicts(cItem, {'good_for_fav': False, 'url':temp_u, 'title':temp_t, 'icon':temp_i, 'desc':temp_l, 'nztsg':temp_n, 'tps':temp_tp, 'azn':temp_az, 'mkt': temp_tut, 'md':temp_md})
                    t_s.append(params)       
            return t_s
        except Exception:
            return []
    
    def gvsn(self, fn=''):
        verzio = 0
        verzio_tmp = 0
        datum = ''
        datum_tmp = ''
        sorList = []
        fnv = fn
        try:
            if fnv != '':
                f = open(fnv, 'r')
                fl1 = f.readline()
                fl2 = f.readline()
                fl3 = f.readline()
                fl4 = f.readline()
                fl5 = f.readline()
                fl6 = f.readline()
                fl7 = f.readline()
                fl8 = f.readline()
                f.close
                if len(fl1) == '': return verzio, datum
                if '#' != fl1[0]: return verzio, datum
                sorList = fl8.split("|")
                if len(sorList) != 2: 
                    return verzio, datum
                m1 = re.search(r'[2]\d{3}-\d{2}-\d{2}',sorList[0])
                if m1 is not None:
                    datum_tmp = m1.group(0)
                if datum_tmp != '':
                    datum = datum_tmp
                m2 = re.search(r'\d+.\d+',fl1)
                if m2 is not None:
                    verzio_tmp = m2.group(0)
                if verzio_tmp == '':
                    verzio = 0
                else:
                    verzio = verzio_tmp
        except Exception:
            verzio = 0
            datum = ''
        return verzio, datum
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 's_webes':
                self.wssrtrtmk(cItem, searchPattern, searchType)
            elif tabID == 's_yt':
                self.ytsrtrtmk(cItem, searchPattern, searchType)
            else:
                return
        except Exception:
            return
        return
        
    def wssrtrtmk(self, cItem, searchPattern, searchType):
        self.susn('2', '10', 'hu_webes_kereses')
        return
        
    def ytsrtrtmk(self, cItem, searchPattern, searchType):
        self.susn('2', '10', 'hu_yt_kereses')
        return
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        try:
            CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
            name     = self.currItem.get("name", '')
            category = self.currItem.get("category", '')
            self.currList = []
            if name == None:
                self.listMainMenu( {'name':'category'} )
            elif category == 'list_main':
                self.listMainItems(self.currItem)
            elif category == 'list_second':
                self.listSecondItems(self.currItem)
            elif category == 'list_third':
                self.listThirdItems(self.currItem)
            elif category == 'list_fourth':
                self.listFourthItems(self.currItem)
            elif category == 'list_fifth':
                self.listFifthItems(self.currItem)
            elif category == 'list_six':
                self.listSixItems(self.currItem)
            elif category in ['search', 'search_next_page']:
                cItem = dict(self.currItem)
                cItem.update({'search_item':False, 'name':'category'}) 
                self.listSearchResult(cItem, searchPattern, searchType)
            elif category == 'search_history':
                self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
            else:
                printExc()
            CBaseHostClass.endHandleService(self, index, refresh)
        except Exception:
            return

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, webhuplayer(), True, [])

    def _isPicture(self, url):
        def _checkExtension(url): 
            return url.endswith(".jpeg") or url.endswith(".jpg") or url.endswith(".png")
        if _checkExtension(url): return True
        if _checkExtension(url.split('|')[0]): return True
        if _checkExtension(url.split('?')[0]): return True
        return False

    def getLinksForVideo(self, Index = 0, selItem = None):
        try:
            listLen = len(self.host.currList)
            if listLen < Index and listLen > 0:
                return RetHost(RetHost.ERROR, value = [])
            if self.host.currList[Index]["type"] != 'video':
                return RetHost(RetHost.ERROR, value = [])
            retlist = []
            uri = self.host.currList[Index].get('url', '')
            urlList = self.host.getLinksForVideo(self.host.currList[Index])
            for item in urlList:
                retlist.append(CUrlItem(item["name"], item["url"], 0))
            return RetHost(RetHost.OK, value = retlist)
        except Exception:
            return

    def convertList(self, cList):
        try:
            hostList = []
            searchTypesOptions = []
            for cItem in cList:
                hostLinks = []
                type = CDisplayListItem.TYPE_UNKNOWN
                possibleTypesOfSearch = None
                if cItem['type'] == 'category':
                    if cItem['title'] == 'Keresés':
                        type = CDisplayListItem.TYPE_SEARCH
                        possibleTypesOfSearch = searchTypesOptions
                    else:
                        type = CDisplayListItem.TYPE_CATEGORY
                elif cItem['type'] == 'video':
                    type = CDisplayListItem.TYPE_VIDEO
                    url = cItem.get('url', '')
                    if self._isPicture(url):
                        type = CDisplayListItem.TYPE_PICTURE
                    else:
                        type = CDisplayListItem.TYPE_VIDEO
                    if '' != url:
                        hostLinks.append(CUrlItem("Link", url, 1))
                elif cItem['type'] == 'article':
                    type = CDisplayListItem.TYPE_ARTICLE
                elif cItem['type'] == 'marker':
                    type = CDisplayListItem.TYPE_MARKER
                elif cItem['type'] == 'audio':
                    type = CDisplayListItem.TYPE_AUDIO
                    url = cItem.get('url', '')
                    if '' != url:
                        hostLinks.append(CUrlItem("Link", url, 1))
                title       =  cItem.get('title', '')
                description =  cItem.get('desc', '')
                icon        =  cItem.get('icon', '')
                if len(icon) == 0: icon = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1S9PTcooLchJrEwtis/JT8/XyypIBwDbUhM+'))
                hostItem = CDisplayListItem(name = title,
                                            description = description,
                                            type = type,
                                            urlItems = hostLinks,
                                            urlSeparateRequest = 1,
                                            iconimage = icon,
                                            possibleTypesOfSearch = possibleTypesOfSearch)
                hostList.append(hostItem)
            return hostList
        except Exception:
            return
            
    def withArticleContent(self, cItem):
        if cItem['type'] != 'article':
            return False
        return True
        
    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except Exception:
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except Exception:
            self.searchPattern = ''
            self.searchType = ''
        return
