-- @j00zek 2017-01-01
-- configuration options and functions

local posix = require "posix"

-- CONFIG definition
confFile="/var/tuxbox/config/IPTV.conf" 
config = configfile.new()
configChanged = 0
conf={
	PythonEnabled = "yes",
	LuaEnabled = "yes",
	UserEnabled = "no",
	PlayerMode = "play",
	StopTV = "yes",
	DelBuffer = "yes",
	}

--Load config
--https://wiki.neutrino-hd.de/wiki/Lua:Neutrino-API:configfile:de
function loadConfig()
	config:loadConfig(confFile)
	for setting, value in pairs(conf) do
		conf[setting] = switchYesNoLang(config:getString(setting, value))
	end
	loadE2config()
	if not fileExists(NaszaSciezka) then
		os.execute("mkdir -p " .. NaszaSciezka)
	end
	if not fileExists(SciezkaCache) then
		os.execute("mkdir -p " .. SciezkaCache)
	end
end

--Save config
function saveConfig()
	if configChanged == 1 then
		local h = hintbox.new{caption="Info", text= Global_SavingSettings, icon="info", has_shadow=true, show_footer=false}
		h:paint()
		for setting in pairs(conf) do
			local value=conf[setting]
			print("j00zek:lua>saveConfig " .. setting .. value)
			value = switchYesNoLang(value)
			config:setString(setting, value)
		end
		config:saveConfig(confFile)
		saveE2config()
		configChanged = 0
		posix.sleep(1)
		h:hide()
	end
end

--Function updates settings of conf[]
function set_setting(mySetting, myValue)
	conf[mySetting]=myValue
	configChanged = 1
end

function CancelKey(a)
	if (configChanged == 1) then
		local res = messagebox.exec{title= Global_SavingQuestionTitle, text= Global_SaveQuestion, buttons={ "no", "yes" }, has_shadow=true }
		if (res == 'yes') then saveConfig() end
	end
	return MENU_RETURN.EXIT
end

-- ###################################################### E2 settings ########################################################
confE2file="/var/tuxbox/config/E2settings.conf"

NaszaSciezka="/hdd/movie/"
SciezkaCache="/hdd/IPTVCache/"

if fileExists("/etc/enigma2/settings") then
    os.execute('mv -f /etc/enigma2/settings ' .. confE2file)
    os.execute('rmdir /etc/enigma2/')
elseif not fileExists(confE2file) then
	os.execute('mkdir -p /var/tuxbox/config/')
	os.execute("echo 'config.misc.firstrun=false' > " .. confE2file)
	if lang == "polski" then
		os.execute("echo 'config.osd.language=pl_PL' >> " .. confE2file)
	end
end

confE2 = configfile.new()
confE2:loadConfig(confE2file)

function loadE2config()
	NaszaSciezka = confE2:getString("config.plugins.iptvplayer.NaszaSciezka",  NaszaSciezka)
	SciezkaCache = confE2:getString("config.plugins.iptvplayer.SciezkaCache",  SciezkaCache)
end

function saveE2config()
	if configChanged == 1 then
		if string.sub(NaszaSciezka,-1) ~= '/' then NaszaSciezka = NaszaSciezka .. '/' end
		if string.sub(SciezkaCache,-1) ~= '/' then SciezkaCache = SciezkaCache .. '/' end
		confE2:setString("config.plugins.iptvplayer.NaszaSciezka", NaszaSciezka)
		confE2:setString("config.plugins.iptvplayer.SciezkaCache", SciezkaCache)
		confE2:saveConfig(confE2file)
	end
end

function setE2setting(mySetting, myValue)
	configChanged = 1
	if mySetting == "NaszaSciezkaID" then NaszaSciezka = myValue
	elseif mySetting == "SciezkaCacheID" then
		if myValue ~= SciezkaCache then
			--os.execute('rm -rf ' .. SciezkaCache .. ' 2>/dev/null')
			if string.sub(myValue,-string.len('IPTVCache')) ~= 'IPTVCache' then 
				local res = messagebox.exec{title= Global_SavingQuestionTitle, text= AddIPTVCacheAtTheEndQuestion, buttons={ "no", "yes" }, has_shadow=true }
			else
				res = 'no'
			end
			if (res == 'yes') then
				SciezkaCache = myValue .. '/IPTVCache'
				os.execute('mkdir -p ' .. SciezkaCache .. ' 2>/dev/null')
			else
				SciezkaCache = myValue
			end
		end
	else configChanged = 0
	end
end
