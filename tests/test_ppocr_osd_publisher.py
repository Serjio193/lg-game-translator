import json
from pathlib import Path
import tempfile
import unittest
from gocr_worker.osd_publisher import OsdPublisher


def result(sequence, text="Emergency Guard", x=20):
    return {"engine": "ppocr", "sequence": sequence, "lines": [{
        "text": text, "translation_allowed": text != "B",
        "appearance": {"box": {"x": x, "y": 20, "width": 200, "height": 40},
                                     "lines": 1, "frame_width": 1280, "frame_height": 720},
        "translation": {"provider": "madlad", "translation": "Аварийная охрана"}}]}


class PublisherTests(unittest.TestCase):
    def test_restart_sequence_with_new_capture_clock_resets_instead_of_freezing(self):
        with tempfile.TemporaryDirectory() as folder:
            publisher=OsdPublisher(Path(folder),lambda:1000)
            for sequence in (100,101,102):
                item=result(sequence);item['capture_ts']=sequence*1000;publisher.publish(item)
            old=publisher.tracks[0]['id']
            item=result(1);item['capture_ts']=103000;publisher.publish(item)
            self.assertEqual(publisher.tracks[0]['count'],1)
            self.assertNotEqual(publisher.tracks[0]['id'],old)
            publisher.publish(item)
            self.assertEqual(publisher.tracks[0]['count'],1,'Duplicate packet is not fresh')

    def test_source_switch_resets_observations_and_placement(self):
        with tempfile.TemporaryDirectory() as folder:
            publisher = OsdPublisher(Path(folder), lambda: 1000)
            for sequence in (1, 2, 3):
                item = result(sequence)
                item['source_session'] = ['com.webos.app.hdmi1', 'madlad', '192.168.1.11', '8765']
                publisher.publish(item)
            item = result(4, x=21)
            item['source_session'] = ['youtube.leanback.v4', 'madlad', '192.168.1.11', '8765']
            publisher.publish(item)
            gate = json.loads((Path(folder)/'ppocr-full-osd-admission.json').read_text())
            self.assertEqual(gate['regions'][0]['observations'], 1)
            self.assertEqual(gate['regions'][0]['appearance']['box']['x'], 21)

    def test_stability_changed_text_disappearance_and_duplicate_sequence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            publisher = OsdPublisher(root, lambda: 1000)
            for sequence in (1, 1, 2, 3):
                publisher.publish(result(sequence))
            def gate():
                return json.loads((root/"ppocr-full-osd-admission.json").read_text())
            entry = gate()["regions"][0]
            self.assertEqual(entry["observations"], 3)
            track = entry["admission"]["track_id"]
            publisher.publish(result(4, "Another dialogue"))
            self.assertEqual(gate()["regions"][0]["observations"], 1)
            self.assertNotEqual(gate()["regions"][0]["admission"]["track_id"], track)
            publisher.publish({"engine": "ppocr", "sequence": 5, "lines": []})
            self.assertEqual(gate()["regions"], [])

    def test_frozen_placement_and_single_button_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            publisher = OsdPublisher(Path(folder), lambda: 1000)
            publisher.publish(result(1))
            publisher.publish(result(2, x=21))
            gate = json.loads((Path(folder)/"ppocr-full-osd-admission.json").read_text())
            self.assertEqual(gate["regions"][0]["appearance"]["box"]["x"], 20)
            publisher.publish(result(3, "B"))
            gate = json.loads((Path(folder)/"ppocr-full-osd-admission.json").read_text())
            self.assertEqual(gate["regions"], [])
