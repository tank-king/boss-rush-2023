from pathlib import Path

import pygame

from src.engine.config import *
from src.engine.scene import Scene
from src.engine.objects import BaseObject
from src.engine.sounds import SoundManager
from src.engine.utils import *
from src.objects.boss1 import Boss1


class Boss1Scene(Scene):
    def __init__(self, manager, name):
        super(Boss1Scene, self).__init__(manager, name)
        self.boss = Boss1()
        self.scale = 4
        self.sheet = SpriteSheet(Path(__file__).parent.parent.parent / 'assets' / 'fonts' / 'font1.png', 10, 10, color_key='black', scale=self.scale)
        self.letters = self.sheet.get_images()
        self.mappings = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '
        SoundManager.play_bg('boss1-intro', 0)
        self.loop = False
        # SoundManager.play_next_bg_with_fadeout('boss1-loop', -1, 0)
        self.timer = Timer('inf')

    def text(self, messages, surf, x, y):
        w, h = self.letters[0].get_size()
        width = 0
        height = 0
        for msg in messages:
            for i in msg.upper():
                letter = self.letters[self.mappings.index(i)]
                width += w
                surf.blit(letter, (x + width, y + height))
            width = 0
            height += h + 25

    def update(self, events: list[pygame.event.Event]):
        self.boss.update(events)
        if self.timer.elapsed >= 13.340 and not self.loop:
            self.loop = True
            SoundManager.play_bg('boss1-loop', -1)
            self.boss.get_component('gun').looping_sprite_sheet.unpause()
        # for e in events:
        #     if e.type == SONG_FINISHED_EVENT:
        #         if not self.loop:
        #             self.loop = True
        #             SoundManager.play_bg('boss1-loop', -1)
        #             self.boss.get_component('gun').looping_sprite_sheet.unpause()

    def draw(self, surf: pygame.Surface):
        self.boss.draw(surf)
        # self.text(['Boss RUSH', '2023'], surf, 50, HEIGHT // 2)
        # for i in range(20):
        #     surf.blit(self.letters[i], (50 + i * self.scale * 16, 450))
