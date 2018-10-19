# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, getConfigListEntry
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.icomponents.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, MergeDicts, rm, formatBytes, CSelOneLink
from Plugins.Extensions.IPTVPlayer.itools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
###################################################

###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
from datetime import  timedelta
###################################################

config.plugins.iptvplayer.christusvincit_preferred_bitrate = ConfigSelection(default = "99999999", choices = [("0",      _("the lowest")),
                                                                                                    ("360000",  "360000"),
                                                                                                    ("590000",  "590000"),
                                                                                                    ("820000",  "820000"),
                                                                                                    ("1250000", "1250000"),
                                                                                                    ("1750000", "1750000"),
                                                                                                    ("2850000", "2850000"),
                                                                                                    ("5420000", "5420000"),
                                                                                                    ("6500000", "6500000"),
                                                                                                    ("9100000", "9100000"),
                                                                                                    ("99999999",_("the highest")),
                                                                                                    ])
config.plugins.iptvplayer.christusvincit_use_preferred_bitrate = ConfigYesNo(default = True)

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Preferred video bitrate",     config.plugins.iptvplayer.christusvincit_preferred_bitrate))
    optionList.append(getConfigListEntry("Use preferred video bitrate", config.plugins.iptvplayer.christusvincit_use_preferred_bitrate))
    return optionList
###################################################


def gettytul():
    return 'http://christusvincit-tv.pl/'

