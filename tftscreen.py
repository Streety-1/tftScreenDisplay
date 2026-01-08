#!/usr/bin/env python3
import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Display configuration
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
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)

# Image buffer
image = Image.new("RGB", (240, 240))
draw = ImageDraw.Draw(image)

font = ImageFont.load_default()

while True:
    draw.rectangle((0, 0, 240, 240), fill=(0, 0, 0))
    draw.text((10, 10), "Pi Zero Status", font=font, fill=(0, 255, 0))
    draw.text((10, 30), time.strftime("%H:%M:%S"), font=font, fill=(255, 255, 255))
    display.image(image)
    time.sleep(1)
