"""Generator for ARC task 66f2d22f (content hash 784b131b3b93).

The input contains two equal-width panels placed side by side with no
separator.  The output marks an aligned position with color 5 exactly when
both panel cells are zero; all other aligned occupancy states map to zero.

Normal draws explicitly contain all four joint states ``00``, ``10``, ``01``,
and ``11``.  This makes the cellwise NOR relation visible while retaining the
canonical 4x14 curriculum profile in every difficulty band.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "784b131b3b93"
TASK_ID = GENERATOR_ID
RULE_HASH = "4b6cdc515f3f"
VERSION = "2.0.0"
SUMMARY = (
    "Two equal-width panels are placed horizontally. Output cell (r,c) is 5 "
    "exactly when both aligned panel cells are 0, otherwise 0. Normal draws "
    "contain all four aligned occupancy states, use distinct non-5 panel "
    "colors, and vary dimensions, colors, exact both-zero count, and layout."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is grid_h by 2*half_w with grid_h in 3..14 and half_w in 3..7",
    "left and right each use background 0 plus one distinct nonzero non-5 color",
    "normal draws contain aligned states 00, 10, 01, and 11",
    "color 5 is output-only",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
# The first three row-major non-00 cells encode the requested layout with a
# unique permutation of the three negative NOR states.  This makes the layout
# an exact, observable axis rather than hidden generation provenance.
PATTERN_SIGNATURES = {
    "random": ("10", "01", "11"),
    "blob": ("10", "11", "01"),
    "diagonal": ("01", "10", "11"),
    "border": ("01", "11", "10"),
    "stripes": ("11", "10", "01"),
    "checker": ("11", "01", "10"),
}
SIGNATURE_PATTERNS = {
    signature: pattern for pattern, signature in PATTERN_SIGNATURES.items()
}
HELPFUL_TEXTURES = PANEL_PATTERNS
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_halves")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 3..14 with a canonical 4-row anchor",
        "valid": "3..14",
    },
    "half_w": {
        "type": "int",
        "default": "difficulty-aware 3..7 with a canonical 7-column anchor",
        "valid": "3..7",
    },
    "left_color": {
        "type": "color",
        "default": "rng nonzero, not 5",
        "valid": "1..9 (≠5)",
    },
    "right_color": {
        "type": "color",
        "default": "rng nonzero, not 5 or left_color",
        "valid": "1..9 (≠5)",
    },
    "both_zero_target": {
        "type": "int",
        "default": "difficulty-aware rng 1..6",
        "valid": "1..6",
    },
    "panel_pattern": {
        "type": "str",
        "default": "rng helpful; exact state signature is observable",
        "valid": "|".join(PANEL_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _validate_call(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and type(difficulty) is not str:
        raise TypeError("difficulty must be None or one of easy/medium/hard")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")


def _normalize_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Normalize the legacy ``texture`` alias and isolate negative fixtures."""
    values = dict(overrides)
    texture = values.pop("texture", None)

    if texture in HELPFUL_TEXTURES:
        if "panel_pattern" in values and values["panel_pattern"] != texture:
            raise ValueError("texture and panel_pattern overrides disagree")
        values["panel_pattern"] = texture
        texture = None
    elif texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")

    unknown = sorted(set(values) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if texture is not None and set(values) - {
        "grid_h",
        "half_w",
        "left_color",
        "right_color",
    }:
        raise ValueError(
            "degenerate textures cannot be combined with count/pattern controls"
        )
    return values, texture


def _dimension_bounds(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (3, 6), (3, 5)
    if difficulty in (None, "medium"):
        return (4, 10), (4, 7)
    if difficulty == "hard":
        return (8, 14), (5, 7)
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _count_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 1, 3
    if difficulty in (None, "medium"):
        return 2, 5
    if difficulty == "hard":
        return 3, 6
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_dimensions(ctx, values: dict[str, Any], difficulty: str | None) -> tuple[int, int]:
    h_bounds, w_bounds = _dimension_bounds(difficulty)
    # Half of fully default samples are exact canonical-profile anchors.  The
    # branch is sample-index based, so it adds no hidden provenance draw.
    canonical_anchor = (
        "grid_h" not in values
        and "half_w" not in values
        and ctx.sample_index % 2 == 0
    )
    if "grid_h" in values:
        grid_h = ctx.draw_int_strict("grid_h", 3, 14)
    elif canonical_anchor:
        grid_h = ctx.draw_int_strict("grid_h", 4, 4)
    else:
        grid_h = ctx.draw_int_strict("grid_h", *h_bounds)

    if "half_w" in values:
        half_w = ctx.draw_int_strict("half_w", 3, 7)
    elif canonical_anchor:
        half_w = ctx.draw_int_strict("half_w", 7, 7)
    else:
        half_w = ctx.draw_int_strict("half_w", *w_bounds)
    return grid_h, half_w


def _draw_colors(ctx, values: dict[str, Any]) -> tuple[int, int]:
    requested_left = values.get("left_color")
    requested_right = values.get("right_color")
    for name, value in (("left_color", requested_left), ("right_color", requested_right)):
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer color (not bool)")
    if requested_left is not None and requested_right is not None:
        if requested_left == requested_right:
            error = ValueError("left_color and right_color must differ")
            error.incompatible_axes = ("left_color", "right_color")
            raise error

    left_exclude = {0, 5}
    if requested_right is not None and requested_left is None:
        left_exclude.add(requested_right)
    left = ctx.draw_color_strict("left_color", exclude=left_exclude)
    right = ctx.draw_color_strict("right_color", exclude={0, 5, left})
    return left, right


def _ordered_cells(height: int, half_w: int, pattern: str, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(height) for c in range(half_w)]
    if pattern == "random":
        rng.shuffle(cells)
        return cells
    if pattern == "blob":
        anchor = rng.choice(cells)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                abs(cell[0] - anchor[0]) + abs(cell[1] - anchor[1]),
                tie[cell],
            ),
        )
    if pattern == "diagonal":
        period = max(height, half_w)
        offset = rng.randrange(period)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (((cell[1] - cell[0] - offset) % period), tie[cell]),
        )
    if pattern == "border":
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                0
                if cell[0] in (0, height - 1) or cell[1] in (0, half_w - 1)
                else 1,
                tie[cell],
            ),
        )
    if pattern == "stripes":
        row_offset = rng.randrange(2)
        tie = {cell: rng.random() for cell in cells}
        return sorted(cells, key=lambda cell: ((cell[0] - row_offset) % 2, tie[cell]))
    if pattern == "checker":
        parity = rng.randrange(2)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: ((cell[0] + cell[1] - parity) % 2, tie[cell]),
        )
    raise ValueError(f"unknown panel_pattern {pattern!r}")


