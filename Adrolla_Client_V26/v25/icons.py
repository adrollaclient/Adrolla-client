"""Gestochen scharfe Icons und Logo, zur Laufzeit mit Pillow gezeichnet.

Alle Icons liegen auf einem 24x24-Raster, werden 8-fach vergrößert gezeichnet und
weich herunterskaliert (Anti-Aliasing). Ohne Pillow liefert `get()` None, die
Oberfläche fällt dann auf Text zurück.
"""
import math

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:  # Pillow fehlt – Oberfläche nutzt Text
    Image = ImageDraw = ImageOps = None
try:
    from PIL import ImageTk
except Exception:  # kein Tk (z. B. Testumgebung)
    ImageTk = None

S = 8  # Zeichen-Überabtastung
_cache = {}


def available():
    return Image is not None


def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _stroke(d, pts, w, fill, closed=False):
    pts = [(x * S, y * S) for x, y in pts]
    if closed:
        pts = pts + [pts[0]]
    d.line(pts, fill=fill, width=int(w * S), joint="curve")
    r = w * S / 2
    for x, y in pts:
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def _circle(d, cx, cy, r, w, fill):
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S),
              outline=fill, width=int(w * S))


def _disc(d, cx, cy, r, fill):
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill)


def _rrect(d, x1, y1, x2, y2, r, fill=None, outline=None, w=2):
    d.rounded_rectangle((x1 * S, y1 * S, x2 * S, y2 * S), radius=r * S, fill=fill,
                        outline=outline, width=int(w * S))


def _home(d, c, w):
    _stroke(d, [(3, 11), (12, 3), (21, 11)], w, c)
    _stroke(d, [(5.5, 9.5), (5.5, 20), (18.5, 20), (18.5, 9.5)], w, c)
    _stroke(d, [(10, 20), (10, 14.5), (14, 14.5), (14, 20)], w, c)


def _mods(d, c, w):
    hexa = [(12, 2.8), (20.2, 7.4), (20.2, 16.6), (12, 21.2), (3.8, 16.6), (3.8, 7.4)]
    _stroke(d, hexa, w, c, closed=True)
    _stroke(d, [(3.8, 7.4), (12, 12), (20.2, 7.4)], w, c)
    _stroke(d, [(12, 12), (12, 21.2)], w, c)


def _modes(d, c, w):
    for x, y in ((3.5, 3.5), (13.5, 3.5), (3.5, 13.5), (13.5, 13.5)):
        _rrect(d, x, y, x + 7, y + 7, 2, outline=c, w=w)


def _profile(d, c, w):
    _circle(d, 12, 8, 4.2, w, c)
    d.arc((4 * S, 14 * S, 20 * S, 30 * S), 180, 360, fill=c, width=int(w * S))
    _stroke(d, [(4, 22), (4, 22)], w, c)
    _stroke(d, [(20, 22), (20, 22)], w, c)


def _settings(d, c, w):
    for i in range(8):
        a = math.radians(i * 45)
        _stroke(d, [(12 + 7.6 * math.cos(a), 12 + 7.6 * math.sin(a)),
                    (12 + 10 * math.cos(a), 12 + 10 * math.sin(a))], w + .6, c)
    _circle(d, 12, 12, 7.2, w, c)
    _circle(d, 12, 12, 2.8, w, c)


def _play(d, c, w):
    pts = [(7.5, 4.5), (19.5, 12), (7.5, 19.5)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=c)
    _stroke(d, pts, 2, c, closed=True)


def _stop(d, c, w):
    _rrect(d, 5.5, 5.5, 18.5, 18.5, 2.5, fill=c)


def _search(d, c, w):
    _circle(d, 10.5, 10.5, 6.3, w, c)
    _stroke(d, [(15.2, 15.2), (20.5, 20.5)], w, c)


def _download(d, c, w):
    _stroke(d, [(12, 3.5), (12, 15)], w, c)
    _stroke(d, [(7, 10.5), (12, 15.5), (17, 10.5)], w, c)
    _stroke(d, [(4.5, 20), (19.5, 20)], w, c)


def _folder(d, c, w):
    _stroke(d, [(3, 7), (3, 19), (21, 19), (21, 9), (11.5, 9), (9.5, 6), (3, 6), (3, 7)], w, c)


