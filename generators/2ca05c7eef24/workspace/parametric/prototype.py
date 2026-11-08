"""Three-panel voting with a causal output-mode finish stage.

``vote_only`` is the exact selected canonical rule. The composed setting first
computes the complete local-vote grid, then finds the unique most frequent
nonzero color in that intermediate and erases every other voted color.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "2ca05c7eef24"
HERE = Path(__file__).resolve().parent
FINISH_RULES = ("vote_only", "vote_then_keep_output_mode")
_DEMO_SHAPES = ((5, 4), (6, 5), (7, 6), (9, 7), (12, 8), (15, 9))
_QUERY_SHAPES = ((8, 4), (16, 6), (24, 8), (30, 9))
_PALETTES = (
    (6, 2, 9),
    (4, 1, 9),
    (7, 3, 9),
    (3, 1, 8),
    (8, 4, 9),
    (6, 1, 9),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish_rule"}:
        raise ValueError("settings must contain exactly finish_rule")
    value = settings["finish_rule"]
    if type(value) is not str or value not in FINISH_RULES:
        raise ValueError(f"finish_rule must be one of {FINISH_RULES}")
    return {"finish_rule": value}


def program(settings: Any) -> str:
    value = normalize_settings(settings)["finish_rule"]
    filename = "canonical.rkt" if value == "vote_only" else "vote_then_keep_output_mode.rkt"
    return (HERE / filename).read_text()


def _split(grid: list[list[int]]) -> list[list[list[int]]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30 or (width - 2) % 3:
        raise ValueError("three panels need total width 3*pw+2 within 30")
    panel_width = (width - 2) // 3
    if not 1 <= panel_width <= 9:
        raise ValueError("panel width must be in 1..9")
    if any(
        type(row) is not list or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact ARC integers")
    separators = (panel_width, 2 * panel_width + 1)
    if any(row[column] != 5 for row in grid for column in separators):
        raise ValueError("both separator columns must be gray 5")
    panels = []
    for index in range(3):
        left = index * (panel_width + 1)
        panel = [row[left:left + panel_width] for row in grid]
        if any(value == 5 for row in panel for value in row):
            raise ValueError("panel values cannot use separator color 5")
        panels.append(panel)
    return panels


def _winner(values: list[int]) -> int:
    nonzero = [value for value in values if value != 0]
    if len(nonzero) < 2:
        return 0
    counts = Counter(nonzero)
    return max(counts, key=lambda value: (counts[value], value))


def vote_grid(grid: list[list[int]]) -> list[list[int]]:
    panels = _split(grid)
    height, width = len(panels[0]), len(panels[0][0])
    return [
        [_winner([panel[row][column] for panel in panels]) for column in range(width)]
        for row in range(height)
    ]


def _mode(values: list[int]) -> int:
    values = [value for value in values if value not in (0, 5)]
    if not values:
        return 0
    counts = Counter(values)
    return max(counts, key=lambda value: (counts[value], value))


def keep_color(grid: list[list[int]], color: int) -> list[list[int]]:
    return [[value if value == color else 0 for value in row] for row in grid]


def finish_python(grid: list[list[int]], settings: Any) -> list[list[int]]:
    value = normalize_settings(settings)["finish_rule"]
    stage = vote_grid(grid)
    return stage if value == "vote_only" else keep_color(stage, _mode([v for row in stage for v in row]))


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    panels = _split(grid)
    stage = vote_grid(grid)
    raw = [value for panel in panels for row in panel for value in row]
    output_counts = Counter(value for row in stage for value in row if value != 0)
    raw_counts = Counter(value for value in raw if value != 0)
    return {
        "output_counts": dict(sorted(output_counts.items())),
        "raw_input_counts": dict(sorted(raw_counts.items())),
        "output_mode": _mode([value for row in stage for value in row]),
        "raw_input_mode": _mode(raw),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:output-mode-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _permute(values: tuple[int, int, int], rng: random.Random) -> tuple[int, int, int]:
    values = list(values)
    rng.shuffle(values)
    return tuple(values)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, panel_width = (_DEMO_SHAPES if split == "train" else _QUERY_SHAPES)[index]
    area = height * panel_width
    winner, runner, distractor = _PALETTES[(index + (0 if split == "train" else 2)) % len(_PALETTES)]
    lowers = [value for value in range(1, winner) if value != 5]
    if len(lowers) < 2:
        raise AssertionError("winner palette needs two lower colors")
    lower1, lower2 = lowers[0], lowers[1]

    winner_count = max(6, area // 4)
    runner_count = winner_count - 1
    distractor_count = max(3, area // 8)
    if winner_count + runner_count + distractor_count > area:
        raise AssertionError("scene count plan exceeds panel area")

    corners = [(0, 0), (0, panel_width - 1), (height - 1, 0), (height - 1, panel_width - 1)]
    remaining = [(row, column) for row in range(height) for column in range(panel_width) if (row, column) not in corners]
    rng = _rng(seed, split, index)
    rng.shuffle(remaining)
    positions = corners + remaining

    triples: list[tuple[int, int, int]] = []
    # Four all-panel corner witnesses force nonzero foreground onto every outer boundary.
    triples.extend([(runner, runner, runner)] * 4)
    for offset in range(winner_count):
        if offset % 3 == 0:
            triple = (winner, winner, distractor)
        elif offset % 3 == 1:
            triple = (winner, lower1, 0)
        else:
            triple = (winner, lower1, lower2)
        triples.append(_permute(triple, rng))
    triples.extend([_permute((runner, runner, runner), rng) for _ in range(runner_count - 4)])
    triples.extend([_permute((distractor, distractor, lower1), rng) for _ in range(distractor_count)])
    while len(triples) < area:
        offset = len(triples)
        triple = (lower1, 0, 0) if offset % 3 == 0 else (0, 0, 0)
        triples.append(_permute(triple, rng))

    panels = [[[0 for _ in range(panel_width)] for _ in range(height)] for _ in range(3)]
    for (row, column), triple in zip(positions, triples):
        for panel_index, value in enumerate(triple):
            panels[panel_index][row][column] = value
    width = 3 * panel_width + 2
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for panel_index, panel in enumerate(panels):
            left = panel_index * (panel_width + 1)
            grid[row][left:left + panel_width] = panel[row]
        grid[row][panel_width] = 5
        grid[row][2 * panel_width + 1] = 5

    facts = analyze_input(grid)
    if facts["output_mode"] != winner or facts["raw_input_mode"] != runner or winner == runner:
        raise AssertionError(f"scene lost intended output/raw-mode confound: {facts}")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    normalized = normalize_settings(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("episode inputs must be distinct")
    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": copy.deepcopy(grid), "output": finish_python(grid, normalized)}
    episode = {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(normalized),
        "settings": copy.deepcopy(normalized),
        "metadata": {
            "schema": "2ca05c7eef24-output-mode-v1",
            "seed": seed,
            "sequential_dependency": {
                "step_a": "apply the canonical local vote at every panel coordinate",
                "intermediate": "the complete voted output grid and its nonzero color histogram",
                "step_b": "keep only cells whose voted color is the unique global output mode",
            },
            "largest_lawful_canvas": "30x29 because three equal panels plus two separators have width 3*pw+2",
        },
    }
    return copy.deepcopy(episode)


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or len(episode["train"]) < 2:
        raise ValueError("episode needs at least two demonstrations")
    rows = []
    for pair in episode["train"]:
        grid = pair["input"]
        stage = vote_grid(grid)
        facts = analyze_input(grid)
        composed = keep_color(stage, facts["output_mode"])
        raw_rival = keep_color(stage, facts["raw_input_mode"])
        rows.append({
            **facts,
            "settings_differ": stage != composed,
            "raw_mode_rival_differs": composed != raw_rival,
            "largest_color_rival_differs": composed != keep_color(stage, max(facts["output_counts"])),
        })
    ok = all(
        row["settings_differ"]
        and row["raw_mode_rival_differs"]
        and row["output_mode"] != row["raw_input_mode"]
        for row in rows
    )
    return {"ok": ok, "demonstrations": rows, "finite_scope": True}


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("invalid private episode")
    query_index = _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
