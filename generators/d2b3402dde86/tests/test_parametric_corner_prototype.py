"""Focused tests for the task-local proposed corner-selection prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "d2b3402dde86"


def prototype_path() -> Path:
    root = find_root(__file__)
    candidates = (
        root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "workspace" / "parametric" / "prototype.py",
    )
    return candidates[0] if candidates[0].is_file() else candidates[1]


@pytest.fixture(scope="module")
def prototype():
    path = prototype_path()
    assert path.is_file(), "parametric prototype.py must exist"
    spec = importlib.util.spec_from_file_location("d2_corner_prototype", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_programs(prototype):
    assert prototype.PARAMETER_NAME == "corner"
    assert prototype.DEFAULT_SETTING == "upper_left"
    assert prototype.ALLOWED_SETTINGS == (
        "upper_left",
        "upper_right",
        "lower_left",
        "lower_right",
    )
    programs = [prototype.program_for(setting) for setting in prototype.ALLOWED_SETTINGS]
    assert len(set(programs)) == len(programs)
    assert all(program.startswith("(rule!") for program in programs)


def test_episode_setting_is_chosen_once_and_every_pair_distinguishes_all_corners(prototype):
    for seed in range(8):
        episode = prototype.build_episode(seed)
        setting = episode["meta"][prototype.PARAMETER_NAME]
        assert setting == prototype.choose_setting(seed)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        for pair in episode["train"] + episode["test"]:
            outputs = {
                candidate: prototype.apply_python(pair["input"], candidate)
                for candidate in prototype.ALLOWED_SETTINGS
            }
            assert len({prototype.freeze(grid) for grid in outputs.values()}) == 4
            assert pair["output"] == outputs[setting]


def test_original_setting_matches_the_selected_canonical_mirror(prototype):
    episode = prototype.build_episode(23, setting="upper_left")
    for pair in episode["train"] + episode["test"]:
        assert prototype.apply_python(pair["input"], "upper_left") == prototype.apply_canonical(pair["input"])


def test_public_challenge_hides_setting_program_and_query_answer(prototype):
    episode = prototype.build_episode(31, setting="lower_right")
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])
    rendered = repr(public)
    assert prototype.PARAMETER_NAME not in rendered
    assert "rule!" not in rendered


@pytest.mark.parametrize("bad", [True, 1.0, "1", None])
def test_invalid_episode_seed_is_rejected(prototype, bad):
    with pytest.raises(TypeError):
        prototype.build_episode(bad)


@pytest.mark.parametrize("bad", [True, 1, None, "center"])
def test_invalid_corner_is_rejected(prototype, bad):
    with pytest.raises((TypeError, ValueError)):
        prototype.program_for(bad)
