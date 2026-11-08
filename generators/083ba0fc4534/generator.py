"""Generator for ARC task 083ba0fc4534 — Three-Panel Consensus.

Two full-height gray (5) columns separate three aligned panels.  At each
panel-local position, copy a nonzero color to the output iff that same color
appears in at least two panels.  Otherwise output background (0).

Generated lessons are sparse and canonical-profiled.  Every input contains all
four positive agreement branches plus at least one two-color disagreement.
The disagreement is deliberate: the labeled canonical examples alone also fit
the wrong shortcut "when at least two panels are occupied, copy the first
nonzero color".  A disagreement cell is the smallest counterexample to that
shortcut.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "083ba0fc4534"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "076637306d69"

DIVIDER_COLOR = 5
BACKGROUND_COLOR = 0
_ALLOWED_FOREGROUND = (1, 2, 3, 4, 6, 7, 8, 9)

SUMMARY = (
    "Three equal sparse panels are separated by two full-height gray columns. "
    "At each aligned position, a nonzero color survives exactly when at least "
    "two panels agree on that color; otherwise the output is 0. Every generated "
    "input covers left+middle, left+right, middle+right, all-three agreement, "
    "and a distinct-color disagreement that refutes the canonical-fitting "
    "occupancy shortcut."
)

INVARIANTS = [
    "two full-height color-5 columns split the input into three equal panels",
    "panel height is 4 or 5 and panel width is 4 or 5",
    "exactly 2 or 3 non-divider foreground colors are used",
    "every generated input contains ab, ax, bx, and abc agreement evidence",
    "every generated input contains 1..3 distinct-color disagreement cells",
    "all nonempty panel-local positions are sparse: 5..7 per input",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng 4..5",
        "valid": "4..5",
    },
    "panel_w": {
        "type": "int",
        "default": "rng 4..5",
        "valid": "4..5",
    },
    "palette_size": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
        "doc": "number of nonzero, non-divider colors used in the panels",
    },
    "n_conflicts": {
        "type": "int",
        "default": "rng 1..3",
        "valid": "1..3",
        "doc": "aligned cells with two occupied panels holding different colors",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

_AXIS_VALUES = {
    "grid_h": (4, 5),
    "panel_w": (4, 5),
    "palette_size": (2, 3),
    "n_conflicts": (1, 2, 3),
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    """Reject misspelled, retired, coerced, or out-of-domain public axes."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if value not in _AXIS_VALUES[name]:
            raise ValueError(
                f"override {name!r}={value!r} outside {list(_AXIS_VALUES[name])}"
            )


def _draw_band_choice(ctx, label: str, values, difficulty) -> int:
    """Draw from the complete axis domain while making bands observably differ."""
    options = tuple(values)
    offsets = {"easy": 0, "medium": 1, "hard": 2}
    offset = offsets.get(difficulty, 0) % len(options)
    rotated = options[offset:] + options[:offset]
    return int(ctx.draw_choice(label, rotated))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, sparse consensus lesson."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    grid_h = _draw_band_choice(ctx, "grid_h", _AXIS_VALUES["grid_h"], difficulty)
    panel_w = _draw_band_choice(ctx, "panel_w", _AXIS_VALUES["panel_w"], difficulty)
    palette_size = _draw_band_choice(
        ctx, "palette_size", _AXIS_VALUES["palette_size"], difficulty
    )
    n_conflicts = _draw_band_choice(
        ctx, "n_conflicts", _AXIS_VALUES["n_conflicts"], difficulty
    )

    palette_rng = ctx.draw_rng("palette")
    colors = tuple(palette_rng.sample(_ALLOWED_FOREGROUND, palette_size))

    # Cycle the required branches through the selected palette.  With three
    # colors, the first three branches guarantee that every declared color is
    # observable; with two colors, both are guaranteed observable.
    ab_color = colors[0]
    ax_color = colors[1 % palette_size]
    bx_color = colors[2 % palette_size]
    abc_color = colors[3 % palette_size]
    triples: list[tuple[int, int, int]] = [
        (ab_color, ab_color, 0),
        (ax_color, 0, ax_color),
        (0, bx_color, bx_color),
        (abc_color, abc_color, abc_color),
    ]

    conflict_rng = ctx.draw_rng("conflicts")
    panel_pairs = [(0, 1), (0, 2), (1, 2)]
    conflict_rng.shuffle(panel_pairs)
    for index in range(n_conflicts):
        first = colors[index % palette_size]
        second = colors[(index + 1) % palette_size]
        panels = panel_pairs[index % len(panel_pairs)]
        values = [0, 0, 0]
        if conflict_rng.randrange(2):
            first, second = second, first
        values[panels[0]] = first
        values[panels[1]] = second
        triples.append(tuple(values))

    width = 3 * panel_w + 2
    divider_1 = panel_w
    divider_2 = 2 * panel_w + 1
    grid = full_grid(grid_h, width, BACKGROUND_COLOR)
    for row in range(grid_h):
        grid[row][divider_1] = DIVIDER_COLOR
        grid[row][divider_2] = DIVIDER_COLOR

    layout_rng = ctx.draw_rng("layout")
    positions = [
        (row, col) for row in range(grid_h) for col in range(panel_w)
    ]
    chosen = layout_rng.sample(positions, len(triples))
    layout_rng.shuffle(triples)
    for (row, col), (left, middle, right) in zip(chosen, triples, strict=True):
        grid[row][col] = left
        grid[row][divider_1 + 1 + col] = middle
        grid[row][divider_2 + 1 + col] = right

    return grid


