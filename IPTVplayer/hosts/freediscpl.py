# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetDefaultLang, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.freediscpl_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.freediscpl_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("e-mail")+":", config.plugins.iptvplayer.freediscpl_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.freediscpl_password))
    return optionList
###################################################


def gettytul():
    return 'https://freedisc.pl/'

class FreeDiscPL(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept':'application/json, text/javascript, */*; q=0.01', 'Content-Type':'application/json; charset=UTF-8'} )
    
    MAIN_URL = 'https://freedisc.pl/'
    SEARCH_URL = MAIN_URL + 'search/get'
    DEFAULT_ICON_URL = "http://i.imgur.com/mANjWqL.png"

    MAIN_CAT_TAB = [{'category':'list_filters',  'title': 'Najnowsze publiczne pliki użytkowników',  'url':MAIN_URL+'explore/start/get_tabs_pages_data/%s/newest/'},
                    {'category':'list_filters',  'title': 'Ostatnio przeglądane pliki',              'url':MAIN_URL+'explore/start/get_tabs_pages_data/%s/visited/'},
                    {'category':'search',        'title': _('Search'), 'search_item':True},
                    {'category':'search_history','title': _('Search history')} ]
    
    FILTERS_TAB = [{'title':_('Movies'),    'filter':'movies'},
                   {'title':_('Music'),     'filter':'music'}]
                   #{'title':_('Pictures'),  'filter':'pictures'} ]
    TYPES = {'movies':7, 'music':6}#, 'pictures':2}
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  FreeDiscPL.tv', 'cookie':'FreeDiscPL.cookie'})
        self.defaultParams = {'with_metadata':True, 'ignore_http_code_ranges':[(410,410),(404,404)], 'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        self.loginMessage = ''
        self.treeCache = {}
        
    def getPage(self, url, params={}, post_data=None):
        if params == {}: params = dict(self.defaultParams)
        sts, data = self.cm.getPage(url, params, post_data)
        if sts and data.meta.get('status_code', 0) in [410, 404] and 'captcha' in data:
            errorMsg = [_('Link protected with google recaptcha v2.')]
            errorMsg.append(_("Please visit \"%s\" and confirm that you are human." % self.getMainUrl()))
            if not self.loggedIn: errorMsg.append(_('Please register and set login and password in the host configuration, to solve this problems permanently.'))
            errorMsg = '\n'.join(errorMsg)
            GetIPTVNotify().push(errorMsg, 'info', 10)
            SetIPTVPlayerLastHostError(errorMsg)
        return sts, data

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("FreeDiscPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listItems(self, cItem):
        printDBG("FreeDiscPL.listItems")
        filter = cItem.get('filter', '')
        type = self.TYPES.get(filter, -1)
        if type == -1: return
        
        page      = cItem.get('page', 0)
        url       = cItem['url'] % (type) + '{0}'.format(page)
        
        sts, data = self.getPage(url)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))['response']
            if 'visited' in url:
                data = data['html_visited']
            else:
                data = data['html_newest']
            splitMarker = "<div class='imageDisplay'>"
            data = data.split(splitMarker)
            if len(data): del data[0]
            for item in data:
                icon  = self.cm.ph.getSearchGroups(item, '''url\(['"]([^'^"]+?)['"]''')[0]
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                if url == '': continue
                title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
                
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon':self.getFullIconUrl(icon), 'desc': self.cleanHtmlStr(item)})
                
                if 'file_icon_7' in item:
                    self.addVideo(params)
                elif 'file_icon_6' in item:
                    self.addAudio(params)
                #elif 'file_icon_2' in item:
                #    self.addPicture(params)
        except Exception:
            printExc()
        
        params = dict(cItem)
        params.update({'title':_('Next page'), 'page':page+1})
        self.addDir(params)
        
    def listItems2(self, cItem, nextCategory):
        printDBG("FreeDiscPL.listItems2 cItem[%s]" % (cItem))
        page = cItem.get('page', 0)
        
        post_data = {"search_phrase":cItem.get('f_search_pattern', ''), "search_type":cItem.get('f_search_type', ''), "search_saved":0, "pages":0, "limit":0}
        if page > 0: post_data['search_page'] = page
        
        params = dict(self.defaultParams)
        params['raw_post_data'] = True
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer']= self.cm.getBaseUrl(self.getMainUrl()) + 'search/%s/%s' % (cItem.get('f_search_type', ''), urllib.quote(cItem.get('f_search_pattern', '')))
        
        sts, data = self.getPage(cItem['url'], params, json.dumps(post_data))
        if not sts: return
        
        printDBG(data)
        
        try:
            data = byteify(json.loads(data))['response']
            logins = data['logins_translated']
            translated = data['directories_translated']
            for item in data['data_files']['data']:
                userItem = logins[str(item['user_id'])]
                dirItem = translated[str(item['parent_id'])]
                icon = 'http://img.freedisc.pl/photo/%s/7/2/%s.png' % (item['id'], item['name_url'])
                url = '/%s,f-%s,%s' % (userItem['url'], item['id'], item['name_url'])
                title = item['name']
                desc = ' | '.join( [item['date_add_format'], item['size_format']] )
                desc += '[/br]' + (_('Added by: %s, directory: %s') % (userItem['display'], dirItem['name']))
                params = dict(cItem)
                params.update({'good_for_fav':True, 'f_user_item':userItem, 'f_dir_item':dirItem, 'category':nextCategory, 'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon':self.getFullIconUrl(icon), 'desc':desc, 'f_type':item.get('type_fk', '')})
                if params['f_type'] in ['7', '6']: self.addDir(params)
            if data['pages'] > page:
                params = dict(cItem)
                params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listExploreItem(self, cItem, nextCategory):
        printDBG("FreeDiscPL.listExploreItem cItem[%s]" % (cItem))
        cItem = dict(cItem)
        userItem = cItem.pop('f_user_item', {})
        dirItem = cItem.pop('f_dir_item', {})
        cItem.pop('page', None)
        
        type = cItem.get('f_type', '')
        
        if type == '7': self.addVideo(cItem)
        elif type == '6': self.addAudio(cItem)
        
        try:
            if userItem != {}:
                url = '/%s,d-%s,%s' % (userItem['url'], userItem['userRootDirID'], userItem['url'])
                desc = ['Ilość plików: %s' % userItem['filesCount']]
                desc.append('Ilość odsłon: %s' % userItem['viewsCount'])
                desc.append('Rozmiar plików: %s' % userItem['files_size_format'])
                desc.append('Ilość pobrań: %s' % userItem['filesCount'])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'title':userItem['display'], 'url':self.getFullUrl(url), 'f_user_id':userItem['url'], 'f_dir_id':userItem['userRootDirID'], 'icon':'', 'desc':'[/br]'.join(desc)})
                self.addDir(params)
            if dirItem != {}:
                url = '/%s,d-%s,%s' % (userItem['url'], dirItem['id'], dirItem['name_url'])
                desc = ['Katalogów: %s' % dirItem['dir_count']]
                desc.append('Plików: %s' % dirItem['file_count'])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'title':dirItem['name'], 'url':self.getFullUrl(url), 'f_user_id':userItem['url'], 'f_dir_id':dirItem['id'], 'icon':'', 'desc':'[/br]'.join(desc)})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listDir(self, cItem):
        printDBG("FreeDiscPL.listDir cItem[%s]" % (cItem))
        
        #sts, data = self.getPage(cItem['url'])
        #if not sts: return
        
        userId = cItem.get('f_user_id', '')
        dirId = cItem.get('f_dir_id', '')
        
        urlParams = dict(self.defaultParams)
        urlParams['raw_post_data'] = True
        urlParams['header'] = dict(self.AJAX_HEADER)
        urlParams['header']['Referer']= cItem['url']
        
        try:
            dirIcon = self.getFullIconUrl('/static/img/icons/big_dir.png')
            
            if userId not in self.treeCache:
                self.treeCache = {}
                url = self.getFullUrl('/directory/directory_data/get_tree/%s' % (userId))
                sts, data = self.getPage(url, urlParams)
                if not sts: return
                
                self.treeCache[userId] = byteify(json.loads(data), '', True)['response']['data']
            
            # sub dirs at first
            if dirId in self.treeCache[userId]:
                dirsTab = []
                for key in self.treeCache[userId][dirId]:
                    if self.treeCache[userId][dirId][key]['type'] == 'd':
                        dirsTab.append(self.treeCache[userId][dirId][key])
                dirsTab.sort(key=lambda item: item['name']) #, reverse=True)
                
                for item in dirsTab:
                    if item['id'] in ['0', dirId]: continue
                    url = '/%s,d-%s,%s' % (userId, item['id'], item['name_url'])
                    title = self.cleanHtmlStr(item['name'])
                    desc = ['Katalogów: %s' % item['dir_count']]
                    desc.append('Plików: %s' % item['file_count'])
                    params = dict(cItem)
                    params.update({'good_for_fav':True, 'title':title, 'url':self.getFullUrl(url), 'icon':dirIcon, 'f_dir_id':item['id'], 'f_prev_dir_id':dirId, 'prev_url':cItem['url'], 'desc':'[/br]'.join(desc)})
                    self.addDir(params)
            
            # now files data
            url = self.getFullUrl('/directory/directory_data/get/%s/%s' % (userId, dirId))
            sts, data = self.getPage(url, urlParams)
            if not sts: return

            data = byteify(json.loads(data), '', True)['response']['data']
            if 'data' in data:
                filesTab = []
                for key in data['data']:
                    if data['data'][key]['type'] == 'f' and data['data'][key]['type_fk'] in ['7', '6']:
                        filesTab.append(data['data'][key])
                filesTab.sort(key=lambda item: item['name']) #, reverse=True)
                url = self.getFullIconUrl('/static/img/icons/big_dir.png')
                for item in filesTab:
                    if '7' == item['type_fk']: icon = 'http://img.freedisc.pl/photo/%s/7/2/%s.png' % (item['id'], item['name_url'])
                    else: icon = ''
                    
                    url = '/%s,f-%s,%s' % (userId, item['id'], item['name_url'])
                    title = self.cleanHtmlStr(item['name'])
                    desc = ' | '.join( [item['date_add_format'], item['size_format']] )
                    params = dict(cItem)
                    params.update({'good_for_fav':True, 'title':title, 'url':self.getFullUrl(url), 'icon':self.getFullIconUrl(icon), 'desc':desc, 'f_type':item.get('type_fk', '')})
                    if params['f_type'] == '7':
                        self.addVideo(params)
                    else:
                        self.addAudio(params)
            
            # find parent id data
            parentId = None
            tmpId = 'd-%s' % dirId
            for key in self.treeCache[userId]:
                printDBG(">>> %s" % key)
                if tmpId in self.treeCache[userId][key]:
                    parentId = self.treeCache[userId][key][tmpId]['parent_id']
                    break
            if parentId == None: return
            
            item = None
            # find parent id item
            tmpId = 'd-%s' % parentId
            for key in self.treeCache[userId]:
                if tmpId in self.treeCache[userId][key]:
                    item = self.treeCache[userId][key][tmpId]
                    break
            if item == None: return
            
            if item['id'] not in ['0', dirId, cItem.get('f_prev_dir_id', '')]:
                url = '/%s,d-%s,%s' % (userId, item['id'], item['name_url'])
                title = self.cleanHtmlStr(item['name'])
                desc = ['Katalogów: %s' % item['dir_count']]
                desc.append('Plików: %s' % item['file_count'])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'title':title, 'url':self.getFullUrl(url), 'icon':dirIcon, 'f_dir_id':item['id'], 'f_prev_dir_id':dirId, 'prev_url':cItem['url'], 'desc':'[/br]'.join(desc)})
                self.currList.insert(0, params)
        except Exception:
            printExc()
        
    def getLinksForVideo(self, cItem):
        printDBG("FreeDiscPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        return self.up.getVideoLinkExt(cItem['url'])
        
    def getLinksForFavourite(self, fav_data):
        printDBG('FreeDiscPL.getLinksForFavourite')
        self.tryTologin()
        
        links = []
        if self.cm.isValidUrl(fav_data):
            links = self.getLinksForVideo({'url':fav_data})
        else:
            try:
                cItem = byteify(json.loads(fav_data))
                links = self.getLinksForVideo(cItem)
            except Exception: printExc()
        return links
        
    def tryTologin(self):
        printDBG('tryTologin start')
        errMsg = []
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.freediscpl_login.value or\
            self.password != config.plugins.iptvplayer.freediscpl_password.value:
        
            self.login = config.plugins.iptvplayer.freediscpl_login.value
            self.password = config.plugins.iptvplayer.freediscpl_password.value
            
            sts, data = self.getPage(self.getMainUrl())
            if not sts: return None
            
            if 200 != data.meta.get('status_code', 0):
                return None
            
            self.loggedIn = False
            self.loginMessage = ''
            
            if '' == self.login.strip() or '' == self.password.strip():
                if 'btnLogout' in data: rm(self.COOKIE_FILE)
                return False
            
            params = dict(self.defaultParams)
            params['raw_post_data'] = True
            params['header'] = dict(self.AJAX_HEADER)
            params['header']['Referer']= self.getMainUrl()
            
            post_data = {"email_login":self.login,"password_login":self.password,"remember_login":1,"provider_login":""}
            sts, data = self.getPage(self.getFullUrl('/account/signin_set'), params, json.dumps(post_data))
            if not sts: return None
            
            try:
                data = byteify(json.loads(data))
                if data['success'] == True: self.loggedIn = True
                else: errMsg = [self.cleanHtmlStr(data['response']['info'])]
            except Exception:
                printExc()
            
            if self.loggedIn != True:
                self.sessionEx.open(MessageBox, _('Login failed.') + '\n' + '\n'.join(errMsg), type = MessageBox.TYPE_ERROR, timeout = 10)
            return self.loggedIn
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FreeDiscPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'url':self.SEARCH_URL, 'category':'list_items2', 'f_search_pattern':searchPattern, 'f_search_type':searchType})
        self.listItems2(cItem, 'explore_item')

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        filter   = self.currItem.get("filter", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_items'
            self.listsTab(self.FILTERS_TAB, cItem)
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'list_items2':
            self.listItems2(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.listExploreItem(self.currItem, 'list_dir')
        elif category == 'list_dir':
            self.listDir(self.currItem)
    #SEARCH
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
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, FreeDiscPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Movies"), "movies"))
        searchTypesOptions.append((_("Music"), "music"))
        return searchTypesOptions