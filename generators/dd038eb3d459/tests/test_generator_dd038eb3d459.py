"""Focused contract and curriculum regressions for generator dd038eb3d459."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "dd038eb3d459"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_rule_pin_canonical_pairs_and_declared_shortcut() -> None:
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "624c38e915df"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    assert set(GEN.CANONICAL_SHORTCUTS) == {"top_left_is_180_degrees"}

    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert pair["input"] == source
        for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
            assert shortcut(source) == pair["output"], name


def test_every_sliding_four_demo_window_refutes_the_shortcut() -> None:
    assert tuple(GEN.SCHEDULE_PROFILES) == ("tl", "tr", "br", "bl")
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos, query = _lesson(7100 + start, start, difficulty)
            assert {
                GEN.schedule_profile(7100 + start, index, difficulty)
                for index in range(start, start + GEN.EXAMPLES_NEEDED)
            } == set(GEN.SCHEDULE_PROFILES)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), name


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = (
        {
            "grid_h": 8,
            "grid_w": 10,
            "corner_position": "tl",
            "red_size": 3,
            "green_size": 5,
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "corner_position": "tr",
            "red_size": 5,
            "green_size": 3,
        },
        {
            "grid_h": 9,
            "grid_w": 11,
            "corner_position": "br",
            "red_size": 4,
            "green_size": 4,
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "corner_position": "bl",
            "red_size": 5,
            "green_size": 5,
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(
                8000 + index,
                20 + index,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(
                grid, difficulty=difficulty, meta={"overrides": requested}
            ) == []

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, misspelled_axis=1)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="corner_position"):
        GEN.generate(0, 0, corner_position="center")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_default_schedule_is_canonical_scaled_and_semantically_decisive() -> None:
    canonical_profiles = {(8, 10), (9, 11), (10, 10), (9, 12), (10, 12)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(9001, index, difficulty=difficulty) for index in range(20)]
        assert all((len(grid), len(grid[0])) in canonical_profiles for grid in grids)
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert any(
            GEN.SEMANTIC_WITNESSES["top_left_rotation_discriminator"](grid)
            for grid in grids
        )
        assert all(
            GEN.rule_mirror(grid) != GEN._rival_top_left_is_180_degrees(grid)
            for grid in grids
            if GEN.observe_overrides(grid)["corner_position"] == "tl"
        )


def test_shape_distribution_is_not_a_tiny_fixed_bank() -> None:
    signatures = set()
    inputs = set()
    for index in range(80):
        grid = GEN.generate(10000 + index, index, difficulty="hard")
        facts = GEN._analyze(grid)[0]
        signatures.add((facts["red_shape"], facts["green_shape"]))
        inputs.add(tuple(tuple(row) for row in grid))
    assert len(signatures) >= 24
    assert len(inputs) >= 72


def test_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(11001, 0, difficulty="medium")
    assert GEN.self_check(valid) == []

    missing_control = copy.deepcopy(valid)
    facts = GEN._analyze(valid)[0]
    r, c = facts["control"]
    missing_control[r][c] = 0

    disconnected_red = copy.deepcopy(valid)
    rr, cc = facts["red_cells"][0]
    disconnected_red[rr][cc] = 0
    disconnected_red[1][1] = 2

    touching = copy.deepcopy(valid)
    for rr, cc in facts["green_cells"]:
        touching[rr][cc] = 0
    red_r, red_c = facts["red_cells"][0]
    touching[red_r][red_c + 1] = 3
    touching[red_r][red_c + 2] = 3
    touching[red_r + 1][red_c + 2] = 3

    illegal = copy.deepcopy(valid)
    illegal[1][1] = 9

    for name, grid in {
        "missing control": missing_control,
        "disconnected red": disconnected_red,
        "touching operands": touching,
        "illegal palette": illegal,
    }.items():
        assert GEN.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20261003)
    before = random.getstate()
    first = GEN.generate(123456, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123456, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(123456, 17, difficulty="hard") == second
