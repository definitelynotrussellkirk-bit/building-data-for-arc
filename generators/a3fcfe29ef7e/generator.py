"""Generator for ARC task f2829549 (content hash ``a3fcfe29ef7e``).

The input is an ``h x 7`` grid containing two aligned three-column panels
separated by one solid column.  The output is ``h x 3`` and writes color 3 at
an aligned position exactly when both panel cells are zero.  All other aligned
occupancy states map to zero.

Ordinary draws contain all four Boolean occupancy states ``00``, ``10``,
``01``, and ``11``.  Consecutive draws alternate different and equal panel
foreground colors.  Equal-color ``11`` cells are essential teaching evidence:
all canonical pairs use different panel colors, so the incorrect rule "mark
raw-equal values" otherwise agrees with every canonical answer.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3fcfe29ef7e"
TASK_ID = GENERATOR_ID
RULE_HASH = "f7f19079511e"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("different", "same")

SUMMARY = (
    "Two aligned three-column panels are separated by one solid column. "
    "Output color 3 appears exactly at aligned 00 positions; 10, 01, and 11 "
    "map to 0. Ordinary draws contain all four states, exclude color 3 from "
    "the input, and alternate different/same panel colors to refute raw-value "
    "equality."
)

INVARIANTS = [
    "input is 3..18 rows by 7 columns (3 left + separator + 3 right)",
    "each panel uses 0 and one nonzero foreground; the solid separator differs from both",
    "ordinary draws contain aligned states 00, 10, 01, and 11",
    "ordinary draws contain exactly 1..6 aligned 00 cells",
    "answer color 3 is output-only",
]

LAYOUTS = ("random", "cluster", "diagonal", "border", "stripes", "checker")
# The first three row-major non-00 cells encode a permutation of the three
# negative NOR states.  This makes the layout control exactly observable even
# when two geometric orderings happen to produce the same positive mask.
LAYOUT_SIGNATURES = {
    "random": ("10", "01", "11"),
    "cluster": ("10", "11", "01"),
    "diagonal": ("01", "10", "11"),
    "border": ("01", "11", "10"),
    "stripes": ("11", "10", "01"),
    "checker": ("11", "01", "10"),
}
SIGNATURE_LAYOUTS = {
    signature: layout for layout, signature in LAYOUT_SIGNATURES.items()
}
HELPFUL_TEXTURES = LAYOUTS
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_panels")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 3..18 with canonical 4-row anchors",
        "valid": "3..18",
    },
    "left_color": {
        "type": "color",
        "default": "rng (not 0 or 3)",
        "valid": "1..9 (≠3)",
    },
    "right_color": {
        "type": "color",
        "default": "scheduled same/different relation; not 0 or 3",
        "valid": "1..9 (≠3)",
    },
    "sep_color": {
        "type": "color",
        "default": "rng distinct from 0, 3, and both panel foregrounds",
        "valid": "1..9 (≠3)",
    },
    "both_zero_count": {
        "type": "int",
        "default": "difficulty-aware rng 1..6",
        "valid": "1..6",
    },
    "layout": {
        "type": "str",
        "default": "rng helpful; exact state-permutation signature is observable",
        "valid": "random|cluster|diagonal|border|stripes|checker",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Alternate palette relation across the declared two-step schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _incompatible(message: str, *axes: str) -> ValueError:
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    return error


def _normalize_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Normalize useful legacy aliases; keep negative fixtures outside AXES."""
    values = dict(overrides)
    texture = values.pop("texture", None)
    legacy_layout = values.pop("panel_pattern", None)
    legacy_count = values.pop("both_zero_target", None)
    legacy_color = values.pop("fg_color", None)

    if legacy_layout is not None:
        if "layout" in values and values["layout"] != legacy_layout:
            raise ValueError("panel_pattern and layout overrides disagree")
        values["layout"] = legacy_layout
    if legacy_count is not None:
        if "both_zero_count" in values and values["both_zero_count"] != legacy_count:
            raise ValueError("both_zero_target and both_zero_count overrides disagree")
        values["both_zero_count"] = legacy_count
    if legacy_color is not None:
        for key in ("left_color", "right_color"):
            if key in values and int(values[key]) != int(legacy_color):
                raise ValueError(f"fg_color and {key} overrides disagree")
            values[key] = legacy_color

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
        "grid_h",
        "left_color",
        "right_color",
        "sep_color",
    }:
        raise ValueError(
            "degenerate textures cannot be combined with count/layout controls"
        )

    if "sep_color" in values and "left_color" in values:
        if int(values["sep_color"]) == int(values["left_color"]):
            raise _incompatible(
                "separator color must differ from left panel foreground",
                "sep_color",
                "left_color",
            )
    if "sep_color" in values and "right_color" in values:
        if int(values["sep_color"]) == int(values["right_color"]):
            raise _incompatible(
                "separator color must differ from right panel foreground",
                "sep_color",
                "right_color",
            )
    return values, texture


