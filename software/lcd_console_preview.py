#!/usr/bin/env python3
"""Console-look preview: renders a REAL shell session transcript at true
fbcon geometry (40 cols x 15 rows, 8x16 cells) on the ST7789 LCD."""
import subprocess, time
from PIL import Image, ImageDraw, ImageFont
from lcd_display import ST7789, W, H

COLS, ROWS = 40, 15
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MOBO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f_out = ImageFont.truetype(MONO, 13)
f_prm = ImageFont.truetype(MOBO, 13)
GREEN = (74, 227, 74); TEXT = (205, 205, 205)

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin:/usr/sbin", "TERM": "dumb"})
    return (r.stdout + r.stderr).rstrip("\n").splitlines()

session = []
for cmd in ["uname -sr", "ip -brief a", "free -h", "df -h /", "uptime"]:
    session.append(("beh@beh:~$ " + cmd, True))
    for ln in run(cmd):
        session.append((ln.expandtabs(4), False))
session.append(("beh@beh:~$ \u2588", True))

lines = []
for text, is_prompt in session:
    if text == "":
        lines.append(("", is_prompt))
    else:
        for i in range(0, len(text), COLS):
            lines.append((text[i:i + COLS], is_prompt))
lines = lines[-ROWS:]

img = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)
for row, (text, is_prompt) in enumerate(lines):
    d.text((2, row * 16 + 2), text, font=f_prm if is_prompt else f_out,
           fill=GREEN if is_prompt else TEXT)

lcd = ST7789()
lcd.show(img)
print("console preview pushed", flush=True)
time.sleep(900)
