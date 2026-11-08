"""Behavioral checks for the declared native request and teaching contracts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"Missing parametric {name} implementation"
    spec = importlib.util.spec_from_file_location(f"_sampling_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_episode_has_distinct_inputs_and_real_large_lattice():
    adapter = load("adapter")
    programs = load("programs")
    episode = adapter.generate(17, {"retention": "all"}, 3, 4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == 7
    large = [p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert len(large) == 1
    assert len(programs.region_data(large[0]["input"])) >= 20
    assert sum(v == 0 for row in large[0]["input"] for v in row) > 450
    assert all(type(v) is int for p in pairs for row in p["input"] for v in row)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_visible_demos_reject_finite_rivals_for_both_matched_settings(demos):
    adapter = load("adapter")
    programs = load("programs")
    episodes = [adapter.generate(8, {"retention": r}, demos, 4)
                for r in ("all", "largest_filled_component")]
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
    for retention, episode in zip(("all", "largest_filled_component"), episodes):
        alternative = "largest_filled_component" if retention == "all" else "all"
        assert any(programs.evaluate(p["input"], alternative) != p["output"]
                   for p in episode["train"])
        for rival in programs.rivals_for(retention):
            assert any(programs.evaluate(p["input"], retention, rival) != p["output"]
                       for p in episode["train"]), (retention, rival)


def test_query_count_is_independent_and_preserves_first_turn():
    adapter = load("adapter")
    short = adapter.generate(2, {"retention": "largest_filled_component"}, 2, 1)
    full = adapter.generate(2, {"retention": "largest_filled_component"}, 2, 4)
    assert short["train"] == full["train"]
    assert short["test"] == full["test"][:1]
    assert adapter.generate(2, {"retention": "largest_filled_component"}, 2, 4) == full


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"retention": "all"}, 3, 4),
    (-1, {"retention": "all"}, 3, 4),
    (0, {"retention": "all"}, True, 4),
    (0, {"retention": "all"}, 1, 4),
    (0, {"retention": "all"}, 7, 4),
    (0, {"retention": "all"}, 3, 0),
    (0, {"retention": "all"}, 3, 5),
    (0, {"retention": "all"}, 3, 4.0),
    (0, {"retention": "unknown"}, 3, 4),
    (0, {"retention": "all", "extra": 1}, 3, 4),
])
def test_invalid_requests_fail_clearly(seed, settings, demos, queries):
    adapter = load("adapter")
    with pytest.raises(ValueError):
        adapter.generate(seed, settings, demos, queries)


def test_sampler_rejects_impossible_geometry_and_exhaustion():
    sampler = load("sampler")
    with pytest.raises(ValueError):
        sampler.sample_grid(0, 10, 10, 5, 5)
    with pytest.raises(ValueError):
        sampler.sample_grid(0, 31, 20, 3, 3)
    with pytest.raises(ValueError):
        sampler.sample_grid(0, 10, 10, 2, 2, max_attempts=0)

