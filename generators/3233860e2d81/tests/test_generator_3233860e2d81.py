from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

MODULE = importlib.import_module("puzzle_generators.per_puzzle.3233860e2d81.generator")
from solvers.grounded_rules import GROUNDED_RULES
from src.core.canonical_pairs import load_task_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "3233860e2d81"
AUTHORITY_FILES = (
    ROOT / "data/base/solutions/augmented/f8ff0b80__1784a3a0c58b.json",
    ROOT / "data/base/solutions/training/f8ff0b80__3233860e2d81.json",
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_all_task_local_sources_are_synchronized():
    grounded = GROUNDED_RULES[TASK_ID]
    canonical_rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical_rows.append(row["program_solution"])
    assert len(canonical_rows) == 2
    assert {_normalized_hash(source) for source in canonical_rows} == {MODULE.RULE_HASH}
    assert _normalized_hash(grounded) == MODULE.RULE_HASH == "3087638f0586"
    for path in AUTHORITY_FILES:
        target = json.loads(path.read_text())["racket_target"]
        assert target["raw_code"] == canonical_rows[0]
        assert target["target_code"] == canonical_rows[0]
        assert _normalized_hash(target["raw_code"]) == MODULE.RULE_HASH


def test_all_canonical_inputs_are_accepted_and_have_distinct_counts():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        canonical_meta = {
            "canonical": True,
            "split": pair["split"],
            "row_index": pair["row_index"],
            "pair_index": pair["pair_index"],
        }
        assert MODULE.self_check(
            pair["input"], difficulty=None, meta=canonical_meta
        ) == []
        counts = Counter(value for row in pair["input"] for value in row if value)
        assert len(counts) == 3
        assert len(set(counts.values())) == 3
        assert MODULE.expected_output(pair["input"]) == pair["output"]


def test_generated_lessons_make_top_three_a_real_selection():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = MODULE.generate(seed, seed * 13 + 5, difficulty=difficulty)
            assert MODULE.self_check(grid) == []
            facts = MODULE.observe_overrides(grid)
            assert 4 <= facts["n_colors"] <= 7
            counts = Counter(value for row in grid for value in row if value)
            assert len(set(counts.values())) == len(counts)
            assert len(MODULE.expected_output(grid)) == 3
            assert facts["count_distribution"] in MODULE.COUNT_DISTRIBUTIONS


def test_exact_override_boundaries_and_observer():
    cases = (
        {"grid_h": 5},
        {"grid_w": 5},
        {"grid_h": 18, "grid_w": 18},
        {"n_colors": 7},
        {"min_count": 4},
        {"min_count_gap": 3},
        {"count_distribution": "wide_spread"},
        {
            "grid_h": 18,
            "grid_w": 18,
            "n_colors": 7,
            "min_count": 4,
            "min_count_gap": 3,
            "count_distribution": "wide_spread",
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = MODULE.generate(900 + index, index, difficulty=difficulty, **case)
            observed = MODULE.observe_overrides(grid)
            for axis, requested in case.items():
                assert observed[axis] == requested
            assert MODULE.self_check(grid, difficulty=difficulty, meta={"overrides": case}) == []


def test_determinism_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = MODULE.generate(101, 7, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(101, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    replay = MODULE.generate(101, 7, difficulty="medium")
    assert replay == second


def test_self_check_rejects_targeted_impostors():
    valid = MODULE.generate(202, 11, difficulty="medium")
    assert MODULE.self_check(valid) == []

    all_background = [[0 for _ in row] for row in valid]
    one_color_full = [[1 for _ in row] for row in valid]
    equal_counts = [[0] * 8 for _ in range(8)]
    for color, start in ((1, 0), (2, 8), (3, 16)):
        for offset in range(4):
            pos = start + offset
            equal_counts[pos // 8][pos % 8] = color
    too_fragmented = [[0] * 10 for _ in range(10)]
    for color, coords in {
        1: [(0, 0), (0, 2)],
        2: [(2, 0), (2, 2), (2, 4)],
        3: [(4, 0), (4, 2), (4, 4), (4, 6)],
        4: [(6, 0), (6, 2), (6, 4), (6, 6), (6, 8)],
    }.items():
        for row, col in coords:
            too_fragmented[row][col] = color

    for impostor in (all_background, one_color_full, equal_counts, too_fragmented):
        assert MODULE.self_check(impostor), impostor


def test_negative_recombination_is_rejected_without_mutating_source():
    grid = MODULE.generate(303, 17, difficulty="hard")
    original = copy.deepcopy(grid)
    counts = Counter(value for row in grid for value in row if value)
    source_color = min(counts, key=counts.get)
    unused_color = next(color for color in range(1, 10) if color not in counts)
    mutated = copy.deepcopy(grid)
    changed = 0
    for row in range(len(mutated)):
        for col in range(len(mutated[0])):
            if mutated[row][col] == source_color and changed == 0:
                mutated[row][col] = unused_color
                changed += 1
    assert grid == original
    assert unused_color not in counts
    assert MODULE.self_check(mutated)


def test_distribution_varies_inputs_and_ranked_outputs():
    grids = [MODULE.generate(seed, 3, difficulty="medium") for seed in range(80)]
    outputs = [MODULE.expected_output(grid) for grid in grids]
    assert len({_grid_key(grid) for grid in grids}) >= 76
    assert len({_grid_key(output) for output in outputs}) >= 45
