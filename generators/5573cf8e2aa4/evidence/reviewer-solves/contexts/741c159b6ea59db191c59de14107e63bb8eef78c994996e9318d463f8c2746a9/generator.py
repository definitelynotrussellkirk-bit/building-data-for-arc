"""Generator for S19_E1 — occupancy union across two side panels.

A full-height maroon(9) divider separates equal left/right panels.  The
output is a cyan(8) mask at coordinates occupied in either panel.  Generated
lessons contain left-only, right-only, overlap, and blank relations, while a
periodic exact-profile anchor preserves the public 5x11, four-color manifold.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5573cf8e2aa4"
TASK_ID = "5573cf8e2aa4"
VERSION = "3.0.0"
RULE_HASH = "59a18f0cd9d4"
SUMMARY = (
    "A full-height maroon(9) divider splits equal left/right panels. Output "
    "is cyan(8) exactly where either corresponding panel cell is occupied. "
    "Ordinary draws expose blank, left-only, right-only, and overlap cases; "
    "same-color overlap periodically distinguishes occupancy union from raw "
    "cell-value inequality."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

INVARIANTS = [
    "odd width with one centered full-height maroon(9) divider",
    "left and right panels have equal dimensions and are individually monochrome",
    "generated draws contain blank, left-only, right-only, and occupied-overlap cells",
    "the output is the cyan(8) union of the two panels' occupied supports",
]

RELATION_PROFILES = ("sparse", "balanced", "dense")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased rng 5..9; every-third canonical anchor 5",
        "valid": "5..9",
    },
    "half_w": {
        "type": "int",
        "default": "difficulty-biased rng 5..9; every-third canonical anchor 5",
        "valid": "5..9",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 1 or 2 panel colors",
        "valid": "1..2",
    },
    "relation_profile": {
        "type": "str",
        "default": "rng; canonical anchors use sparse",
        "valid": "|".join(RELATION_PROFILES),
    },
}

# Avoid 7 so destructive mutation probes can always introduce a new color.
# Colors 0, 8, and 9 retain their task roles.
_PANEL_COLORS = (1, 2, 3, 4, 6)
_RELATIONS = (
    "both_zero",
    "left_only",
    "right_only",
    "overlap_same",
    "overlap_different",
)


def _split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    half_w = (len(grid[0]) - 1) // 2
    return (
        [row[:half_w] for row in grid],
        [row[half_w + 1 :] for row in grid],
    )


def relation_counts(grid: list[list[int]]) -> dict[str, int]:
    """Count corresponding-cell occupancy/color relations."""
    left, right = _split(grid)
    counts = {name: 0 for name in _RELATIONS}
    for r in range(len(left)):
        for c in range(len(left[0])):
            lv, rv = left[r][c], right[r][c]
            if lv == 0 and rv == 0:
                relation = "both_zero"
            elif lv != 0 and rv == 0:
                relation = "left_only"
            elif lv == 0 and rv != 0:
                relation = "right_only"
            elif lv == rv:
                relation = "overlap_same"
            else:
                relation = "overlap_different"
            counts[relation] += 1
    return counts


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror of the selected Racket occupancy-union rule."""
    left, right = _split(grid)
    return [
        [
            8 if left[r][c] != 0 or right[r][c] != 0 else 0
            for c in range(len(left[0]))
        ]
        for r in range(len(left))
    ]


_authoritative_python = rule_mirror


