"""Semantic generator for ARC task 2534c7164e36.

Three 4x4 panels are separated by two full-height divider columns.  The output
overlays corresponding cells with left-to-right priority: Q1, then Q2, then Q3.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2534c7164e36"
VERSION = "3.0.1"
TASK_ID = "2534c7164e36"
RULE_HASH = "3d9402d2c7a5"
SUMMARY = (
    "Overlay three 4x4 panels cell by cell. The first nonzero value in "
    "left-to-right priority Q1 > Q2 > Q3 becomes the corresponding output."
)
INVARIANTS = [
    "input is exactly 4x14 and output is exactly 4x4",
    "columns 4 and 9 are identical full-height nonzero dividers",
    "each panel is nonempty and uses a distinct nonzero color",
    "the divider color differs from all three panel colors",
    "linked scenes preserve one complete published triple of panel masks",
    "generalized scenes witness every priority result and a true overlap",
]
EXAMPLES_NEEDED = 6
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized (3:7)",
        "valid": "linked|generalized",
        "doc": (
            "linked preserves a complete published triple of panel masks up "
            "to a shared square symmetry; generalized recombines all eight "
            "per-cell occupancy states"
        ),
    },
}

BACKGROUND = 0
HEIGHT = 4
WIDTH = 14
PANEL_OFFSETS = (0, 5, 10)
DIVIDER_COLUMNS = (4, 9)
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# One 16-bit occupancy mask per panel, in row-major bit order.  These are the
# six unique published inputs (five training plus one held-out), kept as whole
# linked triples rather than independently recombined marginals.
_PUBLIC_MASK_TRIPLES = (
    (60856, 9816, 64256),
    (3391, 18485, 23064),
    (55975, 31819, 35114),
    (28405, 18048, 43832),
    (61738, 20675, 46880),
    (24756, 56949, 7027),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _mask_positions(mask):
    return {
        (index // 4, index % 4)
        for index in range(16)
        if mask & (1 << index)
    }


def _positions_mask(positions):
    return sum(1 << (row * 4 + col) for row, col in positions)


def _transform_position(position, symmetry):
    row, col = position
    if symmetry >= 4:
        col = 3 - col
        symmetry -= 4
    for _ in range(symmetry):
        row, col = col, 3 - row
    return row, col


def _transform_mask(mask, symmetry):
    return _positions_mask(
        _transform_position(position, symmetry)
        for position in _mask_positions(mask)
    )


_LINKED_MASK_TRIPLES = frozenset(
    tuple(_transform_mask(mask, symmetry) for mask in triple)
    for triple in _PUBLIC_MASK_TRIPLES
    for symmetry in range(8)
)


def _extract_structure(grid):
    if (
        not isinstance(grid, (list, tuple))
        or len(grid) != HEIGHT
        or not all(isinstance(row, (list, tuple)) and len(row) == WIDTH for row in grid)
    ):
        return None
    divider_values = {
        grid[row][col]
        for row in range(HEIGHT)
        for col in DIVIDER_COLUMNS
    }
    if len(divider_values) != 1 or next(iter(divider_values)) == BACKGROUND:
        return None
    divider_color = next(iter(divider_values))
    panel_colors = []
    masks = []
    for offset in PANEL_OFFSETS:
        values = {
            grid[row][offset + col]
            for row in range(HEIGHT)
            for col in range(4)
            if grid[row][offset + col] != BACKGROUND
        }
        if len(values) != 1:
            return None
        panel_colors.append(next(iter(values)))
        masks.append(
            _positions_mask(
                (row, col)
                for row in range(HEIGHT)
                for col in range(4)
                if grid[row][offset + col] != BACKGROUND
            )
        )
    if len(set(panel_colors)) != 3 or divider_color in panel_colors:
        return None
    return {
        "divider_color": divider_color,
        "panel_colors": tuple(panel_colors),
        "masks": tuple(masks),
    }


def canonical_profile_signature(grid):
    structure = _extract_structure(grid)
    if structure is None:
        return "invalid"
    return (
        "linked"
        if structure["masks"] in _LINKED_MASK_TRIPLES
        else "generalized"
    )


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _priority_output(grid):
    return [
        [
            next(
                (
                    grid[row][col + offset]
                    for offset in PANEL_OFFSETS
                    if grid[row][col + offset] != BACKGROUND
                ),
                BACKGROUND,
            )
            for col in range(4)
        ]
        for row in range(HEIGHT)
    ]


def _occupancy_states(masks):
    return tuple(
        (
            bool(masks[0] & (1 << index)),
            bool(masks[1] & (1 << index)),
            bool(masks[2] & (1 << index)),
        )
        for index in range(16)
    )


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty 4x14 matrix"], "facts": None}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(grid) != HEIGHT or widths != {WIDTH}:
        return {
            "errors": [
                f"grid must be exactly {HEIGHT}x{WIDTH}, got "
                f"{len(grid)}x{sorted(widths) if widths else []}"
            ],
            "facts": None,
        }
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")

    structure = _extract_structure(grid)
    if structure is None:
        errors.append(
            "expected two equal nonzero dividers and three nonempty, "
            "single-color panels with four distinct role colors"
        )
        return {"errors": errors, "facts": None}

    states = _occupancy_states(structure["masks"])
    family = (
        "linked"
        if structure["masks"] in _LINKED_MASK_TRIPLES
        else "generalized"
    )
    output = _priority_output(grid)
    output_values = Counter(value for row in output for value in row)
    if family == "generalized":
        q1_color, q2_color, q3_color = structure["panel_colors"]
        required_outputs = {BACKGROUND, q1_color, q2_color, q3_color}
        if not required_outputs.issubset(output_values):
            errors.append(
                "generalized scenes must expose blank, Q1, Q2, and Q3 output results"
            )
        if not any(q1 and (q2 or q3) for q1, q2, q3 in states):
            errors.append("generalized scenes must contain a Q1 priority overlap")
        if not any(not q1 and q2 and q3 for q1, q2, q3 in states):
            errors.append("generalized scenes must contain a Q2-over-Q3 overlap")
        if set(states) != {
            (False, False, False),
            (False, False, True),
            (False, True, False),
            (False, True, True),
            (True, False, False),
            (True, False, True),
            (True, True, False),
            (True, True, True),
        }:
            errors.append("generalized scenes must witness all eight occupancy states")

    facts = {
        **structure,
        "family": family,
        "states": states,
        "state_counts": Counter(states),
        "output": output,
        "output_values": output_values,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def _choose_colors(rng):
    # Canonical pairs already preserve the literal 2/4/9/1 palette. Generated
    # pairs rename the four semantic roles injectively, avoiding a tiny
    # duplicate-prone replay lane while leaving the priority law unchanged.
    divider_color, q1_color, q2_color, q3_color = rng.sample(range(1, 10), 4)
    return divider_color, (q1_color, q2_color, q3_color)


def _paint_scene(masks, divider_color, panel_colors):
    grid = full_grid(HEIGHT, WIDTH, BACKGROUND)
    for row in range(HEIGHT):
        for divider_col in DIVIDER_COLUMNS:
            grid[row][divider_col] = divider_color
    for mask, offset, color in zip(masks, PANEL_OFFSETS, panel_colors):
        for row, col in _mask_positions(mask):
            grid[row][offset + col] = color
    return grid


def _draw_linked_masks(rng):
    triple = rng.choice(_PUBLIC_MASK_TRIPLES)
    symmetry = rng.randrange(8)
    return tuple(_transform_mask(mask, symmetry) for mask in triple)


def _draw_generalized_masks(rng, band):
    # The first eight cells cover the complete truth table. The remaining
    # cells bias the curriculum without removing any priority obligation.
    state_codes = list(range(8))
    extras_by_band = {
        "easy": (0, 1, 2, 4, 4, 4, 7, 7),
        "medium": tuple(range(8)),
        "hard": (0, 3, 3, 5, 5, 6, 6, 7),
    }
    state_codes.extend(rng.choice(extras_by_band[band]) for _ in range(8))
    rng.shuffle(state_codes)
    masks = [0, 0, 0]
    for index, code in enumerate(state_codes):
        for panel_index, bit in enumerate((4, 2, 1)):
            if code & bit:
                masks[panel_index] |= 1 << index
    return tuple(masks)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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
    family = ctx.draw_choice(
        "scene_family",
        ("linked", "linked", "linked", "generalized", "generalized",
         "generalized", "generalized", "generalized", "generalized", "generalized"),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    if family == "linked":
        masks = _draw_linked_masks(rng)
    else:
        masks = _draw_generalized_masks(rng, band)
        if masks in _LINKED_MASK_TRIPLES:
            raise RuntimeError("generalized truth-table scene unexpectedly matched linked masks")
    divider_color, panel_colors = _choose_colors(rng)
    grid = _paint_scene(masks, divider_color, panel_colors)
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(analysis["errors"] or ["scene family mismatch"])
        )
    return grid
