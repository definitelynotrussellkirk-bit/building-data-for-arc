"""Generator for ARC task 7147e98f8173.

A single blue corner cell supplies a rotation command for an asymmetric red
polyomino (TL=0, TR=90 clockwise, BR=180, BL=270).  The displacement from the
green marker to the orange marker supplies a translation vector.  The output
is a blank zero canvas containing the rotated, translated template in cyan.

The four-profile curriculum separates corner from displacement: one corner is
shown with two vectors and one vector is shown with two corners in every cycle.
This directly refutes the strongest canonical-training shortcut, which assigns
one memorized vector to each observed corner.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7147e98f8173"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "228397e84af8"
EXAMPLES_NEEDED = 7
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Rotate the red asymmetric template according to the blue corner "
    "(TL/TR/BR/BL = 0/90/180/270 degrees clockwise), translate it by the "
    "green-to-orange vector, and draw the result in cyan on a blank canvas."
)

INVARIANTS = [
    "exactly one blue control cell occupies a canvas corner",
    "the red object is one recognized connected asymmetric template",
    "exactly one green marker and one orange marker define a nonzero vector",
    "the rotated and translated template remains entirely in bounds",
    "ordinary inputs contain only colors 0, 1, 2, 3, and 6",
]

COUNTER_HYPOTHESES = [
    "each corner has one memorized displacement",
    "copy the template without rotating it",
    "rotate the template but ignore the marker displacement",
    "copy the input or preserve its nonzero cells in the output",
]

_CORNERS = ("tl", "tr", "br", "bl")
_CORNER_TO_TURNS = {"tl": 0, "tr": 1, "br": 2, "bl": 3}
_CORNER_FIXED_VECTORS = {
    "tl": (3, -1),
    "tr": (3, 4),
    "br": (2, 4),
    "bl": (-1, -4),
}

# The named input templates are all asymmetric and are recoverable exactly
# from the returned red cells after translation to their bounding-box origin.
_TEMPLATES: dict[str, tuple[tuple[int, int], ...]] = {
    "l3_down": ((0, 0), (1, 0), (1, 1)),
    "l3_right": ((0, 0), (0, 1), (1, 1)),
    "hook4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "stair4": ((0, 0), (1, 0), (1, 1), (2, 1)),
}
_TEMPLATE_NAMES = tuple(_TEMPLATES)
_TEMPLATE_BY_CELLS = {frozenset(cells): name for name, cells in _TEMPLATES.items()}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 10..16", "valid": "10..16"},
    "grid_w": {"type": "int", "default": "scheduled 12..18", "valid": "12..18"},
    "corner": {"type": "str", "default": "scheduled", "valid": "tl|tr|br|bl"},
    "template": {
        "type": "str",
        "default": "scheduled",
        "valid": "l3_down|l3_right|hook4|stair4",
    },
    "vector_dr": {"type": "int", "default": "scheduled", "valid": "-4..4"},
    "vector_dc": {"type": "int", "default": "scheduled", "valid": "-4..4"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"vector_dr": 0, "vector_dc": 0},
)

_PROFILES = (
    "canonical_anchor",
    "same_corner_new_vector",
    "same_vector_new_corner",
    "independent_rotation_translation",
)
SCHEDULE_PROFILES = _PROFILES

# Each difficulty band includes one empirical canonical axis profile.  The next
# two profiles explicitly decouple corner and vector; the fourth broadens both.
_DEFAULTS = {
    "easy": (
        (10, 12, "tr", "hook4", 3, 4),
        (10, 12, "tr", "stair4", -2, -3),
        (11, 13, "bl", "l3_down", 3, 4),
        (10, 13, "br", "l3_right", -3, 2),
    ),
    "medium": (
        (11, 13, "tr", "stair4", 2, 3),
        (13, 15, "tr", "l3_down", -3, -2),
        (12, 16, "bl", "hook4", 2, 3),
        (14, 15, "br", "l3_right", 3, -4),
    ),
    "hard": (
        (10, 12, "tl", "l3_down", 3, -1),
        (16, 18, "tl", "stair4", -4, 4),
        (15, 17, "br", "hook4", 3, -1),
        (16, 17, "bl", "l3_right", 4, -3),
    ),
}

# Exact observable profiles of all four canonical demonstrations and the test.
_CANONICAL_AXIS_PROFILES = {
    (10, 12, "tl", "l3_down", 3, -1),
    (10, 12, "tr", "hook4", 3, 4),
    (11, 13, "br", "l3_right", 2, 4),
    (10, 12, "bl", "stair4", -1, -4),
    (11, 13, "tr", "stair4", 2, 3),
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_ALLOWED_COLORS = {0, 1, 2, 3, 6}


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _DEFAULTS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the semantic profile selected by sample-index residue."""
    del seed
    _band(difficulty)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    return _PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_once(cells) -> tuple[tuple[int, int], ...]:
    """Rotate normalized cells 90 degrees clockwise and renormalize."""
    normalized = _normalize(cells)
    height = max(r for r, _ in normalized) + 1
    return _normalize((c, height - 1 - r) for r, c in normalized)


