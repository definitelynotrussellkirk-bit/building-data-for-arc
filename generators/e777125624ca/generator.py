"""Generator for ARC task 1b2d62fb (content hash e777125624ca).

The input is an ``h x 7`` grid containing two aligned 3-column panels and a
one-column separator.  The output is ``h x 3`` and marks an aligned position
with color 8 exactly when both panel cells are zero; every other occupancy
state maps to zero.

Ordinary generated examples contain all four aligned occupancy states
``00, 10, 01, 11``.  This prevents a lesson from collapsing into a one-panel
complement, equality test, OR, or count-only shortcut while keeping the
canonical width, palette roles, and per-cell NOR rule exact.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e777125624ca"
VERSION = "2.1.0"  # observable layout axis + task-linked semantic contract
TASK_ID = "e777125624ca"
RULE_HASH = "81c356b17e4e"
SUMMARY = (
    "Two aligned 3-column binary panels, separated by one nonzero marker "
    "column.  Output color 8 appears exactly at aligned 00 positions; 10, "
    "01, and 11 positions all map to 0.  Normal draws contain every state, "
    "exclude answer color 8 from the input, and vary height, colors, count, "
    "and spatial layout."
)

INVARIANTS = [
    "input is 3..18 rows by 7 columns (3 left + separator + 3 right)",
    "the separator is one nonzero non-8 color distinct from the panel color",
    "both panels use only 0 and one shared nonzero non-8 foreground color",
    "there are 1..6 aligned 00 cells and at least one 11 cell",
    "at least one one-sided 10 or 01 cell is present",
]

LAYOUTS = ("random", "cluster", "diagonal", "border", "stripes", "checker")
# The first three lexicographic non-00 cells carry a permutation of the three
# NOR-negative states.  There are exactly six permutations, so the requested
# layout remains recoverable from the returned grid even when two spatial
# ordering heuristics happen to choose the same 00 mask at a small count.
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
DEGENERATE_TEXTURES = ("no_both_zero", "all_both_zero", "same_panels")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 3..18",
        "valid": "3..18",
    },
    "fg_color": {
        "type": "color",
        "default": "rng (not 0 or 8)",
        "valid": "1..9 (≠8)",
    },
    "sep_color": {
        "type": "color",
        "default": "rng (not 0, 8, or fg_color)",
        "valid": "1..9 (≠8)",
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


def _normalize_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Normalize legacy aliases and reject unknown/conflicting controls."""
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
    if texture is not None and set(values) - {"grid_h", "fg_color", "sep_color"}:
        raise ValueError("degenerate textures cannot be combined with count/layout controls")
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
        return 1, 3
    if difficulty == "hard":
        return 3, 6
    if difficulty in (None, "medium"):
        return 2, 5
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_height(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "grid_h" in values:
        return ctx.draw_int("grid_h", 3, 18)
    # Preserve a visible canonical-scale anchor without collapsing the wider
    # distribution: every third easy/medium sample is exactly 5 rows, while
    # the remaining samples use the full difficulty band.
    if difficulty in (None, "easy", "medium") and ctx.sample_index % 3 == 0:
        return ctx.draw_int("grid_h", 5, 5)
    lo, hi = _height_bounds(difficulty)
    return ctx.draw_int("grid_h", lo, hi)


def _draw_count(ctx, values: dict[str, Any], difficulty: str | None) -> int:
    if "both_zero_count" in values:
        return ctx.draw_int("both_zero_count", 1, 6)
    lo, hi = _count_bounds(difficulty)
    return ctx.draw_int("both_zero_count", lo, hi)


def _draw_colors(ctx, values: dict[str, Any]) -> tuple[int, int]:
    requested_fg = values.get("fg_color")
    requested_sep = values.get("sep_color")
    if requested_fg is not None and requested_sep is not None:
        if int(requested_fg) == int(requested_sep):
            raise ValueError("fg_color and sep_color must differ")

    if requested_sep is not None and requested_fg is None:
        fg_exclude = {0, 8, int(requested_sep)}
    else:
        fg_exclude = {0, 8}
    fg = ctx.draw_color("fg_color", exclude=fg_exclude)
    sep = ctx.draw_color("sep_color", exclude={0, 8, fg})
    return fg, sep


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
        offset = rng.randrange(3)
        tie = {cell: rng.random() for cell in cells}
        return sorted(
            cells,
            key=lambda cell: (
                (cell[1] - cell[0] - offset) % 3,
                tie[cell],
            ),
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
        return sorted(cells, key=lambda cell: ((cell[0] + cell[1] - parity) % 2, tie[cell]))
    raise ValueError(f"unknown layout {layout!r}")


def _build_scene(
    h: int,
    fg: int,
    sep: int,
    both_zero_count: int,
    layout: str,
    rng,
) -> list[list[int]]:
    cells = _ordered_cells(h, layout, rng)
    both_zero = set(cells[:both_zero_count])
    remaining = sorted(set(cells) - both_zero)
    if len(remaining) < 3:
        raise ValueError("both_zero_count leaves no room for all NOR-negative states")

    states: dict[tuple[int, int], str] = {}
    for cell, state in zip(remaining[:3], LAYOUT_SIGNATURES[layout]):
        states[cell] = state
    for cell in remaining[3:]:
        states[cell] = rng.choice(("10", "01", "11", "11"))

    grid = full_grid(h, 7, 0)
    for r in range(h):
        grid[r][3] = sep
    for r, c in cells:
        if (r, c) in both_zero:
            continue
        state = states[(r, c)]
        if state[0] == "1":
            grid[r][c] = fg
        if state[1] == "1":
            grid[r][c + 4] = fg
    return grid


def _draw_degenerate(name: str, h: int, fg: int, sep: int, rng) -> list[list[int]]:
    grid = full_grid(h, 7, 0)
    for r in range(h):
        grid[r][3] = sep
    if name == "no_both_zero":
        for r in range(h):
            for c in range(3):
                grid[r][c] = fg
                grid[r][c + 4] = 0 if rng.random() < 0.5 else fg
        return grid
    if name == "all_both_zero":
        return grid
    if name == "same_panels":
        for r in range(h):
            for c in range(3):
                value = fg if rng.random() < 0.5 else 0
                grid[r][c] = value
                grid[r][c + 4] = value
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
    h = _draw_height(ctx, values, difficulty)
    fg, sep = _draw_colors(ctx, values)
    rng = ctx.draw_rng("scene")
    if degenerate is not None:
        return _draw_degenerate(degenerate, h, fg, sep, rng)

    both_zero_count = _draw_count(ctx, values, difficulty)
    layout = ctx.draw_choice("layout", LAYOUTS)
    return _build_scene(h, fg, sep, both_zero_count, layout, rng)


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the exact semantic state counts and palette roles from a grid."""
    h = len(grid)
    sep_values = {row[3] for row in grid} if grid and all(len(row) == 7 for row in grid) else set()
    panel_values = {
        grid[r][c]
        for r in range(h)
        for c in (0, 1, 2, 4, 5, 6)
    } if grid and all(len(row) == 7 for row in grid) else set()
    fg_values = panel_values - {0}
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    nonzero_states: list[tuple[tuple[int, int], str]] = []
    if grid and all(len(row) == 7 for row in grid):
        for r in range(h):
            for c in range(3):
                key = ("1" if grid[r][c] != 0 else "0") + (
                    "1" if grid[r][c + 4] != 0 else "0"
                )
                counts[key] += 1
                if key != "00":
                    nonzero_states.append(((r, c), key))
    signature = tuple(state for _cell, state in nonzero_states[:3])
    return {
        "grid_h": h,
        "sep_values": sep_values,
        "fg_values": fg_values,
        "state_counts": counts,
        "layout": SIGNATURE_LAYOUTS.get(signature),
        "layout_signature": signature,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Return every exact declared axis recoverable from the returned grid."""
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
        "fg_color": next(iter(facts["fg_values"])),
        "sep_color": next(iter(facts["sep_values"])),
        "both_zero_count": facts["state_counts"]["00"],
        "layout": layout,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    return [
        [8 if row[c] == 0 and row[c + 4] == 0 else 0 for c in range(3)]
        for row in grid
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical two-panel NOR teaching grammar."""
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
        errors.append(f"input width must be 7 (3+separator+3), got {width}")
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

    facts = semantic_observables(grid)
    sep_values = facts["sep_values"]
    fg_values = facts["fg_values"]
    counts = facts["state_counts"]

    if len(sep_values) != 1 or 0 in sep_values or 8 in sep_values:
        errors.append(
            "separator column must be one nonzero non-8 color, got "
            f"{sorted(sep_values)}"
        )
    if len(fg_values) != 1 or 8 in fg_values:
        errors.append(
            "panels must use exactly 0 and one shared nonzero non-8 color, got "
            f"{sorted({0} | fg_values)}"
        )
    elif sep_values and next(iter(fg_values)) in sep_values:
        errors.append("separator color must differ from panel foreground color")

    if not 1 <= counts["00"] <= 6:
        errors.append(
            "aligned both-zero count must be in 1..6, got "
            f"{counts['00']}"
        )
    if counts["11"] < 1:
        errors.append("need at least one aligned both-nonzero cell")
    if counts["10"] + counts["01"] < 1:
        errors.append("need at least one one-sided occupied cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the canonical color-renamed two-panel NOR manifold."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _lawful_facts(grid) -> dict[str, Any] | None:
    return None if self_check(grid) else semantic_observables(grid)


def _has_state(state: str):
    return lambda grid: (
        (facts := _lawful_facts(grid)) is not None
        and facts["state_counts"][state] >= 1
    )


SEMANTIC_WITNESSES = {
    "both_zero_positive_branch": _has_state("00"),
    "left_only_negative_branch": _has_state("10"),
    "right_only_negative_branch": _has_state("01"),
    "both_nonzero_negative_branch": _has_state("11"),
}


def _competitor_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    """Plausible local binary rules that the four-state grammar must refute."""
    predicates = {
        "constant_zero": lambda left, right: False,
        "left_zero": lambda left, right: not left,
        "right_zero": lambda left, right: not right,
        "equal": lambda left, right: left == right,
        "xor": lambda left, right: left != right,
        "both_nonzero": lambda left, right: left and right,
        "either_zero": lambda left, right: not (left and right),
    }
    outputs: dict[str, list[list[int]]] = {}
    for name, predicate in predicates.items():
        outputs[name] = [
            [
                8 if predicate(row[c] != 0, row[c + 4] != 0) else 0
                for c in range(3)
            ]
            for row in grid
        ]
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival fits every demo but changes the query."""
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
            reasons.append(f"demo {index} output disagrees with the NOR rule")
            continue
        prepared.append((pair["output"], _competitor_outputs(pair["input"])))
    if reasons:
        return sorted(set(reasons))

    if not isinstance(query, dict) or "input" not in query:
        return ["query is malformed"]
    query_errors = self_check(query["input"])
    if query_errors:
        return ["query input is invalid: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query["input"])
    query_competitors = _competitor_outputs(query["input"])

    for name in sorted(query_competitors):
        survives = all(competitors[name] == output for output, competitors in prepared)
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo but changes the query"
            )
    return reasons
