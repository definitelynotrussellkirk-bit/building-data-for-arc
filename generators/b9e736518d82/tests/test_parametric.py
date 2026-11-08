"""Focused tests for the task-local turn-half rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("b9e736518d82_parametric", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_materialized_program_preserves_canonical_default_and_changes_only_turn_choice():
    prototype = _load_prototype()
    larger = prototype.program_for("larger")
    smaller = prototype.program_for("smaller")
    assert larger == prototype.canonical_program()
    assert prototype.normalized_program_hash(larger) == "b8c560eed7ae"
    assert larger.count("(length half1) (length half2)") == 1
    assert smaller.count("(length half1) (length half2)") == 1
    assert "> (length half1) (length half2)" in larger
    assert "< (length half1) (length half2)" in smaller
    assert larger.replace("> (length half1) (length half2)", "< (length half1) (length half2)") == smaller


@pytest.mark.parametrize("policy", ["larger", "smaller"])
def test_episode_uses_one_policy_and_demonstrations_rule_out_the_rival(policy):
    prototype = _load_prototype()
    episode = prototype.generate_episode(314159, turn_policy=policy)
    assert episode["meta"]["turn_policy"] == policy
    assert len(episode["train"]) == 4
    assert len(episode["test"]) == 1
    assert all(
        pair["output"] == prototype.apply_policy(pair["input"], policy)
        for pair in episode["train"] + episode["test"]
    )
    rival = prototype.other_policy(policy)
    disagreements = [
        index
        for index, pair in enumerate(episode["train"])
        if prototype.apply_policy(pair["input"], rival) != pair["output"]
    ]
    assert len(disagreements) >= 1
    query = episode["test"][0]
    assert prototype.apply_policy(query["input"], rival) != query["output"]


def test_unforced_episode_parameter_is_seed_deterministic_and_not_pair_local():
    prototype = _load_prototype()
    first = prototype.generate_episode(271828)
    second = prototype.generate_episode(271828)
    assert first == second
    assert first["meta"]["turn_policy"] in prototype.TURN_POLICIES
    assert first["program"] == prototype.program_for(first["meta"]["turn_policy"])


def test_public_challenge_omits_hidden_rule_and_query_answers():
    prototype = _load_prototype()
    episode = prototype.generate_episode(161803, turn_policy="smaller")
    public = prototype.public_challenge(episode)
    encoded = json.dumps(public, sort_keys=True)
    assert "turn_policy" not in encoded
    assert "program" not in public
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


def test_real_racket_executes_both_parameter_settings():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    inputs = [pair["input"] for pair in prototype.generate_episode(424242, turn_policy="larger")["train"]]
    for policy in prototype.TURN_POLICIES:
        expected = [prototype.apply_policy(grid, policy) for grid in inputs]
        assert prototype.racket_outputs(prototype.program_for(policy), inputs) == expected
