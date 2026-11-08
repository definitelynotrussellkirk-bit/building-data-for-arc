from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "2ff23bbd7de8"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _pairs(row: dict) -> list[dict]:
    test = row.get("test", [])
    tests = test if isinstance(test, list) else [test]
    return list(row.get("train", [])) + [pair for pair in tests if pair]


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_pairs():
    pairs = _pairs(_canonical_row())
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_regression_radius_four_and_axis_cells_are_distractors():
    axis_grid = gen.generate(20260725, 1, difficulty="medium")
    axis_info, axis_errors = gen._analyse(axis_grid)
    assert axis_errors == []
    assert axis_info["axis_count"] > 0
    assert gen.rule_mirror(axis_grid) != gen._rival_include_axes(axis_grid)

    far_grid = gen.generate(20260725, 2, difficulty="medium")
    far_info, far_errors = gen._analyse(far_grid)
    assert far_errors == []
    assert far_info["far_count"] > 0
    assert gen.rule_mirror(far_grid) != gen._rival_ignore_radius(far_grid)


def test_four_consecutive_demos_identify_the_rule_and_refute_every_competitor():
    for start in range(8):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(314159, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(314159, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


def test_grid_size_override_boundaries_are_exact_and_unknown_keys_reject():
    for difficulty in ("easy", "medium", "hard"):
        for grid_n in (11, 17):
            grid = gen.generate(42, 7, difficulty=difficulty, grid_n=grid_n)
            assert gen.observe_overrides(grid) == {"grid_n": grid_n}
            assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_grid_n=11)


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(99, 3, difficulty="medium", grid_n=11)
    assert gen.self_check(base) == []

    duplicate_origin = copy.deepcopy(base)
    duplicate_origin[0][0] = 2
    assert any("exactly one" in error for error in gen.self_check(duplicate_origin))

    missing_u_arm = copy.deepcopy(base)
    info, _ = gen._analyse(missing_u_arm)
    r3 = info["origin"][0] + info["vx"][0]
    c3 = info["origin"][1] + info["vx"][1]
    missing_u_arm[r3][c3] = 0
    assert any("exactly one" in error for error in gen.self_check(missing_u_arm))

    non_perpendicular = copy.deepcopy(base)
    info, _ = gen._analyse(non_perpendicular)
    r4 = info["origin"][0] + info["vy"][0]
    c4 = info["origin"][1] + info["vy"][1]
    non_perpendicular[r4][c4] = 0
    opposite_u = (-info["vx"][0], -info["vx"][1])
    non_perpendicular[info["origin"][0] + opposite_u[0]][info["origin"][1] + opposite_u[1]] = 4
    assert any("perpendicular" in error for error in gen.self_check(non_perpendicular))

    out_of_radius = copy.deepcopy(base)
    info, _ = gen._analyse(out_of_radius)
    # Expand to the maximum supported size and move one marker to local radius 5.
    expanded = [[0 for _ in range(17)] for _ in range(17)]
    offset = (3, 3)
    for r, row in enumerate(out_of_radius):
        for c, value in enumerate(row):
            expanded[r + offset[0]][c + offset[1]] = value
    einfo, _ = gen._analyse(expanded)
    target = (
        einfo["origin"][0] + 5 * einfo["vx"][0],
        einfo["origin"][1] + 5 * einfo["vx"][1],
    )
    # Remove one existing 8 first so the mutation is isolated.
    removed = False
    for r, row in enumerate(expanded):
        for c, value in enumerate(row):
            if value == 8:
                expanded[r][c] = 0
                removed = True
                break
        if removed:
            break
    expanded[target[0]][target[1]] = 8
    assert any("outside local radius 4" in error for error in gen.self_check(expanded))

    no_countable_points = copy.deepcopy(base)
    info, _ = gen._analyse(no_countable_points)
    for r, row in enumerate(no_countable_points):
        for c, value in enumerate(row):
            if value != 8:
                continue
            u, v = gen._local(info["origin"], info["vx"], info["vy"], (r, c))
            if max(abs(u), abs(v)) <= 3 and gen._quadrant(u, v) is not None:
                no_countable_points[r][c] = 0
    assert any("no off-axis" in error for error in gen.self_check(no_countable_points))


def test_determinism_fresh_returns_and_process_global_rng_purity():
    random.seed(20260725)
    before = random.getstate()
    first = gen.generate(777, 12, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after

    first[0][0] = 9
    assert gen.generate(777, 12, difficulty="hard") == second
