"""Generator for ARC task 18a3c532c9dc (original task 75b8110e).

Split an even rectangular input into four equal quadrants.  The output overlays
corresponding quadrant cells in the fixed priority TL, BR, BL, TR, so the last
nonzero value wins and TR has highest priority.

Every generated input contains explicit conflicts that demonstrate all four
priority levels.  Hidden randomness varies the four colors, conflict locations,
shape, and density; the only public exact controls are the observable dimensions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "18a3c532c9dc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c6cdd9647cb6"

SUMMARY = (
    "Even rectangular grid split into TL/TR/BL/BR quadrants. Corresponding "
    "cells are overlaid with priority TR > BL > BR > TL. Every generated "
    "input includes conflicts that visibly distinguish each adjacent priority "
    "decision, while colors, positions, dimensions, and extra occupancy vary."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "height and width are even values from 4 through 20",
    "background is 0",
    "each quadrant uses one distinct nonzero color",
    "each quadrant is nonempty",
    "generated inputs distinguish TR>BL, BL>BR, and BR>TL",
]

_EVEN_SIZES = (4, 6, 8, 10, 12, 14, 16, 18, 20)
_BAND_SIZES = {
    None: (6, 8, 10, 12, 14, 16),
    "easy": (4, 6, 8, 10),
    "medium": (6, 8, 10, 12, 14),
    "hard": (8, 10, 12, 14, 16, 18, 20),
}
_BAND_DENSITY = {None: 0.38, "easy": 0.24, "medium": 0.38, "hard": 0.52}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted even size; canonical 8 anchor",
        "valid": "4|6|8|10|12|14|16|18|20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted even size; canonical 8 anchor",
        "valid": "4|6|8|10|12|14|16|18|20",
    },
}


def _quadrant_values(grid, row, col):
    h, w = len(grid), len(grid[0])
    hh, hw = h // 2, w // 2
    return {
        "tl": grid[row][col],
        "tr": grid[row][col + hw],
        "bl": grid[row + hh][col],
        "br": grid[row + hh][col + hw],
    }


def _overlay_with_order(grid, order):
    """Diagnostic Python mirror; the pinned Racket program remains authority."""
    h, w = len(grid), len(grid[0])
    hh, hw = h // 2, w // 2
    output = full_grid(hh, hw, 0)
    for row in range(hh):
        for col in range(hw):
            values = _quadrant_values(grid, row, col)
            value = 0
            for quadrant in order:
                if values[quadrant] != 0:
                    value = values[quadrant]
            output[row][col] = value
    return output


def rule_mirror(grid):
    """Mirror the selected rule for tests and finite rival diagnostics."""
    return _overlay_with_order(grid, ("tl", "br", "bl", "tr"))


def _rival_bl_over_tr(grid):
    return _overlay_with_order(grid, ("tl", "br", "tr", "bl"))


def _rival_br_over_bl(grid):
    return _overlay_with_order(grid, ("tl", "bl", "br", "tr"))


def _rival_tl_over_br(grid):
    return _overlay_with_order(grid, ("br", "tl", "bl", "tr"))


SEMANTIC_RIVALS = {
    "bl_over_tr": _rival_bl_over_tr,
    "br_over_bl": _rival_br_over_bl,
    "tl_over_br": _rival_tl_over_br,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _distinguishes(rival_name):
    rival = SEMANTIC_RIVALS[rival_name]

    def witness(grid):
        return rule_mirror(grid) != rival(grid)

    witness.__name__ = f"distinguishes_{rival_name}"
    return witness


SEMANTIC_WITNESSES = {
    "tr_beats_bl": _distinguishes("bl_over_tr"),
    "bl_beats_br": _distinguishes("br_over_bl"),
    "br_beats_tl": _distinguishes("tl_over_br"),
}
WITNESS_RIVALS = {
    "tr_beats_bl": ["bl_over_tr"],
    "bl_beats_br": ["br_over_bl"],
    "br_beats_tl": ["tl_over_br"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a proof against every possible rule."""
    query_grid = query["input"] if isinstance(query, dict) else query
    expected = rule_mirror(query_grid)
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_grid) != expected:
                findings.append(
                    f"declared rival {name} fits all demonstrations and changes query"
                )
    return findings


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the structural domain shared by canonical and generated inputs."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    height = len(grid)
    errors = []
    if height not in _EVEN_SIZES or width not in _EVEN_SIZES:
        errors.append(
            f"height and width must be even values in {_EVEN_SIZES}, got {height}x{width}"
        )
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
    if errors:
        return errors

    hh, hw = height // 2, width // 2
    regions = (
        ("TL", 0, 0),
        ("TR", 0, hw),
        ("BL", hh, 0),
        ("BR", hh, hw),
    )
    colors = []
    for name, row0, col0 in regions:
        present = {
            grid[row0 + row][col0 + col]
            for row in range(hh)
            for col in range(hw)
            if grid[row0 + row][col0 + col] != 0
        }
        if len(present) != 1:
            errors.append(
                f"{name} quadrant must contain exactly one nonzero color, found {sorted(present)}"
            )
        else:
            colors.append(next(iter(present)))
    if len(colors) == 4 and len(set(colors)) != 4:
        errors.append(f"quadrant colors must be distinct, found {colors}")
    return errors


