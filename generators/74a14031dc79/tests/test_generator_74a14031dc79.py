"""Task-local regressions for the 74a14031dc79 side-by-side OR generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import random
from typing import Any

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "74a14031dc79"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
RELATIONS = ("00", "10", "01", "11")
RELATION_PROFILES = (
    "balanced",
    "left_heavy",
    "right_heavy",
    "overlap_heavy",
    "empty_heavy",
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _relation_counts(grid: list[list[int]]) -> dict[str, int]:
    counts = {relation: 0 for relation in RELATIONS}
    for row in range(len(grid)):
        for col in range(3):
            relation = f"{int(grid[row][col] != 0)}{int(grid[row][col + 4] != 0)}"
            counts[relation] += 1
    return counts


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    return [
        [2 if row[col] != 0 or row[col + 4] != 0 else 0 for col in range(3)]
        for row in grid
    ]


def _left_only(grid: list[list[int]]) -> list[list[int]]:
    return [[2 if row[col] else 0 for col in range(3)] for row in grid]


def _right_only(grid: list[list[int]]) -> list[list[int]]:
    return [[2 if row[col + 4] else 0 for col in range(3)] for row in grid]


def _xor(grid: list[list[int]]) -> list[list[int]]:
    return [
        [2 if bool(row[col]) != bool(row[col + 4]) else 0 for col in range(3)]
        for row in grid
    ]


def _and(grid: list[list[int]]) -> list[list[int]]:
    return [
        [2 if row[col] != 0 and row[col + 4] != 0 else 0 for col in range(3)]
        for row in grid
    ]


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": _intended_output(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid, "output": _intended_output(query_grid)}


def test_contract_constants_pin_the_authority_and_teaching_floor():
    assert gen.RULE_HASH == "582367af483f"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.RELATION_PROFILES == RELATION_PROFILES


def test_pinned_profile_floor_census_keeps_at_least_quarter_canonical_scale():
    hits = 0
    per_band = {band: 0 for band in ("easy", "medium", "hard")}
    for band in per_band:
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            if profile == (3, 7, 4):
                hits += 1
                per_band[band] += 1
    assert all(per_band.values()), per_band
    assert hits >= 15, (hits, per_band)


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_pairs_are_accepted_and_python_mirror_matches(pair):
    grid = deepcopy(pair["input"])
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.rule_mirror(grid) == pair["output"] == _intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_grid_contains_the_complete_boolean_truth_table(band):
    for index in range(48):
        grid = gen.generate(10_000 + index, index * 13 + 7, difficulty=band)
        assert gen.self_check(grid) == []
        counts = _relation_counts(grid)
        assert all(counts[relation] > 0 for relation in RELATIONS), counts
        intended = _intended_output(grid)
        assert gen.rule_mirror(grid) == intended
        assert _left_only(grid) != intended
        assert _right_only(grid) != intended
        assert _xor(grid) != intended
        assert _and(grid) != intended


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_and_observable_in_every_band(band):
    requested = {
        "grid_h": 9,
        "left_color": 8,
        "right_color": 3,
        "sep_color": 5,
        "relation_profile": "left_heavy",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert len(grid) == 9 and len(grid[0]) == 7
    assert _relation_counts(grid)["10"] == max(_relation_counts(grid).values())


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 2),
        ("grid_h", 13),
        ("left_color", 0),
        ("left_color", 2),
        ("right_color", 0),
        ("right_color", 2),
        ("sep_color", 0),
        ("sep_color", 2),
        ("relation_profile", "unknown"),
        ("grid_h", True),
        ("grid_h", 4.5),
        ("left_color", "3"),
    ],
)
def test_invalid_or_unknown_overrides_raise(key: str, value: Any):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "overrides",
    [
        {"left_color": 7, "right_color": 7},
        {"left_color": 7, "sep_color": 7},
        {"right_color": 7, "sep_color": 7},
    ],
)
def test_equal_role_color_overrides_raise(overrides):
    with pytest.raises(ValueError, match="distinct"):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_schedule_cycle_contains_a_canonical_shape_and_palette_anchor(band):
    for cycle in range(4):
        grids = [
            gen.generate(
                300 + cycle,
                cycle * len(gen.SCHEDULE_PROFILES) + slot,
                difficulty=band,
            )
            for slot in range(len(gen.SCHEDULE_PROFILES))
        ]
        assert any(
            len(grid) == 3
            and len(grid[0]) == 7
            and {value for row in grid for value in row} == {0, 4, 6, 8}
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
    random.seed(74_140_31)
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
        [[True] * 7 for _ in range(3)],
        [[10] * 7 for _ in range(3)],
        [[0] * 6 for _ in range(3)],
        [[0] * 7 for _ in range(2)],
    ],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_lawful_sparse_inputs_remain_valid_but_are_not_teaching_profiles():
    grid = gen.generate(77, 8, grid_h=6)
    left_color = next(value for row in grid for value in row[:3] if value != 0)
    right_color = next(value for row in grid for value in row[4:] if value != 0)
    for relation in RELATIONS:
        mutated = deepcopy(grid)
        for row in range(len(mutated)):
            for col in range(3):
                actual = f"{int(mutated[row][col] != 0)}{int(mutated[row][col + 4] != 0)}"
                if actual != relation:
                    continue
                if relation == "00":
                    mutated[row][col] = left_color
                elif relation == "10":
                    mutated[row][col + 4] = right_color
                elif relation == "01":
                    mutated[row][col] = left_color
                else:  # 11
                    mutated[row][col + 4] = 0
        assert gen.self_check(mutated) == [], relation
        assert gen.strict_canonical_like(mutated) == [], relation
        assert gen.rule_mirror(mutated) == _intended_output(mutated)
        with pytest.raises(ValueError, match="truth table is incomplete"):
            gen.observe_overrides(mutated)


def test_anchor_adapts_when_only_right_color_is_overridden():
    grid = gen.generate(1, 0, difficulty="easy", right_color=6)
    observed = gen.observe_overrides(grid)
    assert observed["right_color"] == 6
    assert observed["left_color"] != 6
    assert observed["sep_color"] != 6


@pytest.mark.parametrize("profile", RELATION_PROFILES)
def test_relation_profiles_remain_exactly_observable_on_smallest_grid(profile):
    grid = gen.generate(
        7,
        3,
        difficulty="easy",
        grid_h=3,
        relation_profile=profile,
    )
    assert gen.observe_overrides(grid)["relation_profile"] == profile
