from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Quad:
    p0: Point
    p1: Point
    p2: Point
    p3: Point


@dataclass
class Symbol:
    text: str
    confidence: float | None = None
    quad: Quad | None = None


@dataclass
class Word:
    text: str
    confidence: float | None = None
    quad: Quad | None = None
    symbols: list[Symbol] = field(default_factory=list)


@dataclass
class Line:
    line_id: str
    text: str
    source_quad: Quad | None
    angle: float
    detector_confidence: float | None = None
    recognizer_confidence: float | None = None
    words: list[Word] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    crop_sha256: str | None = None
    recognizer_input_sha256: str | None = None


@dataclass
class OcrResult:
    schema: str
    width: int
    height: int
    mode: str
    lines: list[Line]
    timings_ms: dict[str, float] = field(default_factory=dict)
    parity: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
