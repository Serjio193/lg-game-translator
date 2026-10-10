"""Final-only icon markers and cache revision isolation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import server


class IconRoutingTests(unittest.TestCase):
    def test_madlad_final_uses_markers_and_new_cache_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory)
            (model / "model.bin").write_bytes(b"model")
            (model / "tokenizer.json").write_bytes(b"tokenizer")
            cache = Mock()
            cache.translate.side_effect = lambda text, provider, revision, translate, **kwargs: translate(text)
            translate = Mock(side_effect=lambda text: {"translation": text})
            with patch.object(server, "MODEL_PATH", model), patch.object(server, "_cache", cache), \
                    patch.object(server, "_translate_madlad", translate):
                result = server._cached_translate("Press [button] to jump.", "madlad")
                icon_revision = cache.translate.call_args.args[2]
                server._cached_translate("Follow me.", "madlad")
                plain_revision = cache.translate.call_args.args[2]
            self.assertEqual(result["translation"], "Press [button] to jump.")
            self.assertEqual(translate.call_args_list[0].args[0], "Press ZXICON0XZ to jump.")
            self.assertTrue(icon_revision.endswith(":preserved-control-icons-markers-v2"))
            self.assertNotIn("control-icons", plain_revision)

    def test_preview_still_uses_original_split(self):
        translate = Mock(side_effect=lambda text: {"translation": text})
        with patch.object(server, "translate_bergamot", translate):
            result = server._preview("Press [button] to jump.")
        self.assertEqual([call.args[0] for call in translate.call_args_list], ["Press", "to jump."])
        self.assertEqual(result["translation"], "Press [button] to jump.")


if __name__ == "__main__":
    unittest.main()
