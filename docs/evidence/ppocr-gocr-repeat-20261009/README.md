# Installed PP-OCR vs GOCR, identical region replay

2026-10-09. 60 rectified grayscale crops from the same three frames used in the TV_FULL repeat test. Rectification uses the existing GOCR/Pillow reference, with original source quads; PP-OCR's own detector was not run. This is a recognizer comparison on GOCR-selected regions, not a complete PP-OCR detector/pipeline quality or latency comparison.

Running authenticated Orange crop service: PP-OCRv6 small, class-major NPU. One warmup and three measured requests per crop; all returned texts repeat identically. Existing mode 4 includes the installed Tesseract-assisted control-glyph geometry check for instruction text; it does not use Tesseract to replace ordinary PP-OCR wording. Results therefore represent the installed recognition path, not bare PP-OCR network output.

| Input | GOCR | Installed PP-OCR |
|---|---|---|
| Fresh Demo label | Demd | Demo |
| Saved Attack Combos | Attack ComboS | Attack Combos |
| Luigi footer B | Cyrillic В | Latin B |
| Luigi title | Snoutlet School | SnoutletSchool |
| Luigi non-text/illegible crop | empty | 中 |
| Fresh instruction ending guard | guarc | guaro |

Fresh instruction crop visibly cuts the rightmost glyph at its right boundary. Both failures require investigating the crop boundary before attributing them solely to recognizer models. Luigi instruction gets a `[button]` placeholder in the installed path; this is an existing control-icon feature, not a literal image word or PP-OCR-only accuracy proof.

Sequential sum of per-crop median local RPC times: fresh Emergency 2342.8 ms, saved Emergency 2280.3 ms, Luigi 2170.8 ms. This includes loopback RPC, preprocessing, installed icon processing and decoding; excludes own detector, TV/Orange network, stabilization, translation and OSD. It is not a measured whole-frame pipeline latency or a pure NPU inference benchmark. No speed comparison to TV_FULL is admitted from these totals.

No model/config/service/production selection changed by this isolated replay. Raw text, geometry, repetitions and RPC timings are in results.json.
