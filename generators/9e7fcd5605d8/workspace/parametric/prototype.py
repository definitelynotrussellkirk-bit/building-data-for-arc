"""Constructive, setting-independent lessons for enclosed-region thresholds.

Labels here are claims, not execution receipts. The native qualifier and
verify.py re-execute the materialized Racket programs for every retained pair.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent


def _load(path, tag):
    body = path.read_bytes()
    name = "_topology_" + tag + "_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


_base = _load(HERE.parents[1] / "generator.py", "base")
_rules = _load(HERE / "rules.py", "rules")
_PALETTE = (1, 2, 3, 5, 6, 7, 9)
_DEMO_SIZES = ((11, 13), (17, 13), (15, 17), (17, 19), (19, 21), (21, 23))
_QUERY_SIZES = ((11, 11), (18, 24), (24, 21), (30, 30))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _threshold(settings):
    if type(settings) is not dict or set(settings) != {"min_holes"}:
        raise ValueError("settings must contain only min_holes")
    return _integer(settings["min_holes"], 1, 2, "min_holes")


def program(settings):
    threshold = _threshold(settings)
    if threshold == 1:
        return (HERE / "canonical.rkt").read_text(encoding="utf-8")
    return _rules.count_rule(threshold)


def analyze(grid):
    """Read-only component topology, reusing the reviewed canonical mirror."""
    info, errors = _base._analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return info["components"]


def _rng(seed, split, index):
    value = hashlib.sha256(f"topology-threshold-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(value, "big"))


def _spans(length, count):
    usable = length - count + 1
    size, extra = divmod(usable, count)
    spans, start = [], 0
    for i in range(count):
        width = size + (i < extra)
        spans.append((start, start + width))
        start += width + 1
    return spans


def _shape(kind, h, w, rng):
    """Connected masks with variable geometry and a constructive hole count."""
    shape = [[1] * w for _ in range(h)]
    if kind in {"open", "ring", "corner"}:
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                shape[r][c] = 0
        if kind == "open":
            # A genuine path to the bounding-box rim, not a diagonal escape.
            for c in range(1, w - 1):
                shape[0][c] = 0
        elif kind == "corner":
            # This is closed in 4-connectivity, open only in 8-connectivity.
            shape[0][0] = 0
    elif kind == "one":
        # Thick walls and unequal cavity dimensions vary enclosed area.
        rh, rw = rng.randint(1, h - 2), rng.randint(2, w - 2)
        r0, c0 = rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                shape[r][c] = 0
    elif kind == "two_diag":
        shape[1][1] = shape[2][2] = 0
    elif kind in {"two", "three", "four"}:
        cells = [(1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)]
        for r, c in cells[:{"two": 2, "three": 3, "four": 4}[kind]]:
            shape[r][c] = 0
    elif kind == "bay":
        shape[0][1] = shape[1][1] = shape[h - 2][w - 2] = 0
    elif kind != "solid":
        raise ValueError(f"Unknown constructive topology {kind}")
    return shape


def _transform(shape, rng, slot_h, slot_w):
    if rng.randrange(2):
        shape = [row[::-1] for row in shape]
    turns = rng.randrange(4) if len(shape) <= slot_w and len(shape[0]) <= slot_h else 2 * rng.randrange(2)
    for _ in range(turns):
        shape = [list(row) for row in zip(*shape[::-1])]
    return shape


def _input(seed, split, index):
    h, w = (_DEMO_SIZES if split == "train" else _QUERY_SIZES)[index]
    rng = _rng(seed, split, index)
    nr, nc = min(4, (h + 1) // 6), min(4, (w + 1) // 6)
    rows, cols = _spans(h, nr), _spans(w, nc)
    slots = [(r0, r1, c0, c1) for r0, r1 in rows for c0, c1 in cols]
    if split == "train" and index == 0:
        kinds = ["open", "one", "two_diag", "three"]
    elif split == "train" and index == 1:
        # Six objects break relative-rank/median shortcuts while teaching
        # both diagonal escape and exclusion of rim-connected regions.
        kinds = ["solid", "corner", "bay", "ring", "two_diag", "three"]
    else:
        kinds = ["open", "one", "two_diag", "three"]
    bank = ("solid", "open", "one", "ring", "corner", "two", "two_diag", "three", "four", "bay")
    kinds += [rng.choice(bank) for _ in range(len(slots) - len(kinds))]
    rng.shuffle(kinds)
    # The first demo forces opposite labels for the same source color.
    # Subsequent colors are independently drawn; no parameter enters this RNG.
    palette = rng.sample(_PALETTE, 1 if split == "train" and index == 0 else rng.randint(1, 3))
    grid = [[0] * w for _ in range(h)]
    for i, ((r0, r1, c0, c1), kind) in enumerate(zip(slots, kinds)):
        slot_h, slot_w = r1 - r0, c1 - c0
        boundary = h == 30 and w == 30 and r0 in (rows[0][0], rows[-1][0]) and c0 in (cols[0][0], cols[-1][0])
        sh = slot_h if boundary else rng.randint(5, slot_h)
        sw = slot_w if boundary else rng.randint(5, slot_w)
        shape = _transform(_shape(kind, sh, sw, rng), rng, slot_h, slot_w)
        sh, sw = len(shape), len(shape[0])
        top = r0 + rng.randrange(slot_h - sh + 1)
        left = c0 + rng.randrange(slot_w - sw + 1)
        color = palette[i % len(palette)]
        for r in range(sh):
            for c in range(sw):
                if shape[r][c]:
                    grid[top + r][left + c] = color
    objects = analyze(grid)
    if len(objects) != len(slots) or not {0, 1, 2, 3} <= {obj["holes"] for obj in objects}:
        raise RuntimeError("Constructive topology invariant failed")
    return grid


def generate(seed, settings, demos=3, queries=4):
    """Return independent 2..6-demo/1..4-query counts with stable prefixes.

    The supported grammar has separated monochromatic objects, black background,
    and componentwise bbox complements. Nested/touching multicolor scenes are
    outside this sampler, although programs remain total on typed grids.
    """
    threshold = _threshold(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = _input(seed, split, index)
            output = _base._paint_classified(grid, lambda obj: obj["holes"] >= threshold)
            pairs.append({"input": grid, "output": output})
        episode[split] = pairs
    keys = [json.dumps(pair["input"], separators=(",", ":"))
            for split in ("train", "test") for pair in episode[split]]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Input collision: refusing duplicate demonstrations or queries")
    return episode
