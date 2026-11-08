"""Focused tests for the proposed, unapproved scale-factor prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs


ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = ROOT / "generators/2dacb90452ce/workspace/parametric/prototype.py"
EXPECTED_CANONICAL_SHA256 = (
    "511f58f5d47190acd7307da0e87d1e6d84d787e18b14ce8c3c14de0471730050"
)
EXPECTED_CANONICAL_RULE = "(rule! (lambda (g) (upscale g 2)))"
EXPECTED_ALTERNATIVE_RULE = "(rule! (lambda (g) (upscale g 3)))"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "scale-factor prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_2dacb90452ce", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_factor_is_exact_canonical_and_alternative_is_guarded():
    """Catches changing the canonical default or mutating more than the factor site."""
    proto = _prototype()
    canonical = proto.canonical_rule(root=ROOT)
    assert canonical == EXPECTED_CANONICAL_RULE
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert proto.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert tuple(proto.SCALE_FACTORS) == (2, 3)
    assert proto.DEFAULT_SCALE_FACTOR == 2
    assert proto.instantiate_rule(2, root=ROOT) == EXPECTED_CANONICAL_RULE
    alternative = proto.instantiate_rule(3, root=ROOT)
    assert alternative == EXPECTED_ALTERNATIVE_RULE
    assert proto.restore_canonical(alternative, root=ROOT) == EXPECTED_CANONICAL_RULE


@pytest.mark.parametrize("bad", [True, 1, 4, 2.0, "2", None])
def test_invalid_scale_factor_is_rejected(bad):
    """Catches accepting booleans, identity, unsupported, or noninteger settings."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="scale_factor"):
        proto.instantiate_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, 1.5, "0", None, -1])
def test_episode_seed_is_a_nonnegative_plain_integer(bad):
    """Catches implicit coercion or negative episode seeds."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        proto.choose_scale_factor(bad)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("demo_count", 0),
        ("query_count", 0),
        ("demo_count", True),
        ("query_count", 1.5),
        ("query_count", 13),
    ],
)
def test_episode_counts_are_bounded_plain_integers(name, bad):
    """Catches empty, boolean, fractional, and unbounded episode requests."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match=name):
        proto.generate_inputs(0, **{name: bad})


def test_inputs_are_deterministic_distinct_lawful_and_parameter_independent():
    """Catches duplicate queries, unlawful generator output, or parameter-coupled inputs."""
    proto = _prototype()
    assert proto.choose_scale_factor(0) == 2
    assert proto.choose_scale_factor(1) == 3
    assert proto.choose_scale_factor(2) == 2

    first = proto.generate_inputs(23, demo_count=2, query_count=4)
    second = proto.generate_inputs(23, demo_count=2, query_count=4)
    assert first == second
    assert len(first) == 6
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 6
    assert all(proto.GEN.self_check(grid) == [] for grid in first)
    assert max(len(grid) for grid in first) <= 5
    assert max(len(grid[0]) for grid in first) <= 5


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_real_racket_default_matches_canonical_and_three_x_has_literal_witness(bridge):
    """Catches a Python-only label path, wrong wrapper, or incorrect 3x semantics."""
    proto = _prototype()
    canonical = proto.instantiate_rule(2, root=ROOT)
    for pair in canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True):
        assert proto.evaluate(bridge, canonical, pair["input"]) == pair["output"]

    witness = [[2, 1], [3, 1]]
    assert proto.evaluate(bridge, proto.instantiate_rule(3, root=ROOT), witness) == [
        [2, 2, 2, 1, 1, 1],
        [2, 2, 2, 1, 1, 1],
        [2, 2, 2, 1, 1, 1],
        [3, 3, 3, 1, 1, 1],
        [3, 3, 3, 1, 1, 1],
        [3, 3, 3, 1, 1, 1],
    ]


def test_episode_keeps_one_factor_and_each_query_is_identified_from_demos(bridge):
    """Catches pairwise resampling or query checks that borrow query answers."""
    proto = _prototype()
    episodes = [
        proto.make_episode(bridge, seed, demo_count=2, query_count=4)
        for seed in (0, 1)
    ]
    assert {episode["parameters"]["scale_factor"] for episode in episodes} == {2, 3}

    for episode in episodes:
        factor = episode["parameters"]["scale_factor"]
        assert episode["demo_count"] == 2
        assert episode["query_count"] == 4
        assert len(episode["pairs"]) == 6
        assert episode["racket_program"] == proto.instantiate_rule(factor, root=ROOT)
        for pair in episode["pairs"]:
            assert len(pair["output"]) == factor * len(pair["input"])
            assert len(pair["output"][0]) == factor * len(pair["input"][0])

        analysis = proto.analyze_episode(bridge, episode)
        assert analysis["status"] == "no_ambiguity_found"
        assert analysis["demonstrations_used"] == [0, 1]
        assert len(analysis["queries"]) == 4
        for row in analysis["queries"]:
            assert row["status"] == "no_ambiguity_found"
            rival, = row["rivals"]
            assert rival["scale_factor"] == ({2, 3} - {factor}).pop()
            assert rival["refuting_demonstration_indices"] == [0, 1]
            assert rival["query_differs"] is True


