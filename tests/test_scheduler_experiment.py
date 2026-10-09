"""Controller safety and counter regression tests without mutating host scheduling."""
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import patch
from gocr_worker.scheduler_experiment import Placement
from gocr_worker.scheduler_observation import delta, keyed_fields


module_path = Path(__file__).resolve().parents[1] / "scripts/benchmark-gocr-strict-scheduling.py"
spec = importlib.util.spec_from_file_location("strict_scheduling", module_path)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.rows = {100: {"affinity": [0, 1, 2, 3], "policy": 0, "nice": 0},
                     101: {"affinity": [0, 1, 2, 3], "policy": 0, "nice": 0}}

    def controller(self):
        with patch("gocr_worker.scheduler_experiment.tasks", return_value=self.rows), \
             patch("gocr_worker.scheduler_experiment.os.getpid", return_value=100):
            return Placement({101}, {101})

    def test_only_discovered_current_process_tids_are_modified(self):
        obj = self.controller()
        with patch("gocr_worker.scheduler_experiment.tasks", return_value=self.rows), \
             patch("gocr_worker.scheduler_experiment.Path.exists", return_value=True), \
             patch("gocr_worker.scheduler_experiment.os.sched_setaffinity", create=True) as affinity, \
             patch("gocr_worker.scheduler_experiment.os.sched_setscheduler", create=True), \
             patch("gocr_worker.scheduler_experiment.os.setpriority", create=True):
            with patch("gocr_worker.scheduler_experiment.os.SCHED_OTHER", 0, create=True), \
                 patch("gocr_worker.scheduler_experiment.os.SCHED_BATCH", 3, create=True), \
                 patch("gocr_worker.scheduler_experiment.os.PRIO_PROCESS", 0, create=True), \
                 patch("gocr_worker.scheduler_experiment.os.sched_param", create=True):
                obj.apply("main_worker_0_1")
        self.assertEqual(affinity.call_args_list[0].args, (100, [0]))
        self.assertEqual(affinity.call_args_list[1].args, (101, [1]))

    def test_new_thread_rejected_before_any_mutation(self):
        obj = self.controller()
        with patch("gocr_worker.scheduler_experiment.tasks", return_value={**self.rows, 102: {}}), \
             patch("gocr_worker.scheduler_experiment.os.sched_setaffinity", create=True) as affinity:
            with self.assertRaisesRegex(RuntimeError, "new worker"):
                obj.apply("pair_0_1")
            affinity.assert_not_called()

    def test_unapproved_priority_rejected_before_mutation(self):
        obj = self.controller()
        with patch("gocr_worker.scheduler_experiment.os.sched_setaffinity", create=True) as affinity:
            with self.assertRaisesRegex(ValueError, "unsupported"):
                obj.apply("nice_-20")
            affinity.assert_not_called()

    def test_restore_failure_is_reported(self):
        obj = self.controller()
        with patch.object(obj, "apply", side_effect=PermissionError("denied")), \
             patch("gocr_worker.scheduler_experiment.tasks", return_value=self.rows):
            obj.restore()
        self.assertEqual(obj.restore_errors, ["denied"])

    def test_gate_rejects_one_mismatch_or_incomplete_corpus(self):
        report = {"frames": [{"parity": True}], "restore_errors": [], "persistent_tid_set": True}
        self.assertTrue(benchmark.accepted(report, 1))
        self.assertFalse(benchmark.accepted(report, 2))
        report["frames"][0]["parity"] = False
        self.assertFalse(benchmark.accepted(report, 1))

    def test_gate_rejects_failed_restore_or_new_workers(self):
        report = {"frames": [{"parity": True}], "restore_errors": ["denied"], "persistent_tid_set": True}
        self.assertFalse(benchmark.accepted(report, 1))
        report.update(restore_errors=[], persistent_tid_set=False)
        self.assertFalse(benchmark.accepted(report, 1))

    def test_sched_padded_counter_names_are_preserved(self):
        self.assertEqual(keyed_fields("se.nr_migrations       :  234\npolicy : 0"),
                         {"se.nr_migrations": "234", "policy": "0"})

    def test_counter_delta_retains_unavailable_values(self):
        keys = ("cpu_ticks", "runtime_ns", "runqueue_ns", "timeslices", "migrations", "voluntary", "involuntary")
        before = {1: dict.fromkeys(keys, 10)}
        after = {1: dict.fromkeys(keys, 15)}
        before[1]["runqueue_ns"] = None
        observed = delta(before, after)[1]
        self.assertIsNone(observed["runqueue_ns"])
        self.assertEqual(observed["migrations"], 5)


if __name__ == "__main__":
    unittest.main()
