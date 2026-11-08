from __future__ import annotations

import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs
from reviewer_support import find_root


TASK_ID = "c1fd38e5812b"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.c1fd38e5812b.generator"
)


def canonical_pairs():
    pairs = load_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    normalized = []
    for pair in pairs:
        if isinstance(pair, dict):
            normalized.append((pair["input"], pair["output"]))
        else:
            grid, output = pair
            normalized.append((grid, output))
    return normalized


def canonical_program():
    candidates = (
        ROOT / "data" / "canonical" / "puzzles.jsonl",
        ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    for path in candidates:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") != TASK_ID:
                    continue
                program = (
                    row.get("program_solution")
                    or row.get("selected_program")
                    or row.get("program")
                )
                if isinstance(program, str) and program.strip():
                    return program
    raise AssertionError(f"canonical program not found for {TASK_ID}")


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def reference_solve(grid):
    row_starts = [0] + [
        r for r in range(1, len(grid)) if grid[r][0] != grid[r - 1][0]
    ]
    col_starts = [0] + [
        c
        for c in range(1, len(grid[0]))
        if grid[0][c] != grid[0][c - 1]
    ]
    return [[grid[r][c] for c in col_starts] for r in row_starts]


def test_all_public_pairs_match_independent_reference():
    pairs = canonical_pairs()
    assert len(pairs) >= 5
    for grid, expected in pairs:
        assert reference_solve(grid) == expected
        assert GEN.solve_python(grid) == expected


def test_every_declared_profile_is_strict_observable_and_solved():
    for difficulty in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            for sample_index in range(12):
                grid = GEN.generate(
                    81731,
                    sample_index,
                    difficulty=difficulty,
                    scene_profile=profile,
                )
                assert GEN.self_check(grid, difficulty=difficulty) == []
                assert GEN.observe_overrides(grid) == {
                    "scene_profile": profile
                }
                assert GEN.solve_python(grid) == reference_solve(grid)


def test_weighted_distribution_includes_every_profile_and_keeps_contract():
    for difficulty, weights in GEN._WEIGHTED_PROFILES.items():
        assert len(weights) == 20
        assert sum(profile in GEN.PUBLIC_PROFILES for profile in weights) == 5
        assert weights.count("uniform_runs") == 2
        assert weights.count("uniform_rows") == 2
        assert weights.count("uniform_cols") == 2
        assert weights.count("nonuniform_runs") == 6
        assert weights.count("interior_merges") == 3

        counts = Counter()
        for sample_index in range(2000):
            grid = GEN.generate(48179, sample_index, difficulty=difficulty)
            profile = GEN.observe_overrides(grid)["scene_profile"]
            counts[profile] += 1
        assert set(counts) == set(GEN.SCENE_PROFILES)
        public_share = sum(counts[p] for p in GEN.PUBLIC_PROFILES) / 2000
        assert 0.20 <= public_share <= 0.30
        assert 0.05 <= counts["uniform_runs"] / 2000 <= 0.15
        assert 0.05 <= counts["uniform_rows"] / 2000 <= 0.15
        assert 0.05 <= counts["uniform_cols"] / 2000 <= 0.15


def test_public_profiles_do_not_replay_public_input_literals():
    public_literals = {grid_key(grid) for grid, _ in canonical_pairs()}
    for profile in GEN.PUBLIC_PROFILES:
        for sample_index in range(40):
            grid = GEN.generate(
                60427,
                sample_index,
                difficulty="medium",
                scene_profile=profile,
            )
            assert grid_key(grid) not in public_literals


def test_nonuniform_profiles_cover_run_spans_two_through_twelve():
    seen = set()
    for profile in ("nonuniform_runs", "interior_merges"):
        for sample_index in range(1400):
            grid = GEN.generate(
                99173,
                sample_index,
                difficulty="hard",
                scene_profile=profile,
            )
            analysis = GEN._analyze(grid)
            seen.update(analysis["row_spans"])
            seen.update(analysis["col_spans"])
            assert not analysis["uniform_rows"]
            assert not analysis["uniform_cols"]
            assert analysis["scene_profile"] == profile
    assert seen == set(range(2, 13))


def test_uniform_runs_profile_is_uniform_on_both_axes():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(50):
            grid = GEN.generate(
                17111,
                sample_index,
                difficulty=difficulty,
                scene_profile="uniform_runs",
            )
            analysis = GEN._analyze(grid)
            assert analysis["uniform_rows"]
            assert analysis["uniform_cols"]
            assert analysis["scene_profile"] == "uniform_runs"


@pytest.mark.parametrize(
    "profile, rows_uniform, cols_uniform",
    [
        ("uniform_rows", True, False),
        ("uniform_cols", False, True),
    ],
)
def test_mixed_axis_uniformity_is_generated_independently(
    profile, rows_uniform, cols_uniform
):
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(60):
            grid = GEN.generate(
                21977,
                sample_index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            analysis = GEN._analyze(grid)
            assert analysis["uniform_rows"] is rows_uniform
            assert analysis["uniform_cols"] is cols_uniform
            assert analysis["scene_profile"] == profile
            assert GEN.solve_python(grid) == reference_solve(grid)


def test_independent_axis_counterexample_rejects_coupled_chunking():
    logical = [[0, 1], [2, 2], [3, 3], [0, 1], [2, 2], [3, 3]]
    grid = GEN._expand(logical, [2, 2, 2, 2, 2, 2], [4, 8])
    analysis = GEN._analyze(grid)
    assert analysis["scene_profile"] == "uniform_rows"
    assert GEN.solve_python(grid) == logical
    coupled = [
        [grid[row][col] for col in (0, 4, 8)]
        for row in (0, 2, 4, 6, 8, 10)
    ]
    assert coupled != logical


def test_interior_merge_profile_contains_a_real_merge():
    for sample_index in range(80):
        grid = GEN.generate(
            88721,
            sample_index,
            difficulty="hard",
            scene_profile="interior_merges",
        )
        analysis = GEN._analyze(grid)
        assert analysis["interior_merge"]
        assert analysis["scene_profile"] == "interior_merges"


def test_observable_mutations_break_the_declared_profile():
    grid = GEN.generate(
        31119,
        8,
        difficulty="hard",
        scene_profile="uniform_rows",
    )
    analysis = GEN._analyze(grid)
    row_spans = analysis["row_spans"]
    col_spans = analysis["col_spans"]
    logical = analysis["output"]
    assert len(row_spans) >= 2 and row_spans[0] >= 3

    mutated_row_spans = row_spans[:]
    mutated_row_spans[0] -= 1
    mutated_row_spans[1] += 1
    mutated = GEN._expand(logical, mutated_row_spans, col_spans)
    observed = GEN.observe_overrides(mutated)
    assert observed["scene_profile"] != "uniform_rows"


def test_python_oracle_is_input_pure():
    grid = GEN.generate(
        10103,
        5,
        difficulty="hard",
        scene_profile="uniform_cols",
    )
    before = grid_key(grid)
    first = GEN.solve_python(grid)
    second = GEN.solve_python(grid)
    assert first == second == reference_solve(grid)
    assert grid_key(grid) == before


def test_generation_is_deterministic():
    kwargs = {
        "difficulty": "hard",
        "scene_profile": "uniform_rows",
    }
    assert GEN.generate(9127, 37, **kwargs) == GEN.generate(9127, 37, **kwargs)


def test_invalid_overrides_are_rejected():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, unknown_axis="x")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not-a-profile")


def test_authority_pin_matches_selected_canonical_program():
    normalized = " ".join(canonical_program().split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.RULE_HASH == "0805714fcf25"
