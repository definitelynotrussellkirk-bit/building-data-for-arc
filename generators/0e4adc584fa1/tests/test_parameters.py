from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK = "0e4adc584fa1"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_native_family_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_parametric_files_exist():
    expected = {
        "adapter.py",
        "native_family.py",
        "canonical.rkt",
        "promotion.json",
        "audit.py",
    }
    assert expected <= {path.name for path in HOME.iterdir() if path.is_file()}


def test_canonical_program_is_exact_and_settings_are_strict():
    family = _load()
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert family.program({"control_selector": "last_isolated"}) == canonical
    assert family.program({"control_selector": "nearest_object"}) != canonical
    for bad in (
        {},
        {"control_selector": "nearest"},
        {"control_selector": 1},
        {"control_selector": "last_isolated", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            family.program(bad)


def test_counts_are_prefix_stable_and_inputs_match_across_settings():
    family = _load()
    small = family.generate(17, {"control_selector": "nearest_object"}, 2, 1)
    large = family.generate(17, {"control_selector": "nearest_object"}, 6, 4)
    canonical = family.generate(17, {"control_selector": "last_isolated"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert _inputs(large) == _inputs(canonical)
    frozen = {tuple(map(tuple, grid)) for grid in _inputs(large)}
    assert len(frozen) == 10


def test_every_scene_has_a_unique_geometry_selected_control_and_setting_signal():
    family = _load()
    for seed in (0, 17, 31):
        nearest = family.generate(seed, {"control_selector": "nearest_object"}, 6, 4)
        canonical = family.generate(seed, {"control_selector": "last_isolated"}, 6, 4)
        for near_pair, canonical_pair in zip(
            nearest["train"] + nearest["test"],
            canonical["train"] + canonical["test"],
        ):
            summary = family.scene_summary(near_pair["input"])
            assert summary["isolated_controls"] >= 3
            assert summary["nearest_unique"] is True
            assert summary["nearest_code"] != summary["last_code"]
            assert summary["object_cells"] >= 20
            assert near_pair["output"] == family.reference(
                near_pair["input"], {"control_selector": "nearest_object"}
            )
            assert canonical_pair["output"] == family.reference(
                canonical_pair["input"], {"control_selector": "last_isolated"}
            )
            assert near_pair["output"] != canonical_pair["output"]


def test_max_query_is_substantive_30x30_and_causal_counterfactual_changes_output():
    family = _load()
    episode = family.generate(0, {"control_selector": "nearest_object"}, 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    summary = family.scene_summary(grid)
    assert [len(grid), len(grid[0])] == [30, 30]
    assert summary["object_cells"] >= 140
    assert summary["object_bbox_height"] >= 20
    assert summary["object_bbox_width"] >= 20
    assert pair["output"] != family.reference(
        grid, {"control_selector": "last_isolated"}
    )


def test_public_turn_masks_answers_and_future_queries_without_mutation():
    family = _load()
    episode = family.generate(9, {"control_selector": "nearest_object"}, 3, 4)
    snapshot = deepcopy(episode)
    visible = family.public_turn(episode, 2)
    assert episode == snapshot
    assert set(visible) == {"train", "test"}
    assert visible["train"] == episode["train"]
    assert visible["test"] == [{"input": episode["test"][2]["input"]}]
    assert "program_solution" not in visible


def test_declared_rivals_are_refuted_by_minimum_two_demos():
    family = _load()
    for settings in family.SETTINGS:
        for seed in (0, 17, 31):
            episode = family.generate(seed, settings, 2, 4)
            assert family.teaching_survivors(episode["train"], settings) == (
                family.setting_name(settings),
            )
