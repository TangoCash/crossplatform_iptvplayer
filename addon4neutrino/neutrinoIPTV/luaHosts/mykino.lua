function getPluginPath()
        return debug.getinfo(2, "S").source:sub(2):match("(.*/)") 
end
pluginPath = getPluginPath()
if nt == nil then nt =  neutrino() end
	dofile(pluginPath .. "luaLocale/mykino." .. nt.GetLanguage())
nt = nil

-- Mykino Kategorien anzeigen
function show_categories()
	menue_items = {}
	menue_items =
	{
		{["name"] = "Aktuelle Kinofilme", ["urlname"] = "aktuelle-kinofilme"},
		{["name"] = "Abenteuer", ["urlname"] = "abenteuer"},
		{["name"] = "Action", ["urlname"] = "action"},
		{["name"] = "Biographie", ["urlname"] = "biographie"},
		{["name"] = "Drama", ["urlname"] = "drama"},
		{["name"] = "Familie", ["urlname"] = "familie"},
		{["name"] = "Fantasy", ["urlname"] = "fantasy"},
		{["name"] = "Horror", ["urlname"] = "horror"},
		{["name"] = "Komödie", ["urlname"] = "komoedie"},
		{["name"] = "Krimi", ["urlname"] = "krimi"},
		{["name"] = "Romantik", ["urlname"] = "romantik"},
		{["name"] = "Sci-fi", ["urlname"] = "sci-fi"},
		{["name"] = "Thriller", ["urlname"] = "thriller"},
		{["name"] = "Trickfilm", ["urlname"] = "trickfilm"},
		{["name"] = "Western", ["urlname"] = "western"},
		{["name"] = "Krieg", ["urlname"] = "krieg"},
		{["name"] = "Sport", ["urlname"] = "sport"},
	};
	
	selected_categorie_id = 0;
	m_categories = menu.new{name="Mykino.to Kategorien"};
	for index, menue_item in pairs(menue_items) do
		m_categories:addItem{type="forwarder", action="set_categorie", id=index, name=menue_item.name};
	end
	m_categories:exec()
	if tonumber(selected_categorie_id) ~= 0 then
		get_movies(menue_items[selected_categorie_id].name,menue_items[selected_categorie_id].urlname,"1");
	end
	
end

-- Setzen der ausgewählten Kategorie
function set_categorie(_id)
	selected_categorie_id = tonumber(_id);
	return MENU_RETURN["EXIT_ALL"];
end

-- Filme parsen
function get_movies(_name,_urlname,_page)
	local m_url = "";
	
	if _urlname == "aktuelle-kinofilme" then
		m_url = "http://mykino.to/filme/aktuelle-kinofilme/page/" .. _page;
	else
		m_url = "http://mykino.to/" .. _urlname .. "/page/" .. _page ;
		debugg(m_url);
	end
	
	local command = "wget '" .. m_url .. "' -O- -U 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0'"; 
	local movies_data = exec(command);
	
	if (movies_data:match("Nicht gefunden!")) then
		get_movies(_urlname,"1")
	else
		local movies = {};
		local i = 1;
		for movie in string.gmatch(movies_data, "<div class=\"news2 float\">(.-)</div>") do
			movies[i] =
				{
					url = movie:match("<a href=\"(.-)\">");
					title = movie:match("<div class=\"boxgridtext\">.(.*).");
				}
				i = i + 1;
		end
		show_movie_menue(_name,_urlname,_page,movies);	
	end
	
end 

-- Menü mit Filmen erstellen
function show_movie_menue(_name,_urlname,_page,movies)
	local menu_title = _name .. " (Seite " .. _page .. ")";
	selected_movie_id = 0;
	
	m_movies = menu.new{name=menu_title};
	
	m_movies:addItem{type="forwarder", name="Kategorie Auswahl", action="set_movie", id="-3", icon="gruen", directkey=RC["green"]};
	m_movies:addItem{type="forwarder", name="Nächste Seite", action="set_movie", id="-2", icon="blau", directkey=RC["blue"]};
	m_movies:addKey{directkey=RC["right"], action="set_movie", id="-2"}
	if tonumber(_page) > 1 then
		m_movies:addItem{type="forwarder", name="Vorherige Seite", action="set_movie", id="-1", icon="gelb", directkey=RC["yellow"]};
		m_movies:addKey{directkey=RC["left"], action="set_movie", id="-1"}
	end
	m_movies:addItem{type="separatorline"};
	m_movies:addItem{type="separator"};
	for index, movie_detail in pairs(movies) do
		m_movies:addItem{type="forwarder", action="set_movie", id=index, name=movie_detail.title};
	end
	m_movies:exec()	
	-- Zurück zum Kategorien-Menü
	if selected_movie_id == -3 then
		show_categories();
	-- Exit
	elseif selected_movie_id == 0 then
	-- Vorherige Seite laden
	elseif selected_movie_id == -1 then
		newpage = _page - 1;
		get_movies(_name,_urlname,newpage);
	-- Nächste Seite laden
	elseif selected_movie_id == -2 then
		newpage = _page + 1;
		get_movies(_name,_urlname,newpage);
	-- Filminfo anzeigen
	else
		get_mirrors(movies[selected_movie_id].url,movies[selected_movie_id].title);
	end
