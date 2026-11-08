"""Deterministic native prototype for anchor-normalized motif repetition."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any, Callable

TASK_ID = "87aae821984d"
HOME = Path(__file__).resolve().parent
TILE_ANCHORS = ("bottom_right", "top_left")
_PROGRAMS = {
    "bottom_right": (HOME / "rules" / "canonical.rkt").read_text(),
    "top_left": (HOME / "rules" / "top_left.rkt").read_text(),
}

# height, width, counter cells, motif name, distractor density percent
DEMO_PROFILES = (
    (9, 9, 2, "l_2x2", 5),
    (11, 13, 3, "zig_2x3", 8),
    (14, 16, 4, "zig_3x2", 10),
    (17, 19, 5, "hook_2x3", 12),
    (21, 23, 6, "hook_3x2", 15),
    (25, 27, 7, "l_2x2", 18),
)
QUERY_PROFILES = (
    (13, 15, 4, "hook_2x3", 12),
    (19, 21, 6, "zig_3x2", 18),
    (25, 27, 8, "zig_2x3", 25),
    (30, 30, 10, "zig_2x3", 38),
)
_MOTIFS = {
    "l_2x2": ((0, 0), (1, 0), (1, 1)),
    "zig_2x3": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "zig_3x2": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "hook_2x3": ((0, 0), (1, 0), (1, 1), (1, 2)),
    "hook_3x2": ((0, 0), (0, 1), (1, 1), (2, 1)),
}
_DISTRACTOR_PALETTE = (1, 2, 3, 5, 6, 7, 9)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _anchor(value: Any) -> str:
    if type(value) is not str or value not in TILE_ANCHORS:
        raise ValueError(f"tile_anchor must be one of {TILE_ANCHORS}")
    return value


def program_for(tile_anchor: str) -> str:
    return _PROGRAMS[_anchor(tile_anchor)]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty row lists")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must each be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return len(grid), width


def _digest(seed: int, split: str, index: int, row: int, col: int, salt: str) -> int:
    raw = f"{TASK_ID}|anchor-v1|{seed}|{split}|{index}|{row}|{col}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def make_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _integer(index, "index", 0, len(profiles) - 1)
    height, width, counter_cells, motif_name, density = profiles[index]
    motif = _MOTIFS[motif_name]
    local_r1, local_c1, local_r2, local_c2 = _bbox(list(motif))
    motif_h, motif_w = local_r2 - local_r1 + 1, local_c2 - local_c1 + 1

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if _digest(seed, split, index, row, col, "density") % 100 < density:
                grid[row][col] = _DISTRACTOR_PALETTE[
                    _digest(seed, split, index, row, col, "palette") % len(_DISTRACTOR_PALETTE)
                ]

    # Keep both legal 3x3 normalizations in bounds and clear their union so only
    # the motif itself contributes color 8.
    min_origin_row = 3 - motif_h
    max_origin_row = height - 3
    min_origin_col = 3 - motif_w
    max_origin_col = width - 3
    row_span = max_origin_row - min_origin_row + 1
    col_span = max_origin_col - min_origin_col + 1
    motif_row = min_origin_row + _digest(seed, split, index, 0, 0, "motif-row") % row_span
    motif_col = min_origin_col + _digest(seed, split, index, 0, 0, "motif-col") % col_span
    bottom_origin_row = motif_row - (3 - motif_h)
    bottom_origin_col = motif_col - (3 - motif_w)
    for row in range(min(bottom_origin_row, motif_row), max(bottom_origin_row, motif_row) + 3):
        for col in range(min(bottom_origin_col, motif_col), max(bottom_origin_col, motif_col) + 3):
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = 0
    for local_row, local_col in motif:
        grid[motif_row + local_row][motif_col + local_col] = 8

    # Counter cells include an adjacent pair, defeating component-count shortcuts,
    # plus dispersed singletons selected deterministically from the whole canvas.
    forbidden = {
        (row, col)
        for row in range(min(bottom_origin_row, motif_row) - 1, max(bottom_origin_row, motif_row) + 4)
        for col in range(min(bottom_origin_col, motif_col) - 1, max(bottom_origin_col, motif_col) + 4)
        if 0 <= row < height and 0 <= col < width
    }
    candidates = [(row, col) for row in range(height) for col in range(width) if (row, col) not in forbidden]
    candidates.sort(key=lambda cell: _digest(seed, split, index, cell[0], cell[1], "counter"))
    pair_start = None
    candidate_set = set(candidates)
    for row, col in candidates:
        if (row, col + 1) in candidate_set:
            pair_start = (row, col)
            break
    if pair_start is None:
        raise RuntimeError("no adjacent counter pair")
    chosen = [pair_start, (pair_start[0], pair_start[1] + 1)]
    if counter_cells > 2:
        for candidate in candidates:
            if candidate in chosen:
                continue
            if any(max(abs(candidate[0] - r), abs(candidate[1] - c)) <= 1 for r, c in chosen[2:]):
                continue
            chosen.append(candidate)
            if len(chosen) == counter_cells:
                break
    if len(chosen) != counter_cells:
        raise RuntimeError("could not place requested counter cells")
    for row, col in chosen:
        grid[row][col] = 4

    if split == "query" and index == 3:
        # Make the stress case visibly occupy every boundary without changing the
        # two relevant colors or the exact counter count.
        for row, col, value in ((0, 0, 1), (0, width - 1, 2), (height - 1, 0, 3), (height - 1, width - 1, 5)):
            if grid[row][col] not in (4, 8):
                grid[row][col] = value
    return grid


def analyse(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    eights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not eights:
        raise ValueError("grid needs at least one color-8 motif cell")
    r1, c1, r2, c2 = _bbox(eights)
    motif_h, motif_w = r2 - r1 + 1, c2 - c1 + 1
    if motif_h > 3 or motif_w > 3:
        raise ValueError("color-8 motif bbox must fit within 3x3")
    counters = sum(value == 4 for row in grid for value in row)
    if not 1 <= counters <= 10:
        raise ValueError("grid needs 1..10 color-4 counter cells")
    nonzero = sum(value != 0 for row in grid for value in row)
    distractors = sum(value not in (0, 4, 8) for row in grid for value in row)
    boundaries = 0
    if any(value != 0 for value in grid[0]): boundaries += 1
    if any(value != 0 for value in grid[-1]): boundaries += 1
    if any(row[0] != 0 for row in grid): boundaries += 1
    if any(row[-1] != 0 for row in grid): boundaries += 1
    return {
        "shape": [height, width],
        "counter_cells": counters,
        "motif_bbox": [motif_h, motif_w],
        "motif_origin": [r1, c1],
        "nonzero_cells": nonzero,
        "distractor_cells": distractors,
        "occupied_boundaries": boundaries,
    }


def extract_tile(grid: list[list[int]], tile_anchor: str) -> list[list[int]]:
    anchor = _anchor(tile_anchor)
    facts = analyse(grid)
    r1, c1 = facts["motif_origin"]
    motif_h, motif_w = facts["motif_bbox"]
    if anchor == "bottom_right":
        row0 = r1 - (3 - motif_h)
        col0 = c1 - (3 - motif_w)
    else:
        row0, col0 = r1, c1
    height, width = len(grid), len(grid[0])
    return [
        [8 if 0 <= row0 + row < height and 0 <= col0 + col < width and grid[row0 + row][col0 + col] == 8 else 0 for col in range(3)]
        for row in range(3)
    ]


def repeat_tile(tile: list[list[int]], count: int) -> list[list[int]]:
    if type(tile) is not list or len(tile) != 3 or any(type(row) is not list or len(row) != 3 for row in tile):
        raise ValueError("tile must be exactly 3x3")
    _integer(count, "count", 1, 10)
    return [row * count for row in tile]


def solve(grid: list[list[int]], tile_anchor: str) -> list[list[int]]:
    facts = analyse(grid)
    return repeat_tile(extract_tile(grid, tile_anchor), facts["counter_cells"])


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    return {
        "train": [make_input(seed, "demo", index) for index in range(len(DEMO_PROFILES))],
        "test": [make_input(seed, "query", index) for index in range(len(QUERY_PROFILES))],
    }


def generate_episode(seed: int, tile_anchor: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    anchor = _anchor(tile_anchor)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    inputs = episode_inputs(seed)
    return {
        "train": [{"input": copy.deepcopy(grid), "output": solve(grid, anchor)} for grid in inputs["train"][:demos]],
        "test": [{"input": copy.deepcopy(grid), "output": solve(grid, anchor)} for grid in inputs["test"][:queries]],
        "program_solution": program_for(anchor),
    }


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode/query_index is invalid")
    return {"train": copy.deepcopy(train), "test": [{"input": copy.deepcopy(test[query_index]["input"])}]}


def _components_of_four(grid: list[list[int]]) -> int:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    count = 0
    while cells:
        count += 1
        frontier = [cells.pop()]
        while frontier:
            row, col = frontier.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in cells:
                    cells.remove(neighbor); frontier.append(neighbor)
    return count


def _tight_bbox_repeat(grid: list[list[int]], anchor: str) -> list[list[int]]:
    facts = analyse(grid)
    r1, c1 = facts["motif_origin"]
    h, w = facts["motif_bbox"]
    crop = [[8 if grid[r1 + r][c1 + c] == 8 else 0 for c in range(w)] for r in range(h)]
    return [row * facts["counter_cells"] for row in crop]


def _vertical_repeat(grid: list[list[int]], anchor: str) -> list[list[int]]:
    tile = extract_tile(grid, anchor)
    return [copy.deepcopy(row) for _ in range(analyse(grid)["counter_cells"]) for row in tile]


def audit_rivals(tile_anchor: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    anchor = _anchor(tile_anchor)
    other = "top_left" if anchor == "bottom_right" else "bottom_right"
    return {
        f"declared_setting:{other}": lambda grid, other=other: solve(grid, other),
        "fixed_one_repeat": lambda grid, anchor=anchor: repeat_tile(extract_tile(grid, anchor), 1),
        "fixed_three_repeats": lambda grid, anchor=anchor: repeat_tile(extract_tile(grid, anchor), 3),
        "count_four_components": lambda grid, anchor=anchor: repeat_tile(extract_tile(grid, anchor), _components_of_four(grid)),
        "tight_bbox_without_3x3_normalization": lambda grid, anchor=anchor: _tight_bbox_repeat(grid, anchor),
        "repeat_vertically": lambda grid, anchor=anchor: _vertical_repeat(grid, anchor),
    }


def teaching_certificate(episode: dict[str, Any], tile_anchor: str) -> dict[str, Any]:
    anchor = _anchor(tile_anchor)
    demos, queries = episode.get("train"), episode.get("test")
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        raise ValueError("episode must contain nonempty train/test lists")
    declared = [candidate for candidate in TILE_ANCHORS if all(solve(pair["input"], candidate) == pair["output"] for pair in demos)]
    surviving: list[str] = []
    query_changing: list[str] = []
    refutations: dict[str, list[int]] = {}
    for name, rival in audit_rivals(anchor).items():
        mismatches = [index for index, pair in enumerate(demos) if rival(pair["input"]) != pair["output"]]
        refutations[name] = mismatches
        if not mismatches:
            surviving.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                query_changing.append(name)
    return {
        "declared_setting_survivors": declared,
        "surviving_named_rivals": surviving,
        "query_changing_named_survivors": query_changing,
        "demo_refutation_indices": refutations,
        "scope": "Finite declared settings and named deterministic rivals only.",
    }


def dependency_trace(grid: list[list[int]], tile_anchor: str) -> dict[str, Any]:
    anchor = _anchor(tile_anchor)
    facts = analyse(grid)
    tile = extract_tile(grid, anchor)
    output = repeat_tile(tile, facts["counter_cells"])
    return {
        "step_a": "extract the color-8 motif into an anchor-normalized 3x3 tile",
        "intermediate_tile": tile,
        "step_b": "repeat the normalized tile once for every color-4 counter cell",
        "counter_cells": facts["counter_cells"],
        "step_b_output": output,
    }
