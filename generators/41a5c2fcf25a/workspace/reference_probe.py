"""Independent probes for task 41a5c2fcf25a.

This module intentionally does not import implementation helpers from generator.py.
It supplies the portable tests with a small Python oracle and plausible wrong rules.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType

TASK_ID = "41a5c2fcf25a"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | None = None) -> ModuleType:
    source = Path(path).resolve() if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legend(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for row in range(1, h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (1 <= nxt[0] < h and 0 <= nxt[1] < w
                            and grid[nxt[0]][nxt[1]] != 0 and nxt not in seen):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append(sorted(cells))
    return found


def bbox_key(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return min(row for row, _ in cells), min(col for _, col in cells)


def rank_components(grid: list[list[int]], *, mode: str = "canonical") -> list[list[tuple[int, int]]]:
    comps = components(grid)
    if mode == "canonical":
        return sorted(comps, key=lambda cells: (-len(cells), *bbox_key(cells)))
    if mode == "position":
        return sorted(comps, key=bbox_key)
    if mode == "ascending":
        return sorted(comps, key=lambda cells: (len(cells), *bbox_key(cells)))
    if mode == "reverse_ties":
        return sorted(comps, key=lambda cells: (-len(cells), -bbox_key(cells)[0], -bbox_key(cells)[1]))
    raise ValueError(mode)


def recolor(grid: list[list[int]], *, component_mode: str = "canonical",
            legend_values: list[int] | None = None) -> list[list[int]]:
    output = deepcopy(grid)
    colors = legend_values if legend_values is not None else legend(grid)
    for index, cells in enumerate(rank_components(grid, mode=component_mode)):
        color = colors[index] if index < len(colors) else colors[-1]
        for row, col in cells:
            output[row][col] = color
    return output


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    return recolor(grid)


def position_only(grid: list[list[int]]) -> list[list[int]]:
    return recolor(grid, component_mode="position")


def ascending_area(grid: list[list[int]]) -> list[list[int]]:
    return recolor(grid, component_mode="ascending")


def sorted_legend(grid: list[list[int]]) -> list[list[int]]:
    return recolor(grid, legend_values=sorted(legend(grid)))


def reverse_equal_size_ties(grid: list[list[int]]) -> list[list[int]]:
    return recolor(grid, component_mode="reverse_ties")


def exclude_source_from_legend(grid: list[list[int]]) -> list[list[int]]:
    colors = legend(grid)
    if 8 not in colors:
        return recolor(grid)
    kept = [color for color in colors if color != 8]
    if not kept:
        return deepcopy(grid)
    return recolor(grid, legend_values=(kept + [kept[-1]] * len(colors))[:len(colors)])


def identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def analyze(grid: list[list[int]]) -> dict[str, object]:
    colors = legend(grid)
    comps = components(grid)
    sizes = [len(cells) for cells in comps]
    canonical = rank_components(grid)
    positional = rank_components(grid, mode="position")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(comps),
        "palette_size": len({value for row in grid for value in row}),
        "component_sizes": sizes,
        "has_size_tie": len(set(sizes)) < len(sizes),
        "source_in_legend": 8 in colors,
        "legend_not_sorted": colors != sorted(colors),
        "rank_conflicts_position": canonical != positional,
    }
