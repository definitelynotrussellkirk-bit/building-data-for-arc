"""Generator for ``Seeded Frame Fill`` (task 2e5c98d98eed).

A single closed color-8 rectangle encloses exactly one differently colored
seed.  The oracle preserves the frame and fills every strict-interior cell with
the seed color.

The curriculum uses an explicit profile schedule rather than a bag of inert
metadata.  Profiles cover all five canonical morphologies plus minimal, wide,
and tall counterexamples.  Seed color and seed corner rotate independently, so
consecutive lessons reject fixed-color, fixed-position, row-only, column-only,
and solid-bounding-box shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid


GENERATOR_ID = "2e5c98d98eed"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "57607a91f9f7"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "A 0-background grid contains exactly one closed rectangular frame in "
    "color 8 and exactly one non-0/non-8 seed inside it. Fill the complete "
    "strict interior with that seed color while preserving the frame and all "
    "outside background cells."
)

INVARIANTS = [
    "exactly one complete axis-aligned color-8 rectangle of height and width at least 4",
    "exactly one differently colored seed lies in the strict frame interior",
    "all other cells are background 0",
    "the strict interior contains at least one blank cell, so the rule is non-identity",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# name -> (grid_h, grid_w, frame_top, frame_left, frame_h, frame_w)
# The first five profiles reproduce the linked public morphology exactly; the
# final three expand size and aspect ratio without changing the rule grammar.
_PROFILES: dict[str, tuple[int, int, int, int, int, int]] = {
    "canonical_8x9_5x5": (8, 9, 1, 2, 5, 5),
    "canonical_9x10_6x5": (9, 10, 2, 1, 6, 5),
    "canonical_7x11_5x5": (7, 11, 1, 5, 5, 5),
    "canonical_10x9_6x6": (10, 9, 3, 2, 6, 6),
    "canonical_8x12_6x8": (8, 12, 1, 3, 6, 8),
    "wide_shifted_10x14": (10, 14, 2, 1, 6, 9),
    "tall_shifted_14x10": (14, 10, 1, 4, 10, 5),
    "minimal_6x8_4x4": (6, 8, 1, 3, 4, 4),
}
SCHEDULE_PROFILES = tuple(_PROFILES)
_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_SEED_POSITIONS = ("top_left", "bottom_right", "top_right", "bottom_left")
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "seeded canonical-anchored profile schedule",
        "valid": [
            "canonical_8x9_5x5",
            "canonical_9x10_6x5",
            "canonical_7x11_5x5",
            "canonical_10x9_6x6",
            "canonical_8x12_6x8",
            "wide_shifted_10x14",
            "tall_shifted_14x10",
            "minimal_6x8_4x4",
        ],
    },
    "seed_color": {
        "type": "int",
        "default": "seeded rotation over all legal non-{0,8} colors",
        "valid": "1|2|3|4|5|6|7|9",
    },
    "seed_position": {
        "type": "enum",
        "default": "seeded rotation over the four strict-interior corners",
        "valid": ["top_left", "bottom_right", "top_right", "bottom_left"],
    },
}

# Every declared cross-product is legal.  Declaring the empty policy opts the
# override checker into strict mode rather than its legacy message heuristic.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_CANONICAL_SIGNATURES = frozenset(
    {
        (8, 9, 5, 5, 3),
        (9, 10, 6, 5, 3),
        (7, 11, 5, 5, 3),
        (10, 9, 6, 6, 3),
        (8, 12, 6, 8, 3),
    }
)


def _band_offset(difficulty: Any) -> int:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _BAND_OFFSETS[difficulty]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic, seed-sensitive scene-profile curriculum slot."""
    return SCHEDULE_PROFILES[
        (int(sample_index) + int(seed) // 64 + _band_offset(difficulty))
        % len(SCHEDULE_PROFILES)
    ]


def _scheduled_seed_color(seed: int, sample_index: int, difficulty: Any) -> int:
    return _SEED_COLORS[
        (int(sample_index) + int(seed) // 8 + _band_offset(difficulty))
        % len(_SEED_COLORS)
    ]


def _scheduled_seed_position(seed: int, sample_index: int, difficulty: Any) -> str:
    # Use a non-diagonal seed term so common audit/training schedules such as
    # sample_index = seed + constant still exercise all four corners.
    return _SEED_POSITIONS[
        (int(sample_index) + int(seed) // 2 + _band_offset(difficulty))
        % len(_SEED_POSITIONS)
    ]


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                out.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            values: list[int] = []
            for value in row:
                if isinstance(value, bool) or not isinstance(value, int):
                    return []
                values.append(value)
            out.append(values)
        else:
            return []
    return out


def _perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return (
        {(r0, c) for c in range(c0, c1 + 1)}
        | {(r1, c) for c in range(c0, c1 + 1)}
        | {(r, c0) for r in range(r0, r1 + 1)}
        | {(r, c1) for r in range(r0, r1 + 1)}
    )


def _seed_position_name(
    seed: tuple[int, int, int], box: tuple[int, int, int, int]
) -> str | None:
    r, c, _color = seed
    r0, c0, r1, c1 = box
    mapping = {
        (r0 + 1, c0 + 1): "top_left",
        (r1 - 1, c1 - 1): "bottom_right",
        (r0 + 1, c1 - 1): "top_right",
        (r1 - 1, c0 + 1): "bottom_left",
    }
    return mapping.get((r, c))


def _analysis(grid: Any) -> dict[str, Any]:
    g = _coerce_grid(grid)
    errors: list[str] = []
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        return {"errors": ["grid must be nonempty and rectangular"], "grid": g}

    h, w = len(g), len(g[0])
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has non-ARC color {value!r}")

    eights = {(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value == 8}
    seeds = [
        (r, c, value)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    if not eights:
        errors.append("expected a color-8 frame")
        return {
            "errors": errors,
            "grid": g,
            "grid_h": h,
            "grid_w": w,
            "seeds": seeds,
        }

    rows = [r for r, _ in eights]
    cols = [c for _, c in eights]
    box = (min(rows), min(cols), max(rows), max(cols))
    r0, c0, r1, c1 = box
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    if frame_h < 4 or frame_w < 4:
        errors.append(f"frame must be at least 4x4, found {frame_h}x{frame_w}")

    expected_perimeter = _perimeter(box)
    missing = expected_perimeter - eights
    extra = eights - expected_perimeter
    if missing:
        errors.append(f"color-8 rectangle has {len(missing)} missing perimeter cell(s)")
    if extra:
        errors.append(f"found {len(extra)} color-8 cell(s) outside the rectangle perimeter")

    if len(seeds) != 1:
        errors.append(f"expected exactly one non-0/non-8 seed, found {len(seeds)}")
        seed = None
    else:
        seed = seeds[0]
        sr, sc, _ = seed
        if not (r0 < sr < r1 and c0 < sc < c1):
            errors.append("the unique seed must lie in the strict frame interior")

    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    if len(interior) < 4:
        errors.append("frame interior must contain at least four cells")
    if seed is not None and not any(g[r][c] == 0 for r, c in interior):
        errors.append("the seed leaves no blank interior cell for a non-identity fill")

    profile_signature = (h, w, r0, c0, r1, c1)
    profile_by_signature = {
        (ph, pw, pr0, pc0, pr0 + pfh - 1, pc0 + pfw - 1): name
        for name, (ph, pw, pr0, pc0, pfh, pfw) in _PROFILES.items()
    }
    scene_profile = profile_by_signature.get(profile_signature)
    palette_size = len({value for row in g for value in row})
    return {
        "errors": errors,
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "bbox": box,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "interior": interior,
        "seed": seed,
        "seed_color": None if seed is None else seed[2],
        "seed_position": None if seed is None else _seed_position_name(seed, box),
        "scene_profile": scene_profile,
        "palette_size": palette_size,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the oracle-valid grammar and reject structural impostors."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared semantic axis from the returned grid."""
    analysis = _analysis(grid)
    return {
        "scene_profile": analysis.get("scene_profile"),
        "seed_color": analysis.get("seed_color"),
        "seed_position": analysis.get("seed_position"),
    }


def canonical_profile_signature(grid) -> tuple[Any, ...] | None:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["frame_h"],
        analysis["frame_w"],
        analysis["palette_size"],
    )


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked frame profile is outside the five canonical signatures: {signature}"]
    return []


def _draw_axis_choice(ctx, overrides: dict[str, Any], name: str, scheduled: Any, options):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _seed_cell(
    position: str, top: int, left: int, frame_h: int, frame_w: int
) -> tuple[int, int]:
    bottom = top + frame_h - 1
    right = left + frame_w - 1
    return {
        "top_left": (top + 1, left + 1),
        "bottom_right": (bottom - 1, right - 1),
        "top_right": (top + 1, right - 1),
        "bottom_left": (bottom - 1, left + 1),
    }[position]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _band_offset(difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile_name = _draw_axis_choice(
        ctx, overrides, "scene_profile", scheduled_profile, SCHEDULE_PROFILES
    )
    seed_color = _draw_axis_choice(
        ctx,
        overrides,
        "seed_color",
        _scheduled_seed_color(seed, sample_index, difficulty),
        _SEED_COLORS,
    )
    seed_position = _draw_axis_choice(
        ctx,
        overrides,
        "seed_position",
        _scheduled_seed_position(seed, sample_index, difficulty),
        _SEED_POSITIONS,
    )

    h, w, top, left, frame_h, frame_w = _PROFILES[profile_name]
    grid = full_grid(h, w, 0)
    draw_rect_outline(grid, top, left, frame_h, frame_w, 8)
    seed_r, seed_c = _seed_cell(seed_position, top, left, frame_h, frame_w)
    grid[seed_r][seed_c] = seed_color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": ctx.recorded_draws()})
    if errors:
        raise AssertionError("generated invalid seeded-frame lesson: " + "; ".join(errors))
    return grid


def _fill_interior(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("input is outside the seeded-frame teaching grammar")
    out = [row[:] for row in analysis["grid"]]
    color = analysis["seed_color"]
    for r, c in analysis["interior"]:
        out[r][c] = color
    return out


def _identity(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    return [row[:] for row in analysis["grid"]]


def _seed_row_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    out = [row[:] for row in analysis["grid"]]
    seed_r = analysis["seed"][0]
    for r, c in analysis["interior"]:
        if r == seed_r:
            out[r][c] = analysis["seed_color"]
    return out


def _seed_column_only(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    out = [row[:] for row in analysis["grid"]]
    seed_c = analysis["seed"][1]
    for r, c in analysis["interior"]:
        if c == seed_c:
            out[r][c] = analysis["seed_color"]
    return out


def _solid_bbox(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    out = [row[:] for row in analysis["grid"]]
    r0, c0, r1, c1 = analysis["bbox"]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = analysis["seed_color"]
    return out


def _fixed_color_three(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    out = [row[:] for row in analysis["grid"]]
    for r, c in analysis["interior"]:
        out[r][c] = 3
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "seed_row_only": _seed_row_only,
    "seed_column_only": _seed_column_only,
    "solid_bbox": _solid_bbox,
    "fixed_color_3": _fixed_color_three,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def wrapped(grid: Any) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return wrapped


SEMANTIC_WITNESSES = {
    "canonical_profile": _witness(
        lambda analysis: canonical_profile_signature(analysis["grid"])
        in _CANONICAL_SIGNATURES
    ),
    "two_dimensional_interior": _witness(
        lambda analysis: analysis["frame_h"] >= 4 and analysis["frame_w"] >= 4
    ),
    "frame_must_be_preserved": _witness(lambda analysis: True),
    "seed_color_not_fixed_three": _witness(
        lambda analysis: analysis["seed_color"] != 3
    ),
}
WITNESS_RIVALS = {
    "canonical_profile": ["seed_row_only"],
    "two_dimensional_interior": ["seed_row_only", "seed_column_only"],
    "frame_must_be_preserved": ["solid_bbox"],
    "seed_color_not_fixed_three": ["fixed_color_3"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to falsify the named shortcut rules."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos = []
    for index, pair in enumerate(demos):
        try:
            expected = _fill_interior(pair.get("input"))
        except ValueError:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output is not the complete interior fill")
        valid_demos.append(pair)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(pair.get("input")) == pair.get("output") for pair in valid_demos
        ):
            reasons.append(f"demonstrations do not falsify rival rule {name}")

    try:
        query_expected = _fill_interior(query.get("input"))
    except ValueError:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    if query.get("output") != query_expected:
        reasons.append("query output is not the complete interior fill")
    return reasons
