"""Generator for ARC task ``bc1d5164`` / ``9df67b512dad``.

Partition the input into a 3x3 grid of zones: singleton corners, the four edge
strips excluding corners, and the rectangular interior.  The output cell for a
zone is its last non-zero value in row-major order, or zero when the zone is
empty.

The canonical examples use one foreground color, so ``first non-zero``,
``any non-zero``, and ``last non-zero`` all fit them.  Ordinary generated
lessons deliberately include multiple colors within non-corner zones so the
selected Racket rule is identifiable rather than merely executable.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9df67b512dad"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "574840a0b71b"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "Split the grid into nine zones: four singleton corners, four border "
    "strips with the corners removed, and the interior rectangle. Scan each "
    "zone in row-major order. Output a 3x3 grid containing the LAST NON-ZERO "
    "value seen in each zone, or 0 for an empty zone. Generated lessons use "
    "rotating empty-zone masks and multicolor scan conflicts so first-hit and "
    "occupancy-only shortcuts are refuted."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "the grid is at least 5x7, so every non-corner zone has multiple cells",
    "exactly 6 or 7 of the 9 zones are occupied on ordinary draws",
    "every four consecutive samples expose each scheduled empty-zone pattern",
    "non-anchor draws use 2 or 3 foreground colors and make first/last differ in every occupied non-corner zone",
    "one sample in five anchors the canonical 5x7 one-foreground-color profile",
]

# Every four consecutive sample indexes contain every profile, regardless of
# the lesson's starting residue.  Across the four profiles every output cell is
# empty at least once and occupied at least twice.
ZONE_PATTERNS: dict[str, tuple[int, ...]] = {
    "missing_opposite_corners": (1, 2, 3, 4, 5, 6, 7),       # empty 0, 8
    "missing_horizontal_edges": (0, 2, 3, 4, 5, 6, 8),       # empty 1, 7
    "missing_vertical_edges": (0, 1, 2, 4, 6, 7, 8),         # empty 3, 5
    "missing_center_diagonal": (0, 1, 3, 5, 7, 8),           # empty 2, 4, 6
}
SCHEDULE_PROFILES = tuple(ZONE_PATTERNS)

AXES = {
    "grid_h": {"type": "int", "default": "scheduled by difficulty", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "scheduled by difficulty", "valid": "7..16"},
    "palette_size": {"type": "int", "default": "1 on anchors, otherwise 2..3", "valid": "1..3"},
    "zone_pattern": {"type": "str", "default": "four-step lesson schedule", "valid": "missing_opposite_corners|missing_horizontal_edges|missing_vertical_edges|missing_center_diagonal"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_BOUNDS = {
    "grid_h": (5, 14),
    "grid_w": (7, 16),
    "palette_size": (1, 3),
}


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _BOUNDS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    pattern = overrides.get("zone_pattern")
    if pattern is not None and pattern not in ZONE_PATTERNS:
        raise ValueError(
            "zone_pattern must be one of " + ", ".join(SCHEDULE_PROFILES)
        )


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_exact_choice(
    ctx, overrides: dict[str, Any], name: str, default: str, options: tuple[str, ...]
) -> str:
    if name in overrides and overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def schedule_profile(
    seed: int, sample_index: int, difficulty: str | None = None
) -> str:
    """The semantic profile scheduled at this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _default_dimensions(ctx, sample_index: int, difficulty: str | None) -> tuple[int, int]:
    # Canonical anchors appear in every band, including hard.  This is a
    # deliberate curriculum anchor, not a difficulty-bound override rejection.
    if sample_index % 5 == 0:
        return 5, 7
    if difficulty == "easy":
        return (
            ctx.draw_rng("height_band").randint(5, 7),
            ctx.draw_rng("width_band").randint(7, 9),
        )
    if difficulty == "hard":
        return (
            ctx.draw_rng("height_band").randint(10, 14),
            ctx.draw_rng("width_band").randint(12, 16),
        )
    if difficulty == "medium":
        return (
            ctx.draw_rng("height_band").randint(7, 10),
            ctx.draw_rng("width_band").randint(9, 12),
        )
    return (
        ctx.draw_rng("height_band").randint(5, 14),
        ctx.draw_rng("width_band").randint(7, 16),
    )


def _zone_cells(h: int, w: int) -> list[list[tuple[int, int]]]:
    row_groups = ([0], list(range(1, h - 1)), [h - 1])
    col_groups = ([0], list(range(1, w - 1)), [w - 1])
    return [
        [(r, c) for r in rows for c in cols]
        for rows in row_groups
        for cols in col_groups
    ]


def _foreground_palette(ctx, size: int) -> list[int]:
    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    return palette[:size]


def _paint_single_color_zone(
    grid: list[list[int]], cells: list[tuple[int, int]], color: int, rng
) -> None:
    count = 1
    if len(cells) > 1 and rng.random() < 0.35:
        count = 2
    chosen = sorted(rng.sample(cells, min(count, len(cells))))
    for r, c in chosen:
        grid[r][c] = color


