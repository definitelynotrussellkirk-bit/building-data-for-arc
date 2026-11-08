"""Generator for ARC task bca4f37ec5e9 (original task 8eb1be9a).

The input contains one contiguous horizontal block of non-background rows.
The oracle repeats that complete row block vertically, preserving the phase
implied by the block's original top row.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bca4f37ec5e9"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "868f6b6ec7f1"

SUMMARY = (
    "Find the first and last nonzero rows, treat that contiguous row block as "
    "one vertical period, and tile the period over the full grid with the "
    "phase anchored at the original first nonzero row."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and is strictly modal",
    "exactly one contiguous block of 2-5 nonzero rows",
    "at least one all-zero row appears above and below the block",
    "the block uses exactly one nonzero color",
    "every block row is nonempty and the block contains at least two distinct row masks",
    "the block is not solid, so vertical tiling cannot collapse to a modal-color fill",
]

# A joint profile is deliberate: dimensions, period, and vertical placement are
# linked in the official examples.  Keeping them as independent AXES previously
# advertised impossible combinations and made accepted overrides unobservable.
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted keyed choice",
        "valid": (
            "canonical_10x12|canonical_14x13|canonical_15x19|"
            "period2_top|period2_bottom|period3_center|period4_top|"
            "period4_bottom|period5_center|period5_bottom"
        ),
    }
}

# There is only one exact override axis, so every declared value is compatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# name -> (height, width, first nonzero row, period height)
_PROFILE_GEOMETRY = {
    "canonical_10x12": (10, 12, 3, 3),
    "canonical_14x13": (14, 13, 3, 3),
    "canonical_15x19": (15, 19, 4, 3),
    "period2_top": (11, 14, 1, 2),
    "period2_bottom": (12, 16, 9, 2),
    "period3_center": (13, 17, 5, 3),
    "period4_top": (16, 18, 1, 4),
    "period4_bottom": (17, 15, 12, 4),
    "period5_center": (18, 20, 6, 5),
    "period5_bottom": (20, 16, 14, 5),
}
_PROFILE_BY_GEOMETRY = {
    geometry: name for name, geometry in _PROFILE_GEOMETRY.items()
}
_PROFILE_NAMES = tuple(_PROFILE_GEOMETRY)

# Exact official inputs.  These branches keep a substantial, measured fraction
# of ordinary draws on the empirical manifold while the other profiles provide
# period/position/texture counterexamples.
_CANONICAL_ROWS = {
    "canonical_10x12": (
        (2, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 0),
        (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2),
        (2, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 0),
    ),
    "canonical_14x13": (
        (0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0),
        (1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1),
        (1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1),
    ),
    "canonical_15x19": (
        (0, 0, 8, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0),
        (8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8),
        (0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 8, 0),
    ),
}


def _profile_options(
    difficulty: str, sample_index: int, *, override_requested: bool
) -> list[str]:
    """Return the exact lesson-schedule slot or the full override domain.

    Materialized lessons use sequential sample indices.  Slots 0, 1, and 2
    therefore guarantee period-2, period-3, and period-4/5 demonstrations,
    respectively; slot 3 is the query and ranges across the full distribution.
    Slots 0 and 2 always choose a profile whose source-row phase differs from
    grid-row-zero phase.  Every cyclic three-demonstration window therefore
    rejects both a fixed-period rival and an absolute-grid-anchor rival.
    """
    if override_requested:
        return list(_PROFILE_NAMES)
    slot = sample_index % 4
    if slot == 0:
        return ["period2_top", "period2_bottom"]
    if slot == 1:
        return [
            "canonical_10x12",
            "canonical_14x13",
            "canonical_15x19",
            "period3_center",
        ]
    if slot == 2:
        # Every option has first_row % period != 0, so source-anchored and
        # grid-top-anchored tiling visibly disagree in this lesson slot.
        options = ["period4_top", "period5_center", "period5_bottom"]
        if difficulty == "easy":
            options += ["period4_top", "period4_top"]
        elif difficulty == "hard":
            options += ["period5_center", "period5_bottom"]
        return options
    options = list(_PROFILE_NAMES)
    if difficulty == "easy":
        options += ["period2_top", "period2_bottom"] * 2
    elif difficulty == "hard":
        options += ["period4_bottom", "period5_center", "period5_bottom"] * 2
    else:
        options += ["period3_center", "period4_top", "period4_bottom"]
    return options


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in _PROFILE_GEOMETRY:
        raise ValueError(
            "scene_profile must be one of: " + ", ".join(_PROFILE_NAMES)
        )
    return "medium" if difficulty is None else difficulty


def _general_rows(profile: str, width: int, period: int, rng) -> list[list[int]]:
    """Create varied row masks while keeping the band one connected object."""
    family = {
        "period2_top": 0,
        "period2_bottom": 1,
        "period3_center": 2,
        "period4_top": 3,
        "period4_bottom": 0,
        "period5_center": 1,
        "period5_bottom": 2,
    }[profile]
    phase = rng.randrange(0, 7)
    rows: list[list[int]] = []
    for r in range(period):
        if r % 2 == 1:
            # Connector rows make every sparse row above/below part of the same
            # object.  This matches two canonical demonstrations without
            # incorrectly rejecting the one canonical disconnected example.
            rows.append([1] * width)
            continue
        mask: list[int] = []
        for c in range(width):
            if family == 0:
                on = (c + phase + r) % (2 + (r % 2)) != 0
            elif family == 1:
                on = ((c // 2) + r + phase) % 3 != 0
            elif family == 2:
                on = (2 * c + 3 * r + phase) % 7 in (0, 1, 4)
            else:
                on = (c + 2 * r + phase) % 5 in (0, 2, 3)
            if c != 0 and rng.random() < 0.10:
                on = not on
            mask.append(1 if on else 0)
        mask[0] = 1  # vertical spine joins all connector rows
        if all(mask):
            mask[(phase + 5 * r + 1) % (width - 1) + 1] = 0
        rows.append(mask)

    if len({tuple(row) for row in rows}) == 1:
        rows[-1][1] = 0 if rows[-1][1] else 1
    return rows


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(
            band,
            sample_index,
            override_requested="scene_profile" in overrides,
        ),
    )
    h, w, band_start, period = _PROFILE_GEOMETRY[profile]
    grid = full_grid(h, w, 0)

    if profile in _CANONICAL_ROWS:
        rows = [list(row) for row in _CANONICAL_ROWS[profile]]
    else:
        rng = ctx.draw_rng("scene_texture")
        color = rng.choice(tuple(range(1, 10)))
        masks = _general_rows(profile, w, period, rng)
        rows = [[color if value else 0 for value in mask] for mask in masks]

    for offset, row in enumerate(rows):
        grid[band_start + offset] = list(row)
    return grid


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["empty or non-grid input"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    height = len(grid)
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid contains a non-integer or color outside 0..9"]}

    nz_rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    if not nz_rows:
        return {"errors": ["no nonzero row block"]}
    first, last = nz_rows[0], nz_rows[-1]
    expected_rows = list(range(first, last + 1))
    if nz_rows != expected_rows:
        errors.append("nonzero rows must form one contiguous block")
    if first == 0:
        errors.append("row block must have an all-zero row above it")
    if last == height - 1:
        errors.append("row block must have an all-zero row below it")

    period = last - first + 1
    if not 2 <= period <= 5:
        errors.append(f"row block height must be 2..5, got {period}")

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        errors.append(f"row block must use exactly one nonzero color, got {sorted(colors)}")

    band_rows = [tuple(grid[r]) for r in range(first, last + 1)]
    if any(not any(value != 0 for value in row) for row in band_rows):
        errors.append("every row inside the block must contain a nonzero cell")
    if band_rows and all(all(value != 0 for value in row) for row in band_rows):
        errors.append("row block must contain background cells; a solid fill hides the rule")
    if len(set(band_rows)) < 2:
        errors.append("row block must contain at least two distinct row masks")

    geometry = (height, width, first, period)
    profile = _PROFILE_BY_GEOMETRY.get(geometry)
    if profile is None:
        errors.append(
            "grid geometry is outside the declared scene profiles: "
            f"{height}x{width}, first={first}, period={period}"
        )

    zero_count = sum(value == 0 for row in grid for value in row)
    if zero_count * 2 <= height * width:
        errors.append("background 0 must be strictly modal")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "first": first,
        "last": last,
        "period": period,
        "profile": profile,
        "band_rows": band_rows,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe scene_profile: " + "; ".join(analysis["errors"]))
    return {"scene_profile": analysis["profile"]}


def rule_mirror(grid):
    """Python test mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    first = analysis["first"]
    period = analysis["period"]
    rows = analysis["band_rows"]
    height = analysis["height"]
    return [list(rows[(r - first) % period]) for r in range(height)]


