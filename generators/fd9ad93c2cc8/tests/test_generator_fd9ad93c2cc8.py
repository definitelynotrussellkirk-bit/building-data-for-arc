from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.fd9ad93c2cc8 import generator


REPO_ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                value = row[split]
                pairs = value if isinstance(value, list) else [value]
                for pair in pairs:
                    yield pair["input"], pair["output"]
            return
    raise AssertionError("canonical task row not found")


def test_all_canonical_pairs_match_rule_and_strict_profiles():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 3
    signatures = set()
    for grid, expected in pairs:
        before = [row[:] for row in grid]
        assert generator.self_check(grid) == []
        assert generator.rule_mirror(grid) == expected
        assert grid == before
        signatures.add(generator.canonical_profile_signature(grid))
    assert signatures == generator._CANONICAL_PROFILE_SIGNATURES


def test_regression_seed_6_returns_a_canonical_linked_profile():
    grid = generator.generate(6, 6 * 19 + 3, difficulty="easy")
    assert generator.canonical_profile_signature(grid) == (
        7,
        8,
        3,
        (1, 0, 0),
        (),
    )
    assert generator.observe_overrides(grid) == {
        "grid_h": 7,
        "board_w": 8,
        "match_count": 3,
    }
    assert generator.self_check(grid) == []
    assert sum(value == 8 for row in generator.rule_mirror(grid) for value in row) == 3


def test_strict_profile_prior_is_stable_on_disjoint_ranges():
    for start in (0, 50_000):
        for band in ("easy", "medium", "hard"):
            matches = 0
            signatures = set()
            for offset in range(240):
                seed = start + offset
                grid = generator.generate(seed, seed * 29 + 7, difficulty=band)
                assert generator.self_check(grid) == []
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    matches += 1
                    signatures.add(signature)
            assert matches >= 24
            assert signatures == generator._CANONICAL_PROFILE_SIGNATURES


def test_every_exact_override_combination_is_realized_and_observable():
    for band in ("easy", "medium", "hard"):
        for grid_h in range(6, 9):
            for board_w in range(7, 10):
                for match_count in (2, 3):
                    grid = generator.generate(
                        grid_h * 100 + board_w * 10 + match_count,
                        17,
                        difficulty=band,
                        grid_h=grid_h,
                        board_w=board_w,
                        match_count=match_count,
                    )
                    assert generator.self_check(grid) == []
                    assert generator.observe_overrides(grid) == {
                        "grid_h": grid_h,
                        "board_w": board_w,
                        "match_count": match_count,
                    }
                    output = generator.rule_mirror(grid)
                    assert (len(output), len(output[0])) == (grid_h, board_w)
                    assert sum(value == 8 for row in output for value in row) == match_count


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"bogus": 1},
        {"grid_h": 5},
        {"grid_h": 9},
        {"board_w": 6},
        {"board_w": 10},
        {"match_count": 1},
        {"match_count": 4},
        {"texture": "single_match"},
    ],
)
def test_invalid_controls_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, **kwargs)


def test_semantic_branches_and_shortcut_rebuttals_have_support():
    decoy_vectors = Counter()
    singleton_counts = Counter()
    match_counts = Counter()
    distinct_inputs = set()
    distinct_outputs = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(300):
            grid = generator.generate(seed, seed * 31 + 11, difficulty=band)
            scene = generator._inspect_scene(grid)
            decoy_vectors[tuple(len(hits) for hits in scene.decoy_hits)] += 1
            singleton_counts[len(scene.foreign_cells)] += 1
            match_counts[len(scene.target_hits)] += 1
            assert all(value != 8 for row in grid for value in row)
            output = generator.rule_mirror(grid)
            assert sum(value == 8 for row in output for value in row) == len(scene.target_hits)
            distinct_inputs.add(tuple(map(tuple, grid)))
            distinct_outputs.add(tuple(map(tuple, output)))
    assert set(decoy_vectors) == {(1, 0, 0), (0, 1, 0), (0, 0, 1)}
    assert set(singleton_counts) == {0, 1}
    assert set(match_counts) == {2, 3}
    assert len(distinct_inputs) >= 500
    assert len(distinct_outputs) >= 300


def test_self_check_rejects_structure_destroying_mutations():
    valid = generator.generate(6, 117, difficulty="medium")
    mutations = []

    missing_divider = [row[:] for row in valid]
    missing_divider[0][3] = 0
    mutations.append(missing_divider)

    extra_divider = [row[:] for row in valid]
    extra_divider[0][4] = 9
    mutations.append(extra_divider)

    missing_template_cell = [row[:] for row in valid]
    missing_template_cell[0][0] = 0
    mutations.append(missing_template_cell)

    input_mark = [row[:] for row in valid]
    input_mark[-1][-1] = 8
    mutations.append(input_mark)

    extra_red = [row[:] for row in valid]
    for r in range(len(extra_red)):
        for c in range(4, len(extra_red[0])):
            if extra_red[r][c] == 0:
                extra_red[r][c] = 2
                break
        else:
            continue
        break
    mutations.append(extra_red)

    mutations.append([[0] * len(valid[0]) for _ in valid])
    mutations.append([[1] * len(valid[0]) for _ in valid])
    mutations.append([[0, 0], [0]])

    for mutation in mutations:
        assert generator.self_check(mutation), mutation


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(9981)
    state = random.getstate()
    first = generator.generate(19, 31, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
