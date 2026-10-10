import base64
import io
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from google_budget import GoogleBudget, BudgetExceeded, LIMIT, WINDOW
from google_vault import GoogleVault
import google_control
import server
from translation_cache import TranslationCache


class GoogleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = 1791590400.0
        self.budget = GoogleBudget(self.root / 'usage.sqlite3', lambda: self.now)

    def tearDown(self):
        self.temp.cleanup()

    def test_atomic_parallel_limit_and_restart(self):
        self.budget.reserve('x' * (LIMIT-50))
        def reserve(_):
            try:
                self.budget.reserve('1234567890')
                return True
            except BudgetExceeded:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(20))), 5)
        restored = GoogleBudget(self.budget.path, lambda: self.now)
        self.assertEqual(restored.status()['monthly_characters'], LIMIT)
        self.assertTrue(restored.status()['blocked'])
        with self.assertRaises(BudgetExceeded):
            restored.reserve('a')

    def test_unicode_empty_and_unknown_attempts(self):
        text = '日本 中文 😀 [button] '
        attempt = self.budget.reserve(text)
        self.budget.complete(attempt)
        self.budget.reserve(text)  # unknown outcome remains counted
        self.assertEqual(self.budget.status()['monthly_characters'], len(text)*2)
        self.assertEqual(self.budget.status()['request_attempts'], 2)
        with self.assertRaises(ValueError):
            self.budget.reserve('   ')
        with self.assertRaises(BudgetExceeded):
            self.budget.reserve('x' * LIMIT)

    def test_month_reset_preserves_safety_window(self):
        self.budget.reserve('x' * LIMIT)
        self.now += 25*86400
        self.assertEqual(self.budget.status()['monthly_characters'], 0)
        self.assertTrue(self.budget.status()['blocked'])
        self.now += WINDOW
        self.assertEqual(self.budget.status()['remaining'], LIMIT)
        self.assertEqual(self.budget.status()['total_characters'], LIMIT)

    def vault(self):
        return GoogleVault(self.root / 'private')

    def test_encrypted_transport_restart_and_tamper(self):
        vault = self.vault()
        key = 'unit-test-credential-' + 'x'*30
        public = serialization.load_pem_public_key(vault.public_key().encode())
        cipher = public.encrypt(key.encode(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(), label=None))
        vault.import_encrypted(base64.b64encode(cipher).decode())
        self.assertNotIn(key, (vault.directory / 'google-key.enc').read_text())
        self.assertEqual(self.vault().get(), key)
        with self.assertRaises(ValueError):
            vault.import_encrypted('not encrypted')
        path = vault.directory / 'google-key.enc'
        data = json.loads(path.read_text())
        corrupted = bytearray(base64.b64decode(data['ciphertext']))
        corrupted[-1] ^= 1
        data['ciphertext'] = base64.b64encode(corrupted).decode()
        path.write_text(json.dumps(data))
        with self.assertRaises(InvalidTag):
            vault.get()
        if os.name != 'nt':
            self.assertEqual(vault.directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual((vault.directory/'master.key').stat().st_mode & 0o777, 0o600)

    def test_control_auth_and_no_secret_response(self):
        vault = self.vault()
        with patch.object(google_control, 'state', return_value=(vault,self.budget)), \
                patch.object(google_control, 'read_settings', return_value={'provider':'madlad'}):
            self.assertFalse(google_control.authorized({}))
            self.assertTrue(google_control.authorized({'X-OSD-Control-Key':vault.control}))
            self.assertNotIn(vault.control, json.dumps(google_control.status()))
            with self.assertRaises(ValueError):
                google_control.update({'key':'plaintext'})
            with self.assertRaises(ValueError):
                google_control.update({'provider':'google'})

    def test_failed_google_request_counted_and_limit_prevents_http(self):
        vault = self.vault()
        vault.store('unit-test-credential-'+'x'*30)
        with patch.object(google_control, 'state', return_value=(vault,self.budget)):
            with patch.object(server, 'urlopen', side_effect=URLError('private-details')):
                with self.assertRaisesRegex(RuntimeError, 'attempt remains counted'):
                    server._translate_google('hello')
            self.assertEqual(self.budget.status()['monthly_characters'], 5)
            self.budget.reserve('x' * (LIMIT-5))
            with patch.object(server, 'urlopen') as http:
                with self.assertRaises(BudgetExceeded):
                    server._translate_google('new')
                http.assert_not_called()

    def test_cache_hit_survives_exhausted_budget_without_http(self):
        vault = self.vault()
        vault.store('unit-test-credential-'+'x'*30)
        cache = TranslationCache(self.root/'translations.sqlite3')
        payload = b'{"data":{"translations":[{"translatedText":"hello"}]}}'
        with patch.object(google_control,'state',return_value=(vault,self.budget)), \
                patch.object(server,'_cache',cache):
            with patch.object(server,'urlopen',return_value=io.BytesIO(payload)):
                first = server._cached_translate('Follow me!', 'google')
            self.assertFalse(first['cache_hit'])
            self.budget.reserve('x'*(LIMIT-len('Follow me!')))
            with patch.object(server,'urlopen') as http:
                result = server._cached_translate('Follow me!', 'google')
                self.assertTrue(result['cache_hit'])
                self.assertEqual(result['translation'],first['translation'])
                self.assertEqual(self.budget.status()['monthly_characters'],LIMIT)
                http.assert_not_called()


if __name__ == '__main__':
    unittest.main()
