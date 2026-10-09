"""Authenticate the new LAN endpoints; loopback-only tools remain usable."""
import hmac
import ipaddress
from pathlib import Path


def read_token(path):
    if path is None:
        return None
    token = Path(path).read_text().strip()
    if len(token) < 32 or not token.isascii():
        raise ValueError("GOCR transport token must have at least 32 ASCII characters")
    return token


def require_private_bind(bind, token):
    if not ipaddress.ip_address(bind).is_loopback and not token:
        raise ValueError("a token file is required for a LAN GOCR server")


def authorized(headers, token):
    if token is None:
        return True
    return hmac.compare_digest(headers.get("Authorization", ""), "Bearer " + token)
