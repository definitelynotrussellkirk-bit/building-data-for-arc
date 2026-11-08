"""Generator for arc_puzzle_bank_twelfth21:M78 — drop a rigid ensemble.

The maroon (9) horizontal segment is a support line.  Every other colored
cell belongs to one rigid ensemble, even when the cells form several separated
components or use several colors.  Translate that entire ensemble straight
down by one shared delta so its lowest occupied row is immediately above the
support row.  The support segment, colors, shapes, columns, and relative offsets
between all colored cells are preserved.

The scheduled curriculum deliberately alternates canonical one-object anchors
with multi-component, multi-color counterexamples.  Those controls rule out the
three strongest shortcuts admitted by the canonical examples alone: dropping
each component independently, moving only the modal color, or moving only the
largest component.
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fb413112b7c8"
TASK_ID = "fb413112b7c8"
VERSION = "3.0.0"
RULE_HASH = "881504b5004d"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A rectangular 0-background grid contains one contiguous horizontal maroon "
    "(9) support segment in the lower half and 3-8 non-maroon colored cells "
    "strictly above it. Treat every non-0/non-9 cell as one rigid ensemble, "
    "including separated components and multiple colors. Shift the complete "
    "ensemble straight down by one shared delta until its global bottom row is "
    "exactly one row above the support. Preserve the support, every color, every "
    "column, and all relative offsets. Scheduled multi-component/multi-color "
    "lessons distinguish this from dropping components independently or moving "
    "only one selected component/color."
)

INVARIANTS = [
    "background is 0 and support color is 9",
    "exactly one contiguous all-{0,9} support row containing at least four 9 cells",
    "the support row is in the lower half and every colored cell is strictly above it",
    "at least one full empty row separates the ensemble bottom from the support",
    "all 3-8 colored cells form one rigid ensemble under the rule, regardless of connectivity or color",
]

PALETTE_KINDS = ("warm", "cool", "varied")
PALETTES = {
    "warm": (1, 2, 7, 8),
    "cool": (3, 5, 6, 8),
    "varied": (4, 1, 6, 2),
}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/banded", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "scheduled/banded", "valid": "8..22"},
    "palette_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(PALETTE_KINDS),
    },
    "total_cells": {"type": "int", "default": "3-4 anchors / 6-8 controls", "valid": "3..8"},
    "n_pieces": {"type": "int", "default": "1 anchors / 2-3 controls", "valid": "1..3"},
    "n_distinct_colors": {"type": "int", "default": "1 anchors / 2-3 controls", "valid": "1..3"},
    "gap_rows": {"type": "int", "default": "2..5", "valid": "1..5"},
    "support_inset": {
        "type": "int",
        "default": "left inset of support segment",
        "valid": "0..3",
    },
}

# Every Cartesian boundary combination above is constructible.  Declaring an
# explicit empty matrix opts into the strict override-rejection policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "canonical_anchor_a",
    "joint_counterexample_a",
    "joint_counterexample_b",
    "canonical_anchor_b",
)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Four-slot schedule; every four-demo window contains both controls."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_int(ctx, name: str, default: tuple[int, int], valid: tuple[int, int]) -> int:
    return ctx.draw_int(name, *(valid if name in ctx.overrides else default))


def _draw_choice(ctx, name: str, default: tuple[str, ...], valid: tuple[str, ...]) -> str:
    return ctx.draw_choice(name, valid if name in ctx.overrides else default)


def _component_sizes(total_cells: int, n_pieces: int) -> list[int]:
    """Make the lowest component deliberately small when there is a rival."""
    if n_pieces == 1:
        return [total_cells]
    sizes = [1] + [0] * (n_pieces - 1)
    for i in range(total_cells - 1):
        sizes[1 + (i % (n_pieces - 1))] += 1
    return sizes


def _compact_shape(size: int, *, mirror: bool) -> list[tuple[int, int]]:
    """A connected one/two-row shape, normalized with its bottom at row 0."""
    if size == 1:
        return [(0, 0)]
    width = (size + 1) // 2
    bottom_count = min(width, size)
    top_count = size - bottom_count
    cells = [(0, c) for c in range(bottom_count)]
    if top_count:
        start = width - top_count if mirror else 0
        cells.extend([(-1, start + c) for c in range(top_count)])
    return sorted(cells)


def _support_rows(grid) -> list[int]:
    return [
        r
        for r, row in enumerate(grid)
        if any(value == 9 for value in row) and all(value in (0, 9) for value in row)
    ]


def _colored_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def _components(grid) -> list[list[tuple[int, int, int]]]:
    cells = {(r, c): value for r, c, value in _colored_cells(grid)}
    unseen = set(cells)
    result: list[list[tuple[int, int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = []
        while queue:
            r, c = queue.popleft()
            component.append((r, c, cells[(r, c)]))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
        result.append(sorted(component))
    return sorted(result, key=lambda comp: (min(r for r, _, _ in comp), min(c for _, c, _ in comp)))


def _analyze(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    h, w = len(grid), len(grid[0])
    invalid = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        return {"errors": [f"cell values must be integer ARC colors 0..9, got {invalid}"]}

    support_rows = _support_rows(grid)
    if len(support_rows) != 1:
        errors.append(f"expected exactly one all-0/9 support row containing 9, got {len(support_rows)}")
        return {"errors": errors, "h": h, "w": w}
    support_row = support_rows[0]
    if any(grid[r][c] == 9 for r in range(h) for c in range(w) if r != support_row):
        errors.append("color 9 appears outside the support row")

    support_cols = [c for c, value in enumerate(grid[support_row]) if value == 9]
    if len(support_cols) < 4:
        errors.append("support segment must contain at least four 9 cells")
    if support_cols and support_cols != list(range(support_cols[0], support_cols[-1] + 1)):
        errors.append("support 9 cells must form one contiguous segment")

    colored = _colored_cells(grid)
    if not colored:
        errors.append("no droppable colored cells")
        return {
            "errors": errors,
            "h": h,
            "w": w,
            "support_row": support_row,
            "support_cols": support_cols,
        }
    if any(r >= support_row for r, _, _ in colored):
        errors.append("every colored cell must lie strictly above the support row")
    max_row = max(r for r, _, _ in colored)
    gap_rows = support_row - max_row - 1
    if gap_rows < 1:
        errors.append("at least one empty gap row must separate blob and support")

    components = _components(grid)
    return {
        "errors": errors,
        "h": h,
        "w": w,
        "support_row": support_row,
        "support_cols": support_cols,
        "support_inset": support_cols[0] if support_cols else None,
        "colored": colored,
        "total_cells": len(colored),
        "n_distinct_colors": len({value for _, _, value in colored}),
        "gap_rows": gap_rows,
        "components": components,
        "n_pieces": len(components),
        "component_bottoms": [max(r for r, _, _ in comp) for comp in components],
        "component_sizes": [len(comp) for comp in components],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    h = analysis["h"]
    if not 8 <= h <= 20 or not 8 <= analysis["w"] <= 22:
        errors.append("teaching grids must stay within the declared 8..20 by 8..22 envelope")
    if analysis["support_row"] < h // 2:
        errors.append("support row must be in the lower half")
    if not 3 <= analysis["total_cells"] <= 8:
        errors.append("expected 3..8 colored cells")
    if not 1 <= analysis["n_pieces"] <= 3:
        errors.append("expected 1..3 colored connected components")
    if not 1 <= analysis["n_distinct_colors"] <= 3:
        errors.append("expected 1..3 distinct non-support colors")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The complete teaching grammar is a bounded canonical extension."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "total_cells": analysis["total_cells"],
        "n_pieces": analysis["n_pieces"],
        "n_distinct_colors": analysis["n_distinct_colors"],
        "gap_rows": analysis["gap_rows"],
        "support_inset": analysis["support_inset"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    if profile == "canonical_anchor_a":
        h_default, w_default = (8, 8), (8, 8)
        cells_default = (3, 3)
        pieces_default = (1, 1)
        colors_default = (1, 1)
        gap_default = (3, 3)
        inset_default = (1, 1)
        palette_default = ("varied",)
    elif profile == "canonical_anchor_b":
        h_default, w_default = (9, 9), (10, 10)
        cells_default = (4, 4)
        pieces_default = (1, 1)
        colors_default = (1, 1)
        gap_default = (5, 5)
        inset_default = (1, 1)
        palette_default = ("cool",)
    else:
        ranges = {
            "easy": ((9, 11), (10, 13)),
            "medium": ((11, 15), (12, 17)),
            "hard": ((15, 20), (16, 22)),
        }
        h_default, w_default = ranges[band]
        cells_default = (6, 8)
        pieces_default = (2, 3)
        colors_default = (2, 3)
        gap_default = (2, 4)
        inset_default = (0, 2)
        palette_default = PALETTE_KINDS

    h = _draw_int(ctx, "grid_h", h_default, (8, 20))
    w = _draw_int(ctx, "grid_w", w_default, (8, 22))
    total_cells = _draw_int(ctx, "total_cells", cells_default, (3, 8))
    n_pieces = _draw_int(ctx, "n_pieces", pieces_default, (1, 3))
    n_colors = _draw_int(ctx, "n_distinct_colors", colors_default, (1, 3))
    gap_rows = _draw_int(ctx, "gap_rows", gap_default, (1, 5))
    support_inset = _draw_int(ctx, "support_inset", inset_default, (0, 3))
    palette_kind = _draw_choice(ctx, "palette_kind", palette_default, PALETTE_KINDS)

    sizes = _component_sizes(total_cells, n_pieces)
    layout_rng = ctx.draw_rng("layout")
    shapes = [
        _compact_shape(size, mirror=bool((layout_rng.randrange(2) + i) % 2))
        for i, size in enumerate(sizes)
    ]
    widths = [max(c for _, c in shape) + 1 for shape in shapes]
    footprint_width = sum(widths) + (n_pieces - 1)
    if footprint_width > w:
        raise AssertionError(
            f"constructive bounds bug: footprint {footprint_width} exceeds width {w}"
        )

    # Prefer both canonical support positions when feasible.  The final row is
    # always feasible at the declared boundaries because every shape is <=2 rows.
    preferred_support = h - 2 if profile in {"canonical_anchor_a", "joint_counterexample_a"} else h - 1
    support_row = preferred_support
    target_bottom = support_row - gap_rows - 1
    min_same_bottom = max((-min(r for r, _ in shape)) for shape in shapes)
    if target_bottom < min_same_bottom:
        support_row = h - 1
        target_bottom = support_row - gap_rows - 1
    if target_bottom < min_same_bottom:
        raise AssertionError("declared grid/gap bounds cannot fit the colored ensemble")

    can_stagger = n_pieces > 1 and all(
        target_bottom - 1 + min(r for r, _ in shape) >= 0 for shape in shapes[1:]
    )
    bottoms = [target_bottom] + [target_bottom - 1 if can_stagger else target_bottom] * (n_pieces - 1)

    horizontal_slack = w - footprint_width
    start_col = layout_rng.randint(0, horizontal_slack) if horizontal_slack else 0
    component_cells: list[list[tuple[int, int]]] = []
    cursor = start_col
    for shape, width, bottom in zip(shapes, widths, bottoms):
        placed = [(bottom + dr, cursor + dc) for dr, dc in shape]
        component_cells.append(placed)
        cursor += width + 1

    grid = full_grid(h, w, 0)
    for c in range(support_inset, w - 1):
        grid[support_row][c] = 9

    palette = PALETTES[palette_kind][:n_colors]
    ordered_cells = [cell for component in component_cells for cell in component]
    for i, (r, c) in enumerate(ordered_cells):
        grid[r][c] = palette[i % n_colors]

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "total_cells": total_cells,
        "n_pieces": n_pieces,
        "n_distinct_colors": n_colors,
        "gap_rows": gap_rows,
        "support_inset": support_inset,
    }
    if any(observed[key] != value for key, value in expected.items()):
        raise AssertionError(f"constructive override mismatch: expected={expected}, observed={observed}")
    return grid


def _blank_with_support(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9:
                out[r][c] = 9
    return out


def _identity(grid):
    return copy.deepcopy(grid)


def _fixed_one_row_drop(grid):
    out = _blank_with_support(grid)
    h = len(grid)
    for r, c, value in _colored_cells(grid):
        rr = min(h - 1, r + 1)
        out[rr][c] = value
    return out


def _independent_component_drop(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return copy.deepcopy(grid)
    out = _blank_with_support(grid)
    floor = analysis["support_row"] - 1
    for component in analysis["components"]:
        delta = floor - max(r for r, _, _ in component)
        for r, c, value in component:
            out[r + delta][c] = value
    return out


def _move_selected_only(grid, selected: list[tuple[int, int, int]]):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return copy.deepcopy(grid)
    selected_positions = {(r, c) for r, c, _ in selected}
    out = copy.deepcopy(grid)
    for r, c in selected_positions:
        out[r][c] = 0
    delta = analysis["support_row"] - 1 - max(r for r, _, _ in analysis["colored"])
    for r, c, value in selected:
        out[r + delta][c] = value
    return out


def _modal_color_only(grid):
    colored = _colored_cells(grid)
    if not colored:
        return copy.deepcopy(grid)
    counts = Counter(value for _, _, value in colored)
    modal = counts.most_common(1)[0][0]
    return _move_selected_only(grid, [cell for cell in colored if cell[2] == modal])


def _largest_component_only(grid):
    components = _components(grid)
    if not components:
        return copy.deepcopy(grid)
    largest = max(components, key=lambda comp: (len(comp), -min(c for _, c, _ in comp)))
    return _move_selected_only(grid, largest)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "fixed_one_row_drop": _fixed_one_row_drop,
    "independent_component_drop": _independent_component_drop,
    "modal_color_only": _modal_color_only,
    "largest_component_only": _largest_component_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "independent_component_drop": _independent_component_drop,
    "modal_color_only": _modal_color_only,
    "largest_component_only": _largest_component_only,
}


def _valid_analysis(grid) -> dict | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _non_identity(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["gap_rows"] >= 1)


def _gap_exceeds_one(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["gap_rows"] > 1)


def _unequal_component_bottoms(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["n_pieces"] >= 2
        and len(set(analysis["component_bottoms"])) >= 2
    )


def _multiple_colors(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["n_distinct_colors"] >= 2)


def _smallest_component_is_lowest(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis or analysis["n_pieces"] < 2:
        return False
    lowest = max(analysis["component_bottoms"])
    low_sizes = [
        size
        for size, bottom in zip(analysis["component_sizes"], analysis["component_bottoms"])
        if bottom == lowest
    ]
    return min(low_sizes) < max(analysis["component_sizes"])


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "non_identity_rigid_drop": _non_identity,
    "gap_refutes_fixed_one_row": _gap_exceeds_one,
    "unequal_component_bottoms": _unequal_component_bottoms,
    "multiple_colors_preserved": _multiple_colors,
    "small_low_component_refutes_largest_only": _smallest_component_is_lowest,
}
WITNESS_RIVALS = {
    "non_identity_rigid_drop": ["identity"],
    "gap_refutes_fixed_one_row": ["fixed_one_row_drop"],
    "unequal_component_bottoms": ["independent_component_drop"],
    "multiple_colors_preserved": ["modal_color_only"],
    "small_low_component_refutes_largest_only": ["largest_component_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every named rival must be contradicted by at least one demonstration."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a different query output"
                )
    return reasons
