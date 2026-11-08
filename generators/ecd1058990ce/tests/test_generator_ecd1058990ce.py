from __future__ import annotations

import copy
import hashlib
import json
import random

from puzzle_generators.per_puzzle.ecd1058990ce import generator as gen


def _normalized_rule_hash() -> str:
    with open("data/canonical/puzzles.jsonl", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                normalized = " ".join(row["program_solution"].split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError("canonical task row missing")


def test_rule_hash_matches_normalized_canonical_authority():
    assert gen.RULE_HASH == _normalized_rule_hash() == "6c697debe9bc"


def test_palette_boundaries_are_accepted_and_exact_in_every_band():
    for band in ("easy", "medium", "hard"):
        for palette_size in (2, 9):
            grid = gen.generate(
                314159,
                7,
                difficulty=band,
                palette_size=palette_size,
            )
            assert gen.self_check(
                grid,
                difficulty=band,
                meta={"palette_size": palette_size},
            ) == []
            assert gen.observe_overrides(grid)["palette_size"] == palette_size


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(271828, 3, difficulty="medium", palette_size=5)
    impostors = {
        "wrong_shape": [row[:] for row in valid[:2]],
        "monochrome": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        "singleton_marker": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        "duplicate_adjacent_row": [valid[0][:], valid[0][:], valid[2][:]],
        "duplicate_adjacent_column": [
            [row[0], row[0], row[2]] for row in valid
        ],
        "invalid_color": [row[:] for row in valid],
    }
    impostors["invalid_color"][1][1] = 10
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_each_generated_scene_identifies_the_scale_map():
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(12345, sample_index, difficulty="medium")
        demos.append(
            {
                "input": grid,
                "output": gen._scale_map_python(grid, (2, 1, 2), (2, 1, 2)),
            }
        )
    query_grid = gen.generate(12345, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {
        "input": query_grid,
        "output": gen._scale_map_python(query_grid, (2, 1, 2), (2, 1, 2)),
    }
    assert gen.lesson_identifiable(demos, query) == []


def test_generation_is_replayable_fresh_and_global_rng_pure():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(42, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    mutated = copy.deepcopy(first)
    mutated[0][0] = (mutated[0][0] + 1) % 10
    assert second != mutated


def test_negative_recombination_is_rejected_but_oracle_domain_remains_defined():
    grid = gen.generate(20260724, 11, difficulty="easy", palette_size=5)
    malformed = [grid[0][:], grid[0][:], grid[2][:]]
    assert gen.self_check(malformed)
    # The transform is mathematically executable; rejection is specifically a
    # teaching-distribution decision, not a claim that the oracle would crash.
    output = gen._scale_map_python(malformed, (2, 1, 2), (2, 1, 2))
    assert len(output) == 5 and len(output[0]) == 5
