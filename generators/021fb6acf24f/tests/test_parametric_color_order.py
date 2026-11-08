"""Racket-backed contract tests for the proposed color-order extension."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "021fb6acf24f"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "f7b49e9ffb4c0dcaa332d46e67bd1f4d5c9be35200705fc34f394548380bcbb3"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "color-order prototype must be runnable"
    spec = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def test_default_rule_is_exact_pinned_canonical_source(prototype, bridge):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert prototype.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert prototype.DEFAULT_COLOR_ORDER == "ascending"
    assert prototype.materialize_rule("ascending", source=canonical) == canonical
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]


def test_descending_rule_changes_only_the_declared_color_expression(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    descending = prototype.materialize_rule("descending", source=canonical)
    assert descending != canonical
    assert descending.count(prototype.DESCENDING_COLOR_EXPRESSION) == 1
    assert (
        descending.replace(
            prototype.DESCENDING_COLOR_EXPRESSION,
            prototype.CANONICAL_COLOR_EXPRESSION,
            1,
        )
        == canonical
    )


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, 1.0, "ASC", "reverse"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises(ValueError, match="color_order"):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.parameters_for_seed(bad)


def test_both_racket_settings_execute_and_disagree_on_every_fixture(prototype, bridge):
    canonical = prototype.canonical_source(root=ROOT)
    rules = {
        order: prototype.materialize_rule(order, source=canonical)
        for order in prototype.COLOR_ORDERS
    }
    fixtures = prototype.fixtures(root=ROOT)
    assert len(fixtures) == 4
    assert len({json.dumps(row["input"], separators=(",", ":")) for row in fixtures}) == 4
    for fixture in fixtures:
        outputs = {
            order: prototype.execute_rule(source, fixture["input"], bridge=bridge)
            for order, source in rules.items()
        }
        assert outputs["ascending"] != outputs["descending"], fixture["fixture_id"]


def test_two_consecutive_seeds_cover_identifiable_complete_episodes(prototype, bridge):
    episodes = [prototype.make_episode(seed, root=ROOT, bridge=bridge) for seed in (0, 1)]
    assert {row["parameters"]["color_order"] for row in episodes} == set(prototype.COLOR_ORDERS)
    for episode in episodes:
        chosen = episode["parameters"]["color_order"]
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["pairs"]) == 4
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert all(pair["color_order"] == chosen for pair in episode["pairs"])
        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["production"]["status"] == "no_ambiguity_found"
        assert [row["query_index"] for row in analysis["rotations"]] == [0, 1, 2, 3]
        assert all(row["status"] == "no_ambiguity_found" for row in analysis["rotations"])
        assert all(row["rival"]["query_differs"] for row in analysis["rotations"])
        assert all(not row["rival"]["fits_demonstrations"] for row in analysis["rotations"])


def test_public_projection_hides_parameter_program_and_query_answer(prototype, bridge):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(copy.deepcopy(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("color_order", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized
    public["test"][0]["input"][0][0] = 99
    assert episode["pairs"][3]["input"][0][0] != 99


def test_materialized_tree_is_self_verifying_and_separates_public_data(prototype, bridge, tmp_path):
    out = tmp_path / "color-order-evidence"
    report = prototype.materialize(out, seed=0, root=ROOT, bridge=bridge)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_checked"] >= 4
    assert report["counts"]["canonical_labels_passed"] == report["counts"]["canonical_labels_checked"]
    verification = prototype.verify_tree(out, root=ROOT, bridge=bridge)
    assert verification["status"] == "pass"
    for public_path in sorted((out / "public").glob("*.json")):
        text = public_path.read_text()
        assert "color_order" not in text
        assert "racket" not in text.lower()
        payload = json.loads(text)
        assert set(payload["test"][0]) == {"input"}
