"""Focused contract tests for the task-local sort-order rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/sort_order_prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "sort-order prototype must be supplied"
    spec = importlib.util.spec_from_file_location("ee64_sort_order_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_original_setting_is_the_exact_canonical_program_and_alternative_is_distinct():
    proto = load_prototype()
    canonical = proto.canonical_program()
    assert proto.program_for("ascending") == canonical
    descending = proto.program_for("descending")
    assert descending != canonical
    assert "(> (obj-size a) (obj-size b))" in descending
    with pytest.raises(ValueError, match="sort_order"):
        proto.program_for("sideways")


def test_episode_parameter_is_chosen_once_and_both_settings_are_reachable():
    proto = load_prototype()
    assert {proto.setting_for_seed(seed) for seed in range(8)} == {"ascending", "descending"}
    for seed in range(8):
        assert proto.setting_for_seed(seed) == proto.setting_for_seed(seed)


@pytest.mark.parametrize("seed", [0, 1])
def test_complete_episode_teaches_its_fixed_sort_order(seed):
    proto = load_prototype()
    episode = proto.build_episode(seed, difficulty="medium", pair_count=4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["meta"]["sort_order"] == proto.setting_for_seed(seed)
    assert episode["meta"]["canonical_setting"] == "ascending"
    assert episode["meta"]["parameter_fixed_for_episode"] is True
    assert episode["meta"]["all_pairs_distinguish_alternative"] is True
    assert all(pair["output"] != pair["alternative_output"]
               for pair in episode["train"] + episode["test"])
