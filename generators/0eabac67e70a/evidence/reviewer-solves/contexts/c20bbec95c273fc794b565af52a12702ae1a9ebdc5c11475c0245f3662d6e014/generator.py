"""Constructive sampler for pair-defined cyan spans (task 0eabac67e70a).

Every non-background color occurs at exactly two endpoints.  The selected
Racket authority paints the inclusive row, column, or perfect 45-degree span
between each pair onto an otherwise empty grid using cyan (8).
"""
from __future__ import annotations

from collections import Counter, defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0eabac67e70a"
TASK_ID = GENERATOR_ID
RULE_HASH = "4a7acff260a8"
VERSION = "2.0.0"
SUMMARY = (
    "One to four disjoint endpoint pairs define inclusive cyan spans. "
    "Axis-aligned lessons include the canonical two-pair crossing profile; "
    "perfect 45-degree diagonal variants exercise the same pinned authority."
)

INVARIANTS = [
    "background is 0 and endpoint colors exclude output color 8",
    "each non-zero endpoint color occurs exactly twice",
    "all pairs in one input are either axis-aligned or perfect 45-degree diagonals",
    "each pair has at least one interior span cell",
    "generation places every requested pair constructively without retry truncation",
]

LOW_COLORS = (1, 2, 3, 4)
HIGH_COLORS = (5, 6, 7, 9)
ORIENTATION_FAMILIES = ("axis_aligned", "diagonal")
PALETTE_KINDS = ("low", "high")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-size weighted by difficulty",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-size weighted by difficulty",
        "valid": "7..13",
    },
    "n_pairs": {
        "type": "int",
        "default": "weighted toward canonical 2",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng low|high",
        "valid": "low|high",
    },
    "orientation_family": {
        "type": "str",
        "default": "weighted axis_aligned with diagonal coverage",
        "valid": "axis_aligned|diagonal",
    },
}

# The constructor supports the full Cartesian product of the declared domains.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_request(seed, sample_index, difficulty, overrides: dict) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be one of easy, medium, hard, or None; got {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_pairs"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    for name in ("palette_kind", "orientation_family"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")


def _profile_size(ctx, difficulty):
    choices = {
        "easy": (9, 9, 9, 10),
        "medium": (9, 10, 10, 11),
        "hard": (10, 11, 11, 11),
    }.get(difficulty, (9, 10, 10, 11))
    return ctx.draw_choice("profile_size", choices)


def _weighted_int(ctx, name, lo, hi, anchor, *, extras=()):
    # Repetition affects only the default distribution.  Every documented
    # override remains a member of the complete domain and is therefore valid.
    choices = list(range(lo, hi + 1)) + [anchor] * 64 + list(extras)
    return ctx.draw_choice(name, choices)


def _pair_count(ctx, difficulty):
    extras = {
        "easy": (1, 2, 2, 2),
        "medium": (2, 2, 3),
        "hard": (2, 3, 3, 4, 4),
    }.get(difficulty, (1, 2, 2, 3, 4))
    return _weighted_int(ctx, "n_pairs", 1, 4, 2, extras=extras)


def _cross_segments(h, w, rng):
    """Return a horizontal then vertical segment crossing away from endpoints."""
    center_r = rng.randint(2, h - 3)
    center_c = rng.randint(2, w - 3)
    left = rng.randint(1, center_c - 1)
    right = rng.randint(center_c + 1, w - 2)
    top = rng.randint(1, center_r - 1)
    bottom = rng.randint(center_r + 1, h - 2)
    return (
        ((center_r, left), (center_r, right)),
        ((top, center_c), (bottom, center_c)),
    )


def _axis_candidates(h, w):
    candidates = []
    for r in range(h):
        for c1 in range(w - 2):
            for c2 in range(c1 + 2, w):
                candidates.append(((r, c1), (r, c2)))
    for c in range(w):
        for r1 in range(h - 2):
            for r2 in range(r1 + 2, h):
                candidates.append(((r1, c), (r2, c)))
    return candidates


def _diagonal_candidates(h, w):
    candidates = []
    for r in range(h):
        for c in range(w):
            for dr, dc in ((1, 1), (1, -1)):
                length = 2
                while 0 <= r + length * dr < h and 0 <= c + length * dc < w:
                    candidates.append(((r, c), (r + length * dr, c + length * dc)))
                    length += 1
    return candidates


