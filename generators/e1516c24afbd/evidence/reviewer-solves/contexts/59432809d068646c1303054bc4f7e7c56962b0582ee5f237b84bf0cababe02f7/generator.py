"""Generator for ARC task fafffa47 (content hash e1516c24afbd).

The input contains two equal-size panels stacked vertically with no separator.
The output marks an aligned position with color 2 exactly when both panel cells
are zero; all other aligned occupancy states map to zero.

Normal draws explicitly contain all four joint states ``00``, ``10``, ``01``,
and ``11``.  This makes the cellwise NOR relation visible while retaining a
canonical 6x3 curriculum anchor in every difficulty band.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1516c24afbd"
TASK_ID = GENERATOR_ID
RULE_HASH = "de03400353f9"
VERSION = "2.0.0"
SUMMARY = (
    "Two equal-size panels are stacked vertically. Output cell (r,c) is 2 "
    "exactly when both aligned panel cells are 0, otherwise 0. Normal draws "
    "contain all four aligned occupancy states, use distinct non-2 panel "
    "colors, and vary dimensions, colors, positive-mask count, and layout."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is 2*half_h by grid_w with half_h and grid_w in 3..10",
    "top and bottom each use background 0 plus one distinct nonzero non-2 color",
    "normal draws contain aligned states 00, 10, 01, and 11",
    "color 2 is output-only",
]

LAYOUTS = ("random", "cluster", "diagonal", "border", "stripes", "checker")
# The first three lexicographic non-00 cells encode the requested layout with a
# unique permutation of the three negative NOR states.  The layout therefore
# remains exactly observable even when two spatial ordering heuristics happen
# to choose the same small 00 mask.
LAYOUT_SIGNATURES = {
    "random": ("10", "01", "11"),
    "cluster": ("10", "11", "01"),
    "diagonal": ("01", "10", "11"),
    "border": ("01", "11", "10"),
    "stripes": ("11", "10", "01"),
    "checker": ("11", "01", "10"),
}
SIGNATURE_LAYOUTS = {signature: layout for layout, signature in LAYOUT_SIGNATURES.items()}
HELPFUL_TEXTURES = LAYOUTS
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_halves")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "half_h": {
        "type": "int",
        "default": "difficulty-aware 3..10 with a canonical 3-row anchor",
        "valid": "3..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 3..10 with a canonical 3-column anchor",
        "valid": "3..10",
    },
    "top_color": {
        "type": "color",
        "default": "rng nonzero, not 2",
        "valid": "1..9 (≠2)",
    },
    "bot_color": {
        "type": "color",
        "default": "rng nonzero, not 2 or top_color",
        "valid": "1..9 (≠2)",
    },
    "both_zero_count": {
        "type": "int",
        "default": "difficulty-aware rng 1..6",
        "valid": "1..6",
    },
    "layout": {
        "type": "str",
        "default": "rng helpful; exact state signature is observable",
        "valid": "|".join(LAYOUTS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _normalize_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Normalize legacy controls and keep negative fixtures out of AXES."""
    values = dict(overrides)
    texture = values.pop("texture", None)
    legacy_layout = values.pop("panel_pattern", None)
    legacy_count = values.pop("both_zero_target", None)

    if legacy_layout is not None:
        if "layout" in values and values["layout"] != legacy_layout:
            raise ValueError("panel_pattern and layout overrides disagree")
        values["layout"] = legacy_layout
    if legacy_count is not None:
        if "both_zero_count" in values and values["both_zero_count"] != legacy_count:
            raise ValueError("both_zero_target and both_zero_count overrides disagree")
        values["both_zero_count"] = legacy_count

    if texture in HELPFUL_TEXTURES:
        if "layout" in values and values["layout"] != texture:
            raise ValueError("texture and layout overrides disagree")
        values["layout"] = texture
        texture = None
    elif texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")

    unknown = sorted(set(values) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if texture is not None and set(values) - {
        "half_h",
        "grid_w",
        "top_color",
        "bot_color",
    }:
        raise ValueError("degenerate textures cannot be combined with count/layout controls")
    return values, texture


def _dimension_bounds(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (3, 5), (3, 5)
    if difficulty in (None, "medium"):
        return (3, 8), (3, 8)
    if difficulty == "hard":
        return (6, 10), (6, 10)
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
        "half_h" not in values
        and "grid_w" not in values
        and ctx.sample_index % 2 == 0
    )
    if "half_h" in values:
        half_h = ctx.draw_int("half_h", 3, 10)
    elif canonical_anchor:
        half_h = ctx.draw_int("half_h", 3, 3)
    else:
        half_h = ctx.draw_int("half_h", *h_bounds)

    if "grid_w" in values:
        grid_w = ctx.draw_int("grid_w", 3, 10)
    elif canonical_anchor:
        grid_w = ctx.draw_int("grid_w", 3, 3)
    else:
        grid_w = ctx.draw_int("grid_w", *w_bounds)
    return half_h, grid_w


def _draw_colors(ctx, values: dict[str, Any]) -> tuple[int, int]:
    requested_top = values.get("top_color")
    requested_bot = values.get("bot_color")
    if requested_top is not None and requested_bot is not None:
        if int(requested_top) == int(requested_bot):
            error = ValueError("top_color and bot_color must differ")
            error.incompatible_axes = ("top_color", "bot_color")
            raise error

    top_exclude = {0, 2}
    if requested_bot is not None and requested_top is None:
        top_exclude.add(int(requested_bot))
    top = ctx.draw_color("top_color", exclude=top_exclude)
    bot = ctx.draw_color("bot_color", exclude={0, 2, top})
    return top, bot


def _ordered_cells(half_h: int, width: int, layout: str, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(half_h) for c in range(width)]
    if layout == "random":
        rng.shuffle(cells)
        return cells
    if layout == "cluster":
        anchor = rng.choice(cells)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                abs(cell[0] - anchor[0]) + abs(cell[1] - anchor[1]),
                tie[cell],
            ),
        )
    if layout == "diagonal":
        period = max(half_h, width)
        offset = rng.randrange(period)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (((cell[1] - cell[0] - offset) % period), tie[cell]),
        )
    if layout == "border":
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                0
                if cell[0] in (0, half_h - 1) or cell[1] in (0, width - 1)
                else 1,
                tie[cell],
            ),
        )
    if layout == "stripes":
        row_offset = rng.randrange(2)
        tie = {cell: rng.random() for cell in cells}
        return sorted(cells, key=lambda cell: ((cell[0] - row_offset) % 2, tie[cell]))
    if layout == "checker":
        parity = rng.randrange(2)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: ((cell[0] + cell[1] - parity) % 2, tie[cell]),
        )
    raise ValueError(f"unknown layout {layout!r}")


