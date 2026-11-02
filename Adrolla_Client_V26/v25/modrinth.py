"""Modrinth-Anbindung für den Adrolla Client.

Suche, Versionswahl, Pflicht-Abhängigkeiten, Download mit Hash-Prüfung und
ein kleines Manifest, damit installierte Mods erkannt und nicht doppelt
geladen werden. Reine Standardbibliothek, keine GUI-Abhängigkeiten.
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.modrinth.com/v2"
USER_AGENT = "AdrollaClient/19 (Minecraft launcher)"
MAX_DEPTH = 6


class ModrinthError(Exception):
    pass


def _request(url, timeout=20):
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                "Accept": "application/json"})


def _get_json(path, params=None, timeout=20):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(_request(url), timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ModrinthError(f"Modrinth antwortete mit HTTP {exc.code}.") from exc
    except Exception as exc:
        raise ModrinthError(f"Modrinth ist nicht erreichbar: {exc}") from exc


def loader_filter(loader):
    """Modrinth-Loader-Kennungen, die für den gewählten Loader passen."""
    key = (loader or "").lower()
    if key in ("", "vanilla"):
        return []
    if key == "quilt":  # Quilt lädt auch Fabric-Mods
        return ["quilt", "fabric"]
    return [key]


def search(query, project_type="mod", game_version=None, loader=None,
           offset=0, limit=20, index="relevance"):
    facets = [[f"project_type:{project_type}"]]
    if game_version:
        facets.append([f"versions:{game_version}"])
    loaders = loader_filter(loader) if project_type == "mod" else []
    if loaders:
        facets.append([f"categories:{name}" for name in loaders])
    params = {"query": query or "", "limit": str(limit), "offset": str(offset),
              "index": index, "facets": json.dumps(facets)}
    data = _get_json("/search", params)
    return data.get("hits", []), data.get("total_hits", 0)


def project_versions(project_id, game_version=None, loader=None, project_type="mod"):
    params = {}
    if game_version:
        params["game_versions"] = json.dumps([game_version])
    loaders = loader_filter(loader) if project_type == "mod" else []
    if loaders:
        params["loaders"] = json.dumps(loaders)
    return _get_json(f"/project/{project_id}/version", params)


def get_version(version_id):
    return _get_json(f"/version/{version_id}")


def get_project(project_id):
    return _get_json(f"/project/{project_id}")


def pick_version(versions):
    """Neueste Release-Version, sonst Beta, sonst Alpha (API liefert neueste zuerst)."""
    for kind in ("release", "beta", "alpha"):
        for version in versions:
            if version.get("version_type") == kind:
                return version
    return versions[0] if versions else None


def primary_file(version):
    files = version.get("files") or []
    return next((f for f in files if f.get("primary")), files[0] if files else None)


def resolve(project_id, game_version, loader, project_type="mod",
            installed_ids=(), version_id=None):
    """Plan: Hauptprojekt plus alle benötigten Abhängigkeiten.

    Rückgabe: (plan, warnings). Jeder Plan-Eintrag ist ein Dict mit
    project_id, title, version, file, required_by.
    """
    plan, warnings, seen = [], [], set(installed_ids)

    def add(pid, vid, parent, depth):
        if pid in seen and not vid:
            return
        if depth > MAX_DEPTH:
            warnings.append("Abhängigkeitskette zu tief, Rest wurde übersprungen.")
            return
        if vid:
            version = get_version(vid)
            pid = version.get("project_id", pid)
            if pid in seen:
                return
        else:
            versions = project_versions(pid, game_version, loader, project_type)
            version = pick_version(versions)
        title = pid
        project = {}
        try:
            project = get_project(pid)
            title = project.get("title", pid)
        except ModrinthError:
            pass
        if project.get("client_side") == "unsupported":
            raise ModrinthError(
                f"{title} wird laut Modrinth nicht auf dem Minecraft-Client unterstützt."
            )
        if not version:
            msg = (f"Für {title} gibt es keine Version für Minecraft {game_version}"
                   + (f" und {loader}." if loader and loader.lower() != "vanilla" else "."))
            if parent is None:
                raise ModrinthError(msg)
            warnings.append(msg)
            return
        file_info = primary_file(version)
        if not file_info:
            if parent is None:
                raise ModrinthError(f"{title} hat keine Download-Datei.")
            warnings.append(f"{title} hat keine Download-Datei.")
            return
        seen.add(pid)
        entry = {"project_id": pid, "title": title, "icon_url": project.get("icon_url", ""),
                 "version": version,
                 "file": file_info, "required_by": parent}
        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") == "required":
                if dep.get("project_id") or dep.get("version_id"):
                    add(dep.get("project_id"), dep.get("version_id"), title, depth + 1)
        plan.append(entry)

    add(project_id, version_id, None, 0)
    return plan, warnings


def safe_filename(name):
    name = os.path.basename(str(name).replace("\\", "/"))
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        raise ModrinthError("Ungültiger Dateiname von Modrinth.")
    return name


def _unique(directory, filename):
    stem, ext = os.path.splitext(filename)
    path = os.path.join(directory, filename)
    n = 2
    while os.path.exists(path):
        path = os.path.join(directory, f"{stem} ({n}){ext}")
        n += 1
    return path


def _hash_file(path, algorithm):
    digest = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(file_info, directory, progress=None, allowed_ext=(".jar", ".zip", ".mrpack")):
    """Lädt eine Modrinth-Datei, prüft SHA-512 (sonst SHA-1) und die Größe."""
    url = file_info.get("url", "")
    if not (url.startswith("https://") or url.startswith("http://127.0.0.1")):
        raise ModrinthError("Unsichere Download-Adresse wurde abgelehnt.")
    filename = safe_filename(file_info.get("filename") or urllib.parse.urlparse(url).path)
    if not filename.lower().endswith(allowed_ext):
        raise ModrinthError(f"Dateityp von {filename} wird nicht unterstützt.")
    os.makedirs(directory, exist_ok=True)
    final = os.path.join(directory, filename)
    part = final + ".part"
    try:
        with urllib.request.urlopen(_request(url), timeout=60) as response, open(part, "wb") as out:
            total = int(response.headers.get("Content-Length") or file_info.get("size") or 0)
            done = 0
            while True:
                chunk = response.read(1 << 16)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
        hashes = file_info.get("hashes") or {}
        for algorithm in ("sha512", "sha1"):
            expected = hashes.get(algorithm)
            if expected:
                if _hash_file(part, algorithm).lower() != expected.lower():
                    raise ModrinthError(f"Prüfsumme von {filename} stimmt nicht – Datei verworfen.")
                break
        size = file_info.get("size")
        if size and os.path.getsize(part) != int(size):
            raise ModrinthError(f"Größe von {filename} stimmt nicht – Datei verworfen.")
        os.replace(part, final)
        return final
    except ModrinthError:
        raise
    except Exception as exc:
        raise ModrinthError(f"Download von {filename} fehlgeschlagen: {exc}") from exc
    finally:
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass


class Manifest:
    """Merkt sich pro Profil, welche Modrinth-Projekte installiert wurden."""

    def __init__(self, path):
        self.path = path
        self.data = {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self.data = loaded
        except Exception:
            pass

    def installed_ids(self, folder):
        return {pid for pid, item in self.data.items()
                if os.path.isfile(os.path.join(folder, item.get("file", "")))}

    def add(self, project_id, title, filename, version_id, icon_url=""):
        item = {"title": title, "file": filename, "version_id": version_id}
        if icon_url:
            item["icon_url"] = icon_url
        self.data[project_id] = item

    def forget_file(self, filename):
        for pid in [p for p, i in self.data.items() if i.get("file") == filename]:
            del self.data[pid]

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)


def install_project(project_id, game_version, loader, target_dir, library_dir,
                    project_type="mod", progress=None, status=None):
    """Installiert ein Projekt samt Pflicht-Abhängigkeiten.

    Lädt in die Bibliothek (nach Version sortiert) und kopiert ins Zielverzeichnis
    des Profils. Rückgabe: (installierte Dateinamen, Warnungen).
    """
    import shutil
    manifest = Manifest(os.path.join(target_dir, ".adrolla-installed.json"))
    library_manifest = Manifest(os.path.join(library_dir, ".adrolla-library.json"))
    present = manifest.installed_ids(target_dir)
    if status:
        status("Passende Version und Abhängigkeiten werden gesucht …")
    plan, warnings = resolve(project_id, game_version, loader, project_type, present)
    if not plan:
        return [], ["Bereits installiert."]
    os.makedirs(target_dir, exist_ok=True)
    installed = []
    for index, entry in enumerate(plan, 1):
        label = entry["title"] + ("" if not entry["required_by"] else f" (für {entry['required_by']})")
        if status:
            status(f"[{index}/{len(plan)}] {label} wird geladen …")
        cached = download(entry["file"], library_dir, progress)
        filename = os.path.basename(cached)
        library_manifest.add(entry["project_id"], entry["title"], filename,
                             entry["version"].get("id", ""), entry.get("icon_url", ""))
        destination = os.path.join(target_dir, os.path.basename(cached))
        if os.path.exists(destination):
            same = _hash_file(destination, "sha1") == _hash_file(cached, "sha1")
            if not same:
                destination = _unique(target_dir, os.path.basename(cached))
        if not os.path.exists(destination):
            shutil.copy2(cached, destination)
        manifest.add(entry["project_id"], entry["title"], os.path.basename(destination),
                     entry["version"].get("id", ""), entry.get("icon_url", ""))
        installed.append(os.path.basename(destination))
    manifest.save()
    if library_manifest.data:
        library_manifest.save()
    return installed, warnings