def _rotate(cells, quarter_turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(quarter_turns % 4):
        result = _rotate_once(result)
    return result


def _shape_size(cells) -> tuple[int, int]:
    normalized = _normalize(cells)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _corner_cells(h: int, w: int) -> dict[str, tuple[int, int]]:
    return {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "br": (h - 1, w - 1),
        "bl": (h - 1, 0),
    }


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _analyze(grid) -> dict[str, Any]:
    """Recover task semantics from an input grid without generator metadata."""
    result: dict[str, Any] = {"errors": _grid_errors(grid)}
    if result["errors"]:
        return result

    h, w = len(grid), len(grid[0])
    colors = {value for row in grid for value in row}
    extra = sorted(colors - _ALLOWED_COLORS)
    if extra:
        result["errors"].append(f"ordinary input contains unsupported colors: {extra}")

    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (1, 2, 3, 6)
    }
    blues, reds, greens, oranges = (positions[color] for color in (1, 2, 3, 6))

    if len(blues) != 1:
        result["errors"].append(f"expected exactly one blue control, found {len(blues)}")
    corner = None
    if len(blues) == 1:
        inverse = {position: name for name, position in _corner_cells(h, w).items()}
        corner = inverse.get(blues[0])
        if corner is None:
            result["errors"].append("the blue control must occupy a canvas corner")

    if len(greens) != 1:
        result["errors"].append(f"expected exactly one green marker, found {len(greens)}")
    if len(oranges) != 1:
        result["errors"].append(f"expected exactly one orange marker, found {len(oranges)}")

    template = None
    red_origin = None
    red_local: tuple[tuple[int, int], ...] = ()
    if not reds:
        result["errors"].append("expected one red template, found no red cells")
    else:
        red_origin = (min(r for r, _ in reds), min(c for _, c in reds))
        red_local = _normalize(reds)
        template = _TEMPLATE_BY_CELLS.get(frozenset(red_local))
        if template is None:
            result["errors"].append(
                "red cells do not form one recognized connected asymmetric template"
            )

    vector = None
    if len(greens) == 1 and len(oranges) == 1:
        vector = (oranges[0][0] - greens[0][0], oranges[0][1] - greens[0][1])
        if vector == (0, 0):
            result["errors"].append("green-to-orange vector must be nonzero")
        if not (-4 <= vector[0] <= 4 and -4 <= vector[1] <= 4):
            result["errors"].append(
                f"green-to-orange vector {vector!r} lies outside reviewed -4..4 bounds"
            )

    transformed: tuple[tuple[int, int], ...] = ()
    if corner is not None and template is not None and red_origin is not None and vector is not None:
        rotated = _rotate(red_local, _CORNER_TO_TURNS[corner])
        out_origin = (red_origin[0] + vector[0], red_origin[1] + vector[1])
        transformed = tuple((out_origin[0] + r, out_origin[1] + c) for r, c in rotated)
        if any(not (0 <= r < h and 0 <= c < w) for r, c in transformed):
            result["errors"].append("rotated and translated template leaves the canvas")

    result.update(
        {
            "height": h,
            "width": w,
            "corner": corner,
            "template": template,
            "red_cells": tuple(sorted(reds)),
            "red_origin": red_origin,
            "red_local": red_local,
            "green": greens[0] if len(greens) == 1 else None,
            "orange": oranges[0] if len(oranges) == 1 else None,
            "vector": vector,
            "transformed": transformed,
        }
    )
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover all six ordinary axes exactly from the visible input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    dr, dc = analysis["vector"]
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "corner": analysis["corner"],
        "template": analysis["template"],
        "vector_dr": dr,
        "vector_dc": dc,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, mislabeled, or off-contract inputs."""
    errors: list[str] = []
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append(f"unknown difficulty: {difficulty!r}")
    analysis = _analyze(grid)
    errors.extend(analysis["errors"])
    if errors:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict empirical-manifold predicate based on all canonical input axes."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    dr, dc = analysis["vector"]
    profile = (
        analysis["height"],
        analysis["width"],
        analysis["corner"],
        analysis["template"],
        dr,
        dc,
    )
    if profile not in _CANONICAL_AXIS_PROFILES:
        reasons.append(f"axis profile is outside the five canonical profiles: {profile!r}")
    return reasons


def _render_transformation(
    grid,
    *,
    quarter_turns: int,
    vector: tuple[int, int],
) -> list[list[int]]:
    """Render a candidate rule on a zero canvas, clipping rival overflow."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    h, w = analysis["height"], analysis["width"]
    rr, rc = analysis["red_origin"]
    dr, dc = vector
    cells = _rotate(analysis["red_local"], quarter_turns)
    out = full_grid(h, w, 0)
    for r, c in cells:
        tr, tc = rr + dr + r, rc + dc + c
        if 0 <= tr < h and 0 <= tc < w:
            out[tr][tc] = 8
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the synchronized Racket authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return _render_transformation(
        grid,
        quarter_turns=_CORNER_TO_TURNS[analysis["corner"]],
        vector=analysis["vector"],
    )


