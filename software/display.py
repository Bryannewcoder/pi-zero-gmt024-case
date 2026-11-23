#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║  Waveshare 2.13" e-Paper System Info Display         ║
║  Raspberry Pi Zero WH                                ║
║                                                      ║
║  Usage:                                              ║
║    python3 display.py              # run once        ║
║    python3 display.py --loop       # refresh every 60s ║
║    python3 display.py --interval 30  # custom seconds ║
║    python3 display.py --version V4  # force EPD version ║
╚══════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import socket
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ── Add waveshare lib to path ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()

# Search for waveshare_epd lib in common locations
search_paths = [
    SCRIPT_DIR / "waveshare_epd",
    SCRIPT_DIR / "lib" / "waveshare_epd",
    Path.home() / "e-Paper/RaspberryPi_JetsonNano/python/lib",
    Path("/usr/local/lib/python3/dist-packages/waveshare_epd"),
]

lib_found = False
for p in search_paths:
    if p.is_dir() or (p.parent.is_dir() and (p.parent / "waveshare_epd").exists()):
        target = p if p.name == "waveshare_epd" else p / "waveshare_epd"
        sys.path.insert(0, str(p.parent if p.name == "waveshare_epd" else p))
        lib_found = True
        break

if not lib_found:
    # Last resort: check if it's installed as a package
    try:
        import waveshare_epd
        lib_found = True
    except ImportError:
        print("❌ waveshare_epd library not found.")
        print("   Run: bash install.sh")
        sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ Pillow not installed. Run: pip3 install Pillow --break-system-packages")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM INFO GATHERING
# ══════════════════════════════════════════════════════════════════════════════

def get_ip_addresses():
    """Return dict of interface → IP for all active interfaces."""
    ips = {}
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show"],
            capture_output=True, text=True, timeout=3
        )
        iface = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith(("eth", "wlan", "usb", "end", "en", "wl")):
                iface = line.split(":")[0].strip()
            elif line.startswith("inet ") and iface:
                ip = line.split()[1].split("/")[0]
                if ip != "127.0.0.1":
                    ips[iface] = ip
    except Exception:
        pass

    # Fallback
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips[""] = s.getsockname()[0]
            s.close()
        except Exception:
            ips[""] = "No network"
    return ips


