#!/usr/bin/env python3
"""
GMT024-08-SPI8P color LCD system-info display.
Panel identified Oct 31 via the manufacturer (GoldenMorning): the
GMT024-08 uses an ST7789V controller, 240x320, 4-wire SPI - NOT an
ILI9341. Shows the same content as display.py (the Waveshare e-Paper
script), rendered in color at 320x240 landscape, rotated in software
and pushed to the panel in its native 240x320 portrait GRAM.
Wiring (Bryan's, Oct 31): CS=CE1/GPIO7 (spidev0.1), DC=GPIO24, RST=GPIO25,
BL hard-wired to 3.3V (always on).
"""
import sys, time
sys.path.insert(0, "/home/beh")
import numpy as np
import spidev
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import display as epd_src   # reuse collect_system_info() and get_font()

PIN_RST = 25
PIN_DC  = 24
W, H = 320, 240        # rendered landscape size
PW, PH = 240, 320      # panel native portrait GRAM

class ST7789:
    def __init__(self, spi_bus=0, spi_dev=1, speed=24_000_000):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_RST, GPIO.OUT)
        GPIO.setup(PIN_DC, GPIO.OUT)
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.mode = 0
        self.spi.max_speed_hz = speed
        self._init_display()

    def _cmd(self, c, data=None):
        GPIO.output(PIN_DC, GPIO.LOW)
        self.spi.writebytes([c])
        if data:
            GPIO.output(PIN_DC, GPIO.HIGH)
            self.spi.writebytes(list(data))

    def _init_display(self):
        # hardware reset
        GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.01)
        GPIO.output(PIN_RST, GPIO.LOW);  time.sleep(0.02)
        GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.12)
        self._cmd(0x01); time.sleep(0.15)                     # SWRESET
        self._cmd(0x11); time.sleep(0.12)                     # SLPOUT
        self._cmd(0x36, [0x00])                               # MADCTL portrait native scan, RGB order (measured on this panel: MX mirrors, BGR swaps R/B)
        self._cmd(0x3A, [0x55])                               # COLMOD 16-bit
        self._cmd(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])       # PORCTRL
        self._cmd(0xB7, [0x35])                               # GCTRL
        self._cmd(0xBB, [0x19])                               # VCOMS
        self._cmd(0xC0, [0x2C])                               # LCMCTRL
        self._cmd(0xC2, [0x01])                               # VDVVRHEN
        self._cmd(0xC3, [0x12])                               # VRHS
        self._cmd(0xC4, [0x20])                               # VDVS
        self._cmd(0xC6, [0x0F])                               # FRCTRL2
        self._cmd(0xD0, [0xA4, 0xA1])                         # PWCTRL1
        self._cmd(0xE0, [0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,
                         0x4C,0x18,0x0D,0x0B,0x1F,0x23])       # PVGAMCTRL
        self._cmd(0xE1, [0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,
                         0x51,0x2F,0x1F,0x1F,0x20,0x23])       # NVGAMCTRL
        self._cmd(0x21)                                       # INVON (this panel needs it)
        self._cmd(0x13)                                       # NORON
        self._cmd(0x29); time.sleep(0.02)                     # DISPON

    def show(self, img):
        img = img.resize((W, H)).convert("RGB").transpose(Image.ROTATE_90)
        arr = np.asarray(img).astype(np.uint16)
        rgb565 = ((arr[:, :, 0] >> 3) << 11) | ((arr[:, :, 1] >> 2) << 5) | (arr[:, :, 2] >> 3)
        data = rgb565.astype(">u2").tobytes()
        self._cmd(0x2A, [0x00, 0x00, (PW - 1) >> 8, (PW - 1) & 0xFF])
        self._cmd(0x2B, [0x00, 0x00, (PH - 1) >> 8, (PH - 1) & 0xFF])
        GPIO.output(PIN_DC, GPIO.LOW)
        self.spi.writebytes([0x2C])
        GPIO.output(PIN_DC, GPIO.HIGH)
        for i in range(0, len(data), 4096):
            self.spi.writebytes(data[i:i + 4096])

