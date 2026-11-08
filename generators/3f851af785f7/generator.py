"""Semantic generator for ARC task 3f851af785f7.

Each input contains one to four separated monochrome L-triominoes.  Every
triomino occupies exactly three corners of its own 2x2 bounding box.  The
canonical rule fills the one zero corner of every such box with the shape's
color, completing each L to a solid 2x2 square.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f851af785f7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "846fcfd56ec8"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Complete every separated monochrome 2x2 L-triomino by filling its one "
    "missing zero corner with the triomino's color."
)

INVARIANTS = [
    "zero is the background and every nonzero cell belongs to one L-triomino",
    "every monochrome component has exactly three cells in a 2x2 bounding box",
    "each component corresponds to exactly one active 2x2 window with one zero",
    "distinct L-triomino windows are separated by at least one blank row or column",
    "the rule changes exactly one cell per L-triomino and preserves every input cell",
]

PALETTES = {
    "default": (1, 9),
    "warm": (2, 4),
    "cool": (3, 8),
    "varied": (5, 6, 7),
}
PALETTE_KINDS = tuple(PALETTES)
MISSING_CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
_CANONICAL_PROFILES = (
    (7, 7, 2, "warm"),
    (7, 8, 2, "cool"),
    (9, 9, 3, "varied"),
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 7..16",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 7..16",
        "valid": "7..16",
    },
    "n_shapes": {
        "type": "int",
        "default": "difficulty-aware keyed draw 1..4",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice among four disjoint color families",
        "valid": "default|warm|cool|varied",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not (4 <= height <= 30 and 4 <= width <= 30):
        errors.append(f"grid dimensions must be 4..30, got {height}x{width}")
    invalid = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC colors: {invalid[:3]}")
    return errors


def _same_color_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _active_windows(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    active: list[dict[str, Any]] = []
    for row in range(height - 1):
        for col in range(width - 1):
            positions = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[rr][cc] for rr, cc in positions]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                missing = positions[values.index(0)]
                active.append(
                    {
                        "row": row,
                        "col": col,
                        "color": nonzero[0],
                        "missing": missing,
                    }
                )
    return active


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    normalized = [list(row) for row in grid]
    if not any(value == 0 for row in normalized for value in row):
        errors.append("zero background is absent")

    components = _same_color_components(normalized)
    if not components:
        errors.append("expected at least one nonzero L-triomino")

    component_windows: set[tuple[int, int, int]] = set()
    for index, component in enumerate(components):
        cells = component["cells"]
        row0, col0, row1, col1 = component["bbox"]
        box = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
        }
        if len(cells) != 3 or row1 - row0 != 1 or col1 - col0 != 1:
            errors.append(
                f"component {index} must be a three-cell 2x2 L-triomino; "
                f"size={len(cells)} bbox={component['bbox']}"
            )
            continue
        if len(box - cells) != 1:
            errors.append(f"component {index} does not have exactly one missing corner")
            continue
        component_windows.add((row0, col0, component["color"]))

    for left_index, left in enumerate(components):
        lr0, lc0, _, _ = left["bbox"]
        for right_index in range(left_index + 1, len(components)):
            right = components[right_index]
            rr0, rc0, _, _ = right["bbox"]
            if abs(lr0 - rr0) < 3 and abs(lc0 - rc0) < 3:
                errors.append(
                    f"components {left_index} and {right_index} are not separated "
                    "by a blank row or column"
                )

    active = _active_windows(normalized)
    active_keys = {(item["row"], item["col"], item["color"]) for item in active}
    if active_keys != component_windows:
        errors.append(
            "active 2x2 windows do not match the L-components exactly: "
            f"components={len(component_windows)} active={len(active_keys)}"
        )

    output = rule_mirror(normalized)
    changed = [
        (row, col)
        for row in range(len(normalized))
        for col in range(len(normalized[0]))
        if normalized[row][col] != output[row][col]
    ]
    if len(changed) != len(components):
        errors.append(
            f"rule must change exactly one cell per component; changed={len(changed)} "
            f"components={len(components)}"
        )
    if any(normalized[row][col] != 0 for row, col in changed):
        errors.append("rule overwrote a nonzero input cell")

    result.update(
        {
            "errors": errors,
            "components": components,
            "active_windows": active,
            "output": output,
        }
    )
    return result


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the canonical original-window scan."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = [list(row) for row in grid]
    output = [list(row) for row in source]
    for item in _active_windows(source):
        row, col = item["missing"]
        output[row][col] = item["color"]
    return output



def strict_canonical_like(grid) -> list[str]:
    """This task's canonical manifold is exactly the structural teaching grammar."""
    return self_check(grid)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_fixed_corner(grid, corner: tuple[int, int]):
    output = [list(row) for row in grid]
    for item in _active_windows(grid):
        relative = (item["missing"][0] - item["row"], item["missing"][1] - item["col"])
        if relative == corner:
            row, col = item["missing"]
            output[row][col] = item["color"]
    return output


