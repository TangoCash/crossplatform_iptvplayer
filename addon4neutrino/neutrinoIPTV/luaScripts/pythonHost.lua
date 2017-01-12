-- IPTV 4 neutrino
-- manages single python HOST
-- @j00zek 2016.10.28
local posix = require "posix" --sh4 does not need this, cool does 
pluginPath = arg[2]
PlayerMode = arg[3]
TVmode =  arg[4]
dofile(arg[5]) --messages
DelBuffer = arg[6]
dofile(pluginPath .. "luaScripts/toolsBox.lua")
print = printDBG
-- inits
if fileExists('/usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/IPTVdaemon.py') then
	IPTVdaemon='python /usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/IPTVdaemon.py'
else
	IPTVdaemon='python /usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/IPTVdaemon.pyo'
end	
IPTVdaemonCMD='/tmp/.IPTVdaemon/cmd'
IPTVdaemonRET='/tmp/.IPTVdaemon/ret'
IPTVdaemonPID='/tmp/.IPTVdaemon/pid'
IPTVdaemonLOG='/tmp/.IPTVdaemon/log'
IPTVdaemonERR='/tmp/.IPTVdaemon/errors'
currPID=nil
currHOST= string.gsub(arg[1] , "%s", "")
currNAME="unknown"
currLEVEL=0
doExit=0
LogPrefix="[neutrinoIPTV]>pythonHost:"
SearchPattern=''
--managing daemon
function isDeamonWorking()
        if currPID == nil then return false end
    return (posix.stat('/proc/' .. currPID, "type") == 'directory')
end

function startDaemon()
        local hb = hintbox.new{ title=HintBoxTitleInfo, text= startDaemonHboxText .. currHOST, icon="info", has_shadow=true, show_footer=false}
        hb:paint()
        posix.sleep(1)
        os.execute('killall python;' .. IPTVdaemon .. ' restart ' .. currHOST) 
        posix.sleep(1)
        fp = io.open(IPTVdaemonPID, "r")
        if fp == nil then
                doExit=1
        else
                currPID = string.gsub(fp:read(), "%s", "")
                if currPID == nil then isError=1 end
                fp:close()
        end
        hb:hide()
        if doExit == 1 or isDeamonWorking() == false then
                messagebox.exec{title= MsgBoxTitleError, text= MsgBoxTextErrorinitiatingIPTVdaemon, buttons={ "ok" }, has_shadow=true }
                print(LogPrefix .. "startDaemon " ..  MsgBoxTextErrorinitiatingIPTVdaemon .. " "  .. currHOST)
                doExit=1
        else
                local hb = hintbox.new{ title="Info", text= MsgBoxTextIPTVdaemoninitiated .. currHOST .. " (" .. currPID .. ")", icon="info", has_shadow=true, show_footer=false}
                hb:paint()
                posix.sleep(1)
                hb:hide()
                print(LogPrefix .. "startDaemon " .. MsgBoxTextIPTVdaemoninitiated .. currHOST .. " (" .. currPID .. ")")
        end
        return
end

function stopDaemon()
        local hb = hintbox.new{ title= HintBoxTitleInfo, text= stopDaemonHboxText, icon="info", has_shadow=true, show_footer=false}
        hb:paint()
        os.execute(IPTVdaemon .. ' stop') 
        hb:hide()
        return
end

function doCMD( myCommand )
        if myCommand == nil or myCommand == '' then
                        return ''
        elseif isDeamonWorking() == false then
            messagebox.exec{title= MsgBoxTitleError, text= MsgBoxTextDaemonError, buttons={ "ok" }, has_shadow=true }
            CancelKey()
        end
        local hb = hintbox.new{ title= HintBoxTitleInfo, text= HboxTextDownloadingData, icon="info", has_shadow=true, show_footer=false}
        hb:paint()
                -- sending command to daemon
        local retVal= ''
        if fileExists(IPTVdaemonRET) then
                os.execute('rm -f ' .. IPTVdaemonRET) 
        end
        fp = io.open(IPTVdaemonCMD, "w")
        fp:write(myCommand)
        fp:close()
                -- waiting for a response, max 20 seconds
        local WaitTime = 30
        repeat
                posix.sleep(1)
                WaitTime = WaitTime - 1
                print (LogPrefix .. "doCMD Waiting " .. WaitTime)
        until WaitTime <= 1 or fileExists(IPTVdaemonRET)
        if fileExists(IPTVdaemonRET) then
                fp = io.open(IPTVdaemonRET, "r")
                retVal = fp:read()
                fp:close()
                print(LogPrefix .. "doCMD returned:" .. retVal)
	else
            retVal="Timeout"
        end
        hb:hide()
        return retVal
end
--local functions
function CancelKey(id)
        print(LogPrefix .. "CancelKey(" .. id .. ")")
        doExit = 1
        return MENU_RETURN.EXIT
end

