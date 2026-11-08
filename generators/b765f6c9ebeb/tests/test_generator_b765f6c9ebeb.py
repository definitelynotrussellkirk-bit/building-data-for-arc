"""Semantic and distribution regressions for generator b765f6c9ebeb."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import random
import sys

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "b765f6c9ebeb"
REPO = find_root(__file__)
GEN, GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=REPO)


def _canonical_row() -> dict:
    path = canonical_path(REPO)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row is missing")


def _pairs(row: dict) -> list[dict]:
    test = row["test"]
    return [*row["train"], *([test] if isinstance(test, dict) else test)]


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def test_canonical_inputs_are_accepted_and_mirrored_exactly():
    row = _canonical_row()
    for pair in _pairs(row):
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_first_three_default_profiles_cover_canonical_shapes_and_palettes():
    grids = [GEN.generate(20261002, i, difficulty="easy") for i in range(3)]
    assert [(len(g), len(g[0]), _palette_size(g)) for g in grids] == [
        (5, 6, 6),
        (5, 5, 5),
        (5, 7, 5),
    ]
    assert all(GEN.self_check(grid) == [] for grid in grids)


def test_helpful_textures_supply_connectivity_counterexamples():
    mixed = GEN.generate(
        91,
        0,
        difficulty="medium",
        grid_h=7,
        grid_w=8,
        singletons=2,
        objects=3,
        palette_kind="default",
        texture="color_touch",
    )
    diagonal = GEN.generate(
        91,
        1,
        difficulty="medium",
        grid_h=7,
        grid_w=8,
        singletons=2,
        objects=3,
        palette_kind="warm",
        texture="diagonal_same_color",
    )
    assert GEN.SEMANTIC_WITNESSES["mixed_color_contact"](mixed)
    assert GEN.SEMANTIC_WITNESSES["same_color_diagonal_singletons"](diagonal)
    assert GEN.SEMANTIC_RIVALS["multicolor_4"](mixed) != GEN.rule_mirror(mixed)
    assert GEN.SEMANTIC_RIVALS["same_color_8"](diagonal) != GEN.rule_mirror(diagonal)


def test_exact_overrides_are_observable_and_unknown_keys_fail_closed():
    grid = GEN.generate(
        777,
        5,
        difficulty="hard",
        grid_h=8,
        grid_w=10,
        singletons=3,
        objects=2,
        palette_kind="cool",
        texture="color_touch",
    )
    assert (len(grid), len(grid[0])) == (8, 10)
    assert GEN.observe_overrides(grid) == {"singletons": 3, "objects": 2}
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis="ignored")


def test_three_consecutive_scheduled_examples_identify_the_rule():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + 3):
            grid = GEN.generate(8080, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query = GEN.generate(8080, start + 3, difficulty="hard")
        assert GEN.lesson_identifiable(demos, query) == []


def test_determinism_freshness_and_process_rng_purity():
    random.seed(1459)
    state = random.getstate()
    first = GEN.generate(42, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(42, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))


def test_source_avoids_reserved_racket_primitive_identifiers():
    # The generator linter treats these names as evidence that Python may be
    # shadowing the Racket authority.  Keep the production source vocabulary
    # unambiguous so a warning cannot stop the required battery.
    tree = ast.parse(GENERATOR_PATH.read_text())
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    sys.path.insert(0, str(REPO / "shared"))
    from tools.lint_generator import RACKET_PRIMITIVE_NAMES

    assert names.isdisjoint(RACKET_PRIMITIVE_NAMES), sorted(
        names & RACKET_PRIMITIVE_NAMES
    )
