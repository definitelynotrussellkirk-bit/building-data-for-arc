"""Focused tests for the proposed, unapproved cyan-anchor prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/1b9d8370e28b/workspace/parametric/prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_1b9d8370e28b", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_is_exact_canonical_and_right_is_one_guarded_change():
    prototype = _load_prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("left", root=ROOT) == canonical

    right = prototype.materialize_rule("right", root=ROOT)
    assert right != canonical
    assert canonical.count(prototype.CANONICAL_EDGE_FRAGMENT) == 1
    assert right.count(prototype.REVERSED_EDGE_FRAGMENT) == 1
    assert right.replace(
        prototype.REVERSED_EDGE_FRAGMENT,
        prototype.CANONICAL_EDGE_FRAGMENT,
        1,
    ) == canonical


@pytest.mark.parametrize("value", [True, 8, "up", None])
def test_invalid_cyan_anchor_is_rejected(value):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.materialize_rule(value, root=ROOT)


def test_source_guard_rejects_unrelated_or_whitespace_tampering():
    prototype = _load_prototype()
    canonical = prototype.canonical_source(root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical + " ")
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical.replace("(rows g)", "(+ 0 (rows g))"))


def test_left_rule_reproduces_every_labeled_canonical_pair(bridge):
    prototype = _load_prototype()
    source = prototype.materialize_rule("left", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_same_lawful_input_distinguishes_both_settings(bridge):
    prototype = _load_prototype()
    grid = prototype.build_input(20, 0)
    left_source = prototype.materialize_rule("left", root=ROOT)
    right_source = prototype.materialize_rule("right", root=ROOT)
    left = prototype.execute_rule(left_source, grid, bridge=bridge)
    right = prototype.execute_rule(right_source, grid, bridge=bridge)
    assert left != right
    assert left == prototype.apply_rule(grid, "left")
    assert right == prototype.apply_rule(grid, "right")


def test_episode_draws_parameter_once_and_refutes_other_setting(bridge):
    prototype = _load_prototype()
    left_episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    right_episode = prototype.make_episode(1, root=ROOT, bridge=bridge)
    assert left_episode["parameters"] == {"cyan_anchor": "left"}
    assert right_episode["parameters"] == {"cyan_anchor": "right"}

    for episode in (left_episode, right_episode):
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [
            row
            for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["cyan_anchor"] for row in matching] == [episode["parameters"]["cyan_anchor"]]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_challenge_uses_allowlist_and_does_not_alias_private_episode(bridge):
    prototype = _load_prototype()
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    before = json.loads(json.dumps(episode))
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("cyan_anchor", "racket", "seed", "parameter", "program"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_files_and_keeps_query_answers_private(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["passed"] is True
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
    manifest = json.loads((out / "manifest.json").read_text())
    for row in manifest["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(seed):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.parameters_for_seed(seed)
