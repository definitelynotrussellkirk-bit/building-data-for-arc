"""Behavioral tests for the native parametric rotate-and-stamp family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_SHA256 = "60c823b90a2db3726057fb8390669582fa5ddf4beec72d9b79a23f528da00288"
SETTINGS = (
    {"rotation_rule": "anchor_color"},
    {"rotation_rule": "bbox_area_offset"},
)


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("review_693aba8e59d8_parametric_prototype", "prototype.py")


def _adapter():
    return _load("review_693aba8e59d8_parametric_adapter", "adapter.py")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_program_contract_preserves_exact_canonical_source_and_validates_settings():
    prototype = _prototype()
    canonical = prototype.program(SETTINGS[0])
    alternate = prototype.program(SETTINGS[1])

    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert alternate != canonical
    assert prototype.program(deepcopy(SETTINGS[0])) == canonical
    assert prototype.program(deepcopy(SETTINGS[1])) == alternate

    for invalid in ({}, {"rotation_rule": "unknown"}, {"rotation_rule": 1},
                    {"rotation_rule": "anchor_color", "extra": 1}, None):
        with pytest.raises(ValueError):
            prototype.program(invalid)


def test_adapter_exports_the_same_program_and_episode_contract():
    prototype = _prototype()
    adapter = _adapter()
    for settings in SETTINGS:
        assert adapter.program(settings) == prototype.program(settings)
        assert adapter.generate(9, settings, 2, 4) == prototype.generate(9, settings, 2, 4)


def test_inputs_are_setting_independent_and_labels_follow_selected_rule():
    prototype = _prototype()
    canonical = prototype.generate(7, SETTINGS[0], 2, 4)
    alternate = prototype.generate(7, SETTINGS[1], 2, 4)

    assert _inputs(canonical) == _inputs(alternate)
    assert any(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], alternate[split])
    )
    for episode, settings in ((canonical, SETTINGS[0]), (alternate, SETTINGS[1])):
        assert episode["program_solution"] == prototype.program(settings)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.transform(pair["input"], settings)


def test_supported_demo_and_query_counts_are_prefix_stable_and_distinct():
    prototype = _prototype()
    full = prototype.generate(13, SETTINGS[0], 6, 4)
    full_train = full["train"]
    full_test = full["test"]

    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = prototype.generate(13, SETTINGS[0], demos, queries)
            assert episode["train"] == full_train[:demos]
            assert episode["test"] == full_test[:queries]
            encoded = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)]
            assert len(encoded) == len(set(encoded))

    for bad in (1, 7, True, 2.0):
        with pytest.raises(ValueError):
            prototype.generate(0, SETTINGS[0], bad, 4)
    for bad in (0, 5, True, 1.0):
        with pytest.raises(ValueError):
            prototype.generate(0, SETTINGS[0], 2, bad)


def test_minimum_two_demonstrations_identify_each_setting_and_reject_shortcuts():
    prototype = _prototype()
    for seed in (0, 17, 101):
        for settings in SETTINGS:
            episode = prototype.generate(seed, settings, 2, 4)
            certificate = episode["certificate"]
            assert certificate["survivors"] == [settings["rotation_rule"]]
            assert certificate["identified"] is True
            assert certificate["query_answers_used_for_fitting"] is False
            assert certificate["query_identifiable"] == [True, True, True, True]

        facts = [prototype.features(pair["input"]) for pair in
                 prototype.generate(seed, SETTINGS[0], 2, 4)["train"]]
        assert {facts[0]["bbox_area_offset"], facts[1]["bbox_area_offset"]} == {1, 2}
        assert {facts[0]["base_cell_count"], facts[1]["base_cell_count"]} == {4, 5}


def test_fourth_query_is_substantive_30_by_30_and_touches_every_boundary():
    prototype = _prototype()
    episode = prototype.generate(23, SETTINGS[1], 3, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    facts = prototype.features(grid)

    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 90
    assert any(grid[0][col] for col in range(30))
    assert any(grid[29][col] for col in range(30))
    assert any(grid[row][0] for row in range(30))
    assert any(grid[row][29] for row in range(30))
    assert facts["bbox_area_offset"] in (1, 2)
    assert sum(value == 6 for row in output for value in row) == 4 * facts["base_cell_count"]
    assert all(value in (0, 6) for row in output for value in row)


def test_wrong_intermediate_changes_the_final_alternate_output():
    prototype = _prototype()
    episode = prototype.generate(17, SETTINGS[1], 2, 4)
    pair = episode["test"][3]
    actual_offset = prototype.features(pair["input"])["bbox_area_offset"]
    assert actual_offset in (1, 2)
    assert pair["output"] != prototype.transform_with_offset(pair["input"], wrong_offset=0)


def test_public_turn_exposes_only_demos_and_the_current_query_input():
    prototype = _prototype()
    episode = prototype.generate(5, SETTINGS[1], 3, 4)
    visible = json.loads(prototype.visible_turn(episode, 1))

    assert len(visible["train"]) == 3
    assert visible["test"] == [{"input": episode["test"][1]["input"]}]
    assert "settings" not in visible
    assert "program_solution" not in visible
    assert "output" not in visible["test"][0]

    private_mutation = deepcopy(episode)
    private_mutation["settings"] = {"rotation_rule": "anchor_color"}
    private_mutation["program_solution"] = "private changed program"
    private_mutation["test"][1]["output"] = [[9]]
    private_mutation["test"][2]["input"] = [[9]]
    private_mutation["test"][3]["input"] = [[8]]
    assert prototype.visible_turn(private_mutation, 1) == prototype.visible_turn(episode, 1)
