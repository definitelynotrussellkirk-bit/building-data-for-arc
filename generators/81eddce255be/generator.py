"""Generator for 81eddce255be — select the blob whose area matches a header count.

The first row contains K blue (1) cells.  A blank separator row follows.
Exactly three differently colored, four-connected body objects appear below the
separator at distinct areas; exactly one has area K.  The output erases the
header and all distractors, retaining only the area-K object in place.

This implementation is deliberately constructive.  Public axes are recovered
from returned pixels, every documented boundary is legal in every difficulty
band, and the default three-example schedule includes a non-topmost target so
that the strongest shortcut fitting the public demonstrations is refuted.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81eddce255be"
TASK_ID = GENERATOR_ID
RULE_HASH = "70441dae68b0"
VERSION = "3.0.0"
SUMMARY = (
    "Count the blue cells in the first row. Keep the unique body object with "
    "that many cells, preserving its color and position; erase the header and "
    "the other two objects."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the background is 0 and the first row contains one contiguous run of K blue (1) cells",
    "row 1 is an all-zero separator and no blue marker appears below row 0",
    "the body contains exactly three separated same-color 4-connected objects",
    "the three object colors and three object areas are pairwise distinct",
    "exactly one body object has area K",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile 10, 11, or 12",
        "valid": "10..14",
        "doc": "Returned grid height; every value is constructive in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile 10, 11, or 12",
        "valid": "10..14",
        "doc": "Returned grid width; every value is constructive in every band.",
    },
    "K": {
        "type": "int",
        "default": "scheduled 2..6",
        "valid": "2..6",
        "doc": "Number of blue header markers and target-object area.",
    },
    "target_rank": {
        "type": "int",
        "default": "scheduled 0..2",
        "valid": "0..2",
        "doc": "Row-major rank of the unique area-K body object.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
_ALLOWED_DIFFICULTIES = frozenset((None, "easy", "medium", "hard"))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = ((10, 10), (11, 11), (12, 12))

# The size schedule is aligned with sample_index % 3, which is the desired
# target size-rank (smallest, middle, largest).  Across one period it covers
# every K in 2..6 while retaining two distinct legal distractor sizes.
_DEFAULT_K = (2, 3, 4, 3, 4, 5, 4, 5, 6, 5, 6, 3, 2, 4, 6)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot normalize an empty shape")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _build_shape_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All normalized connected subsets of a 2x4 box, grouped by area."""
    box = tuple((r, c) for r in range(2) for c in range(4))
    result: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(1, 8):
        shapes = {
            _normalize(combo)
            for combo in combinations(box, size)
            if _is_connected(combo)
        }
        result[size] = tuple(sorted(shapes))
    return result


_SHAPES_BY_SIZE = _build_shape_bank()


def _basic_grid_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9"
    return None


