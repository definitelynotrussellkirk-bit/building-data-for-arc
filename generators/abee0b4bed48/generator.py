"""Semantic generator for ARC task ``abee0b4bed48`` (source ``17cae0c1``).

The input is a height-3 strip of 3x3 zones.  The canonical Racket rule turns
*every cell* of a zone into a label determined only by that zone's gray (5)
cells:

* one gray cell -> 4;
* eight gray cells -> 3;
* three gray cells filling the top row -> 6;
* three gray cells filling the bottom row -> 1;
* every other three-gray-cell shape -> 9.

Normal scenes are linked semantic profiles, not independent feature marginals.
They deliberately contrast equal-count top/bottom/other triples, vary the
location of singleton cells and eight-cell holes, and include many non-row
three-cell shapes so count-only, fixed-marker, ring-only, and middle-row-only
shortcuts do not explain the curriculum.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "abee0b4bed48"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5e2603a489b9"
SUMMARY = (
    "A 3x(3N) strip of 3x3 zones; each zone is relabeled by gray-cell count, "
    "with three-cell top/bottom/other shapes mapping to different colors."
)

INVARIANTS = [
    "the grid is 3 rows and 3..6 adjacent 3x3 zones wide",
    "cells use only background 0 and semantic gray 5",
    "each zone has exactly 1, 8, or 3 gray cells",
    "top-row triples, bottom-row triples, and all other triples are distinct rule branches",
    "each normal scene belongs to one recognized linked semantic profile with at least three output labels",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "count3_triad",
    "extreme_triad",
    "all_labels",
    "one_position_pair",
    "eight_hole_pair",
    "other_shape_pair",
    "canonical_diagonals",
    "count3_six",
    "repeated_extremes",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted keyed draw; every profile remains overrideable",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_TOP = ((0, 0), (0, 1), (0, 2))
_MIDDLE = ((1, 0), (1, 1), (1, 2))
_BOTTOM = ((2, 0), (2, 1), (2, 2))
_MAIN_DIAGONAL = ((0, 0), (1, 1), (2, 2))
_ANTI_DIAGONAL = ((0, 2), (1, 1), (2, 0))
_ALL_CELLS = tuple((row, col) for row in range(3) for col in range(3))
_OTHER_PATTERNS = tuple(
    pattern
    for pattern in combinations(_ALL_CELLS, 3)
    if pattern not in (_TOP, _BOTTOM)
)

# Profile identity is recoverable from the returned grid.  These branch-count
# vectors are intentionally unique; public examples are recognized by exact
# signature first because two of them share a vector with a general profile.
_PROFILE_COUNTS = {
    "count3_triad": Counter({"top": 1, "bottom": 1, "other": 1}),
    "extreme_triad": Counter({"one": 1, "eight": 1, "other": 1}),
    "all_labels": Counter({"one": 1, "eight": 1, "top": 1, "bottom": 1, "other": 1}),
    "one_position_pair": Counter({"one": 2, "top": 1, "bottom": 1, "other": 1}),
    "eight_hole_pair": Counter({"eight": 2, "top": 1, "bottom": 1, "other": 1}),
    "other_shape_pair": Counter({"one": 1, "eight": 1, "top": 1, "bottom": 1, "other": 2}),
    "canonical_diagonals": Counter({"one": 1, "eight": 1, "other": 2}),
    "count3_six": Counter({"top": 2, "bottom": 2, "other": 2}),
    "repeated_extremes": Counter({"one": 2, "eight": 2, "top": 1, "bottom": 1}),
}
_COUNT_TO_PROFILE = {
    tuple(sorted(counts.items())): profile
    for profile, counts in _PROFILE_COUNTS.items()
}

_PUBLIC_INPUTS = {
    "public_train_1": (
        (5, 5, 5, 5, 5, 5, 0, 0, 0),
        (0, 0, 0, 5, 0, 5, 0, 0, 0),
        (0, 0, 0, 5, 5, 5, 5, 5, 5),
    ),
    "public_train_2": (
        (0, 0, 5, 0, 0, 0, 0, 0, 0),
        (0, 5, 0, 0, 0, 0, 0, 5, 0),
        (5, 0, 0, 5, 5, 5, 0, 0, 0),
    ),
    "public_train_3": (
        (0, 0, 0, 5, 5, 5, 5, 5, 5),
        (0, 5, 0, 0, 0, 0, 5, 0, 5),
        (0, 0, 0, 0, 0, 0, 5, 5, 5),
    ),
    "public_train_4": (
        (5, 5, 5, 0, 0, 0, 0, 0, 5),
        (5, 0, 5, 0, 5, 0, 0, 5, 0),
        (5, 5, 5, 0, 0, 0, 5, 0, 0),
    ),
    "public_test_1": (
        (0, 0, 0, 0, 0, 5, 5, 5, 5),
        (0, 0, 0, 0, 5, 0, 0, 0, 0),
        (5, 5, 5, 5, 0, 0, 0, 0, 0),
    ),
}
_PUBLIC_SIGNATURES = {grid: profile for profile, grid in _PUBLIC_INPUTS.items()}

# Include every profile in every band so every declared override is exact-or-
# loud; duplicates only alter the default mixture.
_PROFILE_WEIGHTS = {
    # Exact public examples stay in every default band, but only as a modest
    # canonical anchor.  The larger generalized pool avoids turning those five
    # finite grids into a memorization shortcut or depressing per-band input
    # distinctness below the review bar.
    "easy": (
        PUBLIC_PROFILES
        + GENERAL_PROFILES * 6
        + ("count3_triad",) * 6
        + ("extreme_triad",) * 6
        + ("all_labels",) * 2
    ),
    "medium": (
        PUBLIC_PROFILES
        + GENERAL_PROFILES * 5
        + ("all_labels",) * 3
        + ("one_position_pair",) * 2
        + ("eight_hole_pair",) * 2
        + ("other_shape_pair",) * 2
    ),
    "hard": (
        PUBLIC_PROFILES
        + GENERAL_PROFILES * 4
        + ("all_labels",) * 3
        + ("one_position_pair",) * 4
        + ("eight_hole_pair",) * 4
        + ("other_shape_pair",) * 6
        + ("canonical_diagonals",) * 3
        + ("count3_six",) * 6
        + ("repeated_extremes",) * 5
    ),
    None: PUBLIC_PROFILES + GENERAL_PROFILES * 6,
}


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("grid contains a non-row value")
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        raise ValueError("grid is ragged or has an empty row")
    return [list(row) for row in grid]


def _zone_record(grid, zone_index):
    cells = tuple(
        (row, col)
        for row in range(3)
        for col in range(3)
        if grid[row][3 * zone_index + col] == 5
    )
    cell_set = set(cells)
    if len(cells) == 1:
        kind, label = "one", 4
    elif len(cells) == 8:
        kind, label = "eight", 3
    elif cells == _TOP:
        kind, label = "top", 6
    elif cells == _BOTTOM:
        kind, label = "bottom", 1
    elif len(cells) == 3:
        kind, label = "other", 9
    else:
        kind, label = "invalid", 0
    holes = tuple(cell for cell in _ALL_CELLS if cell not in cell_set)
    return {
        "index": zone_index,
        "cells": cells,
        "kind": kind,
        "label": label,
        "one_position": cells[0] if kind == "one" else None,
        "eight_hole": holes[0] if kind == "eight" and len(holes) == 1 else None,
        "other_shape": cells if kind == "other" else None,
    }


def _profile_from_records(grid, records):
    signature = tuple(tuple(row) for row in grid)
    public = _PUBLIC_SIGNATURES.get(signature)
    if public is not None:
        return public
    counts = Counter(record["kind"] for record in records)
    profile = _COUNT_TO_PROFILE.get(tuple(sorted(counts.items())))
    if profile is None:
        return None

    one_positions = [record["one_position"] for record in records if record["kind"] == "one"]
    eight_holes = [record["eight_hole"] for record in records if record["kind"] == "eight"]
    other_shapes = [record["other_shape"] for record in records if record["kind"] == "other"]
    if profile in {"one_position_pair", "repeated_extremes"} and len(set(one_positions)) != len(one_positions):
        return None
    if profile in {"eight_hole_pair", "repeated_extremes"} and len(set(eight_holes)) != len(eight_holes):
        return None
    if profile == "other_shape_pair" and len(set(other_shapes)) != len(other_shapes):
        return None
    if profile == "canonical_diagonals" and set(other_shapes) != {_MAIN_DIAGONAL, _ANTI_DIAGONAL}:
        return None
    return profile


def _analysis(grid):
    errors = []
    try:
        normalized = _coerce_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "profile": None, "records": (), "output": None}

    height, width = len(normalized), len(normalized[0])
    if height != 3:
        errors.append(f"grid height must be 3, got {height}")
    if width % 3 != 0 or not 9 <= width <= 18:
        errors.append(f"grid width must be 9..18 and divisible by 3, got {width}")
    if any(type(value) is not int or value not in (0, 5) for row in normalized for value in row):
        errors.append("grid cells must use exactly ARC colors 0 and 5")
    if errors:
        return {"errors": errors, "profile": None, "records": (), "output": None}

    records = tuple(_zone_record(normalized, zone) for zone in range(width // 3))
    invalid = [record["index"] for record in records if record["kind"] == "invalid"]
    if invalid:
        errors.append(
            "each zone must contain exactly 1, 8, or 3 gray cells; invalid zones: "
            + ", ".join(map(str, invalid))
        )
    profile = None if errors else _profile_from_records(normalized, records)
    if profile is None and not errors:
        errors.append("zone branches do not form any recognized linked scene profile")
    labels = {record["label"] for record in records}
    if not errors and len(labels) < 3:
        errors.append("normal scenes must expose at least three distinct output labels")

    output = None
    if not errors:
        output = full_grid(3, width, 0)
        for record in records:
            start = 3 * record["index"]
            for row in range(3):
                for col in range(start, start + 3):
                    output[row][col] = record["label"]
    return {
        "errors": errors,
        "profile": profile,
        "records": records,
        "output": output,
        "branch_counts": Counter(record["kind"] for record in records),
    }


def canonical_profile_signature(grid):
    try:
        signature = tuple(tuple(row) for row in _coerce_grid(grid))
    except ValueError:
        return None
    return _PUBLIC_SIGNATURES.get(signature)


def observe_overrides(grid):
    """Recover the exact linked profile from the returned grid."""
    analysis = _analysis(grid)
    return {"scene_profile": analysis["profile"]} if not analysis["errors"] else {}


def rule_mirror(grid):
    """Python spelling of the canonical rule for focused tests only."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _cells_for_kind(kind, rng, used_one, used_holes, used_other):
    if kind == "top":
        return _TOP
    if kind == "bottom":
        return _BOTTOM
    if kind == "one":
        choices = [cell for cell in _ALL_CELLS if cell not in used_one]
        cell = rng.choice(choices or list(_ALL_CELLS))
        used_one.add(cell)
        return (cell,)
    if kind == "eight":
        choices = [cell for cell in _ALL_CELLS if cell not in used_holes]
        hole = rng.choice(choices or list(_ALL_CELLS))
        used_holes.add(hole)
        return tuple(cell for cell in _ALL_CELLS if cell != hole)
    if kind == "other":
        choices = [pattern for pattern in _OTHER_PATTERNS if pattern not in used_other]
        pattern = rng.choice(choices or list(_OTHER_PATTERNS))
        used_other.add(pattern)
        return pattern
    raise ValueError(f"unknown branch kind: {kind!r}")


