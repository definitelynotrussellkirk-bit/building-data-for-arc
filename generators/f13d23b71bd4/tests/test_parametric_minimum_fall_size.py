"""Focused tests for the proposed minimum-fall-size prototype.

These tests do not change or approve the selected canonical generator.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_id


TASK_ID = "f13d23b71bd4"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
CANONICAL_SHA256 = "71a162d2019efc9e1dad31b9b6f99b2a6f80089126ad749ee444696b61efbf45"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the proposed task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location(
        "parametric_f13d23b71bd4_minimum_fall_size", SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _blank(height: int = 9, width: int = 15):
    return [[7] * width for _ in range(height)]


def _paint(cells_by_colour, *, height: int = 9, width: int = 15):
    grid = _blank(height, width)
    for colour, cells in cells_by_colour.items():
        for row, column in cells:
            assert grid[row][column] == 7
            grid[row][column] = colour
    return grid


def _threshold_witness():
    return _paint({
        2: {(1, 1), (1, 2)},
        3: {(1, 4), (2, 4), (2, 5)},
        4: {(1, 8), (1, 9), (2, 8), (2, 9)},
        5: {(1, 12), (2, 12), (2, 13), (3, 13), (3, 14)},
    })


def _expected_threshold_outputs():
    stationary_two = {(1, 1), (1, 2)}
    size_three_initial = {(1, 4), (2, 4), (2, 5)}
    size_three_bottom = {(7, 4), (8, 4), (8, 5)}
    size_four_initial = {(1, 8), (1, 9), (2, 8), (2, 9)}
    size_four_bottom = {(7, 8), (7, 9), (8, 8), (8, 9)}
    size_five_bottom = {(6, 12), (7, 12), (7, 13), (8, 13), (8, 14)}
    return {
        3: _paint({2: stationary_two, 3: size_three_bottom,
                   4: size_four_bottom, 5: size_five_bottom}),
        4: _paint({2: stationary_two, 3: size_three_initial,
                   4: size_four_bottom, 5: size_five_bottom}),
        5: _paint({2: stationary_two, 3: size_three_initial,
                   4: size_four_initial, 5: size_five_bottom}),
    }


def test_default_materialization_is_exact_and_alternates_only_threshold(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.materialize_rule(4, root=ROOT) == canonical
    for threshold in (3, 5):
        alternate = prototype.materialize_rule(threshold, root=ROOT)
        assert alternate != canonical
        assert alternate.replace(
            f"(>= (obj-size obj) {threshold})", "(>= (obj-size obj) 4)", 1
        ) == canonical


@pytest.mark.parametrize("value", [True, False, 3.0, "4", 2, 6, None])
def test_invalid_threshold_values_fail_closed(prototype, value):
    with pytest.raises(ValueError, match="minimum_fall_size"):
        prototype.materialize_rule(value, root=ROOT)


def test_real_racket_enforces_hand_derived_threshold_boundaries_and_fresh_canvas(prototype):
    grid = _threshold_witness()
    before = copy.deepcopy(grid)
    expected = _expected_threshold_outputs()
    with RacketBridge() as bridge:
        for threshold in (3, 4, 5):
            actual = prototype.execute_rule(
                prototype.materialize_rule(threshold, root=ROOT),
                grid,
                bridge=bridge,
            )
            assert actual == expected[threshold]
    assert grid == before


def test_episode_has_one_fixed_setting_three_demos_and_four_distinct_queries(prototype):
    with RacketBridge() as bridge:
        episode = prototype.make_episode(
            11,
            minimum_fall_size=4,
            demo_count=3,
            query_count=4,
            difficulty="medium",
            root=ROOT,
            bridge=bridge,
        )
    assert episode["status"] == "proposed_unapproved"
    assert episode["approved"] is False
    assert episode["parameters"] == {"minimum_fall_size": 4}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({pair["input_sha256"] for pair in pairs}) == 7
    assert all(pair["minimum_fall_size"] == 4 for pair in pairs)
    selected, = [row for row in episode["parameter_rivals"]
                 if row["minimum_fall_size"] == 4]
    assert selected["status"] == "matches_episode"
    for rival in [row for row in episode["parameter_rivals"]
                  if row["minimum_fall_size"] != 4]:
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
    assert episode["ambiguities"] == []


def test_episode_selection_counts_and_determinism_do_not_touch_global_rng(prototype):
    assert {prototype.parameters_for_seed(seed)["minimum_fall_size"]
            for seed in (0, 1, 2)} == {3, 4, 5}
    random.seed(1947)
    before = random.getstate()
    with RacketBridge() as bridge:
        first = prototype.make_episode(2, demo_count=2, query_count=4,
                                       root=ROOT, bridge=bridge)
        second = prototype.make_episode(2, demo_count=2, query_count=4,
                                        root=ROOT, bridge=bridge)
    assert first == second
    assert random.getstate() == before
    for kwargs in (
        {"demo_count": 0}, {"demo_count": True}, {"demo_count": 17},
        {"query_count": 0}, {"query_count": False}, {"query_count": 17},
        {"difficulty": "extreme"},
    ):
        with pytest.raises(ValueError):
            prototype.make_episode(0, root=ROOT, **kwargs)


def test_public_challenge_masks_answers_and_identity_uses_visible_content_only(prototype):
    with RacketBridge() as bridge:
        episode = prototype.make_episode(0, demo_count=3, query_count=4,
                                         root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    public_id = public_challenge_id(public)

    private_only_mutation = copy.deepcopy(episode)
    private_only_mutation["seed"] = 999999
    private_only_mutation["parameters"]["minimum_fall_size"] = 5
    private_only_mutation["test"][0]["output"][0][0] = (
        private_only_mutation["test"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_challenge(private_only_mutation) == public
    assert public_challenge_id(prototype.public_challenge(private_only_mutation)) == public_id

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 0
    assert episode == before


def test_write_evidence_uses_opaque_public_ids_and_hashes_retained_files(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (2, 0, 1),
        out=out,
        root=ROOT,
        demo_count=3,
        query_count=4,
        difficulty="medium",
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 3
    assert report["counts"]["train_pairs"] == 9
    assert report["counts"]["query_pairs"] == 12
    assert report["counts"]["distinct_input_grids"] == 21
    assert report["counts"]["settings_exercised"] == 3
    assert report["counts"]["canonical_pairs_checked"] == 4
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        visible_id = public_challenge_id(public)
        assert public_path.name == f"challenge-{visible_id}.json"
        assert row["public_id"] == visible_id
        assert prototype.public_challenge(private) == public
        assert "minimum-fall-size" not in public_path.name

    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0,), out=out, root=ROOT)
