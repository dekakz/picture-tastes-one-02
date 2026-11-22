#!/usr/bin/env python3
"""Glossy burger hero image — pure Python stdlib, no external deps.

Renders one big appetising burger (toasted bun, melted cheese drip,
lettuce, tomato, juicy patty) on a warm dark background and writes a
1024x1024 PNG to /output/entry.png. All drawing is done by hand:
scanline ellipse fills, per-column wavy shapes, soft radial highlights.
"""
import math
import os
import random
import struct
import zlib

W = H = 1024
OUT = "/output/entry.png"

fb = bytearray(W * H * 3)
rng = random.Random(20261123)


# ---------------------------------------------------------------- helpers
def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else int(v)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (clamp(lerp(c1[0], c2[0], t)),
            clamp(lerp(c1[1], c2[1], t)),
            clamp(lerp(c1[2], c2[2], t)))


def set_px(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = rgb[0]
        fb[i + 1] = rgb[1]
        fb[i + 2] = rgb[2]


def blend_px(x, y, rgb, a):
    """Blend rgb over the framebuffer pixel by factor a (0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = (y * W + x) * 3
        fb[i] = clamp(lerp(fb[i], rgb[0], a))
        fb[i + 1] = clamp(lerp(fb[i + 1], rgb[1], a))
        fb[i + 2] = clamp(lerp(fb[i + 2], rgb[2], a))


def hspan(y, x0, x1, rgb):
    """Fast solid horizontal span on row y (inclusive bounds)."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0:
        return
    n = x1 - x0 + 1
    fb[y * W * 3 + x0 * 3: y * W * 3 + (x1 + 1) * 3] = bytes(rgb) * n


def ellipse(cx, cy, rx, ry, top, bottom, aa=True):
    """Filled ellipse with a vertical colour gradient (top -> bottom).

    One solid span per row; the two edge pixels are blended at ~50%
    for a cheap anti-aliased rim.
    """
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry))
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        d2 = 1.0 - dy * dy
        if d2 <= 0.0:
            continue
        dx = rx * math.sqrt(d2)
        t = (y - (cy - ry)) / (2.0 * ry)
        col = mix(top, bottom, t)
        x0f, x1f = cx - dx, cx + dx
        hspan(y, math.ceil(x0f), math.floor(x1f), col)
        if aa:
            blend_px(int(math.floor(x0f)), y, col, 0.55)
            blend_px(int(math.ceil(x1f)), y, col, 0.55)


def soft_spot(cx, cy, rx, ry, rgb, peak):
    """Soft radial highlight: alpha falls off quadratically to the rim."""
    x0 = max(0, int(cx - rx))
    x1 = min(W - 1, int(cx + rx))
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry))
    for y in range(y0, y1 + 1):
        ny = (y - cy) / ry
        for x in range(x0, x1 + 1):
            nx = (x - cx) / rx
            d2 = nx * nx + ny * ny
            if d2 < 1.0:
                blend_px(x, y, rgb, peak * (1.0 - d2) * (1.0 - d2))


def disc(cx, cy, r, rgb, a=1.0):
    """Small filled disc, optionally translucent."""
    x0 = max(0, int(cx - r))
    x1 = min(W - 1, int(cx + r))
    y0 = max(0, int(cy - r))
    y1 = min(H - 1, int(cy + r))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                if a >= 1.0:
                    set_px(x, y, rgb)
                else:
                    blend_px(x, y, rgb, a)


def speckle(cx, cy, rx, ry, n, colors, rmin=1, rmax=3):
    """Scatter small dots inside an ellipse region (texture / crumbs)."""
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        rad = math.sqrt(rng.random())
        x = cx + math.cos(ang) * rad * rx
        y = cy + math.sin(ang) * rad * ry
        disc(x, y, rng.uniform(rmin, rmax), rng.choice(colors), 0.55)


# ---------------------------------------------------------------- background
def background():
    # Warm dark vertical gradient: deep espresso top -> near-black base.
    top = (58, 34, 22)
    bot = (20, 11, 7)
    for y in range(H):
        t = y / (H - 1)
        col = mix(top, bot, t * t * 0.85 + t * 0.15)
        hspan(y, 0, W - 1, col)
    # Warm glow from above (the key light), soft and wide.
    soft_spot(512, 150, 560, 420, (255, 176, 92), 0.30)
    soft_spot(512, 240, 380, 260, (255, 205, 130), 0.22)


# ---------------------------------------------------------------- burger
def plate():
    # Soft shadow under the burger, then a dark plate rim.
    ellipse(512, 872, 440, 92, (16, 9, 6), (12, 7, 5))
    ellipse(512, 862, 428, 84, (74, 52, 40), (48, 32, 24))
    ellipse(512, 856, 400, 74, (38, 24, 17), (26, 16, 11))


def bottom_bun():
    # Golden lower bun peeking under the patty.
    ellipse(512, 796, 330, 92, (214, 141, 52), (168, 100, 34))
    soft_spot(430, 770, 220, 60, (255, 205, 120), 0.35)
    ellipse(512, 828, 300, 48, (188, 118, 40), (150, 88, 28))


def patty():
    # Thick juicy patty with a bumpy charred lower edge.
    ellipse(512, 706, 352, 78, (122, 66, 30), (74, 38, 16))
    # A few faint char flecks along the patty's lower rim for texture.
    for x in range(200, 830, 34):
        disc(x, 764 + 5 * math.sin(x * 0.11), 5, (84, 46, 20), 0.35)
    speckle(512, 706, 330, 62, 260,
            [(96, 50, 22), (150, 88, 40), (60, 32, 14), (170, 105, 48)])
    # Juicy sheen stripe across the patty face.
    soft_spot(420, 690, 260, 34, (255, 170, 90), 0.28)


