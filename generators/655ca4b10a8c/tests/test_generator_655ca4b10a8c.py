from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs
gen = importlib.import_module("puzzle_generators.per_puzzle.655ca4b10a8c.generator")


def _move_one_color_cell_far_away(grid, color: int):
    out = copy.deepcopy(grid)
    cells = [(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == color]
    r, c = cells[0]
    out[r][c] = 0
    occupied = {(rr, cc) for rr, row in enumerate(out) for cc, value in enumerate(row) if value != 0}
    for rr in range(1, len(out)):
        for cc in range(len(out[0])):
            if (rr, cc) in occupied:
                continue
            if all(abs(rr - ar) + abs(cc - ac) > 1 for ar, ac in cells[1:]):
                out[rr][cc] = color
                return out
    raise AssertionError("could not construct a disconnected mutation")


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_nine_sample_window_covers_all_key_combinations_and_transfers():
    expected = {(op, transform) for op in gen.OPS for transform in gen.TRANSFORMS}
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(1701, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(1701, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert {
                (pair["input"][0][0], pair["input"][0][-1]) for pair in demos
            } == expected
            assert gen.lesson_identifiable(demos, query) == []


def test_all_declared_overrides_are_observable_and_unknown_names_reject():
    values = {
        "grid_h": (7, 8),
        "grid_w": (11, 12),
        "op": (1, 2, 3),
        "transform": (6, 7, 8),
        "shape_size_a": (4, 5, 6),
        "shape_size_b": (4, 5, 6),
    }
    for name, domain in values.items():
        for value in domain:
            grid = gen.generate(808, 13, difficulty="medium", **{name: value})
            assert gen.observe_overrides(grid)[name] == value
            assert gen.self_check(grid, meta={"overrides": {name: value}}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(808, 13, bogus_axis="typo")


def test_self_check_rejects_targeted_structural_and_rule_hiding_mutations():
    grid = gen.generate(420, 5, difficulty="hard")
    mutations = []

    missing_op = copy.deepcopy(grid)
    missing_op[0][0] = 0
    mutations.append(missing_op)

    missing_transform = copy.deepcopy(grid)
    missing_transform[0][-1] = 0
    mutations.append(missing_transform)

    stray_color = copy.deepcopy(grid)
    stray_color[1][0] = 9
    mutations.append(stray_color)

    mutations.append(_move_one_color_cell_far_away(grid, 4))

    too_small = copy.deepcopy(grid)
    color5_cells = [
        (r, c)
        for r, row in enumerate(too_small)
        for c, value in enumerate(row)
        if value == 5
    ]
    for r, c in color5_cells[3:]:
        too_small[r][c] = 0
    mutations.append(too_small)

    findings = [gen.self_check(mutated) for mutated in mutations]
    assert all(errors for errors in findings)
    assert any("operation key" in " ".join(errors) for errors in findings)
    assert any("transform key" in " ".join(errors) for errors in findings)
    assert any("unexpected colors" in " ".join(errors) for errors in findings)
    assert any("4-connected" in " ".join(errors) for errors in findings)
    assert any("4..6 cells" in " ".join(errors) for errors in findings)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9917)
    before = random.getstate()
    first = gen.generate(55, 23, difficulty="hard")
    after = random.getstate()
    second = gen.generate(55, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))


def test_every_generated_scene_has_nine_distinct_key_answers():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = gen.generate(seed, seed * 7 + 3, difficulty=band)
            info, errors = gen._analyse(grid)
            assert errors == []
            answers = {
                tuple(tuple(row) for row in gen.rule_mirror(
                    grid, forced_op=op, forced_transform=transform
                ))
                for op in gen.OPS
                for transform in gen.TRANSFORMS
            }
            assert len(answers) == 9
