"""Focused tests for the proposed direction-parametric prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/61c0bcd32328/workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "The task-local direction prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_61c0bcd32328", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_rule_is_exact_and_counterclockwise_edit_is_guarded(prototype):
    canonical = prototype.canonical_rule(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e"
    )
    assert prototype.program_for_direction("clockwise", root=ROOT) == canonical
    alternate = prototype.program_for_direction("counterclockwise", root=ROOT)
    assert alternate != canonical
    assert "((eq? corner 'tl) (- h 1 r2))" in alternate
    assert "((eq? corner 'tr) (- 0 c1))" in alternate
    with pytest.raises(ValueError, match="canonical.*SHA|SHA.*canonical"):
        prototype.program_for_direction("counterclockwise", source=canonical + " ")


@pytest.mark.parametrize("value", [None, True, False, 1, "cw", "left", "CLOCKWISE"])
def test_invalid_direction_values_fail_visibly(prototype, value):
    with pytest.raises(ValueError, match="direction"):
        prototype.program_for_direction(value, root=ROOT)


def test_real_racket_sends_singleton_to_direction_specific_corner(prototype):
    grid = [[7 for _ in range(6)] for _ in range(6)]
    grid[0][0] = 1
    grid[2][2] = 2
    grid[4][3] = 3
    before = copy.deepcopy(grid)

    clockwise = prototype.execute_rule(
        prototype.program_for_direction("clockwise", root=ROOT), grid
    )
    counterclockwise = prototype.execute_rule(
        prototype.program_for_direction("counterclockwise", root=ROOT), grid
    )

    expected_clockwise = copy.deepcopy(grid)
    expected_clockwise[0][5] = 1
    expected_counterclockwise = copy.deepcopy(grid)
    expected_counterclockwise[5][0] = 1
    assert clockwise == expected_clockwise
    assert counterclockwise == expected_counterclockwise
    assert grid == before


def test_episode_fixes_one_setting_and_refutes_both_shortcuts(prototype):
    state = random.getstate()
    seen = set()
    for seed in (0, 1):
        episode = prototype.make_episode(
            seed,
            train_count=3,
            test_count=4,
            difficulty="medium",
            root=ROOT,
        )
        replay = prototype.make_episode(
            seed,
            train_count=3,
            test_count=4,
            difficulty="medium",
            root=ROOT,
        )
        assert replay == episode
        direction = episode["parameters"]["direction"]
        seen.add(direction)
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({prototype.grid_sha256(pair["input"]) for pair in pairs}) == 7
        assert {pair["direction"] for pair in pairs} == {direction}
        rival = episode["parameter_rivals"][0]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
        shortcut = episode["shortcut_rivals"][0]
        assert shortcut["name"] == "ignore_singleton_corner_components"
        assert shortcut["status"] == "refuted_by_demonstrations"
        assert shortcut["demonstration_mismatch_indices"]
        assert not episode["ambiguities"]
    assert seen == set(prototype.DIRECTIONS)
    assert random.getstate() == state


def test_public_identifier_depends_only_on_visible_bytes(prototype):
    episode = prototype.make_episode(0, train_count=3, test_count=4, root=ROOT)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    changed_private = copy.deepcopy(episode)
    changed_private["seed"] = 999999
    changed_private["parameters"]["direction"] = "counterclockwise"
    changed_private["test"][0]["output"][0][0] ^= 1
    assert public_challenge_bytes(prototype.public_challenge(changed_private)) == public_challenge_bytes(public)
    assert public_challenge_id(prototype.public_challenge(changed_private)) == public_challenge_id(public)


def test_evidence_has_two_settings_four_queries_and_exact_hashes(prototype, tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (0, 1),
        out=out,
        train_count=3,
        test_count=4,
        difficulty="medium",
        root=ROOT,
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["queries_per_episode"] == 4
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["canonical_pairs_checked"] == len(
        canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)
    )
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert len({row["public_id"] for row in report["episodes"]}) == 2

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        private = json.loads(private_path.read_text())
        assert public_path.read_bytes() == public_challenge_bytes(prototype.public_challenge(private))
        assert hashlib.sha256(public_path.read_bytes()).hexdigest() == row["public_id"]
        assert len(private["test"]) == 4
        assert all("output" in pair for pair in private["test"])
        assert all("output" not in pair for pair in json.loads(public_path.read_text())["test"])
        rule = (out / private["racket_path"]).read_text()
        assert hashlib.sha256(rule.encode()).hexdigest() == private["racket_sha256"]

    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
