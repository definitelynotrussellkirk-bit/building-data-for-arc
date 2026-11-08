"""Focused tests for the separate episode-level rotation prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "371eb0221101"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("rotation_parametric_prototype", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_program_identity():
    proto = _load()
    assert proto.PARAMETER_SPEC["quarter_turns"]["allowed"] == [1, 3]
    assert proto.PARAMETER_SPEC["quarter_turns"]["canonical_default"] == 1
    canonical = proto.program_for(1, root=ROOT)
    alternative = proto.program_for(3, root=ROOT)
    assert canonical != alternative
    assert canonical.count("(t3b-rotate-offsets offs 1)") == 1
    assert alternative.count("(t3b-rotate-offsets offs 3)") == 1


def test_parameter_is_chosen_once_and_both_settings_have_seed_support():
    proto = _load()
    values = {proto.choose_parameters(seed)["quarter_turns"] for seed in range(32)}
    assert values == {1, 3}
    for seed in range(8):
        assert proto.choose_parameters(seed) == proto.choose_parameters(seed)


def test_materialized_episode_is_racket_verified_and_teaches_selected_setting():
    proto = _load()
    evidence = proto.materialize_episode(0, difficulty="easy", root=ROOT)
    assert evidence["racket_verified"] is True
    assert len(evidence["public"]["train"]) == proto.N_TRAIN
    assert len(evidence["public"]["test"]) == proto.N_TEST
    assert all("output" not in pair for pair in evidence["public"]["test"])
    assert "parameter" not in evidence["public"]
    assert evidence["demonstration_difference_indices"]
    assert evidence["query_difference_indices"] == [0]
    assert all(pair["settings_disagree"] for pair in evidence["private"]["train"])
    assert all(pair["settings_disagree"] for pair in evidence["private"]["test"])
