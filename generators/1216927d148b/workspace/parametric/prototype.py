"""Native gallery-order family for ARC generator 1216927d148b.

The default setting preserves the exact canonical fixed AB/AC/BC gallery.
The alternate setting first derives all three pairwise intersections and their
occupied-cell counts, then stably orders the derived masks by decreasing area.
Inputs are matched across settings and keep the source task's three-panel
reasoning while extending height to a substantive 30-row query.
"""
from __future__ import annotations

from copy import deepcopy
from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "1216927d148b"
PARAMETER = "gallery_order"
ORDERS = ("fixed_pairs", "largest_overlap_first")
PAIR_NAMES = ("AB", "AC", "BC")
PANEL_STARTS = (0, 6, 12)
PANEL_WIDTH = 5

# height, pair-only branch lengths (AB, AC, BC), panel-exclusive lengths (A,B,C)
# The first two demonstrations are constructive teaching cases: the first has
# three distinct overlap sizes; the second has an AC/BC tie whose stable
# canonical pair-order tie break is visible.
_DEMOS = (
    (9,  (3, 12, 6),  (0, 10, 0)),
    (12, (5, 9, 9),   (12, 0, 0)),
    (15, (18, 7, 11), (2, 8, 5)),
    (18, (14, 25, 8), (15, 3, 6)),
    (21, (30, 17, 15),(0, 10, 2)),
    (24, (20, 34, 22),(12, 0, 9)),
)
_QUERIES = (
    (5,  (2, 4, 3),   (0, 1, 1)),
    (13, (14, 5, 10), (6, 7, 3)),
    (23, (12, 31, 17),(14, 4, 8)),
    (30, (34, 46, 24),(10, 4, 12)),
)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer, not bool or a coercion")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: dict[str, str]) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in ORDERS
    ):
        raise ValueError(
            "settings must be exactly "
            "{'gallery_order': 'fixed_pairs'|'largest_overlap_first'}"
        )
    return settings[PARAMETER]


def program(settings: dict[str, str]) -> str:
    order = _setting(settings)
    name = "canonical.rkt" if order == "fixed_pairs" else "largest_overlap_first.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, "gallery-order-v1", seed, split, index],
                     separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _neighbors_in_region(cell: tuple[int, int], height: int, columns: set[int]):
    row, col = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nxt = (row + dr, col + dc)
        if 0 <= nxt[0] < height and nxt[1] in columns:
            yield nxt


def _side_path(height: int, side: str, reverse_rows: bool) -> list[tuple[int, int]]:
    """Hamiltonian branch path whose every prefix remains hub-connected.

    The path reaches both row boundaries and the outer panel edge before its
    final quarter, so the large profile is genuine full-extent stress rather
    than a compact middle glyph inside a tall canvas.
    """
    hub = height // 2
    inner, outer = ((1, 0) if side == "left" else (3, 4))
    if not reverse_rows:
        order = (
            [(row, inner) for row in range(hub, -1, -1)]
            + [(0, outer)]
            + [(row, outer) for row in range(1, height)]
            + [(height - 1, inner)]
            + [(row, inner) for row in range(height - 2, hub, -1)]
        )
    else:
        order = (
            [(row, inner) for row in range(hub, height)]
            + [(height - 1, outer)]
            + [(row, outer) for row in range(height - 2, -1, -1)]
            + [(0, inner)]
            + [(row, inner) for row in range(1, hub)]
        )
    if len(order) != 2 * height or len(set(order)) != 2 * height:
        raise AssertionError("side branch did not cover its two-column region once")
    return order


def _center_path(height: int, reverse_rows: bool) -> list[tuple[int, int]]:
    hub = height // 2
    rows = []
    for distance in range(1, height + 1):
        candidates = [hub - distance, hub + distance]
        if reverse_rows:
            candidates.reverse()
        rows.extend(row for row in candidates if 0 <= row < height)
    result = [(row, 2) for row in rows]
    if len(result) != height - 1:
        raise AssertionError("center branch did not cover its column")
    return result


