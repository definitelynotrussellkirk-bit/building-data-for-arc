"""Focused semantic regressions for nested-frame generator 819d58220317."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import shutil

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application


ROOT = Path(__file__).resolve().parents[1]
TASK = "819d58220317"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK}.generator"
)
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/3b7f019624a4/H46__819d58220317.json"
)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_rule_authorities_and_hash_are_synchronized_exactly():
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert target["raw_code"] == target["target_code"] == canonical
    assert target["canonicalization_status"] == (
        "synchronized_to_canonical_program_solution"
    )
    normalized = " ".join(canonical.split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert target["rule_hash"] == GEN.RULE_HASH == digest == "0db6b727334d"


def test_all_five_canonical_pairs_are_accepted_and_mirror_exactly():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_canonical_pairs_is_pure_and_a_b_a_stable():
    source = _canonical_row()["program_solution"]
    pairs = _pairs()
    bridge = RacketBridge()
    try:
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 11),
        ("grid_h", 30),
        ("grid_w", 11),
        ("grid_w", 30),
        ("n_frames", 2),
        ("n_frames", 5),
        ("rank", 1),
        ("rank", 5),
        ("marker_layout", "single_side"),
        ("marker_layout", "multi_side"),
    ],
)
def test_every_declared_axis_boundary_is_realized_exactly(band, axis, value):
    grid = GEN.generate(771, 991, difficulty=band, **{axis: value})
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_linked_override_extremes_are_exact_and_incompatibilities_are_loud(band):
    vectors = (
        {
            "grid_h": 11,
            "grid_w": 11,
            "n_frames": 2,
            "rank": 1,
            "marker_layout": "single_side",
        },
        {
            "grid_h": 30,
            "grid_w": 30,
            "n_frames": 5,
            "rank": 5,
            "marker_layout": "multi_side",
        },
    )
    for overrides in vectors:
        grid = GEN.generate(123, 456, difficulty=band, **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 2, difficulty=band, grid_h=11, n_frames=5)
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 2, difficulty=band, rank=1, marker_layout="multi_side")


def test_unknown_controls_types_and_domains_fail_closed():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, invented_axis=1)
    with pytest.raises(ValueError, match="integer"):
        GEN.generate(0, 0, rank="2")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(0, 0, grid_h=10)
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(0, 0, marker_layout="diagonal")


def test_generation_is_deterministic_fresh_mutation_safe_and_rng_isolated():
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 9
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {
        _frozen(GEN.generate(seed, 17, difficulty="medium"))
        for seed in range(30)
    }
    by_index = {
        _frozen(GEN.generate(17, index, difficulty="medium"))
        for index in range(30)
    }
    assert len(by_seed) >= 28
    assert len(by_index) == 30


def test_sample_index_lessons_always_expose_both_semantic_branches():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            profiles = [
                GEN.semantic_profile(GEN.generate(seed, index, difficulty=band))
                for index in range(4)
            ]
            assert {profile["branch"] for profile in profiles} == {
                "ring",
                "innermost",
            }
            assert {profile["marker_layout"] for profile in profiles} == {
                "single_side",
                "multi_side",
            }


def test_linked_semantic_distribution_has_positive_support_per_band():
    for band in ("easy", "medium", "hard"):
        profiles = [
            GEN.semantic_profile(GEN.generate(10000 + seed, seed, difficulty=band))
            for seed in range(200)
        ]
        assert all(profile["valid"] for profile in profiles)
        branches = Counter(profile["branch"] for profile in profiles)
        layouts = Counter(profile["marker_layout"] for profile in profiles)
        frame_counts = Counter(profile["n_frames"] for profile in profiles)
        ranks = Counter(profile["rank"] for profile in profiles)
        assert branches["ring"] >= 60
        assert branches["innermost"] >= 60
        assert layouts["single_side"] >= 60
        assert layouts["multi_side"] >= 40
        assert len(frame_counts) >= 2
        assert len(ranks) >= 2
        assert min(profile["selected_blank_count"] for profile in profiles) > 0
        assert len({
            (
                profile["grid_h"],
                profile["grid_w"],
                profile["frame_bounds"],
                profile["marker_cells"],
            )
            for profile in profiles
        }) == len(profiles)


def test_self_check_rejects_structural_impostors_without_mutation():
    valid = GEN.generate(41, 5, difficulty="medium")
    cases: dict[str, list[list[int]]] = {
        "all_background": [[0] * 12 for _ in range(12)],
        "singleton": [[4]],
        "solid_yellow": [[4] * 12 for _ in range(12)],
    }

    broken_frame = copy.deepcopy(valid)
    yellow = next(
        (row, col)
        for row, values in enumerate(broken_frame)
        for col, value in enumerate(values)
        if value == 4
    )
    broken_frame[yellow[0]][yellow[1]] = 0
    cases["broken_frame"] = broken_frame

    red_inside = copy.deepcopy(valid)
    profile = GEN.semantic_profile(red_inside)
    red = profile["marker_cells"][0]
    red_inside[red[0]][red[1]] = 0
    outer = profile["outer_bounds"]
    red_inside[outer[0] + 1][outer[1] + 1] = 2
    cases["red_inside"] = red_inside

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 8
    cases["cyan_input"] = invalid_color

    rank_too_high = copy.deepcopy(_pairs()[0]["input"])
    rank_too_high[-1][1] = 2
    rank_too_high[-1][2] = 2
    cases["rank_too_high"] = rank_too_high

    for name, grid in cases.items():
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert GEN.observe_overrides(grid) == {}, name
        assert grid == snapshot, name