def _rectangular_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None
    width = len(first)
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _layout(grid) -> tuple[int, int, int, int] | None:
    shape = _rectangular_shape(grid)
    if shape is None:
        return None
    height, width = shape
    if (width - 2) % 3:
        return None
    panel_w = (width - 2) // 3
    if panel_w <= 0:
        return None
    return height, width, panel_w, 2 * panel_w + 1


def _panels(grid) -> list[list[list[int]]]:
    layout = _layout(grid)
    if layout is None:
        raise ValueError("expected a nonempty rectangular three-panel input")
    height, _width, panel_w, divider_2 = layout
    bases = (0, panel_w + 1, divider_2 + 1)
    return [
        [
            [grid[row][base + col] for col in range(panel_w)]
            for row in range(height)
        ]
        for base in bases
    ]


def _consensus_value(a: int, b: int, x: int) -> int:
    if a != 0 and (a == b or a == x):
        return a
    if b != 0 and b == x:
        return b
    return 0


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    left, middle, right = _panels(grid)
    return [
        [
            _consensus_value(left[row][col], middle[row][col], right[row][col])
            for col in range(len(left[0]))
        ]
        for row in range(len(left))
    ]


_expected_output = rule_mirror


def _cell_kind(a: int, b: int, x: int) -> str:
    nonzero = [value for value in (a, b, x) if value != 0]
    if a != 0 and a == b == x:
        return "abc"
    if a != 0 and a == b and x != a:
        return "ab"
    if a != 0 and a == x and b != a:
        return "ax"
    if b != 0 and b == x and a != b:
        return "bx"
    if not nonzero:
        return "empty"
    if len(nonzero) >= 2 and len(set(nonzero)) == len(nonzero):
        return "conflict"
    if len(nonzero) == 1:
        return "lone"
    return "other"


