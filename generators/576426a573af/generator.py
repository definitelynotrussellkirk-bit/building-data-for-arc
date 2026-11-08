"""Curriculum generator for ARC task 576426a573af.

The selected rule overlays the original grid on top of its up/down flip.  An
original non-zero cell therefore wins; only an original zero cell can be filled
from its vertically mirrored partner.  In particular, two different non-zero
mirror partners are preserved in place rather than swapped or reconciled.

A four-profile sample-index schedule makes that precedence learnable.  Every
four consecutive examples contain a canonical bottom-anchored scene, a top-only
source scene, a bidirectional scene, and multiple conflicting non-zero mirror
pairs. Both conflict-bearing roles retain a singleton source and at least two
conflicts, so holding out either role does not hide conflict multiplicity.
An eight-index subcycle alternates stochastic canonical scenes with recolored
canonical training geometries when the requested shape and palette permit it.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "576426a573af"
VERSION = "2.2.0"
RULE_HASH = "892d64eecd2e"
SUMMARY = (
    "Preserve every original non-zero cell and fill each zero cell from its "
    "up/down mirror when that mirror is non-zero. A four-example curriculum "
    "covers canonical bottom stacks, top sources, both source directions, and "
    "multiple conflicting non-zero mirror pairs whose original colors remain fixed."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is zero and three through six foreground colors are used",
    "at least one off-midline mirror pair has exactly one non-zero source cell",
    "the original non-zero cell always has precedence over its mirrored partner",
    "every four consecutive sample indices cover all four teaching profiles",
    "top_only and conflict profiles each contain at least two conflicting mirror orbits",
]

SCHEDULE_PROFILES = (
    "canonical_bottom",
    "top_only",
    "bidirectional",
    "conflict",
)
LESSON_SCHEDULE_PERIOD = 8

# The two canonical TRAIN geometries, normalized to abstract color labels.
# Their partitions preserve the source's connected stacks and color regions.
# Only half of canonical_bottom slots use these; other roles remain generated.
_CANONICAL_TRAIN_PARTITIONS = {
    3: (
        (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0),
        (0, 0, 0, 1), (0, 0, 0, 1), (0, 2, 0, 1), (0, 3, 2, 1), (3, 3, 2, 1),
    ),
    4: (
        (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0),
        (0, 0, 0, 1), (0, 0, 2, 1), (0, 0, 2, 1), (3, 0, 2, 1), (3, 4, 2, 1),
    ),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10 or difficulty-aware rng 4..18",
        "valid": "4..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 4 or difficulty-aware rng 3..18",
        "valid": "3..18",
    },
    "fg_palette_size": {
        "type": "int",
        "default": "difficulty-aware rng 3..6 (canonical 3..4)",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_HEIGHT_BOUNDS = (4, 18)
_WIDTH_BOUNDS = (3, 18)
_PALETTE_BOUNDS = (3, 6)
_BAND_DIMENSIONS = {
    None: ((4, 18), (3, 18)),
    "easy": ((4, 8), (3, 8)),
    "medium": ((7, 13), (5, 13)),
    "hard": ((12, 18), (10, 18)),
}
_BAND_PALETTES = {
    None: (3, 6),
    "easy": (3, 4),
    "medium": (3, 5),
    "hard": (4, 6),
}
_BAND_ORBIT_CAP = {None: 16, "easy": 8, "medium": 14, "hard": 24}
_CANONICAL_ORBIT_RANGES = {
    None: (8, 14),
    "easy": (8, 9),
    "medium": (10, 11),
    "hard": (12, 14),
}


def _validate_request(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not a coerced scalar")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not a coerced scalar")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in _BAND_DIMENSIONS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    bounds = {
        "grid_h": _HEIGHT_BOUNDS,
        "grid_w": _WIDTH_BOUNDS,
        "fg_palette_size": _PALETTE_BOUNDS,
    }
    for name, (lo, hi) in bounds.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the teaching role; every four consecutive indices cover all roles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, name: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]) -> int:
    """Use the full declared domain for overrides and scheduled bounds otherwise."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, *full_bounds)
    return ctx.draw_int(name, *default_bounds)