def _select_disjoint(candidates, count, rng, *, used=()):
    """Select exactly count endpoint-disjoint segments or fail visibly."""
    ordered = list(candidates)
    rng.shuffle(ordered)
    occupied = set(used)
    chosen = []

    def search(start):
        if len(chosen) == count:
            return True
        needed = count - len(chosen)
        if len(ordered) - start < needed:
            return False
        for index in range(start, len(ordered)):
            first, second = ordered[index]
            if first in occupied or second in occupied:
                continue
            occupied.update((first, second))
            chosen.append((first, second))
            if search(index + 1):
                return True
            chosen.pop()
            occupied.remove(first)
            occupied.remove(second)
        return False

    if not search(0):
        raise RuntimeError("constructive segment placement unexpectedly had no solution")
    return tuple(chosen)


def _segments(ctx, h, w, n_pairs, family):
    rng = ctx.draw_rng("layout")
    if family == "diagonal":
        return _select_disjoint(_diagonal_candidates(h, w), n_pairs, rng)
    if n_pairs == 1:
        # Use the same interior construction as canonical crosses, then select
        # one arm.  This keeps a visible cell outside each endpoint.
        return (rng.choice(_cross_segments(h, w, rng)),)
    first = _cross_segments(h, w, rng)
    used = tuple(point for segment in first for point in segment)
    extras = _select_disjoint(
        _axis_candidates(h, w), n_pairs - 2, rng, used=used
    ) if n_pairs > 2 else ()
    return first + extras


def _colors(ctx, n_pairs, palette_kind, family):
    palette = list(LOW_COLORS if palette_kind == "low" else HIGH_COLORS)
    rng = ctx.draw_rng("colors")
    rng.shuffle(palette)
    if family == "axis_aligned" and n_pairs >= 2 and palette_kind == "low":
        # Canonical examples always use color 2 horizontally and color 3
        # vertically.  At most one of any three consecutive sample indices
        # repeats that shortcut, so ordinary lessons contain counterevidence.
        lead = [2, 3] if ctx.sample_index % 3 == 0 else [3, 2]
        tail = [color for color in palette if color not in lead]
        return tuple((lead + tail)[:n_pairs])
    return tuple(palette[:n_pairs])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    anchor = _profile_size(ctx, difficulty)
    h = _weighted_int(ctx, "grid_h", 7, 13, anchor)
    w = _weighted_int(ctx, "grid_w", 7, 13, anchor)
    n_pairs = _pair_count(ctx, difficulty)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    orientation_options = (
        "axis_aligned", "axis_aligned", "axis_aligned", "axis_aligned",
        "axis_aligned", "axis_aligned", "axis_aligned", "diagonal",
    )
    if difficulty == "hard":
        orientation_options += ("diagonal", "diagonal")
    family = ctx.draw_choice("orientation_family", orientation_options)

    segments = _segments(ctx, h, w, n_pairs, family)
    colors = _colors(ctx, n_pairs, palette_kind, family)
    grid = full_grid(h, w, 0)
    for color, (first, second) in zip(colors, segments):
        for r, c in (first, second):
            if grid[r][c] != 0:
                raise RuntimeError("constructive placement collided at an endpoint")
            grid[r][c] = color
    return grid


def _color_points(grid):
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                points[value].append((r, c))
    return points


