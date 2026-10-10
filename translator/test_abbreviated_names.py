import unittest
from unittest.mock import Mock
from abbreviated_names import has_abbreviated_names, translate_preserving_names


class NameTests(unittest.TestCase):
    def test_full_sentence_context_and_exact_initials_preserved(self):
        translate = Mock(side_effect=lambda text: {"translation": text, "provider": "madlad"})
        text = 'Call me Mr. E for short. Ask Dr. A. B. tomorrow.'
        result = translate_preserving_names(text, translate)
        self.assertEqual(result['translation'], text)
        translate.assert_called_once_with('Call me ZXQ0QXZ for short. Ask ZXQ1QXZ tomorrow.')

    def test_full_surnames_and_regular_words_are_not_selected(self):
        for text in ('Mr. Smith is here.', 'Mr. Encyclopedia', 'Go to the menu.', 'I am Mister Encyclopedia.'):
            self.assertFalse(has_abbreviated_names(text))
        self.assertTrue(has_abbreviated_names('Mr.E is here.'))

    def test_marker_collision_and_corruption(self):
        text = 'ZXQ0QXZ: Mr. E is here.'
        self.assertEqual(translate_preserving_names(text,
            lambda value: {'translation':value})['translation'], text)
        for output in ('Name lost', 'ZXQ0QXZ ZXQ0QXZ'):
            with self.assertRaises(RuntimeError):
                translate_preserving_names('Mr. E is here.', lambda _: {'translation':output})


if __name__ == '__main__':
    unittest.main()