def _paint_scan_conflict_zone(
    grid: list[list[int]], cells: list[tuple[int, int]], palette: list[int], rng
) -> None:
    """Paint a zone whose first and last non-zero colors visibly differ."""
    if len(cells) == 1:
        r, c = cells[0]
        grid[r][c] = palette[0]
        return

    count = min(len(cells), len(palette) + rng.randrange(0, 3))
    count = max(count, len(palette))
    chosen = sorted(rng.sample(cells, count))

    # The first non-zero in every zone is palette[0], so the first non-zero in
    # the whole grid is also palette[0].  The final non-zero is palette[-1].
    # Intermediate cells expose every palette member without assigning meaning
    # to a numeric color value.
    assignments = [palette[0]]
    middle = count - 2
    for index in range(middle):
        assignments.append(palette[1 + (index % (len(palette) - 1))])
    assignments.append(palette[-1])
    for (r, c), color in zip(chosen, assignments):
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _default_dimensions(ctx, sample_index, difficulty)
    h = _draw_exact_int(ctx, overrides, "grid_h", default_h)
    w = _draw_exact_int(ctx, overrides, "grid_w", default_w)
    default_pattern = schedule_profile(seed, sample_index, difficulty)
    zone_pattern = _draw_exact_choice(
        ctx, overrides, "zone_pattern", default_pattern, SCHEDULE_PROFILES
    )
    default_palette_size = (
        1 if sample_index % 5 == 0 else 2 + ctx.draw_rng("palette_size_default").randrange(2)
    )
    palette_size = _draw_exact_int(
        ctx, overrides, "palette_size", default_palette_size
    )

    zones = _zone_cells(h, w)
    palette = _foreground_palette(ctx, palette_size)
    for attempt in range(64):
        grid = full_grid(h, w, 0)
        rng = ctx.draw_rng(f"zone_cells_{attempt}")
        for zone_index in ZONE_PATTERNS[zone_pattern]:
            cells = zones[zone_index]
            if palette_size == 1:
                _paint_single_color_zone(grid, cells, palette[0], rng)
            else:
                _paint_scan_conflict_zone(grid, cells, palette, rng)
        if not _has_solid_foreground_2x2(grid):
            return grid
    raise ValueError("could not place zone witnesses without a solid 2x2 alias")



def _has_solid_foreground_2x2(grid: list[list[int]]) -> bool:
    return any(
        all(grid[r + dr][c + dc] != 0 for dr in (0, 1) for dc in (0, 1))
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]) - 1)
    )

