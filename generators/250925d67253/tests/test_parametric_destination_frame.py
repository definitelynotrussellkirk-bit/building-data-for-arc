"""Focused tests for the task-local destination-frame rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "250925d67253"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "destination-frame prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_destination_frame_250925d67253", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_rule() -> str:
    root = find_root(__file__)
    with (root / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"canonical row {TASK_ID} not found")


def test_parameter_contract_and_canonical_default_rule_are_exact():
    prototype = _load_prototype()
    assert prototype.PARAMETER_SPEC == {
        "name": "destination_frame",
        "values": ("identity", "transpose"),
        "default": "identity",
    }
    assert prototype.materialize_rule("identity") == _canonical_rule()
    transpose = prototype.materialize_rule("transpose")
    assert transpose != _canonical_rule()
    assert "(cons tC tR)" in transpose
    with pytest.raises(ValueError):
        prototype.materialize_rule("rotate90")


def test_parameter_is_episode_scoped_and_both_settings_are_reachable():
    prototype = _load_prototype()
    assert prototype.choose_destination_frame(0) == "identity"
    assert prototype.choose_destination_frame(1) == "transpose"
    assert prototype.choose_destination_frame(0) == prototype.choose_destination_frame(0)
    with pytest.raises(TypeError):
        prototype.choose_destination_frame(True)


@pytest.mark.parametrize("frame", ["identity", "transpose"])
def test_complete_episode_refutes_the_other_setting_and_public_view_is_redacted(frame):
    prototype = _load_prototype()
    episode = prototype.build_episode(
        seed=19,
        destination_frame=frame,
        difficulty="medium",
        start_index=2,
        n_train=3,
        n_test=1,
    )
    assert episode["meta"]["parameters"] == {"destination_frame": frame}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert prototype.parameter_rival_findings(episode) == []

    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "meta" not in public


def test_bounded_evidence_executes_both_racket_rules_and_matches_python():
    prototype = _load_prototype()
    report = prototype.build_evidence(
        seeds=[0, 1],
        difficulty="easy",
        start_index=0,
        n_train=2,
        n_test=1,
    )
    assert report["status"] == "proposed"
    assert report["completion_state"] == "complete"
    assert report["passed"] is True
    assert report["counts"] == {
        "settings_materialized": 2,
        "episodes": 2,
        "distinct_settings_demonstrated": 2,
        "canonical_pairs": 8,
        "canonical_passed": 8,
        "racket_label_executions": 6,
        "python_parity_passed": 6,
        "production_lessons": 2,
        "production_identifiable": 2,
        "query_rotations": 6,
        "rotations_identifiable": 6,
    }
    assert report["canonical_authority_changed"] is False
    assert report["default_program_byte_identical"] is True
    assert report["setting_difference_witness"]["different_cell_count"] > 0


def test_written_public_artifact_names_do_not_reveal_hidden_setting(tmp_path):
    prototype = _load_prototype()
    private_dir = tmp_path / "private"
    public_dir = tmp_path / "public"
    report = prototype.write_evidence(
        out_dir=private_dir,
        public_dir=public_dir,
        seeds=[0, 1],
        difficulty="easy",
        start_index=0,
        n_train=2,
        n_test=1,
    )
    assert report["passed"] is True
    public_names = sorted(path.name for path in public_dir.iterdir())
    assert public_names == ["challenge-01.json", "challenge-02.json"]
    assert not any(
        value in name
        for name in public_names
        for value in prototype.PARAMETER_SPEC["values"]
    )
