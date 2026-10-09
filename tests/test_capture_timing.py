import unittest
from gocr_worker.capture_timing import capture_age_ms


def legacy(milliseconds):
    microseconds = milliseconds*1000
    signed = (microseconds+(1 << 31)) % (1 << 32)-(1 << 31)
    return (signed % (1 << 64))//1000


class CaptureTimingTests(unittest.TestCase):
    def test_legacy_signed_wrap_and_multiple_wraps(self):
        for ms in (3000000, 5000000, 12000000):
            age, source = capture_age_ms(legacy(ms), ms+30)
            self.assertLess(abs(age-30), 1)
            self.assertIn("recovered", source)

    def test_valid_current_timestamp_and_missing(self):
        self.assertEqual(capture_age_ms(1000, 1030), (30, "monotonic_ms"))
        self.assertEqual(capture_age_ms(0, 1030)[0], None)
