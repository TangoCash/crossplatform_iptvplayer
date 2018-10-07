-- IPTV 4 neutrino
-- @j00zek 2016.10.29
-- require "j00zeks.fileExists"
function fileExists(name)
   local f=io.open(name,"r")
   if f~=nil then io.close(f) return true else return false end
end

-- inits
local n = neutrino()
-- init pluginVariable
function getPluginPath()
        return debug.getinfo(2, "S").source:sub(2):match("(.*/)") 
end
pluginPath = getPluginPath()

--get language and translations
lang = n.GetLanguage()

messagesFile = pluginPath .. "messages.english"
if fileExists( pluginPath .. "messages." .. lang) then
	messagesFile = pluginPath .. "messages." .. lang
end
dofile(messagesFile)

dofile(pluginPath .. "luaScripts/toolsBox.lua")
dofile(pluginPath .. "luaScripts/hostslist.lua")
dofile(pluginPath .. "luaScripts/config.lua")

function switchYesNoLang(text)
	--print("j00zek:lua>switchLang from: " .. text)
	local ntext
	if text == "yes" then ntext = Global_yes
	elseif text == Global_yes then ntext = "yes"
	elseif text == "no" then ntext = Global_no
	elseif text == Global_no then ntext = "no"
	else ntext = text
	end
	--print("j00zek:lua>switchLang to: " .. ntext)
	return ntext
end 

--users hosts
local hasUserHost = 0
if fileExists("/var/tuxbox/config/UserHosts.conf") then
        dofile("/var/tuxbox/config/UserHosts.conf")
        hasUserHost = 1
end
--local functions
function CheckSystem()
	disabledPython=""
	if not fileExists('/usr/bin/python') then
		disabledPython= NoPython
	elseif  not fileExists('/usr/share/E2emulator/enigma.py') and not fileExists('/usr/share/E2emulator/enigma.pyo') then
		disabledPython= NoE2Emulator
	elseif  not fileExists('/usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/IPTVdaemon.py') and not fileExists('/usr/share/E2emulator/Plugins/Extensions/IPTVPlayer/IPTVdaemon.pyo') then
		disabledPython= NoIPTVDaemon
	end
	doStopLiveTV()
	return 0
end

function runPythonHost(id)
        mm:hide()
	if disabledPython == "" then
		doStopLiveTV( switchYesNoLang(conf["StopTV"]) )
		n:runScript(pluginPath .. "luaScripts/pythonHost.lua", id, pluginPath, conf["PlayerMode"], switchYesNoLang(conf["StopTV"]), messagesFile, 
				switchYesNoLang(conf["DelBuffer"])
		)
		--os.execute("/usr/ntrino/bin/pzapit -rz")
	else
		messagebox.exec{title= MsgBoxTitleError, text=disabledPython, buttons={ "ok" }, has_shadow=true }
	end
end

function runLuaHost(id)
        mm:hide()
        n:runScript(pluginPath .. id)
end

function CancelKey(id)
        print(id)
        return MENU_RETURN.EXIT
end

function updateIPTVdaemon()
        mm:hide()
        os.execute('echo "UserHostsList={" >' .. "/var/tuxbox/config/UserHosts.conf") 
end

function initUSerHostFile(id)
        if id == "emptyFile" then
                mm:hide()
                os.execute('echo "UserHostsList={" >' .. "/var/tuxbox/config/UserHosts.conf") 
                os.execute('echo "      }" >>' .. "/var/tuxbox/config/UserHosts.conf") 
        else
                print("else")
        end
