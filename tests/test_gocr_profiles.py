import os
import unittest
from unittest.mock import Mock, patch
from gocr_worker.execution_profile import execution_profile
from gocr_worker.detector_backend import create_detector
from gocr_worker.profile_comparison import compare_lines, quad_iou, maximum_assignment, character_distance


def line(text,x=0,y=0):
    points=[(x,y),(x+10,y),(x+10,y+5),(x,y+5)]
    return {"text":text,"source_quad":{f"p{i}":{"x":px,"y":py} for i,(px,py) in enumerate(points)}}


class ProfileTests(unittest.TestCase):
    def test_default_strict_and_explicit_selection(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(execution_profile(),"strict")
        for profile in ("strict","fast_xnnpack"):
            with patch.dict(os.environ,{"GOCR_PROFILE":profile}):
                self.assertEqual(execution_profile(),profile)
        with patch.dict(os.environ,{"GOCR_PROFILE":"typo"}):
            with self.assertRaises(ValueError):
                execution_profile()

    def test_fast_never_silently_falls_back(self):
        with patch.dict(os.environ,{"GOCR_PROFILE":"fast_xnnpack","GOCR_DETECTOR":"native"}), \
             patch("gocr_worker.native_detector.NativeDetector",side_effect=OSError("missing")), \
             patch("gocr_worker.detector_runtime.GoogleConfiguredGroupRpnDetector") as reference:
            with self.assertRaises(RuntimeError):
                create_detector("assets")
            reference.assert_not_called()
        with patch.dict(os.environ,{"GOCR_PROFILE":"fast_xnnpack","GOCR_DETECTOR":"python"}):
            with self.assertRaises(ValueError):
                create_detector("assets")

    def test_delegate_flag_and_legacy_env_cannot_change_strict(self):
        from gocr_worker.native_detector import Config, NativeDetector
        for profile,expected in (("strict",0),("fast_xnnpack",1)):
            library=Mock()
            library.gocr_detector_abi.return_value=1
            library.gocr_detector_create.return_value=123
            with patch.dict(os.environ,{"GOCR_PROFILE":profile,"GOCR_DETECTOR_XNNPACK":"1"}), \
                 patch("gocr_worker.native_detector.C.CDLL",return_value=library), \
                 patch("gocr_worker.native_detector.config_from_assets",return_value=Config()), \
                 patch("gocr_worker.native_detector.locate",return_value="model.tflite"):
                detector=NativeDetector("assets")
                self.assertEqual(library.gocr_detector_create.call_args.args[3],expected)
                self.assertEqual(detector.xnnpack,bool(expected))
                detector.close()

    def test_geometry_matching_ignores_order_and_accounts_for_missing_extra(self):
        result=compare_lines([line("a"),line("b",y=20),line("missing",y=40)],
                             [line("changed",y=20),line("a"),line("extra",y=60)])
        self.assertEqual(result["matched"],2)
        self.assertEqual(result["exact_text_matches"],1)
        self.assertEqual(result["missing_strict_indices"],[2])
        self.assertEqual(result["extra_fast_indices"],[2])
        self.assertGreater(result["character_distance"],0)

    def test_fast_recognizer_failure_closes_detector_without_reference_fallback(self):
        from gocr_worker.worker_full import FullGocrWorker
        detector=Mock(native=Mock())
        with patch.dict(os.environ,{"GOCR_PROFILE":"fast_xnnpack","GOCR_RECOGNIZER":"native"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector",return_value=detector), \
             patch("gocr_worker.native_recognizer.NativeRecognizer",side_effect=OSError("missing")), \
             patch("gocr_worker.worker_full.GocrLineRecognizer") as reference:
            with self.assertRaises(RuntimeError):
                FullGocrWorker("assets")
            detector.close.assert_called_once()
            reference.assert_not_called()

    def test_fast_rejects_generic_images_before_reference_execution(self):
        from PIL import Image
        from gocr_worker.worker_full import FullGocrWorker
        worker=FullGocrWorker.__new__(FullGocrWorker)
        worker.profile="fast_xnnpack"
        for image in (Image.new("L",(1280,720)),Image.new("RGB",(640,360))):
            with self.assertRaises(ValueError):
                worker._ocr(image)

    def test_global_assignment_beats_greedy(self):
        self.assertEqual(set(maximum_assignment([[0.9,0.8],[0.85,0.1]])),{(0,1),(1,0)})
        self.assertEqual(compare_lines([],[]) ["matched"],0)
        self.assertEqual(compare_lines([line("a")],[]) ["missing_strict_indices"],[0])

    def test_rotated_winding_and_unicode(self):
        a=[(0,2),(2,0),(4,2),(2,4)]
        self.assertAlmostEqual(quad_iou(a,list(reversed(a))),1)
        self.assertEqual(quad_iou(a,[(10,0),(11,0),(11,1),(10,1)]),0)
        self.assertEqual(character_distance("あ你好!","あ您好?"),2)


if __name__=="__main__":
    unittest.main()
