"""Generator for ARC task e345f17b (content hash ``a178821cc6bf``).

The input is an ``h x 8`` grid containing two adjacent, aligned 4-column
panels.  The output is ``h x 4`` and marks an aligned position with color 4
exactly when both panel cells are zero.  All other occupancy states map to 0.

Every ordinary draw contains all four aligned occupancy states ``00``, ``10``,
``01``, and ``11``.  Consecutive draws alternate between equal and different
panel foreground colors.  The equal-color example is important: all canonical
pairs use different panel colors, so the incorrect raw-value-equality rule
happens to solve every canonical pair.  A same-color ``11`` cell separates that
shortcut from the intended occupancy NOR rule.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a178821cc6bf"
TASK_ID = "a178821cc6bf"
VERSION = "3.0.0"  # restore canonical 4+4 geometry; add shortcut-complete contract
RULE_HASH = "ff2f0d5fbd0c"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "Two adjacent aligned 4-column panels.  Output color 4 appears exactly at "
    "aligned 00 positions; 10, 01, and 11 positions map to 0.  Ordinary draws "
    "contain every occupancy state, exclude color 4 from the input, and "
    "alternate same/different foreground palettes to refute raw equality."
)

INVARIANTS = [
    "input is 3..18 rows by 8 columns (4-column left panel + 4-column right panel)",
    "each panel uses 0 and exactly one nonzero foreground color; color 4 is absent",
    "ordinary draws contain at least one of every occupancy state 00, 10, 01, and 11",
    "ordinary draws contain 1..8 aligned 00 cells",
    "output is h x 4 and contains 4 exactly at aligned 00 cells",
]

LAYOUTS = ("random", "cluster", "diagonal", "border", "stripes", "checker")
# The first three row-major non-00 cells encode a permutation of the three
# negative states.  This makes the nominal layout control exactly observable,
# even when two spatial ordering heuristics happen to choose the same 00 mask.
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
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_occupancy")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 3..18 with canonical-size anchors",
        "valid": "3..18",
    },
    "left_color": {
        "type": "color",
        "default": "rng (not 0 or 4)",
        "valid": "1..9 (≠4)",
    },
    "right_color": {
        "type": "color",
        "default": "scheduled same/different relation; not 0 or 4",
        "valid": "1..9 (≠4)",
    },
    "both_zero_count": {
        "type": "int",
        "default": "difficulty-aware rng 1..8",
        "valid": "1..8",
    },
    "layout": {
        "type": "str",
        "default": "rng helpful; exact state-permutation signature is observable",
        "valid": "random|cluster|diagonal|border|stripes|checker",
    },
}

SCHEDULE_PROFILES = ("different", "same")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Alternate palette relation so every two-example window has both cases."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Normalize useful legacy aliases and reject unknown/conflicting controls."""
    values = dict(overrides)
    texture = values.pop("texture", None)
    legacy_layout = values.pop("panel_pattern", None)
    legacy_count = values.pop("both_zero_target", None)
    legacy_color = values.pop("fg_color", None)

    if "sep_color" in values:
        raise ValueError("sep_color is invalid: this task has no separator column")

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
    }:
        raise ValueError(
            "degenerate textures cannot be combined with count/layout controls"
        )
    return values, texture