def test_explicit_factors_share_inputs_for_the_same_seed(bridge):
    """Catches leaking the hidden factor into input sampling."""
    proto = _prototype()
    factor_two = proto.make_episode(
        bridge, 7, scale_factor=2, demo_count=2, query_count=4
    )
    factor_three = proto.make_episode(
        bridge, 7, scale_factor=3, demo_count=2, query_count=4
    )
    assert [pair["input"] for pair in factor_two["pairs"]] == [
        pair["input"] for pair in factor_three["pairs"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(factor_two["pairs"], factor_three["pairs"], strict=True)
    )


def test_public_projection_and_name_hide_private_episode_state(bridge):
    """Catches leaking factors, seeds, programs, or query labels through export names."""
    proto = _prototype()
    episode = proto.make_episode(bridge, 0, demo_count=2, query_count=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 2
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("scale_factor", "racket", "parameters", "seed", "query_output"):
        assert forbidden not in serialized

    name = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
    hidden_changed = deepcopy(episode)
    hidden_changed["seed"] = 999
    hidden_changed["parameters"] = {"scale_factor": 3}
    hidden_changed["racket_program"] = "private replacement"
    for pair in hidden_changed["pairs"][hidden_changed["demo_count"] :]:
        pair["output"] = [[9]]
    assert proto.public_filename(hidden_changed) == name

    visible_changed = deepcopy(episode)
    visible_changed["pairs"][0]["output"][0][0] = 9
    assert proto.public_filename(visible_changed) != name


def test_materialized_tree_has_two_complete_four_query_episodes(tmp_path):
    """Catches missing settings, truncated queries, unhashed evidence, or unverifiable exports."""
    proto = _prototype()
    out = tmp_path / "scale-factor"
    report = proto.materialize(out, seed=0, demo_count=2, query_count=4, root=ROOT)
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["canonical_labels_passed"] == 4
    assert report["counts"]["demonstrations"] == 4
    assert report["counts"]["queries"] == 8
    assert report["counts"]["query_ambiguities"] == 0
    assert report["counts"]["settings_seen"] == [2, 3]

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    assert len(list((out / "private" / "rules").glob("scale-factor-*.rkt"))) == 2
    assert len(list((out / "private" / "episodes").glob("*.json"))) == 2
    for path in public_paths:
        challenge = json.loads(path.read_text())
        assert path.name == proto.public_filename(challenge)
        assert len(challenge["train"]) == 2
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input"} for pair in challenge["test"])

    verification = proto.verify_tree(out, root=ROOT)
    assert verification["status"] == "pass"
    assert verification["files_verified"] == len(report["files"])
    assert verification["episodes_verified"] == 2

    with pytest.raises(FileExistsError):
        proto.materialize(out, seed=0, demo_count=2, query_count=4, root=ROOT)


def test_verify_tree_rejects_report_that_skips_all_episode_replay(tmp_path):
    """Catches turning semantic verification into a zero-episode pass by editing report.json."""
    proto = _prototype()
    out = tmp_path / "scale-factor"
    proto.materialize(out, seed=0, demo_count=2, query_count=4, root=ROOT)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["episodes"] = []
    report["counts"].update(
        episodes=0,
        demonstrations=0,
        queries=0,
        query_ambiguities=0,
        settings_seen=[],
    )
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")

    with pytest.raises(ValueError, match="episode"):
        proto.verify_tree(out, root=ROOT)


def test_verify_tree_rejects_generator_hash_rebinding(tmp_path):
    """Catches accepting evidence after its declared generator source is rebound."""
    proto = _prototype()
    out = tmp_path / "scale-factor"
    proto.materialize(out, seed=0, demo_count=2, query_count=4, root=ROOT)
    report_path = out / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["source_hashes"]["generator_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")

    with pytest.raises(ValueError, match="generator"):
        proto.verify_tree(out, root=ROOT)


def test_materializer_emits_public_files_in_visible_id_order(tmp_path, monkeypatch):
    """Catches leaking private seed/setting enumeration through creation order."""
    proto = _prototype()
    writes = []
    original = Path.write_bytes

    def tracked(path, data):
        if path.parent.name == "public" and path.name.startswith("challenge-"):
            writes.append(path.name)
        return original(path, data)

    monkeypatch.setattr(Path, "write_bytes", tracked)
    proto.materialize(
        tmp_path / "ordered-public",
        seed=0,
        demo_count=2,
        query_count=4,
        root=ROOT,
    )
    assert writes == sorted(writes)
