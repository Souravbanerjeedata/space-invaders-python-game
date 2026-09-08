"""
Space Invaders - Advanced Edition
Improved code, fixed bugs, better sizing, particles, stars, score, menus, polish.
"""

import pygame
import os
import sys
import random
import math

# ==================== INIT ====================
pygame.init()
pygame.font.init()
pygame.mixer.init()

# Larger, better proportioned window
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

FPS = 60
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GREEN = (50, 220, 80)
YELLOW = (255, 230, 50)
CYAN = (80, 220, 255)
ORANGE = (255, 150, 40)
GRAY = (140, 140, 160)

# ==================== LOAD & SCALE ASSETS ====================
def load_img(name, size=None):
    path = os.path.join(ASSETS, name)
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

# Player ship (larger, clear)
PLAYER_SHIP = load_img("pixel_ship_yellow.png", (55, 45))
PLAYER_LASER = load_img("pixel_laser_yellow.png", (8, 24))

# Enemy ships - consistent size so they don't look off-screen / mismatched
ENEMY_SIZE = (40, 35)
RED_SHIP = load_img("pixel_ship_red_small.png", ENEMY_SIZE)
GREEN_SHIP = load_img("pixel_ship_green_small.png", ENEMY_SIZE)
BLUE_SHIP = load_img("pixel_ship_blue_small.png", ENEMY_SIZE)

RED_LASER = load_img("pixel_laser_red.png", (6, 18))
GREEN_LASER = load_img("pixel_laser_green.png", (6, 18))
BLUE_LASER = load_img("pixel_laser_blue.png", (6, 18))

BG = load_img("background-black.png", (WIDTH, HEIGHT))

# Fonts - smaller, readable sizes
FONT_SM = pygame.font.SysFont("comicsans", 22)
FONT_MD = pygame.font.SysFont("comicsans", 32)
FONT_LG = pygame.font.SysFont("comicsans", 48)
FONT_XL = pygame.font.SysFont("comicsans", 64)


# ==================== EFFECTS ====================
class Particle:
    def __init__(self, x, y, color, life=None, speed=None):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, math.tau)
        spd = speed if speed else random.uniform(1.0, 4.5)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.life = life if life else random.randint(15, 35)
        self.max_life = self.life
        self.size = random.uniform(1.5, 4.0)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1
        self.size = max(0.3, self.size * 0.96)

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        s = max(1, int(self.size))
        # soft glow
        g = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
        pygame.draw.circle(g, (*self.color, alpha // 3), (s * 2, s * 2), s * 2)
        surf.blit(g, (int(self.x) - s * 2, int(self.y) - s * 2))
        pygame.draw.circle(surf, (*self.color, alpha), (int(self.x), int(self.y)), s)


class Star:
    def __init__(self):
        self.reset(True)

    def reset(self, full=False):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT) if full else random.randint(-20, -5)
        self.speed = random.uniform(0.4, 2.2)
        self.size = random.choice([1, 1, 1, 2, 2, 3])
        self.bright = random.randint(120, 255)
        self.phase = random.uniform(0, math.tau)

    def update(self):
        self.y += self.speed
        self.phase += 0.07
        if self.y > HEIGHT + 5:
            self.reset()

    def draw(self, surf):
        b = int(self.bright * (0.55 + 0.45 * math.sin(self.phase)))
        col = (b, b, min(255, b + 40))
        if self.size >= 2:
            g = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            pygame.draw.circle(g, (*col, 40), (self.size * 2, self.size * 2), self.size * 2)
            surf.blit(g, (int(self.x) - self.size * 2, int(self.y) - self.size * 2))
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.size)


def spawn_explosion(x, y, particles, color, count=16):
    for _ in range(count):
        particles.append(Particle(x, y, color))
        if random.random() < 0.4:
            particles.append(Particle(x, y, ORANGE, life=random.randint(10, 22)))


# ==================== GAME OBJECTS ====================
class Laser:
    def __init__(self, x, y, img, velocity):
        self.x = x
        self.y = y
        self.img = img
        self.vel = velocity
        self.mask = pygame.mask.from_surface(img)
        self.width = img.get_width()
        self.height = img.get_height()

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self):
        self.y += self.vel

    def off_screen(self):
        return self.y > HEIGHT + 20 or self.y < -20

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height


def collide(obj1, obj2):
    """Pixel-perfect collision using masks."""
    offset_x = int(obj2.x - obj1.x)
    offset_y = int(obj2.y - obj1.y)
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


