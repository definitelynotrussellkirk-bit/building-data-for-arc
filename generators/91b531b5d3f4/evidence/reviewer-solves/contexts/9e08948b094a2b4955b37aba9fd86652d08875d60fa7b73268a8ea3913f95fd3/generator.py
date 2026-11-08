"""Semantic generator for ARC task 91b531b5d3f4.

Row 0 is a column header.  A color-1 marker below a nonzero header is
recolored to that header; every other cell is preserved.  Four consecutive
default draws form a complete lesson: one linked official profile, each
negative branch in isolation, and a composition profile where both negative
branches co-occur.  The composition profile also preserves a header-colored
cell below a different live header, ruling out palette- or column-wide
recoloring shortcuts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "91b531b5d3f4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f35595f08cd0"  # sha256(normalized canonical program)[:12]
SUMMARY = (
    "Schedule linked official anchors, isolated negative witnesses, and a "
    "mixed counterfactual that composes both unchanged branches."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
INVARIANTS = [
    "background is 0 and row 0 contains one to three distinct colors from 2..9",
    "every nonzero header column has at least one color-1 marker below it",
    "the canonical profile contains only fired markers in the body",
    "the empty-column profile also contains color-1 markers below zero headers",
    "the distractor profile instead contains unchanged non-1 body cells",
    "the mixed profile composes both negative branches and includes a header-colored conflict witness",
    "applying the canonical rule changes at least one body marker",
    "every four consecutive default draws cover all four semantic profiles",
]

HELPFUL_TEXTURES = (
    "canonical",
    "empty_column_witness",
    "distractors",
    "mixed_witnesses",
)
DEGENERATE_TEXTURES = ()
SCHEDULE_PROFILES = HELPFUL_TEXTURES

# These are exact, observable contracts.  Difficulty changes only the default
# draw range; an explicit override may use the full declared range in any band.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled linked canonical anchor, otherwise easy 5..7, medium 7..9, hard 10..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled linked canonical anchor, otherwise easy 6..8, medium 8..10, hard 11..13",
        "valid": "6..13",
    },
    "header_cols": {
        "type": "int",
        "default": "scheduled linked canonical anchor; mixed defaults use at least 2 headers",
        "valid": "1..3",
    },
    "texture": {
        "type": "enum",
        "default": "four-draw canonical|empty_column_witness|distractors|mixed_witnesses schedule",
        "valid": "canonical|empty_column_witness|distractors|mixed_witnesses",
    },
}

_BAND_RANGES = {
    "easy": {
        "grid_h": (5, 7),
        "grid_w": (6, 8),
        "header_cols": (1, 2),
        "markers_per_header": (1, 2),
        "extra_witnesses": (1, 1),
    },
    "medium": {
        "grid_h": (7, 9),
        "grid_w": (8, 10),
        "header_cols": (2, 3),
        "markers_per_header": (1, 3),
        "extra_witnesses": (1, 2),
    },
    "hard": {
        "grid_h": (10, 12),
        "grid_w": (11, 13),
        "header_cols": (2, 3),
        "markers_per_header": (2, 4),
        "extra_witnesses": (2, 3),
    },
}
_VALID_RANGES = {
    "grid_h": (5, 12),
    "grid_w": (6, 13),
    "header_cols": (1, 3),
}

# Strict linked canonical morphology extracted from the two training inputs and
# one held-out input.  Colors and marker row positions are nuisance factors;
# dimensions, header columns, and per-header marker counts stay linked.
_CANONICAL_PROFILES = (
    (7, 8, (1, 4), (2, 2)),
    (7, 8, (2, 6), (2, 2)),
    (7, 9, (1, 4, 8), (2, 1, 2)),
)
_CANONICAL_PROFILE_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_RANGES:
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic four-slot semantic curriculum profile."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_exact_int(ctx, overrides, label: str, default_range: tuple[int, int]) -> int:
    """Honor full-range explicit overrides while keeping banded defaults."""
    lo, hi = _VALID_RANGES[label] if label in overrides else default_range
    return ctx.draw_int(label, lo, hi)


def _analysis(grid) -> dict:
    errors: list[str] = []
    result = {
        "errors": errors,
        "header_cols": None,
        "texture": None,
        "header_columns": (),
        "fired_markers": 0,
        "empty_column_markers": 0,
        "distractor_cells": 0,
        "live_column_distractors": 0,
        "empty_column_distractors": 0,
        "header_color_distractors": 0,
        "misaligned_header_color_distractors": 0,
    }

    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty list of rows")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("grid rows must be non-empty")
        return result
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    h = len(grid)
    if not (5 <= h <= 12 and 6 <= w <= 13):
        errors.append(f"grid dimensions {h}x{w} are outside 5..12 by 6..13")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
        return result

    if any(value == 1 for value in grid[0]):
        errors.append("row 0 may contain headers 2..9, never marker color 1")
    header_columns = tuple(c for c, value in enumerate(grid[0]) if value != 0)
    header_colors = tuple(grid[0][c] for c in header_columns)
    result["header_cols"] = len(header_columns)
    result["header_columns"] = header_columns
    if not 1 <= len(header_columns) <= 3:
        errors.append("row 0 must contain one to three nonzero headers")
    if len(set(header_colors)) != len(header_colors):
        errors.append("header colors must be distinct")
    if any(color not in range(2, 10) for color in header_colors):
        errors.append("header colors must lie in 2..9")

    fired_by_column = {c: 0 for c in header_columns}
    empty_markers: list[tuple[int, int]] = []
    distractors: list[tuple[int, int, int]] = []
    header_set = set(header_columns)
    for r in range(1, h):
        for c in range(w):
            value = grid[r][c]
            if value == 1:
                if c in header_set:
                    fired_by_column[c] += 1
                else:
                    empty_markers.append((r, c))
            elif value != 0:
                distractors.append((r, c, value))

    missing = [c for c, count in fired_by_column.items() if count == 0]
    if missing:
        errors.append(f"header columns without a marker witness: {missing}")
    max_markers_per_header = min(4, h - 1)
    overloaded = [c for c, count in fired_by_column.items() if count > max_markers_per_header]
    if overloaded:
        errors.append(f"too many markers in header columns: {overloaded}")

    fired = sum(fired_by_column.values())
    result["fired_markers"] = fired
    result["empty_column_markers"] = len(empty_markers)
    result["distractor_cells"] = len(distractors)
    live_distractors = [item for item in distractors if item[1] in header_set]
    empty_distractors = [item for item in distractors if item[1] not in header_set]
    header_color_distractors = [
        item for item in distractors if item[2] in set(header_colors)
    ]
    misaligned_header_color_distractors = [
        item
        for item in live_distractors
        if item[2] in set(header_colors) and item[2] != grid[0][item[1]]
    ]
    result["live_column_distractors"] = len(live_distractors)
    result["empty_column_distractors"] = len(empty_distractors)
    result["header_color_distractors"] = len(header_color_distractors)
    result["misaligned_header_color_distractors"] = len(
        misaligned_header_color_distractors
    )
    if fired == 0:
        errors.append("the canonical rule would not fire")

    if distractors and empty_markers:
        texture = "mixed_witnesses"
        if not 1 <= len(empty_markers) <= 3:
            errors.append("mixed profile must contain one to three empty-column markers")
        if not 3 <= len(distractors) <= 5:
            errors.append("mixed profile must contain three to five distractor cells")
        if not live_distractors:
            errors.append("mixed profile needs a distractor below a nonzero header")
        if not empty_distractors:
            errors.append("mixed profile needs a distractor below an empty header")
        if not header_color_distractors:
            errors.append("mixed profile needs a header-colored distractor")
        if not any(value not in set(header_colors) for _, _, value in distractors):
            errors.append("mixed profile needs a non-header distractor color")
        if len(header_columns) >= 2 and not misaligned_header_color_distractors:
            errors.append(
                "mixed profile needs a header-colored distractor below a different live header"
            )
    elif distractors:
        texture = "distractors"
        colors = {value for _, _, value in distractors}
        if len(colors) != 1:
            errors.append("all distractor cells must share one non-header color")
        elif next(iter(colors)) in set(header_colors) | {0, 1}:
            errors.append("distractor color must differ from background, marker, and headers")
        if not 2 <= len(distractors) <= 4:
            errors.append("distractor profile must contain two to four distractor cells")
        if not any(c in header_set for _, c, _ in distractors):
            errors.append("distractor profile needs a witness below a nonzero header")
        if not any(c not in header_set for _, c, _ in distractors):
            errors.append("distractor profile needs a witness below an empty header")
    elif empty_markers:
        texture = "empty_column_witness"
        if not 1 <= len(empty_markers) <= 3:
            errors.append("empty-column profile must contain one to three unchanged markers")
    else:
        texture = "canonical"

    result["texture"] = texture
    return result


def _canonical_profile_signature(grid):
    """Return the strict official linked morphology, or ``None``.

    This is intentionally narrower than general rule validity: it keeps the
    empirical dimension/header/count tuples linked instead of recombining
    attractive marginals from different official examples.
    """
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["texture"] != "canonical":
        return None
    header_columns = tuple(analysis["header_columns"])
    marker_counts = tuple(
        sum(grid[r][column] == 1 for r in range(1, len(grid)))
        for column in header_columns
    )
    signature = (len(grid), len(grid[0]), header_columns, marker_counts)
    return signature if signature in _CANONICAL_PROFILE_SIGNATURES else None


def strict_canonical_like(grid) -> bool:
    """Whether ``grid`` has one complete official linked input morphology."""
    return _canonical_profile_signature(grid) is not None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject structural impostors while accepting all three lawful profiles."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Return exact semantic-axis values recoverable from the rendered grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "header_cols": analysis["header_cols"],
        "texture": analysis["texture"],
    }


def _copy_grid(grid):
    return [list(row) for row in grid]


def _rule_mirror(grid):
    """Pure Python mirror of the selected canonical Racket rule."""
    out = _copy_grid(grid)
    for row in range(1, len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] == 1 and grid[0][column] != 0:
                out[row][column] = grid[0][column]
    return out


def _rival_erase_unheaded_markers(grid):
    """Wrong: every body marker becomes its header, including header 0."""
    out = _copy_grid(grid)
    for row in range(1, len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] == 1:
                out[row][column] = grid[0][column]
    return out


def _rival_recolor_all_nonzero_in_live_columns(grid):
    """Wrong: every nonzero body cell below a live header is recolored."""
    out = _copy_grid(grid)
    for row in range(1, len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] != 0 and grid[0][column] != 0:
                out[row][column] = grid[0][column]
    return out


def _rival_recolor_markers_and_header_palette(grid):
    """Wrong: marker and header-palette body cells are both column labels."""
    out = _copy_grid(grid)
    header_colors = {value for value in grid[0] if value != 0}
    for row in range(1, len(grid)):
        for column in range(len(grid[0])):
            value = grid[row][column]
            if (
                value in header_colors | {1}
                and grid[0][column] != 0
            ):
                out[row][column] = grid[0][column]
    return out


def _rival_official_profiles_only(grid):
    """Wrong: apply the rule only to the three memorized official profiles."""
    return _rule_mirror(grid) if strict_canonical_like(grid) else _copy_grid(grid)


SEMANTIC_RIVALS = {
    "erase markers below empty headers": _rival_erase_unheaded_markers,
    "recolor every nonzero cell below a live header": (
        _rival_recolor_all_nonzero_in_live_columns
    ),
    "recolor marker and header-palette cells": (
        _rival_recolor_markers_and_header_palette
    ),
    "apply the rule only to official profiles": _rival_official_profiles_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_valid_feature(grid, key: str) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis[key])


SEMANTIC_WITNESSES = {
    "empty_header_marker_preserved": lambda grid: _has_valid_feature(
        grid, "empty_column_markers"
    ),
    "nonmarker_below_live_header_preserved": lambda grid: _has_valid_feature(
        grid, "live_column_distractors"
    ),
    "generalized_scene_still_fires": lambda grid: (
        not _analysis(grid)["errors"]
        and not strict_canonical_like(grid)
        and _analysis(grid)["fired_markers"] > 0
    ),
    "mixed_negative_branches": lambda grid: (
        not _analysis(grid)["errors"]
        and _analysis(grid)["texture"] == "mixed_witnesses"
    ),
    "misaligned_header_color_preserved": lambda grid: _has_valid_feature(
        grid, "misaligned_header_color_distractors"
    ),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "empty_header_marker_preserved": ["erase markers below empty headers"],
    "nonmarker_below_live_header_preserved": [
        "recolor every nonzero cell below a live header"
    ],
    "generalized_scene_still_fires": ["apply the rule only to official profiles"],
    "mixed_negative_branches": [
        "erase markers below empty headers",
        "recolor every nonzero cell below a live header",
        "apply the rule only to official profiles",
    ],
    "misaligned_header_color_preserved": [
        "recolor marker and header-palette cells"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared shortcut viable."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output grids")
            continue
        if _rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def _choose_zero_cell(
    grid: list[list[int]],
    rng,
    *,
    columns: list[int],
) -> tuple[int, int]:
    candidates = [
        (r, c)
        for r in range(1, len(grid))
        for c in columns
        if grid[r][c] == 0
    ]
    if not candidates:
        raise ValueError("no free body cell for requested semantic witness")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = {key: value for key, value in overrides.items() if value is not None}
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=dict(overrides),
    )

    scheduled_texture = schedule_profile(seed, sample_index, difficulty=band)
    if "texture" not in overrides:
        ctx.overrides["texture"] = scheduled_texture

    # Choose one complete official geometry profile for the canonical schedule
    # slot, only for wholly unoverridden defaults.  Inject its exact axis values
    # before typed draws so provenance and the returned grid agree.
    canonical_profile = None
    if not overrides and scheduled_texture == "canonical":
        canonical_profile = ctx.draw_rng("canonical_profile").choice(
            _CANONICAL_PROFILES
        )
        profile_h, profile_w, profile_columns, _ = canonical_profile
        ctx.overrides.update(
            {
                "grid_h": profile_h,
                "grid_w": profile_w,
                "header_cols": len(profile_columns),
                "texture": "canonical",
            }
        )

    ranges = _BAND_RANGES[band]
    effective_overrides = ctx.overrides
    h = _draw_exact_int(ctx, effective_overrides, "grid_h", ranges["grid_h"])
    w = _draw_exact_int(ctx, effective_overrides, "grid_w", ranges["grid_w"])
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    header_range = ranges["header_cols"]
    if texture == "mixed_witnesses" and "header_cols" not in overrides:
        header_range = (max(2, header_range[0]), header_range[1])
    header_count = _draw_exact_int(
        ctx, effective_overrides, "header_cols", header_range
    )

    layout = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    if canonical_profile is None:
        header_columns = sorted(layout.sample(range(w), header_count))
        canonical_marker_counts = None
    else:
        _, _, profile_columns, profile_counts = canonical_profile
        header_columns = list(profile_columns)
        canonical_marker_counts = tuple(profile_counts)
    header_colors = ctx.draw_distinct_colors(
        "header_colors", n=header_count, exclude={0, 1}
    )
    for column, color in zip(header_columns, header_colors):
        grid[0][column] = color

    marker_lo, marker_hi = ranges["markers_per_header"]
    marker_hi = min(marker_hi, h - 1)
    if texture in {"distractors", "mixed_witnesses"}:
        # Reserve at least one zero body cell below a live header, even when a
        # small explicit grid is combined with the hard difficulty band.
        marker_hi = min(marker_hi, h - 2)
    for index, column in enumerate(header_columns):
        count = (
            canonical_marker_counts[index]
            if canonical_marker_counts is not None
            else layout.randint(marker_lo, marker_hi)
        )
        for row in layout.sample(range(1, h), count):
            grid[row][column] = 1

    header_set = set(header_columns)
    empty_columns = [c for c in range(w) if c not in header_set]
    extra_lo, extra_hi = ranges["extra_witnesses"]
    if texture in {"empty_column_witness", "mixed_witnesses"}:
        count = layout.randint(extra_lo, min(extra_hi, 3))
        available = [
            (r, c) for r in range(1, h) for c in empty_columns if grid[r][c] == 0
        ]
        if len(available) < count:
            raise ValueError("not enough empty-column cells for marker witnesses")
        for r, c in layout.sample(available, count):
            grid[r][c] = 1
    if texture == "distractors":
        count = max(2, min(4, layout.randint(extra_lo + 1, extra_hi + 1)))
        distractor_color = ctx.draw_color(
            "distractor_color", exclude={0, 1, *header_colors}
        )
        # One witness below a live header and one below an empty header make
        # the negative branch visible rather than a cosmetic palette change.
        first = _choose_zero_cell(grid, layout, columns=header_columns)
        second = _choose_zero_cell(grid, layout, columns=empty_columns)
        positions = {first, second}
        remaining = [
            (r, c)
            for r in range(1, h)
            for c in range(w)
            if grid[r][c] == 0 and (r, c) not in positions
        ]
        if len(remaining) < count - 2:
            raise ValueError("not enough free body cells for distractors")
        positions.update(layout.sample(remaining, count - 2))
        for r, c in positions:
            grid[r][c] = distractor_color
    elif texture == "mixed_witnesses":
        count = max(3, min(5, layout.randint(extra_lo + 2, extra_hi + 2)))
        neutral_color = ctx.draw_color(
            "distractor_color", exclude={0, 1, *header_colors}
        )

        # A non-header distractor below a live header refutes column-wide
        # recoloring.  Mark it immediately so later position draws stay unique.
        live_neutral = _choose_zero_cell(grid, layout, columns=header_columns)
        grid[live_neutral[0]][live_neutral[1]] = neutral_color
        placed = [live_neutral]

        # Reuse a header color as a preserved body cell.  With two or more
        # headers, put it under a DIFFERENT live header so even a palette-aware
        # column-label shortcut must change it incorrectly.
        if header_count >= 2:
            conflict_columns = [
                column
                for column in header_columns
                if column != live_neutral[1]
                and any(grid[row][column] == 0 for row in range(1, h))
            ]
            if not conflict_columns:
                conflict_columns = [
                    column
                    for column in header_columns
                    if any(grid[row][column] == 0 for row in range(1, h))
                ]
            conflict_column = layout.choice(conflict_columns)
            conflict_position = _choose_zero_cell(
                grid, layout, columns=[conflict_column]
            )
            conflict_colors = [
                grid[0][column]
                for column in header_columns
                if grid[0][column] != grid[0][conflict_column]
            ]
            conflict_color = layout.choice(conflict_colors)
        else:
            conflict_position = _choose_zero_cell(
                grid, layout, columns=empty_columns
            )
            conflict_color = header_colors[0]
        grid[conflict_position[0]][conflict_position[1]] = conflict_color
        placed.append(conflict_position)

        # The mixed profile must also contain a distractor below an empty
        # header.  The one-header conflict already supplies that witness.
        if conflict_position[1] in header_set:
            empty_distractor = _choose_zero_cell(
                grid, layout, columns=empty_columns
            )
            grid[empty_distractor[0]][empty_distractor[1]] = neutral_color
            placed.append(empty_distractor)

        remaining = [
            (r, c)
            for r in range(1, h)
            for c in range(w)
            if grid[r][c] == 0
        ]
        if len(remaining) < count - len(placed):
            raise ValueError("not enough free body cells for mixed distractors")
        extra_positions = layout.sample(remaining, count - len(placed))
        palette = (neutral_color, *header_colors)
        for index, (r, c) in enumerate(extra_positions):
            grid[r][c] = palette[index % len(palette)]

    errors = self_check(grid, difficulty=band, meta={"texture": texture})
    if errors:
        raise ValueError("generated invalid semantic scene: " + "; ".join(errors))
    if canonical_profile is not None and _canonical_profile_signature(grid) is None:
        raise ValueError("canonical prior failed to realize its linked profile")
    return grid
