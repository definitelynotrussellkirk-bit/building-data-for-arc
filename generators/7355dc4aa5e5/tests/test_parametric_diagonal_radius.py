"""Focused tests for the proposed, non-production diagonal-radius prototype."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root

TASK_ID = "7355dc4aa5e5"
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
    assert proto.ALLOWED_DIAGONAL_RADII == (1, 2)
    assert proto.DEFAULT_DIAGONAL_RADIUS == 1
    assert proto.rule_source(1).strip() == _canonical_source()
    assert proto.rule_source(1) != proto.rule_source(2)


@pytest.mark.parametrize("radius", [None, True, False, 0, 3, 1.0, "1", [], {}])
def test_unsupported_radius_fails_closed(radius):
    proto = _prototype()
    with pytest.raises(ValueError, match="diagonal_radius"):
        proto.rule_source(radius)


def test_episode_rule_is_seeded_once_and_inputs_do_not_depend_on_chosen_radius():
    proto = _prototype()
    for seed in range(20261019, 20261029):
        first = proto.sample_episode(seed)
        second = proto.sample_episode(seed)
        assert first == second
        assert first["parameters"] == {
            "diagonal_radius": proto.diagonal_radius_for_seed(seed)
        }
        assert len(first["inputs"]) == 4
        assert first["train_count"] == 3
        assert first["inputs"] == proto.sample_inputs(seed)


def test_every_pair_is_a_lawful_cross_setting_witness_and_every_rotation_refutes_rival():
    proto = _prototype()
    for seed in proto.select_seeds(20261019)["seeds"]:
        episode = proto.sample_episode(seed)
        predictions = {
            radius: [proto.python_mirror(grid, radius) for grid in episode["inputs"]]
            for radius in proto.ALLOWED_DIAGONAL_RADII
        }
        assert all(
            predictions[1][index] != predictions[2][index]
            for index in range(len(episode["inputs"]))
        )
        chosen = episode["parameters"]["diagonal_radius"]
        for query_index in range(len(episode["inputs"])):
            scored = proto.score_rotation(predictions, chosen, query_index)
            assert scored["rivals"] == [{
                "diagonal_radius": 3 - chosen,
                "status": "refuted_by_demonstrations",
                "demonstration_mismatches": [
                    index for index in range(len(episode["inputs"]))
                    if index != query_index
                ],
                "query_disagrees": True,
            }]


def test_public_challenge_omits_hidden_rule_reference_code_and_query_answer():
    proto = _prototype()
    episode = proto.sample_episode(proto.select_seeds(20261019)["seeds"][0])
    radius = episode["parameters"]["diagonal_radius"]
    pairs = [
        {"input": grid, "output": proto.python_mirror(grid, radius)}
        for grid in episode["inputs"]
    ]
    challenge = proto.public_challenge(pairs)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == 3
    assert len(challenge["test"]) == 1
    assert set(challenge["test"][0]) == {"input"}
    serialized = json.dumps(challenge)
    assert "diagonal_radius" not in serialized
    assert "rule!" not in serialized
