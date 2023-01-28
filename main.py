import asyncio

import pygame

from src.engine.game import Game
from src.engine.utils import *

pygame.init()

W, H = 1000, 800

screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption('Boss Rush 2023')

FPS = 60
clock = pygame.time.Clock()


def main():
    running = True
    boss = Boss()
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
        screen.fill(0)
        boss.update(events)
        boss.draw(screen)
        pygame.display.update()
        clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    asyncio.run(game.run())
