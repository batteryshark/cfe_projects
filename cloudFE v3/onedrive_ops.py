'''
    OneDrive Specific Operations
'''
import requests,os,time,hashlib,json,sys
from Queue import Queue
from threading import Thread

#TODO - Return values from LS in a uniform and service-agnostic format.
#Name, Type, size, path/from/root, id, hosting url, md5, description - TODODO
#List All Files in a specific parent

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

#Pull a file into a memory buffer.
def stream_download(self,file_id):
    url = 'https://api.onedrive.com/v1.0/drive/items/%s/content' % file_id
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,headers=headers)   
    data = r.content
    return data


def download_file(self,out_path,file_id,progress_callback=False):
    f_meta = get_info(self,item_id=file_id)
    f_meta['size'] = int(f_meta['size'])
    max_chunk_sz = (1024*1024) * 50
    out_fpath = os.path.join(out_path,f_meta['name'])
    f = open(out_fpath,'wb')
    f_offset = 0
    print("Starting Download: %s  %s" % (f_meta['name'],sizeof_fmt(f_meta['size'])))
    while f_offset < f_meta['size']:
        chk_sz = max_chunk_sz
        if(f_offset+max_chunk_sz > f_meta['size']):
            chk_sz = f_meta['size'] - f_offset
        url = 'https://api.onedrive.com/v1.0/drive/items/%s/content' % file_id
        self.access_check()

        headers = {"Authorization":"Bearer %s" % self.access_token,
        'Range':'bytes=%d-%d' % (f_offset,f_offset+chk_sz)
        }
        r = requests.get(url,headers=headers)
        if(r.status_code < 400):

            f.write(r.content)
            f_offset +=chk_sz+1
            if(progress_callback==True):
                gf = requests.get("%s/download_progress?chk_sz=%s" % (self.callback_url,str(chk_sz+1)))
            print("%s - %s/%s" % (f_meta['name'],sizeof_fmt(f_offset),sizeof_fmt(f_meta['size'])))
        else:
            time.sleep(5)
    f.close()

def get_info(self,item_path=None,item_id=None):
    base_url = ''
    if(item_id != None):
        base_url = 'https://api.onedrive.com/v1.0/drive/items/%s' % item_id
    if(item_path != None):
        base_url = 'https://api.onedrive.com/v1.0%s' % item_path
    if(base_url == ''):
        print("ERROR - NO Path or ID Specified")
        exit(1)

    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(base_url,headers=headers)
    #If the resource isn't found.
    if(r.status_code == 404):
        print("Not Found.")
        print(base_url)    
        exit(1)
    tr = r.json()

    return tr

#Get Icon URL From file Thumbnail.
def get_thumbnail_url(self,file_path=None,file_id=None,size='small'):
    base_url = ''
    if(file_id != None):
        base_url = 'https://api.onedrive.com/v1.0/drive/items/%s/thumbnails/0/%s' % (file_id,size)
    if(file_path != None):
        base_url = 'https://api.onedrive.com/v1.0%s:/thumbnails/0/%s' % (file_path,size)

    if(base_url == ''):
        print("ERROR - NO Thumbnail Path or ID Specified")
        return ''
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(base_url,headers=headers)
    #If the resource isn't found.
    if(r.status_code == 404):
        print("Not Found.")
        print(base_url)
        return ''
    tr = r.json()
    if(not 'url' in tr.keys()):
        print(r.status_code)
        print("ERROR")
        print(tr)
        exit(1)
    return tr['url']

def ls(self,parent_id=None,parent_path=None):
    #The limit of 200 is a hard API limit.
    
    st_response = None
    results = []
    if(parent_id == None):
        url = 'https://api.onedrive.com/v1.0/drive/root/children'
    else:
        url = 'https://api.onedrive.com/v1.0/drive/items/%s/children' % parent_id

    if(parent_path != None):
        url = 'https://api.onedrive.com/v1.0%s:/children' % parent_path

    payload = {'top':200} # 200 results is the hard api limit

    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,params=payload,headers=headers)
    tr = r.json()
    if(not 'value' in tr.keys()):
        print("ERROR")
        print(tr)
        exit(1)
    results.extend(tr['value'])
    while('@odata.nextLink' in tr.keys()):
        skip_token = tr['@odata.nextLink'].split('skiptoken=')[1]
        self.access_check()
        headers = {"Authorization":"Bearer %s" % self.access_token}
        r = requests.get("%s&skiptoken=%s" % (url,skip_token), params=payload,headers=headers)
        tr = r.json()
        try:
            results.extend(tr['value'])
        except:
            print("ERROR")
            print(r.status_code)
            print(r.content)
    return results


def get_url(self,file_id):
    return "https://onedrive.live.com/download.aspx?resid=%s" % file_id

