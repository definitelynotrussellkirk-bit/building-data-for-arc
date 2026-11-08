"""Semantic regressions for Depth-Colored Nested Frames (2d5acf84dd20)."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.2d5acf84dd20.generator"
)

TASK_ID = "2d5acf84dd20"
EXPECTED_RULE_HASH = "9cbecad9efb8"
BANDS = ("easy", "medium", "hard")


def _prior_audit_counterexample() -> list[list[int]]:
    """Three side-by-side components accepted by the old area-rank generator."""
    rows = (
        "0000000000000",
        "0000000000100",
        "0000000011100",
        "0000000000000",
        "0000000000000",
        "0001000000000",
        "0011000000000",
        "0001000000000",
        "0001000000000",
        "0000000000000",
        "0000001111110",
        "0000001111110",
        "0000000000000",
    )
    return [[int(value) for value in row] for row in rows]


def test_rule_hash_and_all_canonical_pairs_are_grounded():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(
            rival(pair["input"]) == pair["output"] for pair in pairs
        ), name


def test_prior_disjoint_area_rank_counterexample_is_rejected():
    errors = gen.self_check(_prior_audit_counterexample())
    assert errors
    assert any("nested" in error or "frame" in error for error in errors)


def test_every_declared_boundary_override_is_exact_and_observable():
    for band in BANDS:
        for frame_count in (2, 4):
            for layout_style in ("concentric", "offset"):
                for outer_margin in ("edge", "inset"):
                    requested = {
                        "frame_count": frame_count,
                        "layout_style": layout_style,
                        "outer_margin": outer_margin,
                    }
                    grid = gen.generate(
                        914,
                        37,
                        difficulty=band,
                        **requested,
                    )
                    assert gen.observe_overrides(grid) == requested
                    assert gen.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": requested},
                    ) == []
                    assert len(grid) <= 30
                    assert len(grid[0]) <= 30


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"frame_count": 1},
        {"frame_count": 5},
        {"layout_style": "diagonal"},
        {"outer_margin": "floating"},
    ],
)
def test_invalid_and_unknown_overrides_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 1, **kwargs)


def test_every_default_draw_is_strictly_canonical_like():
    for band in BANDS:
        for sample_index in range(32):
            grid = gen.generate(500 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.strict_canonical_like(grid) == []


def test_declared_schedule_profiles_match_the_schedule_hook():
    observed = {
        gen.schedule_profile(123, sample_index, difficulty="medium")
        for sample_index in range(16)
    }
    assert observed == set(gen.SCHEDULE_PROFILES)


def test_offset_profiles_always_refute_recentering():
    for band in BANDS:
        for sample_index in range(1, 40, 2):
            grid = gen.generate(1993158372, sample_index, difficulty=band)
            analysis = gen._analyze(grid)
            if analysis["layout_style"] == "offset":
                assert (
                    gen.LESSON_COMPETITORS["recenter_frames"](grid)
                    != gen.rule_mirror(grid)
                ), (band, sample_index, analysis)


def test_every_rotation_of_five_consecutive_pairs_is_identifiable():
    seed = 1993158372
    pairs = []
    for sample_index in range(5, 10):
        grid = gen.generate(seed, sample_index, difficulty="easy")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == [], query_index


def test_every_sliding_four_demo_window_rejects_named_competitors():
    for band in BANDS:
        for start in range(8):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(44, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(45, start + gen.EXAMPLES_NEEDED, difficulty=band)
            assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), name


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    for band in BANDS:
        first = gen.generate(771, 19, difficulty=band)
        second = gen.generate(771, 19, difficulty=band)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        pristine = copy.deepcopy(first)
        first[0][0] = (first[0][0] + 1) % 10
        assert gen.generate(771, 19, difficulty=band) == pristine
        assert random.getstate() == state
