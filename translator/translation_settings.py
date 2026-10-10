"""Persistent HDMI admission settings, independent from capture settings."""

import json
import os
import threading
from urllib.parse import urlsplit
from pathlib import Path

HDMI_INPUTS = [f"com.webos.app.hdmi{index}" for index in range(1, 5)]
_lock = threading.Lock()


def settings_path():
    return Path(os.environ.get("TRANSLATOR_SETTINGS",
        str(Path.home() / ".local/share/lg-game-translator/settings.json")))


def read_settings():
    with _lock:
        path = settings_path()
        if not path.exists():
            return {"hdmi_inputs": HDMI_INPUTS.copy(), "provider": "madlad",
                    "translation_server": "http://192.168.1.11:8765",
                    "russian_idle": True, "language_check_seconds": 60}
        return validate(json.loads(path.read_text(encoding="utf-8")))


def validate(value):
    required = {"hdmi_inputs", "provider", "translation_server"}
    if not isinstance(value, dict) or not required <= set(value) or set(value) - required - {
            "russian_idle", "language_check_seconds"}:
        raise ValueError("Expected HDMI inputs, provider and translation_server")
    idle = value.get("russian_idle", True)
    seconds = value.get("language_check_seconds", 60)
    if not isinstance(idle, bool) or type(seconds) is not int or seconds not in (60, 120, 300):
        raise ValueError("Russian idle must be boolean; language check must be 60, 120 or 300 seconds")
    inputs = value["hdmi_inputs"]
    if not isinstance(inputs, list) or any(item not in HDMI_INPUTS for item in inputs):
        raise ValueError("Only HDMI 1-4 are supported")
    if value["provider"] not in ("madlad", "google"):
        raise ValueError("Provider must be madlad or google")
    address = value["translation_server"]
    if not isinstance(address, str) or len(address) > 240:
        raise ValueError("Invalid server address")
    server = urlsplit(address)
    if (server.scheme != "http" or not server.hostname or server.username or server.password
            or server.query or server.fragment or server.path not in ("", "/")
            or not all(char.isascii() and (char.isalnum() or char in ".-") for char in server.hostname)
            or not 1 <= (server.port or 80) <= 65535):
        raise ValueError("Use an HTTP server address, for example http://192.168.1.11:8765")
    return {"hdmi_inputs": [item for item in HDMI_INPUTS if item in inputs],
            "provider": value["provider"],
            "translation_server": f"http://{server.hostname}:{server.port or 80}",
            "russian_idle": idle, "language_check_seconds": seconds}


def save_settings(value):
    settings = validate(value)
    with _lock:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings) + "\n", encoding="utf-8")
        temporary.replace(path)
    return settings
