from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from contextlib import nullcontext
import socketserver
from PIL import Image
from gocr_worker.source_admission import source_session, require_current
# Windows lacks the unused POSIX server base; exercise the real handler with mock IO.
compat = (nullcontext() if hasattr(socketserver, 'UnixStreamServer') else
          patch.object(socketserver, 'UnixStreamServer', socketserver.TCPServer, create=True))
with compat:
    from gocr_worker.tv_server import FrameHandler


class SourceAdmissionTests(unittest.TestCase):
    def test_handler_discards_accepted_result_completed_after_off(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"state"
            path.write_text('10000 1 madlad 192.168.1.11 8765 0 300 com.webos.app.hdmi1 1\n')
            class Pipeline:
                mode = 'ORANGE_FULL'
                def process(self, *args):
                    path.write_text('10000 0 madlad 192.168.1.11 8765 0 300 com.webos.app.hdmi1 1\n')
                    return {'schema':'gocr.worker.v1','engine':'ppocr','timings_ms':{},
                            'lines':[{'text':'old','translation':{'translation':'late'}}]}
            publisher = Mock()
            with patch('gocr_worker.tv_server.receive_frame', return_value=(Image.new('RGB',(1280,720)),1,2)), \
                 patch('gocr_worker.tv_server.source_session', side_effect=lambda:source_session(path,10000)), \
                 patch('gocr_worker.tv_server.require_current', side_effect=lambda value:require_current(value,path,10000)), \
                 patch('gocr_worker.tv_server.send_result') as send, patch('gocr_worker.tv_server.LOG'):
                FrameHandler(Mock(),None,SimpleNamespace(pipeline=Pipeline(),osd_publisher=publisher))
                self.assertEqual(send.call_args.args[1]['schema'],'gocr.worker.error.v1')
            publisher.publish.assert_not_called()

    def test_handler_does_not_publish_a_late_old_source_result(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"state"
            path.write_text('10000 1 madlad 192.168.1.11 8765 1 60 com.webos.app.hdmi1 1\n')
            class Pipeline:
                mode = 'ORANGE_FULL'
                def process(self, *args):
                    path.write_text('10000 1 madlad 192.168.1.11 8765 1 60 youtube.leanback.v4 2\n')
                    return {'schema': 'gocr.worker.v1', 'engine': 'ppocr', 'timings_ms': {}}
            publisher = Mock()
            server = SimpleNamespace(pipeline=Pipeline(), osd_publisher=publisher)
            with patch('gocr_worker.tv_server.receive_frame', return_value=(Image.new('RGB', (1280, 720)), 1, 2)), \
                 patch('gocr_worker.tv_server.source_session', side_effect=lambda: source_session(path, 10000)), \
                 patch('gocr_worker.tv_server.require_current', side_effect=lambda value: require_current(value, path, 10000)), \
                 patch('gocr_worker.tv_server.send_result') as send, \
                 patch('gocr_worker.tv_server.LOG'):
                FrameHandler(Mock(), None, server)
                self.assertEqual(send.call_args.args[1]['schema'], 'gocr.worker.error.v1')
            publisher.publish.assert_not_called()

    def test_current_selected_app_and_late_reply_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"state"
            path.write_text('10000 1 madlad 192.168.1.11 8765 1 60 youtube.leanback.v4\n')
            session = source_session(path, 11000)
            self.assertEqual(session[0], 'youtube.leanback.v4')
            require_current(session, path, 11000)
            path.write_text('11000 1 madlad 192.168.1.11 8765 1 60 com.webos.app.hdmi1\n')
            with self.assertRaises(ValueError):
                require_current(session, path, 12000)
            self.assertIsNone(source_session(path, 18001))
            path.write_text('18000 0 madlad 192.168.1.11 8765 1 60 youtube.leanback.v4\n')
            self.assertIsNone(source_session(path, 18000))

    def test_reenabling_same_source_changes_session(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"state"
            path.write_text('10000 1 madlad 192.168.1.11 8765 1 60 youtube.leanback.v4 1\n')
            session = source_session(path, 10000)
            path.write_text('10000 1 madlad 192.168.1.11 8765 1 60 youtube.leanback.v4 2\n')
            with self.assertRaises(ValueError):
                require_current(session, path, 10000)
