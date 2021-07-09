import os,sys,cherrypy,json,base64,zipfile,importlib,shutil,subprocess
try:
	from cloudfe import cs, cfe_dbgen
except:
	import cs
	import cfe_dbgen

class CloudFE(object):
	required_dirs = ['databases','loaders','data','tmp']
	supported_svcs = ['gdrive','onedrive']
	cfe_database = {}
	loaderdb = {}

	def __init__(self):
		self.app_root = os.getcwd()
		for d in self.required_dirs:
			if(not os.path.exists(d)):
				os.makedirs(d)
				if(d == 'loaders'):
					f = open(os.path.join('loaders','__init__.py'),'wb')
					f.close()
					
				if(d == 'databases'):
					self.reload_db()
		#Log into all your cloud services.
		self.cloud_services = {}
		for svc in self.supported_svcs:
			asvc = cs.CloudService(svc)
			if(asvc.svc_active == True):
				if(not svc in self.cloud_services.keys()):
					self.cloud_services[svc] = asvc
		
		if(not os.path.exists(os.path.join("databases","Loaders.json"))):
			self.reload_db()
		
		
		self.get_loader_db()
		self.reload_db(True)
		self.d_after = True
		self.local_entry = False
		self.selected_system = None		
		self.cache_system_list = None

		
	def reload_db(self,first_run=False):
		self.cfe_database = {}
		if(first_run == False):
			cfe_dbgen.run()
			self.get_loader_db()
		#Load Any local databases.
		for root,dirs,files in os.walk("databases"):
			for f in files:
				if(f.endswith(".json") and f != "Loaders.json"):
					fb,fe = os.path.splitext(f)
					if(not fb in self.cfe_database.keys()):
						self.cfe_database[fb] = {}
					json_data=open(os.path.join(root,f))
					jd = json.load(json_data)
					json_data.close()
					for j in jd.keys():
						req_emu=""
						if(not 'loader' in jd[j].keys() and os.name in self.loaderdb[jd[j]['system']]):
							req_emu = self.loaderdb[jd[j]['system']][os.name].keys()[0]
						if('loader' in jd[j].keys()):
							req_emu = jd[j]['loader']
						
						
						if(req_emu==""):
							req_emu = self.loaderdb[jd[j]['system']][os.name].keys()[0]
							
						if(os.name in self.loaderdb[fb] and req_emu in self.loaderdb[fb][os.name]):
							jd[j]['has_loader'] = True
							jd[j]['loader'] = req_emu
						else:
							jd[j]['loader'] = ""
							jd[j]['has_loader'] = False
						self.cfe_database[fb][j] = jd[j]		
		
	def get_loader_db(self):
		#Loader Tree: System->Native->Emulator_Name
		self.loaderdb = {}
		
		json_data=open(os.path.join("databases","Loaders.json"))
		self.loaderdb = json.load(json_data)["Loader"]
		json_data.close()
	def sizeof_fmt(self,num, suffix='B'):
		for unit in [' ',' K',' M',' G',' T',' P',' E',' Z']:
			if abs(num) < 1024.0:
				return "%3.1f%s%s" % (num, unit, suffix)
			num /= 1024.0
		return "%.1f%s%s" % (num, ' Y', suffix)
		
		
	def gen_entries(self,selected_system):
		response = ""
		elist = []
		#Sort Titles
		for ek in self.cfe_database[selected_system].keys():
			elist.append((self.cfe_database[selected_system][ek]['name'],ek))
		elist = sorted(elist)
		for ek in elist:
			ek = ek[1]
			entry = self.cfe_database[selected_system][ek]
			#Skip if it's an empty entry.
			if(not "Data" in entry.keys()):
				continue
			if(entry['has_loader']):
				run_req = base64.b64encode("%s|%s" % (selected_system,ek))
			else:
				run_req = ""
			video_entry = ""
			if('Artwork' in entry.keys()):
				for vk in entry['Artwork']:
					if('video' in vk['type']):
						video_entry = vk['url']
						
			if('Icon' in entry.keys()):
				entry_icon = entry['Icon'][0]['url']
			else:
				entry_icon = 'http://i.imgur.com/F2JiYsI.jpg'
				
			response += "<tr>"
			response += "<td><a href='run?req=%s'><video id='preview_video' loop='loop' onclick=\"this.pause()\"  onmouseover=\"this.play()\" onmouseout=\"this.pause();this.src='';this.src='%s'\" poster='%s' width='360' height='240' source src='%s'/></video></a></td>" % (run_req,video_entry,entry_icon,video_entry)
			#Metadata for now.
			
			#response +="<td>Entry_ID: %s</br>" % ek
			response+="<td><font color='white'>"
			if(entry['year'] == ""):
				response+="%s<br/>" % entry['name']
			else:
				response+="%s (%s)<br/>" % (entry['name'],entry['year'])
			response+= "Publisher: %s<br/>" % entry['publisher']
			response+= "Developer: %s<br/>" % entry['developer']
			response+= "Region: %s<br/>" % entry['region']
			response+= "Genre: %s<br/>" % entry['genre']
			response+= "Players: %s<br/>" % entry['players']
			if('data_sz' in entry.keys()):
				response+= "Size: %s<br/>" % self.sizeof_fmt(int(entry['data_sz']))
				self.cfe_database[selected_system][ek]['total_sz'] = self.sizeof_fmt(int(entry['data_sz']))
			else:
				self.cfe_database[selected_system][ek]['total_sz'] = "NO DATA"
				response+= "Size: NO DATA<br/>"
			if('description' in entry.keys()):
				response+= "Description: <p><i>%s</i></p>" % entry['description']
			else:
				self.cfe_database[selected_system][ek]['description'] = "N/A"
				response+= "Description: N/A<br/>"
			
			self.cfe_database[selected_system][ek]['preview_video'] = video_entry
			self.cfe_database[selected_system][ek]['icon_entry'] = entry_icon
			
			'''DEBUG = Show ALL 
			for ei in entry.keys():
				response +="%s: %s<br/>" % (ei,entry[ei])	
			'''
			
			response +="</font></td>"
			response += "</tr>"
		
		return response
		

	@cherrypy.expose
	def index(self,selected_system=None):
	
		
		'''
		response = "<html><head>"
		response+="<style type=\"text/css\">"
		response+="body{text-align: center;}.cfeclass{width: 1000px;height: 480px;position: absolute;margin-left: auto;margin-right: auto;}</style>"
		response+="<script>"
		'''
		if(selected_system == None):
			selected_system = self.cfe_database.keys()[0]
			self.selected_system = selected_system
		if(self.selected_system!=selected_system or self.cache_system_list==""):
			self.cache_system_list = self.gen_entries(selected_system)
			self.selected_system = selected_system			
			
		#This is where the entry keys and json go.
		db_data="<script>"
		db_data+="var e_db = %s;" % json.dumps(self.cfe_database[selected_system])
		
		
		sorted_keys = sorted(self.cfe_database[self.selected_system].keys(), key=lambda y: (self.cfe_database[self.selected_system][y]['name']))
		db_data+="var entry_keys="
		for i in range(0,len(sorted_keys)):
			sorted_keys[i] = str(sorted_keys[i])
		db_data+="%s;" % str(sorted_keys)
		
		
		db_data+="</script>"
		'''
		response+="<body id='app'>"
		response +="<form action=\"index\" method=\"get\">"
		response +="<select name='selected_system' onchange=\"this.form.submit()\">"
		response +="<option value=''>Select System...</option>"
		
		for dr in self.cfe_database.keys():
			response +="<option value='%s'>%s</option>" % (dr,dr)
		response +="</select>"
		response +="</form>"
		
		response+="<div class=\"cfeclass ui-coverflow-wrapper ui-clearfix\">"
		response+="<div id=\"coverflow\">"
		'''
		#This is where the logic for the coverflow stuff goes.
		'''
		for i in range(0,len(sorted_keys)):
			ce = self.cfe_database[self.selected_system][sorted_keys[i]]
			if(not 'icon_entry' in ce):
				ce['icon_entry']='http://i.imgur.com/F2JiYsI.jpg'
			
			#response+="<video id='preview_%d' loop='loop' poster='%s' width='640' height='480' src=''></video>" % (i,ce['icon_entry'])
		'''
		#response+="</div></div>"
		'''
		#This is where the entry metadata displays go...
		response+="<h3 id=\"name\"></h3>"
		response+="<div id=\"publisher\"></div>"
		response+="<div id=\"developer\"></div>"
		response+="<div id=\"region\"></div>"
		response+="<div id=\"genre\"></div>"
		response+="<div id=\"rating\"></div>"
		response+="<div id=\"players\"></div>"
		response+="<div id=\"total_sz\"></div>"
		response+="<div id=\"description\"></div>"
		'''
		#Our form to pick the entry to run.
		'''
		response+="<form id='entry_form' method='get' action='run'><input type='hidden' id='selected_id' name='req' value=''></form>"
		'''
		#This is where my tech includes go.
		#response+="<link rel=\"stylesheet\" type=\"text/css\" href=\"css/coverflow.css\" />"
		#response+="<script src=\"js/jquery.min.js\"></script>"
		#response+="<script src=\"js/coverflow.min.js\"></script>"
		
		#This is where my jQuery Magnificence would go... IF I HAD ANY!!!
		#response+="<script>"
		
		f = open(os.path.join(self.app_root,'index.html'),'rb')
		response=f.read()
		f.close()
		response= response.replace("ADD_ANYTHING_ELSE_HERE",db_data)
	
		#response+="</body></html>"
		return response
	@cherrypy.expose
	def regen(self):
		cfe_dbgen.run()
		self.get_loader_db()
		self.reload_db(True)
		self.cache_system_list=""
		raise cherrypy.HTTPRedirect("/")
		
	@cherrypy.expose
	def cftest(self):
		response = "<html>"
		response +="<head>"
		
		response +="<link rel=\"stylesheet\" href=\"static/coverflow.css\"/>"
		response +="<meta charset=\"utf-8\">"
		response +="</head>"
		response +="<body>"
		response +="<div id=\"container\"></div>"
		response +="<script src='static/coverflow.js'></script>"
		
		response +="</body></html>"
		return response
	
	
	

	
	@cherrypy.expose
	def reset(self):
		os.chdir(self.app_root)
		if(self.local_entry == False):
			if(self.d_after == True):
				shutil.rmtree("tmp")
				#HAAAAAAX - TEH HAAAAAAXXX
				os.makedirs("tmp")
		raise cherrypy.HTTPRedirect("/?selected_system=%s" % self.selected_system)	

	def find_data_dir(self,entry_id):
		tp = os.path.join("data",self.selected_system,"%s" % entry_id)
		if(os.path.exists(tp)):
			self.cloud_rom = False
			print("Local Path Found at %s" % tp)
			return tp
		if(self.d_after == True):
			tp = os.path.join("tmp","data",self.selected_system,"%s" % entry_id)	
		else:
			tp = os.path.join("data",self.selected_system,"%s" % entry_id)
		os.makedirs(tp)
		os.chdir(tp)
		#We need to hit the cloud now.
		entry = self.cfe_database[self.selected_system][entry_id]
		
		for svc in self.cloud_services.keys():
			file_lst = []
			
			for fls in entry["Data"]:
				if(fls['svc'] == svc):
					op = self.cloud_services[svc].get_file(fls['id'])
					if(op != None):
						file_lst.append(op)
			break
		#Go back to root.
		os.chdir(self.app_root)
		return tp
			
				
	@cherrypy.expose
	def run(self,req):
		#req = base64.b64decode(req)
		system = self.selected_system
		entry_id = req
		print(system)
		print(entry_id)
		entry = self.cfe_database[system][entry_id]
		#See if we have the emulator already.
		
		if(not os.path.exists(os.path.join("loaders",entry['loader']))):
			os.makedirs(os.path.join("loaders",entry['loader']))
			out_path = os.path.join(self.app_root,"loaders",entry['loader'])
			#Get the emulator if we can't find it locally.
			os.chdir("tmp")
			
			fls = self.loaderdb[self.selected_system][os.name][entry['loader']]
			
			for svc in self.cloud_services.keys():
				file_lst = []
				if(fls['svc'] == svc):
					for fl in fls['id']:
						op = self.cloud_services[svc].get_file(fl)
						if(op != None):
							file_lst.append(op)
					break
			
			os.chdir(self.app_root)
			file_lst = sorted(file_lst)
			for fl in file_lst:
				fh = open(fl, 'rb')
				z = zipfile.ZipFile(fh)
				for name in z.namelist():
					z.extract(name,out_path)
				fh.close()
				os.remove(fl)

		try:
			ldr = importlib.import_module("loaders.%s" % entry['loader'])
		except:
			return "Error getting emulator module inserted loaders.%s"% entry['loader']	
		#Get all the data files.
				
		data_path = self.find_data_dir(entry_id)
		
		if(data_path != None):
			
			ldr.run(data_path)
			
		else:
			cfe_dbgen.run()
			self.refresh_emucloud_database()
			return "Error - %s Rom not found. Regenerating Database..." % game_name
		#Execute and Cleanup.
		return "<input type='button' name='reset_menu' value='Back to Menu' onclick=\"location.href='reset'\">"

def main():
	curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
	
	conf = {
	 'global':{
	 'server.socket_host': '0.0.0.0',
	'server.socket_port': 1337,
	'response.timeout':1000000000,
	'tools.staticfile.root':curdir,
	'tools.gzip.on':True
	 },
	 '/image': {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': 'bower_components',
		'tools.staticdir.root': os.path.join(curdir),
		
	},
	 '/css': {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': 'css',
		'tools.staticdir.root': os.path.join(curdir),
		
	},
	 '/js': {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': 'js',
		'tools.staticdir.root': os.path.join(curdir),
		
	},
	}
	cherrypy.quickstart(CloudFE(), '/', conf)
	

if(__name__=="__main__"):
	sys.exit(main())
