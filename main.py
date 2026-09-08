"""
Space Invaders - Classic Style
Looks closer to the original arcade game.
"""

import pygame
import os
import sys
import random
import math

pygame.init()
pygame.font.init()

# Optional sound (won't crash if no audio device)
SOUND_ENABLED = False
try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except Exception:
    SOUND_ENABLED = False

# ==================== WINDOW ====================
WIDTH, HEIGHT = 700, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")
FPS = 60

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Classic colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Fonts - classic feel, not oversized
FONT_SCORE = pygame.font.SysFont("courier", 28, bold=True)
FONT_UI = pygame.font.SysFont("courier", 22, bold=True)
FONT_TITLE = pygame.font.SysFont("courier", 48, bold=True)
FONT_MED = pygame.font.SysFont("courier", 32, bold=True)
FONT_SMALL = pygame.font.SysFont("courier", 18)


# ==================== LOAD ASSETS ====================
def load(name, size=None):
    img = pygame.image.load(os.path.join(ASSETS, name)).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

PLAYER_IMG = load("pixel_ship_yellow.png", (48, 40))
# Tint player toward classic green look
def tint_surface(surf, color):
    tinted = surf.copy()
    arr = pygame.surfarray.pixels3d(tinted)
    # simple green preference
    return tinted

# Keep yellow player but scale well; enemies classic sizes
ENEMY_W, ENEMY_H = 36, 28
RED_IMG = load("pixel_ship_red_small.png", (ENEMY_W, ENEMY_H))
GREEN_IMG = load("pixel_ship_green_small.png", (ENEMY_W, ENEMY_H))
BLUE_IMG = load("pixel_ship_blue_small.png", (ENEMY_W, ENEMY_H))

LASER_Y = load("pixel_laser_yellow.png", (4, 16))
LASER_R = load("pixel_laser_red.png", (4, 14))
LASER_G = load("pixel_laser_green.png", (4, 14))
LASER_B = load("pixel_laser_blue.png", (4, 14))

BG = load("background-black.png", (WIDTH, HEIGHT))

