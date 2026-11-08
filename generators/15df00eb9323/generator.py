"""Generator for task ``15df00eb9323`` (normalized majority overlay).

Three isolated, distinct-colour blobs are cropped to their own bounding boxes
and aligned at the top-left.  A cell survives in cyan when at least two cropped
shapes occupy that normalized location; the result is cropped to content.

Version 2.0.0 replaces dead/coercive controls with three exact observable axes,
keeps every canonical input inside the validator, and constructs lessons with
single-, pair-, and triple-support cells so union and unanimity shortcuts are
both visibly false.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "15df00eb9323"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ff0ecb044bc8"

SUMMARY = (
    "Exactly three isolated distinct-colour blobs appear on a zero background. "
    "Crop each blob to its bounding box, align the crops at their top-left "
    "corners, keep normalized cells occupied by at least two blobs, paint them "
    "cyan (8), and crop the result to content."
)

EXAMPLES_NEEDED = 3
PALETTE_KINDS = ("default", "warm", "cool", "varied")
_PALETTES = {
    # The four sets cover every canonical palette exactly while remaining
    # disjoint as complete three-colour signatures for observable overrides.
    "default": (2, 4, 6),
    "warm": (3, 5, 7),
    "cool": (2, 4, 8),
    "varied": (2, 5, 7),
}
_PALETTE_BY_SET = {frozenset(values): name for name, values in _PALETTES.items()}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "11..18"},
    "palette_kind": {
        "type": "str",
        "default": "four-step schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}

INVARIANTS = [
    "rectangular 7..14 by 11..18 zero-background ARC grid",
    "exactly three same-colour 4-connected blobs with an 8-neighbour moat",
    "the three blob colours are distinct and identify one declared palette",
    "normalized occupancy includes support counts one, two, and three",
    "at least two normalized blob shapes differ",
]

# Each profile is a tuple of three connected masks inside a 3x3 box.  Every
# profile contains singleton, exactly-two, and all-three normalized support.
_SHAPE_TRIPLETS = (
    (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
    ),
    (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
)


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(name for name in overrides if name not in AXES)
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    for name, low, high in (("grid_h", 7, 14), ("grid_w", 11, 18)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"{name} must be in {low}..{high}")
    value = overrides.get("palette_kind")
    if value is not None:
        if type(value) is not str:
            raise TypeError("palette_kind must be a string")
        if value not in PALETTE_KINDS:
            raise ValueError("palette_kind must be one of " + ", ".join(PALETTE_KINDS))


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    _validate_call(seed, sample_index, difficulty, {})
    return sample_index % len(_SHAPE_TRIPLETS)


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _transform(shape, code: int):
    cells = set(shape)
    if code >= 4:
        cells = {(r, -c) for r, c in cells}
    for _ in range(code % 4):
        cells = {(c, -r) for r, c in cells}
    return _normalize(cells)


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _support_counts_from_components(comps) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = {}
    for component in comps:
        for cell in component["norm"]:
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def _scheduled_dimensions(sample_index: int, difficulty) -> tuple[int, int]:
    bands = {
        None: ((8, 11), (12, 16)),
        "easy": ((7, 9), (11, 14)),
        "medium": ((8, 11), (12, 16)),
        "hard": ((10, 14), (15, 18)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    h = h0 + (sample_index * 3 + 1) % (h1 - h0 + 1)
    w = w0 + (sample_index * 5 + 2) % (w1 - w0 + 1)
    return h, w


def _draw_axis(ctx, overrides, name: str, scheduled, low, high):
    if overrides.get(name) is None:
        return ctx.draw_int(name, scheduled, scheduled)
    return ctx.draw_int(name, low, high)


def _draw_palette(ctx, overrides, scheduled: str) -> str:
    if overrides.get("palette_kind") is None:
        return str(ctx.draw_choice("palette_kind", (scheduled,)))
    return str(ctx.draw_choice("palette_kind", PALETTE_KINDS))


def _place_triplet(h: int, w: int, shapes, colors, rng) -> list[list[int]]:
    # The shape bank is at most 3 cells wide.  These three shelves leave a full
    # zero column between blobs even at the 11-column lower boundary.
    starts = [0, (w - 3) // 2, w - 3]
    order = [0, 1, 2]
    rng.shuffle(order)
    grid = full_grid(h, w, 0)
    for slot, shape_index in enumerate(order):
        shape = shapes[shape_index]
        sh, sw = _shape_dims(shape)
        left = starts[slot] + (3 - sw) // 2
        top = rng.randint(0, h - sh)
        paint_at(grid, top, left, shape, colors[shape_index])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the registered Racket rule owns labels."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_dimensions(sample_index, difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", scheduled_h, 7, 14)
    w = _draw_axis(ctx, overrides, "grid_w", scheduled_w, 11, 18)
    scheduled_palette = PALETTE_KINDS[sample_index % len(PALETTE_KINDS)]
    palette_kind = _draw_palette(ctx, overrides, scheduled_palette)
    rng = ctx.draw_rng("layout")

    profile = _SHAPE_TRIPLETS[schedule_profile(seed, sample_index, difficulty)]
    code = rng.randrange(8)
    shapes = [_transform(shape, code) for shape in profile]
    colors = list(_PALETTES[palette_kind])
    rng.shuffle(colors)
    grid = _place_triplet(h, w, shapes, colors, rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid majority-overlay scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, requested in overrides.items():
        if requested is not None and observed.get(axis) != requested:
            raise RuntimeError(
                f"axis realization mismatch for {axis}: requested {requested!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return [row[:] for row in grid]


def _crop_to_content(grid: list[list[int]]) -> list[list[int]]:
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not occupied:
        raise ValueError("overlay has no nonzero content")
    r1 = min(r for r, _ in occupied)
    r2 = max(r for r, _ in occupied)
    c1 = min(c for _, c in occupied)
    c2 = max(c for _, c in occupied)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _overlay(grid: Any, threshold: int) -> list[list[int]]:
    comps = components(grid)
    if len(comps) != 3:
        raise ValueError("expected exactly three blobs")
    counts = _support_counts_from_components(comps)
    height = max(r for r, _ in counts) + 1
    width = max(c for _, c in counts) + 1
    output = [
        [8 if counts.get((r, c), 0) >= threshold else 0 for c in range(width)]
        for r in range(height)
    ]
    return _crop_to_content(output)


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for focused tests; Racket remains label authority."""
    return _overlay(grid, 2)


