"""Focused tests for the proposed episode-level tie-order prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "a0ff437161da"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def test_default_rule_is_exact_canonical_source(prototype):
    source = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(source.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.DEFAULT_TIE_ORDER == "ul_ur_ll_lr"
    assert prototype.materialize_rule("ul_ur_ll_lr", source=source) == source


def test_alternative_changes_only_corner_priority(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    alternative = prototype.materialize_rule("lr_ll_ur_ul", source=canonical)
    assert alternative != canonical
    assert alternative.count(prototype.ALTERNATIVE_CORNERS) == 1
    assert (
        alternative.replace(
            prototype.ALTERNATIVE_CORNERS,
            prototype.CANONICAL_CORNERS,
            1,
        )
        == canonical
    )


@pytest.mark.parametrize("bad", [None, True, 0, "reverse", "UL_UR_LL_LR"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises(ValueError, match="tie_order"):
        prototype.materialize_rule(bad, root=ROOT)


def test_both_racket_settings_execute_and_disagree_on_every_fixture(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    sources = {
        setting: prototype.materialize_rule(setting, source=canonical)
        for setting in prototype.ALLOWED_TIE_ORDERS
    }
    fixtures = prototype.fixtures()
    assert len(fixtures) == 4
    with RacketBridge() as bridge:
        for fixture in fixtures:
            outputs = {
                setting: prototype.execute_rule(source, fixture["input"], bridge=bridge)
                for setting, source in sources.items()
            }
            assert outputs["ul_ur_ll_lr"] != outputs["lr_ll_ur_ul"]


def test_seed_selects_one_setting_for_complete_identifiable_episode(prototype):
    assert prototype.parameters_for_seed(0) == {"tie_order": "ul_ur_ll_lr"}
    assert prototype.parameters_for_seed(1) == {"tie_order": "lr_ll_ur_ul"}
    with RacketBridge() as bridge:
        episodes = [prototype.make_episode(seed, root=ROOT, bridge=bridge) for seed in (0, 1)]
    assert {episode["parameters"]["tie_order"] for episode in episodes} == set(
        prototype.ALLOWED_TIE_ORDERS
    )
    for episode in episodes:
        chosen = episode["parameters"]["tie_order"]
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["approved"] is False
        assert episode["status"] == "proposed_unapproved"
        assert all(row["tie_order"] == chosen for row in episode["train"])
        assert episode["test"][0]["tie_order"] == chosen
        rival = next(
            row
            for row in episode["parameter_rivals"]
            if row["tie_order"] != chosen
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
        "tie_order",
        "racket_source",
        "racket_sha256",
        "parameters",
        "seed",
    ):
        assert forbidden not in serialized


def test_canonical_default_replays_every_labeled_pair(prototype):
    source = prototype.materialize_rule("ul_ur_ll_lr", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    with RacketBridge() as bridge:
        for pair in pairs:
            assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]
