"""Generator for S11_M6 — occupancy XOR across two divided panels.

A full-height gray(5) divider separates equal panels.  The output is a
cyan(8) mask at coordinates occupied in exactly one panel; input colors are
otherwise irrelevant.  Ordinary draws deliberately include agreement and
both XOR directions, and multicolor draws include unequal occupied colors so
raw cell-value inequality cannot masquerade as occupancy XOR.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a1d4a2b313a"
TASK_ID = "2a1d4a2b313a"
VERSION = "3.1.0"
RULE_HASH = "6a34b942e3c3"
SUMMARY = (
    "A full-height gray(5) divider splits equal left/right panels. Output is "
    "cyan(8) exactly where one corresponding panel cell is background and "
    "the other is occupied. Generated lessons cover both XOR directions, "
    "occupied agreement, background agreement, and different-color overlap."
)

# Three generated demonstrations suffice because palette-size 1 is reserved
# for isolated canonical anchors; every three consecutive ordinary examples
# include multicolor evidence against raw value inequality.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "odd width with one centered full-height gray(5) divider",
    "left and right panels have equal dimensions",
    "ordinary draws contain left-only, right-only, and occupied-agreement cells",
    "multicolor draws contain different-color occupied overlap",
    "ordinary outputs contain both cyan(8) and background(0)",
]

RELATION_PROFILES = ("sparse", "balanced", "dense")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased rng 4..10",
        "valid": "4..10",
    },
    "half_w": {
        "type": "int",
        "default": "difficulty-biased rng 3..8",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "1 on periodic canonical anchors; otherwise rng 2..4",
        "valid": "1..4",
    },
    "relation_profile": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(RELATION_PROFILES),
    },
}

_PANEL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_RELATIONS = (
    "both_zero",
    "left_only",
    "right_only",
    "same_nonzero",
    "different_nonzero",
)


def _split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    half_w = (len(grid[0]) - 1) // 2
    left = [row[:half_w] for row in grid]
    right = [row[half_w + 1:] for row in grid]
    return left, right


def relation_counts(grid: list[list[int]]) -> dict[str, int]:
    """Count corresponding-cell occupancy/color relations across the panels."""
    left, right = _split(grid)
    counts = {name: 0 for name in _RELATIONS}
    for r in range(len(left)):
        for c in range(len(left[0])):
            lv, rv = left[r][c], right[r][c]
            if lv == 0 and rv == 0:
                key = "both_zero"
            elif lv != 0 and rv == 0:
                key = "left_only"
            elif lv == 0 and rv != 0:
                key = "right_only"
            elif lv == rv:
                key = "same_nonzero"
            else:
                key = "different_nonzero"
            counts[key] += 1
    return counts


def _authoritative_python(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror of the selected Racket occupancy-XOR rule."""
    left, right = _split(grid)
    return [
        [8 if ((left[r][c] == 0) != (right[r][c] == 0)) else 0
         for c in range(len(left[0]))]
        for r in range(len(left))
    ]


def _target_occupied(area: int, profile: str) -> int:
    if profile == "sparse":
        return area // 3
    if profile == "balanced":
        return area // 2
    return area - 1


def _profile_for(grid: list[list[int]]) -> str | None:
    counts = relation_counts(grid)
    area = sum(counts.values())
    occupied = area - counts["both_zero"]
    for profile in RELATION_PROFILES:
        if occupied == _target_occupied(area, profile):
            return profile
    return None


def _panel_palette(grid: list[list[int]]) -> set[int]:
    half_w = (len(grid[0]) - 1) // 2
    return {
        value
        for row in grid
        for c, value in enumerate(row)
        if c != half_w and value not in (0, 5)
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, object]:
    """Recover every exact declared axis from a generated grid."""
    return {
        "grid_h": len(grid),
        "half_w": (len(grid[0]) - 1) // 2,
        "palette_size": len(_panel_palette(grid)),
        "relation_profile": _profile_for(grid),
    }


