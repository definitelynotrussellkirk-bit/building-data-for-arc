"""Native parent-choice API, matched sampling, and deep teaching coverage."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/f59691ac00f3/workspace/parametric"
CANONICAL_SHA256 = "2e50ecc613be187d84268664bd1c2c33cf187efe48d02ecf8330366abd929a63"
LEFT_SHA256 = "941a9fe972678ace003991e35cb51637ca62a7a5dd484c10537c543e20fdea03"


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "the parent-choice native adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("f59691ac00f3_native_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


@pytest.fixture(scope="module")
def episodes(adapter):
    # Both settings on independent seeds, including each large-query profile.
    return {
        (seed, setting): adapter.generate(seed, {"different_parent": setting}, 6, 4)
        for seed in (0, 1, 17)
        for setting in ("right", "left")
    }


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def _active_depth(grid):
    return max(row for row, cells in enumerate(grid) if any(cell != 7 for cell in cells))


def _parent_pairs(top):
    return {(top[col], top[col + 2]) for col in range(len(top) - 2)
            if top[col] != 7 and top[col + 2] != 7}


def _literal(grids):
    return "'(" + " ".join(
        "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for grid in grids
    ) + ")"


def test_native_entrypoint_preserves_exact_canonical_default():
    adapter = _load_adapter()
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["adapter"] == "generators/f59691ac00f3/workspace/parametric/adapter.py"
    assert hashlib.sha256(adapter.program(promotion["default"]).encode()).hexdigest() == CANONICAL_SHA256
    assert hashlib.sha256(adapter.program({"different_parent": "left"}).encode()).hexdigest() == LEFT_SHA256


def test_native_loader_ignores_unrelated_cached_prototype(monkeypatch):
    unrelated = types.ModuleType("prototype")
    unrelated.materialize_rule = lambda *args, **kwargs: "wrong source"
    monkeypatch.setitem(sys.modules, "prototype", unrelated)
    adapter = _load_adapter()
    assert hashlib.sha256(adapter.program({"different_parent": "right"}).encode()).hexdigest() == CANONICAL_SHA256


@pytest.mark.parametrize("settings", [
    None, True, [], {}, {"different_parent": True}, {"different_parent": 0},
    {"different_parent": "both"}, {"different_parent": "RIGHT"},
    {"different_parent": "right", "extra": 1},
])
def test_invalid_settings_are_rejected_by_both_entrypoints(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 2, 4)


@pytest.mark.parametrize("seed", [True, False, -1, 1.5, "0", None, 2**63])
def test_seed_requires_native_bounded_plain_integer(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"different_parent": "right"}, 2, 4)


@pytest.mark.parametrize("demos,queries", [
    (1, 4), (7, 4), (True, 4), (2.0, 4), ("2", 4),
    (2, 0), (2, 5), (2, False), (2, 4.0), (2, None),
])
def test_unsupported_or_boolean_counts_are_rejected(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"different_parent": "right"}, demos, queries)


def test_explicit_settings_have_identical_inputs_but_distinct_teaching_labels(adapter, episodes):
    for seed in (0, 1, 17):
        right, left = episodes[seed, "right"], episodes[seed, "left"]
        for split in ("train", "test"):
            assert _inputs(right, split) == _inputs(left, split)
        for index in (0, 1):
            assert right["train"][index]["output"] != left["train"][index]["output"]
        for setting, episode in (("right", right), ("left", left)):
            assert episode["program_solution"] == adapter.program({"different_parent": setting})


def test_minimum_maximum_counts_and_query_prefix_are_independent(adapter, episodes):
    maximum = episodes[0, "right"]
    minimum = adapter.generate(0, {"different_parent": "right"}, 2, 1)
    four_queries = adapter.generate(0, {"different_parent": "right"}, 2, 4)
    assert (len(minimum["train"]), len(minimum["test"])) == (2, 1)
    assert (len(maximum["train"]), len(maximum["test"])) == (6, 4)
    assert minimum["train"] == maximum["train"][:2] == four_queries["train"]
    assert minimum["test"] == maximum["test"][:1]
    assert four_queries["test"] == maximum["test"]


def test_every_episode_has_strict_distinct_top_seed_inputs(episodes):
    for episode in episodes.values():
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(set(keys)) == 10
        for pair in pairs:
            grid, output = pair["input"], pair["output"]
            height, width = len(grid), len(grid[0])
            assert 3 <= height <= 30 and 5 <= width <= 30
            assert len(output) == height
            assert all(type(row) is list and len(row) == width for row in grid + output)
            assert all(type(cell) is int and cell in (2, 5, 7) for row in grid + output for cell in row)
            assert all(cell == 7 for row in grid[1:] for cell in row)
            assert _parent_pairs(grid[0])
            assert output[0] == grid[0] and output != grid


def test_teaching_covers_full_depth_extinction_and_internal_support_holes(episodes):
    for episode in episodes.values():
        dense, gapped = episode["train"][:2]
        assert (len(dense["input"]), len(dense["input"][0])) == (16, 30)
        assert all(value in (2, 5) for value in dense["input"][0])
        assert _parent_pairs(dense["input"][0]) == {(2, 2), (2, 5), (5, 2), (5, 5)}
        assert _active_depth(dense["output"]) == 14
        assert dense["output"][15] == [7] * 30
        assert sum(cell != 7 for row in dense["output"] for cell in row) == 240
        top = gapped["input"][0]
        assert top[0] != 7 and top[2] == 7 and top[4] != 7
        assert gapped["output"][2][2] == 7
        assert _parent_pairs(top) == {(2, 2), (2, 5), (5, 2), (5, 5)}
        assert max(_active_depth(pair["output"]) for pair in episode["train"]) >= max(
            _active_depth(pair["output"]) for pair in episode["test"]
        )


def test_four_queries_cover_minimum_gapped_and_two_full_size_grids(episodes):
    for episode in episodes.values():
        minimum, medium, dense, varied = episode["test"]
        dimensions = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert dimensions[0] == (3, 5)
        assert minimum["input"][0] in ([2, 7, 5, 7, 2], [5, 7, 2, 7, 5])
        assert minimum["output"][2][2] == minimum["input"][0][0]
        assert 3 < dimensions[1][0] < 30 and 5 < dimensions[1][1] < 30
        assert 7 in medium["input"][0] and medium["input"][0][0] != 7
        assert dimensions[2:] == [(30, 30), (30, 30)]
        assert all(cell != 7 for cell in dense["input"][0])
        assert _active_depth(dense["output"]) == 14
        assert sum(cell != 7 for row in dense["output"] for cell in row) == 240
        assert dense["input"] != varied["input"]
    assert len(set(episodes[1, "right"]["test"][3]["input"][0])) == 1
    assert 7 in episodes[0, "right"]["test"][3]["input"][0]
    assert 7 in episodes[17, "right"]["test"][3]["input"][0]


def test_all_labels_replay_through_independent_protected_rule_wrapper(episodes):
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for episode in episodes.values():
            pairs = episode["train"] + episode["test"]
            expression = f"(map {wrap_rule(episode['program_solution'])} {_literal([p['input'] for p in pairs])})"
            assert bridge.eval_text(expression) == [pair["output"] for pair in pairs]
