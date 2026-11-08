"""Generator for ``bab4d8f5ba7a`` — row headers recolor cyan markers.

The first cell of each active row is a nonzero, non-cyan header.  Every cyan
(8) cell later in that row is recolored to the header color; cyan cells in
headerless rows and all non-cyan body cells are preserved.

The distribution is deliberately lesson-oriented rather than merely varied.
A five-step teaching schedule cycles through the canonical one-marker grammar,
multiple markers in one row, a protected marker in a headerless row, both
conditions together, and inert non-cyan distractors.  Thus generated data
exercises every selected-rule branch without emitting identity-only degenerates.
All declared axes are exact, observable from the returned grid, and legal in
every difficulty band.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "bab4d8f5ba7a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1130750019d1"

SUMMARY = (
    "A zero-background grid has three to six active rows. Each active row's "
    "first cell is its non-cyan color key, and one or more cyan(8) markers "
    "appear later in that row. Recolor every such row-local 8 to the row key. "
    "Scheduled variants also include a cyan marker in a headerless row, which "
    "must stay 8, and non-cyan body distractors, which must remain unchanged."
)

INVARIANTS = [
    "background is 0 and every grid is rectangular with ARC colors 0..9",
    "three to six active rows have nonzero, non-cyan headers in column 0",
    "every active row has at least one cyan marker after its header",
    "at least two header colors occur and at least one row remains headerless",
    "declared scene, palette, and teaching profiles are recoverable exactly",
]

# Exact geometry includes all three canonical input profiles plus compact and
# larger lawful generalizations.  The active-row count is part of the profile,
# so no post-draw clamping can make an override lie.
SCENE_PROFILE_SPECS: dict[str, tuple[int, int, int]] = {
    "canonical_6x7_r3": (6, 7, 3),
    "canonical_7x9_r4": (7, 9, 4),
    "canonical_8x10_r4": (8, 10, 4),
    "compact_5x6_r3": (5, 6, 3),
    "expanded_9x12_r5": (9, 12, 5),
    "expanded_12x16_r6": (12, 16, 6),
}
SCENE_PROFILES = (
    "canonical_6x7_r3",
    "canonical_7x9_r4",
    "canonical_8x10_r4",
    "compact_5x6_r3",
    "expanded_9x12_r5",
    "expanded_12x16_r6",
)
_PROFILE_BY_GEOMETRY = {
    dimensions: name for name, dimensions in SCENE_PROFILE_SPECS.items()
}

# These modes are mutually observable from the column-0 colors.
PALETTE_KINDS = (
    "canonical_distinct",
    "includes_nine",
    "repeated_pair",
)
_HEADER_COLORS = tuple(range(1, 8))

# Each mode creates a different, inferable body grammar.  The first reproduces
# canonical examples; the others are counterexamples to common shortcuts.
TEACHING_PROFILES = (
    "canonical_single",
    "multi_marker",
    "stray_marker",
    "mixed_markers",
    "inert_distractors",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted keyed draw; every value legal in every band",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_kind": {
        "type": "str",
        "default": "difficulty-weighted keyed draw",
        "valid": "|".join(PALETTE_KINDS),
    },
    "teaching_profile": {
        "type": "str",
        "default": "five-step sample-index curriculum",
        "valid": "|".join(TEACHING_PROFILES),
    },
}

# The strict canonical-like branch is intentionally common enough to anchor
# scale and morphology, but not so dominant that the shortcut counterexamples
# disappear from lessons.
MIN_STRICT_FRAC = 0.04


def _scene_options(difficulty: Any) -> tuple[str, ...]:
    """Weighted options retaining the complete exact override domain."""
    c6, c7, c8, compact, expanded, wide = SCENE_PROFILES
    if difficulty == "easy":
        return (c6, c6, c7, c7, c8, compact, expanded, wide)
    if difficulty == "hard":
        return (c6, c7, c8, c8, compact, expanded, expanded, wide, wide)
    return (c6, c7, c7, c8, compact, expanded, wide)


def _palette_options(difficulty: Any) -> tuple[str, ...]:
    """Keep canonical palettes common while all modes remain override-legal."""
    canonical, nine, repeated = PALETTE_KINDS
    if difficulty == "easy":
        return (canonical, canonical, canonical, canonical, nine, repeated)
    if difficulty == "hard":
        return (canonical, canonical, nine, nine, repeated, repeated)
    return (canonical, canonical, canonical, nine, nine, repeated)


def _scheduled_teaching_profile(sample_index: int, difficulty: Any) -> str:
    """Cycle every semantic branch in each consecutive five-instance window."""
    shift = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return TEACHING_PROFILES[(int(sample_index) + shift) % len(TEACHING_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _header_palette(rng: Any, count: int, kind: str) -> list[int]:
    """Materialize one exact palette mode for ``count`` active rows."""
    if kind == "canonical_distinct":
        return rng.sample(_HEADER_COLORS, count)
    if kind == "includes_nine":
        colors = [9, *rng.sample(_HEADER_COLORS, count - 1)]
        rng.shuffle(colors)
        return colors
    if kind == "repeated_pair":
        repeated = rng.choice(_HEADER_COLORS)
        colors = [repeated, repeated]
        colors.extend(rng.sample([c for c in _HEADER_COLORS if c != repeated], count - 2))
        rng.shuffle(colors)
        return colors
    raise ValueError(f"unsupported palette_kind: {kind!r}")


def analyze_grid(grid: Any) -> dict[str, Any]:
    """Return a pure structural analysis used by checks and override observers."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty or non-list grid"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list first row"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged or non-list row"]}
    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"cells must be integer ARC colors 0..9: {bad_cells[:3]}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "scene_profile": None,
            "palette_kind": None,
            "teaching_profile": None,
        }

    active_rows = [row for row, values in enumerate(grid) if values[0] != 0]
    inactive_rows = [row for row, values in enumerate(grid) if values[0] == 0]
    header_colors = [grid[row][0] for row in active_rows]
    marker_positions = [
        [(row, col) for col in range(1, width) if grid[row][col] == 8]
        for row in active_rows
    ]
    distractor_positions = [
        [
            (row, col, grid[row][col])
            for col in range(1, width)
            if grid[row][col] not in (0, 8)
        ]
        for row in active_rows
    ]
    stray_markers = [
        (row, col)
        for row in inactive_rows
        for col in range(1, width)
        if grid[row][col] == 8
    ]
    invalid_inactive = [
        (row, col, grid[row][col])
        for row in inactive_rows
        for col in range(1, width)
        if grid[row][col] not in (0, 8)
    ]
    marker_counts = [len(cells) for cells in marker_positions]
    distractor_counts = [len(cells) for cells in distractor_positions]

    scene_profile = _PROFILE_BY_GEOMETRY.get(
        (height, width, len(active_rows))
    )

    palette_kind: str | None = None
    header_counts = Counter(header_colors)
    if header_colors and all(color in (*_HEADER_COLORS, 9) for color in header_colors):
        if 9 not in header_counts and all(count == 1 for count in header_counts.values()):
            palette_kind = "canonical_distinct"
        elif (
            header_counts.get(9) == 1
            and len(header_counts) == len(header_colors)
            and all(color == 9 or color in _HEADER_COLORS for color in header_counts)
        ):
            palette_kind = "includes_nine"
        elif (
            9 not in header_counts
            and len(header_colors) >= 3
            and sorted(header_counts.values()) == [1] * (len(header_colors) - 2) + [2]
        ):
            palette_kind = "repeated_pair"

    teaching_profile: str | None = None
    one_double = (
        bool(marker_counts)
        and sorted(marker_counts) == [1] * (len(marker_counts) - 1) + [2]
    )
    if not invalid_inactive:
        if (
            all(count == 0 for count in distractor_counts)
            and not stray_markers
            and marker_counts
            and all(count == 1 for count in marker_counts)
        ):
            teaching_profile = "canonical_single"
        elif (
            all(count == 0 for count in distractor_counts)
            and not stray_markers
            and marker_counts
            and all(count == 2 for count in marker_counts)
        ):
            teaching_profile = "multi_marker"
        elif (
            all(count == 0 for count in distractor_counts)
            and len(stray_markers) == 1
            and marker_counts
            and all(count == 1 for count in marker_counts)
        ):
            teaching_profile = "stray_marker"
        elif (
            all(count == 0 for count in distractor_counts)
            and len(stray_markers) == 1
            and one_double
        ):
            teaching_profile = "mixed_markers"
        elif (
            not stray_markers
            and marker_counts
            and all(count == 1 for count in marker_counts)
            and all(count == 1 for count in distractor_counts)
            and all(
                cell[2] != header_colors[index]
                for index, cells in enumerate(distractor_positions)
                for cell in cells
            )
        ):
            teaching_profile = "inert_distractors"

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "active_rows": active_rows,
        "inactive_rows": inactive_rows,
        "header_colors": header_colors,
        "marker_positions": marker_positions,
        "marker_counts": marker_counts,
        "distractor_positions": distractor_positions,
        "distractor_counts": distractor_counts,
        "stray_markers": stray_markers,
        "invalid_inactive": invalid_inactive,
        "scene_profile": scene_profile,
        "palette_kind": palette_kind,
        "teaching_profile": teaching_profile,
    }


