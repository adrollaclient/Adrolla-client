import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
import random
import math
import ctypes
from ctypes import wintypes
import base64
import hashlib
import secrets
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
try:
    import minecraft_launcher_lib
except ImportError:
    minecraft_launcher_lib = None
import re
import tkinter.font as tkfont
import icons
import loaders
import modrinth
import updater

# Adrolla Client - midnight / night-sky theme
BG = "#090909"
SIDEBAR = "#111111"
PANEL = "#171717"
CARD = "#1d1d1d"
CARD_HOVER = "#303030"
ACCENT = "#bdbdbd"
ACCENT2 = "#8f8f8f"
WHITE = "#f2f2f2"
MUTED = "#a0a0a0"
GREEN = "#ff5555"
BORDER = "#343434"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
MC_VERSIONS = [
    "26.3", "26.2", "26.1.1", "26.1",
    "1.21.11", "1.21.10", "1.21.9", "1.21.8", "1.21.7", "1.21.6",
    "1.21.5", "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
    "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
    "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19", "1.18.2", "1.18.1", "1.18",
    "1.17.1", "1.17", "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
    "1.15.2", "1.15.1", "1.15", "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
    "1.13.2", "1.13.1", "1.13", "1.12.2", "1.12.1", "1.12", "1.11.2", "1.11",
    "1.10.2", "1.10", "1.9.4", "1.9.2", "1.9", "1.8.9", "1.8.8", "1.8.7",
    "1.8.6", "1.8.5", "1.8.4", "1.8.3", "1.8.2", "1.8.1", "1.8",
    "1.7.10", "1.7.9", "1.7.8", "1.7.5", "1.7.2", "1.6.4", "1.6.2", "1.6.1",
    "1.5.2", "1.4.7", "1.4.6", "1.4.5", "1.4.4", "1.4.2", "1.3.2", "1.3.1",
    "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.1", "1.0"
]
DEFAULT_MSA_CLIENT_ID = "00000000402b5328"
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Adrolla Client")
SESSION_FILE = os.path.join(DATA_DIR, "accounts.dat")
PROFILES_DIR = os.path.join(DATA_DIR, "Profiles")
ICON_CACHE_DIR = os.path.join(DATA_DIR, "IconCache")
APP_VERSION = "25"


def read_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def update_config(**values):
    data = read_config()
    data.update(values)
    tmp = CONFIG_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CONFIG_FILE)
    except Exception:
        pass


def format_count(n):
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} Mio.".replace(".", ",")
    if n >= 10_000:
        return f"{n // 1000} Tsd."
    if n >= 1_000:
        return f"{n / 1000:.1f} Tsd.".replace(".", ",")
    return str(n)


