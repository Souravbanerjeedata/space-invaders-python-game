import pygame
import os
import time
import random

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
BG = pygame.image.load(os.path.join('assets', 'background-black.png'))