def _height_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 3, 7
    if difficulty == "hard":
        return 10, 18
    if difficulty in (None, "medium"):
        return 5, 12
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _count_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 1, 4
    if difficulty == "hard":
        return 4, 8
    if difficulty in (None, "medium"):
        return 2, 6
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_height(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "grid_h" in values:
        return ctx.draw_int("grid_h", 3, 18)
    # Canonical inputs are 4x8 with a three-color palette.  Every fourth draw
    # is an all-band canonical-size anchor, including hard; easy/medium retain
    # additional even-index anchors.  Anchors land on the scheduled
    # different-color profile, so each band has measurable canonical-profile
    # support without collapsing the non-anchor scale distribution.
    if ctx.sample_index % 4 == 0:
        return ctx.draw_int("grid_h", 4, 4)
    if difficulty in (None, "easy", "medium") and ctx.sample_index % 2 == 0:
        return ctx.draw_int("grid_h", 4, 4)
    lo, hi = _height_bounds(difficulty)
    return ctx.draw_int("grid_h", lo, hi)


def _draw_count(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "both_zero_count" in values:
        return ctx.draw_int("both_zero_count", 1, 8)
    lo, hi = _count_bounds(difficulty)
    return ctx.draw_int("both_zero_count", lo, hi)


def _only_color(color: int) -> set[int]:
    """Return a draw_color exclusion set that leaves only ``color`` legal."""
    return set(range(10)) - {int(color)}


def _draw_colors(
    ctx,
    values: dict[str, Any],
    relation: str,
) -> tuple[int, int]:
    """Draw exact observable colors while respecting explicit overrides."""
    has_left = "left_color" in values
    has_right = "right_color" in values

    if has_left and has_right:
        left = ctx.draw_color("left_color", exclude={0, 4})
        right = ctx.draw_color("right_color", exclude={0, 4})
        return left, right

    if has_right and not has_left:
        right = ctx.draw_color("right_color", exclude={0, 4})
        left_exclude = _only_color(right) if relation == "same" else {0, 4, right}
        left = ctx.draw_color("left_color", exclude=left_exclude)
        return left, right

    left = ctx.draw_color("left_color", exclude={0, 4})
    right_exclude = _only_color(left) if relation == "same" else {0, 4, left}
    right = ctx.draw_color("right_color", exclude=right_exclude)
    return left, right


def _ordered_cells(h: int, layout: str, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(h) for c in range(4)]
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
        offset = rng.randrange(4)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                (cell[1] - cell[0] - offset) % 4,
                tie[cell],
            ),
        )
    if layout == "border":
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                0 if cell[0] in (0, h - 1) or cell[1] in (0, 3) else 1,
                tie[cell],
            ),
        )
    if layout == "stripes":
        row_offset = rng.randrange(2)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: ((cell[0] - row_offset) % 2, tie[cell]),
        )
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

    grid = full_grid(h, 8, 0)
    for r, c in cells:
        if (r, c) in both_zero:
            continue
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
    rng,
) -> list[list[int]]:
    grid = full_grid(h, 8, 0)
    cells = [(r, c) for r in range(h) for c in range(4)]
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
    if name == "same_occupancy":
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
    left_color, right_color = _draw_colors(ctx, values, relation)
    rng = ctx.draw_rng("scene")
    if degenerate is not None:
        return _draw_degenerate(degenerate, h, left_color, right_color, rng)

    both_zero_count = _draw_count(ctx, values, difficulty)
    layout = ctx.draw_choice("layout", LAYOUTS)
    return _build_scene(
        h,
        left_color,
        right_color,
        both_zero_count,
        layout,
        rng,
    )


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    """Recover palette roles, occupancy counts, and all exact declared axes."""
    h = len(grid) if isinstance(grid, list) else 0
    rectangular = bool(grid) and all(
        isinstance(row, list) and len(row) == 8 for row in grid
    )
    left_values: set[int] = set()
    right_values: set[int] = set()
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    nonzero_states: list[str] = []
    if rectangular:
        left_values = {grid[r][c] for r in range(h) for c in range(4)}
        right_values = {grid[r][c] for r in range(h) for c in range(4, 8)}
        for r in range(h):
            for c in range(4):
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
    relation = None
    if left_color is not None and right_color is not None:
        relation = "same" if left_color == right_color else "different"
    signature = tuple(nonzero_states[:3])
    return {
        "grid_h": h,
        "left_values": left_values,
        "right_values": right_values,
        "left_color": left_color,
        "right_color": right_color,
        "color_relation": relation,
        "state_counts": counts,
        "layout": SIGNATURE_LAYOUTS.get(signature),
        "layout_signature": signature,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Return every exact AXES value recoverable from a lawful generated grid."""
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
        "both_zero_count": facts["state_counts"]["00"],
        "layout": layout,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    return [
        [4 if row[c] == 0 and row[c + 4] == 0 else 0 for c in range(4)]
        for row in grid
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical adjacent two-panel NOR teaching grammar."""
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
    if width != 8:
        errors.append(f"input width must be 8 (4+4 adjacent panels), got {width}")
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
    if width != 8 or errors:
        return errors

    palette = {value for row in grid for value in row}
    if 4 in palette:
        errors.append("input must not contain answer color 4")

    facts = semantic_observables(grid)
    left_fg = facts["left_values"] - {0}
    right_fg = facts["right_values"] - {0}
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

    if not 1 <= counts["00"] <= 8:
        errors.append(f"aligned both-zero state 00 count must be in 1..8, got {counts['00']}")
    if counts["10"] < 1:
        errors.append("need at least one left-only state 10")
    if counts["01"] < 1:
        errors.append("need at least one right-only state 01")
    if counts["11"] < 1:
        errors.append("need at least one both-nonzero state 11")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the color-renamed canonical adjacent-panel manifold."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _predicate_rule(
    grid: list[list[int]],
    predicate: Callable[[int, int], bool],
) -> list[list[int]]:
    return [
        [4 if predicate(row[c], row[c + 4]) else 0 for c in range(4)]
        for row in grid
    ]


def _constant_zero(grid):
    return [[0 for _ in range(4)] for _row in grid]


def _left_zero(grid):
    return _predicate_rule(grid, lambda left, right: left == 0)


def _right_zero(grid):
    return _predicate_rule(grid, lambda left, right: right == 0)


def _occupancy_equal(grid):
    return _predicate_rule(grid, lambda left, right: (left == 0) == (right == 0))


def _occupancy_xor(grid):
    return _predicate_rule(grid, lambda left, right: (left == 0) != (right == 0))


def _both_nonzero(grid):
    return _predicate_rule(grid, lambda left, right: left != 0 and right != 0)


def _either_zero(grid):
    return _predicate_rule(grid, lambda left, right: left == 0 or right == 0)


def raw_value_equality(grid):
    """Canonical shortcut: mark raw-equal pairs instead of occupancy 00 pairs."""
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
# All real canonical pairs use different panel colors, so raw equality agrees
# with the intended rule on every one of them.  Generated same-color 11 cells
# are the necessary counterexample.
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
    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], dict[str, list[list[int]]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the occupancy-NOR rule")
            continue
        prepared.append(
            (
                pair["output"],
                {name: competitor(pair["input"]) for name, competitor in LESSON_COMPETITORS.items()},
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