def _trash(d, c, w):
    _stroke(d, [(4, 6.5), (20, 6.5)], w, c)
    _stroke(d, [(9, 6.5), (9, 4), (15, 4), (15, 6.5)], w, c)
    _stroke(d, [(6, 6.5), (7, 20.5), (17, 20.5), (18, 6.5)], w, c)


def _plus(d, c, w):
    _stroke(d, [(12, 5), (12, 19)], w, c)
    _stroke(d, [(5, 12), (19, 12)], w, c)


def _check(d, c, w):
    _stroke(d, [(4.5, 12.5), (9.5, 17.5), (19.5, 6.5)], w, c)


def _close(d, c, w):
    _stroke(d, [(6, 6), (18, 18)], w, c)
    _stroke(d, [(18, 6), (6, 18)], w, c)


def _user(d, c, w):
    _profile(d, c, w)


def _refresh(d, c, w):
    d.arc((4 * S, 4 * S, 20 * S, 20 * S), 30, 300, fill=c, width=int(w * S))
    _stroke(d, [(15.5, 3.5), (20, 6.5), (16, 10)], w, c)


def _globe(d, c, w):
    _circle(d, 12, 12, 9, w, c)
    d.ellipse((7.5 * S, 3 * S, 16.5 * S, 21 * S), outline=c, width=int(w * S))
    _stroke(d, [(3, 12), (21, 12)], w, c)


DRAW = {"home": _home, "mods": _mods, "modes": _modes, "profile": _profile,
        "settings": _settings, "play": _play, "stop": _stop, "search": _search,
        "download": _download, "folder": _folder, "trash": _trash, "plus": _plus,
        "check": _check, "close": _close, "user": _user, "refresh": _refresh,
        "globe": _globe}


def render(name, color, size=22, stroke=1.9):
    """Gibt ein PIL-Image zurück (RGBA, transparent)."""
    if Image is None:
        return None
    big = Image.new("RGBA", (24 * S, 24 * S), (0, 0, 0, 0))
    DRAW[name](ImageDraw.Draw(big), _rgb(color) + (255,), stroke)
    return big.resize((size, size), Image.LANCZOS)


def get(name, color, size=22, stroke=1.9):
    """Tk-PhotoImage mit Zwischenspeicher (Referenz bleibt im Cache erhalten)."""
    if Image is None or ImageTk is None:
        return None
    key = (name, color, size, stroke)
    if key not in _cache:
        _cache[key] = ImageTk.PhotoImage(render(name, color, size, stroke))
    return _cache[key]