def observe_overrides(grid: Grid) -> dict[str, str]:
    """Recover every declared exact axis from the materialized grid."""
    analysis = analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    observed = {
        axis: analysis.get(axis)
        for axis in ("scene_profile", "palette_kind", "teaching_profile")
    }
    missing = [axis for axis, value in observed.items() if value is None]
    if missing:
        raise ValueError(f"grid does not realize declared axis/axes: {missing}")
    return observed  # type: ignore[return-value]


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: Any = None,
) -> list[str]:
    """Validate the complete row-header teaching grammar."""
    del difficulty, meta
    analysis = analyze_grid(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    active_rows = analysis["active_rows"]
    if analysis["scene_profile"] is None:
        errors.append(
            "shape/active-row tuple is outside the declared scene profiles: "
            f"{analysis['height']}x{analysis['width']} with {len(active_rows)} active rows"
        )
    if len(active_rows) < 3:
        errors.append("need at least three active rows")
    if len(active_rows) >= analysis["height"]:
        errors.append("need at least one headerless row")
    if any(color in (0, 8) for color in analysis["header_colors"]):
        errors.append("column-0 headers must be nonzero and non-cyan")
    if analysis["palette_kind"] is None:
        errors.append("header colors do not realize a declared palette_kind")
    if analysis["teaching_profile"] is None:
        errors.append("row bodies do not realize a declared teaching_profile")
    if len(set(analysis["header_colors"])) < 2:
        errors.append("need at least two distinct header colors")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept exactly the public one-marker geometry/palette envelope."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    analysis = analyze_grid(grid)
    reasons: list[str] = []
    if not str(analysis["scene_profile"]).startswith("canonical_"):
        reasons.append("shape/active-row count is not one of the three canonical profiles")
    if analysis["palette_kind"] != "canonical_distinct":
        reasons.append("canonical inputs use distinct headers from colors 1..7")
    if analysis["teaching_profile"] != "canonical_single":
        reasons.append("canonical inputs have one marker per active row and no body decoys")
    return reasons


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    """Generate one deterministic scene while honoring every declared override."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", _scene_options(difficulty))
    palette_kind = ctx.draw_choice("palette_kind", _palette_options(difficulty))
    if "teaching_profile" in overrides:
        teaching_profile = ctx.draw_choice("teaching_profile", TEACHING_PROFILES)
    else:
        # A singleton keyed draw records the scheduled default in normal GenCtx
        # provenance; explicit overrides still receive the complete domain.
        teaching_profile = ctx.draw_choice(
            "teaching_profile",
            (_scheduled_teaching_profile(sample_index, difficulty),),
        )

    height, width, active_count = SCENE_PROFILE_SPECS[scene_profile]
    row_rng = ctx.draw_rng("active_row_layout")
    color_rng = ctx.draw_rng("header_palette")
    body_rng = ctx.draw_rng("body_layout")

    active_rows = sorted(row_rng.sample(range(height), active_count))
    inactive_rows = [row for row in range(height) if row not in set(active_rows)]
    headers = _header_palette(color_rng, active_count, palette_kind)
    grid = full_grid(height, width, 0)

    mixed_row = active_rows[body_rng.randrange(len(active_rows))]
    for row, header in zip(active_rows, headers):
        grid[row][0] = header
        marker_count = 1
        if teaching_profile == "multi_marker":
            marker_count = 2
        elif teaching_profile == "mixed_markers" and row == mixed_row:
            marker_count = 2

        slots_needed = marker_count + (1 if teaching_profile == "inert_distractors" else 0)
        columns = body_rng.sample(range(1, width), slots_needed)
        for col in columns[:marker_count]:
            grid[row][col] = 8
        if teaching_profile == "inert_distractors":
            distractor_choices = [
                color for color in range(1, 10) if color not in (8, header)
            ]
            grid[row][columns[-1]] = body_rng.choice(distractor_choices)

    if teaching_profile in {"stray_marker", "mixed_markers"}:
        row = body_rng.choice(inactive_rows)
        grid[row][body_rng.randrange(1, width)] = 8

    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != requested[axis]:
            raise AssertionError(
                f"axis {axis!r} requested {requested[axis]!r} but materialized "
                f"as {observed[axis]!r}"
            )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python transcription used only by focused tests."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("rule requires a non-empty grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("rule requires a rectangular grid")
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        header = values[0]
        if header == 0:
            continue
        for col in range(1, width):
            if values[col] == 8:
                output[row][col] = header
    return output


def _lawful(grid: Grid) -> bool:
    return not self_check(grid)


def _has_multi_marker_row(grid: Grid) -> bool:
    info = analyze_grid(grid)
    return _lawful(grid) and any(count > 1 for count in info["marker_counts"])


def _has_headerless_marker(grid: Grid) -> bool:
    info = analyze_grid(grid)
    return _lawful(grid) and bool(info["stray_markers"])


def _has_inert_body_cell(grid: Grid) -> bool:
    info = analyze_grid(grid)
    return _lawful(grid) and any(info["distractor_counts"])


def _rival_global_first_header(grid: Grid) -> Grid:
    """Wrong shortcut: paint every marker with the first nonzero header."""
    output = [list(row) for row in grid]
    first_header = next((row[0] for row in grid if row[0] != 0), 0)
    for row, values in enumerate(grid):
        for col in range(1, len(values)):
            if values[col] == 8:
                output[row][col] = first_header
    return output


def _rival_first_marker_only(grid: Grid) -> Grid:
    """Wrong shortcut: recolor only the leftmost marker in each active row."""
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        if values[0] == 0:
            continue
        for col in range(1, len(values)):
            if values[col] == 8:
                output[row][col] = values[0]
                break
    return output


def _rival_zero_header_recolors(grid: Grid) -> Grid:
    """Wrong shortcut: apply the row header even when that header is zero."""
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col in range(1, len(values)):
            if values[col] == 8:
                output[row][col] = values[0]
    return output


def _rival_erase_nonmarker_body(grid: Grid) -> Grid:
    """Wrong shortcut: rebuild rows from headers and markers, erasing decoys."""
    output = rule_mirror(grid)
    for row, values in enumerate(grid):
        for col in range(1, len(values)):
            if values[col] not in (0, 8):
                output[row][col] = 0
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "global_first_header": _rival_global_first_header,
    "first_marker_only": _rival_first_marker_only,
    "zero_header_recolors": _rival_zero_header_recolors,
    "erase_nonmarker_body": _rival_erase_nonmarker_body,
}

# These three shortcuts are answer-equivalent on the public one-marker corpus.
# The generated curriculum therefore owes a verified counterexample to each.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    "first_marker_only": _rival_first_marker_only,
    "zero_header_recolors": _rival_zero_header_recolors,
    "erase_nonmarker_body": _rival_erase_nonmarker_body,
}

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "multiple_row_header_colors": lambda grid: _lawful(grid)
    and len(set(analyze_grid(grid)["header_colors"])) >= 2,
    "multiple_markers_in_one_row": _has_multi_marker_row,
    "headerless_marker_preserved": _has_headerless_marker,
    "non_cyan_body_cell_preserved": _has_inert_body_cell,
    "strict_canonical_anchor": lambda grid: not strict_canonical_like(grid),
}


WITNESS_RIVALS: dict[str, list[str]] = {
    "multiple_row_header_colors": ["global_first_header"],
    "multiple_markers_in_one_row": ["first_marker_only"],
    "headerless_marker_preserved": ["zero_header_recolors"],
    "non_cyan_body_cell_preserved": ["erase_nonmarker_body"],
    "strict_canonical_anchor": ["global_first_header"],
}
