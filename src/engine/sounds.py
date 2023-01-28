import pygame.mixer

from src.engine.config import Globals, SONG_FINISHED_EVENT
from src.engine.utils import get_path


class SoundManager:
    sounds = {
        'boss1-intro': ['boss1', 'intro.wav'],
        'boss1-loop': ['boss1', 'loop.wav'],
        # 'shoot': 'shoot.mp3',
        # 'click': 'click1.ogg',
        # 'hit': 'hit.ogg',
        # 'home_bg': 'game.ogg',
        # 'game_bg': 'game_bg_music.ogg',
        # 'shoot': 'shoot.wav',
        # 'slime': 'slime.wav'
    }
    # for i in range(1, 11):
    #     sounds[f'slime{i}'] = f'slime{i}.wav'

    sound_objects: dict[str, pygame.mixer.Sound] = {}
    bg_sound = 'bg.mp3'
    home_page_sound = ''

    VOLUME = 100

    bg_music = pygame.mixer.music
    bg_channel: pygame.mixer.Channel = None

    @classmethod
    def set_bg_volume(cls, volume):
        if Globals.get_global('speakers_init'):
            cls.bg_channel.set_volume(volume)

    @classmethod
    def load_sounds(cls):
        for i, j in cls.sounds.items():
            print('loading... ', i, get_path('sounds', *j if (isinstance(j, tuple) or isinstance(j, list)) else j))
            cls.sound_objects[i] = pygame.mixer.Sound(get_path('sounds', *j if (isinstance(j, tuple) or isinstance(j, list)) else j))
        # cls.sound_objects = {
        #     i: pygame.mixer.Sound(get_path('sounds', j)) for i, j in cls.sounds.items()
        # }
        for i in cls.sound_objects:
            cls.sound_objects[i].set_volume(cls.VOLUME / 100)
        cls.bg_music.set_volume(cls.VOLUME / 100)
        pygame.mixer.set_reserved(1)
        cls.bg_channel = pygame.mixer.Channel(0)

    @classmethod
    def play(cls, sound, loops=0, preload=True, volume=100):
        if Globals.get_global('speakers_init'):
            if preload:
                if sound in cls.sounds:
                    cls.sound_objects[sound].set_volume(volume / 100)
                    cls.sound_objects[sound].play(loops)
            else:
                if sound in cls.sounds:
                    s = pygame.mixer.Sound(get_path('sounds', cls.sounds[sound]))
                    s.set_volume(volume / 100)
                    s.play(loops)

    @classmethod
    def stop(cls, sound, fadeout=100):
        if Globals.get_global('speakers_init'):
            if sound in cls.sounds:
                cls.sound_objects[sound].fadeout(fadeout)

    @classmethod
    def play_bg(cls, sound, loops=-1, volume=100):
        if Globals.get_global('speakers_init'):
            if sound in cls.sounds:
                cls.bg_channel.set_volume(volume / 100)
                cls.bg_channel.play(cls.sound_objects[sound], loops=loops)
                cls.bg_channel.set_endevent(SONG_FINISHED_EVENT)
            else:
                cls.bg_music.load(sound)
                cls.bg_music.play(loops)
                cls.bg_music.set_volume(volume)

    @classmethod
    def play_next_bg_with_fadeout(cls, sound, loops=-1, fadeout=100, volume=100, type_hint='ogg'):
        if Globals.get_global('speakers_init'):
            if sound in cls.sounds:
                cls.bg_channel.set_volume(volume)
                cls.bg_channel.fadeout(fadeout)
                cls.bg_channel.queue(cls.sound_objects[sound], type_hint, loops)
    #
    # @classmethod
    # def bg_play(cls):
    #     pygame.mixer.music.play(-1)
    #
    # @classmethod
    # def bg_switch(cls, sound):
    #     pygame.mixer.music.load(sound)
