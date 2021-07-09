'''
    Drive Nexus
'''
import os,sys,json,importlib,cherrypy,time,json,hashlib,webbrowser,base64,platform,zipfile,shutil
import cs
from cherrypy.lib.static import serve_file
from operator import itemgetter

#Initial Setup
HOST_OS = ""
if("Windows" in platform.platform()):
    HOST_OS = "win"
if("Linux" in platform.platform()):
    HOST_OS = "linux"
if("Darwin" in platform.platform()):
    HOST_OS = "osx"
if("Darwin" in platform.platform() and "iPhone" in platform.platform()):
    HOST_OS = "ios"
if(platform.linux_distribution()[0] == 'Android'):
    HOST_OS = "android"     
#Root of our frontend directory.
#ROOT_DIR = os.path.join(os.getcwd(), os.path.dirname(__file__))
ROOT_DIR = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))

#Set up our directories.
if(not os.path.exists("local")):
    os.makedirs("local")



class NXS(object):
    def __init__(self,web_root):
        self.onedrive_svc = None
        self.gdrive_svc = None
        self.web_root = web_root
        self.cloud_svc = None
        self.system_list = {}
        
        self.selected_system = None
        self.selected_entry =  {}
        self.system_entry = []
        self.downloaded_size_progress = 0
        self.downloaded_size_total = 0
        self.downloaded_short_circuit = False
        
    def sizeof_fmt(self,num, suffix='B'):
            num = int(num)
            for unit in [' ',' K',' M',' G',' T',' P',' E',' Z']:
                if abs(num) < 1024.0:
                    return "%3.1f%s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f%s%s" % (num, ' Y', suffix) 

    @cherrypy.expose
    def download_progress(self,chk_sz=None):
        #Update the transfer.
        if(chk_sz != None):
            self.downloaded_size_progress +=int(chk_sz)
            return ""
        if(self.downloaded_short_circuit == True):
            return json.dumps({'down_pr':100,"down_str":'','status':"Ready!"})
        if(self.downloaded_size_total == 0):
            dstr = "%s / %s " % (self.sizeof_fmt(self.downloaded_size_progress),self.sizeof_fmt(self.downloaded_size_total))
            if(self.downloaded_size_progress == 0 and self.downloaded_size_total ==0):
                dstr = 'Initializing...'
            pkg = {
                'down_pr':0,
                "down_str":dstr,
                'status':'Starting Download'
            }
            return json.dumps(pkg)            
        try:
            prcnt_down = int((float(self.downloaded_size_progress)/float(int(self.downloaded_size_total))) * 100)
        except:
            pass
        
        if(self.downloaded_size_progress >= self.downloaded_size_total):
            prcnt_down = 100
        pkg = {
            'down_pr':prcnt_down,
            "down_str":"%s / %s " % (self.sizeof_fmt(self.downloaded_size_progress),self.sizeof_fmt(self.downloaded_size_total)),
            'status':'Downloading...'
        }
        return json.dumps(pkg)
        

    @cherrypy.expose
    def get_info(self,entry_id=None,info_id=None,cs_name=None):
        self.cs_login(cs_name)
        if(cs_name == 'OneDrive'):
            cloud_svc = self.onedrive_svc
        if(cs_name == 'GDrive'):
            cloud_svc = self.gdrive_svc

        entry_info = json.loads(cloud_svc.ops.stream_download(cloud_svc,info_id))
        entry_info['local'] = "no"
        print(entry_info)
        local_path = os.path.join('local',entry_info['system'],entry_id)
        if(os.path.exists(local_path)):
            entry_info['local'] = "yes"
        return json.dumps(entry_info)

    @cherrypy.expose
    def system(self,parent_id,parent_name,cs_name):
        #First things first - build the system entry_db
        entry_db = {}
        response = ""
        f = open(os.path.join(ROOT_DIR,'web','system.htm'),'rb')
        response+=f.read()
        f.close()
        self.selected_entry =  {}
        cloud_svc = None
        if(cs_name == 'OneDrive'):
            cloud_svc = self.onedrive_svc
        if(cs_name == 'GDrive'):
            cloud_svc = self.gdrive_svc

        if(cloud_svc == None):
            self.cs_login(cs_name)
        if(cs_name == 'OneDrive'):
            cloud_svc = self.onedrive_svc
        if(cs_name == 'GDrive'):
            cloud_svc = self.gdrive_svc

        loaders_folder_id = ''

        entries  = cloud_svc.ops.ls(cloud_svc,parent_id=parent_id)
        for en in entries:
            print(en['name'])
            if(en['name'] == 'Loaders'):
                loaders_folder_id = en['id']
        for en in entries:
            print(en['name'])

            if(en['name'] == 'Loaders'):
                print("DEBUG - LOADERS FOLDER FOUND!")
                loaders_folder_id = en['id']

                continue
            icon_url = ''
            try:
                en['size'] += int(en['fileSize'])
            except:
                pass
            entry_fls  = cloud_svc.ops.ls(cloud_svc,parent_id=en['id'])
            preview_url = ''
          
            info_id = ''
            total_sz = 0

            for enf in entry_fls:
                total_sz+=int(enf['size'])
                if('icon.' in enf['name']):
                    icon_url = cloud_svc.ops.get_url(cloud_svc,enf['id'])
                if('preview.mp4' in enf['name']):
                    preview_url = cloud_svc.ops.get_url(cloud_svc,enf['id'])
                if('info.json'  == enf['name']):
                    info_id = enf['id']

            entry_db[en['id']] = {'system':parent_name,'cs_name':cs_name,'loaders_folder_id':loaders_folder_id,'info_id':info_id,'size_disp':self.sizeof_fmt(total_sz),'size':total_sz,'id':en['id'],'icon':icon_url,'name':en['name'],'preview_video':preview_url}
            
        
        #Now - build the interface.
        db_data="<script>"
        db_data+="var cs_name=\"%s\";" % cs_name
        db_data+="var selected_system = \"%s\";" % parent_name
        db_data+="var e_db = %s;" % json.dumps(entry_db)
        sorted_keys = sorted(entry_db.keys(), key=lambda y: (entry_db[y]['name']))
        db_data+="var entry_keys="
        for i in range(0,len(sorted_keys)):
            sorted_keys[i] = str(sorted_keys[i])
        db_data+="%s;" % str(sorted_keys)
        db_data+="</script>"
        f = open(os.path.join('web','system.htm'),'rb')
        response=f.read()
        f.close()
        response= response.replace("ADD_ANYTHING_ELSE_HERE",db_data)       

        return response
  

    @cherrypy.expose
    def run(self,entry_id,loaders_folder_id,system_name,cs_name,pref_loader='',save_only='no',wipe_cache='no'):

        if(wipe_cache == 'yes'):
            shutil.rmtree(os.path.abspath(os.path.join('local',system_name,entry_id)))
            return ""
        loader_root_path = ''
        self.downloaded_size_total = 0
        self.downloaded_size_progress = 0
        self.downloaded_short_circuit = False
        os.chdir(self.web_root)
        self.cs_login(cs_name)
        if(cs_name == 'OneDrive'):
            cloud_svc = self.onedrive_svc
        if(cs_name == 'GDrive'):
            cloud_svc = self.gdrive_svc
        try:
            shutil.rmtree("tmp")
            if(not os.path.exists("tmp")):
                os.makedirs("tmp")
        except:
            pass

        response = ''
        #Only if we have a pref loader at the moment.
        if(pref_loader !=''):
            
            loader_path = os.path.abspath(os.path.join('local',system_name,'loaders',pref_loader))
            loader_root_path = os.path.abspath(os.path.join('local',system_name,'loaders'))
            if(not os.path.exists(loader_path)):
                if(save_only != 'yes'):
                    loader_path = os.path.abspath(os.path.join('tmp',system_name,'loaders',pref_loader))
                    loader_root_path = os.path.abspath(os.path.join('tmp',system_name,'loaders'))
                os.makedirs(loader_path)
                p_entries = cloud_svc.ops.ls(cloud_svc,
                    parent_id=loaders_folder_id)
                loaders_plat_id = ''
                for pn in p_entries:
                    if(pn['name'] == HOST_OS):
                        loaders_plat_id = pn['id']
                if(loaders_plat_id == ''):
                    return "ERROR - NO LOADER FOR PLATFORM!"
                f_entries = cloud_svc.ops.ls_srch(cloud_svc,
                    parent_id=loaders_plat_id,
                    q=pref_loader
                    )
                
                cloud_svc.ops.download_file(cloud_svc,'tmp',f_entries[0]['id'])
                
                fh = open(os.path.join('tmp',f_entries[0]['name']), 'rb')
                z = zipfile.ZipFile(fh)
                for name in z.namelist():
                    z.extract(name,loader_path)
                fh.close()
                os.remove(os.path.join('tmp',f_entries[0]['name']))


        
        #Check to see if we have the game locally, get it if we don't.
        data_path = os.path.abspath(os.path.join('local',system_name,entry_id))
        if(not os.path.exists(data_path)):
            if(save_only != 'yes'):
                data_path = os.path.join('tmp',system_name,entry_id)
            e_files = cloud_svc.ops.ls(cloud_svc,parent_id=entry_id)
            if(not os.path.exists(data_path)):
                os.makedirs(data_path)
            for ef in e_files:
                self.downloaded_size_total += int(ef['size'])
            for ef in e_files:
                cloud_svc.ops.download_file(cloud_svc,data_path,ef['id'],progress_callback=True)
        
        data_path = os.path.abspath(data_path)
        self.downloaded_short_circuit = True
        if(save_only == 'yes'):
            print("Downloaded!")
            return ""
        sys.path.append(loader_root_path)
        ldr = importlib.import_module("%s" % pref_loader)
        sys.path.remove(loader_root_path)
        print("Running %s with %s" % (entry_id,pref_loader))
        if(pref_loader == 'pc_windows'):
            ldr.run(data_path,root_dir=ROOT_DIR)
        else:
            ldr.run(data_path)
        print('FINISHED')
        os.chdir(self.web_root)
        return response

    #Read list of shares from static file.
    def parse_sources_lst(self):
        os.chdir(ROOT_DIR)
        f = open('sources.txt','r')
        lines = f.readlines()
        f.close()
        fe_src = {}
        for l in lines:
            #Skip Commented Line
            if(l.startswith('#')):
                continue
            l = l.strip()
            stype,rid = l.split("::")
            if(not stype in fe_src.keys()):
                fe_src[stype] = []
            fe_src[stype].append(rid)
        return fe_src

    def cs_login(self,svc_type):
        if(svc_type == 'OneDrive'):
            if(self.onedrive_svc == None):
                self.onedrive_svc = cs.CloudStorage('onedrive_client.json',callback_url='http://127.0.0.1:1337')
                
        if(svc_type == 'GDrive'):
            if(self.gdrive_svc == None):
                self.gdrive_svc = cs.CloudStorage('gdrive_client.json',callback_url='http://127.0.0.1:1337')




    #Get list of systems for each cloud store.
    def get_system_list(self):
        
        system_list = {}
        src_db = self.parse_sources_lst()
        for scc in src_db.keys():
            cloud = None

            self.cs_login(scc)
            if(scc == 'OneDrive'):
                cloud = self.onedrive_svc
            if(scc == 'GDrive'):
                cloud = self.gdrive_svc

            src_lst = src_db[scc]
            for sc in src_lst:
                rlst = cloud.ops.ls(cloud,parent_id=sc)
                for rl in rlst:
                    user_id = ""
                    if('owners' in rl.keys()):
                        user_id = rl['owners'][0]['emailAddress']
                    else:
                      
                        user_id = rl['createdBy']['user']['id']
                    if(not user_id in system_list.keys()):
                        system_list[user_id] = {
                        'user_name':rl['createdBy']['user']['displayName'],
                        'user_id':user_id,
                        'systems':[],
                        'service_type':cloud.service_type
                        }

                    system_list[user_id]['systems'].append({
                        'share_name':rl['name'],
                        'parent_id':rl['id']
                    })                    
                    
        return system_list

    @cherrypy.expose
    def index(self):
        system_list = self.get_system_list()
        response = ""
        f = open(os.path.join(ROOT_DIR,'web','index.htm'),'rb')
        response+=f.read()
        f.close()
        main_content = "<div id=\"accordion\">"
        
        for sk in system_list.keys():
            s = system_list[sk]
            main_content+="<h3>%s (%s) <img width='16' src='/web/image/%s'/></h3>" %(s['user_name'],s['user_id'],'%s_icon.ico' % s['service_type'])

            main_content+="<div>"
            newlist = sorted(s['systems'], key=itemgetter('share_name'))
            for sy in newlist:
                main_content+="<a href='system?parent_id=%s&parent_name=%s&cs_name=%s'>%s</a><br/>" % (sy['parent_id'],sy['share_name'],s['service_type'],sy['share_name'])
            main_content+="</div>"

        main_content+="</div>"

        response = response.replace("<!--BODY_STUFF-->",main_content)
        return response

if __name__ == '__main__':
    conf = {
     'global':{
                'server.socket_host': '0.0.0.0',
                'server.socket_port': 1337,
                'response.timeout':1000000000,
                'tools.staticfile.root':ROOT_DIR,
                'tools.gzip.on':True,
              },
     '/web': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'web',
        'tools.staticdir.root': ROOT_DIR,
            },
    }
    #Start our webserver.
    cherrypy.quickstart(NXS(ROOT_DIR), '/', conf)
    