from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base as generator_base
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "b06d49e11f7f"
module = importlib.import_module(
    "puzzle_generators.per_puzzle.b06d49e11f7f.generator"
)


def _info(grid):
    info, errors = module._analyse(grid)
    assert errors == []
    return info


def test_rule_hash_and_every_canonical_input_are_pinned_and_accepted():
    assert module.RULE_HASH == canonical_rule_hash(TASK_ID) == "9538488b69e8"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert module.self_check(grid) == []
        assert module.strict_canonical_like(grid) == []
        assert module.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


def test_unknown_override_is_rejected_and_joint_boundary_is_exact():
    with pytest.raises(ValueError, match="unknown override"):
        module.generate(0, 0, difficulty="easy", typo_axis=1)

    for band in ("easy", "medium", "hard"):
        grid = module.generate(
            1234,
            17,
            difficulty=band,
            n_rooms=4,
            grid_h=9,
            grid_w=11,
        )
        assert module.self_check(grid) == []
        assert module.observe_overrides(grid) == {
            "n_rooms": 4,
            "grid_h": 9,
            "grid_w": 11,
        }


def test_default_keyed_axis_requests_equal_observed_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for offset in range(30):
                grid = module.generate(
                    20_000 + band_index * 1_000 + offset,
                    400 + offset,
                    difficulty=band,
                )
                ctx = captured[-1]
                draws = ctx.recorded_draws()
                assert set(draws) >= set(module.AXES)
                assert module.observe_overrides(grid) == {
                    axis: draws[axis] for axis in module.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_random_isolation():
    random.seed(91_157)
    before = random.getstate()
    first = module.generate(91, 13, difficulty="hard")
    after = random.getstate()
    second = module.generate(91, 13, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    frozen_second = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == frozen_second
    assert module.generate(91, 13, difficulty="hard") == frozen_second


def test_self_check_rejects_four_targeted_impostors():
    base = module.generate(8080, 8, difficulty="medium")
    info = _info(base)

    half_pair = copy.deepcopy(base)
    legend_col = info["pairs"][0][0]
    half_pair[1][legend_col] = 0
    assert module.self_check(half_pair)

    broken_frame = copy.deepcopy(base)
    r1, c1, _r2, _c2 = info["frames"][0]["bbox"]
    broken_frame[r1][c1] = 0
    assert module.self_check(broken_frame)

    extra_seed = copy.deepcopy(base)
    frame = info["frames"][0]
    seed_r, seed_c, seed_color = frame["seed"]
    spare = next((r, c) for r, c in frame["interior"] if (r, c) != (seed_r, seed_c))
    extra_seed[spare[0]][spare[1]] = seed_color
    assert module.self_check(extra_seed)

    stray = copy.deepcopy(base)
    occupied = {
        (r, c)
        for r in range(2, len(base))
        for c in range(len(base[0]))
        if base[r][c] != 0
    }
    stray_pos = next(
        (r, c)
        for r in range(2, len(base))
        for c in range(len(base[0]))
        if (r, c) not in occupied
    )
    stray[stray_pos[0]][stray_pos[1]] = info["sources"].copy().pop()
    assert module.self_check(stray)


def test_full_interior_repaint_overwrites_seed_and_preserves_outline():
    grid = module.generate(777, 4, difficulty="hard")
    info = _info(grid)
    output = module.rule_mirror(grid)

    changed = set()
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != output[r][c]:
                changed.add((r, c))

    expected_changed = set()
    for frame in info["frames"]:
        seed_r, seed_c, seed_color = frame["seed"]
        target = info["mapping"][seed_color]
        assert output[seed_r][seed_c] == target != seed_color
        for r, c in frame["interior"]:
            assert output[r][c] == target
            expected_changed.add((r, c))
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    assert output[r][c] == 5
    assert changed == expected_changed


def test_every_sliding_three_demo_window_is_identifiable():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seed = 70_000 + band_index
        for start in range(12):
            pairs = []
            for sample_index in range(start, start + 4):
                grid = module.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": module.rule_mirror(grid)})
            assert module.lesson_identifiable(pairs[:3], pairs[3]) == []
            assert module.lesson_identifiable(pairs[:2], pairs[2])
