"""Focused contract regressions for the separate bounding-box peeling family."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK = "17ea562973ac"
ROOT = find_root(__file__)
ADAPTER = ROOT / "generators" / TASK / "workspace/parametric/adapter.py"


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER.is_file(), "The required native parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("test_missing_box_peeling_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(h, w, cells, color):
    top, left = min(r for r, c in cells), min(c for r, c in cells)
    bottom, right = max(r for r, c in cells), max(c for r, c in cells)
    return [[color if top <= r <= bottom and left <= c <= right
             and (r in (top, bottom) or c in (left, right)) else 0
             for c in range(w)] for r in range(h)]


def test_default_program_is_exact_authority_and_original_pairs_still_match(adapter):
    records = [json.loads(line) for line in canonical_path(ROOT).open()]
    row = next(row for row in records if row.get("task_id") == TASK)
    assert adapter.program({"peel_depth": 0}) == row["program_solution"]
    for pair in row["train"] + row["test"]:
        assert adapter.mirror(pair["input"], {"peel_depth": 0}) == pair["output"]


def test_peeling_requires_joint_boundary_selection_not_coordinate_ranks(adapter):
    outer = [(1, 2), (2, 1), (10, 6), (6, 12)]
    inner = [(3, 4), (4, 9), (8, 7), (5, 6)]
    grid = [[0] * 14 for _ in range(12)]
    for r, c in outer + inner:
        grid[r][c] = 6
    before = deepcopy(grid)
    info = adapter.analyze(grid)
    assert info["bbox"] == (1, 1, 10, 12)
    assert sorted(info["interior"]) == sorted(inner)
    assert info["inner_bbox"] == (3, 4, 8, 9)
    assert adapter.mirror(grid, {"peel_depth": 1}) == frame(12, 14, inner, 6)
    assert adapter.mirror(grid, {"peel_depth": 0}) == frame(12, 14, outer + inner, 6)
    assert grid == before


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_settings_matching_and_every_query_taught(adapter, seed, demos):
    episodes = [adapter.generate(seed, {"peel_depth": depth}, demos, 4) for depth in (0, 1)]
    for depth, episode in enumerate(episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"peel_depth": depth})
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        for grid in inputs:
            assert adapter.validate_input(grid) == []
            assert all(type(c) is int for row in grid for c in row)
        assert not adapter.teaching_check(episode, {"peel_depth": depth})["harmful_survivors"]
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
    assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]


def test_minimum_and_dense_full_canvas_queries(adapter):
    episode = adapter.generate(17, {"peel_depth": 1}, 2, 4)
    small, large = episode["test"][0]["input"], episode["test"][3]["input"]
    assert (len(small), len(small[0])) == (6, 7)
    assert (len(large), len(large[0])) == (30, 30)
    info = adapter.analyze(large)
    assert info["bbox"] == (0, 0, 29, 29)
    assert len(info["cells"]) >= 60
    t, l, b, r = info["inner_bbox"]
    assert (b - t + 1) * (r - l + 1) >= 400
    assert len(adapter.analyze(episode["train"][1]["input"])["interior"]) == 2


def test_two_survivor_demo_repairs_a_real_teaching_hole(adapter):
    episode = adapter.generate(0, {"peel_depth": 1}, 2, 4)
    weak = {"train": episode["train"][:1], "test": [episode["train"][1]]}
    assert "requires_three_survivors" in adapter.teaching_check(weak, {"peel_depth": 1})["harmful_survivors"]
    strong = adapter.teaching_check(episode, {"peel_depth": 1})
    assert "requires_three_survivors" in strong["eliminated"]
    assert strong["harmful_survivors"] == []
    mutated = deepcopy(episode)
    mutated["test"][0]["output"] = [[9]]
    assert adapter.teaching_check(mutated, {"peel_depth": 1})["survivors"] == strong["survivors"]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_first_turn_has_one_query_and_no_count_or_private_hints(adapter, queries):
    episode = adapter.generate(17, {"peel_depth": 1}, 3, queries)
    single = adapter.generate(17, {"peel_depth": 1}, 3, 1)
    view = adapter.public_view(episode)
    assert view == adapter.public_view(single)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    before = public_challenge_bytes(view)
    changed = deepcopy(episode)
    changed.update(settings={"peel_depth": 0}, seed=-1, private_hint="secret", program_solution="private")
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(adapter.public_view(changed)) == before
    assert public_challenge_id(adapter.public_view(changed)) == public_challenge_id(view)
    view["train"][0]["input"][0][0] = 9
    assert adapter.public_view(episode) == adapter.public_view(single)


@pytest.mark.parametrize("settings", [{}, {"peel_depth": True}, {"peel_depth": 1.0}, {"peel_depth": 2}, {"peel_depth": 0, "other": 1}, None])
def test_invalid_parameter_settings_are_rejected(adapter, settings):
    with pytest.raises((ValueError, TypeError)):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 1.0)])
def test_invalid_request_boundaries_are_rejected(adapter, seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, {"peel_depth": 0}, demos, queries)


def test_strict_grid_and_public_projection_reject_invalid_types(adapter):
    valid = adapter.generate(0, {"peel_depth": 0}, 2, 4)
    for value in (True, 1.0, -1, 10):
        bad = deepcopy(valid["test"][0]["input"])
        bad[0][0] = value
        assert adapter.validate_input(bad)
    assert adapter.validate_input([])
    assert adapter.validate_input([[0], [0, 0]])
    for index in (-1, True, 4):
        with pytest.raises((ValueError, TypeError)):
            adapter.public_view(valid, index)