function getList(id)
        print(LogPrefix .. "getList(" .. id .. ")")
                if id == "PreviousList" or id == "RefreshList" or id == "InitList" then
                        currList = doCMD(id)
                        if string.find( currList, "ItemsList={" ) then
                                dofile(IPTVdaemonRET)--; currLEVEL = 1
                                if id == "PreviousList" then
                                        currLEVEL = currLEVEL - 1
                                elseif id == "InitList" then
                                        currLEVEL = 1
                                end
                        end
                else
                        currList = doCMD("ListForItem=" .. id)
                        if string.find( currList, "ItemsList={" ) then
                                dofile(IPTVdaemonRET)
                                currLEVEL = currLEVEL + 1
                        end
                end
        return MENU_RETURN.EXIT
end

function doSearch(k, v)
        print(LogPrefix .. "doSearch, pattern='" .. v .. "'")
        --messagebox.exec{title= MsgBoxTitleInfo, text="Search pattern='" .. v .. "'", buttons={ "ok" }, has_shadow=true }
        SearchPattern = v
        currList = doCMD("Search=" .. SearchPattern)
        if string.find( currList, "ItemsList={" ) then
                dofile(IPTVdaemonRET)
                currLEVEL = currLEVEL + 1
        end
        return MENU_RETURN.EXIT
end

function doSomething(id)
        messagebox.exec{title= MsgBoxTitleInfo, text="Not implemented :(", buttons={ "ok" }, has_shadow=true }
end

function setPlayerMode(mySetting, myValue)
        print(LogPrefix .. "setPlayerMode, PlayerMode='" .. myValue .. "'")
	PlayerMode=myValue
end

function playMovie(idANDname)
        print(LogPrefix .. "playMovie, idANDname='" .. idANDname .. "'")
	movieID, MovieName = idANDname:match("([^,]+)~=~([^,]+)")
	
        function doPlayUrl(url)
		if SML == nil then print(LogPrefix .. "strange, SML nil?!?"); else SML:hide(); end
		
		if PlayerMode == MMPlayerModeR then	   --recorder mode
			local retCMD = doCMD("DownloadURL=" .. url)
			posix.sleep(1)
			if fileExists(retCMD) then
				messagebox.exec{title= MsgBoxTitleInfo, text= MsgBoxTextRecordingof .. retCMD .. MsgBoxTextRecordingStarted, buttons={ "ok" }, has_shadow=true }
				print(LogPrefix .. "doPlayUrl " .. MsgBoxTextRecordingof .. retCMD .. MsgBoxTextRecordingStarted)
			end
-- ### BUFFERING MODE ###
		elseif PlayerMode == MMPlayerModeB then
			local retCMD = doCMD("DownloadURL=" .. url)
			print(LogPrefix .. "doPlayUrl " .. MsgBoxTextBuffering .. " "  .. retCMD)
			local hb = hintbox.new{ title= HintBoxTitleInfo, text= MsgBoxTextBuffering, icon="info", has_shadow=true, show_footer=false}
			hb:paint()
			posix.sleep(10)
			hb:hide()
			if fileExists(retCMD) then
				video = video.new();
				video.setSinglePlay(video);
				video.PlayFile(video, MovieName, retCMD)
				doStopLiveTV(TVmode)
			end
			-- tutaj zamykanie wgeta i czyszczenie
			local res = ''
			if DelBuffer == 'no' then
				res = messagebox.exec{title= MsgBoxTitleQuestion, text= MsgBoxTextDeleteBufferedFile, buttons={ "no", "yes" }, has_shadow=true }
			else
				res = 'yes'
			end
				
			if (res == 'yes') then
				os.execute("kill `ps -ef|grep '" .. retCMD .. "'|pgrep wget`;rm -f '" .. retCMD .. "'*") 
			end
		else                                        --player mode
			print(LogPrefix .. "doPlayUrl PlayFile(" .. MovieName .. ", " ..url .. ")")
			video = video.new();
			video.setSinglePlay(video);
			video.PlayFile(video, MovieName, url)
			doStopLiveTV(TVmode)
		end
		return MENU_RETURN.EXIT
        end
        function resolveUrl(id)
		resolvedVideoUrl = doCMD("ResolveURL=" .. id)
		print(LogPrefix .. "doPlayUrl resolveUrl(" .. id .. ") = '" .. resolvedVideoUrl .. "'")
		if resolvedVideoUrl =="Timeout" then
			messagebox.exec{title= MsgBoxTitleError, text= MsgBoxTextErrorTimeout, buttons={ "ok" }, has_shadow=true }
		elseif resolvedVideoUrl =="ERROR" then
			messagebox.exec{title= MsgBoxTitleError, text= MsgBoxTextErrorNotResolved, buttons={ "ok" }, has_shadow=true }
                elseif resolvedVideoUrl =="WRONGINDEX" then
                        messagebox.exec{title= MsgBoxTitleError, text= MsgBoxTextErrorNotResolved, buttons={ "ok" }, has_shadow=true }
                elseif resolvedVideoUrl =="NOVALIDURLS" then
                        messagebox.exec{title= MsgBoxTitleInfo, text= MsgBoxTextNoValidURLs, buttons={ "ok" }, has_shadow=true }
		else
			doPlayUrl(resolvedVideoUrl)
		end
        end
        function SelectMovieLink()
                SML = menu.new{name= MovieName ..":", has_shadow=true}
                local d = 5
        for i, v in ipairs(UrlsList) do
                        if v.urlNeedsResolve == 0 then
                                SML:addItem{type="forwarder", name=v.name, action="doPlayUrl",enabled=true, id=v.url, directkey=assignDirectKey(d), hint=v.descr}
                        else
                                SML:addItem{type="forwarder", name=v.name, action="resolveUrl",enabled=true, id=v.id, directkey=assignDirectKey(d), hint=v.descr}
                        end
                        d = d + 1
        end
		SML:addItem{type="separatorline", name='Mode'}
		SML:addItem{type="chooser", id="PlayerMode", value=PlayerMode, name= MMPlayerMode,options={MMPlayerModeP, MMPlayerModeB, MMPlayerModeR}, action="setPlayerMode", directkey=assignDirectKey(4)}
                SML:exec()
        end
        hlm:hide()
	
        LinksForVideo = doCMD("getVideoLinks=" .. movieID)
        if string.find( LinksForVideo, "UrlsList={" ) then
                dofile(IPTVdaemonRET)
                local ItemsCount = 0
                for k,v in pairs(UrlsList) do
                        ItemsCount = ItemsCount + 1
                end
                if ItemsCount >= 1 then
			SelectMovieLink()
		end
        end