def ls_srch(self,parent_id=None,parent_path=None,q='*',offset=0):    
    rslts = []
    if(parent_id == None):
        url_base = 'https://api.onedrive.com/v1.0/drive/root/view.search?q=%s' % q
    else:
        url_base = 'https://api.onedrive.com/v1.0/drive/items/%s/view.search?q=%s' % (parent_id,q)
 
    if(parent_path != None):
        url_base = 'https://api.onedrive.com/v1.0%s:/view.search?q=%s' % (parent_path,q)

    payload = {
    'top':50 # HARD API LIMIT
    }
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
   
    r = requests.get(url_base, params=payload,headers=headers)
    tr = r.json()
    
    rslts.extend(tr['value'])
    while('@odata.nextLink' in tr.keys()):
        skip_token = tr['@odata.nextLink'].split('skiptoken=')[1]
        self.access_check()
        headers = {"Authorization":"Bearer %s" % self.access_token}
        r = requests.get("%s&skiptoken=%s" % (url_base,skip_token), params=payload,headers=headers)
        tr = r.json()
        try:
            rslts.extend(tr['value'])
        except:
            print("ERROR")
            print(r.status_code)
            print(r.content)

    return rslts

def test(self):
    pass


def cancel_upload(up_session_url):
    r = requests.delete(up_session_url)
    if(r.status_code !=204):
        print("Upload Cancel Failed!")
        print(r.status_code)
        print(r.content)

