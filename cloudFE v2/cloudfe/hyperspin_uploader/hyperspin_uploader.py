'''
	HyperSpin to GDrive cloudFE Converter
	#EXAMPLE python hyperspin_uploader.py "Super Nintendo" -- All assets will upload to root.
	#EXAMPLE python hyperspin_uploader.py "Super Nintendo" 0B5cM_oMaeyO6M21WRjl6cjZzMzg -- all assets will upload to this directory.
	
'''
import random,string,sys,os,hashlib,json
from xml.dom import minidom
import gd_auth,gd_ops

LOADER = 'desmume'
SUPPORTED_EXTENSIONS = ['smc','sfc','zip','7z','rar']
ROM_DB = {}

def sha1_for_file(f, block_size=2**25):
    sha1 = hashlib.sha1()
    while True:
        data = f.read(block_size)
        if not data:
            break
        sha1.update(data)
    return sha1.hexdigest()
	
def get_sha1sum(infile):
	ff = open(infile,"rb")
	result = sha1_for_file(ff)
	ff.close()
	return result 
	
def get_id():
	return ''.join([random.choice(string.ascii_letters+string.digits) for ch in range(8)])

def find_entry(game_name,game_info):
	for gk in game_info.keys():
		
		if(game_info[gk]['name'] == game_name):
			return gk
	return None
		
def usage():
	print("Usage: %s [system_name] [ldr_name]" % sys.argv[0])
	sys.exit(1)

def gen_json(system_name,game_info):
	#Don't update if we don't need to.
	if(not os.path.exists("%s.txt" % system_name)):
		f = open("%s.txt" % system_name,'wb')
		f.write(json.dumps(game_info))
		f.close()

def upload_data(system_name,game_info):
	dsvc = gd_auth.drive_login()
	if(len(sys.argv) > 3):
		parent_id = sys.argv[3]
	else:
		gd_ops.get_root_id(dsvc)
	upload_list = []
	

	print("Enumerating Roms...")
	for root,dirs,files in os.walk("roms"):
		
		for f in files:
			
			fb,fe = os.path.splitext(f)
			game_id = find_entry(fb,game_info)
			if(game_id == None):
				print("Rom for %s not found." % game_info[game_id]['name'])
				continue
			else:
				#Get hash.
				game_info[game_id]['sha1'] = get_sha1sum(os.path.join(root,f))
				
				#Add rom to our upload list.
				upload_list.append([os.path.join(root,f),"cFE_DATA:%s" % game_id])
				#Add icon to our upload list.
				for root2,dirs2,files2 in os.walk("icon"):
					for f2 in files2:
						if f2.startswith(game_info[game_id]['name']):
							rt,parent = os.path.split(root2)
							basef,ext = os.path.splitext(f2)
							if(not basef.endswith("_%s" % parent)):
								fixed_name = os.path.join(root2,"%s_%s%s" % (basef,parent,ext))
							
								os.rename(os.path.join(root2,f2),fixed_name)
							else:
								fixed_name = os.path.join(root2,f2)
							upload_list.append([fixed_name,"cFE_ICON:%s" % game_id])
							break
				#Add any artwork to our upload list.
				for root3,dirs3,files3 in os.walk("artwork"):
					for f3 in files3:
						if f3.startswith(game_info[game_id]['name']):
							print("Found Artwork %s" % os.path.join(root3,f3))
							rt,parent = os.path.split(root3)
							basef,ext = os.path.splitext(f3)
							if(not basef.endswith("_%s" % parent)):
								fixed_name = os.path.join(root3,"%s_%s%s" % (basef,parent,ext))
								os.rename(os.path.join(root3,f3),fixed_name)
							else:
								fixed_name = os.path.join(root3,f3)
							
							upload_list.append([fixed_name,"cFE_ARTW:%s" % game_id])
			
			
	

	up_total = len(upload_list)
	up_counter = 0
	for item in upload_list:
		#Check to make sure we aren't uploading a duplicate.
		baspth,name = os.path.split(item[0])
		emu_file_obj = gd_ops.get_file_meta(dsvc,"title='%s' and fullText contains '%s'" % (name.replace("'","\\'"),item[1]))
		up_counter+=1
		if(emu_file_obj != []):
			print("[%d/%d] Skipping: %s" % (up_counter,up_total,name))
			continue
			
		print("[%d/%d] Uploading: %s" % (up_counter,up_total,name))
		gd_ops.upload_file(dsvc, name, item[1], parent_id, "", item[0])	
		
		

def game_exist(game_name):
	for root,dirs,files in os.walk("roms"):
		for f in files:
			if(f.startswith(game_name)):
				return True
	
	return False
		
if(__name__=="__main__"):
	game_info = {}
	if(len(sys.argv) < 3):
		usage()
	system_name = sys.argv[1]
	LOADER = sys.argv[2]
	
	
	
	if(os.path.exists("%s.txt" % system_name)):
		print("Found Cached Data...")
		f = open("%s.txt" % system_name,'rb')
		data = f.read()
		f.close() 
		game_info = json.loads(data)
	else:
		#open xml database (if exist)
		if(os.path.exists("%s.xml" % system_name)):
			xmldoc = minidom.parse("%s.xml" % system_name)
			itemlist = xmldoc.getElementsByTagName('game')
			for item in itemlist:
				#Skip games we don't have roms for.
				if(not game_exist(item.attributes['name'].value)):
					print("Missing ROM: %s" % (item.attributes['name'].value))
					continue
				cid = get_id()
				game_info[cid]={}
				game_info[cid]['name'] = item.attributes['name'].value
				game_info[cid]['loader'] = LOADER
				game_info[cid]['system'] = system_name
				game_info[cid]['publisher'] = ""
				game_info[cid]['players'] = ""
				game_info[cid]['emu_status'] = ""
				game_info[cid]['region'] = ""
				game_info[cid]['genre'] = ""
				game_info[cid]['rating'] = ""
				game_info[cid]['developer'] = ""
				game_info[cid]['year'] = ""
				
				for c in item.childNodes:
					#Skip Text Nodes because fuck them.
					if(c.nodeType == 3):
						continue
					tag_name  = c.tagName
					itm = item.getElementsByTagName(tag_name)
					for a in itm:
						try:
							tag_val = a.firstChild.nodeValue 
						except:
							pass
						if(tag_name == 'genre'):
							game_info[cid]['genre'] = tag_val
						if(tag_name=='year'):
							game_info[cid]['year'] = tag_val
						if(tag_name=='manufacturer'):
							game_info[cid]['developer'] = tag_val
						if(tag_name=='rating'):
							game_info[cid]['rating'] = tag_val
	gen_json(system_name,game_info)
	
	upload_data(system_name,game_info)