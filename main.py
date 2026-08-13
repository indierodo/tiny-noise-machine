"""Tiny Noise Machine by Rodo"""

from pathlib import Path
import time
import json
from concurrent.futures import ThreadPoolExecutor

import pygame
import rumps
import Quartz

playing = False
config = {}
audio_players = []
global_volume = 1.0
screen_locked = False
app_running = True
background_executor = ThreadPoolExecutor(max_workers=2)
sound_load_executor = ThreadPoolExecutor(max_workers=1)

GLOBAL_VOLUME_KEY = "global_volume"
MIN_AUDIBLE_VOLUME = 0.01

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
    global app_running, config
    app_running = False
    config_dir = Path.home() / "Library" / "com.indierodo.tinynoisemachine"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "settings.json"
    
    with open(config_file, "w", encoding="utf-8") as f:
        print("Writing to file", end=None)
        print(config)
        json.dump(config, f)

    background_executor.shutdown(wait=False)
    sound_load_executor.shutdown(wait=False)
    rumps.quit_application()

class TinyNoiseMachine(rumps.App):
    def __init__(self, name):
        super(TinyNoiseMachine, self).__init__(name)
        self.menu = ["Loading..."]

    def add_new_item(self, item):
        self.menu.add(item)

def check_screen_locked():
    global screen_locked
    while app_running:
        locked = screen_is_locked()
        if locked != screen_locked:
            screen_locked = locked
            update_all_player_states(load_active=not locked)
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
        playing = False
        update_all_player_states()
        sender.title = "Play"
    else:
        playing = True
        update_all_player_states(load_active=True)
        sender.title = "Pause"


def update_all_player_states(load_active=False):
    for player in audio_players:
        player.apply_playback_state(load_if_active=load_active)


def normalize_volume(value, default=0.0):
    try:
        volume = float(value)
    except (TypeError, ValueError):
        return default

    return max(0, min(volume, 1))


def get_saved_volume(key, default=0.0):
    return normalize_volume(config.get(key, default), default)


class AudioPlayer:
    def __init__(self, audio_file, index):
        self.title = Path(audio_file).stem.capitalize()
        self.audio_file_path = str(audio_file)
        self.index = index
        self.key = f"volume{index}"
        self.sound = None
        self.sound_load_future = None
        self.load_failed = False
        self.channel = pygame.mixer.Channel(index)
        self.volume = get_saved_volume(self.key)
        if self.volume < MIN_AUDIBLE_VOLUME:
            self.volume = 0

        self.slider_item = rumps.SliderMenuItem(
            value=self.volume * 100,
            min_value=0,
            dimensions=(160, 30),
            callback=self.set_volume
        )

    @property
    def effective_volume(self):
        return self.volume * global_volume

    def menu_item(self):
        return [self.title, [self.slider_item]]

    def load_sound_async(self):
        if self.sound is not None:
            return

        if self.sound_load_future is not None or self.load_failed:
            return

        print("loading", self.title)
        self.sound_load_future = sound_load_executor.submit(
            pygame.mixer.Sound,
            self.audio_file_path
        )
        self.sound_load_future.add_done_callback(self.finish_loading_sound)

    def finish_loading_sound(self, future):
        try:
            self.sound = future.result()
        except Exception as e:
            self.load_failed = True
            print(f"Unable to load {self.title}: {e}")
        finally:
            self.sound_load_future = None

        self.apply_playback_state()

    def should_play(self):
        return (
            playing
            and not screen_locked
            and self.volume >= MIN_AUDIBLE_VOLUME
            and global_volume >= MIN_AUDIBLE_VOLUME
        )

    def apply_playback_state(self, load_if_active=False):
        if load_if_active and self.should_play():
            self.load_sound_async()

        if self.sound is None:
            return

        self.channel.set_volume(self.effective_volume)
        if self.should_play():
            if not self.channel.get_busy():
                self.channel.play(self.sound, loops=-1)
            self.channel.unpause()
        else:
            self.channel.pause()

    def set_volume(self, sender):
        global config
        self.volume = normalize_volume(sender.value / 100)
        if self.volume < MIN_AUDIBLE_VOLUME:
            self.volume = 0

        config[self.key] = self.volume
        self.apply_playback_state(load_if_active=True)


def set_global_volume(sender):
    global config, global_volume
    global_volume = normalize_volume(sender.value / 100)
    if global_volume < MIN_AUDIBLE_VOLUME:
        global_volume = 0

    config[GLOBAL_VOLUME_KEY] = global_volume
    update_all_player_states(load_active=True)


def global_volume_menu_items():
    volume = get_saved_volume(GLOBAL_VOLUME_KEY, 1.0)
    if volume < MIN_AUDIBLE_VOLUME:
        volume = 0

    slider_item = rumps.SliderMenuItem(
        value=volume * 100,
        min_value=0,
        dimensions=(160, 30),
        callback=set_global_volume
    )

    return [rumps.MenuItem("Global Volume"), slider_item, rumps.separator], volume


def lazy_load_menu_items(app):
    global audio_players, global_volume
    content_dir = Path.home() / "Library" / "com.indierodo.tinynoisemachine" / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    supported_formats = ['.wav', '.mp3', '.ogg', '.opus', '.flac', '.aiff']
    audio_files = [f.name for f in content_dir.glob("*") if f.suffix.lower() in supported_formats]
    audio_files.sort()
    pygame.mixer.set_num_channels(max(26, len(audio_files)))
    audio_players = [
        AudioPlayer(content_dir / audio_file, i)
        for i, audio_file in enumerate(audio_files)
    ]
    player_menu_items = [player.menu_item() for player in audio_players]
    global_volume_items, global_volume = global_volume_menu_items()

    del app.menu["Loading..."]
    del app.menu["Quit"]

    app.menu = [
        rumps.MenuItem("Play", play_pause),
    ] + global_volume_items + player_menu_items
    app.add_new_item(rumps.MenuItem("Quit", save_and_quit))
    app.title = "〰"
    app.update_menu()

    return True

if __name__ == "__main__":
    pygame.mixer.init()
    app = TinyNoiseMachine("⏳")
    
    def start_lazy_load():
        time.sleep(1)  # Give the app a moment to start
        lazy_load_menu_items(app)

    load_or_create_config_file()
    # Start the lazy load in a separate thread
    background_executor.submit(start_lazy_load)
    background_executor.submit(check_screen_locked)
    app.run()
