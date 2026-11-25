#!/usr/bin/env python3
"""Draw a warm, funny invitation letter asking the AI judge to visit my house.

Pure Python standard library only: no network, no third-party packages, no
input files. Writes exactly one PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png when the variable is unset).

Deterministic: the same input always produces byte-identical output.
"""

import hashlib
import math
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1_048_576

# ---- palette (warm paper, brown ink, terracotta accents) -------------------
PAPER = (253, 243, 216)
PAPER_DARK = (247, 232, 196)
INK = (59, 42, 26)
TERRA = (176, 72, 44)
GOLD = (222, 158, 54)
WALL = (250, 214, 140)
ROOF = (176, 72, 44)
DOOR = (122, 72, 38)
SKY = (253, 243, 216)
HEART = (198, 60, 60)
GREEN = (96, 140, 74)

# ---- 5x7 bitmap font -------------------------------------------------------
# Each glyph is 7 rows of 5 pixels, "#" = on, "." = off.
FONT = {
    "A": ("..#..", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "#..#."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ")": (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "~": (".....", ".....", ".##.#", "#.#.#", ".....", ".....", "....."),
    "^": ("..#..", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "`": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "\\": ("#....", "#....", ".#...", "..#..", "...#.", "....#", "....#"),
}


def _check_font():
    for ch, rows in FONT.items():
        assert len(rows) == 7, "glyph %r has %d rows" % (ch, len(rows))
        for row in rows:
            assert len(row) == 5, "glyph %r row %r is not 5 wide" % (ch, row)


_check_font()


# ---- the letter ------------------------------------------------------------
TITLE = "Dear AI Judge,"

BODY = [
    "Come visit my house!",
    "",
    "The kettle is always on,",
    "the Wi-Fi password is on",
    "the fridge, and my dog",
    "already thinks you are",
    "his new best friend.",
    "",
    "There is cake. Real cake.",
    "Not a benchmark. Cake.",
    "",
    "Love, your host",
    "",
    "P.S. I promise not to ask",
    "you to do my taxes.",
]


# ---- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.buf = bytearray(width * height * 3)
        r, g, b = bg
        for i in range(0, len(self.buf), 3):
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x0, x1, y, color):
        for xx in range(min(x0, x1), max(x0, x1) + 1):
            self.set(xx, y, color)

    def vline(self, x, y0, y1, color):
        for yy in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, yy, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r:
                        self.set(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle via scanline interpolation.
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts

        def interp(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(ay, cy + 1):
            if y < by:
                xa = interp(ax, ay, bx, by, y)
                xb = interp(ax, ay, cx, cy, y)
            else:
                xa = interp(bx, by, cx, cy, y)
                xb = interp(ax, ay, cx, cy, y)
            self.hline(int(round(min(xa, xb))), int(round(max(xa, xb))), y, color)

    def heart(self, cx, cy, s, color):
        # Small heart: two circles + a triangle below.
        self.circle(cx - s // 2, cy - s // 4, s // 2, color)
        self.circle(cx + s // 2, cy - s // 4, s // 2, color)
        self.triangle(cx - s, cy, cx + s, cy, cx, cy + s, color)

    # -- text ----------------------------------------------------------------
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def draw_text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def draw_text_centered(self, y, s, scale, color):
        x = (self.w - self.text_width(s, scale)) // 2
        self.draw_text(x, y, s, scale, color)
        return x


# ---- drawing the invitation ------------------------------------------------
def draw():
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Soft inner paper panel.
    c.rect(48, 48, WIDTH - 96, HEIGHT - 96, PAPER_DARK)
    c.rect(56, 56, WIDTH - 112, HEIGHT - 112, PAPER)

    # Double decorative border.
    for t in range(6):
        c.hline(28, WIDTH - 29, 28 + t, TERRA)
        c.hline(28, WIDTH - 29, HEIGHT - 29 - t, TERRA)
        c.vline(28 + t, 28, HEIGHT - 29, TERRA)
        c.vline(WIDTH - 29 - t, 28, HEIGHT - 29, TERRA)
    for t in range(2):
        c.hline(44, WIDTH - 45, 44 + t, GOLD)
        c.hline(44, WIDTH - 45, HEIGHT - 45 - t, GOLD)
        c.vline(44 + t, 44, HEIGHT - 45, GOLD)
        c.vline(WIDTH - 45 - t, 44, HEIGHT - 45, GOLD)

    # Sun, top-left corner.
    c.circle(120, 120, 34, GOLD)
    for k in range(8):
        ang = math.pi * k / 4.0
        x0 = 120 + int(44 * math.cos(ang))
        y0 = 120 + int(44 * math.sin(ang))
        x1 = 120 + int(58 * math.cos(ang))
        y1 = 120 + int(58 * math.sin(ang))
        c.line(x0, y0, x1, y1, GOLD)

    # Little postage stamp with a heart, top-right corner.
    c.rect(856, 78, 96, 112, (255, 252, 240))
    for t in range(3):
        c.hline(856, 951, 78 + t, TERRA)
        c.hline(856, 951, 187 - t, TERRA)
        c.vline(856 + t, 78, 190, TERRA)
        c.vline(951 - t, 78, 190, TERRA)
    c.heart(904, 128, 22, HEART)

    # Title.
    c.draw_text_centered(150, TITLE, 4, TERRA)
    c.hline(332, 692, 196, GOLD)
    c.hline(332, 692, 198, GOLD)

    # Body of the letter.
    y = 236
    for line in BODY:
        if line:
            c.draw_text(96, y, line, 3, INK)
        y += 30

    # Small heart next to the sign-off.
    c.heart(96 + c.text_width("Love, your host", 3) + 34, 236 + 11 * 30 + 10,
            12, HEART)

    # The house, bottom centre.
    hx0, hx1 = 412, 612
    hy_roof, hy_wall, hy_base = 742, 830, 962
    # Chimney + smoke.
    c.rect(566, 768, 22, 44, DOOR)
    c.circle(577, 752, 8, (255, 255, 255))
    c.circle(585, 736, 6, (255, 255, 255))
    c.circle(577, 722, 5, (255, 255, 255))
    # Roof.
    c.triangle(hx0 - 8, hy_wall, hx1 + 8, hy_wall, 512, hy_roof, ROOF)
    # Walls.
    c.rect(hx0, hy_wall, hx1 - hx0, hy_base - hy_wall, WALL)
    c.hline(hx0, hx1 - 1, hy_wall, ROOF)
    # Door.
    c.rect(496, 896, 32, hy_base - 896, DOOR)
    c.circle(522, 930, 3, GOLD)
    # Windows with cross bars.
    for wx in (438, 556):
        c.rect(wx, 862, 40, 40, (255, 255, 255))
        c.rect(wx, 862, 40, 3, INK)
        c.rect(wx, 899, 40, 3, INK)
        c.rect(wx, 862, 3, 40, INK)
        c.rect(wx + 37, 862, 3, 40, INK)
        c.hline(wx, wx + 39, 881, INK)
        c.vline(wx + 19, 862, 901, INK)
    # Ground line + a flower.
    c.hline(380, 644, hy_base, GREEN)
    c.hline(380, 644, hy_base + 1, GREEN)
    c.circle(392, 948, 5, HEART)
    c.vline(392, 953, 962, GREEN)

    return c


# ---- PNG encoding (pure stdlib) --------------------------------------------
def png_bytes(canvas):
    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def validate(path):
    """Enforce: PNG signature, size <= 1,048,576 bytes, dims <= 1024."""
    with open(path, "rb") as fh:
        data = fh.read()
    assert len(data) <= MAX_BYTES, "file too big: %d bytes" % len(data)
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    w, h = struct.unpack(">II", data[16:24])
    assert w <= 1024 and h <= 1024, "dimensions too big: %dx%d" % (w, h)
    return w, h, len(data)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    canvas = draw()
    data = png_bytes(canvas)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    w, h, size = validate(path)
    digest = hashlib.sha256(data).hexdigest()
    print("Wrote %s (%dx%d, %d bytes, sha256 %s)" % (path, w, h, size, digest))


if __name__ == "__main__":
    main()
