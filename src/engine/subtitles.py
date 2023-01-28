import pygame

from src.engine.objects import BaseStructure
from src.engine.sounds import SoundManager
from src.engine.utils import Timer, text
from src.engine.config import WIDTH, HEIGHT
from typing import Union


class Subtitle:
    def __init__(self, name, time=None, size=35, pos=(WIDTH // 2, HEIGHT // 2), color='white', callback=None):
        self.timer = Timer(time if time and type(time) != str else max(len(name) * 0.25, 0))
        self._time = time
        self.done = False
        self.pos = pos
        self.callback = callback
        self.text = text(name, size, color)

    def update(self):
        if self.timer.tick:
            if self._time != 'inf':
                self.done = True
                if self.callback is not None:
                    self.callback()

    def draw(self, surf: pygame.Surface):
        rect = self.text.get_rect(center=self.pos)
        rect1 = rect.inflate(20, 20)
        pygame.draw.rect(surf, '#511309', rect1)
        pygame.draw.rect(surf, 'black', rect1, 2)
        surf.blit(self.text, rect)


class BlinkingSubtitle(Subtitle):
    def __init__(self, name, time=None, size=35, pos=(WIDTH // 2, HEIGHT // 2), color='white', callback=None, blink_timer=0.5):
        super().__init__(name, time, size, pos, color, callback)
        self.blink_timer = Timer(blink_timer)
        self.visible = True

    def update(self):
        if self.blink_timer.tick:
            self.visible = not self.visible
        super().update()

    def draw(self, surf: pygame.Surface):
        if not self.visible:
            rect = self.text.get_rect(center=self.pos)
            rect1 = rect.inflate(20, 20)
            pygame.draw.rect(surf, '#511309', rect1)
            pygame.draw.rect(surf, 'black', rect1, 2)
            return
        else:
            super().draw(surf)


def get_typed_subtitles(_text, _time=2, _time_diff=0.05, pos=None, callback=None):
    if pos is None:
        pos = (WIDTH // 2, HEIGHT // 2)
    subtitles = []
    for i in range(1, len(_text) - 2):
        subtitles.append(Subtitle(_text[0:i], _time_diff, pos=pos))
    subtitles.append(Subtitle(_text[0:-1], _time_diff, pos=pos, callback=callback))
    subtitles.append(Subtitle(_text, _time, pos=pos))
    return subtitles


class SubtitleManager(BaseStructure):
    def __init__(self):
        self.subtitles = [
            # Subtitle('yo', 1),
            # Subtitle('wassup', 1),
            # *get_typed_subtitles('this is a typed text')
        ]
        self.current_subtitle: Union[Subtitle, None] = None

    def clear(self):
        self.subtitles.clear()
        self.current_subtitle = None

    def add(self, subtitle: Subtitle):
        self.subtitles.append(subtitle)

    def add_multiple(self, subtitles: list[Subtitle]):
        for i in subtitles:
            self.add(i)

    def update(self):
        if self.current_subtitle:
            self.current_subtitle.update()
            try:
                if self.current_subtitle.done:
                    self.current_subtitle = None
                    try:
                        self.current_subtitle = self.subtitles.pop(0)
                        self.current_subtitle.timer.reset()
                        if type(self.current_subtitle) == Subtitle:
                            SoundManager.play('click')
                    except IndexError:
                        pass
            except Exception as e:
                print(e)
        else:
            try:
                self.current_subtitle = self.subtitles.pop(0)
                self.current_subtitle.timer.reset()
            except IndexError:
                pass

    def draw(self, surf: pygame.Surface):
        if self.current_subtitle:
            self.current_subtitle.draw(surf)
