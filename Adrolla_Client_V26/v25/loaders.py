"""Mod-Loader-Installation (Fabric, Quilt, Forge, NeoForge) über minecraft-launcher-lib."""

import inspect
import os
import shutil

LOADERS = ["Vanilla", "Fabric", "Quilt", "Forge", "NeoForge"]


class LoaderError(Exception):
    pass


def _installed_ids(lib, directory):
    try:
        return [item["id"] for item in lib.utils.get_installed_versions(directory)]
    except Exception:
        return []


def _guess_version_id(lib, directory, key, mc_version, before):
    ids = _installed_ids(lib, directory)
    fresh = [i for i in ids if i not in before and key in i.lower() and mc_version in i]
    candidates = fresh or [i for i in ids if key in i.lower() and mc_version in i]
    if not candidates:
        raise LoaderError(f"{key.capitalize()} wurde installiert, aber die Version wurde nicht gefunden.")
    return sorted(candidates)[-1]


def _java_for_installation(lib, mc_version, directory, callback=None):
    """Use Minecraft's bundled Java runtime when a loader installer needs Java."""
    runtime = getattr(lib, "runtime", None)
    if runtime is not None:
        try:
            info = runtime.get_version_runtime_information(mc_version, directory)
            component = info.get("name") if info else None
            if component:
                runtime.install_jvm_runtime(component, directory, callback=callback)
                executable = runtime.get_executable_path(component, directory)
                if executable and os.path.isfile(executable):
                    return executable
        except Exception:
            # Fall back to Java already installed on the system. If neither is
            # available, the loader's own error below will explain the failure.
            pass
    return shutil.which("java") or shutil.which("javaw")


def _install_with_java(installer, mc_version, directory, callback, java):
    """Pass Java when this launcher-lib version exposes the option."""
    kwargs = {"callback": callback}
    try:
        parameters = inspect.signature(installer).parameters.values()
        if any(parameter.name == "java" or parameter.kind == inspect.Parameter.VAR_KEYWORD
               for parameter in parameters):
            kwargs["java"] = java
    except (TypeError, ValueError):
        kwargs["java"] = java
    return installer(mc_version, directory, **kwargs)


def install_loader(lib, loader, mc_version, directory, callback=None):
    """Installiert Minecraft samt Loader und gibt die Start-Versionskennung zurück."""
    key = (loader or "vanilla").lower()
    lib.install.install_minecraft_version(mc_version, directory, callback=callback)
    if key == "vanilla":
        return mc_version
    java = _java_for_installation(lib, mc_version, directory, callback)
    before = set(_installed_ids(lib, directory))
    result = None
    try:
        mod_loader = getattr(lib, "mod_loader", None)
        if mod_loader is not None:
            handler = mod_loader.get_mod_loader(key)
            if not handler.is_minecraft_version_supported(mc_version):
                raise LoaderError(f"{loader} unterstützt Minecraft {mc_version} nicht.")
            result = _install_with_java(handler.install, mc_version, directory, callback, java)
        elif key == "fabric":
            result = _install_with_java(lib.fabric.install_fabric, mc_version, directory, callback, java)
        elif key == "quilt":
            result = _install_with_java(lib.quilt.install_quilt, mc_version, directory, callback, java)
        elif key == "forge":
            forge_version = lib.forge.find_forge_version(mc_version)
            if not forge_version:
                raise LoaderError(f"Für Minecraft {mc_version} gibt es kein Forge.")
            lib.forge.install_forge_version(forge_version, directory, callback=callback)
        else:
            raise LoaderError(f"{loader} wird von dieser Bibliotheksversion nicht unterstützt.")
    except LoaderError:
        raise
    except Exception as exc:
        if isinstance(exc, FileNotFoundError) or getattr(exc, "winerror", None) == 2:
            raise LoaderError(
                f"{loader} konnte nicht installiert werden, weil Java nicht gefunden wurde. "
                "Adrolla hat keine passende Minecraft-Java-Runtime gefunden. "
                "Prüfe die Internetverbindung und starte den Client erneut."
            ) from exc
        hint = ""
        if key in ("forge", "neoforge"):
            hint = " (Forge/NeoForge brauchen ein installiertes Java im PATH.)"
        raise LoaderError(f"{loader} konnte nicht installiert werden: {exc}{hint}") from exc
    if isinstance(result, str) and result:
        return result
    return _guess_version_id(lib, directory, key, mc_version, before)