def _body_components(grid) -> list[dict[str, object]]:
    """Same-color four-connected components below the header, in row-major order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for start_r in range(1, h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    result.sort(key=lambda obj: min(obj["cells"]))
    return result


def _inspect_scene(grid):
    """Return recovered facts and findings; never raise for malformed grids."""
    first = _basic_grid_error(grid)
    if first:
        return None, [first]

    h, w = len(grid), len(grid[0])
    findings: list[str] = []
    if not 10 <= h <= 14:
        findings.append(f"grid height {h} outside 10..14")
    if not 10 <= w <= 14:
        findings.append(f"grid width {w} outside 10..14")

    if any(value not in (0, 1) for value in grid[0]):
        findings.append("row 0 header may contain only background 0 and blue 1")
    marker_columns = [c for c, value in enumerate(grid[0]) if value == 1]
    k = len(marker_columns)
    if not 2 <= k <= 6:
        findings.append(f"row 0 header has K={k} blue cells; expected 2..6")
    elif marker_columns != list(range(marker_columns[0], marker_columns[0] + k)):
        findings.append("row 0 header markers must form one contiguous horizontal run")
    if h >= 2 and any(value != 0 for value in grid[1]):
        findings.append("row 1 separator must be all background 0")
    if any(value == 1 for row in grid[1:] for value in row):
        findings.append("blue header marker 1 appears below row 0")

    components = _body_components(grid)
    if len(components) != 3:
        findings.append(f"expected exactly three body objects, got {len(components)}")

    body_colors = [int(obj["color"]) for obj in components]
    if any(color not in range(2, 10) for color in body_colors):
        findings.append("body object colors must be distinct values from 2..9")
    if len(set(body_colors)) != len(body_colors):
        findings.append("body object colors must be pairwise distinct")

    sizes = [len(obj["cells"]) for obj in components]
    if any(not 1 <= size <= 7 for size in sizes):
        findings.append(f"body object areas must lie in 1..7, got {sizes}")
    if len(set(sizes)) != len(sizes):
        findings.append(f"body object areas must be pairwise distinct, got {sizes}")

    matches = [index for index, size in enumerate(sizes) if size == k]
    if len(matches) != 1:
        findings.append(f"expected exactly one area-K object, got {len(matches)}")

    # Different colors are separate components even when they touch, so check
    # the intended one-cell visual separation explicitly.
    owners = {
        cell: index
        for index, obj in enumerate(components)
        for cell in obj["cells"]
    }
    touching = False
    for (r, c), owner in owners.items():
        for dr, dc in _CARDINAL:
            other = owners.get((r + dr, c + dc))
            if other is not None and other != owner:
                touching = True
                break
        if touching:
            break
    if touching:
        findings.append("body objects must not touch cardinally")

    facts = None
    if not findings:
        facts = {
            "grid_h": h,
            "grid_w": w,
            "K": k,
            "target_rank": matches[0],
            "components": tuple(components),
        }
    return facts, findings


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, findings = _inspect_scene(grid)
    return findings


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _require_scene(grid):
    facts, findings = _inspect_scene(grid)
    if findings:
        raise ValueError("invalid task grid: " + "; ".join(findings[:4]))
    return facts


def observe_overrides(grid) -> dict[str, int]:
    facts = _require_scene(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "K": facts["K"],
        "target_rank": facts["target_rank"],
    }


def oracle_output(grid):
    """Independent Python mirror of the selected rule; does not mutate input."""
    facts = _require_scene(grid)
    out = full_grid(facts["grid_h"], facts["grid_w"], 0)
    target = facts["components"][facts["target_rank"]]
    for r, c in target["cells"]:
        out[r][c] = target["color"]
    return out


def _topmost_object(grid):
    """Plausible but wrong rule: preserve the first body object row-major."""
    facts = _require_scene(grid)
    out = full_grid(facts["grid_h"], facts["grid_w"], 0)
    topmost = facts["components"][0]
    for r, c in topmost["cells"]:
        out[r][c] = topmost["color"]
    return out


def _non_topmost_target(grid) -> bool:
    return observe_overrides(grid)["target_rank"] != 0


SEMANTIC_WITNESSES = {"non_topmost_target": _non_topmost_target}
SEMANTIC_RIVALS = {"topmost_object": _topmost_object}
WITNESS_RIVALS = {"non_topmost_target": ["topmost_object"]}
CANONICAL_SHORTCUTS = {"topmost_object": _topmost_object}
LESSON_COMPETITORS = {"topmost_object": _topmost_object}


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")


def _draw_scheduled_int(ctx, overrides, label, lo, hi, default):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    # Record the scheduled value in public provenance without pretending the
    # default was a random draw over a wider domain.
    return ctx.draw_choice(label, (default,))


def _default_target_rank(sample_index: int) -> int:
    # Over nine samples this crosses every (size-rank, row-rank) pair exactly
    # once, preventing either rank from serving as a proxy for the other.
    return (2 * sample_index + sample_index // 3 + 1) % 3


def _distractor_sizes(k: int, desired_target_size_rank: int) -> tuple[int, int]:
    if desired_target_size_rank == 0 and k <= 5:
        return k + 1, k + 2
    if desired_target_size_rank == 2 and k >= 3:
        return k - 2, k - 1
    # Middle rank is legal for every supported K.  Put the larger distractor
    # first; this also makes shrink-to-K validator mutations deterministic.
    return k + 1, k - 1


def _slot_starts(h: int) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        combo
        for combo in combinations(range(2, h - 1), 3)
        if combo[1] - combo[0] >= 3 and combo[2] - combo[1] >= 3
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _CANONICAL_PROFILES[sample_index % len(_CANONICAL_PROFILES)]
    h = _draw_scheduled_int(ctx, overrides, "grid_h", 10, 14, default_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 10, 14, default_w)
    k = _draw_scheduled_int(
        ctx,
        overrides,
        "K",
        2,
        6,
        _DEFAULT_K[sample_index % len(_DEFAULT_K)],
    )
    target_rank = _draw_scheduled_int(
        ctx,
        overrides,
        "target_rank",
        0,
        2,
        _default_target_rank(sample_index),
    )

    grid = full_grid(h, w, 0)
    # Difficulty changes only nuisance placement, never the four public facts.
    # The offset makes all three named bands observably distinct even when the
    # keyed base draw happens to collide.
    band_offset = {"easy": 0, "medium": 1, "hard": 2, None: 3}[difficulty]
    start_options = w - k + 1
    header_start = (ctx.draw_rng("header_start").randrange(start_options) + band_offset) % start_options
    for c in range(header_start, header_start + k):
        grid[0][c] = 1

    desired_size_rank = sample_index % 3
    distractors = list(_distractor_sizes(k, desired_size_rank))
    slot_sizes: list[int] = []
    for rank in range(3):
        slot_sizes.append(k if rank == target_rank else distractors.pop(0))

    starts = ctx.draw_rng("vertical_slots").choice(_slot_starts(h))
    colors = ctx.draw_rng("body_colors").sample(list(range(2, 10)), 3)
    for rank, (start_r, size, color) in enumerate(zip(starts, slot_sizes, colors)):
        shape = ctx.draw_rng(f"shape_{rank}").choice(_SHAPES_BY_SIZE[size])
        shape_w = max(c for _, c in shape) + 1
        start_c = ctx.draw_rng(f"horizontal_slot_{rank}").randint(0, w - shape_w)
        for dr, dc in shape:
            grid[start_r + dr][start_c + dc] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    return grid
