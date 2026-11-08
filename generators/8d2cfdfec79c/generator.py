"""Constructive inputs for drawing colored rectangle borders from corner pairs.

The label authority remains the task's Racket rule.  ``_predict`` and the
named alternatives below are authoring diagnostics used to make generated
lessons discriminate first-appearance overwrite semantics.  Every public
axis is exact: every declared value is constructible in every difficulty
band and recoverable from the returned pixels by ``observe_overrides``.
"""
from __future__ import annotations

from collections import defaultdict
from functools import partial
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8d2cfdfec79c"
TASK_ID = GENERATOR_ID
RULE_HASH = "23e27bc62b89"
VERSION = "2.0.0"

SUMMARY = (
    "Each nonzero color marks two diagonal corners. In row-major first-appearance "
    "order, draw that color's bounding-box border on a fresh background-0 canvas; "
    "later borders overwrite earlier ones."
)
INVARIANTS = [
    "integer ARC colors 0..9 on an 8..13 by 10..14 background-0 canvas",
    "2..4 nonzero colors occur exactly twice at distinct rows and columns",
    "disjoint, nested, and crossing rectangle layouts are all lawful",
    "crossing borders are resolved by row-major first appearance, with later colors overwriting",
]

LAYOUT_KINDS = ("disjoint", "nested", "crossing")
CANONICAL_SHAPES = ((8, 10), (9, 11), (9, 12), (10, 12), (11, 13))
AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-shape canonical-anchor schedule",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "five-shape canonical-anchor schedule",
        "valid": "10..14",
    },
    "rectangles": {
        "type": "int",
        "default": "curriculum schedule 2,2,3,3",
        "valid": "2..4",
    },
    "layout_kind": {
        "type": "str",
        "default": "curriculum schedule crossing,disjoint,crossing,nested",
        "valid": "|".join(LAYOUT_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
MIN_TRAIN_PAIRS = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "overwrite_pair",
    "separate_pair",
    "overwrite_three",
    "nested_thin_three",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic four-position lesson phase."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _groups(grid):
    """Return nonzero cells in row-major first-appearance color order."""
    groups: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups[color].append((r, c))
    return groups


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _paint_box(out, box, color, *, fill=False):
    r0, c0, r1, c1 = box
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if fill or r in (r0, r1) or c in (c0, c1):
                out[r][c] = color


def _predict(grid, policy="intended"):
    """Python diagnostic mirror; generated labels still come from Racket.

    The intended rule starts from a blank canvas, groups colors in row-major
    first-appearance order, and lets later borders overwrite earlier borders.
    Policies implement plausible shortcuts for semantic-gate counterexamples.
    """
    if policy == "identity":
        return [list(row) for row in grid]

    groups = _groups(grid)
    ordered = list(groups)
    if policy == "reverse_order":
        ordered.reverse()
    elif policy == "completion_order":
        ordered.sort(key=lambda color: groups[color][-1])
    if policy == "first_two_only":
        ordered = ordered[:2]

    out = full_grid(len(grid), len(grid[0]), 0)
    for color in ordered:
        cells = groups[color]
        if len(cells) < 2:
            continue
        box = _bbox(cells)
        r0, c0, r1, c1 = box
        if policy == "min_side_three" and min(r1 - r0 + 1, c1 - c0 + 1) < 3:
            continue
        draw_color = 8 if policy == "fixed_color_8" else color
        _paint_box(out, box, draw_color, fill=(policy == "fill_boxes"))

    if policy == "restore_clues":
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color:
                    out[r][c] = color
    return out


def _distinguishes(grid, policy):
    return _predict(grid) != _predict(grid, policy)


# These alternatives are intentionally executable rather than prose-only.  The
# any three-example window of the four-position schedule refutes every one.
_COMPETITOR_NAMES = (
    "identity",
    "fill_boxes",
    "fixed_color_8",
    "reverse_order",
    "completion_order",
    "restore_clues",
    "first_two_only",
    "min_side_three",
)
LESSON_COMPETITORS = {
    name: partial(_predict, policy=name) for name in _COMPETITOR_NAMES
}
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {
    name: partial(_distinguishes, policy=name) for name in _COMPETITOR_NAMES
}
WITNESS_RIVALS = {name: [name] for name in _COMPETITOR_NAMES}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")

    for name, lo, hi in (("grid_h", 8, 13), ("grid_w", 10, 14), ("rectangles", 2, 4)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool or a coercible scalar)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared [{lo}, {hi}]")

    if "layout_kind" in overrides:
        value = overrides["layout_kind"]
        if type(value) is not str or value not in LAYOUT_KINDS:
            raise ValueError(f"layout_kind must be one of {LAYOUT_KINDS}")


def _axis(ctx, name, legal, default):
    """Consume one exact axis while retaining the full override domain."""
    options = tuple(legal) if name in ctx.overrides else (default,)
    return ctx.draw_choice(name, options)


def _rect_from_tile(tile, rng):
    rlo, clo, rhi, chi = tile
    rows = list(range(rlo, rhi + 1))
    cols = list(range(clo, chi + 1))
    r0, r1 = sorted(rng.sample(rows, 2))
    c0, c1 = sorted(rng.sample(cols, 2))
    return r0, c0, r1, c1


def _disjoint_boxes(h, w, number, rng):
    """One rectangle per non-overlapping quadrant tile."""
    rm = h // 2
    cm = w // 2
    tiles = [
        (0, 0, rm - 1, cm - 1),
        (0, cm, rm - 1, w - 1),
        (rm, 0, h - 1, cm - 1),
        (rm, cm, h - 1, w - 1),
    ]
    rng.shuffle(tiles)
    return [_rect_from_tile(tile, rng) for tile in tiles[:number]]


def _nested_boxes(h, w, number):
    """A containment chain whose innermost box has a two-cell side."""
    boxes = [(level, level, h - 1 - level, w - 1 - level)
             for level in range(number - 1)]
    # h>=8 and number<=4 guarantee this 2-row box is strictly inside the
    # preceding box.  It is the explicit counterexample to a min-side>=3 rule.
    r0 = (h - 2) // 2
    boxes.append((r0, number - 1, r0 + 1, w - number))
    return boxes


def _crossing_boxes(h, w, number):
    """Crossing boxes with first-appearance and completion orders reversed."""
    boxes = [
        (0, 1, h - 1, w - 2),
        (0, 0, h - 2, w - 1),
    ]
    # A three-box crossing scene doubles as the explicit thin-side witness.
    # For four boxes, insert one larger central box before the thin innermost
    # box.  The first two rectangles remain non-comparable overlaps, so the
    # observed layout is unambiguously 'crossing'.
    if number == 4:
        boxes.append((2, 2, h - 3, w - 3))
    if number >= 3:
        r0 = (h - 2) // 2
        inset = number - 1
        boxes.append((r0, inset, r0 + 1, w - 1 - inset))
    return boxes


def _clues_for_boxes(boxes, layout_kind, rng):
    clues = []
    for index, (r0, c0, r1, c1) in enumerate(boxes):
        if layout_kind == "crossing" and index == 1:
            # First clue is on the top row, but the second appears before the
            # first box's bottom clue.  This reverses completion order.
            pair = ((r0, c1), (r1, c0))
        elif layout_kind == "disjoint" and rng.randrange(2):
            pair = ((r0, c1), (r1, c0))
        else:
            pair = ((r0, c0), (r1, c1))
        clues.append(pair)
    return clues


def _candidate(h, w, number, layout_kind, colors, rng):
    if layout_kind == "disjoint":
        boxes = _disjoint_boxes(h, w, number, rng)
    elif layout_kind == "nested":
        boxes = _nested_boxes(h, w, number)
    else:
        boxes = _crossing_boxes(h, w, number)

    clues = _clues_for_boxes(boxes, layout_kind, rng)
    grid = full_grid(h, w, 0)
    for color, pair in zip(colors, clues):
        for r, c in pair:
            if grid[r][c] != 0:
                raise RuntimeError("constructive layout produced colliding clue cells")
            grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Difficulty changes neither legality nor exact override support.  The five
    # canonical shapes are deliberately retained in every band; geometry,
    # palette, diagonal direction, and lesson phase still vary independently.
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    anchor_h, anchor_w = CANONICAL_SHAPES[
        (sample_index + band_offset) % len(CANONICAL_SHAPES)
    ]
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    default_layout = ("crossing", "disjoint", "crossing", "nested")[phase]
    default_rectangles = (2, 2, 3, 3)[phase]

    h = _axis(ctx, "grid_h", range(8, 14), anchor_h)
    w = _axis(ctx, "grid_w", range(10, 15), anchor_w)
    number = _axis(ctx, "rectangles", range(2, 5), default_rectangles)
    layout_kind = _axis(ctx, "layout_kind", LAYOUT_KINDS, default_layout)

    rng = ctx.draw_rng("layout")
    colors = rng.sample(range(1, 10), number)
    grid = _candidate(h, w, number, layout_kind, colors, rng)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator violated its contract: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "rectangles": number,
        "layout_kind": layout_kind,
    }
    if observed != expected:
        raise RuntimeError(f"override observation mismatch: expected {expected}, got {observed}")
    return grid


def _overlaps(a, b):
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _contains(outer, inner):
    or0, oc0, or1, oc1 = outer
    ir0, ic0, ir1, ic1 = inner
    return or0 <= ir0 and oc0 <= ic0 and or1 >= ir1 and oc1 >= ic1


def _layout_kind_from_boxes(boxes):
    saw_overlap = False
    all_comparable = True
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            if not _overlaps(first, second):
                all_comparable = False
                continue
            saw_overlap = True
            if not (_contains(first, second) or _contains(second, first)):
                return "crossing"
    if saw_overlap and all_comparable:
        return "nested"
    return "disjoint"


def observe_overrides(grid):
    """Recover every public semantic axis exactly from returned pixels."""
    groups = _groups(grid)
    boxes = [_bbox(cells) for cells in groups.values()]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rectangles": len(groups),
        "layout_kind": _layout_kind_from_boxes(boxes),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Executable structural contract, including canonical crossing scenes."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (8 <= h <= 13 and 10 <= w <= 14):
        return ["canvas outside declared 8..13 by 10..14 domain"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    groups = _groups(grid)
    if not 2 <= len(groups) <= 4:
        errors.append(f"expected 2..4 paired colors, got {len(groups)}")
    for color, cells in groups.items():
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times; expected exactly 2")
            continue
        if cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            errors.append(f"color {color} cells must differ in both row and column")
    return errors


def strict_canonical_like(grid):
    """The canonical structural manifold permits lawful border overlap."""
    return self_check(grid)
