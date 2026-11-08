"""Focused tests for the proposed episode-level ring-order prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "8291f3ee7e54"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "79951c1fb8d60053930868df5a4f183a5ed50884fe0e479e954ea446b7b8b6bb"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "ring-order prototype must be runnable"
    spec = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def test_default_rule_is_exact_pinned_canonical_source(prototype, bridge):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert prototype.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert prototype.DEFAULT_RING_ORDER == "largest_outside"
    assert prototype.materialize_rule("largest_outside", source=canonical) == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]


def test_smallest_outside_is_one_declared_tail_replacement(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    alternative = prototype.materialize_rule("smallest_outside", source=canonical)
    assert alternative != canonical
    assert alternative.count(prototype.ALTERNATIVE_TAIL) == 1
    assert (
        alternative.replace(prototype.ALTERNATIVE_TAIL, prototype.CANONICAL_TAIL, 1)
        == canonical
    )


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, "reverse", "ascending"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises(ValueError, match="ring_order"):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.parameters_for_seed(bad)


def test_two_consecutive_seeds_cover_identifiable_four_query_episodes(prototype, bridge):
    episodes = [
        prototype.make_episode(seed, n_train=2, n_test=4, root=ROOT, bridge=bridge)
        for seed in (0, 1)
    ]
    assert {row["parameters"]["ring_order"] for row in episodes} == set(prototype.RING_ORDERS)
    for episode in episodes:
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert len(episode["pairs"]) == 6
        inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["pairs"]]
        assert len(set(inputs)) == 6
        assert all(pair["ring_order"] == episode["parameters"]["ring_order"] for pair in episode["pairs"])
        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["status"] == "no_ambiguity_found"
        assert analysis["rival_fits_demonstrations"] is False
        assert len(analysis["queries"]) == 4
        assert all(row["rival_query_differs"] for row in analysis["queries"])


def test_public_projection_and_name_ignore_private_metadata_and_query_answers(prototype, bridge):
    episode = prototype.make_episode(0, n_train=2, n_test=4, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("ring_order", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)
    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["parameters"] = {"ring_order": "smallest_outside"}
    changed["test"][0]["output"] = [[9]]
    assert prototype.public_filename(prototype.public_challenge(changed)) == filename


def test_materialized_tree_is_self_verifying_and_has_four_queries_per_setting(
    prototype, bridge, tmp_path
):
    out = tmp_path / "ring-order-evidence"
    report = prototype.materialize(
        out,
        seed=0,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["queries"] == 8
    assert report["counts"]["demonstrations"] == 4
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    assert len(public_ids) == len(set(public_ids))
    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    for path in public_paths:
        payload = json.loads(path.read_text())
        assert prototype.public_filename(payload) == path.name
        assert len(payload["test"]) == 4
        assert all(set(pair) == {"input"} for pair in payload["test"])


def test_materialized_tree_supports_independent_nondefault_counts(prototype, bridge, tmp_path):
    out = tmp_path / "nondefault-counts"
    report = prototype.materialize(
        out,
        seed=4,
        n_train=3,
        n_test=5,
        root=ROOT,
        bridge=bridge,
    )
    assert report["counts"]["demonstrations"] == 6
    assert report["counts"]["queries"] == 10
    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        assert len(public["train"]) == 3
        assert len(public["test"]) == 5


def test_episode_row_ordering_rejects_duplicate_visible_ids(prototype):
    rows = [
        {"public_id": "b", "seed": 1},
        {"public_id": "a", "seed": 0},
    ]
    ordered = prototype._sorted_unique_episode_rows(rows)
    assert [row["public_id"] for row in ordered] == ["a", "b"]
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        prototype._sorted_unique_episode_rows([rows[0], copy.deepcopy(rows[0])])


def test_verify_tree_rejects_stale_prototype_source_binding(prototype, bridge, tmp_path):
    out = tmp_path / "stale-source-binding"
    prototype.materialize(out, seed=8, n_train=2, n_test=4, root=ROOT, bridge=bridge)

    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    report["prototype_source_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    body = report_path.read_bytes()
    manifest["files"]["report.json"] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "fail"
    assert any("prototype source" in error for error in verification["errors"]), verification


def test_materialized_public_write_plan_is_sorted_and_visible_content_bound(
    prototype, bridge, tmp_path
):
    out = tmp_path / "sorted-public-write-plan"
    report = prototype.materialize(
        out,
        seed=0,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    ids = [row["public_id"] for row in report["episodes"]]
    assert report["public_write_order"] == sorted(ids)
    assert ids == sorted(ids)
    for public_id in ids:
        path = out / "public" / f"challenge-{public_id}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == public_id


def test_duplicate_visible_id_is_rejected_before_any_episode_is_published(
    prototype, bridge, monkeypatch, tmp_path
):
    out = tmp_path / "duplicate-public-id"
    monkeypatch.setattr(prototype, "public_challenge_id", lambda _challenge: "a" * 64)
    with pytest.raises(ValueError, match="duplicate visible public challenge"):
        prototype.materialize(
            out,
            seed=0,
            n_train=2,
            n_test=4,
            root=ROOT,
            bridge=bridge,
        )
    assert not list((out / "public").glob("challenge-*.json"))
    assert not list((out / "private").glob("episode-*.json"))