class Ship:
    COOLDOWN = 28

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

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            # Center laser on ship
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y
            self.lasers.append(Laser(lx, ly, self.laser_img, 0))  # vel set by caller context
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def move_lasers(self, vel, targets, particles=None, score_ref=None):
        """Move lasers. targets can be a single Ship or a list of Ships."""
        self.cooldown()
        for laser in self.lasers[:]:
            laser.vel = vel
            laser.move()
            if laser.off_screen():
                self.lasers.remove(laser)
                continue

            if isinstance(targets, list):
                for t in targets[:]:
                    if collide(laser, t):
                        if particles is not None:
                            spawn_explosion(
                                t.x + t.get_width() // 2,
                                t.y + t.get_height() // 2,
                                particles,
                                RED if hasattr(t, "color") else YELLOW,
                            )
                        if score_ref is not None:
                            score_ref[0] += 100
                        targets.remove(t)
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                        break
            else:
                # single target (player)
                if collide(laser, targets):
                    targets.health -= 12
                    if particles is not None:
                        spawn_explosion(
                            laser.x + laser.get_width() // 2,
                            laser.y + laser.get_height() // 2,
                            particles,
                            RED,
                            count=10,
                        )
                    if laser in self.lasers:
                        self.lasers.remove(laser)


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SHIP
        self.laser_img = PLAYER_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y - 10
            laser = Laser(lx, ly, self.laser_img, -7)  # upward
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def draw(self, window):
        super().draw(window)
        self.draw_healthbar(window)

    def draw_healthbar(self, window):
        bar_w = self.get_width()
        bar_h = 6
        x = self.x
        y = self.y + self.get_height() + 6
        # Keep bar on screen
        if y + bar_h > HEIGHT - 4:
            y = self.y - 12
        ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(window, (40, 40, 50), (x, y, bar_w, bar_h), border_radius=2)
        if ratio > 0:
            col = GREEN if ratio > 0.4 else (ORANGE if ratio > 0.2 else RED)
            pygame.draw.rect(window, col, (x, y, int(bar_w * ratio), bar_h), border_radius=2)
        pygame.draw.rect(window, WHITE, (x, y, bar_w, bar_h), 1, border_radius=2)


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SHIP, RED_LASER),
        "green": (GREEN_SHIP, GREEN_LASER),
        "blue": (BLUE_SHIP, BLUE_LASER),
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.color = color
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.shoot_chance = 0.004  # base, scales with level

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            lx = self.x + self.get_width() // 2 - self.laser_img.get_width() // 2
            ly = self.y + self.get_height()
            laser = Laser(lx, ly, self.laser_img, 5)
            self.lasers.append(laser)
            self.cool_down_counter = 1


