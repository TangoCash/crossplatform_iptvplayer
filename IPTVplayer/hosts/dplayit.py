# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, MergeDicts
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
from datetime import datetime, tzinfo
###################################################


def gettytul():
    return 'https://it.dplay.com/'

class Dplayit(CBaseHostClass):
 
    def __init__(self):

        CBaseHostClass.__init__(self)

        self.MAIN_URL = "http://it.dplay.com/"
        self.TOKEN_URL = "https://dplayproxy.azurewebsites.net/api/config/init"
        self.PROGRAMS_URL = "https://dplayproxy.azurewebsites.net//api/Show/GetList"
        self.SHOW_URL="https://dplayproxy.azurewebsites.net/api/Show/GetById/?id={0}"
        self.VIDEO_URL="https://dplayproxy.azurewebsites.net/api/Video/GetById/?id={0}"

        #self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')        
        #self.defaultParams = {'header':self.HTTP_HEADER}
        self.defaultParams = { 'header': {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0'}}
        self.AccessToken=""
        
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        #printDBG(self.defaultParams)
        return self.cm.getPage(url, addParams, post_data)

    def getHeader(self, add_bearer = False):
        if self.AccessToken == "":
            printDBG('Dplay init and get access token')
            
            sts, data = self.getPage(self.TOKEN_URL)
            if not sts: return
            
            response = json_loads(data)
            self.AccessToken = response['Data']['AccessToken']
            printDBG(' Dplay Access token %s ' % self.AccessToken)         
        
        if self.AccessToken != None and self.AccessToken != "":
            # create header with current access token
            headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0', 
                       'Accept-Encoding' : 'gzip, deflate',
                       'AccessToken' : self.AccessToken}
            if add_bearer:
                headers['Authorization'] = 'Bearer {0}'.format(self.AccessToken[0 : self.AccessToken.index('__!__') - len(self.AccessToken)])
            
            return headers
    
    
    def getLinksForVideo(self, cItem):
        printDBG("Dplay getLinksForVideo [%s]" % cItem)
        linksTab=[]

        if cItem["category"] == 'video':
            video_id=cItem["video_id"]
            url=cItem["url"]
            h=self.getHeader(True)
        
            if h == None or h == "" :
                printDBG('Dplay wrong initialization')
                return linksTab
        
            sts, data = self.getPage(url, { 'header': h })
            if not sts: return
        
            #printDBG(data)
            response=json_loads(data)
            stream_url = response['data']['attributes']['streaming']['hls']['url']
            stream_url=strwithmeta(stream_url, h)
            linksTab.extend(getDirectM3U8Playlist(stream_url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))  
                        
        else: 
            printDBG("Dplay: video form category %s with url %s not handled" % (cItem["category"],cItem["url"]));
            linksTab.append({'url': cItem["url"], 'name': 'link1'})
        
        return linksTab

   
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [{'category':'live_tv', 'title': 'Dirette tv'},
                        {'category':'ondemand', 'title': 'Programmi on demand'}]  
        self.listsTab(MAIN_CAT_TAB, cItem)  

    def listChannels(self,cItem):
        printDBG("Dplay start channel list")
    
    
    def listPrograms(self,cItem):
        printDBG("Dplay start alphabetical index" )

        # 0-9
        params = dict(cItem)
        params.update({'category':'programs_az', 'title': "0-9" })
        self.addDir(params)
        
        #a-z
        for i in range(26):
            params = dict(cItem)
            params.update({'category':'programs_az', 'title': chr(ord('A')+i) })
            self.addDir(params)

    
    def listProgramsByLetter(self,cItem):
        printDBG("Dplay start programs list")
        letter=cItem["title"]
        h=self.getHeader()
        
        if h == None or h == "" :
            printDBG('Dplay wrong initialization')
            return
        
        sts, data = self.getPage(self.PROGRAMS_URL, { 'header': h })
        if not sts: return
        
        printDBG(data)
        response=json_loads(data)
        
        for show in response["Data"]:
            title = show["Name"]
            
            if title[:1].upper() == letter: 
                desc = show["Description"] if "Description" in show else ''
                icon = show['Images'][0]['Src']
                show_id = show['Id']
                params={'category':'program', 'title': title , 'desc': desc, 'icon': icon, 'id': show_id }
                self.addDir(params)     

            if letter == "0-9" and title[:1].isdigit():
                desc = show["Description"] if "Description" in show else ''
                icon = show['Images'][0]['Src']
                show_id = show['Id']
                params={'category':'program', 'title': title , 'desc': desc, 'icon': icon, 'id': show_id }
                self.addDir(params)     
    
    def listProgramItems(self,cItem):
        title = cItem['title']
        show_id = cItem['id']
        printDBG("Dplay start item list of program '%s' with Id %s" % (title,show_id) )
        h=self.getHeader()
        
        if h == None or h == "" :
            printDBG('Dplay wrong initialization')
            return
        
        url=self.SHOW_URL.format(show_id)
        sts, data = self.getPage(url, { 'header': h })
        if not sts: return

        printDBG(data)
        response=json_loads(data)
        
        if len(response["Data"]["Sections"]) > 0:
            icon = response["Data"]['Images'][0]['Src']
            for season in response["Data"]["Sections"][0]["Items"]:
                season_number = season['SeasonNumber'] if 'SeasonNumber' in season else '0'
                if 'Episodes' in season:
                    for video in season['Episodes']:
                        name=video["Name"]
                        desc=video["Description"]
                        num_episode=video["EpisodeNumber"]
                        video_id=video["Id"]
                        if 'PublishEndDate' in video:
                            date = datetime.strptime(video['PublishEndDate'], '%Y-%m-%dT%H:%M:%SZ')
                            desc = '{0}\n\n{1} {2}'.format(desc, "Disponibile fino a ", date.strftime("%d/%m/%Y"))
                        title = '{0} ({1} {2} - {3} {4})'.format(name, "Stagione", season_number, "Episodio", num_episode)
                        videoUrl=video["PlaybackInfoUrl"]
                        params=dict(cItem)
                        params.update ({'title': title,'name': title, 'desc': desc, 'video_id': video_id, 'url':videoUrl, 'icon': icon, 'category': 'video'})
                        #printDBG ("add video '%s' with playback info url '%s'" % (title,videoUrl)) 
            
                        self.addVideo(params)
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('Dplay handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        self.informAboutGeoBlockingIfNeeded('IT')
        
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        subtype  = self.currItem.get("sub-type",'')
        
        printDBG( "handleService: >> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
        elif category == 'live_tv':
            self.listChannels(self.currItem)
        elif category == 'ondemand':
            self.listPrograms(self.currItem)
        elif category == 'programs_az':
            self.listProgramsByLetter(self.currItem)
        elif category == 'program':
            self.listProgramItems(self.currItem)
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Dplayit(), True, [])
    
