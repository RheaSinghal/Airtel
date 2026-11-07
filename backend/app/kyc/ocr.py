"""On-device OCR for KYC documents (no image ever leaves the server).

Pipeline: quality gate (blur) -> watermark removal -> OCR -> deskew if the page is rotated -> rows.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from PIL import Image

BLUR_THRESHOLD = 60.0  # variance of the Laplacian below this => too blurry to trust


@dataclass
class OcrResult:
    rows: list[list[str]]   # each row = cells left-to-right
    blur_score: float
    rotation_deg: float
    mean_confidence: float

    @property
    def lines(self) -> list[str]:
        return [" :: ".join(r) for r in self.rows]


@lru_cache
def _engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGB")


def blur_score(img: Image.Image) -> float:
    """Variance of a 3x3 Laplacian on the grayscale image: low = blurry."""
    g = np.asarray(img.convert("L"), dtype=np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def _remove_watermark(img: Image.Image) -> np.ndarray:
    """Specimen watermarks are light/pink; document text is dark. Keep only dark pixels."""
    a = np.asarray(img).astype(np.int16)
    dark = a.max(axis=2) < 140
    bw = np.where(dark, 0, 255).astype(np.uint8)
    return np.stack([bw] * 3, axis=2)


def _ocr(arr: np.ndarray):
    result, _ = _engine()(arr)
    return result or []


def _angle(boxes) -> float:
    """Median text-baseline angle in degrees from OCR boxes (top-left -> top-right)."""
    angles = []
    for box, text, _ in boxes:
        (x1, y1), (x2, y2) = box[0], box[1]
        if len(text) >= 6 and x2 - x1 > 40:
            angles.append(math.degrees(math.atan2(y2 - y1, x2 - x1)))
    return float(np.median(angles)) if angles else 0.0


def _rows(boxes, tol: int = 22) -> list[list[str]]:
    items = sorted(((float(np.mean([p[1] for p in b])), float(b[0][0]), t) for b, t, _ in boxes))
    rows: list[list] = []
    for y, x, t in items:
        if rows and abs(rows[-1][0] - y) < tol:
            rows[-1][1].append((x, t))
        else:
            rows.append([y, [(x, t)]])
    return [[t for _, t in sorted(cells)] for _, cells in rows]


def read(data: bytes) -> OcrResult:
    img = load_image(data)
    score = blur_score(img)
    arr = _remove_watermark(img)
    boxes = _ocr(arr)
    rotation = _angle(boxes)
    if abs(rotation) > 1.0:
        rotated = Image.fromarray(arr).rotate(rotation, expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
        boxes = _ocr(np.asarray(rotated))
    conf = float(np.mean([c for _, _, c in boxes])) if boxes else 0.0
    return OcrResult(rows=_rows(boxes), blur_score=score, rotation_deg=round(rotation, 1), mean_confidence=round(conf, 3))
