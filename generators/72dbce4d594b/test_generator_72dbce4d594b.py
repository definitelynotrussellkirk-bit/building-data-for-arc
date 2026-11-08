"""Focused regressions for the reviewed 72dbce4d594b generator."""
from __future__ import annotations

import copy
import importlib
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.72dbce4d594b.generator")


def _copy(grid):
    return [row[:] for row in grid]


def _first_blank(grid):
    return next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    )


def test_rule_hash_and_all_canonical_pairs_match_authority():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [11, 16])
@pytest.mark.parametrize("grid_w", [12, 19])
@pytest.mark.parametrize("rank", [1, 3])
@pytest.mark.parametrize("transform", [1, 4])
def test_numeric_axis_boundaries_are_exactly_observable(
    difficulty, grid_h, grid_w, rank, transform
):
    grid = gen.generate(
        7001,
        17,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
        rank=rank,
        transform=transform,
        size_profile="canonical_234",
        red_layout="top",
        green_layout="right",
        target_zone="center",
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "rank": rank,
        "transform": transform,
        "size_profile": "canonical_234",
        "red_layout": "top",
        "green_layout": "right",
        "target_zone": "center",
    }


@pytest.mark.parametrize("size_profile", list(gen._SIZE_PROFILES))
@pytest.mark.parametrize("red_layout", gen._RED_LAYOUTS)
@pytest.mark.parametrize("green_layout", gen._GREEN_LAYOUTS)
@pytest.mark.parametrize("target_zone", gen._TARGET_ZONES)
def test_categorical_axes_are_exactly_observable(
    size_profile, red_layout, green_layout, target_zone
):
    grid = gen.generate(
        8123,
        9,
        difficulty="medium",
        grid_h=16,
        grid_w=19,
        rank=2,
        transform=2,
        size_profile=size_profile,
        red_layout=red_layout,
        green_layout=green_layout,
        target_zone=target_zone,
    )
    observed = gen.observe_overrides(grid)
    assert observed["size_profile"] == size_profile
    assert observed["red_layout"] == red_layout
    assert observed["green_layout"] == green_layout
    assert observed["target_zone"] == target_zone


def test_unknown_invalid_axes_and_difficulty_reject_loudly():
    invalid_calls = (
        {"typo_axis": 1},
        {"grid_h": 10},
        {"grid_w": 20},
        {"rank": 0},
        {"transform": 5},
        {"size_profile": "unknown"},
        {"red_layout": "right"},
        {"green_layout": "left"},
        {"target_zone": "edge"},
    )
    for kwargs in invalid_calls:
        with pytest.raises(ValueError):
            gen.generate(0, 0, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")


def test_determinism_fresh_returns_reentrancy_and_global_rng_purity():
    random.seed(20260727)
    state = random.getstate()
    first = gen.generate(19, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(19, 4, difficulty="hard")
    other = gen.generate(20, 4, difficulty="hard")
    third = gen.generate(19, 4, difficulty="hard")
    assert first == second == third
    assert first != other
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert second == gen.generate(19, 4, difficulty="hard")


def test_targeted_structural_impostors_are_rejected():
    base = gen.generate(
        91,
        7,
        difficulty="medium",
        grid_h=16,
        grid_w=19,
        rank=3,
        transform=2,
        size_profile="wide_358",
        red_layout="top",
        green_layout="right",
        target_zone="top_left",
    )
    analysis = gen._analyze(base)[1]
    assert analysis is not None

    no_blue = _copy(base)
    for row in no_blue:
        for c, value in enumerate(row):
            if value == 1:
                row[c] = 0
    assert gen.self_check(no_blue)

    tied_sizes = _copy(base)
    middle = sorted(analysis["blue"], key=len)[1]
    remaining = set(middle)
    keep = {next(iter(remaining))}
    while len(keep) < 3:
        keep.add(next(
            p for p in remaining - keep
            if any(abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1 for q in keep)
        ))
    for r, c in middle:
        if (r, c) not in keep:
            tied_sizes[r][c] = 0
    assert any("distinct" in finding for finding in gen.self_check(tied_sizes))

    no_red = _copy(base)
    for row in no_red:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    assert any("red marker" in finding for finding in gen.self_check(no_red))

    five_green = _copy(base)
    green_count = sum(value == 3 for row in five_green for value in row)
    while green_count < 5:
        r, c = _first_blank(five_green)
        five_green[r][c] = 3
        green_count += 1
    assert any("1..4" in finding for finding in gen.self_check(five_green))

    no_cyan = _copy(base)
    for row in no_cyan:
        for c, value in enumerate(row):
            if value == 8:
                row[c] = 0
    assert any("cyan" in finding for finding in gen.self_check(no_cyan))

    two_cyan = _copy(base)
    r, c = _first_blank(two_cyan)
    two_cyan[r][c] = 8
    assert any("cyan" in finding for finding in gen.self_check(two_cyan))

    invalid_color = _copy(base)
    r, c = _first_blank(invalid_color)
    invalid_color[r][c] = 9
    assert any("unexpected input colors" in finding for finding in gen.self_check(invalid_color))

    out_of_bounds = _copy(base)
    for row in out_of_bounds:
        for c, value in enumerate(row):
            if value == 8:
                row[c] = 0
    out_of_bounds[-1][-1] = 8
    assert gen.self_check(out_of_bounds)


def test_each_named_rival_is_refuted_by_a_generated_witness():
    witnessed = {name: False for name in gen.SEMANTIC_RIVALS}
    for seed in range(120):
        grid = gen.generate(seed, seed % 17, difficulty=("easy", "medium", "hard")[seed % 3])
        answer = gen.rule_mirror(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            witnessed[name] |= rival(grid) != answer
    assert all(witnessed.values()), witnessed


def test_every_four_demo_window_identifies_the_lesson():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(5003, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(5003, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
