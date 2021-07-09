'''
    CloudStorage Substrate for OAuth2 Cloud Storage Services
'''

import os,sys,pickle,json,time,uuid,platform,webbrowser,requests
from importlib import import_module

class CloudStorage(object):
    def __init__(self,client_info_file,callback_url=None):
        client_info = {}
        try:
            f = open(client_info_file,'rb')
            client_info = json.loads(f.read())
        except:    
            f.close()
            print("Client File Missing or not JSON")
            exit(1)  
        f.close()       
        self.service_type  =  client_info['service_type']
        self.auth_uri      =  client_info['auth_uri']
        self.client_secret =  client_info['client_secret']
        self.token_uri     =  client_info['token_uri']
        self.redirect_uri  =  client_info['redirect_uri']
        self.client_id     =  client_info['client_id']
        self.scopes        =  client_info['scopes']
        self.svc_cache     =  "%s_cred.bin" % self.service_type
        self.access_token     =  None
        self.refresh_token    =  None
        self.token_expiration =  None
        self.rest_callback    =  False
        
        
        #In case we want to alert a remote machine to our driver's activity.
        self.callback_url   = callback_url 
        if(self.callback_url != None):
            self.rest_callback = True

        self.client_machine = platform.node()
        self.user_cookie    = uuid.uuid4()

        if(os.path.exists(self.svc_cache)):
            mp = pickle.load(open(self.svc_cache,"rb"))
            self.access_token     = mp['access_token']
            self.refresh_token    = mp['refresh_token']
            self.token_expiration = int(mp['token_expiration'])
            self.access_check()
        else:
            self.log_in()
        #Pull API-Specific Functionality
        ops = import_module("%s_ops" % self.service_type.lower())
        self.ops = ops
        

    
    #Log In
    def log_in(self):
        #Step 1 - Get Authorization
        params = {
        "client_id"    : self.client_id,
        "scope"        : self.scopes,
        "response_type": 'code',
        "redirect_uri" : self.redirect_uri
        }
        r = requests.get(self.auth_uri,params=params)
        if(r.status_code != 200):
            print("REGISTRATION ERROR")
            print(r.status_code)
            print(r.content)
            exit(1)

        #If UI - this will open a window.
        try:
            webbrowser.open(r.url)
        except:
            pass
        #USER INTERACTION.
        print("No GUI - Go to This Link:")
        print(r.url)
        print(" ")      

        response_code = raw_input("Paste Response Code:")

        #Step 2 - Get the Tokens.
        headers = {
        'content-type':'application/x-www-form-urlencoded'
        }
        payload = {
        "redirect_uri":self.redirect_uri,
        "client_id":self.client_id,
        'grant_type':'authorization_code',
        'client_secret':self.client_secret,
        'code':response_code
        }
        r = requests.post(self.token_uri,data=payload,headers=headers)
        if(r.status_code != 200):
            print("Auth Response Error")
            print(r.status_code)
            print(r.content)
            exit(1)

        data = json.loads(r.content)
        #Copy Response Data To Driver.
        self.refresh_token = data['refresh_token']
        self.access_token  = data['access_token']
        self.token_expiration = time.time() + data['expires_in']
        self.save_creds()       


    #Refresh access token if expiring in the next minute.
    def access_check(self):
        if(time.time() > self.token_expiration - 60):
            self.refresh_access_token()
    
    #Dump credentials to disk to cache login authorization.
    def save_creds(self):
        mp = {
        'access_token':self.access_token,
        'refresh_token':self.refresh_token,
        'token_expiration':self.token_expiration
        }
        pickle.dump(mp,open(self.svc_cache,"wb"))

    #Get new refresh token.
    def refresh_access_token(self):    
        headers = {'content-type':'application/x-www-form-urlencoded'}
        payload = {
        'redirect_uri' :self.redirect_uri,
        'client_id'    :self.client_id,
        'grant_type'   :'refresh_token',
        'refresh_token':self.refresh_token,
        'client_secret':self.client_secret,
        }

        r = requests.post(self.token_uri,data=payload,headers=headers)
        if(r.status_code != 200):
            print("Refresh Token Error")
            print(r.status_code)
            print(r.content)
            return

        data = json.loads(r.content)
        #GDrive doesn't send back the refresh token...
        try:
            self.refresh_token     = data['refresh_token']
        except:
            pass
        self.access_token      = data['access_token']
        self.token_expiration = time.time() + data['expires_in']
        self.save_creds()       



   














def main():
    storage = CloudStorage('onedrive_client.json')
    storage.ops.download_file(storage,'.','4e452184f3436e61!10252')
    #f_entry = storage.ops.upload_dir(storage,'E:\\rsdlc',parent_id='0B5cM_oMaeyO6fmw5SGd1SDVqdHVxc1Qxc083TjFJSzlxVk1kdmxxd25CYU14dF9SSHdXaFE')
    

if __name__ == '__main__':
    main()