def draw_logo(size=256, accent="#d95e68", accent2="#e98890", bg="#15121a", rounded=True):
    """Saturn-Logo: Planet mit Verlauf, geneigter Ring mit korrekter Verdeckung."""
    if Image is None:
        return None
    N = size * 4
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    if bg:
        base = Image.new("RGBA", (N, N), _rgb(bg) + (255,))
        glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((N * .1, N * .1, N * .9, N * .9), fill=_rgb(accent) + (46,))
        base.alpha_composite(glow)
        mask = Image.new("L", (N, N), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, N - 1, N - 1),
                                              radius=int(N * (.22 if rounded else 0)), fill=255)
        img.paste(base, (0, 0), mask)
    cx = cy = N / 2
    r = N * .205
    # Planet mit vertikalem Farbverlauf
    planet = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    grad = Image.new("RGBA", (N, N))
    top, bot = _rgb(accent2), _rgb(accent)
    gd = ImageDraw.Draw(grad)
    for y in range(int(cy - r), int(cy + r) + 1):
        t = (y - (cy - r)) / (2 * r)
        gd.line([(0, y), (N, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
    pmask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(pmask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    planet.paste(grad, (0, 0), pmask)

    def ring(width_px, rx, ry, color, part):
        layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        box = (cx - rx, cy - ry, cx + rx, cy + ry)
        if part == "back":
            ld.arc(box, 180, 360, fill=color, width=width_px)
        else:
            ld.arc(box, 0, 180, fill=color, width=width_px)
        return layer.rotate(20, resample=Image.BICUBIC, center=(cx, cy))

    ring_color = _rgb(accent2) + (255,)
    img.alpha_composite(ring(int(N * .028), N * .40, N * .125, ring_color, "back"))
    img.alpha_composite(planet)
    img.alpha_composite(ring(int(N * .028), N * .40, N * .125, ring_color, "front"))
    # Glanzpunkt
    hi = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(hi).ellipse((cx - r * .55, cy - r * .62, cx - r * .05, cy - r * .2),
                               fill=(255, 255, 255, 60))
    img.alpha_composite(hi)
    return img.resize((size, size), Image.LANCZOS)


def logo_photo(size, accent, accent2, bg):
    if Image is None or ImageTk is None:
        return None
    key = ("logo", size, accent, accent2, bg)
    if key not in _cache:
        _cache[key] = ImageTk.PhotoImage(draw_galaxy(size, bg=bool(bg)))
    return _cache[key]


def write_app_icons(png_path, ico_path, accent="#d95e68", accent2="#e98890"):
    """PNG für das Fenster, ICO mit BMP-Einträgen (Tk/Windows-kompatibel, kein 256-px-PNG)."""
    draw_galaxy(256).save(png_path)
    master = draw_galaxy(128)
    master.save(ico_path, format="ICO", bitmap_format="bmp",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)])


def fit_image(path_or_bytes, size, radius=0.2):
    """Projekt-Icons von Modrinth: quadratisch zuschneiden, Ecken runden."""
    if Image is None or ImageTk is None:
        return None
    import io
    src = Image.open(io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes)
    src = src.convert("RGBA")
    side = min(src.size)
    left, top = (src.width - side) // 2, (src.height - side) // 2
    src = src.crop((left, top, left + side, top + side)).resize((size * 3, size * 3), Image.LANCZOS)
    mask = Image.new("L", src.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, src.width - 1, src.height - 1),
                                          radius=int(src.width * radius), fill=255)
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    return ImageTk.PhotoImage(out.resize((size, size), Image.LANCZOS))


def _falloff(strength):
    """Weicher Verlauf, der sicher bei 0 endet (radial_gradient erreicht am Rand nicht ganz 0)."""
    return lambda v: int(((max(0, v - 80) / 175) ** 1.6) * 255 * strength)


def draw_banner(w, h, accent="#d95e68", accent2="#e98890", bg="#1c1a1d"):
    """Dezentes Banner: weicher Farbschein, feine Sterne und ein angeschnittener Saturn rechts."""
    import random
    if Image is None:
        return None
    base = Image.new("RGB", (w, h), _rgb(bg))
    glow_mask = ImageOps.invert(Image.radial_gradient("L")).point(_falloff(.34))
    gw, gh = int(w * .85), int(h * 3.2)
    glow_mask = glow_mask.resize((gw, gh), Image.BILINEAR)
    base.paste(Image.new("RGB", (gw, gh), _rgb(accent)), (int(w * .72 - gw / 2), int(h * .5 - gh / 2)),
               glow_mask)
    violet = ImageOps.invert(Image.radial_gradient("L")).point(_falloff(.20)).resize(
        (int(w * .6), int(h * 2.6)), Image.BILINEAR)
    base.paste(Image.new("RGB", violet.size, (92, 62, 170)), (int(w * .30 - violet.width / 2),
               int(h * .55 - violet.height / 2)), violet)
    img = base.convert("RGBA")
    stars = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    rng = random.Random(11)
    for _ in range(max(40, w // 11)):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.choice((0.6, 0.8, 1.0, 1.4))
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(235, 228, 255, rng.randrange(40, 150)))
    img.alpha_composite(stars)
    planet = draw_logo(int(h * 1.7), accent, accent2, None)
    img.paste(planet, (w - int(planet.width * .82), int(h * .5 - planet.height * .5)), planet)
    return img


def banner_photo(w, h, accent, accent2, bg):
    if Image is None or ImageTk is None:
        return None
    key = ("banner", w, h, accent, accent2, bg)
    if key not in _cache:
        _cache[key] = ImageTk.PhotoImage(draw_banner(w, h, accent, accent2, bg))
    return _cache[key]


def draw_galaxy(size=256, bg=True, accent="#e98890"):
    """Spiralgalaxie: warmer Kern, zwei geschwungene Arme von Rosé über Violett zu Blau, feine Sterne."""
    import random
    if Image is None:
        return None
    from PIL import ImageFilter
    N = 1024
    rng = random.Random(5)
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    if bg:
        base = Image.new("RGBA", (N, N), (7, 6, 15, 255))
        halo = Image.radial_gradient("L").resize((N, N), Image.BILINEAR)
        halo = ImageOps.invert(halo).point(lambda v: int(((max(0, v - 80) / 175) ** 1.4) * 255 * .55))
        base.paste(Image.new("RGBA", (N, N), (58, 30, 104, 255)), (0, 0), halo)
        mask = Image.new("L", (N, N), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, N - 1, N - 1), radius=int(N * .22), fill=255)
        canvas.paste(base, (0, 0), mask)

    def arm_color(t):
        stops = [(0.0, (255, 226, 200)), (0.28, (240, 140, 160)), (0.65, (150, 110, 240)),
                 (1.0, (80, 150, 255))]
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                f = (t - t0) / (t1 - t0)
                return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))
        return stops[-1][1]

    gal = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    crisp = ImageDraw.Draw(gal)
    cx = cy = N / 2
    R = N * .44
    steps = 90
    for arm in range(2):
        phase = arm * 3.14159
        prev = None
        for i in range(steps + 1):
            t = i / steps
            r = R * (.07 + .93 * t ** .85)
            a = phase + t * 4.5
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if prev:
                width = int(N * (.075 * (1 - t) ** .7 + .012))
                alpha = int(235 * (1 - .55 * t))
                crisp.line([prev, (x, y)], fill=arm_color(t) + (alpha,), width=width)
                crisp.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2),
                              fill=arm_color(t) + (alpha,))
            prev = (x, y)
        for _ in range(520):  # feine Sterne entlang des Arms
            t = rng.random() ** .8
            r = R * (.07 + .93 * t ** .85)
            a = phase + t * 4.5
            off = rng.gauss(0, N * .035 * (.4 + t))
            ang = rng.random() * 6.283
            x = cx + r * math.cos(a) + off * math.cos(ang)
            y = cy + r * math.sin(a) + off * math.sin(ang)
            d = rng.choice((2, 3, 4, 6))
            crisp.ellipse((x - d, y - d, x + d, y + d), fill=(255, 245, 255, rng.randrange(120, 255)))
    glow = gal.filter(ImageFilter.GaussianBlur(N * .03))
    soft = gal.filter(ImageFilter.GaussianBlur(N * .006))
    layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    layer.alpha_composite(glow)
    layer.alpha_composite(soft)
    layer.alpha_composite(gal)
    core = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse((cx - N * .16, cy - N * .16, cx + N * .16, cy + N * .16), fill=(255, 190, 170, 120))
    core = core.filter(ImageFilter.GaussianBlur(N * .05))
    cd2 = ImageDraw.Draw(core)
    cd2.ellipse((cx - N * .07, cy - N * .07, cx + N * .07, cy + N * .07), fill=(255, 238, 220, 255))
    core = core.filter(ImageFilter.GaussianBlur(N * .012))
    layer.alpha_composite(core)
    # leicht gekippt wie eine echte Galaxie
    tilted = layer.resize((N, int(N * .80)), Image.LANCZOS).rotate(
        -24, resample=Image.BICUBIC, expand=True)
    tilted = tilted.resize((int(tilted.width * .98), int(tilted.height * .98)), Image.LANCZOS)
    canvas.alpha_composite(tilted, (max(0, (N - tilted.width) // 2), max(0, (N - tilted.height) // 2))
                           ) if tilted.width <= N and tilted.height <= N else canvas.alpha_composite(
        tilted.crop(((tilted.width - N) // 2, (tilted.height - N) // 2,
                     (tilted.width - N) // 2 + N, (tilted.height - N) // 2 + N)))
    stars = ImageDraw.Draw(canvas)
    for _ in range(70):
        x, y = rng.randrange(N), rng.randrange(N)
        r = rng.choice((2, 3, 4))
        stars.ellipse((x - r, y - r, x + r, y + r), fill=(235, 228, 255, rng.randrange(60, 190)))
    return canvas.resize((size, size), Image.LANCZOS)
