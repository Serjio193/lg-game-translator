import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/benchmark-gocr-strict-runtimes.py"
spec = importlib.util.spec_from_file_location("strict_runtime_benchmark", path)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class StrictRuntimeGateTest(unittest.TestCase):
    def test_tensor_difference_does_not_imply_component_difference(self):
        left = {"tensors": {"output": ["a"]}, "components": [], "decoded_proposals": []}
        right = {"tensors": {"output": ["b"]}, "components": [], "decoded_proposals": []}
        self.assertNotEqual(left["tensors"], right["tensors"])
        self.assertEqual(benchmark.diagnostic_identity(left), benchmark.diagnostic_identity(right))

    def test_component_membership_remains_strict(self):
        left = {"components": [[0, 1], [2]]}
        right = {"components": [[0], [1, 2]]}
        self.assertNotEqual(benchmark.diagnostic_identity(left), benchmark.diagnostic_identity(right))

    def test_semantic_line_fields_remain_strict(self):
        left = {"lines": [{"text": "Hello", "recognizer_confidence": 0.9, "timings_ms": 1}]}
        timed = {"lines": [{"text": "Hello", "recognizer_confidence": 0.9, "timings_ms": 2}]}
        changed = {"lines": [{"text": "Hello", "recognizer_confidence": 0.8, "timings_ms": 1}]}
        self.assertEqual(benchmark.identity(left), benchmark.identity(timed))
        self.assertNotEqual(benchmark.identity(left), benchmark.identity(changed))
