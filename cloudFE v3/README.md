# cloudFE
Cross-Platform Cloud-Based FrontEnd for games, roms, and apps.

![](http://i.imgur.com/4bOBVpb.png)

![](http://i.imgur.com/MMGiRO4.png)

![](http://i.imgur.com/0mD9wI6.png)

### Features:
- Supports OneDrive and Google Drive (any account type). More options planned.
- Supports sharing games/apps with other users: simply give them a folder ID of a cFE directory.
- Supports local storage for offline play.
- Supports video previews and flexible metadata for each entry.
- Supports custom loaders for many types of apps/games or custom loaders for each - your choice.
- Supports python scripting for app/game setup and native support of .7z,.zip,.rar, and other formats.
- Easy to add entries and share with others.

### Requirements:
- Python 2.7.9 (maybe older, but that's what I use)
- requests (pip install requests)
- cherrypy (pip install cherrypy)

### Getting Started - Add Sources
![](http://i.imgur.com/NE2Tjhl.png)

Simply add any folder IDs from your own GDrive/OneDrive shares to sources.txt
The format expected is Service::folder_id (eg OneDrive::folder_id or GDrive::folder_id)
You can also use # for comments to separate your lists.

Note: If you add ids from someone else's account, they will need to share the directories
with your account (see below).

### Getting Started - First Time:
_1. Install all dependencies.

_2. Run python nxs.py

![](http://i.imgur.com/OltylAz.png)

_3. Go to http://127.0.0.1/1337 to begin

_4.(first time only) If you have a GDrive folder id in sources.txt, you'll be greeted with a GDrive login, pick your GDrive account, log in, and accept the permissions; copy the response code into the console. Alternatively, hit enter (leaving the console repsonse blank) to skip.

![](http://i.imgur.com/8rZVK71.png)

![](http://i.imgur.com/twwuiYV.png)

![](http://i.imgur.com/55pGpLW.png)

![](http://i.imgur.com/OrcNrzt.png)

_5.(first time only) You'll then be greeted with a OneDrive login, pick your OneDrive account and log in; copy the response code in the address bar and paste it into the console. Alternatively, hit enter (leaving the console repsonse blank) to skip.

![](http://i.imgur.com/YVoEzqM.png)

![](http://i.imgur.com/fE5OBQd.png)

![](http://i.imgur.com/iaEZ1yV.png)

### Getting Started - Using the FrontEnd
_1.Go to http://127.0.0.1/1337 to begin if you aren't there already from the initial setup.
_2.Select the system desired from your accordion list of shares.

![](http://i.imgur.com/zAhqwub.png)

![](http://i.imgur.com/77bQ8Iu.png)

_3. Arrow keys will control the cover flow of entries - there are a few options:
  * To play a game by pulling the files to a temporary directory, select 'Play Game'.
    If the game is on the local system, it won't download any additional files.
  * To save a game to the local system, select 'Save on Device'.
  * To delete a saved game from the local system, select 'Delete From Device'
  * To go back to system/share select, choose 'Main Menu'
  
### Instructions - Share With Someone
1.Right click on the root folder of your cloudFE directory in GDrive/Onedrive and follow the usual folder share process (entering the email address of the person you want to share with). Then, copy the directory ID and give it to them.

##### OneDrive:

![](http://i.imgur.com/GpImcsC.png)

![](http://i.imgur.com/mM4Hm9K.png)

##### GDrive:

![](http://i.imgur.com/UuL1reo.png)

![](http://i.imgur.com/mkGYV1p.png)

### Tutorial - Add your own content

We'll add the classic game 'SkiFree' as an example - you can find the finished version in examples/skiFree:

_1. Download SkiFree from the site: http://ski.ihoc.net/#download

_2. Create a folder on your system for the game - put the game files into it.

![](http://i.imgur.com/P3g5a0J.png) 

_3. We're going to add a python runner for the game, this is because we use
   'loaders' to run our entries - think of them kind of like a wrapper to 
    extract, install dependencies, anything we want, really. In this case,
    we just want to run the game, so the loader is simple.
  Create a "run.py" text file in our directory write the following:

  ![](http://i.imgur.com/fLZKepH.png)  

  This script will run when the game is ready to be played.

_4.We should have an icon for our selection menu, any image will do - just name it icon (e.g. icon.png, icon.jpg)

_5.We might want a preview video to show some gameplay or other interesting stuff (not required), name the video preview.mp4
Sometimes you can find short videos from youtube and download them, but an alternative is using Fraps and the batch file in utils/previewgen to make an mp4.

_6.Next, we will need an info.json file, use any json editor to ensure you make valid json - I use this:http://jsonformatter.curiousconcept.com/

The json format is pretty straightforward - although most values are not required, it looks the best if we have them.
The example looks like this.

![](http://i.imgur.com/UdqCWWH.png)

One entry to note is 'loader', this allows the frontend to prefer a loader for this entry over another (the frontend will pick the first loader it sees for this system + native platform you're running this on if this isn't specified).

_7.After that, zip up the game data and run.py into a zip file - the directory will look like this and is ready for upload.

![](http://i.imgur.com/PJZp72N.png)

![](http://i.imgur.com/hocOfsT.png)

![](http://i.imgur.com/ZCzzuKX.png)

The biggest thing missing from the tutorial is the PC Windows loader - essentially, the thing that will extract the game and pass control to the run.py file, I have included one in the examples under Loader/win/pc_windows.zip . I also wrote a few other loaders for snes (higan), psx (mednafen), PS2 (pcsx2), and GameCube (dolphin), and DS (desmume) which can deal with 7zipped files, extract items, etc. I'll upload them into the examples as well if there's interest.

Note: You can actually have as many zips or 7zips as you want (in case you want to add patches, updates, updates to the run.py file, etc.). I normally put my game data in separate directories from the run.py itself - up to you, really.
The files will be read in alphabetical order and the data will overwrite anything previously, so feel free to overlay patch after patch :)

After that, simply upload to GDrive/Onedrive and it will be available on the frontend. If this is your first entry, see the "Instructions - Share With Someone" section above to get the root cFE folder ID (the folder with systems in it such as "PC Windows" in our example and add the id to your sources.txt file (see Getting Started - Add Sources)

Entries are pulled every time you refresh the system page - if your friends add a game or rom to the respective system, you'll have immediate access. Also, you can take advantage of instant editing such as modifying the info.json file in onedrive and having the metadata instantly update.









