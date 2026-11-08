"""Native matched-input parametric family for 20b53e0c4957.

The canonical setting preserves C's pre-existing holes.  The alternative first
repairs C's occupied bounding box, then applies the same input-derived A-minus-B
removal mask.  Python labels are claims; qualification replays every pair through
protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

TASK_ID = "20b53e0c4957"
POLICIES = ("preserve", "repair_then_transfer")
DEFAULT = {"hole_policy": "preserve"}
HERE = Path(__file__).resolve().parent

# Height, panel width, object height, object width.  Three panel widths plus two
# separators can reach at most 29 columns, so the stress case is lawfully 30x29.
_DEMO_PROFILES = (
    (6, 5, 4, 4),
    (8, 6, 5, 4),
    (10, 7, 6, 5),
    (12, 8, 8, 6),
    (14, 9, 10, 7),
    (18, 9, 14, 8),
)
_QUERY_PROFILES = (
    (7, 6, 5, 4),
    (11, 7, 7, 5),
    (16, 8, 12, 6),
    (30, 9, 26, 8),
)
_PALETTES = ((2, 7), (4, 6), (3, 7), (1, 8), (9, 2), (6, 8))


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings) -> str:
    if settings is None:
        return DEFAULT["hole_policy"]
    if type(settings) is not dict or set(settings) != {"hole_policy"}:
        raise ValueError("settings must name exactly hole_policy")
    value = settings["hole_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("hole_policy must be preserve or repair_then_transfer")
    return value


def program(settings=None) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "preserve" else "repair-then-transfer.rkt"
    return (HERE / name).read_text()


def _split(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if (width - 2) % 3:
        raise ValueError("grid width must encode three equal panels and two dividers")
    pw = (width - 2) // 3
    if any(row[pw] != 5 or row[2 * pw + 1] != 5 for row in grid):
        raise ValueError("expected two full-height color-5 separators")
    return (
        [row[:pw] for row in grid],
        [row[pw + 1 : 2 * pw + 1] for row in grid],
        [row[2 * pw + 2 :] for row in grid],
    )


def _cells(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _bbox(points):
    if not points:
        raise ValueError("empty foreground")
    return min(r for r, _ in points), min(c for _, c in points), max(r for r, _ in points), max(c for _, c in points)


def intermediate(grid) -> dict:
    """Return the input-dependent removal mask consumed by the second stage."""
    a, b, c = _split(grid)
    ca, cb, cc = _cells(a), _cells(b), _cells(c)
    ar0, ac0, _, _ = _bbox(ca)
    cr0, cc0, cr1, cc1 = _bbox(cc)
    removed = sorted((r - ar0, col - ac0) for r, col in ca - cb)
    return {
        "removed_offsets": [list(p) for p in removed],
        "c_bbox": [cr0, cc0, cr1, cc1],
    }


def transform(grid, settings=None):
    policy = _policy(settings)
    a, b, c = _split(grid)
    ca, cb, cc = _cells(a), _cells(b), _cells(c)
    ar0, ac0, _, _ = _bbox(ca)
    cr0, cc0, cr1, cc1 = _bbox(cc)
    removed = {(r - ar0, col - ac0) for r, col in ca - cb}
    colors = {value for row in c for value in row if value}
    if len(colors) != 1:
        raise ValueError("C must contain one foreground color")
    out = deepcopy(c)
    if policy == "repair_then_transfer":
        color = next(iter(colors))
        for r in range(cr0, cr1 + 1):
            for col in range(cc0, cc1 + 1):
                out[r][col] = color
    for rr, col in removed:
        r, ccol = cr0 + rr, cc0 + col
        if not (0 <= r < len(out) and 0 <= ccol < len(out[0])):
            raise ValueError("transferred removal escaped C")
        out[r][ccol] = 0
    return out


def _paint(panel, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            panel[r][c] = color


def _assemble(a, b, c):
    h, pw = len(a), len(a[0])
    result = [[0] * (3 * pw + 2) for _ in range(h)]
    for r in range(h):
        result[r][:pw] = a[r]
        result[r][pw] = 5
        result[r][pw + 1 : 2 * pw + 1] = b[r]
        result[r][2 * pw + 1] = 5
        result[r][2 * pw + 2 :] = c[r]
    return result


def _scene(seed: int, split: str, index: int):
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    h, pw, oh, ow = profiles[index]
    rng = random.Random(f"{TASK_ID}:{seed}:{split}:{index}")
    color_a, color_c = _PALETTES[(seed + 3 * index + (0 if split == "train" else 2)) % len(_PALETTES)]

    positions = [(r, c) for r in range(h - oh + 1) for c in range(pw - ow + 1)]
    a_top, a_left = rng.choice(positions)
    c_choices = [p for p in positions if p != (a_top, a_left)]
    c_top, c_left = rng.choice(c_choices)

    local = [(r, c) for r in range(oh) for c in range(ow)]
    interior = [(r, c) for r in range(1, oh - 1) for c in range(1, ow - 1)]
    rng.shuffle(local)
    removal_count = min(1 + ((seed + index) % 6), len(local) - 4)
    removed = set(local[:removal_count])
    hole_candidates = [p for p in interior if p not in removed]
    if not hole_candidates:
        # Keep removal_count fixed while reserving one interior position for a
        # genuinely independent C hole.  This branch only fires when the mask
        # happened to consume the entire interior of the smallest profile.
        released = next(p for p in interior if p in removed)
        replacement = next(p for p in local if p not in removed and p not in interior)
        removed.remove(released)
        removed.add(replacement)
        hole_candidates = [p for p in interior if p not in removed]
    rng.shuffle(hole_candidates)
    hole_count = min(1 + ((seed + 2 * index) % 3), len(hole_candidates))
    holes = set(hole_candidates[:hole_count])
    if not holes:
        raise AssertionError("profile must provide an independent interior C hole")

    a = [[0] * pw for _ in range(h)]
    b = [[0] * pw for _ in range(h)]
    c = [[0] * pw for _ in range(h)]
    _paint(a, a_top, a_left, oh, ow, color_a)
    _paint(b, a_top, a_left, oh, ow, color_a)
    _paint(c, c_top, c_left, oh, ow, color_c)
    for rr, cc in removed:
        b[a_top + rr][a_left + cc] = 0
    for rr, cc in holes:
        c[c_top + rr][c_left + cc] = 0
    grid = _assemble(a, b, c)

    # Internal construction assertions pin the intended teaching grammar.
    info = intermediate(grid)
    if {tuple(p) for p in info["removed_offsets"]} != removed:
        raise AssertionError("constructed removal mask changed")
    if transform(grid, {"hole_policy": "preserve"}) == transform(
        grid, {"hole_policy": "repair_then_transfer"}
    ):
        raise AssertionError("scene does not distinguish hole policy")
    return grid


def inputs(seed: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos = [_scene(seed, "train", i) for i in range(len(_DEMO_PROFILES))]
    queries = [_scene(seed, "test", i) for i in range(len(_QUERY_PROFILES))]
    return demos, queries


def generate(seed: int, settings=None, demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = {"hole_policy": _policy(settings)}
    train_inputs, test_inputs = inputs(seed)

    def pairs(grids):
        return [{"input": grid, "output": transform(grid, chosen)} for grid in grids]

    return {
        "train": pairs(train_inputs[:demos]),
        "test": pairs(test_inputs[:queries]),
        "program_solution": program(chosen),
        "settings": chosen,
    }
