import math
import os.path
import pathlib
import time
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pygame

# FONT = os.path.abspath(os.path.join(ASSETS, 'ARCADECLASSIC.TTF'))
from src.engine.config import ASSETS

FONT = 'consolas'


def clamp(value, mini, maxi):
    """Clamp pos between mini and maxi"""
    if value < mini:
        return mini
    elif maxi < value:
        return maxi
    else:
        return value


def distance(p1, p2):
    """Get distance between 2 points"""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def map_to_range(value, from_x, from_y, to_x, to_y):
    """map the pos from one range to another"""
    return clamp(value * (to_y - to_x) / (from_y - from_x), to_x, to_y)


@lru_cache(maxsize=100)
def load_image_with_cache(path: str, alpha: bool = True, scale=1.0, color_key=None):
    img = pygame.image.load(path)
    img = pygame.transform.scale_by(img, scale)
    if color_key:
        img.set_colorkey(color_key)
    if alpha:
        return img.convert_alpha()
    else:
        return img.convert()


def get_path(*args):
    path = pathlib.Path(__file__).parent.parent.parent / ASSETS
    for i in args:
        path /= i
    return path


def load_image(path: str, alpha: bool = True, scale=1.0, color_key=None):
    img = pygame.image.load(path)
    img = pygame.transform.scale_by(img, scale)
    if color_key:
        img.set_colorkey(color_key)
    if alpha:
        return img.convert_alpha()
    else:
        return img.convert()


@lru_cache(maxsize=10)
def font(size):
    return pygame.font.SysFont(FONT, size)


@lru_cache(maxsize=100)
def text(msg, size=50, color=(255, 255, 255), aliased=True):
    return font(size).render(str(msg), aliased, color)


class Timer:
    def __init__(self, timeout=0.0, reset=True):
        self.timeout = timeout
        self.timer = time.time()
        self.paused_timer = time.time()
        self.paused = False
        self._reset = reset
        self._callback = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def set_callback(self, callback):
        self._callback = callback

    def reset(self):
        self.timer = time.time()

    def pause(self):
        self.paused = True
        self.paused_timer = time.time()

    def resume(self):
        self.paused = False
        self.timer -= time.time() - self.paused_timer

    @property
    def elapsed(self):
        if self.paused:
            return time.time() - self.timer - (time.time() - self.paused_timer)
        return time.time() - self.timer

    @property
    def tick(self):
        if self.timeout == 'inf':
            return False
        if self.elapsed > self.timeout:
            if self._reset:
                self.reset()  # reset timer
            else:
                self.timeout = 'inf'
            if self._callback:
                self._callback()
            return True
        else:
            return False


class SpriteSheet:
    """
    Class to load sprite-sheets
    """

    def __init__(self, sheet, rows, cols, images=None, alpha=True, scale=1.0, flipped=(0, 0), color_key=None):
        self._sheet = load_image(sheet, scale=scale) if isinstance(sheet, str) or isinstance(sheet, Path) else sheet
        self._r = rows
        self._c = cols
        self._flipped = flipped
        self._images = images if images else rows * cols
        self._alpha = alpha
        self._scale = scale
        self._color_key = color_key
        self._rects = []
        if flipped:
            self._sheet = pygame.transform.flip(self._sheet, *flipped)

    def __str__(self):
        return f'SpriteSheet Object <{self._sheet.__str__()}>'

    @property
    def surf(self):
        return self._sheet

    def get_rects(self):
        if not self._rects:
            raise Exception('Images not loaded yet from sprite sheet. Call get_images to load images first.')
        return self._rects

    def get_images(self):
        w = self._sheet.get_width() // self._c
        h = self._sheet.get_height() // self._r
        images = []
        for i in range(self._r * self._c):
            rect = pygame.Rect(i % self._c * w, i // self._c * h, w, h)
            self._rects.append(rect)
            images.append(self._sheet.subsurface(rect))
        images = images[0:self._images]
        if self._color_key is not None:
            for i in images:
                i.set_colorkey(self._color_key)
        if self._alpha:
            for i in images:
                i.convert_alpha()
        else:
            for i in images:
                i.convert()
        return images


class LoopingSpriteSheet:
    def __init__(self, sheet, rows, cols, images=None, alpha=True, scale=1.0, flipped=(0, 0), color_key=None, timer=0.1,
                 mode: Literal['center', 'topleft'] = 'center'):
        self.timer = Timer(timeout=timer)
        self.images = SpriteSheet(sheet, rows, cols, images, alpha, scale, flipped, color_key).get_images()
        self.c = 0
        self.mode = mode
        self.paused = False

    @property
    def width(self):
        return self.images[0].get_width()

    @property
    def height(self):
        return self.images[0].get_height()

    @property
    def size(self):
        return self.width, self.height

    @property
    def image(self):
        return self.images[self.c]

    def set_frame(self, frame):
        self.c = frame
        self.c %= len(self.images)

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def draw(self, surf: pygame.Surface, x, y, angle=0, size=1):
        if not self.paused:
            if self.timer.tick:
                self.c += 1
                self.c %= len(self.images)
        img = self.image
        if size != 1:
            img = pygame.transform.scale_by(img, size)
        if angle != 0:
            img = pygame.transform.rotate(img, angle)
        if self.mode == 'center':
            surf.blit(img, img.get_rect(center=(x, y)))
        else:
            surf.blit(img, (x, y))
