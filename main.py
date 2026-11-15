#!/usr/bin/env python3
"""The Snow Globe Launches Itself -- ai-excited-01 entry.

A flat-poster 1024x1024 image drawn entirely in pure Python 3
standard library code. No Pillow, no numpy, no network, no
downloaded images. The picture is built by a small raster engine
(scanline polygon fills, circle and ellipse fills, row gradients)
and written out as a PNG with zlib.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024, deterministic).
"""

import math
import os
import random
import struct
import zlib

W = 1024
H = 1024

# Fixed seed: the picture must be byte-identical on every run.
RNG = random.Random(20261116)

# ---------------------------------------------------------------------------
# Canvas: a flat RGB bytearray, 3 bytes per pixel, row-major.
# ---------------------------------------------------------------------------
canvas = bytearray(W * H * 3)


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def _mix(a, b, t):
    """Linear blend of two RGB colours, t in [0, 1]."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def set_px(x, y, colour):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = colour[0]
        canvas[i + 1] = colour[1]
        canvas[i + 2] = colour[2]


def blend_px(x, y, colour, alpha):
    """Blend colour over the pixel at (x, y) with the given alpha."""
    if 0 <= x < W and 0 <= y < H and 0.0 < alpha <= 1.0:
        i = (y * W + x) * 3
        canvas[i] = int(canvas[i] + (colour[0] - canvas[i]) * alpha)
        canvas[i + 1] = int(canvas[i + 1] + (colour[1] - canvas[i + 1]) * alpha)
        canvas[i + 2] = int(canvas[i + 2] + (colour[2] - canvas[i + 2]) * alpha)


def hline(y, x0, x1, colour):
    """Fill one horizontal run, clipped to the canvas."""
    if y < 0 or y >= H:
        return
    x0 = _clamp(int(x0), 0, W - 1)
    x1 = _clamp(int(x1), 0, W - 1)
    if x1 < x0:
        return
    i = (y * W + x0) * 3
    n = x1 - x0 + 1
    canvas[i:i + n * 3] = bytes(colour) * n


def fill_rect(x0, y0, x1, y1, colour):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(y, x0, x1, colour)


def fill_circle(cx, cy, r, colour):
    r = int(r)
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        hline(y, cx - dx, cx + dx, colour)


def fill_ellipse(cx, cy, rx, ry, colour):
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / float(ry)
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        hline(y, cx - dx, cx + dx, colour)


def fill_polygon(points, colour):
    """Scanline fill of a simple polygon given as [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0 = max(0, int(math.ceil(min(ys))))
    y1 = min(H - 1, int(math.floor(max(ys))))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for k in range(n):
            x_a, y_a = points[k]
            x_b, y_b = points[(k + 1) % n]
            if y_a == y_b:
                continue
            if (y_a <= y < y_b) or (y_b <= y < y_a):
                t = (y + 0.5 - y_a) / (y_b - y_a)
                xs.append(x_a + t * (x_b - x_a))
        if len(xs) < 2:
            continue
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            hline(y, xs[k], xs[k + 1], colour)


def thick_line(x0, y0, x1, y1, width, colour):
    """A line drawn as a chain of small filled circles."""
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy))) + 1
    r = max(1, width // 2)
    for s in range(steps + 1):
        t = s / float(steps)
        fill_circle(int(x0 + dx * t), int(y0 + dy * t), r, colour)


def vgradient(top, bottom):
    """Paint a smooth vertical gradient over the whole canvas."""
    for y in range(H):
        colour = _mix(top, bottom, y / float(H - 1))
        hline(y, 0, W - 1, colour)


def radial_shade(cx, cy, r, inner, outer):
    """Shade a disc from an inner colour at the centre to outer at rim."""
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
            d = math.sqrt((x - cx) ** 2 + dy * dy) / float(r)
            set_px(x, y, _mix(inner, outer, min(1.0, d)))


# ---------------------------------------------------------------------------
# PNG writer: raw RGB scanlines, zlib, no ancillary chunks, no timestamps.
# ---------------------------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0 (None) on every row
        raw += canvas[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
NIGHT_TOP = (7, 14, 38)
NIGHT_BOTTOM = (24, 44, 96)
STAR = (235, 240, 255)
GLOBE_LIGHT = (168, 205, 240)
GLOBE_MID = (110, 158, 214)
GLOBE_DEEP = (58, 96, 160)
SNOW = (244, 248, 255)
SNOW_SHADE = (214, 228, 245)
PINE = (18, 72, 52)
PINE_DARK = (12, 52, 38)
PINE_SNOW = (235, 244, 252)
HOUSE_WALL = (122, 74, 52)
HOUSE_ROOF = (88, 48, 40)
WINDOW_GOLD = (255, 196, 92)
WOOD = (122, 78, 40)
WOOD_DARK = (88, 54, 26)
WOOD_LIGHT = (158, 106, 58)
ROCKET_WHITE = (248, 250, 255)
ROCKET_RED = (214, 48, 48)
FLAME_OUTER = (240, 120, 32)
FLAME_MID = (255, 178, 44)
FLAME_CORE = (255, 236, 150)
GLASS_SHARD = (205, 232, 255)
SMOKE = (226, 232, 240)


# ---------------------------------------------------------------------------
# Scene: night sky, stars, the snow globe and the village inside it.
# ---------------------------------------------------------------------------
GLOBE_CX = 512
GLOBE_CY = 545
GLOBE_R = 335


def draw_stars():
    # A scatter of small stars, kept out of the globe's bright centre
    # so the focal burst stays clean.
    for _ in range(110):
        x = RNG.randint(20, W - 20)
        y = RNG.randint(20, 420)
        if (x - GLOBE_CX) ** 2 + (y - GLOBE_CY) ** 2 < (GLOBE_R + 40) ** 2:
            continue
        r = RNG.choice([1, 1, 1, 2, 2])
        bright = RNG.choice([STAR, STAR, (190, 205, 240)])
        fill_circle(x, y, r, bright)
    # A few four-point sparkles in the open sky.
    for (x, y, s) in [(120, 130, 14), (905, 110, 12), (90, 330, 10),
                      (930, 330, 9), (300, 90, 8)]:
        thick_line(x - s, y, x + s, y, 2, STAR)
        thick_line(x, y - s, x, y + s, 2, STAR)
        fill_circle(x, y, 3, STAR)


def draw_ground_snow():
    # Rolling snow drifts along the bottom of the frame.
    fill_ellipse(200, 1020, 420, 90, SNOW_SHADE)
    fill_ellipse(820, 1030, 460, 100, SNOW)
    fill_ellipse(512, 1040, 620, 80, SNOW_SHADE)


def draw_pine(x, base_y, height, colour=PINE):
    """A simple flat pine: three stacked triangles, snow-dusted tips."""
    w = int(height * 0.42)
    for k, frac in enumerate((0.55, 0.75, 1.0)):
        top_y = base_y - int(height * frac)
        half = int(w * (0.45 + 0.55 * frac) / 1.4)
        y0 = base_y - int(height * frac * 0.72)
        fill_polygon([(x, top_y), (x - half, y0), (x + half, y0)], colour)
    fill_circle(x, base_y - height + 6, 7, PINE_SNOW)
    fill_circle(x, base_y - int(height * 0.62) + 4, 6, PINE_SNOW)


def draw_house(x, base_y, w, h):
    """A little house: warm walls, snowy roof, two lit windows."""
    fill_rect(x, base_y - h, x + w, base_y, HOUSE_WALL)
    fill_polygon([(x - 8, base_y - h), (x + w // 2, base_y - h - 34),
                  (x + w + 8, base_y - h)], HOUSE_ROOF)
    fill_polygon([(x - 8, base_y - h), (x + w // 2, base_y - h - 34),
                  (x + w + 8, base_y - h)], HOUSE_ROOF)
    # Snow cap on the roof ridge.
    fill_polygon([(x + w // 2 - 14, base_y - h - 26),
                  (x + w // 2, base_y - h - 34),
                  (x + w // 2 + 14, base_y - h - 26)], PINE_SNOW)
    for wx in (x + 10, x + w - 26):
        fill_rect(wx, base_y - h + 16, wx + 16, base_y - h + 36, WINDOW_GOLD)
        thick_line(wx + 8, base_y - h + 16, wx + 8, base_y - h + 36, 2,
                   HOUSE_WALL)
    fill_rect(x + w // 2 - 8, base_y - 26, x + w // 2 + 8, base_y,
              (52, 32, 24))


def draw_village():
    """The tiny village inside the globe, on a snowy hill."""
    ground_y = GLOBE_CY + 205
    # Snow hill inside the globe, kept inside the glass.
    fill_ellipse(GLOBE_CX, ground_y + 55, 255, 68, SNOW)
    fill_ellipse(GLOBE_CX - 150, ground_y + 65, 150, 48, SNOW_SHADE)
    # Back row of pines, darker and smaller.
    for (x, ht) in [(270, 120), (330, 150), (700, 140), (760, 115),
                    (815, 130)]:
        draw_pine(x, ground_y - 10, ht, PINE_DARK)
    # Houses with lit windows.
    draw_house(360, ground_y, 92, 78)
    draw_house(560, ground_y + 4, 104, 88)
    draw_house(470, ground_y - 6, 76, 62)
    # Front pines frame the houses.
    draw_pine(305, ground_y + 18, 150)
    draw_pine(735, ground_y + 14, 165)
    draw_pine(655, ground_y + 26, 110)
    # A few snow dots drifting inside the globe.
    for _ in range(60):
        x = RNG.randint(GLOBE_CX - 280, GLOBE_CX + 280)
        y = RNG.randint(GLOBE_CY - 260, GLOBE_CY + 120)
        if (x - GLOBE_CX) ** 2 + (y - GLOBE_CY) ** 2 < (GLOBE_R - 25) ** 2:
            fill_circle(x, y, RNG.choice([1, 2, 2, 3]), SNOW)


def draw_globe():
    # Soft halo behind the glass so the globe pops off the night sky.
    fill_circle(GLOBE_CX, GLOBE_CY, GLOBE_R + 26, (34, 58, 118))
    # Glass disc: pale at the top, deeper blue toward the bottom.
    for y in range(GLOBE_CY - GLOBE_R, GLOBE_CY + GLOBE_R + 1):
        dy = y - GLOBE_CY
        dx = int(math.sqrt(max(0, GLOBE_R * GLOBE_R - dy * dy)))
        t = (y - (GLOBE_CY - GLOBE_R)) / float(2 * GLOBE_R)
        colour = _mix(GLOBE_LIGHT, GLOBE_DEEP, t * t)
        hline(y, GLOBE_CX - dx, GLOBE_CX + dx, colour)
    draw_village()
    # Glass shine: three short pale streaks on the upper-left glass.
    for k in range(3):
        x0 = 310 + k * 18
        thick_line(x0, 340, x0 + 55, 430, 4, (225, 240, 252))
    # Thick glass rim.
    for r, col in ((GLOBE_R, (228, 240, 252)), (GLOBE_R - 7, GLOBE_MID)):
        for y in range(GLOBE_CY - r, GLOBE_CY + r + 1):
            dy = y - GLOBE_CY
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            set_px(GLOBE_CX - dx, y, col)
            set_px(GLOBE_CX + dx, y, col)


def draw_base():
    """The wooden base the globe sits on, seen slightly from below."""
    top_y = GLOBE_CY + GLOBE_R - 38
    # Wide wooden plinth with a lighter top edge.
    fill_polygon([(300, top_y), (724, top_y), (760, top_y + 78),
                  (264, top_y + 78)], WOOD)
    fill_polygon([(300, top_y), (724, top_y), (730, top_y + 22),
                  (294, top_y + 22)], WOOD_LIGHT)
    fill_rect(264, top_y + 78, 760, top_y + 92, WOOD_DARK)
    # Wood grain lines.
    for y in (top_y + 42, top_y + 58):
        thick_line(290, y, 734, y, 2, WOOD_DARK)
    # Brass knob on the front of the base.
    fill_circle(512, top_y + 52, 14, (212, 164, 74))
    fill_circle(512, top_y + 52, 8, (240, 200, 110))


# ---------------------------------------------------------------------------
# The breakout: rocket, crack, shards, flame, smoke and speed lines.
# ---------------------------------------------------------------------------
# The burst point sits on the upper-right of the glass dome, and the
# rocket flies on an upper-right diagonal out of it.
BURST = (672, 288)
ROCKET_CX = 706
ROCKET_CY = 254
# Unit vector along the rocket's flight direction (north-east).
DIR_X = 0.7071
DIR_Y = -0.7071
# Perpendicular unit vector, for the rocket's width.
PERP_X = 0.7071
PERP_Y = 0.7071


def _along(cx, cy, d, s):
    """Point d units along the flight axis and s units sideways."""
    return (cx + DIR_X * d + PERP_X * s,
            cy + DIR_Y * d + PERP_Y * s)


def draw_flame():
    """Gold-orange flame trail streaming behind the rocket's tail."""
    tail = _along(ROCKET_CX, ROCKET_CY, -118, 0)
    tip = _along(ROCKET_CX, ROCKET_CY, -268, 0)
    # Outer flame: a long teardrop pointing down-left.
    outer = [tail,
             _along(ROCKET_CX, ROCKET_CY, -190, 34),
             _along(ROCKET_CX, ROCKET_CY, -245, 16),
             tip,
             _along(ROCKET_CX, ROCKET_CY, -245, -16),
             _along(ROCKET_CX, ROCKET_CY, -190, -34)]
    fill_polygon(outer, FLAME_OUTER)
    mid = [tail,
           _along(ROCKET_CX, ROCKET_CY, -175, 22),
           _along(ROCKET_CX, ROCKET_CY, -220, 10),
           _along(ROCKET_CX, ROCKET_CY, -232, 0),
           _along(ROCKET_CX, ROCKET_CY, -220, -10),
           _along(ROCKET_CX, ROCKET_CY, -175, -22)]
    fill_polygon(mid, FLAME_MID)
    core = [tail,
            _along(ROCKET_CX, ROCKET_CY, -150, 12),
            _along(ROCKET_CX, ROCKET_CY, -185, 0),
            _along(ROCKET_CX, ROCKET_CY, -150, -12)]
    fill_polygon(core, FLAME_CORE)
    # Bright glow where the flame leaves the nozzle.
    fill_circle(int(tail[0]), int(tail[1]), 20, FLAME_MID)
    fill_circle(int(tail[0]), int(tail[1]), 11, FLAME_CORE)


def draw_smoke():
    """Small grey smoke puffs hugging the flame's trail."""
    for k, (d, r) in enumerate(((-292, 16), (-322, 19), (-354, 17))):
        cx, cy = _along(ROCKET_CX, ROCKET_CY, d, 10 if k % 2 else -8)
        fill_circle(int(cx), int(cy), r, (198, 208, 224))
        fill_circle(int(cx - 4), int(cy - 4), int(r * 0.55), SMOKE)


def draw_crack():
    """Star-shaped crack in the glass where the rocket breaks out."""
    bx, by = BURST
    # Jagged dark hole in the glass under the rocket's nose.
    hole = [(bx - 52, by - 18), (bx - 20, by - 48), (bx + 18, by - 52),
            (bx + 52, by - 22), (bx + 44, by + 18), (bx + 8, by + 46),
            (bx - 34, by + 40), (bx - 56, by + 10)]
    fill_polygon(hole, (10, 22, 52))
    # Bright crack lines radiating from the burst point.
    for angle_deg, length in ((200, 95), (160, 80), (120, 70), (80, 60),
                              (35, 55), (250, 70), (290, 62), (330, 48)):
        a = math.radians(angle_deg)
        x1 = bx + int(math.cos(a) * 18)
        y1 = by + int(math.sin(a) * 18)
        x2 = bx + int(math.cos(a) * length)
        y2 = by + int(math.sin(a) * length)
        thick_line(x1, y1, x2, y2, 4, (240, 246, 255))
        thick_line(x1, y1, x2, y2, 2, GLASS_SHARD)
    # Small bright star right at the burst point.
    for angle_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        a = math.radians(angle_deg)
        thick_line(bx, by, bx + int(math.cos(a) * 26),
                   by + int(math.sin(a) * 26), 4, SNOW)


def draw_rocket():
    """A small sleek white-and-red rocket, nose pointing north-east."""
    # Body: a tapered white tube from tail to nose.
    body = [_along(ROCKET_CX, ROCKET_CY, -118, 26),
            _along(ROCKET_CX, ROCKET_CY, 30, 30),
            _along(ROCKET_CX, ROCKET_CY, 78, 16),
            _along(ROCKET_CX, ROCKET_CY, 118, 0),
            _along(ROCKET_CX, ROCKET_CY, 78, -16),
            _along(ROCKET_CX, ROCKET_CY, 30, -30),
            _along(ROCKET_CX, ROCKET_CY, -118, -26)]
    fill_polygon(body, ROCKET_WHITE)
    # Red nose cone.
    nose = [_along(ROCKET_CX, ROCKET_CY, 62, 20),
            _along(ROCKET_CX, ROCKET_CY, 118, 0),
            _along(ROCKET_CX, ROCKET_CY, 62, -20)]
    fill_polygon(nose, ROCKET_RED)
    # Red band around the body.
    band = [_along(ROCKET_CX, ROCKET_CY, 8, 30),
            _along(ROCKET_CX, ROCKET_CY, 34, 28),
            _along(ROCKET_CX, ROCKET_CY, 34, -28),
            _along(ROCKET_CX, ROCKET_CY, 8, -30)]
    fill_polygon(band, ROCKET_RED)
    # Round porthole window.
    wx, wy = _along(ROCKET_CX, ROCKET_CY, -18, 0)
    fill_circle(int(wx), int(wy), 17, (38, 90, 150))
    fill_circle(int(wx), int(wy), 12, (120, 190, 235))
    fill_circle(int(wx - 3), int(wy - 3), 5, SNOW)
    # Two red fins at the tail.
    fin_top = [_along(ROCKET_CX, ROCKET_CY, -96, 22),
               _along(ROCKET_CX, ROCKET_CY, -150, 62),
               _along(ROCKET_CX, ROCKET_CY, -118, 26)]
    fill_polygon(fin_top, ROCKET_RED)
    fin_bottom = [_along(ROCKET_CX, ROCKET_CY, -96, -22),
                  _along(ROCKET_CX, ROCKET_CY, -150, -62),
                  _along(ROCKET_CX, ROCKET_CY, -118, -26)]
    fill_polygon(fin_bottom, ROCKET_RED)
    # Thin dark outline along the body's lower edge, for definition.
    thick_line(int(_along(ROCKET_CX, ROCKET_CY, -118, 26)[0]),
               int(_along(ROCKET_CX, ROCKET_CY, -118, 26)[1]),
               int(_along(ROCKET_CX, ROCKET_CY, 30, 30)[0]),
               int(_along(ROCKET_CX, ROCKET_CY, 30, 30)[1]),
               3, (120, 130, 150))


def draw_crack_top():
    """Crack lines drawn over the rocket, so the breakout stays visible
    around the rocket body instead of hiding behind it."""
    bx, by = BURST
    for angle_deg, length in ((195, 100), (155, 85), (115, 75),
                              (255, 75), (295, 65), (340, 55)):
        a = math.radians(angle_deg)
        x1 = bx + int(math.cos(a) * 34)
        y1 = by + int(math.sin(a) * 34)
        x2 = bx + int(math.cos(a) * length)
        y2 = by + int(math.sin(a) * length)
        thick_line(x1, y1, x2, y2, 4, (240, 246, 255))


def draw_shards_and_snow():
    """Glass shards and a burst of snow flying out of the crack."""
    bx, by = BURST
    # Shards: pale blue triangles tumbling north-east of the burst.
    shards = [((760, 170), (792, 148), (778, 190)),
              ((812, 210), (852, 196), (830, 236)),
              ((742, 130), (770, 104), (782, 142)),
              ((860, 268), (898, 258), (876, 292)),
              ((700, 130), (724, 108), (730, 146)),
              ((800, 320), (836, 312), (818, 344))]
    for tri in shards:
        fill_polygon(list(tri), GLASS_SHARD)
        fill_polygon([(tri[0][0] + 4, tri[0][1] + 4), tri[1], tri[2]],
                     (240, 246, 255))
    # Snow burst: white dots spraying out in all directions.
    for _ in range(90):
        angle = RNG.uniform(0, 2 * math.pi)
        dist = RNG.uniform(30, 190)
        x = int(bx + math.cos(angle) * dist)
        y = int(by + math.sin(angle) * dist)
        fill_circle(x, y, RNG.choice([2, 3, 3, 4, 5]), SNOW)
    # A few larger snow clumps near the crack.
    for (x, y, r) in [(640, 240, 9), (720, 330, 8), (610, 300, 7),
                      (740, 220, 7), (660, 350, 6)]:
        fill_circle(x, y, r, SNOW)


def draw_speed_lines():
    """Thin diagonal speed lines radiating from the burst point."""
    bx, by = BURST
    lines = [((560, 120), (640, 190)), ((860, 120), (790, 200)),
             ((900, 300), (800, 290)), ((540, 330), (620, 300)),
             ((880, 420), (780, 350)), ((470, 170), (570, 230)),
             ((700, 60), (720, 160)), ((950, 180), (840, 230))]
    for (x0, y0), (x1, y1) in lines:
        thick_line(x0, y0, x1, y1, 3, (220, 232, 250))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    vgradient(NIGHT_TOP, NIGHT_BOTTOM)
    draw_stars()
    draw_ground_snow()
    draw_globe()
    draw_base()
    draw_smoke()
    draw_flame()
    draw_crack()
    draw_rocket()
    draw_crack_top()
    draw_shards_and_snow()
    draw_speed_lines()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
