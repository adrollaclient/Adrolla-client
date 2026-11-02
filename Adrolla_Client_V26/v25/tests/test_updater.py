import hashlib, io, json, os, sys, tempfile, unittest, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


class UpdaterTests(unittest.TestCase):
    def test_version_compare(self):
        self.assertTrue(updater.is_newer("26", "25"))
        self.assertTrue(updater.is_newer("25.1", "25"))
        self.assertFalse(updater.is_newer("25", "25.0"))
        self.assertFalse(updater.is_newer("24", "25"))

    def test_https_required(self):
        with self.assertRaises(updater.UpdateError):
            updater.check("http://example.com/update.json", "25")

    def test_zip_slip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            z = os.path.join(d, "u.zip")
            open(z, "wb").write(make_zip({"../evil.txt": b"x", "main.py": b""}))
            stage = os.path.join(d, "stage"); os.makedirs(stage)
            with self.assertRaises(updater.UpdateError):
                updater._safe_extract(z, stage)
            self.assertFalse(os.path.exists(os.path.join(d, "evil.txt")))

    def test_apply_keeps_config_and_adds_keys(self):
        with tempfile.TemporaryDirectory() as d:
            app = os.path.join(d, "app"); os.makedirs(app)
            open(os.path.join(app, "main.py"), "w").write("old")
            json.dump({"theme": "mine"}, open(os.path.join(app, "config.json"), "w"))
            z = os.path.join(d, "u.zip")
            open(z, "wb").write(make_zip({
                "v26/main.py": b"new",
                "v26/config.json": json.dumps({"theme": "default", "update_url": ""}).encode()}))
            stage = os.path.join(d, "stage"); os.makedirs(stage)
            root = updater._safe_extract(z, stage)
            updater._apply(root, app)
            self.assertEqual(open(os.path.join(app, "main.py")).read(), "new")
            cfg = json.load(open(os.path.join(app, "config.json")))
            self.assertEqual(cfg["theme"], "mine")
            self.assertIn("update_url", cfg)


if __name__ == "__main__":
    unittest.main()
