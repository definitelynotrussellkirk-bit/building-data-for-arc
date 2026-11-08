"""Generator for ARC task ebdf2e943f3f: complete monochrome 2x2 corners.

Each lawful input contains two to four non-overlapping 2x2 windows.  Every
window has exactly three cells of one non-zero colour and one zero corner.
Some same-colour windows are edge-connected so that object-level shortcuts do
not replace the intended local window scan.  The output fills every missing
corner with the colour already present in that window.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ebdf2e943f3f"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "59a5d1f77f1b"

SUMMARY = (
    "Find every 2x2 window containing exactly three equal non-zero cells and "
    "one zero cell. Fill that zero corner with the shared colour, preserving "
    "all other cells."
)

INVARIANTS = [
    "background is colour 0",
    "the input contains exactly two to four qualifying 2x2 windows",
    "each qualifying window has one missing corner and three equal non-zero cells",
    "every non-zero input cell belongs to exactly one qualifying window",
    "qualifying windows do not share painted cells",
    "some generated scenes connect two same-colour windows edge-to-edge",
]

# These are the only exact caller-facing controls.  All three can be recovered
# directly from the returned grid by observe_overrides().
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 5..14", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 6..16", "valid": "6..16"},
    "n_blocks": {"type": "int", "default": "difficulty-weighted 2..4", "valid": "2..4"},
}

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

# Canonical sizes are intentionally oversampled while every declared boundary
# remains a valid exact override in every difficulty band.
_HEIGHT_OPTIONS = (5, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14)
_WIDTH_OPTIONS = (6, 6, 6, 7, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _qualifying_windows(grid: Any) -> list[dict[str, Any]]:
    """Return every 2x2 window matching the canonical three-of-one-colour cue."""
    height, width = len(grid), len(grid[0])
    windows: list[dict[str, Any]] = []
    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) != 3 or len(set(nonzero)) != 1 or values.count(0) != 1:
                continue
            missing_index = values.index(0)
            windows.append(
                {
                    "row": row,
                    "col": col,
                    "color": nonzero[0],
                    "missing_index": missing_index,
                    "missing_cell": cells[missing_index],
                    "painted_cells": tuple(
                        cell for index, cell in enumerate(cells) if index != missing_index
                    ),
                }
            )
    return windows


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors, "windows": []}

    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 14:
        errors.append(f"height must be in 5..14, found {height}")
    if not 6 <= width <= 16:
        errors.append(f"width must be in 6..16, found {width}")

    windows = _qualifying_windows(grid)
    if not 2 <= len(windows) <= 4:
        errors.append(f"expected 2-4 qualifying 2x2 windows, found {len(windows)}")

    coverage: dict[tuple[int, int], int] = {}
    for window in windows:
        for cell in window["painted_cells"]:
            coverage[cell] = coverage.get(cell, 0) + 1

    nonzero_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    covered_cells = set(coverage)
    stray = sorted(nonzero_cells - covered_cells)
    if stray:
        errors.append(f"non-zero cells outside qualifying windows: {stray[:4]}")
    overlap = sorted(cell for cell, count in coverage.items() if count != 1)
    if overlap:
        errors.append(f"painted cells belong to multiple qualifying windows: {overlap[:4]}")

    missing_cells = [window["missing_cell"] for window in windows]
    if len(set(missing_cells)) != len(missing_cells):
        errors.append("two qualifying windows claim the same missing corner")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "windows": windows,
        "nonzero_cells": nonzero_cells,
        "colors": {window["color"] for window in windows},
        "missing_indices": {window["missing_index"] for window in windows},
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blocks": len(analysis["windows"]),
    }


def rule_mirror(grid):
    """Independent Python mirror for focused tests; Racket remains authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for window in _qualifying_windows(grid):
        row, col = window["missing_cell"]
        output[row][col] = window["color"]
    return output


def _same_colour_component(grid, start: tuple[int, int]) -> set[tuple[int, int]]:
    """Return the 4-connected component matching the colour at ``start``."""
    height, width = len(grid), len(grid[0])
    color = grid[start[0]][start[1]]
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + drow, col + dcol)
            if (
                0 <= nxt[0] < height
                and 0 <= nxt[1] < width
                and nxt not in seen
                and grid[nxt[0]][nxt[1]] == color
            ):
                seen.add(nxt)
                stack.append(nxt)
    return seen


