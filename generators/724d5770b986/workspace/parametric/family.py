"""Matched-input post-expansion component family for ARC task 724d5770b986.

The exact canonical default expands every blue trigger into its clipped 3x3
neighbourhood while preserving colored blockers.  The alternative first builds
that input-dependent expanded grid, then finds the unique largest 4-connected
blue component *after expansion* and recolors that complete component to 8.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "724d5770b986"
ACTIONS = ("expand_only", "highlight_largest_post_component")
SETTINGS = tuple({"post_action": value} for value in ACTIONS)
DEMO_SIZES = ((12, 14), (15, 17), (18, 20), (21, 23), (24, 26), (27, 29))
QUERY_SIZES = ((16, 18), (20, 24), (26, 30), (30, 30))
HERE = Path(__file__).resolve().parent


def _setting(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"post_action"}
            or type(settings["post_action"]) is not str
            or settings["post_action"] not in ACTIONS):
        raise ValueError(
            "settings must be exactly post_action="
            "expand_only|highlight_largest_post_component"
        )
    return settings["post_action"]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    result = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
        result.append(list(row))
    return result


def program(settings: dict[str, Any]) -> str:
    action = _setting(settings)
    filename = "canonical.rkt" if action == "expand_only" else "highlight_largest_post_component.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _blue_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] != 1 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 1
                            and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            result.append(tuple(sorted(cells)))
    return result


def expand(grid: Any) -> list[list[int]]:
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    output = copy.deepcopy(rows)
    triggers = [(r, c) for r in range(height) for c in range(width) if rows[r][c] == 1]
    for tr, tc in triggers:
        for r in range(max(0, tr - 1), min(height, tr + 2)):
            for c in range(max(0, tc - 1), min(width, tc + 2)):
                if rows[r][c] == 0:
                    output[r][c] = 1
    return output


def _unique_largest(components: Iterable[tuple[tuple[int, int], ...]]):
    ordered = sorted(components, key=lambda cells: (-len(cells), cells))
    if not ordered or (len(ordered) > 1 and len(ordered[0]) == len(ordered[1])):
        raise ValueError("scene must have a unique largest post-expansion blue component")
    return ordered[0]


def solve(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    action = _setting(settings)
    expanded = expand(grid)
    if action == "expand_only":
        return expanded
    winner = _unique_largest(_blue_components(expanded))
    output = copy.deepcopy(expanded)
    for r, c in winner:
        output[r][c] = 8
    return output


def solve_rank_before_expand(grid: Any) -> list[list[int]]:
    rows = _grid(grid)
    winner = _unique_largest(_blue_components(rows))
    output = expand(rows)
    for r, c in winner:
        output[r][c] = 8
    return output


def solve_smallest_post(grid: Any) -> list[list[int]]:
    expanded = expand(grid)
    chosen = min(_blue_components(expanded), key=lambda cells: (len(cells), cells))
    output = copy.deepcopy(expanded)
    for r, c in chosen:
        output[r][c] = 8
    return output


def solve_topmost_post(grid: Any) -> list[list[int]]:
    expanded = expand(grid)
    chosen = min(_blue_components(expanded), key=lambda cells: (min(cells), cells))
    output = copy.deepcopy(expanded)
    for r, c in chosen:
        output[r][c] = 8
    return output


def _transform_position(
    pos: tuple[int, int], height: int, width: int, flip_ud: bool, flip_lr: bool
) -> tuple[int, int]:
    r, c = pos
    return (height - 1 - r if flip_ud else r, width - 1 - c if flip_lr else c)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def sample_input(seed: int, split: str, index: int, *, height: int, width: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 10, 30, "height")
    _integer(width, 10, 30, "width")
    rng = _rng(seed, split, index)
    flip_ud = bool(rng.randrange(2))
    flip_lr = bool(rng.randrange(2))
    palette = [2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(palette)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    pair_raw = ((2, 2), (2, 3))
    winner_raw = (height - 3, width - 3)
    runner_raw = (height - 3, 2)
    edge_raw = (0, width // 2)
    pair = tuple(_transform_position(p, height, width, flip_ud, flip_lr) for p in pair_raw)
    winner = _transform_position(winner_raw, height, width, flip_ud, flip_lr)
    runner = _transform_position(runner_raw, height, width, flip_ud, flip_lr)
    edge = _transform_position(edge_raw, height, width, flip_ud, flip_lr)
    triggers = set(pair) | {winner, runner, edge}
    for r, c in triggers:
        grid[r][c] = 1

    # The two-cell original component is the largest *before* expansion, but
    # blockers keep it tiny. This explicitly defeats rank-before-expand.
    pair_block = palette[0]
    for tr, tc in pair:
        for r in range(max(0, tr - 1), min(height, tr + 2)):
            for c in range(max(0, tc - 1), min(width, tc + 2)):
                if (r, c) not in triggers:
                    grid[r][c] = pair_block

    # Runner-up has eight post-expansion cells; the open winner has nine.
    rr, rc = runner
    runner_neighbors = [
        (r, c)
        for r in range(rr - 1, rr + 2)
        for c in range(rc - 1, rc + 2)
        if 0 <= r < height and 0 <= c < width and (r, c) != runner
    ]
    grid[runner_neighbors[(index + seed) % len(runner_neighbors)][0]][
        runner_neighbors[(index + seed) % len(runner_neighbors)][1]
    ] = palette[1]

    # A clipped edge component exercises boundary handling but cannot win.
    er, ec = edge
    edge_neighbors = [
        (r, c)
        for r in range(max(0, er - 1), min(height, er + 2))
        for c in range(max(0, ec - 1), min(width, ec + 2))
        if (r, c) != edge
    ]
    for offset, (r, c) in enumerate(edge_neighbors[:2]):
        if (r, c) not in triggers:
            grid[r][c] = palette[2 + offset]

    # Visible boundary/density stress, always outside every trigger's radius-2
    # safety halo so the unique 9-cell winner remains invariant.
    for k, (r, c) in enumerate(((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))):
        if (r, c) not in triggers and grid[r][c] == 0:
            grid[r][c] = palette[(3 + k) % len(palette)]
    target_distractors = max(10, (height * width) // 35)
    placed = 0
    attempts = 0
    while placed < target_distractors and attempts < target_distractors * 80:
        attempts += 1
        r = rng.randrange(height)
        c = rng.randrange(width)
        if grid[r][c] != 0:
            continue
        if min(max(abs(r - tr), abs(c - tc)) for tr, tc in triggers) <= 2:
            continue
        grid[r][c] = palette[(placed + index) % len(palette)]
        placed += 1
    if placed != target_distractors:
        raise RuntimeError("could not distribute blocker/distractor stress")

    facts = analyze(grid)
    if not facts["valid"] or not facts["setting_outputs_distinct"]:
        raise RuntimeError(f"constructed invalid post-component scene: {facts}")
    return grid


def analyze(grid: Any) -> dict[str, Any]:
    rows = _grid(grid)
    original = sorted(_blue_components(rows), key=lambda cells: (-len(cells), cells))
    expanded = expand(rows)
    post = sorted(_blue_components(expanded), key=lambda cells: (-len(cells), cells))
    unique = bool(post) and (len(post) == 1 or len(post[0]) > len(post[1]))
    winner = post[0] if unique else ()
    original_trigger_count = sum(rows[r][c] == 1 for r, c in winner)
    return {
        "valid": len(original) >= 4 and unique and len(post[0]) == 9,
        "original_component_sizes": [len(cells) for cells in original],
        "post_component_sizes": [len(cells) for cells in post],
        "largest_original_component": len(original[0]) if original else 0,
        "largest_post_component_original_triggers": original_trigger_count,
        "largest_post_component": [list(cell) for cell in winner],
        "setting_outputs_distinct": (
            solve(rows, SETTINGS[0]) != solve(rows, SETTINGS[1]) if unique else False
        ),
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    action = _setting(settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    normalized_settings = {"post_action": action}
    train_inputs = [
        sample_input(seed, "demo", i, height=DEMO_SIZES[i][0], width=DEMO_SIZES[i][1])
        for i in range(demos)
    ]
    test_inputs = [
        sample_input(seed, "query", i, height=QUERY_SIZES[i][0], width=QUERY_SIZES[i][1])
        for i in range(queries)
    ]
    return {
        "task_id": TASK_ID,
        "settings": copy.deepcopy(normalized_settings),
        "program_solution": program(normalized_settings),
        "train": [
            {"input": copy.deepcopy(grid), "output": solve(grid, normalized_settings)}
            for grid in train_inputs
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": solve(grid, normalized_settings)}
            for grid in test_inputs
        ],
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is out of range")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