def _snake_cells(height: int, width: int, rng) -> list[tuple[int, int]]:
    """Return a randomized Hamiltonian path through one panel."""
    if rng.choice((False, True)):
        cells = [
            (r, c)
            for c in range(width)
            for r in (range(height) if c % 2 == 0 else range(height - 1, -1, -1))
        ]
    else:
        cells = [
            (r, c)
            for r in range(height)
            for c in (range(width) if r % 2 == 0 else range(width - 1, -1, -1))
        ]
    if rng.choice((False, True)):
        cells.reverse()
    return cells


def _structured_relations(
    height: int,
    width: int,
    occupied_target: int,
    palette: list[int],
    rng,
) -> list[tuple[int, int]]:
    """Lay semantic witnesses out as a few connected color runs.

    Along a 4-connected snake path the occupied union is one interval:
    left-only, overlap, then right-only.  Thus each panel's occupied cells
    remain connected, while short boundary color runs expose every requested
    palette color and the decisive different-color occupied overlap.
    """
    if occupied_target < 4:
        raise ValueError("occupancy-XOR lessons need at least four occupied positions")

    # Reserve at least one cell for each XOR direction and two overlap cells
    # (one unequal-color witness and one equal-color witness).
    left_only = rng.randint(1, occupied_target - 3)
    right_only = rng.randint(1, occupied_target - left_only - 2)
    overlap = occupied_target - left_only - right_only

    base = palette[0]
    left_color = palette[2] if len(palette) >= 3 else base
    right_color = palette[3] if len(palette) >= 4 else base

    occupied: list[tuple[int, int]] = []
    occupied.extend((left_color, 0) for _ in range(left_only))
    if len(palette) >= 2:
        occupied.append((base, palette[1]))
        overlap -= 1
    occupied.extend((base, base) for _ in range(overlap))
    occupied.extend((0, right_color) for _ in range(right_only))

    if rng.choice((False, True)):
        occupied = [(right, left) for left, right in occupied]

    area = height * width
    path = _snake_cells(height, width, rng)
    start = rng.randint(0, area - occupied_target)
    relations = [(0, 0)] * area
    for (r, c), relation in zip(path[start:start + occupied_target], occupied):
        relations[r * width + c] = relation
    return relations


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
    # Every fourth unoverridden draw is an exact canonical-scale anchor in
    # every difficulty band.  The other 75% retain the full difficulty-biased
    # shape curriculum; explicit shape overrides always take precedence.
    canonical_anchor = (
        sample_index % 4 == 0
        and "grid_h" not in overrides
        and "half_w" not in overrides
    )
    if canonical_anchor:
        h = ctx.draw_int("grid_h", 4, 4)
        half_w = ctx.draw_int("half_w", 4, 4)
    else:
        h = ctx.draw_int_diff("grid_h", 4, 10)
        half_w = ctx.draw_int_diff("half_w", 3, 8)

    # Keep monochrome canonical anchors sparse in the lesson stream while
    # accepting every explicit palette-size override at every sample index.
    if "palette_size" in overrides:
        palette_size = ctx.draw_choice("palette_size", (1, 2, 3, 4))
    elif sample_index % 4 == 0:
        palette_size = ctx.draw_choice("palette_size", (1,))
    else:
        palette_size = ctx.draw_choice("palette_size", (2, 3, 4))
    profile = ctx.draw_choice("relation_profile", RELATION_PROFILES)

    palette_rng = ctx.draw_rng("palette")
    if palette_size == 1:
        palette = [2]
    else:
        colors = list(_PANEL_COLORS)
        palette_rng.shuffle(colors)
        palette = colors[:palette_size]

    area = h * half_w
    occupied_target = _target_occupied(area, profile)
    relations = _structured_relations(
        h, half_w, occupied_target, palette, ctx.draw_rng("relations")
    )

    width = 2 * half_w + 1
    divider = half_w
    grid = full_grid(h, width, 0)
    for r in range(h):
        grid[r][divider] = 5
    for index, (left_value, right_value) in enumerate(relations):
        r, c = divmod(index, half_w)
        grid[r][c] = left_value
        grid[r][divider + 1 + c] = right_value

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError(f"constructed invalid occupancy-XOR grid: {errors}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate task structure and exact requested-axis realization."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be ARC colors 0..9"]

    height = len(grid)
    if not 4 <= height <= 10:
        errors.append(f"grid height must be 4..10, found {height}")
    if width % 2 != 1:
        errors.append(f"grid width must be odd, found {width}")
        return errors
    half_w = (width - 1) // 2
    if not 3 <= half_w <= 8:
        errors.append(f"panel half-width must be 3..8, found {half_w}")

    if any(row[half_w] != 5 for row in grid):
        errors.append("center divider must be full-height gray(5)")
    if any(value == 5 for row in grid for c, value in enumerate(row) if c != half_w):
        errors.append("gray(5) may appear only in the center divider")

    palette_size = len(_panel_palette(grid))
    if not 1 <= palette_size <= 4:
        errors.append(f"panel palette must contain 1..4 colors, found {palette_size}")

    counts = relation_counts(grid)
    xor_cells = counts["left_only"] + counts["right_only"]
    agreement_cells = counts["both_zero"] + counts["same_nonzero"] + counts["different_nonzero"]
    if xor_cells == 0:
        errors.append("at least one corresponding cell must differ in occupancy")
    if agreement_cells == 0:
        errors.append("at least one corresponding cell must agree in occupancy")

    requested = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the public 4x9, red(2)-only canonical input profile."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (len(grid), len(grid[0])) != (4, 9):
        reasons.append(f"canonical dimensions are 4x9, found {len(grid)}x{len(grid[0])}")
    if _panel_palette(grid) != {2}:
        reasons.append("canonical panels use red(2) as their only occupied color")
    return reasons


def _rival_raw_inequality(grid):
    left, right = _split(grid)
    return [
        [8 if left[r][c] != right[r][c] else 0 for c in range(len(left[0]))]
        for r in range(len(left))
    ]


def _rival_union(grid):
    left, right = _split(grid)
    return [
        [8 if left[r][c] != 0 or right[r][c] != 0 else 0
         for c in range(len(left[0]))]
        for r in range(len(left))
    ]


def _rival_left_only(grid):
    left, _ = _split(grid)
    return [[8 if value != 0 else 0 for value in row] for row in left]


def _rival_right_only(grid):
    _, right = _split(grid)
    return [[8 if value != 0 else 0 for value in row] for row in right]


LESSON_COMPETITORS: dict[str, Callable] = {
    "raw_cell_inequality": _rival_raw_inequality,
    "occupancy_union": _rival_union,
    "copy_left_occupancy": _rival_left_only,
    "copy_right_occupancy": _rival_right_only,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def _valid(grid) -> bool:
    return not self_check(grid)


def _has_relation(grid, name: str) -> bool:
    return _valid(grid) and relation_counts(grid)[name] > 0


def _rival_differs(grid, rival: Callable) -> bool:
    return _valid(grid) and rival(grid) != _authoritative_python(grid)


SEMANTIC_WITNESSES = {
    "left_only_occupancy": lambda grid: _has_relation(grid, "left_only"),
    "right_only_occupancy": lambda grid: _has_relation(grid, "right_only"),
    "occupied_agreement": lambda grid: _has_relation(grid, "same_nonzero"),
    "different_color_overlap": lambda grid: _has_relation(grid, "different_nonzero"),
}

WITNESS_RIVALS = {
    "left_only_occupancy": ["copy_right_occupancy"],
    "right_only_occupancy": ["copy_left_occupancy"],
    "occupied_agreement": ["occupancy_union"],
    "different_color_overlap": ["raw_cell_inequality"],
}



def lesson_identifiable(demos, query) -> list[str]:
    """Report named rival rules that survive all demonstrations."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
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
