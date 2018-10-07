#!/bin/sh
myDir=/usr/share/E2emulator/Plugins/Extensions/IPTVPlayer
if [ -e $myDir/cmdlineIPTV.py ];then
 python $myDir/cmdlineIPTV.py
else
 python $myDir/cmdlineIPTV.pyo
fi