# ==================== UI HELPERS ====================
def draw_text(surf, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    if center:
        x = x - img.get_width() // 2
    surf.blit(img, (x, y))
    return img


def draw_hud(lives, level, score, player_health, max_health):
    # Top bar background
    bar = pygame.Surface((WIDTH, 42), pygame.SRCALPHA)
    bar.fill((0, 0, 20, 160))
    WIN.blit(bar, (0, 0))

    draw_text(WIN, f"Lives: {lives}", FONT_SM, WHITE, 12, 10)
    draw_text(WIN, f"Level: {level}", FONT_SM, CYAN, WIDTH // 2, 10, center=True)
    score_img = FONT_SM.render(f"Score: {score}", True, YELLOW)
    WIN.blit(score_img, (WIDTH - score_img.get_width() - 12, 10))


# ==================== SCREENS ====================
def main_menu(stars):
    clock = pygame.time.Clock()
    pulse = 0
    while True:
        clock.tick(FPS)
        pulse += 0.06

        WIN.blit(BG, (0, 0))
        for s in stars:
            s.update()
            s.draw(WIN)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 120))
        WIN.blit(overlay, (0, 0))

        p = 0.7 + 0.3 * math.sin(pulse)
        title_col = (int(255 * p), int(230 * p), int(60 * p))
        draw_text(WIN, "SPACE INVADERS", FONT_XL, title_col, WIDTH // 2, HEIGHT // 2 - 100, center=True)
        draw_text(WIN, "Advanced Edition", FONT_MD, CYAN, WIDTH // 2, HEIGHT // 2 - 40, center=True)

        if int(pulse * 2) % 2 == 0:
            draw_text(WIN, "Click or press SPACE to start", FONT_SM, GREEN, WIDTH // 2, HEIGHT // 2 + 40, center=True)
        else:
            draw_text(WIN, "Click or press SPACE to start", FONT_SM, (40, 160, 70), WIDTH // 2, HEIGHT // 2 + 40, center=True)

        draw_text(WIN, "Arrows / WASD  move   |   SPACE  shoot   |   ESC  quit", FONT_SM, GRAY, WIDTH // 2, HEIGHT - 50, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


def game_over_screen(stars, score, level, particles):
    clock = pygame.time.Clock()
    while True:
        clock.tick(FPS)
        WIN.blit(BG, (0, 0))
        for s in stars:
            s.update()
            s.draw(WIN)
        for p in particles[:]:
            p.update()
            p.draw(WIN)
            if p.life <= 0:
                particles.remove(p)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 180))
        WIN.blit(overlay, (0, 0))

        draw_text(WIN, "GAME OVER", FONT_XL, RED, WIDTH // 2, HEIGHT // 2 - 90, center=True)
        draw_text(WIN, f"Score: {score}", FONT_MD, YELLOW, WIDTH // 2, HEIGHT // 2 - 20, center=True)
        draw_text(WIN, f"Level reached: {level}", FONT_SM, WHITE, WIDTH // 2, HEIGHT // 2 + 20, center=True)
        draw_text(WIN, "Press R to Restart   |   ESC to Quit", FONT_SM, GREEN, WIDTH // 2, HEIGHT // 2 + 80, center=True)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # restart
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


def main_game(stars):
    clock = pygame.time.Clock()
    run = True

    level = 0
    lives = 5
    score = 0
    score_ref = [0]  # mutable for laser callbacks

    enemies = []
    wave_length = 5
    enemy_vel = 1.0
    player_vel = 6
    laser_vel = 6

    player = Player(WIDTH // 2 - 27, HEIGHT - 90)
    particles = []
    lost = False
    lost_timer = 0

    while run:
        clock.tick(FPS)
        score = score_ref[0]

        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False, score, level, particles

        if lost:
            lost_timer += 1
            # keep drawing for a moment then go to game over
            if lost_timer > FPS * 2:
                return True, score, level, particles  # signal game over

        # ---- Input ----
        if not lost:
            keys = pygame.key.get_pressed()
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player.x - player_vel > 0:
                player.x -= player_vel
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player.x + player_vel + player.get_width() < WIDTH:
                player.x += player_vel
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.y - player_vel > 40:
                player.y -= player_vel
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player.y + player_vel + player.get_height() < HEIGHT - 20:
                player.y += player_vel
            if keys[pygame.K_SPACE]:
                player.shoot()

        # ---- Spawn wave ----
        if not lost and len(enemies) == 0:
            level += 1
            wave_length = 5 + (level - 1) * 3
            enemy_vel = min(1.0 + (level - 1) * 0.15, 3.5)
            for _ in range(wave_length):
                ex = random.randrange(40, WIDTH - 60)
                ey = random.randrange(-1400 - level * 80, -80)
                color = random.choice(["red", "blue", "green"])
                e = Enemy(ex, ey, color)
                e.shoot_chance = min(0.004 + level * 0.0015, 0.02)
                enemies.append(e)

        # ---- Update enemies ----
        if not lost:
            for enemy in enemies[:]:
                enemy.move(enemy_vel)
                enemy.move_lasers(laser_vel, player, particles)

                if random.random() < enemy.shoot_chance:
                    enemy.shoot()

                if collide(enemy, player):
                    player.health -= 15
                    spawn_explosion(
                        enemy.x + enemy.get_width() // 2,
                        enemy.y + enemy.get_height() // 2,
                        particles,
                        RED,
                        count=20,
                    )
                    enemies.remove(enemy)
                    score_ref[0] += 50
                elif enemy.y + enemy.get_height() > HEIGHT:
                    lives -= 1
                    enemies.remove(enemy)

            # Player lasers
            player.move_lasers(-laser_vel, enemies, particles, score_ref)

        # ---- Lose condition ----
        if lives <= 0 or player.health <= 0:
            if not lost:
                lost = True
                spawn_explosion(
                    player.x + player.get_width() // 2,
                    player.y + player.get_height() // 2,
                    particles,
                    YELLOW,
                    count=40,
                )

        # ---- Update effects ----
        for s in stars:
            s.update()
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # ---- Draw ----
        WIN.blit(BG, (0, 0))
        for s in stars:
            s.draw(WIN)

        for enemy in enemies:
            enemy.draw(WIN)

        if not lost or lost_timer < 30:
            player.draw(WIN)

        for p in particles:
            p.draw(WIN)

        draw_hud(lives, level, score_ref[0], player.health, player.max_health)

        if lost:
            draw_text(WIN, "YOU LOST!", FONT_LG, RED, WIDTH // 2, HEIGHT // 2 - 30, center=True)

        pygame.display.update()

    return False, score_ref[0], level, particles


def main():
    stars = [Star() for _ in range(110)]

    while True:
        main_menu(stars)
        go_to_gameover, score, level, particles = main_game(stars)
        if go_to_gameover:
            restart = game_over_screen(stars, score, level, particles)
            if not restart:
                break
        else:
            # ESC from game → back to menu
            continue


if __name__ == "__main__":
    main()
