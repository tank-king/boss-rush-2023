import pathlib
import time
from typing import Literal, Sequence

import pygame

from src.engine.config import WIDTH
from src.engine.objects import BaseObject, AppearSprite
from src.engine.utils import LoopingSpriteSheet, get_path, map_to_range, clamp, Timer

path = get_path('images', 'boss1')


class Component(BaseObject):
    def __init__(
            self,
            x, y,
            looping_sprite_sheet: LoopingSpriteSheet,
            appear=False, appear_vec=(0, 0), timer=0.1, speed=5,
            mask_offset=0, mask_speed=5.0, mask_length=10,
            blink_sequence=(),
            label='component'
    ):
        self.looping_sprite_sheet = looping_sprite_sheet
        self.appear = appear
        self.appear_sprite = AppearSprite(self.looping_sprite_sheet.images[0], appear_vec, timer, speed)
        super(Component, self).__init__(x, y)
        self.image = self.looping_sprite_sheet.image
        self.masks = pygame.mask.from_surface(self.image)
        self.outline = self.masks.outline(1)
        self._c = 0
        self.c = 0
        self._started = False
        self._draw_outline = False
        self._outline_done = False
        self.masking_offset = mask_offset
        self.max_mask_length = len(self.outline) // 4
        self.max_mask_length = mask_length
        self.mask_speed = mask_speed
        self.outline_animation_callback = None
        self.blink_timer = Timer('inf', reset=True)
        # self.blink_timer.set_callback(self.toggle_visibility)
        self.blink_sequence: list = list(blink_sequence)
        self.visible = True
        self.surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.label = label

    def start(self):
        self._started = True
        # self.add_blink_sequence(*self.get_blink_sequence(0.1, 5), 0.5, 0.5, *self.get_blink_sequence(0.1, 5), clear=True)
        # self.add_blink_sequence(0.1, 0.1, 0.5)
        if self.blink_sequence:
            self.add_blink_sequence(*self.blink_sequence, clear=True)

    @staticmethod
    def get_blink_sequence(interval, count):
        return [interval] * count * 2

    @property
    def width(self):
        return self.looping_sprite_sheet.images[0].get_width()

    @property
    def height(self):
        return self.looping_sprite_sheet.images[0].get_height()

    @property
    def size(self):
        return self.width, self.height

    @property
    def outline_done(self):
        return self._outline_done

    @property
    def outline_animation_running(self):
        return self._draw_outline

    @property
    def rect(self) -> pygame.Rect:
        return self.looping_sprite_sheet.image.get_rect()

    @staticmethod
    def bezier_blend(t):
        return t * t * (3.0 - 2.0 * t)

    def toggle_visibility(self):
        self.visible = not self.visible

    def add_blink_sequence(self, *args, clear=False):
        if clear:
            self.blink_sequence = list(args)[1:]
            self.blink_timer = Timer(args[0])
        else:
            self.blink_sequence.extend(args)

    def do_outline_animation(self, mask_speed=None, mask_offset=None, mask_length=None, callback=None):
        self._draw_outline = True
        self._outline_done = False
        self._c = 0
        self.c = 0
        if mask_speed:
            self.mask_speed = mask_speed
        if mask_offset:
            self.masking_offset = mask_offset
        if mask_length:
            self.max_mask_length = mask_length
        if callback:
            self.outline_animation_callback = callback

    def update(self, events: list[pygame.event.Event]):
        if self._started:
            if self.appear and not self.appear_sprite.done:
                self.appear_sprite.update(events)
            else:
                pass
        if self._draw_outline:
            self._c += self.mask_speed
            self.c = int(self._c)
            mid = len(self.outline) // 2
            if self.c > mid * 2:
                self._draw_outline = False
                if self.outline_animation_callback:
                    self.outline_animation_callback()
                self.start()
        if self.blink_sequence and self._started:
            if self.blink_timer.timeout == 'inf':
                self.blink_timer.set_timeout(self.blink_sequence.pop(0))
                self.blink_timer.reset()
                # self.blink_sequence.pop(0)
            elif self.blink_timer.tick:
                self.toggle_visibility()
                self.blink_timer.set_timeout(self.blink_sequence.pop(0))
                self.blink_timer.reset()

    @staticmethod
    def draw_points(points, surf, offset=(0, 0)):
        points = [
            [i[0] + offset[0], i[1] + offset[1]] for i in points
        ]
        if len(points) >= 2:
            pygame.draw.lines(surf, 'white', False, points, 5)

    def draw(self, surf: pygame.Surface):
        if self._started and self.visible:
            if self.appear and not self.appear_sprite.done:
                image = self.appear_sprite.image
                surf.blit(image, (self.x - image.get_width() // 2, self.y - image.get_height() // 2))
                # self.appear_sprite.draw(surf)
            else:
                self.looping_sprite_sheet.draw(surf, self.x, self.y)
        if self._draw_outline:
            points = self.outline[self.c + self.masking_offset: self.c + self.max_mask_length + self.masking_offset]
            self.draw_points(points, self.surf)
            points = self.outline[self.masking_offset - self.c - self.max_mask_length: self.masking_offset - self.c]
            self.draw_points(points, self.surf)
            if self.c + self.masking_offset >= len(self.outline):
                c = len(self.outline) - self.c
                points = self.outline[max(0, self.masking_offset - c - self.max_mask_length): self.masking_offset - c]
                self.draw_points(points, self.surf)
            surf.blit(self.surf, self.surf.get_rect(center=(self.x, self.y)))
            self.surf.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_SUB)


class ConnectedComponentSystem(BaseObject):
    def __init__(
            self,
            x, y,
            components_and_relative_pos: dict[Component, Sequence] = None,
            blink_sequence=()
    ):
        super(ConnectedComponentSystem, self).__init__(x, y)
        self.components = []
        if components_and_relative_pos is None:
            components_and_relative_pos = {}
        for i, j in components_and_relative_pos.items():
            i.pos = [x + j[0], y + j[1]]
            self.components.append(i)
        # self.components_and_relative_pos = components_and_relative_pos
        self.blink_timer = Timer('inf', reset=True)
        # self.blink_timer.set_callback(self.toggle_visibility)
        self.blink_sequence: list = list(blink_sequence)
        self.visible = True

    def toggle_visibility(self):
        self.visible = not self.visible

    def add_blink_sequence(self, *args, clear=False):
        if clear:
            self.blink_sequence = list(args)[1:]
            self.blink_timer = Timer(args[0])
        else:
            self.blink_sequence.extend(args)

    def get_component(self, label):
        for i in self.components:
            if i.label == label:
                return i

    def move(self, dx, dy):
        for i in self.components:
            i.x += dx
            i.y += dy
        self.x += dx
        self.y += dy

    def move_to(self, x, y):
        dx, dy = x - self.x, y - self.y
        self.move(dx, dy)

    @property
    def rect(self) -> pygame.Rect:
        return self.components[0].rect.unionall([i.rect for i in self.components[1:]])

    def update(self, events: list[pygame.event.Event]):
        for i in self.components:
            i.update(events)
        if self.blink_sequence:
            if self.blink_timer.timeout == 'inf':
                self.blink_timer.set_timeout(self.blink_sequence.pop(0))
                self.blink_timer.reset()
                # self.blink_sequence.pop(0)
            elif self.blink_timer.tick:
                self.toggle_visibility()
                self.blink_timer.set_timeout(self.blink_sequence.pop(0))
                self.blink_timer.reset()

    def draw(self, surf: pygame.Surface):
        if not self.visible:
            return
        for i in self.components:
            i.draw(surf)


class Boss1_1(BaseObject):
    def __init__(self, x=WIDTH // 2, y=150):
        super(Boss1_1, self).__init__(x, y)
        self.pos = pygame.Vector2(self.x, self.y)
        self.scale = 5
        self.base_sheet = LoopingSpriteSheet(path / 'base.png', 1, 6, scale=self.scale + 2)
        self.base = Component(
            *self.pos,
            self.base_sheet,
            appear=False,
            mask_speed=2.32, mask_offset=self.base_sheet.width // 2, mask_length=30,
            # blink_sequence=[2.42, 0.05, 0.05, 0.1, 0.1, 0.35, 1.7] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
        )
        self.gun_image = LoopingSpriteSheet(path / 'gun1_2.png', 1, 6, scale=self.scale, timer=0.05)
        self.gun = Component(
            self.pos[0], self.pos[1] + self.base.height // 2 + self.gun_image.images[0].get_height() // 2,
            self.gun_image, appear=True, appear_vec=(0, -1), timer=0.01, speed=10,
        )
        self.side_gun_sprite_sheet = LoopingSpriteSheet(path / 'side-gun_1.png', 1, 5, scale=self.scale, timer=0.08)
        self.right_gun = Component(
            self.pos[0] + self.base.width // 2 + self.side_gun_sprite_sheet.width // 2, self.pos[1],
            self.side_gun_sprite_sheet, appear=True, appear_vec=(-1, -1), timer=0.01, speed=10,
            # blink_sequence=[3.67 - 1 - 0.02] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
        )
        self.left_gun = Component(
            self.pos[0] - self.base.width // 2 - self.side_gun_sprite_sheet.width // 2, self.pos[1],
            LoopingSpriteSheet(path / 'side-gun_1.png', 1, 5, flipped=(1, 0), scale=self.scale, timer=0.08),
            appear=True, appear_vec=(1, -1), timer=0.01, speed=10, mask_offset=self.side_gun_sprite_sheet.width,
            # blink_sequence=[3.67 - 1] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
        )
        self.gun.looping_sprite_sheet.pause()
        # self.base.add_blink_sequence(*self.get_blink_sequence(0.1, 5), 0.5, 0.5, *self.get_blink_sequence(0.1, 5), clear=True)
        self.base.do_outline_animation(callback=lambda: (self.left_gun.do_outline_animation(callback=self.gun.do_outline_animation), self.right_gun.do_outline_animation()))

    @property
    def rect(self) -> pygame.Rect:
        return self.gun_image.image.get_rect()

    def update(self, events):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.pos += [-5, 0]
        if keys[pygame.K_RIGHT]:
            self.pos += [5, 0]
        if keys[pygame.K_SPACE]:
            self.gun.looping_sprite_sheet.unpause()
        else:
            self.gun.looping_sprite_sheet.set_frame(0)
            self.gun.looping_sprite_sheet.pause()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self.gun.looping_sprite_sheet.unpause()
        self.base.update(events)
        self.right_gun.update(events)
        self.left_gun.update(events)
        self.gun.update(events)
        # if not self.base.outline_animation_running and not self.base.outline_done:
        #     self.base.do_outline_animation()
        # if self.base.outline_done:
        #     self.right_gun.do_outline_animation()
        #     self.left_gun.do_outline_animation()
        # if self.left_gun.outline_done and self.right_gun.outline_done:
        #     self.gun.do_outline_animation()

    def draw(self, surf: pygame.Surface):
        self.base.draw(surf)
        self.gun.draw(surf)
        # self.right_gun.draw(surf, self.pos[0] + self.base.width // 2 + self.right_gun.width // 2,
        #                     self.pos[1])
        self.right_gun.draw(surf)
        self.left_gun.draw(surf)


class Boss1(ConnectedComponentSystem):
    def __init__(self, x=WIDTH // 2, y=150):
        scale = 5
        pos = (x, y)
        base_sheet = LoopingSpriteSheet(path / 'base.png', 1, 6, scale=scale + 2)
        base = Component(
            *pos,
            base_sheet,
            appear=False,
            mask_speed=2.32, mask_offset=base_sheet.width // 2, mask_length=30,
            # blink_sequence=[2.42, 0.05, 0.05, 0.1, 0.1, 0.35, 1.7] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
            label='base'
        )
        gun_image = LoopingSpriteSheet(path / 'gun1_2.png', 1, 6, scale=scale, timer=0.05)
        gun = Component(
            pos[0], pos[1] + base.height // 2 + gun_image.images[0].get_height() // 2,
            gun_image, appear=True, appear_vec=(0, -1), timer=0.01, speed=10,
            label='gun'
        )
        side_gun_sprite_sheet = LoopingSpriteSheet(path / 'side-gun_1.png', 1, 5, scale=scale, timer=0.08)
        right_gun = Component(
            pos[0] + base.width // 2 + side_gun_sprite_sheet.width // 2, pos[1],
            side_gun_sprite_sheet, appear=True, appear_vec=(-1, -1), timer=0.01, speed=10,
            # blink_sequence=[3.67 - 1 - 0.02] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
            label='right-gun'
        )
        left_gun = Component(
            pos[0] - base.width // 2 - side_gun_sprite_sheet.width // 2, pos[1],
            LoopingSpriteSheet(path / 'side-gun_1.png', 1, 5, flipped=(1, 0), scale=scale, timer=0.08),
            appear=True, appear_vec=(1, -1), timer=0.01, speed=10, mask_offset=side_gun_sprite_sheet.width,
            # blink_sequence=[3.67 - 1] + Component.get_blink_sequence(0.1, 2) + [0.5, 0.1] + Component.get_blink_sequence(0.05, 6)
            label='left-gun'
        )
        gun.looping_sprite_sheet.pause()
        # base.add_blink_sequence(*get_blink_sequence(0.1, 5), 0.5, 0.5, *get_blink_sequence(0.1, 5), clear=True)
        base.do_outline_animation(callback=lambda: (left_gun.do_outline_animation(callback=gun.do_outline_animation), right_gun.do_outline_animation()))

        super(Boss1, self).__init__(x, y,
                                    {
                                        left_gun: [-base.width // 2 - side_gun_sprite_sheet.width // 2, 0],
                                        right_gun: [base.width // 2 + side_gun_sprite_sheet.width // 2, 0],
                                        gun: [0, base.height // 2 + gun_image.image.get_height() // 2],
                                        base: [0, 0]
                                    },
                                    blink_sequence=[11.5, 0.05] + Component.get_blink_sequence(0.05, 4) + [0.55] + Component.get_blink_sequence(0.02, 10)
                                    )

    def update(self, events: list[pygame.event.Event]):
        super(Boss1, self).update(events)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.move(-5, 0)
        if keys[pygame.K_RIGHT]:
            self.move(5, 0)
        if keys[pygame.K_SPACE]:
            self.get_component('gun').looping_sprite_sheet.unpause()
        else:
            pass
            # self.get_component('gun').looping_sprite_sheet.set_frame(0)
            # self.get_component('gun').looping_sprite_sheet.pause()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self.get_component('gun').looping_sprite_sheet.unpause()