def _rival_first_window_only(grid):
    output = [list(row) for row in grid]
    active = _active_windows(grid)
    if active:
        row, col = active[0]["missing"]
        output[row][col] = active[0]["color"]
    return output


def _rival_color_2_only(grid):
    output = [list(row) for row in grid]
    for item in _active_windows(grid):
        if item["color"] == 2:
            row, col = item["missing"]
            output[row][col] = item["color"]
    return output


def _has_missing_corner(grid, corner: tuple[int, int]) -> bool:
    return any(
        (item["missing"][0] - item["row"], item["missing"][1] - item["col"]) == corner
        for item in _active_windows(grid)
    )


SEMANTIC_WITNESSES = {
    "missing_top_left": lambda grid: _has_missing_corner(grid, (0, 0)),
    "missing_top_right": lambda grid: _has_missing_corner(grid, (0, 1)),
    "missing_bottom_left": lambda grid: _has_missing_corner(grid, (1, 0)),
    "missing_bottom_right": lambda grid: _has_missing_corner(grid, (1, 1)),
    "multiple_shapes": lambda grid: len(_active_windows(grid)) >= 2,
    "multiple_colors": lambda grid: len({item["color"] for item in _active_windows(grid)}) >= 2,
}

SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "fill_top_left_only": lambda grid: _rival_fixed_corner(grid, (0, 0)),
    "fill_bottom_right_only": lambda grid: _rival_fixed_corner(grid, (1, 1)),
    "first_window_only": _rival_first_window_only,
    "fill_color_2_only": _rival_color_2_only,
}

