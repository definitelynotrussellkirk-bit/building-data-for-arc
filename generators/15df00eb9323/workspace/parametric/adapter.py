"""Native majority-versus-unanimous normalized-overlay family.

The visible input is independent of the private setting.  Stage A extracts the
three isolated blobs, crops each to its own bounding box, and forms a normalized
support-count map.  Stage B applies the selected consensus threshold, paints
survivors cyan, and crops the result.  Every generated case contains support
levels one, two, and three, so both settings are causally active.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "15df00eb9323"
LEVELS = ("majority", "unanimous")
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")


def _load_generator():
    path = _TASK_HOME / "generator.py"
    name = "_parametric_source_15df00eb9323"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()
_THRESHOLD = "(>= cnt 2)"
if _CANONICAL.count(_THRESHOLD) != 1:
    raise RuntimeError("canonical support threshold changed; refusing unsafe rewrite")
_UNANIMOUS_PROGRAM = _CANONICAL.replace(_THRESHOLD, "(>= cnt 3)")


def _level(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"consensus_level"}:
        raise ValueError("settings must name exactly consensus_level")
    value = settings["consensus_level"]
    if type(value) is not str or value not in LEVELS:
        raise ValueError("consensus_level must be 'majority' or 'unanimous'")
    return value


def program(settings: dict[str, Any]) -> str:
    level = _level(settings)
    return _CANONICAL if level == "majority" else _UNANIMOUS_PROGRAM


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def _rng(seed: int, phase: str, slot: int) -> random.Random:
    raw = f"{TASK_ID}|consensus-family-v1|{seed}|{phase}|{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _normalize(cells):
    cells = set(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _transform(cells, code: int):
    cells = set(cells)
    if code >= 4:
        cells = {(r, -c) for r, c in cells}
    for _ in range(code % 4):
        cells = {(c, -r) for r, c in cells}
    return _normalize(cells)


def _dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _band_triplet(size: int):
    """Return three connected square masks with support levels 1, 2, and 3.

    A common top/left spine has support three.  Three inner horizontal bands
    are pairwise support, and three further bands are unique.  For size nine,
    each source has 41 cells (123 visible cells total) while the majority
    intermediate has 41 cells and the unanimous intermediate has 17.
    """
    if size not in (7, 9):
        raise ValueError("band triplet size must be 7 or 9")
    common = {(0, c) for c in range(size)} | {(r, 0) for r in range(size)}
    width = range(1, size)
    ab = {(1, c) for c in width}
    ac = {(2, c) for c in width}
    bc = {(3, c) for c in width}
    ua = {(4, c) for c in width}
    ub = {(5, c) for c in width}
    uc = {(6, c) for c in width}
    # The 9x9 case deliberately leaves rows 7 and 8 occupied only through the
    # common left spine, expanding the normalized bbox without changing the
    # exact support spectrum.
    a = frozenset(common | ab | ac | ua)
    b = frozenset(common | ab | bc | ub)
    c = frozenset(common | ac | bc | uc)
    return (a, b, c)


_DEMO_PROFILES = (
    (8, 12, "small", 0),
    (9, 13, "small", 1),
    (10, 14, "small", 2),
    (11, 15, "small", 3),
    (12, 16, "small", 0),
    (14, 18, "small", 1),
)
_QUERY_PROFILES = (
    (7, 11, "small", 2),
    (15, 18, "small", 3),
    (22, 24, "band7", 0),
    (30, 30, "band9", 0),
)


def _shapes_for(profile, rng: random.Random):
    _, _, kind, index = profile
    if kind == "small":
        source = _GENERATOR._SHAPE_TRIPLETS[index]
        code = rng.randrange(8)
        return tuple(_transform(shape, code) for shape in source)
    if kind == "band7":
        return _band_triplet(7)
    if kind == "band9":
        return _band_triplet(9)
    raise ValueError(f"unknown profile kind: {kind}")


def _small_anchors(height: int, width: int, shapes, rng: random.Random):
    starts = [0, (width - 3) // 2, width - 3]
    rng.shuffle(starts)
    anchors = []
    for left, shape in zip(starts, shapes):
        sh, sw = _dims(shape)
        if sh > height or sw > 3:
            raise RuntimeError("small profile does not fit its shelf")
        # Center only after a concrete shape has been assigned to this shelf;
        # shuffling already-centered anchors can move a wider mask past the
        # right boundary (the seed-7 regression).
        anchors.append((rng.randint(0, height - sh), left + (3 - sw) // 2))
    return anchors


def _anchors(height: int, width: int, shapes, kind: str, rng: random.Random):
    if kind == "small":
        return _small_anchors(height, width, shapes, rng)
    size = 7 if kind == "band7" else 9
    if kind == "band7":
        anchors = [(0, 0), ((height - size) // 2, 8), (height - size, width - size)]
    else:
        anchors = [(0, 0), (0, width - size), (height - size, (width - size) // 2)]
    # Permuting which mask occupies which location changes appearance without
    # changing the normalized support map or allowing the setting to leak.
    rng.shuffle(anchors)
    return anchors


def _halo(cells, height: int, width: int):
    result = set()
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    result.add((nr, nc))
    return result


def _paint(profile, rng: random.Random):
    height, width, kind, _ = profile
    shapes = _shapes_for(profile, rng)
    anchors = _anchors(height, width, shapes, kind, rng)
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 9), 3)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    forbidden: set[tuple[int, int]] = set()
    for shape, (top, left), color in zip(shapes, anchors, colors):
        cells = {(top + r, left + c) for r, c in shape}
        if not cells or any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
            raise RuntimeError("profile placement left the grid")
        if cells & forbidden:
            raise RuntimeError("profile placement violates the one-cell moat")
        for r, c in cells:
            grid[r][c] = color
        occupied |= cells
        forbidden |= _halo(cells, height, width)
    if len(occupied) != sum(len(shape) for shape in shapes):
        raise RuntimeError("profile shapes overlap")
    return grid


def _support_counts(grid):
    comps = _GENERATOR.components(grid)
    if len(comps) != 3:
        raise RuntimeError(f"expected three source blobs, found {len(comps)}")
    return _GENERATOR._support_counts_from_components(comps)


def _predict(grid, level: str):
    threshold = 2 if level == "majority" else 3
    return _GENERATOR._overlay(grid, threshold)


def _span(grid):
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return (
        max(r for r, _ in occupied) - min(r for r, _ in occupied),
        max(c for _, c in occupied) - min(c for _, c in occupied),
    )


def _accepted_input(*, seed: int, phase: str, slot: int, profile, seen: set[str]):
    # Profiles are constructive rather than rejection-sampled.  The checks are
    # still kept at the boundary so a future profile edit fails closed.
    rng = _rng(seed, phase, slot)
    grid = _paint(profile, rng)
    counts = _support_counts(grid)
    if set(counts.values()) != {1, 2, 3}:
        raise RuntimeError(f"profile {phase}[{slot}] lost identifying support levels")
    if _predict(grid, "majority") == _predict(grid, "unanimous"):
        raise RuntimeError(f"profile {phase}[{slot}] does not distinguish settings")
    height, width, kind, _ = profile
    if (height, width) == (30, 30):
        if sum(value != 0 for row in grid for value in row) < 120:
            raise RuntimeError("stress profile is too sparse")
        if min(_span(grid)) < 24:
            raise RuntimeError("stress profile does not span the canvas")
        if sum(value != 0 for row in _predict(grid, "majority") for value in row) < 20:
            raise RuntimeError("stress majority intermediate is too small")
    digest = _digest(grid)
    if digest in seen:
        raise RuntimeError(f"duplicate visible input at {phase}[{slot}]")
    seen.add(digest)
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    level = _level(settings)
    _validate_request(seed, demos, queries)
    seen: set[str] = set()
    train = []
    for slot, profile in enumerate(_DEMO_PROFILES[:demos]):
        grid = _accepted_input(seed=seed, phase="demo", slot=slot, profile=profile, seen=seen)
        train.append({"input": copy.deepcopy(grid), "output": _predict(grid, level)})
    test = []
    for slot, profile in enumerate(_QUERY_PROFILES):
        grid = _accepted_input(seed=seed, phase="query", slot=slot, profile=profile, seen=seen)
        test.append({"input": copy.deepcopy(grid), "output": _predict(grid, level)})
    return {"train": train, "test": test, "program_solution": program(settings)}
