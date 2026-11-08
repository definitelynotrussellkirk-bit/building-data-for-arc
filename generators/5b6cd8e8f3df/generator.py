"""Semantic generator for ARC task 5b6cd8e8f3df (Seed Plus Grow).

Every nonzero input cell is an independent seed.  The Racket authority replaces
that seed with the same-color orthogonal radius-1 plus.  The generated teaching
distribution deliberately repeats seed colors: every canonical example uses a
different color at every seed, so canonical data alone cannot refute the false
shortcut "stamp only the first seed of each color".
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5b6cd8e8f3df"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "f8f10f7791eb"
EXAMPLES_NEEDED = 2
LESSON_SAMPLE_STRIDE = 11
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, replace every separated interior seed by a "
    "same-color five-cell orthogonal plus, preserving the grid size."
)

INVARIANTS = [
    "background is color 0",
    "the input contains two to five isolated one-cell seeds",
    "every seed is at least one cell inside the border",
    "radius-1 plus footprints are pairwise disjoint",
    "seed colors may repeat; every seed grows independently",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 7..16",
        "valid": "7..16",
    },
    "n_seeds": {
        "type": "int",
        "default": "canonical anchor or scheduled 3|4|5",
        "valid": "2..5",
    },
    "repeat_colors": {
        "type": "bool",
        "default": "scheduled false|true|false|true",
        "valid": "false|true",
    },
}

# Every Cartesian combination of the four exact axes is supported.  Placement
# profiles are curriculum scheduling, not override axes; when a tiny overridden
# grid cannot realize a preferred profile, placement lawfully falls back to any
# disjoint interior layout rather than rejecting a declared axis combination.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

# Complete linked (height, width, seed-count) profiles from all canonical inputs.
# Slot 0 uses one exact profile and all-distinct colors, reproducing the complete
# canonical (height, width, palette-size) signature in every difficulty band.
_CANONICAL_PROFILES = (
    (7, 8, 2),
    (8, 8, 3),
    (6, 9, 2),
    (7, 7, 3),
)
SCHEDULE_PROFILES = (0, 1, 2, 3)
_REPEAT_SCHEDULE = (False, True, False, True)
_SEED_SCHEDULE = (None, 3, 4, 5)
_POSITION_SCHEDULE = ("any", "mixed", "deep", "border")


def _plus_cells(row: int, col: int) -> set[tuple[int, int]]:
    return {
        (row, col),
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    }


def _compatible(left: tuple[int, int], right: tuple[int, int]) -> bool:
    # Orthogonal radius-1 plus footprints are disjoint iff center distance >= 3.
    return abs(left[0] - right[0]) + abs(left[1] - right[1]) >= 3


def _border_center(row: int, col: int, height: int, width: int) -> bool:
    """A legal interior center whose output plus touches the grid border."""
    return row in (1, height - 2) or col in (1, width - 2)


def _record_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{label} must be an integer in [{lo}, {hi}]")
        return int(ctx._record(label, value, from_override=True))
    if not lo <= default <= hi:
        raise ValueError(f"internal {label} default {default} outside [{lo}, {hi}]")
    return int(ctx._record(label, default, from_override=False))


def _record_bool(ctx, label: str, default: bool) -> bool:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
        if type(value) is not bool:
            raise ValueError(f"{label} must be a boolean")
        return bool(ctx._record(label, value, from_override=True))
    return bool(ctx._record(label, default, from_override=False))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _default_dims(ctx, difficulty) -> tuple[int, int]:
    ranges = {
        "easy": ((6, 9), (7, 10)),
        "medium": ((8, 11), (9, 13)),
        "hard": ((10, 14), (11, 16)),
        None: ((6, 14), (7, 16)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[difficulty]
    rng = ctx.draw_rng("dimensions")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _profile_ok(
    centers: list[tuple[int, int]], profile: str, height: int, width: int
) -> bool:
    flags = [_border_center(row, col, height, width) for row, col in centers]
    if profile == "border":
        return bool(flags) and all(flags)
    if profile == "deep":
        return bool(flags) and not any(flags)
    if profile == "mixed":
        return bool(flags) and any(flags) and not all(flags)
    return True


def _find_centers(
    height: int,
    width: int,
    count: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)

    if profile == "border":
        candidates.sort(
            key=lambda p: (not _border_center(*p, height, width), rng.random())
        )
    elif profile == "deep":
        candidates.sort(
            key=lambda p: (_border_center(*p, height, width), rng.random())
        )
    elif profile == "mixed":
        candidates.sort(
            key=lambda p: (
                0 if _border_center(*p, height, width) else 1,
                rng.random(),
            )
        )

    def solve(require_profile: bool) -> list[tuple[int, int]] | None:
        chosen: list[tuple[int, int]] = []

        def search(start: int) -> bool:
            if len(chosen) == count:
                return not require_profile or _profile_ok(chosen, profile, height, width)
            if len(chosen) + len(candidates) - start < count:
                return False
            for index in range(start, len(candidates)):
                point = candidates[index]
                if all(_compatible(point, other) for other in chosen):
                    chosen.append(point)
                    if search(index + 1):
                        return True
                    chosen.pop()
            return False

        return list(chosen) if search(0) else None

    selected = solve(require_profile=True)
    if selected is None:
        selected = solve(require_profile=False)
    if selected is None:
        raise ValueError(f"cannot place {count} disjoint seeds in {height}x{width}")
    return selected


def _seed_colors(repeat_colors: bool, count: int, rng) -> list[int]:
    if not repeat_colors:
        return rng.sample(range(1, 10), count)
    first = rng.choice(range(1, 10))
    if count == 2:
        return [first, first]
    second = rng.choice([color for color in range(1, 10) if color != first])
    colors = [first, second] + [first] * (count - 2)
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    if slot == 0:
        # One keyed draw supplies all linked canonical fields; dimensions and
        # palette size therefore cannot drift into a noncanonical combination.
        default_h, default_w, default_n = ctx.draw_rng(
            "linked_canonical_profile"
        ).choice(_CANONICAL_PROFILES)
    else:
        default_h, default_w = _default_dims(ctx, difficulty)
        default_n = int(_SEED_SCHEDULE[slot])

    height = _record_int(ctx, "grid_h", 6, 14, default_h)
    width = _record_int(ctx, "grid_w", 7, 16, default_w)
    n_seeds = _record_int(ctx, "n_seeds", 2, 5, default_n)
    repeat_colors = _record_bool(ctx, "repeat_colors", _REPEAT_SCHEDULE[slot])

    centers = _find_centers(
        height,
        width,
        n_seeds,
        _POSITION_SCHEDULE[slot],
        ctx.draw_rng("layout"),
    )
    colors = _seed_colors(repeat_colors, n_seeds, ctx.draw_rng("colors"))

    grid = full_grid(height, width, 0)
    for (row, col), color in zip(centers, colors):
        grid[row][col] = color
    return grid


def _markers(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def observe_overrides(grid) -> dict[str, int | bool]:
    markers = _markers(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_seeds": len(markers),
        "repeat_colors": len({value for _, _, value in markers}) < len(markers),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes from the teaching grammar."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]

    height, width = len(grid), len(grid[0])
    if not (6 <= height <= 14 and 7 <= width <= 16):
        errors.append(f"grid dimensions {height}x{width} outside teaching envelope")
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            return errors + ["ragged grid"]
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return errors + [f"invalid ARC color {value!r}"]

    markers = _markers(grid)
    if not (2 <= len(markers) <= 5):
        errors.append(f"expected 2..5 seeds, found {len(markers)}")

    footprints: list[tuple[tuple[int, int], set[tuple[int, int]]]] = []
    for row, col, _ in markers:
        if row in (0, height - 1) or col in (0, width - 1):
            errors.append(f"seed lies on border at {(row, col)}")
        footprint = _plus_cells(row, col)
        if any(not (0 <= r < height and 0 <= c < width) for r, c in footprint):
            errors.append(f"seed plus would leave grid at {(row, col)}")
        footprints.append(((row, col), footprint))

    for index, (left, left_footprint) in enumerate(footprints):
        for right, right_footprint in footprints[index + 1 :]:
            if left_footprint & right_footprint:
                errors.append(f"plus footprints overlap: {left} and {right}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _analysis(grid) -> dict[str, object]:
    markers = _markers(grid)
    colors = [value for _, _, value in markers]
    return {
        "markers": markers,
        "distinct_colors": len(set(colors)),
        "has_repeated_color": len(set(colors)) < len(colors),
    }


def _paint_neighborhood(grid, cells_fn, color_fn=None):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = full_grid(height, width, 0)
    markers = _markers(grid)
    for index, (row, col, color) in enumerate(markers):
        paint_color = color_fn(markers, index) if color_fn else color
        for rr, cc in cells_fn(row, col):
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = paint_color
    return output


def rule_mirror(grid):
    """Pure test mirror; materialized outputs still come only from Racket."""
    return _paint_neighborhood(grid, _plus_cells)


def _identity(grid):
    return [list(row) for row in grid]


def _horizontal_only(grid):
    return _paint_neighborhood(
        grid, lambda row, col: {(row, col - 1), (row, col), (row, col + 1)}
    )


def _vertical_only(grid):
    return _paint_neighborhood(
        grid, lambda row, col: {(row - 1, col), (row, col), (row + 1, col)}
    )


def _diagonal_x(grid):
    return _paint_neighborhood(
        grid,
        lambda row, col: {
            (row, col),
            (row - 1, col - 1),
            (row - 1, col + 1),
            (row + 1, col - 1),
            (row + 1, col + 1),
        },
    )


def _square_3x3(grid):
    return _paint_neighborhood(
        grid,
        lambda row, col: {
            (row + dr, col + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        },
    )


def _first_seed_only(grid):
    markers = _markers(grid)
    output = full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    if not markers:
        return output
    row, col, color = markers[0]
    for rr, cc in _plus_cells(row, col):
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            output[rr][cc] = color
    return output


def _one_stamp_per_color(grid):
    seen: set[int] = set()
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = full_grid(height, width, 0)
    for row, col, color in _markers(grid):
        if color in seen:
            continue
        seen.add(color)
        for rr, cc in _plus_cells(row, col):
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = color
    return output


def _modal_color_plus(grid):
    colors = [value for _, _, value in _markers(grid)]
    if not colors:
        return full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    counts = Counter(colors)
    modal = min((-count, color) for color, count in counts.items())[1]
    return _paint_neighborhood(grid, _plus_cells, lambda markers, index: modal)


def _valid_scene(grid) -> bool:
    return not self_check(grid)


def _multiple_seeds(grid) -> bool:
    return len(_markers(grid)) >= 2


def _repeated_color_locations(grid) -> bool:
    return bool(_analysis(grid)["has_repeated_color"])


def _mixed_seed_colors(grid) -> bool:
    return int(_analysis(grid)["distinct_colors"]) >= 2


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "orthogonal_plus_rebuttal": _valid_scene,
    "all_seeds_matter": _multiple_seeds,
    "repeated_color_locations": _repeated_color_locations,
    "seed_colors_are_preserved": _mixed_seed_colors,
}

SEMANTIC_RIVALS = {
    "identity": _identity,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "diagonal_x": _diagonal_x,
    "square_3x3": _square_3x3,
    "first_seed_only": _first_seed_only,
    "one_stamp_per_color": _one_stamp_per_color,
    "modal_color_plus": _modal_color_plus,
}

WITNESS_RIVALS = {
    "orthogonal_plus_rebuttal": [
        "identity",
        "horizontal_only",
        "vertical_only",
        "diagonal_x",
        "square_3x3",
    ],
    "all_seeds_matter": ["first_seed_only"],
    "repeated_color_locations": ["one_stamp_per_color"],
    "seed_colors_are_preserved": ["modal_color_plus"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    # Canonical uses one distinct color per seed, so this false rule fits all
    # four official pairs until a generated repeated-color scene refutes it.
    "one_stamp_per_color": _one_stamp_per_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but answers the query differently"
                )
            else:
                reasons.append(f"{name} survives every demonstration and the query")
    return reasons
