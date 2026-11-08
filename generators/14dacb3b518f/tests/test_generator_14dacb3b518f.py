from __future__ import annotations

import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "14dacb3b518f"
GENERATOR_HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    try:
        return importlib.import_module(
            "puzzle_generators.per_puzzle.14dacb3b518f.generator"
        )
    except ModuleNotFoundError:
        spec = importlib.util.spec_from_file_location(
            "review_generator_14dacb3b518f", GENERATOR_HOME / "generator.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


gen = _load_generator()


def _find_canonical_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            candidate = parent / relative
            if candidate.exists():
                return candidate
    raise AssertionError("could not locate canonical puzzles.jsonl")


def _canonical_row() -> dict:
    with _find_canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def test_rule_pin_and_all_canonical_pairs_are_exact():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "fe78a969401a"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_five_profile_lesson_refutes_declared_shortcuts():
    grids = [gen.generate(0, index, difficulty="medium") for index in range(5)]
    assert [gen.schedule_profile(0, index) for index in range(5)] == list(range(5))
    assert all(gen.self_check(grid) == [] for grid in grids)

    observed = [gen.observe_overrides(grid) for grid in grids]
    assert {item["n_holed"] for item in observed} == {1, 2}
    assert {item["n_solid"] for item in observed} == {1, 2}

    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name

    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(
            grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)
        )
        answer = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer

    demos = [
        {"input": grid, "output": gen.rule_mirror(grid)} for grid in grids[:4]
    ]
    query = {"input": grids[4], "output": gen.rule_mirror(grids[4])}
    assert gen.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name


def test_full_override_boundaries_are_exact_observable_and_band_safe():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (10, 14):
            for grid_w in (12, 16):
                for n_holed in (1, 2):
                    for n_solid in (1, 2):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_holed": n_holed,
                            "n_solid": n_solid,
                        }
                        grid = gen.generate(
                            9000 + case_index,
                            case_index % 17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested
                        case_index += 1

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_structural_mutations_and_minimal_impostors_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    minimal_impostors = [
        [[0] * 12 for _ in range(10)],
        [[6] * 12 for _ in range(10)],
        [[6] + [0] * 11] + [[0] * 12 for _ in range(9)],
        [[0] * 12 for _ in range(10)] + [[0]],
    ]
    for grid in minimal_impostors:
        assert gen.self_check(grid)


def test_rule_mirror_recolors_each_component_by_enclosed_hole_count():
    grid = gen.generate(
        31415,
        9,
        difficulty="medium",
        grid_h=14,
        grid_w=16,
        n_holed=2,
        n_solid=2,
    )
    analysis = gen._analyze(grid)
    output = gen.rule_mirror(grid)
    assert output == analysis["output"]
    for component in analysis["holed"]:
        assert component["hole_count"] >= 1
        assert all(output[row][col] == 8 for row, col in component["cells"])
    for component in analysis["solid"]:
        assert component["hole_count"] == 0
        assert all(output[row][col] == 2 for row, col in component["cells"])