def _build_scene(
    half_h: int,
    width: int,
    top_color: int,
    bot_color: int,
    both_zero_count: int,
    layout: str,
    rng,
) -> list[list[int]]:
    cells = _ordered_cells(half_h, width, layout, rng)
    both_zero = set(cells[:both_zero_count])
    remaining = sorted(set(cells) - both_zero)
    if len(remaining) < 3:
        raise ValueError("both_zero_count leaves no room for all NOR-negative states")

    states: dict[tuple[int, int], str] = {}
    for cell, state in zip(remaining[:3], LAYOUT_SIGNATURES[layout]):
        states[cell] = state
    for cell in remaining[3:]:
        states[cell] = rng.choice(("10", "01", "11", "11"))

    grid = full_grid(2 * half_h, width, 0)
    for r, c in remaining:
        state = states[(r, c)]
        if state[0] == "1":
            grid[r][c] = top_color
        if state[1] == "1":
            grid[half_h + r][c] = bot_color
    return grid


def _draw_degenerate(
    name: str,
    half_h: int,
    width: int,
    top_color: int,
    bot_color: int,
    rng,
) -> list[list[int]]:
    grid = full_grid(2 * half_h, width, 0)
    if name == "no_both_zero":
        for r in range(half_h):
            for c in range(width):
                grid[r][c] = top_color
                if rng.random() < 0.5:
                    grid[half_h + r][c] = bot_color
        return grid
    if name == "all_both_zero":
        return grid
    if name == "same_halves":
        for r in range(half_h):
            for c in range(width):
                if rng.random() < 0.5:
                    grid[r][c] = top_color
                    grid[half_h + r][c] = bot_color
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values, degenerate = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    half_h, width = _draw_dimensions(ctx, values, difficulty)
    top_color, bot_color = _draw_colors(ctx, values)
    rng = ctx.draw_rng("scene")
    if degenerate is not None:
        return _draw_degenerate(
            degenerate, half_h, width, top_color, bot_color, rng
        )

    count_lo, count_hi = _count_bounds(difficulty)
    if "both_zero_count" in values:
        both_zero_count = ctx.draw_int("both_zero_count", 1, 6)
    else:
        both_zero_count = ctx.draw_int("both_zero_count", count_lo, count_hi)
    layout = ctx.draw_choice("layout", LAYOUTS)
    return _build_scene(
        half_h,
        width,
        top_color,
        bot_color,
        both_zero_count,
        layout,
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
    if shape is None or shape[0] % 2:
        return None
    height, width = shape
    half_h = height // 2
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    nonzero_states: list[tuple[tuple[int, int], str]] = []
    for r in range(half_h):
        for c in range(width):
            state = ("1" if grid[r][c] != 0 else "0") + (
                "1" if grid[half_h + r][c] != 0 else "0"
            )
            counts[state] += 1
            if state != "00":
                nonzero_states.append(((r, c), state))
    signature = tuple(state for _cell, state in nonzero_states[:3])
    return {
        "half_h": half_h,
        "grid_w": width,
        "top_values": {value for row in grid[:half_h] for value in row},
        "bot_values": {value for row in grid[half_h:] for value in row},
        "state_counts": counts,
        "layout": SIGNATURE_LAYOUTS.get(signature),
        "layout_signature": signature,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the canonical stacked two-panel NOR teaching grammar."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a nonempty rectangular list of rows"]
    height, width = shape
    errors = []
    if height % 2:
        errors.append(f"height {height} is not even (two equal halves required)")
    if height % 2 == 0 and not 3 <= height // 2 <= 10:
        errors.append(f"half height must be in 3..10, got {height // 2}")
    if not 3 <= width <= 10:
        errors.append(f"width must be in 3..10, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
    if height % 2 or errors:
        return errors

    facts = semantic_observables(grid)
    top_values = facts["top_values"]
    bot_values = facts["bot_values"]
    top_fg = top_values - {0}
    bot_fg = bot_values - {0}
    if len(top_fg) != 1 or 2 in top_fg:
        errors.append(
            "top half must use exactly background 0 and one nonzero non-2 color, "
            f"got {sorted(top_values)}"
        )
    if len(bot_fg) != 1 or 2 in bot_fg:
        errors.append(
            "bottom half must use exactly background 0 and one nonzero non-2 color, "
            f"got {sorted(bot_values)}"
        )
    if len(top_fg) == 1 and len(bot_fg) == 1 and top_fg == bot_fg:
        errors.append("top and bottom foreground colors must differ")

    counts = facts["state_counts"]
    if counts["00"] < 1:
        errors.append("need at least one aligned both-zero cell")
    if counts["11"] < 1:
        errors.append("need at least one aligned both-nonzero cell")
    if counts["10"] + counts["01"] < 1:
        errors.append("need at least one one-sided occupied cell")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = semantic_observables(grid)
    layout = facts["layout"]
    if layout is None:
        raise ValueError(
            "cannot observe layout: first three non-00 states are "
            f"{facts['layout_signature']!r}"
        )
    return {
        "half_h": facts["half_h"],
        "grid_w": facts["grid_w"],
        "top_color": next(iter(facts["top_values"] - {0})),
        "bot_color": next(iter(facts["bot_values"] - {0})),
        "both_zero_count": facts["state_counts"]["00"],
        "layout": layout,
    }


def rule_mirror(grid):
    """Python test mirror; the selected Racket rule remains authoritative."""
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            2 if grid[r][c] == 0 and grid[half_h + r][c] == 0 else 0
            for c in range(width)
        ]
        for r in range(half_h)
    ]

