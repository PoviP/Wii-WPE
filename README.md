# Wii WPE
Software for Custom Wii home menu by LillyKyu

HOW TO USE

Due to antiviruses being rude, it's recommended that you avoid downloading the actual app. Instead download Source code (.zip) and build the app yourself via Python/cmd with the guide below.

Any changes you make to the "Apps" will be immediate, no need to restart or reconfigure anything, try it as you go!

FUNCTIONS

"Function" Checkbox - This is used when you're using a command rather than a path to an exe or similar.
"Autostart on login" - Will create a shortcut in \AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup to make sure the app starts (minimized) when you start your computer. Simply uncheck to get rid of the shortcut.
"Save Configuration" - Creates/updates your "config.json" file, making sure to keep all your settings even if the app closes.
"Minimizing app" - You can minimize the app to your System tray (bottom right corner) by simply closing the window with the (X) like usual.
"Quitting the app" - You can quit the app either by clicking the Exit button, or by right clicking on the app in the system tray and clicking Quit.

PATH TYPES

Log file Path: This should be the path to your log file in Wallpaper Engine, default location is C:/Program Files (x86)/Steam/steamapps/common/wallpaper_engine/log.txt, you can use the "browse" button to input it.

SHORTCUTS - For a normal exe file, simply put in the path and make sure NOT to use the "Function" checkbox.
    
Examples:

C:\Program Files (x86)\Steam\steam.exe

C:\Program Files\Mozilla Firefox\firefox.exe

FUNCTIONS - Things like steam apps or websites are functions and will need a "start" at the beginning, as well as the function checkbox ticked.
    
Examples (With function checkbox ticked):

start steam://rungameid/367520 

start https://www.youtube.com

OPEN FILE IN SPECIFIC SOFTWARE - Sometimes you'll want to open a file etc in a specific software. You'll then need the path to firstly the software that you want to open the file in, then the file itself.
    
Example (With function checkbox ticked):
    
start "" "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" "C:\Users\Povve\Downloads\wiishop.mp3"





DO IT YOURSELF

You can make this EXE yourself if you're not crazy enough to launch random EXE files from the internet.
You'll need:

Python - https://www.python.org/downloads/ Make sure you enable PATHS during installation

You can install all dependencies with this CMD command:

pip install pyinstaller winshell pillow pystray pywin32


From the Github Repo you'll need source.py, source.spec, wiiWPE.ico, and icon.png

If you want to make your own .spec file, make sure to add "icon='wiiWPE.ico'," to the EXE and changing the name to WiiWPE, and "hiddenimports=['pystray._win32', 'PIL._imagingtk', 'PIL', 'PIL.ImageTk', 'winshell', 'win32con', 'win32file']," to hiddenimports.

Once everything is downloaded and installed, go through the source.py code and mess around til you're satisfied, then in CMD cd into the directory where you have all the code:

cd C:\path\to\where you have all the scripts\

pyinstaller source.spec

Once it's done, it'll create a dist directory where you have to manually add the icon.png, then start the program and roll.
