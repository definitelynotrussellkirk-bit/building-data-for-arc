"""Generator for the Three-Panel Majority Merge ARC task.

The input contains three aligned 4-column panels separated by full-height gray
(color 5) dividers.  At each panel-local position, the output is cyan (8) iff
at least two panels are occupied there.

Every generated instance deliberately contains all sides of the decision
boundary: one-panel negatives, two-panel positives, and three-panel positives.
That prevents union, intersection, and single-panel-copy shortcuts from fitting
the generated lessons.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8f10b83435aa"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "bd5f126e874d"

PANEL_W = 4
DIVIDER_COLOR = 5
FOREGROUND_COLOR = 2
OUTPUT_COLOR = 8
PANEL_BASES = (0, 5, 10)

SUMMARY = (
    "Three aligned width-4 panels are separated by two full-height color-5 "
    "columns.  A panel-local position becomes color 8 in the output exactly "
    "when at least two of the three panels are occupied there.  Generated "
    "instances include observable one-panel negatives, two-panel positives, "
    "and three-panel positives so common union/intersection/copy shortcuts "
    "are contradicted in every example."
)

INVARIANTS = [
    "background is color 0",
    "input width is 14 with full-height color-5 dividers at columns 4 and 9",
    "three panel-local grids have equal height and width 4",
    "color 8 marks exactly positions occupied in at least two panels",
    "every generated input contains singleton, pair-only, and triple evidence",
]

AXES = {
    "panel_h": {
        "type": "int",
        "default": "rng 6..7",
        "valid": "6..7",
    },
    "n_majority": {
        "type": "int",
        "default": "rng 6..10",
        "valid": "6..10",
    },
    "n_singletons": {
        "type": "int",
        "default": "rng 3..9",
        "valid": "3..9",
    },
    "n_triples": {
        "type": "int",
        "default": "rng 1..3",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")


def _draw_band_choice(ctx, label: str, values, difficulty) -> int:
    options = tuple(values)
    offsets = {"easy": 0, "medium": 1, "hard": 2}
    offset = offsets.get(difficulty, 0) % len(options)
    rotated = options[offset:] + options[:offset]
    return int(ctx.draw_choice(label, rotated))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one exact, deterministic majority-merge input grid."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Every band sees the full declared domain, but rotating each option list
    # makes difficulty enter the keyed draw without invalidating exact
    # overrides or collapsing an axis to a band-specific subrange.
    panel_h = _draw_band_choice(ctx, "panel_h", range(6, 8), difficulty)
    n_majority = _draw_band_choice(ctx, "n_majority", range(6, 11), difficulty)
    n_singletons = _draw_band_choice(ctx, "n_singletons", range(3, 10), difficulty)
    n_triples = _draw_band_choice(ctx, "n_triples", range(1, 4), difficulty)

    capacity = panel_h * PANEL_W
    if n_majority + n_singletons > capacity:
        # The advertised domains make this unreachable, but keep the
        # relationship explicit if future edits expand an axis.
        raise ValueError(
            "n_majority + n_singletons exceeds the panel-local capacity "
            f"({n_majority} + {n_singletons} > {capacity})"
        )
    n_pairs = n_majority - n_triples
    if n_pairs < 3:
        raise ValueError("at least three pair-only positions are required")

    grid = full_grid(panel_h, 3 * PANEL_W + 2, 0)
    for row in range(panel_h):
        grid[row][4] = DIVIDER_COLOR
        grid[row][9] = DIVIDER_COLOR

    rng = ctx.draw_rng("layout")
    local_positions = [(row, col) for row in range(panel_h) for col in range(PANEL_W)]
    chosen = rng.sample(local_positions, n_majority + n_singletons)
    rng.shuffle(chosen)
    majority_positions = chosen[:n_majority]
    singleton_positions = chosen[n_majority:]

    # Triple positives are separated from pair-only positives so both >=2
    # branches are visibly supported.
    rng.shuffle(majority_positions)
    triple_positions = majority_positions[:n_triples]
    pair_positions = majority_positions[n_triples:]

    for row, col in triple_positions:
        _paint_panels(grid, row, col, (0, 1, 2))

    # Start with every pair type, then distribute remaining pair positions.
    pair_assignments = [(0, 1), (0, 2), (1, 2)]
    rng.shuffle(pair_assignments)
    while len(pair_assignments) < len(pair_positions):
        pair_assignments.append(rng.choice(((0, 1), (0, 2), (1, 2))))
    rng.shuffle(pair_assignments)
    for (row, col), panels in zip(pair_positions, pair_assignments, strict=True):
        _paint_panels(grid, row, col, panels)

    # Put at least one false-positive temptation in each individual panel.
    singleton_assignments = [0, 1, 2]
    while len(singleton_assignments) < len(singleton_positions):
        singleton_assignments.append(rng.randrange(3))
    rng.shuffle(singleton_assignments)
    for (row, col), panel in zip(singleton_positions, singleton_assignments, strict=True):
        _paint_panels(grid, row, col, (panel,))

    return grid


def _paint_panels(grid: list[list[int]], row: int, col: int, panels) -> None:
    for panel in panels:
        grid[row][PANEL_BASES[panel] + col] = FOREGROUND_COLOR


def _rectangular_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _panels(grid) -> list[list[list[int]]]:
    shape = _rectangular_shape(grid)
    if shape is None or shape[1] != 14:
        raise ValueError("expected a nonempty rectangular 14-column input")
    height = shape[0]
    return [
        [[grid[row][base + col] for col in range(PANEL_W)] for row in range(height)]
        for base in PANEL_BASES
    ]


def _occupancy_counts(grid) -> list[list[int]]:
    panels = _panels(grid)
    height = len(grid)
    return [
        [
            sum(panel[row][col] != 0 for panel in panels)
            for col in range(PANEL_W)
        ]
        for row in range(height)
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket majority rule."""
    return [
        [OUTPUT_COLOR if count >= 2 else 0 for count in row]
        for row in _occupancy_counts(grid)
    ]