def _mirror_orbits(h: int, w: int) -> list[tuple[int, int, int]]:
    return [(r, h - 1 - r, c) for r in range(h // 2) for c in range(w)]


def _anchored_cells(h: int, w: int, count: int, *, side: str, rng) -> list[tuple[int, int]]:
    """Choose ``count`` cells as contiguous stacks anchored to top or bottom."""
    half = h // 2
    heights = [0] * w
    # A connected anchor row joins the stacks, including sparse wide overrides.
    # When affordable, it occupies every column as the canonical examples do.
    anchor_width = min(count, w)
    first_column = rng.randrange(w - anchor_width + 1)
    for c in range(first_column, first_column + anchor_width):
        heights[c] = 1
    remaining = count - sum(heights)
    while remaining:
        eligible = [c for c in range(w) if heights[c] < half]
        c = rng.choice(eligible)
        heights[c] += 1
        remaining -= 1

    cells: list[tuple[int, int]] = []
    for c, height in enumerate(heights):
        for offset in range(height):
            r = offset if side == "top" else h - 1 - offset
            cells.append((r, c))
    rng.shuffle(cells)
    return cells


def _connected_subset(cells: list[tuple[int, int]], count: int, rng) -> list[tuple[int, int]]:
    """Grow a connected patch inside the connected anchored source region."""
    remaining = set(cells)
    selected = [rng.choice(sorted(remaining))]
    remaining.remove(selected[0])
    frontier: set[tuple[int, int]] = set()
    while len(selected) < count:
        r, c = selected[-1]
        frontier.update({(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} & remaining)
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        remaining.remove(cell)
        selected.append(cell)
    return selected


def _singleton_cells(
    orbits: list[tuple[int, int, int]],
    count: int,
    *,
    mode: str,
    rng,
) -> list[tuple[int, int]]:
    selected = list(orbits)
    rng.shuffle(selected)
    cells = []
    for index, (top, bottom, c) in enumerate(selected[:count]):
        if mode == "top":
            r = top
        elif mode == "bottom":
            r = bottom
        else:
            r = top if index % 2 == 0 else bottom
        cells.append((r, c))
    return cells


def _color_sequence(palette: list[int], count: int, rng) -> list[int]:
    """Return ``count`` colors while guaranteeing every palette color is visible."""
    first = list(palette)
    rng.shuffle(first)
    return first + [rng.choice(palette) for _ in range(count - len(first))]


def _occupied_orbit_count(ctx, role: str, capacity: int, palette_size: int, difficulty) -> int:
    if role == "canonical_bottom":
        canonical_lo, canonical_hi = _CANONICAL_ORBIT_RANGES[difficulty]
        lo = max(palette_size, min(capacity, canonical_lo))
        hi = min(capacity, canonical_hi)
    elif role == "conflict":
        lo = max(3, palette_size - 1)
        hi = min(capacity, max(lo, _BAND_ORBIT_CAP[difficulty]))
    else:
        lo = max(4, palette_size)
        hi = min(capacity, max(lo, _BAND_ORBIT_CAP[difficulty]))
    if hi < lo:  # Defensive: declared global bounds are designed to avoid this.
        raise ValueError(
            f"insufficient mirror-orbit capacity {capacity} for palette size {palette_size}"
        )
    return ctx.draw_int("occupied_orbits", lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    role = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if role in {"canonical_bottom", "top_only"}:
        # Two of four roles retain the canonical shape/palette profile.  Only
        # canonical_bottom is strict-canonical; top_only is the decisive
        # directionality witness.  This keeps the profile floor robust under
        # off-diagonal census indices without duplicating the same lesson role.
        h_defaults, w_defaults = (10, 10), (4, 4)
        palette_defaults = (3, 4)
    else:
        h_defaults, w_defaults = _BAND_DIMENSIONS[difficulty]
        palette_defaults = _BAND_PALETTES[difficulty]

    h = _draw_axis(ctx, "grid_h", h_defaults, _HEIGHT_BOUNDS)
    w = _draw_axis(ctx, "grid_w", w_defaults, _WIDTH_BOUNDS)
    palette_size = _draw_axis(ctx, "fg_palette_size", palette_defaults, _PALETTE_BOUNDS)
    palette = list(ctx.draw_distinct_colors("palette", n=palette_size, exclude={0}))
    placement_rng = ctx.draw_rng("placement")
    color_rng = ctx.draw_rng("colors")

    grid = full_grid(h, w, 0)
    orbits = _mirror_orbits(h, w)
    anchor = (
        _CANONICAL_TRAIN_PARTITIONS.get(palette_size)
        if role == "canonical_bottom" and (h, w) == (10, 4)
        and sample_index % LESSON_SCHEDULE_PERIOD == 0
        else None
    )
    if anchor is None:
        occupied = _occupied_orbit_count(ctx, role, len(orbits), palette_size, difficulty)
    else:
        anchor_count = sum(value != 0 for row in anchor for value in row)
        occupied = ctx.draw_int("occupied_orbits", anchor_count, anchor_count)

    if role == "canonical_bottom":
        if anchor is not None:
            grid = [[palette[value - 1] if value else 0 for value in row] for row in anchor]
        else:
            cells = _anchored_cells(h, w, occupied, side="bottom", rng=placement_rng)
            colors = _color_sequence(palette, len(cells), color_rng)
            for (r, c), color in zip(cells, colors):
                grid[r][c] = color
    elif role == "top_only":
        cells = _anchored_cells(h, w, occupied, side="top", rng=placement_rng)
        colors = _color_sequence(palette, len(cells), color_rng)
        for (r, c), color in zip(cells, colors):
            grid[r][c] = color

        # Repeat the multiplicity witness so a held-out conflict role leaves
        # enough evidence. Reserve at least one top-only source for copying.
        conflicts = ctx.draw_int("conflicting_orbits", 2, min(4, occupied - 1))
        conflict_cells = _connected_subset(cells, conflicts, ctx.draw_rng("conflict_placement"))
        for conflict_r, conflict_c in conflict_cells:
            mirror_r = h - 1 - conflict_r
            alternatives = [color for color in palette if color != grid[conflict_r][conflict_c]]
            grid[mirror_r][conflict_c] = color_rng.choice(alternatives)
    elif role == "bidirectional":
        cells = _singleton_cells(orbits, occupied, mode="alternating", rng=placement_rng)
        colors = _color_sequence(palette, len(cells), color_rng)
        for (r, c), color in zip(cells, colors):
            grid[r][c] = color
    else:  # conflict
        chosen = list(orbits)
        placement_rng.shuffle(chosen)
        conflicts = ctx.draw_int("conflicting_orbits", 2, min(4, occupied - 1))
        cells = []
        for index, (top, bottom, col) in enumerate(chosen[:occupied]):
            if index < conflicts:
                cells.extend(((top, col), (bottom, col)))
            else:
                cells.append((top if (index - conflicts) % 2 == 0 else bottom, col))
        colors = _color_sequence(palette, len(cells), color_rng)
        for index, ((r, col), color) in enumerate(zip(cells, colors)):
            if index < 2 * conflicts and index % 2 and color == colors[index - 1]:
                # The equal partner retains this color, so replacing its
                # duplicate cannot remove a foreground color from the grid.
                color = color_rng.choice([value for value in palette if value != color])
            grid[r][col] = color

    errors = self_check(grid)
    if errors:  # A production draw should never rely on silent repair.
        raise AssertionError(f"internal generator defect for role {role}: {errors}")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be ARC color integers from zero through nine"]
    return []


def _has_singleton_mirror_pair(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        (grid[r][c] == 0) != (grid[h - 1 - r][c] == 0)
        for r in range(h // 2)
        for c in range(w)
    )


def _has_top_source(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] != 0 and grid[h - 1 - r][c] == 0
        for r in range(h // 2)
        for c in range(w)
    )


def _conflicting_pair_count(grid) -> int:
    h, w = len(grid), len(grid[0])
    return sum(
        grid[r][c] != 0
        and grid[h - 1 - r][c] != 0
        and grid[r][c] != grid[h - 1 - r][c]
        for r in range(h // 2)
        for c in range(w)
    )


def _has_conflicting_pair(grid) -> bool:
    return _conflicting_pair_count(grid) >= 1


def _has_multiple_conflicting_pairs(grid) -> bool:
    return _conflicting_pair_count(grid) >= 2


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not _HEIGHT_BOUNDS[0] <= h <= _HEIGHT_BOUNDS[1]:
        errors.append(f"grid height {h} outside {_HEIGHT_BOUNDS[0]}..{_HEIGHT_BOUNDS[1]}")
    if not _WIDTH_BOUNDS[0] <= w <= _WIDTH_BOUNDS[1]:
        errors.append(f"grid width {w} outside {_WIDTH_BOUNDS[0]}..{_WIDTH_BOUNDS[1]}")

    values = [value for row in grid for value in row]
    foreground = [value for value in values if value != 0]
    palette = set(foreground)
    if 0 not in values:
        errors.append("zero background must remain visible")
    if not _PALETTE_BOUNDS[0] <= len(palette) <= _PALETTE_BOUNDS[1]:
        errors.append(
            f"foreground palette size {len(palette)} outside "
            f"{_PALETTE_BOUNDS[0]}..{_PALETTE_BOUNDS[1]}"
        )
    if len(foreground) < 4:
        errors.append("at least four foreground cells are required")
    if h % 2 and any(grid[h // 2][c] != 0 for c in range(w)):
        errors.append("the self-mirrored middle row must remain background")
    if not _has_singleton_mirror_pair(grid):
        errors.append("at least one mirror pair must contain exactly one non-zero source")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) != (10, 4):
        return ["canonical input shape is exactly 10x4"]
    palette_size = len({value for row in grid for value in row if value != 0})
    if palette_size not in (3, 4):
        return ["canonical inputs use three or four foreground colors"]
    if any(value != 0 for row in grid[:5] for value in row):
        return ["canonical inputs place all foreground in the bottom half"]
    foreground_count = sum(value != 0 for row in grid for value in row)
    if not 8 <= foreground_count <= 14:
        return ["canonical inputs contain eight through fourteen foreground cells"]
    for c in range(w):
        column = [grid[r][c] != 0 for r in range(5, 10)]
        if not any(column):
            return ["canonical inputs occupy every column"]
        first = column.index(True)
        if not all(column[first:]):
            return ["canonical columns are bottom-anchored without holes"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    if _grid_errors(grid):
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "fg_palette_size": len({value for row in grid for value in row if value != 0}),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of ``grid-overlay-on (flip-ud g) g``."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h = len(grid)
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def rival_bottom_to_top_only(grid) -> list[list[int]]:
    """Canonical-compatible shortcut that never copies a top source downward."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r in range(h // 2):
        mirror = h - 1 - r
        for c in range(w):
            if grid[r][c] == 0 and grid[mirror][c] != 0:
                out[r][c] = grid[mirror][c]
    return out


def rival_mirror_wins_conflicts(grid) -> list[list[int]]:
    """Canonical-compatible shortcut that swaps conflicting non-zero partners."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h = len(grid)
    return [
        [grid[h - 1 - r][c] if grid[h - 1 - r][c] != 0 else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def rival_preserve_first_conflict_only(grid) -> list[list[int]]:
    """Canonical-compatible count limit: mirror wins after the first conflict."""
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    seen_conflict = False
    for top in range(h // 2):
        bottom = h - 1 - top
        for col in range(w):
            a, b = grid[top][col], grid[bottom][col]
            if a != 0 and b != 0 and a != b:
                if seen_conflict:
                    out[top][col], out[bottom][col] = b, a
                seen_conflict = True
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "bottom_to_top_only": rival_bottom_to_top_only,
    "mirror_wins_conflicts": rival_mirror_wins_conflicts,
    "preserve_first_conflict_only": rival_preserve_first_conflict_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "top_source": _has_top_source,
    "conflicting_pair": _has_conflicting_pair,
    "multiple_conflicting_pairs": _has_multiple_conflicting_pairs,
}
WITNESS_RIVALS = {
    "top_source": ["bottom_to_top_only"],
    "conflicting_pair": ["mirror_wins_conflicts"],
    "multiple_conflicting_pairs": ["preserve_first_conflict_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named canonical-compatible shortcut survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} outside task grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        valid_demos.append(pair)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query outside task grammar: {errors[0]}")
        elif "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the selected rule")
    return reasons


def mutation_fixtures():
    """Small named structural impostors for future validator regressions."""
    return [
        ("blank", [[0] * 4 for _ in range(10)]),
        ("singleton", [[0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 0]]),
        ("monochrome_block", [[1, 1, 0], [1, 1, 0], [0, 0, 0], [0, 0, 0]]),
        ("already_symmetric", [[1, 2, 3], [0, 0, 0], [0, 0, 0], [1, 2, 3]]),
    ]
