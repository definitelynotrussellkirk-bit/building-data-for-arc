"""Independent task-local oracle and shortcut probes for 7bba59d92716.

This module is reviewer tooling, not output authority.  It deliberately spells the
component rule and plausible wrong rules independently from ``generator.py`` so
future reviewers can reproduce the semantic witnesses without reading Racket.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Callable, Iterable

from reviewer_support import find_root

TASK = "7bba59d92716"
ROOT = find_root(__file__)
CANONICAL_PROFILES = {
    "p8x10c4": (8, 10, 4),
    "p8x13c3": (8, 13, 3),
    "p9x12c4": (9, 12, 4),
    "p10x11c3": (10, 11, 3),
    "p10x13c3": (10, 13, 3),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_7bba59d92716", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs

    return load_pairs(TASK, root=ROOT, labeled_only=True)


def _grid_copy(grid):
    return [list(row) for row in grid]


def components(grid, color: int = 1):
    """Return sorted 4-connected components of ``color``."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def is_vertical_line(cells, length: int | None = None) -> bool:
    if not cells or (length is not None and len(cells) != length):
        return False
    rows = sorted(r for r, _ in cells)
    cols = {c for _, c in cells}
    return len(cols) == 1 and rows == list(range(rows[0], rows[0] + len(rows)))


def is_horizontal_line(cells, length: int | None = None) -> bool:
    if not cells or (length is not None and len(cells) != length):
        return False
    cols = sorted(c for _, c in cells)
    rows = {r for r, _ in cells}
    return len(rows) == 1 and cols == list(range(cols[0], cols[0] + len(cols)))


def intended_output(grid):
    """Independent mirror of the selected rule: exact vertical 1-components of five."""
    out = _grid_copy(grid)
    for cells in components(grid, 1):
        if is_vertical_line(cells, 5):
            r = sorted(row for row, _ in cells)[2]
            c = cells[0][1]
            out[r][c] = 2
    return out


def run5_ignores_branches(grid):
    """Shortcut: mark every maximal vertical run of exactly five, even in a branch."""
    out = _grid_copy(grid)
    h, w = len(grid), len(grid[0])
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] != 1:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] == 1:
                r += 1
            if r - start == 5:
                out[start + 2][c] = 2
    return out


def run5_skips_midpoint_side_neighbor(grid):
    """Shortcut: treat only a side neighbor at the run midpoint as a branch."""
    out = _grid_copy(grid)
    h, w = len(grid), len(grid[0])
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] != 1:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] == 1:
                r += 1
            if r - start != 5:
                continue
            middle = start + 2
            has_midpoint_arm = (
                (c > 0 and grid[middle][c - 1] == 1)
                or (c + 1 < w and grid[middle][c + 1] == 1)
            )
            if not has_midpoint_arm:
                out[middle][c] = 2
    return out


def run5_skips_six_cell_branch(grid):
    """Shortcut: exempt only six-cell components containing a five-cell run."""
    out = _grid_copy(grid)
    for cells in components(grid, 1):
        by_col = {}
        for row, col in cells:
            by_col.setdefault(col, []).append(row)
        for col, rows in by_col.items():
            rows = sorted(rows)
            if rows == list(range(rows[0], rows[0] + 5)) and len(rows) == 5:
                if len(cells) != 6:
                    out[rows[2]][col] = 2
    return out


def branched_run5_signatures(grid):
    """Return (component_size, side-row offsets) for branched five-run components."""
    result = []
    for cells in components(grid, 1):
        if len(cells) <= 5:
            continue
        for col in sorted({c for _, c in cells}):
            rows = sorted(r for r, c in cells if c == col)
            if len(rows) != 5 or rows != list(range(rows[0], rows[0] + 5)):
                continue
            side_offsets = tuple(sorted(r - rows[0] for r, c in cells if c != col))
            if side_offsets:
                result.append((len(cells), side_offsets))
    return result


def component_size5_any_shape(grid):
    """Shortcut: mark the median cell of every five-cell blue component."""
    out = _grid_copy(grid)
    for cells in components(grid, 1):
        if len(cells) == 5:
            r, c = sorted(cells)[2]
            out[r][c] = 2
    return out


