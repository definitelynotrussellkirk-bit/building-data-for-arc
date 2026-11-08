"""Focused tests for the separate episode-level slide-direction prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "536de2f7591b"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("slide_direction_parametric_prototype", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    matches = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def test_parameter_contract_and_canonical_program_identity():
    proto = _load()
    spec = proto.PARAMETER_SPEC["direction"]
    assert spec["allowed"] == ["left", "right"]
    assert spec["canonical_default"] == "left"
    left = proto.program_for("left", root=ROOT)
    right = proto.program_for("right", root=ROOT)
    assert left == _canonical_program()
    assert right != left
    assert "(reverse (range 0 glen))" in right
    with pytest.raises(ValueError):
        proto.program_for("up", root=ROOT)


def test_parameter_is_chosen_once_and_both_settings_have_seed_support():
    proto = _load()
    values = {proto.choose_parameters(seed)["direction"] for seed in range(64)}
    assert values == {"left", "right"}
    retained_values = {
        proto.choose_parameters(seed)["direction"] for seed in proto.DEFAULT_EVIDENCE_SEEDS
    }
    assert retained_values == {"left", "right"}
    for seed in range(8):
        assert proto.choose_parameters(seed) == proto.choose_parameters(seed)
    with pytest.raises(TypeError):
        proto.choose_parameters(True)


def test_materialized_episode_is_racket_verified_and_teaches_direction():
    proto = _load()
    evidence = proto.materialize_episode(0, difficulty="easy", root=ROOT)
    assert evidence["racket_verified"] is True
    assert evidence["selected_generator_self_check_passed"] is True
    assert len(evidence["public"]["train"]) == proto.N_TRAIN
    assert len(evidence["public"]["test"]) == proto.N_TEST
    assert all("output" not in pair for pair in evidence["public"]["test"])
    assert "parameter" not in evidence["public"]
    assert evidence["demonstration_difference_indices"] == list(range(proto.N_TRAIN))
    assert evidence["query_difference_indices"] == list(range(proto.N_TEST))
    assert all(pair["settings_disagree"] for pair in evidence["private"]["train"])
    assert all(pair["settings_disagree"] for pair in evidence["private"]["test"])