end

--##### host settings in IPTVdamen #####
function set_E2config(id)
	print ("set_E2config" .. id)
end
	
function saveE2config(id)
	print ("saveE2config" .. id)
end
	
-- HostLists
function HostListMenu()
        hlm = menu.new{name= currNAME .. " (".. currLEVEL .. ")", has_shadow=true}
        hlm:addKey{directkey = RC["home"], id = "home", action = "CancelKey"}
        hlm:addKey{directkey = RC["RC_backspace"], id = "RC_backspace", action = "CancelKey"}
        --hlm:addItem{type = "back", action = "CancelKey"}
        --hlm:addItem{type="separatorline", name=''}
                if currLEVEL > 1 then
                        hlm:addItem{type="forwarder", name= hlmPrevious, action="getList",enabled=true, id="PreviousList", directkey=assignDirectKey(1), hint= hlmPreviousHint}
        end
                hlm:addItem{type="forwarder", name= hlmReloadList, action="getList",enabled=true, id="RefreshList", directkey=assignDirectKey(2), hint= hlmReloadListHint}
        hlm:addItem{type="forwarder", name= hlmInitList, action="getList",enabled=true, id="InitList", directkey=assignDirectKey(3), hint= hlmInitListHint}
        hlm:addItem{type="separatorline", name= hlmCategories}
	local d = 5 -- directkey, starts with 1
        for i, v in ipairs(ItemsList) do
                        local dkey = assignDirectKey(d)
                        if v.type == "VIDEO" then
                                hlm:addItem{type="forwarder", name=v.name, action="playMovie",enabled=true, id=v.id .. "~=~" .. v.name, directkey=dkey, hint=v.descr}
                        elseif v.type == "CATEGORY" then
                                hlm:addItem{type="forwarder", name=v.name, action="getList",enabled=true, id=v.id, directkey=dkey, hint=v.descr}
                        elseif v.type == "SEARCH" then
                                hlm:addItem{type="keyboardinput", name=v.name, action="doSearch",enabled=true, id=v.id, directkey=dkey, value=SearchPattern}
                        --else
                        --        hlm:addItem{type="forwarder", name=v.name, action="doSomething",enabled=true, id=v.id, directkey=dkey, hint=v.descr}
                        end
                        d = d + 1
        end
        if HostConfig == nil then
		print 'host has no config'
	elseif currLEVEL == 1 then
		hlm:addItem{type="separatorline", name= Settings}
		for i, v in ipairs(HostConfig) do
			if v.type == 'ConfigSelection' then
				hlm:addItem{type="chooser", id=v.id, action="set_E2config", name=v.name, value=v.valName, options=v.chNames}
			elseif v.type == 'ConfigYesNo' then
				if v.value == 'yes' then v.value = Global_yes
				elseif v.value == 'no' then v.value = Global_no
				end
				hlm:addItem{type="chooser", id=v.id, action="set_E2config", name= v.name, value= v.value, options={Global_yes, Global_no}}
			elseif v.type == 'ConfigText' then
				hlm:addItem{type="stringinput", id=v.id, action="set_E2config", name= v.name, value=v.value,  sms=1}
			end
		end
		hlm:addItem{type="forwarder", name= Global_save, action="saveE2config", enabled="false"}
	end
	hlm:exec()
end 

function _main_()
        local retVal
        startDaemon()
        if doExit == 1 then return end
        currNAME = doCMD("Title")
        currList = doCMD("InitList")
        if string.find( currList, "ItemsList={" ) then dofile(IPTVdaemonRET); currLEVEL = 1; end
        if doExit == 1 then return end
        repeat
            HostListMenu()
        until doExit == 1
end 

_main_()
stopDaemon()
collectgarbage()
