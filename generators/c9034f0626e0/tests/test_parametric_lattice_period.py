"""Focused tests for the task-local lattice-period prototype."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import sys

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC_HOME = TASK_HOME / "workspace" / "parametric"
sys.path.insert(0, str(PARAMETRIC_HOME))

from prototype import (  # noqa: E402
    ALLOWED_PERIODS,
    DEFAULT_PERIOD,
    PAIR_COUNT,
    period_for_seed,
    public_challenge,
    python_mirror,
    rule_source,
    run_evidence,
    sample_episode,
    sample_inputs,
    score_rotation,
)


def _canonical_program() -> str:
    from reviewer_support import canonical_path, find_root

    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    matches = [
        row
        for row in rows
        if row.get("task_id") == "c9034f0626e0"
        and row.get("content_hash") == "c9034f0626e0"
    ]
    assert len(matches) == 1
    return matches[0]["program_solution"].strip()


def test_rule_sources_preserve_exact_default_and_change_only_the_lattice_period():
    canonical = _canonical_program()
    assert DEFAULT_PERIOD == 2
    assert ALLOWED_PERIODS == (2, 3)
    assert rule_source(2) == canonical
    assert canonical.count("remainder") == 4
    assert rule_source(3) == canonical.replace("remainder mr 2", "remainder mr 3").replace(
        "remainder mc 2", "remainder mc 3"
    ).replace("remainder r 2", "remainder r 3").replace(
        "remainder c 2", "remainder c 3"
    )
    assert rule_source(3) != canonical


@pytest.mark.parametrize("value", [True, False, 1, 4, 0, "2", None])
def test_period_validation_rejects_values_outside_literal_two_or_three(value):
    with pytest.raises(ValueError):
        rule_source(value)


@pytest.mark.parametrize("value", [True, 1.5, "7", None])
def test_seed_validation_rejects_non_literal_integers(value):
    with pytest.raises(TypeError):
        period_for_seed(value)


def test_episode_choice_is_deterministic_once_and_inputs_do_not_depend_on_setting():
    seed = 20261023
    episode = sample_episode(seed)
    assert episode == sample_episode(seed)
    assert episode["parameters"] == {"lattice_period": period_for_seed(seed)}
    assert episode["program"] == rule_source(episode["parameters"]["lattice_period"])
    assert episode["inputs"] == sample_inputs(seed)
    assert len(episode["inputs"]) == PAIR_COUNT == 4


def test_every_sampled_input_is_lawful_and_distinguishes_both_periods():
    from reviewer_support import find_root, load_selected_generator

    parent, _path, _sha = load_selected_generator("c9034f0626e0", root=find_root(__file__))
    for grid in sample_inputs(20261023):
        assert parent.self_check(grid) == []
        assert parent.strict_canonical_like(grid) == []
        assert python_mirror(grid, 2) != python_mirror(grid, 3)


def test_public_challenge_masks_parameter_program_and_query_answer():
    episode = sample_episode(20261023)
    chosen = episode["parameters"]["lattice_period"]
    pairs = [
        {"input": grid, "output": python_mirror(grid, chosen)}
        for grid in episode["inputs"]
    ]
    public = public_challenge(pairs)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert public["test"] == [{"input": pairs[3]["input"]}]
    assert "output" not in public["test"][0]
    serialized = json.dumps(public)
    assert "lattice_period" not in serialized
    assert "program" not in serialized


def test_every_query_rotation_refutes_the_alternate_period_in_demonstrations():
    inputs = sample_inputs(20261023)
    predictions = {
        period: [python_mirror(grid, period) for grid in inputs]
        for period in ALLOWED_PERIODS
    }
    for chosen in ALLOWED_PERIODS:
        for query_index in range(PAIR_COUNT):
            result = score_rotation(predictions, chosen, query_index)
            assert result["rivals"] == [
                {
                    "lattice_period": 3 if chosen == 2 else 2,
                    "status": "refuted_by_demonstrations",
                    "demonstration_mismatches": [
                        index for index in range(PAIR_COUNT) if index != query_index
                    ],
                    "query_disagrees": True,
                }
            ]


def test_evidence_builder_executes_both_rules_and_exports_verifiable_artifacts(tmp_path):
    racket_path = os.environ.get("RACKET_PATH")
    assert racket_path, "RACKET_PATH must be supplied by the packet wrapper"

    out = tmp_path / "evidence"
    report = run_evidence(out, base_seed=20261023, racket_path=racket_path)

    assert report["status"] == "pass", report
    assert report["parameter_contract"]["name"] == "lattice_period"
    assert report["parameter_contract"]["allowed_values"] == [2, 3]
    assert report["parameter_contract"]["original_default"] == 2
    assert [row["parameters"]["lattice_period"] for row in report["rules"]] == [2, 3]
    assert report["rules"][0]["canonical_default"] is True
    assert report["rules"][0]["source"] == _canonical_program()
    assert report["rules"][1]["canonical_default"] is False
    assert report["rules"][0]["sha256"] != report["rules"][1]["sha256"]
    assert {row["parameters"]["lattice_period"] for row in report["episodes"]} == {2, 3}
    assert report["summary"] == {
        "episodes": 2,
        "episode_pairs": 8,
        "racket_rule_applications": 16,
        "racket_canaries": 2,
        "python_mirror_matches": 16,
        "query_rotations": 8,
        "rotation_rival_checks": 8,
        "refuted_rotation_rivals": 8,
        "ambiguous_rotation_rivals": 0,
        "survived_rotation_rivals": 0,
    }

    witness = json.loads((out / "private/cross_setting_witness.json").read_text())
    assert witness["pairwise_outputs_distinct"] is True
    assert set(witness["outputs"]) == {"2", "3"}

    for episode in report["episodes"]:
        from reviewer_support import public_challenge_bytes
        path = out / episode["public_path"]
        public = json.loads(path.read_text())
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        assert path.read_bytes() == public_challenge_bytes(public)
        serialized = json.dumps(public)
        assert "lattice_period" not in serialized
        assert "rule!" not in serialized
        assert set(public["test"][0]) == {"input"}

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "pass"
    assert manifest["report_sha256"]
    assert len(manifest["public_challenges"]) == 2
    assert len(manifest["private_evidence"]) == 2
    assert all((out / row["path"]).is_file() for row in manifest["files"])

    failed_out = tmp_path / "failed-evidence"
    failed = run_evidence(
        failed_out,
        base_seed=20261023,
        racket_path=str(tmp_path / "missing-racket"),
    )
    assert failed["status"] == "error"
    assert failed["error"]["type"] == "FileNotFoundError"
    assert json.loads((failed_out / "report.json").read_text())["status"] == "error"
    assert json.loads((failed_out / "manifest.json").read_text())["status"] == "error"
