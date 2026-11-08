"""Semantic generator for ARC task ``401aff907774`` (``S7_E3``).

Two yellow (4) singleton markers are opposite corners of an axis-aligned
rectangle.  The answer is every cell strictly between their rows and columns;
the markers, surrounding canvas, and any lawful outside distractors are not
returned.  A three-profile schedule preserves exact canonical morphology while
forcing demonstrations that refute color-blind bounding-box and tight-content
crop shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "401aff907774"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "abc6ea951972"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Exactly two yellow (4) markers occupy opposite corners of a rectangle; "
    "return the complete interior subgrid, preserving every color and zero."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "there are exactly two color-4 markers in different rows and columns",
    "the marker rectangle has a 2..5 by 2..5 interior",
    "the interior contains at least two colored cells and at least one zero",
    "interior colors never use 4, so the two crop markers are unambiguous",
    "zero to four non-4 colored distractor cells may occur outside the marker rectangle",
]

COUNTER_HYPOTHESES = [
    "crop the bounding box of every nonzero cell and inset it by one",
    "crop the marker bounding box including the yellow markers",
    "tightly crop only the colored cells inside the marker rectangle",
    "assume the upper marker is always the left marker",
    "replace the interior by a solid block or discard its zeros",
    "copy only the colored pattern, ignoring its zero padding",
    "memorize a fixed output size, marker position, or canonical palette",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 8..10 or rng 7..14",
        "valid": "7..14",
        "doc": "Full input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9..11 or rng 7..14",
        "valid": "7..14",
        "doc": "Full input-grid width.",
    },
    "crop_h": {
        "type": "int",
        "default": "canonical 3..5 or rng 2..5",
        "valid": "2..5",
        "doc": "Number of rows strictly between the two markers.",
    },
    "crop_w": {
        "type": "int",
        "default": "canonical 4..5 or rng 2..5",
        "valid": "2..5",
        "doc": "Number of columns strictly between the two markers.",
    },
    "marker_diagonal": {
        "type": "enum",
        "default": "scheduled main or anti",
        "valid": "main|anti",
        "doc": "Which pair of opposite marker-bbox corners contains color 4.",
    },
    "interior_palette_size": {
        "type": "int",
        "default": "canonical 2..3 or rng 1..3",
        "valid": "1..3",
        "doc": "Distinct nonzero, non-4 colors strictly inside the marker rectangle.",
    },
    "ignored_distractor_count": {
        "type": "int",
        "default": "0 canonical; scheduled 0..4 generalized",
        "valid": "0..4",
        "doc": "Colored non-4 cells outside the strict output interior, excluding the markers.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
SCHEDULE_PROFILES = (
    "canonical_profile",
    "outside_distractor",
    "zero_border",
)

# Canonical canvas dimensions and exact interiors, train then test.
_CANONICAL_CASES = (
    (8, 9, ((2, 3, 0, 0), (2, 0, 3, 0), (0, 3, 3, 2))),
    (
        9,
        10,
        (
            (1, 2, 0, 0, 0),
            (1, 0, 2, 3, 0),
            (0, 0, 2, 3, 0),
            (3, 3, 0, 0, 1),
        ),
    ),
    (
        10,
        11,
        (
            (0, 0, 1, 2, 0),
            (2, 2, 1, 0, 0),
            (0, 2, 0, 2, 0),
            (0, 0, 1, 1, 1),
            (3, 0, 0, 0, 3),
        ),
    ),
)


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")

    integer_bounds = {
        "grid_h": (7, 14),
        "grid_w": (7, 14),
        "crop_h": (2, 5),
        "crop_w": (2, 5),
        "interior_palette_size": (1, 3),
        "ignored_distractor_count": (0, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "marker_diagonal":
            if not isinstance(value, str):
                raise TypeError("override 'marker_diagonal' must be a string")
            if value not in ("main", "anti"):
                raise ValueError("override 'marker_diagonal' must be 'main' or 'anti'")
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        lo, hi = integer_bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Any three consecutive sample indexes contain every teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _marker_facts(grid) -> tuple[list[tuple[int, int]], tuple[int, int, int, int] | None]:
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    if len(markers) != 2:
        return markers, None
    (ra, ca), (rb, cb) = markers
    return markers, (min(ra, rb), max(ra, rb), min(ca, cb), max(ca, cb))


def _interior_from_box(grid, box: tuple[int, int, int, int]):
    r0, r1, c0, c1 = box
    return [list(row[c0 + 1:c1]) for row in grid[r0 + 1:r1]]


def _authoritative_python(grid):
    markers, box = _marker_facts(grid)
    if len(markers) != 2 or box is None:
        return []
    return _interior_from_box(grid, box)


def _outside_cells(grid, box: tuple[int, int, int, int]):
    r0, r1, c0, c1 = box
    return [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 4) and not (r0 <= r <= r1 and c0 <= c <= c1)
    ]


def _ignored_distractor_cells(grid, box: tuple[int, int, int, int]):
    r0, r1, c0, c1 = box
    return [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 4)
        and not (r0 < r < r1 and c0 < c < c1)
    ]


def _pattern_signature(grid) -> tuple[tuple[int, ...], ...]:
    """Normalize nonzero colors by first occurrence while preserving equality."""
    mapping: dict[int, int] = {}
    next_label = 1
    rows: list[tuple[int, ...]] = []
    for row in grid:
        out: list[int] = []
        for value in row:
            if value == 0:
                out.append(0)
                continue
            if value not in mapping:
                mapping[value] = next_label
                next_label += 1
            out.append(mapping[value])
        rows.append(tuple(out))
    return tuple(rows)


def _transform_grid(grid, transform: int):
    rows = tuple(tuple(row) for row in grid)
    if transform >= 4:
        rows = tuple(tuple(reversed(row)) for row in rows)
        transform -= 4
    for _ in range(transform):
        rows = tuple(
            tuple(rows[len(rows) - 1 - r][c] for r in range(len(rows)))
            for c in range(len(rows[0]))
        )
    return rows


def _transform_diagonal(transform: int) -> str:
    # Starting markers are top-left and bottom-right.  A quarter turn or a
    # left-right reflection swaps them to the anti-diagonal.
    reflected = transform >= 4
    rotations = transform - 4 if reflected else transform
    anti = reflected ^ (rotations % 2 == 1)
    return "anti" if anti else "main"


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    markers, box = _marker_facts(grid)
    result.update({"grid_h": h, "grid_w": w, "marker_count": len(markers), "marker_box": box})
    if box is None:
        return result
    r0, r1, c0, c1 = box
    crop_h = r1 - r0 - 1
    crop_w = c1 - c0 - 1
    interior = _interior_from_box(grid, box) if crop_h > 0 and crop_w > 0 else []
    palette = sorted({value for row in interior for value in row if value not in (0, 4)})
    outside = _outside_cells(grid, box)
    ignored = _ignored_distractor_cells(grid, box)
    top_marker = min(markers)
    diagonal = "main" if top_marker[1] == c0 else "anti"
    edge_nonzero = {
        "top": sum(value != 0 for value in interior[0]) if interior else 0,
        "bottom": sum(value != 0 for value in interior[-1]) if interior else 0,
        "left": sum(row[0] != 0 for row in interior) if interior else 0,
        "right": sum(row[-1] != 0 for row in interior) if interior else 0,
    }
    result.update(
        {
            "crop_h": crop_h,
            "crop_w": crop_w,
            "marker_diagonal": diagonal,
            "interior": interior,
            "interior_signature": _pattern_signature(interior),
            "interior_palette": palette,
            "interior_palette_size": len(palette),
            "interior_nonzero_count": sum(value != 0 for row in interior for value in row),
            "interior_zero_count": sum(value == 0 for row in interior for value in row),
            "interior_color4_count": sum(value == 4 for row in interior for value in row),
            "outside_inclusive_nonzero_count": len(outside),
            "outside_inclusive_nonzero_cells": outside,
            "ignored_distractor_count": len(ignored),
            "ignored_distractor_cells": ignored,
            "edge_nonzero": edge_nonzero,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid input grammar, including all canonicals."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    h, w = facts["grid_h"], facts["grid_w"]
    if not 7 <= h <= 14 or not 7 <= w <= 14:
        errors.append(f"canvas must be 7..14 per side, found {h}x{w}")
    if facts["marker_count"] != 2 or facts.get("marker_box") is None:
        errors.append(f"expected exactly two color-4 markers, found {facts['marker_count']}")
        return errors
    crop_h, crop_w = facts["crop_h"], facts["crop_w"]
    if not 2 <= crop_h <= 5 or not 2 <= crop_w <= 5:
        errors.append(f"marker interior must be 2..5 by 2..5, found {crop_h}x{crop_w}")
        return errors
    if facts["interior_color4_count"]:
        errors.append("color 4 may appear only at the two crop markers")
    if facts["interior_nonzero_count"] < 2:
        errors.append("interior must contain at least two colored cells")
    if facts["interior_zero_count"] < 1:
        errors.append("interior must retain at least one zero cell")
    if not 1 <= facts["interior_palette_size"] <= 3:
        errors.append(
            "interior must use 1..3 nonzero non-marker colors, found "
            f"{facts['interior_palette_size']}"
        )
    if facts["ignored_distractor_count"] > 4:
        errors.append(
            f"at most four ignored distractor cells are allowed, found {facts['ignored_distractor_count']}"
        )
    return errors


# Exact canonical-profile signatures under the full D4 nuisance group.
_CANONICAL_SIGNATURES: frozenset[tuple[int, int, tuple[tuple[int, ...], ...]]] = frozenset(
    (
        len(_transform_grid([[0] * canvas_w for _ in range(canvas_h)], transform)),
        len(_transform_grid([[0] * canvas_w for _ in range(canvas_h)], transform)[0]),
        _pattern_signature(_transform_grid(interior, transform)),
    )
    for canvas_h, canvas_w, interior in _CANONICAL_CASES
    for transform in range(8)
)


def strict_canonical_like(grid) -> list[str]:
    """Exact canonical morphology up to D4, translation, and color renaming."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["ignored_distractor_count"] != 0:
        reasons.append("canonical inputs have no nonzero cells outside the marker rectangle")
    key = (facts["grid_h"], facts["grid_w"], facts["interior_signature"])
    if key not in _CANONICAL_SIGNATURES:
        reasons.append("interior equality pattern/canvas size is not a canonical D4 variant")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts.get("marker_box") is None:
        raise ValueError("cannot observe axes from an invalid marker scene")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "crop_h": facts["crop_h"],
        "crop_w": facts["crop_w"],
        "marker_diagonal": facts["marker_diagonal"],
        "interior_palette_size": facts["interior_palette_size"],
        "ignored_distractor_count": facts["ignored_distractor_count"],
    }


