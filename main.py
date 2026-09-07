import pygame
import os
import time
import random

WIDTH, HEIGHT = 550, 550
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

RED_SPACESHIP_IMAGE = pygame.image.load(os.path.join('assets', 'pixel_ship_red_small.png'))
GREEN_SPACESHIP_IMAGE = pygame.image.load(os.path.join('assets', 'pixel_ship_green_small.png'))
BLUE_SPACESHIP_IMAGE = pygame.image.load(os.path.join('assets', 'pixel_ship_blue_small.png'))

# PLAYER SHIP
YELLOW_SPACESHIP_IMAGE = pygame.image.load(os.path.join('assets', 'pixel_ship_yellow.png'))

# Lasers
RED_LASER = pygame.image.load(os.path.join('assets', 'pixel_laser_red.png'))
GREEN_LASER = pygame.image.load(os.path.join('assets', 'pixel_laser_green.png'))
BLUE_LASER = pygame.image.load(os.path.join('assets', 'pixel_laser_blue.png'))
YELLOW_LASER = pygame.image.load(os.path.join('assets', 'pixel_laser_yellow.png'))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'background-black.png')), (WIDTH, HEIGHT))

def main():
    run = True
    clock = pygame.time.Clock()

    def redraw_window():
        WIN.blit(BG, (0, 0))
        pygame.display.update() 

    while run:
        clock.tick(60)
        redraw_window()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

main()