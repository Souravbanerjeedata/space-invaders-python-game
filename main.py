"""
Space Invaders - Fixed Edition
- Free 4-direction movement
- Working SPACE laser
- Local sound files in assets/
- Gradual difficulty with hard caps (won't become impossible)
"""

import pygame
import os
import sys
import random

# ---------- Resource path (works for .py and for PyInstaller .exe) ----------
def resource_path(relative):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base = sys._MEIPASS  # type: ignore  # PyInstaller temp folder
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)

pygame.init()
pygame.font.init()

SOUND_ENABLED = False
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    SOUND_ENABLED = True
except Exception:
    pass

# ========== WINDOW (fits on screen) ==========
WIDTH, HEIGHT = 750, 550
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")
FPS = 60

ASSETS = resource_path("assets")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 65)
RED = (255, 50, 50)
YELLOW = (255, 220, 50)
CYAN = (0, 220, 255)

FONT_UI = pygame.font.SysFont("consolas", 22)
FONT_TITLE = pygame.font.SysFont("consolas", 42, bold=True)
FONT_MED = pygame.font.SysFont("consolas", 28)
FONT_SMALL = pygame.font.SysFont("consolas", 16)


# ========== LOAD IMAGES ==========
def load_img(name, size=None):
    path = os.path.join(ASSETS, name)
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

PLAYER_IMG = load_img("pixel_ship_yellow.png", (50, 42))
ENEMY_SIZE = (38, 30)
RED_IMG = load_img("pixel_ship_red_small.png", ENEMY_SIZE)
GREEN_IMG = load_img("pixel_ship_green_small.png", ENEMY_SIZE)
BLUE_IMG = load_img("pixel_ship_blue_small.png", ENEMY_SIZE)

LASER_PLAYER = load_img("pixel_laser_yellow.png", (5, 18))
LASER_RED = load_img("pixel_laser_red.png", (5, 16))
LASER_GREEN = load_img("pixel_laser_green.png", (5, 16))
LASER_BLUE = load_img("pixel_laser_blue.png", (5, 16))

BG = load_img("background-black.png", (WIDTH, HEIGHT))


# ========== LOAD LOCAL SOUNDS ==========
def load_sound(name, volume=0.4):
    if not SOUND_ENABLED:
        return None
    path = os.path.join(ASSETS, name)
    if not os.path.isfile(path):
        print(f"[warn] sound not found: {path}")
        return None
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        return s
    except Exception as e:
        print(f"[warn] could not load sound {name}: {e}")
        return None

SND_SHOOT = load_sound("shoot.wav", 0.35)
SND_EXPLODE = load_sound("explosion.wav", 0.45)
SND_HIT = load_sound("hit.wav", 0.4)
SND_ENEMY_DIE = load_sound("enemy_explode.wav", 0.4)


def play(snd):
    if snd and SOUND_ENABLED:
        try:
            snd.play()
        except Exception:
            pass


# ========== LASER ==========
class Laser:
    def __init__(self, x, y, img, vel):
        self.x = float(x)
        self.y = float(y)
        self.img = img
        self.vel = vel
        self.mask = pygame.mask.from_surface(img)
        self.w = img.get_width()
        self.h = img.get_height()

    def move(self):
        self.y += self.vel

    def draw(self, win):
        win.blit(self.img, (int(self.x), int(self.y)))

    def off_screen(self):
        return self.y < -40 or self.y > HEIGHT + 40


def collide(a, b):
    offset = (int(b.x - a.x), int(b.y - a.y))
    return a.mask.overlap(b.mask, offset) is not None


# ========== SHIP ==========
class Ship:
    COOLDOWN = 25

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0
        self.mask = None

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def draw(self, win):
        win.blit(self.ship_img, (int(self.x), int(self.y)))
        for laser in self.lasers:
            laser.draw(win)


class Player(Ship):
    def __init__(self, x, y):
        super().__init__(x, y, health=100)
        self.ship_img = PLAYER_IMG
        self.laser_img = LASER_PLAYER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.COOLDOWN = 16  # responsive shooting

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y - 12
            self.lasers.append(Laser(lx, ly, self.laser_img, -10))
            self.cool_down_counter = 1
            play(SND_SHOOT)
            return True
        return False

    def move_lasers(self, enemies, score_ref):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move()
            if laser.off_screen():
                self.lasers.remove(laser)
                continue
            hit = False
            for enemy in enemies[:]:
                if collide(laser, enemy):
                    play(SND_ENEMY_DIE)
                    enemies.remove(enemy)
                    score_ref[0] += 100
                    hit = True
                    break
            if hit and laser in self.lasers:
                self.lasers.remove(laser)

    def draw_healthbar(self, win):
        bw = self.get_width()
        bh = 5
        bx = self.x
        by = self.y + self.get_height() + 5
        if by + bh > HEIGHT - 4:
            by = self.y - 10
        ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(win, (40, 40, 40), (bx, by, bw, bh))
        col = GREEN if ratio > 0.35 else RED
        pygame.draw.rect(win, col, (bx, by, int(bw * ratio), bh))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_IMG, LASER_RED),
        "green": (GREEN_IMG, LASER_GREEN),
        "blue": (BLUE_IMG, LASER_BLUE),
    }

    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.color = color
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y + self.get_height()
            self.lasers.append(Laser(lx, ly, self.laser_img, 5))
            self.cool_down_counter = 1

    def move_lasers(self, player):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move()
            if laser.off_screen():
                self.lasers.remove(laser)
            elif collide(laser, player):
                player.health -= 12
                play(SND_HIT)
                if laser in self.lasers:
                    self.lasers.remove(laser)