def sizeof_fmt(num, suffix='B'):

        for unit in [' ',' K',' M',' G',' T',' P',' E',' Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, ' Y', suffix)

def upload_file_small(self,in_file,parent_id=None,parent_path=None):
    fsz = os.path.getsize(in_file)
    f = open(in_file,'rb')
    data = f.read()
    f.close()
    if(parent_id != None):
        url = 'https://api.onedrive.com/v1.0/drive/items/%s/children/%s/content' % (parent_id,os.path.split(in_file)[1])
    elif(parent_path != None):
        fpath = os.path.join(parent_path,os.path.split(in_file)[1])
        url = 'https://api.onedrive.com/v1.0/drive/root:/%s:/content' % (fpath)
    else:
        url = 'https://api.onedrive.com/v1.0/drive/root:/%s:/content' % (os.path.split(in_file)[1])
    start_time = time.time()

    while 1:
        self.access_check()
        headers = {"Authorization":"Bearer %s" % self.access_token,
        'Content-Type':'text/plain'
        }    
        r = requests.put(url,headers=headers,data=data)
        if(r.status_code > 202):
            print(r.status_code)
            print(r.content)
            time.sleep(5)
            continue
        break
    elapsed_time = time.time() - start_time
    print("%s Finished @ %s/sec" % (in_file,sizeof_fmt(fsz/elapsed_time)))

    return r.json()



def upload_file_small_wrapper(self,q):
    sys.stdout.write('\r')
    while not q.empty():
        (root_id,in_file) = q.get()
        g = upload_file_small(self,in_file,parent_id=root_id)
        q.task_done()

def upload_file_large_wrapper(self,q):
    sys.stdout.write('\r')
    while not q.empty():
        (root_id,in_file) = q.get()
        g = upload_file(self,in_file,parent_id=root_id)
        q.task_done()

#TODO - DO THIS.
def create_dir(self,folder_name,parent_id=None,parent_path=None):
    url = ''
    if(parent_id != None):
        url = 'https://api.onedrive.com/v1.0/drive/items/%s/children' % parent_id
    elif(parent_path != None):
        url = 'https://api.onedrive.com/v1.0/drive/root:/%s:/children' % parent_path
    else:
        url = 'https://api.onedrive.com/v1.0/drive/root/children'
    self.access_check()
    
    headers = {"Authorization":"Bearer %s" % self.access_token,
    'Content-Type':'application/json'
    }
    data = {
    "name": folder_name,
    "folder": { }
    }
    r = requests.post(url,data=json.dumps(data)+"  ",headers=headers)
    if(r.status_code > 202):
        print(r.status_code)
        print(r.content)
    
    return r.json()




    q.task_done()

def proc_upload_list(self,root_id,flist,up_type):
  if(flist == []):
    return
  upload_queue = Queue()
  num_upload_threads = 5
  if(up_type == "small"):
    for i in range(num_upload_threads):
        worker = Thread(target=upload_file_small_wrapper, args=(self,upload_queue))
        worker.daemon = True
        worker.start()
  if(up_type == "large"):
    for i in range(num_upload_threads):
      worker = Thread(target=upload_file_large_wrapper, args=(self,upload_queue))
      worker.daemon = True
      worker.start()
      
    for fls in flist:
        upload_queue.put((root_id,fls))
    upload_queue.join()


#MultiThreaded Upload Function :3
def upload_dir(self,in_path,parent_id=None,parent_path=None,depth=0):
    old_path = os.getcwd()
    os.chdir(in_path)
    print("CD to %s" % in_path)
    #Get all dirs
    dir_list = []
    remote_dir_list = {}
    file_list = []
    root_dir = os.path.basename(os.path.normpath(in_path))
    
    for root,dirs,files in os.walk(unicode('.')):
        for d in dirs:
            dir_list.append(d)
        for f in files:
            file_list.append(f)
        break
    
    parent_lst = ls(self,parent_id,parent_path)
    
    if(depth != 0):
        root_id = parent_id
    else:
        root_id = ''
        for pr in parent_lst:
            if(pr['name'] == root_dir):
                if('folder' in pr.keys()):
                    root_id = pr['id']
                else:
                    print("ERROR - Destination Dir is Filename!")
                    print("%s @  %s %s" % (root_dir,parent_id,parent_path))
                    return
        if(root_id == ''):
            root_id = create_dir(self,root_dir,parent_id,parent_path)['id']
    
    root_lst = ls(self,root_id,parent_path)
    
    for rr in root_lst:
        if('folder' in rr.keys()):
            remote_dir_list[rr['name']] = rr['id']
        if(rr['name'] in file_list):
            if('folder' in rr.keys()):
                print("ERROR - Destination file is dir!")
                file_list.remove(rr['name'])
            else:
                local_sha1 = get_sha1sum(rr['name']).upper()
                if(local_sha1 == rr['file']['hashes']['sha1Hash']):
                    #Skip file if already present.
                    file_list.remove(rr['name'])
        if(rr['name'] in dir_list):
            if(not 'folder' in rr.keys()):
                print("ERROR - Destination dir is a file!")
                dir_list.remove(rr['name'])
            
    file_list_large = []
    file_list_small = []
    for fl in file_list:
        if(os.path.getsize(fl) > 90*(1024*1024)):
            if(os.path.getsize(fl) < 10000 *(1024*1024)):#10GB limit for onedrive :<
              file_list_large.append(fl)
            else:
              print("Warning: %s Skipped because it's > 10GB" % fl)
        else:
            file_list_small.append(fl)
    proc_upload_list(self,root_id,file_list_small,"small")
    proc_upload_list(self,root_id,file_list_large,"large")


    for dirl in dir_list:
        if(not dirl in remote_dir_list.keys()):
            nd_id = create_dir(self,dirl,root_id)['id']
        else:
            nd_id = remote_dir_list[dirl]
        upload_dir(self,dirl,parent_id=nd_id,depth=depth+1)
    os.chdir(old_path)



def upload_file(self,in_file,parent_id=None,parent_path=None):
    max_chunk_sz = (1024*1024) * 50
    fsz = os.path.getsize(in_file)
    f_offset = 0

    #Init Download
    if(parent_id != None):
        url = 'https://api.onedrive.com/v1.0/drive/items/%s:/%s:/upload.createSession' % (parent_id,os.path.split(in_file)[1])
    elif(parent_path != None):
        fpath = os.path.join(parent_path,os.path.split(in_file)[1])
        url = 'https://api.onedrive.com/v1.0/drive/root:/%s:/upload.createSession' % (fpath)
    else:
        url = 'https://api.onedrive.com/v1.0/drive/root:/%s:/upload.createSession' % (os.path.split(in_file)[1])
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    up_session_url = ''
    while 1:
        r = requests.post(url,headers=headers)
        if(r.status_code != 200):
            print(r.status_code)
            print(r.content)
            time.sleep(5)
            continue
        up_session_url = r.json()['uploadUrl']
        print("Uploading %s" % in_file)
        break


    start_time = time.time()
    while(f_offset < fsz):
        chk_sz = max_chunk_sz
        if(fsz-f_offset < max_chunk_sz):
            chk_sz = fsz-f_offset
        f=open(in_file,'rb')
        f.seek(f_offset)
        data = f.read(chk_sz)

        f.close()

        while 1:
            self.access_check()
            headers = {"Authorization":"Bearer %s" % self.access_token,
            'Content-Range':'bytes %d-%d/%d' % (f_offset,(f_offset+chk_sz)-1,fsz)
            }
            r = requests.put(up_session_url,headers=headers,data=data)
            if(r.status_code > 202):
                print(r.status_code)
                print(r.content)
                time.sleep(5)
                continue
            else:
                break
        f_offset += chk_sz
        print("%s Progress: %s/%s" % (in_file,sizeof_fmt(f_offset),sizeof_fmt(fsz)))
    elapsed_time = time.time() - start_time
    print("%s Finished @ %s/sec" % (in_file,sizeof_fmt(fsz/elapsed_time)))

    return r.json()




