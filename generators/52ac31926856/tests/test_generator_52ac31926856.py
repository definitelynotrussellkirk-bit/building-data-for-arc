from __future__ import annotations

import importlib

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.52ac31926856.generator"
)


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_schedule_covers_all_three_semantic_outcomes():
    observed = []
    for sample_index in range(3):
        grid = gen.generate(1729, sample_index, difficulty="medium")
        assert gen.self_check(grid) == []
        observed.append(gen.observe_overrides(grid)["landing"])
    assert observed == ["first", "second", "bottom"]


def test_exact_override_boundaries_are_observable():
    cases = [
        dict(grid_h=10, grid_w=10, landing="second", target_width=5),
        dict(grid_h=20, grid_w=20, landing="bottom", target_width=1),
        dict(grid_h=10, grid_w=20, landing="first", target_width=5),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(9000 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_self_check_rejects_targeted_impostors():
    impostors = [
        [[0] * 10 for _ in range(10)],
        [[1] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)],
    ]
    impostors[2][0][4] = 1
    impostors[2][3][2] = 2
    impostors[2][3][7] = 2  # walls have no height/floor
    impostors[3][0][4] = 1
    for row in range(3, 7):
        impostors[3][row][2] = 2
        impostors[3][row][7] = 2
    for col in range(2, 8):
        impostors[3][6][col] = 2
    impostors[3][4][4] = 2  # illegal red cell in the interior above the floor
    for grid in impostors:
        assert gen.self_check(grid)


def test_three_demo_window_identifies_query_against_declared_rivals():
    seed = 424242
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_replay_is_deterministic_and_returns_fresh_objects():
    args = (12345, 2)
    first = gen.generate(*args, difficulty="easy")
    second = gen.generate(*args, difficulty="easy")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert gen.generate(*args, difficulty="easy") == second
