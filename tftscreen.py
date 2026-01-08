#!/usr/bin/env python3

import time
import socket
import subprocess
from pathlib import Path
from datetime import datetime

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# =========================
# USER CONFIG
# =========================
SCALE = 1.2          # <-- Adjust text/layout size
REFRESH_RATE = 1    # seconds

WIDTH = 240
HEIGHT = 240

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 180, 0)
RED = (180, 0, 0)
GRAY = (80, 80, 80)

# =========================
# DISPLAY INIT
# =========================
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=64000000,
    width=WIDTH,
    height=HEIGHT,
    x_offset=0,
    y_offset=80,
)

image = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(image)

# Fonts
try:
    font_title = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        int(18 * SCALE),
    )
    font_body = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        int(14 * SCALE),
    )
    font_small = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        int(12 * SCALE),
    )
except Exception:
    font_title = font_body = font_small = ImageFont.load_default()

# =========================
# STATUS FUNCTIONS
# =========================

def usb_connected():
    for udc in Path("/sys/class/udc").iterdir():
        if (udc / "state").read_text().strip() == "configured":
            return True
    return False


def serial_active():
    try:
        out = subprocess.check_output(["who"], text=True)
        return any(t in out for t in ("ttyGS0", "ttyAMA0", "ttyS0"))
    except Exception:
        return False


def internet_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except Exception:
        return False


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def get_uptime():
    try:
        with open("/proc/uptime") as f:
            seconds = int(float(f.readline().split()[0]))
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        return " ".join(parts)
    except Exception:
        return "unknown"

# =========================
# DRAW HELPERS
# =========================

def draw_status_line(y, label, value, ok):
    label_x = int(10 * SCALE)
    value_x = int(150 * SCALE)
    box_height = int(20 * SCALE)

    draw.text((label_x, y), label, font=font_body, fill=WHITE)

    bg = GREEN if ok else RED
    draw.rectangle(
        (value_x, y - 2, WIDTH - 10, y + box_height),
        fill=bg,
    )

    draw.text(
        (value_x + 5, y),
        value,
        font=font_body,
        fill=WHITE,
    )

# =========================
# MAIN LOOP
# =========================

while True:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BLACK)

    # Title
    title_text = "--[ Securo ]--"
    tw, th = draw.textsize(title_text, font=font_title)
    draw.text(((WIDTH - tw) // 2, 10), title_text, font=font_title, fill=WHITE)

    # Internet check first (used by time & IP)
    net = internet_connected()

    # Time (top right, only if internet)
    if net:
        now = datetime.now().strftime("%H:%M:%S")
        time_w, _ = draw.textsize(now, font=font_small)
        draw.text(
            (WIDTH - time_w - 6, 10),
            now,
            font=font_small,
            fill=GRAY,
        )

    y = int(50 * SCALE)
    line_gap = int(28 * SCALE)

    # USB
    usb = usb_connected()
    draw_status_line(y, "USB Connection", "YES" if usb else "NO", usb)
    y += line_gap

    # Serial
    serial = serial_active()
    draw_status_line(y, "Serial Connection", "ACTIVE" if serial else "IDLE", serial)
    y += line_gap

    # Internet
    draw_status_line(y, "Internet", "YES" if net else "NO", net)
    y += line_gap

    # IP
    ip = get_ip() if net else "0.0.0.0"
    draw_status_line(y, "Current IP", ip, net)
    y += line_gap

    # Runtime
    runtime = get_uptime()
    draw_status_line(y, "Securo Runtime", runtime, True)

    display.image(image)
    time.sleep(REFRESH_RATE)
