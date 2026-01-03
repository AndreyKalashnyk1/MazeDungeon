import pygame
import os
from typing import Dict, Optional
from constants import resource_path

class SoundManager:
    def __init__(self, sounds_dir: str = "sounds"):
        pygame.mixer.init()
        
        self.sounds_dir = resource_path(sounds_dir)
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music = None
        self.music_enabled = True
        self.sfx_enabled = True
        self._load_sounds()

    def _load_sounds(self):

        sound_files = {
            "menu_music": "menu_music.wav",
            "footstep": "footstep.wav",
            "enemy_attack": "enemy_attack.wav",
            "damage": "damage.wav",
            "collect_key": "collect_key.wav",
            "collect_artifact": "collect_artifact.wav",
            "coin_pickup": "coin_pickup.wav",
            "artifact_weapon": "artifact_weapon.wav",
            "fire": "fire.wav",
            "victory": "victory.wav",
            "defeat": "defeat.wav",
        }

        for name, filename in sound_files.items():
            path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception:
                    pass

    def play_sound(self, sound_name: str, loops: int = 0):
        if not self.sfx_enabled or sound_name not in self.sounds:
            return
        try:
            self.sounds[sound_name].play(loops=loops)
        except Exception:
            pass

    def play_music(self, music_name: str, loops: int = -1):
        if not self.music_enabled or music_name not in self.sounds:
            return
        try:
            pygame.mixer.music.stop()
            path = os.path.join(self.sounds_dir, f"{music_name}.wav")
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=loops)
            self.current_music = music_name

        except Exception:
            pass

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None
    
    def stop_sound(self, sound_name: str):
        if sound_name in self.sounds:
            self.sounds[sound_name].stop()

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()

    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled

    def set_volume(self, sound_name: str, volume: float):
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(max(0.0, min(1.0, volume)))

    def set_music_volume(self, volume: float):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
