"""Selected-frame byte contract before the existing native detector."""
import importlib.util
from pathlib import Path
import unittest

from PIL import Image

source = Path(__file__).resolve().parents[1] / "scripts/ppocr_frame_replay.py"
spec = importlib.util.spec_from_file_location("ppocr_replay_test", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrameContractTests(unittest.TestCase):
    def test_rgb_luminance_and_contiguous_frame(self):
        image = Image.new("RGB", (1280, 720), "white")
        for x, color in enumerate(((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255))):
            image.putpixel((x, 0), color)
        gray = module.gray_frame(image)
        self.assertEqual(gray[0, :5].tolist(), [0, 76, 149, 28, 255])
        self.assertEqual(gray.nbytes, 921600)
        self.assertTrue(gray.flags.c_contiguous)

    def test_rejects_changed_selected_frame_contract(self):
        for image in (Image.new("RGB", (1920, 1080)), Image.new("L", (1280, 720))):
            with self.assertRaises(ValueError):
                module.gray_frame(image)

    def test_tsv_ignores_non_word_rows_and_preserves_icon_marker(self):
        tsv = "header\n1\t1\t1\t1\t1\t1\t0\t0\t0\t0\t-1\tignored\n"
        tsv += "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90\tHold\n"
        tsv += "5\t1\t1\t1\t1\t2\t10\t0\t10\t10\t80\t[button]\n"
        self.assertEqual(module.parse_tsv(tsv), "Hold [button]")


if __name__ == "__main__":
    unittest.main()
