"""Focused contract tests for the task-local rank-delta rule prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes


TASK_ID = "dafb4f819b93"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
CANONICAL_SHA256 = "fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "rank-delta prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_rank_delta_{TASK_ID}", PROTOTYPE_PATH
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
    with RacketBridge(max_calls_before_restart=128) as instance:
        yield instance


def test_default_rule_is_exact_canonical_and_alternative_is_distinct(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.PARAMETER_SPEC == {
        "name": "rank_delta",
        "values": (0, 1),
        "default": 0,
        "meaning": "fill with the row label when row-rank minus column-rank equals rank_delta",
    }
    assert prototype.materialize_rule(0, root=ROOT) == canonical
    alternative = prototype.materialize_rule(1, root=ROOT)
    assert alternative != canonical
    assert "enumerate-list ordered-colors" in alternative
    assert "(- (first row-entry) (first col-entry))" in alternative
    for bad in (-1, 2, True, 0.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="rank_delta"):
            prototype.materialize_rule(bad, root=ROOT)


def test_parameter_is_chosen_once_and_both_settings_are_reachable(prototype):
    assert prototype.parameters_for_seed(0) == {"rank_delta": 0}
    assert prototype.parameters_for_seed(1) == {"rank_delta": 1}
    assert prototype.parameters_for_seed(100) == {"rank_delta": 0}
    for bad in (-1, True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="seed"):
            prototype.parameters_for_seed(bad)


def test_racket_and_python_match_canonical_pairs_and_alternative_witness(
    prototype, bridge
):
    canonical = prototype.materialize_rule(0, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair[
            "output"
        ]
        assert prototype.apply_python(pair["input"], 0, root=ROOT) == pair["output"]

    witness = pairs[0]["input"]
    alternative = prototype.materialize_rule(1, root=ROOT)
    racket_output = prototype.execute_rule(alternative, witness, bridge=bridge)
    assert racket_output == prototype.apply_python(witness, 1, root=ROOT)
    assert racket_output != pairs[0]["output"]


@pytest.mark.parametrize("rank_delta", [0, 1])
def test_complete_four_query_episode_is_fixed_identifiable_and_distinct(
    prototype, bridge, rank_delta
):
    episode = prototype.make_episode(
        17 + rank_delta,
        rank_delta=rank_delta,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert episode["status"] == "proposed_unapproved"
    assert episode["approved"] is False
    assert episode["parameters"] == {"rank_delta": rank_delta}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert len(episode["pairs"]) == 6
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["pairs"]]
    assert len(inputs) == len(set(inputs)) == 6
    assert all(pair["rank_delta"] == rank_delta for pair in episode["pairs"])

    analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
    assert analysis["status"] == "no_ambiguity_found"
    assert analysis["rival_fits_demonstrations"] is False
    assert analysis["python_parity"] is True
    assert len(analysis["queries"]) == 4
    assert all(row["rival_query_differs"] for row in analysis["queries"])


def test_public_projection_and_id_ignore_private_metadata_and_query_answers(
    prototype, bridge
):
    episode = prototype.make_episode(23, n_train=2, n_test=4, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("rank_delta", "racket", "parameters", "seed", "output_sha256"):
        assert forbidden not in serialized

    filename = prototype.public_filename(public)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", filename)
    changed = copy.deepcopy(episode)
    changed["seed"] = 999
    changed["parameters"] = {"rank_delta": 1 - episode["parameters"]["rank_delta"]}
    changed["test"][0]["output"] = [[9]]
    changed_public = prototype.public_challenge(changed)
    assert prototype.public_filename(changed_public) == filename
    assert public_challenge_bytes(public) == public_challenge_bytes(changed_public)


def test_materialized_tree_verifies_and_rejects_public_tampering(
    prototype, bridge, tmp_path
):
    out = tmp_path / "rank-delta-evidence"
    report = prototype.materialize(
        out,
        seed=31,
        n_train=2,
        n_test=4,
        root=ROOT,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["passed"] is True
    assert report["canonical_authority_changed"] is False
    assert report["default_program_byte_identical"] is True
    assert report["counts"] == {
        "settings": 2,
        "episodes": 2,
        "demonstrations": 4,
        "queries": 8,
        "distinct_inputs": 12,
        "racket_labels": 12,
        "canonical_pairs": 4,
        "canonical_pairs_passed": 4,
        "identifiable_episodes": 2,
        "queries_refuting_rival": 8,
    }
    assert report["setting_difference_witness"]["different_cell_count"] > 0

    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    assert all(len(json.loads(path.read_text())["test"]) == 4 for path in public_paths)

    payload = json.loads(public_paths[0].read_text())
    payload["test"][0]["input"][0][0] = 9
    public_paths[0].write_text(json.dumps(payload, sort_keys=True))
    with pytest.raises(ValueError, match="public"):
        prototype.verify_tree(out, root=ROOT, bridge=bridge)