def all_vertical_components(grid):
    """Shortcut: mark the midpoint of every straight vertical blue component."""
    out = _grid_copy(grid)
    for cells in components(grid, 1):
        if is_vertical_line(cells):
            rows = sorted(r for r, _ in cells)
            out[rows[(len(rows) - 1) // 2]][cells[0][1]] = 2
    return out


def vertical_length_at_least5(grid):
    """Shortcut: mark every straight vertical component with five or more cells."""
    out = _grid_copy(grid)
    for cells in components(grid, 1):
        if len(cells) >= 5 and is_vertical_line(cells):
            rows = sorted(r for r, _ in cells)
            out[rows[(len(rows) - 1) // 2]][cells[0][1]] = 2
    return out


def has_branched_run5(grid) -> bool:
    for cells in components(grid, 1):
        if len(cells) <= 5:
            continue
        cell_set = set(cells)
        for c in {col for _, col in cells}:
            rows = sorted(r for r, col in cells if col == c)
            if len(rows) == 5 and rows == list(range(rows[0], rows[0] + 5)):
                # The component contains an attached off-column cell.
                if any(col != c for _, col in cell_set):
                    return True
    return False


def observed(grid):
    comps = components(grid, 1)
    palette = {value for row in grid for value in row}
    profile = next(
        (
            name
            for name, dims in CANONICAL_PROFILES.items()
            if dims == (len(grid), len(grid[0]), len(palette))
        ),
        None,
    )
    wrong_lengths = sorted(
        len(cells)
        for cells in comps
        if is_vertical_line(cells) and len(cells) in (3, 4, 6)
    )
    return {
        "profile": profile,
        "n_targets": sum(is_vertical_line(cells, 5) for cells in comps),
        "decoy_length": wrong_lengths[0] if len(wrong_lengths) == 1 else None,
        "n_distractors": sum(value in (6, 7) for row in grid for value in row),
        "branched_run5": has_branched_run5(grid),
        "horizontal5": any(is_horizontal_line(cells, 5) for cells in comps),
        "palette": sorted(palette),
        "component_sizes": sorted(len(cells) for cells in comps),
    }


def branch_witness():
    """Exact accepted-domain counterexample from the retained prior audit."""
    grid = [[0] * 10 for _ in range(8)]
    for r in range(1, 6):
        grid[r][2] = 1
        grid[r][7] = 1
    grid[3][3] = 1
    return grid


def off_midpoint_branch_witness():
    """Accepted witness whose branch attaches at the top, not the midpoint."""
    grid = [[0] * 10 for _ in range(8)]
    for r in range(1, 6):
        grid[r][2] = 1
        grid[r][7] = 1
    grid[1][3] = 1
    return grid


def changed_cells(left, right):
    return [
        (r, c, left[r][c], right[r][c])
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def audit(module=None, *, per_band: int = 40):
    """Emit compact distribution and shortcut evidence for future reviewers."""
    gen = module or load_generator()
    pairs = canonical_pairs()
    shortcuts: dict[str, Callable] = {
        "run5_ignores_branches": run5_ignores_branches,
        "run5_skips_midpoint_side_neighbor": run5_skips_midpoint_side_neighbor,
        "run5_skips_six_cell_branch": run5_skips_six_cell_branch,
        "component_size5_any_shape": component_size5_any_shape,
    }
    report = {
        "task": TASK,
        "source_version": getattr(gen, "VERSION", None),
        "canonical_shortcut_fit": {
            name: all(rule(pair["input"]) == pair["output"] for pair in pairs)
            for name, rule in shortcuts.items()
        },
        "bands": {},
    }
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(per_band):
            grid = gen.generate(1700 + index, index * 11, difficulty=band)
            row = observed(grid)
            row["self_check"] = gen.self_check(grid)
            row["run5_differs"] = run5_ignores_branches(grid) != intended_output(grid)
            row["midpoint_branch_differs"] = (
                run5_skips_midpoint_side_neighbor(grid) != intended_output(grid)
            )
            row["size6_branch_differs"] = (
                run5_skips_six_cell_branch(grid) != intended_output(grid)
            )
            row["branch_signatures"] = branched_run5_signatures(grid)
            row["shape_differs"] = component_size5_any_shape(grid) != intended_output(grid)
            rows.append(row)
        report["bands"][band] = {
            "draws": len(rows),
            "self_check_failures": sum(bool(row["self_check"]) for row in rows),
            "profiles": sorted({row["profile"] for row in rows}),
            "branched_run5": sum(row["branched_run5"] for row in rows),
            "horizontal5": sum(row["horizontal5"] for row in rows),
            "run5_counterexamples": sum(row["run5_differs"] for row in rows),
            "midpoint_branch_counterexamples": sum(
                row["midpoint_branch_differs"] for row in rows
            ),
            "size6_branch_counterexamples": sum(
                row["size6_branch_differs"] for row in rows
            ),
            "branch_signatures": sorted(
                {tuple(signature) for row in rows for signature in row["branch_signatures"]}
            ),
            "shape_counterexamples": sum(row["shape_differs"] for row in rows),
        }
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
