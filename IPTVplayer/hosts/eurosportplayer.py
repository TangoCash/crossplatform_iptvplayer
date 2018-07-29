# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, NextDay, PrevDay, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import time
import re
import urllib
import string
import random
import base64
from datetime import datetime, timedelta
from hashlib import md5
from copy import deepcopy
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper, iptv_js_execute
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.eurosportplayer_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.eurosportplayer_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("e-mail")+":",    config.plugins.iptvplayer.eurosportplayer_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.eurosportplayer_password))
    return optionList
###################################################
def gettytul():
    return 'https://www.eurosportplayer.com/'

class EuroSportPlayer(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'eurosportplayer.com', 'cookie':'eurosportplayer.com.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        self.MAIN_URL = 'https://www.eurosportplayer.com/'
        self.DEFAULT_ICON_URL = 'https://superrepo.org/static/images/icons/original/xplugin.video.eurosportplayer.png.pagespeed.ic.xB5vsEn8I9.png'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/vnd.media-service+json; version=1', 'Origin':self.getMainUrl()[:-1]} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        self.serverApiData = {}
        self.tokenData = {}
        self.langsMap = {}
        
        self.OFFSET = datetime.now() - datetime.utcnow()
        seconds = self.OFFSET.seconds + self.OFFSET.days * 24 * 3600
        if ((seconds + 1) % 10) == 0: seconds += 1  
        elif ((seconds - 1) % 10) == 0: seconds -= 1 
        self.OFFSET = timedelta(seconds=seconds)
        
        self.ABBREVIATED_MONTH_NAME_TAB = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        self.ABBREVIATED_DAYS_NAME_TAB = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)
        
    def getJSPage(self, baseUrl, addParams = {}, post_data = None):
        try:
            if self.tokenData['timeout'] <= time.time():
                self.getToken('refresh')
        
            getParams = dict(self.defaultParams)
            getParams.update(addParams)
            getParams['header'] = dict(self.AJAX_HEADER)
            getParams['header'].update(addParams.get('header', {}))
            getParams['header']['Authorization']  = self.tokenData['access_token']
            
            sts, data = self.cm.getPage(baseUrl, getParams, post_data)
        except Exception:
            printExc()
        return sts, data
    
    def listMainMenu(self, cItem):
        printDBG("EuroSportPlayer.listMainMenu")
        
        try:
            CAT_TAB = [{'category':'on_air',             'title': _('On Air'),        }, 
                       {'category':'schedule',           'title': self.serverApiData['i18n_dictionary'].get('Web_Title_Schedule', _('Schedule')),},
                       {'category':'vod_sport_filters',  'title': self.serverApiData['i18n_dictionary'].get('Nav_On_Demand', _('VOD')),},
                       {'category':'events',             'title': self.serverApiData['i18n_dictionary'].get('Nav_Events', _('Events')), 'f_type':'nonolympics'}, 
                       {'category':'events',             'title': self.serverApiData['i18n_dictionary'].get('Olympics', _('Olympics')), 'f_type':'olympics'   }, 
                       {'category':'search',             'title': _('Search'),          'search_item':True    }, 
                       {'category':'search_history',     'title': _('Search history')},]
            
            self.listsTab(CAT_TAB, cItem)
        except Exception:
            printExc()
        
    def _str2date(self, txt):
        txt = self.cm.ph.getSearchGroups(txt, '([0-9]+\-[0-9]+\-[0-9]+T[0-9]+\:[0-9]+:[0-9]+)')[0]
        return datetime.strptime(txt, '%Y-%m-%dT%H:%M:%S')
        
    def _gmt2local(self, txt):
        utc_date = self._str2date(txt)
        utc_date = utc_date + self.OFFSET
        if utc_date.time().second == 59:
            utc_date = utc_date + timedelta(0,1)
        return utc_date
        
    def _absTimeDelta(self, d1, d2, div=60):
        if d1 > d2: td = d1 - d2
        else: td = d2 - d1
        return (td.seconds + td.days * 24 * 3600) / div
        
    def _getLanguageDisplayName(self, key):
        langName = key
        if self.langsMap == {}:
            try:
                for item in self.serverApiData['locale']['languageMenuModel']['list']:
                    self.langsMap[item['locale']] = item['displayName']
            except Exception:
                printExc()
        return self.langsMap.get(key, str(key))
        
    def _getCatsDisplay(self, cats):
        tab = []
        for item in cats:
            val = self.serverApiData['i18n_dictionary'].get('sport_' + item)
            if val != '': tab.append(val)
        return ', '.join(tab)
        
    def fillServerApiData(self):
        printDBG('EuroSportPlayer.fillServerApiData')
        if self.serverApiData != {}:
            return
        
        serverApiData = {}
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return False
        
        jscode = ['var window={};function getStartupDeviceTypeString(){return "desktop";}\nwindow.requirejs_data={};requirejs=function(){if (2 == arguments.length) {window.requirejs_data.siteScripts=arguments[0];arguments[1]()} else {window.requirejs_data.scripts=arguments[0];}};requirejs.config=function(){window.requirejs_data.config=arguments[0];};']
        markers = ['window.server_path','window.i18n_dictionary','window.locale','window.SPORTS_BY_ID','window.bamTrackingConfig','window.specialEvents','requirejs']
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in data:
            for m in markers:
                if m in item:
                    jscode.append(item)
                    break
        jscode.append('\nprint(JSON.stringify(window));')
        ret = iptv_js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = ret['data'].strip()
            try:
                serverApiData = byteify(json.loads(data))
                clientId = serverApiData['server_path']['sdk']['clientId']
                env = serverApiData['server_path']['sdk']['environment']
                url = 'https://bam-sdk-configs.mlbam.net/v0.1/%s/browser/v2.1/windows/chrome/%s.json' % (clientId, env)
                sts, data = self.getPage(url)
                if not sts: return False
                serverApiData['prod'] =  byteify(json.loads(data))
            except Exception:
                printExc()
                return
        
        self.serverApiData = serverApiData
        
    def getToken(self, grantType):
        printDBG('EuroSportPlayer.getToken start')
        bRet = False
        try:
            getParams = dict(self.defaultParams)
            getParams['header'] = dict(self.AJAX_HEADER)
        
            clientData = self.serverApiData['prod']['authorization']['client']
            
            url = clientData['links'][0]['href']
            getParams['header'].update(clientData['links'][0]['headers'])
            getParams['header']['Authorization'] = getParams['header']['Authorization'].replace('{encodedApiToken}', self.serverApiData['server_path']['sdk']['clientApiKey'])
            post_data = None
            if grantType == 'init':
                import uuid
                post_data = {'grant_type':'client_credentials', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':str(uuid.uuid4())}
            elif grantType == 'refresh':
                post_data = {'grant_type':'refresh_token', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':self.tokenData['refresh_token']}
            elif grantType == 'code':
                post_data = {'grant_type':'urn:mlbam:params:oauth:grant_type:token', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':self.tokenData['access_code']}
            sts, data = self.getPage(url, getParams, post_data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            self.tokenData.update(byteify(json.loads(data)))
            self.tokenData['timeout'] = time.time() + self.tokenData['expires_in'] # expires_in - in seconds
            bRet = True
        except Exception:
            printExc()
        printDBG('EuroSportPlayer.getToken end bRet[%s]' % bRet)
        return bRet
        
    def _addItem(self, cItem, item, NOW, sData=None, eData=None, fType=None):
        try:
            printDBG("*********************************************************")
            printDBG(item)
            printDBG("*********************************************************")
            title = self.cleanHtmlStr(item['titles'][0]['title'])
            try: 
                icon = item['photos'][0].get('uri', None)
                if icon == None: icon = item['photos'][0]['rawImage'] + ''
            except Exception: icon = ''
            duration =  self.cleanHtmlStr(item['runTime'])
            
            startDate = item.get('startDate', None)
            if startDate == None: startDate = item.get('releaseDate', None)
            if startDate == None: startDate = item.get('appears', None)
            if startDate != None: startDate = self._gmt2local(startDate)
            
            if startDate != None and sData != None and eData != None and \
               (startDate < sData or startDate > eData):
                return
            
            endDate = item.get('endDate', None) 
            if endDate != None: endDate = self._gmt2local(endDate)
            
            try: 
                language = item['titles'][0].get('language', None)
                for tmp in item['titles'][0]['tags']:
                    if tmp.get('type', '') == 'language':
                        language = tmp['value']
                language = self._getLanguageDisplayName(language)
            except Exception: language = None
                
            categories = self._getCatsDisplay(item['genres'])
            try: channel = item['channel']['callsign']
            except Exception: channel = None
            
            episodeName = item['titles'][0].get('episodeName', None)
            
            desc = []
            desc.insert(0, categories)
            if language != None: desc.insert(0, str(language))
            if channel != None: desc.insert(0, self.cleanHtmlStr(channel))
            
            try: prefix = item['mediaConfig']['productType'].lower()
            except Exception: prefix = ''
            
            upcoming = False
            type = item.get('type', '').lower()
            if type == 'airing' and prefix != 'vod':
                try: state = item['mediaConfig']['state'].lower()
                except Exception: state = ''
                
                if item.get('liveBroadcast', True) and state != 'off' and (None == startDate or startDate <= NOW ):
                    prefix = self.serverApiData['i18n_dictionary']['Live']
                elif startDate != None and  NOW < startDate and self._absTimeDelta(NOW, startDate, 60) > 5: 
                    prefix = self.serverApiData['i18n_dictionary']['Header_Upcoming']
                    upcoming = True
                else:
                    prefix = ''
            else:
                try: prefix = item['mediaConfig']['type'].upper()
                except Exception: prefix = item['type'].upper()
            
            if fType != None:
                if fType == 'VIDEO' and prefix != 'VIDEO': return
                elif fType != 'VIDEO' and prefix == 'VIDEO': return
                
            if prefix != '': title = '[%s] %s' % (prefix, title)
            if episodeName != None: title = '%s - %s' % (title, self.cleanHtmlStr(episodeName))
            
            printDBG("+++++++++++++++++++++++++++++++++++++++++++ [%s]" % prefix)
            if prefix.lower() == 'video' or startDate == None or endDate == None: dateStr = str(item['runTime'])
            else: dateStr = '%s - %s' % (startDate.strftime('%H:%M'), endDate.strftime('%H:%M'))
            
            if startDate != None: 
                month = self.ABBREVIATED_MONTH_NAME_TAB[startDate.month-1]
                if startDate.year == NOW.year: dateStr += ' | %s %s' % (startDate.day, self.serverApiData['i18n_dictionary'].get(month, month))
                else: dateStr += ' | %s %s, %s' % (startDate.day, self.serverApiData['i18n_dictionary'].get(month, month), startDate.year)
            
            summary = ''
            try: summary = item['titles'][0]['descriptionLong']
            except Exception: summary = item['titles'][0]['summaryLong']
            desc.insert(0, dateStr)
            desc = ' | '.join(desc) + '[/br]' + self.cleanHtmlStr(str(summary))
            
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':title, 'icon':icon, 'desc':desc, 'priv_item':item})
            if upcoming: self.addArticle(params)
            else: self.addVideo(params)
            
        except Exception:
            printExc()
    
    def listSportFilters(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listSportFilters [%s]" % cItem)
        try:
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/ListByTitle/sports_filter'
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            for item in data['data']['sports_filter']['list']:
                sportId = item['sport']
                icon = item['logoImage'][-1]['rawImage']
                title = self.serverApiData['i18n_dictionary']['sport_%s' % sportId]
                
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'icon':icon, 'f_sport_id':sportId})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listVodTypesFilters(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listVodTypesFilters [%s]" % cItem)
        try:
            sportId = cItem['f_sport_id']
            variables = {"must":[{"attributeName":"category","values":["%s" % sportId]}],"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/ondemand/counts/bycategory?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            totall = 0
            data = byteify(json.loads(data))
            for item in [('replays', 'Ondemand_Subnav_Replay'), ('highlights', 'Ondemand_Subnav_Highlights'), ('news', 'Ondemand_Subnav_News')]:
                try:
                    vodType = item[0]
                    count = int(data['data'][vodType]['meta']['hits'])
                    if count <= 0: continue
                    totall += count
                    title = '%s (%s)' % (self.serverApiData['i18n_dictionary'][item[1]], count)
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'f_vod_type':vodType})
                    self.addDir(params)
                except Exception:
                    printExc()
            
            if totall > 0 and len(self.currList) > 1:
                title = '%s (%s)' % (self.serverApiData['i18n_dictionary']['Ondemand_Subnav_All'], totall)
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title})
                self.currList.insert(0, params)
        except Exception:
            printExc()
        
    def listVodItems(self, cItem):
        printDBG("EuroSportPlayer.listVodItems [%s]" % cItem)
        try:
            page = cItem.get('page', 1)
            sportId = cItem['f_sport_id']
            vodType = cItem.get('f_vod_type', 'all')
            
            variables = {"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/ondemand/' + vodType
            if vodType == 'all':
                variables = {"pageSize":30,"page":page,"uiLang":self.serverApiData['locale'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder'],"must":{"termsFilters":[{"attributeName":"category","values":["%s" % sportId]}]}}
                url += '?variables='
            else:
                variables = {"pageSize":30,"page":page,"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder'],"category":"%s" % sportId}
                url += '/category?variables='
            url += urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            if vodType == 'all':
                data = byteify(json.loads(data))['data']['bucket']
                all  = data['meta']['hits']
                data = data['aggs'][0]['buckets'][0]
            else:
                data = byteify(json.loads(data))['data']['query']
                all  = data['meta']['hits']
            
            NOW = datetime.now()
            for item in data['hits']:
                self._addItem(cItem, item['hit'], NOW)
            
            if page*30 < all:
                params = dict(cItem)
                params.pop('priv_item', None)
                params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
                self.addDir(params)
        except Exception:
            printExc()
        
    def listOnAir(self, cItem):
        printDBG("EuroSportPlayer.listOnAir [%s]" % cItem)
        try:
            variables = {"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/Airings/onAir?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            NOW = datetime.now()
            for item in data['data']['Airings']:
                self._addItem(cItem, item, NOW)
        except Exception:
            printExc()
        
    def listEventsCategories(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listEventsCategories [%s]" % cItem)
        
        def _str2dateShort(txt):
            date = self._str2date(txt)
            month = self.ABBREVIATED_MONTH_NAME_TAB[date.month-1]
            return ' %s %s, %s' % (date.day, self.serverApiData['i18n_dictionary'].get(month, month), date.year)
                
        try:
            if cItem['f_type'] == 'nonolympics': type = 'Non'
            else: type = ''
            
            variables = {"include_images":True,"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/%sOlympicsEventPageAll?variables=%s' % (type, urllib.quote(json.dumps(variables, separators=(',', ':'))))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            data['data']['EventPageAll'].sort(key=lambda item: item['eventDetails'][0]['title'])
            for item in data['data']['EventPageAll']:
                title = self.cleanHtmlStr(item['eventDetails'][0]['title'])
                desc = '%s - %s' % (_str2dateShort(item['startDate']), _str2dateShort(item['endDate']))
                icon = item['heroImage'][0]['photos'][0]['imageLocation']
                
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'desc':desc, 'icon':icon, 'f_content_id':item['contentId']})
                self.addDir(params)
                
        except Exception:
            printExc()
        
    def listEventsMenu(self, cItem):
        printDBG("EuroSportPlayer.listEventsMenu")
        try:
            thisWeek = "This_Week"
            onDemand = "Nav_On_Demand"
            CAT_TAB = [{'category':'events_airings', 'title': self.serverApiData['i18n_dictionary'].get(thisWeek, thisWeek),}, 
                       {'category':'events_videos',  'title': self.serverApiData['i18n_dictionary'].get(onDemand, onDemand),}]
            self.listsTab(CAT_TAB, cItem)
        except Exception:
            printExc()
        
    def listEventsItems(self, cItem):
        printDBG("EuroSportPlayer.listEventsItems [%s]" % cItem)
        try:
            contentId = cItem['f_content_id']
            variables = {"contentId":contentId,"include_media":True,"include_images":True,"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/EventPageByContentId?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            name = cItem['category'].split('_', 1)[-1]
            if name == 'airings': fType = ''
            else: fType = 'VIDEO'
            for tmp in data['data']['EventPageByContentId']['media']:
                tmp = tmp['videos']
                if name == 'airings': tmp.reverse()
                
                NOW = datetime.now()
                for item in tmp:
                    self._addItem(cItem, item, NOW, fType=fType)
        except Exception:
            printExc()
        
    def listDays(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listDays [%s]" % cItem)
        NOW = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        
        def _dataLabel(d):
            weekday = self.ABBREVIATED_DAYS_NAME_TAB[d.weekday()]
            return '%s %s' % (d.day, self.serverApiData['i18n_dictionary'].get(weekday, weekday))
        
        itemsList = []
        #NextDay, PrevDay
        day = NOW
        for idx in range(7):
            day = PrevDay(day)
            itemsList.append(day)
        
        itemsList.reverse()
        itemsList.append(NOW)
        
        day = NOW
        for idx in range(7):
            day = NextDay(day)
            itemsList.append(day)
        
        for item in itemsList:
            title = _dataLabel(item)
            sData = item
            eData = item.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=None)
            
            if item == NOW: 
                title = 'Today'
                title = self.serverApiData['i18n_dictionary'].get(title, title)
            
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'f_sdate':sData, 'f_edate':eData})
            self.addDir(params)
        
    def listSchedule(self, cItem):
        printDBG("EuroSportPlayer.listSchedule [%s]" % cItem)
        
        def _dateStr(d):
            return d.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        try:
            cItem = dict(cItem)
            sData = cItem.pop('f_sdate')
            eData = cItem.pop('f_edate')
            variables = {"startDate":_dateStr(sData - self.OFFSET),"endDate":_dateStr(eData - self.OFFSET),"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/Airings/DateRange?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            
            data['data']['Airings'].sort(key=lambda item: item['startDate']) #, reverse=True)
            
            NOW = datetime.now()
            for item in data['data']['Airings']:
                if item.get('playbackUrls', []) in (None, []):
                    continue 
                self._addItem(cItem, item, NOW, sData+self.OFFSET-timedelta(days=1), eData+self.OFFSET+timedelta(days=1))
        except Exception:
            printExc()
            
    def listSearchItems(self, cItem):
        printDBG("EuroSportPlayer.listSearchItems [%s]" % cItem)
        try:
            page = cItem.get('page', 1)
            variables = {"index":"eurosport_global","preferredLanguages":["pl","en"],"uiLang":"pl","mediaRights":["GeoMediaRight"],"page":page,"pageSize":20,"q":cItem['f_query'],"type":["Video","Airing","EventPage"],"include_images":True}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/core/sitesearch?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))['data']['sitesearch']
            NOW = datetime.now()
            for item in data['hits']:
                self._addItem(cItem, item['hit'], NOW)
            
            if page*20 < data['meta']['hits']:
                params = dict(cItem)
                params.pop('priv_item', None)
                params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
                self.addDir(params)
        except Exception:
            printExc()
    
    def tryTologin(self):
        printDBG('EuroSportPlayer.tryTologin start')
        errorMsg = _('Error communicating with the server.')
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.eurosportplayer_login.value or\
            self.password != config.plugins.iptvplayer.eurosportplayer_password.value:
        
            self.login = config.plugins.iptvplayer.eurosportplayer_login.value
            self.password = config.plugins.iptvplayer.eurosportplayer_password.value
            
            rm(self.COOKIE_FILE)
            
            self.loggedIn = False
            self.loginMessage = ''
            
            if '' == self.login.strip() or '' == self.password.strip():
                msg = ''
                sts, data = self.getPage(self.getMainUrl())
                if sts and '/subscribe' not in data: msg = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '"message"'), ('</div', '>'))[1])
                if msg == '': msg = _('The host %s requires subscription.\nPlease fill your login and password in the host configuration - available under blue button.') % self.getMainUrl()
                GetIPTVNotify().push(msg, 'info', 10)
                return False
            
            if not self.getToken('init'):
                msg = _(errorMsg) + _('\nError[1].')
                GetIPTVNotify().push(msg, 'error', 10)
                return False
            
            try:
                baseUrl = self.serverApiData['server_path']['server'] + '/'
                url = self.getFullUrl('/login', baseUrl)
                
                sts, data = self.getPage(url)
                if not sts: return False
                
                getParams = dict(self.defaultParams)
                getParams['raw_post_data'] = True
                getParams['header'] = dict(self.AJAX_HEADER)
            
                clientData = self.serverApiData['prod']['authentication']['client']
                
                url = clientData['links'][0]['href']
                getParams['header'].update(clientData['links'][0]['headers'])
                getParams['header']['Authorization'] = getParams['header']['Authorization'].replace('{encodedUserToken}', self.tokenData['access_token'])
                post_data = '{"type":"email-password","email":{"address":"%s"},"password":{"value":"%s"}}' % (self.login, self.password)
                
                sts, data = self.getPage(url, getParams, post_data)
                if not sts and '401' in str(data):
                    msg =  _('Login failed. Invalid email or password.')
                    GetIPTVNotify().push(msg, 'error', 10)
                    return False
                else:
                    data = byteify(json.loads(data))
                    printDBG(data)
                    self.tokenData['access_code'] = data['code']
                    self.tokenData['access_timeout'] = time.time() + (data['exp'] - data['iat']) / 1000.0
                    
                    if not self.getToken('code'):
                        msg = _(errorMsg) + _('\nError[2].')
                        GetIPTVNotify().push(msg, 'error', 10)
                        return False
                    self.loggedIn = True
            except Exception:
                printExc()
            
            printDBG('EuroSportPlayer.tryTologin end loggedIn[%s]' % self.loggedIn)
            return self.loggedIn
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EuroSportPlayer.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        params = dict(cItem)
        params.update({'category':'list_search_items', 'f_query':searchPattern})
        self.listSearchItems(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("EuroSportPlayer.getLinksForVideo [%s]" % cItem)
        self.fillServerApiData()
        self.tryTologin()
        
        linksTab = []
        try:
            privItem = cItem['priv_item']
            
            if 'playbackUrls' in privItem: playbackUrls = privItem['playbackUrls']
            else: playbackUrls = privItem['media'][0]['playbackUrls']
            
            for urlItem in  playbackUrls:
                url = urlItem['href'].replace('{scenario}', 'browser~unlimited')
                sts, data = self.getJSPage(url)
                data = byteify(json.loads(data))['stream']
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++")
                printDBG(data)
                for item in [('slide', 'slide'), ('complete', 'complete')]:
                    if item[0] not in data: continue
                    linksTab.append({'url':data[item[0]], 'name':'%s - %s' % (urlItem['rel'], item[1]), 'need_resolve':1})
        except Exception:
            printExc()
        
        return linksTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("EuroSportPlayer.getVideoLinks [%s]" % baseUrl)
        self.getToken('refresh')
        
        videoUrl = strwithmeta(baseUrl)
        linksTab = []
        
        try:
            getParams = dict(self.defaultParams)
            getParams['header'] = dict(self.HTTP_HEADER)
            getParams['header']['Authorization']  = self.tokenData['access_token']
            linksTab = getDirectM3U8Playlist(baseUrl, cookieParams=getParams, checkContent=False, sortWithMaxBitrate=999999999)
            token = self.tokenData['access_token']
            referer = self.serverApiData['server_path']['server'] + '/'
            for idx in range(len(linksTab)):
                linksTab[idx]['url'] = strwithmeta(linksTab[idx]['url'], {'Authorization':token, 'User-Agent':getParams['header']['User-Agent'], 'Referer':referer, 'Origin':referer[:-1]})
        except Exception:
            printExc()
        
        return linksTab
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        self.fillServerApiData()
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||| name[%s], category[%s] " % (name, category) )
        self.cacheLinks = {}
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        
    # ON AIR
        elif category == 'on_air':
            self.listOnAir(self.currItem)
        
    # SCHEDULE
        elif category == 'schedule':
            self.listDays(self.currItem, 'list_schedule')
        elif category == 'list_schedule':
            self.listSchedule(self.currItem)
        
    # VOD
        elif category == 'vod_sport_filters':
            self.listSportFilters(self.currItem, 'vod_types_filters')
        elif category == 'vod_types_filters':
            self.listVodTypesFilters(self.currItem, 'list_vod_items')
        elif category == 'list_vod_items':
            self.listVodItems(self.currItem)
            
    # EVENTS
        elif category == 'events':
            self.listEventsCategories(self.currItem, 'events_types')
        elif category == 'events_types':
            self.listEventsMenu(self.currItem)
        elif category in ['events_airings', 'events_videos']:
            self.listEventsItems(self.currItem)
    #SEARCH
        elif category == 'list_search_items':
            self.listSearchItems(self.currItem)
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, EuroSportPlayer(), True, [])
    