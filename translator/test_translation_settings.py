import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from translation_settings import read_settings, save_settings, validate, HDMI_INPUTS


class SettingsTests(unittest.TestCase):
    def test_application_selection_and_old_client_preservation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,
                {"TRANSLATOR_SETTINGS": str(Path(directory)/"settings.json")}):
            self.assertEqual(read_settings()["applications"], [])
            value = {**read_settings(), "applications": ["youtube.leanback.v4", "youtube.leanback.v4"]}
            saved = save_settings(value)
            self.assertEqual(saved["applications"], ["youtube.leanback.v4"])
            old = {k: v for k, v in saved.items() if k != "applications"}
            self.assertEqual(save_settings(old)["applications"], saved["applications"])
            self.assertEqual(save_settings({**old, "applications": []})["applications"], [])
            for ids in ("app.test", ["../bad"], ["with spaces"], [HDMI_INPUTS[0]], [None]):
                with self.assertRaises(ValueError):
                    validate({**old, "applications": ids})

    def test_defaults_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"TRANSLATOR_SETTINGS": str(Path(directory) / "settings.json")}):
                defaults = read_settings()
                self.assertEqual(defaults["hdmi_inputs"], HDMI_INPUTS)
                selected = {**defaults, "hdmi_inputs": [HDMI_INPUTS[3]], "provider": "google"}
                save_settings(selected)
                self.assertEqual(read_settings(), selected)
                save_settings({**selected, "hdmi_inputs": []})
                self.assertEqual(read_settings()["hdmi_inputs"], [])

    def test_reject_unsafe_addresses_and_unknown_inputs(self):
        defaults = {"hdmi_inputs": HDMI_INPUTS, "provider": "madlad",
                    "translation_server": "http://192.168.1.11:8765"}
        for address in ["https://example.com", "http://user:pass@host", "http://host/path",
                        "http://host:99999", "http://host?key=value", "http://[::1]", "http://host\nX-Test:bad"]:
            with self.assertRaises(ValueError):
                validate({**defaults, "translation_server": address})
        with self.assertRaises(ValueError):
            validate({**defaults, "hdmi_inputs": ["com.webos.app.browser"]})
        with self.assertRaises(ValueError):
            validate({**defaults, "provider": "unknown"})

    def test_russian_idle_migration_and_validation(self):
        old = {"hdmi_inputs": HDMI_INPUTS, "provider": "madlad",
               "translation_server": "http://192.168.1.11:8765"}
        self.assertTrue(validate(old)["russian_idle"])
        self.assertEqual(validate(old)["language_check_seconds"], 60)
        for seconds in (60, 120, 300):
            self.assertEqual(validate({**old, "russian_idle": False,
                                      "language_check_seconds": seconds})["language_check_seconds"], seconds)
        for seconds in (0, 30, 600, True, "60"):
            with self.assertRaises(ValueError):
                validate({**old, "language_check_seconds": seconds})
        with self.assertRaises(ValueError):
            validate({**old, "russian_idle": "true"})


if __name__ == "__main__":
    unittest.main()