def _draw_palette(ctx, n: int, label: str) -> tuple[int, ...]:
    return ctx.draw_distinct_colors(label, n=n, exclude={0, 4})


def _paint_interior(
    crop_h: int,
    crop_w: int,
    palette: tuple[int, ...],
    rng,
    *,
    zero_border: bool,
):
    cells = [(r, c) for r in range(crop_h) for c in range(crop_w)]
    forbidden_edge: set[tuple[int, int]] = set()
    if zero_border:
        side = rng.choice(("top", "bottom", "left", "right"))
        if side == "top":
            forbidden_edge = {(0, c) for c in range(crop_w)}
        elif side == "bottom":
            forbidden_edge = {(crop_h - 1, c) for c in range(crop_w)}
        elif side == "left":
            forbidden_edge = {(r, 0) for r in range(crop_h)}
        else:
            forbidden_edge = {(r, crop_w - 1) for r in range(crop_h)}
    candidates = [cell for cell in cells if cell not in forbidden_edge]
    minimum = max(2, len(palette))
    maximum = max(minimum, min(len(candidates), crop_h * crop_w - 1))
    target = rng.randint(minimum, maximum)
    rng.shuffle(candidates)
    occupied = candidates[:target]
    if len(occupied) < len(palette):
        raise ValueError("interior has fewer available cells than requested colors")
    values: dict[tuple[int, int], int] = {}
    for cell, color in zip(occupied, palette):
        values[cell] = color
    for cell in occupied[len(palette):]:
        values[cell] = rng.choice(palette)
    return [
        [values.get((r, c), 0) for c in range(crop_w)]
        for r in range(crop_h)
    ]


