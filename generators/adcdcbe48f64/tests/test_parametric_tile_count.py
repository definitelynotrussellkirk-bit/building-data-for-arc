"""Focused tests for the isolated tile-count rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "adcdcbe48f64"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "tile_count.py"


def _load():
    assert PROTOTYPE_PATH.is_file(), "tile-count prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("tile_count_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_seeded_choice_are_bounded_and_stable():
    proto = _load()
    assert proto.TILE_COUNTS == (3, 5)
    assert proto.DEFAULT_TILE_COUNT == 5
    assert {proto.choose_tile_count(seed) for seed in range(64)} == {3, 5}
    for seed in range(64):
        assert proto.choose_tile_count(seed) == proto.choose_tile_count(seed)


@pytest.mark.parametrize("bad", [True, False, 0, 1, 2, 4, 6, "5", None])
def test_materialize_rule_rejects_invalid_tile_counts(bad):
    proto = _load()
    with pytest.raises((TypeError, ValueError)):
        proto.materialize_rule(bad)


def test_default_materialization_is_exact_canonical_authority():
    proto = _load()
    assert proto.materialize_rule(5) == proto.canonical_rule()
    assert proto.rule_hash(proto.materialize_rule(5))[:12] == "5ed1759c50b3"


def test_both_rules_execute_in_racket_and_disagree_on_the_same_input():
    proto = _load()
    grid = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]["input"]
    outputs = {
        count: proto.execute_rule(proto.materialize_rule(count), [grid])[0]
        for count in proto.TILE_COUNTS
    }
    for count, output in outputs.items():
        assert output == proto.python_apply(grid, count)
        assert len(output) == len(grid)
        assert len(output[0]) == count * len(grid[0])
    assert outputs[3] != outputs[5]


@pytest.mark.parametrize("count", [3, 5])
def test_episode_fixes_one_rule_and_all_pairs_distinguish_the_rival(count):
    proto = _load()
    episode = proto.build_episode(71 + count, tile_count=count, difficulty="medium", start=0)
    assert episode["private"]["parameters"] == {"tile_count": count}
    assert len(episode["challenge"]["train"]) == 3
    assert len(episode["challenge"]["test"]) == 1
    assert "output" not in episode["challenge"]["test"][0]
    check = episode["private"]["rival_setting_check"]
    assert check["rejected_by_demo_indices"] == [0, 1, 2]
    assert check["query_disagrees"] is True
    assert episode["private"]["all_pairs_separate_settings"] is True
