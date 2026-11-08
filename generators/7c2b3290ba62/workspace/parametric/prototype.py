"""Episode-fixed marker-role family for ARC task 7c2b3290ba62.

Both settings first identify the unique unordered candidate pair whose occupied
cells complete TARGET together with SOURCE.  The canonical setting marks both
selected positions cyan.  The alternate then compares the two selected
candidate areas: the larger selected part is cyan and the smaller is red.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import hashlib
from pathlib import Path
import random
from typing import Any, Sequence

MODES = ("pair_cyan", "size_roles")
_HOME = Path(__file__).resolve().parent

# (height, panel width, candidate count, answer pair, left member is larger)
_DEMO_PROFILES = (
    (6, 4, 4, (0, 3), False),
    (9, 2, 7, (1, 5), True),
    (12, 3, 5, (0, 4), False),
    (18, 2, 6, (2, 5), True),
    (24, 2, 7, (0, 6), False),
    (30, 4, 4, (1, 2), True),
)
_QUERY_PROFILES = (
    (30, 4, 4, (0, 3), False),
    (21, 3, 5, (1, 4), True),
    (16, 2, 7, (2, 6), False),
    (11, 2, 6, (0, 5), True),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"marker_mode"}:
        raise ValueError("settings must contain exactly marker_mode")
    mode = settings["marker_mode"]
    if mode not in MODES:
        raise ValueError("marker_mode must be pair_cyan or size_roles")
    return mode


def program(settings: dict[str, Any]) -> str:
    mode = _mode(settings)
    filename = "canonical.rkt" if mode == "pair_cyan" else "size_roles.rkt"
    return (_HOME / filename).read_text(encoding="utf-8")


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"7c2b3290ba62:marker-role:v1:{seed}:{stream}:{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _total_width(panel_w: int, n_cands: int) -> int:
    return (n_cands + 2) * panel_w + n_cands + 1


def _paint(
    grid: list[list[int]],
    panel_index: int,
    panel_w: int,
    cells: set[tuple[int, int]],
    color: int,
) -> None:
    start = panel_index * (panel_w + 1)
    for row, col in cells:
        grid[row][start + col] = color


def _palette(rng: random.Random, n_cands: int) -> tuple[int, list[int]]:
    colors = list(range(1, 8))
    rng.shuffle(colors)
    if n_cands == 7:
        return colors[0], colors[:]
    return colors[0], colors[1 : n_cands + 1]


def _scene(
    seed: int,
    stream: str,
    index: int,
    profile: tuple[int, int, int, tuple[int, int], bool],
) -> list[list[int]]:
    height, panel_w, n_cands, answer_pair, left_larger = profile
    width = _total_width(panel_w, n_cands)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("profile exceeds ARC dimensions")
    rng = _rng(seed, stream, index)
    cells = [(row, col) for row in range(height) for col in range(panel_w)]
    capacity = len(cells)

    target_count = min(capacity - 2, max(8, round(capacity * 0.55)))
    missing_count = min(target_count - 1, max(5, capacity // 7 + 2))
    small_count = max(1, missing_count // 3)
    large_count = missing_count - small_count
    if large_count == small_count:
        large_count += 1
        small_count -= 1

    # Make the large profile genuinely distributed: TARGET always touches all
    # four panel boundaries, then fills a deterministic random spread.
    anchors = {(0, 0), (0, panel_w - 1), (height - 1, 0), (height - 1, panel_w - 1)}
    remaining = [cell for cell in cells if cell not in anchors]
    rng.shuffle(remaining)
    target = set(anchors)
    target.update(remaining[: target_count - len(target)])

    shuffled_target = sorted(target)
    rng.shuffle(shuffled_target)
    missing = shuffled_target[:missing_count]
    source = target - set(missing)
    small = set(missing[:small_count])
    large = set(missing[small_count:])

    left_index, right_index = answer_pair
    left_part, right_part = (large, small) if left_larger else (small, large)
    candidate_cells: list[set[tuple[int, int]]] = [set() for _ in range(n_cands)]
    candidate_cells[left_index] = left_part
    candidate_cells[right_index] = right_part

    outside = [cell for cell in cells if cell not in target]
    available = [cell for cell in cells if cell not in source]
    distractors = [i for i in range(n_cands) if i not in answer_pair]
    for rank, candidate_index in enumerate(distractors):
        if rank == 0:
            count = min(len(available), large_count + 3)
        elif rank == 1:
            count = 1
        else:
            count = min(len(available), 2 + ((seed + index + rank) % max(2, min(large_count + 2, 9))))
        local = available[:]
        rng.shuffle(local)
        chosen = set(local[:count])
        if not (chosen - target):
            chosen.add(rng.choice(outside))
        candidate_cells[candidate_index] = chosen

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for panel_index in range(1, n_cands + 2):
        separator = panel_index * (panel_w + 1) - 1
        for row in range(height):
            grid[row][separator] = 9

    source_color, candidate_colors = _palette(_rng(seed, stream + ":palette", index), n_cands)
    _paint(grid, 0, panel_w, source, source_color)
    _paint(grid, 1, panel_w, target, source_color)
    for candidate_index, occupied in enumerate(candidate_cells):
        _paint(grid, 2 + candidate_index, panel_w, occupied, candidate_colors[candidate_index])
    return grid


def _grid(grid: Any) -> list[list[int]]:
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
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    separators = [col for col in range(width) if all(source[row][col] == 9 for row in range(height))]
    if len(separators) < 4:
        raise ValueError("expected at least four full color-9 separators")
    panel_w = separators[0]
    if panel_w < 1 or separators != list(range(panel_w, width, panel_w + 1)):
        raise ValueError("separator columns must be single and evenly spaced")
    panels: list[list[list[int]]] = []
    start = 0
    for separator in separators + [width]:
        panel = [row[start:separator] for row in source]
        if any(len(row) != panel_w for row in panel):
            raise ValueError("panels must have equal width")
        panels.append(panel)
        start = separator + 1
    return panels


def _occupancy(panel: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value not in (0, 9)
    }


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    panels = _split_panels(grid)
    if len(panels) < 5:
        raise ValueError("expected SOURCE, TARGET and at least three candidates")
    source = _occupancy(panels[0])
    target = _occupancy(panels[1])
    candidates = [_occupancy(panel) for panel in panels[2:]]
    good_pairs = [
        pair
        for pair in combinations(range(len(candidates)), 2)
        if source | candidates[pair[0]] | candidates[pair[1]] == target
    ]
    return {
        "panels": panels,
        "panel_h": len(grid),
        "panel_w": len(panels[0][0]),
        "source": source,
        "target": target,
        "candidates": candidates,
        "candidate_sizes": [len(candidate) for candidate in candidates],
        "good_pairs": good_pairs,
    }


def solve_python(grid: list[list[int]], marker_mode: str) -> list[list[int]]:
    if marker_mode not in MODES:
        raise ValueError("marker_mode must be pair_cyan or size_roles")
    facts = analyze(grid)
    output = [[0] * len(facts["candidates"])]
    if not facts["good_pairs"]:
        return output
    left, right = facts["good_pairs"][0]
    if marker_mode == "pair_cyan":
        output[0][left] = 8
        output[0][right] = 8
    else:
        sizes = facts["candidate_sizes"]
        larger, smaller = (left, right) if sizes[left] >= sizes[right] else (right, left)
        output[0][larger] = 8
        output[0][smaller] = 2
    return output


def _pair(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    return {"input": [row[:] for row in grid], "output": solve_python(grid, mode)}


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")

    demo_inputs = [_scene(seed, "demo", index, _DEMO_PROFILES[index]) for index in range(demos)]
    query_inputs = [_scene(seed, "query", index, _QUERY_PROFILES[index]) for index in range(queries)]
    frozen = [tuple(tuple(row) for row in grid) for grid in demo_inputs + query_inputs]
    if len(frozen) != len(set(frozen)):
        raise ValueError("all demonstration and query inputs must be distinct")
    for grid in demo_inputs + query_inputs:
        facts = analyze(grid)
        if len(facts["good_pairs"]) != 1:
            raise ValueError("sampled input must have exactly one completing pair")
        left, right = facts["good_pairs"][0]
        if facts["candidate_sizes"][left] == facts["candidate_sizes"][right]:
            raise ValueError("selected candidate areas must differ")
        if solve_python(grid, "pair_cyan") == solve_python(grid, "size_roles"):
            raise ValueError("every sampled input must distinguish both settings")

    return {
        "train": [_pair(grid, mode) for grid in demo_inputs],
        "test": [_pair(grid, mode) for grid in query_inputs],
        "program_solution": program(settings),
        "settings": {"marker_mode": mode},
        "seed": seed,
        "teaching": {
            "used_query_answers": False,
            "minimum_demos_cover": ["selected-right-larger", "selected-left-larger"],
            "exact_30_wide_unavailable": "equal panels plus single separators cannot total width 30; largest retained profile is 30x29",
        },
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    """Return visible demonstrations plus exactly one masked query."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    try:
        train = [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        query = {"input": deepcopy(episode["test"][query_index]["input"])}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require input grids and demonstration outputs") from error
    return {"train": train, "test": [query]}
