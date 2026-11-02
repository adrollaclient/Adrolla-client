from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random
from pathlib import Path


OUT = Path(__file__).parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080

# Layered charcoal background with a subtle Adrolla red-violet glow.
image = Image.new("RGB", (W, H), "#08080d")
pixels = image.load()
for y in range(H):
    vertical = y / H
    for x in range(W):
        dx = (x - W * 0.28) / W
        dy = (y - H * 0.48) / H
        glow = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy) * 2.3)
        edge = vertical * 5
        pixels[x, y] = (int(8 + glow * 15), int(8 + glow * 7 + edge), int(13 + glow * 23 + edge))

draw = ImageDraw.Draw(image, "RGBA")
random.seed(42)
for _ in range(240):
    x, y = random.randrange(W), random.randrange(H)
    radius = random.choice((1, 1, 2))
    alpha = random.randrange(28, 100)
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(226, 220, 255, alpha))

# Soft nebula haze and orbit lines, kept away from the central button column.
haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(haze, "RGBA")
hd.ellipse((40, 170, 940, 950), fill=(82, 44, 145, 42))
hd.ellipse((120, 300, 820, 760), fill=(192, 73, 105, 24))
haze = haze.filter(ImageFilter.GaussianBlur(100))
image = Image.alpha_composite(image.convert("RGBA"), haze)

# Saturn: a shaded planet with a broad, soft coral and lilac ring.
planet_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(planet_layer, "RGBA")
pd.ellipse((40, 330, 850, 760), outline=(176, 116, 236, 78), width=32)
pd.ellipse((55, 345, 835, 745), outline=(231, 102, 128, 125), width=9)
pd.ellipse((115, 365, 770, 720), outline=(255, 184, 193, 90), width=3)
pd.ellipse((240, 350, 650, 770), fill=(0, 0, 0, 0))
planet = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
planet_px = planet.load()
for y in range(500):
    for x in range(500):
        dx, dy = (x-250)/250, (y-250)/250
        radius = math.sqrt(dx*dx + dy*dy)
        if radius <= 1:
            light = max(0, 1 - math.sqrt((dx+0.38)**2 + (dy+0.3)**2))
            bands = 0.5 + 0.5 * math.sin(y * 0.085)
            shade = max(0.0, 1 - radius * 0.55)
            planet_px[x, y] = (int(55 + 85*light + 35*bands),
                               int(26 + 43*light + 10*bands),
                               int(47 + 75*light + 18*bands),
                               int(255 * min(1, shade + 0.38)))
pd2 = ImageDraw.Draw(planet)
for stripe_y, alpha in ((145, 35), (220, 48), (278, 32), (340, 43)):
    pd2.arc((0, stripe_y-45, 500, stripe_y+45), 188, 352,
            fill=(255, 183, 193, alpha), width=9)
planet_layer.alpha_composite(planet, (195, 300))
image = Image.alpha_composite(image, planet_layer)

# A restrained matte card behind the vanilla menu controls.
panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
panel_draw = ImageDraw.Draw(panel, "RGBA")
panel_draw.rounded_rectangle((500, 520, 1420, 1040), radius=42,
                             fill=(13, 13, 19, 170), outline=(225, 96, 112, 78), width=2)
image = Image.alpha_composite(image, panel)
draw = ImageDraw.Draw(image, "RGBA")

font_path = "C:/Windows/Fonts/segoeuib.ttf"
small_path = "C:/Windows/Fonts/segoeui.ttf"
try:
    brand_font = ImageFont.truetype(font_path, 46)
    subtitle_font = ImageFont.truetype(small_path, 18)
except OSError:
    brand_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
draw.text((105, 94), "ADROLLA", font=brand_font, fill=(248, 242, 248, 245), stroke_width=0)
draw.text((110, 151), "CLIENT  •  DEIN UNIVERSUM", font=subtitle_font,
          fill=(225, 105, 126, 235), stroke_width=0)
draw.line((110, 193, 300, 193), fill=(225, 96, 112, 165), width=3)
draw.text((110, 1015), "ADROLLA CLIENT", font=subtitle_font,
          fill=(226, 220, 236, 180), stroke_width=0)
draw.text((110, 1043), "YOUR UNIVERSE STARTS HERE", font=subtitle_font,
          fill=(225, 105, 126, 180), stroke_width=0)

image.convert("RGB").save(OUT / "adrolla_background.png", optimize=True)

# Rounded textures for FancyMenu vanilla button styling (normal and hover).
for filename, color, border, accent in (
    ("adrolla_button.png", (29, 27, 35, 238), (90, 73, 87, 255), (225, 96, 112, 255)),
    ("adrolla_button_hover.png", (57, 35, 48, 250), (231, 112, 128, 255), (255, 196, 205, 255)),
):
    button = Image.new("RGBA", (192, 64), (0, 0, 0, 0))
    bd = ImageDraw.Draw(button)
    bd.rounded_rectangle((2, 2, 189, 61), radius=17, fill=color, outline=border, width=2)
    bd.line((22, 5, 170, 5), fill=accent, width=2)
    button.save(OUT / filename, optimize=True)
