"""Focused tests for the cue-parity parametric family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("parametric_2243318b8e96", HOME / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def test_default_program_is_exact_canonical_and_settings_are_strict():
    assert P.program(P.DEFAULT) == P.CANONICAL_PROGRAM
    assert P.SETTINGS == [
        {"parity_reference": "absolute"},
        {"parity_reference": "same_as_cue"},
        {"parity_reference": "opposite_to_cue"},
    ]
    with pytest.raises(ValueError):
        P.program({})
    with pytest.raises(ValueError):
        P.program({"parity_reference": "same_as_cue", "extra": 1})
    with pytest.raises(ValueError):
        P.program({"parity_reference": "unknown"})


def test_minimum_two_demo_lesson_identifies_all_three_settings_on_matched_inputs():
    episodes = [P.generate(17, setting, 2, 4) for setting in P.SETTINGS]
    inputs = [[pair["input"] for pair in ep["train"] + ep["test"]] for ep in episodes]
    assert inputs[0] == inputs[1] == inputs[2]
    for episode in episodes:
        cert = P.certify(episode)
        assert cert["survivors"] == [episode["settings"]]
        assert set(cert["rivals"].values()) == {"refuted"}


def test_demo_query_count_boundaries_and_four_query_bank_are_stable():
    for demos in (2, 3, 6):
        episode = P.generate(991, P.DEFAULT, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert len({P.digest(pair["input"]) for pair in episode["train"] + episode["test"]}) == demos + 4
    short = P.generate(991, P.DEFAULT, 2, 4)
    long = P.generate(991, P.DEFAULT, 6, 4)
    assert [x["input"] for x in short["test"]] == [x["input"] for x in long["test"]]
    for bad in (1, 7, True, 2.0):
        with pytest.raises(ValueError):
            P.generate(1, P.DEFAULT, bad, 4)
    for bad in (1, 3, 5, True, 4.0):
        with pytest.raises(ValueError):
            P.generate(1, P.DEFAULT, 2, bad)


def test_queries_cover_real_size_boundaries_and_substantive_30x30_content():
    episode = P.generate(1234, {"parity_reference": "same_as_cue"}, 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[-1] == (30, 30)
    assert len(set(shapes)) == 4
    stress = episode["test"][-1]["input"]
    profile = P.scene_profile(stress)
    assert profile["component_count"] == 6
    assert profile["nonzero_cells"] >= 60
    assert profile["row_span"] >= 24
    assert profile["column_span"] >= 24
    assert profile["boundary_components"] >= 2
    assert profile["diagonal_same_color_contacts"] >= 1


def test_public_turn_is_one_query_only_and_private_fields_do_not_leak():
    episode = P.generate(88, {"parity_reference": "opposite_to_cue"}, 3, 4)
    for index in range(4):
        visible = P.public_turn(episode, index)
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
        assert visible["test"][0]["input"] == episode["test"][index]["input"]
        assert "settings" not in repr(visible)
        assert "program" not in repr(visible)
    altered = copy.deepcopy(episode)
    altered["settings"] = {"parity_reference": "absolute"}
    altered["test"][0]["output"][0][0] = (altered["test"][0]["output"][0][0] + 1) % 10
    assert P.public_turn(altered, 0) == P.public_turn(episode, 0)


def test_scene_and_episode_verifiers_reject_forgery_and_malformed_types():
    episode = P.generate(9, P.DEFAULT, 2, 4)
    forged = copy.deepcopy(episode)
    forged["train"][0]["output"] = copy.deepcopy(forged["train"][1]["output"])
    with pytest.raises(ValueError):
        P.certify(forged)
    duplicated = copy.deepcopy(episode)
    duplicated["test"][0]["input"] = copy.deepcopy(duplicated["train"][0]["input"])
    with pytest.raises(ValueError):
        P.certify(duplicated)
    malformed = copy.deepcopy(episode)
    malformed["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError):
        P.certify(malformed)
