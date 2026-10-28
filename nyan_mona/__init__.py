"""Nyan Mona for the Universe 2026 Badger 2350 / MonaOS runtime.

SELECT: pause/resume. LEFT/RIGHT: speed. MENU: show/hide controls.
HOME is handled by MonaOS. No external assets or network required.
"""
import math

badge.mode(HIRES | VSYNC)
screen.font = font.nope

PALETTE = {
    "K": color.rgb(20, 16, 31),
    "G": color.rgb(55, 42, 70),
    "W": color.rgb(255, 255, 255),
    "P": color.rgb(255, 177, 190),
    "T": color.rgb(255, 217, 186),
    "B": color.rgb(104, 196, 240),
}
RAINBOW_RGB = (
    (255, 65, 90), (255, 161, 61), (255, 227, 81),
    (100, 230, 112), (65, 188, 255), (168, 112, 255))
# Contribution levels are tinted toward the starfield, keeping every row's hue.
RAINBOW = tuple(tuple(color.rgb(*(
    bg + (channel - bg) * level // 100
    for channel, bg in zip(rgb, (9, 18, 49))))
    for level in (12, 35, 65, 100)) for rgb in RAINBOW_RGB)
BACKGROUND = color.rgb(9, 18, 49)
WHITE = color.rgb(224, 239, 255)
DIM = color.rgb(130, 158, 197)

# Original pixel-art interpretation of GitHub's Mona the Octocat.
# Cat ears, peach face and animated octopus arms; no pastry body.
SPRITE = (
    '......KKK..............KKK......',
    '.....KGGGK............KGGGK.....',
    '.....KGPGGK..........KGGPGK.....',
    '.....KGPPGGKKKKKKKKKKGGPPGK.....',
    '.....KGGGGGGGGGGGGGGGGGGGGK.....',
    '....KGGGGGGGGGGGGGGGGGGGGGGK....',
    '....KGGGTTTTTTTTTTTTTTGGGGK.....',
    '....KGGTTTTTTTTTTTTTTTTGGGK.....',
    '....KGGTTTKKTTTTTTKKTTTGGGK.....',
    '....KGGTTTKWTTTTTTKWTTTGGGK.....',
    '....KGGTTTKKTTTTTTKKTTTGGGK.....',
    '....KGGTPPTTTTTTTTTTPPTGGK......',
    '.....KGGTTTTTTKKTTTTTTGGK.......',
    '......KGGTTTTTTTTTTTTGGK........',
    '.......KKGGGGGGGGGGGGKK.........',
    '.........KKGGGGGGGGKK...........',
    '...........KGGGGGGK.............',
    '...........KGGGGGGK.............',
)

# Merge adjacent pixels into runs to keep per-frame drawing inexpensive.
RUNS = []
for row_index, row in enumerate(SPRITE):
    start = 0
    while start < len(row):
        end = start + 1
        while end < len(row) and row[end] == row[start]:
            end += 1
        if row[start] in PALETTE:
            RUNS.append((start, row_index, end - start, PALETTE[row[start]]))
        start = end

elapsed = 0.0
speed_index = 1
SPEEDS = (0.5, 1.0, 1.5, 2.0, 3.0)
paused = False
show_controls = True


def block(x, y, w, h, pen):
    screen.pen = pen
    screen.rectangle(int(x), int(y), int(w), int(h))


def mona(x, y, scale, frame):
    def pixel(px, py, w, h, pen):
        block(x + px * scale, y + py * scale, w * scale, h * scale, pen)

    # Four curling octopus arms flex in a six-frame flying cycle.
    step = (0, 1, 2, 2, 1, 0)[frame]
    for arm in range(4):
        base = 10 + arm * 3
        direction = -1 if arm < 2 else 1
        bend = step if arm % 2 else 2 - step
        pixel(base, 17, 3, 3 + bend, PALETTE["K"])
        pixel(base + direction * 2, 19 + bend, 4, 2, PALETTE["K"])
        pixel(base + direction * 4, 18 + bend, 2, 2, PALETTE["K"])
        pixel(base + direction * 2, 19 + bend, 2, 1, PALETTE["B"])
    for px, py, width, pen in RUNS:
        pixel(px, py, width, 1, pen)


def rainbow_trail(x, y, scale, time):
    cell = 2 * scale
    pitch = 3 * scale
    travel = time * 24 * scale
    first_column = int(travel // pitch)
    offset = int(travel % pitch)
    end = x + 5 * scale
    for column in range((end + offset) // pitch + 1):
        rx = column * pitch - offset
        wave = int(math.sin((rx - x) / (8.0 * scale) + time * 12) * scale)
        # A cell keeps its activity level as it scrolls away from Mona.
        world_column = first_column + column
        for row, levels in enumerate(RAINBOW):
            activity = ((world_column * 37 + row * 67)
                        ^ (world_column * 13 + row * 31) >> 2) % 11
            level = 0 if activity == 0 else 1 if activity < 4 else 2 if activity < 7 else 3
            block(rx, y + (row * 3 - 1) * scale + wave,
                  min(cell, end - rx), cell, levels[level])


def update():
    global elapsed, speed_index, paused, show_controls
    if badge.pressed(BUTTON_SELECT):
        paused = not paused
    if badge.pressed(BUTTON_LEFT):
        speed_index = max(0, speed_index - 1)
    if badge.pressed(BUTTON_RIGHT):
        speed_index = min(len(SPEEDS) - 1, speed_index + 1)
    if badge.pressed(BUTTON_MENU):
        show_controls = not show_controls
    if not paused:
        elapsed += min(max(badge.ticks_delta, 0), 100) / 1000.0 * SPEEDS[speed_index]

    w, h = screen.width, screen.height
    screen.pen = BACKGROUND
    screen.clear()
    scale = max(1, min(w // 100, h // 70))
    frame = int(elapsed * 12) % 6
    x = w // 2 - 12 * scale
    y = h // 2 - 11 * scale + (0, 0, 1, 2, 2, 1)[frame] * scale

    for i in range(26):
        sx = int((i * 73 + 19 - elapsed * (18 + i % 4 * 12)) % (w + 12)) - 6
        sy = (i * 47 + 11) % h
        radius = 1 + (int(elapsed * 5 + i) % 4 == 0)
        block(sx - radius, sy, radius * 2 + 1, 1, WHITE)
        block(sx, sy - radius, 1, radius * 2 + 1, WHITE)

    rainbow_trail(x, y, scale, elapsed)
    mona(x, y, scale, frame)

    screen.pen = WHITE
    screen.text("NYAN MONA", 8, 8)
    screen.pen = DIM
    screen.text("%gx%s" % (SPEEDS[speed_index], "  PAUSED" if paused else ""), 8, 23)
    if show_controls:
        screen.pen = WHITE
        screen.text("SELECT pause   L/R speed", 8, h - 26)
        screen.pen = DIM
        screen.text("MENU hints     HOME exit", 8, h - 14)


run(update)
