"""Protected Google provisioning/status control, separate from public settings."""
import hmac
import os
import threading
from pathlib import Path
from google_budget import GoogleBudget
from google_vault import GoogleVault
from translation_settings import read_settings, save_settings

_lock = threading.Lock()
_state = None


def state():
    global _state
    with _lock:
        if _state is None:
            directory = Path(os.environ.get("TRANSLATOR_PRIVATE_DIR",
                str(Path.home() / ".local/share/lg-game-translator/private")))
            vault = GoogleVault(directory)
            _state = (vault, GoogleBudget(directory / "google-usage.sqlite3"))
        return _state


def authorized(headers):
    supplied = headers.get("X-OSD-Control-Key", "")
    return isinstance(supplied, str) and hmac.compare_digest(supplied, state()[0].control)


def status():
    vault, budget = state()
    return {"provider": read_settings()["provider"], "key_configured": vault.configured(),
            "public_key": vault.public_key(), "budget": budget.status()}


def update(value):
    if not isinstance(value, dict) or set(value) - {"provider", "encrypted_key"}:
        raise ValueError("Expected provider and encrypted_key only")
    provider = value.get("provider")
    if provider is not None and provider not in ("madlad", "google"):
        raise ValueError("Invalid translator")
    vault, _ = state()
    if "encrypted_key" in value:
        vault.import_encrypted(value["encrypted_key"])
    if provider is not None:
        if provider == "google" and not vault.configured():
            raise ValueError("Save the Google API key first")
        save_settings({**read_settings(), "provider": provider})
    return status()
