"""Focused tests for the proposed, unapproved triangle-leg prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/747486860e56/workspace/parametric/prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "triangle-leg prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_747486860e56", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_default_rule_is_exact_canonical_and_alternative_is_one_guarded_change(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("residual_minus_one", root=ROOT) == canonical

    alternative = prototype.materialize_rule("residual_count", root=ROOT)
    assert alternative != canonical
    assert canonical.count(prototype.CANONICAL_LEG_SITE) == 1
    assert alternative.count(prototype.ALTERNATIVE_LEG_SITE) == 1
    assert alternative.replace(
        prototype.ALTERNATIVE_LEG_SITE, prototype.CANONICAL_LEG_SITE, 1
    ) == canonical


@pytest.mark.parametrize("value", [True, 1, "plus_one", None])
def test_invalid_triangle_leg_mode_is_rejected(prototype, value):
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


def test_source_guard_rejects_unrelated_or_whitespace_tampering(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical + " ")
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical.replace("(objects-multicolor g 0)", "(objects-multicolor g 1)"))


def test_canonical_setting_reproduces_every_labeled_canonical_pair(prototype, bridge):
    source = prototype.materialize_rule("residual_minus_one", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_triangle_leg_setting_changes_every_authored_fixture(prototype, bridge):
    fixtures = prototype.fixtures()
    canonical = prototype.materialize_rule("residual_minus_one", root=ROOT)
    alternative = prototype.materialize_rule("residual_count", root=ROOT)
    assert len(fixtures) == 4
    for fixture in fixtures:
        assert fixture["residual_count"] <= min(len(fixture["input"]), len(fixture["input"][0]))
        assert prototype.execute_rule(canonical, fixture["input"], bridge=bridge) != prototype.execute_rule(
            alternative, fixture["input"], bridge=bridge
        )


def test_episode_draws_parameter_once_and_demonstrations_refute_other_setting(prototype, bridge):
    episodes = [prototype.make_episode(seed, root=ROOT, bridge=bridge) for seed in (0, 1)]
    assert {episode["parameters"]["triangle_leg_mode"] for episode in episodes} == set(
        prototype.ALLOWED_TRIANGLE_LEG_MODES
    )
    for episode in episodes:
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["triangle_leg_mode"] for row in matching] == [
            episode["parameters"]["triangle_leg_mode"]
        ]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_challenge_allowlist_hides_rule_and_query_answer(prototype, bridge):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    before = json.loads(json.dumps(episode))
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    for forbidden in ("triangle_leg_mode", "racket", "seed", "parameter"):
        assert forbidden not in serialized
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_hashes_files_and_keeps_query_answers_private(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
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
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "0"])
def test_invalid_episode_seed_is_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)