def _canonical_input(profile: str) -> list[list[int]]:
    h, w, first, _period = _PROFILE_GEOMETRY[profile]
    grid = full_grid(h, w, 0)
    for offset, row in enumerate(_CANONICAL_ROWS[profile]):
        grid[first + offset] = list(row)
    return grid


_STRICT_CANONICAL_INPUTS = tuple(
    tuple(tuple(row) for row in _canonical_input(profile))
    for profile in _CANONICAL_ROWS
)


def strict_canonical_like(grid) -> bool:
    """Exact empirical-manifold predicate over all unique official inputs."""
    try:
        frozen = tuple(tuple(row) for row in grid)
    except TypeError:
        return False
    return frozen in _STRICT_CANONICAL_INPUTS


def semantic_features(grid) -> dict[str, Any]:
    """Executable linked feature extractor used by review censuses/tests."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    color = next(value for row in grid for value in row if value != 0)
    signatures = []
    for row in analysis["band_rows"]:
        occupied = [c for c, value in enumerate(row) if value != 0]
        runs = sum(
            1
            for index, c in enumerate(occupied)
            if index == 0 or c != occupied[index - 1] + 1
        )
        signatures.append((len(occupied), runs, occupied[0], occupied[-1]))
    return {
        "scene_profile": analysis["profile"],
        "height": analysis["height"],
        "width": analysis["width"],
        "first_row": analysis["first"],
        "period": analysis["period"],
        "nonzero_color": color,
        "empty_rows_above": analysis["first"],
        "empty_rows_below": analysis["height"] - analysis["last"] - 1,
        "row_signatures": tuple(signatures),
        "strict_canonical_like": strict_canonical_like(grid),
    }


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes that a structural checker must reject."""
    import copy

    base = generate(2718, 3141, difficulty="medium", scene_profile="period4_top")
    analysis = _analyze(base)
    first, last = analysis["first"], analysis["last"]

    no_band = full_grid(len(base), len(base[0]), 0)

    touches_top = full_grid(len(base), len(base[0]), 0)
    for offset, row in enumerate(base[first:last + 1]):
        touches_top[offset] = list(row)

    internal_gap = copy.deepcopy(base)
    internal_gap[first + 1] = [0] * len(base[0])

    second_color = copy.deepcopy(base)
    original_color = next(value for row in base for value in row if value != 0)
    replacement = 1 if original_color != 1 else 2
    for r in range(first, last + 1):
        for c, value in enumerate(second_color[r]):
            if value != 0:
                second_color[r][c] = replacement
                break
        else:
            continue
        break

    repeated_single_row = copy.deepcopy(base)
    for r in range(first + 1, last + 1):
        repeated_single_row[r] = list(repeated_single_row[first])

    return [
        ("no_band", no_band),
        ("touches_top", touches_top),
        ("internal_blank_row", internal_gap),
        ("second_nonzero_color", second_color),
        ("single_row_mask_repeated", repeated_single_row),
    ]
