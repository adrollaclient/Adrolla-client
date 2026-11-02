import hashlib
import json
import os
import sys
import tempfile
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import loaders  # noqa: E402
import modrinth  # noqa: E402

JAR_A = b"mod-a-bytes" * 50
JAR_B = b"dependency-bytes" * 40
JAR_C = b"other"


def sha512(b):
    return hashlib.sha512(b).hexdigest()


class Handler(BaseHTTPRequestHandler):
    base = ""

    def log_message(self, *a):
        pass

    def reply(self, obj, raw=False):
        body = obj if raw else json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        base = Handler.base
        files = {
            "A": {"url": f"{base}/cdn/a.jar", "filename": "../evil/a-1.0.jar", "primary": True,
                  "hashes": {"sha512": sha512(JAR_A)}, "size": len(JAR_A)},
            "B": {"url": f"{base}/cdn/b.jar", "filename": "b-2.0.jar", "primary": True,
                  "hashes": {"sha512": sha512(JAR_B)}, "size": len(JAR_B)},
            "C": {"url": f"{base}/cdn/c.jar", "filename": "c.jar", "primary": True,
                  "hashes": {"sha512": "0" * 128}, "size": len(JAR_C)},
        }
        if p == "/v2/project/projA/version":
            self.reply([
                {"id": "va-beta", "project_id": "projA", "version_type": "beta", "files": [files["A"]],
                 "dependencies": []},
                {"id": "va", "project_id": "projA", "version_type": "release", "files": [files["A"]],
                 "dependencies": [{"project_id": "projB", "dependency_type": "required"},
                                  {"project_id": "projOpt", "dependency_type": "optional"}]}])
        elif p == "/v2/project/projB/version":
            self.reply([{"id": "vb", "project_id": "projB", "version_type": "release",
                         "files": [files["B"]], "dependencies": [
                             {"project_id": "projA", "dependency_type": "required"}]}])
        elif p == "/v2/project/projC/version":
            self.reply([{"id": "vc", "project_id": "projC", "version_type": "release",
                         "files": [files["C"]], "dependencies": []}])
        elif p == "/v2/project/projNone/version":
            self.reply([])
        elif p.startswith("/v2/project/"):
            pid = p.rsplit("/", 1)[1]
            self.reply({"title": "Title " + pid})
        elif p == "/v2/search":
            self.reply({"hits": [{"title": "x"}], "total_hits": 1, "_q": self.path})
        elif p == "/cdn/a.jar":
            self.reply(JAR_A, raw=True)
        elif p == "/cdn/b.jar":
            self.reply(JAR_B, raw=True)
        elif p == "/cdn/c.jar":
            self.reply(JAR_C, raw=True)
        else:
            self.send_response(404)
            self.end_headers()


class ModrinthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        Handler.base = f"http://127.0.0.1:{cls.server.server_port}"
        modrinth.API = Handler.base + "/v2"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_loader_filter(self):
        self.assertEqual(modrinth.loader_filter("Quilt"), ["quilt", "fabric"])
        self.assertEqual(modrinth.loader_filter("Vanilla"), [])
        self.assertEqual(modrinth.loader_filter("NeoForge"), ["neoforge"])

    def test_pick_prefers_release(self):
        vs = [{"version_type": "beta", "id": 1}, {"version_type": "release", "id": 2}]
        self.assertEqual(modrinth.pick_version(vs)["id"], 2)

    def test_resolve_handles_cycle_and_skips_optional(self):
        plan, warnings = modrinth.resolve("projA", "1.21", "Fabric")
        self.assertEqual([e["project_id"] for e in plan], ["projB", "projA"])
        self.assertEqual(plan[0]["required_by"], "Title projA")
        self.assertEqual(warnings, [])

    def test_resolve_missing_main_raises(self):
        with self.assertRaises(modrinth.ModrinthError):
            modrinth.resolve("projNone", "1.21", "Fabric")

    def test_install_with_dependency_and_traversal_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            mods, lib = os.path.join(tmp, "mods"), os.path.join(tmp, "lib")
            done, warn = modrinth.install_project("projA", "1.21", "Fabric", mods, lib)
            self.assertEqual(sorted(done), ["a-1.0.jar", "b-2.0.jar"])
            self.assertEqual(sorted(n for n in os.listdir(lib) if not n.startswith(".")), ["a-1.0.jar", "b-2.0.jar"])
            self.assertTrue(os.path.isfile(os.path.join(mods, ".adrolla-installed.json")))
            self.assertFalse(os.path.exists(os.path.join(tmp, "evil")))
            again, warn2 = modrinth.install_project("projA", "1.21", "Fabric", mods, lib)
            self.assertEqual(again, [])

    def test_bad_hash_is_rejected_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(modrinth.ModrinthError) as ctx:
                modrinth.install_project("projC", "1.21", "Fabric", os.path.join(tmp, "m"),
                                         os.path.join(tmp, "l"))
            self.assertIn("Prüfsumme", str(ctx.exception))
            self.assertEqual([n for n in os.listdir(os.path.join(tmp, "l")) if not n.startswith(".")], [])

    def test_rejects_unsafe_url_and_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(modrinth.ModrinthError):
                modrinth.download({"url": "http://evil.example/a.jar", "filename": "a.jar"}, tmp)
            with self.assertRaises(modrinth.ModrinthError):
                modrinth.download({"url": "https://x/a.exe", "filename": "a.exe"}, tmp)

    def test_search_builds_loader_facets(self):
        hits, total = modrinth.search("sodium", "mod", "1.21", "Quilt")
        self.assertEqual(total, 1)


class FakeLib:
    """Minimale Attrappe von minecraft_launcher_lib (v8-Stil mit mod_loader)."""

    def __init__(self, returns_id=True, supported=True):
        self.installed = [{"id": "1.21"}]
        outer = self

        class Handler_:
            def is_minecraft_version_supported(self, v):
                return supported

            def install(self, mc, d, callback=None):
                outer.installed.append({"id": f"fabric-loader-0.16-{mc}"})
                return f"fabric-loader-0.16-{mc}" if returns_id else None

        self.install = types.SimpleNamespace(install_minecraft_version=lambda *a, **k: None)
        self.utils = types.SimpleNamespace(get_installed_versions=lambda d: list(self.installed))
        self.mod_loader = types.SimpleNamespace(get_mod_loader=lambda key: Handler_())


class LoaderTests(unittest.TestCase):
    def test_vanilla(self):
        self.assertEqual(loaders.install_loader(FakeLib(), "Vanilla", "1.21", "/x"), "1.21")

    def test_returned_id(self):
        self.assertEqual(loaders.install_loader(FakeLib(), "Fabric", "1.21", "/x"),
                         "fabric-loader-0.16-1.21")

    def test_id_guessed_when_not_returned(self):
        self.assertEqual(loaders.install_loader(FakeLib(returns_id=False), "Fabric", "1.21", "/x"),
                         "fabric-loader-0.16-1.21")

    def test_unsupported_version(self):
        with self.assertRaises(loaders.LoaderError):
            loaders.install_loader(FakeLib(supported=False), "Fabric", "1.21", "/x")


if __name__ == "__main__":
    unittest.main()
