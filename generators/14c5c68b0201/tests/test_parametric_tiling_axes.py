"""Racket-backed contract tests for the proposed tiling-axis extension."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "14c5c68b0201"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "fa934e93825cfb3338263045d7d27ce5d7f56f9ced48bbb04d897159bb8a112a"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "tiling-axis prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_14c5c68b0201", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_guarded_rule_materialization():
    """Catches default drift, a non-unique patch site, or an undeclared rule edit."""
    proto = _prototype()
    canonical = proto.canonical_rule(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert proto.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert tuple(proto.TILING_AXES) == ("both", "horizontal", "vertical")
    assert proto.DEFAULT_TILING_AXES == "both"
    assert proto.instantiate_rule("both", root=ROOT) == canonical

    horizontal = proto.instantiate_rule("horizontal", root=ROOT)
    vertical = proto.instantiate_rule("vertical", root=ROOT)
    assert len({canonical, horizontal, vertical}) == 3
    assert proto.restore_canonical(horizontal, root=ROOT) == canonical
    assert proto.restore_canonical(vertical, root=ROOT) == canonical

    for bad in (True, False, None, 0, "diagonal", ""):
        with pytest.raises((TypeError, ValueError), match="tiling_axes"):
            proto.instantiate_rule(bad, root=ROOT)


def test_real_racket_default_matches_every_labeled_canonical_pair():
    """Catches a wrapper/evaluator bug even when the source text is hash-correct."""
    proto = _prototype()
    program = proto.instantiate_rule("both", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    with RacketBridge() as bridge:
        for pair in pairs:
            assert proto.evaluate(bridge, program, pair["input"]) == pair["output"]


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "0", None])
def test_episode_seed_is_a_nonnegative_plain_integer(bad):
    """Catches bool-as-int coercion and non-deterministic seed normalization."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        proto.choose_tiling_axes(bad)


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
    """Catches silent short episodes, bool counts, and unbounded evidence runs."""
    proto = _prototype()
    with pytest.raises((TypeError, ValueError), match=name):
        proto.generate_inputs(0, **{name: bad})


def test_inputs_are_distinct_lawful_deterministic_and_setting_independent():
    """Catches duplicate pairs, hidden-setting leakage, or an unlawful sampler."""
    proto = _prototype()
    first = proto.generate_inputs(23, demo_count=3, query_count=4)
    second = proto.generate_inputs(23, demo_count=3, query_count=4)
    assert first == second
    assert len(first) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in first}) == 7
    assert all(proto.GEN.self_check(grid) == [] for grid in first)

    with RacketBridge() as bridge:
        episodes = [
            proto.make_episode(
                bridge,
                23,
                tiling_axes=setting,
                demo_count=3,
                query_count=4,
            )
            for setting in proto.TILING_AXES
        ]
    inputs = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes
    ]
    assert inputs[0] == inputs[1] == inputs[2]


def test_all_settings_have_complete_four_query_racket_episodes_and_demo_refute_rivals():
    """Catches per-pair resampling, Python-only labels, or ambiguous demonstrations."""
    proto = _prototype()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        episodes = [
            proto.make_episode(bridge, seed, demo_count=3, query_count=4)
            for seed in (0, 1, 2)
        ]
        assert {episode["parameters"]["tiling_axes"] for episode in episodes} == set(
            proto.TILING_AXES
        )
        for episode in episodes:
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 4
            assert episode["demo_count"] == 3
            assert episode["query_count"] == 4
            all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({proto.grid_sha256(grid) for grid in all_inputs}) == 7
            selected = episode["parameters"]["tiling_axes"]
            selected_program = proto.instantiate_rule(selected, root=ROOT)
            for pair in episode["train"] + episode["test"]:
                assert proto.evaluate(bridge, selected_program, pair["input"]) == pair["output"]

            analysis = proto.analyze_episode(bridge, episode)
            assert analysis["status"] == "no_ambiguity_found"
            assert len(analysis["queries"]) == 4
            for query in analysis["queries"]:
                assert len(query["rivals"]) == 2
                assert all(rival["refuting_demonstration_indices"] for rival in query["rivals"])
                assert all(rival["query_differs"] for rival in query["rivals"])
                assert all(rival["status"] == "refuted_by_demonstrations" for rival in query["rivals"])


