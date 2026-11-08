"""Curriculum generator for ARC task ``5ffd8d801705``.

Every solid monochrome 2x2 square is replaced by its main diagonal.  The
canonical program also preserves nonzero cells that are not part of a square;
this generator deliberately emits the cleaner all-squares grammar while its
``rule_mirror`` implements the full canonical behavior.

The previous generator placed every square on anchors ``(3i, 3j)``.  A global
coordinate mask therefore solved every generated example without finding
objects.  Repaired default scenes include an edge square, anchors from multiple
modulo-3 classes, and both checkerboard parities in every draw.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Anchor = tuple[int, int]

GENERATOR_ID = "5ffd8d801705"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "c845504525a2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Place distinct-color solid 2x2 squares at non-overlapping arbitrary "
    "anchors, including edge and mixed coordinate-residue witnesses. Replace "
    "each square by its top-left/bottom-right diagonal and preserve all other "
    "cells."
)

INVARIANTS = [
    "background is color 0",
    "each nonzero color forms exactly one solid 2x2 square",
    "squares do not overlap and use distinct colors",
    "default draws contain edge, modulo-3, and checkerboard shortcut witnesses",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 6..14", "valid": "4..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 6..14", "valid": "4..14"},
    "n_blocks": {"type": "int", "default": "difficulty-aware 3..8", "valid": "1..8"},
}

# The exact packing capacity depends jointly on all three axes.  Generation
# rejects an impossible request with a concrete ValueError instead of silently
# drawing fewer objects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIFFICULTY_BANDS = {
    None: ((6, 12), (6, 12), (3, 6)),
    "easy": ((6, 8), (6, 8), (3, 4)),
    "medium": ((8, 11), (8, 11), (4, 6)),
    "hard": ((10, 14), (10, 14), (5, 8)),
}


def _validate_public_controls(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTY_BANDS:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _draw_axis_int(
    ctx,
    label: str,
    *,
    default: tuple[int, int],
    legal: tuple[int, int],
    overrides: dict[str, Any],
) -> int:
    """Honor any legal override independent of the selected difficulty band."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, legal[0], legal[1])
    return ctx.draw_int_strict(label, default[0], default[1])


def _cells(anchor: Anchor) -> frozenset[tuple[int, int]]:
    r, c = anchor
    return frozenset(((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)))


def _is_edge(anchor: Anchor, h: int, w: int) -> bool:
    r, c = anchor
    return r in (0, h - 2) or c in (0, w - 2)


def _witness_complete(anchors: Sequence[Anchor], h: int, w: int) -> bool:
    if not anchors:
        return False
    if not any(_is_edge(anchor, h, w) for anchor in anchors):
        return False
    if not any(r % 3 != c % 3 for r, c in anchors):
        return False
    if len(anchors) == 1:
        return True
    return (
        len({(r % 3, c % 3) for r, c in anchors}) >= 2
        and {(r + c) % 2 for r, c in anchors} == {0, 1}
    )


