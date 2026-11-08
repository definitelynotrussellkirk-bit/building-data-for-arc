"""Focused tests for the proposed episode-level parent-choice prototype."""
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

TASK_ID = "f59691ac00f3"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
EXPECTED_CANONICAL_SHA256 = (
    "2e50ecc613be187d84268664bd1c2c33cf187efe48d02ecf8330366abd929a63"
)


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parent-choice prototype must be runnable"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE_PATH
    )
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
    assert prototype.DEFAULT_DIFFERENT_PARENT == "right"
    assert prototype.materialize_rule("right", source=canonical) == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]


def test_left_parent_variant_is_one_guarded_branch_replacement(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    alternative = prototype.materialize_rule("left", source=canonical)
    assert alternative != canonical
    assert canonical.count(prototype.CANONICAL_BRANCH) == 1
    assert alternative.count(prototype.ALTERNATIVE_BRANCH) == 1
    assert prototype.restore_canonical(alternative) == canonical
    assert alternative.replace(
        prototype.ALTERNATIVE_BRANCH, prototype.CANONICAL_BRANCH, 1
    ) == canonical


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, "both", "random"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="different_parent"):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.choose_setting(bad)


@pytest.mark.parametrize("name,bad", [("demo_count", 0), ("query_count", -1), ("demo_count", True), ("query_count", 2.5)])
def test_counts_are_positive_plain_integers(prototype, name, bad):
    kwargs = {"demo_count": 2, "query_count": 4, name: bad}
    with pytest.raises((TypeError, ValueError), match=name):
        prototype.make_episode(0, root=ROOT, **kwargs)


def test_two_consecutive_seeds_cover_identifiable_four_query_episodes(prototype, bridge):
    episodes = [
        prototype.make_episode(
            seed,
            demo_count=2,
            query_count=4,
            root=ROOT,
            bridge=bridge,
        )
        for seed in (0, 1)
    ]
    assert {row["parameters"]["different_parent"] for row in episodes} == set(
        prototype.DIFFERENT_PARENT_POLICIES
    )
    for episode in episodes:
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert len(episode["pairs"]) == 6
        inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["pairs"]
        ]
        assert len(set(inputs)) == 6
        assert all(
            pair["different_parent"]
            == episode["parameters"]["different_parent"]
            for pair in episode["pairs"]
        )
        assert all(set(pair["parent_pairs"]) == {"22", "25", "52", "55"} for pair in episode["pairs"])
        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["status"] == "no_ambiguity_found"
        assert analysis["rival_fits_demonstrations"] is False
        assert len(analysis["queries"]) == 4
        assert all(row["rival_query_differs"] for row in analysis["queries"])


def test_public_projection_and_name_ignore_private_metadata_and_query_answers(
    prototype, bridge
):
    episode = prototype.make_episode(
        0, demo_count=2, query_count=4, root=ROOT, bridge=bridge
    )
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in (
        "different_parent",
        "racket",
        "parameters",
        "seed",
        "query_output",
        "right",
        "left",
    ):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)
    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["parameters"] = {"different_parent": "left"}
    changed["test"][0]["output"] = [[9]]
    assert prototype.public_filename(prototype.public_challenge(changed)) == filename


def test_materialized_tree_is_self_verifying_and_has_four_queries_per_setting(
    prototype, bridge, tmp_path
):
    out = tmp_path / "parent-choice-evidence"
    report = prototype.materialize(
        out,
        seeds=(0, 1),
        demo_count=2,
        query_count=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "episodes": 2,
        "demonstrations": 4,
        "queries": 8,
    }
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


def test_materialized_tree_supports_independent_nondefault_counts(
    prototype, bridge, tmp_path
):
    out = tmp_path / "nondefault-counts"
    report = prototype.materialize(
        out,
        seeds=(4, 5),
        demo_count=3,
        query_count=5,
        root=ROOT,
        bridge=bridge,
    )
    assert report["counts"] == {
        "episodes": 2,
        "demonstrations": 6,
        "queries": 10,
    }
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


def test_verify_tree_rejects_stale_prototype_source_binding(
    prototype, bridge, tmp_path
):
    out = tmp_path / "stale-source-binding"
    prototype.materialize(
        out,
        seeds=(8, 9),
        demo_count=2,
        query_count=4,
        root=ROOT,
        bridge=bridge,
    )

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
