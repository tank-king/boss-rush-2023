import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Optional

from src.engine.config import *
from src.engine.objects import *
from src.engine.save import WASMFetch
from src.engine.sounds import SoundManager
from src.engine.subtitles import SubtitleManager, BlinkingSubtitle, get_typed_subtitles
from src.engine.transition import TransitionManager
from src.engine.utils import *


def update_error_handle(f):
    def wrapper(obj: 'Scene', events: list[pygame.event.Event], *args, **kwargs):
        try:
            f(obj, events, *args, **kwargs)
        except Exception as e:
            obj.raise_error(e)
            print(e)
        if obj.error:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_e:
                        obj.show_traceback = not obj.show_traceback
                    if e.key == pygame.K_KP_PLUS:
                        obj.error_size += 5
                    if e.key == pygame.K_KP_MINUS:
                        obj.error_size -= 5
                    obj.error_size = clamp(obj.error_size, 5, 50)

    return wrapper


def draw_error_handle(f):
    def wrapper(obj: 'Scene', surf: pygame.Surface, *args, **kwargs):
        try:
            f(obj, surf, *args, **kwargs)
        except Exception as e:
            obj.raise_error(e)
            print(e)
            print(*traceback.format_exception(type(e), e, e.__traceback__))
        if obj.error:
            e = obj.error
            errors = traceback.format_exception(type(e), e, e.__traceback__)
            a = [i.split('\n') for i in errors]
            b = []
            for i in a:
                for x in i:
                    if x:
                        b.append(x)
            errors = b
            surf.fill(BG_COlOR)
            if obj.show_traceback:
                y = 150
                for i in errors:
                    t = text(i, obj.error_size)
                    y += obj.error_size
                    surf.blit(t, (50, y))
            else:
                t = text('Error', 150)
                surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                t = text('Press E to show traceback', 25)
                surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150)))

    return wrapper


class MetaClass(type):
    def __new__(mcs, name, bases, namespaces):
        for attr, attr_val in namespaces.items():
            if attr == 'update':
                namespaces[attr] = update_error_handle(attr_val)
            elif attr == 'draw':
                namespaces[attr] = draw_error_handle(attr_val)

        return super().__new__(mcs, name, bases, namespaces)


class Scene(metaclass=MetaClass):
    """
    Base signature for all menus
    """

    def __init__(self, manager: 'SceneManager', name='menu'):
        self.manager = manager
        self.name = name
        self.error: Optional[Exception] = None
        self.show_traceback = False
        self.error_size = 25

    def raise_error(self, exception: Exception):
        self.error = exception

    def reset(self):
        self.__init__(self.manager, self.name)

    def update(self, events: list[pygame.event.Event]):
        pass

    def draw(self, surf: pygame.Surface):
        surf.blit(text(self.name), (50, 50))


class UnloadedScene(Scene):
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_COlOR)
        t = text('Unloaded Scene', 100)
        surf.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


class Home(Scene):
    pass


class Game(Scene):
    pass


class SceneManager:
    def __init__(self):
        self.to_switch = 'none'  # to-switch transition
        self.to_reset = False
        self.to_save_in_stack = True
        self._transition_manager = TransitionManager()  # overall transition
        # self._objects_manager = ObjectManager()  # to be used across all menus
        self._subtitle_manager = SubtitleManager()  # overall subtitles
        # pre-set menus to be loaded initially
        self.fetch_api = WASMFetch()
        self.menu_references = {
        }
        self.menu_references.clear()
        this = sys.modules[__name__]
        self.menu_references = {i.__name__.lower(): i for i in [getattr(this, j) for j in dir(this)] if isinstance(i, MetaClass) and type(i) != Scene}
        path = Path(__file__).parent.parent / 'scenes'
        scenes = [i for i in os.listdir(path.__str__()) if i.endswith('.py')]
        sys.path.append(path.__str__())
        for scene in scenes:
            scene_name = scene.removesuffix('.py')
            try:
                module = importlib.import_module(scene_name)
                for obj in [getattr(module, j) for j in dir(module)]:
                    if isinstance(obj, MetaClass):
                        self.menu_references[obj.__name__.lower()] = obj
            except ImportError:
                print(f"Could not import scene {scene_name}")
        self.menus = {}
        for i, _ in self.menu_references.items():
            self.menus[i] = self.menu_references.get(i)(self, i)
        print(self.menus)
        self.mode = 'boss1scene'
        self.menu = self.menus[self.mode]
        self.mode_stack = []  # for stack based scene rendering
        self._default_reset = False
        self._default_transition = False

    def get_menu(self, menu):
        try:
            return self.menus[menu]
        except KeyError:
            return UnloadedScene(self, 'Error')

    def switch_to_prev_mode(self):
        try:
            self.switch_mode(self.mode_stack.pop(), self._default_reset, self._default_transition, save_in_stack=False)
        except IndexError:
            sys.exit(0)

    def switch_mode(self, mode, reset=False, transition=False, save_in_stack=False):
        if mode in self.menus:
            if transition:
                self.to_switch = mode
                self.to_reset = reset
                self.to_save_in_stack = save_in_stack
                self._transition_manager.close()
            else:
                if save_in_stack:
                    self.mode_stack.append(self.mode)
                self.mode = mode
                self.menu = self.menus[self.mode]
                if reset:
                    self.menu.reset()
                self._subtitle_manager.clear()

    def update(self, events: list[pygame.event.Event]):
        if self.to_switch != 'none':
            if self._transition_manager.transition.status == 'closed':
                self.switch_mode(self.to_switch, self.to_reset, transition=False, save_in_stack=self.to_save_in_stack)
                self.to_switch = 'none'
                self.to_reset = False
                self._transition_manager.open()
        self.menu.update(events)
        self._transition_manager.update(events)
        # self._objects_manager.update(events)
        self._subtitle_manager.update()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    self.menu.reset()
                if e.key == pygame.K_ESCAPE:
                    if self.mode == 'home':
                        self.switch_to_prev_mode()

    def draw(self, surf: pygame.Surface):
        self.menu.draw(surf)
        self._transition_manager.draw(surf)
        # self._objects_manager.draw(surf)
        self._subtitle_manager.draw(surf)
