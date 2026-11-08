"""Behavioral contract for the native reconstruct-then-mark family."""
from __future__ import annotations

from collections import Counter, deque
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "5295bc5ff1cb"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode: dict) -> list[dict]:
    return [*episode["train"], *episode["test"]]


def _input_facts(grid: list[list[int]]) -> dict[str, int]:
    cover = grid[-1][-1]
    top_h = next(r for r in range(len(grid)) if grid[r][0] == cover)
    prefix_width = next(c for c in range(len(grid[0])) if grid[0][c] == cover)
    prefix = grid[0][:prefix_width]
    col_period = next(
        p for p in range(1, len(prefix) + 1)
        if all(value == prefix[i % p] for i, value in enumerate(prefix))
    )
    row_period = next(
        p for p in range(1, top_h + 1)
        if all(
            grid[r][c] == grid[r % p][c]
            for r in range(top_h)
            for c in range(col_period)
        )
    )
    return {
        "cover": cover,
        "top_h": top_h,
        "prefix_width": prefix_width,
        "row_period": row_period,
        "col_period": col_period,
    }


def _tile(grid: list[list[int]], *, shift: int) -> list[list[int]]:
    info = _input_facts(grid)
    return [
        [
            grid[r % info["row_period"]][(c + shift) % info["col_period"]]
            for c in range(len(grid[0]))
        ]
        for r in range(len(grid))
    ]


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        pending = deque([start])
        while pending:
            r, c = pending.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        result.append((color, cells))
    return result


def _spanning_components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    return [
        (color, cells)
        for color, cells in _components(grid)
        if min(r for r, _ in cells) == 0
        and max(r for r, _ in cells) == h - 1
        and min(c for _, c in cells) == 0
        and max(c for _, c in cells) == w - 1
    ]


def _paint_cells(grid: list[list[int]], cells: set[tuple[int, int]], color: int) -> list[list[int]]:
    return [
        [color if (r, c) in cells else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _replace_color(grid: list[list[int]], old: int, new: int) -> list[list[int]]:
    return [[new if value == old else value for value in row] for row in grid]


def test_default_program_is_exact_canonical_and_contract_is_finite():
    adapter = _load("adapter")
    assert adapter.program({"mode": "tile_only"}) == _canonical_program()
    assert adapter.program({"mode": "tile_then_mark_span"}) != _canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": ["tile_only", "tile_then_mark_span"]}
    assert contract["default"] == {"mode": "tile_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_distinct_inputs_matched_grammar_and_30x30_query(demos: int):
    adapter = _load("adapter")
    plain = adapter.generate(941, {"mode": "tile_only"}, demos, 4)
    marked = adapter.generate(941, {"mode": "tile_then_mark_span"}, demos, 4)
    assert len(plain["train"]) == demos
    assert len(plain["test"]) == 4
    plain_inputs = [pair["input"] for pair in _pairs(plain)]
    marked_inputs = [pair["input"] for pair in _pairs(marked)]
    assert plain_inputs == marked_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in plain_inputs}) == demos + 4
    assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in plain["test"])
    assert all(a["output"] != b["output"] for a, b in zip(_pairs(plain), _pairs(marked), strict=True))


def test_stage_a_uses_declared_smallest_period_and_removes_cover():
    adapter = _load("adapter")
    for seed in range(12):
        episode = adapter.generate(seed, {"mode": "tile_only"}, 3, 4)
        for pair in _pairs(episode):
            info = _input_facts(pair["input"])
            assert info["row_period"] in (4, 5)
            assert info["col_period"] in (4, 5)
            assert info["top_h"] % info["row_period"] == 0
            assert info["prefix_width"] % info["col_period"] == 0
            assert pair["output"] == _tile(pair["input"], shift=1)
            assert info["cover"] not in {value for row in pair["output"] for value in row}


def test_stage_b_consumes_reconstructed_unique_spanning_component():
    adapter = _load("adapter")
    family = _load("family")
    spanning_colors = set()
    for seed in range(12):
        episode = adapter.generate(seed, {"mode": "tile_then_mark_span"}, 3, 4)
        for pair in _pairs(episode):
            info = _input_facts(pair["input"])
            stage_a = _tile(pair["input"], shift=1)
            spanning = _spanning_components(stage_a)
            assert len(spanning) == 1
            color, cells = spanning[0]
            spanning_colors.add(color)
            assert pair["output"] == _paint_cells(stage_a, cells, info["cover"])
            analyzed = family.analyze(pair["input"])
            assert analyzed["spanning_color"] == color
            assert analyzed["spanning_cell_count"] == len(cells)
    assert len(spanning_colors) >= 4


def test_named_direct_shortcuts_fail_visible_demos():
    adapter = _load("adapter")
    survivors = Counter()
    for seed in range(24):
        episode = adapter.generate(seed, {"mode": "tile_then_mark_span"}, 2, 4)
        episode_ok = Counter({name: 1 for name in (
            "tile_only", "no_shift", "visible_only", "most_frequent_visible", "fixed_lowest_visible"
        )})
        for pair in episode["train"]:
            grid = pair["input"]
            info = _input_facts(grid)
            target = pair["output"]
            stage_a = _tile(grid, shift=1)
            no_shift = _tile(grid, shift=0)
            visible_only = [row[:] for row in grid]
            for r in range(info["top_h"]):
                for c in range(info["prefix_width"]):
                    visible_only[r][c] = stage_a[r][c]
            visible_counts = Counter(
                grid[r][c]
                for r in range(info["top_h"])
                for c in range(info["prefix_width"])
            )
            most = visible_counts.most_common(1)[0][0]
            lowest = min(visible_counts)
            rivals = {
                "tile_only": stage_a,
                "no_shift": no_shift,
                "visible_only": visible_only,
                "most_frequent_visible": _replace_color(stage_a, most, info["cover"]),
                "fixed_lowest_visible": _replace_color(stage_a, lowest, info["cover"]),
            }
            for name, output in rivals.items():
                episode_ok[name] &= output == target
        survivors.update(episode_ok)
    assert survivors == Counter({
        "tile_only": 0,
        "no_shift": 0,
        "visible_only": 0,
        "most_frequent_visible": 0,
        "fixed_lowest_visible": 0,
    })


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"mode": "unknown"}, 3, 4),
        ({"mode": "tile_only", "extra": True}, 3, 4),
        ({"mode": "tile_only"}, True, 4),
        ({"mode": "tile_only"}, 1, 4),
        ({"mode": "tile_only"}, 7, 4),
        ({"mode": "tile_only"}, 3, 3),
        ({"mode": "tile_only"}, 3, 5),
    ],
)
def test_invalid_settings_and_counts_fail_loudly(settings: dict, demos: int, queries: int):
    adapter = _load("adapter")
    with pytest.raises(ValueError):
        adapter.generate(1, settings, demos, queries)
