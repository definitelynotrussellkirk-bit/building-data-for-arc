"""Focused tests for the proposed, unapproved neighbourhood-radius prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/724d5770b986/workspace/parametric/prototype.py"


def test_prototype_exists():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_724d5770b986", PROTOTYPE_PATH)
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


def test_default_radius_executes_the_exact_canonical_rule(prototype, bridge):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "31f92053867f6921de4e420f4d92859d82e5fcf319edc87a74a1c03af61d51da"
    )
    assert prototype.materialize_rule(1, root=ROOT) == canonical
    assert prototype.rule_setting(canonical, root=ROOT) == 1

    pairs = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    actual = prototype.execute_rule_many(
        canonical,
        [pair["input"] for pair in pairs],
        bridge=bridge,
        root=ROOT,
    )
    assert actual == [pair["output"] for pair in pairs]


def test_radius_two_changes_only_the_neighbourhood_extent(prototype, bridge):
    canonical = prototype.materialize_rule(1, root=ROOT)
    radius_two = prototype.materialize_rule(2, root=ROOT)
    assert radius_two != canonical
    assert prototype.rule_setting(radius_two, root=ROOT) == 2

    grid = prototype.distinguishing_input()
    one = prototype.execute_rule(canonical, grid, bridge=bridge, root=ROOT)
    two = prototype.execute_rule(radius_two, grid, bridge=bridge, root=ROOT)
    assert one != two
    assert one[4][2] == 0
    assert two[4][2] == 1
    assert one[3][4] == two[3][4] == 6
    assert one[0][0] == two[0][0] == 1


def test_source_guard_rejects_tampering_and_invalid_radius(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    with pytest.raises(ValueError):
        prototype.materialize_rule(0, root=ROOT)
    with pytest.raises(ValueError):
        prototype.materialize_rule(True, root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical + " ", root=ROOT)
    with pytest.raises(ValueError):
        prototype.rule_callable(canonical.replace("(w (cols g))", "(w (+ 1 (cols g)))"), root=ROOT)


def test_each_setting_has_two_identifying_demos_and_four_distinct_queries(prototype, bridge):
    expected = {1: 1, 0: 2}
    for seed, radius in expected.items():
        episode = prototype.make_episode(
            seed,
            train_count=2,
            test_count=4,
            root=ROOT,
            bridge=bridge,
        )
        assert episode["parameters"] == {"radius": radius}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["ambiguities"] == []

        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
        assert len(set(serialized)) == 6
        assert all(prototype.distinguishing_cells(grid) for grid in inputs)

        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [
            row
            for row in episode["parameter_rivals"]
            if row["status"] == "refuted_by_demonstrations"
        ]
        assert [row["radius"] for row in matching] == [radius]
        assert [row["radius"] for row in refuted] == [3 - radius]
        assert refuted[0]["demonstration_mismatch_indices"] == [0, 1]
        assert refuted[0]["query_mismatch_indices"] == [0, 1, 2, 3]

        source = prototype.materialize_rule(radius, root=ROOT)
        actual = prototype.execute_rule_many(source, inputs, bridge=bridge, root=ROOT)
        expected_outputs = [pair["output"] for pair in episode["train"] + episode["test"]]
        assert actual == expected_outputs


def test_sampler_supports_declared_count_boundaries_without_clones(prototype, bridge):
    episode = prototype.make_episode(
        7,
        train_count=prototype.MAX_TRAIN_COUNT,
        test_count=prototype.MAX_TEST_COUNT,
        root=ROOT,
        bridge=bridge,
    )
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len(inputs) == prototype.MAX_TRAIN_COUNT + prototype.MAX_TEST_COUNT
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
    assert episode["ambiguities"] == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_count": 0, "test_count": 4},
        {"train_count": 2, "test_count": 0},
        {"train_count": True, "test_count": 4},
        {"train_count": 2, "test_count": 1.5},
        {"train_count": 5, "test_count": 4},
        {"train_count": 2, "test_count": 9},
    ],
)
def test_invalid_episode_counts_are_rejected(prototype, kwargs):
    with pytest.raises(ValueError):
        prototype.make_episode(1, root=ROOT, **kwargs)


@pytest.mark.parametrize("seed", [False, -1, 2**63, 1.5, "1"])
def test_invalid_episode_seeds_are_rejected(prototype, seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)


def test_public_projection_uses_only_visible_bytes(prototype, bridge):
    episode = prototype.make_episode(1, train_count=2, test_count=4, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public_challenge_bytes(public) == prototype.public_bytes(episode)
    assert public_challenge_id(public) == prototype.public_id(episode)

    mutated = copy.deepcopy(episode)
    mutated["seed"] = 999
    mutated["parameters"] = {"radius": 2}
    mutated["rule"]["racket_source"] = "private mutation"
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert prototype.public_id(mutated) == prototype.public_id(episode)
    assert prototype.public_bytes(mutated) == prototype.public_bytes(episode)

    public["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9


def test_evidence_writer_hashes_outputs_and_keeps_queries_private(prototype, tmp_path):
    out = tmp_path / "radius-evidence"
    report = prototype.write_evidence(
        (0, 1),
        train_count=2,
        test_count=4,
        out=out,
        root=ROOT,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 2,
        "settings_exercised": 2,
        "demonstrations_per_episode": 2,
        "queries_per_episode": 4,
        "ambiguous_parameter_rivals": 0,
        "canonical_pairs_checked": len(canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)),
    }
    assert {row["parameters"]["radius"] for row in report["episodes"]} == {1, 2}
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)

    public_names = []
    for episode_row in report["episodes"]:
        public_path = out / episode_row["public_path"]
        private_path = out / episode_row["private_path"]
        public_names.append(public_path.name)
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        assert public == prototype.public_challenge(private)
        assert public_path.name == f"challenge-{public_challenge_id(public)}.json"
        assert all("output" not in pair for pair in public["test"])
        assert all("output" in pair for pair in private["test"])
        leaked = json.dumps(public, sort_keys=True)
        for forbidden in ("radius", "racket", "seed", "parameter", "query_answer"):
            assert forbidden not in leaked

    assert len(set(public_names)) == 2
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((1, 0), train_count=2, test_count=4, out=out, root=ROOT)


def test_evidence_writer_rejects_duplicate_visible_challenges(prototype, tmp_path):
    with pytest.raises(ValueError, match="duplicate visible challenge"):
        prototype.write_evidence(
            (1, 1),
            train_count=2,
            test_count=4,
            out=tmp_path / "duplicate-evidence",
            root=ROOT,
        )
