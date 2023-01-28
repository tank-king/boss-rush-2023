import random
from operator import attrgetter
from typing import Union, Callable

from src.engine.sounds import SoundManager
from src.engine.utils import *
from src.engine.config import *


class BaseObject:
    def __init__(self, x=0, y=0):
        self.x, self.y = x, y
        self.alive = True
        self.z = 0  # for sorting
        self.object_manager: Union[ObjectManager, None] = None

    @property
    def pos(self):
        return self.x, self.y

    @pos.setter
    def pos(self, position):
        self.x, self.y = position

    @property
    def rect(self) -> pygame.Rect:
        raise NotImplementedError

    def update(self, events: list[pygame.event.Event]):
        pass

    def adjust_pos(self):
        self.x = clamp(self.x, VIEWPORT_RECT.left + self.rect.w // 2, VIEWPORT_RECT.right - self.rect.w // 2)
        self.y = clamp(self.y, VIEWPORT_RECT.top + self.rect.h // 2, VIEWPORT_RECT.bottom - self.rect.h // 2)

    def draw(self, surf: pygame.Surface):
        pass


class AppearSprite(BaseObject):
    def __init__(self, sprite: pygame.Surface, vec=(0, 0), timer=0.1, speed=5):
        super().__init__()
        self.vec = vec
        self.timer = Timer(timer)
        self.speed = speed
        self.sprite = sprite
        self.surf = pygame.Surface(self.sprite.get_size(), pygame.SRCALPHA)
        self.c_x = 0
        self.c_v = 0
        self.x_done = False
        self.y_done = False

    def rect(self) -> pygame.Rect:
        return self.surf.get_rect()

    @property
    def done(self):
        return self.x_done and self.y_done

    @property
    def image(self):
        if self.x_done and self.y_done:
            return self.surf
        self.surf = pygame.Surface(self.sprite.get_size(), pygame.SRCALPHA)
        pos = [self.vec[0] * self.sprite.get_width(), self.vec[1] * self.sprite.get_height()]
        pos[0] -= self.c_x * self.vec[0]
        pos[1] -= self.c_v * self.vec[1]
        self.surf.blit(self.sprite, pos)
        return self.surf

    def update(self, events: list[pygame.event.Event]):
        if self.timer.tick:
            self.c_v += self.speed
            self.c_x += self.speed
            if self.c_x >= self.sprite.get_width():
                self.c_x = self.sprite.get_width()
                self.x_done = True
            if self.c_v >= self.sprite.get_height():
                self.c_v = self.sprite.get_height()
                self.y_done = True


class Player(BaseObject):
    control_mappings = {
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'up': pygame.K_UP,
        'down': pygame.K_DOWN
    }
    vec_mappings = {
        'none': [0, 0],
        'left': [-1, 0],
        'right': [1, 0],
        'up': [0, -1],
        'down': [0, 1]
    }
    angle_mappings = {
        'left': 180,
        'right': 0,
        'up': 90,
        'down': 270
    }

    intermission_config = {
        0: {
            'vel': 6,
            'bullet_timer': 0.2,
        },

        1: {
            'vel': 10,
            'bullet_timer': 0.1,
        },

        2: {
            'vel': 15,
            'bullet_timer': 0.1,
        }
    }

    TOTAL_LIVES = 3
    # lives = TOTAL_LIVES

    def __init__(self, x=WIDTH // 2, y=HEIGHT // 2, intermission=0):
        super().__init__()
        intermission_config = self.intermission_config[intermission]
        self.x = x
        self.y = y
        self.vel = intermission_config['vel']
        self.bullet_timer = Timer(intermission_config['bullet_timer'], reset=False)
        self.dir = 'none'
        # self.sheet = LoopingSpriteSheet(get_path('images', 'player_sheet_2.png'), 1, 3, 3, True, 3, timer=0.1)
        # self.image = load_image(get_path('images', 'player.png'), scale=2, color_key='white')
        self.c = 0
        self.color_timer = Timer(0.1)
        self.color_flag = True
        self.flash_counter = 0
        self.r = 0
        self.destroyed = False
        self.angle = 0
        self.moving = False
        self.scale = 1
        self.recoil_scale = 0
        self.score = 0
        self.lives = Globals.get_global('lives')
        self.is_playing = True
        self.is_intermission = Globals.get_global('intermission')

    @property
    def rect(self):
        return
        # return self.sheet.image.get_rect(center=(self.x, self.y)).inflate(-60, -40).move(0, 20)

    def set_intermission_config(self, intermission):
        intermission_config = self.intermission_config[intermission]
        self.vel = intermission_config['vel']
        self.bullet_timer = Timer(intermission_config['bullet_timer'], reset=False)

    def update(self, events: list[pygame.event.Event]):
        Globals.set_global('lives', self.lives)
        Globals.set_global('intermission', self.is_intermission)

        self.scale *= 0.9
        self.scale = clamp(self.scale, 1, 2)
        self.recoil_scale *= 0.9
        self.recoil_scale = clamp(self.recoil_scale, 0, 2)
        keys = pygame.key.get_pressed()
        if not self.alive:
            return
        self.moving = False
        if self.is_playing:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    for _dir, key in self.control_mappings.items():
                        if e.key == key:
                            self.dir = _dir
                if e.type == pygame.KEYUP:
                    for _dir, key in self.control_mappings.items():
                        if keys[key] and key != e.key:
                            self.dir = _dir
            if self.dir == 'none':
                for _dir, key in self.control_mappings.items():
                    if keys[key]:
                        self.dir = _dir
                        print(_dir)
                        break
            vec = self.vec_mappings[self.dir]
        else:
            vec = [0, 0]

        self.angle = 90

        if any(keys[i] for i in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]):
            self.x += self.vel * vec[0]
            self.y += self.vel * vec[1]
            self.adjust_pos()
            self.moving = True

        if self.is_playing:
            if self.bullet_timer.tick:
                self.launch()
        self.adjust_pos()

    def destroy(self):
        self.dir = 'none'
        self.is_playing = False
        # if not self.is_intermission:
        #     self.is_intermission = True
        # else:
        #     self.alive = False
        self.alive = False
        # if not self.is_intermission:
        #     self.is_intermission = True
        self.is_intermission = not self.is_intermission
        self.object_manager.add(
            Explosion(self.x,
                      self.y,
                      ('#511309', 'black', '#55241b', '#45283c'),
                      diff=45,
                      particles_per_line=15,
                      rate=5,
                      max_particle_size=7
                      )
        )

    def restart(self):
        self.alive = True
        self.is_playing = True
        # self.is_intermission = False

    def launch(self):
        self.bullet_timer.reset()
        self.object_manager.add(PlayerBullet(self.x, self.y, 'up', 0))
        self.scale = 1.0
        self.recoil_scale = 1.5
        SoundManager.play('shoot')

    def handle_collisions(self):
        pass

    def draw(self, surf: pygame.Surface):
        return
        # self.recoil_scale = 50
        # if self.alive:
        #     self.sheet.draw(surf, self.x, self.y + self.recoil_scale * 15, self.angle - 90, self.scale)
        # s = pygame.transform.rotate(self.image, self.angle - 90)
        # if self.alive:
        #     surf.blit(s, s.get_rect(center=(self.x, self.y)))


class Bug(BaseObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.sheet = LoopingSpriteSheet(get_path('images', 'minibug_sheet.png'), 1, 3, 3, True, 2, timer=0.2)
        self.appear_sprite = AppearSprite(pygame.transform.rotate(self.sheet.image, 180), vec=(0, -1), timer=0.05)
        # self.image = load_image(get_path('images', 'bug1.png'), scale=2, color_key='white')
        self.angle = 270
        self.vel = 1
        self.angle_timer = Timer(2)

    @property
    def rect(self) -> pygame.Rect:
        return self.sheet.image.get_rect(center=(self.x, self.y)).inflate(-15, -15)

    @property
    def score(self):
        if Globals.get_global('intermission'):
            return 50
        else:
            return 100

    def use_ai(self):
        return
        # if self.angle_timer.tick:
        #     self.angle = random.choice(range(0, 360, 90))

    def destroy(self):
        self.alive = False
        self.object_manager.add(
            Explosion(self.x, self.y, ('red', 'black'))
        )
        SoundManager.play(f'slime{random.randint(1, 10)}')

    def update(self, events: list[pygame.event.Event]):
        for i in self.object_manager.objects:
            if isinstance(i, PlayerBullet):
                if i.rect.colliderect(self.rect):
                    i.alive = False
                    self.destroy()
                    Globals.set_global('score_to_add', Globals.get_global('score_to_add') + self.score)
                    return
        self.use_ai()
        if self.appear_sprite.done:
            dx = math.cos(math.radians(self.angle)) * self.vel
            dy = -math.sin(math.radians(self.angle)) * self.vel
            self.x += dx
            self.y += dy
            if not SCREEN_COLLISION_RECT.colliderect(self.rect):
                self.alive = False
        if self.rect.bottom > SCREEN_RECT.bottom + 10:
            self.destroy()
            if self.object_manager.player.is_playing:
                self.object_manager.player.destroy()
        if self.rect.colliderect(self.object_manager.player.rect):
            self.destroy()
            if self.object_manager.player.is_playing:
                self.object_manager.player.destroy()
        self.appear_sprite.update(events)
        # self.adjust_pos()

    def draw(self, surf: pygame.Surface):
        if not self.appear_sprite.done:
            image = self.appear_sprite.image
            surf.blit(image, image.get_rect(center=(self.x, self.y)))
        else:
            self.sheet.draw(surf, self.x, self.y, self.angle - 90)
        # pygame.draw.rect(surf, 'black', self.rect, 2)
        # s = pygame.transform.rotate(self.image, self.angle - 90)
        # if self.alive:
        #     surf.blit(s, s.get_rect(center=(self.x, self.y)))


class BugHole(BaseObject):
    # surf = None

    def __init__(self, x, y, bug_count=5):
        super().__init__(x, y)
        # if self.surf is None:
        #     BugHole.surf = load_image(get_path('images', 'bug_hole.png'), scale=2)
        self.surf = load_image(get_path('images', 'bug_hole.png'), scale=2)
        self.appear_sprite = AppearSprite(self.surf, vec=(0, 1), timer=0.05, speed=5)
        self.c = 0
        self.surf.scroll(0, self.surf.get_height())
        self.scroll_timer = Timer(0.1)
        self.k = 2
        self.bugs = []  # keeps a reference to all bugs in the column
        self.destroy_timer = Timer(0.1)
        self.spawn_bugs = True
        self.destroy_all_bugs_in_col = False
        self.paused = False
        self.total_bug_count = bug_count
        self.bug_count = 0

    def pause(self):
        self.set_vel(0)
        self.destroy_bugs()

    def resume(self):
        self.set_vel(1)
        self.start_spawn()

    def spawn(self, bug_type: type):
        if self.spawn_done():
            return
            # self.alive = False
            # self.object_manager.add(
            #     Explosion(self.x, self.y, ('brown', 'black'))
            # )
        if self.spawn_bugs and self.appear_sprite.done:
            bug = bug_type(self.x, self.y + self.surf.get_height() // 2)
            self.object_manager.add(bug)
            self.bugs.append(bug)
            self.bug_count += 1

    def spawn_done(self):
        return self.bug_count >= self.total_bug_count

    def done(self):
        return self.spawn_done() and len(self.bugs) == 0

    def set_vel(self, vel):
        # apply a new velocity to all bugs launched from this hole
        for i in self.bugs:
            i.vel = vel

    def destroy_bugs(self):
        self.stop_spawn()
        self.destroy_timer.reset()
        self.destroy_all_bugs_in_col = True

    def start_spawn(self):
        self.spawn_bugs = True

    def stop_spawn(self):
        self.spawn_bugs = False

    @property
    def rect(self) -> pygame.Rect:
        return self.appear_sprite.image.get_rect(center=(self.x, self.y))

    @property
    def image(self):
        return self.appear_sprite.image
        # img = self.surf.copy()
        # img.scroll(0, self.c)
        # return img

    def update(self, events: list[pygame.event.Event]):
        self.appear_sprite.update(events)
        self.bugs = [i for i in self.bugs if i.alive]
        if self.destroy_all_bugs_in_col:
            if self.destroy_timer.tick:
                if self.bugs:
                    self.bugs.pop().destroy()
                    self.bug_count -= 1
                else:
                    self.destroy_all_bugs_in_col = False
        # k = self.k
        # if self.c < self.surf.get_height():
        #     # self.k *= -1
        #     if self.scroll_timer.tick:
        #         self.c += k
        #         self.surf.scroll(0, k)

    def draw(self, surf: pygame.Surface):
        image = self.image
        surf.blit(image, image.get_rect(center=(self.x, self.y)))
        # pygame.draw.rect(surf, 'brown', (self.x -))


class Boss(BaseObject):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.sheet = LoopingSpriteSheet(get_path('images', 'boss1.png'), 1, 3, 3, True, 2, timer=0.2)
        # self.image = load_image(get_path('images', 'bug1.png'), scale=2, color_key='white')
        self.angle = 270
        self.vel = 0
        self.angle_timer = Timer(2)

    @property
    def rect(self) -> pygame.Rect:
        return self.sheet.image.get_rect().inflate(-5, -5)

    def update(self, events: list[pygame.event.Event]):
        dx = math.cos(math.radians(self.angle)) * self.vel
        dy = -math.sin(math.radians(self.angle)) * self.vel
        self.x += dx
        self.y += dy
        self.adjust_pos()

    def draw(self, surf: pygame.Surface):
        self.sheet.draw(surf, self.x, self.y, self.angle - 90)
        # s = pygame.transform.rotate(self.image, self.angle - 90)
        # if self.alive:
        #     surf.blit(s, s.get_rect(center=(self.x, self.y)))


class PlayerBullet(BaseObject):
    dir = [0, -1]
    _image = None

    def __init__(self, x, y, _dir=None, vel_add=0):
        super().__init__()
        self.x = x
        self.y = y
        if _dir is not None:
            self.dx, self.dy = Player.vec_mappings[_dir]
            if vel_add != 0:
                self.dx += vel_add * self.dx
                self.dy += vel_add * self.dy
        else:
            self.dx, self.dy = self.dir
        self.angle = Player.angle_mappings[_dir]
        # print(self.dx, self.dy, 'yooo')
        self.vel = 10
        self.alive = True
        self.length = 20
        if self._image is None:
            self._image = load_image(get_path('images', 'bullet1.png'), True, 2)

    @property
    def image(self):
        return pygame.transform.rotate(self._image, self.angle - 90)

    @property
    def rect(self) -> pygame.Rect:
        return self.image.get_rect(center=(self.x, self.y))

    def update(self, events: list[pygame.event.Event]):
        # print(self.dx, self.dy)
        self.x += self.dx * self.vel
        self.y += self.dy * self.vel
        offset = 50
        if self.x > WIDTH + offset or self.x < -offset or self.y > HEIGHT + offset or self.y < -offset:
            self.alive = False

    def draw(self, surf: pygame.Surface):
        image = self.image
        surf.blit(image, image.get_rect(center=(self.x, self.y)))
        # pygame.draw.line(surf, (15, 109, 1), (self.x, self.y), (self.x + self.dx * length, self.y + self.dy * length), 5)


class Explosion(BaseObject):
    def __init__(self, x, y, colors, vec=(0, 0), diff=45, particles_per_line=3, rate=5, max_particle_size=5):
        super().__init__(x, y)
        self.colors = colors
        self.r = 0
        self.vec = vec
        self.diff = diff
        self.particles_per_line = particles_per_line
        self.rate = rate
        self.max_particle_size = max_particle_size

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 10, 10)

    def update(self, events: list[pygame.event.Event]):
        self.r += self.rate
        if self.r > 200:
            self.r = 200
            self.alive = False

    def draw(self, surf: pygame.Surface):
        # pygame.draw.rect(surf, 'white', (0, 0, 100, 100))
        draw_rect = pygame.draw.rect
        for i in range(0, 360, self.diff):
            for k in range(1, self.particles_per_line):
                x = k * self.r * math.cos(math.radians(i)) + self.r * k * self.vec[0]
                y = k * self.r * math.sin(math.radians(i)) + self.r * k * self.vec[1]
                color = self.colors[int(map_to_range(i, 0, 360, 0, len(self.colors)))]
                rect = (self.x + x, self.y + y, self.max_particle_size - k, self.max_particle_size - k)
                draw_rect(surf, color, rect)
                # draw_rect(surf, 'black', rect, 2)


class EntryAnimationObject(BaseObject):
    def __init__(self, x, y, colors, callback: Callable, vec=(0, 0), diff=45, particles_per_line=3, rate=5, max_particle_size=5):
        super().__init__(x, y)
        self.colors = colors
        self.r = 200
        self.vec = vec
        self.callback = callback
        self.diff = diff
        self.particles_per_line = particles_per_line
        self.rate = rate
        self.max_particle_size = max_particle_size

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 10, 10)

    def update(self, events: list[pygame.event.Event]):
        self.r -= self.rate
        if self.r < 0:
            self.r = 0
            self.callback()
            # if isinstance(self.object_type, type):
            #     self.object_manager.add(self.object_type(self.x, self.y))
            # else:
            #     self.object_type.alive = True
            self.alive = False

    def draw(self, surf: pygame.Surface):
        # pygame.draw.rect(surf, 'white', (0, 0, 100, 100))
        draw_rect = pygame.draw.rect
        for i in range(0, 360, self.diff):
            for k in range(1, self.particles_per_line):
                x = k * self.r * math.cos(math.radians(i)) + self.r * k * self.vec[0]
                y = k * self.r * math.sin(math.radians(i)) + self.r * k * self.vec[1]
                color = self.colors[int(map_to_range(i, 0, 360, 0, len(self.colors)))]
                rect = (self.x + x, self.y + y, self.max_particle_size - k, self.max_particle_size - k)
                draw_rect(surf, color, rect)
                # draw_rect(surf, 'black', rect, 2)


class ObjectManager:
    def __init__(self):
        self.objects: list[BaseObject] = []
        self._to_add: list[BaseObject] = []
        self.collision_enabled = True
        self.player = Player()
        self.player.object_manager = self

    def get_object_count(self, instance):
        c = 0
        for i in self.objects:
            if type(i) == instance:
                c += 1
        return c

    def clear(self):
        self._to_add.clear()
        self.objects.clear()

    def add(self, _object: BaseObject):
        _object.object_manager = self
        self._to_add.append(_object)

    def add_multiple(self, _objects: list[BaseObject]):
        for i in _objects:
            self.add(i)

    def update(self, events: list[pygame.event.Event]):
        self.player.update(events)
        if self._to_add:
            self.objects.extend(self._to_add)
            self._to_add.clear()
        self.objects = [i for i in self.objects if i.alive]
        self.objects.sort(key=attrgetter('z'))
        for i in self.objects:
            i.update(events)

    def draw(self, surf: pygame.Surface):
        for i in self.objects:
            i.draw(surf)
        self.player.draw(surf)
        # pygame.draw.rect(surf, 'black', self.player.rect, 2)
