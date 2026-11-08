"""Regression and teaching-contract tests for f4725b891d89."""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    grid_profile,
    header_entries,
    load_generator,
    observed_axes,
    reference_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_RULE_HASH = "d0cb884b1dae"


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": reference_output(grid)}


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{GEN.TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_rule_pin_and_python_mirror_match_all_canonical_pairs():
    assert getattr(GEN, "RULE_HASH", None) == EXPECTED_RULE_HASH
    assert getattr(GEN, "VERSION", None) == "3.0.0"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_exact_axis_boundary_round_trips(difficulty):
    for h in (8, 18):
        for w in (8, 18):
            for n_top in (3, 5):
                for n_left in (3, 5):
                    requested = {
                        "frame_h": h,
                        "frame_w": w,
                        "n_top_markers": n_top,
                        "n_left_markers": n_left,
                    }
                    grid = GEN.generate(1031, h * 1000 + w * 100 + n_top * 10 + n_left,
                                        difficulty=difficulty, **requested)
                    assert GEN.self_check(grid) == []
                    assert observed_axes(grid) == requested
                    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"frame_h": 7},
        {"frame_h": 19},
        {"frame_w": True},
        {"n_top_markers": 2},
        {"n_top_markers": 6},
        {"n_left_markers": 3.0},
    ],
)
def test_invalid_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **overrides)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_profile_floor_support_and_palette_breadth_in_every_band():
    canonical_profiles = {grid_profile(pair["input"]) for pair in canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        grids = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grids.append(GEN.generate(seed, seed % 7919 + index, difficulty=band))
        assert any(grid_profile(grid) in canonical_profiles for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert {4, 5} <= {grid_profile(grid)[2] for grid in grids}
        assert len({frozenset(color for _pos, color in header_entries(grid)[0])
                    for grid in grids}) >= 4
        assert len({(len(grid), len(grid[0])) for grid in grids}) >= 4


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(901, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(901, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))
    first[0][0] = 0
    assert first != second


def test_structural_mutations_are_rejected():
    base = GEN.generate(404, 2, frame_h=9, frame_w=9,
                        n_top_markers=4, n_left_markers=4)
    assert GEN.self_check(base) == []

    broken_border = copy.deepcopy(base)
    broken_border[0][0] = 0

    interior_ink = copy.deepcopy(base)
    interior_ink[2][2] = 9

    too_few_top = copy.deepcopy(base)
    top, _left = header_entries(too_few_top)
    for col, _color in top[2:]:
        too_few_top[1][col] = 0

    mismatched_color_sets = copy.deepcopy(base)
    _top, left = header_entries(mismatched_color_sets)
    mismatched_color_sets[left[0][0]][1] = 9

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    for grid in (broken_border, interior_ink, too_few_top,
                 mismatched_color_sets, ragged):
        assert GEN.self_check(grid), grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_schedule_profile_is_a_real_counterexample_and_lessons_identify_rule(difficulty):
    profiles = set(GEN.SCHEDULE_PROFILES)
    for start in range(8):
        grids = [GEN.generate(7300 + start, start + offset, difficulty=difficulty)
                 for offset in range(GEN.EXAMPLES_NEEDED + 1)]
        assert {GEN.schedule_profile(7300 + start, start + offset, difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)} == profiles
        for grid in grids:
            truth = reference_output(grid)
            assert GEN.rule_mirror(grid) == truth
            for rival_name, rival in GEN.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, rival_name
            for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
                assert witness(grid), witness_name
        demos = [_pair(grid) for grid in grids[:GEN.EXAMPLES_NEEDED]]
        query = _pair(grids[-1])
        assert GEN.lesson_identifiable(demos, query) == []


def test_no_declared_rival_matches_every_canonical_label():
    pairs = canonical_pairs()
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name
