import os
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from PIL import Image

from gocr_worker.detector_backend import create_detector


class BackendTests(unittest.TestCase):
    def test_native_selected_without_constructing_python_interpreter(self):
        with patch.dict(os.environ,{"GOCR_DETECTOR":"native"}), \
             patch("gocr_worker.native_detector.NativeDetector",return_value="native") as native, \
             patch("gocr_worker.detector_runtime.GoogleConfiguredGroupRpnDetector") as reference:
            self.assertEqual(create_detector("assets",2).native,"native")
            native.assert_called_once_with("assets",2)
            reference.assert_not_called()

    def test_library_unavailable_uses_reference_with_warning(self):
        with patch.dict(os.environ,{"GOCR_DETECTOR":"native"}), \
             patch("gocr_worker.native_detector.NativeDetector",side_effect=OSError("missing library")), \
             patch("gocr_worker.detector_runtime.GoogleConfiguredGroupRpnDetector",return_value="python"):
            with self.assertWarns(RuntimeWarning):
                self.assertEqual(create_detector("assets",2),"python")

    def test_python_debug_does_not_load_native_library(self):
        with patch.dict(os.environ,{"GOCR_DETECTOR":"python"}), \
             patch("gocr_worker.native_detector.NativeDetector") as native, \
             patch("gocr_worker.detector_runtime.GoogleConfiguredGroupRpnDetector",return_value="python"):
            self.assertEqual(create_detector("assets",1),"python")
            native.assert_not_called()

    def test_unknown_backend_is_configuration_error(self):
        with patch.dict(os.environ,{"GOCR_DETECTOR":"invalid"}):
            with self.assertRaises(ValueError):
                create_detector("assets")

    def test_generic_images_preserve_reference_api_and_selected_frame_uses_native(self):
        backend=Mock()
        backend.detect.return_value="native"
        ref=Mock()
        ref.detect.return_value="reference"
        with patch.dict(os.environ,{"GOCR_DETECTOR":"native"}), \
             patch("gocr_worker.native_detector.NativeDetector",return_value=backend), \
             patch("gocr_worker.detector_runtime.GoogleConfiguredGroupRpnDetector",return_value=ref) as constructor:
            selected=create_detector("assets",2)
            self.assertEqual(selected.detect(Image.new("RGB",(1280,720))),"native")
            constructor.assert_not_called()
            self.assertEqual(selected.detect(Image.new("L",(1280,720))),"reference")
            self.assertEqual(selected.detect(Image.new("RGB",(640,360))),"reference")
            constructor.assert_called_once_with("assets",2)
            self.assertEqual(backend.detect.call_count,1)
            self.assertEqual(ref.detect.call_count,2)


if __name__=="__main__":
    unittest.main()
