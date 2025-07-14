"""Tiny Noise Machine by Rodo"""

import math
import os
from pathlib import Path
import time
from json.decoder import JSONDecodeError
import json
from concurrent.futures import ThreadPoolExecutor

import pygame
import rumps
import Quartz

playing = False
config = {}

def load_or_create_config_file():
    global config
    config_dir = Path.home() / "Library" / "com.indierodo.tinynoisemachine"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "settings.json"

    if not config_file.exists():
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{}\n")

    with open(config_file, "r", encoding="utf-8") as settings_json:
        config = json.load(settings_json)

def save_and_quit(sender):
    global config
    config_dir = Path.home() / "Library" / "com.indierodo.tinynoisemachine"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "settings.json"
    
    with open(config_file, "w", encoding="utf-8") as f:
        print("Writing to file", end=None)
        print(config)
        json.dump(config, f)

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
    title = Path(audio_file).stem.capitalize()
    audio_file_path = str(audio_file)

    key = f"volume{index}"
    
    def set_volume(sender):
        new_volume = sender.value / 100
        channel.set_volume(new_volume)
        
        if new_volume < 0.01:
            channel.pause()
        elif new_volume >= 0.01:
            channel.unpause()

        global config
        config[key] = new_volume

    sound = pygame.mixer.Sound(audio_file_path)
    channel = pygame.mixer.Channel(index)
    channel.play(sound, loops=-1)
    channel.pause()
    channel.set_volume(0)

    global config
    if key in config:
        volume = float(config[key])
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

    return [title, [slider_item]]

def lazy_load_menu_items(app):
    content_dir = Path.home() / "Library" / "com.indierodo.tinynoisemachine" / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    supported_formats = ['.wav', '.mp3', '.ogg', '.opus', '.flac', '.aiff']
    audio_files = [f.name for f in content_dir.glob("*") if f.suffix.lower() in supported_formats]
    audio_files.sort()
    players = []

    for i, audio_file in enumerate(audio_files):
        filename = content_dir / audio_file
        a_p = audio_player(audio_file, filename, i)
        players.append(a_p)

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

    load_or_create_config_file()
    # Start the lazy load in a separate thread
    ThreadPoolExecutor(max_workers=1).submit(start_lazy_load)
    ThreadPoolExecutor(max_workers=1).submit(check_screen_locked)
    app.run()
