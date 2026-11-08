from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = REPO_ROOT / "generators" / "ada76e18c19c" / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location("review_ada76e18c19c", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") != "ada76e18c19c":
                continue
            raw_pairs = [*record["train"], record["test"]]
            return [
                {"input": _decode(pair["input"]), "output": _decode(pair["output"])}
                for pair in raw_pairs
            ]
    raise AssertionError("canonical task ada76e18c19c not found")


def _qualifying_rows(grid: list[list[int]]) -> int:
    total = 0
    for row in grid:
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(cells) == 2 and cells[0][1] == cells[1][1]:
            total += 1
    return total


def test_selected_rule_contract_matches_every_canonical_pair():
    gen = _load_generator()

    assert gen.RULE_HASH == "714e73d2362f"
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert gen.EXAMPLES_NEEDED == 3

    for pair in _canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before, "rule_mirror mutated its input"


def test_rule_mirror_changes_only_rows_with_exactly_two_equal_nonzero_cells():
    gen = _load_generator()
    grid = [
        [2, 0, 0, 0, 2, 0, 0, 0, 0],      # qualifying
        [3, 0, 0, 0, 4, 0, 0, 0, 0],      # mismatched pair
        [5, 0, 5, 0, 0, 5, 0, 0, 0],      # three of one color
        [6, 0, 7, 0, 0, 0, 6, 0, 0],      # blocked equal pair
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    expected = copy.deepcopy(grid)
    expected[0][0:5] = [2, 2, 2, 2, 2]

    assert gen.rule_mirror(grid) == expected
    assert grid[0] == [2, 0, 0, 0, 2, 0, 0, 0, 0]


def test_default_schedule_cycles_exact_canonical_profiles_and_semantic_witnesses():
    gen = _load_generator()
    canonical_profiles = ((7, 10), (8, 9), (6, 11), (9, 12), (8, 10))
    witness_profiles = ("mismatched_pair", "extra_same_color", "blocked_pair")

    assert tuple(gen.SCHEDULE_PROFILES) == witness_profiles
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(15):
            grid = gen.generate(20260928, sample_index, difficulty=difficulty)
            assert (len(grid), len(grid[0])) == canonical_profiles[sample_index % 5]
            assert gen.schedule_profile(20260928, sample_index, difficulty) == witness_profiles[sample_index % 3]
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.strict_canonical_like(grid) == []
            assert len({value for row in grid for value in row}) == 4
            assert _qualifying_rows(grid) == 3
            witness = gen.SEMANTIC_WITNESSES[witness_profiles[sample_index % 3]]
            assert witness(grid)


def test_every_three_demo_window_refutes_canonical_shortcuts():
    gen = _load_generator()
    canonical = _canonical_pairs()

    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical), name

    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(717, index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(717, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
                assert any(shortcut(pair["input"]) != pair["output"] for pair in demos), name


def test_exact_dimension_overrides_are_observable_and_bad_calls_are_rejected():
    gen = _load_generator()

    for height, width in ((6, 9), (7, 10), (9, 12)):
        grid = gen.generate(13, 4, grid_h=height, grid_w=width)
        assert gen.observe_overrides(grid) == {"grid_h": height, "grid_w": width}
        assert gen.self_check(grid) == []

    for kwargs in (
        {"grid_h": 5},
        {"grid_h": 10},
        {"grid_w": 8},
        {"grid_w": 13},
        {"typo_axis": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(13, 4, **kwargs)

    with pytest.raises(ValueError):
        gen.generate(13, 4, difficulty="impossible")


def test_task_linked_mutations_are_all_rejected():
    gen = _load_generator()
    fixtures = list(gen.mutation_fixtures())
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name
    assert gen.self_check([[4, 4], [4, 4]])


def test_generation_is_deterministic_and_does_not_touch_global_random_state():
    gen = _load_generator()

    first = gen.generate(991, 7, difficulty="hard")
    second = gen.generate(991, 7, difficulty="hard")
    assert first == second

    random.seed(123456)
    expected = [random.random() for _ in range(6)]
    random.seed(123456)
    gen.generate(991, 7, difficulty="hard")
    actual = [random.random() for _ in range(6)]
    assert actual == expected
