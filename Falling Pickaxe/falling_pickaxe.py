import pygame
import sys
import random
import math
from collections import deque

pygame.init()

# ---------------- WINDOW ----------------
WIDTH, HEIGHT = 900, 800
GAME_WIDTH = 600
UI_WIDTH = WIDTH - GAME_WIDTH

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Falling Pickaxe Live")

CLOCK = pygame.time.Clock()
FPS = 60

# ---------------- COLORS ----------------
BG = (10, 10, 20)
TEXT = (230, 230, 230)
PANEL = (20, 20, 35)

# ---------------- GRID ----------------
TILE = 40
COLS = GAME_WIDTH // TILE

# ---------------- BLOCKS ----------------
ORE_BLOCKS = ["diamond", "lapis", "redstone", "gold", "coal", "copper"]
SOLID_BLOCKS = ["bedrock", "andesite", "obsidian", "cobblestone"]

# ---------------- PICKAXE LOADING ----------------
PX_W, PX_H = 50, 50

PICKAXE_NAMES = ["wood", "stone", "iron", "diamond"]

def remove_bg(img):
    img = img.convert_alpha()
    pixels = pygame.PixelArray(img)

    for x in range(img.get_width()):
        for y in range(img.get_height()):
            r, g, b, a = img.unmap_rgb(pixels[x, y])
            if r > 200 and g > 200 and b > 200:
                pixels[x, y] = (0, 0, 0, 0)

    del pixels
    return img

PICKAXES = []
for name in PICKAXE_NAMES:
    img = pygame.image.load(f"{name}.png")
    img = remove_bg(img)
    img = pygame.transform.scale(img, (PX_W, PX_H))
    PICKAXES.append(img)

current_pickaxe = 0

# ---------------- TEXTURES ----------------
def make_block_texture(base, ore=None):
    surf = pygame.Surface((TILE, TILE))
    surf.fill(base)

    for _ in range(40):
        x = random.randint(0, TILE - 1)
        y = random.randint(0, TILE - 1)
        surf.set_at((x, y), base)

    if ore:
        for _ in range(10):
            x = random.randint(4, TILE - 6)
            y = random.randint(4, TILE - 6)
            surf.set_at((x, y), ore)

    return surf

BLOCK_TEXTURES = {
    "cobblestone": make_block_texture((110,110,110)),
    "andesite": make_block_texture((130,130,135)),
    "bedrock": make_block_texture((40,40,45)),
    "obsidian": make_block_texture((20,10,40)),
    "coal": make_block_texture((90,90,90),(20,20,20)),
    "gold": make_block_texture((130,110,60),(240,210,80)),
    "diamond": make_block_texture((100,140,150),(80,240,240)),
    "lapis": make_block_texture((60,80,150),(40,80,220)),
    "redstone": make_block_texture((90,90,90),(220,40,40)),
    "copper": make_block_texture((120,90,70),(220,140,90)),
}

# ---------------- GAME STATE ----------------
blocks = []
scroll = 0
depth_y = 0

px = GAME_WIDTH // 2
py = 120

vel_x = 0
fall_speed = 1.5

tnts = []
ore_counts = {k:0 for k in ORE_BLOCKS}
queue = deque()

# ---------------- WORLD GEN ----------------
def gen_row(y):
    row = []
    for col in range(COLS):
        r = random.random()
        if r < 0.1:
            t = random.choice(ORE_BLOCKS)
        else:
            t = random.choice(SOLID_BLOCKS)

        row.append({"x": col*TILE, "y": y, "type": t})
    return row

def reset():
    global blocks, scroll
    blocks = []
    for i in range(HEIGHT//TILE + 5):
        blocks.extend(gen_row(i*TILE))
    scroll = 0

# ---------------- TNT ----------------
def spawn_tnt(x,y):
    tnts.append({"x":x,"y":y,"timer":40,"radius":120})

def explode(t):
    global blocks
    new = []
    for b in blocks:
        bx = b["x"] + TILE//2
        by = b["y"] - scroll + TILE//2
        if math.hypot(bx-t["x"], by-t["y"]) > t["radius"]:
            new.append(b)
        else:
            if b["type"] in ore_counts:
                ore_counts[b["type"]] += 1
    blocks = new

# ---------------- BREAK ----------------
def break_blocks():
    global px, vel_x

    rect = pygame.Rect(px, py, PX_W, PX_H)

    for b in blocks:
        if b["type"] == "air":
            continue

        br = pygame.Rect(b["x"], b["y"] - scroll, TILE, TILE)

        if rect.colliderect(br):
            # pickaxe strength
            chance = (current_pickaxe + 1) * 0.4

            if random.random() < chance:
                if b["type"] in ore_counts:
                    ore_counts[b["type"]] += 1
                b["type"] = "air"

            vel_x *= -1
            break

# ---------------- COMMANDS ----------------
def handle_cmd(cmd):
    global fall_speed, current_pickaxe

    if cmd == "tnt":
        spawn_tnt(px, py)

    elif cmd == "fast":
        fall_speed += 0.5

    elif cmd == "slow":
        fall_speed = max(0.5, fall_speed - 0.5)

    elif cmd == "upgrade":
        current_pickaxe = min(len(PICKAXES)-1, current_pickaxe+1)

# ---------------- DRAW ----------------
def draw():
    WIN.fill(BG)

    # blocks
    for b in blocks:
        y = b["y"] - scroll
        if -TILE < y < HEIGHT and b["type"] != "air":
            WIN.blit(BLOCK_TEXTURES[b["type"]], (b["x"], y))

    # TNT
    for t in tnts:
        pygame.draw.circle(WIN, (200,50,50), (int(t["x"]), int(t["y"])), 10)

    # pickaxe
    WIN.blit(PICKAXES[current_pickaxe], (px, py))

    # UI
    font = pygame.font.SysFont("consolas", 20)
    WIN.blit(font.render(f"Pickaxe: {PICKAXE_NAMES[current_pickaxe]}", True, TEXT), (10,10))
    WIN.blit(font.render(f"Depth: {-int(scroll//TILE)}", True, TEXT), (10,35))

    pygame.display.update()

# ---------------- LOOP ----------------
def run():
    global px, vel_x, scroll

    reset()

    while True:
        CLOCK.tick(FPS)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    queue.append("upgrade")  # test

        # movement
        vel_x += random.choice([-1,1])*0.2
        vel_x = max(-4, min(4, vel_x))
        px += vel_x

        if px < 0 or px > GAME_WIDTH-PX_W:
            vel_x *= -1

        break_blocks()

        scroll += fall_speed

        # generate
        max_y = max(b["y"] for b in blocks)
        while max_y - scroll < HEIGHT:
            max_y += TILE
            blocks.extend(gen_row(max_y))

        # TNT
        for t in tnts:
            t["y"] += fall_speed
            t["timer"] -= 1

        for t in [x for x in tnts if x["timer"] <= 0]:
            explode(t)

        tnts[:] = [x for x in tnts if x["timer"] > 0]

        if queue:
            handle_cmd(queue.popleft())

        draw()

run()