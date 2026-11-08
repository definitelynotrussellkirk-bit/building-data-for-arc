"""Checks for proposed lookup depth; existing production remains separate."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest


@pytest.fixture(scope="module")
def prototype():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    assert path.is_file(), "The lookup-depth prototype must exist"
    spec = importlib.util.spec_from_file_location("_lookup_depth_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _board(panels):
    height = max(len(panel) for panel in panels)
    out = [[] for _ in range(height)]
    for i, panel in enumerate(panels):
        for r in range(height):
            if i:
                out[r].append(9)
            out[r].extend(panel[r] if r < len(panel) else [0] * len(panel[0]))
    return out


def test_second_lookup_consumes_the_selected_value(prototype):
    v1 = [[2, 0], [5, 5]]
    v2 = [[1, 5], [5, 0]]
    grid = _board([[[1]], v1, [[2]], v2, [[1]]])
    before = copy.deepcopy(grid)
    assert prototype.mirror(grid, {"lookup_depth": 1}) == v1
    assert prototype.mirror(grid, {"lookup_depth": 2}) == v2
    grid2 = _board([[[1]], v1, [[2]], v2, [[2]]])
    assert prototype.mirror(grid2, {"lookup_depth": 1}) == v2
    assert prototype.mirror(grid2, {"lookup_depth": 2}) == v1
    assert grid == before


def test_self_loop_is_not_unconditional_inversion(prototype):
    v1, v2 = [[1, 5], [0, 5]], [[2, 5], [5, 0]]
    grid = _board([[[1]], v1, [[2]], v2, [[1]]])
    assert prototype.mirror(grid, {"lookup_depth": 1}) == v1
    assert prototype.mirror(grid, {"lookup_depth": 2}) == v1


def test_default_source_is_exact_selected_authority(prototype):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    programs = {v["program_solution"] for v in Catalog(find_root(__file__)).get(
        "0b6b3a286ad0")["variants"]}
    assert programs == {prototype.program({"lookup_depth": 1})}
    assert prototype.program({"lookup_depth": 2}).startswith("(rule!")
    assert prototype.program({"lookup_depth": 2}) not in programs


def test_matching_requires_orientation_color_and_every_nonzero_cell(prototype):
    key = [[1, 0, 0], [1, 0, 0], [1, 1, 1]]
    filled = [[1, 5, 5], [1, 5, 5], [1, 1, 1]]
    assert prototype.find_matches(filled, key) == [(0, 0)]
    assert prototype.find_matches(filled, key, wildcard=False) == []
    assert prototype.find_matches([[2 if v == 1 else 0 for v in row] for row in key], key) == []
    near = copy.deepcopy(key); near[0][0] = 0
    assert prototype.find_matches(near, key) == []
    rotated = [list(row) for row in zip(*key[::-1])]
    assert prototype.find_matches(rotated, key) == []


def test_inputs_are_matched_and_count_prefixes_are_stable(prototype):
    state = random.getstate()
    small = prototype.generate(17, {"lookup_depth": 1}, 3, 1)
    full = prototype.generate(17, {"lookup_depth": 1}, 6, 4)
    alt = prototype.generate(17, {"lookup_depth": 2}, 6, 4)
    assert random.getstate() == state
    assert full["train"][:3] == small["train"]
    assert full["test"][:1] == small["test"]
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in alt[split]]
    assert full["program_solution"] == prototype.program({"lookup_depth": 1})
    assert alt["program_solution"] == prototype.program({"lookup_depth": 2})
    assert full == prototype.generate(17, {"lookup_depth": 1}, 6, 4)
    full["train"][0]["input"][0][0] = 9
    assert small == prototype.generate(17, {"lookup_depth": 1}, 3, 1)


def test_three_demos_teach_both_branches_and_nontrivial_successors(prototype):
    for seed in (0, 17, 2**63 - 1):
        episode = prototype.generate(seed, {"lookup_depth": 2}, 3, 4)
        facts = [prototype.analyze(p["input"]) for p in episode["train"]]
        assert [p["first_index"] for p in facts] == [0, 1, 1]
        assert [p["second_index"] for p in facts] == [1, 1, 0]
        assert len({json.dumps(p["input"]) for p in episode["train"] + episode["test"]}) == 7
        for pair in episode["train"] + episode["test"]:
            p = prototype.parse(pair["input"])
            assert p["value1"] != p["value2"]
            for board in (p["query"], p["value1"], p["value2"]):
                # Supported successor states always visibly contain one key.
                assert bool(prototype.find_matches(board, p["key1"])) != bool(prototype.find_matches(board, p["key2"]))


def test_large_profile_has_real_content_and_tall_output(prototype):
    pairs = prototype.generate(17, {"lookup_depth": 2}, 3, 4)["test"]
    pair = next(p for p in pairs if len(p["input"]) == len(p["input"][0]) == 30)
    grid = pair["input"]
    assert len(grid) == len(grid[0]) == 30
    p = prototype.parse(grid)
    assert sum(v not in (0, 9) for row in grid for v in row) >= 220
    assert len(pair["output"]) >= 24 and len(pair["output"][0]) == 4
    occupied_rows = {r for r, row in enumerate(p["query"]) if any(v for v in row)}
    assert min(occupied_rows) == 0 and max(occupied_rows) == 29
    assert len(occupied_rows) >= 18
    assert any(row[-1] != 0 for row in p["query"])


def test_first_query_varies_in_size_branch_and_depth_effect(prototype):
    shapes, first_indices, depth_effects = set(), set(), set()
    for seed in range(16):
        pair = prototype.generate(seed, {"lookup_depth": 2}, 3, 1)["test"][0]
        facts = prototype.analyze(pair["input"])
        shapes.add(tuple(facts["input_shape"]))
        first_indices.add(facts["first_index"])
        depth_effects.add(facts["first_index"] != facts["second_index"])
    assert shapes == {(8, 25), (22, 29), (30, 30), (26, 28)}
    assert first_indices == {0, 1}
    assert depth_effects == {False, True}


def test_key_color_frequency_cannot_replace_either_lookup(prototype):
    for seed in (0, 17):
        first_rank, second_rank = set(), set()
        for pair in prototype.generate(seed, {"lookup_depth": 2}, 3, 4)["train"]:
            parts = prototype.parse(pair["input"])
            facts = prototype.analyze(pair["input"])
            colors = [next(v for row in parts[f"key{i}"] for v in row if v) for i in (1, 2)]
            for board, target, ranks in ((parts["query"], facts["first_index"], first_rank),
                    (facts["selected_value"], facts["second_index"], second_rank)):
                counts = [sum(v == color for row in board for v in row) for color in colors]
                assert min(counts) > 0
                ranks.add(counts[target] > counts[1 - target])
        assert first_rank == {False, True}
        assert second_rank == {False, True}


@pytest.mark.parametrize("settings", [None, {}, {"lookup_depth": True},
    {"lookup_depth": 1.0}, {"lookup_depth": "1"}, {"lookup_depth": 0},
    {"lookup_depth": 3}, {"lookup_depth": 1, "extra": 0}])
def test_settings_are_exact_and_bounded(prototype, settings):
    with pytest.raises(ValueError): prototype.program(settings)
    with pytest.raises(ValueError): prototype.generate(0, settings)


@pytest.mark.parametrize("seed", [True, -1, 1.0, "0", 2**63])
def test_seed_is_exact_and_bounded(prototype, seed):
    with pytest.raises(ValueError, match="seed"):
        prototype.generate(seed, {"lookup_depth": 1})


@pytest.mark.parametrize("demos,queries", [(True, 4), (2, 4), (7, 4), (3.0, 4),
    (3, True), (3, 0), (3, 5), (3, 4.0)])
def test_counts_are_independent_and_bounded(prototype, demos, queries):
    with pytest.raises(ValueError):
        prototype.generate(0, {"lookup_depth": 1}, demos, queries)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[-1]], [[10]], [[0] * 31]])
def test_bad_grids_fail_before_matching(prototype, grid):
    with pytest.raises(ValueError): prototype.mirror(grid, {"lookup_depth": 1})
