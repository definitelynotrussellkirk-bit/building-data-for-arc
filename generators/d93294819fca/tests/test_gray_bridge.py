"""Tests for the opt-in prototype; canonical generator scope is unchanged."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"


def load():
    path = PROTO / "prototype.py"
    spec = importlib.util.spec_from_file_location("_d932_gray_bridge_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_program():
    from arcpuzzles.catalog import Catalog
    p = load()
    reference = Catalog(HOME.parents[1])._variants()["d93294819fca"][0]["program_solution"]
    assert p.program({"gray_role": "inert"}) == reference
    assert p.program({"gray_role": "bridge"}) != reference


@pytest.mark.parametrize("seed", [0, 17, 391, 2**63 - 1])
def test_matched_inputs_teaching_and_distinct_queries(seed):
    p = load()
    a = p.generate(seed, {"gray_role": "inert"}, 3, 4)
    b = p.generate(seed, {"gray_role": "bridge"}, 3, 4)
    assert [x["input"] for s in ("train", "test") for x in a[s]] == [
        x["input"] for s in ("train", "test") for x in b[s]]
    for setting, episode in (("inert", a), ("bridge", b)):
        inputs = [json.dumps(x["input"]) for s in ("train", "test") for x in episode[s]]
        assert len(inputs) == len(set(inputs)) == 7
        certificate = p.teaching_check(episode, {"gray_role": setting})
        assert certificate["ok"]
        assert certificate["surviving_rivals"] == []
        assert all(p.transform(x["input"], {"gray_role": setting}) == x["output"]
                   for s in ("train", "test") for x in episode[s])


def test_counts_do_not_change_prefix_or_first_turn():
    p = load()
    for value in p.GRAY_ROLES:
        s = {"gray_role": value}
        one = p.generate(17, s, 3, 1)
        four = p.generate(17, s, 3, 4)
        six = p.generate(17, s, 6, 4)
        assert one["train"] == four["train"] == six["train"][:3]
        assert one["test"] == four["test"][:1]
        assert four["test"] == six["test"]
        assert p.visible_turn(one, 0) == p.visible_turn(four, 0)
        for i in range(4):
            turn = p.visible_turn(four, i)
            assert set(turn) == {"train", "test"}
            assert turn["test"] == [{"input": four["test"][i]["input"]}]


def test_deterministic_without_global_rng_side_effects():
    p = load()
    before = random.getstate()
    a = p.generate(39, {"gray_role": "bridge"}, 3, 4)
    assert random.getstate() == before
    assert a == p.generate(39, {"gray_role": "bridge"}, 3, 4)


@pytest.mark.parametrize("height,width", [(8, 8), (8, 30), (30, 8), (30, 30)])
def test_actual_size_boundaries_and_unique_minima(height, width):
    p = load()
    for index in range(3):
        grid = p.sample_input(27, index, height, width)
        assert (len(grid), len(grid[0])) == (height, width)
        info = p.validate_input(grid)
        assert info["original_minimum_count"] == info["merged_minimum_count"] == 1
        assert info["original_components"] > info["merged_components"] >= 2
        if height == width == 30:
            assert info["original_components"] >= 16
            cells = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x]
            assert len(cells) >= 100
            assert max(r for r, c in cells) - min(r for r, c in cells) >= 24
            assert max(c for r, c in cells) - min(c for r, c in cells) >= 24
            assert any(9 <= r < 21 and 9 <= c < 21 for r, c in cells)


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", -1), ("seed", 2**63), ("seed", 1.5),
    ("demos", True), ("demos", 2), ("demos", 7), ("demos", 3.0),
    ("queries", True), ("queries", 0), ("queries", 5), ("queries", 4.0),
])
def test_rejects_invalid_request_values(name, value):
    p = load()
    args = dict(seed=0, settings={"gray_role": "inert"}, demos=3, queries=4)
    args[name] = value
    with pytest.raises(ValueError):
        p.generate(**args)


@pytest.mark.parametrize("settings", [{}, {"gray_role": "bad"}, {"gray_role": True},
                                       {"gray_role": "inert", "extra": 1}, None])
def test_rejects_undeclared_settings(settings):
    p = load()
    with pytest.raises(ValueError):
        p.program(settings)


def test_causal_and_gray_area_shortcuts_are_exposed_by_demos():
    p = load()
    episode = p.generate(0, {"gray_role": "bridge"}, 3, 4)
    first = episode["train"][0]
    assert p.rival_output(first["input"], "bridge", "wrong_order") != first["output"]
    assert p.rival_output(first["input"], "bridge", "ignore_gray_area") != first["output"]
    assert p.rival_output(first["input"], "bridge", "original_anchor") != first["output"]
    assert p.rival_output(episode["train"][1]["input"], "bridge", "smallest_unbridged") != episode["train"][1]["output"]


def test_demonstrations_refute_perimeter_shortcut_seed17():
    p = load()
    def perimeter(cells):
        return sum((r + dr, c + dc) not in cells for r, c in cells
                   for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    def prediction(grid):
        joined = [[3 if x == 5 else x for x in row] for row in grid]
        chosen = min(p.components(joined), key=perimeter)
        out = deepcopy(joined)
        for r, c in chosen:
            out[r][c] = 4
        return out
    episode = p.generate(17, {"gray_role": "bridge"}, 3, 4)
    assert any(prediction(pair["input"]) != pair["output"] for pair in episode["train"])


def test_teaching_check_rejects_wrong_labels_and_missing_branch():
    p = load()
    settings = {"gray_role": "bridge"}
    episode = p.generate(0, settings, 3, 4)
    bad = deepcopy(episode)
    bad["train"][0]["output"] = deepcopy(bad["train"][0]["input"])
    assert not p.teaching_check(bad, settings)["ok"]
    short = deepcopy(episode)
    short["train"] = [episode["train"][0], episode["train"][2]]
    cert = p.teaching_check(short, settings)
    assert not cert["ok"]
    assert "smallest_unbridged" in cert["surviving_rivals"]
    assert cert["query_disagreements"]["smallest_unbridged"]


def test_public_identity_ignores_private_fields_and_writer_rejects_duplicates(tmp_path):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    p = load()
    episode = p.generate(0, {"gray_role": "bridge"}, 3, 4)
    mutated = deepcopy(episode)
    mutated["program_solution"] = "private changed"
    mutated["metadata"] = {"seed": 999, "settings": {"gray_role": "inert"}}
    for pair in mutated["test"]:
        pair["output"] = [[0]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(mutated)
    assert public_challenge_id(episode) == public_challenge_id(mutated)
    p.write_batch([episode], tmp_path / "ok")
    files = list((tmp_path / "ok" / "public").glob("*.json"))
    assert len(files) == 1
    assert files[0].stem == public_challenge_id(episode)
    assert files[0].read_bytes() == public_challenge_bytes(episode)
    assert all(set(x) == {"input"} for x in json.loads(files[0].read_bytes())["test"])
    with pytest.raises(ValueError, match="duplicate"):
        p.write_batch([episode, mutated], tmp_path / "duplicate")
    assert not (tmp_path / "duplicate").exists()


def test_visible_turn_strips_pair_metadata():
    p = load()
    episode = p.generate(0, {"gray_role": "bridge"}, 3, 4)
    expected = p.visible_turn(episode, 0)
    episode["train"][0]["private_settings"] = {"gray_role": "bridge"}
    episode["train"][1]["private_seed"] = 42
    episode["test"][0]["private_program"] = "secret"
    assert p.visible_turn(episode, 0) == expected


def test_invalid_grids_and_tied_minima_are_not_admitted():
    p = load()
    for grid in ([[True]], [[3.0]], [[3], [3, 0]], [[10]], [[3, 0, 3]]):
        with pytest.raises(ValueError):
            p.validate_input(grid)
