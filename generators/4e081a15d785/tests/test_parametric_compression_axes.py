"""Focused tests for the proposed, unapproved compression-axis prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/4e081a15d785/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_4e081a15d785", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30.0) as runtime:
        yield runtime


def _deletion_counts(grid):
    rows = sum(1 for _ in itertools.groupby(map(tuple, grid)))
    columns = sum(1 for _ in itertools.groupby(zip(*grid)))
    return len(grid) - rows, len(grid[0]) - columns


def test_default_rule_is_exact_canonical_and_alternatives_are_guarded(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert canonical == "(rule! (compress-grid g))"
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule("both", root=ROOT) == canonical

    sources = {
        setting: prototype.materialize_rule(setting, root=ROOT)
        for setting in prototype.COMPRESSION_AXES
    }
    assert len(set(sources.values())) == 3
    assert {prototype.rule_setting(source) for source in sources.values()} == set(
        prototype.COMPRESSION_AXES
    )
    assert "dedup-consecutive" in sources["rows"]
    assert "dedup-consecutive" in sources["columns"]


@pytest.mark.parametrize("bad", [None, True, 0, "all", "row", "column", []])
def test_undeclared_axis_settings_are_rejected(prototype, bad):
    with pytest.raises((TypeError, ValueError)):
        prototype.materialize_rule(bad, root=ROOT)


@pytest.mark.parametrize("bad", [False, -1, 2**63, 1.5, "0"])
def test_episode_seed_must_be_a_bounded_nonnegative_plain_integer(prototype, bad):
    with pytest.raises((TypeError, ValueError)):
        prototype.choose_setting(bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demo_count": 0},
        {"query_count": 0},
        {"demo_count": True},
        {"query_count": 1.5},
        {"demo_count": 20, "query_count": 20},
    ],
)
def test_episode_counts_are_separate_positive_bounded_integers(prototype, bridge, kwargs):
    with pytest.raises((TypeError, ValueError)):
        prototype.make_episode(0, root=ROOT, bridge=bridge, **kwargs)


def test_exact_default_racket_replays_every_canonical_label(prototype, bridge):
    source = prototype.materialize_rule("both", root=ROOT)
    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_distinguishing_witness_separates_all_three_axis_settings(prototype, bridge):
    witness = prototype.distinguishing_input()
    outputs = {
        setting: prototype.execute_rule(
            prototype.materialize_rule(setting, root=ROOT), witness, bridge=bridge
        )
        for setting in prototype.COMPRESSION_AXES
    }
    assert outputs == {
        "both": [[1, 2], [3, 4]],
        "rows": [[1, 1, 2, 2], [3, 3, 4, 4]],
        "columns": [[1, 2], [1, 2], [3, 4], [3, 4]],
    }


def test_three_seeds_cover_fixed_setting_three_demo_four_query_episodes(
    prototype, bridge
):
    expected = {0: "both", 1: "rows", 2: "columns"}
    for seed, setting in expected.items():
        episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
        assert episode["parameters"] == {"compression_axes": setting}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["ambiguities"] == []

        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(pair["input"], sort_keys=True) for pair in pairs}) == 7
        assert all(all(value > 0 for value in _deletion_counts(pair["input"])) for pair in pairs)

        source = prototype.materialize_rule(setting, root=ROOT)
        assert all(
            prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]
            for pair in pairs
        )

        matching = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "matches_episode"
        ]
        refuted = [
            row for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["compression_axes"] for row in matching] == [setting]
        assert {row["compression_axes"] for row in refuted} == (
            set(prototype.COMPRESSION_AXES) - {setting}
        )
        assert all(row["demonstration_mismatch_indices"] for row in refuted)
        assert all(row["query_mismatch_indices"] == [0, 1, 2, 3] for row in refuted)


def test_demo_and_query_counts_are_independently_configurable(prototype, bridge):
    episode = prototype.make_episode(
        4, demo_count=2, query_count=5, root=ROOT, bridge=bridge
    )
    assert episode["counts"] == {"demonstrations": 2, "queries": 5}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 5
    assert episode["ambiguities"] == []


def test_public_projection_and_filename_depend_only_on_visible_bytes(prototype, bridge):
    episode = prototype.make_episode(1, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public_challenge_bytes(public).endswith(b"\n")

    original_name = prototype.public_filename(episode)
    private_only = copy.deepcopy(episode)
    private_only["seed"] = 999
    private_only["parameters"]["compression_axes"] = "columns"
    private_only["test"][0]["output"][0][0] = (
        private_only["test"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_filename(private_only) == original_name

    visible_change = copy.deepcopy(episode)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert prototype.public_filename(visible_change) != original_name

    public["train"][0]["input"][0][0] = 9
    assert public != prototype.public_challenge(episode)


def test_evidence_writer_builds_verified_sorted_public_private_bundle(
    prototype, bridge, tmp_path
):
    out = tmp_path / "compression-axes-evidence"
    report = prototype.write_evidence(
        (0, 1, 2), out=out, root=ROOT, bridge=bridge
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 3,
        "settings_exercised": 3,
        "demonstrations": 9,
        "queries": 12,
        "ambiguous_parameter_rivals": 0,
    }

    stored_report = json.loads((out / "report.json").read_text())
    verification = json.loads((out / "verification.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    assert stored_report == report
    assert verification["status"] == "pass"
    assert verification["live_labels_checked"] == 27
    assert verification["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )

    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)
    assert {row["parameters"]["compression_axes"] for row in report["episodes"]} == set(
        prototype.COMPRESSION_AXES
    )

    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
        assert row["public_path"].endswith(f"challenge-{row['public_id']}.json")

    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    for setting in prototype.COMPRESSION_AXES:
        rule_path = out / f"private/rules/compression-axes-{setting}.rkt"
        assert rule_path.read_text() == prototype.materialize_rule(setting, root=ROOT) + "\n"


def test_duplicate_visible_challenges_fail_before_writing(prototype, bridge, tmp_path):
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible challenge"):
        prototype.write_evidence((0, 0), out=out, root=ROOT, bridge=bridge)
    assert not out.exists()


def test_evidence_writer_fails_closed_if_output_exists(prototype, bridge, tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0,), out=out, root=ROOT, bridge=bridge)
