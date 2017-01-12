# -*- coding: utf-8 -*-
# Based on techdealer-xbmc.googlecode.com/svn/trunk/plugin.audio.musicbox/

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, GetLogoDir
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import byteify, printExc, CSelOneLink
from Components.config import config, getConfigListEntry, ConfigYesNo, ConfigText
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
###################################################
# FOREIGN import
###################################################
import re
import urllib
try:    import json
except Exception: import simplejson as json
####################################################
# E2 GUI COMMPONENTS
####################################################
from Screens.MessageBox import MessageBox
####################################################
# Config options for HOST
####################################################
config.plugins.iptvplayer.MusicBox_premium = ConfigYesNo(default=False)
config.plugins.iptvplayer.MusicBox_login = ConfigText(default="", fixed_size=False)
####################################################
# Api keys
####################################################
audioscrobbler_api_key = "d49b72ffd881c2cb13b4595e67005ac4"
youtube_api_key = 'AIzaSyBbDY0UzvF5Es77M7S1UChMzNp0KsbaDPI'
HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0'}

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Użytkownik Last.fm", config.plugins.iptvplayer.MusicBox_premium))
    if config.plugins.iptvplayer.MusicBox_premium.value:
        optionList.append(getConfigListEntry(" Last.fm login:", config.plugins.iptvplayer.MusicBox_login))
    return optionList


def gettytul():
    return 'Music-Box'


class MusicBox(CBaseHostClass):
    SERVICE_MENU_TABLE = {
        1: "Itunes - Top songs by country",
        2: "Itunes - Top albums by country",
#        3: "Dezzer - Top Tracks",
        4: "Beatport - Top 100",
#        5: "Official Charts UK",
        6: "Bilboard - The Hot 100",
        7: "Bilboard - 200",
#        8: "Bilboard - Heatseekers Songs",
        9: "Bilboard - Heatseekers Albums",
        10: "Bilboard - Hot Pop Songs",
        11: "Bilboard - Hot Country Songs",
        12: "Bilboard - Hot Country Albums",
        13: "Bilboard - Hot Rock Songs",
        14: "Bilboard - Hot Rock Albums",
        15: "Bilboard - Hot R&B/Hip-Hop Songs",
        16: "Bilboard - Hot R&B/Hip-Hop Albums",
        17: "Bilboard - Hot Dance/Electronic Songs",
        18: "Bilboard - Hot Dance/Electronic Albums",
        19: "Bilboard - Hot Latin Songs",
        20: "Bilboard - Hot Latin Albums",
        21: "Last.fm - Moja lista",
    }

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.ytformats = config.plugins.iptvplayer.ytformat.value
        self.ytp = YouTubeParser()
        self.lastfm_username = config.plugins.iptvplayer.MusicBox_login.value
        self.usePremiumAccount = config.plugins.iptvplayer.MusicBox_premium.value

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'category': val, 'title': val, 'icon': ''}
            self.addDir(params)