def tomato():
    # Two bright red tomato slices peeking out at the sides.
    ellipse(512, 656, 338, 46, (226, 62, 40), (176, 34, 22))
    soft_spot(512, 640, 300, 22, (255, 120, 90), 0.35)
    # Inner flesh hint on the left slice.
    ellipse(300, 668, 92, 26, (240, 96, 66), (210, 60, 38))


def lettuce():
    # Ruffly green lettuce band, wavy top and bottom edges.
    x0, x1 = 168, 856
    for x in range(x0, x1 + 1):
        top_e = 622 + 13 * math.sin(x / 46.0) + 6 * math.sin(x / 17.0 + 1.3)
        bot_e = 668 + 16 * math.sin(x / 38.0 + 0.7) + 5 * math.sin(x / 13.0)
        for y in range(int(top_e), int(bot_e) + 1):
            t = (y - top_e) / max(1.0, bot_e - top_e)
            col = mix((126, 196, 66), (58, 128, 34), t)
            # A few darker veins for leaf texture.
            if int(x * 0.7 + y * 1.9) % 29 == 0:
                col = mix(col, (40, 96, 26), 0.5)
            set_px(x, y, col)
    # Crisp light edge along the top of the leaves.
    for x in range(x0, x1 + 1):
        y = int(622 + 13 * math.sin(x / 46.0) + 6 * math.sin(x / 17.0 + 1.3))
        blend_px(x, y, (190, 235, 120), 0.7)
        blend_px(x, y + 1, (150, 215, 90), 0.4)


def cheese():
    # Molten cheese sheet with long drips hanging over the patty.
    # Drip centres (x, depth, width).
    drips = [(330, 92, 46), (512, 142, 58), (692, 74, 42), (238, 48, 30),
             (800, 52, 32)]
    x0, x1 = 158, 866
    for x in range(x0, x1 + 1):
        # Cheese top edge follows the bun curve slightly.
        top_e = 566 - 22 * math.cos((x - 512) / 354.0)
        # Bottom edge: base line plus gaussian drips.
        depth = 34.0
        for cx, d, w in drips:
            depth += d * math.exp(-((x - cx) ** 2) / (2.0 * w * w))
        bot_e = 566 + depth
        for y in range(int(top_e), int(bot_e) + 1):
            t = (y - top_e) / max(1.0, bot_e - top_e)
            col = mix((255, 196, 60), (240, 140, 18), t)
            # Gloss streak near the top of the sheet.
            if y - top_e < 10:
                col = mix(col, (255, 226, 130), 0.55)
            set_px(x, y, col)
    # Rounded drip tips.
    for cx, d, w in drips:
        disc(cx, 566 + 34 + d, w * 0.42, (244, 150, 22), 1.0)
        disc(cx - 4, 566 + 34 + d - 6, w * 0.22, (255, 205, 90), 0.9)
    # Shiny highlight running down the longest drip.
    for y in range(590, 700):
        blend_px(500, y, (255, 228, 140), 0.5)
        blend_px(501, y, (255, 228, 140), 0.35)


def top_bun():
    # Big domed golden bun — the hero of the picture.
    ellipse(512, 440, 362, 205, (246, 184, 96), (196, 118, 40))
    # Buttery sheen: strong warm highlight upper-left, soft lower-right.
    soft_spot(400, 330, 260, 150, (255, 222, 150), 0.55)
    soft_spot(620, 300, 170, 110, (255, 236, 180), 0.30)
    # Toasted darker band along the bun's lower rim.
    for y in range(600, 650):
        t = (y - 600) / 50.0
        col = mix((214, 138, 52), (150, 84, 26), t)
        dy = (y - 440) / 205.0
        if abs(dy) < 1.0:
            dx = 362 * math.sqrt(1.0 - dy * dy)
            hspan(y, 512 - dx, 512 + dx, col)
    # Fine crumb speckles for baked texture.
    speckle(512, 430, 320, 180, 200,
            [(232, 168, 84), (180, 104, 34), (255, 210, 130)], 1, 2)
    sesame()


def sesame():
    # Toasted sesame seeds scattered over the dome, each with a shadow.
    seeds = [(360, 330), (440, 290), (520, 268), (610, 300), (680, 350),
             (330, 420), (420, 380), (500, 350), (590, 380), (700, 430),
             (380, 470), (470, 440), (560, 440), (650, 480), (300, 500),
             (730, 510), (540, 300), (450, 520)]
    for sx, sy in seeds:
        # Tiny shadow offset down-right, then the pale seed.
        ellipse(sx + 3, sy + 4, 15, 8, (150, 92, 30), (150, 92, 30))
        ellipse(sx, sy, 14, 7, (255, 232, 170), (238, 200, 130))
        disc(sx - 3, sy - 2, 3, (255, 244, 205), 0.8)


def steam():
    # Very faint warm steam wisps above the bun (appetite cue, subtle).
    for cx, base in [(430, 210), (512, 195), (595, 215)]:
        for k in range(3):
            soft_spot(cx + 8 * math.sin(k * 1.7), base - k * 26, 26, 34,
                      (255, 240, 220), 0.10)


def write_png(path, w, h, data):
    def chunk(tag, payload):
        c = tag + payload
        return (struct.pack(">I", len(payload)) + c +
                struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    raw = b"".join(b"\x00" + bytes(data[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    background()
    plate()
    bottom_bun()
    patty()
    tomato()
    lettuce()
    cheese()
    top_bun()
    steam()
    size = write_png(OUT, W, H, fb)
    print(f"wrote {OUT} {W}x{H} {size} bytes")


if __name__ == "__main__":
    main()
