# Display software for the Pi Zero LCD console case

Two ways to drive the GMT024-08 panel once it's wired up (see the wiring
table in the main README). **Pick one — they are mutually exclusive.** The
kernel console (Mode 1) owns the panel through a framebuffer driver; the
stats display (Mode 2) drives the panel directly over SPI from userspace.
The stats script will not work while the console overlay is in place, and
the console will not appear while the stats script is running.

Both modes assume the wiring in the main README: CS on CE1 (GPIO 7,
spidev0.1), RST on GPIO 25, DC on GPIO 24.

## Mode 1 — the LCD as a live CLI console

This is the setup the reference build runs today: the panel becomes the
Pi's real login console (tty1) — boot messages, the login prompt, and a
working shell, no HDMI monitor needed. Add a USB keyboard and it's a
self-contained micro terminal.

1. Open the boot config:

   ```
   sudo nano /boot/firmware/config.txt
   ```

   (On older Raspberry Pi OS images the path is `/boot/config.txt`.)

2. Add this line at the end:

   ```
   dtoverlay=fbtft,spi0-1,st7789v,reset_pin=25,dc_pin=24,rotate=90
   ```

3. Reboot. The kernel registers the panel as `/dev/fb0`
   (fb_st7789v, 320x240) and maps console 1 to it — the login prompt
   appears on the little screen and survives reboots on its own.

Notes:

- The pin numbers in the overlay are BCM GPIOs and must match the wiring:
  `reset_pin=25` and `dc_pin=24`, and `spi0-1` selects CE1, matching the
  CS wire on pin 26.
- fbtft is a staging driver; a warning about it in `dmesg` is expected
  and harmless.
- To go back to the stats display, remove the line (or comment it out)
  and reboot.

## Mode 2 — system stats display (Python)

A Python script drives the panel directly over SPI with a hand-rolled
ST7789 driver and draws a status page, refreshed every 60 seconds:

- Header: hostname and time
- IP address of each network interface
- CPU load and temperature, with a bar
- RAM use, with a bar
- Disk use, with a bar
- Footer: uptime and date

Requirements: Python 3 with `spidev`, `RPi.GPIO`, `numpy` and `Pillow`,
SPI enabled (`sudo raspi-config` → Interface Options → SPI), and **no**
fbtft overlay from Mode 1 in the boot config.

Files in this folder:

- `lcd_display.py` — the stats display itself, including the hand-rolled
  ST7789 driver (init sequence measured on this exact panel).
- `display.py` — the author's earlier Waveshare 2.13" e-Paper status
  script. `lcd_display.py` imports two helpers from it
  (`collect_system_info()` and `get_font()`), so it has to sit alongside.
  One wart, stated plainly: `display.py` looks for the Waveshare
  `waveshare_epd` library at import time and exits if it can't find it —
  on the reference build the library is installed because the e-Paper
  display came first. If you only want the LCD stats and don't have the
  e-Paper library, lift the two helper functions into `lcd_display.py`
  instead of importing the module.
- `lcd_console_preview.py` — a one-off helper from the build: renders a
  real shell session transcript onto the panel at true framebuffer-console
  geometry, to preview the Mode 1 look before switching. Not needed by
  either mode.

Run:

```
python3 ~/lcd_display.py            # 60-second refresh loop, Ctrl-C stops
python3 ~/lcd_display.py --once     # draw a single frame (quick test)
```