def blend(c1, c2, t):
    a = [int(c1.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(c2.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def resource_path(filename):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def set_windows_app_user_model_id():
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Adrolla.Client")
        except Exception:
            pass

def _make_theme(accent, tint=0.14):
    """Erzeugt eine stimmige Palette aus einer Akzentfarbe: feste Helligkeitsstufen für die
    Flächen (leicht getönt), gut lesbarer Text und ein passender Hover-/Zweitakzent."""
    import colorsys
    r, g, b = (int(accent[k:k + 2], 16) / 255 for k in (1, 3, 5))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)

    def hls(lightness, saturation=None, h=hue):
        rgb = colorsys.hls_to_rgb(h, lightness, tint if saturation is None else saturation)
        return "#%02x%02x%02x" % tuple(round(c * 255) for c in rgb)

    return {"BG": hls(.045), "SIDEBAR": hls(.075), "PANEL": hls(.105), "CARD": hls(.14),
            "CARD_HOVER": hls(.19), "ACCENT": accent, "ACCENT2": hls(min(.84, light + .10), sat),
            "WHITE": hls(.95, .12), "MUTED": hls(.66, .07), "GREEN": hls(.70, .45, .39),
            "BORDER": hls(.25, tint * 1.1)}


THEMES = {
    "Adrolla Red": _make_theme("#e2606c", .13),
    "Black & Grey": _make_theme("#c4c8cd", .02),
    "Midnight Blue": _make_theme("#6f9df2", .16),
    "Purple Haze": _make_theme("#ab86e8", .15),
    "Emerald": _make_theme("#4fc99b", .13),
    "Sunset": _make_theme("#f2a366", .13),
}

def set_palette(name):
    global BG, SIDEBAR, PANEL, CARD, CARD_HOVER, ACCENT, ACCENT2, WHITE, MUTED, GREEN, BORDER
    palette = THEMES.get(name, THEMES["Black & Grey"])
    globals().update(palette)


class AuthError(Exception):
    pass

def http_json(url, data=None, headers=None):
    body = None
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
            msg = detail.get("errorMessage") or detail.get("error_description") or detail.get("Message") or raw
        except Exception:
            msg = raw or str(e)
        raise AuthError(f"HTTP {e.code}: {msg}") from e
    except Exception as e:
        raise AuthError(str(e)) from e

def load_client_id():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("client_id", "").strip() or DEFAULT_MSA_CLIENT_ID
    except Exception:
        return DEFAULT_MSA_CLIENT_ID


def _windows_protect(data, decrypt=False):
    if sys.platform != "win32":
        raise OSError("Sitzungsspeicherung ist nur unter Windows verfügbar.")

    class DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    source_buffer = ctypes.create_string_buffer(data)
    source = DataBlob(len(data), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        description = wintypes.LPWSTR()
        call = crypt32.CryptUnprotectData
        call.argtypes = [ctypes.POINTER(DataBlob), ctypes.POINTER(wintypes.LPWSTR),
                         ctypes.POINTER(DataBlob), wintypes.LPVOID, wintypes.LPVOID,
                         wintypes.DWORD, ctypes.POINTER(DataBlob)]
        call.restype = wintypes.BOOL
        ok = call(ctypes.byref(source), ctypes.byref(description), None, None, None,
                  0x1, ctypes.byref(result))
        if description:
            kernel32.LocalFree(ctypes.cast(description, ctypes.c_void_p))
    else:
        call = crypt32.CryptProtectData
        call.argtypes = [ctypes.POINTER(DataBlob), wintypes.LPCWSTR, ctypes.POINTER(DataBlob),
                         wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD,
                         ctypes.POINTER(DataBlob)]
        call.restype = wintypes.BOOL
        ok = call(ctypes.byref(source), "Adrolla Client account session", None, None, None,
                  0x1, ctypes.byref(result))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(result.pbData, ctypes.c_void_p))


def _minecraft_account_from_msa_token(client_id, token):
    ms_access = token["access_token"]
    rps_ticket = ms_access if client_id.lower() == DEFAULT_MSA_CLIENT_ID else "d=" + ms_access
    xbl = http_json("https://user.auth.xboxlive.com/user/authenticate", {
        "Properties": {"AuthMethod": "RPS", "SiteName": "user.auth.xboxlive.com", "RpsTicket": rps_ticket},
        "RelyingParty": "http://auth.xboxlive.com", "TokenType": "JWT"
    })
    xbl_token = xbl["Token"]
    user_hash = xbl["DisplayClaims"]["xui"][0]["uhs"]
    xsts = http_json("https://xsts.auth.xboxlive.com/xsts/authorize", {
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
        "RelyingParty": "rp://api.minecraftservices.com/", "TokenType": "JWT"
    })
    xsts_token = xsts["Token"]
    user_hash = xsts["DisplayClaims"]["xui"][0]["uhs"]
    mc = http_json("https://api.minecraftservices.com/authentication/login_with_xbox", {
        "identityToken": f"XBL3.0 x={user_hash};{xsts_token}"
    })
    mc_access = mc.get("access_token")
    if not mc_access:
        raise AuthError("Minecraft hat kein Zugriffstoken zurückgegeben.")
    profile = http_json("https://api.minecraftservices.com/minecraft/profile",
        headers={"Authorization": "Bearer " + mc_access})
    return {"name": profile.get("name") or "Minecraft-Spieler",
            "uuid": profile.get("id", ""), "minecraft_access_token": mc_access,
            "refresh_token": token.get("refresh_token", "")}


def refresh_minecraft_account(client_id, refresh_token):
    if client_id.lower() == DEFAULT_MSA_CLIENT_ID:
        endpoint = "https://login.live.com/oauth20_token.srf"
        form = {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "scope": "service::user.auth.xboxlive.com::MBI_SSL",
        }
    else:
        endpoint = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
        form = {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": "XboxLive.signin offline_access",
        }
    req = urllib.request.Request(endpoint, data=urllib.parse.urlencode(form).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            token = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("error_description") or raw
        except Exception:
            detail = raw or str(exc)
        raise AuthError("Die gespeicherte Microsoft-Sitzung konnte nicht erneuert werden: " + detail) from exc
    if not token.get("access_token"):
        raise AuthError("Microsoft hat beim Erneuern der Sitzung kein Zugriffstoken zurückgegeben.")
    return _minecraft_account_from_msa_token(client_id, token)

def _open_firefox(url):
    paths = [
        shutil.which("firefox"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Mozilla Firefox", "firefox.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Mozilla Firefox", "firefox.exe"),
    ]
    firefox = next((path for path in paths if path and os.path.isfile(path)), None)
    if firefox:
        subprocess.Popen([firefox, url])
        return
    try:
        webbrowser.get("firefox").open(url)
    except Exception as exc:
        raise AuthError("Firefox wurde nicht gefunden. Installiere Firefox oder setze ihn "
                        "als Standardbrowser.") from exc


def microsoft_to_minecraft(client_id, status_callback, prompt_redirect_url=None):
    if client_id.lower() == "00000000402b5328":
        # This legacy Minecraft Java client is registered for Microsoft's
        # desktop.srf redirect, not an arbitrary localhost redirect.
        redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        legacy_scope = "service::user.auth.xboxlive.com::MBI_SSL"
        state = secrets.token_urlsafe(24)
        auth_url = "https://login.live.com/oauth20_authorize.srf?" + urllib.parse.urlencode({
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": legacy_scope,
            "state": state,
            "locale": "de-DE",
        })
        status_callback("Firefox wird für die Microsoft-Anmeldung geöffnet …")
        _open_firefox(auth_url)
        if prompt_redirect_url is None:
            raise AuthError("Für diese Microsoft-App-ID muss nach dem Login die Rücksprung-URL "
                            "aus Firefox in Adrolla eingefügt werden.")
        pasted_url = prompt_redirect_url()
        try:
            parsed_url = urlsplit(pasted_url.strip())
            query = parse_qs(parsed_url.query)
        except Exception as exc:
            raise AuthError("Die eingefügte Microsoft-Rücksprung-URL ist ungültig.") from exc
        if parsed_url.hostname != "login.live.com" or parsed_url.path.rstrip("/") != "/oauth20_desktop.srf":
            raise AuthError("Bitte kopiere die vollständige URL aus der Firefox-Adressleiste, "
                            "nachdem Microsoft dich zu oauth20_desktop.srf zurückgeleitet hat.")
        if query.get("state", [None])[0] != state:
            raise AuthError("Der Anmeldeaufruf passt nicht zu dieser Sitzung. Bitte erneut anmelden.")
        if query.get("error"):
            raise AuthError("Microsoft-Anmeldung fehlgeschlagen: " + query.get(
                "error_description", query["error"])[0])
        code = query.get("code", [None])[0]
        if not code:
            raise AuthError("In der Rücksprung-URL wurde kein Anmeldecode gefunden.")
        form = urllib.parse.urlencode({
            "client_id": client_id,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "scope": legacy_scope,
        }).encode()
        req = urllib.request.Request(
            "https://login.live.com/oauth20_token.srf", data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                token = json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw).get("error_description") or raw
            except Exception:
                detail = raw or str(exc)
            raise AuthError("Microsoft konnte den Login-Code nicht einlösen: " + detail) from exc
        if not token.get("access_token"):
            raise AuthError("Microsoft hat kein Zugriffstoken zurückgegeben.")
    else:
        token = None
    # Native-app authorization code flow: Firefox handles the Microsoft sign-in,
    # then redirects to this temporary loopback listener in Adrolla.
    if token is None:
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
        state = secrets.token_urlsafe(32)
        response = {}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                response.update(parse_qs(urlsplit(self.path).query))
                body = ("<html><meta charset='utf-8'><title>Adrolla</title>"
                        "<body style='font:16px Segoe UI;background:#111;color:#eee;padding:40px'>"
                        "Anmeldung abgeschlossen. Du kannst dieses Fenster schließen und zu Adrolla "
                        "zurückkehren.</body></html>").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

    # Fixed loopback URI makes the value easy to register in Entra and avoids
    # redirect mismatches caused by a different ephemeral port on each login.
        redirect_uri = "http://localhost:53682"
        try:
            listener = HTTPServer(("localhost", 53682), CallbackHandler)
        except OSError as exc:
            raise AuthError("Der lokale Microsoft-Anmeldeport 53682 ist bereits belegt. "
                            "Schließe Adrolla und versuche es erneut.") from exc
        listener.timeout = 1
        auth_params = urllib.parse.urlencode({
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": "XboxLive.signin offline_access",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        })
        auth_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?" + auth_params
        status_callback("Firefox wird für die Microsoft-Anmeldung geöffnet …")
        try:
            _open_firefox(auth_url)
        except Exception:
            listener.server_close()
            raise

        deadline = time.time() + 300
        try:
            while time.time() < deadline and not response:
                listener.handle_request()
        finally:
            listener.server_close()
        if not response:
            raise AuthError("Die Microsoft-Anmeldung wurde nicht rechtzeitig abgeschlossen.")
        if response.get("state", [None])[0] != state:
            raise AuthError("Die Microsoft-Anmeldung konnte aus Sicherheitsgründen nicht zugeordnet werden."
                            " Bitte starte sie erneut.")
        if response.get("error"):
            detail = response.get("error_description", response["error"])[0]
            if "redirect_uri" in detail.lower() or "reply url" in detail.lower():
                detail += ("\n\nTrage in derselben App-Registrierung unter Authentifizierung → "
                           "Plattform hinzufügen → Mobile und Desktopanwendungen die Redirect-URI "
                           "http://localhost:53682 ein und speichere die Änderung.")
            raise AuthError("Microsoft-Anmeldung fehlgeschlagen: " + detail)
        auth_code = response.get("code", [None])[0]
        if not auth_code:
            raise AuthError("Microsoft hat keinen Anmeldecode zurückgegeben.")

        token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
        token_data = urllib.parse.urlencode({
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
            "scope": "XboxLive.signin offline_access",
        }).encode()
        token_req = urllib.request.Request(token_url, data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            with urllib.request.urlopen(token_req, timeout=25) as r:
                token = json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw).get("error_description") or raw
            except Exception:
                detail = raw or str(exc)
            raise AuthError("Microsoft konnte die Anmeldung nicht abschließen: " + detail) from exc
        if not token.get("access_token"):
            raise AuthError("Microsoft hat kein Zugriffstoken zurückgegeben.")

    status_callback("Microsoft bestätigt. Xbox Live wird geprüft …")
    account = _minecraft_account_from_msa_token(client_id, token)
    status_callback("Xbox Live bestätigt. Minecraft-Konto ist bereit …")
    return account


class RoundedButton(tk.Canvas):
    """Flacher, abgerundeter Button. Formen werden einmal gezeichnet; Hover blendet weich über."""
    def __init__(self, parent, text, command=None, bg="#252525", fg="#f2f2f2",
                 activebackground="#3a3a3a", font=("Segoe UI", 10, "bold"),
                 padx=18, pady=10, width=None, radius=12, icon_name=None, icon_size=18, **kwargs):
        self._text = text
        self._command = command
        self._normal_bg = bg
        self._hover_bg = activebackground
        self._fg = fg
        self._font = font
        self._padx = padx
        self._pady = pady
        self._radius = max(14, radius)
        self._enabled = True
        self._icon_name = icon_name if icons.available() else None
        self._icon_size = icon_size
        self._char_width = width
        self._icon_ref = None
        self._shape = None
        self._anim_job = None
        self._metrics = tkfont.Font(font=font)
        self._width, self._height = self._measure()
        super().__init__(parent, width=self._width, height=self._height, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self._current_bg = bg
        self._build()
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._click)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _parts(self):
        text_w = self._metrics.measure(self._text) if self._text else 0
        icon_w = self._icon_size if self._icon_name else 0
        return text_w, icon_w, (8 if text_w and icon_w else 0)

    def _measure(self):
        text_w, icon_w, gap = self._parts()
        if self._char_width:
            w = max(38, self._char_width * 9 + 2 * self._padx)
        else:
            w = max(38, text_w + icon_w + gap + 2 * self._padx)
        h = max(self._metrics.metrics("linespace"), icon_w) + 2 * self._pady
        return w, h

    def _points(self, x1, y1, x2, y2, r):
        return [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
                x1,y2, x1,y2-r, x1,y1+r, x1,y1]

    def _build(self):
        self.delete("all")
        self._shape = self.create_polygon(
            self._points(1, 1, self._width-1, self._height-1, self._radius), smooth=True,
            splinesteps=8, fill=self._current_bg, outline=self._current_bg)
        color = self._fg if self._enabled else blend(self._fg, self._current_bg, .55)
        text_w, icon_w, gap = self._parts()
        x = (self._width - (text_w + icon_w + gap)) / 2
        if icon_w:
            self._icon_ref = icons.get(self._icon_name, color, self._icon_size)
            if self._icon_ref:
                self.create_image(x, self._height / 2, image=self._icon_ref, anchor="w")
            x += icon_w + gap
        if self._text:
            self.create_text(x, self._height / 2, text=self._text, fill=color,
                             font=self._font, anchor="w")

    def _animate_bg(self, target, steps=5, delay=14):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        start = self._current_bg

        def step(i):
            self._current_bg = blend(start, target, i / steps)
            try:
                self.itemconfigure(self._shape, fill=self._current_bg, outline=self._current_bg)
            except tk.TclError:
                return
            self._anim_job = self.after(delay, lambda: step(i + 1)) if i < steps else None

        step(1)

    def _on_destroy(self, _event=None):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

    def _enter(self, _e=None):
        if self._enabled:
            self._animate_bg(self._hover_bg)

    def _leave(self, _e=None):
        if self._enabled:
            self._animate_bg(self._normal_bg)

    def _click(self, _e=None):
        if self._enabled and self._command: self._command()

    def configure(self, cnf=None, **kw):
        if isinstance(cnf, dict): kw.update(cnf)
        resize = False
        if "text" in kw: self._text = kw.pop("text"); resize = True
        if "icon_name" in kw:
            self._icon_name = kw.pop("icon_name") if icons.available() else None; resize = True
        if "bg" in kw: self._normal_bg = kw.pop("bg"); self._current_bg = self._normal_bg
        if "fg" in kw: self._fg = kw.pop("fg")
        if "activebackground" in kw: self._hover_bg = kw.pop("activebackground")
        if "state" in kw:
            self._enabled = kw.pop("state") != "disabled"
            self._current_bg = self._normal_bg
        result = super().configure(**kw) if kw else None
        if resize and not self._char_width:
            self._width, self._height = self._measure()
            super().configure(width=self._width, height=self._height)
        self._build()
        return result
    config = configure


class SmoothScroller:
    """Weiches Mausrad-Scrollen: nähert sich dem Ziel in kleinen, gebremsten Schritten."""
    def __init__(self, canvas, step=110):
        self.canvas, self.step = canvas, step
        self.target = None
        self.job = None

    def _metrics(self):
        box = self.canvas.bbox("all")
        total = (box[3] - box[1]) if box else 0
        return total, self.canvas.winfo_height()

    def scroll(self, notches):
        try:
            total, view = self._metrics()
            if total <= view:
                return
            current = self.canvas.yview()[0] * total
            base = self.target if self.target is not None else current
            self.target = min(max(base + notches * self.step, 0), total - view)
            if self.job is None:
                self._tick()
        except tk.TclError:
            self.reset()

    def _tick(self):
        try:
            total, view = self._metrics()
            current = self.canvas.yview()[0] * total
            diff = self.target - current
            if abs(diff) < 1.5:
                self.canvas.yview_moveto(self.target / total)
                self.target, self.job = None, None
                return
            self.canvas.yview_moveto((current + diff * .34) / total)
            self.canvas.update_idletasks()  # Schritt komplett malen, bevor der nächste kommt
            self.job = self.canvas.after(16, self._tick)
        except (tk.TclError, ZeroDivisionError, TypeError):
            self.target, self.job = None, None

    def reset(self):
        if self.job is not None:
            try:
                self.canvas.after_cancel(self.job)
            except tk.TclError:
                pass
        self.target, self.job = None, None


class AdrollaClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self._faded = self._prepare_fade(self)
        self.title("Adrolla Client")
        self._set_saturn_window_icon()
        self._fullscreen = False
        self._apply_monitor_size()
        self.configure(bg=BG)
        self.bind("<Escape>", self._escape_fullscreen)
        self.bind("<F11>", self._toggle_fullscreen_hotkey)
        self.accounts, self.account_name = self._load_persistent_sessions()
        self.auth_result = None
        self._session_refreshing = bool(self.account_name and
                                        self.accounts.get(self.account_name, {}).get("refresh_token"))
        self._pending_auth_result = None
        self._login_purpose = "online"
        self._login_in_progress = False
        self._launch_in_progress = False
        self._theme_installing = False
        self._skip_adrolla_theme_once = False
        self.game_process = None
        self._play_label, self._play_icon, self._play_enabled = "SPIELEN", "play", True
        self.active_page = "Startseite"
        self.mod_library_section = "mods"
        self.language = "Deutsch"
        self.theme = self._load_theme()
        self.profiles = self._load_profiles()
        saved_profile_dirs = read_config().get("profile_dirs", {})
        self.profile_dirs = dict(saved_profile_dirs) if isinstance(saved_profile_dirs, dict) else {}
        saved_descriptions = read_config().get("profile_descriptions", {})
        self.profile_descriptions = dict(saved_descriptions) if isinstance(saved_descriptions, dict) else {}
        self.profile_settings = self._load_profile_settings()
        saved_active = read_config().get("active_profile")
        self.active_profile = saved_active if saved_active in self.profiles else self.profiles[0]
        self.mod_section = "Mods"
        self._migrate_legacy_modes_to_profiles(
            self._load_selected_game_mode(), self._load_custom_modes())
        self.selected_version = self.profile_settings.get(self.active_profile, {}).get(
            "version") or self._load_selected_version()
        self.play_mode = self._load_play_mode()
        set_palette(self.theme)
        self._make_shell()
        self._start_intro_animation()
        self.show_page("Startseite")
        self._intro_layer.lift()
        if self._faded:
            self.after(10, lambda: self._fade_in(self))
        # Das Einblenden (Transparenz) erzeugt das Fenster-Handle neu: Symbol danach erneut setzen,
        # sonst zeigt die Taskleiste das Python-Symbol.
        for delay in (350, 1700):
            self.after(delay, self._set_saturn_window_icon)
        if self._session_refreshing:
            self.after(250, self._restore_saved_sessions)
            self.after(4000, self._check_for_updates)

    def _prepare_fade(self, window):
        try:
            window.attributes("-alpha", 0.0)
            window.after(1500, lambda: self._force_opaque(window))  # Sicherheitsnetz
            return True
        except tk.TclError:
            return False

    def _force_opaque(self, window):
        try:
            window.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

    def _fade_in(self, window, steps=8, delay=14):
        def step(i):
            try:
                window.attributes("-alpha", min(1.0, i / steps))
            except tk.TclError:
                return
            if i < steps:
                window.after(delay, lambda: step(i + 1))
        step(1)

    def _start_intro_animation(self):
        self._intro_layer = tk.Frame(self, bg="#05050b")
        self._intro_layer.place(relx=0, rely=0, relwidth=1, relheight=1)
        for sequence in ("<Button-1>", "<Key>"):
            self.bind(sequence, self._skip_intro, add="+")
        self._intro_canvas = tk.Canvas(self._intro_layer, bg="#05050b", highlightthickness=0)
        self._intro_canvas.pack(fill="both", expand=True)
        rng = random.Random(918)
        self._intro_stars = [(rng.random() * math.tau, rng.random(), rng.choice((1, 1, 1, 2)))
                             for _ in range(105)]
        self._intro_cloud_ids = []
        self._intro_arm_ids = []
        self._intro_arm_glow_ids = []
        self._intro_arm_base_points = []
        self._intro_arc_ids = []
        self._intro_star_ids = []
        self._intro_halo_ids = []
        self._intro_core_id = None
        self._intro_dot_id = None
        self._intro_wordmark_ids = []
        self._intro_bar_track_id = None
        self._intro_bar_progress_id = None
        self._intro_frame = 0
        self._animate_intro()

    def _skip_intro(self, _event=None):
        self._intro_frame = 10 ** 6

    def _animate_intro(self):
        if not self._intro_layer.winfo_exists():
            return
        canvas = self._intro_canvas
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width <= 1 or height <= 1:
            self.after(25, self._animate_intro)
            return
        scale = min(width, height)
        cx, cy = width / 2, height / 2
        frame = self._intro_frame
        galaxy_radius = min(width * .29, height * .46)
        clouds = [(-.12, "#49317f", 1.00, .010),
                  (.10, "#245279", .78, .013),
                  (.02, "#713d78", .55, .008)]
        for index, (offset, color, factor, wobble) in enumerate(clouds):
            # The nebula is intentionally static; moving it adds redraw work
            # without making the animation look meaningfully smoother.
            x = cx + math.cos(offset) * scale * wobble
            y = cy + math.sin(offset) * scale * wobble * .55
            rx, ry = galaxy_radius * factor, galaxy_radius * factor * .49
            box = (x-rx, y-ry, x+rx, y+ry)
            if frame == 0:
                self._intro_cloud_ids.append(canvas.create_oval(
                    *box, fill=color, outline="", stipple="gray75"))

        max_radius = galaxy_radius * .78
        if frame == 0:
            for arm in range(3):
                base_points = []
                for step in range(40):
                    ratio = .035 + step / 40 * .96
                    angle = arm * math.tau / 3 + ratio * 7.8
                    radius = ratio * max_radius
                    base_points.append((math.cos(angle) * radius,
                                        math.sin(angle) * radius * .54))
                self._intro_arm_base_points.append(base_points)
        rotation = frame * .022
        rotation_cos, rotation_sin = math.cos(rotation), math.sin(rotation)
        for arm in range(3):
            points = []
            for base_x, base_y in self._intro_arm_base_points[arm]:
                points.extend((cx + base_x * rotation_cos - base_y * rotation_sin,
                               cy + base_x * rotation_sin + base_y * rotation_cos))
            if frame == 0:
                self._intro_arm_glow_ids.append(canvas.create_line(
                    *points, fill="#7760b4", width=5, smooth=True,
                    splinesteps=10, stipple="gray75"))
                self._intro_arm_ids.append(canvas.create_line(
                    *points, fill=ACCENT2 if arm == 0 else "#a594e0",
                    width=1.5 if arm == 0 else 1, smooth=True, splinesteps=10,
                    stipple="gray50"))
            else:
                canvas.coords(self._intro_arm_glow_ids[arm], *points)
                canvas.coords(self._intro_arm_ids[arm], *points)

        orbit_w, orbit_h = galaxy_radius * 1.92, galaxy_radius * .83
        orbit_box = (cx-orbit_w/2, cy-orbit_h/2, cx+orbit_w/2, cy+orbit_h/2)
        if frame == 0:
            self._intro_arc_ids = [
                canvas.create_arc(*orbit_box, start=18, extent=148, style="arc",
                                  outline="#8f75d1", width=1),
                canvas.create_arc(*orbit_box, start=205, extent=128, style="arc",
                                  outline=ACCENT2, width=2),
            ]
        # The orbital arcs are static; only the spiral arms carry rotation.

        star_states = (enumerate(self._intro_stars) if frame == 0
                       else enumerate(self._intro_stars[:14]))
        for index, (angle, radius, size) in star_states:
            # Keep most of the starfield fixed and animate only a small set of
            # bright stars. This cuts per-frame canvas updates substantially.
            animated = index < 14
            spin = frame * (.0015 + (1 - radius) * .003) if animated else 0
            a = angle + spin
            r = radius * max_radius * (1 + .012 * math.sin(frame * .04 + index)) if animated else radius * max_radius
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r * .54
            glow = "#f2eaff" if index % 9 == 0 else "#b5b4d7"
            star_size = size * (1 + .12 * math.sin(frame * .04 + index)) if animated else size
            star_box = (x-star_size, y-star_size, x+star_size, y+star_size)
            if frame == 0:
                self._intro_star_ids.append(canvas.create_oval(
                    *star_box, fill=glow, outline=""))
            elif animated:
                canvas.coords(self._intro_star_ids[index], *star_box)

        core = scale * (.022 + .0025 * math.sin(frame * .08))
        for index, (halo, color) in enumerate(((3.8, "#593ba5"), (2.6, "#7957cc"),
                                               (1.55, "#b28bf0"))):
            radius = core * halo
            box = (cx-radius, cy-radius, cx+radius, cy+radius)
            if frame == 0:
                self._intro_halo_ids.append(canvas.create_oval(
                    *box, fill=color, outline="", stipple="gray50"))
        # Keep the broad glow layers fixed; pulse only the small bright core.
        core_box = (cx-core, cy-core, cx+core, cy+core)
        if frame == 0:
            self._intro_core_id = canvas.create_oval(*core_box, fill="#fff4ff", outline="")
        else:
            canvas.coords(self._intro_core_id, *core_box)
        center_dot = max(2, scale * .0045)
        dot_box = (cx-center_dot, cy-center_dot, cx+center_dot, cy+center_dot)
        if frame == 0:
            self._intro_dot_id = canvas.create_oval(*dot_box, fill="#ffffff", outline="")
        # The pinpoint stays fixed in the exact center of the galaxy.
        wordmark_y = cy + scale * .30
        if frame == 0:
            self._intro_wordmark_ids = [
                canvas.create_text(cx, wordmark_y, text="A D R O L L A",
                                   fill="#f5f2ff", font=("Segoe UI", 25, "bold"), anchor="center"),
                canvas.create_text(cx, wordmark_y + 36, text=self.tr("DEIN UNIVERSUM STARTET"),
                                   fill=ACCENT2, font=("Segoe UI", 9, "bold"), anchor="center"),
            ]
        # Wordmark and subtitle are static, so only create them on the first frame.
        bar_width = min(250, width * .36)
        bar_y = wordmark_y + 64
        left, right = cx-bar_width/2, cx+bar_width/2
        if frame == 0:
            self._intro_bar_track_id = canvas.create_line(
                left, bar_y, right, bar_y, fill="#302a42", width=4, capstyle="round")
            self._intro_bar_progress_id = canvas.create_line(
                left, bar_y, left, bar_y, fill=ACCENT, width=4, capstyle="round")
        # The track is static; only the illuminated segment moves.
        sweep = (frame % 60) / 60
        segment = bar_width * .38
        start_x = left + (bar_width + segment) * sweep - segment
        canvas.coords(self._intro_bar_progress_id, max(left, start_x), bar_y,
                      min(right, start_x+segment), bar_y)

        self._intro_frame += 1
        if self._intro_frame >= 48:
            self._intro_layer.destroy()
            return
        self.after(16, self._animate_intro)

    def _apply_monitor_size(self):
        # Adapt the launcher window to the current monitor resolution.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1360, max(820, int(screen_w * 0.88)))
        height = min(900, max(600, int(screen_h * 0.86)))
        width = min(width, screen_w)
        height = min(height, screen_h)
        self.geometry(f"{width}x{height}")
        self.minsize(min(760, screen_w), min(520, screen_h))
        self.update_idletasks()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def set_fullscreen(self, enabled):
        self._fullscreen = bool(enabled)
        self.attributes("-fullscreen", self._fullscreen)
        if hasattr(self, "fullscreen_var"):
            self.fullscreen_var.set(self._fullscreen)
        if not self._fullscreen:
            self._apply_monitor_size()

    def _toggle_fullscreen_hotkey(self, event=None):
        self.set_fullscreen(not self._fullscreen)
        return "break"

    def _escape_fullscreen(self, event=None):
        if self._fullscreen:
            self.set_fullscreen(False)
            return "break"

    def _load_selected_game_mode(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("selected_game_mode", "PvP")
        except Exception:
            return "PvP"

    def _load_custom_modes(self):
        saved_modes = read_config().get("custom_modes", [])
        if not isinstance(saved_modes, list):
            return []
        modes = []
        for item in saved_modes[:9]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()[:24]
            description = str(item.get("description", "")).strip()[:80]
            if name:
                created_version = str(item.get("created_version", "")).strip()[:20]
                modes.append({"name": name, "description": description,
                              "created_version": created_version})
        return modes

    def _load_selected_version(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                selected = json.load(f).get("selected_version", MC_VERSIONS[0])
            return selected if selected in MC_VERSIONS else MC_VERSIONS[0]
        except Exception:
            return MC_VERSIONS[0]

    def _load_play_mode(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return "Online" if json.load(f).get("play_mode") == "Online" else "Offline"
        except Exception:
            return "Offline"

    def _save_play_mode(self):
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["play_mode"] = self.play_mode
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_persistent_sessions(self):
        try:
            with open(SESSION_FILE, "rb") as session_file:
                payload = _windows_protect(session_file.read(), decrypt=True)
            saved = json.loads(payload.decode("utf-8"))
            accounts = saved.get("accounts", {})
            active = saved.get("active_account")
            if not isinstance(accounts, dict):
                return {}, None
            return accounts, active if active in accounts else None
        except Exception:
            return {}, None

    def _save_persistent_sessions(self):
        try:
            accounts = {}
            for name, result in self.accounts.items():
                refresh_token = result.get("refresh_token")
                if refresh_token:
                    accounts[name] = {
                        "name": result.get("name", name),
                        "uuid": result.get("uuid", ""),
                        "refresh_token": refresh_token,
                    }
            if not accounts:
                if os.path.isfile(SESSION_FILE):
                    os.remove(SESSION_FILE)
                return
            os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
            data = json.dumps({"accounts": accounts, "active_account": self.account_name},
                              ensure_ascii=False).encode("utf-8")
            encrypted = _windows_protect(data)
            temp_file = SESSION_FILE + ".tmp"
            with open(temp_file, "wb") as session_file:
                session_file.write(encrypted)
            os.replace(temp_file, SESSION_FILE)
        except Exception as exc:
            if hasattr(self, "status_label"):
                self._set_status(f"Sitzung konnte nicht gespeichert werden: {exc}")

    def _restore_saved_sessions(self):
        self.status_label.config(text=self.tr("●  Microsoft-Sitzung wird erneuert …"), fg=ACCENT2)
        self._play_btn("ANMELDUNG …", "play", False)
        self.account_menu_button.configure(state="disabled")
        threading.Thread(target=self._restore_saved_sessions_worker, daemon=True).start()

    def _restore_saved_sessions_worker(self):
        restored, failed = {}, {}
        client_id = load_client_id()
        for name, stored in list(self.accounts.items()):
            refresh_token = stored.get("refresh_token")
            if not refresh_token:
                failed[name] = "Kein Erneuerungstoken vorhanden."
                continue
            try:
                restored[name] = refresh_minecraft_account(client_id, refresh_token)
            except Exception as exc:
                failed[name] = str(exc)
        self.after(0, lambda: self._finish_session_restore(restored, failed))

    def _finish_session_restore(self, restored, failed):
        self._session_refreshing = False
        self._play_btn("SPIELEN", "play")
        self.account_menu_button.configure(state="normal")
        for name, account in restored.items():
            self.accounts[name] = account
        for name in failed:
            self.accounts.pop(name, None)
        if self.account_name in restored:
            self.auth_result = restored[self.account_name]
        elif self.account_name:
            self.account_name = None
            self.auth_result = None
            self.play_mode = "Offline"
        self._save_play_mode()
        self._save_persistent_sessions()
        self._refresh_mode_button()
        if failed and not restored:
            self.status_label.config(text=self.tr("●  Bitte Microsoft-Konto erneut anmelden"), fg=ACCENT2)

    def _switch_account_async(self, name):
        stored = self.accounts.get(name)
        if not stored:
            return
        if stored.get("minecraft_access_token"):
            self.account_name = name
            self.auth_result = stored
            self.play_mode = "Online"
            self._save_play_mode()
            self._save_persistent_sessions()
            self._refresh_mode_button()
            return
        self.account_name = name
        self.auth_result = None
        self._session_refreshing = True
        self.play_mode = "Online"
        self._save_play_mode()
        self._refresh_mode_button()
        threading.Thread(target=self._refresh_switched_account_worker,
                         args=(name, stored.get("refresh_token", "")), daemon=True).start()

    def _refresh_switched_account_worker(self, name, refresh_token):
        try:
            account = refresh_minecraft_account(load_client_id(), refresh_token)
            self.after(0, lambda: self._switch_account_refreshed(name, account, None))
        except Exception as exc:
            error = str(exc)
            self.after(0, lambda: self._switch_account_refreshed(name, None, error))

    def _switch_account_refreshed(self, name, account, error):
        self._session_refreshing = False
        if account:
            self.accounts[name] = account
            self.account_name = name
            self.auth_result = account
            self.play_mode = "Online"
            self._save_persistent_sessions()
            self._refresh_mode_button()
        else:
            self.auth_result = None
            self._refresh_mode_button()
            self._messagebox("showerror", "Anmeldung konnte nicht erneuert werden", error or "Unbekannter Fehler")

    def _store_refreshed_active_account(self, account):
        if self.account_name:
            self.accounts[self.account_name] = account
            self.auth_result = account
            self._save_persistent_sessions()
            self._refresh_mode_button()

    def change_version(self, selected):
        if selected not in MC_VERSIONS:
            return
        self.selected_version = selected
        self.profile_settings.setdefault(self.active_profile, {"loader": "Vanilla"})["version"] = selected
        self._save_profiles()

    def change_loader(self, selected):
        if selected not in loaders.LOADERS:
            return
        self.profile_settings.setdefault(self.active_profile, {"version": self.selected_version})[
            "loader"] = selected
        self._save_profiles()

    def save_client_id(self):
        client_id = self.client_id_var.get().strip()
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["client_id"] = client_id
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._messagebox("showinfo", "Gespeichert", "Die Microsoft-App-Client-ID wurde gespeichert.")
        except Exception as exc:
            self._messagebox("showerror", "Speichern fehlgeschlagen", str(exc))

    def _load_theme(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "Adrolla Red")
        except Exception:
            return "Black & Grey"

    def _load_profiles(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            profiles = data.get("profiles", ["Profil 1"])
            return profiles[:10] if isinstance(profiles, list) and profiles else ["Profil 1"]
        except Exception:
            return ["Profil 1"]

    def _save_profiles(self):
        update_config(profiles=self.profiles[:10], active_profile=self.active_profile,
                      profile_settings=self.profile_settings, profile_dirs=self.profile_dirs,
                      profile_descriptions=self.profile_descriptions,
                      selected_version=self.selected_version)

    def _load_profile_settings(self):
        raw = read_config().get("profile_settings", {})
        fallback = self._load_selected_version()
        result = {}
        for name in self.profiles:
            item = raw.get(name, {}) if isinstance(raw, dict) else {}
            version, loader = item.get("version"), item.get("loader")
            result[name] = {"version": version if version in MC_VERSIONS else fallback,
                            "loader": loader if loader in loaders.LOADERS else "Vanilla"}
        return result

    @property
    def active_loader(self):
        return self.profile_settings.get(self.active_profile, {}).get("loader", "Vanilla")

    def _profile_dir(self, name=None):
        name = name or self.active_profile
        safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in name).strip(" .") or "Profil"
        root = os.path.abspath(PROFILES_DIR)
        mapped = self.profile_dirs.get(name) if hasattr(self, "profile_dirs") else None
        path = os.path.join(root, safe)
        if isinstance(mapped, str) and mapped and not os.path.isabs(mapped):
            candidate = os.path.abspath(os.path.join(root, mapped))
            try:
                if os.path.commonpath((root, candidate)) == root:
                    path = candidate
            except ValueError:
                pass
        os.makedirs(path, exist_ok=True)
        return path

    def _copy_legacy_mode_mods(self, source_dir, target_dir, manifest_extra=None,
                               only_files=None):
        if not os.path.isdir(source_dir):
            return
        os.makedirs(target_dir, exist_ok=True)
        source_manifest = modrinth.Manifest(os.path.join(source_dir, ".adrolla-installed.json"))
        target_manifest = modrinth.Manifest(os.path.join(target_dir, ".adrolla-installed.json"))
        source_names = [name for name in os.listdir(source_dir)
                        if name.lower().endswith(".jar")
                        and (only_files is None or name in only_files)]
        renamed = {}
        for filename in source_names:
            source = os.path.join(source_dir, filename)
            destination_name = filename
            destination = os.path.join(target_dir, destination_name)
            if os.path.exists(destination):
                try:
                    same_file = os.path.getsize(source) == os.path.getsize(destination)
                    if same_file:
                        with open(source, "rb") as left, open(destination, "rb") as right:
                            same_file = hashlib.sha256(left.read()).digest() == hashlib.sha256(right.read()).digest()
                except OSError:
                    same_file = False
                if not same_file:
                    stem, extension = os.path.splitext(filename)
                    number = 2
                    while os.path.exists(os.path.join(target_dir, f"{stem} (import {number}){extension}")):
                        number += 1
                    destination_name = f"{stem} (import {number}){extension}"
                    destination = os.path.join(target_dir, destination_name)
                else:
                    renamed[filename] = destination_name
                    continue
            shutil.copy2(source, destination)
            renamed[filename] = destination_name

        for project_id, item in source_manifest.data.items():
            if only_files is None or item.get("file") in only_files:
                updated = dict(item)
                updated["file"] = renamed.get(item.get("file"), item.get("file"))
                target_manifest.data[project_id] = updated
        if manifest_extra:
            target_manifest.data.update(manifest_extra)
        if source_manifest.data or manifest_extra:
            target_manifest.save()

    def _migrate_legacy_modes_to_profiles(self, selected_mode, custom_modes):
        config = read_config()
        if config.get("modes_migrated_to_profiles"):
            return

        builtin_modes = [
            ("PvP", "Duelle und schnelle Kämpfe"),
            ("SMP", "Gemeinsames Survival"),
            ("BedWars", "Schnelle Runden und Teamplay"),
            ("Survival", "Erkundung und entspanntes Bauen"),
            ("SkyWars", "Kämpfe auf schwebenden Inseln"),
        ]
        mode_descriptions = {name: description for name, description in builtin_modes}
        mode_names = [name for name, _ in builtin_modes]
        for item in custom_modes:
            name = str(item.get("name", "")).strip()
            if name and name.casefold() not in {entry.casefold() for entry in mode_names}:
                mode_names.append(name)
                mode_descriptions[name] = str(item.get("description", "")).strip()
        selected_mode = selected_mode if selected_mode in mode_names else mode_names[0]

        source_profile = self.active_profile
        source_root = self._profile_dir(source_profile)
        source_mods = os.path.join(source_root, "mods")
        core_data = self._adrolla_core_mod_data()
        core_files = set(core_data.get("files", []))
        try:
            core_files.update(name for name in os.listdir(source_mods)
                              if name.lower().startswith(("fancymenu", "konkrete", "melody"))
                              and name.lower().endswith(".jar"))
        except OSError:
            pass
        source_settings = dict(self.profile_settings.get(
            source_profile, {"version": self._load_selected_version(), "loader": "Vanilla"}))
        profiles = list(self.profiles)
        settings = dict(self.profile_settings)
        directories = dict(self.profile_dirs)
        descriptions = dict(self.profile_descriptions)
        def unique_profile_name(base):
            candidate = base
            suffix = " Profil"
            number = 2
            while any(name.casefold() == candidate.casefold() for name in profiles):
                candidate = f"{base}{suffix if number == 2 else f' {number}'}"
                number += 1
            return candidate

        if source_profile.casefold() == selected_mode.casefold():
            active_target = source_profile
        elif not any(name.casefold() == selected_mode.casefold() for name in profiles):
            active_target = selected_mode
            try:
                source_index = profiles.index(source_profile)
            except ValueError:
                source_index = 0
            profiles[source_index] = active_target
            settings.pop(source_profile, None)
            settings[active_target] = source_settings
            old_relative = os.path.relpath(source_root, os.path.abspath(PROFILES_DIR))
            directories.pop(source_profile, None)
            directories[active_target] = old_relative
            descriptions[active_target] = mode_descriptions.get(active_target, "")
        else:
            active_target = unique_profile_name(selected_mode)
            profiles.append(active_target)
            settings[active_target] = dict(source_settings)
            profile_key = hashlib.sha1(selected_mode.casefold().encode("utf-8")).hexdigest()[:10]
            safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in active_target).strip(" .") or "Profil"
            directories[active_target] = os.path.join("mode-profiles", f"{safe[:32]}-{profile_key}")
            descriptions[active_target] = mode_descriptions.get(selected_mode, "")

        if active_target == source_profile:
            descriptions.setdefault(active_target, mode_descriptions.get(selected_mode, ""))

        targets = {selected_mode: active_target}
        for mode_name in mode_names:
            if mode_name == selected_mode:
                continue
            target_name = unique_profile_name(mode_name)
            profiles.append(target_name)
            settings[target_name] = dict(source_settings)
            profile_key = hashlib.sha1(mode_name.casefold().encode("utf-8")).hexdigest()[:10]
            safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in target_name).strip(" .") or "Profil"
            directories[target_name] = os.path.join("mode-profiles", f"{safe[:32]}-{profile_key}")
            descriptions[target_name] = mode_descriptions.get(mode_name, "")
            targets[mode_name] = target_name

        legacy_mode_root = os.path.join(source_root, "mode-mods")
        for mode_name, target_name in targets.items():
            target_dir = os.path.abspath(self._profile_dir(target_name))
            target_mods = os.path.join(target_dir, "mods")
            if os.path.abspath(target_dir) != os.path.abspath(source_root):
                if mode_name == selected_mode:
                    self._copy_legacy_mode_mods(source_mods, target_mods)
                else:
                    self._copy_legacy_mode_mods(source_mods, target_mods,
                                                manifest_extra=core_data.get("manifest", {}),
                                                only_files=core_files)
                safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in mode_name).strip(" .") or "Modus"
                key = hashlib.sha1(mode_name.casefold().encode("utf-8")).hexdigest()[:10]
                mode_store = os.path.join(legacy_mode_root, f"{safe[:32]}-{key}")
                self._copy_legacy_mode_mods(mode_store, target_mods)
                core_file = os.path.join(source_root, "adrolla_core_mods.json")
                if os.path.isfile(core_file):
                    shutil.copy2(core_file, os.path.join(target_dir, "adrolla_core_mods.json"))
            settings.setdefault(target_name, dict(source_settings))

        ordered_profiles = list(dict.fromkeys(profiles))
        self.profiles = [active_target] + [name for name in ordered_profiles
                                         if name != active_target][:9]
        self.profile_settings = settings
        self.profile_dirs = directories
        self.profile_descriptions = descriptions
        self.active_profile = active_target
        config.pop("selected_game_mode", None)
        config.pop("custom_modes", None)
        config.update({
            "profiles": self.profiles,
            "profile_settings": self.profile_settings,
            "profile_dirs": self.profile_dirs,
            "profile_descriptions": self.profile_descriptions,
            "active_profile": self.active_profile,
            "selected_version": source_settings.get("version", self._load_selected_version()),
            "modes_migrated_to_profiles": True,
        })
        tmp_path = CONFIG_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, ensure_ascii=False)
        os.replace(tmp_path, CONFIG_FILE)
        if os.path.isdir(legacy_mode_root):
            shutil.rmtree(legacy_mode_root)

    def _sync_profile_to(self, version, loader):
        cfg = self.profile_settings.setdefault(
            self.active_profile, {"version": self.selected_version, "loader": "Vanilla"})
        notes = []
        if loader and cfg.get("loader") != loader:
            cfg["loader"] = loader
            notes.append(loader)
        if version and cfg.get("version") != version:
            cfg["version"] = version
            self.selected_version = version
            notes.append(f"Minecraft {version}")
        if notes:
            self._save_profiles()
            return "Profil umgestellt auf " + " + ".join(notes)
        return ""

    def _option_menu(self, parent, var, values, command=None):
        original_values = list(values)
        display_values = [self.tr(str(value)) for value in original_values]
        display_var = tk.StringVar(value=self.tr(str(var.get())))

        def select(display_value):
            try:
                original_value = original_values[display_values.index(display_value)]
            except ValueError:
                original_value = display_value
            var.set(original_value)
            if command:
                command(original_value)

        menu = tk.OptionMenu(parent, display_var, *display_values, command=select)
        menu.config(bg=CARD_HOVER, fg=WHITE, activebackground=ACCENT, activeforeground=BG,
                    relief="flat", bd=0, highlightthickness=0, font=("Segoe UI", 9, "bold"),
                    padx=12, pady=7, cursor="hand2")
        menu["menu"].config(bg=CARD, fg=WHITE, activebackground=ACCENT, activeforeground=BG,
                            bd=0, font=("Segoe UI", 9))
        return menu

    def _edit_profile(self, name):
        cfg = self.profile_settings.setdefault(
            name, {"version": self.selected_version, "loader": "Vanilla"})
        win = tk.Toplevel(self)
        win.title(f"{self.tr('Profil')} “{name}”")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        body = tk.Frame(win, bg=BG, padx=26, pady=22)
        body.pack()
        self.txt(body, name, 16, WHITE, "bold", bg=BG).pack(anchor="w")
        self.txt(body, "Version und Mod-Loader dieses Profils. Jedes Profil hat eigene Mods.",
                 9, MUTED, bg=BG).pack(anchor="w", pady=(4, 16))
        version_var = tk.StringVar(value=cfg.get("version", self.selected_version))
        loader_var = tk.StringVar(value=cfg.get("loader", "Vanilla"))
        for label, var, values in (("Minecraft-Version", version_var, MC_VERSIONS),
                                   ("Mod-Loader", loader_var, loaders.LOADERS)):
            row = tk.Frame(body, bg=BG)
            row.pack(fill="x", pady=5)
            self.txt(row, label, 10, WHITE, "bold", bg=BG).pack(side="left", padx=(0, 30))
            self._option_menu(row, var, values).pack(side="right")

        def save():
            cfg["version"], cfg["loader"] = version_var.get(), loader_var.get()
            if name == self.active_profile:
                self.selected_version = cfg["version"]
            self._save_profiles()
            win.destroy()
            self.show_page(self.active_page)

        self.btn(body, "Speichern", save, primary=True, icon="check").pack(anchor="e", pady=(16, 0))
        win.grab_set()

    def _save_theme(self):
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["theme"] = self.theme
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def change_theme(self, selected):
        self.theme = selected if selected in THEMES else "Adrolla Red"
        set_palette(self.theme)
        self._save_theme()
        # Rebuild the interface using the new palette, without opening a new window.
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=BG)
        self._make_shell()
        self.show_page("Einstellungen")

    def _set_saturn_window_icon(self):
        icon_path = resource_path("saturn.ico")
        try:
            if os.path.isfile(icon_path):
                self.iconbitmap(default=icon_path)
        except tk.TclError:
            pass
        try:
            icon = tk.PhotoImage(file=resource_path("saturn.png"))
        except tk.TclError:
            # Keep a vector-like Tk fallback if the packaged image is missing.
            icon = tk.PhotoImage(width=32, height=32)
            icon.put("#0d0c0e", to=(0, 0, 32, 32))
            for y in range(9, 23):
                for x in range(9, 23):
                    if (x - 16) ** 2 + (y - 16) ** 2 <= 43:
                        icon.put("#d95e68", (x, y))
            for x in range(2, 30):
                for y in range(11, 22):
                    ellipse = ((x - 16) / 14) ** 2 + ((y - 16) / 4.5) ** 2
                    if 0.78 <= ellipse <= 1.22:
                        icon.put("#e6808a", (x, y))
            for y in range(10, 23):
                for x in range(10, 23):
                    if (x - 16) ** 2 + (y - 16) ** 2 <= 36:
                        icon.put("#d95e68", (x, y))
        self._window_icon = icon
        self.iconphoto(True, icon)
        if sys.platform == "win32":
            try:
                user32 = ctypes.WinDLL("user32", use_last_error=True)
                user32.LoadImageW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR,
                                              wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                              wintypes.UINT]
                user32.LoadImageW.restype = wintypes.HANDLE
                user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                                ctypes.c_size_t, ctypes.c_ssize_t]
                user32.SendMessageW.restype = ctypes.c_ssize_t
                set_class_icon = getattr(user32, "SetClassLongPtrW", user32.SetClassLongW)
                set_class_icon.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
                set_class_icon.restype = ctypes.c_void_p
                native_icon = user32.LoadImageW(None, icon_path, 1, 0, 0, 0x10 | 0x40)
                if native_icon:
                    handles = {self.winfo_id()}
                    try:
                        handles.add(int(self.tk.call("wm", "frame", self._w), 0))
                    except Exception:
                        pass
                    for handle in handles:
                        hwnd = wintypes.HWND(handle)
                        user32.SendMessageW(hwnd, 0x80, 1, native_icon)
                        user32.SendMessageW(hwnd, 0x80, 0, native_icon)
                        set_class_icon(hwnd, -14, native_icon)  # GCLP_HICON
                        set_class_icon(hwnd, -34, native_icon)  # GCLP_HICONSM
                    self._native_taskbar_icon = native_icon
            except Exception:
                pass

    def tr(self, text):
        if self.language != "English":
            return text
        memo = self.__dict__.setdefault("_tr_memo", {})
        result = memo.get(text)
        if result is None:
            result = memo[text] = self._tr_uncached(text)
        return result

    def _tr_uncached(self, text):
        if self.language != "English":
            return text
        translations = {
            "Startseite":"Home", "Mod Manager":"Mod Manager", "Profile":"Profiles",
            "DEIN UNIVERSUM STARTET":"YOUR UNIVERSE STARTS",
            "Einstellungen":"Settings", "NAVIGATION":"NAVIGATION",
            "MIDNIGHT EDITION":"BLACK & GREY EDITION", "Anmelden":"Sign in",
            "Nicht angemeldet":"Not signed in", "MINECRAFT JAVA EDITION  •  CLIENT LAUNCHER":"MINECRAFT JAVA EDITION  •  CLIENT LAUNCHER",
            "Deine Welt.\\nDein Setup.":"Your world.\\nYour setup.",
            "Willkommen bei Adrolla Client.":"Welcome to Adrolla Client.",
            "SPIELEN":"PLAY", "STOPPEN":"STOP", "WIRD GESTARTET …":"STARTING …",
            "ANMELDUNG …":"SIGNING IN …", "SCHNELLZUGRIFF":"QUICK ACCESS",
            "MOD MANAGER":"MOD MANAGER", "Module und HUD verwalten":"Manage modules and HUD",
            "PROFILE":"PROFILES", "Deine Client-Profile":"Your client profiles",
            "EINSTELLUNGEN":"SETTINGS", "Launcher anpassen":"Customize launcher",
            "Öffnen":"Open", "✦   Ein ruhiger Platz für dein nächstes Abenteuer.":"✦   A calm place for your next adventure.",
            "Verwalte die geplanten Client-Module an einem Ort.":"Manage planned client modules in one place.",
            "INFO  •  Diese Module sind aktuell Vorschau-Einträge und noch nicht im Spiel aktiv.":"INFO  •  These modules are previews and are not active in-game yet.",
            "GEPLANT":"PLANNED", "Dein Setup":"Your setup",
            "Unterschiedliche Konfigurationen für verschiedene Spielstile.":"Different configurations for different play styles.",
            "STANDARDPROFIL":"DEFAULT PROFILE",
            "Dein Ausgangsprofil für Minecraft Java Edition.":"Your starting profile for Minecraft Java Edition.",
            "STATUS: VORSCHAU":"STATUS: PREVIEW",
            "Die lokale Speicherung und das Wechseln von Profilen kommen in einem späteren Update.":"Local saving and profile switching will arrive in a future update.",
            "Die Oberfläche im Adrolla-Nachtmodus.":"The Adrolla dark theme interface.",
            "Design":"Theme", "Sprache":"Language", "Deutsch":"German",
            "Minecraft-Version":"Minecraft version",
            "Fenstermodus":"Window mode",
            "Ein Fenster – Navigation bleibt im Client":"One window – navigation stays inside the client",
            "Midnight Sky  •  Dunkelblau":"Black & Grey",
            "Einstellungen":"Settings", "Launcher anpassen":"Customize launcher",
            "Nicht angemeldet":"Not signed in",
            "Wechsle zwischen Mods und Texture Packs.":"Switch between mods and texture packs.",
            "Texture Packs":"Texture Packs", "Mods":"Mods",
            "Hier erscheinen deine installierten Client-Mods.":"Your installed client mods appear here.",
            "VORSCHAU":"PREVIEW", "Verwalte hier deine Minecraft-Texture-Packs.":"Manage your Minecraft texture packs here.",
            "Hinweis: Die Einträge sind Platzhalter. Import und Aktivierung von Packs kommen später.":"Note: These entries are placeholders. Importing and activating packs will come later.",
            "Jeder Spielstil ist jetzt ein eigenes Minecraft-Profil.":"Each play style is now its own Minecraft profile.",
            "Erstelle und verwalte bis zu 10 Profile.":"Create and manage up to 10 profiles.",
            "Profile erstellt":"profiles created",
            "Vorlagen":"Templates", "Vorlagen ansehen":"Browse templates",
            "Vorlage hinzufügen":"Add template", "PROFIL-VORLAGEN":"PROFILE TEMPLATES",
            "Füge ein vorbereitetes Spielprofil hinzu und passe es anschließend an.":"Add a ready-made game profile, then customize it.",
            "Vorlage verwendet die aktuell ausgewählte Minecraft-Version.":"Template uses the currently selected Minecraft version.",
            "Vorlage nutzt Fabric und die aktuell ausgewählte Minecraft-Version.":"Template uses Fabric and the currently selected Minecraft version.",
            "Vorlagenprofile verwenden deine aktuelle Minecraft-Version und können einzeln angepasst werden.":"Template profiles use your current Minecraft version and can be customized individually.",
            "Wähle eine Vorlage wie SMP oder PvP und erstelle daraus ein eigenes Profil.":"Choose a template such as SMP or PvP to create your own profile.",
            "Duelle und schnelle Kämpfe":"Duels and fast fights",
            "Gemeinsames Survival mit Freunden":"Survival with friends",
            "Schnelle Runden und Teamplay":"Quick rounds and team play",
            "Erkundung und entspanntes Bauen":"Exploration and relaxed building",
            "Kämpfe auf schwebenden Inseln":"Fights on floating islands",
            "Leeres Profil":"Empty profile",
            "Ein neutrales Profil ohne Spielstil-Vorlage":"A blank profile without a play style template",
            "Neues Profil":"New profile", "Erstellen":"Create", "Auswählen":"Select",
            "Löschen":"Delete", "AKTIV":"ACTIVE",
            "Vollbild":"Fullscreen", "Aktivieren":"Enable",
            "Tipp: F11 schaltet Vollbild um, Esc beendet den Vollbildmodus.":"Tip: F11 toggles fullscreen; Esc exits fullscreen.",
            "Spielmodi":"Game Modes",
            "Wähle ein Setup passend zu deinem Minecraft-Spielstil.":"Choose a setup for your Minecraft play style.",
            "DEIN SPIELSTIL":"YOUR PLAY STYLE", "5 PRESETS":"5 PRESETS",
            "Schnell wechseln. Direkt loslegen.":"Switch quickly. Jump right in.",
            "Die Auswahl speichert deinen bevorzugten Spielmodus im Adrolla Client.":"Your profile selection is saved in Adrolla Client.",
            "VORGESTELLTE MODI":"FEATURED MODES",
            "Für Duelle und schnelle Kämpfe":"For duels and fast fights",
            "Für gemeinsames Survival":"For playing survival together",
            "Für schnelle Runden und Teamplay":"For quick rounds and team play",
            "Für Erkundung und entspanntes Bauen":"For exploring and relaxed building",
            "Für Kämpfe auf schwebenden Inseln":"For fights on floating islands",
            "Keystrokes • CPS • FPS":"Keystrokes • CPS • FPS",
            "Coordinates • Armor Status":"Coordinates • Armor Status",
            "FPS • Keystrokes • CPS":"FPS • Keystrokes • CPS",
            "Coordinates • Fullbright":"Coordinates • Fullbright",
            "Keystrokes • FPS • Zoom":"Keystrokes • FPS • Zoom",
            "Auswählen":"Select", "AUSGEWÄHLT":"SELECTED",
            "AKTUELLE AUSWAHL":"CURRENT SELECTION",
            "Hinweis: Die Presets speichern aktuell nur deine Auswahl. Die genannten Mods werden noch nicht automatisch installiert oder im Spiel aktiviert.":"Note: Presets currently only save your selection. The listed mods are not automatically installed or activated in-game."
        }
        translations.update({
            "Start":"Home", "Setup":"Settings",
            "DEIN MINECRAFT WORKSPACE":"YOUR MINECRAFT WORKSPACE",
            "Alles bereit für\ndein nächstes Setup.":"Everything is ready for\nyour next setup.",
            "Verwalte Mods, Texture Packs und deine Profile an einem Ort.":"Manage mods, resource packs, and profiles in one place.",
            "AKTIVES PROFIL":"ACTIVE PROFILE", "SPIELMODUS":"ACTIVE PROFILE",
            "MINECRAFT-VERSION":"MINECRAFT VERSION", "MOD-LOADER":"MOD LOADER",
            "Mods verwalten":"Manage mods", "SCHNELLZUGRIFF":"QUICK ACCESS",
            "Mods über Modrinth installieren":"Install mods from Modrinth",
            "Version, Loader und Mods pro Profil":"Version, loader, and mods per profile",
            "Design, Sprache, Konto":"Theme, language, account",
            "Deine Einstellungen und dein aktives Profil bleiben lokal gespeichert.":"Your settings and active profile are saved locally.",
            "Mods entdecken":"Discover mods", "Texture Packs entdecken":"Discover resource packs",
            "INSTALLIERTE MODS":"INSTALLED MODS", "INSTALLIERTE TEXTURE PACKS":"INSTALLED RESOURCE PACKS",
            "Unterstützt werden .jar-Dateien.":"Supported files: .jar",
            "Unterstützt werden .zip-Texture-Packs.":"Supported files: .zip resource packs",
            "PROFIL-ORDNER":"PROFILE FOLDER", "Dateien hinzufügen":"Add files",
            "Ordner öffnen":"Open folder", "Noch keine Dateien gefunden":"No files found yet",
            "Lade Inhalte aus dem Katalog oder füge Dateien von deinem PC hinzu.":"Browse the catalog or add files from your PC.",
            "MEINE MOD-BIBLIOTHEK":"MY MOD LIBRARY", "MEINE TEXTURE-PACK-BIBLIOTHEK":"MY RESOURCE PACK LIBRARY",
            "Noch nichts gespeichert. Suche im Modrinth-Katalog und lade es direkt hierher.":"Nothing saved yet. Browse Modrinth and download items here.",
            "Installieren":"Install", "Löschen":"Delete", "Entfernen":"Remove",
            "Dateien":"files", "Im Profil":"In profile",
            "Keine Dateien passen zu deiner Suche.":"No files match your search.",
            "Version & Loader":"Version & loader", "Modrinth durchsuchen":"Browse Modrinth",
            "CurseForge öffnen":"Open CurseForge", "ADROLLA PRESETS":"ADROLLA PRESETS",
            "Wähle ein Setup passend zu deinem Minecraft-Spielstil.":"Choose a setup for your Minecraft play style.",
            "DEIN SPIELSTIL":"YOUR PLAY STYLE", "Welcher Spielstil passt heute?":"What play style fits today?",
            "Wähle ein Preset. Deine Auswahl wird im Client gespeichert.":"Choose a preset. Your selection is saved in the client.",
            "VORGESTELLTE MODI":"FEATURED MODES", "Für Duelle und schnelle Kämpfe":"For duels and fast fights",
            "Für gemeinsames Survival":"For playing survival together", "Für schnelle Runden und Teamplay":"For quick rounds and team play",
            "Für Erkundung und entspanntes Bauen":"For exploring and relaxed building",
            "Für Kämpfe auf schwebenden Inseln":"For fights on floating islands", "●  AKTIV":"●  ACTIVE",
            "✓  Ausgewählt":"✓  Selected", "Modus auswählen":"Select mode", "Aktiver Modus: ":"Active mode: ",
            "Dein Setup":"Your setup", "Erstelle und verwalte bis zu 10 Profile.":"Create and manage up to 10 profiles.",
            "Neues Profil":"New profile", "Erstellen":"Create", "Auswählen":"Select", "Bearbeiten":"Edit",
            "Einstellungen":"Settings", "Passe deinen Adrolla Client an.":"Customize your Adrolla client.",
            "Desktop-Symbol":"Desktop shortcut", "Adrolla-Verknüpfung mit Galaxie-Symbol erstellen.":"Create an Adrolla shortcut with the galaxy icon.",
            "Zum Desktop hinzufügen":"Add to desktop", "MICROSOFT-ANMELDUNG":"MICROSOFT SIGN-IN",
            "App-Client-ID":"App client ID", "Speichern":"Save",
            "Standardmäßig Microsofts Minecraft-Anmeldung. Firefox-Login, danach die Rücksprung-URL einmal in Adrolla einfügen. Eigene App-ID optional.":"Uses Microsoft's Minecraft sign-in by default. Sign in through Firefox, then paste the return URL into Adrolla once. A custom app ID is optional.",
            "Microsoft-Anleitung zur App-Registrierung öffnen":"Open Microsoft's app registration guide",
            "Dein Look":"Your theme", "Design wählen  ▾":"Choose theme  ▾",
            "Mod-Loader (aktives Profil)":"Mod loader (active profile)",
            "Version wird verwendet für":"Version used for", "Spielstart und Modrinth-Suche":"Game launch and Modrinth search",
            "Ein Fenster – Navigation bleibt im Client":"Single window — navigation stays in the client",
            "Tipp: F11 schaltet Vollbild um, Esc beendet den Vollbildmodus.":"Tip: Press F11 to toggle fullscreen; Esc exits fullscreen.",
            "Beliebteste":"Most popular", "Relevanz":"Relevance", "Neueste":"Newest", "Zuletzt aktualisiert":"Recently updated",
            "Suchen":"Search", "Lädt …":"Loading…", "Suche auf Modrinth …":"Searching Modrinth…",
            "Mehr laden":"Load more", "von ":"by ", "AKTIV":"ACTIVE", "Nicht verfügbar":"Unavailable",
            "Datei fehlt":"File missing", "Ordner konnte nicht geöffnet werden":"Could not open folder",
            "Minecraft-Konto erforderlich":"Minecraft account required", "Startkomponente fehlt":"Missing launch component",
            "Minecraft-Start fehlgeschlagen":"Minecraft launch failed", "Minecraft konnte nicht gestartet werden.":"Minecraft could not be started.",
            "Lokaler Modus":"Local mode", "SCHLIESSE …":"CLOSING…", "Minecraft wird geschlossen …":"Closing Minecraft…",
            "Minecraft wurde geschlossen.":"Minecraft has closed.", "Minecraft läuft weiter.":"Minecraft is still running.",
            "Minecraft schließen":"Close Minecraft", "Profil":"Profile", "Offline spielen":"Play offline",
            "Online spielen":"Play online", "German":"German", "Deutsch":"German",
            "wechseln":"switch", "Account wechseln":"Switch account", "Mod-Manager":"Mod manager",
            "Installierte Mods":"Installed mods", "Installierte Texture Packs":"Installed resource packs",
            "Profil-Ordner":"Profile folder", "Meine Mod-Bibliothek":"My mod library",
            "Suche fehlgeschlagen: ":"Search failed: ", "Installation fehlgeschlagen: ":"Installation failed: ",
            "Bereits installiert.":"Already installed.", "Installiert: ":"Installed: ",
            " Downloads   ·   ":" downloads   ·   ", " Follower":" followers",
            "App-Client-ID":"App client ID", "Anmeldung …":"Signing in…",
            "Anmeldung …":"Signing in…", "Microsoft-Account anmelden":"Sign in with Microsoft",
            "Abmelden":"Sign out", "Weiteren Account hinzufügen":"Add another account",
            "Angemeldet: ":"Signed in: ", "Zu ":"Switch to ",
            "●  Lokaler Modus":"●  Local mode", "Microsoft-Sitzung wird erneuert …":"Refreshing Microsoft session…",
            "Finde Mods und Resource Packs direkt im Adrolla Client.":"Find mods and resource packs directly in the Adrolla client.",
            "Ohne Mod-Loader laden Mods nicht – wähle Fabric, Forge …":"Mods need a mod loader. Choose Fabric, Forge, or another loader.",
            "Installiert ins Profil":"Installed into profile",
            "Mods, die über Modrinth installiert wurden, passen automatisch zur Spielversion und zum Loader des Profils. Pflicht-Abhängigkeiten werden mitinstalliert und Downloads auf Prüfsummen geprüft.":"Mods installed from Modrinth match the profile's game version and loader. Required dependencies are installed, and downloads are checksum-verified.",
            "Über Modrinth installierte Mods passen automatisch zu Version und Loader des Profils, inklusive Pflicht-Abhängigkeiten und Prüfsummen-Kontrolle. Der Loader wird beim Spielstart installiert. Selbst importierte Mods prüft Adrolla nicht.":"Mods installed from Modrinth match the profile's game version and loader, including required dependencies and checksum verification. The loader is installed when you launch the game. Adrolla does not verify imported mods.",
            "Texture Packs werden in den resourcepacks-Ordner kopiert. Aktiviere sie anschließend in Minecraft unter Optionen → Ressourcenpakete.":"Resource packs are copied to the resourcepacks folder. Enable them in Minecraft under Options → Resource Packs.",
            "Pflicht-Abhängigkeiten":"required dependencies", "Prüfsummen-Kontrolle":"checksum verification",
            "FileNotFoundError":"File not found", "Desktop-Verknüpfungen werden hier nur unter Windows erstellt.":"Desktop shortcuts are only available on Windows.",
            "Die Datei ist nicht mehr in der Bibliothek.":"This file is no longer in the library.",
            "Minecraft Java":"Minecraft Java", "Profil wurde umgestellt auf ":"Profile changed to ",
            "●  Microsoft-Sitzung wird erneuert …":"●  Refreshing Microsoft session…",
            "Microsoft-Sitzung wird für den Spielstart erneuert …":"Refreshing Microsoft session for launch…",
            "Java-Runtime für diese ältere Minecraft-Version wird geprüft …":"Checking the Java runtime for this older Minecraft version…",
            "●  Microsoft-Anmeldung wird gestartet …":"●  Starting Microsoft sign-in…",
            "PROFIL FÜR DIE MODI":"PROFILE",
            "Profilübersicht öffnen":"View profile overview",
            "Sitzung konnte nicht gespeichert werden: ":"Could not save session: ",
            "Kein Erneuerungstoken vorhanden.":"No refresh token is available.",
            "Profil-Ordner":"Profile folder", "MEINE MOD-BIBLIOTHEK":"MY MOD LIBRARY",
            "MEINE TEXTURE-PACK-BIBLIOTHEK":"MY RESOURCE PACK LIBRARY",
            "●  Bitte Microsoft-Konto erneut anmelden":"●  Please sign in to your Microsoft account again",
            "Datei entfernen":"Remove file", "Aus Bibliothek löschen":"Delete from library",
            "Die Datei wirklich entfernen?":"Are you sure you want to remove this file?",
            "Minecraft-Mods auswählen":"Select Minecraft mods", "Minecraft-Texture-Packs auswählen":"Select Minecraft resource packs",
            "Alle Dateien":"All files", "Mod-Dateien":"Mod files", "Texture Packs":"Resource packs",
            "Minecraft-Version":"Minecraft version",
            "Bitte wähle einen anderen Profilnamen.":"Please choose a different profile name.",
            "Du kannst höchstens 10 Profile erstellen.":"You can create up to 10 profiles.",
            "Mindestens ein Profil muss vorhanden sein.":"At least one profile must remain.",
            "Die Datei ist nicht mehr in der Bibliothek.":"This file is no longer in the library.",
            "FileNotFoundError":"File not found",
            "Gespeichert":"Saved", "Die Microsoft-App-Client-ID wurde gespeichert.":"The Microsoft app client ID was saved.",
            "Speichern fehlgeschlagen":"Could not save", "Unbekannter Fehler":"Unknown error",
            "Import abgeschlossen":"Import complete", "Datei(en) hinzugefügt nach:":" file(s) added to:",
            "Datei entfernen":"Remove file", "aus Minecraft entfernen?":" from Minecraft?",
            "Datei fehlt":"File missing", "Diese Datei ist nicht mehr in der Bibliothek.":"This file is no longer in the library.",
            "Installiert":"Installed", "wurde installiert.":" was installed.",
            "Installation fehlgeschlagen":"Installation failed", "Löschen fehlgeschlagen":"Could not delete",
            "Aus Bibliothek löschen":"Delete from library", "Maximale Anzahl":"Maximum reached",
            "Name bereits vorhanden":"Name already exists", "Profil behalten":"Keep profile",
            "Online-Anmeldung nicht eingerichtet":"Online sign-in not configured",
            "Für die Microsoft-Anmeldung fehlt die App-Client-ID.":"The app client ID is missing for Microsoft sign-in.",
            "Trage die Client-ID unter Einstellungen → Microsoft-Anmeldung ein und versuche es erneut.":"Enter the client ID under Settings → Microsoft sign-in, then try again.",
            "Falsche App-Client-ID":"Incorrect app client ID",
            "Desktop-Symbol erstellt":"Desktop shortcut created",
            "Anmeldung konnte nicht erneuert werden":"Could not refresh sign-in",
            "Anmeldung fehlgeschlagen":"Sign-in failed", "Angemeldet":"Signed in",
            "Account hinzugefügt":"Account added", "Nicht importiert":"Not imported",
            "Verknüpfung konnte nicht erstellt werden":"Could not create shortcut",
            "Datei entfernen":"Remove file", "Löschen":"Delete", "Abbrechen":"Cancel",
            "Weitere Version oder Loader wählen.":"Choose another version or loader.",
            "EIGENE MODI":"CUSTOM MODES", "FREIER PLATZ":"EMPTY SLOT",
            "Eigenen Modus erstellen":"Create custom mode", "Alle 9 Plätze belegt":"All 9 slots are used",
            "Du kannst höchstens neun eigene Modi erstellen.":"You can create up to nine custom modes.",
            "Eigenen Modus bearbeiten":"Edit custom mode", "Modusname":"Mode name",
            "Beschreibung":"Description", "Du kannst bis zu neun eigene Modi speichern.":"You can save up to nine custom modes.",
            "Ältere Version":"Older version",
            "Name fehlt":"Name is missing", "Gib deinem Modus einen Namen.":"Enter a name for your mode.",
            "Name bereits vergeben":"Name is already in use",
            "Wähle einen anderen Namen für diesen Modus.":"Choose a different name for this mode.",
            "Eigenen Modus löschen":"Delete custom mode",
            "Möchtest du diesen eigenen Modus wirklich löschen?":"Are you sure you want to delete this custom mode?",
            "Name und Beschreibung selbst festlegen.":"Choose a name and description.",
            "Eigener Spielmodus":"Custom game mode", "Eigener Modus":"Custom mode",
            "Logs öffnen":"Open logs",
            "Noch nicht erstellt":"Not created yet", "Mods hinzufügen":"Add mods",
            "Modus auswählen":"Select mode",
            "Füge über „Mods hinzufügen“ echte Mods für diesen Modus hinzu. Sie werden passend zu Minecraft-Version und Loader installiert.":"Use ‘Add mods’ to add real mods for this mode. They are installed for the selected Minecraft version and loader.",
            "Mods benötigen einen Loader":"Mods need a loader",
            "Für diesen Modus sind Mods installiert, aber das Profil verwendet Vanilla. Wähle Fabric, Quilt, Forge oder NeoForge, damit Minecraft die Mods lädt.":"This mode has mods installed, but the profile uses Vanilla. Choose Fabric, Quilt, Forge, or NeoForge so Minecraft can load them.",
            "Minecraft läuft noch":"Minecraft is still running",
            "Schließe Minecraft, bevor du das Menüdesign einrichtest.":"Close Minecraft before setting up the menu theme.",
            "Mod-Loader erforderlich":"Mod loader required",
            "Das Adrolla-Menü benötigt einen Mod-Loader. Wähle Fabric, Quilt, Forge oder NeoForge.":"The Adrolla menu needs a mod loader. Choose Fabric, Quilt, Forge, or NeoForge.",
            "Adrolla-Menü wird eingerichtet":"Setting up the Adrolla menu",
            "Minecraft-Menü im Adrolla-Stil":"Minecraft menu in Adrolla style",
            "Dunkler Saturn-Hintergrund und runde Akzentflächen für Minecraft.":"Dark Saturn background and rounded accents for Minecraft.",
            "Menü einrichten":"Set up menu",
            "FancyMenu wird vorbereitet …":"Preparing FancyMenu…",
            "FancyMenu wird passend zu Version und Loader installiert …":"Installing FancyMenu for the selected version and loader…",
            "Adrolla-Hintergrund und Menülayout werden kopiert …":"Copying the Adrolla background and menu layout…",
            "Adrolla-Menü konnte nicht eingerichtet werden":"Could not set up the Adrolla menu",
            "Adrolla-Menü eingerichtet":"Adrolla menu is ready",
            "FancyMenu und das Adrolla-Design sind installiert. Starte Minecraft neu, damit das neue Hauptmenü erscheint.":"FancyMenu and the Adrolla theme are installed. Restart Minecraft to see the new main menu.",
            "FancyMenu wurde nicht im Profil-Mods-Ordner gefunden.":"FancyMenu was not found in the profile's mods folder.",
            "Beende Minecraft, bevor du den Spielmodus wechselst.":"Close Minecraft before switching game modes.",
            "Moduswechsel fehlgeschlagen":"Could not switch game mode"
        })
        translated = translations.get(text)
        if translated is not None:
            return translated
        if text.isupper():
            title_case = text.title()
            if title_case in translations:
                return translations[title_case].upper()
        if text:
            for source, target in (
                ("Für die Microsoft-Anmeldung fehlt die App-Client-ID.", "The Microsoft app client ID is missing."),
                ("Trage die Client-ID unter Einstellungen → Microsoft-Anmeldung ein und versuche es erneut.", "Enter the client ID under Settings → Microsoft sign-in, then try again."),
                ("Diese ID gehört zur Microsoft-Entra-Verwaltungsoberfläche (ADIbizaUX), nicht zu Adrolla.", "This ID belongs to Microsoft's Entra admin center (ADIbizaUX), not Adrolla."),
                ("Registriere eine eigene App, die persönliche Microsoft-Konten unterstützt, ", "Register an app that supports personal Microsoft accounts, "),
                ("aktiviere den Public Client Flow und trage deren Application (client) ID hier ein.", "enable the public client flow, and enter its application (client) ID here."),
                (" wurde hinzugefügt.", " was added."),
                ("Zum Wechseln unten links auf das Profil-Symbol klicken.", "Click the profile button in the lower left to switch accounts."),
                ("Dein Konto ist angemeldet. Online-Multiplayer ist jetzt verfügbar. Den Spielmodus kannst du oben rechts umschalten.", "Your account is signed in. Online multiplayer is available now. You can switch between online and offline play in the top right."),
                ("Adrolla startet Minecraft Java ", "Adrolla launches Minecraft Java "),
                ("direkt. Dafür braucht Minecraft ein gültiges Microsoft-Konto mit Java-Lizenz. Melde dich unten links über das Profil-Symbol an.", "directly. Online play requires a valid Microsoft account with a Java license. Sign in using the profile button in the lower left."),
                ("Für Online-Multiplayer ist eine erfolgreiche Microsoft-Anmeldung erforderlich.", "Online multiplayer requires a successful Microsoft sign-in."),
                ("Die Minecraft-Startkomponente ist nicht installiert. Starte START_ADROLLA.bat erneut oder installiere minecraft-launcher-lib mit pip.", "The Minecraft launch component is missing. Run START_ADROLLA.bat again or install minecraft-launcher-lib with pip."),
                ("Adrolla konnte Minecraft nicht starten. Prüfe die ausgewählte Version, deine Internetverbindung und ob dein angemeldetes Konto Minecraft Java besitzt.", "Adrolla could not launch Minecraft. Check the selected version, your internet connection, and whether your signed-in account owns Minecraft Java."),
                ("Adrolla mit Galaxie-Symbol liegt jetzt auf dem Desktop:", "The Adrolla galaxy shortcut is now on your desktop:"),
                ("Profil umgestellt auf ", "Profile changed to "),
                ("Minecraft reagiert nicht auf das normale Schließen.", "Minecraft did not close normally."),
                ("Soll der Prozess jetzt erzwungen beendet werden? Ungespeicherter Fortschritt kann verloren gehen.", "Force quit the process now? Unsaved progress may be lost."),
                ("wird installiert/geprüft", "is being installed/checked"),
                ("wird vorbereitet", "is being prepared"),
                ("wird installiert", "is being installed"), ("wird geladen", "is loading"),
                (" wird laut Modrinth nicht auf dem Minecraft-Client unterstützt.",
                 " is not supported on the Minecraft client according to Modrinth."),
                ("wurde im ", "started in "), (" wurde geschlossen", " has closed"),
                ("-Modus", " mode"), ("Modus.", "mode."),
                ("Profil ", "Profile "), ("Ergebnisse für", "results for"),
                (" von ", " of "), ("Keine Treffer für", "No results for"),
                (". Andere Version oder anderen Loader wählen.", ". Try another version or loader."),
                ("wurde installiert.", "was installed."), ("Minecraft wird geschlossen", "Closing Minecraft"),
                ("Minecraft wurde geschlossen.", "Minecraft has closed."),
                ("Aktiver Modus: ", "Active mode: "),
                ("Installiert ins Profil ", "Installed into profile "),
                (" Profile erstellt", " profiles created"),
                (" aus Minecraft entfernen?", " from Minecraft?"),
                (" wurde installiert.", " was installed."),
                (" – mit Pflicht-Abhängigkeiten ", " — with "),
                (" und Prüfsummen-Kontrolle.", " and checksum verification."),
                ("Profil ", "Profile "),
                ("Minecraft-Profil: ", "Minecraft profile: "),
                ("Profil umgestellt auf ", "Profile changed to "),
                (" Profile erstellt", " profiles created"),
                (" Dateien hinzugefügt nach:", " files added to:"),
            ):
                text = text.replace(source, target)
        return text

    def _messagebox(self, method, title, message="", **kwargs):
        return getattr(messagebox, method)(self.tr(title), self.tr(message), **kwargs)

    def txt(self, parent, text, size=10, color=WHITE, weight="normal", bg=None):
        return tk.Label(parent, text=self.tr(text), bg=bg or parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, weight))

    def btn(self, parent, text, command, primary=False, width=None, icon=None, big=False):
        normal = ACCENT if primary else CARD_HOVER
        hover = ACCENT2 if primary else BORDER
        return RoundedButton(parent, self.tr(text), command, bg=normal, fg=BG if primary else WHITE,
                             activebackground=hover, font=("Segoe UI", 11 if big else 10, "bold"),
                             padx=22 if big else 18, pady=13 if big else 9, width=width, radius=18,
                             icon_name=icon, icon_size=19 if big else 17)

    def _play_btn(self, label, icon="play", enabled=True):
        self._play_label, self._play_icon, self._play_enabled = label, icon, enabled
        button = getattr(self, "play_button", None)
        if button is None:
            return
        try:
            button.configure(text=self.tr(label), icon_name=icon,
                             state="normal" if enabled else "disabled")
        except tk.TclError:
            pass  # Startseite ist gerade nicht sichtbar

    def _make_shell(self):
        # Compact Minecraft-client layout inspired by the supplied reference:
        # dark translucent-looking workspace, narrow icon rail and red accents.
        header = tk.Frame(self, bg=SIDEBAR, height=54, highlightthickness=0)
        header.pack(fill="x")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        header.pack_propagate(False)
        brand = tk.Frame(header, bg=SIDEBAR)
        brand.pack(side="left", fill="y", padx=18)
        self._logo_img = icons.logo_photo(36, ACCENT, ACCENT2, None)
        if self._logo_img:
            tk.Label(brand, image=self._logo_img, bg=SIDEBAR, bd=0).pack(side="left", pady=8)
        self.txt(brand, "ADROLLA", 13, WHITE, "bold", bg=SIDEBAR).pack(side="left", padx=(8, 3))
        self.txt(brand, "CLIENT", 8, ACCENT2, "bold", bg=SIDEBAR).pack(side="left", pady=(5, 0))
        self.status_label = self.txt(header, "●  Lokaler Modus", 9, ACCENT2, "bold", bg=SIDEBAR)
        self.status_label.pack(side="right", padx=(12, 18))
        self.mode_button = tk.Menubutton(header, text="Offline  ▾", bg=CARD_HOVER,
                                         fg=WHITE, activebackground=ACCENT,
                                         activeforeground=BG, relief="flat", bd=0,
                                         highlightthickness=0, cursor="hand2",
                                         font=("Segoe UI", 9, "bold"), padx=14, pady=8)
        self.mode_menu = tk.Menu(self.mode_button, tearoff=0, bg=CARD, fg=WHITE,
                                 activebackground=ACCENT, activeforeground=BG,
                                 font=("Segoe UI", 9), bd=0)
        self.mode_menu.add_command(label=self.tr("Offline spielen"), command=lambda: self.set_play_mode("Offline"))
        self.mode_menu.add_command(label=self.tr("Online spielen"), command=lambda: self.set_play_mode("Online"))
        self.mode_button.configure(menu=self.mode_menu)
        self.mode_button.pack(side="right", pady=8, padx=(0, 8))
        self._refresh_mode_button()

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        self.sidebar = tk.Frame(body, bg=SIDEBAR, width=84, highlightthickness=0)
        self.sidebar.pack(side="left", fill="y", padx=(0, 12))
        self.sidebar.pack_propagate(False)
        self.nav_buttons = {}
        self.nav_labels = {}
        self.nav_indicators = {}
        self.nav_icons = {"Startseite": "home", "Mod Manager": "mods",
                          "Profile": "profile", "Vorlagen": "modes",
                          "Einstellungen": "settings"}
        self.nav_glyphs = {"Startseite": "⌂", "Mod Manager": "▤",
                           "Profile": "◉", "Vorlagen": "▦", "Einstellungen": "⚙"}
        nav_names = {"Startseite": "Start", "Mod Manager": "Mods",
                     "Profile": "Profile", "Vorlagen": "Vorlagen",
                     "Einstellungen": "Setup"}
        nav_items = list(self.nav_icons.items())
        for label, icon in nav_items:
            item = tk.Frame(self.sidebar, bg=SIDEBAR, cursor="hand2")
            item.pack(fill="x", padx=5, pady=(7, 2))
            use_icon = icons.available()
            b = RoundedButton(item, "" if use_icon else self.nav_glyphs[label],
                command=lambda page=label: self._nav(page),
                bg=CARD_HOVER if label == self.active_page else SIDEBAR,
                fg=ACCENT if label == self.active_page else MUTED, activebackground=CARD_HOVER,
                font=("Segoe UI Symbol", 17, "bold"), padx=0, pady=10,
                width=6, radius=14, icon_name=icon if use_icon else None, icon_size=24)
            b.pack(anchor="center")
            caption = self.txt(item, nav_names[label], 8,
                               ACCENT2 if label == self.active_page else MUTED,
                               "bold", bg=SIDEBAR)
            caption.pack(fill="x", anchor="center", pady=(4, 0))
            caption.configure(anchor="center", justify="center")
            caption.bind("<Button-1>", lambda _event, page=label: self._nav(page))
            item.bind("<Button-1>", lambda _event, page=label: self._nav(page))
            indicator = tk.Frame(item, bg=ACCENT if label == self.active_page else SIDEBAR, width=3)
            indicator.place(x=0, y=8, width=3, height=38)
            self.nav_indicators[label] = indicator
            self.nav_buttons[label] = b
            self.nav_labels[label] = caption
        self.account_menu_button = RoundedButton(
            self.sidebar, "" if icons.available() else "AD", command=self._show_account_menu,
            bg=CARD_HOVER, fg=ACCENT2, activebackground=ACCENT,
            font=("Segoe UI", 9, "bold"), padx=0, pady=10, width=6, radius=16,
            icon_name="user" if icons.available() else None, icon_size=22)
        self.account_menu_button.pack(side="bottom", anchor="center", pady=12)

        workspace = tk.Frame(body, bg=PANEL, highlightthickness=0)
        workspace.pack(side="left", fill="both", expand=True)
        titlebar = tk.Frame(workspace, bg=SIDEBAR, height=40)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)
        self.page_title = self.txt(titlebar, "  Startseite", 10, WHITE, "bold", bg=SIDEBAR)
        self.page_title.pack(side="left", padx=8, pady=8)

        # Scrollable workspace; the compact navigation rail remains fixed.
        self.content_canvas = tk.Canvas(workspace, bg=BG, highlightthickness=0, bd=0)
        self.content_canvas.pack(side="left", fill="both", expand=True, padx=14, pady=12)
        self.content_scroll_frame = tk.Frame(self.content_canvas, bg=BG)
        self.content_window = self.content_canvas.create_window(
            (0, 0), window=self.content_scroll_frame, anchor="nw"
        )
        self.content_scroll_frame.bind("<Configure>", self._update_scroll_region)
        self.content_canvas.bind("<Configure>", self._resize_scroll_frame)
        self.content = self.content_scroll_frame
        self._scroller = SmoothScroller(self.content_canvas)
        self._scroll_job = None
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _update_scroll_region(self, event=None):
        if self._scroll_job is None:  # viele Änderungen pro Seitenaufbau -> nur einmal
            self._scroll_job = self.after_idle(self._apply_scroll_region)

    def _apply_scroll_region(self):
        self._scroll_job = None
        try:
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        except tk.TclError:
            pass

    def _resize_scroll_frame(self, event):
        self.content_canvas.itemconfigure(self.content_window, width=event.width)

    def _on_mousewheel(self, event):
        # Only scroll when the pointer is over the main page area.
        try:
            if event.widget.winfo_toplevel() is not self:
                return
        except Exception:
            pass
        x = self.winfo_pointerx()
        canvas_left = self.content_canvas.winfo_rootx()
        canvas_right = canvas_left + self.content_canvas.winfo_width()
        if canvas_left <= x <= canvas_right:
            self._scroller.scroll(-event.delta / 120)

    def _on_mousewheel_linux(self, event):
        try:
            if event.widget.winfo_toplevel() is not self:
                return
        except Exception:
            pass
        x = self.winfo_pointerx()
        canvas_left = self.content_canvas.winfo_rootx()
        canvas_right = canvas_left + self.content_canvas.winfo_width()
        if canvas_left <= x <= canvas_right:
            self._scroller.scroll(-1 if event.num == 4 else 1)

    def _clear_content(self):
        self._cancel_chunks()
        for child in self.content.winfo_children():
            child.destroy()
        self.profile_list = None

    def _cancel_chunks(self):
        jobs = self.__dict__.setdefault("_chunk_jobs", {})
        for job in list(jobs.values()):
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
        jobs.clear()

    def _paged(self, items, build, parent, key, page=40, done=None):
        """Zeigt lange Listen in Seiten à `page` Zeilen; „Mehr anzeigen“ lädt die nächsten."""
        items = list(items)

        def render(start):
            chunk = items[start:start + page]
            more_left = len(items) - (start + len(chunk))

            def finished():
                if more_left > 0:
                    holder = {}

                    def show_more():
                        holder["btn"].destroy()
                        render(start + page)

                    holder["btn"] = self.btn(parent, f"Mehr anzeigen ({more_left})", show_more,
                                             icon="plus")
                    holder["btn"].pack(pady=10)
                if done:
                    done()

            self._chunked(chunk, build, key=key + str(start), done=finished)

        render(0)

    def _chunked(self, items, build, size=6, done=None, key="default"):
        """Baut Zeilen in kleinen Portionen auf, damit die Oberfläche nie hängt."""
        jobs = self.__dict__.setdefault("_chunk_jobs", {})
        previous = jobs.pop(key, None)
        if previous is not None:
            try:
                self.after_cancel(previous)
            except tk.TclError:
                pass
        queue, position = list(items), [0]

        def step():
            jobs.pop(key, None)
            end = min(position[0] + size, len(queue))
            try:
                for item in queue[position[0]:end]:
                    build(item)
            except tk.TclError:
                return  # Seite wurde inzwischen gewechselt
            position[0] = end
            if end < len(queue):
                jobs[key] = self.after(8, step)
            elif done:
                try:
                    done()
                except tk.TclError:
                    pass

        step()

    def _star_canvas(self, parent, height=150):
        canvas = tk.Canvas(parent, height=height, bg=PANEL, highlightthickness=0)
        canvas.pack(fill="x")
        rng = random.Random(21)
        width = 900
        for _ in range(95):
            x = rng.randint(8, width)
            y = rng.randint(5, height-5)
            r = rng.choice([1, 1, 1, 2])
            color = rng.choice([ACCENT, ACCENT2, BORDER, MUTED])
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")
        canvas.create_oval(width-190, -65, width-55, 70, outline=BORDER, width=2)
        canvas.create_oval(width-165, -42, width-75, 48, outline=CARD_HOVER, width=2)
        return canvas

    def _page_heading(self, eyebrow, title, subtitle):
        self.txt(self.content, eyebrow.upper(), 9, ACCENT2, "bold").pack(anchor="w", pady=(10, 9))
        self.txt(self.content, title, 25, WHITE, "bold").pack(anchor="w")
        self.txt(self.content, subtitle, 10, MUTED).pack(anchor="w", pady=(8, 25))

    def _rounded_panel(self, parent, color=None, outline=None, radius=20):
        """Flache Karte mit feinem Rand. Bewusst ohne Canvas-Hintergrund: ein einzelnes Widget
        lässt sich beim Scrollen sauber verschieben, übereinandergelegte Zeichenflächen nicht."""
        color = color or CARD
        edge = blend(color, outline, .55) if outline == BORDER else (outline or color)
        outer = tk.Frame(parent, bg=color, bd=0, highlightthickness=1,
                         highlightbackground=edge, highlightcolor=edge)
        inner = tk.Frame(outer, bg=color, bd=0, highlightthickness=0)
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        return outer, inner

    def _card(self, parent, title, desc, action_text=None, command=None, icon=None, active=False):
        outer, card = self._rounded_panel(parent, CARD_HOVER if active else CARD,
                                          ACCENT if active else BORDER)
        card.configure(padx=8, pady=7)
        head = tk.Frame(card, bg=card.cget("bg"))
        head.pack(fill="x")
        chip = icons.get(icon, ACCENT if active else ACCENT2, 20) if icon else None
        if chip:
            tk.Label(head, image=chip, bg=head.cget("bg"), bd=0).pack(side="left", padx=(0, 8))
        self.txt(head, title, 11, WHITE, "bold", bg=head.cget("bg")).pack(side="left")
        self.txt(card, desc, 9, MUTED, bg=card.cget("bg")).pack(anchor="w", pady=(8, 14))
        if action_text and command:
            self.btn(card, action_text, command).pack(anchor="w")
        return outer

    def _nav(self, page):
        if page != self.active_page:
            self.show_page(page)

    def show_page(self, page):
        self.active_page = page
        # Unsichtbar aufbauen und erst am Ende einblenden: kein Flackern, weniger Neuzeichnen.
        self.content_canvas.itemconfigure(self.content_window, state="hidden")
        self._clear_content()
        self._scroller.reset()
        self.content_canvas.yview_moveto(0)
        for name, button in self.nav_buttons.items():
            button.configure(bg=CARD_HOVER if name == page else SIDEBAR,
                             fg=ACCENT if name == page else MUTED)
            self.nav_labels[name].configure(fg=ACCENT2 if name == page else MUTED)
            self.nav_indicators[name].configure(bg=ACCENT if name == page else SIDEBAR)
        self.page_title.configure(text="  " + self.tr(page))
        if page == "Startseite":
            self._home_page()
        elif page == "Mod Manager":
            self._mods_page()
        elif page == "Profile":
            self._profiles_page()
        elif page == "Vorlagen":
            self._templates_page()
        elif page == "Einstellungen":
            self._settings_page()
        self.content_canvas.itemconfigure(self.content_window, state="normal")
        self._apply_scroll_region()

    def _home_page(self):
        hero_outer, hero = self._rounded_panel(self.content, PANEL, BORDER, radius=24)
        hero.configure(padx=16, pady=15)
        hero_outer.pack(fill="x")
        banner_h = 112
        banner_img = icons.banner_photo(1400, banner_h, ACCENT, ACCENT2, PANEL)
        if banner_img:
            banner = tk.Canvas(hero_outer, height=banner_h, bg=PANEL, highlightthickness=0, bd=0)
            banner_item = banner.create_image(0, 0, image=banner_img, anchor="nw")
            banner.bind("<Configure>", lambda e: banner.coords(banner_item, e.width - 1400, 0))
            banner.pack(fill="x", before=hero, side="top")
        hero_top = tk.Frame(hero, bg=PANEL)
        hero_top.pack(fill="x")
        intro = tk.Frame(hero_top, bg=PANEL)
        intro.pack(side="left", fill="both", expand=True)
        self.txt(intro, "DEIN MINECRAFT WORKSPACE", 9, ACCENT2, "bold", bg=PANEL).pack(anchor="w")
        self.txt(intro, "Alles bereit für\ndein nächstes Setup.", 27, WHITE, "bold", bg=PANEL).pack(anchor="w", pady=(12, 7))
        self.txt(intro, "Verwalte Mods, Texture Packs und deine Profile an einem Ort.",
                 10, MUTED, bg=PANEL).pack(anchor="w")
        status_outer, status = self._rounded_panel(hero_top, CARD, BORDER, radius=20)
        status.configure(padx=5, pady=3)
        status_outer.pack(side="right", padx=(20, 0), anchor="center")
        self.txt(status, "AKTIVES PROFIL", 8, MUTED, "bold", bg=CARD).pack(anchor="w")
        self.txt(status, self.active_profile, 12, WHITE, "bold", bg=CARD).pack(anchor="w", pady=(5, 0))
        self.txt(status, "MINECRAFT-VERSION", 8, MUTED, "bold", bg=CARD).pack(anchor="w", pady=(10, 0))
        self.txt(status, self.selected_version, 10, ACCENT2, "bold", bg=CARD).pack(anchor="w", pady=(5, 0))
        self.txt(status, "MOD-LOADER", 8, MUTED, "bold", bg=CARD).pack(anchor="w", pady=(10, 0))
        self.txt(status, self.active_loader, 10, ACCENT2, "bold", bg=CARD).pack(anchor="w", pady=(5, 0))
        actions = tk.Frame(hero, bg=PANEL)
        actions.pack(fill="x", pady=(22, 0))
        self.play_button = self.btn(actions, self._play_label, self.play, primary=True,
                                    width=19, icon=self._play_icon, big=True)
        self.play_button.pack(side="left")
        if not self._play_enabled:
            self.play_button.configure(state="disabled")
        self.btn(actions, "Mods verwalten", lambda: self.show_page("Mod Manager"),
                 icon="mods").pack(side="left", padx=(9, 0))
        self.btn(actions, "Logs öffnen", self._open_logs,
                 icon="folder").pack(side="left", padx=(9, 0))
        self.btn(actions, "Profile", lambda: self.show_page("Profile"),
                 icon="profile").pack(side="left", padx=(9, 0))
        self.txt(hero, f"Minecraft Java {self.selected_version} · {self.active_loader} · Profil {self.active_profile}",
                 9, MUTED, bg=PANEL).pack(anchor="w", pady=(17, 0))
        self.txt(self.content, "SCHNELLZUGRIFF · PROFILE", 9, MUTED, "bold").pack(anchor="w", pady=(22, 12))
        profile_row = tk.Frame(self.content, bg=BG)
        profile_row.pack(fill="x")
        for slot, name in enumerate(self.profiles[:10]):
            cfg = self.profile_settings.get(name, {})
            desc = self.profile_descriptions.get(name) or (
                f"Minecraft {cfg.get('version', self.selected_version)} · {cfg.get('loader', 'Vanilla')}")
            active = name == self.active_profile
            card = self._card(profile_row, name, desc,
                              "Aktives Profil" if active else "Profil öffnen",
                              (lambda n=name: self.show_page("Profile")) if active else
                              (lambda n=name: self._quick_select_profile(n)),
                              icon="check" if active else "profile", active=active)
            card.grid(row=slot // 3, column=slot % 3, sticky="nsew",
                      padx=(0, 10), pady=(0, 10))
        for column in range(3):
            profile_row.columnconfigure(column, weight=1, uniform="home_profile")
        self.txt(self.content, "Deine Profile und Einstellungen bleiben lokal gespeichert.", 9, MUTED).pack(
            anchor="w", pady=(16, 0))

    def _quick_select_profile(self, profile_name):
        self.select_profile(profile_name)
        self.show_page("Startseite")

    def _minecraft_dir(self):
        # Standard Minecraft Java directory on Windows.
        if sys.platform == "win32":
            return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), ".minecraft")
        if sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/minecraft")
        return os.path.expanduser("~/.minecraft")

    def _open_logs(self):
        logs_dir = os.path.join(self._profile_dir(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        target = os.path.join(logs_dir, "latest.log")
        if not os.path.isfile(target):
            target = logs_dir
        try:
            if sys.platform == "win32":
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            self._messagebox("showerror", "Ordner konnte nicht geöffnet werden", str(exc))

    def _section_dir(self, section):
        target = os.path.join(self._profile_dir(), section)
        os.makedirs(target, exist_ok=True)
        return target

    def _adrolla_core_mod_data(self):
        path = os.path.join(self._profile_dir(), "adrolla_core_mods.json")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"files": [], "manifest": {}}

    def _adrolla_menu_theme_ready(self):
        profile_dir = self._profile_dir()
        customization = os.path.join(profile_dir, "config", "fancymenu", "customization")
        assets = os.path.join(profile_dir, "config", "fancymenu", "assets")
        fancymenu_config = os.path.join(profile_dir, "config", "fancymenu")
        mods_dir = self._section_dir("mods")
        layout_path = os.path.join(customization, "title_screen_layout.txt")
        try:
            with open(layout_path, "r", encoding="utf-8") as handle:
                layout = handle.read()
            with open(os.path.join(fancymenu_config, "options.txt"), "r", encoding="utf-8") as handle:
                options = handle.read()
            mod_files = os.listdir(mods_dir)
        except OSError:
            return False
        required_buttons = (
            "mc_titlescreen_singleplayer_button",
            "mc_titlescreen_multiplayer_button",
            "mc_titlescreen_realms_button",
            "mc_titlescreen_options_button",
            "mc_titlescreen_quit_button",
            "mc_titlescreen_language_button",
            "mc_titlescreen_accessibility_button",
            "mc_titlescreen_mods_button",
            "title_screen_realms_notification",
            "width = 770",
            "height = 78",
        )
        required_options = (
            "global_button_background_normal = '[source:local]/config/fancymenu/assets/adrolla_button.png'",
            "global_button_background_hover = '[source:local]/config/fancymenu/assets/adrolla_button_hover.png'",
            "global_button_label_base_color = '#F2EAF0'",
        )
        required_assets = (
            "adrolla_background.png",
            "adrolla_button.png",
            "adrolla_button_hover.png",
        )
        return (
            all(button in layout for button in required_buttons)
            and all(option in options for option in required_options)
            and all(os.path.isfile(os.path.join(assets, name)) for name in required_assets)
            and any(name.lower().startswith("fancymenu") and name.lower().endswith(".jar")
                    for name in mod_files)
        )

    def _configure_adrolla_fancymenu_options(self, options_path):
        settings = {
            "global_button_background_normal": "S:'[source:local]/config/fancymenu/assets/adrolla_button.png'",
            "global_button_background_hover": "S:'[source:local]/config/fancymenu/assets/adrolla_button_hover.png'",
            "global_button_background_inactive": "S:'[source:local]/config/fancymenu/assets/adrolla_button.png'",
            "global_button_background_transparent": "B:'false'",
            "global_button_background_nine_slice": "B:'true'",
            "global_button_background_nine_slice_border_left": "I:'18'",
            "global_button_background_nine_slice_border_right": "I:'18'",
            "global_button_background_nine_slice_border_top": "I:'18'",
            "global_button_background_nine_slice_border_bottom": "I:'18'",
            "global_button_label_base_color": "S:'#F2EAF0'",
            "global_button_label_hover_color": "S:'#FFFFFF'",
            "global_button_label_scale": "F:'1.1'",
            "global_button_label_shadow": "B:'true'",
            "global_button_label_underline_on_hover": "B:'false'",
        }
        try:
            with open(options_path, "r", encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except OSError:
            lines = []

        section_start = next((i for i, line in enumerate(lines)
                              if line.strip() == "##[global_customizations]"), None)
        if section_start is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append("##[global_customizations]")
            section_start = len(lines) - 1

        section_end = next((i for i in range(section_start + 1, len(lines))
                            if lines[i].lstrip().startswith("##[")), len(lines))
        for key, typed_value in settings.items():
            prefix, value = typed_value.split(":", 1)
            replacement = f"{prefix}:{key} = {value};"
            match_index = next((i for i, line in enumerate(lines)
                                if re.match(rf"\s*[SBFI]:{re.escape(key)}\s*=", line)), None)
            if match_index is not None:
                lines[match_index] = replacement
            else:
                lines.insert(section_end, replacement)
                section_end += 1

        os.makedirs(os.path.dirname(options_path), exist_ok=True)
        with open(options_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines).rstrip() + "\n")

    def _write_adrolla_core_mod_data(self, data):
        path = os.path.join(self._profile_dir(), "adrolla_core_mods.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)

    def _install_adrolla_minecraft_theme(self, auto_launch=False):
        if self._theme_installing:
            return
        if self.game_process is not None and self.game_process.poll() is None:
            self._messagebox("showinfo", "Minecraft läuft noch",
                             "Schließe Minecraft, bevor du das Menüdesign einrichtest.")
            return
        if self.active_loader == "Vanilla":
            self._messagebox("showinfo", "Mod-Loader erforderlich",
                             "Das Adrolla-Menü benötigt einen Mod-Loader. Wähle Fabric, Quilt, Forge oder NeoForge.")
            self._edit_profile(self.active_profile)
            return

        dialog = tk.Toplevel(self)
        dialog.title(self.tr("Adrolla-Menü wird eingerichtet"))
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self)
        frame = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        frame.pack(fill="both", expand=True)
        self.txt(frame, "Minecraft-Menü im Adrolla-Stil", 12, WHITE, "bold", bg=BG).pack(anchor="w")
        status = tk.StringVar(value=self.tr("FancyMenu wird vorbereitet …"))
        self.txt(frame, status, 9, MUTED, bg=BG).pack(anchor="w", pady=(8, 0))

        def set_status(text):
            try:
                self.after(0, lambda value=text: status.set(self.tr(value)) if dialog.winfo_exists() else None)
            except (tk.TclError, RuntimeError):
                pass

        def finish(error=None):
            self._theme_installing = False
            try:
                if dialog.winfo_exists():
                    dialog.destroy()
            except tk.TclError:
                pass
            if error:
                self._messagebox("showerror", "Adrolla-Menü konnte nicht eingerichtet werden", error)
                if auto_launch:
                    self._skip_adrolla_theme_once = True
                    self.after(250, self.play)
                return
            if auto_launch:
                self.after(150, self.play)
                return
            self._messagebox("showinfo", "Adrolla-Menü eingerichtet",
                             "FancyMenu und das Adrolla-Design sind installiert. Starte Minecraft neu, damit das neue Hauptmenü erscheint.")

        def worker():
            try:
                version, loader = self.selected_version, self.active_loader
                mods_dir = self._section_dir("mods")
                library_dir = self._mod_library_dir(version, "mods")
                set_status("FancyMenu wird passend zu Version und Loader installiert …")
                installed, warnings = modrinth.install_project(
                    "Wq5SjeWM", version, loader, mods_dir, library_dir, "mod",
                    status=set_status)
                core_files = {name for name in installed if name.lower().endswith(".jar")}
                core_files.update(name for name in os.listdir(mods_dir)
                                  if name.lower().startswith(("fancymenu", "konkrete", "melody"))
                                  and name.lower().endswith(".jar"))
                if not any(name.lower().startswith("fancymenu") for name in core_files):
                    raise RuntimeError("FancyMenu wurde nicht im Profil-Mods-Ordner gefunden.")

                game_dir = self._profile_dir()
                assets_dir = os.path.join(game_dir, "config", "fancymenu", "assets")
                layout_dir = os.path.join(game_dir, "config", "fancymenu", "customization")
                os.makedirs(assets_dir, exist_ok=True)
                os.makedirs(layout_dir, exist_ok=True)
                set_status("Adrolla-Hintergrund und Menülayout werden kopiert …")
                for asset in ("adrolla_background.png", "adrolla_button.png", "adrolla_button_hover.png"):
                    shutil.copy2(resource_path(os.path.join("minecraft_theme", "assets", asset)),
                                 os.path.join(assets_dir, asset))
                shutil.copy2(resource_path(os.path.join("minecraft_theme", "title_screen_layout.txt")),
                             os.path.join(layout_dir, "title_screen_layout.txt"))
                self._configure_adrolla_fancymenu_options(
                    os.path.join(game_dir, "config", "fancymenu", "options.txt"))
                menus_file = os.path.join(game_dir, "config", "fancymenu", "customizablemenus.txt")
                try:
                    with open(menus_file, "r", encoding="utf-8") as handle:
                        menu_config = handle.read()
                except OSError:
                    menu_config = "type = customizablemenus\n\n"
                screen_class = "net.minecraft.client.gui.screens.TitleScreen"
                if screen_class not in menu_config:
                    with open(menus_file, "w", encoding="utf-8") as handle:
                        handle.write(menu_config.rstrip() + f"\n\n{screen_class} {{\n}}\n")

                manifest_path = os.path.join(mods_dir, ".adrolla-installed.json")
                manifest = modrinth.Manifest(manifest_path)
                core_manifest = {pid: item for pid, item in manifest.data.items()
                                 if item.get("file") in core_files}
                core_data = self._adrolla_core_mod_data()
                saved_files = set(core_data.get("files", []))
                saved_files.update(core_files)
                core_data["files"] = sorted(saved_files)
                core_data.setdefault("manifest", {}).update(core_manifest)
                core_data["version"] = version
                core_data["loader"] = loader
                self._write_adrolla_core_mod_data(core_data)
                self.after(0, finish)
            except Exception as exc:
                message = str(exc)
                self.after(0, lambda error=message: finish(error))

        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        dialog.grab_set()
        self._theme_installing = True
        threading.Thread(target=worker, daemon=True).start()

    def _target_dir(self):
        return self._section_dir("mods" if self.mod_section == "Mods" else "resourcepacks")

    def _mod_library_dir(self, version=None, section=None):
        version = version or self.selected_version
        section = section or ("mods" if self.mod_section == "Mods" else "resourcepacks")
        root = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                            "Adrolla Client", "Mod Library", version, section)
        os.makedirs(root, exist_ok=True)
        return root

    def _queue_mod_icons(self, jobs):
        if not jobs:
            return
        if not hasattr(self, "_mod_icon_url_cache"):
            self._mod_icon_url_cache = {}

        def show_icon(label, data):
            try:
                if not label.winfo_exists():
                    return
                image = icons.fit_image(data, 30)
                if image:
                    label.configure(image=image)
                    label.image = image
            except (tk.TclError, OSError, ValueError):
                pass

        def load_icons():
            try:
                os.makedirs(ICON_CACHE_DIR, exist_ok=True)
            except OSError:
                return
            for icon_url, project_id, label in jobs:
                try:
                    if project_id and icon_url:
                        self._mod_icon_url_cache[project_id] = icon_url
                    elif project_id:
                        icon_url = self._mod_icon_url_cache.get(project_id, "")
                    if not icon_url and project_id:
                        icon_url = modrinth.get_project(project_id).get("icon_url", "")
                        if icon_url:
                            self._mod_icon_url_cache[project_id] = icon_url
                    if not icon_url:
                        continue
                    cache = os.path.join(ICON_CACHE_DIR,
                                         hashlib.sha1(icon_url.encode("utf-8")).hexdigest())
                    if os.path.isfile(cache):
                        with open(cache, "rb") as handle:
                            data = handle.read()
                    else:
                        with urllib.request.urlopen(modrinth._request(icon_url), timeout=10) as response:
                            data = response.read(2_000_000)
                        with open(cache, "wb") as handle:
                            handle.write(data)
                    self.after(0, lambda target=label, image_data=data:
                               show_icon(target, image_data))
                except Exception:
                    continue

        threading.Thread(target=load_icons, daemon=True).start()

    def _open_target_folder(self):
        target = self._target_dir()
        try:
            if sys.platform == "win32":
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            self._messagebox("showerror", "Ordner konnte nicht geöffnet werden", str(exc))

    def _add_minecraft_files(self):
        if self.mod_section == "Mods":
            files = filedialog.askopenfilenames(
                title=self.tr("Minecraft-Mods auswählen"),
                filetypes=[(self.tr("Mod-Dateien"), "*.jar"), (self.tr("Alle Dateien"), "*.*")]
            )
            allowed = (".jar",)
        else:
            files = filedialog.askopenfilenames(
                title=self.tr("Minecraft-Texture-Packs auswählen"),
                filetypes=[(self.tr("Texture Packs"), "*.zip"), (self.tr("Alle Dateien"), "*.*")]
            )
            allowed = (".zip",)
        if not files:
            return
        target = self._target_dir()
        added, skipped = [], []
        for source in files:
            name = os.path.basename(source)
            if not name.lower().endswith(allowed):
                skipped.append(name)
                continue
            destination = os.path.join(target, name)
            if os.path.exists(destination):
                base, ext = os.path.splitext(name)
                number = 2
                while os.path.exists(os.path.join(target, f"{base} ({number}){ext}")):
                    number += 1
                destination = os.path.join(target, f"{base} ({number}){ext}")
            try:
                shutil.copy2(source, destination)
                added.append(os.path.basename(destination))
            except Exception as exc:
                skipped.append(f"{name}: {exc}")
        self._render_mod_section()
        if added:
            self._messagebox("showinfo", "Import abgeschlossen",
                                f"{len(added)} Datei(en) hinzugefügt nach:\n{target}")
        if skipped:
            self._messagebox("showwarning", "Nicht importiert", "\n".join(skipped[:8]))

    def _remove_minecraft_file(self, filename):
        target = os.path.join(self._target_dir(), filename)
        if not self._messagebox("askyesno", "Datei entfernen",
                                   f"{filename} aus Minecraft entfernen?"):
            return
        try:
            if os.path.isfile(target):
                os.remove(target)
            elif os.path.isdir(target):
                shutil.rmtree(target)
            try:
                manifest = modrinth.Manifest(os.path.join(self._target_dir(), ".adrolla-installed.json"))
                manifest.forget_file(filename)
                manifest.save()
            except Exception:
                pass
            self._render_mod_section()
        except Exception as exc:
            self._messagebox("showerror", "Fehler", str(exc))

    def _install_library_file(self, library_dir, filename):
        source = os.path.join(library_dir, os.path.basename(filename))
        if not os.path.isfile(source):
            self._messagebox("showerror", "Datei fehlt", "Diese Datei ist nicht mehr in der Bibliothek.")
            self._render_mod_section()
            return
        target = self._target_dir()
        destination = os.path.join(target, os.path.basename(filename))
        if os.path.exists(destination):
            stem, ext = os.path.splitext(os.path.basename(filename))
            index = 2
            while os.path.exists(os.path.join(target, f"{stem} ({index}){ext}")):
                index += 1
            destination = os.path.join(target, f"{stem} ({index}){ext}")
        try:
            shutil.copy2(source, destination)
            self._render_mod_section()
            self._messagebox("showinfo", "Installiert", f"{os.path.basename(destination)} wurde installiert.")
        except Exception as exc:
            self._messagebox("showerror", "Installation fehlgeschlagen", str(exc))

    def _remove_library_file(self, library_dir, filename):
        path = os.path.join(library_dir, os.path.basename(filename))
        if not os.path.isfile(path):
            self._render_mod_section()
            return
        if not self._messagebox("askyesno", "Aus Bibliothek löschen",
                                   f"{os.path.basename(filename)} dauerhaft aus der Adrolla-Bibliothek löschen?"):
            return
        try:
            os.remove(path)
            self._render_mod_section()
        except Exception as exc:
            self._messagebox("showerror", "Löschen fehlgeschlagen", str(exc))

    def _mods_page(self):
        self._page_heading("Adrolla Client", "Mod Manager",
                           "Finde Mods und Resource Packs direkt im Adrolla Client.")
        info = tk.Frame(self.content, bg=BG)
        info.pack(fill="x", pady=(0, 12))
        no_loader = self.mod_section == "Mods" and self.active_loader == "Vanilla"
        self.txt(info, f"Profil {self.active_profile}  ·  Minecraft {self.selected_version}  ·  "
                 f"{self.active_loader}",
                 9, ACCENT2, "bold").pack(side="left")
        if no_loader:
            self.txt(info, "   Ohne Mod-Loader laden Mods nicht – wähle Fabric, Forge …",
                     9, MUTED).pack(side="left")
        self.btn(info, "Version & Loader", lambda: self._edit_profile(self.active_profile),
                 icon="settings").pack(side="right")
        tabs = tk.Frame(self.content, bg=BG)
        tabs.pack(fill="x", pady=(0, 12))
        self.btn(tabs, "Mods", lambda: self.show_mod_section("Mods"),
                 primary=self.mod_section == "Mods").pack(side="left", padx=(0, 8))
        self.btn(tabs, "Texture Packs", lambda: self.show_mod_section("Texture Packs"),
                 primary=self.mod_section == "Texture Packs").pack(side="left", padx=(0, 8))
        self.btn(tabs, "Modrinth durchsuchen", self.open_modrinth_browser,
                 primary=True, icon="search").pack(side="left", padx=(0, 8))
        self.btn(tabs, "CurseForge öffnen", self.open_curseforge).pack(side="left")
        self.mod_list_area = tk.Frame(self.content, bg=BG)
        self.mod_list_area.pack(fill="both", expand=True)
        self._render_mod_section()

    def open_curseforge(self):
        # CurseForge's official API requires a developer key; open its official catalogue.
        kind = "mc-mods" if self.mod_section == "Mods" else "texture-packs"
        webbrowser.open("https://www.curseforge.com/minecraft/" + kind)
        self._messagebox("showinfo", 
            "CurseForge",
            "CurseForge ist geöffnet. Die direkte Suche und Installation in Adrolla "
            "benötigt einen genehmigten CurseForge-API-Schlüssel. Du kannst Dateien "
            "dort herunterladen und anschließend über „Dateien hinzufügen“ importieren."
        )

    def open_modrinth_browser(self):
        is_mod = self.mod_section == "Mods"
        ptype = "mod" if is_mod else "resourcepack"
        section = "mods" if is_mod else "resourcepacks"
        win = tk.Toplevel(self)
        win.title("Adrolla • Modrinth")
        win.geometry("980x740")
        win.minsize(780, 560)
        win.configure(bg=BG)
        try:
            win.iconphoto(False, self._window_icon)
        except Exception:
            pass

        sorts = {"Beliebteste": "downloads", "Relevanz": "relevance",
                 "Neueste": "newest", "Zuletzt aktualisiert": "updated"}
        state = {"offset": 0, "token": 0, "loading": False}
        query_var = tk.StringVar()
        version_var = tk.StringVar(value=self.selected_version)
        loader_var = tk.StringVar(value=self.active_loader if self.active_loader != "Vanilla" else "Fabric")
        sort_var = tk.StringVar(value="Beliebteste")
        status = tk.StringVar(value="")
        desc_labels = []
        more = {"widget": None}

        def ui(fn):
            try:
                win.after(0, lambda: fn() if win.winfo_exists() else None)
            except (tk.TclError, RuntimeError):
                pass

        head = tk.Frame(win, bg=BG)
        head.pack(fill="x", padx=22, pady=(20, 4))
        self.txt(head, "Mods entdecken" if is_mod else "Texture Packs entdecken",
                 20, WHITE, "bold", bg=BG).pack(anchor="w")
        self.txt(head, f"Installiert ins Profil „{self.active_profile}“ – mit Pflicht-Abhängigkeiten "
                 "und Prüfsummen-Kontrolle.", 9, MUTED, bg=BG).pack(anchor="w", pady=(4, 0))

        bar = tk.Frame(win, bg=BG)
        bar.pack(fill="x", padx=22, pady=(14, 8))
        box = tk.Frame(bar, bg=CARD, highlightthickness=1, highlightbackground=BORDER,
                       highlightcolor=ACCENT)
        box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_icon = icons.get("search", MUTED, 18)
        if search_icon:
            tk.Label(box, image=search_icon, bg=CARD, bd=0).pack(side="left", padx=(12, 2))
        entry = tk.Entry(box, textvariable=query_var, font=("Segoe UI", 11), bg=CARD, fg=WHITE,
                         insertbackground=WHITE, relief="flat", bd=0)
        entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(6, 10))
        again = lambda _value=None: run_search(True)
        self._option_menu(bar, version_var, MC_VERSIONS, again).pack(side="left", padx=(0, 8))
        if is_mod:
            self._option_menu(bar, loader_var, [n for n in loaders.LOADERS if n != "Vanilla"],
                              again).pack(side="left", padx=(0, 8))
        self._option_menu(bar, sort_var, list(sorts), again).pack(side="left", padx=(0, 8))
        self.btn(bar, "Suchen", lambda: run_search(True), primary=True).pack(side="left")

        tk.Label(win, textvariable=status, bg=BG, fg=MUTED, font=("Segoe UI", 9),
                 anchor="w").pack(fill="x", padx=24, pady=(0, 6))
        holder = tk.Frame(win, bg=BG)
        holder.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        rows = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window((0, 0), window=rows, anchor="nw")

        wrap_job = {"id": None}

        def apply_wrap(width):
            wrap_job["id"] = None
            for label in desc_labels:
                try:
                    label.configure(wraplength=max(240, width - 260))
                except tk.TclError:
                    pass

        def on_canvas(event):
            canvas.itemconfigure(window_id, width=event.width)
            if wrap_job["id"] is not None:
                win.after_cancel(wrap_job["id"])
            wrap_job["id"] = win.after(70, lambda: apply_wrap(event.width))

        canvas.bind("<Configure>", on_canvas)
        rows.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        scroller = SmoothScroller(canvas, step=120)

        def wheel(event):
            try:
                top = event.widget.winfo_toplevel()
            except Exception:
                top = None
            if top is not win:  # Mausrad im Hauptfenster weiterreichen
                return (self._on_mousewheel_linux(event) if event.num in (4, 5)
                        else self._on_mousewheel(event))
            up = event.num == 4 or (event.num != 5 and event.delta > 0)
            scroller.scroll(-1 if up else 1)

        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            win.bind_all(sequence, wheel)

        def restore_wheel(event):
            if event.widget is win:
                self.bind_all("<MouseWheel>", self._on_mousewheel)
                self.bind_all("<Button-4>", self._on_mousewheel_linux)
                self.bind_all("<Button-5>", self._on_mousewheel_linux)

        win.bind("<Destroy>", restore_wheel)

        def installed_ids():
            folder = self._section_dir(section)
            return modrinth.Manifest(
                os.path.join(folder, ".adrolla-installed.json")).installed_ids(folder)

        def add_row(item, done_ids):
            row = tk.Frame(rows, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=4)
            inner = tk.Frame(row, bg=CARD)
            inner.pack(fill="x", padx=14, pady=12)
            slot = tk.Frame(inner, bg=CARD, width=52, height=52)
            slot.pack(side="left", padx=(0, 14))
            slot.pack_propagate(False)
            thumb = tk.Label(slot, bg=CARD, bd=0)
            placeholder = icons.get("mods" if is_mod else "folder", MUTED, 28)
            if placeholder:
                thumb.configure(image=placeholder)
            thumb.pack(expand=True)
            text = tk.Frame(inner, bg=CARD)
            text.pack(side="left", fill="x", expand=True)
            top = tk.Frame(text, bg=CARD)
            top.pack(fill="x")
            tk.Label(top, text=item.get("title", "?"), bg=CARD, fg=WHITE,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(top, text=self.tr("von ") + str(item.get("author", "?")), bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))
            desc = tk.Label(text, text=item.get("description", ""), bg=CARD, fg=MUTED,
                            font=("Segoe UI", 9), justify="left", anchor="w",
                            wraplength=max(240, canvas.winfo_width() - 260))
            desc.pack(fill="x", pady=(3, 5))
            desc_labels.append(desc)
            tk.Label(text, text=f"{format_count(item.get('downloads'))} Downloads   ·   "
                     f"{format_count(item.get('follows'))} Follower", bg=CARD, fg=ACCENT2,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
            if item.get("project_id") in done_ids:
                button = self.btn(inner, "Installiert", lambda: None, icon="check")
                button.configure(state="disabled")
            else:
                ref = []
                button = self.btn(inner, "Installieren", lambda it=item: install(it, ref[0]),
                                  primary=True, icon="download")
                ref.append(button)
            button.pack(side="right", padx=(14, 0))
            return thumb

        def set_thumb(label, data):
            try:
                image = icons.fit_image(data, 44)
                if image:
                    label.configure(image=image)
                    label.image = image
            except Exception:
                pass

        def load_icons(batch):
            try:
                os.makedirs(ICON_CACHE_DIR, exist_ok=True)
            except OSError:
                return
            for url, label in batch:
                try:
                    cache = os.path.join(ICON_CACHE_DIR, hashlib.sha1(url.encode()).hexdigest())
                    if os.path.isfile(cache):
                        with open(cache, "rb") as handle:
                            data = handle.read()
                    else:
                        with urllib.request.urlopen(modrinth._request(url), timeout=10) as response:
                            data = response.read(2_000_000)
                        with open(cache, "wb") as handle:
                            handle.write(data)
                    ui(lambda d=data, l=label: set_thumb(l, d))
                except Exception:
                    continue

        def show(token, hits, total, version, loader):
            if token != state["token"]:
                return
            done_ids = installed_ids()
            batch = []

            def build(item):
                thumb = add_row(item, done_ids)
                if item.get("icon_url"):
                    batch.append((item["icon_url"], thumb))

            def finish():
                state["loading"] = False
                state["offset"] += len(hits)
                if more["widget"] is not None:
                    try:
                        more["widget"].destroy()
                    except tk.TclError:
                        pass
                    more["widget"] = None
                target = f"Minecraft {version}" + (f" · {loader}" if loader else "")
                status.set(self.tr(f"{state['offset']} von {total} Ergebnissen für {target}") if total
                           else self.tr(f"Keine Treffer für {target}. Andere Version oder anderen Loader wählen."))
                if state["offset"] < total:
                    button = self.btn(rows, "Mehr laden", lambda: run_search(False), icon="plus")
                    button.pack(pady=14)
                    more["widget"] = button
                if batch:
                    threading.Thread(target=load_icons, args=(batch,), daemon=True).start()

            self._chunked(hits, build, size=4, done=finish, key=f"modrinth-{id(win)}")

        def fail(token, message):
            if token == state["token"]:
                state["loading"] = False
                status.set(self.tr("Suche fehlgeschlagen: ") + message)

        def run_search(reset=True):
            if reset:
                state["token"] += 1
                state["offset"] = 0
                for child in rows.winfo_children():
                    child.destroy()
                desc_labels.clear()
                more["widget"] = None
                canvas.yview_moveto(0)
            elif state["loading"]:
                return
            state["loading"] = True
            token, offset = state["token"], state["offset"]
            query = query_var.get().strip()
            version = version_var.get()
            loader = loader_var.get() if is_mod else None
            index = sorts.get(sort_var.get(), "relevance")
            status.set(self.tr("Suche auf Modrinth …"))

            def worker():
                try:
                    hits, total = modrinth.search(query, ptype, version, loader, offset, 20, index)
                    ui(lambda: show(token, hits, total, version, loader))
                except Exception as exc:
                    message = str(exc)
                    ui(lambda: fail(token, message))

            threading.Thread(target=worker, daemon=True).start()

        def install(item, button):
            version = version_var.get()
            loader = loader_var.get() if is_mod else None
            target = self._section_dir(section)
            library = self._mod_library_dir(version, section)
            button.configure(state="disabled", text=self.tr("Lädt …"))

            def worker():
                try:
                    installed, warnings = modrinth.install_project(
                        item["project_id"], version, loader, target, library, ptype,
                        status=lambda text: ui(lambda: status.set(self.tr(text))))
                    ui(lambda: finished(button, installed, warnings, version, loader))
                except Exception as exc:
                    message = str(exc)
                    ui(lambda: failed(button, message))

            threading.Thread(target=worker, daemon=True).start()

        def finished(button, installed, warnings, version, loader):
            button.configure(text=self.tr("Installiert"), icon_name="check", bg=CARD_HOVER, fg=WHITE,
                             state="disabled")
            parts = []
            if installed:
                parts.append("Installiert: " + ", ".join(installed))
            parts += [w for w in warnings if w != "Bereits installiert."]
            note = self._sync_profile_to(version, loader)
            if note:
                parts.append(note)
            status.set(self.tr("  ·  ".join(parts) or "Bereits installiert."))
            if self.active_page == "Mod Manager":
                try:
                    self._render_mod_section()
                except tk.TclError:
                    pass

        def failed(button, message):
            button.configure(state="normal", text=self.tr("Installieren"), icon_name="download")
            status.set(self.tr("Installation fehlgeschlagen: ") + message)
            self._messagebox("showerror", "Installation fehlgeschlagen", message, parent=win)

        entry.bind("<Return>", lambda _e: run_search(True))
        entry.focus_set()
        run_search(True)

    def show_mod_section(self, section):
        self.mod_section = section
        self.show_page("Mod Manager")

    def _render_mod_section(self):
        for child in self.mod_list_area.winfo_children():
            child.destroy()

        is_mod = self.mod_section == "Mods"
        title = "INSTALLIERTE MODS" if is_mod else "INSTALLIERTE TEXTURE PACKS"
        ext_note = "Unterstützt werden .jar-Dateien." if is_mod else "Unterstützt werden .zip-Texture-Packs."
        target = self._target_dir()

        self.txt(self.mod_list_area, title, 10, ACCENT2, "bold").pack(anchor="w", pady=(2, 8))
        path_outer, path_card = self._rounded_panel(self.mod_list_area, PANEL, BORDER)
        path_outer.pack(fill="x", pady=(0, 10))
        self.txt(path_card, "PROFIL-ORDNER", 8, MUTED, "bold", bg=PANEL).pack(anchor="w")
        self.txt(path_card, target, 9, WHITE, bg=PANEL).pack(anchor="w", pady=(4, 0))
        self.txt(path_card, ext_note, 8, MUTED, bg=PANEL).pack(anchor="w", pady=(5, 0))

        actions = tk.Frame(self.mod_list_area, bg=BG)
        actions.pack(fill="x", pady=(0, 12))
        self.btn(actions, "Dateien hinzufügen", self._add_minecraft_files,
                 primary=True, icon="plus").pack(side="left", padx=(0, 8))
        self.btn(actions, "Ordner öffnen", self._open_target_folder, icon="folder").pack(side="left")

        files_frame = tk.Frame(self.mod_list_area, bg=BG)
        files_frame.pack(fill="both", expand=True)
        try:
            entries = sorted(os.listdir(target), key=str.lower)
        except OSError:
            entries = []
        valid_ext = (".jar",) if is_mod else (".zip",)
        entries = [n for n in entries if n.lower().endswith(valid_ext)]
        profile_manifest = modrinth.Manifest(os.path.join(target, ".adrolla-installed.json"))
        profile_mods = {}
        for project_id, item in profile_manifest.data.items():
            if isinstance(item, dict) and item.get("file"):
                profile_mods[item["file"]] = (item.get("icon_url", ""), project_id)
        installed_icon_jobs = []
        if not entries:
            empty_outer, empty = self._rounded_panel(files_frame, CARD, BORDER)
            empty_outer.pack(fill="x", pady=4)
            self.txt(empty, "Noch keine Dateien gefunden", 11, WHITE, "bold", bg=CARD).pack(anchor="w")
            self.txt(empty, "Lade Inhalte aus dem Katalog oder füge Dateien von deinem PC hinzu.",
                     9, MUTED, bg=CARD).pack(anchor="w", pady=(5, 0))
        else:
            def build_entry(filename):
                row_outer, row = self._rounded_panel(files_frame, CARD, BORDER)
                row_outer.pack(fill="x", pady=3)
                if is_mod:
                    icon_label = tk.Label(row, bg=CARD, bd=0,
                                          image=icons.get("mods", ACCENT2, 22))
                    icon_label.pack(side="left", padx=(0, 9))
                    icon_label.image = icons.get("mods", ACCENT2, 22)
                    if filename in profile_mods:
                        icon_url, project_id = profile_mods[filename]
                        installed_icon_jobs.append((icon_url, project_id, icon_label))
                self.txt(row, filename, 9, WHITE, "bold", bg=CARD).pack(side="left", fill="x", expand=True)
                self.btn(row, "Entfernen", lambda n=filename: self._remove_minecraft_file(n),
                         icon="trash").pack(side="right")

            self._paged(entries, build_entry, files_frame, "installed", done=(
                lambda: self._queue_mod_icons(installed_icon_jobs)) if is_mod else None)

        library_title = "MEINE MOD-BIBLIOTHEK" if is_mod else "MEINE TEXTURE-PACK-BIBLIOTHEK"
        library_dir = self._mod_library_dir(section="mods" if is_mod else "resourcepacks")
        lib_outer, lib_card = self._rounded_panel(self.mod_list_area, PANEL, BORDER)
        lib_outer.pack(fill="x", pady=(14, 5))
        lib_header = tk.Frame(lib_card, bg=PANEL)
        lib_header.pack(fill="x")
        self.txt(lib_header, library_title, 10, WHITE, "bold", bg=PANEL).pack(side="left")
        try:
            library_entries = sorted(os.listdir(library_dir), key=str.lower)
        except OSError:
            library_entries = []
        valid_ext = (".jar",) if is_mod else (".zip",)
        library_entries = [n for n in library_entries if n.lower().endswith(valid_ext)]
        library_manifest = modrinth.Manifest(os.path.join(library_dir, ".adrolla-library.json"))
        library_mods = {}
        for project_id, item in library_manifest.data.items():
            if isinstance(item, dict) and item.get("file"):
                library_mods[item["file"]] = (item.get("icon_url", ""), project_id)
        for filename, metadata in profile_mods.items():
            library_mods.setdefault(filename, metadata)
        self.txt(lib_header, f"{len(library_entries)} {self.tr('Dateien')}",
                 8, MUTED, bg=PANEL).pack(side="right", padx=(8, 0))
        self.txt(lib_header, f"Minecraft {self.selected_version}", 8, ACCENT2,
                 "bold", bg=PANEL).pack(side="right")

        library_search_row = tk.Frame(lib_card, bg=PANEL)
        library_search_row.pack(fill="x", pady=(10, 8))
        self.txt(library_search_row, "Suchen", 8, MUTED, bg=PANEL).pack(side="left", padx=(0, 8))
        library_search = tk.StringVar()
        search_entry = tk.Entry(library_search_row, textvariable=library_search,
                                bg=CARD, fg=WHITE, insertbackground=ACCENT2,
                                relief="flat", font=("Segoe UI", 9))
        search_entry.pack(side="left", fill="x", expand=True, ipady=6)

        library_list = tk.Frame(lib_card, bg=PANEL)
        library_list.pack(fill="x")

        def render_library(query=""):
            for child in library_list.winfo_children():
                child.destroy()
            library_icon_jobs = []
            filtered = [name for name in library_entries if query.casefold() in name.casefold()]
            if not filtered:
                empty_text = ("Noch nichts gespeichert. Suche im Modrinth-Katalog und lade es direkt hierher."
                              if not library_entries else "Keine Dateien passen zu deiner Suche.")
                self.txt(library_list, empty_text, 8, MUTED, bg=PANEL).pack(anchor="w", pady=(4, 2))
                return
            def build_row(filename):
                row_outer, row = self._rounded_panel(library_list, CARD, BORDER, radius=14)
                row_outer.pack(fill="x", pady=3)
                if is_mod:
                    icon_label = tk.Label(row, bg=CARD, bd=0,
                                          image=icons.get("mods", ACCENT2, 22))
                    icon_label.pack(side="left", padx=(0, 9))
                    icon_label.image = icons.get("mods", ACCENT2, 22)
                    if filename in library_mods:
                        icon_url, project_id = library_mods[filename]
                        library_icon_jobs.append((icon_url, project_id, icon_label))
                details = tk.Frame(row, bg=CARD)
                details.pack(side="left", fill="x", expand=True)
                title = os.path.splitext(filename)[0]
                self.txt(details, title, 9, WHITE, "bold", bg=CARD).pack(anchor="w")
                try:
                    size_mb = os.path.getsize(os.path.join(library_dir, filename)) / (1024 * 1024)
                    detail_text = f"{filename}  ·  {size_mb:.1f} MB"
                except OSError:
                    detail_text = filename
                self.txt(details, detail_text, 7, MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))
                installed_path = os.path.join(target, filename)
                if os.path.isfile(installed_path):
                    installed_button = self.btn(row, "Im Profil", lambda: None, icon="check")
                    installed_button.configure(state="disabled")
                    installed_button.pack(side="right", padx=(6, 0))
                else:
                    self.btn(row, "Installieren", lambda n=filename, d=library_dir:
                             self._install_library_file(d, n), icon="download").pack(
                                 side="right", padx=(6, 0))
                self.btn(row, "Löschen", lambda n=filename, d=library_dir:
                         self._remove_library_file(d, n), icon="trash").pack(side="right")

            self._paged(filtered, build_row, library_list, "library", done=(
                lambda: self._queue_mod_icons(library_icon_jobs)) if is_mod else None)

        search_job = {"id": None}

        def on_search(*_args):  # kurz warten, bis zu Ende getippt ist
            if search_job["id"] is not None:
                try:
                    self.after_cancel(search_job["id"])
                except tk.TclError:
                    pass
            search_job["id"] = self.after(170, lambda: render_library(library_search.get().strip()))

        library_search.trace_add("write", on_search)
        render_library()

        if is_mod:
            note = self.tr("Über Modrinth installierte Mods passen automatisch zu Version und Loader des "
                    "Profils, inklusive Pflicht-Abhängigkeiten und Prüfsummen-Kontrolle. Der Loader "
                    "wird beim Spielstart installiert. Selbst importierte Mods prüft Adrolla nicht.")
        else:
            note = self.tr("Texture Packs werden in den resourcepacks-Ordner kopiert. "
                    "Aktiviere sie anschließend in Minecraft unter Optionen → Ressourcenpakete.")
        self.txt(self.mod_list_area, note, 8, MUTED).pack(anchor="w", pady=(10, 0))

    def _profiles_page(self):
        self._page_heading("Dein Setup", "Profile", "Jeder Spielstil ist jetzt ein eigenes Minecraft-Profil.")
        summary_outer, summary = self._rounded_panel(self.content, PANEL, BORDER)
        summary_outer.pack(fill="x", pady=(0, 14))
        self.txt(summary, f"{len(self.profiles)} / 10 {self.tr('Profile erstellt')}",
                 10, ACCENT2, "bold", bg=PANEL).pack(anchor="w")
        create_outer, create_row = self._rounded_panel(self.content, CARD, BORDER)
        create_row.configure(padx=7, pady=5)
        create_outer.pack(fill="x", pady=(0, 14))
        self.txt(create_row, "Neues Profil", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
        self.txt(create_row, "Wähle eine Vorlage wie SMP oder PvP und erstelle daraus ein eigenes Profil.",
                 9, MUTED, bg=CARD).pack(anchor="w", pady=(4, 10))
        self.btn(create_row, "Vorlagen ansehen", lambda: self.show_page("Vorlagen"),
                 primary=True, icon="plus").pack(anchor="e")
        self.profile_list = tk.Frame(self.content, bg=BG)
        self.profile_list.pack(fill="x")
        self._render_profiles()

    def _render_profiles(self):
        for child in self.profile_list.winfo_children():
            child.destroy()
        for index, name in enumerate(self.profiles, start=1):
            cfg = self.profile_settings.get(name, {})
            row_outer, row = self._rounded_panel(self.profile_list, CARD, BORDER)
            row.configure(padx=5, pady=3)
            row_outer.pack(fill="x", pady=4)
            left = tk.Frame(row, bg=CARD)
            left.pack(side="left", fill="x", expand=True)
            self.txt(left, f"{index:02d}  {name}", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
            profile_description = self.profile_descriptions.get(name)
            self.txt(left, profile_description or
                     f"Minecraft {cfg.get('version', self.selected_version)}  ·  {cfg.get('loader', 'Vanilla')}",
                     8, MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))
            if name == self.active_profile:
                self.txt(left, "AKTIV", 8, ACCENT2, "bold", bg=CARD).pack(anchor="w", pady=(3, 0))
            self.btn(row, "Mods", lambda n=name: self._open_profile_mods(n),
                     icon="mods").pack(side="right", padx=(5, 0))
            self.btn(row, "Auswählen", lambda n=name: self.select_profile(n),
                     icon="check").pack(side="right", padx=(5, 0))
            self.btn(row, "Bearbeiten", lambda n=name: self._edit_profile(n),
                     icon="settings").pack(side="right", padx=(5, 0))
            self.btn(row, "Löschen", lambda n=name: self.delete_profile(n),
                     icon="trash").pack(side="right")

    def _profile_templates(self):
        return [
            ("Leeres Profil", "Ein neutrales Profil ohne Spielstil-Vorlage", "Vanilla"),
            ("PvP", "Duelle und schnelle Kämpfe", "Fabric"),
            ("SMP", "Gemeinsames Survival mit Freunden", "Fabric"),
            ("BedWars", "Schnelle Runden und Teamplay", "Fabric"),
            ("Survival", "Erkundung und entspanntes Bauen", "Fabric"),
            ("SkyWars", "Kämpfe auf schwebenden Inseln", "Fabric"),
        ]

    def _open_profile_mods(self, name):
        self.active_profile = name
        self.selected_version = self.profile_settings.get(name, {}).get(
            "version", self.selected_version)
        self.mod_section = "Mods"
        self._save_profiles()
        self.show_page("Mod Manager")

    def _templates_page(self):
        self._page_heading("PROFIL-VORLAGEN", "Vorlagen",
                           "Füge ein vorbereitetes Spielprofil hinzu und passe es anschließend an.")
        summary_outer, summary = self._rounded_panel(self.content, PANEL, BORDER)
        summary_outer.pack(fill="x", pady=(0, 14))
        self.txt(summary, "Vorlagenprofile verwenden deine aktuelle Minecraft-Version und können einzeln angepasst werden.",
                 9, MUTED, bg=PANEL).pack(anchor="w")

        grid = tk.Frame(self.content, bg=BG)
        grid.pack(fill="x")
        for index, (name, description, loader) in enumerate(self._profile_templates()):
            outer, card = self._rounded_panel(grid, CARD, BORDER, radius=18)
            outer.grid(row=index // 2, column=index % 2, sticky="nsew",
                       padx=(0, 10 if index % 2 == 0 else 0), pady=(0, 10))
            card.configure(padx=10, pady=9)
            self.txt(card, name, 13, WHITE, "bold", bg=CARD).pack(anchor="w")
            self.txt(card, description, 9, MUTED, bg=CARD).pack(anchor="w", pady=(5, 10))
            loader_text = ("Vorlage nutzt Fabric und die aktuell ausgewählte Minecraft-Version."
                           if loader == "Fabric" else
                           "Vorlage verwendet die aktuell ausgewählte Minecraft-Version.")
            self.txt(card, loader_text, 8, ACCENT2, "bold", bg=CARD).pack(anchor="w", pady=(0, 12))
            self.btn(card, "Vorlage hinzufügen",
                     lambda n=name, d=description, l=loader: self._add_profile_template(n, d, l),
                     primary=True, icon="plus").pack(anchor="w")
        grid.columnconfigure(0, weight=1, uniform="profile_template_page")
        grid.columnconfigure(1, weight=1, uniform="profile_template_page")

    def _add_profile_template(self, name, description, loader):
        if len(self.profiles) >= 10:
            self._messagebox("showinfo", "Maximale Anzahl", "Du kannst höchstens 10 Profile erstellen.")
            return
        base_name = f"{self.tr('Profil')} {len(self.profiles) + 1}" if name == "Leeres Profil" else name
        candidate, suffix = base_name, 2
        existing_names = {profile.casefold() for profile in self.profiles}
        while candidate.casefold() in existing_names:
            candidate, suffix = f"{base_name} {suffix}", suffix + 1
        if self.create_profile(candidate, description, loader):
            self.show_page("Profile")

    def create_profile(self, name=None, description="", loader="Vanilla"):
        if len(self.profiles) >= 10:
            self._messagebox("showinfo", "Maximale Anzahl", "Du kannst höchstens 10 Profile erstellen.")
            return False
        name = (name or "").strip()
        if not name:
            name = f"{self.tr('Profil')} {len(self.profiles) + 1}"
        if any(existing.casefold() == name.casefold() for existing in self.profiles):
            self._messagebox("showwarning", "Name bereits vorhanden", "Bitte wähle einen anderen Profilnamen.")
            return False
        self.profiles.append(name)
        self.profile_settings[name] = {"version": self.selected_version,
                                       "loader": loader if loader in loaders.LOADERS else "Vanilla"}
        self.profile_descriptions[name] = description
        self.active_profile = name
        self._save_profiles()
        if getattr(self, "profile_list", None) and self.profile_list.winfo_exists():
            self._render_profiles()
        return True

    def select_profile(self, name):
        self.active_profile = name
        cfg = self.profile_settings.get(name, {})
        self.selected_version = cfg.get("version", self.selected_version)
        self._save_profiles()
        if self.active_page == "Profile" and hasattr(self, "profile_list"):
            self._render_profiles()
        else:
            self.show_page(self.active_page)

    def delete_profile(self, name):
        if len(self.profiles) <= 1:
            self._messagebox("showinfo", "Profil behalten", "Mindestens ein Profil muss vorhanden sein.")
            return
        self.profiles.remove(name)
        self.profile_settings.pop(name, None)
        self.profile_dirs.pop(name, None)
        self.profile_descriptions.pop(name, None)
        if self.active_profile == name:
            self.active_profile = self.profiles[0]
            self.selected_version = self.profile_settings.get(
                self.active_profile, {}).get("version", self.selected_version)
        self._save_profiles()
        self._render_profiles()

    def _draw_theme_swatches(self, canvas, palette):
        canvas.delete("all")
        width = max(90, canvas.winfo_width())
        colors = [palette[key] for key in ("BG", "SIDEBAR", "PANEL", "CARD", "ACCENT", "ACCENT2")]
        gap = 4
        swatch_width = max(12, (width - gap * (len(colors) - 1)) / len(colors))
        for index, color in enumerate(colors):
            left = index * (swatch_width + gap)
            points = [left + 5, 2, left + swatch_width - 5, 2,
                      left + swatch_width, 2, left + swatch_width, 7,
                      left + swatch_width, 19, left + swatch_width, 24,
                      left + swatch_width - 5, 24, left + 5, 24,
                      left, 24, left, 19, left, 7, left, 2]
            canvas.create_polygon(points, smooth=True, splinesteps=8, fill=color, outline="")

    def _settings_page(self):
        self.txt(self.content, "Einstellungen", 20, WHITE, "bold").pack(anchor="w", pady=(10, 4))
        self.txt(self.content, "Passe deinen Adrolla Client an.", 9, MUTED).pack(anchor="w", pady=(0, 16))

        shortcut_outer, shortcut_row = self._rounded_panel(self.content, CARD, BORDER)
        shortcut_outer.pack(fill="x", pady=(0, 14))
        shortcut_text = tk.Frame(shortcut_row, bg=CARD)
        shortcut_text.pack(side="left", fill="x", expand=True)
        self.txt(shortcut_text, "Desktop-Symbol", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
        self.txt(shortcut_text, "Adrolla-Verknüpfung mit Galaxie-Symbol erstellen.",
                 8, MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))
        self.btn(shortcut_row, "Zum Desktop hinzufügen", self._create_desktop_shortcut,
                 primary=True).pack(side="right")

        menu_outer, menu_row = self._rounded_panel(self.content, CARD, BORDER)
        menu_outer.pack(fill="x", pady=(0, 14))
        menu_text = tk.Frame(menu_row, bg=CARD)
        menu_text.pack(side="left", fill="x", expand=True)
        self.txt(menu_text, "Minecraft-Menü im Adrolla-Stil", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
        self.txt(menu_text, "Dunkler Saturn-Hintergrund und runde Akzentflächen für Minecraft.",
                 8, MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))
        self.btn(menu_row, "Menü einrichten", self._install_adrolla_minecraft_theme,
                 primary=True, icon="settings").pack(side="right")

        self.txt(self.content, "MICROSOFT-ANMELDUNG", 9, ACCENT2, "bold").pack(anchor="w", pady=(0, 7))
        client_outer, client_row = self._rounded_panel(self.content, CARD, BORDER)
        client_outer.pack(fill="x", pady=(0, 7))
        client_fields = tk.Frame(client_row, bg=CARD)
        client_fields.pack(fill="x")
        self.txt(client_fields, "App-Client-ID", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
        self.client_id_var = tk.StringVar(value=load_client_id())
        client_entry = tk.Entry(client_fields, textvariable=self.client_id_var,
                                bg=CARD_HOVER, fg=WHITE, insertbackground=ACCENT2,
                                relief="flat", font=("Segoe UI", 9))
        client_entry.pack(side="left", fill="x", expand=True, ipady=8, pady=(8, 0), padx=(0, 9))
        self.btn(client_fields, "Speichern", self.save_client_id, primary=True).pack(side="right", pady=(8, 0))
        self.txt(client_row,
                 "Standardmäßig Microsofts Minecraft-Anmeldung. Firefox-Login, danach die "
                 "Rücksprung-URL einmal in Adrolla einfügen. Eigene App-ID optional.",
                 8, MUTED, bg=CARD).pack(anchor="w", pady=(8, 0))
        help_link = self.txt(client_row, "Microsoft-Anleitung zur App-Registrierung öffnen", 8, ACCENT2, bg=CARD)
        help_link.pack(anchor="w", pady=(4, 0))
        help_link.configure(cursor="hand2")
        help_link.bind("<Button-1>", lambda _event: webbrowser.open(
            "https://learn.microsoft.com/en-us/entra/identity-platform/scenario-desktop-app-registration"))

        theme_outer, theme_row = self._rounded_panel(self.content, CARD, BORDER)
        theme_outer.pack(fill="x", pady=(0, 14))
        swatches = tk.Canvas(theme_row, width=145, height=22, bg=CARD, highlightthickness=0)
        swatches.pack(side="left", padx=(0, 12))
        self._draw_theme_swatches(swatches, THEMES.get(self.theme, THEMES["Black & Grey"]))
        theme_text = tk.Frame(theme_row, bg=CARD)
        theme_text.pack(side="left", fill="x", expand=True)
        self.txt(theme_text, "Dein Look", 10, WHITE, "bold", bg=CARD).pack(anchor="w")
        self.txt(theme_text, self.theme, 8, MUTED, bg=CARD).pack(anchor="w", pady=(2, 0))
        theme_button = tk.Menubutton(theme_row, text=self.tr("Design wählen  ▾"),
                                     bg=CARD_HOVER, fg=WHITE, activebackground=ACCENT,
                                     activeforeground=BG, relief="flat", bd=0,
                                     highlightthickness=0, cursor="hand2",
                                     font=("Segoe UI", 9, "bold"), padx=12, pady=8)
        theme_menu = tk.Menu(theme_button, tearoff=0, bg=CARD, fg=WHITE,
                             activebackground=ACCENT, activeforeground=BG,
                             font=("Segoe UI", 9), bd=0)
        for name in THEMES:
            theme_menu.add_command(label=("✓  " if name == self.theme else "    ") + self.tr(name),
                                   command=lambda n=name: self.change_theme(n))
        theme_button.configure(menu=theme_menu)
        theme_button.pack(side="right")

        version_outer, version_row = self._rounded_panel(self.content, CARD, BORDER)
        version_outer.pack(fill="x", pady=5)
        self.txt(version_row, "Minecraft-Version", 10, WHITE, "bold", bg=CARD).pack(side="left")
        self.version_var = tk.StringVar(value=self.selected_version)
        version_menu = self._option_menu(version_row, self.version_var, MC_VERSIONS,
                                         command=self.change_version)
        version_menu.config(bg=CARD_HOVER, fg=WHITE, activebackground=ACCENT,
                            activeforeground=BG, relief="flat", bd=0,
                            highlightthickness=0, font=("Segoe UI", 9), padx=8)
        version_menu["menu"].config(bg=CARD, fg=WHITE,
                                    activebackground=ACCENT, activeforeground=BG)
        version_menu.pack(side="right")

        loader_outer, loader_row = self._rounded_panel(self.content, CARD, BORDER)
        loader_outer.pack(fill="x", pady=5)
        self.txt(loader_row, "Mod-Loader (aktives Profil)", 10, WHITE, "bold", bg=CARD).pack(side="left")
        self.loader_var = tk.StringVar(value=self.active_loader)
        self._option_menu(loader_row, self.loader_var, loaders.LOADERS,
                          command=self.change_loader).pack(side="right")

        rows = [
            ("Version wird verwendet für", "Spielstart und Modrinth-Suche"),
            ("Fenstermodus", "Ein Fenster – Navigation bleibt im Client")
        ]
        for title, value in rows:
            row_outer, row = self._rounded_panel(self.content, CARD, BORDER)
            row_outer.pack(fill="x", pady=5)
            self.txt(row, title, 10, WHITE, "bold", bg=CARD).pack(side="left")
            self.txt(row, value, 9, MUTED, bg=CARD).pack(side="right")

        lang_outer, lang_row = self._rounded_panel(self.content, CARD, BORDER)
        lang_outer.pack(fill="x", pady=5)
        self.txt(lang_row, "Sprache", 10, WHITE, "bold", bg=CARD).pack(side="left")
        self.language_var = tk.StringVar(value=self.tr(self.language))
        language_menu = tk.OptionMenu(
            lang_row, self.language_var, self.tr("Deutsch"), "English",
            command=lambda choice: self.change_language(
                "Deutsch" if choice in ("German", "Deutsch") else "English"))
        language_menu.config(bg=CARD_HOVER, fg=WHITE, activebackground=ACCENT,
                             activeforeground=WHITE, relief="flat", bd=0,
                             highlightthickness=0, font=("Segoe UI", 9))
        language_menu["menu"].config(bg=CARD_HOVER, fg=WHITE,
                                     activebackground=ACCENT, activeforeground=WHITE)
        language_menu.pack(side="right")

        fullscreen_outer, fullscreen_row = self._rounded_panel(self.content, CARD, BORDER)
        fullscreen_outer.pack(fill="x", pady=5)
        self.txt(fullscreen_row, "Vollbild", 10, WHITE, "bold", bg=CARD).pack(side="left")
        self.fullscreen_var = tk.BooleanVar(value=self._fullscreen)
        fullscreen_check = tk.Checkbutton(
            fullscreen_row, text=self.tr("Aktivieren"), variable=self.fullscreen_var,
            command=lambda: self.set_fullscreen(self.fullscreen_var.get()),
            bg=CARD, fg=WHITE, activebackground=CARD, activeforeground=WHITE,
            selectcolor=CARD_HOVER, font=("Segoe UI", 9), relief="flat",
            highlightthickness=0
        )
        fullscreen_check.pack(side="right")
        self.txt(self.content,
                 "Tipp: F11 schaltet Vollbild um, Esc beendet den Vollbildmodus.",
                 9, MUTED).pack(anchor="w", pady=(8, 0))

    def _create_desktop_shortcut(self):
        if sys.platform != "win32":
            self._messagebox("showerror", "Nicht verfügbar", "Desktop-Verknüpfungen werden hier nur unter Windows erstellt.")
            return
        try:
            app_dir = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                       else os.path.dirname(os.path.abspath(__file__)))
            icon_source = resource_path("saturn.ico")
            data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                                    "Adrolla Client")
            os.makedirs(data_dir, exist_ok=True)
            icon_target = os.path.join(data_dir, "saturn.ico")
            shutil.copy2(icon_source, icon_target)

            if getattr(sys, "frozen", False):
                target = sys.executable
                arguments = ""
            else:
                target = os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                                      "System32", "wscript.exe")
                script = os.path.join(app_dir, "START_ADROLLA.vbs")
                if not os.path.isfile(script):
                    raise FileNotFoundError("START_ADROLLA.vbs wurde im Client-Ordner nicht gefunden.")
                arguments = f'"{script}"'

            desktop_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "[Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)"],
                capture_output=True, text=True, timeout=10
            )
            desktop = desktop_result.stdout.strip() or os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desktop, exist_ok=True)
            shortcut_path = os.path.join(desktop, "Adrolla Client.lnk")

            # Encode values as Base64 so paths with spaces or quotes are passed safely to PowerShell.
            encode = lambda value: base64.b64encode(value.encode("utf-8")).decode("ascii")
            values = {"target": target, "arguments": arguments, "app_dir": app_dir,
                      "icon": icon_target, "shortcut": shortcut_path}
            assignments = "\n".join(
                f"${key}=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encode(value)}'))"
                for key, value in values.items()
            )
            ps_script = assignments + "\n" + (
                "$shell=New-Object -ComObject WScript.Shell; "
                "$link=$shell.CreateShortcut($shortcut); "
                "$link.TargetPath=$target; $link.Arguments=$arguments; "
                "$link.WorkingDirectory=$app_dir; $link.IconLocation=($icon + ',0'); "
                "$link.Description='Adrolla Client'; $link.Save()"
            )
            encoded_script = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-EncodedCommand", encoded_script],
                capture_output=True, text=True, timeout=20
            )
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Windows konnte die Verknüpfung nicht erstellen.")
            self._messagebox("showinfo", "Desktop-Symbol erstellt",
                                f"Adrolla mit Galaxie-Symbol liegt jetzt auf dem Desktop:\n{shortcut_path}")
        except Exception as exc:
            self._messagebox("showerror", "Verknüpfung konnte nicht erstellt werden", str(exc))

    def change_language(self, selected):
        self.language = "English" if selected == "English" else "Deutsch"
        english_names = {"Startseite": "Home", "Mod Manager": "Mods",
                         "Profile": "Profiles", "Vorlagen": "Templates",
                         "Einstellungen": "Settings"}
        german_names = {"Startseite": "Start", "Mod Manager": "Mods",
                        "Profile": "Profile", "Vorlagen": "Vorlagen",
                        "Einstellungen": "Setup"}
        for label, button in self.nav_buttons.items():
            self.nav_labels[label].configure(text=(english_names if self.language == "English"
                                                   else german_names)[label])
        self.mode_menu.entryconfigure(0, label=self.tr("Offline spielen"))
        self.mode_menu.entryconfigure(1, label=self.tr("Online spielen"))
        self._refresh_mode_button()
        self.show_page(self.active_page)

    def _refresh_mode_button(self):
        if self.play_mode == "Online" and not self.auth_result and not self._session_refreshing:
            self.play_mode = "Offline"
            self._save_play_mode()
        label = "Online" if self.play_mode == "Online" else "Offline"
        self.mode_button.configure(text=f"{label}  ▾", fg=GREEN if label == "Online" else WHITE)
        if self.account_name:
            self.status_label.config(text=f"●  {label} · {self.account_name}",
                                     fg=GREEN if label == "Online" else ACCENT2)
        else:
            self.status_label.config(text=self.tr("●  Lokaler Modus"), fg=ACCENT2)

    def _show_account_menu(self):
        if hasattr(self, "account_menu"):
            try:
                self.account_menu.destroy()
            except tk.TclError:
                pass
        menu = tk.Menu(self, tearoff=0, bg=CARD, fg=WHITE,
                       activebackground=ACCENT, activeforeground=BG,
                       font=("Segoe UI", 9), bd=0)
        if self.account_name:
            menu.add_command(label=self.tr("Angemeldet: ") + self.account_name, state="disabled")
            menu.add_command(label=self.tr("Abmelden"), command=self.logout_account)
        else:
            menu.add_command(label=self.tr("Microsoft-Account anmelden"), command=lambda: self._begin_login("account"))
        menu.add_command(label=self.tr("Weiteren Account hinzufügen"), command=self.add_account)
        others = [name for name in self.accounts if name != self.account_name]
        if others:
            menu.add_separator()
            for name in others:
                menu.add_command(label=self.tr("Account wechseln") + ": " + name,
                                 command=lambda n=name: self._switch_account(n))
        self.account_menu = menu
        menu.update_idletasks()
        button = self.account_menu_button
        x = button.winfo_rootx()
        y = max(0, button.winfo_rooty() - menu.winfo_reqheight())
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def add_account(self):
        self._begin_login("add")

    def _begin_login(self, purpose):
        if self._login_in_progress:
            return
        client_id = load_client_id()
        if not client_id or client_id == "PASTE_YOUR_MICROSOFT_APP_CLIENT_ID_HERE":
            self._messagebox("showerror", 
                "Online-Anmeldung nicht eingerichtet",
                "Für die Microsoft-Anmeldung fehlt die App-Client-ID.\n\n"
                "Trage die Client-ID unter Einstellungen → Microsoft-Anmeldung ein und versuche es erneut."
            )
            return
        if client_id.lower() == "74658136-14ec-4630-ad9b-26e160ff0fc6":
            self._messagebox("showerror", 
                "Falsche App-Client-ID",
                "Diese ID gehört zur Microsoft-Entra-Verwaltungsoberfläche (ADIbizaUX), nicht zu Adrolla.\n\n"
                "Registriere eine eigene App, die persönliche Microsoft-Konten unterstützt, "
                "aktiviere den Public Client Flow und trage deren Application (client) ID hier ein."
            )
            return
        self._login_purpose = purpose
        self._login_in_progress = True
        self.mode_button.configure(state="disabled", text=self.tr("Anmeldung …"))
        self.account_menu_button.configure(state="disabled")
        self.status_label.config(text=self.tr("●  Microsoft-Anmeldung wird gestartet …"), fg=ACCENT2)
        threading.Thread(target=self._login_worker, args=(client_id,), daemon=True).start()

    def _switch_account(self, name):
        self._switch_account_async(name)

    def logout_account(self):
        if self.account_name:
            self.accounts.pop(self.account_name, None)
        self.account_name = None
        self.auth_result = None
        self.play_mode = "Offline"
        self._save_play_mode()
        self._save_persistent_sessions()
        self._refresh_mode_button()

    def set_play_mode(self, mode):
        if mode not in ("Offline", "Online"):
            return
        if mode == "Online" and not self.auth_result:
            self._messagebox("showinfo", 
                "Microsoft-Konto erforderlich",
                "Melde dich zuerst unten links über das Profil-Symbol mit einem Minecraft-Java-Konto an, "
                "um Online-Multiplayer zu aktivieren."
            )
            return
        self.play_mode = mode
        self._save_play_mode()
        self._refresh_mode_button()

    def _set_status(self, text):
        self.after(0, lambda: self.status_label.config(text=self.tr(text), fg=ACCENT))

    def _login_worker(self, client_id):
        try:
            result = microsoft_to_minecraft(client_id, self._set_status,
                                            self._prompt_legacy_redirect_url)
            self._pending_auth_result = result
            self.after(0, self._login_success)
        except Exception as e:
            error_text = str(e)
            self.after(0, lambda error=error_text: self._login_failed(error))

    def _prompt_legacy_redirect_url(self):
        completed = threading.Event()
        result = {}

        def ask_for_url():
            result["url"] = simpledialog.askstring(
                "Microsoft-Anmeldung abschließen",
                "Melde dich in Firefox an. Danach wirst du zu einer Seite mit „oauth20_desktop.srf“ "
                "in der Adresszeile weitergeleitet. Kopiere die vollständige URL aus der "
                "Adresszeile, füge sie hier ein und klicke auf OK.",
                parent=self,
            )
            completed.set()

        self.after(0, ask_for_url)
        if not completed.wait(300):
            raise AuthError("Zeitüberschreitung beim Warten auf die Microsoft-Rücksprung-URL.")
        if not result.get("url"):
            raise AuthError("Microsoft-Anmeldung abgebrochen.")
        return result["url"]

    def _login_success(self):
        result = self._pending_auth_result
        self._pending_auth_result = None
        self._login_in_progress = False
        self.mode_button.config(state="normal")
        self.account_menu_button.configure(state="normal")
        if not result:
            self._refresh_mode_button()
            return
        name = result["name"]
        self.accounts[name] = result
        if self._login_purpose == "add" and self.account_name:
            self._save_persistent_sessions()
            self._refresh_mode_button()
            self._messagebox("showinfo", "Account hinzugefügt",
                                f"{name} wurde hinzugefügt.\n\nZum Wechseln unten links auf das Profil-Symbol klicken.")
            return
        self.account_name = name
        self.auth_result = result
        self.play_mode = "Online"
        self._save_play_mode()
        self._save_persistent_sessions()
        self._refresh_mode_button()
        self._messagebox("showinfo", "Angemeldet",
            f"Minecraft-Profil: {self.account_name}\n\n"
            "Dein Konto ist angemeldet. Online-Multiplayer ist jetzt verfügbar. "
            "Deine Spielprofile kannst du im Profile-Bereich wechseln.")

    def _login_failed(self, error):
        purpose = self._login_purpose
        self._login_in_progress = False
        self.mode_button.config(state="normal")
        self.account_menu_button.configure(state="normal")
        if purpose != "add" or not self.account_name:
            self.play_mode = "Offline"
            self._save_play_mode()
        self._refresh_mode_button()
        self._messagebox("showerror", "Anmeldung fehlgeschlagen", error)

    def play(self):
        if self._launch_in_progress:
            return
        if self._theme_installing:
            self._set_status("Adrolla-Menü wird eingerichtet …")
            return
        if self.game_process is not None:
            if self.game_process.poll() is None:
                self.stop_minecraft()
                return
            self._game_exited(self.game_process)
        if self._session_refreshing:
            self._set_status("Dein Microsoft-Konto wird noch angemeldet …")
            return
        if self.active_loader == "Vanilla":
            try:
                has_mods = any(name.lower().endswith(".jar")
                               for name in os.listdir(self._section_dir("mods")))
            except OSError:
                has_mods = False
            if has_mods:
                self._messagebox(
                    "showwarning", "Mods benötigen einen Loader",
                    "Für dieses Profil sind Mods installiert, aber es verwendet Vanilla. "
                    "Wähle Fabric, Quilt, Forge oder NeoForge, damit Minecraft die Mods lädt.")
                self._edit_profile(self.active_profile)
                return
        account = self.auth_result
        account_valid = bool(account and all(account.get(key) for key in
                                             ("name", "uuid", "minecraft_access_token")))
        if self.play_mode == "Online" and not account_valid:
            self._messagebox("showinfo", 
                "Minecraft-Konto erforderlich",
                f"Adrolla startet Minecraft Java {self.selected_version} direkt. Dafür braucht Minecraft ein gültiges "
                "Microsoft-Konto mit Java-Lizenz. Melde dich unten links über das Profil-Symbol an.\n\n"
                "Für Online-Multiplayer ist eine erfolgreiche Microsoft-Anmeldung erforderlich."
            )
            return
        if self.play_mode != "Online" and not account_valid:
            # Minecraft supports a local offline profile. Multiplayer and chat are
            # disabled in the launch options below, so no Microsoft token is used.
            local_name = read_config().get("offline_name", "AdrollaSpieler")
            if not isinstance(local_name, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,16}", local_name):
                local_name = "AdrollaSpieler"
            account = {
                "name": local_name,
                "uuid": uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{local_name}").hex,
                "minecraft_access_token": "0",
            }
        if minecraft_launcher_lib is None:
            self._messagebox("showerror", 
                "Startkomponente fehlt",
                "Die Minecraft-Startkomponente ist nicht installiert. Starte START_ADROLLA.bat "
                "erneut oder installiere minecraft-launcher-lib mit pip."
            )
            return

        skip_theme_once = self._skip_adrolla_theme_once
        self._skip_adrolla_theme_once = False
        if (not skip_theme_once and self.active_loader != "Vanilla"
                and not self._adrolla_menu_theme_ready()):
            self._install_adrolla_minecraft_theme(auto_launch=True)
            return

        self._launch_in_progress = True
        version = self.selected_version
        loader = self.active_loader
        game_dir = self._profile_dir()
        self._play_btn("WIRD GESTARTET …", "play", False)
        self._set_status(f"Minecraft Java {version} ({loader}) wird vorbereitet …")
        threading.Thread(target=self._launch_minecraft_worker,
                         args=(version, loader, game_dir, dict(account), self.play_mode),
                         daemon=True).start()

    def _launch_minecraft_worker(self, version, loader, game_dir, account, play_mode):
        try:
            if account.get("refresh_token"):
                self._set_status("Microsoft-Sitzung wird für den Spielstart erneuert …")
                account = refresh_minecraft_account(load_client_id(), account["refresh_token"])
                self.after(0, lambda refreshed=account: self._store_refreshed_active_account(refreshed))
            directory = self._minecraft_dir()
            self._set_status(f"Minecraft {version} wird installiert/geprüft …")
            callback = {
                "setStatus": lambda text: self._set_status(f"Minecraft: {text}"),
                "setProgress": lambda value: self._set_status(f"Minecraft wird geladen … {value}%"),
                "setMax": lambda value: None,
            }
            version_id = loaders.install_loader(
                minecraft_launcher_lib, loader, version, directory, callback=callback)
            runtime_options = {}
            version_parts = version.split(".")
            if len(version_parts) > 1 and version_parts[0] == "1" and int(version_parts[1]) <= 16:
                self._set_status("Java-Runtime für diese ältere Minecraft-Version wird geprüft …")
                minecraft_launcher_lib.runtime.install_jvm_runtime(
                    "jre-legacy", directory, callback=callback
                )
                java_path = minecraft_launcher_lib.runtime.get_executable_path(
                    "jre-legacy", directory
                )
                if java_path:
                    runtime_options["executablePath"] = java_path
            options = {
                "username": account["name"],
                "uuid": account["uuid"],
                "token": account["minecraft_access_token"],
                "launcherName": "Adrolla Client",
                "launcherVersion": APP_VERSION,
                "gameDirectory": game_dir,
                "disableMultiplayer": play_mode != "Online",
                "disableChat": play_mode != "Online",
            }
            options.update(runtime_options)
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version_id, directory, options
            )
            os.makedirs(game_dir, exist_ok=True)
            process = subprocess.Popen(command, cwd=game_dir)
            self.after(0, lambda proc=process: self._launch_finished(
                f"Minecraft {version} ({loader}) wurde im {play_mode}-Modus gestartet.", proc))
        except Exception as exc:
            self.after(0, lambda error=str(exc): self._launch_failed(error))

    def _launch_finished(self, status, process):
        self._launch_in_progress = False
        self.game_process = process
        self._play_btn("STOPPEN", "stop")
        self._set_status(status)
        threading.Thread(target=self._monitor_game_process, args=(process,), daemon=True).start()

    def _monitor_game_process(self, process):
        while process.poll() is None:
            time.sleep(0.75)
        self.after(0, lambda proc=process: self._game_exited(proc))

    def _game_exited(self, process):
        if self.game_process is not process:
            return
        self.game_process = None
        self._play_btn("SPIELEN", "play")
        self._set_status("Minecraft wurde geschlossen.")

    def stop_minecraft(self):
        process = self.game_process
        if process is None or process.poll() is not None:
            if process is not None:
                self._game_exited(process)
            return
        self._play_btn("SCHLIESSE …", "stop", False)
        self._set_status("Minecraft wird geschlossen …")
        threading.Thread(target=self._stop_minecraft_worker, args=(process,), daemon=True).start()

    def _stop_minecraft_worker(self, process):
        # Ask the game window to close normally first, preserving its save/exit flow.
        sent_close = False
        if sys.platform == "win32":
            try:
                enum_windows = ctypes.windll.user32.EnumWindows
                get_window_pid = ctypes.windll.user32.GetWindowThreadProcessId
                post_message = ctypes.windll.user32.PostMessageW
                is_visible = ctypes.windll.user32.IsWindowVisible
                callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

                def visit(hwnd, _lparam):
                    nonlocal sent_close
                    pid = wintypes.DWORD()
                    get_window_pid(hwnd, ctypes.byref(pid))
                    if pid.value == process.pid and is_visible(hwnd):
                        sent_close = bool(post_message(hwnd, 0x0010, 0, 0)) or sent_close  # WM_CLOSE
                    return True

                callback = callback_type(visit)
                enum_windows(callback, 0)
            except Exception:
                pass

        try:
            process.wait(timeout=8)
            self.after(0, lambda proc=process: self._game_exited(proc))
            return
        except subprocess.TimeoutExpired:
            pass

        answer = threading.Event()
        choice = {"force": False}

        def ask_force():
            if self.game_process is not process or process.poll() is not None:
                answer.set()
                return
            choice["force"] = self._messagebox("askyesno", 
                "Minecraft schließen",
                "Minecraft reagiert nicht auf das normale Schließen.\n\n"
                "Soll der Prozess jetzt erzwungen beendet werden? Ungespeicherter Fortschritt kann verloren gehen."
            )
            answer.set()

        self.after(0, ask_force)
        answer.wait(60)
        if choice["force"] and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            self.after(0, lambda proc=process: self._game_exited(proc))
        else:
            self.after(0, lambda proc=process: self._stop_cancelled(proc))

    def _stop_cancelled(self, process):
        if self.game_process is process and process.poll() is None:
            self._play_btn("STOPPEN", "stop")
            self._set_status("Minecraft läuft weiter.")

    def _launch_failed(self, error):
        self._launch_in_progress = False
        self.game_process = None
        self._play_btn("SPIELEN", "play")
        self._set_status("Minecraft konnte nicht gestartet werden.")
        self._messagebox("showerror", 
            "Minecraft-Start fehlgeschlagen",
            "Adrolla konnte Minecraft nicht starten. Prüfe die ausgewählte Version, "
            "deine Internetverbindung und ob dein angemeldetes Konto Minecraft Java besitzt.\n\n"
            f"Details: {error}"
        )

    # ---- Auto-Update -------------------------------------------------------
    def _check_for_updates(self):
        cfg = read_config()
        url = str(cfg.get("update_url", "")).strip()
        if not url or cfg.get("auto_update", True) is False:
            return

        def worker():
            try:
                info = updater.check(url, APP_VERSION)
            except Exception:
                return  # keine Verbindung o. Ä.: still ignorieren
            if info:
                self.after(0, lambda: self._offer_update(info))

        threading.Thread(target=worker, daemon=True).start()

    def _offer_update(self, info):
        notes = f"\n\n{info['notes']}" if info.get("notes") else ""
        if not self._messagebox(
            "askyesno", "Update verfügbar",
            f"Adrolla {info['version']} ist verfügbar (installiert: {APP_VERSION}).{notes}\n\n"
            "Jetzt aktualisieren? Einstellungen und Konten bleiben erhalten."
        ):
            return
        if getattr(sys, "frozen", False):
            webbrowser.open(info["url"])
            return
        self._set_status("Update wird geladen ...")

        def worker():
            try:
                updater.install(info, os.path.dirname(os.path.abspath(__file__)))
            except Exception as exc:
                self.after(0, lambda: self._update_failed(str(exc)))
                return
            self.after(0, self._restart_after_update)

        threading.Thread(target=worker, daemon=True).start()

    def _update_failed(self, error):
        self._set_status("Update fehlgeschlagen.")
        self._messagebox("showerror", "Update fehlgeschlagen", error)

    def _restart_after_update(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        launcher = os.path.join(folder, "START_ADROLLA.vbs")
        try:
            if os.path.exists(launcher) and hasattr(os, "startfile"):
                os.startfile(launcher)
            else:
                subprocess.Popen([sys.executable, os.path.join(folder, "main.py")], cwd=folder)
        except Exception as exc:
            self._messagebox("showinfo", "Update installiert",
                             f"Bitte Adrolla neu starten.\n\n{exc}")
            return
        self.destroy()

if __name__ == "__main__":
    set_windows_app_user_model_id()
    AdrollaClient().mainloop()