def _build_scene(
    height: int,
    half_w: int,
    left_color: int,
    right_color: int,
    both_zero_target: int,
    panel_pattern: str,
    rng,
) -> list[list[int]]:
    cells = _ordered_cells(height, half_w, panel_pattern, rng)
    both_zero = set(cells[:both_zero_target])
    remaining = sorted(set(cells) - both_zero)
    if len(remaining) < 3:
        raise ValueError("both_zero_target leaves no room for all NOR-negative states")

    states: dict[tuple[int, int], str] = {}
    for cell, state in zip(remaining[:3], PATTERN_SIGNATURES[panel_pattern]):
        states[cell] = state
    for cell in remaining[3:]:
        states[cell] = rng.choice(("10", "01", "11", "11"))

    grid = full_grid(height, 2 * half_w, 0)
    for r, c in remaining:
        state = states[(r, c)]
        if state[0] == "1":
            grid[r][c] = left_color
        if state[1] == "1":
            grid[r][half_w + c] = right_color
    return grid


def _draw_degenerate(
    name: str,
    height: int,
    half_w: int,
    left_color: int,
    right_color: int,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, 2 * half_w, 0)
    if name == "no_both_zero":
        for r in range(height):
            for c in range(half_w):
                grid[r][c] = left_color
                if rng.random() < 0.5:
                    grid[r][half_w + c] = right_color
        return grid
    if name == "all_both_zero":
        return grid
    if name == "same_halves":
        for r in range(height):
            for c in range(half_w):
                if rng.random() < 0.5:
                    grid[r][c] = left_color
                    grid[r][half_w + c] = right_color
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    values, degenerate = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    height, half_w = _draw_dimensions(ctx, values, difficulty)
    left_color, right_color = _draw_colors(ctx, values)
    rng = ctx.draw_rng("scene")
    if degenerate is not None:
        return _draw_degenerate(
            degenerate, height, half_w, left_color, right_color, rng
        )

    count_lo, count_hi = _count_bounds(difficulty)
    if "both_zero_target" in values:
        both_zero_target = ctx.draw_int_strict("both_zero_target", 1, 6)
    else:
        both_zero_target = ctx.draw_int_strict(
            "both_zero_target", count_lo, count_hi
        )
    panel_pattern = ctx.draw_choice("panel_pattern", PANEL_PATTERNS)
    return _build_scene(
        height,
        half_w,
        left_color,
        right_color,
        both_zero_target,
        panel_pattern,
        rng,
    )