end
-- MainMenu
function MainMenu()
        mm = menu.new{name= MMTitle, has_shadow=true}
        mm:addKey{directkey = RC["home"], id = "home", action = "CancelKey"}
        mm:addKey{directkey = RC["RC_backspace"], id = "RC_backspace", action = "CancelKey"}
        mm:addItem{type = "back"}
        --mm:addItem{type="separatorline", name=''}
        local d = 0 -- directkey
        -- python hosts
        if conf["PythonEnabled"] == Global_yes then
		if disabledPython == "" then
			mm:addItem{type="separatorline", name= MMPythonHosts}
			for i, v in ipairs(HostsList) do
				d = d + 1
				local dkey = assignDirectKey(d)
				if v.type == "py" then
					mm:addItem{type="forwarder", name=v.title, action="runPythonHost",enabled=true,id=v.id,directkey=dkey}
				end
			end
		else
			d = d + 1;mm:addItem{type="forwarder", name= pythonHostUnavailable, action="runPythonHost",enabled=true,id="",directkey= assignDirectKey(d)}
		end
        end
        -- lua hosts
        if conf["LuaEnabled"] == Global_yes then
                mm:addItem{type="separatorline", name= MMLuaHosts}
                for i, v in ipairs(HostsList) do
                        d = d + 1
                        local dkey = assignDirectKey(d)
                        if v.type == "lua" then
                                mm:addItem{type="forwarder", name=v.title, action="runLuaHost",enabled=true,id=v.fileName,directkey=dkey}
                        end
                end
        end
        -- user hosts
        if conf["UserEnabled"] == Global_yes then
                mm:addItem{type="separatorline", name= MMUserHosts}
                if hasUserHost == 1 then
                        for i, v in ipairs(UserHostsList) do
                                d = d + 1
                                local dkey = assignDirectKey(d)
                                if v.type == "py" then
                                        mm:addItem{type="forwarder", name=v.title, action="runPythonHost",enabled=true,id=v.id,directkey=dkey}
                                else
                                        mm:addItem{type="forwarder", name=v.title, action="runLuaHost",enabled=true,id=v.fileName,directkey=dkey}
                                end
                        end
                        mm:addItem{type="forwarder", name= MMbuildUserHostsFromStardard , action="initUSerHostFile", enabled=true, id="SetupUserHosts"}
                else
                        mm:addItem{type="forwarder", name= MMInitiateEmptyUserHosts , action="initUSerHostFile", enabled=true, id="emptyFile"}
                end
        end
        mm:addItem{type="separatorline", name= MMSettings}
        mm:addItem{type="chooser", id="PythonEnabled", value=conf["PythonEnabled"],name= MMDisplayPythonHosts,options={Global_yes,Global_no}, action="set_setting"}
        mm:addItem{type="chooser", id="LuaEnabled",    value=conf["LuaEnabled"],   name= MMDisplayLuaHosts,   options={Global_yes, Global_no}, action="set_setting"}
        mm:addItem{type="chooser", id="UserEnabled",   value=conf["UserEnabled"],  name= MMDisplayUserHosts  ,options={Global_yes, Global_no}, action="set_setting"}
        mm:addItem{type="chooser", id="StopTV",        value=conf["StopTV"],       name= MMStopTV,            options={Global_yes, Global_no}, action="set_setting"}
        mm:addItem{type="chooser", id="DelBuffer",     value=conf["DelBuffer"],    name= MMDelBuffer,         options={Global_yes, Global_no}, action="set_setting"}
        mm:addItem{type="chooser", id="PlayerMode",    value=conf["PlayerMode"],   name= MMPlayerMode,        options={MMPlayerModeP, MMPlayerModeB, MMPlayerModeR}, action="set_setting"}

	if fileExists(NaszaSciezka) then
		mm:addItem{type="filebrowser", id="NaszaSciezkaID", value= NaszaSciezka, name= MMNaszaSciezka, dir_mode= 1, action="setE2setting"}
	else
		mm:addItem{type="filebrowser", id="NaszaSciezkaID", value= "/hdd/movie/", name= MMNaszaSciezka, dir_mode= 1, action="setE2setting"}
	end
	if fileExists(SciezkaCache) then
		mm:addItem{type="filebrowser", id="SciezkaCacheID", value= SciezkaCache, name= MMSciezkaCache, dir_mode= 1, action="setE2setting"}
	else
		mm:addItem{type="filebrowser", id="SciezkaCacheID", value= "/hdd/IPTVCache/", name= MMSciezkaCache, dir_mode= 1, action="setE2setting"}
	end
	
        mm:addItem{type="separatorline"}
        mm:addItem{type="forwarder", name= Global_save, action="saveConfig"}
        mm:exec()
end 

function _main_()
	if CheckSystem() == 0 then
		loadConfig()
		MainMenu()
	end
end 

_main_()
