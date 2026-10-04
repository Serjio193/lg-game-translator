#!/usr/bin/env python3
"""Measure translation models through CTranslate2 on an ARM host."""

import argparse
import json
import os
import statistics
import time

import ctranslate2
import sentencepiece as spm


SOURCE = (
    "When the captain said, “Hold the line, watch the bank, and don’t touch "
    "the key,” Mira spotted a duck by the river—not the bank’s vault—and "
    "knew he meant the shore."
)


def proc_value(name):
    with open("/proc/self/status", encoding="ascii") as status:
        for line in status:
            if line.startswith(name + ":"):
                return int(line.split()[1])
    return None


def mem_available_kib():
    with open("/proc/meminfo", encoding="ascii") as meminfo:
        for line in meminfo:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--family", choices=("argos", "nllb", "opusmt", "m2m100"), required=True
    )
    parser.add_argument("--model", default=os.environ.get("TRANSLATION_MODEL", "model"))
    parser.add_argument("--sentencepiece", default=os.environ.get(
        "TRANSLATION_SENTENCEPIECE", "sentencepiece.model"
    ))
    parser.add_argument("--target-sentencepiece")
    parser.add_argument("--tokenizer")
    parser.add_argument("--source-language", default="en")
    parser.add_argument("--target-language", default="ru")
    parser.add_argument("--text", default=SOURCE)
    parser.add_argument("--beam-size", type=int, default=4)
    parser.add_argument("--max-decoding-length", type=int, default=256)
    parser.add_argument("--threads", type=int, default=int(os.environ.get(
        "TRANSLATION_THREADS", "1"
    )))
    args = parser.parse_args()

    load_start = time.perf_counter()
    hf_tokenizer = None
    if args.family == "m2m100":
        if not args.tokenizer:
            parser.error("--tokenizer is required for m2m100")
        from transformers import M2M100Tokenizer

        hf_tokenizer = M2M100Tokenizer.from_pretrained(args.tokenizer)
        hf_tokenizer.src_lang = args.source_language
        source_tokenizer = target_tokenizer = None
    else:
        source_tokenizer = spm.SentencePieceProcessor(model_file=args.sentencepiece)
        target_tokenizer = spm.SentencePieceProcessor(
            model_file=args.target_sentencepiece or args.sentencepiece
        )
    translator = ctranslate2.Translator(
        args.model, device="cpu", inter_threads=1, intra_threads=args.threads
    )
    load_seconds = time.perf_counter() - load_start
    if hf_tokenizer:
        source_ids = hf_tokenizer.encode(args.text)
        pieces = hf_tokenizer.convert_ids_to_tokens(source_ids)
        target_prefix = [hf_tokenizer.lang_code_to_token[args.target_language]]
    else:
        pieces = source_tokenizer.encode(args.text, out_type=str)
        target_prefix = None

    def translate():
        if args.family == "nllb":
            source_tokens = ["eng_Latn"] + pieces + ["</s>"]
            hypotheses = translator.translate_batch(
                [source_tokens], target_prefix=[["rus_Cyrl"]],
                beam_size=args.beam_size,
                max_decoding_length=args.max_decoding_length,
            )[0].hypotheses[0]
            if hypotheses and hypotheses[0] == "rus_Cyrl":
                hypotheses = hypotheses[1:]
        elif args.family == "m2m100":
            hypotheses = translator.translate_batch(
                [pieces], target_prefix=[target_prefix],
                beam_size=args.beam_size,
                max_decoding_length=args.max_decoding_length,
            )[0].hypotheses[0]
            if hypotheses and hypotheses[0] == target_prefix[0]:
                hypotheses = hypotheses[1:]
            return hf_tokenizer.decode(
                hf_tokenizer.convert_tokens_to_ids(hypotheses),
                skip_special_tokens=True,
            ), hypotheses
        else:
            hypotheses = translator.translate_batch(
                [pieces], beam_size=args.beam_size,
                max_decoding_length=args.max_decoding_length,
            )[0].hypotheses[0]
        return target_tokenizer.decode(hypotheses), hypotheses

    warmup, warmup_tokens = translate()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    latencies = []
    outputs = []
    output_token_lengths = []
    for _ in range(5):
        start = time.perf_counter()
        translation, tokens = translate()
        outputs.append(translation)
        output_token_lengths.append(len(tokens))
        latencies.append(time.perf_counter() - start)
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    print(json.dumps({
        "family": args.family,
        "source": args.text,
        "model_path": args.model,
        "runtime": ctranslate2.__version__,
        "sentencepiece": spm.__version__,
        "target_sentencepiece": args.target_sentencepiece,
        "tokenizer": args.tokenizer,
        "intra_threads": args.threads,
        "beam_size": args.beam_size,
        "max_decoding_length": args.max_decoding_length,
        "source_tokens": len(pieces),
        "load_ms": round(load_seconds * 1000, 2),
        "warmup_translation": warmup,
        "warmup_token_count": len(warmup_tokens),
        "warmup_token_prefix": warmup_tokens[:40],
        "translations": outputs,
        "output_token_lengths": output_token_lengths,
        "latencies_ms": [round(value * 1000, 2) for value in latencies],
        "median_ms": round(statistics.median(latencies) * 1000, 2),
        "cpu_seconds_over_five_runs": round(cpu_seconds, 3),
        "wall_seconds_over_five_runs": round(wall_seconds, 3),
        "cpu_one_core_percent": round(100 * cpu_seconds / wall_seconds, 1),
        "vmhwm_kib": proc_value("VmHWM"),
        "mem_available_kib": mem_available_kib(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