def _isolated_l_components_only(grid):
    """Plausible rival: complete only isolated three-cell monochrome Ls."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    component_sizes: dict[tuple[int, int], int] = {}
    for window in _qualifying_windows(grid):
        anchor = window["painted_cells"][0]
        if anchor not in component_sizes:
            component = _same_colour_component(grid, anchor)
            size = len(component)
            for cell in component:
                component_sizes[cell] = size
        if component_sizes[anchor] == 3:
            row, col = window["missing_cell"]
            output[row][col] = window["color"]
    return output


SEMANTIC_RIVALS = {"isolated_l_components_only": _isolated_l_components_only}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid) -> list[str]:
    """This generator's lawful grammar is the task-linked canonical manifold."""
    return self_check(grid)


def _witness_connected_same_colour_windows(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and rule_mirror(grid) != _isolated_l_components_only(grid)
    )


def _witness_missing_corner(index: int):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and index in analysis["missing_indices"]

    return witness


def _witness_reused_colour(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len(analysis["colors"]) < len(analysis["windows"])
    )


def _witness_distinct_colours(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len(analysis["colors"]) == len(analysis["windows"])
    )


SEMANTIC_WITNESSES = {
    "connected_same_colour_windows": _witness_connected_same_colour_windows,
    "missing_top_left": _witness_missing_corner(0),
    "missing_top_right": _witness_missing_corner(1),
    "missing_bottom_left": _witness_missing_corner(2),
    "missing_bottom_right": _witness_missing_corner(3),
    "reused_block_colour": _witness_reused_colour,
    "distinct_block_colours": _witness_distinct_colours,
}

WITNESS_RIVALS = {
    "connected_same_colour_windows": ["isolated_l_components_only"],
}

