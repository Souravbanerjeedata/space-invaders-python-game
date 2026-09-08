import pygame
import os
import time
import random
pygame.font.init()

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

class Ship:
    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y, 40, 40))


def main():
    run = True
    clock = pygame.time.Clock()
    level = 1
    lives = 5
    main_font = pygame.font.SysFont('comicsans', 20)

    ship = Ship(235, 450)

    player_vel = 5

    def redraw_window():
        WIN.blit(BG, (0, 0))
        live_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

        WIN.blit(live_label, (5, 5))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 5, 5))

        ship.draw(WIN)

        pygame.display.update() 

    while run:
        clock.tick(60)
        redraw_window()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and ship.x - player_vel > 0:
            ship.x -= player_vel
        if keys[pygame.K_RIGHT] and ship.x + player_vel + 40 < WIDTH:
            ship.x += player_vel
        if keys[pygame.K_UP] and ship.y - player_vel > 0:
            ship.y -= player_vel
        if keys[pygame.K_DOWN] and ship.y + player_vel + 40 < HEIGHT:
            ship.y += player_vel

main()