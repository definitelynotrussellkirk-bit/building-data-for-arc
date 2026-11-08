"""Nested tile-mask completion family for public parent b99e7126."""
from __future__ import annotations

from collections import Counter
import hashlib
from itertools import combinations
import random
from typing import Any

SETTINGS = ("complete_only", "complete_then_highlight_densest_row")
HIGHLIGHT = 9
MASKS = (
    frozenset({(0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}),  # U
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)}),  # inverted U
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)}),          # staircase
    frozenset({(0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)}),          # mirrored staircase
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)}),          # F
)
COMMON_SHARED_PATTERNS = (
    frozenset({(1, 1)}),
    frozenset({(0, 0), (1, 1), (2, 2)}),
    frozenset({(0, 2), (1, 1), (2, 0)}),
    frozenset({(0, 1), (1, 1), (2, 1)}),
    frozenset({(1, 0), (1, 1), (1, 2)}),
)


def checked_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("Expected rectangular exact integer-color grid with dimensions 1..30")
    return grid


def _runs(indices: list[int]) -> list[list[int]]:
    if not indices:
        return []
    out = [[indices[0]]]
    for value in indices[1:]:
        if value == out[-1][-1] + 1:
            out[-1].append(value)
        else:
            out.append([value])
    return out


def _lattice(grid: list[list[int]]):
    rows, cols = len(grid), len(grid[0])
    candidates = []
    for color in range(10):
        separator_rows = {r for r in range(rows) if all(grid[r][c] == color for c in range(cols))}
        separator_cols = {c for c in range(cols) if all(grid[r][c] == color for r in range(rows))}
        row_runs = _runs([r for r in range(rows) if r not in separator_rows])
        col_runs = _runs([c for c in range(cols) if c not in separator_cols])
        if (
            len(separator_rows) >= 2
            and len(separator_cols) >= 2
            and 3 <= len(row_runs) <= 9
            and 3 <= len(col_runs) <= 9
            and len({len(run) for run in row_runs}) == 1
            and len({len(run) for run in col_runs}) == 1
            and len(row_runs[0]) == len(col_runs[0])
            and len(row_runs[0]) >= 2
        ):
            candidates.append((len(separator_rows) + len(separator_cols), color, row_runs, col_runs))
    if not candidates:
        raise ValueError("Expected a uniform separator lattice around equal square tiles")
    candidates.sort(key=lambda item: item[0], reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise ValueError("Separator lattice is ambiguous")
    _, color, row_runs, col_runs = candidates[0]
    return color, row_runs, col_runs


def _tile(grid, row_run, col_run):
    return tuple(tuple(grid[r][c] for c in col_run) for r in row_run)


def analyze(grid):
    grid = checked_grid(grid)
    separator, row_runs, col_runs = _lattice(grid)
    tiles = {
        (macro_r, macro_c): _tile(grid, row_run, col_run)
        for macro_r, row_run in enumerate(row_runs)
        for macro_c, col_run in enumerate(col_runs)
    }
    counts = Counter(tiles.values())
    if len(counts) != 2:
        raise ValueError("Expected exactly one common tile pattern and one rare tile pattern")
    ordered = counts.most_common()
    if ordered[0][1] == ordered[1][1]:
        raise ValueError("Common and rare tile patterns must have distinct counts")
    common_tile, rare_tile = ordered[0][0], ordered[1][0]
    common_colors = {value for row in common_tile for value in row}
    rare_colors = {value for row in rare_tile for value in row}
    unique_colors = rare_colors - common_colors
    if len(unique_colors) != 1:
        raise ValueError("Rare tile must contain exactly one color absent from the common tile")
    ink = next(iter(unique_colors))
    mask = {
        (r, c)
        for r, row in enumerate(rare_tile)
        for c, value in enumerate(row)
        if value == ink
    }
    if len(mask) < 3:
        raise ValueError("Encoded macro-mask must contain at least three cells")
    current = {position for position, tile in tiles.items() if tile == rare_tile}
    candidates = []
    macro_rows, macro_cols = len(row_runs), len(col_runs)
    tile_h, tile_w = len(rare_tile), len(rare_tile[0])
    for top in range(macro_rows - tile_h + 1):
        for left in range(macro_cols - tile_w + 1):
            target = {(top + r, left + c) for r, c in mask}
            if current <= target:
                candidates.append((top, left, target))
    if len(candidates) != 1:
        raise ValueError("Visible rare tiles must identify exactly one translated encoded mask")
    top, left, target = candidates[0]
    return {
        "separator": separator,
        "row_runs": row_runs,
        "col_runs": col_runs,
        "common_tile": common_tile,
        "rare_tile": rare_tile,
        "ink": ink,
        "mask": mask,
        "current": current,
        "target": target,
        "anchor": (top, left),
    }


def complete(grid):
    grid = checked_grid(grid)
    info = analyze(grid)
    out = [row[:] for row in grid]
    added = []
    for macro_r, macro_c in sorted(info["target"]):
        if (macro_r, macro_c) in info["current"]:
            continue
        for local_r, row in enumerate(info["rare_tile"]):
            for local_c, value in enumerate(row):
                out[info["row_runs"][macro_r][local_r]][info["col_runs"][macro_c][local_c]] = value
        added.append((macro_r, macro_c))
    return out, added, info


def _unique_max(counter: Counter) -> int:
    ordered = counter.most_common()
    if not ordered or (len(ordered) > 1 and ordered[0][1] == ordered[1][1]):
        raise ValueError("Expected a unique maximum")
    return ordered[0][0]


def solve(grid, finish_rule="complete_only"):
    if finish_rule not in SETTINGS:
        raise ValueError("Unknown finish_rule")
    completed, _, info = complete(grid)
    if finish_rule == "complete_only":
        return completed
    selected_row = _unique_max(Counter(row for row, _ in info["target"]))
    out = [row[:] for row in completed]
    for macro_r, macro_c in info["target"]:
        if macro_r != selected_row:
            continue
        for local_r, local_c in info["mask"]:
            out[info["row_runs"][macro_r][local_r]][info["col_runs"][macro_c][local_c]] = HIGHLIGHT
    return out


def causal_intermediate(grid):
    _, _, info = complete(grid)
    target_counts = Counter(row for row, _ in info["target"])
    current_counts = Counter(row for row, _ in info["current"])
    return {
        "completed_macro_tiles": [list(position) for position in sorted(info["target"])],
        "visible_macro_tiles": [list(position) for position in sorted(info["current"])],
        "completed_row_counts": dict(target_counts),
        "visible_row_counts": dict(current_counts),
        "completed_densest_row": _unique_max(target_counts),
        "visible_densest_row": _unique_max(current_counts),
    }


def validate_request(seed, demos, queries):
    for value, low, high, name in (
        (seed, 0, 2**63 - 1, "seed"),
        (demos, 2, 6, "demos"),
        (queries, 1, 4, "queries"),
    ):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, index, query):
    digest = hashlib.sha256(f"b99e7126-v1|{seed}|{query}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _unique_max_row(cells):
    counts = Counter(row for row, _ in cells)
    if not counts:
        return None
    ordered = counts.most_common()
    return ordered[0][0] if len(ordered) == 1 or ordered[0][1] > ordered[1][1] else None


def _teaching_subsets(mask, macro_size, anchor):
    full_row = _unique_max_row(mask)
    out = []
    for size in (3, 4):
        if size >= len(mask):
            continue
        for subset_tuple in combinations(sorted(mask), size):
            subset = set(subset_tuple)
            raw_row = _unique_max_row(subset)
            if raw_row is None or raw_row == full_row:
                continue
            current = {(anchor[0] + row, anchor[1] + col) for row, col in subset}
            anchors = []
            for top in range(macro_size - 2):
                for left in range(macro_size - 2):
                    target = {(top + row, left + col) for row, col in mask}
                    if current <= target:
                        anchors.append((top, left))
            if anchors == [anchor]:
                out.append(subset)
    return out


def _write_tile(grid, starts, macro_row, macro_col, tile):
    row_start, col_start = starts[macro_row], starts[macro_col]
    for local_row, values in enumerate(tile):
        for local_col, value in enumerate(values):
            grid[row_start + local_row][col_start + local_col] = value


def scene(seed, index, *, query=False):
    if type(seed) is not int or not 0 <= seed < 2**63 or type(index) is not int or index < 0:
        raise ValueError("Invalid seed/index")
    rng = _rng(seed, index, query)
    stress = query and index % 4 == 3
    macro_size = 7 if stress else 5 + ((seed + index + (1 if query else 0)) % 3)
    base_size = 4 * macro_size + 1
    side = 30 if stress else base_size
    palette = rng.sample(range(1, 9), 4)
    separator, shared, common_only, ink = palette
    # The first visible demonstration must teach the encoded mask orientation;
    # otherwise horizontally symmetric masks let a reflected-mask shortcut survive.
    mask_index = 2 + (seed % 3) if not query and index == 0 else rng.randrange(len(MASKS))
    mask = set(MASKS[mask_index])
    full_row = _unique_max_row(mask)
    if full_row is None:
        raise RuntimeError("Mask lacks unique densest row")
    top = rng.randrange(macro_size - 2)
    left = rng.randrange(macro_size - 2)
    subsets = _teaching_subsets(mask, macro_size, (top, left))
    if not subsets:
        raise RuntimeError("Mask lacks a causally separating teaching subset")
    visible_local = set(subsets[rng.randrange(len(subsets))])
    common_shared = COMMON_SHARED_PATTERNS[rng.randrange(len(COMMON_SHARED_PATTERNS))]
    common_tile = tuple(
        tuple(shared if (row, col) in common_shared else common_only for col in range(3))
        for row in range(3)
    )
    rare_tile = tuple(
        tuple(ink if (row, col) in mask else shared for col in range(3))
        for row in range(3)
    )
    grid = [[separator for _ in range(side)] for _ in range(side)]
    starts = [1 + 4 * value for value in range(macro_size)]
    for macro_row in range(macro_size):
        for macro_col in range(macro_size):
            _write_tile(grid, starts, macro_row, macro_col, common_tile)
    visible = {(top + row, left + col) for row, col in visible_local}
    for macro_row, macro_col in visible:
        _write_tile(grid, starts, macro_row, macro_col, rare_tile)
    info = analyze(grid)
    expected_target = {(top + row, left + col) for row, col in mask}
    if info["target"] != expected_target or info["current"] != visible:
        raise RuntimeError("Generated nested-mask scene did not round-trip")
    intermediate = causal_intermediate(grid)
    if intermediate["completed_densest_row"] == intermediate["visible_densest_row"]:
        raise RuntimeError("Generated scene failed wrong-intermediate separation")
    if stress:
        if len(grid) != 30 or len(grid[0]) != 30:
            raise RuntimeError("Stress scene must be 30x30")
        if not all(any(grid[row][col] != 0 for row, col in edge) for edge in (
            [(0, col) for col in range(side)],
            [(side - 1, col) for col in range(side)],
            [(row, 0) for row in range(side)],
            [(row, side - 1) for row in range(side)],
        )):
            raise RuntimeError("Stress scene must touch all boundaries")
    return grid
