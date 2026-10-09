"""Test-process-only placement controller; no changes to system threads or DVFS."""
import os
from pathlib import Path
from .scheduler_observation import tasks


VARIANTS = ("baseline", "pair_0_1", "pair_0_2", "pair_0_3", "pair_1_2",
            "pair_1_3", "pair_2_3", "main_worker_0_1", "detector_spread",
            "nice_-5", "nice_5", "batch")


class Placement:
    def __init__(self, detector_tids, worker_tids):
        self.pid = os.getpid()
        self.detector_tids = set(detector_tids)
        self.worker_tids = set(worker_tids)
        self.original = tasks(self.pid)
        self.restore_errors = []

    def apply(self, variant):
        if variant not in VARIANTS:
            raise ValueError("unsupported scheduling variant")
        current = tasks(self.pid)
        for tid in current:
            if tid not in self.original:
                raise RuntimeError("new worker after discovery; placement experiment must rediscover it")
        for tid, original in self.original.items():
            if not Path(f"/proc/{self.pid}/task/{tid}").exists():
                continue
            affinity = original["affinity"]
            policy, nice = original["policy"], original["nice"]
            if variant.startswith("pair_"):
                affinity = [int(core) for core in variant[5:].split("_")]
            elif variant == "main_worker_0_1":
                if tid == self.pid:
                    affinity = [0]
                elif tid in self.worker_tids:
                    affinity = [1]
            elif variant == "detector_spread":
                ordered = [self.pid] + sorted(self.detector_tids)
                if tid in ordered:
                    if len(ordered) > 4:
                        raise RuntimeError("more than four detector participants; unique-core placement impossible")
                    affinity = [ordered.index(tid)]
            elif variant.startswith("nice_"):
                nice = int(variant[5:])
            elif variant == "batch":
                policy = os.SCHED_BATCH
            elif variant != "baseline":
                raise ValueError("unknown placement")
            if policy not in (os.SCHED_OTHER, os.SCHED_BATCH):
                raise RuntimeError("only non-realtime scheduler policies allowed")
            os.sched_setaffinity(tid, affinity)
            os.sched_setscheduler(tid, policy, os.sched_param(0))
            os.setpriority(os.PRIO_PROCESS, tid, nice)

    def restore(self):
        try:
            self.apply("baseline")
        except (OSError, RuntimeError) as exc:
            self.restore_errors.append(str(exc))
        restored = tasks(self.pid)
        for tid, row in restored.items():
            if tid in self.original:
                for key in ("affinity", "policy", "nice"):
                    if row[key] != self.original[tid][key]:
                        self.restore_errors.append(f"TID {tid}: {key} not restored")
        return restored