def _general_grid(profile, rng):
    counts = _PROFILE_COUNTS[profile]
    kinds = [kind for kind, count in counts.items() for _ in range(count)]
    rng.shuffle(kinds)
    used_one = set()
    used_holes = set()
    used_other = set()
    forced_other = []
    if profile == "canonical_diagonals":
        forced_other = [_MAIN_DIAGONAL, _ANTI_DIAGONAL]
        rng.shuffle(forced_other)

    grid = full_grid(3, 3 * len(kinds), 0)
    for zone, kind in enumerate(kinds):
        if kind == "other" and forced_other:
            cells = forced_other.pop()
            used_other.add(cells)
        else:
            cells = _cells_for_kind(kind, rng, used_one, used_holes, used_other)
        for row, col in cells:
            grid[row][3 * zone + col] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", _PROFILE_WEIGHTS[difficulty])
    if profile in PUBLIC_PROFILES:
        return [list(row) for row in _PUBLIC_INPUTS[profile]]

    rng = context.draw_rng("scene")
    for _ in range(64):
        grid = _general_grid(profile, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["profile"] == profile:
            return [row[:] for row in grid]
    raise RuntimeError(f"could not construct scene_profile={profile!r}")


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = sorted(set(overrides) - {"scene_profile"})
        if unknown:
            errors.append("unknown override(s): " + ", ".join(unknown))
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and analysis["profile"] != requested:
            errors.append(
                f"requested scene_profile {requested!r}, observed {analysis['profile']!r}"
            )
    return errors
