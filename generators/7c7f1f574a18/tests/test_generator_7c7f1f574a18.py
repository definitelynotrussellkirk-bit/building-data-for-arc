"""Task-local regressions for 7c7f1f574a18.

The tests bind the sampler to the canonical Racket rule without using the
production Python mirror as the only oracle: canonical examples come from the
pinned catalog, structural observations are recomputed independently here, and
Racket parity is exercised by the packet's task-test stage.
"""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "7c7f1f574a18"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.7c7f1f574a18.generator"
)


def _filled_rect(color: int = 1) -> list[list[int]]:
    grid = [[4] * 9 for _ in range(7)]
    for row in range(2, 5):
        for col in range(2, 5):
            grid[row][col] = color
    return grid


def _frame(color: int = 1) -> list[list[int]]:
    grid = [[4] * 9 for _ in range(7)]
    for col in range(2, 5):
        grid[2][col] = color
        grid[4][col] = color
    for row in range(2, 5):
        grid[row][2] = color
        grid[row][4] = color
    return grid


def _open_ring(color: int = 1) -> list[list[int]]:
    grid = _frame(color)
    grid[4][3] = 4
    return grid


def test_rule_hash_and_all_canonical_pairs_match_independent_mirror() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_true(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 19,
            "grid_w": 19,
            "n_closed": 2,
            "n_open": 1,
            "palette_profile": "canonical",
        },
        {
            "grid_h": 24,
            "grid_w": 26,
            "n_closed": 3,
            "n_open": 2,
            "palette_profile": "binary",
        },
        {
            "grid_h": 22,
            "grid_w": 24,
            "n_closed": 3,
            "n_open": 1,
            "palette_profile": "multicolor",
        },
    ],
)
def test_exact_overrides_are_observable_in_every_band(
    band: str | None, requested: dict[str, object]
) -> None:
    grid = gen.generate(314159, 7, difficulty=band, **requested)
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"grid_h": 18},
        {"grid_h": 25},
        {"grid_w": 18},
        {"grid_w": 27},
        {"n_closed": 1},
        {"n_closed": 4},
        {"n_open": 0},
        {"n_open": 3},
        {"palette_profile": "rainbow"},
        {"grid_h": True},
        {"n_open": 1.5},
    ],
)
def test_invalid_overrides_fail_loudly(override: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        gen.generate(1, 0, **override)


def test_every_ordinary_scene_refutes_declared_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(20261003, index, difficulty=band)
            expected = gen.rule_true(grid)
            assert gen.self_check(grid) == []
            assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(copy.deepcopy(grid)) != expected, name


def test_lessons_are_identifiable_against_named_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(99 + start, start * 17 + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_true(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_self_check_rejects_low_information_impostors() -> None:
    all_background = [[4] * 9 for _ in range(7)]
    all_closed = _filled_rect()
    all_open = _open_ring()
    lone_hollow = _frame()
    full_grid = [[2] * 9 for _ in range(7)]
    ragged = [[4, 4], [4]]
    for grid in (all_background, all_closed, all_open, lone_hollow, full_grid, ragged):
        assert gen.self_check(grid), grid


def test_generated_roles_cross_input_side_and_preserve_rows() -> None:
    for index in range(32):
        grid = gen.generate(707, index, difficulty="hard")
        analysis = gen._analysis(grid)
        midpoint = (len(grid[0]) - 1) / 2
        assert any(obj["closed"] and obj["center_col"] > midpoint for obj in analysis["components"])
        assert any(not obj["closed"] and obj["center_col"] < midpoint for obj in analysis["components"])
        out = gen.rule_true(grid)
        for obj in analysis["components"]:
            occupied_rows = {row for row, _ in obj["cells"]}
            color = 2 if obj["closed"] else 3
            assert occupied_rows <= {
                row for row, values in enumerate(out) if color in values
            }


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
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_generated_object_scale_overlaps_canonical_examples() -> None:
    maxima = []
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            analysis = gen._analysis(gen.generate(8080, index, difficulty=band))
            maxima.append(max(len(obj["cells"]) for obj in analysis["components"]))
    assert min(maxima) >= 15
    assert max(maxima) >= 17
