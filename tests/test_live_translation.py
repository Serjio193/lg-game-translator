import copy
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock
from PIL import Image
from gocr_worker.frame_pipeline import FramePipeline
from gocr_worker.live_translation import LiveTranslations, client_for
from gocr_worker.osd_publisher import OsdPublisher

SESSION = ('com.webos.app.hdmi1', 'google', '192.168.1.11', '8765', '1')


def frame(sequence, texts=('Follow me!',), x=20, session=SESSION):
    return {'engine':'ppocr','sequence':sequence,'source_session':session,
            'timings_ms':{},'lines':[{'text':text,'translation_allowed':True,
                'appearance':{'box':{'x':x+i*300,'y':20,'width':200,'height':40},'lines':1},
                'timings_ms':{}} for i,text in enumerate(texts)]}


class RecordingPublisher(OsdPublisher):
    def __init__(self, root):
        super().__init__(root, lambda:1000)
        self.events, self.condition = [], threading.Condition()

    def emit(self, entries, responses, **options):
        super().emit(entries,responses,**options)
        with self.condition:
            self.events.append((copy.deepcopy(entries),copy.deepcopy(responses)))
            self.condition.notify_all()

    def wait(self, predicate):
        with self.condition:
            if not self.condition.wait_for(lambda:any(predicate(*event) for event in self.events),3):
                raise AssertionError('Expected OSD event did not arrive')


