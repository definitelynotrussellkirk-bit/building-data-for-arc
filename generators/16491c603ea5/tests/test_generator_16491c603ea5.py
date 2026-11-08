from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from scripts.generator_module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "16491c603ea5"
    / "generator.py"
)
generator = load_module_from_path("generator_16491c603ea5_test", GENERATOR_PATH)


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                pairs = row.get(split) or []
                if isinstance(pairs, dict):
                    pairs = [pairs]
                for pair in pairs:
                    yield pair["input"], pair["output"]


def expected_output(grid):
    facts = generator.semantic_observables(grid)
    out_h, out_w = facts["expected_output_shape"]
    return [[8] * out_w for _ in range(out_h)]


def test_rule_hash_metadata_and_all_canonical_pairs():
    pairs = list(canonical_pairs())
    assert len(pairs) == 3
    assert generator.RULE_HASH == "4a66dcca2f33"
    assert generator.EXPECTED_OUTPUT_CODOMAIN == 3
    for grid, official_output in pairs:
        before = [row[:] for row in grid]
        assert generator.self_check(grid) == []
        assert expected_output(grid) == official_output
        assert grid == before


def test_regression_exact_overrides_are_observable_at_boundaries():
    # The v2.1.0 baseline accepted these controls but ignored all six probed
    # semantic axes.  This witness requires every repaired axis to be exact.
    calls = [
        dict(grid_h=7, grid_w=8, n_decoys=1, target_edge="top"),
        dict(grid_h=22, grid_w=24, n_decoys=4, target_edge="bottom_right"),
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(calls):
            grid = generator.generate(
                200 + index,
                300 + index,
                difficulty=band,
                **overrides,
            )
            assert generator.self_check(grid) == []
            assert generator.observe_overrides(grid) == overrides

    for edge in generator.TARGET_EDGES:
        grid = generator.generate(
            700,
            701,
            difficulty="medium",
            grid_h=12,
            grid_w=13,
            n_decoys=2,
            target_edge=edge,
        )
        assert generator.observe_overrides(grid)["target_edge"] == edge


def test_three_sample_schedule_covers_all_answer_shapes_per_lesson():
    expected_shapes = [(2, 3), (3, 2), (2, 2)]
    for band in ("easy", "medium", "hard"):
        for lesson in range(20):
            shapes = []
            for phase in range(generator.EXAMPLES_NEEDED):
                sample_index = lesson * generator.EXAMPLES_NEEDED + phase
                grid = generator.generate(
                    10_000 + lesson,
                    sample_index,
                    difficulty=band,
                )
                facts = generator.semantic_observables(grid)
                assert generator.self_check(grid) == []
                shapes.append(facts["expected_output_shape"])
            assert shapes == expected_shapes


def test_self_check_rejects_targeted_structural_impostors():
    control = generator.generate(
        19,
        20,
        difficulty="medium",
        grid_h=12,
        grid_w=13,
        n_decoys=2,
        target_edge="top",
    )
    facts = generator.semantic_observables(control)
    assert generator.self_check(control) == []
    target = facts["target"]
    decoys = [point for point in facts["seeds"] if point != target]

    no_target = [row[:] for row in control]
    no_target[target[0]][target[1]] = 0
    assert generator.self_check(no_target)

    no_decoys = [row[:] for row in control]
    for row, col in decoys:
        no_decoys[row][col] = 0
    assert generator.self_check(no_decoys)

    second_border_target = [row[:] for row in control]
    second_border_target[-1][1] = 2
    assert generator.self_check(second_border_target)

    illegal_palette = [row[:] for row in control]
    blank = next(
        (row, col)
        for row, values in enumerate(illegal_palette)
        for col, value in enumerate(values)
        if value == 0
    )
    illegal_palette[blank[0]][blank[1]] = 3
    assert generator.self_check(illegal_palette)

    overlapping_growth = [row[:] for row in control]
    row, col = decoys[0]
    nearby = (row, col + 1) if col + 1 < len(control[0]) else (row, col - 1)
    overlapping_growth[nearby[0]][nearby[1]] = 2
    assert generator.self_check(overlapping_growth)


def test_impossible_combination_rejects_loudly():
    with pytest.raises(ValueError, match="geometrically incompatible"):
        generator.generate(
            0,
            0,
            difficulty="easy",
            grid_h=7,
            grid_w=8,
            n_decoys=4,
            target_edge="top_left",
        )


def test_determinism_fresh_returns_global_rng_and_exact_provenance():
    state = random.getstate()
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                first = generator.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                )
            finally:
                base.set_ctx_observer(None)
            second = generator.generate(
                seed,
                seed * 17 + 3,
                difficulty=band,
            )
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            observed = generator.observe_overrides(first)
            assert captured[-1].recorded_draws() == observed
            old_value = second[0][0]
            first[0][0] = (first[0][0] + 1) % 10
            replay = generator.generate(
                seed,
                seed * 17 + 3,
                difficulty=band,
            )
            assert replay[0][0] == old_value
    assert random.getstate() == state
