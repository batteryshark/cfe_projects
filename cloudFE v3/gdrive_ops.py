'''
    GDrive Specific Operations
'''
import requests,os,time,hashlib,json,sys
from Queue import Queue
from threading import Thread


def md5_for_file(f, block_size=2**25):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()
    
def get_md5sum(infile):
    ff = open(infile,"rb")
    result = md5_for_file(ff)
    ff.close()
    return result 


def stream_download(self,file_id):
    url = 'https://www.googleapis.com/drive/v2/files/%s?alt=media' % file_id
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,headers=headers)   
    data = r.content
    return data
#TODO - MD5 Check on local file exists.
def download_file(self,out_path,file_id,progress_callback=False):
    f_meta = get_file_info(self,item_id=file_id)[0]
    f_meta['fileSize'] = int(f_meta['fileSize'])
    max_chunk_sz = (1024*1024) * 50
    out_fpath = os.path.join(out_path,f_meta['title'])
    if(os.path.exists(out_fpath)):
        local_md5 = get_md5sum(out_fpath)
        if(local_md5.lower() == f_meta['md5Checksum'].lower()):
            if(progress_callback==True):
                gf = requests.get("%s/download_progress?chk_sz=%s" % (self.callback_url,str(os.path.getsize(out_fpath))))
            print("%s Skipped - Already Downloaded" % f_meta['title'])
            #TODO - callback to update file size for server.
            return
    f = open(out_fpath,'wb')
    f_offset = 0
    print("Starting Download: %s  %s" % (f_meta['title'],sizeof_fmt(f_meta['fileSize'])))
    while f_offset < f_meta['fileSize']:
        chk_sz = max_chunk_sz
        if(f_offset+max_chunk_sz > f_meta['fileSize']):
            chk_sz = f_meta['fileSize'] - f_offset
        url = 'https://www.googleapis.com/drive/v2/files/%s?alt=media' % file_id
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
            print("%s - %s/%s" % (f_meta['title'],sizeof_fmt(f_offset),sizeof_fmt(f_meta['fileSize'])))
        else:
            time.sleep(5)
    f.close()

def get_file_info(self,item_id):
    url = 'https://www.googleapis.com/drive/v2/files/%s' % item_id
    self.access_check()
    params = {
    'acknowledgeAbuse':True
    }
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,headers=headers,params=params) 
    data = r.json()
    data = [data]
    data = normalize_items(data)
    return data    

def get_info(self,item_path=None,item_id=None):
    url = 'https://www.googleapis.com/drive/v2/files/%s' % item_id
    self.access_check()
    params = {
    'acknowledgeAbuse':True
    }
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,headers=headers,params=params) 
    data = r.json()
    
    data = normalize_items(data)
    
    return data

def about(self):
    url = 'https://www.googleapis.com/drive/v2/about'
    self.access_check()
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,headers=headers) 
    data = r.json()
    return data

'''
def get_file_by_id(dsvc,file_id):
    try:
        file = dsvc.files().get(fileId=file_id).execute()
        return file
    except errors.HttpError, error:
        if("HttpError 404" in str(error)):
            print("Error - File/Directory Not Found with that ID on this GDrive")
            exit(1)
        print 'An error occurred: %s' % error
        exit(1)
'''

def get_url(self,file_id):
    return "https://googledrive.com/host/%s" % file_id
    

#Adds params that come out of onedrive normally for proper names.
def normalize_items(data):
    for i in range(0,len(data)):
    
        data[i]['name'] = data[i]['title']
        #Handling for the fact that gdrive doesnt let you.
        try:
            data[i]['size'] = data[i]['fileSize']
        except:
            data[i]['size'] = 0
        data[i]['createdBy'] = {"user":{}}
        data[i]['createdBy']['user']['displayName'] = data[i]['user'] = data[i]['owners'][0]['displayName']
        
        try:
            data[i]['md5'] = data[i]['md5Checksum']
        except:
            data[i]['md5'] = ''
        try:
            data[i]['url'] = data[i]['webViewLink']
            data[i]['path'] = data[i]['webViewLink']
        except:
            data[i]['path'] = ''
            data[i]['url'] = ''
        data[i]['parentReference'] = {}
        data[i]['parentReference']['path'] = data[i]['parents'][0]
        
    return data

def ls(self,parent_id=None,parent_path=None):
    results = []
    url = 'https://www.googleapis.com/drive/v2/files'
    self.access_check()
    params = {
    'q':"'%s' in parents" % parent_id
    }
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,params=params,headers=headers) 
    odata = r.json()
    data = odata['items']
    data = normalize_items(data)
    results.extend(data)
    while('nextPageToken' in odata.keys()):
            skip_token = odata['nextPageToken']
            self.access_check()
            headers = {"Authorization":"Bearer %s" % self.access_token}
            payload = {
            'pageToken':skip_token,
            'q':"'%s' in parents" % parent_id
            }
            r = requests.get(url,params=payload,headers=headers)
            odata = r.json()
            data = odata['items']
            data = normalize_items(data)
            results.extend(data)            
    return results
    
    
