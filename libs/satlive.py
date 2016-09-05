# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import time
import base64
try:    import simplejson as json
except: import json
from os import path as os_path
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

config.plugins.iptvplayer.satlivetv_premium                = ConfigYesNo(default = False)
config.plugins.iptvplayer.satlivetv_login                  = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.satlivetv_password               = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry('web-live.tv ' + _("premium user?"), config.plugins.iptvplayer.satlivetv_premium))
    if config.plugins.iptvplayer.satlivetv_premium.value:
        optionList.append(getConfigListEntry('web-live.tv ' + _("login") + ':', config.plugins.iptvplayer.satlivetv_login))
        optionList.append(getConfigListEntry('web-live.tv ' + _("password") + ':', config.plugins.iptvplayer.satlivetv_password))
    return optionList
###################################################

class SatLiveApi:
    MAINURL      = 'http://web-live.tv/'
    LIST_URL     = MAINURL + 'transmissions/transmission/index'
    SWF_URL      = MAINURL + 'themes/default/swf/jwplayer.flash.swf'
    LOGIN_URL    = MAINURL + 'site/site/login'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('satlivetv.cookie')
        self.cm = common()
        self.sessionEx = MainSessionWrapper()
        self.loggedIn  = True
        self.http_params = {}
        
        #self._reInit()
        #self.channelsList = []

    def getChannelsList(self):
        printDBG("SatLiveApi.getChannelsList")
        
        # login
        premium  = config.plugins.iptvplayer.satlivetv_premium.value
        login    = config.plugins.iptvplayer.satlivetv_login.value
        password = config.plugins.iptvplayer.satlivetv_password.value
        if premium:        
            if self.doLogin(login, password):
                self.loggedIn = True
                self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
            else:
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % login, type = MessageBox.TYPE_INFO, timeout = 10 )

        # get channels
        channelsList = []
        sts, data = self.cm.getPage(SatLiveApi.LIST_URL, self.http_params)
        if not sts:
            return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab-pane active" id="live">', '<div class="tab-pane" id="all">', False)[1]
        data = data.split('</li>')
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, '<h4><a href="([^"]+?)">([^<]+?)</a></h4>', 2)
            if '' != tmp[0]:
                params = {}
                params['url']   = SatLiveApi.MAINURL + tmp[0]
                params['title'] = tmp[1]
                icon = self.cm.ph.getSearchGroups(item, '<img class="" src="([^"]+?)"')[0]
                if '' != icon:
                    params['icon']  = SatLiveApi.MAINURL + icon
                params['desc']      = self.cm.ph.removeDoubles(clean_html(item.replace('>', '> ')).replace('\t', ' '), ' ')
                channelsList.append(params)
        if True:
                                                                                                                                                                                                                                                                                        num = 1
                                                                                                                                                                                                                                                                                        m = 'eyI1NzkiOiAiVFZQIDEiLCAiNjA0IjogIlBvbHNhdCBTcG9ydCIsICI2MTgiOiAiUG9sc2F0IFNwb3J0IiwgIjU3MiI6ICJUQ00iLCAiNjA2IjogIlBvbHNhdCBTcG9ydCBFeHRyYSIsICI2MDAiOiAiQ2FuYWwrIFNwb3J0IiwgIjYwMiI6ICJQb2xzYXQiLCAiNDY5IjogIkhCTyBbSERdIiwgIjEyMCI6ICJBWE4gV2hpdGUiLCAiOTgiOiAiTmF0R2VvIiwgIjEyMiI6ICJOYXRHZW8gV2lsZCIsICI5MyI6ICJIQk8iLCAiOTQiOiAiSEJPIDIiLCAiOTciOiAiQ2luZW1heCAyIiwgIjU5MSI6ICJDYW5hbCsgW0hEXSIsICI1OTAiOiAiTWluaU1pbmkiLCAiNTkzIjogIkNhbmFsKyBGaWxtIiwgIjU5MiI6ICJDYW5hbCsiLCAiNjAxIjogIlBvbHNhdCBbSERdIiwgIjU5NCI6ICJBbGVLaW5vKyIsICI1OTciOiAiQ2FuYWwrIFNlcmlhbGUiLCAiNTk2IjogIlRlbGVUb29uIiwgIjU5OSI6ICJDYW5hbCsgRmFtaWx5IiwgIjU5OCI6ICJDYW5hbCsiLCAiMTE0IjogIkRpc2NvdmVyeSBTY2llbmNlIiwgIjExNyI6ICJEaXNuZXkgSnVuaW9yIiwgIjExMCI6ICJEaXNuZXkgWEQiLCAiMTEyIjogIkZpbG1ib3giLCAiMTE5IjogIkZPWCIsICIxMTgiOiAiVHJhdmVsIENoYW5uZWwiLCAiNTI4IjogIlR1cmJvIFh0cmEiLCAiNTg3IjogIm5TcG9ydCIsICI1ODQiOiAiVFZQIFNlcmlhbGUiLCAiNTg1IjogIlRWUCBTcG9ydCIsICI1ODIiOiAiVFZQIDIgW0hEXSIsICI1ODMiOiAiVFZQIEluZm8iLCAiNTgwIjogIlRWUCAxIFtIRF0iLCAiNTgxIjogIlRWUCAyIiwgIjYxMiI6ICJVbmtub3duIiwgIjYxMyI6ICJVbmtub3duIiwgIjYxMCI6ICJVbmtub3duIiwgIjYxMSI6ICJUVk4gMjQiLCAiNTg4IjogIm5TcG9ydCBbSERdIiwgIjU4OSI6ICJDYW5hbCsgU3BvcnQgW0hEXSIsICIxMDgiOiAiRGlzY292ZXJ5IGxpZmUiLCAiMTA5IjogIkFYTiIsICIxMDIiOiAiRXVyb3Nwb3J0IDIiLCAiMTAxIjogIkV1cm9zcG9ydCIsICIxMDYiOiAiSEJPIENvbWVkeSIsICIxMDciOiAiS2lubyBQb2xza2EiLCAiMTA0IjogIlRMQyIsICI0NzAiOiAiRGlzY292ZXJ5IFtIRF0iLCAiNDcxIjogIk5hdEdlbyBbSERdIiwgIjQ3NiI6ICJCQkMgZWFydGgiLCAiNDc0IjogIkRpc2NvdmVyeSIsICI0NzgiOiAiVmlhc2F0IE5hdHVyZSIsICI0NzkiOiAiVmlhc2F0IEhpc3RvcnkiLCAiNjE2IjogIlBvbHNhdCBIRCIsICI2MTciOiAiUG9sc2F0IiwgIjYxOSI6ICJQb2xzYXQgU3BvcnQgRXh0cmEifQ=='
                                                                                                                                                                                                                                                                                        try: m = byteify(json.loads(base64.b64decode(m)))
                                                                                                                                                                                                                                                                                        except: m = {}
                                                                                                                                                                                                                                                                                        for a in base64.b64decode('OTMsOTQsOTcsOTgsMTAxLDEwMiwxMDQsMTA2LDEwOSwxMTAsMTEyLDExNCwxMTcsMTE4LDExOSwxMjAsMTIyLDQ2OSw0NzAsNDcxLDQ3NCw0NzYsNDc4LDQ3OSw1MjgsNTcxLDU3Miw1NzksNTgwLDU4MSw1ODIsNTgzLDU4NCw1ODUsNTg3LDU4OCw1ODksNTkwLDU5MSw1OTIsNTkzLDU5NCw1OTUsNTk2LDU5Nyw1OTgsNTk5LDYwMCw2MTAsNjExLDYxMiw2MTMsNjE2LDYxNyw2MTgsNjE5').split(','):
                                                                                                                                                                                                                                                                                            channelsList.append({'title':'Test %s' % m.get(a, ''), 'url':SatLiveApi.MAINURL+'/id/%s/' % a, 'icon':'http://web-live.tv/uploads/transmissions/Transmission/live/%s.jpg?%s' % (a, time.time()), 'desc':''})
                                                                                                                                                                                                                                                                                            num += 1
        return channelsList
    
    def getVideoLink(self, url):
        printDBG("SatLiveApi.getVideoLink")
        id = self.cm.ph.getSearchGroups(url+"/", 'id/([0-9]+?)/')[0]
        sts, data = self.cm.getPage(SatLiveApi.MAINURL + 'ge/' + id, self.http_params)
        if not sts:
            return ''
        base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
        src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        if base.startswith('rtmp'):
            return base + '/' + src + ' swfUrl=%s live=1' % SatLiveApi.SWF_URL
        return ''

    def doLogin(self, login, password):
        logged = False
        HTTP_HEADER= dict(SatLiveApi.HTTP_HEADER)
        HTTP_HEADER.update( {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With' : 'XMLHttpRequest'} )

        
        post_data = {'LoginForm[email]' : login, 'LoginForm[password]' : password, 'ajax' : 'fast-login-form', 'undefined' : '' }
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        sts, data = self.cm.getPage( SatLiveApi.LOGIN_URL, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                printDBG(data)
                if '[]' == data:
                    printDBG('SatLiveApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('SatLiveApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('SatLiveApi.doLogin there is no cookie file after login')
        return logged