# Executable semantic contract -------------------------------------------------
# These rivals are deliberately simple occupancy truth tables.  A lawful
# default draw contains all four inputs to that table, so every individual
# example is already a complete counterexample set for the intended NOR rule.
def _occupancy_rule(grid, predicate):
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            2
            if predicate(grid[r][c] != 0, grid[half_h + r][c] != 0)
            else 0
            for c in range(width)
        ]
        for r in range(half_h)
    ]


def _constant_zero(grid):
    return _occupancy_rule(grid, lambda _top, _bot: False)


def _top_zero(grid):
    return _occupancy_rule(grid, lambda top, _bot: not top)


def _bottom_zero(grid):
    return _occupancy_rule(grid, lambda _top, bot: not bot)


def _equal_occupancy(grid):
    return _occupancy_rule(grid, lambda top, bot: top == bot)


def _xor_occupancy(grid):
    return _occupancy_rule(grid, lambda top, bot: top != bot)


def _both_nonzero(grid):
    return _occupancy_rule(grid, lambda top, bot: top and bot)


def _either_zero(grid):
    return _occupancy_rule(grid, lambda top, bot: not (top and bot))


SEMANTIC_RIVALS = {
    "constant_zero": _constant_zero,
    "top_zero": _top_zero,
    "bottom_zero": _bottom_zero,
    "equal_occupancy": _equal_occupancy,
    "xor_occupancy": _xor_occupancy,
    "both_nonzero": _both_nonzero,
    "either_zero": _either_zero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every declared rival is already contradicted by the canonical corpus.  The
# map remains explicit so the semantic gate can distinguish "none found" from
# an omitted declaration.
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
    "state_10": ["bottom_zero", "xor_occupancy", "either_zero"],
    "state_01": ["top_zero", "xor_occupancy", "either_zero"],
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