def _rival_corner_fixed_vector(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return _render_transformation(
        grid,
        quarter_turns=_CORNER_TO_TURNS[analysis["corner"]],
        vector=_CORNER_FIXED_VECTORS[analysis["corner"]],
    )


def _rival_ignore_rotation(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return _render_transformation(grid, quarter_turns=0, vector=analysis["vector"])


def _rival_ignore_vector(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return _render_transformation(
        grid,
        quarter_turns=_CORNER_TO_TURNS[analysis["corner"]],
        vector=(0, 0),
    )


def _rival_identity(grid):
    return [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "corner_fixed_vector": _rival_corner_fixed_vector,
    "ignore_rotation": _rival_ignore_rotation,
    "ignore_vector": _rival_ignore_vector,
    "identity": _rival_identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"corner_fixed_vector": _rival_corner_fixed_vector}


def _lawful(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _witness_corner_vector_decoupled(grid) -> bool:
    analysis = _lawful(grid)
    return bool(
        analysis
        and analysis["vector"] != _CORNER_FIXED_VECTORS[analysis["corner"]]
        and rule_mirror(grid) != _rival_corner_fixed_vector(grid)
    )


def _witness_rotation_required(grid) -> bool:
    analysis = _lawful(grid)
    return bool(
        analysis
        and analysis["corner"] != "tl"
        and rule_mirror(grid) != _rival_ignore_rotation(grid)
    )


def _witness_translation_required(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and rule_mirror(grid) != _rival_ignore_vector(grid))


def _witness_blank_output(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and rule_mirror(grid) != _rival_identity(grid))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "corner_vector_decoupled": _witness_corner_vector_decoupled,
    "rotation_required": _witness_rotation_required,
    "translation_required": _witness_translation_required,
    "blank_output": _witness_blank_output,
}
WITNESS_RIVALS = {
    "corner_vector_decoupled": ["corner_fixed_vector"],
    "rotation_required": ["ignore_rotation"],
    "translation_required": ["ignore_vector"],
    "blank_output": ["identity"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any seven-demo lesson that leaves a named rival viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    corner_to_vectors: dict[str, set[tuple[int, int]]] = defaultdict(set)
    vector_to_corners: dict[tuple[int, int], set[str]] = defaultdict(set)

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the rotation-vector rule")
            continue
        valid_demos.append(demo)
        vector = analysis["vector"]
        corner_to_vectors[analysis["corner"]].add(vector)
        vector_to_corners[vector].add(analysis["corner"])

    if not any(len(vectors) >= 2 for vectors in corner_to_vectors.values()):
        reasons.append("demonstrations never reuse one corner with multiple vectors")
    if not any(len(corners) >= 2 for corners in vector_to_corners.values()):
        reasons.append("demonstrations never reuse one vector with multiple corners")

    q_analysis = _analyze(query["input"])
    if q_analysis["errors"]:
        reasons.append("query input is outside the task grammar")
        return reasons
    q_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != q_truth:
        reasons.append("query output disagrees with the rotation-vector rule")

    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in valid_demos
            )
            if survives and competitor(query["input"]) != q_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (
        ("grid_h", 10, 16),
        ("grid_w", 12, 18),
        ("vector_dr", -4, 4),
        ("vector_dc", -4, 4),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    for name, options in (("corner", _CORNERS), ("template", _TEMPLATE_NAMES)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if value not in options:
            raise ValueError(f"{name} override {value!r} not in {options}")

    dr = overrides.get("vector_dr")
    dc = overrides.get("vector_dc")
    if dr == 0 and dc == 0:
        raise ValueError("incompatible overrides vector_dr=0 and vector_dc=0")


def _draw_profile_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_profile_choice(ctx, overrides, name: str, default: str, options):
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _placement_candidates(
    *,
    h: int,
    w: int,
    corner: str,
    template: str,
    vector: tuple[int, int],
) -> list[tuple[tuple[int, int], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]]:
    """Enumerate red origins with lawful original and transformed cells."""
    local = _TEMPLATES[template]
    rotated = _rotate(local, _CORNER_TO_TURNS[corner])
    th, tw = _shape_size(local)
    control = _corner_cells(h, w)[corner]
    all_corners = set(_corner_cells(h, w).values())
    dr, dc = vector
    candidates = []
    for rr in range(h - th + 1):
        for rc in range(w - tw + 1):
            red = tuple((rr + r, rc + c) for r, c in local)
            transformed = tuple((rr + dr + r, rc + dc + c) for r, c in rotated)
            if any(not (0 <= r < h and 0 <= c < w) for r, c in transformed):
                continue
            if control in red or set(red) & all_corners:
                continue
            candidates.append(((rr, rc), red, transformed))
    return candidates


def _marker_candidates(
    *,
    h: int,
    w: int,
    vector: tuple[int, int],
    occupied: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    dr, dc = vector
    all_corners = set(_corner_cells(h, w).values())
    candidates = []
    for gr in range(h):
        for gc in range(w):
            orange = (gr + dr, gc + dc)
            green = (gr, gc)
            if not (0 <= orange[0] < h and 0 <= orange[1] < w):
                continue
            if green in occupied or orange in occupied:
                continue
            if green in all_corners or orange in all_corners:
                continue
            candidates.append((green, orange))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful task input; Racket remains authority."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    band = _band(difficulty)
    _validate_overrides(overrides)

    residue = sample_index % LESSON_SCHEDULE_PERIOD
    default_h, default_w, default_corner, default_template, default_dr, default_dc = (
        _DEFAULTS[band][residue]
    )

    # A single pinned zero component must remain satisfiable.  All scheduled
    # defaults already have both components nonzero, but keep this explicit if
    # future curricula add an axis-aligned default.
    if overrides.get("vector_dr") == 0 and "vector_dc" not in overrides and default_dc == 0:
        default_dc = 1
    if overrides.get("vector_dc") == 0 and "vector_dr" not in overrides and default_dr == 0:
        default_dr = 1

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", default_h, 10, 16)
    w = _draw_profile_int(ctx, overrides, "grid_w", default_w, 12, 18)
    corner = _draw_profile_choice(ctx, overrides, "corner", default_corner, _CORNERS)
    template = _draw_profile_choice(ctx, overrides, "template", default_template, _TEMPLATE_NAMES)
    dr = _draw_profile_int(ctx, overrides, "vector_dr", default_dr, -4, 4)
    dc = _draw_profile_int(ctx, overrides, "vector_dc", default_dc, -4, 4)
    if (dr, dc) == (0, 0):
        raise ValueError("incompatible realized axes vector_dr=0 and vector_dc=0")

    layout_rng = ctx.draw_rng("layout")
    placements = _placement_candidates(
        h=h,
        w=w,
        corner=corner,
        template=template,
        vector=(dr, dc),
    )
    if not placements:
        raise ValueError(
            f"no lawful template placement for {h}x{w}, {corner}, {template}, {(dr, dc)}"
        )
    _origin, red_cells, transformed_cells = layout_rng.choice(placements)

    control = _corner_cells(h, w)[corner]
    occupied = {control, *red_cells, *transformed_cells}
    marker_pairs = _marker_candidates(
        h=h,
        w=w,
        vector=(dr, dc),
        occupied=occupied,
    )
    if not marker_pairs:
        # Transformed cells do not exist in the input, so allowing a marker there
        # is a safe constructive fallback for unusually tight future profiles.
        marker_pairs = _marker_candidates(
            h=h,
            w=w,
            vector=(dr, dc),
            occupied={control, *red_cells},
        )
    if not marker_pairs:
        raise ValueError(
            f"no lawful marker pair for {h}x{w}, {corner}, {template}, {(dr, dc)}"
        )
    green, orange = layout_rng.choice(marker_pairs)

    grid = full_grid(h, w, 0)
    grid[control[0]][control[1]] = 1
    for r, c in red_cells:
        grid[r][c] = 2
    grid[green[0]][green[1]] = 3
    grid[orange[0]][orange[1]] = 6

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("constructed grid failed self_check: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for name, requested in overrides.items():
        if requested is not None and observed.get(name) != requested:
            raise ValueError(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return grid