def _metrics(grid) -> dict[str, Any]:
    left, middle, right = _panels(grid)
    counts: dict[str, int] = {
        name: 0
        for name in ("abc", "ab", "ax", "bx", "conflict", "lone", "other", "empty")
    }
    consensus_colors: set[int] = set()
    for row in range(len(left)):
        for col in range(len(left[0])):
            values = (left[row][col], middle[row][col], right[row][col])
            kind = _cell_kind(*values)
            counts[kind] += 1
            consensus = _consensus_value(*values)
            if consensus:
                consensus_colors.add(consensus)
    return {"counts": counts, "consensus_colors": consensus_colors}


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover every exact public axis from returned pixels."""
    if self_check(grid):
        return {name: None for name in AXES}
    assert _layout(grid) is not None
    height, _width, panel_w, _divider_2 = _layout(grid)
    foreground = {
        value
        for row in grid
        for value in row
        if value not in (BACKGROUND_COLOR, DIVIDER_COLOR)
    }
    counts = _metrics(grid)["counts"]
    return {
        "grid_h": height,
        "panel_w": panel_w,
        "palette_size": len(foreground),
        "n_conflicts": counts["conflict"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical layout, palette, sparsity, and branch evidence."""
    del difficulty, meta
    layout = _layout(grid)
    if layout is None:
        return ["expected a nonempty rectangular three-panel grid"]
    height, width, panel_w, divider_2 = layout
    divider_1 = panel_w
    errors: list[str] = []

    if height not in _AXIS_VALUES["grid_h"]:
        errors.append(f"grid_h={height} outside {list(_AXIS_VALUES['grid_h'])}")
    if panel_w not in _AXIS_VALUES["panel_w"]:
        errors.append(f"panel_w={panel_w} outside {list(_AXIS_VALUES['panel_w'])}")
    if width != 3 * panel_w + 2:
        errors.append("width does not encode three equal panels plus two dividers")

    illegal = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if illegal:
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    for col in (divider_1, divider_2):
        if any(grid[row][col] != DIVIDER_COLOR for row in range(height)):
            errors.append(f"column {col} is not a full-height color-5 divider")
    if any(
        grid[row][col] == DIVIDER_COLOR
        for row in range(height)
        for col in range(width)
        if col not in (divider_1, divider_2)
    ):
        errors.append("color 5 appears outside the two divider columns")
    if errors:
        return errors

    foreground = {
        value
        for row in grid
        for value in row
        if value not in (BACKGROUND_COLOR, DIVIDER_COLOR)
    }
    if len(foreground) not in _AXIS_VALUES["palette_size"]:
        errors.append(
            f"foreground palette size {len(foreground)} outside "
            f"{list(_AXIS_VALUES['palette_size'])}"
        )

    metrics = _metrics(grid)
    counts = metrics["counts"]
    active = sum(value for name, value in counts.items() if name != "empty")
    consensus = sum(counts[name] for name in ("ab", "ax", "bx", "abc"))
    branch_types = sum(counts[name] > 0 for name in ("ab", "ax", "bx", "abc"))
    if not 4 <= active <= 7:
        errors.append(f"expected 4..7 nonempty local positions, found {active}")
    if consensus < 4:
        errors.append(f"expected at least four consensus positions, found {consensus}")
    if branch_types < 3:
        errors.append(
            f"expected at least three distinct consensus branches, found {branch_types}"
        )
    if counts["lone"]:
        errors.append("lone occupied cells are outside the canonical sparse manifold")
    if counts["other"]:
        errors.append("found an unsupported ambiguous cell pattern")
    if counts["conflict"] > 3:
        errors.append(f"expected at most three disagreement cells, found {counts['conflict']}")
    if foreground - metrics["consensus_colors"]:
        errors.append("every foreground color must occur in at least one consensus cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict semantic manifold is the validated canonical sparse form."""
    return self_check(grid)


def _map_cells(grid, transform: Callable[[int, int, int], int]) -> list[list[int]]:
    left, middle, right = _panels(grid)
    return [
        [
            transform(left[row][col], middle[row][col], right[row][col])
            for col in range(len(left[0]))
        ]
        for row in range(len(left))
    ]


def _first_nonzero_if_two_occupied(grid):
    def solve(a: int, b: int, x: int) -> int:
        occupied = [value for value in (a, b, x) if value != 0]
        return occupied[0] if len(occupied) >= 2 else 0

    return _map_cells(grid, solve)


def _left_middle_only(grid):
    return _map_cells(grid, lambda a, b, x: a if a != 0 and a == b else 0)


def _left_right_only(grid):
    return _map_cells(grid, lambda a, b, x: a if a != 0 and a == x else 0)


def _middle_right_only(grid):
    return _map_cells(grid, lambda a, b, x: b if b != 0 and b == x else 0)


def _unanimous_only(grid):
    return _map_cells(grid, lambda a, b, x: a if a != 0 and a == b == x else 0)


def _copy_left(grid):
    return _panels(grid)[0]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "first_nonzero_if_two_occupied": _first_nonzero_if_two_occupied,
    "left_middle_only": _left_middle_only,
    "left_right_only": _left_right_only,
    "middle_right_only": _middle_right_only,
    "unanimous_only": _unanimous_only,
    "copy_left": _copy_left,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "first_nonzero_if_two_occupied": _first_nonzero_if_two_occupied,
}


def _rival_disagrees(name: str, grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "conflict_refutes_occupancy_shortcut": lambda grid: _rival_disagrees(
        "first_nonzero_if_two_occupied", grid
    ),
    "ax_refutes_left_middle_only": lambda grid: _rival_disagrees(
        "left_middle_only", grid
    ),
    "ab_refutes_left_right_only": lambda grid: _rival_disagrees(
        "left_right_only", grid
    ),
    "ab_refutes_middle_right_only": lambda grid: _rival_disagrees(
        "middle_right_only", grid
    ),
    "pair_consensus_refutes_unanimous_only": lambda grid: _rival_disagrees(
        "unanimous_only", grid
    ),
    "bx_refutes_copy_left": lambda grid: _rival_disagrees("copy_left", grid),
}
WITNESS_RIVALS = {
    "conflict_refutes_occupancy_shortcut": ["first_nonzero_if_two_occupied"],
    "ax_refutes_left_middle_only": ["left_middle_only"],
    "ab_refutes_left_right_only": ["left_right_only"],
    "ab_refutes_middle_right_only": ["middle_right_only"],
    "pair_consensus_refutes_unanimous_only": ["unanimous_only"],
    "bx_refutes_copy_left": ["copy_left"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any competitor that fits every demo yet changes the query."""
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
