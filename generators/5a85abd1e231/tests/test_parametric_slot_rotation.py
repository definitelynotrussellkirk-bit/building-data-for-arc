"""Focused tests for the separate episode-level slot-rotation prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "5a85abd1e231"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("compass_slot_rotation_prototype", PROTOTYPE_PATH)
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


def test_parameter_contract_and_exact_canonical_default() -> None:
    proto = _load()
    spec = proto.PARAMETER_SPEC["slot_rotation_quarters"]
    assert spec["allowed"] == [0, 1, 2, 3]
    assert spec["canonical_default"] == 0
    programs = {turns: proto.program_for(turns, root=ROOT) for turns in proto.ROTATIONS}
    assert programs[0] == _canonical_program()
    assert len(set(programs.values())) == 4
    with pytest.raises(ValueError, match="slot_rotation_quarters"):
        proto.program_for(4, root=ROOT)


def test_parameter_is_chosen_once_deterministically_and_retained_seeds_cover_all_settings() -> None:
    proto = _load()
    assert {proto.choose_parameters(seed)["slot_rotation_quarters"] for seed in range(128)} == set(
        proto.ROTATIONS
    )
    assert {
        proto.choose_parameters(seed)["slot_rotation_quarters"]
        for seed in proto.DEFAULT_EVIDENCE_SEEDS
    } == set(proto.ROTATIONS)
    for seed in range(8):
        assert proto.choose_parameters(seed) == proto.choose_parameters(seed)
    with pytest.raises(TypeError, match="seed"):
        proto.choose_parameters(True)


def test_canonical_program_is_racket_verified_against_every_labeled_pair() -> None:
    proto = _load()
    records = proto.verify_canonical_default(root=ROOT)
    assert len(records) == 3
    assert all(record["passed"] for record in records)


def test_materialized_episode_is_racket_labeled_publicly_redacted_and_identifiable() -> None:
    proto = _load()
    evidence = proto.materialize_episode(proto.DEFAULT_EVIDENCE_SEEDS[0], difficulty="easy", root=ROOT)
    selected = evidence["parameter"]["slot_rotation_quarters"]
    assert evidence["racket_verified"] is True
    assert evidence["selected_generator_self_check_passed"] is True
    assert len(evidence["public"]["train"]) == proto.N_TRAIN
    assert len(evidence["public"]["test"]) == proto.N_TEST
    assert all(set(pair) == {"input", "output"} for pair in evidence["public"]["train"])
    assert all(set(pair) == {"input"} for pair in evidence["public"]["test"])
    public_text = json.dumps(evidence["public"], sort_keys=True)
    assert all(secret not in public_text for secret in ("slot_rotation", "program", "seed", "query_output"))
    assert set(evidence["rivals"]) == set(proto.ROTATIONS) - {selected}
    for rival in evidence["rivals"].values():
        assert rival == {"demo_mismatches": [0, 1, 2], "query_differs": True}
    for pair in evidence["private"]["train"] + evidence["private"]["test"]:
        assert len({json.dumps(output) for output in pair["outputs"].values()}) == len(proto.ROTATIONS)
