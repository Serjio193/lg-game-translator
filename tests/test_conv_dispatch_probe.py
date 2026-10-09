import copy
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/probe-gocr-conv-dispatch.py"
spec = importlib.util.spec_from_file_location("conv_dispatch_probe", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ConvDispatchGateTest(unittest.TestCase):
    def report(self):
        sample = {"identity": [{"text": "Hello", "quad": [1, 2], "crop_sha": "a"}],
                  "tensors": {"inputs": ["a"] * 4, "outputs": ["b"] * 11}}
        return {"runs": [{"frame": "a.ppm", "samples": [sample],
                          "diagnostics": {"components": [[0, 1]]}}]}

    def test_every_output_must_match(self):
        left = self.report()
        right = copy.deepcopy(left)
        right["runs"][0]["samples"][0]["tensors"]["outputs"][10] = "changed"
        self.assertFalse(probe.compare(left, right)[0]["all_4_inputs_11_outputs_exact"])

    def test_no_weaker_geometry_or_text_gate(self):
        left = self.report()
        for field, value in (("text", "Hallo"), ("quad", [1, 3]), ("crop_sha", "b")):
            right = copy.deepcopy(left)
            right["runs"][0]["samples"][0]["identity"][0][field] = value
            self.assertFalse(probe.compare(left, right)[0]["quads_crops_windows_utf8_exact"])

    def test_membership_and_corpus_identity(self):
        left = self.report()
        right = copy.deepcopy(left)
        right["runs"][0]["diagnostics"]["components"] = [[0], [1]]
        right["runs"][0]["frame"] = "b.ppm"
        gate = probe.compare(left, right)[0]
        self.assertFalse(gate["proposals_dedupe_components_exact"])
        self.assertFalse(gate["same_frame"])

    def test_empty_corpus_cannot_prove_parity(self):
        with self.assertRaises(ValueError):
            probe.compare({"runs": []}, {"runs": []})
