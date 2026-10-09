import hashlib
import math


def fingerprint(image):
    header = f"{image.mode}:{image.width}:{image.height}:".encode()
    return hashlib.sha256(header + image.tobytes()).hexdigest()


def quad_points(value):
    if isinstance(value, dict):
        value = [[value[f"p{i}"]["x"], value[f"p{i}"]["y"]] for i in range(4)]
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("source_quad must have four points")
    points = []
    for point in value:
        if len(point) != 2:
            raise ValueError("source_quad point must contain x,y")
        x, y = map(float, point)
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("source_quad coordinates must be finite")
        points.append([x, y])
    return points