def _place_scene(
    h: int,
    w: int,
    interior,
    diagonal: str,
    outside_count: int,
    rng,
):
    crop_h, crop_w = len(interior), len(interior[0])
    r0 = rng.randint(0, h - crop_h - 2)
    c0 = rng.randint(0, w - crop_w - 2)
    r1 = r0 + crop_h + 1
    c1 = c0 + crop_w + 1
    grid = full_grid(h, w, 0)
    if diagonal == "main":
        marker_cells = ((r0, c0), (r1, c1))
    else:
        marker_cells = ((r0, c1), (r1, c0))
    for r, c in marker_cells:
        grid[r][c] = 4
    for dr, row in enumerate(interior):
        for dc, value in enumerate(row):
            grid[r0 + 1 + dr][c0 + 1 + dc] = value

    outside_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (r0 <= r <= r1 and c0 <= c <= c1)
    ]
    border_candidates = [
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r in (r0, r1) or c in (c0, c1)) and (r, c) not in marker_cells
    ]
    rng.shuffle(outside_candidates)
    rng.shuffle(border_candidates)
    candidates = outside_candidates + border_candidates
    distractor_palette = [value for row in interior for value in row if value not in (0, 4)]
    if not distractor_palette:
        distractor_palette = [1]
    for idx, (r, c) in enumerate(candidates[:outside_count]):
        grid[r][c] = distractor_palette[idx % len(distractor_palette)]
    return grid


