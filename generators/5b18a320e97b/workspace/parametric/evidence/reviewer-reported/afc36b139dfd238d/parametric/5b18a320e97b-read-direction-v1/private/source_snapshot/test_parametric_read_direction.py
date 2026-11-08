"""Racket-backed contract tests for the proposed read-direction prototype."""
from __future__ import annotations

import copy
import hashlib
import json
import importlib.util
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK_ID = "5b18a320e97b"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EXPECTED_CANONICAL_SHA256 = "c88b81c9786841551051d1c26625321375d4849229760bd0e40b7329fda63231"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "read-direction prototype must be runnable"
    spec = importlib.util.spec_from_file_location(
        f"parametric_read_direction_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30) as instance:
        yield instance


def test_default_rule_is_exact_canonical_and_reverse_is_one_guarded_change(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert prototype.CANONICAL_SHA256 == EXPECTED_CANONICAL_SHA256
    assert prototype.DEFAULT_READ_DIRECTION == "forward"
    assert prototype.materialize_rule("forward", source=canonical) == canonical

    reverse = prototype.materialize_rule("reverse", source=canonical)
    assert reverse != canonical
    assert reverse.count(prototype.REVERSE_SORT_BINDING) == 1
    assert prototype.restore_canonical(reverse) == canonical


def test_exact_default_racket_replays_every_canonical_label(prototype, bridge):
    canonical = prototype.materialize_rule("forward", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(canonical, pair["input"], bridge=bridge) == pair["output"]


def test_reverse_racket_reverses_the_visible_line_order(prototype, bridge):
    first = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]
    reverse = prototype.materialize_rule("reverse", root=ROOT)
    assert prototype.execute_rule(reverse, first["input"], bridge=bridge) == [
        [4, 2, 1],
        [4, 2, 1],
        [4, 2, 1],
    ]


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, 1.0, "backward", "FORWARD"])
def test_materialize_rule_rejects_undeclared_settings(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="read_direction"):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [True, False, -1, 1.0, "1", None])
def test_episode_seed_requires_a_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.choose_setting(bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demo_count": 0},
        {"demo_count": True},
        {"query_count": 0},
        {"query_count": 1.5},
    ],
)
def test_episode_counts_require_positive_plain_integers(prototype, bridge, kwargs):
    with pytest.raises((TypeError, ValueError), match="count"):
        prototype.make_episode(0, root=ROOT, bridge=bridge, **kwargs)


def test_two_seeds_cover_fixed_setting_three_demo_four_query_episodes(prototype, bridge):
    episodes = [
        prototype.make_episode(seed, root=ROOT, bridge=bridge)
        for seed in (0, 1)
    ]
    assert {episode["parameters"]["read_direction"] for episode in episodes} == set(
        prototype.READ_DIRECTIONS
    )
    for episode in episodes:
        selected = episode["parameters"]["read_direction"]
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert len(episode["pairs"]) == 7
        assert {pair["read_direction"] for pair in episode["pairs"]} == {selected}
        inputs = [
            json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["pairs"]
        ]
        assert len(set(inputs)) == 7

        analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
        assert analysis["status"] == "no_ambiguity_found"
        selected_rows = [
            row for row in analysis["settings"] if row["status"] == "matches_episode"
        ]
        rival_rows = [
            row
            for row in analysis["settings"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["read_direction"] for row in selected_rows] == [selected]
        assert len(rival_rows) == 1
        assert rival_rows[0]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival_rows[0]["query_mismatch_indices"] == [0, 1, 2, 3]


def test_episode_inputs_cover_both_orientations_and_multiple_color_counts(prototype, bridge):
    episode = prototype.make_episode(7, root=ROOT, bridge=bridge)
    profiles = [pair["sampling"]["scene_profile"] for pair in episode["pairs"]]
    assert any(profile.startswith("horizontal_") for profile in profiles)
    assert any(profile.startswith("vertical_") for profile in profiles)
    assert len({int(profile.rsplit("n", 1)[1]) for profile in profiles}) >= 4


def test_public_projection_and_filename_depend_only_on_visible_challenge(prototype, bridge):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("read_direction", "racket", "program", "seed", "counterfactual"):
        assert forbidden not in serialized

    name = prototype.public_filename(episode)
    assert name.startswith("challenge-") and name.endswith(".json")
    changed_private = copy.deepcopy(episode)
    changed_private["seed"] = 999
    changed_private["parameters"] = {"read_direction": "private-change"}
    changed_private["program"] = "private-change"
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
    assert prototype.public_filename(changed_private) == name

    changed_visible = copy.deepcopy(episode)
    changed_visible["train"][0]["output"][0][0] = (
        changed_visible["train"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_filename(changed_visible) != name



def test_public_writer_rejects_duplicate_visible_payloads(prototype, bridge, tmp_path):
    episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    path = tmp_path / prototype.public_filename(episode)

    prototype._write_public(path, public)
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype._write_public(path, public)


def test_evidence_writer_fails_closed_on_existing_output(prototype, tmp_path):
    out = tmp_path / "already-there"
    out.mkdir()
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert list(out.iterdir()) == []


def test_evidence_writer_builds_verified_public_private_bundle(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (1, 0),
        out=out,
        root=ROOT,
        demo_count=3,
        query_count=4,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "read_direction",
        "allowed_values": ["forward", "reverse"],
        "original_default": "forward",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 8
    assert report["counts"]["distinct_input_grids"] == 14
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0

    verification = json.loads((out / "verification.json").read_text())
    assert verification["status"] == "pass"
    assert verification["episodes_checked"] == 2
    assert verification["labels_checked"] == 14
    assert verification["rival_predictions_checked"] == 28

    rules = {row["read_direction"]: row for row in report["rules"]}
    assert set(rules) == set(prototype.READ_DIRECTIONS)
    for setting, row in rules.items():
        path = out / row["path"]
        assert path.read_text() == prototype.materialize_rule(setting, root=ROOT)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)

    seen_public_names = set()
    for row in report["episodes"]:
        episode = json.loads((out / row["private_path"]).read_text())
        analysis = json.loads((out / row["analysis_path"]).read_text())
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_text())
        assert analysis["status"] == "no_ambiguity_found"
        assert public == prototype.public_challenge(episode)
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert public_path.name == prototype.public_filename(episode)
        assert public_path.name.startswith("challenge-")
        identifier = public_path.name[len("challenge-") : -len(".json")]
        assert len(identifier) == 64
        assert set(identifier) <= set("0123456789abcdef")
        assert all("output" not in pair for pair in public["test"])
        seen_public_names.add(public_path.name)
    assert len(seen_public_names) == 2

    for row in report["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
