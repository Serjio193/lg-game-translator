import os
import threading
import unittest
from types import SimpleNamespace as S
from unittest.mock import Mock, patch
from PIL import Image
from gocr_worker.worker_full import FullGocrWorker


class FullSelectionTests(unittest.TestCase):
    def test_independent_thread_counts_reach_their_own_interpreters(self):
        detector=Mock(native=Mock())
        with patch.dict(os.environ,{"GOCR_RECOGNIZER":"native"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector",return_value=detector) as det, \
             patch("gocr_worker.native_recognizer.NativeRecognizer") as rec, \
             patch("gocr_worker.native_recognizer.NativeFull"):
            worker=FullGocrWorker("assets",2,detector_threads=4,recognizer_threads=1)
            det.assert_called_once_with("assets",threads=4)
            rec.assert_called_once_with("assets",1)
            self.assertEqual((worker.detector_threads,worker.recognizer_threads),(4,1))

    def test_invalid_thread_count_is_rejected_before_interpreter_creation(self):
        with patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector") as detector:
            for value in (0,5,-1):
                with self.assertRaises(ValueError):
                    FullGocrWorker("assets",2,recognizer_threads=value)
            detector.assert_not_called()

    def test_native_selected_and_no_python_recognizer_or_rectification_called(self):
        detector=Mock(native=Mock())
        rec=Mock(spec=["close","lib","context"])
        stats=S(detector=S(grouping=S(deduped_count=0,pair_tests=0,component_count=0),
            invoke_ms=1,total_ms=2,prepare_ms=0.1,decode_ms=0.1,postprocess_ms=0.2,
            raw_pieces=0,raw_groups=0),rectify_ms=0)
        full=Mock()
        full.run.return_value=([],stats)
        with patch.dict(os.environ,{"GOCR_RECOGNIZER":"native"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector",return_value=detector), \
             patch("gocr_worker.native_recognizer.NativeRecognizer",return_value=rec), \
             patch("gocr_worker.native_recognizer.NativeFull",return_value=full), \
             patch("gocr_worker.worker_full.GocrLineRecognizer") as reference, \
             patch("gocr_worker.worker_full.rectify_crop") as rectify:
            worker=FullGocrWorker("assets",2)
            result=worker.ocr(Image.new("RGB",(1280,720)))
            reference.assert_not_called(); rectify.assert_not_called()
            self.assertEqual(result["telemetry"]["ocr_execution"],"native")
            worker.close()
            full.close.assert_called_once(); rec.close.assert_called_once(); detector.close.assert_called_once()

    def test_unavailable_native_library_warns_and_preserves_reference(self):
        reference=Mock()
        with patch.dict(os.environ,{"GOCR_RECOGNIZER":"native"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector",return_value=Mock(native=Mock())), \
             patch("gocr_worker.native_recognizer.NativeRecognizer",side_effect=OSError("missing")), \
             patch("gocr_worker.worker_full.GocrLineRecognizer",return_value=reference):
            with self.assertWarns(RuntimeWarning):
                worker=FullGocrWorker("assets",2)
            self.assertIsNone(worker.native_full)
            self.assertIs(worker.recognizer,reference)

    def test_python_debug_does_not_load_native_recognizer(self):
        with patch.dict(os.environ,{"GOCR_RECOGNIZER":"python"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector",return_value=Mock(native=Mock())), \
             patch("gocr_worker.native_recognizer.NativeRecognizer") as native, \
             patch("gocr_worker.worker_full.GocrLineRecognizer"):
            self.assertIsNone(FullGocrWorker("assets",2).native_full)
            native.assert_not_called()

    def test_invalid_mode_is_configuration_error(self):
        with patch.dict(os.environ,{"GOCR_RECOGNIZER":"other"}), \
             patch("gocr_worker.worker_full.verify_bundle",return_value={}), \
             patch("gocr_worker.worker_full.create_detector"):
            with self.assertRaises(ValueError):
                FullGocrWorker("assets",2)

    def test_concurrent_requests_do_not_reuse_native_buffers_in_parallel(self):
        worker=FullGocrWorker.__new__(FullGocrWorker)
        worker.lock=threading.Lock()
        entered=threading.Event()
        release=threading.Event()
        calls=[]
        def operation(image):
            calls.append(image)
            entered.set()
            self.assertTrue(release.wait(2))
            return image
        worker._ocr=operation
        first=threading.Thread(target=worker.ocr,args=(1,))
        second=threading.Thread(target=worker.ocr,args=(2,))
        first.start(); self.assertTrue(entered.wait(2)); second.start()
        self.assertEqual(calls,[1])
        release.set(); first.join(); second.join()
        self.assertEqual(calls,[1,2])


if __name__=="__main__":
    unittest.main()
