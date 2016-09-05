# -*- coding: utf-8 -*-
#
#  Konfigurator dla iptv 2013
#  autorzy: j00zek, samsamsam
#

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvtools import printDBG, printExc, GetSkinsList, GetHostsList, GetEnabledHostsList, \
                                                          IsHostEnabled, IsExecutable, CFakeMoviePlayerOption, GetAvailableIconSize
from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _, IPTVPlayerNeedInit
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.Screen import Screen

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, ConfigOnOff, Config, ConfigInteger, ConfigSubList, ConfigText, getConfigListEntry, configfile
###################################################


###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer = ConfigSubsection()


config.plugins.iptvplayer.exteplayer3path = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.gstplayerpath   = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.wgetpath        = ConfigText(default = "wget", fixed_size = False)
config.plugins.iptvplayer.rtmpdumppath    = ConfigText(default = "rtmpdump", fixed_size = False)
config.plugins.iptvplayer.f4mdumppath     = ConfigText(default = "f4mdump", fixed_size = False)
config.plugins.iptvplayer.uchardetpath    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.set_curr_title  = ConfigYesNo(default = False)
config.plugins.iptvplayer.curr_title_file = ConfigText(default = "", fixed_size = False) 
config.plugins.iptvplayer.plarform        = ConfigSelection(default = "auto", choices = [("auto", "auto"),("mipsel", _("mipsel")),("sh4", _("sh4")),("i686", _("i686")), ("armv7", _("armv7")), ("armv5t", _("armv5t")), ("unknown", _("unknown"))])

config.plugins.iptvplayer.showcover          = ConfigYesNo(default = False)
config.plugins.iptvplayer.deleteIcons        = ConfigSelection(default = "3", choices = [("0", _("after closing")),("1", _("after day")),("3", _("after three days")),("7", _("after a week"))]) 
config.plugins.iptvplayer.allowedcoverformats= ConfigSelection(default = "jpeg,png", choices = [("jpeg,png,gif", _("jpeg,png,gif")),("jpeg,png", _("jpeg,png")),("jpeg", _("jpeg")),("all", _("all"))]) 
config.plugins.iptvplayer.showinextensions   = ConfigYesNo(default = True)
config.plugins.iptvplayer.showinMainMenu     = ConfigYesNo(default = False)
config.plugins.iptvplayer.ListaGraficzna     = ConfigYesNo(default = False)
config.plugins.iptvplayer.NaszaSciezka       = ConfigDirectory(default = "/hdd/movie/") #, fixed_size = False)
config.plugins.iptvplayer.bufferingPath      = ConfigDirectory(default = config.plugins.iptvplayer.NaszaSciezka.value) #, fixed_size = False)
config.plugins.iptvplayer.buforowanie        = ConfigYesNo(default = False)
config.plugins.iptvplayer.buforowanie_m3u8   = ConfigYesNo(default = True)
config.plugins.iptvplayer.buforowanie_rtmp   = ConfigYesNo(default = False)
config.plugins.iptvplayer.requestedBuffSize  = ConfigInteger(5, (1,120))
config.plugins.iptvplayer.requestedAudioBuffSize  = ConfigInteger(256, (1,10240))

config.plugins.iptvplayer.IPTVDMRunAtStart      = ConfigYesNo(default = False)
config.plugins.iptvplayer.IPTVDMShowAfterAdd    = ConfigYesNo(default = True)
config.plugins.iptvplayer.IPTVDMMaxDownloadItem = ConfigSelection(default = "1", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4")])

config.plugins.iptvplayer.AktualizacjaWmenu = ConfigYesNo(default = True)
config.plugins.iptvplayer.sortuj = ConfigYesNo(default = True)
config.plugins.iptvplayer.remove_diabled_hosts = ConfigYesNo(default = False)

def GetMoviePlayerName(player):
    map = {"auto":_("auto"), "mini": _("internal"), "standard":_("standard"), 'exteplayer': _("external eplayer3"), 'extgstplayer': _("external gstplayer")}
    return map.get(player, _('unknown'))
    
def ConfigPlayer(player):
    return (player, GetMoviePlayerName(player))

config.plugins.iptvplayer.NaszPlayer = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"), ConfigPlayer("mini"), ConfigPlayer('extgstplayer'), ConfigPlayer("standard")])

# without buffering mode
#sh4
config.plugins.iptvplayer.defaultSH4MoviePlayer0         = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('exteplayer'),ConfigPlayer('extgstplayer')]) 
config.plugins.iptvplayer.alternativeSH4MoviePlayer0     = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('exteplayer'),ConfigPlayer('extgstplayer')]) 

#mipsel
config.plugins.iptvplayer.defaultMIPSELMoviePlayer0      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeMIPSELMoviePlayer0  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

#i686
config.plugins.iptvplayer.defaultI686MoviePlayer0        = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer')])
config.plugins.iptvplayer.alternativeI686MoviePlayer0    = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer')])
# end without buffering mode players

#armv7
config.plugins.iptvplayer.defaultARMV7MoviePlayer0      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeARMV7MoviePlayer0  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

#armv5t
config.plugins.iptvplayer.defaultARMV5TMoviePlayer0      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeARMV5TMoviePlayer0  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

# with buffering mode
#sh4
config.plugins.iptvplayer.defaultSH4MoviePlayer         = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('exteplayer'),ConfigPlayer('extgstplayer')]) 
config.plugins.iptvplayer.alternativeSH4MoviePlayer     = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('exteplayer'),ConfigPlayer('extgstplayer')]) 

#mipsel
config.plugins.iptvplayer.defaultMIPSELMoviePlayer      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeMIPSELMoviePlayer  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

