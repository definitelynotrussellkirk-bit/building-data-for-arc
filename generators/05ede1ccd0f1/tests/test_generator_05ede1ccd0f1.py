from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.05ede1ccd0f1.generator")


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append((color, cells))
    return result


def test_rule_hash_and_python_mirror_are_bound_to_every_canonical_pair():
    assert gen.RULE_HASH == "55bc14a48684"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("texture", ["plain", "clip", "right_content", "eight_decoy"])
@pytest.mark.parametrize("h,w,n", [(4, 6, 8), (12, 16, 2), (5, 11, 5)])
def test_every_declared_override_round_trips_at_boundaries(band, texture, h, w, n):
    options = {"grid_h": h, "grid_w": w, "n_cells": n, "texture": texture}
    grid = gen.generate(117, h * 1000 + w * 10 + n, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 3}, {"grid_h": 13}, {"grid_w": 5}, {"grid_w": 17},
        {"n_cells": 1}, {"n_cells": 9},
        {"texture": "source_on_right"}, {"texture": "unknown"},
        {"grid_h": True}, {"grid_w": 7.0}, {"n_cells": "3"},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_scalars_fail_loudly(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


def test_lawful_texture_witnesses_are_real_and_mutually_observable():
    grids = {
        texture: gen.generate(900, index, grid_h=8, grid_w=11, n_cells=6, texture=texture)
        for index, texture in enumerate(gen.HELPFUL_TEXTURES)
    }
    facts = {name: gen._analyze(grid) for name, grid in grids.items()}

    assert facts["plain"]["texture"] == "plain"
    assert facts["plain"]["oob_source_count"] == 0
    assert facts["plain"]["right_cell_count"] == 0
    assert facts["plain"]["off_axis_eight_count"] == 0

    assert facts["clip"]["texture"] == "clip"
    assert facts["clip"]["oob_source_count"] >= 1
    assert facts["clip"]["in_bounds_source_count"] >= 1

    assert facts["right_content"]["texture"] == "right_content"
    assert facts["right_content"]["right_cell_count"] >= 1
    right_input = grids["right_content"]
    right_output = gen.rule_mirror(right_input)
    assert any(
        c > facts["right_content"]["axis"] and right_input[r][c] != right_output[r][c]
        for r, row in enumerate(right_input)
        for c, _ in enumerate(row)
    )

    assert facts["eight_decoy"]["texture"] == "eight_decoy"
    assert facts["eight_decoy"]["off_axis_eight_count"] >= 1
    decoy_input = grids["eight_decoy"]
    decoy_output = gen.rule_mirror(decoy_input)
    assert all(
        decoy_output[r][c] == 8
        for r, c in facts["eight_decoy"]["off_axis_eights"]
    )


def test_canonical_profile_slots_overlap_the_real_task_structure_in_every_band():
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 2, 4, 6):
            grid = gen.generate(500 + sample_index, sample_index, difficulty=band)
            facts = gen._analyze(grid)
            assert facts["texture"] == "plain"
            assert (len(grid), len(grid[0])) in {(5, 7), (4, 9), (5, 11)}
            assert len(facts["source_colors"]) == 1
            assert len(_components(grid)) == 2  # one source object plus the full cyan axis
            assert all(len(cells) > 1 for _, cells in _components(grid))


def test_every_rotated_three_demo_window_refutes_grid_center_shortcut():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 8
    assert set(gen.WITNESS_RIVALS) == {
        "off_center_axis",
        "multiple_source_colors",
        "multiple_source_components",
        "source_precedes_wall_in_scan",
    }
    rival = gen.CANONICAL_SHORTCUTS["mirror_about_grid_center"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _pairs())

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [
                gen.generate(7000 + band_index, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs = [_pair(grid) for grid in grids]
            for query_index in range(len(pairs)):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                    witness = gen.SEMANTIC_WITNESSES[witness_name]
                    assert any(witness(p["input"]) for p in demos), (
                        band, start, query_index, witness_name
                    )
                    assert any(
                        gen.SEMANTIC_RIVALS[rival_name](p["input"]) != p["output"]
                        for p in demos
                        for rival_name in rival_names
                    ), (band, start, query_index, witness_name)
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_canonical_only_demos_leave_the_center_axis_shortcut_ambiguous():
    canonical = _pairs()
    witness = gen.generate(991, 1, grid_h=8, grid_w=12, n_cells=5, texture="plain")
    assert gen.SEMANTIC_WITNESSES["off_center_axis"](witness)
    reasons = gen.lesson_identifiable(canonical, _pair(witness))
    assert any("mirror_about_grid_center" in reason for reason in reasons)


def test_self_check_rejects_malformed_and_identity_inputs():
    for grid in (None, [], [[]], [[0], [0, 0]], [[True] * 6 for _ in range(4)]):
        assert gen.self_check(grid)

    base = gen.generate(71, 3, grid_h=6, grid_w=9, n_cells=4, texture="plain")
    facts = gen._analyze(base)
    axis = facts["axis"]

    no_axis = copy.deepcopy(base)
    for row in no_axis:
        row[axis] = 0
    assert gen.self_check(no_axis)

    second_axis = copy.deepcopy(base)
    other = 0 if axis != 0 else 1
    for row in second_axis:
        row[other] = 8
    assert gen.self_check(second_axis)

    no_left_source = copy.deepcopy(base)
    for r, c in facts["left_sources"]:
        no_left_source[r][c] = 0
    assert gen.self_check(no_left_source)


def test_degenerate_source_on_right_is_retained_as_a_negative_fixture():
    grid = gen.generate_degenerate(19, 4, "source_on_right")
    assert gen.self_check(grid)
    assert gen.rule_mirror(grid) == grid


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(331, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(331, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(331, 17, difficulty="hard") == second
