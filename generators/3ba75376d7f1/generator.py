"""Semantic generator for ARC task 342dd610 / content hash 3ba75376d7f1.

Every non-background dot moves by a fixed color-coded vector:
7 moves two rows up, 2 moves two columns left, 9 moves two rows down,
and 1 moves one column right.  The original dots disappear.

The default sample-index schedule deliberately mirrors the official teaching
structure while also adding mixed-color lessons.  In a standard episode,
sample indices 0..2 expose all four color rules before index 3 asks for a
mixed-color query.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ba75376d7f1"
TASK_ID = "3ba75376d7f1"
VERSION = "3.0.0"
RULE_HASH = "64565f984008"

SUMMARY = (
    "On an 8-background grid, erase every isolated colored dot and repaint it "
    "at its color-specific destination: 7 up two, 2 left two, 9 down two, "
    "and 1 right one. Generated lessons keep all destinations in bounds, "
    "unique, and separate from every source dot."
)

INVARIANTS = [
    "8 is the unique modal background",
    "all non-8 cells are isolated singleton dots colored only 1, 2, 7, or 9",
    "each dot's color-specific destination is in bounds",
    "destinations are pairwise unique and never coincide with a source dot",
    "the sample-index 0..2 demonstrations expose every color used by the mixed sample-index 3 query",
]

SHIFT = {7: (-2, 0), 2: (0, -2), 9: (2, 0), 1: (0, 1)}
_ALLOWED_COLORS = frozenset(SHIFT)

# These are the only free exact axes. Color composition and placement style are
# a deterministic pedagogical schedule, not caller-controlled pseudo-axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile/difficulty schedule",
        "valid": "6..16",
        "doc": "Returned grid height; explicit overrides are valid across every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "profile/difficulty schedule",
        "valid": "6..16",
        "doc": "Returned grid width; explicit overrides are valid across every difficulty band.",
    },
    "n_marks": {
        "type": "int",
        "default": "profile/difficulty schedule",
        "valid": "1..10",
        "doc": "Exact number of colored source dots. A singleton is restricted to the official 10x10 color-9 profile.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Eight deterministic profile slots. The first four are episode-critical:
# demos 0 and 1 teach 7/2, demo 2 teaches 9/1, and query 3 combines all four.
_PROFILE_NAMES = (
    "canonical_train_7",
    "canonical_train_2",
    "mixed_9_1",
    "canonical_test_mix",
    "canonical_train_9",
    "canonical_train_1",
    "vertical_pair",
    "horizontal_pair",
)

_CANONICAL_TEST_COUNTS = Counter({9: 3, 2: 3, 7: 2, 1: 2})
_CANONICAL_TRAIN_COUNTS = {
    7: 2,
    2: 2,
    9: 1,
    1: 2,
}


def _is_arc_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty row sequence"], "facts": None}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty"], "facts": None}

    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if not (6 <= h <= 16 and 6 <= w <= 16):
        errors.append(f"grid dimensions must be within 6..16, got {h}x{w}")
    if any(not _is_arc_int(value) for row in grid for value in row):
        errors.append("all cells must be literal ARC integers 0..9")
        return {"errors": errors, "facts": None}

    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    if counts[8] <= max((count for color, count in counts.items() if color != 8), default=0):
        errors.append("8 must be the unique modal background")

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 8
    ]
    n_marks = len(markers)
    if not 1 <= n_marks <= 10:
        errors.append(f"marker count must be within 1..10, got {n_marks}")

    bad_colors = sorted({value for _, _, value in markers if value not in _ALLOWED_COLORS})
    if bad_colors:
        errors.append(f"marker colors must be a subset of {{1,2,7,9}}, got {bad_colors}")

    sources = {(r, c) for r, c, _ in markers}
    if len(sources) != n_marks:
        errors.append("source-dot coordinates must be unique")

    # Official dots are isolated even diagonally; this rejects lines, blocks,
    # and connected texture shortcuts while preserving every canonical input.
    for i, (r, c, _) in enumerate(markers):
        for rr, cc, _ in markers[i + 1 :]:
            if max(abs(r - rr), abs(c - cc)) <= 1:
                errors.append("colored dots must be isolated under 8-connectivity")
                break
        if errors and errors[-1].startswith("colored dots"):
            break

    targets: list[tuple[int, int]] = []
    if not bad_colors:
        for r, c, color in markers:
            dr, dc = SHIFT[color]
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                errors.append(f"color {color} at ({r},{c}) shifts out of bounds")
            targets.append((nr, nc))
        if len(set(targets)) != len(targets):
            errors.append("shifted destinations must be pairwise unique")
        if set(targets) & sources:
            errors.append("shifted destinations must not coincide with source dots")

    palette_counts = Counter(value for _, _, value in markers)
    if n_marks == 1 and not (
        h == 10 and w == 10 and palette_counts == Counter({9: 1})
    ):
        errors.append("the only lawful singleton lesson is the official 10x10 color-9 profile")

    facts = {
        "height": h,
        "width": w,
        "markers": markers,
        "n_marks": n_marks,
        "palette_counts": palette_counts,
        "sources": sources,
        "targets": targets,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-specific lesson grammar, not merely palette/shape."""
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, int]:
    """Expose exact semantic axes recoverable from the returned grid."""
    analysis = _analysis(grid)
    facts = analysis["facts"]
    return {"n_marks": facts["n_marks"]} if facts is not None and not analysis["errors"] else {}


