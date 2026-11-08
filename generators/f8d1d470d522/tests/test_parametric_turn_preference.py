"""Focused checks for the proposed episode-level turn-preference prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "f8d1d470d522"
ROOT = find_root(__file__)
GENERATOR, SELECTED_SOURCE, _SOURCE_SHA = load_selected_generator(
    TASK_ID,
    root=ROOT,
)
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    entries = [
        row
        for row in json.loads(MANIFEST.read_text())["files"]
        if row.get("library_path") == identity
    ]
    entries.sort(key=lambda row: row.get("runtime_path") == identity)
    assert entries, "portable runtime must retain the parametric prototype"
    PROTOTYPE_PATH = ROOT / entries[0]["runtime_path"]
else:
    PROTOTYPE_PATH = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "turn-preference prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "f8d1d470d522_turn_preference_prototype",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_seed_choice_are_episode_level():
    p = prototype()
    assert p.PARAMETER_NAME == "turn_preference"
    assert p.ALLOWED_TURN_PREFERENCES == ("fewest", "most")
    assert p.DEFAULT_TURN_PREFERENCE == "fewest"
    assert {p.choose_parameters(seed)[p.PARAMETER_NAME] for seed in range(8)} == {
        "fewest",
        "most",
    }
    assert p.choose_parameters(17) == p.choose_parameters(17)
    with pytest.raises(TypeError, match="episode seed"):
        p.choose_parameters(True)


def test_shared_inputs_distinguish_settings_and_default_matches_canonical():
    p = prototype()
    seen = set()
    for seed in range(6):
        for pair_index in range(3):
            grid = p.build_input(seed, pair_index)
            frozen = tuple(map(tuple, grid))
            seen.add(frozen)
            assert GENERATOR.self_check(grid) == []
            fewest = p.python_reference(grid, turn_preference="fewest")
            most = p.python_reference(grid, turn_preference="most")
            assert fewest == GENERATOR.rule_mirror(grid)
            assert fewest != most
    assert len(seen) == 18


def test_episode_public_redaction_and_rival_checks_are_complete():
    p = prototype()
    for preference in p.ALLOWED_TURN_PREFERENCES:
        episode = p.build_episode(19, turn_preference=preference)
        public = p.public_challenge(episode)
        assert episode["parameter"] == {"turn_preference": preference}
        assert set(public) == {"schema", "train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert "parameter" not in repr(public)
        assert "turn_preference" not in repr(public)
        other = next(
            value
            for value in p.ALLOWED_TURN_PREFERENCES
            if value != preference
        )
        assert all(
            p.python_reference(pair["input"], turn_preference=other)
            != pair["output"]
            for pair in episode["train"]
        )


def test_racket_programs_are_distinct_and_setting_specific():
    p = prototype()
    programs = {
        preference: p.racket_program(preference)
        for preference in p.ALLOWED_TURN_PREFERENCES
    }
    assert programs["fewest"] != programs["most"]
    assert "TURN-PREFERENCE 'fewest" in programs["fewest"]
    assert "TURN-PREFERENCE 'most" in programs["most"]
    for preference, program in programs.items():
        assert p.rule_sha256(preference) == p.sha256_text(program)
