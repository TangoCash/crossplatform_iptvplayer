#!/bin/bash
tmpDir="/tmp"
daemonDir="/usr/share/E2emulator/Plugins/Extensions/IPTVPlayer"
pluginDir="/var/tuxbox/plugins/neutrinoIPTV"
daemonTMPDir="/tmp/IPTVPlayer"
[ -e $daemonTMPDir ] || mkdir $daemonTMPDir

if `grep -q 'language=polski'</var/tuxbox/config/neutrino.conf`;then
	isPL=1
fi

############################## syncing neutrinoIPTV and components from opkg ##############################
[ $isPL ] && (echo "Aktualizacja opkg...") || (echo "Updating opkg...")
opkg update >/dev/null
if `opkg list-upgradable|grep -q 'neutrino-full-python-src'`;then # in case python dev package has changed
  [ $isPL ] && (echo "Aktualizacja neutrino-full-python-src") || (echo "Updating neutrino-full-python-src")
  opkg upgrade neutrino-full-python-src
  sync
fi
if `opkg list-upgradable|grep -q 'neutrino-mini-python-iptv'`;then # in case python package has changed
  [ $isPL ] && (echo "Aktualizacja neutrino-mini-python-iptv") || (echo "Updating neutrino-mini-python-iptv")
  opkg upgrade neutrino-mini-python-iptv
  sync
fi
if `opkg list-upgradable|grep -q 'neutrino-e2emulator-by-j00zek'`;then #in case E2emulator has changed
  [ $isPL ] && (echo "Aktualizacja neutrino-e2emulator-by-j00zek") || (echo "Updating neutrino-e2emulator-by-j00zek")
  opkg upgrade neutrino-e2emulator-by-j00zek
  sync
fi
if `opkg list-upgradable|grep -q 'neutrino-iptvplayer-by-j00zek'`;then #to get latest neutrino specific scripts
  [ $isPL ] && (echo "Aktualizacja neutrino-iptvplayer-by-j00zek") || (echo "Updating neutrino-iptvplayer-by-j00zek")
  opkg upgrade neutrino-iptvplayer-by-j00zek
  sync
fi
############################## downloading IPTVdaemon ##############################
[ $isPL ] && (echo "Sprawdzanie aktualności obecnej wersji") || (echo "Checking if current version is up-2-date")
versionURL="http://iptvplayer.vline.pl/download/update/lastversion.php"
latestGZ="http://iptvplayer.vline.pl/download/update/latest.pythonX.X.tar.gz"
[ -e $daemonDir ] || exit 0
[ -f $daemonDir/version ] || exit 0
curVER=`cat $daemonDir/version`
lastVER=`wget -q $versionURL -O -`
if [ $? -gt 0 ];then 
  [ $isPL ] && (echo "Błąd pobierania numeru wersji z iptvplayer.vline.pl") || (echo "Error getting version info from iptvplayer.vline.pl")
  exit 0
elif [ "$curVER" == "$lastVER" ];then
  [ $isPL ] && (echo "Aktualna wersja ($curVER) jest już zainstalowana :)") || (echo "The lates version ($curVER) is already installed")
  exit 0
fi
echo "[$curVER] > [$lastVER]"

[ -e $tmpDir/iptvupd.tar.gz ] && rm -f $tmpDir/iptvupd.tar.gz
[ $isPL ] && (echo "Pobieranie archiwum") || (echo "Downloading archive")
wget -q $latestGZ -O $tmpDir/iptvupd.tar.gz
if [ $? -gt 0 ] || [ ! -e $tmpDir/iptvupd.tar.gz ] || [ "`stat -c %s /tmp/iptvupd.tar.gz`" -lt 500000 ];then
  [ $isPL ] && (echo "Błąd pobierania archiwum z iptvplayer.vline.pl") || (echo "Error downloading archive from iptvplayer.vline.pl")
  exit 0
fi
[ $isPL ] && (echo "Rozpakowywanie archiwum...") || (echo "extracting archive")
cd $tmpDir
tar -xzf ./iptvupd.tar.gz
if [ $? -gt 0 ];then
  [ $isPL ] && (echo "Błąd rozpakowania archiwum") || (echo "Error extracting archive")
  exit 0
fi
rm -f $tmpDir/iptvupd.tar.gz
if [ ! -e /tmp/iptvplayer-for-e2.git ]; then
  [ $isPL ] && (echo "Rozpakowane archiwum ma złą strukturę katalogów") || (echo "Extracted archive has incorrect folders structure")
  exit 0
fi
############################## preparing/patching IPTVdaemon ##############################
[ $isPL ] && echo "Przygotowanie IPTVdemona" || echo 'patching IPTVdaemon...'
cd /tmp/iptvplayer-for-e2.git