def get_cpu_temp():
    """Return CPU temperature in °C as float, or None."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        try:
            result = subprocess.run(
                ["vcgencmd", "measure_temp"],
                capture_output=True, text=True, timeout=2
            )
            temp_str = result.stdout.strip().replace("temp=", "").replace("'C", "")
            return float(temp_str)
        except Exception:
            return None


def get_cpu_usage():
    """Return CPU usage percent as float."""
    try:
        # Read /proc/stat twice with a short sleep for accurate reading
        def read_stat():
            with open("/proc/stat") as f:
                line = f.readline()
            vals = list(map(int, line.split()[1:]))
            idle = vals[3]
            total = sum(vals)
            return idle, total

        idle1, total1 = read_stat()
        time.sleep(0.1)
        idle2, total2 = read_stat()
        idle_delta = idle2 - idle1
        total_delta = total2 - total1
        if total_delta == 0:
            return 0.0
        return round(100.0 * (1 - idle_delta / total_delta), 1)
    except Exception:
        return 0.0


def get_memory_info():
    """Return (used_mb, total_mb, percent) as floats."""
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            parts = line.split()
            info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", 0)
        used = total - available
        pct = round(100 * used / total, 1) if total > 0 else 0
        return used // 1024, total // 1024, pct
    except Exception:
        return 0, 0, 0


def get_disk_info():
    """Return (used_gb, total_gb, percent) for root partition."""
    try:
        result = subprocess.run(
            ["df", "-BM", "/"],
            capture_output=True, text=True, timeout=3
        )
        lines = result.stdout.strip().splitlines()
        parts = lines[1].split()
        total = int(parts[1].rstrip("M"))
        used = int(parts[2].rstrip("M"))
        pct = int(parts[4].rstrip("%"))
        return used // 1024, total // 1024, pct
    except Exception:
        return 0, 0, 0


def get_uptime():
    """Return uptime as formatted string like '2d 3h 15m'."""
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        d = int(seconds // 86400)
        h = int((seconds % 86400) // 3600)
        m = int((seconds % 3600) // 60)
        if d > 0:
            return f"{d}d {h}h {m}m"
        elif h > 0:
            return f"{h}h {m}m"
        else:
            return f"{m}m"
    except Exception:
        return "?"


def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "raspberry"


def collect_system_info():
    """Collect all system info into a dict."""
    ips = get_ip_addresses()
    used_mem, total_mem, mem_pct = get_memory_info()
    used_disk, total_disk, disk_pct = get_disk_info()
    cpu_temp = get_cpu_temp()
    cpu_usage = get_cpu_usage()

    return {
        "hostname": get_hostname(),
        "ips": ips,
        "cpu_usage": cpu_usage,
        "cpu_temp": cpu_temp,
        "mem_used": used_mem,
        "mem_total": total_mem,
        "mem_pct": mem_pct,
        "disk_used": used_disk,
        "disk_total": total_disk,
        "disk_pct": disk_pct,
        "uptime": get_uptime(),
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%b %d %Y"),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DISPLAY RENDERING
# ══════════════════════════════════════════════════════════════════════════════

# 2.13" display is 250×122 pixels (landscape when rotated)
EPD_WIDTH  = 250
EPD_HEIGHT = 122

def get_font(size, bold=False):
    """Try to load DejaVu font, fall back to default."""
    font_names_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    candidates = font_names_bold if bold else font_names
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def bar(draw, x, y, w, h, pct, fill=0):
    """Draw a simple percentage bar."""
    draw.rectangle([x, y, x + w, y + h], outline=fill)
    inner_w = int((w - 2) * min(pct, 100) / 100)
    if inner_w > 0:
        draw.rectangle([x + 1, y + 1, x + 1 + inner_w, y + h - 1], fill=fill)


def render_image(info: dict) -> Image.Image:
    """
    Render all system info onto a 250×122 black-and-white image.
    Layout (landscape):
      ┌─────────────────────────────────────────┐
      │ 🖥 hostname              HH:MM  Jan 01  │  ← row 0: header
      ├─────────────────────────────────────────┤
      │ IP  wlan0: 192.168.1.42                 │  ← row 1: IP(s)
      │     eth0:  10.0.0.5                     │
      ├─────────────────────────────────────────┤
      │ CPU  12.4%  [████████░░░░░░]  45.2°C    │  ← row 2: CPU
      │ RAM  312/512 MB (61%)  [██████░░░░░░]   │  ← row 3: RAM
      │ DSK  4/16 GB   (25%)  [███░░░░░░░░░]   │  ← row 4: Disk
      ├─────────────────────────────────────────┤
      │ UP  2d 3h 15m                           │  ← row 5: uptime
      └─────────────────────────────────────────┘
    """
    img = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)  # 255 = white
    draw = ImageDraw.Draw(img)

    BLACK = 0
    WHITE = 255

    f_tiny  = get_font(9)
    f_small = get_font(10)
    f_med   = get_font(11)
    f_bold  = get_font(11, bold=True)
    f_big   = get_font(13, bold=True)

    # ── Header bar ───────────────────────────────────────────────────────────
    draw.rectangle([0, 0, EPD_WIDTH - 1, 17], fill=BLACK)
    hostname = info["hostname"][:14]
    draw.text((3, 3), hostname, font=f_bold, fill=WHITE)
    time_str = f"{info['time']}  {info['date']}"
    # Right-align time
    bbox = draw.textbbox((0, 0), time_str, font=f_tiny)
    tw = bbox[2] - bbox[0]
    draw.text((EPD_WIDTH - tw - 3, 4), time_str, font=f_tiny, fill=WHITE)

    # ── IP addresses ─────────────────────────────────────────────────────────
    y = 20
    ips = info["ips"]
    if ips:
        for iface, ip in list(ips.items())[:2]:  # max 2 IPs
            label = f"{iface[:6]}:" if iface else "IP:"
            draw.text((2, y), label, font=f_tiny, fill=BLACK)
            draw.text((38, y), ip, font=f_bold, fill=BLACK)
            y += 12
    else:
        draw.text((2, y), "IP: No network", font=f_small, fill=BLACK)
        y += 12

    y = max(y, 44)  # ensure we don't overlap next section

    # ── Divider ──────────────────────────────────────────────────────────────
    draw.line([(0, y - 2), (EPD_WIDTH, y - 2)], fill=BLACK, width=1)

    # ── CPU ──────────────────────────────────────────────────────────────────
    cpu_label = f"CPU {info['cpu_usage']}%"
    draw.text((2, y), cpu_label, font=f_tiny, fill=BLACK)
    bar(draw, 58, y + 2, 110, 8, info["cpu_usage"])
    if info["cpu_temp"] is not None:
        temp_str = f"{info['cpu_temp']:.1f}C"
        draw.text((172, y), temp_str, font=f_tiny, fill=BLACK)
    y += 13

    # ── RAM ──────────────────────────────────────────────────────────────────
    ram_label = f"RAM {info['mem_used']}M"
    draw.text((2, y), ram_label, font=f_tiny, fill=BLACK)
    bar(draw, 58, y + 2, 110, 8, info["mem_pct"])
    draw.text((172, y), f"{info['mem_pct']}%", font=f_tiny, fill=BLACK)
    y += 13

    # ── Disk ─────────────────────────────────────────────────────────────────
    disk_label = f"DSK {info['disk_used']}G"
    draw.text((2, y), disk_label, font=f_tiny, fill=BLACK)
    bar(draw, 58, y + 2, 110, 8, info["disk_pct"])
    draw.text((172, y), f"{info['disk_pct']}%", font=f_tiny, fill=BLACK)
    y += 13

    # ── Divider ──────────────────────────────────────────────────────────────
    draw.line([(0, y), (EPD_WIDTH, y)], fill=BLACK, width=1)
    y += 2

    # ── Uptime ───────────────────────────────────────────────────────────────
    up_str = f"UP  {info['uptime']}"
    draw.text((2, y), up_str, font=f_tiny, fill=BLACK)

    # ── Border ───────────────────────────────────────────────────────────────
    draw.rectangle([0, 0, EPD_WIDTH - 1, EPD_HEIGHT - 1], outline=BLACK)

    return img


# ══════════════════════════════════════════════════════════════════════════════
#  EPD DRIVER — auto-detect version
# ══════════════════════════════════════════════════════════════════════════════

def load_epd(version_hint: str = None):
    """
    Try to load the correct EPD driver for 2.13" display.
    Returns initialized EPD object.
    """
    candidates = []

    if version_hint:
        # User specified version — try that first
        v = version_hint.upper().replace("V", "")
        candidates = [
            f"epd2in13_V{v}",
            f"epd2in13_{version_hint}",
            "epd2in13",
        ]
    else:
        # Auto-detect order: newest to oldest
        candidates = [
            "epd2in13_V4",
            "epd2in13_V3",
            "epd2in13_V2",
            "epd2in13",
        ]

    last_err = None
    for module_name in candidates:
        try:
            import importlib
            module = importlib.import_module(f"waveshare_epd.{module_name}")
            epd = module.EPD()
            print(f"  ✓ Loaded driver: {module_name}")
            return epd, module_name
        except ImportError as e:
            last_err = e
            continue
        except Exception as e:
            last_err = e
            continue

    raise ImportError(
        f"Could not load any EPD 2.13 driver. Last error: {last_err}\n"
        "Try specifying --version V2, V3, or V4"
    )


def display_on_epaper(img: Image.Image, epd, module_name: str):
    """Initialize EPD, push image, then sleep the display."""
    print("  → Initializing display...")
    epd.init()

    # Rotate image: the HAT is physically landscape but library expects portrait
    # Rotate 90° for landscape orientation on the 250×122 panel
    img_rotated = img.rotate(0)  # Already rendered in correct orientation

    print("  → Clearing display...")
    epd.Clear(0xFF)

    print("  → Sending image...")
    epd.display(epd.getbuffer(img_rotated))

    print("  → Putting display to sleep...")
    epd.sleep()
    print("  ✓ Display updated!")


def display_preview(img: Image.Image):
    """Save a PNG preview for debugging without real hardware."""
    preview_path = Path(SCRIPT_DIR) / "preview.png"
    # Scale up for easier viewing
    preview = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    preview.save(str(preview_path))
    print(f"  ✓ Preview saved to: {preview_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_once(epd=None, module_name=None, args=None, dry_run=False):
    print("\n  📊 Collecting system info...")
    info = collect_system_info()

    # Print to terminal too
    print(f"     Hostname : {info['hostname']}")
    for iface, ip in info['ips'].items():
        print(f"     IP ({iface:6}): {ip}")
    print(f"     CPU      : {info['cpu_usage']}%  |  Temp: {info['cpu_temp']}°C")
    print(f"     RAM      : {info['mem_used']}MB / {info['mem_total']}MB  ({info['mem_pct']}%)")
    print(f"     Disk     : {info['disk_used']}GB / {info['disk_total']}GB  ({info['disk_pct']}%)")
    print(f"     Uptime   : {info['uptime']}")

    print("\n  🖼  Rendering image...")
    img = render_image(info)

    if dry_run:
        display_preview(img)
    else:
        display_on_epaper(img, epd, module_name)


def main():
    parser = argparse.ArgumentParser(
        description="Waveshare 2.13\" e-Paper System Info Display"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Keep running, refreshing display on interval"
    )
    parser.add_argument(
        "--interval", type=int, default=60,
        help="Refresh interval in seconds when using --loop (default: 60)"
    )
    parser.add_argument(
        "--version", type=str, default=None,
        help="Force EPD driver version: V2, V3, or V4"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Dry-run: render to preview.png instead of real display"
    )
    args = parser.parse_args()

    print("")
    print("╔══════════════════════════════════════════════╗")
    print("║  Waveshare 2.13\" e-Paper Display             ║")
    print("╚══════════════════════════════════════════════╝")

    dry_run = args.preview

    if not dry_run:
        try:
            print("\n  Loading EPD driver...")
            epd, module_name = load_epd(args.version)
        except Exception as e:
            print(f"\n  ❌ Failed to load display driver: {e}")
            print("  Falling back to --preview mode (saves preview.png)")
            dry_run = True
            epd, module_name = None, None
    else:
        epd, module_name = None, None

    if args.loop:
        print(f"\n  🔄 Loop mode — refreshing every {args.interval}s  (Ctrl+C to stop)")
        try:
            while True:
                run_once(epd, module_name, args, dry_run)
                print(f"\n  ⏳ Next refresh in {args.interval}s...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n  Stopped by user.")
    else:
        run_once(epd, module_name, args, dry_run)

    print("")


if __name__ == "__main__":
    main()
