import unittest
from types import SimpleNamespace
from unittest.mock import patch

import server
from sentences import split_sentences


class SentenceTests(unittest.TestCase):
    def test_complete_reply(self):
        self.assertEqual(split_sentences("Did you pack a toothbrush? Oh, I'm sure you did. Take care now!"),
                         ["Did you pack a toothbrush?", "Oh, I'm sure you did.", "Take care now!"])

    def test_preserve_clause_and_abbreviations(self):
        for text in ["Dr. Smith is here.", "J. R. Smith is here.",
                     "It costs 3.5 coins.", "I passed out... When I woke up, I was here.",
                     "Use the sword— be sure to equip it.", "Follow me"]:
            self.assertEqual(split_sentences(text), [text])
        self.assertEqual(split_sentences('“Come here!” Then follow me.'),
                         ['“Come here!”', 'Then follow me.'])

    def test_batch_returns_every_sentence_in_order(self):
        inputs = []

        def encode(text):
            inputs.append(text)
            return SimpleNamespace(tokens=[text])

        tokenizer = SimpleNamespace(encode=encode, token_to_id=lambda token: token,
                                    decode=lambda ids, **kwargs: ids[0])
        model = SimpleNamespace(translate_batch=lambda pieces, **kwargs: [
            SimpleNamespace(hypotheses=[[f"перевод {index}"]])
            for index, _ in enumerate(pieces)])
        with patch.object(server, "_model", model), patch.object(server, "_tokenizer", tokenizer):
            result = server._translate_madlad("Where are we? Come here. Follow me!")
        self.assertEqual(inputs, ["<2ru> Where are we?", "<2ru> Come here.", "<2ru> Follow me!"])
        self.assertEqual(result["translation"], "перевод 0 перевод 1 перевод 2")
        self.assertEqual(result["sentence_count"], 3)
        self.assertEqual(result["generated_tokens"], 3)


if __name__ == "__main__":
    unittest.main()
