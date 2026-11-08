"""Construction, teaching and API regressions for the native staircase family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def proto():
    spec = importlib.util.spec_from_file_location(
        "native_staircase_family_test", HOME / "workspace/parametric/prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_rich_motif_respects_requested_period_at_the_upper_boundary(proto):
    for period in (7, 8, 9):
        sequence = proto._rich_sequence(random.Random(0), period)
        assert len(sequence) == period
        grid = proto._staircase(sequence, True)
        assert proto._GEN.self_check(grid) == []
        assert len(grid) == period + 1


@pytest.mark.parametrize("seed", [0, 1, 17, 22, 131, 2**80 + 7])
def test_counts_prefixes_settings_and_novelty_share_one_input_bank(proto, seed):
    complete = proto.generate(seed, {"output_scale": 2}, demos=6, queries=4)
    inputs = [p["input"] for p in complete["train"] + complete["test"]]
    assert len({key(g) for g in inputs}) == 10
    assert all(proto._GEN.self_check(g) == [] for g in inputs)
    for demos in (2, 3, 6):
        for queries in (1, 4):
            for scale in (2, 3):
                episode = proto.generate(seed, {"output_scale": scale}, demos=demos, queries=queries)
                assert [p["input"] for p in episode["train"]] == inputs[:demos]
                assert [p["input"] for p in episode["test"]] == inputs[6:6 + queries]
                for pair in episode["train"] + episode["test"]:
                    assert pair["output"] == proto.solve(pair["input"], output_scale=scale)


@pytest.mark.parametrize("seed", [0, 1, 17, 22])
@pytest.mark.parametrize("scale", [2, 3])
def test_first_two_demos_teach_declared_rivals_without_query_answers(proto, seed, scale):
    episode = proto.generate(seed, {"output_scale": scale}, demos=2, queries=4)
    observed = [proto._GEN.observe_overrides(p["input"]) for p in episode["train"]]
    assert {o["padding"] for o in observed} == {"one", "none"}
    assert any(o["period"] > 5 for o in observed)
    assert {len(p["input"]) == 5 for p in episode["train"]} == {True, False}
    for query in episode["test"]:
        assert proto.lesson_identifiable(episode["train"], {"input": query["input"]}, output_scale=scale) == []
    for name in proto.RIVAL_NAMES:
        assert any(proto._rival_outputs(p["input"], output_scale=scale)[name] != p["output"]
                   for p in episode["train"]), name


def test_large_query_uses_full_continuation_canvas_and_padding_dependency(proto):
    for seed in (0, 17, 22):
        episode = proto.generate(seed, {"output_scale": 3}, demos=3, queries=4)
        pair = episode["test"][3]
        grid, answer = pair["input"], pair["output"]
        assert len(grid) == len(grid[0]) == 10
        assert grid[-1] == [0] * 10
        assert len(proto._active_diagonal(grid)) == 9
        assert len(answer) == len(answer[0]) == 30
        assert all(c != 0 for row in answer for c in row)
        assert len({c for row in answer for c in row}) >= 4
        assert proto._rival_outputs(grid, output_scale=3)["keep_terminal_zero_in_period"] != answer
        assert answer[0] == [grid[i % 9][i % 9] for i in range(30)]


def test_sampler_varies_relational_patterns_not_only_palette(proto):
    structures = set()
    patterns = set()
    periods = set()
    for seed in range(12):
        episode = proto.generate(seed, {"output_scale": 2}, demos=6, queries=4)
        for pair in episode["train"] + episode["test"]:
            obs = proto._GEN.observe_overrides(pair["input"])
            patterns.add(obs["pattern_class"])
            periods.add(obs["period"])
        seq = proto._active_diagonal(episode["train"][1]["input"])
        palette = list(dict.fromkeys(seq))
        structures.add(tuple(palette.index(c) for c in seq))
    assert len(structures) >= 4
    assert patterns == {"distinct", "prefix_run", "complex_repeat"}
    assert min(periods) == 4 and max(periods) == 9


def test_outputs_are_independent_and_calls_are_pure(proto):
    settings = {"output_scale": 3}
    before = deepcopy(settings)
    episode = proto.generate(17, settings, demos=2, queries=4)
    reference = deepcopy(episode)
    episode["train"][0]["input"][0][0] = 0
    episode["test"][0]["output"][0][0] = 0
    assert settings == before
    assert proto.generate(17, settings, demos=2, queries=4) == reference


@pytest.mark.parametrize("settings", [None, 2, {}, {"output_scale": True},
    {"output_scale": 2.0}, {"output_scale": "2"}, {"output_scale": 1},
    {"output_scale": 4}, {"output_scale": 2, "extra": 1}])
def test_native_settings_fail_closed(proto, settings):
    with pytest.raises(ValueError):
        proto.program(settings)
    with pytest.raises(ValueError):
        proto.generate(0, settings)


@pytest.mark.parametrize("kwargs", [
    {"seed": -1}, {"seed": True}, {"seed": 1.0}, {"seed": "1"},
    {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 1.0},
])
def test_native_counts_and_seed_fail_closed(proto, kwargs):
    request = {"seed": 0, "settings": {"output_scale": 2}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        proto.generate(**request)
