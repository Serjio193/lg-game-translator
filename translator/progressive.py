"""Race an uncached preview against a final cached translation."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import logging
import os

LOG = logging.getLogger("lg-game-translator")
_finals = ThreadPoolExecutor(max_workers=max(1, min(2, int(os.environ.get("TRANSLATOR_WORKERS", "1")))),
                            thread_name_prefix="final-translation")
_previews = ThreadPoolExecutor(max_workers=1, thread_name_prefix="preview-translation")


def results(text, lookup, final, preview):
    cached = lookup()
    if cached is not None:
        yield {**cached, "stage": "final", "engine": "madlad"}
        return
    future = _finals.submit(final)
    quick_future = _previews.submit(preview, text)
    wait((future, quick_future), return_when=FIRST_COMPLETED)
    if future.done():
        quick_future.cancel()
        yield {**future.result(), "stage": "final", "engine": "madlad"}
        return
    try:
        quick = quick_future.result()
        if not future.done():
            yield {**quick, "provider": "madlad", "engine": "bergamot",
                   "stage": "preliminary", "cache_hit": False}
    except Exception:
        LOG.exception("Bergamot preview failed; waiting for MADLAD")
    yield {**future.result(), "stage": "final", "engine": "madlad"}