# ── Color rendering: same fields as the e-Paper version ────────────────────
BG     = (11, 16, 38)       # dark navy
HEADER = (0, 95, 143)       # deep cyan-blue
WHITE  = (255, 255, 255)
CYAN   = (0, 229, 255)
YELLOW = (255, 213, 79)
ORANGE = (255, 145, 60)
GREY   = (120, 140, 170)
GREEN  = (76, 255, 120)
RED    = (255, 82, 82)
BLUE   = (64, 156, 255)
PURPLE = (199, 125, 255)

def level_color(pct):
    return GREEN if pct < 50 else (YELLOW if pct < 80 else RED)

def cbar(draw, x, y, w, h, pct, color):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, outline=GREY, width=1)
    inner = int((w - 4) * min(pct, 100) / 100)
    if inner > 0:
        draw.rounded_rectangle([x + 2, y + 2, x + 2 + inner, y + h - 2], radius=2, fill=color)

def render(info):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = epd_src.get_font(21, bold=True)
    f_row   = epd_src.get_font(17, bold=True)
    f_small = epd_src.get_font(14)

    d.rectangle([0, 0, W - 1, 36], fill=HEADER)
    d.text((8, 7), info["hostname"], font=f_title, fill=WHITE)
    t = info["time"]
    tw = d.textlength(t, font=f_title)
    d.text((W - tw - 8, 7), t, font=f_title, fill=YELLOW)

    y = 42
    if info["ips"]:
        for iface, ip in info["ips"].items():
            d.text((8, y), f"{iface[:6]}:" if iface else "IP:", font=f_small, fill=CYAN)
            d.text((64, y), ip, font=f_row, fill=WHITE)
            y += 21
    else:
        d.text((8, y), "IP: No network", font=f_row, fill=RED)
        y += 21

    y += 2
    d.line([(8, y), (W - 8, y)], fill=GREY); y += 8

    pct = info["cpu_usage"]
    d.text((8, y), f"CPU {pct}%", font=f_row, fill=WHITE)
    if info["cpu_temp"] is not None:
        ts = f"{info["cpu_temp"]:.0f}C"
        tw = d.textlength(ts, font=f_row)
        d.text((W - tw - 8, y), ts, font=f_row, fill=ORANGE)
    y += 22
    cbar(d, 8, y, W - 16, 12, pct, level_color(pct)); y += 20

    d.text((8, y), f"RAM {info["mem_used"]}M", font=f_row, fill=WHITE)
    ps = f"{info["mem_pct"]}%"
    tw = d.textlength(ps, font=f_row)
    d.text((W - tw - 8, y), ps, font=f_row, fill=BLUE)
    y += 22
    cbar(d, 8, y, W - 16, 12, info["mem_pct"], BLUE); y += 20

    d.text((8, y), f"DSK {info["disk_used"]}G", font=f_row, fill=WHITE)
    ps = f"{info["disk_pct"]}%"
    tw = d.textlength(ps, font=f_row)
    d.text((W - tw - 8, y), ps, font=f_row, fill=PURPLE)
    y += 22
    cbar(d, 8, y, W - 16, 12, info["disk_pct"], PURPLE); y += 14

    d.line([(8, y), (W - 8, y)], fill=GREY); y += 6
    d.text((8, y), f"Up {info["uptime"]}", font=f_small, fill=ORANGE)
    dt = info["date"]
    tw = d.textlength(dt, font=f_small)
    d.text((W - tw - 8, y), dt, font=f_small, fill=CYAN)

    d.rectangle([0, 0, W - 1, H - 1], outline=CYAN)
    return img

def main():
    once = "--once" in sys.argv
    lcd = ST7789()
    while True:
        try:
            lcd.show(render(epd_src.collect_system_info()))
            print("frame pushed", flush=True)
        except Exception as e:
            print(f"render/push error: {e}", flush=True)
        if once:
            break
        time.sleep(60)

if __name__ == "__main__":
    main()