###############################################################################
# Itunes
###############################################################################
    def Itunes_countries_menu(self, url, mode):
        country_name = ["Albania", "Algeria", "Angola", "Anguilla", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Botswana", "Brazil", "British Virgin Islands", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Cambodia", "Canada", "Cape Verde", "Cayman Islands", "Chad", "Chile", "China", "Colombia", "Congo, Republic of the", "Costa Rica", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Estonia", "Fiji", "Finland", "France", "Gambia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea-Bissau", "Guyana", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Korea, Republic Of", "Kuwait", "Kyrgyzstan", "Lao, People's Democratic Republic", "Latvia", "Lebanon", "Liberia", "Lithuania", "Luxembourg", "Macau", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Mali", "Malta", "Mauritania", "Mauritius", "Mexico", "Micronesia, Federated States of", "Moldova", "Mongolia", "Montserrat", "Mozambique", "Namibia", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Saudi Arabia", "Senegal", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "South Africa", "Spain", "Sri Lanka", "St. Kitts and Nevis", "St. Lucia", "St. Vincent and The Grenadines", "Suriname", "Swaziland", "Sweden", "Switzerland", "São Tomé and Príncipe", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zimbabwe"]
        country_code = ["al", "dz", "ao", "ai", "ag", "ar", "am", "au", "at", "az", "bs", "bh", "bb", "by", "be", "bz", "bj", "bm", "bt", "bo", "bw", "br", "vg", "bn", "bg", "bf", "kh", "ca", "cv", "ky", "td", "cl", "cn", "co", "cg", "cr", "hr", "cy", "cz", "dk", "dm", "do", "ec", "eg", "sv", "ee", "fj", "fi", "fr", "gm", "de", "gh", "gr", "gd", "gt", "gw", "gy", "hn", "hk", "hu", "is", "in", "id", "ie", "ir", "it", "jm", "jp", "jo", "kz", "ke", "kr", "kw", "kg", "la", "lv", "lb", "lr", "lt", "lu", "mo", "mk", "mg", "mw", "my", "ml", "mt", "mr", "mu", "mx", "fm", "md", "mn", "ms", "mz", "na", "np", "nl", "nz", "ni", "ne", "ng", "no", "om", "pk", "pw", "pa", "pg", "py", "pe", "ph", "pl", "pt", "qa", "ro", "ru", "sa", "sn", "sc", "sl", "sg", "sk", "si", "sb", "za", "es", "lk", "kn", "lc", "vc", "sr", "sz", "se", "ch", "st", "tw", "tj", "tz", "th", "tt", "tn", "tr", "tm", "tc", "ug", "ua", "ae", "gb", "us", "uy", "uz", "ve", "vn", "ye", "zw"]
        for x in range(0, len(country_name)):
            if country_code[x] not in ["al", "dz", "ao", "bj", "bt", "td", "cn", "cg", "gy", "is", "jm", "kr", "kw", "lr", "mk", "mg", "mw", "ml", "mr", "ms", "pk", "pw", "sn", "sc", "sl", "sb", "lc", "vc", "sr", "st", "tz", "tn", "tc", "uy", "ye"]: #Countries without music store
                url = country_code[x]
                title = country_name[x]
                icon = 'http://www.geonames.org/flags/x/' + country_code[x] + '.gif'
                desc = title
                if mode == 'song':
                    params = {'name': 'Itunes_track_charts', 'title': title, 'page': url, 'icon': icon, 'plot': desc}
                    self.addDir(params)
                elif mode == 'album':
                    params = {'name': 'Itunes_album_charts', 'title': title, 'page': url, 'icon': icon, 'plot': desc}
                    self.addDir(params)

    def Itunes_track_charts(self, url):
        country = url
        sts, data = self.cm.getPage('https://itunes.apple.com/%s/rss/topsongs/limit=100/explicit=true/json' % country, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['feed']['entry']
            for x in range(len(data)):
                item = data[x]
                artist = item['im:artist']['label']
                track_name = item['im:name']['label']
                try:
                    iconimage = item['im:image'][2]['label']
                except Exception:
                    iconimage = ''
                plot = ''
                search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                params = {'title': str(x + 1) + '. ' + artist + '- ' + track_name, 'page': search_string, 'icon': iconimage, 'plot': plot}
                self.addVideo(params)
        except Exception:
            printExc()  # wypisz co poszło nie tak

    def Itunes_album_charts(self, url):
        country = url
        sts, data = self.cm.getPage('https://itunes.apple.com/%s/rss/topalbums/limit=100/explicit=true/json' % country, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['feed']['entry']
            for x in range(len(data)):
                item = data[x]
                artist = item['im:artist']['label']
                album_name = item['im:name']['label']
                idx = item['id']['attributes']['im:id']
                try:
                    iconimage = item['im:image'][2]['label']
                except Exception:
                    iconimage = ''
                plot = ''
                params = {'name': 'Itunes_list_album_tracks','title': str(x + 1) + '. ' + artist + '- ' + album_name, 'page': idx, 'album': album_name, 'country': country, 'icon': iconimage, 'plot': plot}
                self.addDir(params)
        except Exception:
            printExc()  # wypisz co poszło nie tak

    def Itunes_list_album_tracks(self, url, album, country):
        sts, data = self.cm.getPage('https://itunes.apple.com/lookup?id='+url+'&country='+country+'&entity=song&limit=200', {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['results']
            for x in range(1, len(data)):
                item = data[x]
                artist = item['artistName']
                track_name = item['trackName']
                try:
                    iconimage = item['artworkUrl100']
                except Exception:
                    iconimage = ''
                plot = ''
                search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                params = {'title': artist + '- ' + track_name, 'page': search_string, 'icon': iconimage, 'plot': plot}
                self.addVideo(params)
        except Exception:
            printExc()
###############################################################################
# Beatport
###############################################################################

    def Beatport_top100(self, url):
        sts, data = self.cm.getPage(url)
        if not sts:
            return
        match = re.findall('<li class="bucket-item track">.*?<img.*?data-src="(.*?)".*?>.*?</a>.*?<div class="buk-track-num">(.+?)</div>.*?<p class="buk-track-title">.*?<a.*?>.*?<span class="buk-track-primary-title">(.*?)</span>.*?<span class="buk-track-remixed">(.*?)</span>.*?</a>.*?</p>.*?<p class="buk-track-artists">(.*?)</p>.*?<p class="buk-track-remixers">(.*?)</p>.*?</li>', data, re.DOTALL)
        if len(match) > 0:
            for i in range(len(match)):
                try:
                    track_number = match[i][1]
                    title_primary = (re.sub('\s+', ' ', (re.sub('<[^>]*>', '', match[i][2])))).replace("&amp;", "&").replace("&#39;", "'")
                    remixed = '(' + (re.sub('\s+', ' ', (re.sub('<[^>]*>', '', match[i][3])))).replace("&amp;", "&").replace("&#39;", "'") + ')'
                    track_name = title_primary + ' ' + remixed
                    artist = re.sub('<[^>]*>', '', match[i][4])
                    artist = re.sub('\s+', ' ', artist.strip())
                    artist = artist.replace("&amp;", "&").replace("&#39;", "'")
                    iconimage = match[i][0].replace('/95x95/', '/300x300/')
                    search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                    params = {'title': track_number + '. ' + artist + '- ' + track_name, 'page': search_string, 'icon': iconimage, 'plot': ''}
                    self.addVideo(params)
                except Exception:
                    pass
###############################################################################
# Bilboard
###############################################################################

    def Billboard_charts(self, url):
        sts, data = self.cm.getPage(url, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['query']['results']['item']
            for x in range(0, len(data)):
                item = data[x]
                name = item['title']
                artist = item['artist']
                track_name = item['chart_item_title']
                search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                params = {'title': name + ' - ' + artist, 'page': search_string, 'icon': '', 'plot': ''}
                self.addVideo(params)
        except Exception:
            printExc()  # wypisz co poszło nie tak

    def Billboard_chartsalbums(self, url):
        sts, data1 = self.cm.getPage(url, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data1))['query']['results']['item']
            for x in range(0, len(data)):
                item = data[x]
                name = item['title']
                artist = item['artist']
                album_name = item['chart_item_title']
                params = {'name': 'List_album_tracks','title': name + ' - ' + artist, 'page': 0, 'artist': artist, 'album': album_name, 'icon': '', 'plot': ''}
                self.addDir(params)
        except Exception:
            printExc()  # wypisz co poszło nie tak
###############################################################################
# Szukanie tytułu z albumow
###############################################################################

    def List_album_tracks(self, url, artist, album):
        if url != 0:
            sts, data = self.cm.getPage('http://ws.audioscrobbler.com/2.0/?method=album.getInfo&mbid='+url+'&api_key=' + audioscrobbler_api_key + '&format=json', {'header': HEADER})
            if not sts:
                return
        else:
            sts, data = self.cm.getPage('http://ws.audioscrobbler.com/2.0/?method=album.getInfo&artist='+urllib.quote(artist)+'&album='+urllib.quote(album)+'&api_key=' + audioscrobbler_api_key + '&format=json', {'header': HEADER})
            if not sts:
                return
        try:
            data = byteify(json.loads(data))['album']['tracks']['track']
            for x in range(0, len(data)):
                item = data[x]
                artist = item['artist']['name']
                track_name = item['name']
                try:
                    iconimage = item['album']['image'][3]['#text']
                except Exception:
                    iconimage = ''
                search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                params = {'title': track_name + ' - ' + artist, 'page': search_string, 'icon': iconimage, 'plot': ''}
                self.addVideo(params)
        except Exception:
                        printExc()  # wypisz co poszło nie tak

###############################################################################
# Moja playlista z Last.fm
###############################################################################

    def Lastfmlist(self):
        if False == self.usePremiumAccount:
            self.sessionEx.waitForFinishOpen(MessageBox, 'Wpisz login do last.fm.', type=MessageBox.TYPE_INFO, timeout=10)
        else:
            url = 'http://ws.audioscrobbler.com/2.0/?method=user.getPlaylists&user=' + self.lastfm_username + '&api_key=' + audioscrobbler_api_key + '&format=json'
            sts, data = self.cm.getPage(url, {'header': HEADER})
            if not sts:
                return
            try:
                data = byteify(json.loads(data))['playlists']['playlist']
                for x in range(len(data)):
                    item = data[x]
                    playlist_name = item['title']
                    playlist_id = item['id']
                    params = {'name': 'Lastfmlist_track', 'title': playlist_name, 'artist': playlist_id}
                    self.addDir(params)
            except Exception:
                printExc()  # wypisz co poszło nie tak

    def Lastfmlist_track(self, artist):
        playlist_id = "lastfm://playlist/" + artist
        url = 'http://ws.audioscrobbler.com/2.0/?method=playlist.fetch&playlistURL=' + playlist_id + '&api_key=' + audioscrobbler_api_key + '&format=json'
        print url
        sts, data = self.cm.getPage(url, {'header': HEADER})
        if not sts:
            return
        try:
            data = byteify(json.loads(data))['playlist']['trackList']['track']
            print data
            for x in range(len(data)):
                item = data[x]
                artist = item['creator']
                track_name = item['title']
                try:
                    iconimage = item['image']
                except Exception:
                    iconimage = ''
                search_string = urllib.quote(artist + ' ' + track_name + ' music video')
                params = {'title': track_name + ' - ' + artist, 'page': search_string, 'icon': iconimage, 'plot': ''}
                self.addVideo(params)
        except Exception:
            printExc()  # wypisz co poszło nie tak

###############################################################################
# Szukanie linku do materiału na youtube
###############################################################################

    def Search_videoclip(self, url):
        sts, data = self.cm.getPage("https://www.googleapis.com/youtube/v3/search?part=id%2Csnippet&q=" + url + "&type=Music&maxResults=1&key=" + youtube_api_key)
        if not sts:
            return []
        match = re.compile('"videoId": "([^"]+?)"').findall(data)
        videoUrls = []
        for item in match:
            video_path = "https://www.youtube.com/watch?v=" + item
            videoUrls = self.getLinksForVideo(video_path)
        return videoUrls

    def getLinksForVideo(self, url):
        printDBG("getLinksForVideo url[%s]" % url)
        ytformats = config.plugins.iptvplayer.ytformat.value
        maxRes    = int(config.plugins.iptvplayer.ytDefaultformat.value) * 1.1
        dash      = config.plugins.iptvplayer.ytShowDash.value

        if not url.startswith("http://") and not url.startswith("https://") :
            url = 'http://www.youtube.com/' + url
        tmpTab, dashTab = self.ytp.getDirectLinks(url, ytformats, dash, dashSepareteList = True)
        
        def __getLinkQuality( itemLink ):
            val = self.cm.ph.getSearchGroups('|%s|' %itemLink['format'], '[^0-9]([0-9]+?)[^0-9]')[0]
            if '' == val: return 0
            return int(val)
        tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
        if config.plugins.iptvplayer.ytUseDF.value and 0 < len(tmpTab):
            tmpTab = [tmpTab[0]]
        
        videoUrls = []
        for item in tmpTab:
            videoUrls.append({'name': item['format'] + ' | ' + item['ext'] , 'url':item['url']})
        for item in dashTab:
            videoUrls.append({'name': _("[dash] ") + item['format'] + ' | ' + item['ext'] , 'url':item['url']})
        return videoUrls
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG("handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)))
                return
            if -1 == index:
                # use default value
                self.currItem = {"name": None}
                printDBG("handleService for first self.category")
            else:
                self.currItem = self.currList[index]

        name = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')
        album = self.currItem.get("album", '')
        country = self.currItem.get("country", '')
        artist = self.currItem.get("artist", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

        if str(page)=='None' or page=='': page = '0'

    #MAIN MENU
        if name is None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #LISTA
    #  "Itunes - Top songs by country"
        elif category == self.setTable()[1]:
            self.Itunes_countries_menu('http://www.geonames.org/flags/x/', 'song')
    #  "Itunes - Top albums by country"
        elif category == self.setTable()[2]:
            self.Itunes_countries_menu('http://www.geonames.org/flags/x/', 'album')
    #  "Beatport - Top 100"
        elif category == self.setTable()[4]:
            self.Beatport_top100('https://pro.beatport.com/top-100')
    #  "Bilboard - The Hot 100"
        elif category == self.setTable()[6]:
            item = 'hot-100'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item +'%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - 200"
        elif category == self.setTable()[7]:
            item = 'billboard-200'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,200)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item +'%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Heatseekers Albums"
        elif category == self.setTable()[9]:
            item = 'heatseekers-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,200)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item +'%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Pop Songs"
        elif category == self.setTable()[10]:
            item = 'pop-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Country Songs"
        elif category == self.setTable()[11]:
            item = 'country-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Country Albums"
        elif category == self.setTable()[12]:
            item = 'country-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Rock Songs"
        elif category == self.setTable()[13]:
            item = 'rock-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Rock Albums"
        elif category == self.setTable()[14]:
            item = 'rock-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot R&B/Hip-Hop Songs"
        elif category == self.setTable()[15]:
            item = 'r-b-hip-hop-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot R&B/Hip-Hop Albums"
        elif category == self.setTable()[16]:
            item = 'r-b-hip-hop-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Dance/Electronic Songs"
        elif category == self.setTable()[17]:
            item = 'dance-electronic-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Dance/Electronic Albums"
        elif category == self.setTable()[18]:
            item = 'dance-electronic-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Latin Songs"
        elif category == self.setTable()[19]:
            item = 'latin-songs'
            self.Billboard_charts('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
    #  "Bilboard - Hot Latin Albums"
        elif category == self.setTable()[20]:
            item = 'latin-albums'
            self.Billboard_chartsalbums('http://query.yahooapis.com/v1/public/yql?q=SELECT+*+FROM+feed(1,100)+WHERE+url=%22http://www.billboard.com/rss/charts/' + item + '%22&format=json&diagnostics=true&callback=')
        elif category == self.setTable()[21]:
            self.Lastfmlist()
    ###########
        elif name == 'Itunes_track_charts':
            self.Itunes_track_charts(page)
        elif name == 'Itunes_album_charts':
            self.Itunes_album_charts(page)
        elif name == 'Itunes_list_album_tracks':
            self.Itunes_list_album_tracks(page, album, country)
        elif name == 'List_album_tracks':
            self.List_album_tracks(page, artist, album)
        elif name == 'Lastfmlist_track':
            self.Lastfmlist_track(artist)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, MusicBox(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value=[GetLogoDir('musicboxlogo.png')])

    def getLinksForVideo(self, Index=0, selItem=None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        urlList = self.host.Search_videoclip(self.host.currList[Index].get('page', ''))
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))
        return RetHost(RetHost.OK, value=retlist)

    def getResolvedURL(self, url):
#        if url != None and url != '':
        if url is not None and url is not '':
            ret = self.host.up.getVideoLink(url)
            list = []
            if ret:
                list.append(ret)
            return RetHost(RetHost.OK, value=list)
        return RetHost(RetHost.NOT_IMPLEMENTED, value=[])

    def convertList(self, cList):
        hostList = []

        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))

            title = cItem.get('title', '')
            description = cItem.get('plot', '')
            icon = cItem.get('icon', '')

            hostItem = CDisplayListItem(name=title,
                                        description=description,
                                        type=type,
                                        urlItems=hostLinks,
                                        urlSeparateRequest=1,
                                        iconimage=icon)
            hostList.append(hostItem)

        return hostList
    # end convertList

