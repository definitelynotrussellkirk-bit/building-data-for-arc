from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.8b6543be4517.generator")
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "8b6543be4517"


def test_rule_hash_pins_selected_canonical_authority():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "4b5d3dcd179a"


def test_canonical_pairs_are_accepted_and_python_semantic_mirror_matches_outputs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_scene_profile_override_is_exact_and_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(1000 + index, index, difficulty=band, scene_profile=profile)
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="medium", typo_axis="oops")


def test_ordinary_draws_preserve_core_witnesses_and_witness_claims_are_sound():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(5000 + sample_index, sample_index, difficulty=band)
            info = gen._analysis(grid)
            assert info["unmatched_neg"]
            assert info["unmatched_pos"]
            assert info["preserved_asymmetric_distractors"]
            official = gen.rule_mirror(grid)
            for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                if gen.SEMANTIC_WITNESSES[witness_name](grid):
                    assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(77, 0, difficulty="medium", scene_profile="m_col_6")
    orientation, mid = gen._divider(grid)
    assert orientation == "col"

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    broken_divider = copy.deepcopy(grid)
    broken_divider[0][mid] = 0
    assert gen.self_check(broken_divider)

    missing_markers = [[0 if value == 7 else value for value in row] for row in grid]
    assert gen.self_check(missing_markers)

    stray_eight = copy.deepcopy(grid)
    cell = next((r, c) for r, row in enumerate(stray_eight) for c, v in enumerate(row) if v == 0 and c != mid)
    stray_eight[cell[0]][cell[1]] = 8
    assert gen.self_check(stray_eight)

    second_divider = copy.deepcopy(grid)
    row = next(r for r in range(len(grid)) if r != 0 and all(second_divider[r][c] != 7 for c in range(len(grid[0]))))
    for c in range(len(second_divider[0])):
        second_divider[row][c] = 8
    assert gen.self_check(second_divider)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(42, 7, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 3
    assert gen.generate(42, 7, difficulty="hard") == second


def test_four_demo_lessons_kill_named_rivals():
    demos = []
    for i in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(900 + i, i, difficulty="easy")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(999, 2, difficulty="hard")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
