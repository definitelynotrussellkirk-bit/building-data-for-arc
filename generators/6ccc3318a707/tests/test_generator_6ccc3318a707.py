"""Regression tests for the 6ccc3318a707 anti-diagonal reflection generator."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "6ccc3318a707"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError(f"canonical row not found for {TASK_ID}")


def _lesson(seed: int, start: int, difficulty: str):
    demos = []
    for index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_rule_pin_and_all_canonical_pairs_are_owned_exactly():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "ea62a41435bf"
    pairs = _canonical_pairs()
    assert len(pairs) == 3

    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_default_draw_is_canonical_profile_and_refutes_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(711, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.strict_canonical_like(grid) == []
            assert 6 <= len(grid) <= 8
            assert len(grid) == len(grid[0])
            assert len({value for row in grid for value in row}) == 5

            intended = GEN.rule_mirror(grid)
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                assert witness(grid), (difficulty, sample_index, name)
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                assert rival(grid) != intended, (difficulty, sample_index, name)


def test_exact_override_boundaries_are_observable_in_every_band():
    case = 0
    axes = {
        "grid_size": (6, 8),
        "diagonal_marks": (1, 2),
        "mirror_pairs": (1, 2),
        "singletons": (2, 3),
    }
    names = tuple(axes)
    for difficulty in ("easy", "medium", "hard"):
        for values in itertools.product(*(axes[name] for name in names)):
            requested = dict(zip(names, values))
            grid = GEN.generate(
                9200 + case,
                case,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.self_check(
                grid, difficulty=difficulty, meta={"overrides": requested}
            ) == []
            assert GEN.observe_overrides(grid) == requested
            case += 1


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"unknown_axis": 1}, "unknown override"),
        ({"grid_size": 5}, "grid_size"),
        ({"diagonal_marks": 0}, "diagonal_marks"),
        ({"mirror_pairs": 3}, "mirror_pairs"),
        ({"singletons": 1}, "singletons"),
        ({"difficulty": "extreme"}, "difficulty"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        GEN.generate(1, 0, **kwargs)


def test_difficulty_bands_change_layout_without_changing_the_task_manifold():
    for sample_index in range(12):
        grids = [
            GEN.generate(5150, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({repr(grid) for grid in grids}) >= 2
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert {len({value for row in grid for value in row}) for grid in grids} == {5}


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_every_sliding_lesson_refutes_all_named_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos, query = _lesson(404, start, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), name


def test_declared_canonical_shortcuts_are_real_and_generated_counterexamples_exist():
    assert {"keep_occupied_pairs", "reflect_only_unique_colors"} <= set(
        GEN.CANONICAL_SHORTCUTS
    )
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name

        for index in range(12):
            grid = GEN.generate(808, index, difficulty="medium")
            assert shortcut(grid) != GEN.rule_mirror(grid), (name, index)


def test_self_check_rejects_structural_impostors():
    valid = GEN.generate(99, 3)
    bad_cases = {
        "empty": [],
        "blank": [[0 for _ in range(6)] for _ in range(6)],
        "ragged": [[0, 0], [0]],
        "rectangle": [[0 for _ in range(7)] for _ in range(6)],
        "out_of_range": copy.deepcopy(valid),
        "too_few_colors": copy.deepcopy(valid),
    }
    bad_cases["out_of_range"][0][0] = 10
    for row in bad_cases["too_few_colors"]:
        for col, value in enumerate(row):
            if value:
                row[col] = 1

    for name, grid in bad_cases.items():
        assert GEN.self_check(grid), name
