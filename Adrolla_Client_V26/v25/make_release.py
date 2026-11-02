"""Erzeugt ein Update-Paket und das passende update.json.

Aufruf:  python make_release.py https://dein-server/Adrolla_Client_V26.zip
Dann beide Dateien (ZIP + update.json) auf deinen Server / GitHub-Release
hochladen und die Adresse der update.json als "update_url" in config.json eintragen.
"""
import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {"__pycache__", "_update_backup", "_update_tmp", "dist", "build", ".git"}
SKIP_FILES = {"config.json", "accounts.dat"}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    url = sys.argv[1]
    version = None
    with open(os.path.join(ROOT, "main.py"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("APP_VERSION"):
                version = line.split("=", 1)[1].strip().strip('"\'')
                break
    if not version:
        print("APP_VERSION nicht gefunden.")
        return 1
    zip_name = f"Adrolla_Client_V{version}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for name in files:
                if name in SKIP_FILES or name.endswith((".zip", ".pyc")) or name == "update.json":
                    continue
                path = os.path.join(base, name)
                zf.write(path, os.path.relpath(path, ROOT))
    with open(zip_name, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    with open("update.json", "w", encoding="utf-8") as f:
        json.dump({"version": version, "url": url, "sha256": sha, "notes": ""}, f, indent=2)
    print(f"{zip_name} und update.json erstellt (SHA-256 {sha[:12]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
