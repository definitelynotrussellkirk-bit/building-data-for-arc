"""High-evidence generator for ``Solidify the Box`` (c7c6836fd350).

The authoritative rule finds every green (3) cell, computes their smallest
axis-aligned bounding box, and paints that entire rectangle green on a fresh
zero grid of the same dimensions.  Ordinary lessons are scheduled in four
slots.  Two slots stay tightly anchored to canonical dimensions and palettes;
one uses a tall split-extrema layout; and one adds a *more numerous* non-green
decoy segment outside the green box.  Together those episodes distinguish the
true color-3 bounding-box rule from endpoint-only, all-nonzero, modal-color,
and bbox-outline shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7c6836fd350"
VERSION = "3.0.0"
TASK_ID = "c7c6836fd350"
RULE_HASH = "0af61c7b2115"

SUMMARY = (
    "Find all green (3) cells, fill their complete axis-aligned bounding box "
    "with green on a fresh same-sized black grid, and erase every other color. "
    "A four-slot lesson schedule includes canonical two-color anchors, "
    "split-extrema marker layouts, and a dominant non-green decoy outside the "
    "green box so all-nonzero and modal-color shortcuts are observable."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

INVARIANTS = [
    "the canvas is 6..10 rows by 8..11 columns with ARC colors 0..9",
    "there are 3..5 green (3) marker cells",
    "the green bounding box spans at least three rows and three columns",
    "the green box contains unmarked cells, so solidification is non-identity",
    "optional decoy evidence is one six-cell horizontal segment outside the green box",
    "when present, the decoy is more numerous than the green markers",
]

PALETTE_PROFILES = ("plain", "decoy_dominant")
BBOX_PROFILES = (
    "interior_wide",
    "interior_square",
    "interior_tall",
    "edge_wide",
    "edge_square",
    "edge_tall",
)

AXES = {
    "palette_profile": {
        "type": "enum",
        "default": "four-slot schedule: plain|plain|decoy_dominant|plain",
        "valid": "plain|decoy_dominant",
    },
    "bbox_profile": {
        "type": "enum",
        "default": (
            "four-slot schedule: interior_wide|edge_tall|"
            "interior_wide|edge_square"
        ),
        "valid": "|".join(BBOX_PROFILES),
    },
}

# Every declared override combination is realizable.  Declaring the empty set
# opts the checker into strict incompatibility accounting instead of its legacy
# warning-only policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCHEDULE_PROFILES = (
    "canonical_corner_pair",
    "plain_split_extrema",
    "dominant_decoy_color_trap",
    "canonical_square_split",
)

_SCHEDULE = (
    {
        "palette_profile": "plain",
        "bbox_profile": "interior_wide",
        "green_count": 3,
        "marker_pattern": "corner_pair",
    },
    {
        "palette_profile": "plain",
        "bbox_profile": "edge_tall",
        "green_count": 4,
        "marker_pattern": "split_extrema",
    },
    {
        "palette_profile": "decoy_dominant",
        "bbox_profile": "interior_wide",
        "green_count": 5,
        "marker_pattern": "split_extrema",
    },
    {
        "palette_profile": "plain",
        "bbox_profile": "edge_square",
        "green_count": 4,
        "marker_pattern": "split_extrema",
    },
)

_CANONICAL_DIMS = ((7, 8), (8, 9), (6, 10), (9, 9))
_CANONICAL_DIMS_BY_BAND = {
    "easy": ((7, 8), (8, 9)),
    "medium": _CANONICAL_DIMS,
    "hard": ((8, 9), (9, 9), (6, 10)),
}
_GENERALIZED_DIMS_BY_BAND = {
    "easy": ((8, 10), (8, 11)),
    "medium": ((8, 10), (9, 11), (10, 10)),
    "hard": ((9, 11), (10, 10), (10, 11)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the residue-class teaching role for a generated pair."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    if "palette_profile" in overrides and overrides["palette_profile"] is not None:
        if overrides["palette_profile"] not in PALETTE_PROFILES:
            raise ValueError(
                "palette_profile must be one of "
                f"{PALETTE_PROFILES}, got {overrides['palette_profile']!r}"
            )
    if "bbox_profile" in overrides and overrides["bbox_profile"] is not None:
        if overrides["bbox_profile"] not in BBOX_PROFILES:
            raise ValueError(
                f"bbox_profile must be one of {BBOX_PROFILES}, "
                f"got {overrides['bbox_profile']!r}"
            )
    return "medium" if difficulty is None else difficulty


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _bbox_size_candidates(
    h: int, w: int, *, aspect: str
) -> list[tuple[int, int]]:
    candidates = {
        "wide": ((3, 4), (3, 5), (4, 5), (4, 6)),
        "square": ((3, 3), (4, 4), (5, 5)),
        "tall": ((4, 3), (5, 3), (5, 4), (6, 4)),
    }[aspect]
    # Leave a margin on both dimensions.  Even edge-touching boxes then have a
    # guaranteed opposite-side row where the decoy segment can live.
    return [
        (box_h, box_w)
        for box_h, box_w in candidates
        if box_h <= h - 2 and box_w <= w - 2
    ]


def _choose_bbox(ctx, h: int, w: int, profile: str) -> tuple[int, int, int, int]:
    touch, aspect = profile.split("_", 1)
    candidates = _bbox_size_candidates(h, w, aspect=aspect)
    if not candidates:
        raise ValueError(f"cannot realize bbox_profile={profile!r} on {h}x{w}")
    box_h, box_w = ctx.draw_choice("bbox_size", candidates)
    rng = ctx.draw_rng("bbox_position")

    if touch == "interior":
        top = rng.randint(1, h - box_h - 1)
        left = rng.randint(1, w - box_w - 1)
    else:
        side = ctx.draw_choice("edge_side", ("top", "right", "bottom", "left"))
        if side == "top":
            top = 0
            left = rng.randint(1, w - box_w - 1)
        elif side == "bottom":
            top = h - box_h
            left = rng.randint(1, w - box_w - 1)
        elif side == "left":
            top = rng.randint(1, h - box_h - 1)
            left = 0
        else:
            top = rng.randint(1, h - box_h - 1)
            left = w - box_w
    return top, left, top + box_h - 1, left + box_w - 1


def _marker_cells(
    bbox: tuple[int, int, int, int], count: int, pattern: str
) -> list[tuple[int, int]]:
    top, left, bottom, right = bbox
    mid_r = (top + bottom) // 2
    mid_c = (left + right) // 2

    if pattern == "corner_pair":
        # Row-major first and last markers are opposite bbox corners.  This
        # intentionally supplies one episode on which the endpoint shortcut
        # fits, so the split-extrema episodes are meaningful discriminators.
        ordered = [
            (top, left),
            (bottom, right),
            (top, right - 1),
            (bottom - 1, left),
            (mid_r, mid_c),
        ]
    elif count == 3:
        # Three markers jointly define four extrema, but no single pair does.
        ordered = [(top, mid_c), (bottom, left), (mid_r, right)]
    else:
        ordered = [
            (top, mid_c),
            (bottom, mid_c),
            (mid_r, left),
            (mid_r, right),
            (mid_r, mid_c),
        ]

    cells: list[tuple[int, int]] = []
    for cell in ordered:
        if cell not in cells:
            cells.append(cell)
        if len(cells) == count:
            return cells
    raise AssertionError(f"could not place {count} distinct markers in bbox {bbox}")


def _place_dominant_decoy(
    ctx,
    grid: list[list[int]],
    bbox: tuple[int, int, int, int],
    green_count: int,
) -> None:
    h, w = len(grid), len(grid[0])
    top, _left, bottom, _right = bbox
    rows_outside = [row for row in range(h) if row < top or row > bottom]
    if not rows_outside or w < 6:
        raise ValueError("decoy profile requires a row outside the green bbox")
    rng = ctx.draw_rng("decoy_segment")
    row = rows_outside[rng.randrange(len(rows_outside))]
    left = rng.randint(0, w - 6)
    color = ctx.draw_color("decoy_color", exclude={0, 3})
    for col in range(left, left + 6):
        grid[row][col] = color
    if 6 <= green_count:
        raise AssertionError("decoy must remain more numerous than green markers")


def _filled_bbox_output(
    grid: list[list[int]], cells: list[tuple[int, int]], color: int = 3
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    if not cells:
        return output
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            output[row][col] = color
    return output


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list of rows"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["every row must be a nonempty list"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid values must be integer ARC colors 0..9"]}

    height = len(grid)
    if not 6 <= height <= 10:
        errors.append(f"height must be 6..10, got {height}")
    if not 8 <= width <= 11:
        errors.append(f"width must be 8..11, got {width}")

    green = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    ]
    if not 3 <= len(green) <= 5:
        errors.append(f"expected 3..5 green cells, found {len(green)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "green_cells": tuple(green),
        }

    rows = [row for row, _col in green]
    cols = [col for _row, col in green]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    bbox_h, bbox_w = bottom - top + 1, right - left + 1
    if bbox_h < 3:
        errors.append(f"green bbox row span must be at least 3, got {bbox_h}")
    if bbox_w < 3:
        errors.append(f"green bbox column span must be at least 3, got {bbox_w}")
    if bbox_h * bbox_w <= len(green):
        errors.append("green bbox must contain cells that solidification adds")

    extra_colors = sorted({value for row in grid for value in row} - {0, 3})
    decoy_cells: list[tuple[int, int]] = []
    decoy_color: int | None = None
    if len(extra_colors) > 1:
        errors.append(f"expected at most one decoy color, got {extra_colors}")
    elif extra_colors:
        decoy_color = extra_colors[0]
        decoy_cells = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == decoy_color
        ]
        if len(decoy_cells) != 6:
            errors.append(f"decoy segment must contain exactly 6 cells, got {len(decoy_cells)}")
        decoy_rows = {row for row, _col in decoy_cells}
        decoy_cols = sorted(col for _row, col in decoy_cells)
        if len(decoy_rows) != 1:
            errors.append("decoy cells must form one horizontal segment")
        if decoy_cols and decoy_cols != list(range(decoy_cols[0], decoy_cols[0] + len(decoy_cols))):
            errors.append("decoy segment columns must be consecutive")
        if decoy_rows:
            decoy_row = next(iter(decoy_rows))
            if top <= decoy_row <= bottom:
                errors.append("decoy segment must lie outside the green bbox rows")
        if len(decoy_cells) <= len(green):
            errors.append("decoy must be more numerous than the green markers")

    aspect = "square" if bbox_h == bbox_w else ("wide" if bbox_w > bbox_h else "tall")
    touches_edge = top == 0 or left == 0 or bottom == height - 1 or right == width - 1
    bbox_profile = f"{'edge' if touches_edge else 'interior'}_{aspect}"
    palette_profile = "decoy_dominant" if extra_colors else "plain"

    ordered_green = sorted(green)
    endpoint_output = _filled_bbox_output(grid, [ordered_green[0], ordered_green[-1]])
    truth = _filled_bbox_output(grid, green)
    opposite_corner_pair = any(
        {first, second} == {(top, left), (bottom, right)}
        or {first, second} == {(top, right), (bottom, left)}
        for index, first in enumerate(green)
        for second in green[index + 1:]
    )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "colors": tuple(sorted({value for row in grid for value in row})),
        "green_cells": tuple(sorted(green)),
        "green_count": len(green),
        "bbox": (top, left, bottom, right),
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "bbox_area": bbox_h * bbox_w,
        "bbox_profile": bbox_profile,
        "palette_profile": palette_profile,
        "decoy_color": decoy_color,
        "decoy_cells": tuple(sorted(decoy_cells)),
        "decoy_count": len(decoy_cells),
        "opposite_corner_pair": opposite_corner_pair,
        "endpoint_bbox_matches": endpoint_output == truth,
        "truth": truth,
    }


def observe_overrides(grid) -> dict[str, str]:
    """Recover both exact declared semantic axes from the returned grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "palette_profile": facts["palette_profile"],
        "bbox_profile": facts["bbox_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lawful input grammar and any requested exact axes."""
    del difficulty
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {name: candidate[name] for name in AXES if name in candidate}
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if value is not None and observed[name] != value:
                errors.append(f"override {name}={value!r} realized as {observed[name]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the demonstrated two-color dimensional/geometry manifold."""
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if facts["palette_profile"] != "plain":
        errors.append("canonical inputs contain only colors 0 and 3")
    if (facts["height"], facts["width"]) not in _CANONICAL_DIMS:
        errors.append(
            f"dimensions {facts['height']}x{facts['width']} are outside canonical profiles"
        )
    if facts["green_count"] not in (3, 4):
        errors.append(f"canonical green count is 3 or 4, got {facts['green_count']}")
    if facts["bbox_w"] < facts["bbox_h"]:
        errors.append("canonical green bboxes are wide or square, not tall")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket program remains authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid Solidify-the-Box grid: " + "; ".join(facts["errors"]))
    return [row[:] for row in facts["truth"]]


def _rival_all_nonzero_bbox(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    ]
    return _filled_bbox_output(grid, cells)


def _rival_modal_nonzero_bbox(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return full_grid(len(grid), len(grid[0]), 0)
    modal = sorted(counts, key=lambda color: (-counts[color], color))[0]
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == modal
    ]
    return _filled_bbox_output(grid, cells)


def _rival_row_major_endpoints(grid: list[list[int]]) -> list[list[int]]:
    green = sorted(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 3
    )
    return _filled_bbox_output(grid, [green[0], green[-1]])


def _rival_bbox_outline(grid: list[list[int]]) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    top, left, bottom, right = facts["bbox"]
    output = full_grid(facts["height"], facts["width"], 0)
    for col in range(left, right + 1):
        output[top][col] = 3
        output[bottom][col] = 3
    for row in range(top, bottom + 1):
        output[row][left] = 3
        output[row][right] = 3
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "bbox_of_all_nonzero_cells": _rival_all_nonzero_bbox,
    "bbox_of_modal_nonzero_color": _rival_modal_nonzero_bbox,
    "bbox_from_row_major_endpoints": _rival_row_major_endpoints,
    "outline_green_bbox_only": _rival_bbox_outline,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _lawful_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _witness_decoy(grid) -> bool:
    facts = _lawful_facts(grid)
    return (
        facts is not None
        and facts["palette_profile"] == "decoy_dominant"
        and _rival_all_nonzero_bbox(grid) != facts["truth"]
    )


def _witness_modal_trap(grid) -> bool:
    facts = _lawful_facts(grid)
    return (
        facts is not None
        and facts["decoy_count"] > facts["green_count"]
        and _rival_modal_nonzero_bbox(grid) != facts["truth"]
    )


def _witness_split_extrema(grid) -> bool:
    facts = _lawful_facts(grid)
    return facts is not None and not facts["endpoint_bbox_matches"]


def _witness_solid_interior(grid) -> bool:
    facts = _lawful_facts(grid)
    return facts is not None and _rival_bbox_outline(grid) != facts["truth"]


SEMANTIC_WITNESSES = {
    "decoy_outside_green_bbox": _witness_decoy,
    "dominant_decoy_refutes_modal_color": _witness_modal_trap,
    "split_extrema_refute_endpoint_bbox": _witness_split_extrema,
    "solid_interior_refutes_bbox_outline": _witness_solid_interior,
}

WITNESS_RIVALS = {
    "decoy_outside_green_bbox": ["bbox_of_all_nonzero_cells"],
    "dominant_decoy_refutes_modal_color": ["bbox_of_modal_nonzero_color"],
    "split_extrema_refute_endpoint_bbox": ["bbox_from_row_major_endpoints"],
    "solid_interior_refutes_bbox_outline": ["outline_green_bbox_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any four-demo lesson that leaves a named shortcut viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    demo_facts: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not isinstance(pair.get("input"), list):
            reasons.append(f"demonstration {index} is missing an input grid")
            continue
        facts = _analyze(pair["input"])
        if facts["errors"]:
            reasons.append(
                f"demonstration {index} violates the grammar: "
                + "; ".join(facts["errors"])
            )
            continue
        expected = facts["truth"]
        if pair.get("output") != expected:
            reasons.append(f"demonstration {index} output disagrees with the green bbox rule")
        demo_facts.append(facts)

    if reasons:
        return reasons
    if not any(facts["palette_profile"] == "decoy_dominant" for facts in demo_facts):
        reasons.append("demonstrations omit the non-green decoy discriminator")
    if not any(not facts["endpoint_bbox_matches"] for facts in demo_facts):
        reasons.append("demonstrations omit a split-extrema endpoint counterexample")
    if not any(not strict_canonical_like(pair["input"]) for pair in demos):
        reasons.append("demonstrations omit a strict canonical-profile anchor")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives:
            reasons.append(f"named competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or not isinstance(query.get("input"), list):
        reasons.append("query is missing an input grid")
    else:
        query_facts = _analyze(query["input"])
        if query_facts["errors"]:
            reasons.append("query violates the grammar: " + "; ".join(query_facts["errors"]))
        elif query.get("output") is not None and query["output"] != query_facts["truth"]:
            reasons.append("query output disagrees with the green bbox rule")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    slot = int(sample_index) % EXAMPLES_NEEDED
    scheduled = _SCHEDULE[slot]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    palette_profile = _scheduled_choice(
        ctx,
        "palette_profile",
        PALETTE_PROFILES,
        scheduled["palette_profile"],
    )
    bbox_profile = _scheduled_choice(
        ctx,
        "bbox_profile",
        BBOX_PROFILES,
        scheduled["bbox_profile"],
    )

    dims_options = (
        _CANONICAL_DIMS_BY_BAND[band]
        if palette_profile == "plain"
        else _GENERALIZED_DIMS_BY_BAND[band]
    )
    height, width = ctx.draw_choice("grid_dims", dims_options)
    bbox = _choose_bbox(ctx, height, width, bbox_profile)
    green_count = int(scheduled["green_count"])
    markers = _marker_cells(bbox, green_count, str(scheduled["marker_pattern"]))

    grid = full_grid(height, width, 0)
    for row, col in markers:
        grid[row][col] = 3
    if palette_profile == "decoy_dominant":
        _place_dominant_decoy(ctx, grid, bbox, green_count)

    errors = self_check(
        grid,
        difficulty=band,
        meta={"overrides": ctx.recorded_draws()},
    )
    if errors:
        raise AssertionError("generated invalid Solidify-the-Box input: " + "; ".join(errors))
    return grid
