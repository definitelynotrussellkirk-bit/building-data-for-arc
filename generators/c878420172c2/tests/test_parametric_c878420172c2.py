"""Behavioral contract for the overlap/largest-component parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/c878420172c2/workspace/parametric"
SETTINGS = [
    {"overlap_mode": "all_overlap"},
    {"overlap_mode": "largest_component"},
]


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"build {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_c878_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


def _literal_grid():
    grid = [[0] * 14 for _ in range(12)]
    core = {(0, 0), (0, 1), (1, 0), (1, 1)}
    tail2 = {(0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (3, 4), (4, 4)}
    tail3 = {(2, 0), (3, 0), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)}
    for r, c in core | tail2:
        grid[1 + r][1 + c] = 2
    for r, c in core | tail3:
        grid[6 + r][8 + c] = 3
    return grid


def test_default_program_is_exact_canonical_and_alternative_is_distinct(adapter):
    record = Catalog(ROOT).get("c878420172c2")
    programs = {row["program_solution"] for row in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[1]) != canonical


def test_literal_intersection_then_largest_component_semantics(adapter):
    grid = _literal_grid()
    inter = adapter.stage_a(grid)
    assert inter == {(0, 0), (0, 1), (1, 0), (1, 1), (4, 4)}
    all_overlap = adapter.solve(grid, "all_overlap")
    largest = adapter.solve(grid, "largest_component")
    assert sum(value == 8 for row in all_overlap for value in row) == 5
    assert sum(value == 8 for row in largest for value in row) == 4
    assert largest == adapter.stage_b(inter, len(grid), len(grid[0]))
    assert largest != adapter.stage_b(adapter.normalize_color(grid, 2), len(grid), len(grid[0]))


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_prefixes_reproducibility_and_matched_inputs(adapter, demos, queries):
    full = adapter.generate(17, SETTINGS[1], 6, 4)
    episode = adapter.generate(17, SETTINGS[1], demos, queries)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]
    assert episode == adapter.generate(17, SETTINGS[1], demos, queries)
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in inputs}) == len(inputs)
    baseline = adapter.generate(17, SETTINGS[0], demos, queries)
    assert [p["input"] for s in ("train", "test") for p in baseline[s]] == inputs

    changed = copy.deepcopy(episode)
    changed["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, SETTINGS[1], demos, queries) == episode


def test_two_demos_identify_both_settings(adapter):
    for chosen, setting in enumerate(SETTINGS):
        episode = adapter.generate(29, setting, 2, 4)
        survivors = []
        for rival, candidate in enumerate(SETTINGS):
            labels = [adapter.solve(pair["input"], candidate["overlap_mode"])
                      for pair in episode["train"]]
            if labels == [pair["output"] for pair in episode["train"]]:
                survivors.append(rival)
        assert survivors == [chosen]


def test_generated_intermediate_has_unique_largest_and_real_dependency(adapter):
    episode = adapter.generate(63, SETTINGS[1], 6, 4)
    for split in ("train", "test"):
        for pair in episode[split]:
            inter = adapter.stage_a(pair["input"])
            components = adapter.components(inter)
            sizes = sorted((len(component) for component in components), reverse=True)
            assert len(sizes) >= 2 and sizes[0] > sizes[1]
            expected = pair["output"]
            assert expected == adapter.stage_b(inter, len(pair["input"]), len(pair["input"][0]))
            wrong = adapter.stage_b(adapter.normalize_color(pair["input"], 2),
                                    len(pair["input"]), len(pair["input"][0]))
            assert expected != wrong


def test_large_query_is_substantive_30x30_boundary_stress(adapter):
    episode = adapter.generate(0, SETTINGS[1], 2, 4)
    pair = next(pair for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
    source = pair["input"]
    occupied = [(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v]
    assert len(occupied) >= 70
    assert any(r == 0 for r, _ in occupied) and any(r == 29 for r, _ in occupied)
    assert any(c == 0 for _, c in occupied) and any(c == 29 for _, c in occupied)
    assert all(any(source[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))


def test_public_turn_masks_private_fields_and_future_queries(adapter):
    episode = adapter.generate(2, SETTINGS[1], 3, 4)
    visible = adapter.public_turn(episode, 0)
    assert visible == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    changed = copy.deepcopy(episode)
    changed["seed"] = -1
    changed["settings"] = {"private": True}
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn(changed, 0) == visible


@pytest.mark.parametrize("settings", [None, {}, {"overlap_mode": "bad"},
    {"overlap_mode": True}, {"overlap_mode": "all_overlap", "extra": 1}])
def test_bad_settings_rejected(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 2, 1)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 1), (-1, 2, 1), (2**63, 2, 1), (1.0, 2, 1),
    (0, True, 1), (0, 1, 1), (0, 7, 1), (0, 2.0, 1),
    (0, 2, True), (0, 2, 0), (0, 2, 5), (0, 2, 1.0),
])
def test_bad_counts_and_seeds_rejected(adapter, seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, SETTINGS[0], demos, queries)


def test_bounded_audit_replays_teaching_and_causality(tmp_path):
    audit = _load("audit")
    report = audit.run_audit(tmp_path / "audit.json", seeds=(0, 17, 29, 63))
    assert report["status"] == "pass"
    assert report["settings_checked"] == 8
    assert report["minimum_demo_survivors"] == 8
    assert report["alternative_pairs_checked"] == 40
    assert report["differs_from_skip_a"] == 40
    assert report["unique_largest_intermediates"] == 40
    assert report["nontrivial_secondary_components"] == 40
    assert report["singleton_deletion_disagreements"] == 40
    assert report["eight_connectivity_disagreements"] == 40
    assert report["shortcut_rivals_checked"] == 8
    assert report["shortcut_rivals_refuted_by_minimum_demos"] == 8
    assert report["shortcut_rivals_disagree_on_queries"] == 8


def _paint_cells(cells, height, width):
    out = [[0] * width for _ in range(height)]
    for row, column in cells:
        out[row][column] = 8
    return out


def _remove_only_singleton_components(adapter, grid):
    cells = set().union(*(
        component for component in adapter.components(adapter.stage_a(grid))
        if len(component) > 1
    ))
    return _paint_cells(cells, len(grid), len(grid[0]))


def _largest_eight_connected_component(adapter, grid):
    remaining = set(adapter.stage_a(grid))
    parts = []
    while remaining:
        first = min(remaining)
        part = {first}
        stack = [first]
        remaining.remove(first)
        while stack:
            row, column = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    neighbor = (row + dr, column + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        part.add(neighbor)
                        stack.append(neighbor)
        parts.append(part)
    parts.sort(key=lambda part: (-len(part), min(part)))
    return _paint_cells(parts[0] if parts else set(), len(grid), len(grid[0]))


def test_two_demos_refute_singleton_deletion_and_eight_connectivity(adapter):
    episode = adapter.generate(29, SETTINGS[1], 2, 4)
    expected = [pair["output"] for pair in episode["train"]]
    remove_singletons = [
        _remove_only_singleton_components(adapter, pair["input"])
        for pair in episode["train"]
    ]
    eight_connected = [
        _largest_eight_connected_component(adapter, pair["input"])
        for pair in episode["train"]
    ]
    assert remove_singletons != expected
    assert eight_connected != expected
