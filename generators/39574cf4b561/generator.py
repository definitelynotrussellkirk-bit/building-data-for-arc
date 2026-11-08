"""Generator for bank task E61: complete every three-corner rectangle.

Each active color appears at exactly three corners of an axis-aligned
rectangle.  The output adds that color at the missing fourth corner.  The
canonical lessons also contain one irrelevant singleton of color 9.  Default
synthetic lessons retain those canonical anchors but rotate color 9 into an
active rectangle role once in every three scheduled samples, so each three-demo
lesson forces the model to use occurrence count and geometry rather than
memorizing that color 9 is always irrelevant.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39574cf4b561"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "6af9170b5713"
SUMMARY = (
    "A 0-background grid contains three or four distinct-color clues. Each "
    "clue is exactly three corners of an axis-aligned rectangle; complete its "
    "missing fourth corner in the same color. Preserve every existing cell, "
    "including the unrelated singleton distractor; color 9 becomes an active "
    "rectangle once in every three scheduled synthetic samples."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.5

INVARIANTS = [
    "background is 0",
    "exactly one nonzero color occurs once as an irrelevant distractor",
    "three or four other nonzero colors occur exactly three times",
    "color 9 is either the singleton or one active rectangle color",
    "each active color spans two rows and two columns with one empty corner",
    "the implied four-corner sets of distinct colors are disjoint",
    "the output fills every implied corner and preserves all other cells",
]

# The four linked (height, width, active-color-count) profiles occurring in the
# five official train/test inputs.  The duplicated 11x11/three-color profile is
# represented once because it is structurally identical.
SCENE_PROFILES = {
    "p10x10_three": (10, 10, 3),
    "p11x11_three": (11, 11, 3),
    "p11x11_four": (11, 11, 4),
    "p12x12_three": (12, 12, 3),
}
_SCENE_NAMES = tuple(SCENE_PROFILES)
_PROFILE_BY_SHAPE = {value: name for name, value in SCENE_PROFILES.items()}

MISSING_PATTERNS = ("tl", "tr", "bl", "br", "mixed")
DISTRACTOR_RELATIONS = ("outside", "inside")
PALETTE_KINDS = ("low", "high", "mixed")
ROLE_ASSIGNMENTS = ("canonical_9", "rotated_9_active")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule over canonical linked profiles",
        "valid": "p10x10_three|p11x11_three|p11x11_four|p12x12_three",
    },
    "missing_pattern": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "tl|tr|bl|br|mixed",
    },
    "distractor_relation": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "outside|inside",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "low|high|mixed",
    },
}

# Every Cartesian combination of the four exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
SCHEDULE_PROFILES = _SCENE_NAMES

_CORNER_NAMES = ("tl", "tr", "bl", "br")


def schedule_profile(seed, sample_index, difficulty=None):
    """Public deterministic profile schedule used by the semantic gate."""
    del seed, difficulty
    return _SCENE_NAMES[int(sample_index) % len(_SCENE_NAMES)]


def schedule_role_assignment(seed, sample_index, difficulty=None):
    """Place one shortcut-breaking role in every three-example lesson."""
    del seed, difficulty
    return (
        "rotated_9_active"
        if int(sample_index) % 3 == 2
        else "canonical_9"
    )


def _scheduled_value(options, sample_index, stride, offset=0):
    return options[(int(sample_index) // stride + offset) % len(options)]


def _profile_name(height, width, active_count):
    return _PROFILE_BY_SHAPE.get((height, width, active_count))


def _analyze(grid):
    """Return task-local geometry facts and validation errors."""
    if not grid or not grid[0]:
        return {"errors": ["empty grid"]}
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}

    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in values
    ):
        return {"errors": ["cell value outside integer ARC palette 0..9"]}

    errors: list[str] = []
    if 0 not in values:
        errors.append("zero background is absent")

    counts = Counter(value for value in values if value != 0)
    singleton_colors = sorted(
        color for color, count in counts.items() if count == 1
    )
    active_colors = sorted(
        color for color, count in counts.items() if count == 3
    )
    bad_counts = sorted(
        (color, count)
        for color, count in counts.items()
        if count not in (1, 3)
    )
    if bad_counts:
        errors.append(
            f"nonzero colors must occur once or three times, got {bad_counts}"
        )
    if len(singleton_colors) != 1:
        errors.append(
            "expected exactly one singleton distractor color, "
            f"got {singleton_colors}"
        )

    profile = _profile_name(height, width, len(active_colors))
    if profile is None:
        errors.append(
            "canvas/active-count tuple "
            f"{(height, width, len(active_colors))} is not canonical-linked"
        )

    cells_by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                cells_by_color[value].append((row_index, col_index))

    rectangles = []
    occupied_corners: set[tuple[int, int]] = set()
    for color in active_colors:
        cells = tuple(cells_by_color[color])
        rows = tuple(sorted({row for row, _ in cells}))
        cols = tuple(sorted({col for _, col in cells}))
        if len(rows) != 2 or len(cols) != 2:
            errors.append(
                f"color {color} must span exactly two rows and two columns"
            )
            continue
        if not (
            2 <= rows[1] - rows[0] <= 4
            and 2 <= cols[1] - cols[0] <= 4
        ):
            errors.append(
                f"color {color} rectangle row/column spans must both be in 2..4"
            )
        corners = {(row, col) for row in rows for col in cols}
        missing = corners - set(cells)
        if len(missing) != 1:
            errors.append(
                f"color {color} does not define exactly one missing corner"
            )
            continue
        missing_cell = next(iter(missing))
        if grid[missing_cell[0]][missing_cell[1]] != 0:
            errors.append(f"color {color} implied corner is not empty")
        overlap = occupied_corners & corners
        if overlap:
            errors.append(f"rectangle corners overlap at {sorted(overlap)}")
        occupied_corners.update(corners)
        rectangles.append(
            {
                "color": color,
                "cells": cells,
                "rows": rows,
                "cols": cols,
                "corners": frozenset(corners),
                "missing": missing_cell,
            }
        )

    singleton_color = singleton_colors[0] if len(singleton_colors) == 1 else None
    singleton_cell = (
        cells_by_color[singleton_color][0]
        if singleton_color is not None
        and len(cells_by_color[singleton_color]) == 1
        else None
    )
    if singleton_cell in occupied_corners:
        errors.append("singleton distractor may not occupy a rectangle corner")

    role_assignment = None
    if singleton_color is not None:
        if singleton_color == 9 and 9 not in active_colors:
            role_assignment = "canonical_9"
        elif singleton_color != 9 and 9 in active_colors:
            role_assignment = "rotated_9_active"
        else:
            errors.append(
                "color 9 must be either the singleton distractor or one active "
                "rectangle color"
            )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "counts": counts,
        "profile": profile,
        "active_colors": tuple(active_colors),
        "singleton_color": singleton_color,
        "singleton": singleton_cell,
        "role_assignment": role_assignment,
        "rectangles": tuple(rectangles),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the linked canonical family, including the singleton 9 role."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact canonical color-role manifold within the curriculum."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if not errors and analysis["role_assignment"] != "canonical_9":
        errors.append("canonical-linked examples use color 9 as the singleton")
    return errors


def canonical_profile_signature(grid):
    """Return the linked profile name, or ``None`` for an invalid scene."""
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis["profile"]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected Racket rule."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [list(row) for row in grid]
    for rectangle in analysis["rectangles"]:
        row, col = rectangle["missing"]
        out[row][col] = rectangle["color"]
    return out


def _all_rectangles(height, width):
    rectangles = []
    for top in range(height):
        for row_gap in range(2, 5):
            bottom = top + row_gap
            if bottom >= height:
                continue
            for left in range(width):
                for col_gap in range(2, 5):
                    right = left + col_gap
                    if right >= width:
                        continue
                    corners = (
                        (top, left),
                        (top, right),
                        (bottom, left),
                        (bottom, right),
                    )
                    rectangles.append(
                        {
                            "rows": (top, bottom),
                            "cols": (left, right),
                            "corners": corners,
                        }
                    )
    return rectangles


def _singleton_candidates(height, width, rectangles, relation):
    used = {
        cell
        for rectangle in rectangles
        for cell in rectangle["corners"]
    }
    candidates = []
    for row in range(height):
        for col in range(width):
            cell = (row, col)
            if cell in used:
                continue
            inside_any = any(
                rectangle["rows"][0] <= row <= rectangle["rows"][1]
                and rectangle["cols"][0] <= col <= rectangle["cols"][1]
                for rectangle in rectangles
            )
            if (relation == "inside" and inside_any) or (
                relation == "outside" and not inside_any
            ):
                candidates.append(cell)
    return candidates


def _select_layout(height, width, active_count, relation, rng):
    all_rectangles = _all_rectangles(height, width)
    for _ in range(256):
        candidates = list(all_rectangles)
        rng.shuffle(candidates)
        selected = []
        used: set[tuple[int, int]] = set()
        for rectangle in candidates:
            corners = set(rectangle["corners"])
            if corners & used:
                continue
            selected.append(rectangle)
            used.update(corners)
            if len(selected) == active_count:
                break
        if len(selected) != active_count:
            continue
        singleton_cells = _singleton_candidates(
            height, width, selected, relation
        )
        if singleton_cells:
            return selected, rng.choice(singleton_cells)
    raise RuntimeError(
        f"could not place {active_count} rectangles with {relation} singleton"
    )


def _role_colors(palette_kind, active_count, role_assignment, rng):
    low = list(range(1, 5))
    high = list(range(5, 9))
    chosen_count = active_count if role_assignment == "canonical_9" else active_count - 1
    if palette_kind == "low":
        colors = rng.sample(low, chosen_count)
    elif palette_kind == "high":
        colors = rng.sample(high, chosen_count)
    else:
        low_count = rng.randint(1, chosen_count - 1)
        colors = rng.sample(low, low_count) + rng.sample(
            high, chosen_count - low_count
        )
    if role_assignment == "canonical_9":
        singleton_color = 9
    else:
        colors.append(9)
        singleton_color = rng.choice(
            [color for color in range(1, 9) if color not in colors]
        )
    rng.shuffle(colors)
    return colors, singleton_color


def _missing_names(pattern, active_count, rng):
    if pattern != "mixed":
        return [pattern] * active_count
    names = list(_CORNER_NAMES)
    rng.shuffle(names)
    return [names[index % len(names)] for index in range(active_count)]


def _corner_map(rectangle):
    top, bottom = rectangle["rows"]
    left, right = rectangle["cols"]
    return {
        "tl": (top, left),
        "tr": (top, right),
        "bl": (bottom, left),
        "br": (bottom, right),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    allowed = set(AXES)
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    # Scheduled defaults prevent small lesson windows from accidentally
    # omitting a canonical profile or a decisive semantic branch. Explicit
    # caller overrides still pass through GenCtx's exact-domain validation.
    effective = dict(overrides)
    effective.setdefault(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    effective.setdefault(
        "missing_pattern",
        _scheduled_value(MISSING_PATTERNS, sample_index, 1),
    )
    effective.setdefault(
        "distractor_relation",
        _scheduled_value(DISTRACTOR_RELATIONS, sample_index, 2),
    )
    effective.setdefault(
        "palette_kind",
        _scheduled_value(PALETTE_KINDS, sample_index, 3),
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile_name = ctx.draw_choice("scene_profile", _SCENE_NAMES)
    missing_pattern = ctx.draw_choice("missing_pattern", MISSING_PATTERNS)
    relation = ctx.draw_choice(
        "distractor_relation", DISTRACTOR_RELATIONS
    )
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    role_assignment = schedule_role_assignment(seed, sample_index, difficulty)

    height, width, active_count = SCENE_PROFILES[profile_name]
    band = difficulty or "medium"
    rng = ctx.draw_rng(f"layout:{band}")
    rectangles, singleton = _select_layout(
        height, width, active_count, relation, rng
    )
    colors, singleton_color = _role_colors(
        palette_kind, active_count, role_assignment, rng
    )
    missing_names = _missing_names(missing_pattern, active_count, rng)

    grid = full_grid(height, width, 0)
    for rectangle, color, missing_name in zip(
        rectangles, colors, missing_names
    ):
        for name, (row, col) in _corner_map(rectangle).items():
            if name != missing_name:
                grid[row][col] = color
    grid[singleton[0]][singleton[1]] = singleton_color
    return grid


def _missing_name(rectangle):
    for name, cell in _corner_map(rectangle).items():
        if cell == rectangle["missing"]:
            return name
    raise AssertionError("missing corner is outside its rectangle")


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact semantic axis from a lawful returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"scene_profile": analysis.get("profile") or "unknown"}

    missing_names = {
        _missing_name(rectangle) for rectangle in analysis["rectangles"]
    }
    missing_pattern = (
        next(iter(missing_names)) if len(missing_names) == 1 else "mixed"
    )

    singleton_row, singleton_col = analysis["singleton"]
    inside_any = any(
        rectangle["rows"][0] <= singleton_row <= rectangle["rows"][1]
        and rectangle["cols"][0] <= singleton_col <= rectangle["cols"][1]
        for rectangle in analysis["rectangles"]
    )
    active_colors = tuple(
        color for color in analysis["active_colors"] if color != 9
    )
    if active_colors and max(active_colors) <= 4:
        palette_kind = "low"
    elif active_colors and min(active_colors) >= 5:
        palette_kind = "high"
    else:
        palette_kind = "mixed"

    return {
        "scene_profile": analysis["profile"],
        "missing_pattern": missing_pattern,
        "distractor_relation": "inside" if inside_any else "outside",
        "palette_kind": palette_kind,
    }

# ---------------------------------------------------------------------------
# Task-linked semantic evidence
# ---------------------------------------------------------------------------

def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _has_missing_orientation(grid, orientation):
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and any(
            _missing_name(rectangle) == orientation
            for rectangle in analysis["rectangles"]
        )
    )


def _has_relation(grid, relation):
    analysis = _lawful_analysis(grid)
    return bool(
        analysis
        and observe_overrides(grid)["distractor_relation"] == relation
    )


def _has_palette(grid, palette_kind):
    analysis = _lawful_analysis(grid)
    return bool(
        analysis and observe_overrides(grid)["palette_kind"] == palette_kind
    )


def _has_role_assignment(grid, role_assignment):
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["role_assignment"] == role_assignment)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_complete_first(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    rectangle = analysis["rectangles"][0]
    row, col = rectangle["missing"]
    out[row][col] = rectangle["color"]
    return out


def _rival_erase_singleton(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return [list(row) for row in grid]
    out = rule_mirror(grid)
    row, col = analysis["singleton"]
    out[row][col] = 0
    return out


def _rival_fixed_orientation(grid, orientation):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    for rectangle in analysis["rectangles"]:
        if _missing_name(rectangle) == orientation:
            row, col = rectangle["missing"]
            out[row][col] = rectangle["color"]
    return out


def _rival_fixed_tl(grid):
    return _rival_fixed_orientation(grid, "tl")


def _rival_fixed_tr(grid):
    return _rival_fixed_orientation(grid, "tr")


def _rival_fixed_bl(grid):
    return _rival_fixed_orientation(grid, "bl")


def _rival_fixed_br(grid):
    return _rival_fixed_orientation(grid, "br")


def _rival_never_complete_color_9(grid):
    """Canonical-fitting shortcut that memorizes color 9 as irrelevant."""
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    for rectangle in analysis["rectangles"]:
        if rectangle["color"] == 9:
            continue
        row, col = rectangle["missing"]
        out[row][col] = rectangle["color"]
    return out


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "complete_first_rectangle": _rival_complete_first,
    "erase_singleton": _rival_erase_singleton,
    "complete_tl_only": _rival_fixed_tl,
    "complete_tr_only": _rival_fixed_tr,
    "complete_bl_only": _rival_fixed_bl,
    "complete_br_only": _rival_fixed_br,
    "never_complete_color_9": _rival_never_complete_color_9,
}

SEMANTIC_WITNESSES = {
    "missing_tl": lambda grid: _has_missing_orientation(grid, "tl"),
    "missing_tr": lambda grid: _has_missing_orientation(grid, "tr"),
    "missing_bl": lambda grid: _has_missing_orientation(grid, "bl"),
    "missing_br": lambda grid: _has_missing_orientation(grid, "br"),
    "mixed_missing_orientations": lambda grid: (
        (analysis := _lawful_analysis(grid)) is not None
        and len(
            {
                _missing_name(rectangle)
                for rectangle in analysis["rectangles"]
            }
        )
        > 1
    ),
    "multiple_rectangles": lambda grid: (
        (analysis := _lawful_analysis(grid)) is not None
        and len(analysis["rectangles"]) >= 3
    ),
    "three_rectangles": lambda grid: (
        (analysis := _lawful_analysis(grid)) is not None
        and len(analysis["rectangles"]) == 3
    ),
    "four_rectangles": lambda grid: (
        (analysis := _lawful_analysis(grid)) is not None
        and len(analysis["rectangles"]) == 4
    ),
    "singleton_inside_rectangle": lambda grid: _has_relation(grid, "inside"),
    "singleton_outside_rectangles": lambda grid: _has_relation(grid, "outside"),
    "palette_low": lambda grid: _has_palette(grid, "low"),
    "palette_high": lambda grid: _has_palette(grid, "high"),
    "palette_mixed": lambda grid: _has_palette(grid, "mixed"),
    "canonical_9_singleton": lambda grid: _has_role_assignment(
        grid, "canonical_9"
    ),
    "rotated_9_active": lambda grid: _has_role_assignment(
        grid, "rotated_9_active"
    ),
}

WITNESS_RIVALS = {
    # A fixed-orientation completion rule must miss at least the witnessed
    # opposite orientation, even in a mixed-orientation scene.
    "missing_tl": ["complete_br_only"],
    "missing_tr": ["complete_bl_only"],
    "missing_bl": ["complete_tr_only"],
    "missing_br": ["complete_tl_only"],
    "mixed_missing_orientations": ["complete_first_rectangle"],
    "multiple_rectangles": ["complete_first_rectangle"],
    "three_rectangles": ["complete_first_rectangle"],
    "four_rectangles": ["complete_first_rectangle"],
    "singleton_inside_rectangle": ["erase_singleton"],
    "singleton_outside_rectangles": ["erase_singleton"],
    "palette_low": ["identity"],
    "palette_high": ["identity"],
    "palette_mixed": ["identity"],
    "canonical_9_singleton": ["identity"],
    "rotated_9_active": ["never_complete_color_9"],
}


CANONICAL_SHORTCUTS = {
    "never_complete_color_9": _rival_never_complete_color_9,
}

LESSON_COMPETITORS = {
    "identity": _rival_identity,
    "complete_first_rectangle": _rival_complete_first,
    "erase_singleton": _rival_erase_singleton,
    "complete_tl_only": _rival_fixed_tl,
    "complete_tr_only": _rival_fixed_tr,
    "complete_bl_only": _rival_fixed_bl,
    "complete_br_only": _rival_fixed_br,
    "never_complete_color_9": _rival_never_complete_color_9,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named wrong rule to be refuted by the visible demos."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        ) and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes query")
    return reasons
