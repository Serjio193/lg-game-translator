"""Add the GOCR branch to the existing selected-frame consumer, never its producer."""
import argparse
from pathlib import Path
import shutil


def copy_transport(target, sources):
    for name in ("gocr_frame_transport.c", "gocr_frame_transport.h"):
        shutil.copy2(sources / name, target / "unicapture" / name)


def install(target, sources):
    worker = target / "unicapture/ocr_worker.c"
    cmake = target / "unicapture/CMakeLists.txt"
    text = worker.read_text(encoding="utf-8")
    # Refuse incompatible historical monolithic patches instead of guessing APIs.
    if "ocr_color_snapshot(worker, &local_rgb, &color_capacity);" not in text:
        raise ValueError("selected RGB snapshot API is missing; use the current PicCap checkout")
    if "gocr_submit_selected_rgb" in text:
        copy_transport(target, sources)
        return
    producer = text[text.index("void ocr_worker_submit("):]
    modified = text.replace('#include "ocr_worker.h"',
                            '#include "ocr_worker.h"\n#include "gocr_frame_transport.h"', 1)
    needle = '    text_detector_t* detector = text_detector_create(model_prefix);'
    if needle not in modified:
        raise ValueError("detector initialization point is missing")
    modified = modified.replace(needle, '    bool gocr = gocr_selected_frame_enabled();\n'
                                '    text_detector_t* detector = gocr ? NULL : text_detector_create(model_prefix);', 1)
    modified = modified.replace('    if (!detector)\n', '    if (!gocr && !detector)\n', 1)
    modified = modified.replace('    else\n        INFO("PP-OCRv5 text detector loaded',
                                '    else if (detector)\n        INFO("PP-OCRv5 text detector loaded', 1)
    modified = modified.replace('tesseract_pool_t* tesseract = ppocr_only ? NULL',
                                'tesseract_pool_t* tesseract = gocr || ppocr_only ? NULL', 1)
    modified = modified.replace('bool available = configured ? remote != NULL\n',
                                'bool available = gocr_selected_frame_enabled() || (configured ? remote != NULL\n', 1)
    modified = modified.replace('&& access("/usr/share/tessdata/eng.traineddata", R_OK) == 0;',
                                '&& access("/usr/share/tessdata/eng.traineddata", R_OK) == 0);', 1)
    needle = '        ocr_control_endpoint_t endpoint = {0};'
    position = modified.index(needle, modified.index("ocr_color_snapshot("))
    branch = ('        if (gocr) {\n'
              '            ocr_admission_publish(&(translator_frame_context_t){.sequence = sequence}, false);\n'
              '            if (gocr_submit_selected_rgb(local_rgb, width, height, sequence, sampled_ms) == 0) completed++;\n'
              '            continue;\n'
              '        }\n')
    modified = modified[:position]+branch+modified[position:]
    if modified[modified.index("void ocr_worker_submit("):] != producer:
        raise AssertionError("capture/selection producer must remain byte-identical")
    build = cmake.read_text(encoding="utf-8")
    if '        ocr_worker.c' not in build:
        raise ValueError("OCR source list is missing")
    build = build.replace('        ocr_worker.c', '        gocr_frame_transport.c\n        ocr_worker.c', 1)
    copy_transport(target, sources)
    worker.write_text(modified, encoding="utf-8")
    cmake.write_text(build, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("piccap_native", type=Path)
    args = parser.parse_args()
    install(args.piccap_native, Path(__file__).resolve().parents[1] / "native")