class Client:
    def __init__(self, provider='google'):
        self.provider=provider
        self.previews,self.finals=[],[]
        self.preview_started,self.release=threading.Event(),threading.Event()
        self.final_started=threading.Event()
        self.block_preview=False
        self.block_final=False

    def preview(self,text,**metadata):
        self.previews.append(text);self.preview_started.set()
        if self.block_preview and not self.release.wait(3):raise TimeoutError()
        return {'provider':self.provider,'translation':'preview '+text,
                'engine':'bergamot','stage':'preliminary','cache_hit':False}

    def translate(self,text,**metadata):
        self.finals.append(text)
        self.final_started.set()
        if self.block_final and not self.release.wait(3):raise TimeoutError()
        return {'provider':self.provider,'translation':'final '+text}


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.publisher=RecordingPublisher(Path(self.temp.name))
        self.client=Client();self.allowed=True
        def guard(session):
            if not self.allowed:raise ValueError('OFF')
        self.manager=LiveTranslations(self.publisher,client_factory=lambda session:self.client,guard=guard)

    def tearDown(self):
        self.client.release.set();self.manager.close();self.temp.cleanup()

    def preview_visible(self,text):
        self.publisher.wait(lambda entries,responses:any(
            response.get('stage')=='preliminary' and response['translation']=='preview '+text
            for response in responses.values()))

    def test_final_only_after_three_distinct_ocr_observations(self):
        self.manager.observe(frame(1));self.preview_visible('Follow me!')
        self.manager.observe(frame(1));self.manager.observe(frame(2))
        self.assertEqual(self.client.finals,[])
        self.manager.observe(frame(3))
        self.publisher.wait(lambda entries,responses:any(r.get('stage')=='final' for r in responses.values()))
        self.assertEqual(self.client.finals,['Follow me!'])
        self.assertEqual(self.publisher.tracks[0]['count'],3)
        self.assertEqual(self.publisher.timestamp,1000)

    def test_blocked_preview_does_not_block_frames_and_final_waits_for_preview(self):
        self.client.block_preview=True
        self.manager.observe(frame(1));self.assertTrue(self.client.preview_started.wait(1))
        self.manager.observe(frame(2));self.manager.observe(frame(3))
        self.assertEqual(self.client.finals,[])
        self.client.release.set()
        self.publisher.wait(lambda entries,responses:any(r.get('stage')=='final' for r in responses.values()))
        self.assertEqual(self.client.finals,['Follow me!'])

    def test_case_change_resets_source_confirmation(self):
        self.manager.observe(frame(1));self.preview_visible('Follow me!')
        self.manager.observe(frame(2))
        self.manager.observe(frame(3,('FOLLOW ME!',)))
        self.preview_visible('FOLLOW ME!')
        self.assertEqual(self.client.finals,[])
        self.assertEqual(self.publisher.tracks[0]['count'],1)
        self.manager.observe(frame(4,('FOLLOW ME!',)));self.manager.observe(frame(5,('FOLLOW ME!',)))
        self.publisher.wait(lambda entries,responses:any(r.get('translation')=='final FOLLOW ME!' for r in responses.values()))
        self.assertEqual(self.client.finals,['FOLLOW ME!'])

    def test_identical_regions_share_requests_but_keep_independent_tracks(self):
        self.manager.observe(frame(1,('Follow me!','Follow me!')))
        self.preview_visible('Follow me!')
        self.manager.observe(frame(2,('Follow me!','Follow me!')))
        self.manager.observe(frame(3,('Follow me!','Follow me!')))
        self.publisher.wait(lambda entries,responses:len(responses)==2 and all(r['stage']=='final' for r in responses.values()))
        self.assertEqual(self.client.previews,['Follow me!'])
        self.assertEqual(self.client.finals,['Follow me!'])
        self.assertEqual(len(self.publisher.tracks),2)

    def test_late_preview_after_off_is_not_published(self):
        self.client.block_preview=True
        self.manager.observe(frame(1));self.assertTrue(self.client.preview_started.wait(1))
        self.allowed=False;self.client.release.set()
        with self.manager.changed:
            self.assertTrue(self.manager.changed.wait_for(lambda:not self.manager.running,3))
        self.assertTrue(all(not responses for entries,responses in self.publisher.events))
        self.assertEqual(self.client.finals,[])

    def test_blocked_final_never_blocks_new_preview(self):
        self.client.block_final=True
        self.manager.observe(frame(1));self.preview_visible('Follow me!')
        self.manager.observe(frame(2));self.manager.observe(frame(3))
        self.assertTrue(self.client.final_started.wait(1))
        self.manager.observe(frame(4,('A new reply!',)))
        self.preview_visible('A new reply!')
        self.client.release.set()
        with self.manager.changed:
            self.assertTrue(self.manager.changed.wait_for(lambda:not self.manager.running,3))
        self.assertTrue(all(response.get('translation')!='final Follow me!'
            for entries,responses in self.publisher.events if entries and entries[0]['source_text']=='A new reply!'
            for response in responses.values()))

    def test_shared_final_is_not_published_for_an_unconfirmed_second_region(self):
        self.manager.observe(frame(1));self.preview_visible('Follow me!')
        self.manager.observe(frame(2));self.manager.observe(frame(3,('Follow me!','Follow me!')))
        self.publisher.wait(lambda entries,responses:len(responses)==2 and
            responses[0]['stage']=='final' and responses[1]['stage']=='preliminary')
        self.assertEqual([t['count'] for t in self.publisher.tracks],[3,1])
        self.assertEqual(self.client.finals,['Follow me!'])

    def test_no_pending_history_while_models_are_blocked(self):
        self.client.block_preview=True
        for sequence in range(1,30):
            self.manager.observe(frame(sequence,(f'New text {sequence}!',)))
        self.assertLessEqual(len(self.manager.groups),1)
        self.assertLessEqual(len(self.manager.running),2)
        self.client.release.set()
        self.preview_visible('New text 29!')
        self.assertLessEqual(len(self.client.previews),3)

    def test_cache_hit_skips_both_models_and_waits_for_source_confirmation(self):
        self.client.preview=Mock(return_value={'provider':'google','translation':'cached',
                                              'stage':'final','cache_hit':True})
        self.manager.observe(frame(1))
        with self.manager.changed:
            self.assertTrue(self.manager.changed.wait_for(lambda:not self.manager.running,3))
        self.assertTrue(all(not responses for entries,responses in self.publisher.events))
        self.manager.observe(frame(2));self.manager.observe(frame(3))
        self.publisher.wait(lambda entries,responses:any(r['translation']=='cached' for r in responses.values()))
        self.assertEqual(self.client.finals,[])
        self.client.preview.assert_called_once()

    def test_ocr_only_path_never_calls_inline_translator(self):
        client=Mock();client.ocr.return_value=(frame(1),123)
        translator=Mock()
        pipeline=FramePipeline(Path('unused'),'ORANGE_FULL',frame_client=client,translator=translator)
        try:
            result=pipeline.process(Image.new('RGB',(1280,720)),1,2,ocr_only=True)
            self.assertEqual(result['lines'][0]['text'],'Follow me!')
            translator.translate.assert_not_called()
            self.assertEqual(result['timings_ms']['translation'],0)
        finally:pipeline.close()

    def test_client_uses_provider_and_address_from_current_session(self):
        client=client_for(('hdmi','google','192.168.1.20','9000','2'))
        self.assertEqual(client.provider,'google')
        self.assertEqual(client.address,'http://192.168.1.20:9000/api/translate')

    def test_sentences_append_without_retranslating_prefix_or_typing_tail(self):
        self.manager.observe(frame(1,('Follow me! Take',)))
        self.preview_visible('Follow me!')
        self.assertEqual(self.client.previews, ['Follow me!'])
        self.manager.observe(frame(2,('Follow me! Take care!',)))
        self.publisher.wait(lambda entries, responses: any(
            r['translation'] == 'preview Follow me! preview Take care!' for r in responses.values()))
        self.assertEqual(self.client.previews, ['Follow me!', 'Take care!'])
        self.assertEqual(self.client.finals, [])
        self.manager.observe(frame(3,('Follow me! Take care!',)))
        self.manager.observe(frame(4,('Follow me! Take care!',)))
        self.publisher.wait(lambda entries, responses: any(r.get('stage')=='final' for r in responses.values()))
        self.assertEqual(self.client.finals, ['Follow me! Take care!'])

    def test_unfinished_text_waits_but_confirmed_unpunctuated_heading_translates(self):
        self.manager.observe(frame(1,('Check your gear',)))
        self.manager.observe(frame(2,('Check your gear',)))
        self.assertEqual(self.client.previews, [])
        self.manager.observe(frame(3,('Check your gear',)))
        self.preview_visible('Check your gear')

    def test_late_prefix_is_reused_but_old_whole_block_is_not_published(self):
        self.client.block_preview=True
        self.manager.observe(frame(1,('Follow me! Take',)))
        self.assertTrue(self.client.preview_started.wait(1))
        self.manager.observe(frame(2,('Follow me! Take care!',)))
        self.client.release.set()
        self.publisher.wait(lambda entries, responses: any(
            r['translation']=='preview Follow me! preview Take care!' for r in responses.values()))
        self.assertEqual(self.client.previews.count('Follow me!'), 1)
        self.assertTrue(all(not responses for entries, responses in self.publisher.events
                            if entries and entries[0]['source_text']=='Follow me! Take'))

    def test_corrected_sentence_is_translated_again(self):
        self.manager.observe(frame(1,('Follow me!',)));self.preview_visible('Follow me!')
        self.manager.observe(frame(2,('Follow us!',)));self.preview_visible('Follow us!')
        self.assertEqual(self.client.previews, ['Follow me!', 'Follow us!'])


if __name__=='__main__':unittest.main()
