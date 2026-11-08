"""Focused tests for the proposed, unapproved occupancy-rule prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

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
        assert len(episode["train"]) == prototype.DEFAULT_DEMO_COUNT
        assert len(episode["test"]) == prototype.DEFAULT_QUERY_COUNT
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["occupancy_rule"] for row in matching] == [setting]
        assert {row["occupancy_rule"] for row in refuted} == set(prototype.ALLOWED_OCCUPANCY_RULES) - {setting}
        assert all(row["demonstration_mismatch_indices"] for row in refuted)
        assert all(
            row["query_mismatch_indices"] == list(range(prototype.DEFAULT_QUERY_COUNT))
            for row in refuted
        )
        assert all(
            prototype.relation_set(pair["input"]) == {"00", "10", "01", "11"}
            for pair in episode["train"] + episode["test"]
        )


def test_demo_and_query_counts_are_independent_with_four_distinct_racket_queries(bridge):
    episode = prototype.make_episode(
        1,
        demo_count=2,
        query_count=4,
        root=ROOT,
        bridge=bridge,
    )
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    input_hashes = [prototype.grid_sha256(pair["input"]) for pair in pairs]
    assert len(input_hashes) == len(set(input_hashes)) == 6

    selected_source = prototype.materialize_rule(
        episode["parameters"]["occupancy_rule"], root=ROOT
    )
    query_outputs = prototype.execute_rule_many(
        selected_source,
        [pair["input"] for pair in episode["test"]],
        bridge=bridge,
        root=ROOT,
    )
    assert query_outputs == [pair["output"] for pair in episode["test"]]


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


def test_public_filename_depends_only_on_visible_challenge_bytes():
    episode = {
        "seed": 1,
        "parameters": {"occupancy_rule": "or"},
        "rule": {"racket_source": "private"},
        "train": [{"input": [[0, 1]], "output": [[2, 0]]}],
        "test": [{"input": [[1, 0]], "output": [[0, 2]]}],
    }
    name = prototype.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)

    private_changes = deepcopy(episode)
    private_changes["seed"] = 99
    private_changes["parameters"] = {"occupancy_rule": "and"}
    private_changes["rule"] = {"racket_source": "different private source"}
    private_changes["test"][0]["output"] = [[2, 2]]
    assert prototype.public_filename(private_changes) == name

    visible_change = deepcopy(episode)
    visible_change["test"][0]["input"] = [[0, 0]]
    assert prototype.public_filename(visible_change) != name


def test_evidence_writer_uses_opaque_public_names_and_four_distinct_queries(tmp_path):
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
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 12
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )
    assert report["verification"]["status"] == "pass"
    assert {row["parameters"]["occupancy_rule"] for row in report["episodes"]} == set(
        prototype.ALLOWED_OCCUPANCY_RULES
    )
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    assert [row["private_path"] for row in report["episodes"]] == [
        f"private/episode-{index:03d}.json" for index in range(3)
    ]

    public_names = set()
    for episode_row in report["episodes"]:
        public_path = out / episode_row["public_path"]
        private_path = out / episode_row["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        assert public == prototype.public_challenge(private)
        assert public_path.name == prototype.public_filename(private)
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert public_path.name not in public_names
        public_names.add(public_path.name)
        assert len(public["train"]) == 2
        assert len(public["test"]) == 4
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
        query_hashes = [prototype.grid_sha256(pair["input"]) for pair in public["test"]]
        assert len(query_hashes) == len(set(query_hashes)) == 4

    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((1, 0, 5), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)


@pytest.mark.parametrize("name,value", [("demo", True), ("query", 0), ("demo", -1), ("query", 1.5), ("demo", "2")])
def test_invalid_demo_or_query_count_is_rejected(name, value):
    kwargs = {"demo_count": 2, "query_count": 4}
    kwargs[f"{name}_count"] = value
    with pytest.raises((TypeError, ValueError)):
        prototype.make_episode(1, root=ROOT, **kwargs)
