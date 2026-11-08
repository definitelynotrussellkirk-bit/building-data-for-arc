"""Focused tests for the proposed, unapproved phase-relation prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/b7c3b8bc9805/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert PROTOTYPE_PATH.is_file(), "phase_relation prototype has not been built"
    spec = importlib.util.spec_from_file_location(
        "parametric_b7c3b8bc9805", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_is_exact_canonical_and_opposite_is_one_guarded_change(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("same", root=ROOT) == canonical

    opposite = prototype.materialize_rule("opposite", root=ROOT)
    assert opposite != canonical
    assert canonical.count(prototype.SAME_PHASE_SITE) == 1
    assert opposite.count(prototype.OPPOSITE_PHASE_SITE) == 1
    assert opposite.replace(
        prototype.OPPOSITE_PHASE_SITE, prototype.SAME_PHASE_SITE, 1
    ) == canonical


@pytest.mark.parametrize("value", [True, 8, "rotated", None])
def test_invalid_phase_relation_is_rejected(prototype, value):
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


def test_source_guard_rejects_unrelated_or_whitespace_tampering(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical + " ")
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical.replace("(find-color g 5)", "(find-color g 4)"))


def test_same_rule_reproduces_every_labeled_canonical_pair(prototype, bridge):
    source = prototype.materialize_rule("same", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_both_settings_execute_on_shared_lawful_inputs_and_are_distinct(prototype, bridge):
    fixtures = prototype.fixtures(root=ROOT)
    assert len(fixtures) == 5
    same = prototype.materialize_rule("same", root=ROOT)
    opposite = prototype.materialize_rule("opposite", root=ROOT)
    for fixture in fixtures:
        same_output = prototype.execute_rule(same, fixture["input"], bridge=bridge)
        opposite_output = prototype.execute_rule(opposite, fixture["input"], bridge=bridge)
        assert same_output != opposite_output, fixture["fixture_id"]


def test_episode_draws_parameter_once_is_deterministic_and_refutes_other_setting(
    prototype, bridge
):
    opposite_episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    same_episode = prototype.make_episode(1, root=ROOT, bridge=bridge)
    assert opposite_episode == prototype.make_episode(0, root=ROOT, bridge=bridge)
    assert opposite_episode["parameters"] == {"phase_relation": "opposite"}
    assert same_episode["parameters"] == {"phase_relation": "same"}

    for episode in (opposite_episode, same_episode):
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "matches_episode"
        ]
        refuted = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["phase_relation"] for row in matching] == [
            episode["parameters"]["phase_relation"]
        ]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_challenge_is_an_allowlist_and_does_not_alias_private_episode(
    prototype, bridge
):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    before = json.loads(json.dumps(episode))
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("phase_relation", "racket", "seed", "parameter"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_files_and_keeps_query_answers_private(
    prototype, tmp_path
):
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["episode_settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )

    for episode_row in report["episodes"]:
        public = json.loads((out / episode_row["public_path"]).read_text())
        private = json.loads((out / episode_row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert "output" not in public["test"][0]
        assert "output" in private["test"][0]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)