def _generate_canonical_profile(ctx):
    rng = ctx.draw_rng("canonical_profile")
    canvas_h, canvas_w, base_interior = rng.choice(_CANONICAL_CASES)
    transform = rng.randrange(8)
    interior = _transform_grid(base_interior, transform)
    if transform % 4 in (1, 3):
        h0, w0 = canvas_w, canvas_h
    else:
        h0, w0 = canvas_h, canvas_w
    diagonal = _transform_diagonal(transform)
    colors_in_order = []
    for row in interior:
        for value in row:
            if value and value not in colors_in_order:
                colors_in_order.append(value)
    palette = _draw_palette(ctx, len(colors_in_order), "canonical_palette")
    remap = dict(zip(colors_in_order, palette))
    interior = tuple(tuple(remap.get(value, 0) for value in row) for row in interior)

    h = ctx.draw_int("grid_h", h0, h0)
    w = ctx.draw_int("grid_w", w0, w0)
    crop_h = ctx.draw_int("crop_h", len(interior), len(interior))
    crop_w = ctx.draw_int("crop_w", len(interior[0]), len(interior[0]))
    ctx.draw_choice("marker_diagonal", (diagonal,))
    ctx.draw_int("interior_palette_size", len(palette), len(palette))
    ctx.draw_int("ignored_distractor_count", 0, 0)
    place_rng = ctx.draw_rng("canonical_position")
    return _place_scene(h, w, interior, diagonal, 0, place_rng)


