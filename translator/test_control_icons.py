import unittest
from control_icons import translate_around_icons, translate_preserving_icons
from unittest.mock import Mock


class ControlIconTests(unittest.TestCase):
    def test_provider_never_receives_icon(self):
        received = []

        def translate(text):
            received.append(text)
            return {"translation": "перевод", "provider": "test", "generated_tokens": 1}

        result = translate_around_icons("Press [button] to jump. Then press [button].", translate)
        self.assertEqual(received, ["Press", "to jump. Then press"])
        self.assertEqual(result["translation"], "перевод [button] перевод [button].")
        self.assertEqual(result["generated_tokens"], 2)

    def test_plain_text_is_unchanged(self):
        self.assertEqual(translate_around_icons("Follow me", lambda text: {"translation": text}),
                         {"translation": "Follow me"})

    def test_markers_keep_full_context_and_metadata(self):
        translate = Mock(side_effect=lambda text: {"translation": text, "provider": "madlad"})
        text = "Press [button] to jump, then [button] to fly."
        result = translate_preserving_icons(text, translate)
        translate.assert_called_once_with("Press ZXICON0XZ to jump, then ZXICON1XZ to fly.")
        self.assertEqual(result["translation"], text)
        self.assertEqual(result["provider"], "madlad")
        self.assertEqual(result["icon_strategy"], "markers")

    def test_invalid_markers_fall_back_without_leaking(self):
        for bad in ("lost", "ZXICON0XZ ZXICON0XZ ZXICON1XZ",
                    "ZXICON1XZ ZXICON0XZ", "ZXICON0XZ ZXICON1XZ [button]",
                    "ZXICON0XZ ZXICON1XZ ZXICON9XZ"):
            translate = Mock(side_effect=[{"translation": bad}, {"translation": "Первый"},
                                          {"translation": "Второй"}, {"translation": "Третий"}])
            result = translate_preserving_icons("First [button] second [button] third", translate)
            self.assertEqual(result["translation"], "Первый [button] Второй [button] Третий")
            self.assertEqual(result["icon_strategy"], "split_fallback")
            self.assertEqual(translate.call_count, 4)

    def test_collision_and_plain_text(self):
        translate = Mock(side_effect=lambda text: {"translation": text})
        text = "ZXICON0XZ: press [button]."
        self.assertEqual(translate_preserving_icons(text, translate)["translation"], text)
        self.assertIn("ZXICONX0XZ", translate.call_args.args[0])
        translate.reset_mock()
        self.assertEqual(translate_preserving_icons("Follow me", translate), {"translation": "Follow me"})
        translate.assert_called_once_with("Follow me")


if __name__ == "__main__":
    unittest.main()
