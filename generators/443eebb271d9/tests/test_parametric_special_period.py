"""Focused tests for the isolated special-period rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "443eebb271d9"
ROOT = find_root(__file__)
GEN, _GEN_PATH, _GEN_SHA = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("special_period_prototype", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def _first_seed_for(value: int) -> int:
    for seed in range(10_000):
        if PROTOTYPE.choose_parameters(seed)[PROTOTYPE.PARAMETER_NAME] == value:
            return seed
    raise AssertionError(f"no deterministic seed selects special_period={value}")


def test_parameter_contract_and_episode_seed_choice_cover_both_settings() -> None:
    assert PROTOTYPE.PARAMETER_NAME == "special_period"
    assert PROTOTYPE.DEFAULT_SPECIAL_PERIOD == 3
    assert PROTOTYPE.ALLOWED_SPECIAL_PERIODS == (3, 2)
    assert {
        PROTOTYPE.choose_parameters(_first_seed_for(value))[PROTOTYPE.PARAMETER_NAME]
        for value in PROTOTYPE.ALLOWED_SPECIAL_PERIODS
    } == {2, 3}
    for seed in range(30):
        assert PROTOTYPE.choose_parameters(seed) == PROTOTYPE.choose_parameters(seed)
    with pytest.raises(TypeError, match="episode seed"):
        PROTOTYPE.choose_parameters(True)


def test_inputs_stay_in_selected_family_and_every_pair_distinguishes_settings() -> None:
    seen = set()
    for episode_seed in range(6):
        for pair_index in range(4):
            grid = PROTOTYPE.build_input(GEN, episode_seed, pair_index)
            seen.add(tuple(map(tuple, grid)))
            assert GEN.self_check(grid) == []
            default = PROTOTYPE.python_reference(grid, special_period=3)
            alternative = PROTOTYPE.python_reference(grid, special_period=2)
            assert default == GEN.rule_mirror(grid)
            assert default != alternative
    assert len(seen) >= 20


def test_racket_materialization_is_setting_specific() -> None:
    programs = {
        value: PROTOTYPE.racket_program({"special_period": value})
        for value in PROTOTYPE.ALLOWED_SPECIAL_PERIODS
    }
    assert programs[3] != programs[2]
    assert "(mod inst 3) 2" in programs[3]
    assert "(mod inst 2) 1" in programs[2]
    assert "rule!" not in programs[3]
    with pytest.raises(ValueError, match="special_period"):
        PROTOTYPE.racket_program({"special_period": 4})
    with pytest.raises(ValueError, match="special_period"):
        PROTOTYPE.python_reference([[0]], special_period=True)


def test_public_challenge_redacts_hidden_rule_and_query_answer() -> None:
    grid = PROTOTYPE.build_input(GEN, 7, 0)
    out = PROTOTYPE.python_reference(grid, special_period=3)
    episode = {
        "episode_seed": 7,
        "parameters": {"special_period": 3},
        "racket_program": "secret",
        "demos": [
            {"input": grid, "output": out},
            {"input": grid, "output": out},
            {"input": grid, "output": out},
        ],
        "query": {"input": grid, "output": out},
    }
    challenge = PROTOTYPE.public_challenge(episode)
    assert challenge["demos"] == episode["demos"]
    assert challenge["query"] == {"input": grid}
    serialized = repr(challenge)
    assert "special_period" not in serialized
    assert "racket" not in serialized.lower()
    assert "episode_seed" not in serialized
    challenge["demos"][0]["input"][0][0] = 9
    assert episode["demos"][0]["input"][0][0] == grid[0][0]