def strict_canonical_like(grid):
    """The lawful quadrant-overlay domain, not an exact silhouette match."""
    return self_check(grid)


def _validated_size(name, value):
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value not in _EVEN_SIZES:
        raise ValueError(f"{name} must be one of {_EVEN_SIZES}, got {value}")
    return value


def _choose_dimensions(ctx, seed, sample_index, difficulty, overrides):
    explicit_h = _validated_size("grid_h", overrides.get("grid_h"))
    explicit_w = _validated_size("grid_w", overrides.get("grid_w"))
    if explicit_h is None and explicit_w is None:
        # A high-rate keyed anchor keeps the real 8x8x5 canonical profile in
        # every difficulty band while still leaving ample rectangular variety.
        anchor = ctx.draw_choice("canonical_profile", (True, True, True, False))
        if anchor:
            # Exact public axes must retain keyed provenance even when the
            # canonical-profile branch fixes their values.
            return (
                ctx.draw_choice("grid_h", (8,)),
                ctx.draw_choice("grid_w", (8,)),
            )
    options = _BAND_SIZES[difficulty]
    height = explicit_h if explicit_h is not None else ctx.draw_choice("grid_h", options)
    width = explicit_w if explicit_w is not None else ctx.draw_choice("grid_w", options)
    return height, width


def _place(grid, hh, hw, colors, row, col, occupied):
    for quadrant in occupied:
        row0 = hh if quadrant in ("bl", "br") else 0
        col0 = hw if quadrant in ("tr", "br") else 0
        grid[row0 + row][col0 + col] = colors[quadrant]


def _generate_grid(ctx, height, width, difficulty):
    rng = ctx.draw_rng("scene")
    hh, hw = height // 2, width // 2
    palette = rng.sample(range(1, 10), 4)
    colors = dict(zip(("tl", "tr", "bl", "br"), palette))
    grid = full_grid(height, width, 0)

    coordinates = [(row, col) for row in range(hh) for col in range(hw)]
    rng.shuffle(coordinates)
    reserved = coordinates[:4]
    roles = (
        ("tl", "tr", "bl", "br"),  # TR wins.
        ("tl", "bl", "br"),        # BL wins when TR is absent.
        ("tl", "br"),              # BR wins when TR and BL are absent.
        ("tl",),                    # TL survives when alone.
    )
    for (row, col), occupied in zip(reserved, roles):
        _place(grid, hh, hw, colors, row, col, occupied)

    density = _BAND_DENSITY[difficulty]
    for row, col in coordinates[4:]:
        for quadrant in ("tl", "tr", "bl", "br"):
            if rng.random() < density:
                _place(grid, hh, hw, colors, row, col, (quadrant,))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_SIZES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    for name in AXES:
        _validated_size(name, overrides.get(name))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width = _choose_dimensions(ctx, seed, sample_index, difficulty, overrides)
    grid = _generate_grid(ctx, height, width, difficulty)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    return grid
