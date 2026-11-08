"""Constructive sampler for the cropped four-arm spiral family."""
from __future__ import annotations

import hashlib
import importlib.util
import random
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent


def _load_engine():
    path = BASE / "engine.py"
    key = "_spiral_sampler_engine_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


engine = _load_engine()


def integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    return value


def _cross(h: int, w: int, cr: int, cc: int, length: int) -> list[list[int]]:
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for dr, dc in engine.DIRECTIONS:
        for step in range(1, length + 1):
            grid[cr + dr * step][cc + dc * step] = 8
    return grid


def _candidate_specs(h: int, w: int) -> list[tuple[int, int, int]]:
    """Small edge/center bank; selection stops at the first certified candidate."""
    specs: list[tuple[int, int, int]] = []
    for length in range(1, min(7, (min(h, w) - 1) // 2 + 1)):
        rows = sorted({
            length, length + 1, length + 2, length + 3,
            h - length - 1, h - length - 2, h - length - 3,
            h // 2 - 1, h // 2, h // 2 + 1,
        })
        cols = sorted({
            length, length + 1, length + 2, length + 3,
            w - length - 1, w - length - 2, w - length - 3,
            w // 2 - 1, w // 2, w // 2 + 1,
        })
        for cr in rows:
            for cc in cols:
                if length <= cr < h - length and length <= cc < w - length:
                    specs.append((cr, cc, length))
    return specs


def _choose_spec(h: int, w: int, seed: int, index: int, split: str) -> tuple[int, int, int]:
    specs = _candidate_specs(h, w)
    rng = random.Random(f"spiral-placement-v4:{seed}:{split}:{index}:{h}:{w}")
    rng.shuffle(specs)
    desired_winner = index % 4
    fallback = None
    for cr, cc, length in specs:
        grid = _cross(h, w, cr, cc, length)
        counts = engine.analyze(grid)["visible_counts"]
        if len(set(counts)) != 4 or min(counts) <= 0:
            continue
        if fallback is None:
            fallback = (cr, cc, length)
        if counts.index(max(counts)) == desired_winner:
            return cr, cc, length
    if fallback is not None:
        raise RuntimeError(
            f"unique placements exist for {h}x{w}, but none teaches winner {desired_winner}"
        )
    raise RuntimeError(f"no unique-visibility spiral placement for {h}x{w}")


def _dimensions(seed: int, index: int, split: str) -> tuple[int, int]:
    if split == "test" and index == 103:
        return 30, 30
    rng = random.Random(f"spiral-dim-v2:{seed}:{split}:{index}")
    return rng.randint(18, 29), rng.randint(18, 29)


def draw(seed: int, index: int, *, split: str = "train") -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 10_000, "index")
    if split not in {"train", "test", "production"}:
        raise ValueError("split must be train, test, or production")
    effective = "test" if split == "test" else split
    h, w = _dimensions(seed, index, effective)
    cr, cc, length = _choose_spec(h, w, seed, index, split)
    return _cross(h, w, cr, cc, length)
