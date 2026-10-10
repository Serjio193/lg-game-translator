"""Session-local sentence previews; no persistent preliminary translation cache."""
from concurrent.futures import Future
import threading

try:
    from translator.sentences import completed_sentences
except ModuleNotFoundError:
    # TV bundle ships the canonical translator/sentences.py under this name.
    from .sentence_boundaries import completed_sentences


def units(text, confirmed=False):
    sentences, tail = completed_sentences(text)
    return sentences + ([tail] if confirmed and tail else [])


class SentencePreviews:
    def __init__(self):
        self.lock = threading.Lock()
        self.active, self.results, self.running = set(), {}, {}

    def retain(self, groups):
        with self.lock:
            self.active = {(g['session'], g['metadata']['text_type'], sentence)
                           for g in groups for sentence in units(g['text'], True)}
            self.results = {k: v for k, v in self.results.items() if k in self.active}

    @staticmethod
    def combine(group, sentences, responses):
        if len(responses) == 1 and sentences[0] == group['text']:
            return responses[0]
        return {'provider': group['session'][1], 'stage': 'preliminary', 'engine': 'bergamot',
                'translation': ' '.join(r['translation'] for r in responses), 'cache_hit': False}

    def snapshot(self, group):
        sentences, responses = units(group['text']), []
        with self.lock:
            for sentence in sentences:
                result = self.results.get((group['session'], group['metadata']['text_type'], sentence))
                if result is None:
                    break
                responses.append(result)
        return self.combine(group, sentences[:len(responses)], responses) if responses else None

    def translate(self, group, guard, progress):
        sentences = units(group['text'], max(e['observations'] for e in group['entries']) >= 3)
        responses = []
        for sentence in sentences:
            key = (group['session'], group['metadata']['text_type'], sentence)
            with self.lock:
                result = self.results.get(key)
                future = self.running.get(key)
                owner = result is None and future is None
                if owner:
                    future = self.running[key] = Future()
            if result is None:
                if owner:
                    try:
                        guard(group['session'])
                        with self.lock:
                            if key not in self.active:
                                raise ValueError('Obsolete sentence')
                        result = group['client'].preview(sentence, **group['metadata'])
                        if (result.get('provider') != group['session'][1]
                                or not result.get('translation', '').strip()
                                or not (result.get('stage') == 'final' and result.get('cache_hit') is True
                                        or result.get('stage') == 'preliminary'
                                        and result.get('engine') == 'bergamot')):
                            raise ValueError('Invalid sentence preview')
                        with self.lock:
                            if key in self.active:
                                self.results[key] = result
                        future.set_result(result)
                    except Exception as error:
                        future.set_exception(error)
                    finally:
                        with self.lock:
                            self.running.pop(key, None)
                result = future.result()
            responses.append(result)
            response = self.combine(group, sentences[:len(responses)], responses)
            if response.get('stage') == 'preliminary':
                progress(response)
        if not responses:
            return None
        return self.combine(group, sentences, responses)