class Christusvincit(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'christusvincit-tv.pl', 'cookie':'christusvincit-tv.pl.cookie'})

        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        self.defaultParams = {'header':self.HTTP_HEADER}

        self.MAIN_URL   = 'http://christusvincit-tv.pl/'
        self.DEFAULT_ICON_URL = 'http://christusvincit-tv.pl/images/christusbg.jpg'
        self.reImgObj = re.compile(r'''<img[^>]+?src=(['"])([^>]*?)(?:\1)''', re.I)
        self.titlesMap = {"wspolodkupicielka":"Współodkupicielka i Pośredniczka Wszelkich Łask",
                          "rekolkap":"Rekolekcje kapłańskie",
                          "medalionbogaojca":"Medalion Boga Ojca",
                          "mojkosciele":"Mój Kościele co oni Tobie uczynili",
                          "redemptorismater":"Redemptoris Mater",
                          "luter":"Luter świadkiem Chrystusa ?",
                          "bn2017":"Boże Narodzenie w tajemnicy Trójcy Przenajświętszej",
                          "synowielaski":"Synowie łaski przywołajcie narody i miasta",
                          "witajoblubienico":"Witaj Oblubienico Ducha Świętego",
                          "mowaboga":"Orędzia-Mowa Boga",
                          "chwalaboga":"Chwała Boga-doszliśmy do absurdu",
                          "maciewybor":"Macie wybór między Niebem a Piekłem",
                          "kontds":"Kontemplacja Ducha Świętego",
                          "listyp":"Kontemplacja Ducha Świętego w listach św. Pawła",
                          "prosby":"Prośby Matki Bożej",
                          "zyciesak":"Życie sakramentalne wg. św. Agnieszki",
                          "objquito":"Objawienia w Quito",
                          "poznajmy":"Poznajmy Wroga",
                          "tajemnicabn":"Tajemnica Bożego Narodzenia",
                          "lag2016":"Mała Intronizacja 2016",
                          "dsroz":"Duchu Święty Rozpal",
                          "kontemplacjajch":"Kontemplacja Jezusa Chrystusa",
                          "cierpienieo":"Cierpienie Oblubienicy",
                          "rekokap":"Rekolekcje o kapłaństwie",
                          "intronizacja":"Intronizacja-może się zegną",
                          "quito_nowe":"Objawienia Matki Bożejz Quito",
                          "bogmowi":"Bóg mówi do swego kapłana",
                          "kazanieslowa1":"Słowa ks.P.Natanka do ks.kard.S.Dziwisza",
                          "rekolekcje":"Rekolekcje o Mszy św.",
                          "glebiamodlitwy":"Głębia modlitwy Ojcze nasz",
                          "tatojestem":"Tato jestem",
                          "30-lecieksp":"30-lecie kapłaństwa ks.P.M.Natanka",
                          "gazetym":"Gazety mówią o księdzu",
                          "regulam":"Reguła Mariańska",
                          "bozatajemnica":"Boża Tajemnica Maryja",
                          "kochamkaplana":"Kocham polskiego katolickiego kapłana",
                          "bitwa_o_post":"Bitwa o post",
                          "tajemnice_glowny":"Tajemnica różańca świętego",
                          "bog_umacnia":"Bóg umacnia",
                          "bajka_sprawozdanie_komisarzy":"Bajka sprawozdanie komisarzy",
                          "dlaczego_rok_1960":"Dlaczego rok 1960? Żądania Matki Bożej Fatimskiej",
                          "Polsko_Bog_jeszcze_czeka_na_Ciebie":"Polsko, Bóg jeszcze czeka na Ciebie",
                          "istota_ojcostwa_boga":"Istota Ojcostwa Boga",
                          "polsko_ciebie_maryja_uratuje":"Polsko, Ciebie tylko Maryja uratuje",
                          "katechezy_boga":"Katechezy Boga Ojca",
                          "potega_slowa":"Potęga Słowa Bożego",
                          "rozwazania_drogi_krzyzowej":"Rozważania drogi krzyżowej",
                          "uczynmnieniewolnikiemtwojejmilosci":"Uczyń Mnie niewolnikiem Twojej miłości",
                          "drogapojednania":"Droga pojednania",
                          "leniwiwwierze":"Leniwi w wierze",
                          "kazaniapogrzebowe":"Kazania pogrzebowe",
                          "czysciec":"Tajemnica czyśćca",
                          "cierpienieboga":"Cierpienie Boga",
                          "czynie":"Czynię nieprzyjaźń między żywiołami",
                          "swiatduchaiswiatciala":"Świat ducha i świat ciała",
                          "medalik_benedykta":"Medalik św. Benedykta",
                          "triduum2012":"Święte Triduum",
                          "grzechy":"Cztery grzechy główne ks. Piotra Natanka",
                          "plomien":"Kościół płonie",
                          "pokuta":"Sakrament pokuty - niezmierzona Miłość Boga",
                          "droga2":"Droga Czasów Ostatecznych",
                          "niebianskie":"Bóg powala z nóg - katechezy niebiańskie",
                          "objawienia":"Objawienia w Montichiari - Godzina Łaski",
                          "zertka":"Polacy, Bóg chce się podeprzeć o Waszą ofiarę",
                          "krol_b":"Polsko, oto Król nadchodzi!",
                          "kaplani1":"Kapłani Chrystusowi czemu śpicie?",
                          "polska1":"Kocham Polskę",
                          "modernizm":"Rozsadzenie Kościoła od wewnątrz",
                          "msza_sw":"O Mszy Świętej",
                          "encykliki":"Encykliki papieskie",
                          "kaplan":"Tylko kapłan katolicki uratuje świat",
                          "dollar_s":"Lucyferyczny plan zniszczenia Kościoła Świętego",
                          "list_kaplani":"List Otwarty do Kapłanów Kościoła Katolickiego",
                          "gietrzwald":"Katechezy gietrzwałdzkie",
                          "kongresmaryjny":"Kongres Maryjny",
                          "czestochowa_kategoria":"Pielgrzymki do Częstochowy",
                          "kategoria_niepokalane_poczecie_nmp":"Niepokalane Poczęcie NMP",
                          "kategoria_chrystus_krol":"Chrystus Król - Słowa do Rycerzy",
                          "kategoria_bog_ojciec":"Bóg Ojciec",
                          "kategoria_dwa_serca":"Dwa Serca",
                          "kategoria_najdrozsza_krew":"Najdroższa Krew Pana Jezusa",
                          "slowodorycerzy1":"Słowa do Rycerzy Chrystusa Króla",
                          "reformalit":"Reforma liturgiczna",
                          "dwaserca2018":"Dwa Serca 2018",
                          "dwojgaserc2018":"Uroczystość Dwojga Serc 29.09.2018r.",
                          "sekretlasal":"Sekret La Salette i kompleks księży saletynów",
                          "kazkrew2018":"O Krwi Najdroższej 2018",
                          "koronacjamb2018":"Koronacja Matki Bożej z Quito",
                          "quito2018":"Objawienia Matki Bożej w Quito",
                          "cierboga":"Cierpienie Boga w Trójcy Jedynego",
                          "encyklikimaryjne":"Encykliki Maryjne",
                          "uczpm":"Uczymy się Pieśni Maryjnych",
                          "manifestacjazbiorcze":"Królowa idzie do Sejmu",
                          "kazschol":"Pierwsze kazanie scholastyczne",
                          "krolowanie":"Królowanie Pana Jezusa i Królowanie Maryi",
                          "postzbiorcze":"Posty - Pomagamy Matce Bożej",
                          "zesrocz":"Zestawienie roczne",
                          "domychk":"Domy Chrystusa Króla",
                          "zesl4062017":"Zesłanie Ducha Świętego 04.06.2017r.",
                          "kazaniawielkanocy":"Kazanie Czasu Wielkanocy",
                          "kfront":"Kazanie frontowe",
                          "24meki":"24 godziny Męki naszego Pana Jezusa Chrystusa",
                          "kontsj":"Kontemplacja Najświętszego Serca Jezusa",
                          "boguzdrawia":"Bóg czyni cuda i uzdrawia",
                          "wdsnabw":"Wieczernik Ducha Świętego nabożeństwo wieczorne",
                          "rozwazaniacz":"Rozważania czerwcowe",
                          "adwokat":"Nająłem Adwokata na godzinę śmierci",
                          "inner":"Inne retransmisje",
                          "adwentglowne":"Liturgiczne inicjacje adwentowe",
                          "objawieniawakita1":"Objawienia w Akita",
                          "wieczornice":"Wieczornice",
                          "burzanadpd":"Burza nad pustelnią - Dokumenty",
                          "paninarodow":"Pani Wszystkich Narodów",
                          "blogjest":"Błogosławiony jestem",
                          "oduchuswietym":"O Duchu Świętym",
                          "miloscspraw":"Miłość wypełnia się w sprawiedliwości",
                          "refleksje":"Refleksje betlejemskie",
                          "nasza_matka-garabandal":"Nasza Matka - Garabandal",
                          "kazania_pasyjne_glowny":"Kazania Pasyjne",
                          "kazania_nabozenstwa_patriotyczne":"Kazania i nabożeństwa patriotyczne",
                          "w_obronie_garabandal":"W obronie Garabandal",
                          "nabozenstwouzdrawianiaiuwalniania":"Nabożeństwa uzdrawiania i uwalniania",
                          "tajemnicamszywgojcapio":"Tajemnica Mszy Św. wg św. Ojca Pio",
                          "25lecie_pustelni":"25-lecie Pustelni",
                          "ratujcie_dusze":"Ratujcie dusze",
                          "bog_trwa_zawsze":"Bóg trwa zawsze. Czas który jest przeminie",
                          "quovadis":"Quo Vadis",
                          "bitwa_pod_wiedniem":"Bitwa pod Wiedniem",
                          "detronizacjakrola":"Detronizacja Króla. Oni Mnie nie chcą",
                          "kosciele":"Kościele obudź się!",
                          "czestochowa06102012":"Częstochowa - 06.10.2012r Rok Wiary",
                          "bruksela":"Bruksela - współczesny Jeroboam",
                          "wykrot":"Słowa do pielgrzymów z Wykrotu",
                          "galeria_bobola_prawy":"Rotunda św.Boboli",
                          "kimnaprawdejesteskaplanie":"Kim naprawdę jesteś kapłanie?",
                          "objawienia_prywatne":"Objawienia prywatne",
                          "przebaczenie":"O naturze przebaczenia",
                          "ktokrolem":"Kogo wybierzemy Królem - 01.04.2012r.",
                          "droga":"Droga którą idę, jest...",
                          "swjan":"Wspomnienie św. Jana Ewangelisty",
                          "przyspiesze":"Przyśpieszę Dzień Mojego Przyjścia",
                          "hold1":"Rocznica Hołdu Ruskiego - Msza święta z 5.11.2011r.",
                          "uwiedzony":"Uwiedzony świat i ludzkość - kazanie z 2 października 2011r.",
                          "oni_nie_zrobia":"Oni nie zrobią Intronizacji",
                          "heretyk":"Prawdziwe oblicze HERETYKÓW i SEKCIARZY w Kościele",
                          "baal":"Wzywam proroków Baal'a na konfrontację",
                          "natanek1":"ks.Natanek nieposłuszny?",
                          "katechezy":"Katechezy czasów ostatecznych",
                          "ogloszenia_biezace":"Ogłoszenia bieżące",
                          "slowodorycerzy1":"Pilne! Słowa do Rycerzy Chrystusa Króla",
                          "nowennabogojciec":"Nowenna ku czci Boga Ojca",
                          "zakon":"Powstaje zakon",
                          "banner_oferty_parafii":"Oferty Parafii Internetowej",
                          "wykrot_banner":"Nocna Pielgrzymka do Wykrotu (1-2/03/2014)",
                          "slowobozenacodzien":"Słowo Boże na co dzień",
                          "oredzianaczasyostateczne":"Orędzia na Czasy Ostateczne - czyta ks. Piotr",
                          "zywoty_swietych_panskich":"Żywoty Świętych Pańskich",
                          "msze_swiete":"Całe msze święte - nowe okienko",
                          "ewangeliawspol":"Ewangelia współcześnie",
                          "matka_swietych_polska":"Matka Świętych Polska",
                          "filozofiamyslenia":"Filozofia myślenia",
                          "slowobozevaltorta":"Słowo Boże na co dzień - M. Valtorta",
                          "dni_wiernych_parafii":"Dni wiernych parafii",
                          "pielgrzymki_550x120":"Pielgrzymki Odbijamy Europę",
                          }

    def listMain(self, cItem, nextCategory):
        printDBG("Christusvincit.listMain")

        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        data = re.sub("<!--[\s\S]*?-->", "", data)
        sections = ph.rfindall(data, '</table>', ('<td', '>', 'capmain-left'), flags=0)
        for section in sections:
            self.handleSection(cItem, nextCategory, section)

        rtmpUrl = ph.search(data, '''netConnectionUrl['"\s]*?:\s*?['"](rtmp://[^'^"]+?)['"]''')[0]
        # move live to the top
        prevlist = self.currList
        self.currList = []
        for item in prevlist:
            if "na żywo" in item['title']:
                if rtmpUrl:
                    try:
                        rtmpUrl = strwithmeta(rtmpUrl, {'iptv_proto':'rtmp', 'iptv_livestream':True})
                        item['sub_items'].append({'title':'%s [RTMP]' % item['title'], 'url':rtmpUrl, 'type':'video'})
                    except Exception:
                        printExc()
                self.currList.insert(0, item)
            else:
                self.currList.append(item)

        MAIN_CAT_TAB = [{'category':'search',         'title': _('Search'),       'search_item':True},
                        {'category':'search_history', 'title': _('Search history'),                 }]
        self.listsTab(MAIN_CAT_TAB, cItem)

    def handleSection(self, cItem, nextCategory, section):
        printDBG("Christusvincit.handleSection")
        section = ph.STRIP_HTML_COMMENT_RE.sub("", section)

        tmp = section.split('</table>', 1)
        sTitle = self.cleanHtmlStr(tmp[0])
        if sTitle.lower() in ('linki',): #'kategorie'
            return
        sIcon = self.getFullUrl( ph.search(section, ph.IMAGE_SRC_URI_RE)[1] )

        subItems = []
        uniques = set()
        iframes = ph.findall(section, '<center>', '</iframe>')
        if iframes:
            for iframe in iframes:
                title = self.cleanHtmlStr(iframe).split('Video Platform', 1)[0].strip()
                iframe = ph.search(iframe, ph.IFRAME_SRC_URI_RE)[1]
                if iframe in uniques:
                    continue
                uniques.add(iframe)
                if not title: title = sTitle
                subItems.append(MergeDicts(cItem, {'category':nextCategory, 'title':title, 'url':iframe}))

        iframes = ph.IFRAME_SRC_URI_RE.findall(section)
        if iframes:
            for iframe in iframes:
                iframe = iframe[1]
                if iframe in uniques:
                    continue
                uniques.add(iframe)
                subItems.append(MergeDicts(cItem, {'category':nextCategory, 'title':sTitle, 'url':iframe}))
        section = ph.findall(section, ('<a', '>', ph.check(ph.any, ('articles.php', 'readarticle.php'))), '</a>')
        for item in section:
            url = self.getFullUrl( ph.search(item, ph.A_HREF_URI_RE)[1] )
            icon = self.getFullUrl( ph.search(item, self.reImgObj)[1] )
            title = self.cleanHtmlStr(item)
            if not title: 
                title = icon.rsplit('/', 1)[-1].rsplit('.', 1)[0]
                title = self.titlesMap.get(title, title.upper())
            subItems.append(MergeDicts(cItem, {'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon}))

        if len(subItems) > 1:
            self.addDir(MergeDicts(cItem, {'category':'sub_items', 'title':sTitle, 'icon':sIcon, 'sub_items':subItems}))
        elif len(subItems) == 1:
            params = subItems[0]
            params.update({'title':sTitle})
            self.addDir(params)

    def getPage(self, baseUrl, addParams={}, post_data=None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)

    def getFullUrl(self, url, currUrl=None):
        return CBaseHostClass.getFullUrl(self, url.replace('&amp;', '&'), currUrl)

    def listSubItems(self, cItem):
        printDBG("Christusvincit.listSubItems")
        self.currList = cItem['sub_items']

    def exploreItem(self, cItem):
        printDBG("Christusvincit.exploreItem")
        playerConfig = None

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        cUrl = self.cm.meta['url']
        self.setMainUrl(cUrl)

        if 'articles.php' in cUrl:
            iframe = ph.search(data, ph.IFRAME_SRC_URI_RE)[1]
            if not iframe: 
                iframe = ph.find(data, ('<script', '>', 'embedIframeJs'))[1]
                iframe = ph.getattr(iframe, 'src')

            if iframe and '?' in iframe:
                sts, tmp = self.getPage(self.getFullUrl(iframe.replace('?', '?iframeembed=true&')))
                if not sts: return
                playerConfig = ph.find(tmp, '{"playerConfig"', '};')[1][:-1]
            else:
                sections = ph.find(data, '<noscript', 'scapmain-left')[1]
                sections = ph.rfindall(sections, '</table>', ('<td', '>', 'capmain-left'), flags=0)
                for section in sections:
                    self.handleSection(cItem, cItem['category'], section)
        else:
            playerConfig = ph.find(data, '{"playerConfig"', '};')[1][:-1]

        if playerConfig:
            try:
                playerConfig = json_loads(playerConfig)
                playlistResult = playerConfig.get('playlistResult', {})
                if not playlistResult: playlistResult['0'] = {'items':[playerConfig['entryResult']['meta']]}
                for key, section in playlistResult.iteritems():
                    for item in section['items']:
                        icon = self.getFullUrl(item['thumbnailUrl'])
                        title = item['name']
                        desc = '%s | %s' % (str(timedelta(seconds=item['duration'])), item['description'])
                        params = {'title':title, 'icon':icon, 'desc':desc, 'f_id':item['id']}
                        if item.get('hlsStreamUrl'): params['url'] = item['hlsStreamUrl']
                        self.addVideo(params)
            except Exception:
                printExc()

    def listSearchResult(self, cItem, searchPattern, searchType):

        url = self.getFullUrl('/search.php?stext=%s&search=Szukaj&method=AND&stype=articles&forum_id=0&datelimit=0&fields=2&sort=datestamp&order=0&chars=50' % urllib.quote_plus(searchPattern))
        cItem = MergeDicts(cItem, {'category':'list_search', 'url':url})
        self.listSearchItems(cItem)

    def listSearchItems(self, cItem):
        printDBG("Christusvincit.listSearchItems")
        page = cItem.get('page', 1)

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        data = ph.find(data, 'search_result', '</table>', flags=0)[1]
        data = re.compile('''<div[^>]+?pagenav[^>]*?>''').split(data, 1)
        if len(data) == 2: 
            nextPage = ph.find(data[-1], ('<a', '>%s<' % (page+1)))[1]
            nextPage = self.getFullUrl(ph.getattr(nextPage, 'href'))
        else: nextPage = ''

        data = ph.findall(data[0], ('<a', '>', ph.check(ph.any, ('articles.php', 'readarticle.php'))), '</span>')
        for item in data:
            url = self.getFullUrl( ph.search(item, ph.A_HREF_URI_RE)[1] )
            icon = self.getFullUrl( ph.search(item, self.reImgObj)[1] )
            item = item.split('</a>', 1)
            title = self.cleanHtmlStr(item[0])
            desc = self.cleanHtmlStr(item[-1])

            self.addDir(MergeDicts(cItem, {'good_for_fav':True, 'category':'explore_item', 'title':title, 'url':url, 'icon':icon, 'desc':desc}))
        if nextPage:
            self.addDir(MergeDicts(cItem, {'good_for_fav':False, 'title':_('Next page'), 'page':page+1, 'url':nextPage}))

    def getLinksForVideo(self, cItem):
        urlsTab = []

        if 'url' in cItem and cItem['url'].startswith('rtmp://'):
            urlsTab = [{'name':'rtmp', 'url':cItem['url'], 'need_resolve':0}]
        elif 'url' in cItem:
            urlsTab = getDirectM3U8Playlist(cItem['url'])
        else:
            url = 'http://mediaserwer3.christusvincit-tv.pl/api_v3/index.php?service=multirequest&apiVersion=3.1&expiry=86400&clientTag=kwidget%3Av2.41&format=1&ignoreNull=1&action=null&1:service=session&1:action=startWidgetSession&1:widgetId=_100&2:ks=%7B1%3Aresult%3Aks%7D&2:service=baseentry&2:action=list&2:filter:objectType=KalturaBaseEntryFilter&2:filter:redirectFromEntryId='
            url += cItem['f_id']
            url += '&3:ks=%7B1%3Aresult%3Aks%7D&3:contextDataParams:referrer=http%3A%2F%2Fmediaserwer3.christusvincit-tv.pl&3:contextDataParams:objectType=KalturaEntryContextDataParams&3:contextDataParams:flavorTags=all&3:contextDataParams:streamerType=auto&3:service=baseentry&3:entryId=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&3:action=getContextData&4:ks=%7B1%3Aresult%3Aks%7D&4:service=metadata_metadata&4:action=list&4:version=-1&4:filter:metadataObjectTypeEqual=1&4:filter:orderBy=%2BcreatedAt&4:filter:objectIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&4:pager:pageSize=1&5:ks=%7B1%3Aresult%3Aks%7D&5:service=cuepoint_cuepoint&5:action=list&5:filter:objectType=KalturaCuePointFilter&5:filter:orderBy=%2BstartTime&5:filter:statusEqual=1&5:filter:entryIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&kalsig=404d9c08e114ce91328cd739e5151b80'
            sts, data = self.getPage(url)
            if not sts: return []

            try:
                data = json_loads(data)
                baseUrl = data[1]['objects'][0]['dataUrl']
                for item in data[2]['flavorAssets']:
                    if item['fileExt'] != 'mp4' or not item['isWeb']: continue
                    item['bitrate'] *= 1024
                    name = '%sx%s %s, bitrate: %s' % (item['width'], item['height'], formatBytes(item['size']*1024), item['bitrate'])
                    url = baseUrl.replace('/format/', '/flavorId/%s/format/' % item['id'])
                    urlsTab.append({'name':name, 'url':url, 'need_resolve':0, 'bitrate':item['bitrate'], 'original':item['isOriginal']})
                urlsTab.sort(key=lambda x: x['bitrate'], reverse=True)
            except Exception:
                printExc()
        if len(urlsTab):
            max_bitrate = int(config.plugins.iptvplayer.christusvincit_preferred_bitrate.value)
            urlsTab = CSelOneLink(urlsTab, lambda x: int(x['bitrate']), max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.christusvincit_use_preferred_bitrate.value:
                urlsTab = [urlsTab[0]]
        return urlsTab

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: ||| name[%s], category[%s] " % (name, category) )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listMain({'name':'category', 'type':'category'}, 'explore_item')

        elif category == 'explore_item':
            self.exploreItem(self.currItem)

        elif category == 'sub_items':
            self.listSubItems(self.currItem)

    #SEARCH
        elif category == 'list_search':
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
        CHostBase.__init__(self, Christusvincit(), True, [])

