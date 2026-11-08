"""Task-local regressions for the 55993f4c12af half-height OR generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
from typing import Any

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "55993f4c12af"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
RELATIONS = ("00", "10", "01", "11")


def _relation_counts(grid: list[list[int]]) -> dict[str, int]:
    half_h = len(grid) // 2
    width = len(grid[0])
    counts = {relation: 0 for relation in RELATIONS}
    for row in range(half_h):
        for col in range(width):
            relation = f"{int(grid[row][col] != 0)}{int(grid[half_h + row][col] != 0)}"
            counts[relation] += 1
    return counts


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            4 if grid[row][col] != 0 or grid[half_h + row][col] != 0 else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _top_only(grid: list[list[int]]) -> list[list[int]]:
    half_h = len(grid) // 2
    return [[4 if value else 0 for value in row] for row in grid[:half_h]]


def _bottom_only(grid: list[list[int]]) -> list[list[int]]:
    half_h = len(grid) // 2
    return [[4 if value else 0 for value in row] for row in grid[half_h:]]


def _xor(grid: list[list[int]]) -> list[list[int]]:
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            4 if bool(grid[row][col]) != bool(grid[half_h + row][col]) else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _and(grid: list[list[int]]) -> list[list[int]]:
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            4 if grid[row][col] != 0 and grid[half_h + row][col] != 0 else 0
            for col in range(width)
        ]
        for row in range(half_h)
    ]


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": _intended_output(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid, "output": _intended_output(query_grid)}


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_pairs_are_accepted_and_python_mirror_matches(pair):
    grid = deepcopy(pair["input"])
    assert gen.RULE_HASH == "ce2dee847896"
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.rule_mirror(grid) == pair["output"] == _intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_grid_contains_the_complete_boolean_truth_table(band):
    for index in range(80):
        grid = gen.generate(10_000 + index, index * 13 + 7, difficulty=band)
        assert gen.self_check(grid) == []
        counts = _relation_counts(grid)
        assert all(counts[relation] > 0 for relation in RELATIONS), counts
        intended = _intended_output(grid)
        assert gen.rule_mirror(grid) == intended
        assert _top_only(grid) != intended
        assert _bottom_only(grid) != intended
        assert _xor(grid) != intended
        assert _and(grid) != intended


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_and_observable_in_every_band(band):
    requested = {
        "half_h": 6,
        "grid_w": 9,
        "top_color": 8,
        "bot_color": 2,
        "relation_profile": "top_heavy",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert len(grid) == 12 and len(grid[0]) == 9
    assert _relation_counts(grid)["10"] == max(_relation_counts(grid).values())


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("half_h", 2),
        ("half_h", 8),
        ("grid_w", 2),
        ("grid_w", 15),
        ("top_color", 0),
        ("top_color", 4),
        ("bot_color", 0),
        ("bot_color", 4),
        ("relation_profile", "unknown"),
        ("half_h", True),
        ("grid_w", 4.5),
        ("top_color", "3"),
    ],
)
def test_invalid_or_unknown_overrides_raise(key: str, value: Any):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_equal_panel_color_overrides_raise():
    with pytest.raises(ValueError, match="distinct"):
        gen.generate(0, 0, top_color=7, bot_color=7)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_schedule_cycle_contains_a_canonical_shape_and_palette_anchor(band):
    for cycle in range(4):
        grids = [
            gen.generate(300 + cycle, cycle * len(gen.SCHEDULE_PROFILES) + slot, difficulty=band)
            for slot in range(len(gen.SCHEDULE_PROFILES))
        ]
        assert any(
            len(grid) == 12
            and len(grid[0]) == 4
            and {value for row in grid for value in row} == {0, 3, 5}
            for grid in grids
        )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_refutes_all_declared_competitors(band):
    for start in range(20):
        demos, query = _episode(91_000 + start, start, band)
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_semantic_witnesses_have_default_support_in_each_band(band):
    grids = [gen.generate(5_000 + index, index, difficulty=band) for index in range(20)]
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), (band, name)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(55993)
    state = random.getstate()
    first = gen.generate(412, 111, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 0 if first[0][0] else 1
    assert first != second
    assert second != gen.generate(413, 111, difficulty="hard")
    assert second != gen.generate(412, 112, difficulty="hard")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 4 for _ in range(12)],
        [[10] * 4 for _ in range(12)],
        [[0] * 4 for _ in range(11)],
    ],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_each_missing_truth_table_branch():
    grid = gen.generate(77, 8, half_h=6, grid_w=4)
    half_h = len(grid) // 2
    for relation in RELATIONS:
        mutated = deepcopy(grid)
        for row in range(half_h):
            for col in range(len(mutated[0])):
                actual = f"{int(mutated[row][col] != 0)}{int(mutated[half_h + row][col] != 0)}"
                if actual != relation:
                    continue
                if relation == "00":
                    mutated[row][col] = 3
                elif relation == "10":
                    mutated[half_h + row][col] = 5
                elif relation == "01":
                    mutated[row][col] = 3
                else:  # 11
                    mutated[half_h + row][col] = 0
        assert gen.self_check(mutated), relation


def test_anchor_adapts_when_only_bottom_color_is_overridden():
    grid = gen.generate(1, 0, difficulty="easy", bot_color=3)
    observed = gen.observe_overrides(grid)
    assert observed["bot_color"] == 3
    assert observed["top_color"] != 3


@pytest.mark.parametrize("profile", gen.RELATION_PROFILES)
def test_relation_profiles_remain_exactly_observable_on_smallest_grid(profile):
    grid = gen.generate(
        7,
        3,
        difficulty="easy",
        half_h=3,
        grid_w=3,
        relation_profile=profile,
    )
    assert gen.observe_overrides(grid)["relation_profile"] == profile


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_rejects_non_literal_integers(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None, -1])
def test_sample_index_rejects_non_literal_or_negative_integers(bad_index):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(991, bad_index, difficulty="hard")
