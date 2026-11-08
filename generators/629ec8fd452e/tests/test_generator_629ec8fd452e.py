from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "629ec8fd452e"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.629ec8fd452e.generator"
)


def _frame(color: int = 4) -> list[list[int]]:
    grid = [[0] * 5 for _ in range(5)]
    for col in range(1, 4):
        grid[1][col] = color
        grid[3][col] = color
    for row in range(1, 4):
        grid[row][1] = color
        grid[row][3] = color
    return grid


def test_rule_hash_and_all_canonical_pairs_match_python_mirror() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_true(pair["input"]) == pair["output"]


def test_declared_override_boundaries_are_exact_and_observable() -> None:
    seed = 314159
    for grid_h in (9, 14):
        for grid_w in (10, 16):
            for n_hollow in (1, 2):
                for n_solid in (1, 2):
                    for shared_reject_role in ("solid", "open"):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_hollow": n_hollow,
                            "n_solid": n_solid,
                            "shared_reject_role": shared_reject_role,
                        }
                        grid = gen.generate(
                            seed,
                            7,
                            difficulty="medium",
                            **requested,
                        )
                        assert gen.observe_overrides(grid) == requested
                        assert gen.self_check(grid, meta={"overrides": requested}) == []


def test_unknown_override_is_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_every_generated_scene_carries_all_shortcut_rebuttals() -> None:
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(2026, 11, difficulty=band)
        expected = gen.rule_true(grid)
        assert gen.self_check(grid) == []
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), name
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(copy.deepcopy(grid)) != expected, name


def test_lessons_are_identifiable_against_named_rivals() -> None:
    demos = []
    for sample_index in range(3):
        grid = gen.generate(73, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_true(grid)})
    query_grid = gen.generate(73, 3, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_true(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_four_targeted_impostors() -> None:
    # 1. All-solid: no survivor branch.
    all_solid = [[0] * 7 for _ in range(6)]
    for row in (1, 2, 3):
        for col in (1, 2, 3):
            all_solid[row][col] = 2
    assert any("no component with a true enclosed hole" in e for e in gen.self_check(all_solid))

    # 2. All-hollow: no erased branch.
    all_hollow = _frame(4)
    assert any("no non-hole component" in e for e in gen.self_check(all_hollow))

    # 3. Open almost-ring plus a solid: bbox interior is missing, but no true hole.
    open_plus_solid = [[0] * 9 for _ in range(6)]
    for row, col in gen._open_almost_ring():
        open_plus_solid[row + 1][col + 1] = 5
    for row in (2, 3):
        for col in (6, 7):
            open_plus_solid[row][col] = 7
    errors = gen.self_check(open_plus_solid)
    assert any("no component with a true enclosed hole" in e for e in errors)

    # 4. A lone true-hole frame: transformation would be identity/no contrast.
    lone_hollow = _frame(8)
    errors = gen.self_check(lone_hollow)
    assert any("no non-hole component" in e for e in errors)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(987654321)
    before_state = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    after_state = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")
    assert before_state == after_state
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
