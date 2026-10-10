import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from unittest.mock import patch
from contextlib import closing
import server
from translation_cache import TranslationCache


class PreviewApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.cache=TranslationCache(Path(self.temp.name)/'cache.sqlite3')
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever);self.thread.start()

    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();self.temp.cleanup()

    def post(self,text='Follow me!',**extra):
        request=Request(f'http://127.0.0.1:{self.http.server_port}/api/translate-preview',
                        json.dumps({'text':text,'provider':'google',**extra}).encode(),
                        {'Content-Type':'application/json'})
        try:response=urlopen(request,timeout=3)
        except HTTPError as error:response=error
        with response:return response.status,json.load(response)

    def test_miss_runs_only_bergamot_and_never_persists_preview(self):
        with patch.object(server,'_cache',self.cache), \
             patch.object(server,'_preview',return_value={'provider':'bergamot','translation':'За мной!'}) as preview, \
             patch.object(server,'_translate_google') as google:
            status,value=self.post()
        self.assertEqual(status,200);self.assertEqual(value['stage'],'preliminary')
        self.assertEqual(value['provider'],'google');self.assertEqual(value['engine'],'bergamot')
        preview.assert_called_once_with('Follow me!');google.assert_not_called()
        with closing(sqlite3.connect(self.cache.path)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM translations').fetchone()[0],0)

    def test_final_google_cache_hit_never_runs_a_model(self):
        self.cache.translate('Follow me!','google','google-nmt-v2:whole-reply-v1',
            lambda text:{'provider':'google','translation':'cached','latency_ms':1})
        with patch.object(server,'_cache',self.cache),patch.object(server,'_preview') as preview, \
             patch.object(server,'_translate_google') as google:
            status,value=self.post()
        self.assertEqual(status,200);self.assertEqual(value['stage'],'final')
        self.assertTrue(value['cache_hit']);self.assertEqual(value['translation'],'cached')
        preview.assert_not_called();google.assert_not_called()

    def test_invalid_or_unsupported_preview_never_runs_bergamot(self):
        with patch.object(server,'_preview') as preview:
            self.assertEqual(self.post(source_lang='ja')[0],400)
            self.assertEqual(self.post(text='')[0],400)
            self.assertEqual(self.post(text_type='bad')[0],400)
        preview.assert_not_called()


if __name__=='__main__':unittest.main()
