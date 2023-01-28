import os
import sys

# constants declaration
import pygame

GAME_NAME = 'boss rush 2023'

WIDTH = 1000  # width of the screen
HEIGHT = 850  # height of the screen
SCREEN_RECT = pygame.Rect(0, 0, WIDTH, HEIGHT)
SCREEN_COLLISION_RECT = SCREEN_RECT.inflate(100, 100)

VIEWPORT_OFFSET = [0, 0, 50, 10]  # left right top bottom
VIEWPORT_RECT = pygame.Rect(
    VIEWPORT_OFFSET[0],
    VIEWPORT_OFFSET[2],
    WIDTH - VIEWPORT_OFFSET[0] - VIEWPORT_OFFSET[1],
    HEIGHT - VIEWPORT_OFFSET[2] - VIEWPORT_OFFSET[3]
)
BG_COlOR = (247, 213, 147)
TEXT_COLOR = '#511309'
VOLUME = 100  # sound volume
FPS = 60
ASSETS = 'assets'

SONG_FINISHED_EVENT = pygame.event.custom_type()

SCORE_ADD_RATE = 5


# for handling global objects

class Globals:
    _global_dict = {}

    @classmethod
    def set_global(cls, key, value):
        cls._global_dict[key] = value

    @classmethod
    def get_global(cls, key):
        return cls._global_dict.get(key)

    @classmethod
    def pop_global(cls, key):
        try:
            cls._global_dict.pop(key)
        except KeyError:
            pass


# for closing pyinstaller splash screen if loaded from bundle

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle')
    ASSETS = os.path.join(sys._MEIPASS, ASSETS)
    try:
        import pyi_splash

        pyi_splash.close()
    except ImportError:
        pass
else:
    print('running in a normal Python process')