# Simple generated beeps (works without external files)
def make_beep(freq=440, duration_ms=80, volume=0.25):
    if not SOUND_ENABLED:
        return None
    try:
        import array
        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000)
        if n_samples < 1:
            return None
        period = max(1, sample_rate // freq)
        amp = int(32000 * volume)
        samples = array.array("h")
        for i in range(n_samples):
            # square wave with quick fade
            val = amp if ((i // (period // 2)) % 2 == 0) else -amp
            fade = max(0.0, 1.0 - (i / n_samples))
            samples.append(int(val * fade))
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None

SHOOT_SOUND = make_beep(880, 50, 0.2)
HIT_SOUND = make_beep(200, 90, 0.3)
DIE_SOUND = make_beep(90, 180, 0.35)
INVADER_SOUND = make_beep(160, 30, 0.12)


def play(sound):
    if sound and SOUND_ENABLED:
        try:
            sound.play()
        except Exception:
            pass


# ==================== BARRIERS (classic green bunkers) ====================
class Barrier:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 70
        self.h = 50
        # Pixel damage map (classic look)
        self.grid_w = 14
        self.grid_h = 10
        self.cell = 5
        self.blocks = [[1 for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        # Carve classic shape (arch)
        for row in range(self.grid_h):
            for col in range(self.grid_w):
                # top corners cut
                if row < 2 and (col < 2 or col > self.grid_w - 3):
                    self.blocks[row][col] = 0
                # bottom arch hole
                if row > 5 and 3 < col < 10:
                    self.blocks[row][col] = 0

    def draw(self, surf):
        for row in range(self.grid_h):
            for col in range(self.grid_w):
                if self.blocks[row][col]:
                    pygame.draw.rect(
                        surf, GREEN,
                        (self.x + col * self.cell, self.y + row * self.cell, self.cell, self.cell)
                    )

    def hit(self, lx, ly, lw, lh):
        """Destroy blocks that the laser touches. Returns True if any block hit."""
        hit_any = False
        for row in range(self.grid_h):
            for col in range(self.grid_w):
                if not self.blocks[row][col]:
                    continue
                bx = self.x + col * self.cell
                by = self.y + row * self.cell
                if (lx < bx + self.cell and lx + lw > bx and
                        ly < by + self.cell and ly + lh > by):
                    self.blocks[row][col] = 0
                    # also damage neighbors a bit
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        rr, cc = row + dr, col + dc
                        if 0 <= rr < self.grid_h and 0 <= cc < self.grid_w:
                            if random.random() < 0.5:
                                self.blocks[rr][cc] = 0
                    hit_any = True
        return hit_any


# ==================== LASER ====================
class Laser:
    def __init__(self, x, y, img, vel):
        self.x = x
        self.y = y
        self.img = img
        self.vel = vel
        self.mask = pygame.mask.from_surface(img)
        self.w = img.get_width()
        self.h = img.get_height()

    def move(self):
        self.y += self.vel

    def draw(self, window):
        window.blit(self.img, (int(self.x), int(self.y)))

    def off_screen(self):
        return self.y < -20 or self.y > HEIGHT + 20

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


def collide(a, b):
    offset = (int(b.x - a.x), int(b.y - a.y))
    return a.mask.overlap(b.mask, offset) is not None


# ==================== SHIPS ====================
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

    def draw(self, window):
        window.blit(self.ship_img, (int(self.x), int(self.y)))
        for laser in self.lasers:
            laser.draw(window)


class Player(Ship):
    def __init__(self, x, y):
        super().__init__(x, y, health=100)
        self.ship_img = PLAYER_IMG
        self.laser_img = LASER_Y
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.COOLDOWN = 20

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y - 12
            self.lasers.append(Laser(lx, ly, self.laser_img, -8))
            self.cool_down_counter = 1
            play(SHOOT_SOUND)

    def move_lasers(self, enemies, barriers, score_holder):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move()
            if laser.off_screen():
                self.lasers.remove(laser)
                continue

            # Barriers
            hit_barrier = False
            for bar in barriers:
                if bar.hit(laser.x, laser.y, laser.w, laser.h):
                    hit_barrier = True
                    break
            if hit_barrier:
                if laser in self.lasers:
                    self.lasers.remove(laser)
                continue

            # Enemies
            for enemy in enemies[:]:
                if collide(laser, enemy):
                    play(HIT_SOUND)
                    enemies.remove(enemy)
                    score_holder[0] += 100
                    if laser in self.lasers:
                        self.lasers.remove(laser)
                    break

    def draw_health(self, window):
        # Small bar under ship, stays on screen
        bw = self.get_width()
        bh = 5
        bx = self.x
        by = min(self.y + self.get_height() + 4, HEIGHT - 12)
        ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(window, (40, 40, 40), (bx, by, bw, bh))
        col = GREEN if ratio > 0.35 else RED
        pygame.draw.rect(window, col, (bx, by, int(bw * ratio), bh))


class Enemy(Ship):
    MAP = {
        "red": (RED_IMG, LASER_R),
        "green": (GREEN_IMG, LASER_G),
        "blue": (BLUE_IMG, LASER_B),
    }

    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.color = color
        self.ship_img, self.laser_img = self.MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.direction = 1  # for formation movement

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y + self.get_height()
            self.lasers.append(Laser(lx, ly, self.laser_img, 5))
            self.cool_down_counter = 1

    def move_lasers(self, player, barriers):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move()
            if laser.off_screen():
                self.lasers.remove(laser)
                continue

            for bar in barriers:
                if bar.hit(laser.x, laser.y, laser.w, laser.h):
                    if laser in self.lasers:
                        self.lasers.remove(laser)
                    break
            else:
                if collide(laser, player):
                    player.health -= 15
                    play(HIT_SOUND)
                    if laser in self.lasers:
                        self.lasers.remove(laser)


# ==================== FORMATION (classic row movement) ====================
class Formation:
    """Classic left-right then drop movement for the alien grid."""
    def __init__(self, rows=5, cols=8):
        self.enemies = []
        self.dir = 1  # 1 right, -1 left
        self.speed = 0.6
        self.drop = 18
        self.rows = rows
        self.cols = cols
        self.spawn()

    def spawn(self):
        self.enemies.clear()
        start_x = 80
        start_y = 90
        gap_x = 55
        gap_y = 42
        colors = ["red", "red", "green", "green", "blue"]
        for r in range(self.rows):
            for c in range(self.cols):
                x = start_x + c * gap_x
                y = start_y + r * gap_y
                color = colors[r % len(colors)]
                self.enemies.append(Enemy(x, y, color))

    def update(self):
        if not self.enemies:
            return

        # Find edges
        min_x = min(e.x for e in self.enemies)
        max_x = max(e.x + e.get_width() for e in self.enemies)

        should_drop = False
        if self.dir > 0 and max_x >= WIDTH - 20:
            should_drop = True
            self.dir = -1
        elif self.dir < 0 and min_x <= 20:
            should_drop = True
            self.dir = 1

        for e in self.enemies:
            if should_drop:
                e.y += self.drop
            e.x += self.speed * self.dir

    def draw(self, window):
        for e in self.enemies:
            e.draw(window)


# ==================== UI ====================
def draw_classic_hud(score, hi_score, lives, level):
    # Classic top layout similar to original
    draw = FONT_SCORE.render
    s1 = draw(f"SCORE<1>", True, WHITE)
    s2 = draw(f"{score:04d}", True, WHITE)
    hi = draw(f"HI-SCORE", True, WHITE)
    hi_v = draw(f"{hi_score:04d}", True, WHITE)

    WIN.blit(s1, (30, 12))
    WIN.blit(s2, (50, 42))
    WIN.blit(hi, (WIDTH // 2 - hi.get_width() // 2, 12))
    WIN.blit(hi_v, (WIDTH // 2 - hi_v.get_width() // 2, 42))

    # Lives as small ships at bottom left
    lives_label = FONT_SMALL.render(f"{lives}", True, WHITE)
    WIN.blit(lives_label, (20, HEIGHT - 28))
    for i in range(max(0, lives - 1)):
        small = pygame.transform.scale(PLAYER_IMG, (24, 20))
        WIN.blit(small, (45 + i * 30, HEIGHT - 30))

    # Level
    lvl = FONT_SMALL.render(f"LEVEL {level}", True, WHITE)
    WIN.blit(lvl, (WIDTH - lvl.get_width() - 20, HEIGHT - 28))


# ==================== SCREENS ====================
def main_menu(hi_score):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        WIN.fill(BLACK)

        title = FONT_TITLE.render("SPACE INVADERS", True, GREEN)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))

        sub = FONT_UI.render("CLASSIC STYLE", True, WHITE)
        WIN.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 250))

        prompt = FONT_UI.render("PRESS SPACE TO START", True, YELLOW)
        WIN.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 380))

        hi = FONT_SMALL.render(f"HI-SCORE  {hi_score:04d}", True, WHITE)
        WIN.blit(hi, (WIDTH // 2 - hi.get_width() // 2, 450))

        controls = FONT_SMALL.render("ARROWS / WASD  MOVE    SPACE  FIRE    ESC  QUIT", True, (120, 120, 120))
        WIN.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT - 60))

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


def game_over_screen(score, hi_score, level):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        WIN.fill(BLACK)

        over = FONT_TITLE.render("GAME OVER", True, RED)
        WIN.blit(over, (WIDTH // 2 - over.get_width() // 2, 220))

        sc = FONT_MED.render(f"SCORE  {score:04d}", True, WHITE)
        WIN.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 320))

        hi = FONT_UI.render(f"HI-SCORE  {hi_score:04d}", True, YELLOW)
        WIN.blit(hi, (WIDTH // 2 - hi.get_width() // 2, 370))

        lvl = FONT_SMALL.render(f"LEVEL REACHED  {level}", True, WHITE)
        WIN.blit(lvl, (WIDTH // 2 - lvl.get_width() // 2, 420))

        prompt = FONT_UI.render("PRESS R TO RESTART   ESC TO QUIT", True, GREEN)
        WIN.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 520))

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


def run_game(hi_score):
    clock = pygame.time.Clock()
    player = Player(WIDTH // 2 - 24, HEIGHT - 100)
    formation = Formation(rows=5, cols=8)
    barriers = [
        Barrier(90, HEIGHT - 220),
        Barrier(250, HEIGHT - 220),
        Barrier(410, HEIGHT - 220),
        Barrier(570, HEIGHT - 220),
    ]

    score = 0
    score_holder = [0]
    lives = 3
    level = 1
    enemy_shoot_timer = 0
    invader_step_timer = 0

    while True:
        clock.tick(FPS)
        score = score_holder[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False, score, hi_score  # back to menu

        # Input
        keys = pygame.key.get_pressed()
        speed = 5
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player.x > 10:
            player.x -= speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player.x + player.get_width() < WIDTH - 10:
            player.x += speed
        if keys[pygame.K_SPACE]:
            player.shoot()

        # Formation movement (classic)
        invader_step_timer += 1
        step_every = max(8, 28 - level * 2)
        if invader_step_timer >= step_every:
            invader_step_timer = 0
            formation.speed = 0.8 + level * 0.15
            formation.update()
            play(INVADER_SOUND)

        # Enemy shooting
        enemy_shoot_timer += 1
        if enemy_shoot_timer > max(20, 50 - level * 3) and formation.enemies:
            enemy_shoot_timer = 0
            shooter = random.choice(formation.enemies)
            shooter.shoot()

        # Update lasers
        player.move_lasers(formation.enemies, barriers, score_holder)
        for e in formation.enemies:
            e.move_lasers(player, barriers)

        # Collision ship vs player
        for e in formation.enemies[:]:
            if collide(e, player) or e.y + e.get_height() > player.y + 10:
                play(DIE_SOUND)
                lives -= 1
                formation.enemies.remove(e)
                player.health -= 30
                if lives <= 0 or player.health <= 0:
                    hi_score = max(hi_score, score_holder[0])
                    return True, score_holder[0], hi_score

        # Next wave
        if not formation.enemies:
            level += 1
            formation = Formation(rows=5, cols=min(10, 7 + level))
            formation.speed = 0.7 + level * 0.2
            # rebuild barriers a bit damaged? keep for now
            player.health = min(100, player.health + 25)

        # Draw
        WIN.fill(BLACK)
        # subtle scanline feel (optional light lines)
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(WIN, (8, 8, 8), (0, y), (WIDTH, y))

        formation.draw(WIN)
        for bar in barriers:
            bar.draw(WIN)

        player.draw(WIN)
        player.draw_health(WIN)

        draw_classic_hud(score_holder[0], hi_score, lives, level)

        pygame.display.update()


def main():
    hi_score = 0
    while True:
        main_menu(hi_score)
        game_over, score, hi_score = run_game(hi_score)
        if game_over:
            if not game_over_screen(score, hi_score, 1):
                break
        # else ESC → menu again


if __name__ == "__main__":
    main()
