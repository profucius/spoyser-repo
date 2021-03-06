#
#      Copyright (C) 2014 Sean Poyser
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
#  The code was originally based on the XBMC Last.FM - SlideShow by divingmule
#  (script.image.lastfm.slideshow) also released under the 
#  GNU General Public License
#

import urllib
import urllib2
import os
import xbmcaddon
import xbmc
import xbmcgui
import sys

import random
import re


#if sys.version_info >=  (2, 7):
#    import json
#else:
#    import simplejson as json 

import json
if not 'load' in dir(json):
    import simplejson as json

ADDONID   = 'script.image.music.slideshow'
ADDON     = xbmcaddon.Addon(id=ADDONID)
HOME      = ADDON.getAddonInfo('path')
ICON      = os.path.join(HOME, 'icon.png')
GETSTRING = ADDON.getLocalizedString
TITLE     = GETSTRING(30000)

global MODULES
MODULES = None



def log(text):
    try:
        output = '%s : %s' % (ADDONID, text)
        print output
        xbmc.log(output, xbmc.LOGDEBUG)
    except:
        pass

def Start():
    Restart()


def Restart():
    Reset()

    if not xbmc.Player().isPlayingAudio():
        xbmc.executebuiltin("XBMC.Notification("+TITLE+","+GETSTRING(30001)+",5000,"+ICON+")")      
        #Reset()
        return

    quit = False #need to work out how to tell that user has quit slideshow using stop (probably use a keymap - override STOP)
    if quit:
        Reset()
        return

    artist = GetArtist()

    if artist != '':
        Initialise()

    while True:
        xbmc.sleep(1000)
        if artist == '' or artist != GetArtist():
            break
        if not xbmc.Player().isPlayingAudio():
            break 

    Restart()


def Reset():
    players = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method":"Player.GetActivePlayers", "id": 1}'))
    p = players['result']

    id = -1
    for player in p:
        if player['type'] == 'picture':
            id = player['playerid']
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.Stop", "params": {"playerid":%i}, "id": 1}' % id)

    if id != -1:
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid":%i}, "id": 1}' % id)


def AddImages(images):
    items =[]
    for image in images:
        if not xbmc.Player().isPlayingAudio():
            return
        if '\'' in image:
            continue
        image = urllib.unquote_plus(image)    
        item  = '{ "jsonrpc": "2.0", "method": "Playlist.Add", "params": { "playlistid": 2 , "item": {"file": "%s"} }, "id": 1 }' % image
        try:
            items.append(item.encode('ascii'))
            xbmc.executeJSONRPC(str(items[-1]).replace("'",""))
        except:
            pass 

    log('Adding - %d valid images ' % len(items))
    

def GetModuleImages(module, artist = None):
    images = []

    if not artist:
        artist = GetArtist()

    if artist == '':
        return images

    if not MODULES:
        ImportModules()

    try:
        if module.upper() == 'ALL':
            modules = random.sample(MODULES, len(MODULES))
            for module in modules:
                m = GetModule(module)
                images += m.GetImages(artist)
        else:
            module = GetModule(module)
            if module:
                images = module.GetImages(artist)
    except:
        pass

    return images


def GetImages(artist):
    module = ADDON.getSetting('SOURCE')
    images = GetModuleImages(module, artist)

    log('Total number of images found = %d' % len(images))

    #if len(images) > 50:
    #    images = images[:50]

    random.shuffle(images)
    #log(images)
    return images


def Initialise():
    artist = GetArtist()

    log("Initialising slideshow for %s" % artist)

    #don't do notification if playing CD - causes XBMC to lockup
    notify = True
    try:
        file = xbmc.Player().getPlayingFile()
        if file.startswith('cdda'):
            notify = False
    except:
        pass

    if notify:
        xbmc.executebuiltin("XBMC.Notification("+TITLE+","+GETSTRING(30004)+" "+artist.replace(',', '')+",5000,"+ICON+")")        

    images = GetImages(artist)

    if not ShowImages(images, artist):
        Reset()

        
def ShowImages(images, artist):  
    xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid":2}, "id": 1}')
    if len(images) == 0:
        xbmc.executebuiltin("XBMC.Notification("+TITLE+","+GETSTRING(30002)+" "+artist+",5000,"+ICON+")")
        return False

    while len(images) > 5:
        AddImages(images[:5])
        if artist != GetArtist():
            return True
        if not DoPlaylist():
            return True
        images = images[5:]

    AddImages(images)

    return True        


def DoPlaylist(): 
    playlist = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.GetItems", "params": {"playlistid":2}, "id": 1}'))

    try:
        if playlist['result']['limits']['total'] > 0:
            players = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}'))
            found = False

            for i in players['result']:
                if i['type'] == 'picture':
                    found = True
                else: continue

            if not found:
                play = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open","params":{"item":{"playlistid":2}} }')
    except:
        return False

    return True       


def GetArtist():
    artist = ''

    try:
        artist = xbmc.Player().getMusicInfoTag().getArtist()
    except:
        pass
        
    if len(artist) < 1: 
        try:    artist = xbmc.Player().getMusicInfoTag().getTitle().split(' - ')[0]
        except: pass

    return artist


def TestModule(module, artist):
    images = []

    print '*************************************************'
    print 'script.image.music.slideshow Slideshow TEST'
    print 'Search %s for %s' % (module, artist)

    images = GetModuleImages(module, artist)

    print '**** Total number of images found = %d ****' % len(images)
    print images
    print '**** Total number of images found = %d ****' % len(images)
    print '*************************************************'


def GetModule(name):
    try:    return MODULES[name]
    except: return None
        

def ImportModules():
    global MODULES
    MODULES = dict()

    libPath = os.path.join(HOME, 'lib')
    sys.path.insert(0, libPath)

    module = []

    import glob
    lib   = os.path.join(HOME, 'lib', '*.py')
    files = glob.glob(lib)
    for name in files:
        name = name.rsplit(os.sep, 1)[1]
        if name.rsplit('.', 1)[1] == 'py':
            module.append(name .rsplit('.', 1)[0])

    modules = map(__import__, module)

    for module in modules:
        MODULES[module.__name__] = module


def main():
    try:
        if xbmcgui.Window(10000).getProperty('script.image.music.slideshow.running') == 'true':
            return

        xbmcgui.Window(10000).setProperty('script.image.music.slideshow.running', 'true')
        xbmc.executebuiltin('ActivateWindow(10025)')
        Start()
    except Exception, e:        
        pass

    xbmcgui.Window(10000).setProperty('script.image.music.slideshow.running', 'false')


#TestModule('AllMusic', 'Europe')


if not xbmc.Player().isPlayingAudio():
    ADDON.openSettings()

elif __name__ == '__main__':
    main()