def ls_srch(self,parent_id=None,parent_path=None,q='*',offset=0):
    results = []
    url = 'https://www.googleapis.com/drive/v2/files'
    self.access_check()
    params = {
    'q':"fullText contains \"%s\" and  '%s' in parents" % (q,parent_id)
    }
    headers = {"Authorization":"Bearer %s" % self.access_token}
    r = requests.get(url,params=params,headers=headers) 

    odata = r.json()
    data = odata['items']
    data = normalize_items(data)
    results.extend(data)
    while('nextPageToken' in odata.keys()):
            skip_token = odata['nextPageToken']
            self.access_check()
            headers = {"Authorization":"Bearer %s" % self.access_token}
            payload = {
            'pageToken':skip_token,
            'q':"fullText contains \"%s\" and  '%s' in parents" % (q,parent_id)
            }
            r = requests.get(url,params=payload,headers=headers)
            odata = r.json()
            data = odata['items']
            data = normalize_items(data)
            results.extend(data)            
    return results



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
    print("Uploading %s" % in_file)
    fsz = os.path.getsize(in_file)
    f = open(in_file,'rb')
    data = f.read()
    fname = os.path.split(in_file)[1]
    f.close()
    url = 'https://www.googleapis.com/upload/drive/v2/files?uploadType=multipart'
   
    start_time = time.time()
    file_meta = {'title':fname}
    if(parent_id != None):
        file_meta['parents'] = [{"id":'%s' % parent_id}]
    while 1:
        self.access_check()
        headers = {"Authorization":"Bearer %s" % self.access_token,
        'Content-Type': 'multipart/mixed; boundary="bundry"'
        }    


        payload = "--bundry\nContent-Type: application/json; charset=UTF-8 \n\n"
        payload += json.dumps(file_meta)+"  \n\n--bundry\nContent-Type: application/octet-stream\n\n"
        payload += data+'\n'
        payload += "--bundry--\n"
      
        r = requests.post(url,headers=headers,data=payload)
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
    while True:
        (root_id,in_file) = q.get()
        g = upload_file_small(self,in_file,parent_id=root_id)
        q.task_done()

def upload_file_large_wrapper(self,q):
    while True:
        (root_id,in_file) = q.get()
        g = upload_file(self,in_file,parent_id=root_id)
        q.task_done()

#TODO - DO THIS.
def create_dir(self,folder_name,parent_id=None,parent_path=None):
    url = 'https://www.googleapis.com/drive/v2/files'
    
    self.access_check()
    
    headers = {"Authorization":"Bearer %s" % self.access_token,
    'Content-Type':'application/json'
    }
    data = {
    "title": folder_name,
    "mimeType": "application/vnd.google-apps.folder"
    }
    if(parent_id != None):
        data['parents'] = [{"id":'%s' % parent_id}]

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
            if(pr['title'] == root_dir):
                if(pr['mimeType'] == "application/vnd.google-apps.folder"):
                    root_id = pr['id']
                else:
                    print("ERROR - Destination Dir is Filename!")
                    print("%s @  %s %s" % (root_dir,parent_id,parent_path))
                    return
        if(root_id == ''):
            root_id = create_dir(self,root_dir,parent_id,parent_path)['id']
    
    root_lst = ls(self,root_id,parent_path)
    
    for rr in root_lst:
        if(rr['mimeType'] == "application/vnd.google-apps.folder"):
            remote_dir_list[rr['title']] = rr['id']
        if(rr['title'] in file_list):
            if(rr['mimeType'] == "application/vnd.google-apps.folder"):
                print("ERROR - Destination file is dir!")
                file_list.remove(rr['title'])
            else:
                local_md5 = get_md5sum(rr['title']).upper()
                if(local_md5 == rr['md5Checksum']):
                    #Skip file if already present.
                    file_list.remove(rr['title'])
        if(rr['title'] in dir_list):
            if(rr['mimeType'] != "application/vnd.google-apps.folder"):
                print("ERROR - Destination dir is a file!")
                dir_list.remove(rr['title'])
            
    file_list_large = []
    file_list_small = []
    for fl in file_list:
        if(os.path.getsize(fl) > 90*(1024*1024)):
              file_list_large.append(fl)
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
    url = 'https://www.googleapis.com/upload/drive/v2/files?uploadType=resumable'
    
    payload = {
    'title': os.path.split(in_file)[1]
    }
    if(parent_id != None):
        payload['parents'] = [{"id":parent_id}]
    up_session_url = ''
    while 1:
        self.access_check()
        headers = {
            "Authorization":"Bearer %s" % self.access_token,
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Length':fsz
        }
        r = requests.post(url,headers=headers,data=json.dumps(payload)+"  ")
        if(r.status_code != 200):
            print(r.status_code)
            print(r.content)
            time.sleep(5)
            continue
        up_session_url = r.headers['location']
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
            if(r.status_code > 202 and r.status_code != 308): #because 308 is ok too
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

