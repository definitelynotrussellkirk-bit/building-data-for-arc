"""Focused tests for the proposed task-local parametric rule family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "964b23808a3c"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
SPEC = importlib.util.spec_from_file_location(
    f"parametric_prototype_{TASK_ID}", PROTOTYPE_PATH
)
assert SPEC is not None and SPEC.loader is not None
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=None) as live:
        yield live


@pytest.fixture(scope="module")
def episodes(bridge):
    return {
        setting: p.build_episode(17, bridge, setting)
        for setting in p.ALL_SETTINGS
    }


def test_setting_space_and_seed_selection_are_bounded_and_deterministic():
    assert p.DEFAULT_SETTING == p.RuleSetting("ends_in_5", "current")
    assert len(p.ALL_SETTINGS) == 4
    assert {setting.selector_mode for setting in p.ALL_SETTINGS} == {
        "ends_in_5", "contains_5"
    }
    assert {setting.segment_mode for setting in p.ALL_SETTINGS} == {
        "current", "previous"
    }
    assert [p.choose_setting(seed) for seed in range(8)] == list(p.ALL_SETTINGS) * 2
    with pytest.raises((TypeError, ValueError), match="seed.*nonnegative integer"):
        p.choose_setting(True)
    with pytest.raises((TypeError, ValueError), match="seed.*nonnegative integer"):
        p.choose_setting(-1)


def test_default_program_is_exact_canonical_and_all_variants_are_minimal_edits():
    source = p.canonical_rows()[0]["program_solution"]
    assert p.program() == source
    assert p.program(p.DEFAULT_SETTING) == source
    assert len({p.program(setting) for setting in p.ALL_SETTINGS}) == 4
    for setting in p.ALL_SETTINGS:
        text = p.program(setting)
        if setting.selector_mode == "ends_in_5":
            assert p.CANONICAL_SELECTOR_REJECT in text
        else:
            assert p.CONTAINS_FIVE_REJECT in text
        if setting.segment_mode == "current":
            assert p.CANONICAL_COLOR_BINDING in text
            assert p.CANONICAL_RANGE in text
        else:
            assert p.PREVIOUS_COLOR_BINDING in text
            assert p.PREVIOUS_RANGE in text


def test_python_default_matches_all_canonical_labels_and_parent_mirror():
    assert len(PAIRS) == 5
    parent = p.generator()
    for pair in PAIRS:
        assert p.python_transform(pair["input"], p.DEFAULT_SETTING) == pair["output"]
        assert p.python_transform(pair["input"], p.DEFAULT_SETTING) == parent.rule_mirror(
            pair["input"]
        )


def test_each_setting_has_racket_python_parity_on_one_complete_episode(episodes):
    for setting in p.ALL_SETTINGS:
        public, private = episodes[setting]
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert private["parameters"] == setting.as_dict()
        assert private["program_sha256"] == p.digest(p.program(setting))
        assert len(private["pairs"]) == 4
        for pair in private["pairs"]:
            assert pair["outputs"][setting.slug] == p.python_transform(
                pair["input"], setting
            )
        assert set(private["rivals"]) == {
            other.slug for other in p.ALL_SETTINGS if other != setting
        }
        assert all(item["demo_mismatches"] for item in private["rivals"].values())
        assert all(item["query_differs"] for item in private["rivals"].values())


def test_public_episode_hides_parameters_program_and_query_answer(episodes):
    chosen = p.choose_setting(17)
    public, private = episodes[chosen]
    assert private["parameters"] == chosen.as_dict()
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for secret in (
        "selector_mode", "segment_mode", "program", "parameters",
        "query_output", "rivals", "seed"
    ):
        assert secret not in encoded
    assert private["public_sha256"] == p.digest(p.encoded(public))


def test_noisy_training_pair_and_dense_query_distinguish_all_four_settings(episodes):
    _, private = episodes[p.DEFAULT_SETTING]
    noisy = private["pairs"][2]["outputs"]
    dense = private["pairs"][3]["outputs"]
    assert len({p.encoded(grid) for grid in noisy.values()}) == 4
    assert len({p.encoded(grid) for grid in dense.values()}) == 4
