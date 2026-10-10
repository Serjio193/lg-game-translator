"""API credential at rest: AES-256-GCM, with a local owner-only master key."""
import base64
import json
import os
import secrets
import threading
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CONTEXT = b"lg-game-translator.google-key.v1"


class GoogleVault:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            self.directory.chmod(0o700)
        self.lock = threading.Lock()
        self.master = self.create_secret("master.key", lambda: secrets.token_bytes(32))
        private = self.create_secret("transport.pem", lambda: rsa.generate_private_key(
            public_exponent=65537, key_size=2048).private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
        self.private = serialization.load_pem_private_key(private, password=None)
        self.control = self.create_secret("control.key", lambda: secrets.token_hex(32).encode()).decode()

    def create_secret(self, name, factory):
        path = self.directory / name
        if not path.exists():
            value = factory()
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(value)
                    stream.flush()
                    os.fsync(stream.fileno())
        if os.name != "nt":
            path.chmod(0o600)
        return path.read_bytes()

    def public_key(self):
        return self.private.public_key().public_bytes(serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def configured(self):
        return (self.directory / "google-key.enc").exists()

    def get(self):
        with self.lock:
            if not self.configured():
                raise RuntimeError("Google API key is not configured")
            value = json.loads((self.directory / "google-key.enc").read_text())
            return AESGCM(self.master).decrypt(base64.b64decode(value["nonce"]),
                base64.b64decode(value["ciphertext"]), CONTEXT).decode()

    def import_encrypted(self, envelope):
        try:
            cipher = base64.b64decode(envelope, validate=True)
            if len(cipher) != 256:
                raise ValueError()
            key = self.private.decrypt(cipher, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(), label=None)).decode()
            if not 20 <= len(key) <= 200 or not all(c.isascii() and (c.isalnum() or c in "_-") for c in key):
                raise ValueError()
        except Exception:
            raise ValueError("Invalid encrypted Google credential") from None
        self.store(key)

    def store(self, key):
        with self.lock:
            nonce = secrets.token_bytes(12)
            value = {"version": 1, "nonce": base64.b64encode(nonce).decode(),
                "ciphertext": base64.b64encode(AESGCM(self.master).encrypt(nonce,
                    key.encode(), CONTEXT)).decode()}
            path = self.directory / "google-key.enc"
            temporary = self.directory / (".key-" + secrets.token_hex(8))
            try:
                descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w") as stream:
                    json.dump(value, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
