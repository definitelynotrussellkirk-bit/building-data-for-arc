"""Generator for ``arc_puzzle_bank_seventh21:H44``.

The 11x11 input is split by a full colour-9 row and column into four 5x5
panels.  The top pair demonstrates a 90-degree clockwise rotation.  The
bottom-left panel is a fresh query pattern and the bottom-right panel is blank;
the selected Racket rule rotates the query clockwise into that blank panel.

Ordinary draws use asymmetric one-to-three-colour patterns whose eight
dihedral images are distinct.  The query is also not a dihedral copy of the top template.  This
makes clockwise rotation distinguishable from copy, counter-clockwise,
180-degree, transpose, reflection, and "reuse the demonstrated answer"
shortcuts while remaining anchored exactly to the canonical panel grammar.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5df55418cdc1"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"  # restore the canonical four-panel analogy teaching grammar
RULE_HASH = "6627469a82cf"

SUMMARY = (
    "An 11x11 grid is divided by a full colour-9 middle row and column into "
    "four 5x5 panels.  Top-left -> top-right demonstrates a 90-degree "
    "clockwise rotation.  Rotate the independent bottom-left query clockwise "
    "into the blank bottom-right panel, preserving every other cell."
)

INVARIANTS = [
    "the grid is exactly 11x11 with a full colour-9 row 5 and column 5",
    "top-right is the 90-degree clockwise rotation of top-left",
    "top-left and bottom-left are non-empty and contain no divider colour 9",
    "bottom-right is empty in the input",
    "ordinary generated top and query patterns have eight distinct dihedral images",
    "ordinary generated query patterns are not dihedral copies of the top pattern",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PANEL_N = 5
_DIVIDER = 5
_PALETTE_LO, _PALETTE_HI = 1, 3
_CELLS_LO, _CELLS_HI = 3, 10

AXES = {
    "top_palette_size": {
        "type": "int",
        "default": "1 on odd sample indexes; 1..2 on even indexes",
        "valid": "1..3",
    },
    "query_palette_size": {
        "type": "int",
        "default": "1 on odd sample indexes; 2 on even indexes",
        "valid": "1..3",
    },
    "top_cells": {
        "type": "int",
        "default": "3..5 easy, 4..7 medium, 6..10 hard",
        "valid": "3..10",
    },
    "query_cells": {
        "type": "int",
        "default": "3..5 easy, 4..7 medium, 6..10 hard",
        "valid": "3..10",
    },
}

Grid = list[list[int]]
Cells = frozenset[tuple[int, int]]


SCHEDULE_PROFILES = ("multicolor_discriminator", "canonical_monochrome")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the two-residue lesson schedule; every two demos cover both roles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _panel(grid: Grid, top: int, left: int) -> Grid:
    return [row[left : left + _PANEL_N] for row in grid[top : top + _PANEL_N]]


def _rotate_cw(panel: Grid) -> Grid:
    return [list(row) for row in zip(*panel[::-1])]


def _rotate_ccw(panel: Grid) -> Grid:
    return [list(row) for row in zip(*panel)][::-1]


def _rotate_180(panel: Grid) -> Grid:
    return [list(reversed(row)) for row in reversed(panel)]


def _transpose(panel: Grid) -> Grid:
    return [list(row) for row in zip(*panel)]


def _flip_lr(panel: Grid) -> Grid:
    return [list(reversed(row)) for row in panel]


def _flip_ud(panel: Grid) -> Grid:
    return [list(row) for row in reversed(panel)]


def _paste_panel(grid: Grid, panel: Grid, top: int, left: int) -> Grid:
    out = [row[:] for row in grid]
    for r in range(_PANEL_N):
        for c in range(_PANEL_N):
            out[top + r][left + c] = panel[r][c]
    return out


def _cells_from_panel(panel: Grid) -> Cells:
    return frozenset(
        (r, c)
        for r in range(_PANEL_N)
        for c in range(_PANEL_N)
        if panel[r][c] != 0
    )


def _rot_cells(cells: Cells) -> Cells:
    return frozenset((c, _PANEL_N - 1 - r) for r, c in cells)


def _d4_images(cells: Cells) -> set[Cells]:
    def transform(cell_set: Cells, code: int) -> Cells:
        if code == 0:
            return cell_set
        if code == 1:
            return frozenset((r, _PANEL_N - 1 - c) for r, c in cell_set)
        if code == 2:
            return frozenset((_PANEL_N - 1 - r, c) for r, c in cell_set)
        if code == 3:
            return frozenset((c, _PANEL_N - 1 - r) for r, c in cell_set)
        if code == 4:
            return frozenset(
                (_PANEL_N - 1 - r, _PANEL_N - 1 - c) for r, c in cell_set
            )
        if code == 5:
            return frozenset((_PANEL_N - 1 - c, r) for r, c in cell_set)
        if code == 6:
            return frozenset((c, r) for r, c in cell_set)
        return frozenset(
            (_PANEL_N - 1 - c, _PANEL_N - 1 - r) for r, c in cell_set
        )

    return {transform(cells, code) for code in range(8)}


def _connected(cells: Cells) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(cells)


def _asymmetric_cells(rng, count: int, *, forbidden_orbit: set[Cells] | None = None) -> Cells:
    positions = [(r, c) for r in range(_PANEL_N) for c in range(_PANEL_N)]
    for _ in range(4000):
        cells = {rng.choice(positions)}
        while len(cells) < count:
            frontier = sorted({
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= r + dr < _PANEL_N
                and 0 <= c + dc < _PANEL_N
                and (r + dr, c + dc) not in cells
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        frozen = frozenset(cells)
        if len(frozen) != count or not _connected(frozen):
            continue
        orbit = _d4_images(frozen)
        if len(orbit) != 8:
            continue
        if forbidden_orbit is not None and frozen in forbidden_orbit:
            continue
        return frozen
    raise RuntimeError(f"no connected asymmetric {count}-cell 5x5 pattern found")


def _draw_axis_int(ctx, overrides: dict, label: str, lo: int, hi: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, {
            "top_palette_size": _PALETTE_LO,
            "query_palette_size": _PALETTE_LO,
            "top_cells": _CELLS_LO,
            "query_cells": _CELLS_LO,
        }[label], {
            "top_palette_size": _PALETTE_HI,
            "query_palette_size": _PALETTE_HI,
            "top_cells": _CELLS_HI,
            "query_cells": _CELLS_HI,
        }[label])
    return ctx.draw_int(label, lo, hi)


def _colored_pattern(cells: Cells, palette: list[int], rng) -> dict[tuple[int, int], int]:
    ordered = sorted(cells)
    rng.shuffle(ordered)
    colors = list(palette)
    rng.shuffle(colors)
    painted: dict[tuple[int, int], int] = {}
    for index, cell in enumerate(ordered):
        painted[cell] = colors[index] if index < len(colors) else rng.choice(colors)
    return painted


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        cell_lo, cell_hi = 3, 5
        palette_lo, palette_hi = 1, 2
    elif difficulty == "hard":
        cell_lo, cell_hi = 6, 10
        palette_lo, palette_hi = 1, 2
    else:
        cell_lo, cell_hi = 4, 7
        palette_lo, palette_hi = 1, 2

    if overrides.get("top_palette_size") is not None:
        top_palette_size = _draw_axis_int(
            ctx, overrides, "top_palette_size", palette_lo, palette_hi
        )
    elif sample_index % 2:
        top_palette_size = ctx.draw_int("top_palette_size", 1, 1)
    else:
        top_palette_size = ctx.draw_int("top_palette_size", palette_lo, palette_hi)

    if overrides.get("query_palette_size") is not None:
        query_palette_size = _draw_axis_int(
            ctx, overrides, "query_palette_size", palette_lo, palette_hi
        )
    else:
        scheduled_query_palette = 1 if sample_index % 2 else 2
        query_palette_size = ctx.draw_int(
            "query_palette_size", scheduled_query_palette, scheduled_query_palette
        )
    top_count = _draw_axis_int(ctx, overrides, "top_cells", cell_lo, cell_hi)
    query_count = _draw_axis_int(ctx, overrides, "query_cells", cell_lo, cell_hi)

    top_cells = _asymmetric_cells(ctx.draw_rng("top_pattern"), top_count)
    top_orbit = _d4_images(top_cells)
    query_cells = _asymmetric_cells(
        ctx.draw_rng("query_pattern"), query_count, forbidden_orbit=top_orbit
    )

    color_rng = ctx.draw_rng("palettes")
    all_colors = list(range(1, 9))
    top_palette = color_rng.sample(all_colors, top_palette_size)
    remaining = [color for color in all_colors if color not in top_palette]
    query_palette = color_rng.sample(remaining, query_palette_size)
    top_painted = _colored_pattern(top_cells, top_palette, ctx.draw_rng("top_colors"))
    query_painted = _colored_pattern(
        query_cells, query_palette, ctx.draw_rng("query_colors")
    )

    grid = full_grid(11, 11, 0)
    for i in range(11):
        grid[_DIVIDER][i] = 9
        grid[i][_DIVIDER] = 9

    for (r, c), color in top_painted.items():
        grid[r][c] = color
        grid[c][6 + (_PANEL_N - 1 - r)] = color
    for (r, c), color in query_painted.items():
        grid[r + 6][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid four-panel input grammar."""
    del difficulty, meta
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]
    if len(grid) != 11 or len(grid[0]) != 11:
        return [f"expected canonical 11x11 panel layout, got {len(grid)}x{len(grid[0])}"]

    errors: list[str] = []
    if any(grid[_DIVIDER][c] != 9 for c in range(11)):
        errors.append("row 5 must be a full colour-9 divider")
    if any(grid[r][_DIVIDER] != 9 for r in range(11)):
        errors.append("column 5 must be a full colour-9 divider")

    tl = _panel(grid, 0, 0)
    tr = _panel(grid, 0, 6)
    bl = _panel(grid, 6, 0)
    br = _panel(grid, 6, 6)
    if not any(value != 0 for row in tl for value in row):
        errors.append("top-left demonstration source is empty")
    if not any(value != 0 for row in bl for value in row):
        errors.append("bottom-left query source is empty")
    if any(value == 9 for panel in (tl, tr, bl, br) for row in panel for value in row):
        errors.append("divider colour 9 may not appear inside a panel")
    if tr != _rotate_cw(tl):
        errors.append("top-right must be the clockwise rotation of top-left")
    if any(value != 0 for row in br for value in row):
        errors.append("bottom-right query destination must be empty")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical-role predicate used by the linked semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    tl = _panel(grid, 0, 0)
    bl = _panel(grid, 6, 0)
    reasons: list[str] = []
    for name, panel in (("top-left", tl), ("bottom-left", bl)):
        colors = {value for row in panel for value in row if value != 0}
        if not (1 <= len(colors) <= 3):
            reasons.append(f"{name} source must use one to three nonzero colours")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    tl = _panel(grid, 0, 0)
    bl = _panel(grid, 6, 0)
    top_values = [value for row in tl for value in row if value != 0]
    query_values = [value for row in bl for value in row if value != 0]
    return {
        "top_palette_size": len(set(top_values)),
        "query_palette_size": len(set(query_values)),
        "top_cells": len(top_values),
        "query_cells": len(query_values),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python diagnostic mirror; the selected Racket rule remains authority."""
    return _paste_panel(grid, _rotate_cw(_panel(grid, 6, 0)), 6, 6)


def _with_query_transform(grid: Grid, transform: Callable[[Grid], Grid]) -> Grid:
    return _paste_panel(grid, transform(_panel(grid, 6, 0)), 6, 6)


def _rival_copy(grid: Grid) -> Grid:
    return _with_query_transform(grid, lambda panel: [row[:] for row in panel])


def _rival_ccw(grid: Grid) -> Grid:
    return _with_query_transform(grid, _rotate_ccw)


def _rival_180(grid: Grid) -> Grid:
    return _with_query_transform(grid, _rotate_180)


def _rival_transpose(grid: Grid) -> Grid:
    return _with_query_transform(grid, _transpose)


def _rival_flip_lr(grid: Grid) -> Grid:
    return _with_query_transform(grid, _flip_lr)


def _rival_flip_ud(grid: Grid) -> Grid:
    return _with_query_transform(grid, _flip_ud)


def _rival_reuse_top_answer(grid: Grid) -> Grid:
    return _paste_panel(grid, _panel(grid, 0, 6), 6, 6)


def _rival_monochrome_query(grid: Grid) -> Grid:
    panel = _panel(grid, 6, 0)
    colors = sorted({value for row in panel for value in row if value != 0})
    if not colors:
        return [row[:] for row in grid]
    color = colors[0]
    mono = [[color if value != 0 else 0 for value in row] for row in panel]
    return _paste_panel(grid, _rotate_cw(mono), 6, 6)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "copy_query": _rival_copy,
    "rotate_query_ccw": _rival_ccw,
    "rotate_query_180": _rival_180,
    "transpose_query": _rival_transpose,
    "flip_query_lr": _rival_flip_lr,
    "flip_query_ud": _rival_flip_ud,
    "reuse_top_answer": _rival_reuse_top_answer,
    "monochrome_query": _rival_monochrome_query,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_clockwise_demo(grid: Grid) -> bool:
    return not self_check(grid) and _panel(grid, 0, 6) == _rotate_cw(_panel(grid, 0, 0))


def _witness_query_dihedral_asymmetry(grid: Grid) -> bool:
    if self_check(grid):
        return False
    return len(_d4_images(_cells_from_panel(_panel(grid, 6, 0)))) == 8


def _witness_query_not_top_orbit(grid: Grid) -> bool:
    if self_check(grid):
        return False
    top = _cells_from_panel(_panel(grid, 0, 0))
    query = _cells_from_panel(_panel(grid, 6, 0))
    return query not in _d4_images(top)


def _witness_query_multicolor(grid: Grid) -> bool:
    if self_check(grid):
        return False
    colors = {value for row in _panel(grid, 6, 0) for value in row if value != 0}
    return len(colors) >= 2


def _witness_canonical_layout(grid: Grid) -> bool:
    return not strict_canonical_like(grid)


SEMANTIC_WITNESSES = {
    "clockwise_top_demo": _witness_clockwise_demo,
    "query_has_eight_dihedral_images": _witness_query_dihedral_asymmetry,
    "query_is_not_top_template": _witness_query_not_top_orbit,
    "query_is_multicolor": _witness_query_multicolor,
    "canonical_four_panel_layout": _witness_canonical_layout,
}
WITNESS_RIVALS = {
    "clockwise_top_demo": ["rotate_query_ccw", "rotate_query_180", "transpose_query"],
    "query_has_eight_dihedral_images": [
        "copy_query",
        "rotate_query_ccw",
        "rotate_query_180",
        "transpose_query",
        "flip_query_lr",
        "flip_query_ud",
    ],
    "query_is_not_top_template": ["reuse_top_answer"],
    "query_is_multicolor": ["monochrome_query"],
    "canonical_four_panel_layout": ["copy_query"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any episode where a named simple rival survives the demos."""
    reasons: list[str] = []
    for index, item in enumerate([*demos, query]):
        label = f"demo {index}" if index < len(demos) else "query"
        input_grid = item.get("input")
        output_grid = item.get("output")
        grammar_errors = self_check(input_grid)
        if grammar_errors:
            reasons.append(f"{label} input is outside the teaching grammar: {grammar_errors}")
            continue
        if rule_mirror(input_grid) != output_grid:
            reasons.append(f"{label} output is not the clockwise bottom-panel rotation")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons
