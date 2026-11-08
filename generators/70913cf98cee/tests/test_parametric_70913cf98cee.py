from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "70913cf98cee"
HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("parametric_70913cf98cee", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(set(matches)) == 1
    return matches[0]


def _pairs(grid: list[list[int]]) -> list[tuple[int, int]]:
    values = [value for value in grid[0] if value]
    assert len(values) >= 4 and len(values) % 2 == 0
    return list(zip(values[::2], values[1::2]))


def _components(grid: list[list[int]], color: int, *, row0: int = 2) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r in range(row0, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _direct(grid: list[list[int]]) -> list[list[int]]:
    mapping = dict(_pairs(grid))
    return [
        list(row) if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def _cycle_dominoes(grid: list[list[int]]) -> list[list[int]]:
    pairs = _pairs(grid)
    destinations = [dst for _, dst in pairs]
    next_destination = {
        destination: destinations[(i + 1) % len(destinations)]
        for i, destination in enumerate(destinations)
    }
    mapped = _direct(grid)
    out = [list(row) for row in mapped]
    for destination in destinations:
        for component in _components(mapped, destination):
            if len(component) == 2:
                for r, c in component:
                    out[r][c] = next_destination[destination]
    return out


def _all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _mixed_domino(component: set[tuple[int, int]], grid: list[list[int]], src: int, dst: int) -> bool:
    values = {grid[r][c] for r, c in component}
    return values == {src, dst}


def _has_created_domino(grid: list[list[int]]) -> bool:
    mapped = _direct(grid)
    for src, dst in _pairs(grid):
        if any(len(component) == 2 and _mixed_domino(component, grid, src, dst)
               for component in _components(mapped, dst)):
            return True
    return False


def _has_destroyed_source_domino(grid: list[list[int]]) -> bool:
    mapped = _direct(grid)
    for src, dst in _pairs(grid):
        for source_component in _components(grid, src):
            if len(source_component) != 2:
                continue
            mapped_component = next(
                component for component in _components(mapped, dst)
                if source_component <= component
            )
            if len(mapped_component) > 2:
                return True
    return False


def _qualifying_domino_orientations(grid: list[list[int]]) -> dict[int, set[str]]:
    mapped = _direct(grid)
    result: dict[int, set[str]] = {}
    for _src, destination in _pairs(grid):
        orientations: set[str] = set()
        for component in _components(mapped, destination):
            if len(component) != 2:
                continue
            rows = {r for r, _c in component}
            cols = {c for _r, c in component}
            assert len(rows) == 1 or len(cols) == 1
            orientations.add("horizontal" if len(rows) == 1 else "vertical")
        result[destination] = orientations
    return result


def test_default_program_is_exact_canonical_and_settings_are_strict():
    adapter = _load_adapter()
    direct = {"postprocess": "direct"}
    domino = {"postprocess": "cycle_dominoes"}
    assert adapter.program(direct) == _canonical_program()
    assert adapter.program(domino).startswith("(rule!")
    assert adapter.program(domino) != adapter.program(direct)
    for bad in ({}, {"postprocess": "other"}, {"postprocess": True},
                {"postprocess": "direct", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_two_demo_minimum_teaches_both_settings_on_identical_inputs():
    adapter = _load_adapter()
    direct = adapter.generate(17, {"postprocess": "direct"}, 2, 4)
    domino = adapter.generate(17, {"postprocess": "cycle_dominoes"}, 2, 4)
    assert _all_inputs(direct) == _all_inputs(domino)
    assert len({json.dumps(grid) for grid in _all_inputs(direct)}) == 6
    assert all(pair["output"] == _direct(pair["input"]) for pair in direct["train"] + direct["test"])
    assert all(pair["output"] == _cycle_dominoes(pair["input"]) for pair in domino["train"] + domino["test"])
    assert all(a["output"] != b["output"] for a, b in zip(direct["train"], domino["train"]))


def test_minimum_lesson_contains_created_and_destroyed_topology_traps():
    adapter = _load_adapter()
    episode = adapter.generate(31, {"postprocess": "cycle_dominoes"}, 2, 4)
    demo_inputs = [pair["input"] for pair in episode["train"]]
    assert any(_has_created_domino(grid) for grid in demo_inputs)
    assert any(_has_destroyed_source_domino(grid) for grid in demo_inputs)


def test_every_minimum_lesson_disambiguates_pair_scope_orientation_and_cycle_direction():
    adapter = _load_adapter()
    for seed in range(64):
        episode = adapter.generate(seed, {"postprocess": "cycle_dominoes"}, 2, 4)
        for pair in episode["train"]:
            grid = pair["input"]
            legend = _pairs(grid)
            assert len(legend) >= 3
            orientations = _qualifying_domino_orientations(grid)
            assert set(orientations) == {destination for _source, destination in legend}
            assert all(orientations.values())
            assert set().union(*orientations.values()) == {"horizontal", "vertical"}


def test_every_minimum_demo_contains_a_four_vs_eight_connectivity_and_singleton_trap():
    adapter = _load_adapter()
    for seed in range(64):
        episode = adapter.generate(seed, {"postprocess": "cycle_dominoes"}, 2, 4)
        for pair in episode["train"]:
            grid = pair["input"]
            mapped = _direct(grid)
            found = False
            for _source, destination in _pairs(grid):
                singleton_cells = [
                    next(iter(component))
                    for component in _components(mapped, destination)
                    if len(component) == 1
                ]
                if any(
                    abs(r1 - r2) == 1 and abs(c1 - c2) == 1
                    for i, (r1, c1) in enumerate(singleton_cells)
                    for r2, c2 in singleton_cells[i + 1:]
                ):
                    found = True
                    break
            assert found


def test_minimum_three_pair_anchor_exposes_replaceable_unmapped_nuisance_color():
    adapter = _load_adapter()
    for seed in range(64):
        episode = adapter.generate(seed, {"postprocess": "cycle_dominoes"}, 2, 4)
        grid = next(pair["input"] for pair in episode["train"] if len(_pairs(pair["input"])) == 3)
        header = {value for value in grid[0] if value}
        body = {value for row in grid[2:] for value in row if value}
        assert len(body - header) == 1
        assert set(range(1, 10)) - header - body


def test_count_prefixes_bounds_and_query_bank_include_substantive_30x30():
    adapter = _load_adapter()
    setting = {"postprocess": "cycle_dominoes"}
    short = adapter.generate(2026, setting, 2, 1)
    full = adapter.generate(2026, setting, 6, 4)
    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert len(full["train"]) == 6 and len(full["test"]) == 4
    sizes = {(len(pair["input"]), len(pair["input"][0])) for pair in full["test"]}
    assert (30, 30) in sizes
    large = next(pair["input"] for pair in full["test"] if len(pair["input"]) == 30)
    body_nonzero = sum(value != 0 for row in large[2:] for value in row)
    assert body_nonzero >= 60
    quadrants = [False, False, False, False]
    for r in range(2, 30):
        for c in range(30):
            if large[r][c]:
                quadrants[(r >= 16) * 2 + (c >= 15)] = True
    assert all(quadrants)

    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, True)):
        with pytest.raises(ValueError):
            adapter.generate(0, setting, demos, queries)


def test_generation_is_deterministic_fresh_and_settings_do_not_change_inputs():
    adapter = _load_adapter()
    one = adapter.generate(99, {"postprocess": "direct"}, 3, 4)
    two = adapter.generate(99, {"postprocess": "direct"}, 3, 4)
    alternate = adapter.generate(99, {"postprocess": "cycle_dominoes"}, 3, 4)
    assert one == two and one is not two
    assert _all_inputs(one) == _all_inputs(alternate)
    original = one["train"][0]["input"][0][0]
    one["train"][0]["input"][0][0] = 0 if original != 0 else 1
    assert one != two
