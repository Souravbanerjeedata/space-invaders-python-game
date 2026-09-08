# Space Invaders

Classic Space Invaders in Python + Pygame.

---

## Game Preview

<!-- 
  Add your screenshot or GIF here later.
  ![Preview](preview.png)
-->

**[Insert Game Preview Image Here]**

---

## Features

- Free 4-direction movement (Arrows + WASD)
- Working laser (SPACE)
- Local sound effects (shoot, hit, explosion) in `assets/`
- Gradual difficulty with **hard caps** (won’t become impossible)
- Lives + health bar + score
- Menu and game-over screens
- Window size 750×550 (fits on screen)
- Ready for packaging into `.exe` (uses `resource_path`)

---

## Difficulty (capped)

| Level | Enemies (approx) | Speed |
|-------|------------------|--------|
| 1     | 5                | 1.0    |
| 3     | 11               | 1.24   |
| 5     | 17               | 1.48   |
| 7+    | **max 22**       | **max 2.4** |

Enemy count and speed stop increasing after the caps.

---

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow keys or WASD |
| Shoot | SPACE |
| Start | SPACE |
| Restart | R |
| Quit / Menu | ESC |

---

## Run

```bash
pip install pygame
python main.py
```

---

## Assets (all local)

```
assets/
├── background-black.png
├── pixel_ship_*.png
├── pixel_laser_*.png
├── shoot.wav
├── hit.wav
├── explosion.wav
└── enemy_explode.wav
```

All images and sounds are stored inside the project so packaging to `.exe` works.

---

## Build .exe later (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "assets;assets" main.py
```

---

**Made with ❤️ by Sourav Banerjee**
