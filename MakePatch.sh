myDir=`dirname $0`
cd $myDir
diff -Naur ~/iptvplayer-GitLab-master-version/IPTVPlayer/ ./IPTVplayer/ -X ./exclude.pats >./iptvplayer-fork.patch
