"""Focused contract tests for the proposed target-policy prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "089c14df9952"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def test_default_rule_is_exact_pinned_canonical_source(prototype):
    source = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(source.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.DEFAULT_TARGET_POLICY == "all"
    assert prototype.materialize_rule("all", source=source) == source


def test_alternative_changes_exactly_the_target_selection_guard(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    alternative = prototype.materialize_rule("hinted_only", source=canonical)
    assert alternative != canonical
    assert alternative.count(prototype.ALTERNATIVE_TARGET_GUARD) == 1
    assert (
        alternative.replace(
            prototype.ALTERNATIVE_TARGET_GUARD,
            prototype.CANONICAL_TARGET_GUARD,
            1,
        )
        == canonical
    )


@pytest.mark.parametrize("bad", [None, True, 0, "hinted", "ALL"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises(ValueError, match="target_policy"):
        prototype.materialize_rule(bad, root=ROOT)


def test_both_racket_settings_execute_and_disagree_on_every_fixture(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    sources = {
        policy: prototype.materialize_rule(policy, source=canonical)
        for policy in prototype.ALLOWED_TARGET_POLICIES
    }
    fixtures = prototype.fixtures(root=ROOT)
    assert len(fixtures) == 4
    with RacketBridge() as bridge:
        for fixture in fixtures:
            outputs = {
                policy: prototype.execute_rule(source, fixture["input"], bridge=bridge)
                for policy, source in sources.items()
            }
            assert outputs["all"] != outputs["hinted_only"], fixture["fixture_id"]


def test_seed_selects_one_policy_for_complete_identifiable_episode(prototype):
    assert prototype.parameters_for_seed(0) == {"target_policy": "hinted_only"}
    assert prototype.parameters_for_seed(1) == {"target_policy": "all"}
    with RacketBridge() as bridge:
        episodes = [
            prototype.make_episode(seed, root=ROOT, bridge=bridge)
            for seed in (0, 1)
        ]
    assert {episode["parameters"]["target_policy"] for episode in episodes} == {
        "all",
        "hinted_only",
    }
    for episode in episodes:
        chosen = episode["parameters"]["target_policy"]
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["approved"] is False
        assert episode["status"] == "proposed_unapproved"
        assert all(row["target_policy"] == chosen for row in episode["train"])
        assert episode["test"][0]["target_policy"] == chosen
        rival = next(
            row
            for row in episode["parameter_rivals"]
            if row["target_policy"] != chosen
        )
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0]
        assert episode["ambiguities"] == []


def test_public_challenge_omits_private_rule_and_query_answer(prototype):
    with RacketBridge() as bridge:
        episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = repr(public)
    for forbidden in (
        "target_policy",
        "racket_source",
        "racket_sha256",
        "parameters",
        "seed",
    ):
        assert forbidden not in serialized


def test_canonical_default_replays_every_labeled_canonical_pair(prototype):
    source = prototype.materialize_rule("all", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    with RacketBridge() as bridge:
        for pair in pairs:
            assert (
                prototype.execute_rule(source, pair["input"], bridge=bridge)
                == pair["output"]
            )