def observe_overrides(grid):
    """Recover every advertised axis from returned pixels."""
    points = _color_points(grid)
    colors = set(points)
    if colors and colors <= set(LOW_COLORS):
        palette_kind = "low"
    elif colors and colors <= set(HIGH_COLORS):
        palette_kind = "high"
    else:
        raise ValueError("endpoint colors do not identify one declared palette kind")

    families = set()
    for cells in points.values():
        if len(cells) != 2:
            raise ValueError("every endpoint color must occur exactly twice")
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            families.add("axis_aligned")
        elif abs(r2 - r1) == abs(c2 - c1):
            families.add("diagonal")
        else:
            raise ValueError("pair is neither axis-aligned nor a perfect diagonal")
    if len(families) != 1:
        raise ValueError("input mixes declared orientation families")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(points),
        "palette_kind": palette_kind,
        "orientation_family": next(iter(families)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input manifold emitted by this sampler."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must contain nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    errors = []
    h = len(grid)
    if not 7 <= h <= 13:
        errors.append(f"grid_h={h} outside [7,13]")
    if not 7 <= width <= 13:
        errors.append(f"grid_w={width} outside [7,13]")
    if any(value == 8 for row in grid for value in row):
        errors.append("input endpoints must not use output color 8")

    counts = Counter(value for row in grid for value in row if value)
    if not 1 <= len(counts) <= 4:
        errors.append(f"expected 1..4 endpoint colors, found {len(counts)}")
    bad_counts = sorted(color for color, count in counts.items() if count != 2)
    if bad_counts:
        errors.append(f"colors with endpoint count != 2: {bad_counts}")
    colors = set(counts)
    if colors and not (colors <= set(LOW_COLORS) or colors <= set(HIGH_COLORS)):
        errors.append("endpoint colors must come entirely from low or high palette")

    families = set()
    points = _color_points(grid)
    for color, cells in sorted(points.items()):
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        distance = max(abs(r2 - r1), abs(c2 - c1))
        if distance < 2:
            errors.append(f"color {color} endpoints are adjacent or coincident")
        if r1 == r2 or c1 == c2:
            families.add("axis_aligned")
        elif abs(r2 - r1) == abs(c2 - c1):
            families.add("diagonal")
        else:
            errors.append(f"color {color} endpoints are not a clean span")
    if len(families) > 1:
        errors.append("input mixes axis-aligned and diagonal pair families")
    return errors


def strict_canonical_like(grid):
    """Recognize the canonical two-arm crossing manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if h != w or h not in (9, 10, 11):
        reasons.append("canonical profile is a 9x9, 10x10, or 11x11 square")
    points = _color_points(grid)
    if len(points) != 2:
        reasons.append("canonical profile has exactly two endpoint colors")
        return reasons
    horizontal = []
    vertical = []
    for cells in points.values():
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            horizontal.append((r1, min(c1, c2), max(c1, c2)))
        elif c1 == c2:
            vertical.append((c1, min(r1, r2), max(r1, r2)))
        else:
            reasons.append("canonical profile uses one horizontal and one vertical pair")
    if len(horizontal) != 1 or len(vertical) != 1:
        reasons.append("canonical profile uses one horizontal and one vertical pair")
        return reasons
    row, left, right = horizontal[0]
    col, top, bottom = vertical[0]
    if not (left < col < right and top < row < bottom):
        reasons.append("canonical pair spans cross away from their endpoints")
    return reasons


def _fixed_color_roles(grid):
    """Rival: assume color 2 is horizontal and color 3 is vertical."""
    out = full_grid(len(grid), len(grid[0]), 0)
    points = _color_points(grid)
    cells = points.get(2, ())
    if len(cells) == 2 and cells[0][0] == cells[1][0]:
        row = cells[0][0]
        for col in range(min(cells[0][1], cells[1][1]),
                         max(cells[0][1], cells[1][1]) + 1):
            out[row][col] = 8
    cells = points.get(3, ())
    if len(cells) == 2 and cells[0][1] == cells[1][1]:
        col = cells[0][1]
        for row in range(min(cells[0][0], cells[1][0]),
                         max(cells[0][0], cells[1][0]) + 1):
            out[row][col] = 8
    return out


CANONICAL_SHORTCUTS = {"fixed_color_roles": _fixed_color_roles}


def _span_union(grid):
    """Local deterministic translation used only for semantic rival comparisons."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for cells in _color_points(grid).values():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        dr = (r2 > r1) - (r2 < r1)
        dc = (c2 > c1) - (c2 < c1)
        steps = max(abs(r2 - r1), abs(c2 - c1))
        for index in range(steps + 1):
            out[r1 + index * dr][c1 + index * dc] = 8
    return out


def _breaks_fixed_color_roles(grid):
    return _fixed_color_roles(grid) != _span_union(grid)


SEMANTIC_WITNESSES = {
    "fixed_color_role_counterexample": _breaks_fixed_color_roles,
}
SEMANTIC_RIVALS = {"fixed_color_roles": _fixed_color_roles}
WITNESS_RIVALS = {
    "fixed_color_role_counterexample": ["fixed_color_roles"],
}


EXAMPLES_NEEDED = 2
LESSON_COMPETITORS = {"fixed_color_roles": _fixed_color_roles}


def lesson_identifiable(demos, query):
    """Check that demonstrations refute the strongest canonical shortcut."""
    for pair in demos:
        if _fixed_color_roles(pair["input"]) != pair["output"]:
            return []
    return ["demonstrations do not refute the fixed-color-role shortcut"]
