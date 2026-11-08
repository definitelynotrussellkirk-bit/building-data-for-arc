"""Generator for 12b:m78 — recolor a cropped canvas through a two-row legend.

The first two rows are aligned source/target legend pairs, row 2 is an empty
separator, and rows 3+ are the canvas.  The output is the cropped canvas with
all mapped source colors replaced by their targets; unmapped colors pass
through unchanged.

The official task uses compact 6-7 column canvases with three legend pairs and
moderately dense, texture-free bodies.  Ordinary draws keep a substantial
linked prior on those profiles, while generalized draws vary size, pair count,
legend placement, body density, and the rule's unmapped-color fallback.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69cab6228fdc"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
# sha256[:12] of the whitespace-normalized selected canonical program_solution.
RULE_HASH = "8fec6004f588"

SUMMARY = (
    "Rows 0 and 1 contain aligned nonzero source->target legend pairs; row 2 "
    "is all-zero separation. Crop away those three rows. In the remaining "
    "canvas replace each legend source color by its paired target and preserve "
    "0 plus any color absent from the legend."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and row 2 is an all-zero separator",
    "2-4 aligned legend pairs occupy rows 0 and 1 with no half-pair columns",
    "legend sources and targets are all nonzero, pairwise distinct, and disjoint",
    "every legend source appears in the body so every declared mapping is taught",
    "the body is cropped from rows 3+ and contains a visible recoloring",
    "up to two unmapped body colors each appear at least twice and pass through",
]

LEGEND_LAYOUTS = ("scattered", "contiguous")
BODY_PROFILES = ("sparse", "medium", "dense")
PASSTHROUGH_MODES = ("absent", "present")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked official prior or difficulty-aware draw",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "linked official prior or difficulty-aware draw",
        "valid": "6..14",
    },
    "n_pairs": {
        "type": "int",
        "default": "linked official prior uses 3; otherwise difficulty-aware 2..4",
        "valid": "2..4",
    },
    "legend_layout": {
        "type": "str",
        "default": "linked official prior or keyed choice",
        "valid": "|".join(LEGEND_LAYOUTS),
    },
    "body_profile": {
        "type": "str",
        "default": "linked official prior or keyed density band",
        "valid": "|".join(BODY_PROFILES),
    },
    "passthrough": {
        "type": "str",
        "default": "A/P/P/A sample-index schedule",
        "valid": "|".join(PASSTHROUGH_MODES),
    },
}

# Every three-consecutive-example lesson sees both the mapped-only branch and
# the unmapped-color fallback branch, regardless of its starting residue.
_PASSTHROUGH_SCHEDULE = ("absent", "present", "present", "absent")
SCHEDULE_PROFILES = PASSTHROUGH_MODES

# (height, width, body profile, legend layout) mirrors all official dimensions
# and their medium/dense occupancy range.  The linked prior is only eligible on
# scheduled mapped-only draws, so it does not erase fallback witnesses.
_LINKED_CANONICAL_PROFILES = (
    (9, 6, "dense", "scattered"),
    (7, 6, "medium", "scattered"),
    (7, 6, "dense", "scattered"),
    (8, 6, "dense", "scattered"),
    (8, 7, "dense", "contiguous"),
)
_LINKED_PRIOR_WHEN_ABSENT = 0.72

_BAND_H = {
    "easy": (7, 9),
    "medium": (7, 11),
    "hard": (10, 14),
    None: (7, 14),
}
_BAND_W = {
    "easy": (6, 8),
    "medium": (6, 11),
    "hard": (10, 14),
    None: (6, 14),
}
_BAND_PAIRS = {
    "easy": (2, 3),
    "medium": (2, 4),
    "hard": (3, 4),
    None: (2, 4),
}
_BAND_BODY_PROFILES = {
    "easy": ("medium", "dense", "sparse"),
    "medium": BODY_PROFILES,
    "hard": ("dense", "medium", "sparse"),
    None: BODY_PROFILES,
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic fallback-branch profile for gate auditing."""
    del seed, difficulty
    return _PASSTHROUGH_SCHEDULE[sample_index % len(_PASSTHROUGH_SCHEDULE)]


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 7, 14), ("grid_w", 6, 14), ("n_pairs", 2, 4)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    for name, options in (
        ("legend_layout", LEGEND_LAYOUTS),
        ("body_profile", BODY_PROFILES),
        ("passthrough", PASSTHROUGH_MODES),
    ):
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"{name} must be one of {options}")


