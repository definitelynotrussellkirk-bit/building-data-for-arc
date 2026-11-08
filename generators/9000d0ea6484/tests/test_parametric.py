"""Focused tests for the task-local priority-scan prototype."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace" / "parametric"))

import prototype  # noqa: E402
from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from reviewer_support import find_root  # noqa: E402


def test_priority_parameter_domain_is_small_unique_and_keeps_canonical_default():
    settings = prototype.all_settings()
    orders = {prototype.priority_order(start, direction) for start, direction in settings}
    assert len(settings) == 8
    assert len(orders) == 8
    assert prototype.priority_order(2, "forward") == (2, 3, 0, 1)
    assert prototype.priority_order(2, "reverse") == (2, 1, 0, 3)


@pytest.mark.parametrize(
    ("start", "direction"),
    [(True, "forward"), (-1, "forward"), (4, "forward"), (2, True), (2, "sideways")],
)
def test_invalid_parameter_values_are_rejected(start, direction):
    with pytest.raises((TypeError, ValueError)):
        prototype.priority_order(start, direction)


def test_default_rule_is_byte_identical_and_every_setting_changes_execution_text():
    root = find_root(__file__)
    canonical = prototype.canonical_rule(root)
    programs = {
        setting: prototype.materialize_rule(*setting, root=root)
        for setting in prototype.all_settings()
    }
    assert programs[(2, "forward")] == canonical
    assert len(set(programs.values())) == 8
    assert "(priority (list 2 3 0 1))" in programs[(2, "forward")]
    assert "(priority (list 2 1 0 3))" in programs[(2, "reverse")]


def test_complete_episode_is_racket_labelled_and_refutes_every_parameter_rival():
    root = find_root(__file__)
    with RacketBridge(timeout=20) as bridge:
        for seed, expected in [(2, (2, "forward")), (6, (2, "reverse"))]:
            episode = prototype.build_episode(seed, root=root, bridge=bridge)
            assert (
                episode["parameters"]["start_section"],
                episode["parameters"]["scan_direction"],
            ) == expected
            assert len(episode["labelled_pairs"]) == 4
            assert all(row["racket_matches_python"] for row in episode["execution_checks"])
            assert all(row["all_rivals_refuted"] for row in episode["pair_rival_checks"])
            assert all(row["identifiable"] for row in episode["query_rotations"])


def test_public_challenge_masks_hidden_rule_and_query_answer():
    root = find_root(__file__)
    with RacketBridge(timeout=20) as bridge:
        episode = prototype.build_episode(6, root=root, bridge=bridge)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    encoded = json.dumps(challenge)
    assert "start_section" not in encoded
    assert "scan_direction" not in encoded
    assert "rule!" not in encoded


def test_evidence_writer_materializes_default_and_alternative(tmp_path):
    out = tmp_path / "evidence"
    report = prototype.run_evidence(out, [2, 6])
    assert report["passed"] is True
    assert report["counts"]["settings_materialized"] == 8
    assert report["counts"]["distinct_settings_demonstrated"] == 2
    assert report["counts"]["canonical_pairs_failed"] == 0
    assert (out / "report.json").is_file()
    assert (out / "private" / "episode_seed_2.json").is_file()
    assert (out / "public" / "challenge_seed_6.json").is_file()
    public = json.loads((out / "public" / "challenge_seed_6.json").read_text())
    assert all("output" not in pair for pair in public["test"])
