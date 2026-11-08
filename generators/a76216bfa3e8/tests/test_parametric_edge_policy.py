from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "a76216bfa3e8"
ROOT = find_root(__file__)
GEN, _GEN_PATH, _GEN_SHA = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("a762_edge_policy_prototype", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def _first_seed_for(setting: str) -> int:
    for seed in range(1000):
        if PROTOTYPE.choose_parameters(seed)[PROTOTYPE.PARAMETER_NAME] == setting:
            return seed
    raise AssertionError(setting)


def test_parameter_contract_and_episode_seed_cover_both_settings():
    assert PROTOTYPE.PARAMETER_NAME == "edge_policy"
    assert PROTOTYPE.DEFAULT_SETTING == "clip"
    assert PROTOTYPE.SETTINGS == ("clip", "full_only")
    assert PROTOTYPE.DEFAULT_DEMO_COUNT == 4
    assert PROTOTYPE.DEFAULT_QUERY_COUNT == 4
    assert {
        PROTOTYPE.choose_parameters(_first_seed_for(setting))["edge_policy"]
        for setting in PROTOTYPE.SETTINGS
    } == set(PROTOTYPE.SETTINGS)
    for seed in range(20):
        assert PROTOTYPE.choose_parameters(seed) == PROTOTYPE.choose_parameters(seed)
    with pytest.raises(TypeError, match="episode seed"):
        PROTOTYPE.choose_parameters(True)


def test_python_reference_preserves_canonical_clip_and_changes_partial_cells():
    grid = PROTOTYPE.build_input(17, 0)
    assert GEN.self_check(grid) == []
    clipped = PROTOTYPE.apply_python(grid, "clip")
    full_only = PROTOTYPE.apply_python(grid, "full_only")
    assert clipped == GEN.rule_mirror(grid)
    assert full_only == GEN.rival_skip_partial_cells(grid)
    assert clipped != full_only
    with pytest.raises(ValueError, match="edge_policy"):
        PROTOTYPE.apply_python(grid, "unknown")


def test_complete_episode_has_fixed_setting_distinct_inputs_and_identifiable_demos():
    for setting in PROTOTYPE.SETTINGS:
        seed = _first_seed_for(setting)
        episode = PROTOTYPE.build_episode(seed, demo_count=4, query_count=4)
        assert episode["parameter"]["value"] == setting
        assert episode["counts"] == {"demonstrations": 4, "queries": 4}
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({tuple(map(tuple, grid)) for grid in inputs}) == 8
        assert all(GEN.self_check(grid) == [] for grid in inputs)
        assert PROTOTYPE.surviving_settings(episode["train"]) == [setting]
        assert all(
            PROTOTYPE.apply_python(pair["input"], "clip")
            != PROTOTYPE.apply_python(pair["input"], "full_only")
            for pair in episode["train"] + episode["test"]
        )


def test_setting_specific_racket_and_public_projection_hide_private_answers():
    programs = {setting: PROTOTYPE.racket_program(setting) for setting in PROTOTYPE.SETTINGS}
    assert programs["clip"] != programs["full_only"]
    assert "full 3x3 destination cells only" in programs["full_only"]

    episode = PROTOTYPE.build_episode(_first_seed_for("clip"), demo_count=4, query_count=4)
    public = PROTOTYPE.public_challenge(episode)
    assert list(public) == ["train", "test"]
    assert len(public["train"]) == 4
    assert len(public["test"]) == 4
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public_challenge_bytes(public) == public_challenge_bytes(episode)
    serialized = public_challenge_bytes(public).decode("utf-8")
    assert "edge_policy" not in serialized
    assert "full_only" not in serialized
    assert "racket" not in serialized.lower()
    filename = PROTOTYPE.public_identifier(episode)
    assert filename.startswith("challenge-") and filename.endswith(".json")
    assert "clip" not in filename and "full" not in filename
