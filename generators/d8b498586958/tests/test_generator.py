"""Regression and semantic-contract tests for d8b498586958."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "d8b498586958"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_python_mirror_accepts_and_replays_every_canonical_pair(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_observable_in_every_band(band):
    requested = {
        "panel_side": 4,
        "operation": 3,
        "shared_cells": 5,
        "a_only_cells": 5,
        "b_only_cells": 5,
        "b_color": 7,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("panel_side", 3),
        ("panel_side", 10),
        ("operation", -1),
        ("operation", 4),
        ("shared_cells", 0),
        ("shared_cells", 6),
        ("a_only_cells", 0),
        ("b_only_cells", 6),
        ("b_color", 2),
        ("b_color", 5),
        ("panel_side", True),
        ("operation", 1.0),
        ("a_only_cells", "2"),
    ],
)
def test_invalid_or_unknown_overrides_raise(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_four_consecutive_default_examples_cover_all_operation_markers():
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17):
            operations = {
                gen.observe_overrides(gen.generate(seed, index, difficulty=band))["operation"]
                for index in range(4)
            }
            assert operations == {0, 1, 2, 3}


def test_all_four_operations_are_observationally_distinct_on_same_operands():
    outputs = []
    operands = []
    for operation in range(4):
        grid = gen.generate(
            91,
            7,
            panel_side=5,
            operation=operation,
            shared_cells=3,
            a_only_cells=4,
            b_only_cells=2,
            b_color=4,
        )
        observed = gen.observe_overrides(grid)
        assert observed["operation"] == operation
        operands.append((observed["shared_cells"], observed["a_only_cells"], observed["b_only_cells"]))
        outputs.append(gen.rule_mirror(grid))
    assert len(set(operands)) == 1
    assert len({tuple(map(tuple, output)) for output in outputs}) == 4


def test_column_only_shortcut_fits_demos_but_fails_canonical_query():
    shortcut = gen.CANONICAL_SHORTCUTS["column_only_header"]
    demonstrations = [pair for pair in PAIRS if pair["split"] == "train"]
    queries = [pair for pair in PAIRS if pair["split"] == "test"]
    assert demonstrations and queries
    assert all(shortcut(pair["input"]) == pair["output"] for pair in demonstrations)
    disagreements = [pair for pair in queries if shortcut(pair["input"]) != pair["output"]]
    assert disagreements
    query = disagreements[0]
    intended = query["output"]
    rival = shortcut(query["input"])
    assert [(r, c) for r in range(len(intended)) for c in range(len(intended[0])) if intended[r][c] != rival[r][c]] == [
        (2, 1), (2, 2), (2, 3)
    ]


def test_scheduled_four_demo_lesson_refutes_every_declared_competitor():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(123, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(123, gen.EXAMPLES_NEEDED, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


def test_self_check_rejects_marker_and_operand_contract_mutations():
    grid = gen.generate(44, 0, operation=2, shared_cells=2, a_only_cells=2, b_only_cells=2)
    assert gen.self_check(grid) == []

    missing_marker = deepcopy(grid)
    for row in range(2):
        for col in range(len(grid[0])):
            if missing_marker[row][col] == 5:
                missing_marker[row][col] = 0
    assert gen.self_check(missing_marker)

    duplicate_marker = deepcopy(grid)
    duplicate_marker[0][-1] = 5
    assert gen.self_check(duplicate_marker)

    erase_b = deepcopy(grid)
    divider_rows = [r for r, row in enumerate(erase_b) if all(value == 9 for value in row)]
    for row in range(divider_rows[1] + 1, len(erase_b)):
        erase_b[row] = [0] * len(erase_b[row])
    assert gen.self_check(erase_b)


def test_generation_is_keyed_and_repeatable():
    first = gen.generate(712, 31, difficulty="hard")
    for index in range(100):
        gen.generate(index, index * 7, difficulty="easy")
    assert gen.generate(712, 31, difficulty="hard") == first