def _grid_shape(grid):
    if not isinstance(grid, list) or not grid:
        return None
    if any(not isinstance(row, list) or not row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def semantic_observables(grid):
    shape = _grid_shape(grid)
    if shape is None or shape[1] % 2:
        return None
    height, width = shape
    half_w = width // 2
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    nonzero_states: list[tuple[tuple[int, int], str]] = []
    for r in range(height):
        for c in range(half_w):
            state = ("1" if grid[r][c] != 0 else "0") + (
                "1" if grid[r][half_w + c] != 0 else "0"
            )
            counts[state] += 1
            if state != "00":
                nonzero_states.append(((r, c), state))
    signature = tuple(state for _cell, state in nonzero_states[:3])
    return {
        "grid_h": height,
        "half_w": half_w,
        "left_values": {grid[r][c] for r in range(height) for c in range(half_w)},
        "right_values": {
            grid[r][half_w + c] for r in range(height) for c in range(half_w)
        },
        "state_counts": counts,
        "panel_pattern": SIGNATURE_PATTERNS.get(signature),
        "pattern_signature": signature,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the canonical horizontal two-panel NOR teaching grammar."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a nonempty rectangular list of rows"]
    height, width = shape
    errors = []
    if not 3 <= height <= 14:
        errors.append(f"height must be in 3..14, got {height}")
    if width % 2:
        errors.append(f"width {width} is not even (two equal halves required)")
    if width % 2 == 0 and not 3 <= width // 2 <= 7:
        errors.append(f"half width must be in 3..7, got {width // 2}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
    if width % 2 or errors:
        return errors

    facts = semantic_observables(grid)
    left_values = facts["left_values"]
    right_values = facts["right_values"]
    left_fg = left_values - {0}
    right_fg = right_values - {0}
    if len(left_fg) != 1 or 5 in left_fg:
        errors.append(
            "left half must use exactly background 0 and one nonzero non-5 color, "
            f"got {sorted(left_values)}"
        )
    if len(right_fg) != 1 or 5 in right_fg:
        errors.append(
            "right half must use exactly background 0 and one nonzero non-5 color, "
            f"got {sorted(right_values)}"
        )
    if len(left_fg) == 1 and len(right_fg) == 1 and left_fg == right_fg:
        errors.append("left and right foreground colors must differ")

    counts = facts["state_counts"]
    for state, label in (
        ("00", "both-zero"),
        ("10", "left-only"),
        ("01", "right-only"),
        ("11", "both-nonzero"),
    ):
        if counts[state] < 1:
            errors.append(f"need at least one aligned {label} cell")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = semantic_observables(grid)
    pattern = facts["panel_pattern"]
    if pattern is None:
        raise ValueError(
            "cannot observe panel_pattern: first three non-00 states are "
            f"{facts['pattern_signature']!r}"
        )
    return {
        "grid_h": facts["grid_h"],
        "half_w": facts["half_w"],
        "left_color": next(iter(facts["left_values"] - {0})),
        "right_color": next(iter(facts["right_values"] - {0})),
        "both_zero_target": facts["state_counts"]["00"],
        "panel_pattern": pattern,
    }


def rule_mirror(grid):
    """Python test mirror; the selected Racket rule remains authoritative."""
    height = len(grid)
    half_w = len(grid[0]) // 2
    return [
        [
            5 if grid[r][c] == 0 and grid[r][half_w + c] == 0 else 0
            for c in range(half_w)
        ]
        for r in range(height)
    ]


# Executable semantic contract -------------------------------------------------
# These rivals are deliberately simple occupancy truth tables.  A lawful
# default draw contains all four inputs to that table, so every individual
# example is already a complete counterexample set for the intended NOR rule.
def _occupancy_rule(grid, predicate):
    height = len(grid)
    half_w = len(grid[0]) // 2
    return [
        [
            5
            if predicate(grid[r][c] != 0, grid[r][half_w + c] != 0)
            else 0
            for c in range(half_w)
        ]
        for r in range(height)
    ]


def _constant_zero(grid):
    return _occupancy_rule(grid, lambda _left, _right: False)


def _left_zero(grid):
    return _occupancy_rule(grid, lambda left, _right: not left)


def _right_zero(grid):
    return _occupancy_rule(grid, lambda _left, right: not right)


def _equal_occupancy(grid):
    return _occupancy_rule(grid, lambda left, right: left == right)


def _xor_occupancy(grid):
    return _occupancy_rule(grid, lambda left, right: left != right)


def _both_nonzero(grid):
    return _occupancy_rule(grid, lambda left, right: left and right)


def _either_zero(grid):
    return _occupancy_rule(grid, lambda left, right: not (left and right))


SEMANTIC_RIVALS = {
    "constant_zero": _constant_zero,
    "left_zero": _left_zero,
    "right_zero": _right_zero,
    "equal_occupancy": _equal_occupancy,
    "xor_occupancy": _xor_occupancy,
    "both_nonzero": _both_nonzero,
    "either_zero": _either_zero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}


def _has_state(state: str):
    def witness(grid) -> bool:
        if self_check(grid):
            return False
        return semantic_observables(grid)["state_counts"][state] > 0

    return witness


SEMANTIC_WITNESSES = {
    "state_00": _has_state("00"),
    "state_10": _has_state("10"),
    "state_01": _has_state("01"),
    "state_11": _has_state("11"),
}
WITNESS_RIVALS = {
    "state_00": ["constant_zero", "xor_occupancy", "both_nonzero"],
    "state_10": ["right_zero", "xor_occupancy", "either_zero"],
    "state_01": ["left_zero", "xor_occupancy", "either_zero"],
    "state_11": ["equal_occupancy", "both_nonzero"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a declared truth-table rival can change the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    survivors = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        if self_check(grid):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        official = rule_mirror(grid)
        if demo["output"] != official:
            reasons.append(f"demo {index} output does not match aligned NOR")
            continue
        survivors = {
            name
            for name in survivors
            if LESSON_COMPETITORS[name](grid) == demo["output"]
        }

    query_grid = query["input"]
    if self_check(query_grid):
        reasons.append("query input is outside the teaching grammar")
        return reasons
    official_query = rule_mirror(query_grid)
    if "output" in query and query["output"] != official_query:
        reasons.append("query output does not match aligned NOR")
    if reasons:
        return reasons

    for name in sorted(survivors):
        if LESSON_COMPETITORS[name](query_grid) != official_query:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
