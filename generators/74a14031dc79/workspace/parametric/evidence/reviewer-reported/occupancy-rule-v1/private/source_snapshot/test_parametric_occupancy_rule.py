"""Focused tests for the proposed, unapproved occupancy-rule prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/74a14031dc79/workspace/parametric/prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_74a14031dc79", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_is_exact_canonical_and_alternatives_are_guarded_changes():
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("or", root=ROOT) == canonical
    assert canonical.count(prototype.CANONICAL_CONDITION) == 1

    for setting, condition in prototype.RULE_CONDITIONS.items():
        source = prototype.materialize_rule(setting, root=ROOT)
        assert source.count(condition) == 1
        assert prototype.rule_setting(source) == setting
        if setting != "or":
            assert source.replace(condition, prototype.CANONICAL_CONDITION, 1) == canonical


@pytest.mark.parametrize("value", [True, 0, "union", None])
def test_invalid_occupancy_rule_is_rejected(value):
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


def test_source_guard_rejects_whitespace_or_unrelated_tampering():
    canonical = prototype.canonical_source(root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical + " ")
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical.replace("(w 3)", "(w 4)"))


def test_or_rule_reproduces_every_labeled_canonical_pair(bridge):
    source = prototype.materialize_rule("or", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_batch_execution_matches_single_grid_execution(bridge):
    source = prototype.materialize_rule("or", root=ROOT)
    grids = [pair["input"] for pair in canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)[:3]]
    batched = prototype.execute_rule_many(source, grids, bridge=bridge, root=ROOT)
    singles = [prototype.execute_rule(source, grid, bridge=bridge, root=ROOT) for grid in grids]
    assert batched == singles


def test_all_settings_produce_distinct_outputs_on_truth_table_witness(bridge):
    witness = prototype.distinguishing_input()
    outputs = {
        setting: prototype.execute_rule(
            prototype.materialize_rule(setting, root=ROOT), witness, bridge=bridge
        )
        for setting in prototype.ALLOWED_OCCUPANCY_RULES
    }
    assert len({json.dumps(value) for value in outputs.values()}) == 3
    assert prototype.relation_set(witness) == {"00", "10", "01", "11"}


def test_episode_draws_one_rule_and_demonstrations_refute_all_other_settings(bridge):
    expected = {1: "or", 0: "xor", 5: "and"}
    for seed, setting in expected.items():
        episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
        assert episode["parameters"] == {"occupancy_rule": setting}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["occupancy_rule"] for row in matching] == [setting]
        assert {row["occupancy_rule"] for row in refuted} == set(prototype.ALLOWED_OCCUPANCY_RULES) - {setting}
        assert all(row["demonstration_mismatch_indices"] for row in refuted)
        assert all(row["query_mismatch_indices"] == [0] for row in refuted)
        assert all(prototype.relation_set(pair["input"]) == {"00", "10", "01", "11"} for pair in episode["train"] + episode["test"])


def test_public_challenge_is_allowlisted_and_does_not_alias_private_episode(bridge):
    episode = prototype.make_episode(1, root=ROOT, bridge=bridge)
    before = json.loads(json.dumps(episode))
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("occupancy_rule", "racket", "seed", "parameter", "query_answer"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_files_and_keeps_query_answers_private(tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence((1, 0, 5), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["episode_settings_exercised"] == 3
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )
    assert {row["parameters"]["occupancy_rule"] for row in report["episodes"]} == set(
        prototype.ALLOWED_OCCUPANCY_RULES
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
        prototype.write_evidence((1, 0, 5), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)