def _draw_int_axis(ctx, label: str, band: tuple[int, int], valid: tuple[int, int]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *band)


def _draw_choice_axis(ctx, label: str, band_options, valid_options):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, valid_options)
    return ctx.draw_choice(label, band_options)


def _draw_axes(ctx, difficulty: str | None, overrides: dict[str, Any]):
    explicit = any(value is not None for value in overrides.values())
    scheduled_passthrough = schedule_profile(ctx.seed, ctx.sample_index, difficulty)
    passthrough = ctx.draw_choice(
        "passthrough",
        PASSTHROUGH_MODES if overrides.get("passthrough") is not None
        else (scheduled_passthrough,),
    )

    prior_rng = ctx.draw_rng("linked_canonical_profile")
    linked = (
        not explicit
        and passthrough == "absent"
        and prior_rng.random() < _LINKED_PRIOR_WHEN_ABSENT
    )
    if linked:
        h, w, body_profile, legend_layout = prior_rng.choice(_LINKED_CANONICAL_PROFILES)
        return (
            ctx.draw_int("grid_h", h, h),
            ctx.draw_int("grid_w", w, w),
            ctx.draw_int("n_pairs", 3, 3),
            ctx.draw_choice("legend_layout", (legend_layout,)),
            ctx.draw_choice("body_profile", (body_profile,)),
            passthrough,
            True,
        )

    pair_band = _BAND_PAIRS[difficulty]
    if passthrough == "present" and overrides.get("n_pairs") is None:
        # Reserve at least two palette colors for a multi-passthrough witness.
        # Exact n_pairs=4 overrides remain lawful but have only one free color.
        pair_band = (pair_band[0], min(pair_band[1], 3))

    return (
        _draw_int_axis(ctx, "grid_h", _BAND_H[difficulty], (7, 14)),
        _draw_int_axis(ctx, "grid_w", _BAND_W[difficulty], (6, 14)),
        _draw_int_axis(ctx, "n_pairs", pair_band, (2, 4)),
        _draw_choice_axis(ctx, "legend_layout", LEGEND_LAYOUTS, LEGEND_LAYOUTS),
        _draw_choice_axis(
            ctx,
            "body_profile",
            _BAND_BODY_PROFILES[difficulty],
            BODY_PROFILES,
        ),
        passthrough,
        False,
    )


def _legend_columns(width: int, n_pairs: int, layout: str, rng) -> list[int]:
    if layout == "contiguous":
        start = rng.randint(0, width - n_pairs)
        return list(range(start, start + n_pairs))
    choices = [
        combo
        for combo in combinations(range(width), n_pairs)
        if combo[-1] - combo[0] + 1 != n_pairs
    ]
    if not choices:
        raise ValueError("grid width leaves no scattered legend placement")
    return list(rng.choice(choices))


def _body_count(profile: str, area: int, minimum: int, rng) -> int:
    fractions = {
        "sparse": (0.18, 0.28),
        "medium": (0.40, 0.50),
        "dense": (0.56, 0.68),
    }
    lo_frac, hi_frac = fractions[profile]
    lo = max(minimum, int(area * lo_frac + 0.999999))
    hi = max(lo, int(area * hi_frac))
    hi = min(hi, area - 1)
    if hi < lo:
        raise ValueError(
            f"body profile {profile!r} cannot fit minimum {minimum} in area {area}"
        )
    return rng.randint(lo, hi)