#i686
config.plugins.iptvplayer.defaultI686MoviePlayer        = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer')])
config.plugins.iptvplayer.alternativeI686MoviePlayer    = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer')])

#armv7
config.plugins.iptvplayer.defaultARMV7MoviePlayer      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeARMV7MoviePlayer  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

#armv5t
config.plugins.iptvplayer.defaultARMV5TMoviePlayer      = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])
config.plugins.iptvplayer.alternativeARMV5TMoviePlayer  = ConfigSelection(default = "auto", choices = [ConfigPlayer("auto"),ConfigPlayer("mini"),ConfigPlayer("standard"),ConfigPlayer('extgstplayer'),ConfigPlayer('exteplayer')])

# end with buffering mode players

config.plugins.iptvplayer.SciezkaCache = ConfigDirectory(default = "/hdd/IPTVCache/") #, fixed_size = False)
config.plugins.iptvplayer.NaszaTMP = ConfigDirectory(default = "/tmp/") #, fixed_size = False)
config.plugins.iptvplayer.ZablokujWMV = ConfigYesNo(default = True)

#config.plugins.iptvplayer.hd3d_login    = ConfigText(default="", fixed_size = False)
#config.plugins.iptvplayer.hd3d_password = ConfigText(default="", fixed_size = False)

config.plugins.iptvplayer.useSubtitlesParserExtension = ConfigYesNo(default = True)
config.plugins.iptvplayer.opensuborg_login    = ConfigText(default="", fixed_size = False)
config.plugins.iptvplayer.opensuborg_password = ConfigText(default="", fixed_size = False)

config.plugins.iptvplayer.debugprint = ConfigSelection(default = "", choices = [("", _("no")),("console", _("yes, to console")),("debugfile", _("yes, to file /hdd/iptv.dbg"))]) 

#icons
config.plugins.iptvplayer.IconsSize = ConfigSelection(default = "135", choices = [("135", "135x135"),("120", "120x120"),("100", "100x100")]) 
config.plugins.iptvplayer.numOfRow = ConfigSelection(default = "0", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4"),("0", "auto")])
config.plugins.iptvplayer.numOfCol = ConfigSelection(default = "0", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4"),("5", "5"),("6", "6"),("7", "7"),("8", "8"),("0", "auto")])

config.plugins.iptvplayer.skin = ConfigSelection(default = "Default", choices = GetSkinsList())

#Pin code

config.plugins.iptvplayer.fakePin = ConfigSelection(default = "fake", choices = [("fake", "****")])
config.plugins.iptvplayer.pin = ConfigText(default = "0000", fixed_size = False)
config.plugins.iptvplayer.disable_live = ConfigYesNo(default = False)
config.plugins.iptvplayer.configProtectedByPin = ConfigYesNo(default = False)
config.plugins.iptvplayer.pluginProtectedByPin = ConfigYesNo(default = False)

config.plugins.iptvplayer.httpssslcertvalidation = ConfigYesNo(default = False)

#PROXY
config.plugins.iptvplayer.proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)
config.plugins.iptvplayer.german_proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)
config.plugins.iptvplayer.russian_proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)
config.plugins.iptvplayer.ukrainian_proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)

# Update
config.plugins.iptvplayer.autoCheckForUpdate = ConfigYesNo(default = False)
config.plugins.iptvplayer.updateLastCheckedVersion = ConfigText(default = "00.00.00.00", fixed_size = False)
config.plugins.iptvplayer.fakeUpdate               = ConfigSelection(default = "fake", choices = [("fake", "  ")])
config.plugins.iptvplayer.downgradePossible        = ConfigYesNo(default = False)
config.plugins.iptvplayer.possibleUpdateType       = ConfigSelection(default = "precompiled", choices = [("sourcecode", _("with source code")),("precompiled", _("precompiled")), ("all", _("all types"))]) 

# Hosts lists
config.plugins.iptvplayer.fakeHostsList = ConfigSelection(default = "fake", choices = [("fake", "  ")])


# External movie player settings
config.plugins.iptvplayer.fakExtMoviePlayerList = ConfigSelection(default = "fake", choices = [("fake", "  ")])

# hidden options
config.plugins.iptvplayer.hiddenAllVersionInUpdate = ConfigYesNo(default = False)
config.plugins.iptvplayer.hidden_ext_player_def_aspect_ratio = ConfigSelection(default = "-1", choices = [("-1", _("default")), ("0", _("4:3 Letterbox")), ("1", _("4:3 PanScan")), ("2", _("16:9")), ("3", _("16:9 always")), ("4", _("16:10 Letterbox")), ("5", _("16:10 PanScan")), ("6", _("16:9 Letterbox"))] )
        
config.plugins.iptvplayer.search_history_size  = ConfigInteger(50, (0, 1000000))
config.plugins.iptvplayer.autoplay_start_delay  = ConfigInteger(3, (1, 1000000))

###################################################

########################################################
# Generate list of hosts options for Enabling/Disabling
########################################################
class ConfigIPTVHostOnOff(ConfigOnOff):
    def __init__(self, default = False):
        ConfigOnOff.__init__(self, default = default)

gListOfHostsNames = GetHostsList()
for hostName in gListOfHostsNames:
    try:
        # as default all hosts are enabled
        if hostName in ['ipla']:
            enabledByDefault = 'False'
        else:
            enabledByDefault = 'True'
        exec('config.plugins.iptvplayer.host' + hostName + ' = ConfigIPTVHostOnOff(default = ' + enabledByDefault + ')')
    except:
        printExc(hostName)

###################################################