def _normalise_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["every grid row must be a list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return None, ["grid must be rectangular with nonempty rows"]
    values = [list(row) for row in grid]
    h, w = len(values), len(values[0])
    if h < 5 or w < 7:
        errors.append(f"grid must be at least 5x7, got {h}x{w}")
    bad = [
        value
        for row in values
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        errors.append("cells must be literal ARC color integers 0..9")
    return values, errors


def _analyse(grid: Any) -> dict[str, Any]:
    values, errors = _normalise_grid(grid)
    if values is None:
        return {"errors": errors}
    h, w = len(values), len(values[0])
    zones = _zone_cells(h, w)
    zone_values = [
        [values[r][c] for r, c in cells if values[r][c] != 0]
        for cells in zones
    ]
    occupied = tuple(index for index, vals in enumerate(zone_values) if vals)
    if not 4 <= len(occupied) <= 8:
        errors.append(
            f"expected 4..8 occupied zones with at least one empty contrast, got {len(occupied)}"
        )
    palette = tuple(sorted({value for vals in zone_values for value in vals}))
    if not palette:
        errors.append("grid must contain at least one non-zero color")
    if _has_solid_foreground_2x2(values):
        errors.append("solid 2x2 foreground blocks are outside the sparse zone-marker grammar")
    pattern = next(
        (name for name, indices in ZONE_PATTERNS.items() if tuple(indices) == occupied),
        None,
    )
    output = [
        [zone_values[3 * out_r + out_c][-1] if zone_values[3 * out_r + out_c] else 0
         for out_c in range(3)]
        for out_r in range(3)
    ]
    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "zones": zones,
        "zone_values": zone_values,
        "occupied": occupied,
        "zone_pattern": pattern,
        "palette": palette,
        "palette_size": len(palette),
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed grids, tiny aliases, all-filled scenes, and weak masks."""
    del difficulty, meta
    return list(_analyse(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """Recognise the canonical 5x7, one-foreground-color sparse manifold."""
    analysis = _analyse(grid)
    reasons = list(analysis.get("errors", []))
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) != (5, 7):
        reasons.append("canonical inputs are exactly 5x7")
    if analysis["palette_size"] != 1:
        reasons.append("canonical inputs use exactly one non-zero color")
    nonzero_count = sum(len(values) for values in analysis["zone_values"])
    if not 4 <= nonzero_count <= 12:
        reasons.append("canonical inputs contain 4..12 non-zero cells")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyse(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    if analysis["zone_pattern"] is None:
        raise ValueError("occupied-zone mask is not one of the declared exact patterns")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "palette_size": analysis["palette_size"],
        "zone_pattern": analysis["zone_pattern"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Exact Python mirror of the selected row-major last-non-zero Racket rule."""
    values, errors = _normalise_grid(grid)
    if values is None or errors:
        raise ValueError("; ".join(errors))
    h, w = len(values), len(values[0])
    output: list[list[int]] = []
    for cells in _zone_cells(h, w):
        value = 0
        for r, c in cells:
            if values[r][c] != 0:
                value = values[r][c]
        if not output or len(output[-1]) == 3:
            output.append([])
        output[-1].append(value)
    return output


def _rival_first_nonzero(grid) -> list[list[int]]:
    values, errors = _normalise_grid(grid)
    if values is None or errors:
        raise ValueError("; ".join(errors))
    h, w = len(values), len(values[0])
    result: list[int] = []
    for cells in _zone_cells(h, w):
        result.append(next((values[r][c] for r, c in cells if values[r][c] != 0), 0))
    return [result[0:3], result[3:6], result[6:9]]


def _rival_occupancy_global_first(grid) -> list[list[int]]:
    values, errors = _normalise_grid(grid)
    if values is None or errors:
        raise ValueError("; ".join(errors))
    first = next((value for row in values for value in row if value != 0), 0)
    h, w = len(values), len(values[0])
    result = [
        first if any(values[r][c] != 0 for r, c in cells) else 0
        for cells in _zone_cells(h, w)
    ]
    return [result[0:3], result[3:6], result[6:9]]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_nonzero_per_zone": _rival_first_nonzero,
    "occupied_zone_uses_global_first_color": _rival_occupancy_global_first,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _refutes_first_nonzero(grid) -> bool:
    analysis = _analyse(grid)
    return not analysis.get("errors") and _rival_first_nonzero(grid) != analysis["output"]


def _refutes_global_occupancy_color(grid) -> bool:
    analysis = _analyse(grid)
    return (
        not analysis.get("errors")
        and _rival_occupancy_global_first(grid) != analysis["output"]
    )


SEMANTIC_WITNESSES = {
    "row_major_last_refutes_first_hit": _refutes_first_nonzero,
    "zone_local_last_color_refutes_global_occupancy_color": _refutes_global_occupancy_color,
}
WITNESS_RIVALS = {
    "row_major_last_refutes_first_hit": ["first_nonzero_per_zone"],
    "zone_local_last_color_refutes_global_occupancy_color": [
        "occupied_zone_uses_global_first_color"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate pairs and reject surviving rivals that change the query answer.

    Scheduled masks provide curriculum variety; a query rotation need not leave
    every mask in the demonstrations.  Identifiability here is relative to the
    declared competitors, including answer-equivalent survivors.
    """
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    lawful_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyse(pair["input"])
        if analysis.get("errors"):
            reasons.append(f"demo {index} input is unlawful: {analysis['errors'][0]}")
            continue
        if pair["output"] != analysis["output"]:
            reasons.append(f"demo {index} output does not match row-major last-non-zero")
            continue
        lawful_pairs.append(pair)

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output grids")
    else:
        analysis = _analyse(query["input"])
        if analysis.get("errors"):
            reasons.append(f"query input is unlawful: {analysis['errors'][0]}")
        elif query["output"] != analysis["output"]:
            reasons.append("query output does not match row-major last-non-zero")
        else:
            for name, rival in LESSON_COMPETITORS.items():
                if (
                    lawful_pairs
                    and all(rival(pair["input"]) == pair["output"] for pair in lawful_pairs)
                    and rival(query["input"]) != query["output"]
                ):
                    reasons.append(
                        f"rival rule {name!r} survives every demonstration "
                        "and changes the query answer"
                    )
    return reasons


def mutation_fixtures():
    """Focused must-reject structural impostors for defect-lint replay."""
    base = generate(991, 2, difficulty="medium")

    all_zero = [[0 for _ in row] for row in base]

    singleton = [[0 for _ in row] for row in base]
    singleton[len(singleton) // 2][len(singleton[0]) // 2] = 3

    all_zones = copy.deepcopy(base)
    for r, c in (
        (0, 0), (0, len(base[0]) // 2), (0, len(base[0]) - 1),
        (len(base) // 2, 0), (len(base) // 2, len(base[0]) // 2),
        (len(base) // 2, len(base[0]) - 1), (len(base) - 1, 0),
        (len(base) - 1, len(base[0]) // 2), (len(base) - 1, len(base[0]) - 1),
    ):
        all_zones[r][c] = 4

    illegal_color = copy.deepcopy(base)
    illegal_color[0][0] = 10

    ragged = copy.deepcopy(base)
    ragged[0] = ragged[0][:-1]

    too_small = [[0 for _ in range(6)] for _ in range(4)]
    too_small[0][0] = too_small[0][2] = too_small[2][0] = too_small[2][2] = 2

    return [
        ("all_zero_rule_hiding_scene", all_zero),
        ("single_occupied_zone", singleton),
        ("all_nine_zones_occupied_no_empty_contrast", all_zones),
        ("illegal_arc_color", illegal_color),
        ("ragged_grid", ragged),
        ("grid_too_small_for_declared_zone_grammar", too_small),
    ]
