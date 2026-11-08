from __future__ import annotations

import copy
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from puzzle_generators.per_puzzle.f6b9f647b109 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_sliding_lesson_window_is_identifiable_and_refutes_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(5)]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_sixteen_slot_schedule_declares_each_profile_once_per_period():
    observed = tuple(
        gen.schedule_profile(0, sample_index)
        for sample_index in range(len(gen.SCHEDULE_PROFILES))
    )
    assert len(observed) == 16
    assert observed == gen.SCHEDULE_PROFILES
    assert len(set(observed)) == len(observed)


def test_exact_override_axes_round_trip_at_boundaries_in_every_band():
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w in ((6, 6), (26, 26)):
            for major_axis in gen.MAJOR_AXES:
                for distance_profile in gen.DISTANCE_PROFILES:
                    for direction in gen.DIRECTIONS:
                        overrides = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "major_axis": major_axis,
                            "distance_profile": distance_profile,
                            "direction": direction,
                        }
                        grid = gen.generate(91, 17, difficulty=band, **overrides)
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == overrides


def test_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis="row")


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(1234, 0, difficulty="medium")
    red, blue, _, _ = gen._geometry(valid)

    no_blue = copy.deepcopy(valid)
    no_blue[blue[0]][blue[1]] = 0

    extra_red = copy.deepcopy(valid)
    extra_red[0][0] = 2
    if (0, 0) == red:
        extra_red[0][1] = 2

    same_row = copy.deepcopy(valid)
    same_row[blue[0]][blue[1]] = 0
    replacement_col = red[1] + 1 if red[1] + 1 < len(valid[0]) else red[1] - 1
    same_row[red[0]][replacement_col] = 1

    foreign_color = copy.deepcopy(valid)
    foreign_color[0][0] = 9
    if (0, 0) in (red, blue):
        foreign_color[-1][-1] = 9

    adjacent = [[0] * 6 for _ in range(6)]
    adjacent[2][2] = 2
    adjacent[3][3] = 1

    fixtures = [no_blue, extra_red, same_row, foreign_color, adjacent]
    for fixture in fixtures:
        assert gen.self_check(fixture), fixture


def test_generation_is_deterministic_fresh_and_preserves_global_rng_state():
    random.seed(20260726)
    state_before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_canonical_anchor_support_exists_in_every_band():
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 1):
            grid = gen.generate(808, sample_index, difficulty=band)
            assert gen.strict_canonical_like(grid) == []


def _scheduled_observation(sample_index: int) -> tuple[dict, list[list[int]]]:
    grid = gen.generate(271828, sample_index, difficulty="medium")
    return gen.observe_overrides(grid), grid


def test_default_schedule_crosses_every_direction_with_every_axis_distance_pair():
    expected_pairs = set(product(gen.MAJOR_AXES, gen.DISTANCE_PROFILES))
    support = {direction: set() for direction in gen.DIRECTIONS}

    for sample_index in range(len(gen.SCHEDULE_PROFILES)):
        observed, _ = _scheduled_observation(sample_index)
        support[observed["direction"]].add(
            (observed["major_axis"], observed["distance_profile"])
        )

    assert support == {direction: expected_pairs for direction in gen.DIRECTIONS}


def test_query_slot_recombines_its_direction_in_every_sliding_lesson_window():
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        demo_observations = [
            _scheduled_observation(start + offset)[0]
            for offset in range(gen.EXAMPLES_NEEDED)
        ]
        query_observation = _scheduled_observation(start + gen.EXAMPLES_NEEDED)[0]
        same_direction = [
            item
            for item in demo_observations
            if item["direction"] == query_observation["direction"]
        ]

        assert len(same_direction) == 1
        assert (
            same_direction[0]["major_axis"],
            same_direction[0]["distance_profile"],
        ) != (
            query_observation["major_axis"],
            query_observation["distance_profile"],
        )


def test_every_sliding_lesson_window_keeps_coverage_and_two_size_anchors():
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        items = [
            _scheduled_observation(start + offset)
            for offset in range(gen.EXAMPLES_NEEDED)
        ]
        observations = [item[0] for item in items]
        grids = [item[1] for item in items]

        assert {item["direction"] for item in observations} == set(gen.DIRECTIONS)
        assert {item["major_axis"] for item in observations} == set(gen.MAJOR_AXES)
        assert {item["distance_profile"] for item in observations} == set(
            gen.DISTANCE_PROFILES
        )
        assert sum(not gen.strict_canonical_like(grid) for grid in grids) >= 2


def test_every_semantic_witness_is_classified_as_rival_or_positive_branch():
    rival_claiming = set(gen.WITNESS_RIVALS)
    positive_branches = set(gen.BRANCH_WITNESSES)

    assert positive_branches == {
        "row_dominant_path",
        "column_dominant_path",
        "compact_phase_order",
        "extended_phase_order",
    }
    assert set(gen.SEMANTIC_WITNESSES) == rival_claiming | positive_branches


def test_schedule_audit_tool_reports_clean_factor_crossed_support():
    script = Path(__file__).resolve().parents[1] / "workspace" / "analyze_schedule.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"
    assert report["period"] == 16
    assert report["violations"] == []
