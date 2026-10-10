"""Persistent, exclusively owned RKNN contexts behind one frame job queue."""
from concurrent.futures import Future
import ctypes as C
from queue import Queue
import threading


def pinned_engine(root, library, mask):
    from ocr.engines import Engines
    from runtime import Runtime
    engine = Engines(root)
    runtime = Runtime(library)
    runtime.lib.npu_set_core.argtypes = [C.c_void_p, C.c_int]
    runtime.lib.npu_set_core.restype = C.c_int
    original = runtime.model

    def model(path):
        result = original(path)
        code = runtime.lib.npu_set_core(result.context, mask)
        if code:
            result.close()
            raise RuntimeError(f"RKNN core placement failed: mask={mask}, code={code}")
        return result

    runtime.model = model
    engine.runtime = runtime
    return engine


def close_engine(engine):
    for model in engine.npu.values():
        model.close()
    for model, _ in getattr(engine.local, "models", {}).values():
        model.close()


class RecognizerPool:
    def __init__(self, factory, masks=(1, 2, 4)):
        self.masks = tuple(masks)
        if not self.masks:
            raise ValueError("At least one worker required")
        self.queue = Queue(maxsize=576)  # Existing detector: <=24 regions x 24 lines.
        self.local = threading.local()
        self.lock = threading.Lock()
        self.closed = False
        self.counts = [0]*len(masks)
        self.threads, ready = [], []
        for slot, mask in enumerate(masks):
            initialized = Future()
            thread = threading.Thread(target=self._run, args=(factory, slot, mask, initialized),
                                      name=f"ppocr-npu-{slot}")
            self.threads.append(thread)
            ready.append(initialized)
            thread.start()
        try:
            engines = [future.result() for future in ready]
            self.reference = engines[0]
        except BaseException:
            self.close()
            raise

    def __getattr__(self, name):
        return getattr(self.reference, name)

    def _run(self, factory, slot, mask, ready):
        try:
            engine = factory(mask)
        except BaseException as error:
            ready.set_exception(error)
            return
        self.local.engine = engine
        ready.set_result(engine)
        try:
            while True:
                job = self.queue.get()
                try:
                    if job is None:
                        return
                    future, function, args = job
                    if future.set_running_or_notify_cancel():
                        value, failure = None, None
                        try:
                            value = function(*args)
                        except BaseException as error:
                            failure = error
                        finally:
                            with self.lock:
                                self.counts[slot] += 1
                        if failure is not None:
                            future.set_exception(failure)
                        else:
                            future.set_result(value)
                finally:
                    self.queue.task_done()
        finally:
            close_engine(engine)

    def submit(self, function, *args):
        with self.lock:
            if self.closed:
                raise RuntimeError("Recognizer queue closed")
            future = Future()
            self.queue.put_nowait((future, function, args))
            return future

    def recognize(self, *args):
        engine = getattr(self.local, "engine", None)
        if engine is None:
            raise RuntimeError("Recognition must run on its owning worker")
        return engine.recognize(*args)

    def worker_stats(self):
        with self.lock:
            return {"core_masks": list(self.masks), "completed_jobs": list(self.counts)}

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
        for thread in self.threads:
            if thread.is_alive():
                self.queue.put(None)
        for thread in self.threads:
            thread.join()
