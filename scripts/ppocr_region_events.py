"""Original region appearance/envelope shared by early and final OCR results."""
import numpy as np


def region_line(index, region, rgb):
    b = region["box"]
    points = [(b["x"], b["y"]), (b["x"]+b["width"], b["y"]),
              (b["x"]+b["width"], b["y"]+b["height"]), (b["x"], b["y"]+b["height"])]
    crop = rgb[b["y"]:b["y"]+b["height"], b["x"]:b["x"]+b["width"]]
    edges = np.concatenate((crop[0], crop[-1], crop[:, 0], crop[:, -1]))
    bg = np.median(edges, axis=0)
    reliable = np.percentile(np.max(np.abs(edges.astype(float)-bg), axis=1), 90) < 20
    appearance = {"frame_width": 1280, "frame_height": 720, "box": b,
                  "lines": max(1, min(12, len(region["lines"]))),
                  "background_reliable": bool(reliable), "background": bg.astype(int).tolist(),
                  "foreground": [255, 255, 255] if bg.mean() < 128 else [0, 0, 0]}
    return {"line_id": str(index), "text": region["text"], "appearance": appearance,
            "recognition_lines": region["lines"], "timings_ms": {},
            "source_quad": {f"p{k}": {"x": x, "y": y} for k, (x, y) in enumerate(points)}}