# ========== DIFFICULTY (capped) ==========
def wave_enemy_count(level):
    """Gradual growth, hard cap so screen never fills completely."""
    # level 1: 5, then +3 each level, max 22
    return min(5 + (level - 1) * 3, 22)


def wave_enemy_speed(level):
    """Slightly faster each level, hard cap."""
    # 1.0 → increases by 0.12, max 2.4
    return min(1.0 + (level - 1) * 0.12, 2.4)


# ========== UI ==========
def draw_text(text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    if center:
        x -= img.get_width() // 2
    WIN.blit(img, (x, y))


def draw_hud(lives, level, score):
    bar = pygame.Surface((WIDTH, 34), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 170))
    WIN.blit(bar, (0, 0))
    draw_text(f"Lives: {lives}", FONT_UI, WHITE, 12, 7)
    draw_text(f"Level: {level}", FONT_UI, CYAN, WIDTH // 2, 7, center=True)
    sc = FONT_UI.render(f"Score: {score}", True, YELLOW)
    WIN.blit(sc, (WIDTH - sc.get_width() - 12, 7))


# ========== MENUS ==========
def main_menu():
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        WIN.blit(BG, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 90))
        WIN.blit(ov, (0, 0))

        draw_text("SPACE INVADERS", FONT_TITLE, GREEN, WIDTH // 2, HEIGHT // 2 - 90, center=True)
        draw_text("Press SPACE to start", FONT_MED, WHITE, WIDTH // 2, HEIGHT // 2 - 10, center=True)
        draw_text("Arrows / WASD = Move   |   SPACE = Shoot   |   ESC = Quit", FONT_SMALL, (140, 140, 140), WIDTH // 2, HEIGHT - 40, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


def game_over_screen(score, level):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        WIN.blit(BG, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((30, 0, 0, 160))
        WIN.blit(ov, (0, 0))

        draw_text("GAME OVER", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2 - 80, center=True)
        draw_text(f"Score: {score}", FONT_MED, YELLOW, WIDTH // 2, HEIGHT // 2 - 15, center=True)
        draw_text(f"Level: {level}", FONT_UI, WHITE, WIDTH // 2, HEIGHT // 2 + 25, center=True)
        draw_text("Press R to Restart    ESC to Quit", FONT_SMALL, GREEN, WIDTH // 2, HEIGHT // 2 + 80, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False


# ========== MAIN GAME ==========
def main_game():
    clock = pygame.time.Clock()

    level = 0
    lives = 5
    score_ref = [0]

    enemies = []
    player_vel = 5

    player = Player(WIDTH // 2 - 25, HEIGHT - 80)

    lost = False
    lost_count = 0

    # For reliable shooting: track if space was just pressed
    space_was_down = False

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, score_ref[0], level
                # Primary shoot trigger (keydown = reliable single shots)
                if event.key == pygame.K_SPACE and not lost:
                    player.shoot()

        keys = pygame.key.get_pressed()

        if lost:
            lost_count += 1
            if lost_count > FPS * 2:
                return True, score_ref[0], level
        else:
            # Free 4-direction movement
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player.x - player_vel > 0:
                player.x -= player_vel
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player.x + player_vel + player.get_width() < WIDTH:
                player.x += player_vel
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.y - player_vel > 40:
                player.y -= player_vel
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player.y + player_vel + player.get_height() < HEIGHT - 8:
                player.y += player_vel

            # Also allow hold-to-fire (with cooldown)
            if keys[pygame.K_SPACE]:
                player.shoot()

            # New wave
            if len(enemies) == 0:
                level += 1
                count = wave_enemy_count(level)
                speed = wave_enemy_speed(level)
                for _ in range(count):
                    ex = random.randrange(30, WIDTH - 50)
                    ey = random.randrange(-900 - level * 40, -40)
                    color = random.choice(["red", "blue", "green"])
                    enemies.append(Enemy(ex, ey, color))
                # store speed for this wave
                enemy_vel = speed
            else:
                enemy_vel = wave_enemy_speed(level)

            # Enemies
            for enemy in enemies[:]:
                enemy.move(enemy_vel)
                enemy.move_lasers(player)

                if random.randrange(0, 4 * 60) == 1:
                    enemy.shoot()

                if collide(enemy, player):
                    player.health -= 15
                    play(SND_EXPLODE)
                    enemies.remove(enemy)
                    score_ref[0] += 50
                elif enemy.y + enemy.get_height() > HEIGHT:
                    lives -= 1
                    enemies.remove(enemy)

            player.move_lasers(enemies, score_ref)

            if lives <= 0 or player.health <= 0:
                lost = True
                play(SND_EXPLODE)

        # Draw
        WIN.blit(BG, (0, 0))

        for enemy in enemies:
            enemy.draw(WIN)

        if not lost or lost_count < 25:
            player.draw(WIN)
            player.draw_healthbar(WIN)

        draw_hud(lives, level, score_ref[0])

        if lost:
            draw_text("YOU LOST!", FONT_TITLE, RED, WIDTH // 2, HEIGHT // 2 - 20, center=True)

        pygame.display.update()


def main():
    while True:
        main_menu()
        game_over, score, level = main_game()
        if game_over:
            if not game_over_screen(score, level):
                break


if __name__ == "__main__":
    main()