def test_public_projection_and_filename_ignore_all_private_state():
    """Catches leakage of settings, seeds, programs, or query answers into public artifacts."""
    proto = _prototype()
    with RacketBridge(max_calls_before_restart=64) as bridge:
        episode = proto.make_episode(bridge, 0, demo_count=3, query_count=4)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("tiling_axes", "parameters", "seed", "racket", "query_output"):
        assert forbidden not in serialized

    name = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)

    hidden_changed = deepcopy(episode)
    hidden_changed["seed"] = 999
    hidden_changed["parameters"] = {"tiling_axes": "vertical"}
    hidden_changed["racket_program"] = "private replacement"
    hidden_changed["test"][0]["output"] = [[9]]
    assert proto.public_filename(hidden_changed) == name

    visible_demo_changed = deepcopy(episode)
    visible_demo_changed["train"][0]["output"][0][0] = (
        visible_demo_changed["train"][0]["output"][0][0] + 1
    ) % 10
    assert proto.public_filename(visible_demo_changed) != name

    visible_query_changed = deepcopy(episode)
    visible_query_changed["test"][0]["input"][0][0] = (
        visible_query_changed["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_filename(visible_query_changed) != name


def test_materialized_tree_has_three_complete_four_query_episodes_and_replays(tmp_path):
    """Catches missing settings, short query sets, unhashed files, or non-replayable labels."""
    proto = _prototype()
    out = tmp_path / "tiling-axes"
    report = proto.materialize(
        out,
        seed=0,
        demo_count=3,
        query_count=4,
        root=ROOT,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["demonstrations"] == 9
    assert report["counts"]["queries"] == 12
    assert report["counts"]["canonical_labels_passed"] == 8
    assert report["counts"]["query_ambiguities"] == 0
    assert report["counts"]["nondistinguishing_rival_queries"] == 0
    assert report["counts"]["settings_seen"] == list(proto.TILING_AXES)
    assert set(report["sources"]) == {
        "prototype.py",
        "test_parametric_tiling_axes.py",
        "generator.py",
        "canonical_racket",
    }
    assert all(len(value) == 64 for value in report["sources"].values())

    public_ids_in_report_order = [
        Path(row["public_path"]).stem.removeprefix("challenge-")
        for row in report["episodes"]
    ]
    assert public_ids_in_report_order == sorted(public_ids_in_report_order)

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private" / "episodes").glob("episode-*.json"))
    rule_paths = sorted((out / "private" / "rules").glob("*.rkt"))
    assert len(public_paths) == len(private_paths) == len(rule_paths) == 3
    for path in public_paths:
        challenge = json.loads(path.read_text())
        assert path.name == proto.public_filename(challenge)
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input"} for pair in challenge["test"])

    verification = proto.verify_tree(out, root=ROOT)
    assert verification["status"] == "pass"
    assert verification["errors"] == []

    with pytest.raises(FileExistsError):
        proto.materialize(out, seed=0, demo_count=3, query_count=4, root=ROOT)


def test_evidence_verifier_rejects_public_file_tampering(tmp_path):
    """Catches a verifier that trusts its manifest without rechecking bytes/projection."""
    proto = _prototype()
    out = tmp_path / "tiling-axes-tamper"
    proto.materialize(out, seed=3, demo_count=3, query_count=4, root=ROOT)
    public_path = next((out / "public").glob("challenge-*.json"))
    challenge = json.loads(public_path.read_text())
    challenge["test"][0]["input"][0][0] = (challenge["test"][0]["input"][0][0] + 1) % 10
    public_path.write_text(json.dumps(challenge, indent=2, sort_keys=True) + "\n")
    verification = proto.verify_tree(out, root=ROOT)
    assert verification["status"] == "failed"
    assert any("hash" in error or "public" in error for error in verification["errors"])


def test_evidence_verifier_rejects_noncanonical_public_bytes_after_receipt_rewrite(tmp_path):
    """Catches semantic-only checks that trust a rewritten receipt over exact public bytes."""
    proto = _prototype()
    out = tmp_path / "tiling-axes-public-bytes"
    proto.materialize(out, seed=6, demo_count=3, query_count=4, root=ROOT)
    public_path = next((out / "public").glob("challenge-*.json"))
    challenge = json.loads(public_path.read_text())
    public_path.write_text(json.dumps(challenge, indent=2, sort_keys=True) + "\n")

    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    relative = str(public_path.relative_to(out))
    report["files"][relative] = hashlib.sha256(public_path.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = proto.verify_tree(out, root=ROOT)
    assert verification["status"] == "failed"
    assert any("public bytes" in error for error in verification["errors"])


def test_evidence_verifier_rejects_rule_path_outside_tree(tmp_path):
    """Catches report-controlled reads of Racket source outside the evidence tree."""
    proto = _prototype()
    out = tmp_path / "tiling-axes-path"
    proto.materialize(out, seed=9, demo_count=3, query_count=4, root=ROOT)

    report_path = out / "report.json"
    report = json.loads(report_path.read_text())
    row = report["episodes"][0]
    outside = tmp_path / "outside.rkt"
    outside.write_text(proto.instantiate_rule(row["tiling_axes"], root=ROOT))
    row["rule_path"] = "../outside.rkt"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    verification = proto.verify_tree(out, root=ROOT)
    assert verification["status"] == "failed"
    assert any("unsafe" in error and "rule" in error for error in verification["errors"])


def test_materializer_rejects_duplicate_or_colliding_public_ids(tmp_path, monkeypatch):
    """Catches silent public-file overwrite when two payloads share an identifier."""
    proto = _prototype()
    monkeypatch.setattr(proto, "public_challenge_id", lambda challenge: "0" * 64)
    with pytest.raises(ValueError, match="duplicate.*public|public.*collision"):
        proto.materialize(
            tmp_path / "tiling-axes-collision",
            seed=0,
            demo_count=1,
            query_count=1,
            root=ROOT,
        )