end

-- Setzen des ausgewählten Films
function set_movie(_id)
	selected_movie_id = tonumber(_id);
	return MENU_RETURN["EXIT_ALL"];
end

-- Streamcloud Mirrors auslesen
function get_mirrors(_url,_name);
	command = "wget '" .. _url .. "' -O- -U 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0'"; 
	mirrors_data = exec(command);
	mirrors = {};
		
	for mirror in string.gmatch(mirrors_data, "-href=\"(.-)\">") do
		if (mirror:match("http://streamcloud.eu")) then
			local i = 1;
			for mirror_url in string.gmatch(mirror, '([^,]+)') do
				mirrors[i] = mirror_url;
				i = i + 1;
			end
		end
	end
	show_mirrors_menue(mirrors,_url,_name);
end

-- Menü mit Mirrors anzeigen
function show_mirrors_menue(_mirrors,_url,_name);
	selected_mirrors_id = 0;
	m_mirrors = menu.new{name="Streamcloud Mirrors"};
	for index, lv_mirror_url in pairs(_mirrors) do
		lv_mirror = "Mirror " .. index;
		m_mirrors:addItem{type="forwarder", action="set_mirror", id=index, name=lv_mirror};
	end
	m_mirrors:exec()
	if tonumber(selected_mirrors_id) ~= 0 then
		get_stream(_mirrors[selected_mirrors_id],_name,_url);
	end
end

-- Setzen des ausgewählten Mirrors
function set_mirror(_id)
	selected_mirrors_id = tonumber(_id);
	return MENU_RETURN["EXIT_ALL"];
end

-- Streamdaten parsen und starten
function get_stream(_hoster_url,_name,_url)
	gv_postdata = get_postdata(_hoster_url);
	gv_poststring = get_poststring(gv_postdata);
	if gv_poststring == "not found" then
		get_mirrors(_url,_name);
	else
		gv_pagedata = get_pagedata(_hoster_url,gv_poststring);
		gv_streamlink = get_streamurl(gv_pagedata)
		start_stream(gv_streamlink,_name);	
	end
end

-- Postdaten ermitteln
function get_postdata(_fileurl)
	local command = "wget '" .. _fileurl .. "' -O- -U 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0'";
	local postdata = exec(command);
	local h = hintbox.new{ title="Streamdaten werden geladen", text="Einen Moment Gedult bitte (Plugin by Ezak for coolstream.to)", icon="info"}
	h:paint()
	os.execute("sleep 20");
	h:hide{no_restore="true"}
	return postdata;
end

-- Poststring erstellen
function get_poststring(_pagedata)
	postdata = _pagedata:match("<form action=\"\" method=\"POST\" class=\"proform\">(.-)</form>");
	if postdata == nil then
		local d = hintbox.new{ title="Hinweis", text="Datei nicht gefunden", icon="info"};
		d:exec();
		poststring = "not found";
	else
		op = postdata:match("<input type=\"hidden\" name=\"op\" value=\"(.-)\">");
		usr_login = postdata:match("<input type=\"hidden\" name=\"usr_login\" value=\"(.-)\">");
		id =  postdata:match("<input type=\"hidden\" name=\"id\" value=\"(.-)\">");
		fname = postdata:match("<input type=\"hidden\" name=\"fname\" value=\"(.-)\">");
		referer = postdata:match("<input type=\"hidden\" name=\"referer\" value=\"(.-)\">"); 
		hash = postdata:match("<input type=\"hidden\" name=\"hash\" value=\"(.-)\">"); 
		imhuman = postdata:match("<input type=\"submit\" name=\"imhuman\" id=\"btn_download\" class=\"button gray\" value=\"(.-)\">");
		
		imhuman = string.gsub(imhuman," ","%%20");
		
		poststring = "op=" .. op .. "&usr_login=" .. usr_login .. "&id=" .. id .. "&fname=" .. fname .. "&referer=" .. referer .. "&hash=" .. hash .. "&imhuman=" .. imhuman;
	end
	return poststring;
end

-- Pagedaten ermitteln
function get_pagedata(_fileurl,_poststring)	
	local command = "wget '" .. _fileurl .. "' -O- -U 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0' -q  " .. "--post-data=\"" .. _poststring .. "\"";
	local pagedata = exec(command);
	return pagedata;
end

-- Stream url parsen
function get_streamurl(_pagedata)
	local streamurl = _pagedata:match("file: \"(.-)\",");
	return streamurl;
end

-- Starten des Streams
function start_stream(_streamlink,_name)
	n:PlayFile(_name, _streamlink);
end

function debugg(_string)
	local d = hintbox.new{ title="Debug", text=_string, icon="info"};
	d:exec();
end

-- Ausführen eines Kommando auf der Console und Ausgabe zurückgeben
function exec(_command)
	local handle = io.popen(_command)
	local result = handle:read("*a")
	handle:close()
	return result;
end

-- Log schreiben
function write_log(_line)
	local f,err = io.open("mykino.log","a")
	if not f then return print(err) end
	f:write(_line)
	f:close()
end

n = neutrino();
show_categories();