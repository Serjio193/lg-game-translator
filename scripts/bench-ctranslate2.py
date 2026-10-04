#!/usr/bin/env python3
"""Measure an Argos or NLLB CTranslate2 model on an ARM host."""

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
    parser.add_argument("--family", choices=("argos", "nllb"), required=True)
    parser.add_argument("--model", default=os.environ.get("TRANSLATION_MODEL", "model"))
    parser.add_argument("--sentencepiece", default=os.environ.get(
        "TRANSLATION_SENTENCEPIECE", "sentencepiece.model"
    ))
    parser.add_argument("--threads", type=int, default=int(os.environ.get(
        "TRANSLATION_THREADS", "1"
    )))
    args = parser.parse_args()

    load_start = time.perf_counter()
    tokenizer = spm.SentencePieceProcessor(model_file=args.sentencepiece)
    translator = ctranslate2.Translator(
        args.model, device="cpu", inter_threads=1, intra_threads=args.threads
    )
    load_seconds = time.perf_counter() - load_start
    pieces = tokenizer.encode(SOURCE, out_type=str)

    def translate():
        if args.family == "nllb":
            source_tokens = ["eng_Latn"] + pieces + ["</s>"]
            hypotheses = translator.translate_batch(
                [source_tokens], target_prefix=[["rus_Cyrl"]],
                beam_size=4, max_decoding_length=256,
            )[0].hypotheses[0]
            if hypotheses and hypotheses[0] == "rus_Cyrl":
                hypotheses = hypotheses[1:]
        else:
            hypotheses = translator.translate_batch(
                [pieces], beam_size=4, max_decoding_length=256,
            )[0].hypotheses[0]
        return tokenizer.decode(hypotheses)

    warmup = translate()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    latencies = []
    outputs = []
    for _ in range(5):
        start = time.perf_counter()
        outputs.append(translate())
        latencies.append(time.perf_counter() - start)
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    print(json.dumps({
        "family": args.family,
        "model_path": args.model,
        "runtime": ctranslate2.__version__,
        "tokenizer": spm.__version__,
        "intra_threads": args.threads,
        "source_tokens": len(pieces),
        "load_ms": round(load_seconds * 1000, 2),
        "warmup_translation": warmup,
        "translations": outputs,
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
