-- @j00zek 2016-10-29

local posix = require('posix')

function doStopLiveTV(myAction)
	if myAction == nil then
		return
	elseif myAction == 'yes' then
		os.execute("/usr/ntrino/bin/pzapit -p") --stop liveTV to speedup
	end
end
	
function fileExists(fname) 
	--returns true/false
	local ff=io.open(fname, "r")
	if ff==nil then
		return false
	else
		ff.close()
		return true
	end
end

function assignDirectKey(d)
	local  _dkey = ""
	if d == 1 then _dkey = RC["red"]
	elseif d == 2 then _dkey = RC["green"]
	elseif d == 3 then _dkey = RC["yellow"]
	elseif d == 4 then _dkey = RC["blue"]
	elseif d < 14 then _dkey = RC[""..d - 4 ..""]
	elseif d == 14 then _dkey = RC["0"]
	else
		-- rest
		_dkey = ""
	end
	return _dkey
end

function printDBG( myText )
	local myDBGfile = io.open("/hdd/neutrinoIPTV.log", "a")
	if myDBGfile == nil then
		local fakeError = 1
	else
		myDBGfile:write(myText .. "\n")
		myDBGfile:close()
	end
end