def _draw_general_axis_ranges(ctx, band: str, profile: str, overrides: dict[str, Any]):
    if overrides:
        h = ctx.draw_int("grid_h", 7, 14)
        w = ctx.draw_int("grid_w", 7, 14)
        crop_h = ctx.draw_int("crop_h", 2, 5)
        crop_w = ctx.draw_int("crop_w", 2, 5)
        diagonal = ctx.draw_choice("marker_diagonal", ("main", "anti"))
        palette_size = ctx.draw_int("interior_palette_size", 1, 3)
        outside_count = ctx.draw_int("ignored_distractor_count", 0, 4)
        return h, w, crop_h, crop_w, diagonal, palette_size, outside_count

    size_ranges = {
        "easy": (7, 10),
        "medium": (8, 12),
        "hard": (10, 14),
    }
    lo, hi = size_ranges[band]
    h = ctx.draw_int("grid_h", lo, hi)
    w = ctx.draw_int("grid_w", lo, hi)
    crop_h = ctx.draw_int("crop_h", 2, min(5, h - 3))
    crop_w = ctx.draw_int("crop_w", 2, min(5, w - 2))
    if profile == "outside_distractor":
        diagonal = ctx.draw_choice("marker_diagonal", ("anti",))
        palette_size = ctx.draw_int("interior_palette_size", 3, 3)
        outside_count = ctx.draw_int("ignored_distractor_count", 2, 4)
    else:
        diagonal = ctx.draw_choice("marker_diagonal", ("main",))
        # A zero-border profile reserves one full edge.  Keep the requested
        # palette observable and feasible even for the 2x2 boundary case.
        available_after_edge = crop_h * crop_w - max(crop_h, crop_w)
        palette_size = ctx.draw_int(
            "interior_palette_size", 2, min(3, available_after_edge)
        )
        outside_count = ctx.draw_int("ignored_distractor_count", 0, 1)
    return h, w, crop_h, crop_w, diagonal, palette_size, outside_count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)
    if profile == "canonical_profile" and not overrides:
        grid = _generate_canonical_profile(ctx)
    else:
        h, w, crop_h, crop_w, diagonal, palette_size, outside_count = _draw_general_axis_ranges(
            ctx, band, profile, overrides
        )
        palette = _draw_palette(ctx, palette_size, "interior_palette")
        interior_rng = ctx.draw_rng("interior_pattern")
        interior = _paint_interior(
            crop_h,
            crop_w,
            palette,
            interior_rng,
            zero_border=(profile == "zero_border" and not overrides),
        )
        grid = _place_scene(
            h,
            w,
            interior,
            diagonal,
            outside_count,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Named rival rules and task-linked lesson identifiability
# ---------------------------------------------------------------------------


def _bbox_of_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return None
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def _rival_all_nonzero_bbox_inset(grid):
    box = _bbox_of_nonzero(grid)
    if box is None:
        return []
    r0, r1, c0, c1 = box
    return [list(row[c0 + 1:c1]) for row in grid[r0 + 1:r1]]


def _rival_inclusive_marker_bbox(grid):
    _, box = _marker_facts(grid)
    if box is None:
        return []
    r0, r1, c0, c1 = box
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _rival_tight_interior_nonzero_crop(grid):
    interior = _authoritative_python(grid)
    box = _bbox_of_nonzero(interior)
    if box is None:
        return []
    r0, r1, c0, c1 = box
    return [list(row[c0:c1 + 1]) for row in interior[r0:r1 + 1]]


def _rival_ordered_main_diagonal_only(grid):
    markers, _ = _marker_facts(grid)
    if len(markers) != 2:
        return []
    (r0, c0), (r1, c1) = sorted(markers)
    return [list(row[c0 + 1:c1]) for row in grid[r0 + 1:r1]]


def _rival_solid_interior(grid):
    interior = _authoritative_python(grid)
    colors = [value for row in interior for value in row if value != 0]
    if not interior or not colors:
        return []
    fill = Counter(colors).most_common(1)[0][0]
    return [[fill for _ in row] for row in interior]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "all_nonzero_bbox_inset": _rival_all_nonzero_bbox_inset,
    "inclusive_marker_bbox": _rival_inclusive_marker_bbox,
    "tight_interior_nonzero_crop": _rival_tight_interior_nonzero_crop,
    "ordered_main_diagonal_only": _rival_ordered_main_diagonal_only,
    "solid_interior": _rival_solid_interior,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "all_nonzero_bbox_inset": _rival_all_nonzero_bbox_inset,
    "tight_interior_nonzero_crop": _rival_tight_interior_nonzero_crop,
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _rival_disagrees(name: str, grid) -> bool:
    return not _grids_equal(SEMANTIC_RIVALS[name](grid), _authoritative_python(grid))


SEMANTIC_WITNESSES = {
    "all_nonzero_bbox_inset": lambda grid: _rival_disagrees("all_nonzero_bbox_inset", grid),
    "inclusive_marker_bbox": lambda grid: _rival_disagrees("inclusive_marker_bbox", grid),
    "tight_interior_nonzero_crop": lambda grid: _rival_disagrees("tight_interior_nonzero_crop", grid),
    "ordered_main_diagonal_only": lambda grid: _rival_disagrees("ordered_main_diagonal_only", grid),
    "solid_interior": lambda grid: _rival_disagrees("solid_interior", grid),
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson for which a named wrong rule survives every demo."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits_demos:
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives every demo and the query")
            else:
                reasons.append(f"competitor {name!r} fits every demo but disagrees on query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
