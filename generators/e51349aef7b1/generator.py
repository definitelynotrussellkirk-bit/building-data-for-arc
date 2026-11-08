"""Generator for H105 — cropped color-and-transform analogy.

Two full-height color-5 columns split the input into three equal square panels.
The rule crops each panel, finds the *first* code in
(identity, rotate-cw, rotate-180, transpose, flip-lr, flip-ud) that maps the
binary shape in A to the binary shape in B, then applies that code to cropped C
and recolors the result with B's foreground color.

The production schedule deliberately includes two ambiguous A->B profiles.  It
therefore teaches both crop-invariant matching and the authority's first-match
precedence rather than silently simplifying every input to a unique transform.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e51349aef7b1"
TASK_ID = GENERATOR_ID
RULE_HASH = "cb2d64bc2f44"
VERSION = "3.0.0"

SUMMARY = (
    "Three equal square panels are separated by full color-5 columns. Crop A, "
    "B and C to their nonzero bounding boxes; choose the first transform in "
    "identity/rot-cw/rot-180/transpose/flip-lr/flip-ud that maps binary(A) "
    "to binary(B); apply it to C and recolor every foreground cell with B's "
    "color. A four-profile schedule includes two ambiguous first-match cases "
    "and independently translates A and B, refuting uncropped-panel matching."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "background is 0 and the two full-height separator columns are color 5",
    "the separators create three equal square panels",
    "each panel has one nonzero foreground color and the three colors are distinct",
    "cropped binary A maps to cropped binary B under at least one authority transform",
    "the authority chooses the first matching transform code",
    "A and B placements are independent, so uncropped full-panel matching fails",
]

# These five triples are the exact palette sequence used by the canonical task.
_PALETTES = (
    (2, 7, 4),
    (3, 8, 6),
    (4, 2, 7),
    (6, 3, 8),
    (7, 4, 2),
)

AXES = {
    "panel_n": {
        "type": "int",
        "default": "weighted 5|6 in every band; canonical size 5 retained",
        "valid": "5..6",
    },
    "c_cells": {
        "type": "int",
        "default": "difficulty-weighted 4..8",
        "valid": "4..8",
    },
    "palette_id": {
        "type": "int",
        "default": "uniform 0..4 canonical palette cycle",
        "valid": "0..4",
    },
}

# Ambiguous canonical-style legends.  Their exact cropped match sets are [2,6]
# and [3,6], so the output must reveal the authority's first-match precedence.
_AMBIGUOUS_A = (
    (
        (1, 0, 0),
        (1, 0, 0),
        (1, 1, 1),
    ),
    (
        (1, 1, 1),
        (0, 1, 0),
        (0, 1, 0),
    ),
)

# Fully asymmetric under all six authority transforms.
_ASYMMETRIC_A = (
    (1, 1, 1),
    (1, 0, 0),
)

# Connected, fully asymmetric C templates with exactly 4..8 cells.  A keyed
# orientation draw supplies additional shape variety while preserving counts.
_C_TEMPLATES = {
    4: ((1, 1, 1), (1, 0, 0)),
    5: ((1, 1, 1, 1), (1, 0, 0, 0)),
    6: ((1, 1, 1, 1), (1, 1, 0, 0)),
    7: ((1, 1, 1, 1), (1, 1, 1, 0)),
    8: ((1, 1, 1, 1), (1, 1, 1, 0), (1, 0, 0, 0)),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _transform_grid(grid, code):
    """Apply one authority transform to a nonempty rectangular grid."""
    if code == 1:
        return _copy_grid(grid)
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in grid]
    if code == 6:
        return [list(row) for row in reversed(grid)]
    raise ValueError(f"unknown transform code {code}")


def _binary(grid):
    return [[1 if value else 0 for value in row] for row in grid]


def _crop(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not points:
        raise ValueError("cannot crop an empty panel")
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _matching_codes(a, b, *, crop=True):
    aa = _binary(_crop(a) if crop else a)
    bb = _binary(_crop(b) if crop else b)
    return [code for code in range(1, 7) if _transform_grid(aa, code) == bb]


def _split_panels(grid):
    h = len(grid)
    dividers = [c for c in range(len(grid[0])) if all(grid[r][c] == 5 for r in range(h))]
    if len(dividers) != 2:
        raise ValueError(f"expected two full-height color-5 dividers, found {len(dividers)}")
    d1, d2 = dividers
    return (
        [list(row[:d1]) for row in grid],
        [list(row[d1 + 1 : d2]) for row in grid],
        [list(row[d2 + 1 :]) for row in grid],
    )


def _foreground_color(panel):
    colors = {value for row in panel for value in row if value not in (0, 5)}
    if len(colors) != 1:
        raise ValueError(f"expected one panel foreground color, found {sorted(colors)}")
    return next(iter(colors))


def _fit_positions(n, shape):
    h, w = len(shape), len(shape[0])
    return [(r, c) for r in range(n - h + 1) for c in range(n - w + 1)]


def _panel_with_shape(n, shape, top, left, color=1):
    panel = full_grid(n, n, 0)
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if value:
                panel[top + r][left + c] = color
    return panel


def _paint_panel(grid, panel_index, n, shape, position, color):
    left = panel_index * (n + 1)
    top, local_left = position
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if value:
                grid[top + r][left + local_left + c] = color


def _draw_axis(ctx, name, options):
    """Weighted exact integer control with strict override typing."""
    value = ctx.overrides.get(name)
    if value is not None and type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    return ctx.draw_choice(name, options)


def _profile_shape(ctx, profile):
    if profile == 0:
        return _copy_grid(_AMBIGUOUS_A[0]), 2
    if profile == 1:
        return _copy_grid(_AMBIGUOUS_A[1]), 3

    orientation = ctx.draw_choice("a_orientation", (1, 2, 3, 4, 5, 6))
    shape = _transform_grid(_ASYMMETRIC_A, orientation)
    if profile == 2:
        code = ctx.draw_choice("profile2_transform", (1, 4))
    else:
        code = ctx.draw_choice("profile3_transform", (5, 6))
    return shape, code


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    panel_options = {
        "easy": (5, 5, 5, 6),
        "medium": (5, 5, 6, 6),
        "hard": (5, 6, 6, 6),
        None: (5, 5, 6, 6),
    }[difficulty]
    cell_options = {
        "easy": (4, 4, 5, 5, 6, 7, 8),
        "medium": (4, 5, 5, 6, 6, 7, 8),
        "hard": (4, 5, 6, 7, 7, 8, 8),
        None: (4, 5, 6, 7, 8),
    }[difficulty]
    n = _draw_axis(ctx, "panel_n", panel_options)
    c_cells = _draw_axis(ctx, "c_cells", cell_options)
    palette_id = _draw_axis(ctx, "palette_id", (0, 1, 2, 3, 4))

    profile = sample_index % LESSON_SCHEDULE_PERIOD
    shape_a, code = _profile_shape(ctx, profile)
    shape_b = _transform_grid(shape_a, code)
    expected_matches = _matching_codes(shape_a, shape_b, crop=False)
    if profile == 0 and expected_matches != [2, 6]:
        raise RuntimeError(f"profile 0 drifted: {expected_matches}")
    if profile == 1 and expected_matches != [3, 6]:
        raise RuntimeError(f"profile 1 drifted: {expected_matches}")
    if profile >= 2 and expected_matches != [code]:
        raise RuntimeError(f"unique profile drifted: code={code}, matches={expected_matches}")

    c_orientation = ctx.draw_choice("c_orientation", (1, 2, 3, 4, 5, 6))
    shape_c = _transform_grid(_C_TEMPLATES[c_cells], c_orientation)

    positions_a = _fit_positions(n, shape_a)
    position_a = ctx.draw_rng("a_position").choice(positions_a)
    full_a = _panel_with_shape(n, shape_a, *position_a)

    # B is translated independently.  Reject only positions that accidentally
    # restore an uncropped full-panel transform; this is constructive for n=5,6.
    positions_b = []
    for candidate in _fit_positions(n, shape_b):
        full_b = _panel_with_shape(n, shape_b, *candidate)
        if not _matching_codes(full_a, full_b, crop=False):
            positions_b.append(candidate)
    if not positions_b:
        raise RuntimeError("no independent B placement refutes uncropped matching")
    position_b = ctx.draw_rng("b_position").choice(positions_b)
    position_c = ctx.draw_rng("c_position").choice(_fit_positions(n, shape_c))

    color_a, color_b, color_c = _PALETTES[palette_id]
    grid = full_grid(n, 3 * n + 2, 0)
    for row in range(n):
        grid[row][n] = 5
        grid[row][2 * n + 1] = 5
    _paint_panel(grid, 0, n, shape_a, position_a, color_a)
    _paint_panel(grid, 1, n, shape_b, position_b, color_b)
    _paint_panel(grid, 2, n, shape_c, position_c, color_c)
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (booleans are not colors)"]

    h = len(grid)
    errors = []
    dividers = [c for c in range(width) if all(grid[r][c] == 5 for r in range(h))]
    if len(dividers) != 2:
        return [f"expected exactly two full-height color-5 dividers, found {len(dividers)}"]
    d1, d2 = dividers
    if d1 != h or d2 != 2 * h + 1 or width != 3 * h + 2:
        errors.append("dividers must create three equal square panels")
    if any(value == 5 and c not in dividers for row in grid for c, value in enumerate(row)):
        errors.append("color 5 may appear only in the two divider columns")
    if errors:
        return errors

    try:
        a, b, c = _split_panels(grid)
        colors = (_foreground_color(a), _foreground_color(b), _foreground_color(c))
        if len(set(colors)) != 3:
            errors.append("A, B and C foreground colors must be distinct")
        matches = _matching_codes(a, b)
        if not matches:
            errors.append("cropped binary A does not map to cropped binary B under any authority transform")
        _crop(c)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def strict_canonical_like(grid):
    """Lawful inputs for the selected authority; generated lessons are stricter."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    a, b, c = _split_panels(grid)
    palette = (_foreground_color(a), _foreground_color(b), _foreground_color(c))
    try:
        palette_id = _PALETTES.index(palette)
    except ValueError as exc:
        raise ValueError(f"palette {palette} is outside the exact generated palette cycle") from exc
    return {
        "panel_n": len(grid),
        "c_cells": sum(value != 0 for row in c for value in row),
        "palette_id": palette_id,
    }