def _profile(split: str, index: int):
    specs = _DEMOS if split == "train" else _QUERIES
    _integer("index", index, 0, len(specs) - 1)
    return specs[index]


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    height, shared_values, unique_values = _profile(split, index)
    rng = _rng(seed, split, index)
    shared = dict(zip(PAIR_NAMES, shared_values, strict=True))
    unique = dict(zip(("A", "B", "C"), unique_values, strict=True))
    pair_tail = {"AB": unique["A"], "AC": unique["C"], "BC": unique["B"]}

    reverse_rows = bool(rng.randrange(2))
    paths = {
        "left": _side_path(height, "left", reverse_rows),
        "right": _side_path(height, "right", not reverse_rows),
        "center": _center_path(height, reverse_rows),
    }
    capacities = {name: len(path) for name, path in paths.items()}
    valid = []
    import itertools
    for names in itertools.permutations(paths):
        assignment = dict(zip(PAIR_NAMES, names, strict=True))
        if all(shared[pair] + pair_tail[pair] <= capacities[assignment[pair]]
               for pair in PAIR_NAMES):
            valid.append(assignment)
    if not valid:
        raise ValueError(f"profile {split}[{index}] does not fit branch capacities")
    hub = (height // 2, 2)

    def panels_for(assignment, flip_horizontal):
        pair_cells: dict[str, set[tuple[int, int]]] = {}
        tail_cells: dict[str, set[tuple[int, int]]] = {}
        for pair in PAIR_NAMES:
            path = paths[assignment[pair]]
            length = shared[pair]
            pair_cells[pair] = set(path[:length])
            tail_cells[pair] = set(path[length:length + pair_tail[pair]])
        result = {
            "A": {hub} | pair_cells["AB"] | pair_cells["AC"] | tail_cells["AB"],
            "B": {hub} | pair_cells["AB"] | pair_cells["BC"] | tail_cells["BC"],
            "C": {hub} | pair_cells["AC"] | pair_cells["BC"] | tail_cells["AC"],
        }
        if flip_horizontal:
            result = {
                name: {(row, PANEL_WIDTH - 1 - col) for row, col in cells}
                for name, cells in result.items()
            }
        return result

    configurations = [
        (assignment, flip_horizontal, panels_for(assignment, flip_horizontal))
        for assignment in valid
        for flip_horizontal in (False, True)
    ]
    if split == "test" and index == len(_QUERIES) - 1:
        configurations = [
            item for item in configurations
            if any(col == 0 for _row, col in item[2]["A"])
            and any(col == PANEL_WIDTH - 1 for _row, col in item[2]["C"])
        ]
        if not configurations:
            raise AssertionError("large profile has no all-boundary branch assignment")
    assignment, flip_horizontal, panels = configurations[rng.randrange(len(configurations))]

    # The same semantic scene may also be reflected vertically. Reflection
    # happens after role assignment, so branch position is not a stable proxy
    # for pair identity or overlap rank.
    flip_vertical = bool(rng.randrange(2))
    if flip_vertical:
        panels = {
            name: {(height - 1 - row, col) for row, col in cells}
            for name, cells in panels.items()
        }

    palette = rng.sample(range(1, 10), 3)
    grid = [[0] * 17 for _ in range(height)]
    for start, name, color in zip(PANEL_STARTS, ("A", "B", "C"), palette, strict=True):
        for row, col in panels[name]:
            grid[row][start + col] = color
    return grid


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0])
    if not 1 <= width <= 30:
        raise ValueError("grid must have 1..30 columns")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC integers 0..9")
    return [row[:] for row in grid]


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    if width != 17:
        raise ValueError("gallery input must be exactly 17 columns wide")
    if any(source[row][5] or source[row][11] for row in range(height)):
        raise ValueError("gallery separator columns must be background")
    masks = []
    for start in PANEL_STARTS:
        mask = {(row, col) for row in range(height) for col in range(PANEL_WIDTH)
                if source[row][start + col] != 0}
        if not mask:
            raise ValueError("all three gallery panels must be nonempty")
        masks.append(mask)
    intersections = (
        masks[0] & masks[1],
        masks[0] & masks[2],
        masks[1] & masks[2],
    )
    counts = [len(cells) for cells in intersections]
    ranked = sorted(range(3), key=lambda i: (-counts[i], i))
    return {
        "height": height,
        "panel_masks": masks,
        "intersections": intersections,
        "intersection_counts": counts,
        "ranked_pair_names": [PAIR_NAMES[i] for i in ranked],
        "ranked_indices": ranked,
    }


def _mask_grid(height: int, cells: set[tuple[int, int]]) -> list[list[int]]:
    return [[8 if (row, col) in cells else 0 for col in range(PANEL_WIDTH)]
            for row in range(height)]


def _hstack(grids: list[list[list[int]]], gap: int = 1) -> list[list[int]]:
    height = max(len(grid) for grid in grids)
    result = []
    for row in range(height):
        values = []
        for index, grid in enumerate(grids):
            if index:
                values.extend([0] * gap)
            values.extend(grid[row] if row < len(grid) else [0] * len(grid[0]))
        result.append(values)
    return result


def claimed_output(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    order = _setting(settings)
    analysis = analyze_input(grid)
    indices = [0, 1, 2] if order == "fixed_pairs" else analysis["ranked_indices"]
    pieces = [_mask_grid(analysis["height"], analysis["intersections"][i]) for i in indices]
    return _hstack(pieces, 1)


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer("seed", seed, 0, 2**63 - 1)
    _setting(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = _input(seed, split, index)
            fingerprint = json.dumps(grid, separators=(",", ":"))
            if fingerprint in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(fingerprint)
            episode[split].append({
                "input": grid,
                "output": claimed_output(grid, settings),
            })
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, 3)
    if type(episode) is not dict or type(episode.get("train")) is not list \
            or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if query_index >= len(episode["test"]):
        raise ValueError("query_index exceeds the episode's stored query bank")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    from reviewer_support import public_challenge_bytes
    return public_challenge_bytes(public_turn(episode, query_index))


def public_turn_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()
