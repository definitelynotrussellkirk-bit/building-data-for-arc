"""Focused tests for the isolated shift-distance prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "db95939a5dd0"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = (
    GENERATOR_PATH.parent / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "db95939a5dd0_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_program_materialization_are_bounded():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "shift_distance"
    assert proto.ALLOWED_SHIFT_DISTANCES == (1, 2)
    assert proto.DEFAULT_SHIFT_DISTANCE == 1
    assert proto.program_for(1) == proto.canonical_program()
    assert proto.program_for(1) != proto.program_for(2)
    assert proto.program_for(2).count("(- (second p) 2)") == 1
    assert proto.program_for(2).count("(+ (second p) 2)") == 1
    for bad in (True, False, 0, 3, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(bad)


def test_episode_parameter_choice_is_deterministic_and_reaches_both_settings():
    proto = _load_prototype()
    observed = {proto.choose_shift_distance(seed) for seed in range(32)}
    assert observed == set(proto.ALLOWED_SHIFT_DISTANCES)
    for seed in range(16):
        assert proto.choose_shift_distance(seed) == proto.choose_shift_distance(seed)
    with pytest.raises(TypeError):
        proto.choose_shift_distance(True)


def test_prototype_inputs_are_canonical_lawful_and_distinguish_distances():
    proto = _load_prototype()
    for pair_index in range(8):
        grid = proto.make_input(271828, pair_index)
        assert GEN.self_check(grid) == []
        assert proto.apply_python(grid, 1) == GEN._rule_output(grid)
        assert proto.apply_python(grid, 1) != proto.apply_python(grid, 2)
        assert proto.domain_errors(grid, distance=1) == []
        assert proto.domain_errors(grid, distance=2) == []


def test_complete_episode_uses_one_setting_and_demos_refute_the_other():
    proto = _load_prototype()
    for distance in proto.ALLOWED_SHIFT_DISTANCES:
        episode = proto.build_episode(9000 + distance, distance=distance)
        assert episode["parameters"] == {"shift_distance": distance}
        assert len(episode["demos"]) == 3
        assert set(episode["query"]) == {"input", "output"}
        for pair in [*episode["demos"], episode["query"]]:
            assert pair["output"] == proto.apply_python(pair["input"], distance)
        findings = proto.parameter_rival_findings(episode)
        rival = 2 if distance == 1 else 1
        assert findings[str(rival)]["fits_all_demos"] is False
        assert findings[str(rival)]["changes_query"] is True
        assert findings[str(rival)]["refuted_demo_indices"]


def test_public_challenge_redacts_hidden_rule_and_query_answer():
    proto = _load_prototype()
    episode = proto.build_episode(42, distance=2)
    public = proto.public_challenge(episode)
    text = json.dumps(public, sort_keys=True)
    assert public["task_id"] == TASK_ID
    assert len(public["demos"]) == 3
    assert set(public["query"]) == {"input"}
    assert "shift_distance" not in text
    assert "racket" not in text.lower()
    assert episode["query"]["output"] not in public.values()



def test_racket_callable_unwraps_rule_bang_without_parser_dependency():
    proto = _load_prototype()
    for distance in proto.ALLOWED_SHIFT_DISTANCES:
        source = proto.program_for(distance)
        callable_text = proto.racket_callable(distance)
        assert callable_text == source[len("(rule! ") : -1]
        assert callable_text.startswith("(lambda ")
        assert callable_text.endswith(")")
        assert "(rule!" not in callable_text


def test_racket_executor_reuses_one_live_bridge_for_multiple_inputs():
    proto = _load_prototype()
    with proto.RacketRuleExecutor(2) as executor:
        pid = executor.bridge_pid
        assert pid > 0
        for pair_index in range(3):
            grid = proto.make_input(314159, pair_index)
            assert executor.apply(grid) == proto.apply_python(grid, 2)
            assert executor.bridge_pid == pid
        assert executor.call_count == 3
        assert executor.closed is False
    assert executor.closed is True

def test_materialized_rule_files_match_program_factory(tmp_path: Path):
    proto = _load_prototype()
    paths = proto.materialize_rules(tmp_path)
    assert set(paths) == {1, 2}
    for distance, path in paths.items():
        assert path.read_text() == proto.program_for(distance) + "\n"
