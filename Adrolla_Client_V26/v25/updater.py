"""Auto-Updater für den Adrolla Client.

Ablauf: Manifest (JSON) per https laden -> neuere Version? -> ZIP laden ->
SHA-256 prüfen -> sicher entpacken -> Dateien ersetzen (mit Backup) ->
Neustart. Benutzerdaten (config.json) bleiben erhalten, neue Einstellungs-
schlüssel werden ergänzt.

Manifest-Beispiel (update.json, siehe make_release.py):
  {"version": "26", "url": "https://.../Adrolla_Client_V26.zip",
   "sha256": "<hex>", "notes": "Was ist neu"}
Reine Standardbibliothek.
"""
import hashlib
import json
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile

USER_AGENT = "AdrollaClient-Updater"
MAX_MANIFEST = 64 * 1024
MAX_ZIP = 200 * 1024 * 1024
MAX_UNPACKED = 500 * 1024 * 1024
PRESERVE = {"config.json"}          # nie überschreiben (nur neue Schlüssel ergänzen)
SKIP_DIRS = {"__pycache__", "_update_backup", "_update_tmp"}


class UpdateError(Exception):
    pass


def _require_https(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise UpdateError("Update-Adresse muss https verwenden.")


def parse_version(text):
    nums = []
    for piece in str(text).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        nums.append(int(digits) if digits else 0)
    return tuple(nums)


def is_newer(remote, local):
    a, b = parse_version(remote), parse_version(local)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


def check(manifest_url, current_version, timeout=15):
    """Gibt das Manifest zurück, wenn eine neuere Version existiert, sonst None."""
    _require_https(manifest_url)
    req = urllib.request.Request(manifest_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_MANIFEST + 1)
    except Exception as exc:
        raise UpdateError(f"Update-Prüfung fehlgeschlagen: {exc}") from exc
    if len(raw) > MAX_MANIFEST:
        raise UpdateError("Update-Manifest ist zu groß.")
    try:
        data = json.loads(raw.decode("utf-8"))
        version = str(data["version"])
        url = str(data["url"])
        sha = str(data["sha256"]).lower()
    except Exception as exc:
        raise UpdateError("Update-Manifest ist ungültig.") from exc
    _require_https(url)
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise UpdateError("Update-Manifest enthält keine gültige SHA-256-Prüfsumme.")
    if not is_newer(version, current_version):
        return None
    return {"version": version, "url": url, "sha256": sha, "notes": str(data.get("notes", ""))}


def _download(url, expected_sha, dest, progress=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    done = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0)
            if total > MAX_ZIP:
                raise UpdateError("Update-Datei ist zu groß.")
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                done += len(chunk)
                if done > MAX_ZIP:
                    raise UpdateError("Update-Datei ist zu groß.")
                digest.update(chunk)
                out.write(chunk)
                if progress and total:
                    progress(done / total)
    except UpdateError:
        raise
    except Exception as exc:
        raise UpdateError(f"Download fehlgeschlagen: {exc}") from exc
    if digest.hexdigest() != expected_sha:
        raise UpdateError("Prüfsumme stimmt nicht – Update wurde verworfen.")


def _safe_extract(zip_path, stage):
    """Entpackt ohne Pfad-Tricks (Zip-Slip) und ohne Symlinks. Gibt das App-Root zurück."""
    stage_real = os.path.realpath(stage)
    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if sum(m.file_size for m in members) > MAX_UNPACKED:
            raise UpdateError("Update-Archiv ist entpackt zu groß.")
        for m in members:
            if (m.external_attr >> 16) & 0o170000 == 0o120000:
                raise UpdateError("Update-Archiv enthält Symlinks.")
            target = os.path.realpath(os.path.join(stage, m.filename))
            if os.path.commonpath([stage_real, target]) != stage_real:
                raise UpdateError("Update-Archiv enthält ungültige Pfade.")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(m) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    if os.path.isfile(os.path.join(stage, "main.py")):
        return stage
    subdirs = [d for d in os.listdir(stage) if os.path.isdir(os.path.join(stage, d))]
    for d in subdirs:
        if os.path.isfile(os.path.join(stage, d, "main.py")):
            return os.path.join(stage, d)
    raise UpdateError("Update-Archiv enthält keine main.py.")


def _merge_config(new_path, current_path):
    try:
        with open(new_path, "r", encoding="utf-8") as f:
            new = json.load(f)
        with open(current_path, "r", encoding="utf-8") as f:
            cur = json.load(f)
    except Exception:
        return
    changed = False
    for key, value in new.items():
        if key not in cur:
            cur[key] = value
            changed = True
    if changed:
        tmp = current_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cur, f, indent=2, ensure_ascii=False)
        os.replace(tmp, current_path)


def _apply(src_root, app_dir):
    backup = os.path.join(app_dir, "_update_backup")
    shutil.rmtree(backup, ignore_errors=True)
    changed = []   # (relativer Pfad, hatte_vorher_eine_datei)
    try:
        for base, dirs, files in os.walk(src_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                src = os.path.join(base, name)
                rel = os.path.relpath(src, src_root)
                dst = os.path.join(app_dir, rel)
                if rel in PRESERVE:
                    if os.path.exists(dst):
                        _merge_config(src, dst)
                        continue
                existed = os.path.exists(dst)
                if existed:
                    os.makedirs(os.path.dirname(os.path.join(backup, rel)), exist_ok=True)
                    shutil.copy2(dst, os.path.join(backup, rel))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                tmp = dst + ".new"
                shutil.copy2(src, tmp)
                os.replace(tmp, dst)
                changed.append((rel, existed))
    except Exception as exc:
        for rel, existed in reversed(changed):
            dst = os.path.join(app_dir, rel)
            try:
                if existed:
                    shutil.copy2(os.path.join(backup, rel), dst)
                else:
                    os.remove(dst)
            except Exception:
                pass
        raise UpdateError(f"Update konnte nicht installiert werden (zurückgesetzt): {exc}") from exc


def install(info, app_dir, progress=None):
    """Lädt und installiert das Update. Wirft UpdateError bei Problemen."""
    work = tempfile.mkdtemp(prefix="adrolla_update_")
    try:
        zip_path = os.path.join(work, "update.zip")
        _download(info["url"], info["sha256"], zip_path, progress)
        stage = os.path.join(work, "stage")
        os.makedirs(stage)
        root = _safe_extract(zip_path, stage)
        _apply(root, app_dir)
    finally:
        shutil.rmtree(work, ignore_errors=True)
