"""Timing wrappers for the unchanged installed recognizer, test process only."""
from collections import defaultdict
import time


class StageProfiler:
    def __init__(self, pipeline):
        if pipeline.pool is not None:
            raise ValueError("Stage profiler requires the current sequential pipeline")
        self.values = defaultdict(float)
        self.counts = defaultdict(int)
        self.restore = []
        self.pipeline = pipeline
        pipeline.profiler = self
        import ocr.engines as engines_module
        import runtime
        for name, label in (("preprocess", "recognizer_prepare"),
                            ("decode", "ctc_decode"), ("preserve", "icon_preserve_inclusive")):
            self.wrap(engines_module, name, label)
        self.wrap(runtime.Model, "__call__", "npu_python_call_inclusive")
        self.wrap(runtime.Runtime, "model", "model_load")
        self.wrap(pipeline.engines.runtime.lib, "npu_run", "npu_bridge_run")
        self.wrap(pipeline.detector, "lines", "line_geometry")
        engines = pipeline.engines
        original = engines.recognize
        def recognize(mode, *args):
            start = time.perf_counter()
            try:
                return original(mode, *args)
            finally:
                if mode in (1, 2):
                    self.add("tesseract_icons_subset", (time.perf_counter()-start)*1000)
        engines.recognize = recognize
        self.restore.append((engines, "recognize", original))

    def add(self, name, milliseconds):
        self.values[name] += milliseconds
        self.counts[name] += 1

    def wrap(self, owner, name, label):
        original = getattr(owner, name)
        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                self.add(label, (time.perf_counter()-start)*1000)
        setattr(owner, name, wrapped)
        self.restore.append((owner, name, original))

    def begin(self):
        self.values.clear()
        self.counts.clear()

    def snapshot(self):
        values = dict(self.values)
        values["npu_binding_copy_checks"] = max(0, values.get("npu_python_call_inclusive", 0)
                                                - values.get("npu_bridge_run", 0))
        return {"totals_ms": values, "calls": dict(self.counts)}

    def close(self):
        self.pipeline.profiler = None
        for owner, name, original in reversed(self.restore):
            setattr(owner, name, original)
