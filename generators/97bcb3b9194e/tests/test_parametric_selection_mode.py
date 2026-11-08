"""Focused tests for the isolated fewest/most selection prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "97bcb3b9194e"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load():
    assert PROTOTYPE_PATH.is_file(), "selection-mode prototype is missing"
    spec = importlib.util.spec_from_file_location("selection_mode_97bcb3b9194e", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program():
    import json

    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row.get("program_solution"))
    assert None not in programs and len(programs) == 1
    return programs.pop()


def test_parameter_contract_and_exact_canonical_default():
    proto = _load()
    assert proto.SELECTION_MODES == ("fewest", "most")
    assert proto.CANONICAL_DEFAULT == "fewest"
    assert proto.PARAMETER_SPEC["selection_mode"]["chosen_once_per_episode"] is True
    fewest = proto.program_for("fewest", root=ROOT)
    most = proto.program_for("most", root=ROOT)
    assert fewest == _canonical_program()
    assert most != fewest
    assert "(< (first a) (first b))" in fewest
    assert "(> (first a) (first b))" in most


def test_parameter_choice_is_deterministic_and_covers_both_settings():
    proto = _load()
    observed = {proto.choose_parameters(seed)["selection_mode"] for seed in range(64)}
    assert observed == set(proto.SELECTION_MODES)
    for seed in range(16):
        assert proto.choose_parameters(seed) == proto.choose_parameters(seed)


@pytest.mark.parametrize("bad", [True, 0, 1.0, "minimum", None])
def test_program_rejects_coerced_or_unknown_parameter_values(bad):
    proto = _load()
    with pytest.raises(ValueError):
        proto.program_for(bad, root=ROOT)


def test_racket_verified_episode_teaches_setting_and_hides_query_answer():
    proto = _load()
    evidence = proto.materialize_episode(0, difficulty="easy", root=ROOT)
    assert evidence["racket_verified"] is True
    assert evidence["demonstration_difference_indices"] == list(range(proto.N_TRAIN))
    assert evidence["query_difference_indices"] == [0]
    assert all(pair["settings_disagree"] for pair in evidence["private"]["train"])
    assert all(pair["settings_disagree"] for pair in evidence["private"]["test"])
    assert "parameter" not in evidence["public"]
    assert all("output" not in pair for pair in evidence["public"]["test"])


def test_retained_evidence_seeds_cover_both_parameter_settings():
    proto = _load()
    assert {
        proto.choose_parameters(seed)["selection_mode"]
        for seed in proto.DEFAULT_EVIDENCE_SEEDS
    } == set(proto.SELECTION_MODES)
