import os
import unittest
from unittest.mock import Mock,patch
from gocr_worker.worker_full import FullGocrWorker
from gocr_worker.execution_profile import execution_profile,google_runner_contract
from gocr_worker.runner_config import decode_cached_runner


class GoogleRunnerTests(unittest.TestCase):
    def test_profile_forces_independent_four_two_even_with_legacy_threads(self):
        for legacy in (1,2,4):
            with patch.dict(os.environ,{"GOCR_PROFILE":"google_runner_experimental","GOCR_RECOGNIZER":"native"}), \
                 patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
                 patch("gocr_worker.worker_full.google_runner_contract",return_value={"interpreter_num_threads":4}), \
                 patch("gocr_worker.worker_full.create_detector",return_value=Mock(native=Mock())) as detector, \
                 patch("gocr_worker.native_recognizer.NativeRecognizer") as recognizer, \
                 patch("gocr_worker.native_recognizer.NativeFull"):
                worker=FullGocrWorker("assets",threads=legacy)
                self.assertEqual(execution_profile(),"google_runner_experimental")
                detector.assert_called_once_with("assets",threads=4)
                recognizer.assert_called_once_with("assets",2)
                self.assertEqual((worker.detector_threads,worker.recognizer_threads),(4,2))

    def test_conflicting_explicit_counts_fail_before_interpreter_creation(self):
        with patch.dict(os.environ,{"GOCR_PROFILE":"google_runner_experimental"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.google_runner_contract",return_value={"interpreter_num_threads":4}), \
             patch("gocr_worker.worker_full.create_detector") as detector:
            for kwargs in ({"detector_threads":2},{"recognizer_threads":4}):
                with self.assertRaises(ValueError):
                    FullGocrWorker("assets",**kwargs)
            detector.assert_not_called()

    def test_changed_original_contract_rejected(self):
        with patch("gocr_worker.assets.locate",return_value="config"), \
             patch("gocr_worker.runner_config.decode_detector_binarypb",return_value={"interpreter_num_threads":2}):
            with self.assertRaises(ValueError):
                google_runner_contract("assets")

    def test_schema_numbers_decode_without_assets(self):
        # Original runner field numbers: threads=3, multi=6, cache=16, delegate=17.
        data=bytes([24,4,48,1,128,1,5,136,1,1])
        result=decode_cached_runner(data)
        self.assertEqual(result["interpreter_num_threads"],4)
        self.assertEqual(result["cache_max_size"],5)
        self.assertTrue(result["use_xnnpack_delegate"])
        self.assertTrue(result["multiple_inputs"])


if __name__=="__main__":
    unittest.main()