def _output_for_code(grid, code):
    _, b, c = _split_panels(grid)
    color_b = _foreground_color(b)
    transformed = _transform_grid(_crop(c), code)
    return [[color_b if value else 0 for value in row] for row in transformed]


def rule_mirror(grid):
    a, b, _ = _split_panels(grid)
    matches = _matching_codes(a, b)
    return _output_for_code(grid, matches[0] if matches else 1)


def _uncropped_full_panels(grid):
    a, b, _ = _split_panels(grid)
    matches = _matching_codes(a, b, crop=False)
    return _output_for_code(grid, matches[0] if matches else 1)


def _last_matching_transform(grid):
    a, b, _ = _split_panels(grid)
    matches = _matching_codes(a, b)
    return _output_for_code(grid, matches[-1] if matches else 1)


def _cropped_alignment_witness(grid):
    return _uncropped_full_panels(grid) != rule_mirror(grid)


def _first_match_witness(grid):
    return _last_matching_transform(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "cropped_alignment": _cropped_alignment_witness,
    "first_match_precedence": _first_match_witness,
}
SEMANTIC_RIVALS = {
    "uncropped_full_panels": _uncropped_full_panels,
    "last_matching_transform": _last_matching_transform,
}
WITNESS_RIVALS = {
    "cropped_alignment": ["uncropped_full_panels"],
    "first_match_precedence": ["last_matching_transform"],
}
CANONICAL_SHORTCUTS = {
    "uncropped_full_panels": _uncropped_full_panels,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demonstrations, query):
    """Require each declared rival to be contradicted by a visible demo."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demonstrations):
            reasons.append(f"{name} fits every demonstration")
    return reasons
