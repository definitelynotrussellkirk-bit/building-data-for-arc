"""Generator for arc_additional_puzzle_bank_volume10:E66.

The selected Racket authority caps each maximal horizontal yellow (4) run of
exactly three cells with magenta (6) in any immediately adjacent background
cells.  Generated inputs deliberately include two negative controls:

* yellow runs whose length is not three, and
* same-colour non-yellow runs whose length is exactly three.

The canonical inputs use both three- and four-colour palettes.  Four-colour
draws therefore add one isolated auxiliary-colour cell far from every bar;
it is irrelevant to the transformation but keeps canonical palette profiles
reachable in every difficulty band.

Together they distinguish exact length and yellow-specificity without changing
the authoritative rule.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2da4094bc0e1"
TASK_ID = GENERATOR_ID
RULE_HASH = "5f2c21d44ce7"
VERSION = "3.0.0"
SUMMARY = (
    "Cap maximal horizontal yellow length-3 runs with magenta; every generated "
    "input also contains uncapped wrong-length yellow runs and uncapped exact-3 "
    "runs in another colour, with canonical three/four-colour palette support."
)

INVARIANTS = [
    "background is 0; target yellow is 4 and cap colour is 6",
    "every target is a maximal horizontal yellow run of exactly length 3",
    "target cap cells are in bounds and initially background",
    "at least one wrong-length yellow run has empty in-bounds neighbours",
    "at least one same-colour non-yellow length-3 run has empty in-bounds neighbours",
    "all advertised counts are recoverable from returned pixels",
    "palette_size is exactly 3 or 4 and is observable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical sizes 10|11 favored", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "canonical widths 13|14 favored", "valid": "7..16"},
    "n_bars": {"type": "int", "default": "difficulty-weighted 1..3", "valid": "1..3"},
    "n_wrong_bars": {"type": "int", "default": "difficulty-weighted 1..3", "valid": "1..3"},
    "n_color_decoys": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "decoy_color": {"type": "int", "default": "rng 5|7|9", "valid": "5|7|9"},
    "palette_size": {"type": "int", "default": "difficulty-weighted 3|4", "valid": "3|4"},
}

# The smallest grid has eight rows, while the largest requested bar population
# is 3 + 3 + 2 = 8.  Width seven fits a length-5 distractor plus two cap cells.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_INT_AXES = frozenset(AXES)
_DECOY_COLORS = (5, 7, 9)
_AUX_COLOR_BY_DECOY = {5: 7, 7: 9, 9: 5}


def _weighted_choice(ctx, name, values, favored):
    """Keep the complete override domain while biasing ordinary draws."""
    options = list(values) + list(favored) * 12
    return ctx.draw_choice(name, options)


def _difficulty_favorites(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (10, 10, 11),
            "grid_w": (13, 13, 14),
            "n_bars": (1, 2),
            "n_wrong_bars": (1, 2),
            "n_color_decoys": (1,),
            "palette_size": (3, 4),
        }
    if difficulty == "hard":
        return {
            # Hardness comes from more positive and negative bars, not from
            # abandoning the published scale.  Bias these two dimensions and
            # four-colour palettes so the pinned hard census retains exact
            # canonical-profile support.
            "grid_h": (10, 11, 11),
            "grid_w": (13, 14, 14),
            "n_bars": (3,),
            "n_wrong_bars": (3,),
            "n_color_decoys": (2,),
            "palette_size": (4, 4),
        }
    return {
        "grid_h": (10, 11, 11),
        "grid_w": (13, 14, 14),
        "n_bars": (2, 3),
        "n_wrong_bars": (2,),
        "n_color_decoys": (1, 2),
        "palette_size": (3, 4),
    }


def _place_aux_color(grid, color, rng):
    """Add one isolated cell without occupying or touching any bar cap cell."""
    width = len(grid[0])
    candidates = []
    for row_index, row in enumerate(grid):
        for col in range(width):
            if row[col] != 0:
                continue
            left_clear = col == 0 or row[col - 1] == 0
            right_clear = col == width - 1 or row[col + 1] == 0
            if left_clear and right_clear:
                candidates.append((row_index, col))
    if not candidates:  # defensive: declared dimensions/counts always leave one
        raise ValueError("no safe location for auxiliary palette colour")
    row, col = rng.choice(candidates)
    grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    favored = _difficulty_favorites(difficulty)
    height = _weighted_choice(ctx, "grid_h", range(8, 15), favored["grid_h"])
    width = _weighted_choice(ctx, "grid_w", range(7, 17), favored["grid_w"])
    n_bars = _weighted_choice(ctx, "n_bars", range(1, 4), favored["n_bars"])
    n_wrong = _weighted_choice(
        ctx, "n_wrong_bars", range(1, 4), favored["n_wrong_bars"]
    )
    n_color_decoys = _weighted_choice(
        ctx, "n_color_decoys", range(1, 3), favored["n_color_decoys"]
    )
    decoy_color = _weighted_choice(ctx, "decoy_color", _DECOY_COLORS, _DECOY_COLORS)
    palette_size = _weighted_choice(
        ctx, "palette_size", (3, 4), favored["palette_size"]
    )

    total_rows = n_bars + n_wrong + n_color_decoys
    if total_rows > height:  # defensive; the declared Cartesian product cannot hit this
        raise ValueError("requested bars do not fit distinct rows")

    grid = full_grid(height, width, 0)
    rows = ctx.draw_rng("bar_rows").sample(range(height), total_rows)
    target_rows = rows[:n_bars]
    wrong_rows = rows[n_bars : n_bars + n_wrong]
    decoy_rows = rows[n_bars + n_wrong :]

    target_rng = ctx.draw_rng("target_positions")
    for row in target_rows:
        start = target_rng.randint(1, width - 4)
        grid[row][start : start + 3] = [4, 4, 4]

    wrong_rng = ctx.draw_rng("wrong_length_positions")
    # The first distractor is always long, so the tempting "at least three"
    # rival is refuted in every generated input.  Additional distractors also
    # cover canonical-like short runs.
    wrong_lengths = [wrong_rng.choice((4, 5))]
    wrong_lengths.extend(wrong_rng.choice((1, 2, 4, 5)) for _ in range(n_wrong - 1))
    for row, length in zip(wrong_rows, wrong_lengths):
        start = wrong_rng.randint(1, width - length - 1)
        grid[row][start : start + length] = [4] * length

    decoy_rng = ctx.draw_rng("color_decoy_positions")
    for row in decoy_rows:
        start = decoy_rng.randint(1, width - 4)
        grid[row][start : start + 3] = [decoy_color] * 3

    if palette_size == 4:
        _place_aux_color(
            grid,
            _AUX_COLOR_BY_DECOY[decoy_color],
            ctx.draw_rng("aux_color_position"),
        )

    return grid


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9"]
    return []


def _horizontal_runs(grid):
    """Yield (color, row, start, length) for maximal non-background runs."""
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            color = row[col]
            start = col
            while col < len(row) and row[col] == color:
                col += 1
            if color != 0:
                yield color, row_index, start, col - start


def _has_empty_caps(grid, row, start, length):
    width = len(grid[0])
    return (
        start > 0
        and start + length < width
        and grid[row][start - 1] == 0
        and grid[row][start + length] == 0
    )


def _cap_matching_runs(grid, predicate):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    out = deepcopy(grid)
    width = len(grid[0])
    for color, row, start, length in _horizontal_runs(grid):
        if not predicate(color, length):
            continue
        if start > 0 and grid[row][start - 1] == 0:
            out[row][start - 1] = 6
        stop = start + length
        if stop < width and grid[row][stop] == 0:
            out[row][stop] = 6
    return out


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    return _cap_matching_runs(grid, lambda color, length: color == 4 and length == 3)


def _color_agnostic_exact3(grid):
    """Plausible shortcut: cap every same-colour exact length-3 run."""
    return _cap_matching_runs(grid, lambda _color, length: length == 3)


def _yellow_at_least3(grid):
    """Plausible wrong rule: treat three as a lower bound, not an exact length."""
    return _cap_matching_runs(grid, lambda color, length: color == 4 and length >= 3)


def observe_overrides(grid):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    runs = list(_horizontal_runs(grid))
    targets = [run for run in runs if run[0] == 4 and run[3] == 3]
    wrong = [run for run in runs if run[0] == 4 and run[3] != 3]
    color_decoys = [
        run for run in runs if run[0] in _DECOY_COLORS and run[3] == 3
    ]
    colors = {run[0] for run in color_decoys}
    if len(colors) != 1:
        raise ValueError("expected one shared decoy colour across exact-3 decoy runs")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_bars": len(targets),
        "n_wrong_bars": len(wrong),
        "n_color_decoys": len(color_decoys),
        "decoy_color": next(iter(colors)),
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors
    runs = list(_horizontal_runs(grid))
    targets = [run for run in runs if run[0] == 4 and run[3] == 3]
    wrong = [run for run in runs if run[0] == 4 and run[3] != 3]
    if not targets:
        errors.append("expected at least one exact length-3 yellow target bar")
    if not wrong:
        errors.append("expected at least one wrong-length yellow distractor")
    for _color, row, start, length in targets:
        if not _has_empty_caps(grid, row, start, length):
            errors.append("target yellow bar must have empty in-bounds cap cells")
    return errors


def strict_canonical_like(grid):
    """Accept lawful canonical/task inputs, not only this sampler's exact pixels."""
    return self_check(grid)


def _has_color_specificity_witness(grid):
    if _grid_errors(grid):
        return False
    return any(
        color != 4
        and color != 6
        and length == 3
        and _has_empty_caps(grid, row, start, length)
        for color, row, start, length in _horizontal_runs(grid)
    )


def _has_exact_length_witness(grid):
    if _grid_errors(grid):
        return False
    return any(
        color == 4
        and length > 3
        and _has_empty_caps(grid, row, start, length)
        for color, row, start, length in _horizontal_runs(grid)
    )


def lesson_identifiable(demos, query):
    """Require every named lesson competitor to be refuted by a demonstration."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name} still fits every demonstration")
    return reasons


SEMANTIC_WITNESSES = {
    "color_specificity": _has_color_specificity_witness,
    "exact_length": _has_exact_length_witness,
}
SEMANTIC_RIVALS = {
    "color_agnostic_exact3": _color_agnostic_exact3,
    "yellow_at_least3": _yellow_at_least3,
}
WITNESS_RIVALS = {
    "color_specificity": ["color_agnostic_exact3"],
    "exact_length": ["yellow_at_least3"],
}
CANONICAL_SHORTCUTS = {"color_agnostic_exact3": _color_agnostic_exact3}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