subDIRs="cache components icons/logos hosts libs scripts tools iptvdm locale"
for subDIR in $subDIRs
do
  [ -e $daemonDir/$subDIR ] && rm -rf $daemonDir/$subDIR/* || mkdir -p $daemonDir/$subDIR
  #cp -a ./IPTVPlayer/$subDIR/* $daemonDir/$subDIR/
  [ -e $daemonTMPDir/$subDIR ] && rm -rf $daemonTMPDir/$subDIR/* || mkdir -p $daemonTMPDir/$subDIR
  cp -a ./IPTVPlayer/$subDIR/* $daemonTMPDir/$subDIR/
done
subDIRs="components hosts libs scripts tools iptvdm dToolsSet"
for subDIR in $subDIRs
do
  [ -e $daemonTMPDir/$subDIR/ ] || mkdir -p $daemonTMPDir/$subDIR/
  ln -sf $daemonDir/__init__.py $daemonTMPDir/$subDIR/__init__.py
done
sed -i "s/^name=.*$/name=IPTV for Neutrino @j00zek v.$wersja/" $pluginDir/neutrinoIPTV.cfg
sed -i "s/^name.polski=.*$/name.polski=IPTV dla Neutrino @j00zek w.$wersja/" $pluginDir/neutrinoIPTV.cfg
rm -rf /tmp/iptvplayer-for-e2.git
############################## logos structure & names ##############################
[ $isPL ] && echo "Przenoszenie ikon..." || echo 'Moving logos...'
mv -f $daemonTMPDir/icons/logos/*.png $daemonTMPDir/icons/
rm -rf $daemonTMPDir/icons/logos/
rm -rf $daemonTMPDir/icons/favourites*
cd $daemonTMPDir/icons/
for myfile in `ls ./*logo.png|grep -v '__init__'`
do
  newName=`echo $myfile|sed 's/logo//'`
  mv -f $myfile $newName
done
############################## hosts names ##############################
[ $isPL ] && echo "Zmiana nazw hostów..." || echo 'Changing hosts names...'
cd $daemonTMPDir/hosts/
rm -f ./list.txt
for myfile in `ls ./*.py`
do
  newName=`echo $myfile|sed 's/host//'`
  [ $myfile == $newName ] || mv -f $myfile $newName
done
############################## Adapt congig.py file ##############################
[ $isPL ] && echo "Modyfikowanie konfiguacji..." || echo 'Changing configuration...'
myFile=$daemonTMPDir/components/iptvconfigmenu.py
sed -i '/class ConfigMenu(ConfigBaseWidget)/,$d' $myFile
#remove unnecesary stuff
sed -i 's;from iptvpin import IPTVPinWidget;;g
  
  ' $myFile
#own settings
sed -i 's;\(^.*ListaGraficzna.*default[ ]*=[ ]*\)True\(.*$\);\1False\2; 
  s;\(^.*showcover.*default[ ]*=[ ]*\)True\(.*$\);\1False\2; 
  s;\(^.*autoCheckForUpdate.*default[ ]*=[ ]*\)True\(.*$\);\1False\2; 
  s;\(^.*wgetpath.*default = \)"";\1"wget"; 
  s;\(^.*f4mdumppath.*default = \)"";\1"f4mdump"; 
  s;\(^.*rtmpdumppath.*default = \)"";\1"rtmpdump"; 
  ' $myFile
############################## Keep only interesting hosts ##############################
[ $isPL ] && echo "Usuwanie nieuwspieranych serwisów..." || echo 'Removing not supported services...'
cd $daemonTMPDir
#step 1 remove all definitevely unwanted
HostsList='anime chomikuj favourites disabled blocked localmedia wolnelekturypl'
for myfile in $HostsList
do
  rm -rf ./hosts/*$myfile*
  rm -rf ./icons/*$myfile*
done
############################## cleaning unused components #######################################################################################
[ $isPL ] && echo "Usuwanie nieużywanych komponentów ze skryptów..." || echo 'Cleaning not used components from scripts...'
cd $daemonTMPDir
pyCount=`find -type f -name '*.py'| wc -l`
iIndex=0
for myfile in `find -type f -name '*.py'`
do
  iIndex=$(( iIndex+1 ))
  echo -ne "\r$iIndex/$pyCount"
  
  sed -i "s;\(from .*\.\)components\(\.iptvplayerinit\);\1dToolsSet\2;g" $myfile #use own fake initscript
  sed -i "s;\(from .*\.\)tools\(\.iptvtools\);\1dToolsSet\2;g" $myfile #use own fake tools script
  toDel='MessageBox';[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='ConfigBaseWidget';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='ConfigHostsMenu';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='IPTVDirectorySelectorWidget';	[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='IPTVSetupMainWidget';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='Screen';			[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='VirtualKeyBoard';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='Label';			[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='ConfigListScreen';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='boundFunction';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='IPTVUpdateWindow';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='ActionMap';			[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='ConfigExtMoviePlayer';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  toDel='IPTVMultipleInputBox';		[[ `grep -c $toDel<$myfile` -gt 1 ]] || sed -i "/import .*$toDel/d" $myfile
  #toDel='self.console_appClosed_conn';	[[ `grep -q $toDel<$myfile` ]] || sed -i "/$toDel/d" $myfile
  #toDel='self.console_stderrAvail_conn';[[ `grep -q $toDel<$myfile` ]] || sed -i "/$toDel/d" $myfile
  
  #adding missing
  toAdd='iptvplayerinit import TranslateTXT as _';         [[ `grep -c "$toAdd"<$myfile` -ge 1 ]] || sed -i "/ihost import IHost/a from Plugins.Extensions.IPTVPlayer.dToolsSet.iptvplayerinit import TranslateTXT as _" $myfile
  
  #probably to del later ;)
  #toDel='eConsoleAppContainer';		[[ `grep -c $toDel<$myfile` -ge 1 ]] && echo $myfile #sed -i "s/\(^.*$toDel\)/#\1/g" $myfile
  sed -i 's/\(raise BaseException\)("\(.*\)")/printDBG("\1(\2)")/g' $myfile
  #sed -i "s/\(getListForItem begin\)\(['\"]+\)/\1 Index=%d, selItem=%s \2 % (Index,str(selItem))/g" $myfile
  #list of imports to build mini python ;)
done
# copy to the location
cp -a $daemonTMPDir/* $daemonDir/
#specific for hosts
[ -e $daemonDir/hosts/XXX.py ] && sed -i "s/\(_url.*hostXXX.py\)/\1qpa/g" $daemonDir/hosts/XXX.py
###################### step 2 create lua list with titles
echo "HostsList={ ">$pluginDir/luaScripts/hostslist.lua
echo "# -*- coding: utf-8 -*-
HostsList=[ ">$daemonDir/dToolsSet/hostslist.py
for myfile in `cd ./hosts;ls ./*.py|grep -v '_init_'|sort -fi`
do
    fileNameRoot=`echo $myfile|sed 's/\.\/\(.*\)\.py/\1/'`
    tytul=`sed -n '/def gettytul..:/ {n;p}' ./hosts/$myfile`
    if `grep -v '[ \t]*#'< ./hosts/$myfile|grep -q 'optionList\.append(getConfigListEntry('`;then
	hasConfig=1
    else
	hasConfig=0
    fi
    if ! `echo $tytul|grep -q 'return'`;then
      tytul=$fileNameRoot
    else
      #tytul=`echo $tytul|cut -d "'" -f2|sed "s;http://;;"|sed "s;/$;;"|sed "s;www\.;;"`
      tytul=`echo $tytul|sed "s/^.*['\"]\(.*\)['\"].*$/\1/"|sed 's/^ *//;s/ *$//'`
    fi
    #echo "	{id=\"$fileNameRoot\", title=\"$tytul\", fileName=\"hosts/$fileNameRoot.py\", logoName=\"icons/$fileNameRoot.png\", type=\"py\"},">>$pluginDir/luaScripts/hostslist.lua
    echo "      {id=\"$fileNameRoot\", title=\"$tytul\", type=\"py\"},">>$pluginDir/luaScripts/hostslist.lua
    echo "	(\"$fileNameRoot\", \"$tytul\"),">>$daemonDir/dToolsSet/hostslist.py
done
echo "	]">>$daemonDir/dToolsSet/hostslist.py
##################### step 3 the same for lua scripts
cd $pluginDir
for myfile in `cd ./luaHosts;ls ./*.lua|sort -fi`
do
    fileNameRoot=`echo $myfile|sed 's/\.\/\(.*\)\.lua/\1/'`
    tytul=`sed -n '/def gettytul..:/ {n;p}' ./luaHosts/$myfile`
    if ! `echo $tytul|grep -q 'return'`;then
      tytul=$fileNameRoot
    else
      tytul=`echo $tytul|cut -d "'" -f2|sed "s;http://;;"|sed "s;/$;;"|sed "s;www\.;;"`
    fi
    echo "	{id=\"$fileNameRoot\", title=\"$tytul\", fileName=\"luaHosts/$fileNameRoot.lua\", logoName=\"luaHosts/$fileNameRoot.png\", type=\"lua\"},">>$pluginDir/luaScripts/hostslist.lua
done
echo "	}">>$pluginDir/luaScripts/hostslist.lua
############################## Reload plugins ##############################
echo "$lastVER" > $daemonDir/version
wget -q http://127.0.0.1/control/reloadplugins -O /dev/null