def observe_overrides(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"grid_h": 0, "grid_w": 0, "palette_kind": None}
    colors = frozenset(value for row in grid for value in row if type(value) is int and value != 0)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid and isinstance(grid[0], (list, tuple)) else 0,
        "palette_kind": _PALETTE_BY_SET.get(colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangle"]
    if not all(isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["grid must be a non-empty rectangle"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 14 or not 11 <= width <= 18:
        errors.append(f"grid dimensions {height}x{width} outside 7..14 by 11..18")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be exact integer ARC colors in 0..9")
        return errors
    comps = components(grid)
    if len(comps) != 3:
        errors.append(f"expected exactly 3 isolated blobs, got {len(comps)}")
        return errors
    if len({component["color"] for component in comps}) != 3:
        errors.append("the three blobs must have distinct colors")
    if not components_have_clearance(grid, comps):
        errors.append("blobs must have an eight-neighbour zero moat")
    if any(not 4 <= len(component["cells"]) <= 6 for component in comps):
        errors.append("each blob must contain 4..6 cells")
    support = _support_counts_from_components(comps)
    if set(support.values()) != {1, 2, 3}:
        errors.append("normalized support must contain single, pair, and triple cells")
    if len({component["norm"] for component in comps}) < 2:
        errors.append("at least two normalized shapes must differ")
    if frozenset(component["color"] for component in comps) not in _PALETTE_BY_SET:
        errors.append("blob colors must identify one declared palette kind")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    shape = (len(grid), len(grid[0]))
    if shape not in {(8, 12), (8, 13), (9, 14)}:
        return [f"dimension profile {shape} is not canonical"]
    sizes = sorted(len(component["cells"]) for component in components(grid))
    if sizes not in ([4, 5, 5], [5, 5, 5]):
        return [f"component sizes {sizes} are not canonical"]
    return []


def _rival_union(grid):
    return _overlay(grid, 1)


def _rival_unanimous(grid):
    return _overlay(grid, 3)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "union_of_normalized_shapes": _rival_union,
    "unanimous_only": _rival_unanimous,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "single_support_refutes_union": lambda grid: 1 in _support_counts_from_components(components(grid)).values(),
    "pair_support_refutes_unanimity": lambda grid: 2 in _support_counts_from_components(components(grid)).values(),
    "triple_support_present": lambda grid: 3 in _support_counts_from_components(components(grid)).values(),
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} input outside grammar: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with majority overlay")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            suffix = "and query" if rival(query["input"]) == query["output"] else "but changes query"
            reasons.append(f"shortcut {name!r} fits every demo {suffix}")
    return reasons