WITNESS_RIVALS = {
    "missing_top_left": ["fill_bottom_right_only"],
    "missing_top_right": ["fill_top_left_only", "fill_bottom_right_only"],
    "missing_bottom_left": ["fill_top_left_only", "fill_bottom_right_only"],
    "missing_bottom_right": ["fill_top_left_only"],
    "multiple_shapes": ["first_window_only"],
    "multiple_colors": ["fill_color_2_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    return sample_index % 4


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival fits demos but changes query."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(pair["input"]) == pair["output"] for pair in demos):
            continue
        if competitor(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demo but changes the query answer")
        else:
            reasons.append(f"{name} survives every demo and the query")
    return reasons

def _palette_kind(colors: Iterable[int]) -> str | None:
    used = set(colors)
    matches = [name for name, palette in PALETTES.items() if used and used <= set(palette)]
    return matches[0] if len(matches) == 1 else None


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str | None]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    components = analysis.get("components") or []
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_shapes": len(components),
        "palette_kind": _palette_kind(component["color"] for component in components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = list(_analyze(grid)["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def mutation_fixtures():
    """Named malformed near-misses that structural validation must reject."""
    blank = full_grid(7, 7, 0)

    full_square = full_grid(7, 7, 0)
    for row in (2, 3):
        for col in (2, 3):
            full_square[row][col] = 4

    two_corners = full_grid(7, 7, 0)
    two_corners[2][2] = 4
    two_corners[3][3] = 4

    mixed_l = full_grid(7, 7, 0)
    mixed_l[2][2] = 4
    mixed_l[2][3] = 4
    mixed_l[3][2] = 5

    touching_ls = full_grid(7, 7, 0)
    for row, col in ((1, 1), (1, 2), (2, 1), (3, 3), (3, 4), (4, 3)):
        touching_ls[row][col] = 6

    short_line = full_grid(7, 7, 0)
    short_line[2][2] = short_line[2][3] = short_line[2][4] = 7

    return [
        ("no_shapes", blank),
        ("already_full_2x2", full_square),
        ("two_diagonal_corners", two_corners),
        ("mixed_color_l", mixed_l),
        ("unseparated_l_pair", touching_ls),
        ("three_cell_line", short_line),
    ]


def _compatible(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return abs(a[0] - b[0]) >= 3 or abs(a[1] - b[1]) >= 3


def _choose_positions(
    height: int, width: int, count: int, rng
) -> list[tuple[int, int]]:
    candidates = [(row, col) for row in range(height - 1) for col in range(width - 1)]
    rng.shuffle(candidates)

    def search(start: int, chosen: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return list(chosen)
        need = count - len(chosen)
        if len(candidates) - start < need:
            return None
        for index in range(start, len(candidates)):
            candidate = candidates[index]
            if all(_compatible(candidate, previous) for previous in chosen):
                chosen.append(candidate)
                found = search(index + 1, chosen)
                if found is not None:
                    return found
                chosen.pop()
        return None

    positions = search(0, [])
    if positions is None:  # The declared 7..16 / 1..4 domain is constructible.
        raise RuntimeError(f"could not place {count} separated L-shapes in {height}x{width}")
    return positions


def _shape_colors(palette_kind: str, count: int, rng) -> list[int]:
    palette = list(PALETTES[palette_kind])
    rng.shuffle(palette)
    distinct = min(count, len(palette))
    colors = palette[:distinct]
    while len(colors) < count:
        colors.append(palette[len(colors) % len(palette)])
    rng.shuffle(colors)
    return colors


def _missing_corners(count: int, seed: int, sample_index: int) -> list[tuple[int, int]]:
    """Cycle the first missing corner across consecutive lesson samples.

    The seed supplies a phase, so layouts do not share a global fixed answer,
    while any four consecutive demonstrations cover all four corner branches.
    """
    start = (seed + sample_index) % len(MISSING_CORNERS)
    return [MISSING_CORNERS[(start + index) % len(MISSING_CORNERS)] for index in range(count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    # Every fourth ordinary sample anchors one exact canonical (height, width,
    # palette-size) profile.  The three-profile cycle makes a four-example
    # lesson include a canonical-scale witness without fixing its placement or
    # missing-corner pattern.  Explicit overrides always take precedence.
    if not overrides and sample_index % 4 == 0:
        height0, width0, count0, palette0 = _CANONICAL_PROFILES[
            (sample_index // 4) % len(_CANONICAL_PROFILES)
        ]
        ctx.overrides.update(
            grid_h=height0,
            grid_w=width0,
            n_shapes=count0,
            palette_kind=palette0,
        )

    height = ctx.draw_int_diff("grid_h", 7, 16)
    width = ctx.draw_int_diff("grid_w", 7, 16)
    count = ctx.draw_int_diff("n_shapes", 1, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    layout_rng = ctx.draw_rng("layout")
    positions = _choose_positions(height, width, count, layout_rng)
    colors = _shape_colors(palette_kind, count, ctx.draw_rng("colors"))
    missing = _missing_corners(count, seed, sample_index)

    grid = full_grid(height, width, 0)
    for (row0, col0), color, absent in zip(positions, colors, missing):
        for dr, dc in MISSING_CORNERS:
            if (dr, dc) != absent:
                grid[row0 + dr][col0 + dc] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # Construction bugs must fail loudly, never leak bad labels.
        raise RuntimeError("constructed invalid lesson: " + "; ".join(errors))
    return grid