BRANCH_WITNESSES = {
    "missing_top_left",
    "missing_top_right",
    "missing_bottom_left",
    "missing_bottom_right",
    "reused_block_colour",
    "distinct_block_colours",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that refute fixed-corner and colour shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    seen_corners: set[int] = set()
    saw_reused = False
    saw_distinct = False
    saw_multi_corner_scene = False
    saw_connected_same_colour = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not complete-all-qualifying-windows")
        seen_corners.update(analysis["missing_indices"])
        saw_multi_corner_scene |= len(analysis["missing_indices"]) >= 2
        saw_reused |= len(analysis["colors"]) < len(analysis["windows"])
        saw_distinct |= len(analysis["colors"]) == len(analysis["windows"])
        saw_connected_same_colour |= _witness_connected_same_colour_windows(
            demo["input"]
        )

    if seen_corners != {0, 1, 2, 3}:
        reasons.append(
            "demonstrations do not cover all four missing-corner orientations"
        )
    if not saw_multi_corner_scene:
        reasons.append("no demonstration requires completing different corners together")
    if not saw_reused:
        reasons.append("no demonstration refutes one-distinct-colour-per-window shortcuts")
    if not saw_distinct:
        reasons.append("no demonstration shows independent colours across windows")
    if not saw_connected_same_colour:
        reasons.append(
            "no demonstration refutes the isolated-L-component shortcut"
        )
    return reasons


def _valid_lattices(height: int, width: int, target: int):
    options: list[tuple[list[int], list[int]]] = []
    for row_offset in range(3):
        rows = list(range(row_offset, height - 1, 3))
        for col_offset in range(3):
            cols = list(range(col_offset, width - 1, 3))
            if len(rows) * len(cols) >= target:
                options.append((rows, cols))
    return options


_CONNECTED_PATTERN_CYCLES = {
    "horizontal": (
        ((0, 3), (2, 1)),
        ((2, 1), (0, 3)),
    ),
    "vertical": (
        ((0, 2), (1, 3)),
        ((3, 1), (2, 0)),
    ),
}


def _spaced_positions(length: int, needed: int, layout_rng) -> list[int]:
    options = [
        list(range(offset, length - 1, 3))
        for offset in range(3)
        if len(range(offset, length - 1, 3)) >= needed
    ]
    if not options:
        raise ValueError(f"no {needed}-slot spaced layout in extent {length}")
    positions = list(layout_rng.choice(options))
    layout_rng.shuffle(positions)
    return positions[:needed]


def _connected_layout(height: int, width: int, target: int, layout_rng, sample_index: int):
    """Place one same-colour connected pair plus zero to two isolated windows."""
    remaining = target - 2
    cycle = sample_index // 4
    horizontal = cycle % 2 == 0
    direction = "horizontal" if horizontal else "vertical"
    phase = (cycle // 2) % len(_CONNECTED_PATTERN_CYCLES[direction])
    residue_slot = sample_index % 4 - 1
    pattern = _CONNECTED_PATTERN_CYCLES[direction][phase][residue_slot]

    if horizontal:
        pair_row = layout_rng.choice((0, height - 2))
        pair_col = layout_rng.randrange(width - 3)
        slots = [(pair_row, pair_col), (pair_row, pair_col + 2)]
        if remaining:
            other_row = height - 2 if pair_row == 0 else 0
            slots.extend(
                (other_row, col)
                for col in _spaced_positions(width, remaining, layout_rng)
            )
    else:
        pair_col = layout_rng.choice((0, width - 2))
        pair_row = layout_rng.randrange(height - 3)
        slots = [(pair_row, pair_col), (pair_row + 2, pair_col)]
        if remaining:
            other_col = width - 2 if pair_col == 0 else 0
            slots.extend(
                (row, other_col)
                for row in _spaced_positions(height, remaining, layout_rng)
            )

    missing_indices = list(pattern)
    missing_indices.extend(
        index for index in range(4) if index not in pattern
    )
    return slots, missing_indices[:target]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule owns output."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # One quarter of ordinary draws are exact canonical-profile anchors.
    # Explicit overrides always retain the full declared boundary domain.
    canonical_anchor = sample_index % 4 == 0
    height_options = (5, 6) if canonical_anchor and "grid_h" not in overrides else _HEIGHT_OPTIONS
    height = ctx.draw_choice("grid_h", height_options)
    if canonical_anchor and "grid_w" not in overrides:
        width_options = (6, 7) if height == 5 else (7,)
    else:
        width_options = _WIDTH_OPTIONS
    width = ctx.draw_choice("grid_w", width_options)
    if difficulty == "easy":
        block_options = (2, 2, 2, 3, 3, 4)
    elif difficulty == "hard":
        block_options = (2, 3, 4, 4, 4)
    else:
        block_options = (2, 2, 3, 3, 4, 4)
    if canonical_anchor and "n_blocks" not in overrides:
        block_options = (2,)
    target = ctx.draw_choice("n_blocks", block_options)

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    # Two adjacent counterexample slots per four-sample cycle ensure that a
    # five-pair lesson still contains one after any single query rotation.
    connected_anchor = sample_index % 4 in (1, 2)
    if connected_anchor:
        slots, missing_indices = _connected_layout(
            height, width, target, layout_rng, sample_index
        )
    else:
        lattices = _valid_lattices(height, width, target)
        if not lattices:
            raise ValueError(
                f"no isolated layout for grid_h={height}, grid_w={width}, "
                f"n_blocks={target}"
            )
        rows, cols = layout_rng.choice(lattices)
        slots = [(row, col) for row in rows for col in cols]
        layout_rng.shuffle(slots)
        slots = slots[:target]
        # Residues 0 and 3 are the isolated branches. Their first two
        # orientations are complementary so any three schedule residues still
        # teach all four corners after one held-out query rotation.
        base_corner = 0 if sample_index % 4 == 0 else 2
        missing_indices = [(base_corner + index) % 4 for index in range(target)]

    # Consecutive sample indices deliberately alternate shared/distinct colour
    # lessons.  A four-demo episode therefore cannot hide colour independence.
    palette = list(range(1, 10))
    layout_rng.shuffle(palette)
    if connected_anchor:
        # The first two slots are the connected pair and must share a colour.
        # The odd anchor keeps any remaining windows colour-independent; the
        # even anchor remains an all-reused-colour stress case.
        colors = [palette[0], palette[0]]
        if sample_index % 2 == 1:
            colors.extend(palette[1 : 1 + target - 2])
        else:
            colors.extend([palette[0]] * (target - 2))
    elif canonical_anchor or sample_index % 2 == 1:
        colors = palette[:target]
    else:
        colors = [palette[0]] * target

    # Non-connected scenes advance the base corner with sample_index. Connected
    # scenes use only adjacency patterns that create exactly the intended pair.
    grid = full_grid(height, width, 0)
    for (row, col), color, missing_index in zip(slots, colors, missing_indices):
        cells = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
        for index, (cell_row, cell_col) in enumerate(cells):
            if index != missing_index:
                grid[cell_row][cell_col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
