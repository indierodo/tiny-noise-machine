"""Tiny Noise Machine by Rodo"""

import math
import os
import time
from json.decoder import JSONDecodeError
import json
from concurrent.futures import ThreadPoolExecutor

import pygame
import rumps
import Quartz

playing = False
settings = {}

file_path = "settings.json"
try:
    if not os.path.isfile(file_path):
        open(file_path, 'a', encoding="utf-8").close()
    else:
        with open(file_path, "r", encoding="utf-8") as settings_json:
            try:
                settings = json.load(settings_json)
            except json.JSONDecodeError:
                pass
except Exception as e:
    pass

def save_and_quit(sender):
    global settings
    
    with open("settings.json", "w", encoding="utf-8") as settings_json:
        json.dump(settings, settings_json)

    rumps.quit_application()

class TinyNoiseMachine(rumps.App):
    def __init__(self, name):
        super(TinyNoiseMachine, self).__init__(name)
        self.menu = ["Loading..."]

    def add_new_item(self, item):
        self.menu.add(item)

def check_screen_locked():
    while True:
        if screen_is_locked():
            pygame.mixer.pause()
        else:
            if playing:
                pygame.mixer.unpause()
        time.sleep(1)

def screen_is_locked():
    try:
        quartz_dict = Quartz.CGSessionCopyCurrentDictionary()
        return 'CGSSessionScreenIsLocked' in quartz_dict
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def play_pause(sender):
    global playing
    if playing:
        pygame.mixer.pause()
        sender.title = "Play"
    else:
        pygame.mixer.unpause()
        sender.title = "Pause"

    playing = not playing

def audio_player(title, audio_file, index):

    key = f"volume{index}"
    
    def set_volume(sender):
        new_volume = sender.value / 100
        channel.set_volume(new_volume)
        
        if new_volume < 0.01:
            channel.pause()
        elif new_volume >= 0.01:
            channel.unpause()

        global settings
        settings[key] = new_volume

    sound = pygame.mixer.Sound(audio_file)
    channel = pygame.mixer.Channel(index)
    channel.play(sound, loops=-1)
    channel.pause()
    channel.set_volume(0)

    global settings
    if key in settings:
        volume = float(settings[key])
        if volume >= 0.01:
            print("setting volume of", title, "to", volume)
            channel.set_volume(volume)
        else:
            volume = 0
    else:
        volume = 0

    slider_item = rumps.SliderMenuItem(
        value=volume*100,
        min_value=0,
        dimensions=(160, 30),
        callback=set_volume
    )

    title = audio_file.replace('.opus', '').replace('content/', '')

    print("creating menu for", title)

    return [title, [slider_item]]

def lazy_load_menu_items(app):
    audio_files = [f for f in os.listdir("content") if f.endswith(".opus")]
    audio_files.sort()

    print("start loading")
    players = [
        audio_player(audio_files[i], "content/" + audio_files[i], i)
        for i in range(len(audio_files))
    ]
    print("finished loading")

    del app.menu["Loading..."]
    del app.menu["Quit"]

    app.add_new_item(rumps.MenuItem("Play", play_pause))
    app.menu = players
    app.add_new_item(rumps.MenuItem("Quit", save_and_quit))
    app.title = "〰"
    app.update_menu()

    return True

if __name__ == "__main__":
    pygame.mixer.init()
    pygame.mixer.set_num_channels(26)
    app = TinyNoiseMachine("⏳")
    
    def start_lazy_load():
        time.sleep(1)  # Give the app a moment to start
        lazy_load_menu_items(app)

    # Start the lazy load in a separate thread
    ThreadPoolExecutor(max_workers=1).submit(start_lazy_load)
    ThreadPoolExecutor(max_workers=1).submit(check_screen_locked)
    app.run()