def _target_occupied(area: int, profile: str) -> int:
    if profile == "sparse":
        return max(4, area // 3)
    if profile == "balanced":
        return max(4, area // 2)
    if profile == "dense":
        return area - 1
    raise ValueError(f"unknown relation profile: {profile!r}")


def _profile_for(grid: list[list[int]]) -> str | None:
    counts = relation_counts(grid)
    area = sum(counts.values())
    occupied = area - counts["both_zero"]
    for profile in RELATION_PROFILES:
        if occupied == _target_occupied(area, profile):
            return profile
    return None


def _panel_color_sets(grid: list[list[int]]) -> tuple[set[int], set[int]]:
    left, right = _split(grid)
    left_colors = {value for row in left for value in row if value != 0}
    right_colors = {value for row in right for value in row if value != 0}
    return left_colors, right_colors


def _panel_palette(grid: list[list[int]]) -> set[int]:
    left_colors, right_colors = _panel_color_sets(grid)
    return left_colors | right_colors


def observe_overrides(grid: list[list[int]]) -> dict[str, object]:
    """Recover every exact declared axis from a generated grid."""
    return {
        "grid_h": len(grid),
        "half_w": (len(grid[0]) - 1) // 2,
        "palette_size": len(_panel_palette(grid)),
        "relation_profile": _profile_for(grid),
    }


def _snake_cells(height: int, width: int, rng) -> list[tuple[int, int]]:
    """Return a randomized 4-connected Hamiltonian path through one panel."""
    if rng.choice((False, True)):
        cells = [
            (r, c)
            for c in range(width)
            for r in (
                range(height) if c % 2 == 0 else range(height - 1, -1, -1)
            )
        ]
    else:
        cells = [
            (r, c)
            for r in range(height)
            for c in (
                range(width) if r % 2 == 0 else range(width - 1, -1, -1)
            )
        ]
    if rng.choice((False, True)):
        cells.reverse()
    return cells


def _relation_run(
    occupied_target: int,
    left_color: int,
    right_color: int,
    rng,
    *,
    swap_roles: bool = True,
) -> list[tuple[int, int]]:
    """Build one interval whose panel projections are each connected."""
    if occupied_target < 3:
        raise ValueError("occupancy-union lessons need at least three occupied cells")

    overlap = rng.randint(1, max(1, occupied_target // 3))
    remaining = occupied_target - overlap
    left_only = rng.randint(1, remaining - 1)
    right_only = remaining - left_only

    run = (
        [(left_color, 0)] * left_only
        + [(left_color, right_color)] * overlap
        + [(0, right_color)] * right_only
    )
    if swap_roles and rng.choice((False, True)):
        run = [(right, left) for left, right in reversed(run)]
    return run


def _assemble(
    height: int,
    half_w: int,
    occupied_target: int,
    left_color: int,
    right_color: int,
    rng,
    *,
    swap_roles: bool = True,
) -> list[list[int]]:
    area = height * half_w
    if not 3 <= occupied_target < area:
        raise ValueError(
            f"occupied target must be in [3, {area - 1}], found {occupied_target}"
        )

    path = _snake_cells(height, half_w, rng)
    start = rng.randint(0, area - occupied_target)
    run = _relation_run(
        occupied_target, left_color, right_color, rng, swap_roles=swap_roles
    )

    relations = [(0, 0)] * area
    for (r, c), relation in zip(path[start : start + occupied_target], run):
        relations[r * half_w + c] = relation

    divider = half_w
    grid = full_grid(height, 2 * half_w + 1, 0)
    for r in range(height):
        grid[r][divider] = 9
    for index, (left_value, right_value) in enumerate(relations):
        r, c = divmod(index, half_w)
        grid[r][c] = left_value
        grid[r][divider + 1 + c] = right_value
    return grid


def _canonical_anchor(ctx) -> list[list[int]]:
    """Draw an exact public-profile example without copying a canonical grid."""
    height = ctx.draw_int("grid_h", 5, 5)
    half_w = ctx.draw_int("half_w", 5, 5)
    ctx.draw_choice("palette_size", (2,))
    profile = ctx.draw_choice("relation_profile", ("sparse",))
    right_color = ctx.draw_rng("anchor_right_color").choice((3, 4))
    return _assemble(
        height,
        half_w,
        _target_occupied(height * half_w, profile),
        2,
        right_color,
        ctx.draw_rng("anchor_relations"),
        swap_roles=False,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if sample_index % 3 == 0 and not overrides:
        grid = _canonical_anchor(ctx)
    else:
        height = ctx.draw_int_diff("grid_h", 5, 9)
        half_w = ctx.draw_int_diff("half_w", 5, 9)

        if "palette_size" in overrides:
            palette_size = ctx.draw_choice("palette_size", (1, 2))
        else:
            # Any three consecutive samples contain one two-color canonical
            # anchor and two one-color lessons.  The latter make occupied
            # overlap disagree with raw cell-value inequality.
            palette_size = ctx.draw_choice("palette_size", (1,))

        profile = ctx.draw_choice("relation_profile", RELATION_PROFILES)
        color_rng = ctx.draw_rng("panel_colors")
        left_color = color_rng.choice(_PANEL_COLORS)
        if palette_size == 1:
            right_color = left_color
        else:
            right_color = color_rng.choice(
                [color for color in _PANEL_COLORS if color != left_color]
            )

        grid = _assemble(
            height,
            half_w,
            _target_occupied(height * half_w, profile),
            left_color,
            right_color,
            ctx.draw_rng("relations"),
        )

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError(f"constructed invalid occupancy-union grid: {errors}")
    return [row[:] for row in grid]


def _canonical_shape_palette_candidate(grid: list[list[int]]) -> bool:
    if len(grid) != 5 or len(grid[0]) != 11:
        return False
    left_colors, right_colors = _panel_color_sets(grid)
    return left_colors == {2} and right_colors in ({3}, {4})


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate task structure, semantic coverage, and exact overrides."""
    del difficulty
    if not isinstance(grid, list) or not grid or not all(
        isinstance(row, list) for row in grid
    ):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(
        not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be ARC colors 0..9"]

    errors: list[str] = []
    height = len(grid)
    if not 5 <= height <= 9:
        errors.append(f"grid height must be 5..9, found {height}")
    if width % 2 != 1:
        errors.append(f"grid width must be odd, found {width}")
        return errors
    half_w = (width - 1) // 2
    if not 5 <= half_w <= 9:
        errors.append(f"panel half-width must be 5..9, found {half_w}")

    if any(row[half_w] != 9 for row in grid):
        errors.append("center divider must be full-height maroon(9)")
    if any(
        value == 9
        for row in grid
        for c, value in enumerate(row)
        if c != half_w
    ):
        errors.append("maroon(9) may appear only in the center divider")

    left_colors, right_colors = _panel_color_sets(grid)
    if not left_colors:
        errors.append("left panel must contain occupied cells")
    elif len(left_colors) != 1:
        errors.append("left panel must be monochrome")
    if not right_colors:
        errors.append("right panel must contain occupied cells")
    elif len(right_colors) != 1:
        errors.append("right panel must be monochrome")
    if any(color not in _PANEL_COLORS for color in left_colors | right_colors):
        errors.append(
            f"panel colors must come from {_PANEL_COLORS}, found "
            f"{sorted(left_colors | right_colors)}"
        )

    counts = relation_counts(grid)
    if counts["both_zero"] == 0:
        errors.append("at least one corresponding cell must be blank in both panels")
    if counts["left_only"] == 0:
        errors.append("at least one left-only occupied cell is required")
    if counts["right_only"] == 0:
        errors.append("at least one right-only occupied cell is required")

    occupied_overlap = counts["overlap_same"] + counts["overlap_different"]
    occupied = sum(counts.values()) - counts["both_zero"]
    canonical_exception = (
        not errors
        and _canonical_shape_palette_candidate(grid)
        and occupied in (7, 8)
    )
    if occupied_overlap == 0 and not canonical_exception:
        errors.append("generated lessons require at least one occupied-overlap cell")
    if _profile_for(grid) is None and not canonical_exception:
        errors.append(
            "occupied union size must match sparse, balanced, or dense profile"
        )

    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {
                axis: value for axis, value in candidate.items() if axis in AXES
            }
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the public 5x11, red-left/green-or-yellow-right profile."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (len(grid), len(grid[0])) != (5, 11):
        reasons.append(
            f"canonical dimensions are 5x11, found {len(grid)}x{len(grid[0])}"
        )
    left_colors, right_colors = _panel_color_sets(grid)
    if left_colors != {2}:
        reasons.append("canonical left panel uses red(2)")
    if right_colors not in ({3}, {4}):
        reasons.append("canonical right panel uses green(3) or yellow(4)")
    return reasons


def _rival_intersection(grid):
    left, right = _split(grid)
    return [
        [
            8 if left[r][c] != 0 and right[r][c] != 0 else 0
            for c in range(len(left[0]))
        ]
        for r in range(len(left))
    ]


def _rival_xor(grid):
    left, right = _split(grid)
    return [
        [
            8 if (left[r][c] == 0) != (right[r][c] == 0) else 0
            for c in range(len(left[0]))
        ]
        for r in range(len(left))
    ]


def _rival_copy_left(grid):
    left, _ = _split(grid)
    return [[8 if value != 0 else 0 for value in row] for row in left]


def _rival_copy_right(grid):
    _, right = _split(grid)
    return [[8 if value != 0 else 0 for value in row] for row in right]


def _rival_raw_inequality(grid):
    left, right = _split(grid)
    return [
        [8 if left[r][c] != right[r][c] else 0 for c in range(len(left[0]))]
        for r in range(len(left))
    ]


LESSON_COMPETITORS: dict[str, Callable] = {
    "occupancy_intersection": _rival_intersection,
    "occupancy_xor": _rival_xor,
    "copy_left_occupancy": _rival_copy_left,
    "copy_right_occupancy": _rival_copy_right,
    "raw_cell_inequality": _rival_raw_inequality,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def _valid(grid) -> bool:
    return not self_check(grid)


def _has_relation(grid, relation: str) -> bool:
    return _valid(grid) and relation_counts(grid)[relation] > 0


SEMANTIC_WITNESSES = {
    "left_only_occupancy": lambda grid: _has_relation(grid, "left_only"),
    "right_only_occupancy": lambda grid: _has_relation(grid, "right_only"),
    "occupied_overlap": lambda grid: _valid(grid)
    and (
        relation_counts(grid)["overlap_same"]
        + relation_counts(grid)["overlap_different"]
        > 0
    ),
    "same_color_overlap": lambda grid: _has_relation(grid, "overlap_same"),
}

WITNESS_RIVALS = {
    "left_only_occupancy": ["occupancy_intersection", "copy_right_occupancy"],
    "right_only_occupancy": ["occupancy_intersection", "copy_left_occupancy"],
    "occupied_overlap": ["occupancy_xor"],
    "same_color_overlap": ["raw_cell_inequality"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report named rival rules that survive all demonstrations."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if not fits_demos:
            continue
        if competitor(query["input"]) == query["output"]:
            reasons.append(f"{name} survives every demo and the query")
        else:
            reasons.append(f"{name} fits every demo but changes the query answer")
    return reasons
