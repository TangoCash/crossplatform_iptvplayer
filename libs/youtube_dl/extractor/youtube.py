#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, time
from urlparse import urlparse, urlunparse
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import *
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import _unquote
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetDefaultLang, byteify
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.jsinterp import JSInterpreter
from Plugins.Extensions.IPTVPlayer.iptvtools.iptvtypes import strwithmeta

try: import json
except Exception: import simplejson as json

SignAlgoExtractorObj = None

def ExtractorError(text):
    printDBG(text)
    SetIPTVPlayerLastHostError(_(text))
    

class CVevoSignAlgoExtractor:
    # MAX RECURSION Depth for security
    MAX_REC_DEPTH = 5

    def __init__(self):
        self.algoCache = {}
        self._cleanTmpVariables()
        self.cm = common()
        self.cm.HOST = 'python-urllib/2.7'

    def _cleanTmpVariables(self):
        self.fullAlgoCode = ''
        self.allLocalFunNamesTab = []
        self.objCache = {}
        self.playerData = ''

    def _jsToPy(self, jsFunBody):
        classNames = set()
        pythonFunBody = jsFunBody.replace('function', 'def').replace('{', ':\n\t').replace('}', '').replace(';', '\n\t').replace('var ', '')

        lines = pythonFunBody.split('\n')
        for i in range(len(lines)):
            #
            if '.reverse()' in lines[i] and '=' in lines[i] or 'return' in lines[i]:
                    lines[i] = lines[i].replace('.reverse()', '[::-1]')
            
            # a.split("") -> list(a)
            match = re.search('(\w+?)\.split\(""\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'list(' + match.group(1)  + ')')
            # a.length -> len(a)
            match = re.search('(\w+?)\.length', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'len(' + match.group(1)  + ')')
            # a.slice(3) -> a[3:]
            match = re.search('(\w+?)\.slice\(([0-9]+?)\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(1) + ('[%s:]' % match.group(2)) )
                if '=' not in lines[i] and 'return' not in lines[i]:
                    lines[i] = match.group(1) + '=' + lines[i]
                else:
                    TODO()
            
            # a.splice(e,f) -> a[e:f]
            match = re.search('(\w+?)\.splice\(([^,]+,[^,]+)\)', lines[i])
            if match:
                if '=' not in lines[i] and 'return' not in lines[i]:
                    lines[i] = lines[i].replace( match.group(0), 'del ' + match.group(1) + ('[%s]' % match.group(2).replace(',', ':')) )
                else:
                    TODO()
                
            # a.join("") -> "".join(a)
            match = re.search('(\w+?)\.join\(("[^"]*?")\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(2) + '.join(' + match.group(1) + ')' )
                
            # check if not class
            match = re.search('(\w+?)\.(\w+?)\((.+)\)', lines[i])
            if match and match.group(2) not in ['split', 'length', 'slice', 'join']:
                printDBG(': adding class [%s]\n' % match.group(1))
                classNames.add(match.group(1))
            
        return "\n".join(lines), classNames

    def _getLocalFunBody(self, funcname):
        # get function body
        func_m = re.search(
            r'''(?x)
                (?:function\s+%s|[{;,]\s*%s\s*=\s*function|var\s+%s\s*=\s*function)\s*
                \((?P<args>[^)]*)\)\s*
                \{(?P<code>[^}]+)\}''' % (
                re.escape(funcname), re.escape(funcname), re.escape(funcname)),
            self.playerData)
        if func_m is None:
            SetIPTVPlayerLastHostError(_('Could not find JS function %r') % funcname)
            return ''
        if func_m:
            # return jsFunBody
            return 'function %s(%s){%s}' % (funcname, func_m.group('args'), func_m.group('code').replace('\n', '').replace('\r', ''))
        return ''
        
    def _getFakeClassMethodName(self, className, methodName):
        return 'obj_%s_%s' % (className, methodName)
        
    def _extract_object(self, objname):
        obj = {}
        obj_m = re.search(
            (r'(?:var\s+)?%s\s*=\s*\{' % re.escape(objname)) +
            r'\s*(?P<fields>([a-zA-Z$0-9]+\s*:\s*function\(.*?\)\s*\{.*?\}(?:,\s*)?)*)' +
            r'\}\s*;',
            self.playerData)
        fields = obj_m.group('fields')
        # Currently, it only supports function definitions
        fields_m = re.finditer(
            r'(?P<key>[a-zA-Z$0-9]+)\s*:\s*function'
            r'\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}',
            fields)
        
        for f in fields_m:
            argnames = f.group('args').split(',')
            argnames.append('*args')
            argnames.append('**kwargs')
            obj[f.group('key')] = 'function %s(%s){%s}' % (self._getFakeClassMethodName(objname, f.group('key')), ','.join(argnames), f.group('code'))
        
        return obj

    def _getAllLocalSubFunNames(self, mainFunBody):
        #match = re.compile('[ =(,](\w+?)\([^)]*?\)').findall( mainFunBody )
        #printDBG("|||||||||||||||||||||| ALL FUNCTION NAMES:")
        match = re.compile('[ =(,]([a-zA-Z$]+?)\([a-z0-9,]*?\)').findall( mainFunBody )
        if len(match):
            # first item is name of main function, so omit it
            funNameTab = set( match[1:] )
            #printDBG("|||||||||||||||||||||| ALL FUNCTION NAMES: [%r]\n" % funNameTab)
            return funNameTab
        return set()

    def decryptSignature(self, s, playerUrl, extract_type='own'):
        printDBG("decrypt_signature sign_len[%d] playerUrl[%s] extract_type[%s] " % (len(s), playerUrl, extract_type) )
        # clear local data
        self._cleanTmpVariables()

        # use algoCache
        if playerUrl not in self.algoCache:
            # get player HTML 5 sript
            sts, self.playerData = self.cm.getPage(playerUrl)
            if sts: self.playerData = self.playerData.decode('utf-8', 'ignore')
            else:
                printExc('Unable to download playerUrl webpage')
                self._cleanTmpVariables()
                return '', extract_type
        
            #match = re.search("signature=([$a-zA-Z]+)", self.playerData)
            #if not match:
            #get main function name 
            match = re.search(r'\.sig\|\|([a-zA-Z0-9\$]+)\(', self.playerData)
            if match:
                mainFunName = match.group(1)
                printDBG('Main signature function name = "%s"' % mainFunName)
            else: 
                printDBG('Can not get main signature function name')
                self._cleanTmpVariables()
                return '', extract_type
            
            if extract_type == 'own':
                self._getfullAlgoCode(mainFunName)
                
                # wrap all local algo function into one function extractedSignatureAlgo()
                algoLines = self.fullAlgoCode.split('\n')
                for i in range(len(algoLines)):
                    algoLines[i] = '\t' + algoLines[i]
                self.fullAlgoCode  = 'def extractedSignatureAlgo(param):'
                self.fullAlgoCode += '\n'.join(algoLines)
                self.fullAlgoCode += '\n\treturn %s(param)' % mainFunName
                self.fullAlgoCode += '\noutSignature = extractedSignatureAlgo\n'
                self.fullAlgoCode = self.fullAlgoCode.replace("$", "xyz_")
                
                printDBG( "---------------------------------------" )
                printDBG( "|    ALGO FOR SIGNATURE DECRYPTION    |" )
                printDBG( "---------------------------------------" )
                printDBG( self.fullAlgoCode                         )
                printDBG( "---------------------------------------" )
                
                try:
                    algoCodeObj = compile(self.fullAlgoCode, '', 'exec')
                    # for security alow only flew python global function in algo code
                    vGlobals = {"__builtins__": None, 'len': len, 'list': list}

                    # local variable to pass encrypted sign and get decrypted sign
                    vLocals = { 'outSignature': '' }
                    
                    # execute prepared code
                    exec algoCodeObj in vGlobals, vLocals
                    algoCodeObj = vLocals['outSignature']
                    
                except Exception:
                    printExc('decryptSignature compile algo code EXCEPTION')
                    return '', extract_type
            else:
                jsi = JSInterpreter(self.playerData)
                initial_function = jsi.extract_function(mainFunName)
                algoCodeObj = lambda s: initial_function([s])
        else:
            # get algoCodeObj from algoCache
            extract_type = self.algoCache[playerUrl][0]
            algoCodeObj = self.algoCache[playerUrl][1]
            printDBG('Algo taken from cache extract_type[%s]' % extract_type)
        
        
        try:
            sig = algoCodeObj(s)
        except Exception:
            printExc('decryptSignature exec code EXCEPTION')
            self._cleanTmpVariables()
            return '', extract_type
        
        # if algo seems ok and not in cache, add it to cache
        if playerUrl not in self.algoCache and '' != sig:
            printDBG('Algo from player [%s] added to cache' % playerUrl)
            self.algoCache[playerUrl] = (extract_type, algoCodeObj)
            
        # free not needed data
        self._cleanTmpVariables()
        
        return sig, extract_type

    # Note, this method is using a recursion
    def _getfullAlgoCode( self, mainFunName, recDepth = 0, funBody = None ):
        if self.MAX_REC_DEPTH <= recDepth:
            printDBG('_getfullAlgoCode: Maximum recursion depth exceeded')
            return 
        
        if funBody == None:
            printDBG("============================================")
            printDBG(mainFunName)
            printDBG("============================================")
            funBody = self._getLocalFunBody( mainFunName )
            printDBG(funBody)
            printDBG("============================================")
        if '' != funBody:
            funNames = self._getAllLocalSubFunNames(funBody)
            if len(funNames):
                for funName in funNames:
                    if funName not in self.allLocalFunNamesTab:
                        self.allLocalFunNamesTab.append(funName)
                        printDBG("Add local function %s to known functions" % mainFunName)
                        self._getfullAlgoCode( funName, recDepth + 1 )

            # conver code from javascript to python 
            funBody, cassesNames = self._jsToPy(funBody)
            for className in cassesNames:
                addMethods = False
                if className in self.objCache:
                    obj = self.objCache[className]
                else:
                    obj = self._extract_object(className)
                    self.objCache[className] = obj
                    addMethods = True
                    
                for method in obj:
                    if addMethods:
                        fakeFunName = self._getFakeClassMethodName(className, method)
                        self._getfullAlgoCode( fakeFunName, recDepth + 1, obj[method] )
                    funBody = funBody.replace('%s.%s(' % (className, method), '%s(' % fakeFunName)
            
            self.fullAlgoCode += '\n' + funBody + '\n'
        return

class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information about the video (or videos) the URL refers to. This
    information includes the real video URL, the video title, author and
    others. The information is stored in a dictionary which is then
    passed to the FileDownloader. The FileDownloader processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The dictionaries must include the following fields:

    id:             Video identifier.
    url:            Final video URL.
    title:          Video title, unescaped.
    ext:            Video filename extension.

    The following fields are optional:

    format:         The video format, defaults to ext (used for --get-format)
    thumbnail:      Full URL to a video thumbnail image.
    description:    One-line video description.
    uploader:       Full name of the video uploader.
    upload_date:    Video upload date (YYYYMMDD).
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location of the video.
    player_url:     SWF Player URL (used for rtmpdump).
    subtitles:      The subtitle file contents.
    urlhandle:      [internal] The urlHandle to be used to download the file,
                    like returned by urllib.request.urlopen

    The fields should all be Unicode strings.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.

    _real_extract() must return a *list* of information dictionaries as
    described above.

    Finally, the _WORKING attribute should be set to False for broken IEs
    in order to warn the users and skip the tests.
    """

    _ready = False
    _downloader = None
    _WORKING = True

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url) is not None

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

    @property
    def IE_NAME(self):
        return type(self).__name__[:-2]

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            printDBG(u'%s: %s' % (video_id, note))
        sts, response = self.cm.getPage(url_or_request, {'return_data':False})
        if sts:
            return response
        else:
            raise ExtractorError('ERROR _request_webpage')

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns a tuple (page content as string, URL handle) """
        urlh = self._request_webpage(url_or_request, video_id, note, errnote)
        content_type = urlh.headers.get('Content-Type', '')
        m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
        if m:
            encoding = m.group(1)
        else:
            encoding = 'utf-8'
        webpage_bytes = urlh.read()

        try:
            url = url_or_request.get_full_url()
        except AttributeError:
            url = url_or_request
        #printDBG(u'Dumping request to ' + url)
        #dump = base64.b64encode(webpage_bytes).decode('ascii')
        #printDBG(dump)
        content = webpage_bytes.decode(encoding, 'replace')
        return (content, urlh)

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the data of the page as a string """
        return self._download_webpage_handle(url_or_request, video_id, note, errnote)[0]

    def to_screen(self, msg):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        printDBG(u'[%s] %s' % (self.IE_NAME, msg))

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        printDBG(u'%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        printDBG(u'%s: Downloading webpage' % video_id)

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        printDBG(u'Confirming age')

    #Methods for following #608
    #They set the correct value of the '_type' key
    def video_result(self, video_info):
        """Returns a video"""
        video_info['_type'] = 'video'
        return video_info
    def url_result(self, url, ie=None):
        """Returns a url that points to a page that should be processed"""
        #TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        return video_info
    def playlist_result(self, entries, playlist_id=None, playlist_title=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        return video_info

class SearchInfoExtractor(InfoExtractor):
    """
    Base class for paged search queries extractors.
    They accept urls in the format _SEARCH_KEY(|all|[0-9]):{query}
    Instances should define _SEARCH_KEY and _MAX_RESULTS.
    """

    @classmethod
    def _make_valid_url(cls):
        return r'%s(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\s\S]+)' % cls._SEARCH_KEY

    @classmethod
    def suitable(cls, url):
        return re.match(cls._make_valid_url(), url) is not None

    def _real_extract(self, query):
        mobj = re.match(self._make_valid_url(), query)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % query)

        prefix = mobj.group('prefix')
        query = mobj.group('query')
        if prefix == '':
            return self._get_n_results(query, 1)
        elif prefix == 'all':
            return self._get_n_results(query, self._MAX_RESULTS)
        else:
            n = int(prefix)
            if n <= 0:
                printDBG('invalid download number %s for query "%s"' % (n, query))
                raise ExtractorError('invalid download number %s for query "%s"' % (n, query))
            elif n > self._MAX_RESULTS:
                self._downloader.report_warning(u'%s returns max %i results (you requested %i)' % (self._SEARCH_KEY, self._MAX_RESULTS, n))
                n = self._MAX_RESULTS
            return self._get_n_results(query, n)

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        printDBG("This method must be implemented by sublclasses")
        raise NotImplementedError("This method must be implemented by sublclasses")
        


class YoutubeIE(InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/)                             # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:watch(?:_popup)?(?:\.php)?)?              # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         )?                                                   # optional -> youtube.com/xxxx is OK
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]+)                                         # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '36', '17', '13',
                          # Apple HTTP Live Streaming
                          '96', '95', '94', '93', '92', '132', '151',
                          # 3D
                          '85', '84', '102', '83', '101', '82', '100',
                          # Dash video
                          '138', '137', '248', '136', '247', '135', '246',
                          '245', '244', '134', '243', '133', '242', '160',
                          # Dash audio
                          '141', '172', '140', '171', '139',
                          ]
    _available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '36', '17', '13',
                                      # Apple HTTP Live Streaming
                                      '96', '95', '94', '93', '92', '132', '151',
                                      # 3D
                                      '85', '102', '84', '101', '83', '100', '82',
                                      # Dash video
                                      '138', '248', '137', '247', '136', '246', '245',
                                      '244', '135', '243', '134', '242', '133', '160',
                                      # Dash audio
                                      '172', '141', '171', '140', '139',
                                      ]
                                      
    _supported_formats = ['18', '22', '37', '38', # mp4
                          '82', '83', '84', '85', # mp4 3D
                          '92', '93', '94', '95', '96', '132', '151', # Apple HTTP Live Streaming
                          '133', '134', '135', '136', '137', '138', '160', # Dash mp4
                          '139', '140', '141', # Dash mp4 audio
                          ]
    
    _video_formats_map = {
        'flv': ['35', '34', '6', '5'],
        '3gp': ['36', '17', '13'],
        'mp4': ['38', '37', '22', '18'],
        'webm': ['46', '45', '44', '43'],
    }
    _video_extensions = {
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',

        # 3d videos
        '82': 'mp4',
        '83': 'mp4',
        '84': 'mp4',
        '85': 'mp4',
        '100': 'webm',
        '101': 'webm',
        '102': 'webm',

        # Apple HTTP Live Streaming
        '92': 'mp4',
        '93': 'mp4',
        '94': 'mp4',
        '95': 'mp4',
        '96': 'mp4',
        '132': 'mp4',
        '151': 'mp4',

        # Dash mp4
        '133': 'mp4v',
        '134': 'mp4v',
        '135': 'mp4v',
        '136': 'mp4v',
        '137': 'mp4v',
        '138': 'mp4v',
        '160': 'mp4v',

        # Dash mp4 audio
        '139': 'mp4a',
        '140': 'mp4a',
        '141': 'mp4a',

        # Dash webm
        '171': 'webm',
        '172': 'webm',
        '242': 'webm',
        '243': 'webm',
        '244': 'webm',
        '245': 'webm',
        '246': 'webm',
        '247': 'webm',
        '248': 'webm',
    }
    _video_dimensions = {
        '5': '240x400',
        '6': '???',
        '13': '???',
        '17': '144x176',
        '18': '360x640',
        '22': '720x1280',
        '34': '360x640',
        '35': '480x854',
        '36': '240x320',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
        '46': '1080x1920',
        '82': '360p',
        '83': '480p',
        '84': '720p',
        '85': '1080p',
        '92': '240p',
        '93': '360p',
        '94': '480p',
        '95': '720p',
        '96': '1080p',
        '100': '360p',
        '101': '480p',
        '102': '720p',
        '132': '240p',
        '151': '72p',
        '133': '240p',
        '134': '360p',
        '135': '480p',
        '136': '720p',
        '137': '1080p',
        '138': '>1080p',
        '139': '48k',
        '140': '128k',
        '141': '256k',
        '160': '192p',
        '171': '128k',
        '172': '256k',
        '242': '240p',
        '243': '360p',
        '244': '480p',
        '245': '480p',
        '246': '480p',
        '247': '720p',
        '248': '1080p',
    }

    _special_itags = {
        '82': '3D',
        '83': '3D',
        '84': '3D',
        '85': '3D',
        '100': '3D',
        '101': '3D',
        '102': '3D',
        '133': 'DASH Video',
        '134': 'DASH Video',
        '135': 'DASH Video',
        '136': 'DASH Video',
        '137': 'DASH Video',
        '138': 'DASH Video',
        '139': 'DASH Audio',
        '140': 'DASH Audio',
        '141': 'DASH Audio',
        '160': 'DASH Video',
        '171': 'DASH Audio',
        '172': 'DASH Audio',
        '242': 'DASH Video',
        '243': 'DASH Video',
        '244': 'DASH Video',
        '245': 'DASH Video',
        '246': 'DASH Video',
        '247': 'DASH Video',
        '248': 'DASH Video',
    }
    IE_NAME = u'youtube'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def __init__(self, params={}):
        proxyURL = params.get('proxyURL', '')
        useProxy = params.get('useProxy', False)
        self.cm = common(proxyURL, useProxy)
        self.cm.HOST = 'Mpython-urllib/2.7'
        
    def report_lang(self):
        """Report attempt to set language."""
        printDBG(u'Setting language')

    def report_login(self):
        """Report attempt to log in."""
        printDBG(u'Logging in')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        printDBG(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Downloading video info webpage' % video_id)

    def report_video_subtitles_download(self, video_id):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Checking available subtitles' % video_id)

    def report_video_subtitles_request(self, video_id, sub_lang, format):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Downloading video subtitles for %s.%s' % (video_id, sub_lang, format))

    def report_video_subtitles_available(self, video_id, sub_lang_list):
        """Report available subtitles."""
        sub_lang = ",".join(list(sub_lang_list.keys()))
        printDBG(u'%s: Available subtitles for video: %s' % (video_id, sub_lang))

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        printDBG(u'%s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        printDBG(u'%s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        printDBG(u'RTMP download detected')

    def _print_formats(self, formats):
        printDBG('Available formats:')
        for x in formats:
            printDBG('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???')))

    def _real_initialize(self):

        # Set language
        self.report_lang()
        sts, data = self.cm.getPage(self._LANG_URL)
        if not sts:
            self._downloader.report_warning(u'unable to set language')

        # No authentication to be performed
        if username is None: return
        sts, login_page = self.cm.getPage(self._LOGIN_URL)
        if sts: login_page = login_page.decode('utf-8')
        else:
            self._downloader.report_warning(u'unable to fetch login page')
            return

        galx = None
        dsh = None
        match = re.search(re.compile(r'<input.+?name="GALX".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          galx = match.group(1)

        match = re.search(re.compile(r'<input.+?name="dsh".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          dsh = match.group(1)

        # Log in
        login_form_strs = {
                u'continue': u'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
                u'Email': username,
                u'GALX': galx,
                u'Passwd': password,
                u'PersistentCookie': u'yes',
                u'_utf8': u'霱',
                u'bgresponse': u'js_disabled',
                u'checkConnection': u'',
                u'checkedDomains': u'youtube',
                u'dnConn': u'',
                u'dsh': dsh,
                u'pstMsg': u'0',
                u'rmShown': u'1',
                u'secTok': u'',
                u'signIn': u'Sign in',
                u'timeStmp': u'',
                u'service': u'youtube',
                u'uilel': u'3',
                u'hl': u'en_US',
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
        
        
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')
        self.report_login()
        sts, login_results = self.cm.getPage(self._LOGIN_URL, {'raw_post_data':True}, login_data)
        if sts:
            login_results = login_results.decode('utf-8')
            printDBG(login_results)
            if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username or password')
                return
        else:
            self._downloader.report_warning(u'unable to log in')
            return

        # Confirm age
        age_form = { 'next_url': '/', 'action_confirm': 'Confirm',}
        self.report_age_confirmation()
        sts, age_results = self.cm.getPage(self._AGE_URL, {}, age_form)
        if not sts:
            printDBG('Unable to confirm age')
            raise ExtractorError('Unable to confirm age')

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            printDBG('Invalid URL: %s' % url)
            raise ExtractorError('Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _get_automatic_captions(self, video_id, webpage=None):
        sub_tracks = []
        if None == webpage:
            url = 'http://www.youtube.com/watch?v=%s&hl=%s&has_verified=1' % (video_id, GetDefaultLang())
            sts, data = self.cm.getPage(url)
            if not sts: return sub_tracks
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, ';ytplayer.config =', '};', False)
        if not sts: return sub_tracks
        try:
            player_config = byteify(json.loads(data.strip()+'}'))
            args = player_config['args']
            caption_url = args.get('ttsurl')
            if caption_url:
                timestamp = args['timestamp']
                # We get the available subtitles
                list_params = urllib.urlencode({
                    'type': 'list',
                    'tlangs': 1,
                    'asrs': 1,
                })
                list_url = caption_url + '&' + list_params
                caption_list = self.cm.getPage(list_url)
                printDBG(caption_list)
                return sub_lang_list
                
                original_lang_node = caption_list.find('track')
                if original_lang_node is None:
                    return []
                original_lang = original_lang_node.attrib['lang_code']
                caption_kind = original_lang_node.attrib.get('kind', '')

                sub_lang_list = {}
                for lang_node in caption_list.findall('target'):
                    sub_lang = lang_node.attrib['lang_code']
                    sub_formats = []
                    for ext in self._SUBTITLE_FORMATS:
                        params = urllib.urlencode({
                            'lang': original_lang,
                            'tlang': sub_lang,
                            'fmt': ext,
                            'ts': timestamp,
                            'kind': caption_kind,
                        })
                        sub_formats.append({
                            'url': caption_url + '&' + params,
                            'ext': ext,
                        })
                    sub_lang_list[sub_lang] = sub_formats
                return sub_lang_list
            
            # Some videos don't provide ttsurl but rather caption_tracks and
            # caption_translation_languages (e.g. 20LmZk1hakA)
            caption_tracks = args['caption_tracks']
            caption_translation_languages = args['caption_translation_languages']
            caption_url = compat_parse_qs(caption_tracks.split(',')[0])['u'][0]
            parsed_caption_url = urlparse(caption_url)
            caption_qs = compat_parse_qs(parsed_caption_url.query)

            sub_lang_list = {}
            for lang in caption_translation_languages.split(','):
                lang_qs = compat_parse_qs(urllib.unquote_plus(lang))
                sub_lang = lang_qs.get('lc', [None])[0]
                if not sub_lang: continue
                caption_qs.update({
                    'tlang': [sub_lang],
                    'fmt': ['vtt'],
                })
                sub_url = urlunparse(parsed_caption_url._replace(
                    query=urllib.urlencode(caption_qs, True)))
                sub_tracks.append({'title':lang_qs['n'][0].encode('utf-8'), 'url':sub_url, 'lang':sub_lang.encode('utf-8'), 'ytid':len(sub_tracks), 'format':'vtt'})
        except Exception:
            printExc()
        return sub_tracks
        
    def _get_subtitles(self, video_id):
        sub_tracks = []
        try:
            url = 'https://video.google.com/timedtext?hl=%s&type=list&v=%s' % (GetDefaultLang(), video_id)
            sts, data = self.cm.getPage(url)
            if not sts: return sub_tracks
            
            encoding = self.cm.ph.getDataBeetwenMarkers(data, 'encoding="', '"', False)[1]
            
            def getArg(item, name):
                val = self.cm.ph.getDataBeetwenMarkers(item, '%s="' % name, '"', False)[1]
                return val.decode(encoding).encode(encoding)
            
            data = data.split('/>')
            for item in data:
                if 'lang_code' not in item: continue
                id = getArg(item, 'id')
                name = getArg(item, 'name')
                lang_code = getArg(item, 'lang_code')
                lang_original = getArg(item, 'lang_original')
                lang_translated = getArg(item, 'lang_translated')

                title = (name + ' ' + lang_translated).strip()
                params = {'lang':lang_code, 'v':video_id, 'fmt':'vtt', 'name':name}
                url = 'https://www.youtube.com/api/timedtext?' + urllib.urlencode(params)
                sub_tracks.append({'title':title, 'url':url, 'lang':lang_code, 'ytid':id, 'format':'vtt'})
        except Exception:
            printExc()
        printDBG(sub_tracks)
        return sub_tracks

    def _real_extract(self, url, ):
        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            #https
            url = 'http://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self._extract_id(url)
        
        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        
        sts, video_webpage_bytes = self.cm.getPage(url)
        
        if not sts:
            raise ExtractorError('Unable to download video webpage')

        video_webpage = video_webpage_bytes.decode('utf-8', 'ignore')
        
        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = ''

        # Get video info
        self.report_video_info_webpage_download(video_id)

        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            self.report_age_confirmation()
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            data = compat_urllib_parse.urlencode({'video_id': video_id,
                                                  'el': 'embedded',
                                                  'gl': 'US',
                                                  'hl': 'en',
                                                  'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                                                  'asv': 3,
                                                  'sts':'1588',
                                                  })
            video_info_url = 'https://www.youtube.com/get_video_info?' + data
            video_info = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
        else:
            age_gate = False
            for el_type in ['&el=detailpage', '&el=embedded', '&el=vevo', '']:
                #https
                video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                        % (video_id, el_type))
                video_info = self._download_webpage(video_info_url, video_id,
                                        note=False,
                                        errnote='unable to download video info webpage')
                if '&token=' in video_info:
                    break
        if '&token=' not in video_info:
            if 'reason' in video_info:
                pass # ToDo extract reason
            raise ExtractorError('"token" parameter not in video info')
        
        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            printDBG('"rental" videos not supported')
            raise ExtractorError('"rental" videos not supported')

        # Start extracting information
        self.report_information_extraction(video_id)
        
        video_info = video_info.split('&')
        video_info2 = {}
        for item in video_info:
            item = item.split('=')
            if len(item) < 2: continue
            video_info2[item[0].strip()] = item[1].strip()
        video_info = video_info2
        del video_info2

        # subtitles
        if 'length_seconds' not in video_info:
            video_duration = ''
        else:
            video_duration = video_info['length_seconds']
        
        if 'url_encoded_fmt_stream_map' in video_info:
            video_info['url_encoded_fmt_stream_map'] = [_unquote(video_info['url_encoded_fmt_stream_map'])]
        if 'adaptive_fmts' in video_info:
            video_info['adaptive_fmts'] = [_unquote(video_info['adaptive_fmts'])]
        
        # Decide which formats to download
        try:
            mobj = re.search(r';ytplayer.config = ({.*?});', video_webpage)
            if not mobj:
                raise ValueError('Could not find vevo ID')
            ytplayer_config = json.loads(mobj.group(1))
            args = ytplayer_config['args']
            # Easy way to know if the 's' value is in url_encoded_fmt_stream_map
            # this signatures are encrypted
            if 'url_encoded_fmt_stream_map' not in args:
                raise ValueError(u'No stream_map present') # caught below
            re_signature = re.compile(r'[&,]s=')
            m_s = re_signature.search(args['url_encoded_fmt_stream_map'])
            if m_s is not None:
                self.to_screen(u'%s: Encrypted signatures detected.' % video_id)
                video_info['url_encoded_fmt_stream_map'] = [args['url_encoded_fmt_stream_map']]
            m_s = re_signature.search(args.get('adaptive_fmts', ''))
        except ValueError:
            pass

        # Decide which formats to download
        req_format = 'all'
        
        is_m3u8 = 'no'
        
        url_map = {}
        if len(video_info.get('url_encoded_fmt_stream_map', [])) >= 1 or len(video_info.get('adaptive_fmts', [])) >= 1:
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts',[''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                printDBG('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.')
                raise
            
            for url_data_str in encoded_url_map.split(','):
                add = True
                if 'itag=' in url_data_str and 'url=' in url_data_str:
                    url_data_str = url_data_str.split('&')
                    url_data = {}
                    
                    supported = False
                    for item in url_data_str:
                        item = item.split('=')
                        if len(item) < 2: continue
                        key = item[1].strip()
                        if item[0] == 'itag':
                            if key in self._supported_formats:
                                supported = True
                            else:
                                break
                        url_data[item[0]] = key
                            
                    if not supported:
                        continue
                    
                    url = _unquote(url_data['url'])
                    if 'sig' in url_data:
                        signature = url_data['sig']
                        url += '&signature=' + signature
                    elif 's' in url_data:
                        encrypted_sig = url_data['s']
                        signature = ''
                        match = re.search('"([^"]+?html5player-[^"]+?\.js)"', video_webpage)
                        if None == match:
                            match = re.search('"([^"]+?(?:www|player)-([^/]+)/base\.js)"', video_webpage)
                        if match:
                            playerUrl = match.group(1).replace('\\', '').replace('https:', 'http:')
                            if not playerUrl.startswith('http'):
                                playerUrl = 'http:' + playerUrl
                            global SignAlgoExtractorObj
                            if None == SignAlgoExtractorObj:
                                SignAlgoExtractorObj = CVevoSignAlgoExtractor()
                            signature, eType = SignAlgoExtractorObj.decryptSignature( encrypted_sig, playerUrl )
                            if '' == signature and eType == 'own':
                                signature, eType = SignAlgoExtractorObj.decryptSignature( encrypted_sig, playerUrl, 'youtube_dl' )
                        else:
                            printDBG("YT HTML PLAYER not available!")
                        if 0 == len(signature):
                            printDBG("YT signature description problem")
                            add = False
                        url += '&signature=' + signature

                    if not 'ratebypass' in url:
                        url += '&ratebypass=yes'
                    if add:
                        url_map[url_data['itag']] = url
            video_url_list = self._get_video_url_list(url_map)
   
        if video_info.get('hlsvp') and not video_url_list:
            is_m3u8 = 'yes'
            manifest_url = _unquote(video_info['hlsvp'])
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            video_url_list = self._get_video_url_list(url_map)
        
        if not video_url_list:
            return []
        
        sub_tracks = self._get_subtitles(video_id)
        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            #video_format = '{0} - {1}'.format(format_param if format_param else video_extension,
            #                                  self._video_dimensions.get(format_param, '???'))
            video_format = self._video_dimensions.get(format_param, '???')
            video_real_url = video_real_url.encode('utf-8')
            if len(sub_tracks):
                video_real_url = strwithmeta(video_real_url, {'external_sub_tracks':sub_tracks})

            results.append({
                'id':       video_id.encode('utf-8'),
                'url':      video_real_url,
                'uploader': '',
                'title':    '',
                'ext':      video_extension.encode('utf-8'),
                'format':   video_format.encode('utf-8'),
                'thumbnail':    '',
                'duration':     video_duration.encode('utf-8'),
                'player_url':   player_url.encode('utf-8'),
                'm3u8'      :   is_m3u8.encode('utf-8'),
            })
            
        return results
        

    def _extract_from_m3u8(self, manifest_url, video_id):
        url_map = {}
        def _get_urls(_manifest):
            lines = _manifest.split('\n')
            urls = filter(lambda l: l and not l.startswith('#'),
                            lines)
            return urls
        manifest = self._download_webpage(manifest_url, video_id, u'Downloading formats manifest')
        formats_urls = _get_urls(manifest)
        for format_url in formats_urls:
            itag = self._search_regex(r'itag/(\d+?)/', format_url, 'itag')
            url_map[itag] = format_url
        return url_map

    def _search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        compiled_regex_type = type(re.compile(''))
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj: break

        if mobj:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif default is not None:
            return default
        elif fatal:
            printDBG('Unable to extract %s' % name)
            raise
        else:
            printDBG('unable to extract %s; please report this issue on http://yt-dl.org/bug' % name)
            return None
            
    def _get_video_url_list(self, url_map):
        format_list = self._available_formats_prefer_free # available_formats
        existing_formats = [x for x in format_list if x in url_map]
        
        return [(f, url_map[f]) for f in existing_formats] # All formats

        