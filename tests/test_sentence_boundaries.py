import unittest
from translator.sentences import completed_sentences


class Boundaries(unittest.TestCase):
    def test_finished_prefix_and_unfinished_tail(self):
        self.assertEqual(completed_sentences('Where are we? Follow me! Take'),
                         (['Where are we?', 'Follow me!'], 'Take'))

    def test_abbreviations_decimals_and_ellipsis_are_not_terminal(self):
        for text in ['Dr.', 'J.', 'It costs 3.5', 'Wait...']:
            self.assertEqual(completed_sentences(text), ([], text))
        self.assertEqual(completed_sentences('Dr. Smith is here. Go'),
                         (['Dr. Smith is here.'], 'Go'))


if __name__ == '__main__':
    unittest.main()