def canonical_profile_signature(grid) -> str | None:
    """Return the strict empirical-manifold profile, if any.

    This helper is descriptive only; review censuses use an independent
    extractor over returned grids.
    """
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    h, w = facts["height"], facts["width"]
    counts = facts["palette_counts"]
    if h == w == 10 and len(counts) == 1:
        color, count = next(iter(counts.items()))
        if _CANONICAL_TRAIN_COUNTS.get(color) == count:
            return f"canonical_train_{color}"
    if h == w == 16 and counts == _CANONICAL_TEST_COUNTS:
        return "canonical_test_mix"
    return None


def _draw_axis_int(ctx, label: str, default_lo: int, default_hi: int, global_lo: int, global_hi: int) -> int:
    """Use the full declared domain for explicit overrides, band/profile bounds otherwise."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, global_lo, global_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _general_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 9), (6, 9), (4, 4)
    if difficulty == "hard":
        return (11, 16), (11, 16), (6, 10)
    return (8, 13), (8, 13), (4, 6)


def _profile_defaults(profile: str, difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if profile in {"canonical_train_7", "canonical_train_2", "canonical_train_9", "canonical_train_1"}:
        count = {"canonical_train_7": 2, "canonical_train_2": 2, "canonical_train_9": 1, "canonical_train_1": 2}[profile]
        return (10, 10), (10, 10), (count, count)
    if profile == "canonical_test_mix":
        return (16, 16), (16, 16), (10, 10)
    return _general_ranges(difficulty)


def _color_plan(profile: str, n_marks: int, rng) -> list[int]:
    if n_marks == 1:
        return [9]
    if profile == "canonical_train_7":
        colors = [7] * n_marks
    elif profile == "canonical_train_2":
        colors = [2] * n_marks
    elif profile == "canonical_train_9":
        colors = [9] * n_marks
    elif profile == "canonical_train_1":
        colors = [1] * n_marks
    elif profile == "mixed_9_1":
        colors = [9 if i % 2 == 0 else 1 for i in range(n_marks)]
    elif profile == "vertical_pair":
        colors = [7 if i % 2 == 0 else 9 for i in range(n_marks)]
    elif profile == "horizontal_pair":
        colors = [2 if i % 2 == 0 else 1 for i in range(n_marks)]
    elif n_marks == 10:
        colors = [9, 9, 9, 2, 2, 2, 7, 7, 1, 1]
    else:
        cycle = [7, 2, 9, 1]
        colors = [cycle[i % len(cycle)] for i in range(n_marks)]
    rng.shuffle(colors)
    return colors


def _candidate_positions(h: int, w: int, color: int) -> list[tuple[int, int]]:
    dr, dc = SHIFT[color]
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def _place_markers(h: int, w: int, colors: list[int], rng, style: int) -> list[tuple[int, int, int]]:
    """Greedily place isolated sources with unique, source-disjoint targets."""
    for _attempt in range(256):
        placed: list[tuple[int, int, int]] = []
        sources: set[tuple[int, int]] = set()
        targets: set[tuple[int, int]] = set()
        success = True
        for color in colors:
            candidates = _candidate_positions(h, w, color)
            rng.shuffle(candidates)
            if style == 0:  # edge-aware
                candidates.sort(key=lambda rc: min(rc[0], h - 1 - rc[0], rc[1], w - 1 - rc[1]))
            elif style == 1:  # interior-aware
                candidates.sort(key=lambda rc: -min(rc[0], h - 1 - rc[0], rc[1], w - 1 - rc[1]))
            elif style == 2:  # diagonal spread
                candidates.sort(key=lambda rc: (abs(rc[0] - rc[1]), rc[0] + rc[1]))
            selected = None
            dr, dc = SHIFT[color]
            for r, c in candidates:
                target = (r + dr, c + dc)
                if (r, c) in sources or (r, c) in targets or target in sources or target in targets:
                    continue
                if any(max(abs(r - rr), abs(c - cc)) <= 1 for rr, cc in sources):
                    continue
                selected = (r, c, color)
                break
            if selected is None:
                success = False
                break
            r, c, color = selected
            dr, dc = SHIFT[color]
            placed.append(selected)
            sources.add((r, c))
            targets.add((r + dr, c + dc))
        if success:
            return placed
    raise ValueError(
        f"incompatible dimensions/count: cannot place {len(colors)} isolated dots on {h}x{w} "
        "with unique source-disjoint destinations"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _profile_defaults(profile, difficulty)

    explicit_n = overrides.get("n_marks")
    if explicit_n is not None and int(explicit_n) >= 8:
        # A large requested count gets enough default canvas unless dimensions
        # were explicitly pinned; incompatible explicit combinations reject later.
        h_lo, h_hi = max(h_lo, 8), max(h_hi, 8)
        w_lo, w_hi = max(w_lo, 8), max(w_hi, 8)
    if explicit_n is not None and int(explicit_n) == 1:
        if overrides.get("grid_h") is None:
            h_lo = h_hi = 10
        if overrides.get("grid_w") is None:
            w_lo = w_hi = 10

    h = _draw_axis_int(ctx, "grid_h", h_lo, h_hi, 6, 16)
    w = _draw_axis_int(ctx, "grid_w", w_lo, w_hi, 6, 16)

    if profile == "canonical_train_9" and explicit_n is None and (h, w) != (10, 10):
        n_lo = n_hi = 2
    n_marks = _draw_axis_int(ctx, "n_marks", n_lo, n_hi, 1, 10)
    if n_marks == 1 and (h, w) != (10, 10):
        raise ValueError("n_marks=1 is compatible only with the official 10x10 color-9 lesson profile")

    rng = ctx.draw_rng("placement")
    colors = _color_plan(profile, n_marks, rng)
    markers = _place_markers(h, w, colors, rng, sample_index % 4)

    grid = full_grid(h, w, 8)
    for r, c, color in markers:
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid
