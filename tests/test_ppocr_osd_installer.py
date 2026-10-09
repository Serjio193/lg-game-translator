import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1]/"scripts/install-ppocr-osd-feed.py"
spec = importlib.util.spec_from_file_location("osd_installer", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallerTests(unittest.TestCase):
    def test_generated_and_readable_watchers_keep_backup_and_are_idempotent(self):
        for quote in ("'", '"'):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/"watcher.js"
                source = ("function readResponses(gate) { return " + quote
                          + "/tmp/piccap-translation-slot-" + quote + "; }\nvar gate="
                          + quote + "/tmp/piccap-translation-admission.json" + quote + ";")
                path.write_text(source)
                module.install(path)
                installed = path.read_text()
                self.assertIn("ppocr-full-osd-admission.json", installed)
                self.assertIn("ppocr-full-osd-slot-", installed)
                self.assertEqual(path.with_name("watcher.js.before-ppocr-full").read_text(), source)
                module.install(path)
                self.assertEqual(path.read_text(), installed)

    def test_unrelated_source_is_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"watcher.js"
            path.write_text("other")
            with self.assertRaises(ValueError):
                module.install(path)
            self.assertEqual(path.read_text(), "other")
