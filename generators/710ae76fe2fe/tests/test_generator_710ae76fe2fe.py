"""Focused semantic regressions for Ferrers-cap generator 710ae76fe2fe."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "710ae76fe2fe"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _headers(grid):
    return (
        [grid[row][0] for row in range(1, len(grid))],
        [grid[0][column] for column in range(1, len(grid[0]))],
    )


def test_rule_hash_and_every_canonical_pair_are_pinned():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    # Pin the canonical program text itself.  The runner wraps this expression
    # as a callable, so hashing runner.rule_callable_text would hash a different
    # representation even when the selected rule is synchronized.
    canonical_path = Path(__file__).parents[1] / "data" / "canonical" / "puzzles.jsonl"
    canonical_rule = None
    for line in canonical_path.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            canonical_rule = record["program_solution"]
            break
    assert canonical_rule is not None
    assert _normalized_hash(canonical_rule) == GEN.RULE_HASH
    assert GEN.RULE_HASH == "68e3bc631fba"

    profiles = []
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before
        profiles.append(GEN.observe_overrides(source)["scene_profile"])
    assert profiles.count("consistent") == 3
    assert profiles.count("row_loose") == 1


def test_regression_old_random_headers_are_now_monotone_positive_caps():
    # Baseline v2.1.1 at this exact tuple emitted row headers [2,1,0,0,1]
    # and column headers [0,4,5], violating positivity and monotonicity while
    # self_check still accepted it.  The repaired source produces a lawful cap
    # profile for the same replay tuple.
    grid = GEN.generate(20_000, 20_000, difficulty="easy")
    rows, columns = _headers(grid)
    assert min(rows) >= 1 and min(columns) >= 1
    assert rows == sorted(rows, reverse=True)
    assert columns == sorted(columns, reverse=True)
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) != GEN._full_inner_canvas(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260726)
    state = random.getstate()
    first = GEN.generate(917, 311, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(917, 311, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second == GEN.generate(917, 311, difficulty="hard")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_axis_boundaries_and_all_profiles_are_observable(difficulty):
    for grid_h, grid_w in ((4, 4), (10, 10)):
        for profile in GEN.SCENE_PROFILES:
            requested = {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "scene_profile": profile,
            }
            grid = GEN.generate(71, 19, difficulty=difficulty, **requested)
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(grid) == []
            assert GEN.rule_mirror(grid) == GEN._intersection_from_headers(*_headers(grid))
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(71, 19, header_mode="random")


def test_six_step_schedule_covers_every_cap_relationship():
    observed = []
    for sample_index in range(6):
        grid = GEN.generate(43, sample_index, difficulty="medium")
        observed.append(GEN.observe_overrides(grid)["scene_profile"])
    assert observed == list(GEN._PROFILE_SCHEDULE)
    assert set(observed) == set(GEN.SCENE_PROFILES)


def test_ordinary_distribution_is_ferrers_and_shortcut_rebutting():
    profile_counts = {profile: 0 for profile in GEN.SCENE_PROFILES}
    strict = 0
    for difficulty in ("easy", "medium", "hard"):
        for index in range(60):
            grid = GEN.generate(30_000 + index, 40_000 + index, difficulty=difficulty)
            analysis = GEN._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["row_lengths"] == sorted(analysis["row_lengths"], reverse=True)
            assert analysis["col_heights"] == sorted(analysis["col_heights"], reverse=True)
            assert analysis["output_row_lengths"] == sorted(
                analysis["output_row_lengths"], reverse=True
            )
            assert len(set(analysis["output_row_lengths"])) >= 3
            assert len(set(analysis["output_col_heights"])) >= 3
            profile_counts[analysis["scene_profile"]] += 1
            strict += int(not GEN.strict_canonical_like(grid))
            if analysis["scene_profile"] == "crossing":
                expected = GEN.rule_mirror(grid)
                for rival in (
                    GEN._row_headers_only,
                    GEN._column_headers_only,
                    GEN._union_of_headers,
                ):
                    assert rival(grid) != expected
    assert all(count > 0 for count in profile_counts.values())
    assert strict >= 30


def test_each_one_sided_profile_has_the_declared_binding_header():
    consistent = GEN.generate(5, 7, grid_h=6, grid_w=7, scene_profile="consistent")
    row_loose = GEN.generate(5, 7, grid_h=6, grid_w=7, scene_profile="row_loose")
    column_loose = GEN.generate(5, 7, grid_h=6, grid_w=7, scene_profile="column_loose")
    crossing = GEN.generate(5, 7, grid_h=6, grid_w=7, scene_profile="crossing")

    assert GEN.rule_mirror(consistent) == GEN._row_headers_only(consistent)
    assert GEN.rule_mirror(consistent) == GEN._column_headers_only(consistent)

    assert GEN.rule_mirror(row_loose) == GEN._column_headers_only(row_loose)
    assert GEN.rule_mirror(row_loose) != GEN._row_headers_only(row_loose)

    assert GEN.rule_mirror(column_loose) == GEN._row_headers_only(column_loose)
    assert GEN.rule_mirror(column_loose) != GEN._column_headers_only(column_loose)

    assert GEN.rule_mirror(crossing) != GEN._row_headers_only(crossing)
    assert GEN.rule_mirror(crossing) != GEN._column_headers_only(crossing)


def test_every_three_demo_window_refutes_named_query_shortcuts():
    for start in range(6):
        pairs = []
        for offset in range(4):
            sample_index = start + offset
            grid = GEN.generate(991, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_declared_mutations_and_negative_recombination_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(copy.deepcopy(grid)), name

    row_source = GEN.generate(
        0, 0, grid_h=4, grid_w=4, scene_profile="row_loose"
    )
    column_source = GEN.generate(
        0, 0, grid_h=4, grid_w=4, scene_profile="column_loose"
    )
    recombined = copy.deepcopy(row_source)
    recombined[0][1:] = column_source[0][1:]
    errors = GEN.self_check(recombined)
    assert "the output must expose at least three distinct row lengths" in errors
    assert "the output must expose at least three distinct column heights" in errors