def _choose_anchors(h: int, w: int, n: int, rng) -> list[Anchor]:
    """Find exactly ``n`` disjoint anchors while forcing shortcut witnesses."""
    capacity = (h // 2) * (w // 2)
    if n > capacity:
        raise ValueError(
            f"cannot fit {n} non-overlapping 2x2 blocks in {h}x{w}; "
            f"packing capacity is {capacity}"
        )

    candidates = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    requirements: tuple[Callable[[Anchor], bool], ...] = (
        lambda anchor: _is_edge(anchor, h, w),
        lambda anchor: anchor[0] % 3 != anchor[1] % 3,
    )
    if n >= 2:
        requirements += (
            lambda anchor: (anchor[0] + anchor[1]) % 2 == 0,
            lambda anchor: (anchor[0] + anchor[1]) % 2 == 1,
        )

    # Randomized greedy is deterministic because ``rng`` is keyed by the
    # generator context.  Repeated orderings avoid a bad early edge choice from
    # reducing an otherwise feasible packing.
    for _ in range(512):
        order = candidates[:]
        rng.shuffle(order)
        selected: list[Anchor] = []
        occupied: set[tuple[int, int]] = set()

        reqs = list(requirements)
        rng.shuffle(reqs)
        failed = False
        for predicate in reqs:
            if any(predicate(anchor) for anchor in selected):
                continue
            choices = [
                anchor
                for anchor in order
                if predicate(anchor) and not (_cells(anchor) & occupied)
            ]
            if not choices:
                failed = True
                break
            anchor = choices[0]
            selected.append(anchor)
            occupied.update(_cells(anchor))
        if failed or len(selected) > n:
            continue

        for anchor in order:
            if len(selected) == n:
                break
            if anchor in selected or (_cells(anchor) & occupied):
                continue
            selected.append(anchor)
            occupied.update(_cells(anchor))

        if len(selected) == n and _witness_complete(selected, h, w):
            return selected

    raise ValueError(
        f"cannot place {n} blocks in {h}x{w} while preserving the declared "
        "edge and coordinate-residue teaching witnesses"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_public_controls(seed, sample_index, difficulty, overrides)
    h_band, w_band, n_band = _DIFFICULTY_BANDS[difficulty]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_axis_int(ctx, "grid_h", default=h_band, legal=(4, 14), overrides=overrides)
    w = _draw_axis_int(ctx, "grid_w", default=w_band, legal=(4, 14), overrides=overrides)
    n = _draw_axis_int(ctx, "n_blocks", default=n_band, legal=(1, 8), overrides=overrides)

    try:
        anchors = _choose_anchors(h, w, n, ctx.draw_rng("layout"))
    except ValueError as exc:
        supplied_axes = tuple(
            name for name in ("grid_h", "grid_w", "n_blocks")
            if overrides.get(name) is not None
        )
        if len(supplied_axes) >= 2:
            exc.incompatible_axes = supplied_axes
        raise
    colors = ctx.draw_distinct_colors("colors", n=n, exclude={0})
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(anchors, colors, strict=True):
        for rr, cc in _cells((r, c)):
            grid[rr][cc] = color
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    if not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an integer color in 0..9"]
    return []


def _solid_blocks(grid: Grid) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    blocks: list[tuple[int, int, int]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            color = grid[r][c]
            if color and all(
                grid[rr][cc] == color
                for rr, cc in ((r, c + 1), (r + 1, c), (r + 1, c + 1))
            ):
                blocks.append((r, c, color))
    return blocks


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the emitted all-squares grammar without mutating ``grid``."""
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, []).append((r, c))
    if not by_color:
        return ["scene contains no solid 2x2 block"]

    for color, cells in sorted(by_color.items()):
        if len(cells) != 4:
            errors.append(f"color {color} occupies {len(cells)} cells instead of one 2x2 block")
            continue
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(rows) != 2 or len(cols) != 2:
            errors.append(f"color {color} does not form a 2x2 bounding box")
            continue
        r0, r1 = sorted(rows)
        c0, c1 = sorted(cols)
        if r1 != r0 + 1 or c1 != c0 + 1 or set(cells) != set(_cells((r0, c0))):
            errors.append(f"color {color} is not one solid 2x2 block")
    return errors


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected canonical Racket program."""
    if _grid_shape_errors(grid):
        raise ValueError("rule_mirror requires a nonempty rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    blocks = _solid_blocks(grid)
    used = {
        (rr, cc)
        for r, c, _ in blocks
        for rr, cc in _cells((r, c))
    }
    out = full_grid(h, w, 0)
    for r, c, color in blocks:
        out[r][c] = color
        out[r + 1][c + 1] = color
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color and (r, c) not in used:
                out[r][c] = color
    return out


def _global_mod3(grid: Grid) -> Grid:
    return [
        [value if value and r % 3 == c % 3 else 0 for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _global_checkerboard(grid: Grid) -> Grid:
    blocks = _solid_blocks(grid)
    if not blocks:
        return deepcopy(grid)
    parity = (blocks[0][0] + blocks[0][1]) % 2
    return [
        [value if value and (r + c) % 2 == parity else 0 for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


SEMANTIC_RIVALS = {
    "global_mod3": _global_mod3,
    "global_checkerboard": _global_checkerboard,
}
CANONICAL_SHORTCUTS: dict[str, object] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave either named shortcut alive."""
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} is structurally invalid: {structural[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"rival {name!r} survives every demonstration")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        structural = self_check(query["input"])
        if structural:
            reasons.append(f"query is structurally invalid: {structural[0]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the canonical rule")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, int]:
    """Recover the public axes from a generated grid for override audits."""
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blocks": len(_solid_blocks(grid)),
    }
