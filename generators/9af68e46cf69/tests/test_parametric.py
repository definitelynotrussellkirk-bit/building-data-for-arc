"""Behavioral checks for enclosed-region ranking, separate from the base sampler."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK = "9af68e46cf69"
ROOT = find_root(__file__)
PATH = ROOT / "generators" / TASK / "workspace/parametric/adapter.py"
ALL = {"selection": "all_enclosed"}
LARGEST = {"selection": "largest_enclosed_region"}


@pytest.fixture(scope="module")
def adapter():
    assert PATH.is_file(), "The native enclosure-ranking adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("test_enclosure_ranking_adapter", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ring(h, w):
    return {(r, c) for r in range(h) for c in range(w)
            if r in (0, h - 1) or c in (0, w - 1)}


def literal_scene(tied=False):
    """Independent hand-built objects with known enclosed-region areas."""
    grid = [[9] * 20 for _ in range(18)]
    if tied:
        a = ring(3, 3) - {(0, 0)}
        b = ring(3, 5) | {(1, 2)}
    else:
        a = ring(4, 4) | {(1, 4)}
        b = ring(3, 9) | {(1, 4)}
    negative = ring(5, 12) - {(4, 6)}
    groups = [{(r + y, c + x) for r, c in shape}
              for shape, y, x in [(a, 1, 1), (b, 1, 9), (negative, 10, 4)]]
    for group in groups:
        for r, c in group:
            grid[r][c] = 1
    return grid, groups


def recolor(grid, groups):
    out = deepcopy(grid)
    for group in groups:
        for r, c in group:
            out[r][c] = 8
    return out


@pytest.mark.parametrize("tied,areas", [(False, [[4], [3, 3], []]), (True, [[1], [1, 1], []])])
def test_geometry_and_labels_use_largest_single_region_and_all_ties(adapter, tied, areas):
    grid, groups = literal_scene(tied)
    before = deepcopy(grid)
    info = adapter.analyze(grid)
    assert [obj["hole_areas"] for obj in info["objects"]] == areas
    assert info["maximum_score"] == (1 if tied else 4)
    assert adapter.validate_input(grid) == []
    assert adapter.mirror(grid, ALL) == recolor(grid, groups[:2])
    assert adapter.mirror(grid, LARGEST) == recolor(grid, groups[:2] if tied else groups[:1])
    assert grid == before


def test_default_keeps_exact_canonical_program_and_saved_labels(adapter):
    row = next(json.loads(line) for line in canonical_path(ROOT).open()
               if json.loads(line).get("task_id") == TASK)
    assert adapter.program(ALL) == row["program_solution"]
    for pair in row["train"] + row["test"]:
        assert adapter.mirror(pair["input"], ALL) == pair["output"]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_constructive_counts_domain_matching_and_teaching(adapter, seed, demos):
    episodes = [adapter.generate(seed, settings, demos, 4) for settings in (ALL, LARGEST)]
    for settings, episode in zip((ALL, LARGEST), episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert episode["program_solution"] == adapter.program(settings)
        for grid in inputs:
            assert adapter.validate_input(grid) == []
        assert adapter.teaching_check(episode, settings)["harmful_survivors"] == []
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]
    assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]


def test_minimum_and_substantive_thirty_canvas(adapter):
    episode = adapter.generate(17, LARGEST, 2, 4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [(9, 11), (12, 16), (22, 26), (30, 30)]
    grid = episode["test"][3]["input"]
    info = adapter.analyze(grid)
    cells = [p for obj in info["objects"] for p in obj["cells"]]
    assert len(cells) >= 100
    assert max(r for r, c in cells) - min(r for r, c in cells) + 1 >= 27
    assert max(c for r, c in cells) - min(c for r, c in cells) + 1 >= 27
    assert info["maximum_score"] >= 20


def test_tie_demo_repairs_a_real_teaching_hole_and_query_labels_do_not_fit_rivals(adapter):
    episode = adapter.generate(0, LARGEST, 2, 4)
    weak = {"train": episode["train"][:1], "test": episode["train"][1:2]}
    check = adapter.teaching_check(weak, LARGEST)
    assert "first_tie_only" in check["harmful_survivors"]
    strong = adapter.teaching_check(episode, LARGEST)
    assert "first_tie_only" in strong["eliminated"]
    assert "background_eight_connected" in strong["eliminated"]
    assert strong["harmful_survivors"] == []
    corrupted = deepcopy(episode)
    for pair in corrupted["test"]:
        pair["output"] = [[0]]
    assert adapter.teaching_check(corrupted, LARGEST) == strong


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_one_query_projection_has_stable_first_turn_and_no_private_metadata(adapter, queries):
    episode = adapter.generate(17, LARGEST, 3, queries)
    single = adapter.generate(17, LARGEST, 3, 1)
    public = adapter.public_view(episode)
    assert public == adapter.public_view(single)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    changed = deepcopy(episode)
    changed.update(settings=ALL, seed=-1, program_solution="secret", hidden="private")
    changed["test"][0]["output"] = [[0]]
    changed["train"][0]["private"] = "secret"
    assert public_challenge_bytes(adapter.public_view(changed)) == public_challenge_bytes(public)
    assert public_challenge_id(adapter.public_view(changed)) == public_challenge_id(public)
    public["train"][0]["input"][0][0] = 0
    assert adapter.public_view(episode) == adapter.public_view(single)


@pytest.mark.parametrize("settings", [{}, None, {"selection": True}, {"selection": 0}, {"selection": "largest"}, {"selection": "all_enclosed", "extra": 1}])
def test_unknown_or_wrong_type_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (1.0, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 1.0)])
def test_request_scalar_and_count_boundaries_are_strict(adapter, seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, ALL, demos, queries)


def test_grid_domain_rejects_invalid_palette_missing_witness_and_bad_projection(adapter):
    valid = adapter.generate(0, ALL, 2, 4)
    for value in (True, 1.0, 0, 8, -1):
        bad = deepcopy(valid["test"][0]["input"])
        bad[0][0] = value
        assert adapter.validate_input(bad)
    assert adapter.validate_input([])
    assert adapter.validate_input([[9], [9, 9]])
    grid, groups = literal_scene()
    for r, c in groups[2]:
        grid[r][c] = 9
    assert adapter.validate_input(grid)
    for index in (-1, True, 4):
        with pytest.raises((ValueError, TypeError)):
            adapter.public_view(valid, index)
