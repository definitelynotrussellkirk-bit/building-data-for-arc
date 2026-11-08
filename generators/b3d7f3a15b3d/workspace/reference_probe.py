"""Independent authoring probes for b3d7f3a15b3d.

This module intentionally does not import production geometry or rule helpers.
It lets task-local tests and future reviewers replay canonical coverage,
observable profiles, and plausible rival rules against retained source bytes.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib
import importlib.util
from pathlib import Path
from typing import Callable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "b3d7f3a15b3d"
TASK_HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)

SCENE_PROFILES = {
    "canonical_3x3_p5": (3, 3, 5),
    "canonical_4x4_p5": (4, 4, 5),
    "canonical_5x4_p6": (5, 4, 6),
    "canonical_5x5_p7": (5, 5, 7),
}


def load_generator(path: str | Path | None = None):
    """Load either the copied runtime source or the selected task source."""
    if path is None:
        try:
            return importlib.import_module(
                f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
            )
        except ModuleNotFoundError:
            path = TASK_HOME / "generator.py"
    source = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=ROOT)


def _validate_rectangular_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        raise ValueError("colors must be integers 0..9")
    return len(grid), width


def _block_geometry(grid):
    height, width = _validate_rectangular_grid(grid)
    if (height - 1) % 5 or (width - 1) % 5:
        raise ValueError("expected outer separators and 4x4 cells")
    cell_rows = (height - 1) // 5
    cell_cols = (width - 1) // 5
    if not (3 <= cell_rows <= 5 and 3 <= cell_cols <= 5):
        raise ValueError("expected 3..5 cell rows and columns")
    separator_rows = set(range(0, height, 5))
    separator_cols = set(range(0, width, 5))
    for row in separator_rows:
        if any(grid[row][col] != 0 for col in range(width)):
            raise ValueError(f"separator row {row} is not zero")
    for col in separator_cols:
        if any(grid[row][col] != 0 for row in range(height)):
            raise ValueError(f"separator column {col} is not zero")
    return cell_rows, cell_cols


def inspect_grid(grid):
    """Return independently observed geometry and semantic branch facts."""
    cell_rows, cell_cols = _block_geometry(grid)
    height, width = len(grid), len(grid[0])
    border_values = []
    interior_values = []
    for i in range(cell_rows):
        rs = 1 + 5 * i
        for j in range(cell_cols):
            cs = 1 + 5 * j
            for dr in range(4):
                for dc in range(4):
                    value = grid[rs + dr][cs + dc]
                    if dr in (0, 3) or dc in (0, 3):
                        border_values.append(value)
                    else:
                        interior_values.append(value)
    if not border_values or len(set(border_values)) != 1 or border_values[0] == 0:
        raise ValueError("all frame borders must share one nonzero color")
    counts = Counter(interior_values)
    if not counts:
        raise ValueError("missing interiors")
    common, common_count = counts.most_common(1)[0]
    if common == 0:
        raise ValueError("common interior color must be nonzero")
    if len(counts) > 1 and common_count == counts.most_common(2)[1][1]:
        raise ValueError("common interior color is not uniquely modal")
    border = border_values[0]
    if border == common:
        raise ValueError("border and common colors must differ")
    palette = sorted({value for row in grid for value in row})
    specials = sorted(set(interior_values) - {common})

    output = independent_output(grid)
    changed = {
        (row, col): output[row][col]
        for row in range(height)
        for col in range(width)
        if output[row][col] != grid[row][col]
    }
    horizontal_changes = set()
    vertical_changes = set()
    changed_colors = set(changed.values())
    for color in specials:
        for dr in (1, 2):
            for dc in (1, 2):
                for i in range(cell_rows):
                    js = [
                        j for j in range(cell_cols)
                        if grid[1 + 5 * i + dr][1 + 5 * j + dc] == color
                    ]
                    if len(js) >= 2:
                        for j in range(min(js), max(js) + 1):
                            point = (1 + 5 * i + dr, 1 + 5 * j + dc)
                            if point in changed:
                                horizontal_changes.add(point)
                for j in range(cell_cols):
                    rows = [
                        i for i in range(cell_rows)
                        if grid[1 + 5 * i + dr][1 + 5 * j + dc] == color
                    ]
                    if len(rows) >= 2:
                        for i in range(min(rows), max(rows) + 1):
                            point = (1 + 5 * i + dr, 1 + 5 * j + dc)
                            if point in changed:
                                vertical_changes.add(point)

    profile = next(
        (
            name
            for name, facts in SCENE_PROFILES.items()
            if facts == (cell_rows, cell_cols, len(palette))
        ),
        None,
    )
    return {
        "height": height,
        "width": width,
        "cell_rows": cell_rows,
        "cell_cols": cell_cols,
        "palette_size": len(palette),
        "scene_profile": profile,
        "border": border,
        "common": common,
        "specials": specials,
        "changed": changed,
        "changed_colors": changed_colors,
        "horizontal_changes": horizontal_changes,
        "vertical_changes": vertical_changes,
    }


def observed(grid):
    facts = inspect_grid(grid)
    return {"scene_profile": facts["scene_profile"]}


def independent_output(grid, *, horizontal=True, vertical=True,
                       color_filter: Callable[[int], bool] | None = None):
    """Independent Python translation of the selected Racket authority."""
    cell_rows, cell_cols = _block_geometry(grid)
    out = deepcopy(grid)
    interior_values = [
        grid[1 + 5 * i + dr][1 + 5 * j + dc]
        for i in range(cell_rows)
        for j in range(cell_cols)
        for dr in (1, 2)
        for dc in (1, 2)
    ]
    common = Counter(interior_values).most_common(1)[0][0]
    colors = sorted({value for row in grid for value in row} - {0, common})
    if color_filter is not None:
        colors = [color for color in colors if color_filter(color)]
    for color in colors:
        for dr in (1, 2):
            for dc in (1, 2):
                if horizontal:
                    for i in range(cell_rows):
                        js = [
                            j for j in range(cell_cols)
                            if grid[1 + 5 * i + dr][1 + 5 * j + dc] == color
                        ]
                        if len(js) >= 2:
                            for j in range(min(js), max(js) + 1):
                                out[1 + 5 * i + dr][1 + 5 * j + dc] = color
                if vertical:
                    for j in range(cell_cols):
                        rows = [
                            i for i in range(cell_rows)
                            if grid[1 + 5 * i + dr][1 + 5 * j + dc] == color
                        ]
                        if len(rows) >= 2:
                            for i in range(min(rows), max(rows) + 1):
                                out[1 + 5 * i + dr][1 + 5 * j + dc] = color
    return out


def horizontal_only(grid):
    return independent_output(grid, horizontal=True, vertical=False)


def vertical_only(grid):
    return independent_output(grid, horizontal=False, vertical=True)


def first_special_only(grid):
    facts = inspect_grid(grid)
    first = min(facts["specials"])
    return independent_output(grid, color_filter=lambda color: color == first)
