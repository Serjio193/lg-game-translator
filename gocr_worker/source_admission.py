"""Read the existing TV controller admission; source changes invalidate late work."""
from pathlib import Path
import re
import time

CONTROL = Path("/tmp/game-translator-control.state")


def source_session(path=CONTROL, now_ms=None):
    try:
        fields = Path(path).read_text().split()
        if len(fields) not in (8, 9) or fields[1] != "1":
            return None
        timestamp = int(fields[0])
        now = int(time.time()*1000) if now_ms is None else now_ms
        if timestamp > now+1000 or now-timestamp > 6000:
            return None
        if fields[2] not in ("madlad", "google"):
            return None
        if not re.fullmatch(r"[A-Za-z0-9.-]{1,240}", fields[3]):
            return None
        if not fields[4].isdigit() or not 1 <= int(fields[4]) <= 65535:
            return None
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", fields[7]) or fields[7] == "none":
            return None
        if len(fields) == 9 and not re.fullmatch(r"[0-9]{1,20}", fields[8]):
            return None
        session = (fields[7], fields[2], fields[3], fields[4])
        return session + (fields[8],) if len(fields) == 9 else session
    except (OSError, ValueError):
        return None


def require_current(session, path=CONTROL, now_ms=None):
    if session is None or source_session(path, now_ms) != session:
        raise ValueError("Selected translation source changed or was disabled")
