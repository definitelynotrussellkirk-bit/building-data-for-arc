"""Focused tests for the proposed, non-production triangle-growth prototype."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root

TASK_ID = "156bae9e7b79"
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    path = find_root(__file__) / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"].strip()
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def test_parameter_contract_is_small_and_default_program_is_exactly_canonical():
    proto = _prototype()
    assert proto.ALLOWED_GROWTH_RATES == (1, 2)
    assert proto.DEFAULT_GROWTH_RATE == 1
    assert proto.TRAIN_COUNT == 3
    assert proto.PAIR_COUNT == 4
    assert proto.rule_source(1).strip() == _canonical_source()
    assert proto.rule_source(1) != proto.rule_source(2)


@pytest.mark.parametrize("rate", [None, True, False, 0, 3, 1.0, "1", [], {}])
def test_unsupported_growth_rate_fails_closed(rate):
    proto = _prototype()
    with pytest.raises(ValueError, match="growth_rate"):
        proto.rule_source(rate)


def test_episode_rule_is_seeded_once_and_inputs_do_not_depend_on_chosen_rate():
    proto = _prototype()
    for seed in range(20261021, 20261031):
        first = proto.sample_episode(seed)
        second = proto.sample_episode(seed)
        assert first == second
        assert first["parameters"] == {"growth_rate": proto.growth_rate_for_seed(seed)}
        assert len(first["inputs"]) == proto.PAIR_COUNT
        assert first["train_count"] == proto.TRAIN_COUNT
        assert first["inputs"] == proto.sample_inputs(seed)


def test_every_pair_distinguishes_settings_and_every_rotation_refutes_the_rival():
    proto = _prototype()
    for seed in proto.select_seeds(20261021)["seeds"]:
        episode = proto.sample_episode(seed)
        predictions = {
            rate: [proto.python_mirror(grid, rate) for grid in episode["inputs"]]
            for rate in proto.ALLOWED_GROWTH_RATES
        }
        assert all(
            predictions[1][index] != predictions[2][index]
            for index in range(proto.PAIR_COUNT)
        )
        chosen = episode["parameters"]["growth_rate"]
        for query_index in range(proto.PAIR_COUNT):
            scored = proto.score_rotation(predictions, chosen, query_index)
            assert scored["rivals"] == [{
                "growth_rate": 3 - chosen,
                "status": "refuted_by_demonstrations",
                "demonstration_mismatches": [
                    index for index in range(proto.PAIR_COUNT)
                    if index != query_index
                ],
                "query_disagrees": True,
            }]


def test_public_challenge_omits_hidden_rule_reference_code_and_query_answer():
    proto = _prototype()
    episode = proto.sample_episode(proto.select_seeds(20261021)["seeds"][0])
    rate = episode["parameters"]["growth_rate"]
    pairs = [
        {"input": grid, "output": proto.python_mirror(grid, rate)}
        for grid in episode["inputs"]
    ]
    challenge = proto.public_challenge(pairs)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == proto.TRAIN_COUNT
    assert len(challenge["test"]) == 1
    assert set(challenge["test"][0]) == {"input"}
    serialized = json.dumps(challenge)
    assert "growth_rate" not in serialized
    assert "rule!" not in serialized


def test_both_exact_racket_programs_match_independent_python_mirror():
    proto = _prototype()
    from arc_repl.isolated_verifier import verify_candidate

    racket_path = os.environ.get("RACKET_PATH")
    assert racket_path, "RACKET_PATH must be supplied by run_with_racket.py"
    inputs = proto.sample_inputs(20261021)
    for rate in proto.ALLOWED_GROWTH_RATES:
        canary_input = inputs[0]
        task = {
            "train": [{
                "input": canary_input,
                "output": proto.python_mirror(canary_input, rate),
            }],
            "test": [{"input": grid} for grid in inputs],
        }
        receipt = verify_candidate(task, proto.rule_source(rate), racket_path=racket_path)
        assert receipt["status"] == "pass", receipt
        assert receipt["backend"] == "racket"
        assert receipt["test_outputs"] == [
            proto.python_mirror(grid, rate) for grid in inputs
        ]
