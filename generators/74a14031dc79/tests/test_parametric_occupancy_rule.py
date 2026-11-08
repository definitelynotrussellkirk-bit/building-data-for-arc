"""Focused tests for the proposed, unapproved occupancy-rule prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

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


def test_episode_defaults_to_three_demonstrations_and_four_distinct_queries(bridge):
    expected = {1: "or", 0: "xor", 5: "and"}
    for seed, setting in expected.items():
        episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
        assert episode["parameters"] == {"occupancy_rule": setting}
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["occupancy_rule"] for row in matching] == [setting]
        assert {row["occupancy_rule"] for row in refuted} == set(prototype.ALLOWED_OCCUPANCY_RULES) - {setting}
        assert all(row["demonstration_mismatch_indices"] for row in refuted)
        assert all(row["query_mismatch_indices"] == [0, 1, 2, 3] for row in refuted)
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"]) for pair in pairs}) == 7
        assert all(
            prototype.relation_set(pair["input"]) == {"00", "10", "01", "11"}
            for pair in pairs
        )


def test_episode_accepts_independent_demonstration_and_query_counts(bridge):
    episode = prototype.make_episode(
        1,
        demo_count=2,
        query_count=5,
        root=ROOT,
        bridge=bridge,
    )
    assert episode["counts"] == {"demonstrations": 2, "queries": 5}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 5
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == 7
    assert all(row["query_mismatch_indices"] == [0, 1, 2, 3, 4] for row in episode["parameter_rivals"] if row["occupancy_rule"] != "or")


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("demo_count", True),
        ("demo_count", 0),
        ("demo_count", -1),
        ("demo_count", 1.5),
        ("demo_count", "3"),
        ("demo_count", 17),
        ("query_count", True),
        ("query_count", 0),
        ("query_count", -1),
        ("query_count", 1.5),
        ("query_count", "4"),
        ("query_count", 17),
    ],
)
def test_episode_rejects_invalid_or_unsupported_counts(keyword, value):
    kwargs = {"demo_count": 3, "query_count": 4, keyword: value}
    with pytest.raises(ValueError):
        prototype.make_episode(1, root=ROOT, **kwargs)


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


def test_public_export_plan_uses_visible_content_ids_and_rejects_duplicates(bridge):
    episodes = [
        prototype.make_episode(seed, demo_count=1, query_count=2, root=ROOT, bridge=bridge)
        for seed in (1, 0, 5)
    ]
    forward = prototype.public_export_plan(episodes)
    reverse = prototype.public_export_plan(list(reversed(episodes)))
    assert [row["public_id"] for row in forward] == [row["public_id"] for row in reverse]
    assert [row["public_id"] for row in forward] == sorted(
        row["public_id"] for row in forward
    )
    for row in forward:
        assert row["public_id"] == public_challenge_id(row["episode"])
        assert row["public_bytes"] == public_challenge_bytes(row["episode"])

    changed_private = json.loads(json.dumps(episodes[0]))
    changed_private["seed"] = 999
    changed_private["parameters"] = {"occupancy_rule": "private-change"}
    changed_private["rule"] = {"racket_source": "private-change"}
    changed_private["test"][0]["output"][0][0] = 9
    assert public_challenge_id(changed_private) == public_challenge_id(episodes[0])

    changed_visible = json.loads(json.dumps(episodes[0]))
    changed_visible["test"][0]["input"][0][0] = (
        changed_visible["test"][0]["input"][0][0] + 1
    ) % 10
    assert public_challenge_id(changed_visible) != public_challenge_id(episodes[0])

    with pytest.raises(ValueError, match="duplicate visible public payload"):
        prototype.public_export_plan([episodes[0], json.loads(json.dumps(episodes[0]))])


def test_evidence_writer_hashes_visible_bytes_and_keeps_query_answers_private(tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (1, 0, 5),
        out=out,
        demo_count=2,
        query_count=4,
        root=ROOT,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["episode_settings_exercised"] == 3
    assert report["counts"]["demonstrations_per_episode"] == 2
    assert report["counts"]["queries_per_episode"] == 4
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 12
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )
    assert {row["parameters"]["occupancy_rule"] for row in report["episodes"]} == set(
        prototype.ALLOWED_OCCUPANCY_RULES
    )
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )

    for episode_row in report["episodes"]:
        public_path = out / episode_row["public_path"]
        private_path = out / episode_row["private_path"]
        private = json.loads(private_path.read_text())
        assert public_path.name == f'{public_challenge_id(private)}.json'
        assert private_path.name == public_path.name
        assert public_path.read_bytes() == public_challenge_bytes(private)
        public = json.loads(public_path.read_text())
        assert public == prototype.public_challenge(private)
        assert len(public["train"]) == 2
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
        assert "episode-" not in episode_row["public_path"]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            (1, 0, 5),
            out=out,
            demo_count=2,
            query_count=4,
            root=ROOT,
        )


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)


def test_retained_evidence_replays_exact_racket_and_rejects_tampering(tmp_path):
    output = tmp_path / "evidence"
    report = prototype.write_evidence((1, 0, 5), out=output, root=ROOT, demo_count=1, query_count=1)
    verification = prototype.verify_evidence(output, root=ROOT)
    assert verification["episodes_checked"] == 3
    assert verification["labels_checked"] == 6
    assert verification["query_labels_checked"] == 3
    public = output / report["episodes"][0]["public_path"]
    public.write_bytes(public.read_bytes() + b" ")
    with pytest.raises(AssertionError, match="bytes|hash"):
        prototype.verify_evidence(output, root=ROOT)
