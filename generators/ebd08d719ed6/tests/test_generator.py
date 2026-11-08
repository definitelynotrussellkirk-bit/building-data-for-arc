from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root
def _load_generator():
    source = Path(
        os.environ.get(
            "GENERATOR_UNDER_TEST",
            Path(__file__).resolve().parents[1] / "generator.py",
        )
    )
    spec = importlib.util.spec_from_file_location("ebd08d719ed6_generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()

TASK_ID = "ebd08d719ed6"
EXPECTED_RULE_HASH = "f5f6e2df9282"


def _tile_with_count(count: int, color: int = 2) -> list[list[int]]:
    tile = [[0, 0, 0] for _ in range(3)]
    for index in range(count):
        tile[index // 3][index % 3] = color
    return tile


def _assemble(tile_rows: list[list[list[list[int]]]]) -> list[list[int]]:
    rows = len(tile_rows)
    cols = len(tile_rows[0])
    height = rows * 3 + rows - 1
    width = cols * 3 + cols - 1
    grid = [[9 for _ in range(width)] for _ in range(height)]
    for tile_row, row in enumerate(tile_rows):
        for tile_col, tile in enumerate(row):
            for r in range(3):
                for c in range(3):
                    grid[tile_row * 4 + r][tile_col * 4 + c] = tile[r][c]
    return grid


def test_rule_pin_and_canonical_pairs_are_supported() -> None:
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_three_example_schedule_teaches_beyond_fixed_five() -> None:
    expected_profiles = (
        "canonical_2345",
        "max4_no5",
        "max7_with5_distractor",
    )
    for difficulty in (None, "easy", "medium", "hard"):
        grids = [gen.generate(1701, index, difficulty=difficulty) for index in range(3)]
        assert [gen.observe_overrides(grid)["count_profile"] for grid in grids] == list(
            expected_profiles
        )
        assert gen.strict_canonical_like(grids[0]) == []
        assert all(gen.self_check(grid) == [] for grid in grids)
        truth = [gen.rule_mirror(grid) for grid in grids]
        rival = [gen.SEMANTIC_RIVALS["fixed_five"](grid) for grid in grids]
        assert rival[0] == truth[0]
        assert rival[1] != truth[1]
        assert rival[2] != truth[2]


def test_every_declared_override_is_exact_in_every_band() -> None:
    cases = (
        {
            "tile_rows": 2,
            "tile_cols": 2,
            "count_profile": "canonical_2345",
            "palette_profile": "canonical_single",
        },
        {
            "tile_rows": 4,
            "tile_cols": 4,
            "count_profile": "max4_no5",
            "palette_profile": "mixed_shared",
        },
        {
            "tile_rows": 3,
            "tile_cols": 4,
            "count_profile": "max7_with5_distractor",
            "palette_profile": "mixed_shared",
        },
    )
    for difficulty in (None, "easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(2300 + index, index, difficulty=difficulty, **requested)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    ("axis", "value"),
    (
        ("typo_axis", 1),
        ("tile_rows", 1),
        ("tile_rows", 5),
        ("tile_cols", 1),
        ("tile_cols", 5),
        ("tile_rows", True),
        ("tile_cols", 2.5),
        ("count_profile", "unknown"),
        ("palette_profile", "unknown"),
    ),
)
def test_invalid_overrides_fail_loudly(axis: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{axis: value})


def test_self_check_rejects_single_tile_ties_and_unknown_profiles() -> None:
    single = _assemble([[_tile_with_count(5)]])
    tied = _assemble(
        [
            [_tile_with_count(4), _tile_with_count(4)],
            [_tile_with_count(2), _tile_with_count(3)],
        ]
    )
    unsupported_counts = _assemble(
        [
            [_tile_with_count(1), _tile_with_count(2)],
            [_tile_with_count(3), _tile_with_count(6)],
        ]
    )
    unsupported_palette = _assemble(
        [
            [_tile_with_count(2, 4), _tile_with_count(3, 4)],
            [_tile_with_count(4, 4), _tile_with_count(5, 4)],
        ]
    )
    assert gen.self_check(single)
    assert gen.self_check(tied)
    assert gen.self_check(unsupported_counts)
    assert gen.self_check(unsupported_palette)


@pytest.mark.parametrize("profile", ("max4_no5", "max7_with5_distractor"))
def test_semantic_witness_is_an_exact_fixed_five_counterexample(profile: str) -> None:
    grid = gen.generate(
        991,
        7,
        tile_rows=2,
        tile_cols=2,
        count_profile=profile,
        palette_profile="canonical_single",
    )
    assert gen.SEMANTIC_WITNESSES["fixed_five_counterexample"](grid)
    assert gen.SEMANTIC_RIVALS["fixed_five"](grid) != gen.rule_mirror(grid)


def test_generation_is_deterministic_and_does_not_mutate_global_rng() -> None:
    state = random.getstate()
    first = gen.generate(812, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(812, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99


def test_fixed_five_is_a_real_canonical_shortcut() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert gen.SEMANTIC_RIVALS["fixed_five"](pair["input"]) == pair["output"]


def test_every_cyclic_lesson_start_and_query_rotation_refutes_fixed_five() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(3):
            grids = [
                gen.generate(6100 + start, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            truths = [gen.rule_mirror(grid) for grid in grids]
            rivals = [gen.SEMANTIC_RIVALS["fixed_five"](grid) for grid in grids]
            for query_index in range(4):
                demonstrations = [index for index in range(4) if index != query_index]
                assert any(rivals[index] != truths[index] for index in demonstrations)