def _height_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 3, 7
    if difficulty in (None, "medium"):
        return 5, 12
    if difficulty == "hard":
        return 10, 18
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _count_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 1, 3
    if difficulty in (None, "medium"):
        return 2, 5
    if difficulty == "hard":
        return 3, 6
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_height(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "grid_h" in values:
        return ctx.draw_int("grid_h", 3, 18)
    # Canonical inputs are 4x7 and use three distinct nonzero input colors.
    # Every fourth sample is therefore an all-band canonical-profile anchor.
    if ctx.sample_index % 4 == 0:
        return ctx.draw_int("grid_h", 4, 4)
    lo, hi = _height_bounds(difficulty)
    return ctx.draw_int("grid_h", lo, hi)


def _draw_count(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "both_zero_count" in values:
        return ctx.draw_int("both_zero_count", 1, 6)
    lo, hi = _count_bounds(difficulty)
    return ctx.draw_int("both_zero_count", lo, hi)


def _only_color(color: int) -> set[int]:
    return set(range(10)) - {int(color)}


def _draw_colors(
    ctx,
    values: dict[str, Any],
    relation: str,
) -> tuple[int, int, int]:
    has_left = "left_color" in values
    has_right = "right_color" in values
    requested_sep = values.get("sep_color")
    sep_forbidden = {int(requested_sep)} if requested_sep is not None else set()

    if has_left and has_right:
        left = ctx.draw_color("left_color", exclude={0, 3})
        right = ctx.draw_color("right_color", exclude={0, 3})
    elif has_right and not has_left:
        right = ctx.draw_color("right_color", exclude={0, 3})
        if relation == "same":
            left_exclude = _only_color(right)
        else:
            left_exclude = {0, 3, right} | sep_forbidden
        left = ctx.draw_color("left_color", exclude=left_exclude)
    else:
        left = ctx.draw_color("left_color", exclude={0, 3} | sep_forbidden)
        if relation == "same":
            right_exclude = _only_color(left)
        else:
            right_exclude = {0, 3, left} | sep_forbidden
        right = ctx.draw_color("right_color", exclude=right_exclude)

    if requested_sep is not None and int(requested_sep) in {left, right}:
        axes = ["sep_color"]
        if has_left and int(requested_sep) == left:
            axes.append("left_color")
        if has_right and int(requested_sep) == right:
            axes.append("right_color")
        raise _incompatible("separator color collides with a panel foreground", *axes)
    separator = ctx.draw_color("sep_color", exclude={0, 3, left, right})
    return left, right, separator


def _ordered_cells(h: int, layout: str, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(h) for c in range(3)]
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
        period = max(h, 3)
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
                0 if cell[0] in (0, h - 1) or cell[1] in (0, 2) else 1,
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
    h: int,
    left_color: int,
    right_color: int,
    sep_color: int,
    both_zero_count: int,
    layout: str,
    rng,
) -> list[list[int]]:
    cells = _ordered_cells(h, layout, rng)
    both_zero = set(cells[:both_zero_count])
    remaining = sorted(set(cells) - both_zero)
    if len(remaining) < 3:
        raise ValueError("both_zero_count leaves no room for all three negative states")

    states: dict[tuple[int, int], str] = {}
    for cell, state in zip(remaining[:3], LAYOUT_SIGNATURES[layout]):
        states[cell] = state
    for cell in remaining[3:]:
        states[cell] = rng.choice(("10", "01", "11", "11"))

    grid = full_grid(h, 7, 0)
    for row in grid:
        row[3] = sep_color
    for r, c in remaining:
        state = states[(r, c)]
        if state[0] == "1":
            grid[r][c] = left_color
        if state[1] == "1":
            grid[r][c + 4] = right_color
    return grid


def _draw_degenerate(
    name: str,
    h: int,
    left_color: int,
    right_color: int,
    sep_color: int,
    rng,
) -> list[list[int]]:
    grid = full_grid(h, 7, 0)
    for row in grid:
        row[3] = sep_color
    cells = [(r, c) for r in range(h) for c in range(3)]
    if name == "no_both_zero":
        states = ("10", "01", "11")
        for index, (r, c) in enumerate(cells):
            state = states[index % len(states)]
            if state[0] == "1":
                grid[r][c] = left_color
            if state[1] == "1":
                grid[r][c + 4] = right_color
        return grid
    if name == "all_both_zero":
        return grid
    if name == "same_panels":
        rng.shuffle(cells)
        for r, c in cells[: max(1, len(cells) // 2)]:
            grid[r][c] = left_color
            grid[r][c + 4] = right_color
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values, degenerate = _normalize_overrides(overrides)
    relation = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    h = _draw_height(ctx, values, difficulty)
    left_color, right_color, sep_color = _draw_colors(ctx, values, relation)
    rng = ctx.draw_rng("scene")
    if degenerate is not None:
        return _draw_degenerate(
            degenerate, h, left_color, right_color, sep_color, rng
        )

    both_zero_count = _draw_count(ctx, values, difficulty)
    layout = ctx.draw_choice("layout", LAYOUTS)
    return _build_scene(
        h,
        left_color,
        right_color,
        sep_color,
        both_zero_count,
        layout,
        rng,
    )


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    """Recover palette roles, occupancy counts, and all declared exact axes."""
    h = len(grid) if isinstance(grid, list) else 0
    rectangular = bool(grid) and all(
        isinstance(row, list) and len(row) == 7 for row in grid
    )
    left_values: set[int] = set()
    right_values: set[int] = set()
    separator_values: set[int] = set()
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    nonzero_states: list[str] = []
    if rectangular:
        left_values = {grid[r][c] for r in range(h) for c in range(3)}
        right_values = {grid[r][c] for r in range(h) for c in range(4, 7)}
        separator_values = {grid[r][3] for r in range(h)}
        for r in range(h):
            for c in range(3):
                state = ("1" if grid[r][c] != 0 else "0") + (
                    "1" if grid[r][c + 4] != 0 else "0"
                )
                counts[state] += 1
                if state != "00":
                    nonzero_states.append(state)

    left_fg = left_values - {0}
    right_fg = right_values - {0}
    left_color = next(iter(left_fg)) if len(left_fg) == 1 else None
    right_color = next(iter(right_fg)) if len(right_fg) == 1 else None
    sep_color = next(iter(separator_values)) if len(separator_values) == 1 else None
    relation = None
    if left_color is not None and right_color is not None:
        relation = "same" if left_color == right_color else "different"
    signature = tuple(nonzero_states[:3])
    return {
        "grid_h": h,
        "left_values": left_values,
        "right_values": right_values,
        "separator_values": separator_values,
        "left_color": left_color,
        "right_color": right_color,
        "sep_color": sep_color,
        "color_relation": relation,
        "state_counts": counts,
        "layout": SIGNATURE_LAYOUTS.get(signature),
        "layout_signature": signature,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Return every exact AXES value observed in a lawful generated grid."""
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
        "grid_h": facts["grid_h"],
        "left_color": facts["left_color"],
        "right_color": facts["right_color"],
        "sep_color": facts["sep_color"],
        "both_zero_count": facts["state_counts"]["00"],
        "layout": layout,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror; the selected canonical Racket rule is authoritative."""
    return [
        [3 if row[c] == 0 and row[c + 4] == 0 else 0 for c in range(3)]
        for row in grid
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical separated-panel NOR teaching grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty 2D list"]
    if any(not isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    h = len(grid)
    if width != 7:
        errors.append(f"input width must be 7 (3+1+3), got {width}")
    if not 3 <= h <= 18:
        errors.append(f"input height must be in 3..18, got {h}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
    if width != 7 or errors:
        return errors

    palette = {value for row in grid for value in row}
    if 3 in palette:
        errors.append("input must not contain answer color 3")

    facts = semantic_observables(grid)
    left_fg = facts["left_values"] - {0}
    right_fg = facts["right_values"] - {0}
    sep_values = facts["separator_values"]
    counts = facts["state_counts"]

    if len(left_fg) != 1:
        errors.append(
            "left panel must use exactly 0 and one foreground color, got "
            f"{sorted(facts['left_values'])}"
        )
    if len(right_fg) != 1:
        errors.append(
            "right panel must use exactly 0 and one foreground color, got "
            f"{sorted(facts['right_values'])}"
        )
    if len(sep_values) != 1 or 0 in sep_values or 3 in sep_values:
        errors.append(
            "separator column must be one constant nonzero non-3 color, got "
            f"{sorted(sep_values)}"
        )
    if len(sep_values) == 1:
        separator = next(iter(sep_values))
        if separator in left_fg or separator in right_fg:
            errors.append("separator color must differ from both panel foregrounds")

    if not 1 <= counts["00"] <= 6:
        errors.append(
            f"aligned both-zero state 00 count must be in 1..6, got {counts['00']}"
        )
    if counts["10"] < 1:
        errors.append("need at least one left-only state 10")
    if counts["01"] < 1:
        errors.append("need at least one right-only state 01")
    if counts["11"] < 1:
        errors.append("need at least one both-nonzero state 11")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the color-renamed canonical separated-panel manifold."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _predicate_rule(
    grid: list[list[int]],
    predicate: Callable[[int, int], bool],
) -> list[list[int]]:
    return [
        [3 if predicate(row[c], row[c + 4]) else 0 for c in range(3)]
        for row in grid
    ]


def _constant_zero(grid):
    return [[0 for _ in range(3)] for _row in grid]


def _left_zero(grid):
    return _predicate_rule(grid, lambda left, _right: left == 0)


def _right_zero(grid):
    return _predicate_rule(grid, lambda _left, right: right == 0)


def _occupancy_equal(grid):
    return _predicate_rule(grid, lambda left, right: (left == 0) == (right == 0))


def _occupancy_xor(grid):
    return _predicate_rule(grid, lambda left, right: (left == 0) != (right == 0))


def _both_nonzero(grid):
    return _predicate_rule(grid, lambda left, right: left != 0 and right != 0)


def _either_zero(grid):
    return _predicate_rule(grid, lambda left, right: left == 0 or right == 0)


def raw_value_equality(grid):
    """Canonical shortcut: mark raw-equal pairs rather than occupancy 00 pairs."""
    return _predicate_rule(grid, lambda left, right: left == right)


SEMANTIC_RIVALS = {
    "constant_zero": _constant_zero,
    "left_zero": _left_zero,
    "right_zero": _right_zero,
    "occupancy_equal": _occupancy_equal,
    "occupancy_xor": _occupancy_xor,
    "both_nonzero": _both_nonzero,
    "either_zero": _either_zero,
    "raw_value_equality": raw_value_equality,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Canonical left and right foregrounds are 7 and 5, so raw equality occurs only
# at 00 cells.  Same-color generated 11 cells are the separating witness.
CANONICAL_SHORTCUTS = {"raw_value_equality": raw_value_equality}


def _lawful_facts(grid) -> dict[str, Any] | None:
    return None if self_check(grid) else semantic_observables(grid)


def _has_state(state: str):
    return lambda grid: (
        (facts := _lawful_facts(grid)) is not None
        and facts["state_counts"][state] >= 1
    )


def _same_color_nonzero_pair(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(
        facts is not None
        and facts["color_relation"] == "same"
        and facts["state_counts"]["11"] >= 1
    )


SEMANTIC_WITNESSES = {
    "both_zero_positive_branch": _has_state("00"),
    "left_only_negative_branch": _has_state("10"),
    "right_only_negative_branch": _has_state("01"),
    "both_nonzero_negative_branch": _has_state("11"),
    "same_color_nonzero_pair": _same_color_nonzero_pair,
}
WITNESS_RIVALS = {
    "both_zero_positive_branch": ["constant_zero"],
    "left_only_negative_branch": ["right_zero", "occupancy_xor", "either_zero"],
    "right_only_negative_branch": ["left_zero", "occupancy_xor", "either_zero"],
    "both_nonzero_negative_branch": ["occupancy_equal", "both_nonzero"],
    "same_color_nonzero_pair": ["raw_value_equality"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named rival fits all demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], dict[str, list[list[int]]]]] = []
    for index, item in enumerate(demos):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(item["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(item["input"])
        if item["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the occupancy-NOR rule")
            continue
        prepared.append(
            (
                item["output"],
                {
                    name: competitor(item["input"])
                    for name, competitor in LESSON_COMPETITORS.items()
                },
            )
        )
    if reasons:
        return sorted(set(reasons))

    if not isinstance(query, dict) or "input" not in query:
        return ["query is malformed"]
    query_errors = self_check(query["input"])
    if query_errors:
        return ["query input is invalid: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query["input"])
    if "output" in query and query["output"] != query_truth:
        return ["query output disagrees with the occupancy-NOR rule"]
    query_competitors = {
        name: competitor(query["input"])
        for name, competitor in LESSON_COMPETITORS.items()
    }
    for name in sorted(query_competitors):
        survives = all(
            competitor_outputs[name] == output
            for output, competitor_outputs in prepared
        )
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but changes the query"
            )
    return reasons