_expected_output = rule_mirror


def _union_any(grid) -> list[list[int]]:
    return [
        [OUTPUT_COLOR if count >= 1 else 0 for count in row]
        for row in _occupancy_counts(grid)
    ]


def _all_three_only(grid) -> list[list[int]]:
    return [
        [OUTPUT_COLOR if count == 3 else 0 for count in row]
        for row in _occupancy_counts(grid)
    ]


def _copy_panel(grid, panel_index: int) -> list[list[int]]:
    panel = _panels(grid)[panel_index]
    return [
        [OUTPUT_COLOR if value != 0 else 0 for value in row]
        for row in panel
    ]


def _copy_panel_0(grid):
    return _copy_panel(grid, 0)


def _copy_panel_1(grid):
    return _copy_panel(grid, 1)


def _copy_panel_2(grid):
    return _copy_panel(grid, 2)


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover every exact public axis from the returned pixels."""
    shape = _rectangular_shape(grid)
    if shape is None or shape[1] != 14:
        return {name: None for name in AXES}
    try:
        counts = _occupancy_counts(grid)
    except (TypeError, ValueError, IndexError):
        return {name: None for name in AXES}
    flat = [value for row in counts for value in row]
    return {
        "panel_h": shape[0],
        "n_majority": sum(value >= 2 for value in flat),
        "n_singletons": sum(value == 1 for value in flat),
        "n_triples": sum(value == 3 for value in flat),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical layout without rejecting public canonical counts."""
    del difficulty, meta
    shape = _rectangular_shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors: list[str] = []
    if height not in (6, 7):
        errors.append(f"panel_h={height} outside canonical heights {{6,7}}")
    if width != 14:
        return errors + [f"expected width 14, found {width}"]

    illegal = [
        value
        for row in grid
        for value in row
        if type(value) is not int or value not in {0, FOREGROUND_COLOR, DIVIDER_COLOR}
    ]
    if illegal:
        errors.append("cells must use only integer colors {0,2,5}")

    for col in (4, 9):
        if any(grid[row][col] != DIVIDER_COLOR for row in range(height)):
            errors.append(f"column {col} is not a full-height color-5 divider")
    stray_dividers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if col not in (4, 9) and grid[row][col] == DIVIDER_COLOR
    ]
    if stray_dividers:
        errors.append("color 5 appears outside divider columns")

    if errors:
        return errors
    counts = [value for row in _occupancy_counts(grid) for value in row]
    if not any(value >= 2 for value in counts):
        errors.append("input contains no majority-positive position")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical structure plus evidence on both threshold sides."""
    errors = self_check(grid)
    if errors:
        return errors
    counts = [value for row in _occupancy_counts(grid) for value in row]
    if not any(value == 1 for value in counts):
        errors.append("missing one-panel negative evidence")
    if not any(value == 2 for value in counts):
        errors.append("missing pair-only positive evidence")
    return errors


def _rival_disagrees(name: str, grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable] = {
    "union_any": _union_any,
    "all_three_only": _all_three_only,
    "copy_panel_0": _copy_panel_0,
    "copy_panel_1": _copy_panel_1,
    "copy_panel_2": _copy_panel_2,
}
SEMANTIC_WITNESSES = {
    "one_panel_negatives_refute_union": lambda grid: _rival_disagrees("union_any", grid),
    "pair_only_positives_refute_intersection": lambda grid: _rival_disagrees("all_three_only", grid),
    "panel_0_is_not_the_answer": lambda grid: _rival_disagrees("copy_panel_0", grid),
    "panel_1_is_not_the_answer": lambda grid: _rival_disagrees("copy_panel_1", grid),
    "panel_2_is_not_the_answer": lambda grid: _rival_disagrees("copy_panel_2", grid),
}
WITNESS_RIVALS = {
    "one_panel_negatives_refute_union": ["union_any"],
    "pair_only_positives_refute_intersection": ["all_three_only"],
    "panel_0_is_not_the_answer": ["copy_panel_0"],
    "panel_1_is_not_the_answer": ["copy_panel_1"],
    "panel_2_is_not_the_answer": ["copy_panel_2"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of these rivals fits all labeled canonical pairs, so there is no
# canonical-only shortcut claim to make.
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that fit every demo but would change the query."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
