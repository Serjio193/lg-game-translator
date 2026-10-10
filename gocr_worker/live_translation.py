"""Bounded, latest-version translation queues independent of the frame RPC."""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from .source_admission import require_current
from .translation_client import TranslationClient

LOG = logging.getLogger("gocr-tv")


def client_for(session):
    return TranslationClient(f"http://{session[2]}:{session[3]}", session[1])


class LiveTranslations:
    def __init__(self, publisher, *, client_factory=client_for, guard=require_current):
        self.publisher, self.client_factory, self.guard = publisher, client_factory, guard
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.pools = {stage: ThreadPoolExecutor(max_workers=2, thread_name_prefix=stage)
                      for stage in ("preview", "final")}
        self.running, self.groups, self.entries = {}, {}, []
        self.session, self.closed = None, False

    def _current(self, session):
        try:
            self.guard(session)
            return True
        except (ValueError, OSError):
            return False

    def observe(self, result):
        """Only OCR observations advance stability; translations never do."""
        session = tuple(result.get("source_session", ()))
        with self.lock:
            if self.closed or not session or not self._current(session):
                return
            entries = self.publisher.observe(result)
            if entries is None:
                return
            self.session, self.entries = session, entries
            groups = {}
            for entry in entries:
                text_type = entry["line"].get("text_type", "dialogue")
                if text_type not in ("dialogue", "description", "heading", "menu"):
                    text_type = "dialogue"
                key = (session, entry["admission"]["text"], text_type)
                group = groups.get(key) or self.groups.get(key)
                if group is None:
                    group = {"key": key, "session": session, "text": key[1],
                             "metadata": {"text_type": text_type},
                             "client": self.client_factory(session), "preview_done": False,
                             "final_done": False, "preview": None, "final": None}
                if key not in groups:
                    group["entries"] = []
                group["entries"].append(entry)
                groups[key] = group
            # No historical pending queue: only <=20 groups of the latest frame.
            self.groups = groups
            self._emit()
            self._pump()

    def _emit(self):
        if self.closed or not self.session or not self._current(self.session):
            return
        responses = {}
        for group in self.groups.values():
            for entry in group["entries"]:
                response = group["final"] if entry["observations"] >= 3 else group["preview"]
                response = response or group["preview"]
                if response is not None:
                    responses[entry["slot"]] = response
        # The gate keeps the latest real OCR timestamp, not callback completion time.
        self.publisher.emit(self.entries, responses)

    @staticmethod
    def _priority(group):
        return max((entry["appearance"].get("lines", 1),
                    entry["appearance"]["box"]["width"] * entry["appearance"]["box"]["height"])
                   for entry in group["entries"])

    def _pump(self):
        if self.closed or not self.session or not self._current(self.session):
            return
        ordered = sorted(self.groups.values(), key=self._priority, reverse=True)
        for stage in ("preview", "final"):
            slots = 2 - sum(key[1] == stage for key in self.running)
            for group in ordered:
                job = (id(group), stage)
                if slots <= 0:
                    break
                if job in self.running or group[stage + "_done"]:
                    continue
                if stage == "final" and (not group["preview_done"] or
                        max(entry["observations"] for entry in group["entries"]) < 3):
                    continue
                # Install the marker before submit: a very fast future may finish now.
                self.running[job] = group
                slots -= 1
                future = self.pools[stage].submit(self._run, group, stage)
                future.add_done_callback(lambda value, g=group, s=stage, j=job:
                                         self._complete(g, s, j, value))

    def _run(self, group, stage):
        with self.lock:
            if self.closed or self.groups.get(group["key"]) is not group:
                return None
            self.guard(group["session"])
            text, metadata = group["text"], dict(group["metadata"])
            if stage == "final" and max(e["observations"] for e in group["entries"]) < 3:
                return None
        function = group["client"].preview if stage == "preview" else group["client"].translate
        result = function(text, **metadata)
        if result.get("provider") != group["session"][1] or not result.get("translation", "").strip():
            raise ValueError("Invalid translation identity")
        if stage == "preview":
            if result.get("stage") == "final" and result.get("cache_hit") is True:
                return {**result, "stage": "final"}
            if result.get("stage") != "preliminary" or result.get("engine") != "bergamot":
                raise ValueError("Invalid preview stage")
            return {**result, "confirmation_policy": "three-final-v1"}
        return {**result, "stage": "final", "engine": group["session"][1]}

    def _complete(self, group, stage, job, future):
        failed = False
        try:
            result = future.result()
        except Exception as error:
            LOG.warning("%s translation failed: %s", stage, type(error).__name__)
            result = None
            failed = True
        with self.changed:
            self.running.pop(job, None)
            if self.groups.get(group["key"]) is group:
                group[stage + "_done"] = failed or result is not None
                if result is not None:
                    if result["stage"] == "final":
                        group["final"], group["final_done"] = result, True
                    else:
                        group["preview"] = result
                try:
                    self._emit()
                except (OSError, ValueError) as error:
                    LOG.warning("OSD publication failed: %s", type(error).__name__)
            self._pump()
            self.changed.notify_all()

    def close(self):
        with self.lock:
            self.closed = True
            self.groups = {}
        for pool in self.pools.values():
            pool.shutdown(wait=True, cancel_futures=True)