def _paint_body(
    grid: list[list[int]],
    sources: list[int],
    passthrough_colors: list[int],
    body_profile: str,
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    positions = [(r, c) for r in range(3, height) for c in range(width)]
    minimum = len(sources) + 2 * len(passthrough_colors)
    count = _body_count(body_profile, len(positions), minimum, rng)

    # Keep every body row represented.  This matches the official dense canvas
    # grammar and prevents row-count/crop shortcuts from being underdetermined.
    chosen = set()
    for row in range(3, height):
        chosen.add((row, rng.randrange(width)))
    remaining = [position for position in positions if position not in chosen]
    rng.shuffle(remaining)
    chosen.update(remaining[: count - len(chosen)])
    chosen = list(chosen)
    rng.shuffle(chosen)

    values = list(sources)
    for passthrough_color in passthrough_colors:
        values.extend([passthrough_color, passthrough_color])
    while len(values) < count:
        values.append(rng.choice(sources))
    rng.shuffle(values)
    for (row, col), value in zip(chosen, values):
        grid[row][col] = value


def _analyze(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], {}
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], {}
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular with nonempty rows"], {}
    height = len(grid)
    if not 7 <= height <= 14:
        errors.append(f"grid height {height} outside 7..14")
    if not 6 <= width <= 14:
        errors.append(f"grid width {width} outside 6..14")
    if height < 3:
        return errors + ["grid lacks two legend rows and separator"], {}

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer ARC color 0..9")
                return errors, {}

    if any(value != 0 for value in grid[2]):
        errors.append("row 2 must be an all-zero separator")

    active_columns = [
        c for c in range(width) if grid[0][c] != 0 or grid[1][c] != 0
    ]
    half_pairs = [
        c for c in active_columns if (grid[0][c] == 0) != (grid[1][c] == 0)
    ]
    if half_pairs:
        errors.append(f"legend contains half-pair columns: {half_pairs}")
    pair_columns = [
        c for c in active_columns if grid[0][c] != 0 and grid[1][c] != 0
    ]
    if not 2 <= len(pair_columns) <= 4:
        errors.append(f"expected 2-4 complete legend pairs, found {len(pair_columns)}")

    sources = [grid[0][c] for c in pair_columns]
    targets = [grid[1][c] for c in pair_columns]
    if len(set(sources)) != len(sources):
        errors.append("legend source colors must be pairwise distinct")
    if len(set(targets)) != len(targets):
        errors.append("legend target colors must be pairwise distinct")
    if set(sources) & set(targets):
        errors.append("legend source and target palettes must be disjoint")

    contiguous = bool(pair_columns) and pair_columns == list(
        range(pair_columns[0], pair_columns[0] + len(pair_columns))
    )
    legend_layout = "contiguous" if contiguous else "scattered"

    body = grid[3:]
    body_values = [value for row in body for value in row]
    nonzero_body = [value for value in body_values if value != 0]
    if not nonzero_body:
        errors.append("body must contain nonzero cells")
    source_counts = {source: nonzero_body.count(source) for source in sources}
    missing_sources = [source for source, count in source_counts.items() if count == 0]
    if missing_sources:
        errors.append(f"body omits legend source colors: {missing_sources}")

    passthrough_values = sorted(set(nonzero_body) - set(sources))
    if len(passthrough_values) > 2:
        errors.append(
            f"body may contain at most two unmapped colors, found {passthrough_values}"
        )
    if set(passthrough_values) & set(targets):
        errors.append("unmapped body color must not reuse a legend target color")
    sparse_passthrough = [
        value for value in passthrough_values if nonzero_body.count(value) < 2
    ]
    if sparse_passthrough:
        errors.append(
            "each unmapped body color must appear at least twice: "
            f"{sparse_passthrough}"
        )
    passthrough = "present" if passthrough_values else "absent"

    area = max(1, len(body_values))
    density = len(nonzero_body) / area
    if density < 0.15:
        errors.append(f"body density {density:.3f} is below the teaching floor")
        body_profile = "invalid"
    elif density <= 0.30:
        body_profile = "sparse"
    elif density <= 0.53:
        body_profile = "medium"
    elif density <= 0.72:
        body_profile = "dense"
    else:
        body_profile = "invalid"
        errors.append(f"body density {density:.3f} exceeds the declared profiles")

    if not pair_columns or not any(source_counts.values()):
        errors.append("no visible source->target recoloring is taught")

    return errors, {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": len(pair_columns),
        "legend_layout": legend_layout,
        "body_profile": body_profile,
        "passthrough": passthrough,
        "pair_columns": tuple(pair_columns),
        "sources": tuple(sources),
        "targets": tuple(targets),
        "passthrough_values": tuple(passthrough_values),
        "body_density": density,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes; accept every official input."""
    del difficulty, meta
    errors, _ = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid."""
    errors, features = _analyze(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    return {
        key: features[key]
        for key in (
            "grid_h",
            "grid_w",
            "n_pairs",
            "legend_layout",
            "body_profile",
            "passthrough",
        )
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (
        height,
        width,
        n_pairs,
        legend_layout,
        body_profile,
        passthrough,
        _linked_prior,
    ) = _draw_axes(ctx, difficulty, overrides)

    palette_rng = ctx.draw_rng("legend_palette")
    palette = palette_rng.sample(range(1, 10), 2 * n_pairs)
    sources = palette[:n_pairs]
    targets = palette[n_pairs:]
    unused = [color for color in range(1, 10) if color not in palette]
    passthrough_colors = (
        ctx.draw_rng("passthrough_colors").sample(unused, min(2, len(unused)))
        if passthrough == "present"
        else []
    )

    grid = full_grid(height, width, 0)
    columns = _legend_columns(
        width, n_pairs, legend_layout, ctx.draw_rng("legend_columns")
    )
    for column, source, target in zip(columns, sources, targets):
        grid[0][column] = source
        grid[1][column] = target

    _paint_body(
        grid,
        sources,
        passthrough_colors,
        body_profile,
        ctx.draw_rng("body_cells"),
    )
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def _pairs(grid) -> list[tuple[int, int]]:
    return [
        (grid[0][c], grid[1][c])
        for c in range(len(grid[0]))
        if grid[0][c] != 0 and grid[1][c] != 0
    ]


def _solve(grid):
    mapping = dict(_pairs(grid))
    return [[mapping.get(value, value) for value in row] for row in grid[3:]]


rule_mirror = _solve


def _rival_crop_only(grid):
    return [row[:] for row in grid[3:]]


def _rival_reverse_legend(grid):
    mapping = {target: source for source, target in _pairs(grid)}
    return [[mapping.get(value, value) for value in row] for row in grid[3:]]


def _rival_first_pair_only(grid):
    source, target = _pairs(grid)[0]
    return [
        [target if value == source else value for value in row]
        for row in grid[3:]
    ]


def _rival_keep_full_canvas(grid):
    mapping = dict(_pairs(grid))
    return [[mapping.get(value, value) for value in row] for row in grid]


def _rival_zero_unmapped(grid):
    mapping = dict(_pairs(grid))
    return [[mapping.get(value, 0) for value in row] for row in grid[3:]]


def _rival_first_unmapped_only(grid):
    mapping = dict(_pairs(grid))
    sources = set(mapping)
    unmapped = sorted(
        {value for row in grid[3:] for value in row if value and value not in sources}
    )
    keep = unmapped[0] if unmapped else None
    return [
        [mapping.get(value, value if value in {0, keep} else 0) for value in row]
        for row in grid[3:]
    ]


def strict_canonical_like(grid) -> list[str]:
    errors, features = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if not 7 <= features["grid_h"] <= 9:
        reasons.append("official inputs have height 7..9")
    if not 6 <= features["grid_w"] <= 7:
        reasons.append("official inputs have width 6..7")
    if features["n_pairs"] != 3:
        reasons.append("official inputs use exactly three legend pairs")
    if features["passthrough"] != "absent":
        reasons.append("official bodies use only mapped source colors")
    if not 0.40 <= features["body_density"] <= 0.68:
        reasons.append("official body density lies in 0.40..0.68")
    return reasons


MIN_STRICT_FRAC = 0.25

SEMANTIC_RIVALS = {
    "crop_only": _rival_crop_only,
    "reverse_legend": _rival_reverse_legend,
    "first_pair_only": _rival_first_pair_only,
    "keep_full_canvas": _rival_keep_full_canvas,
    "zero_unmapped": _rival_zero_unmapped,
    "first_unmapped_only": _rival_first_unmapped_only,
}

SEMANTIC_WITNESSES = {
    "crop_removes_header_and_gap": lambda grid: len(grid) > 3,
    "multiple_legend_pairs_are_used": lambda grid: all(
        any(value == source for row in grid[3:] for value in row)
        for source, _ in _pairs(grid)
    ),
    "source_to_target_direction_is_visible": lambda grid: bool(_pairs(grid)),
    "unmapped_color_passes_through": lambda grid: _analyze(grid)[1].get(
        "passthrough"
    ) == "present",
    "multiple_unmapped_colors_pass_through": lambda grid: len(
        _analyze(grid)[1].get("passthrough_values", ())
    ) >= 2,
}

WITNESS_RIVALS = {
    "crop_removes_header_and_gap": ["keep_full_canvas"],
    "multiple_legend_pairs_are_used": ["first_pair_only", "crop_only"],
    "source_to_target_direction_is_visible": ["reverse_legend"],
    "unmapped_color_passes_through": ["zero_unmapped"],
    "multiple_unmapped_colors_pass_through": ["first_unmapped_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# This wrong fallback is answer-equivalent on every official pair because the
# official bodies contain no unmapped nonzero colors. Generated passthrough
# witnesses are therefore required to refute it.
CANONICAL_SHORTCUTS = {
    "zero_unmapped": _rival_zero_unmapped,
    "first_unmapped_only": _rival_first_unmapped_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives demos and forks query."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(example["input"]) == example["output"]
                for example in demos
            )
            query_differs = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives and query_differs:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query answer"
            )
    return reasons
