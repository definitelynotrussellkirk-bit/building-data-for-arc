from __future__ import annotations

import copy
import importlib
import random
from itertools import product

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.53ffc8bc9584.generator")


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _empty_cell_far_from_marks(grid: list[list[int]]) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    marked = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if all(max(abs(r - rr), abs(c - cc)) > 1 for rr, cc in marked):
                return r, c
    raise AssertionError("test fixture has no isolated empty cell")


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == "fbd60dec4738"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3

    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

    # Every named shortcut is genuinely ambiguous on all canonical examples.
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_declared_override_boundary_cross_product_is_exact_and_observable():
    for band, h, w, n_targets, family in product(
        ("easy", "medium", "hard"),
        (7, 11),
        (7, 11),
        (2, 3),
        gen.SCENE_FAMILIES,
    ):
        expected = {
            "grid_h": h,
            "grid_w": w,
            "n_targets": n_targets,
            "scene_family": family,
        }
        grid = gen.generate(
            seed=91,
            sample_index=7,
            difficulty=band,
            **expected,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == expected
        assert gen.rule_mirror(grid) != grid


def test_unknown_invalid_overrides_and_difficulty_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, imaginary_axis=3)
    with pytest.raises((ValueError, KeyError)):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises((ValueError, KeyError)):
        gen.generate(1, 0, scene_family="not-a-family")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_every_four_demo_sliding_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [_pair(4_200 + start, start + offset, band) for offset in range(4)]
            query = _pair(9_900 + start, start + 4, band)
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.observe_overrides(pair["input"])["scene_family"]
                for pair in demos
            } == set(gen.SCENE_FAMILIES)


def test_each_counterexample_family_refutes_its_named_canonical_shortcut():
    family_to_rival = {
        "linked": "isolated_components_only",
        "sandwich": "two_cardinal_yellows",
        "colored": "color_blind_equal_l",
    }
    for band in ("easy", "medium", "hard"):
        for sample_index, family in enumerate(gen.SCENE_FAMILIES):
            # Keep the episode seed fixed: its phase rotates the family cycle.
            grid = gen.generate(700, sample_index, difficulty=band)
            assert gen.observe_overrides(grid)["scene_family"] == family
            if family in family_to_rival:
                rival = gen.CANONICAL_SHORTCUTS[family_to_rival[family]]
                assert rival(grid) != gen.rule_mirror(grid)


def test_self_check_rejects_five_structural_impostors():
    base = gen.generate(123, 0, difficulty="medium", scene_family="isolated")
    info, errors = gen._analyse(base)
    assert errors == []

    unsupported_color = copy.deepcopy(base)
    r, c = _empty_cell_far_from_marks(unsupported_color)
    unsupported_color[r][c] = 9
    assert any("unsupported" in error for error in gen.self_check(unsupported_color))

    orphan_singleton = copy.deepcopy(base)
    r, c = _empty_cell_far_from_marks(orphan_singleton)
    orphan_singleton[r][c] = 4
    assert any("singleton" in error for error in gen.self_check(orphan_singleton))

    completed_l = copy.deepcopy(base)
    tr, tc = info["targets"][0]
    completed_l[tr][tc] = 4
    assert gen.self_check(completed_l)

    no_targets = [[0 for _ in row] for row in base]
    assert any("2..3" in error for error in gen.self_check(no_targets))

    ragged = copy.deepcopy(base)
    ragged[-1].pop()
    assert any("rectangular" in error for error in gen.self_check(ragged))


def test_deterministic_replay_fresh_returns_and_global_rng_isolation():
    random.seed(123456)
    state_before = random.getstate()
    first = gen.generate(9_876, 11, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(9_876, 11, difficulty="hard")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(9_876, 11, difficulty="hard")
