import asyncio
import time
from pathlib import Path

import pygame

from src.engine.scene import SceneManager
from src.engine.config import *
from src.engine.sounds import SoundManager
from src.engine.utils import clamp

parent = Path(__file__).parent
sys.path.append(parent.absolute().__str__())
#
try:
    pygame.mixer.init()
    pygame.mixer.set_num_channels(16)
    Globals.set_global('speakers_init', True)
    SoundManager.load_sounds()
except pygame.error:
    Globals.set_global('speakers_init', False)
    try:
        pygame.init()
    except pygame.error:
        pass
#
# SoundManager.load_sounds()
#
# pygame.key.set_repeat(500, 50)


class Game:
    def __init__(self):
        flags = pygame.SCALED | pygame.FULLSCREEN
        full_screen = True
        if full_screen:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Boss Rush 2023')
        # self.window = Window("save the crabs", (WIDTH, HEIGHT))
        # self.renderer = Renderer(self.window, target_texture=True)
        # self.renderer.logical_size = (WIDTH, HEIGHT)
        self.full_screen = False
        self.manager = SceneManager()
        self.clock = pygame.time.Clock()

    def toggle_full_screen(self):
        self.full_screen = not self.full_screen
        if self.full_screen:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    async def run(self):
        # time.sleep(20)
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_f:
                        self.toggle_full_screen()
                    if e.key == pygame.K_ESCAPE:
                        sys.exit(0)
            await asyncio.sleep(0)
            self.screen.fill(0)
            # print(self.manager.fetch_api.post_response())
            self.manager.update(events)
            self.manager.draw(self.screen)
            # fps = self.clock.get_fps()
            # self.screen.blit(text('FPS', 64), (10, 20))
            # self.screen.blit(text(f'{round(fps)}', 64), (10, 80))
            # pygame.draw.rect(self.screen, 'black', VIEWPORT_RECT, 2)
            pygame.display.update()
            # self.renderer.present()
            self.clock.tick(60)
            try:
                dt = TARGET_FPS / self.clock.get_fps()
            except ZeroDivisionError:
                dt = 1
            dt = clamp(dt, 0.1, 2)
            # print(self.clock.get_fps())
