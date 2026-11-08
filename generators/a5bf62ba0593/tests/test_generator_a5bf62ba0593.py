from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.a5bf62ba0593.generator"
)
TASK_ID = "a5bf62ba0593"
ROOT = Path(__file__).resolve().parents[1]


def _canonical_rows() -> list[dict]:
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    assert rows, f"missing canonical task {TASK_ID}"
    return rows


def _canonical_pairs() -> list[dict]:
    return [
        pair
        for row in _canonical_rows()
        for split in ("train", "test")
        for pair in row[split]
    ]


def _unused_color(grid: list[list[int]]) -> int:
    used = {value for row in grid for value in row}
    return next(color for color in range(1, 10) if color not in used)


def test_generator_a5bf62ba0593_accepts_and_solves_every_canonical_pair():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_generator_a5bf62ba0593_rule_hash_is_pinned():
    assert MODULE.RULE_HASH == "55334b2b3d61"
    assert MODULE.VERSION == "2.0.0"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "grid_w,n_objects,selector_cells,transform_code",
    [(10, 2, 3, 1), (16, 4, 7, 5), (13, 3, 5, 3)],
)
def test_generator_a5bf62ba0593_exact_override_boundaries_are_observable(
    band, grid_w, n_objects, selector_cells, transform_code
):
    grid = MODULE.generate(
        314159,
        17,
        difficulty=band,
        grid_w=grid_w,
        n_objects=n_objects,
        selector_cells=selector_cells,
        transform_code=transform_code,
    )
    assert MODULE.observe_overrides(grid) == {
        "grid_w": grid_w,
        "n_objects": n_objects,
        "selector_cells": selector_cells,
        "transform_code": transform_code,
    }
    assert MODULE.self_check(grid, difficulty=band) == []
    assert len(grid) == 8
    assert len(grid[0]) == grid_w
    assert MODULE.rule_mirror(grid) != grid


def test_generator_a5bf62ba0593_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9137)
    state = random.getstate()
    first = MODULE.generate(123, 7, difficulty="hard")
    second = MODULE.generate(123, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0
    assert random.getstate() == state


def test_generator_a5bf62ba0593_regression_keeps_every_object_in_oracle_window():
    # The v1 generator's easy seed=0/sample_index=0 selector occupied rows
    # 8..10, which the Racket rule never reads. The same replay is now 8 rows.
    grid = MODULE.generate(0, 0, difficulty="easy")
    assert len(grid) == 8
    assert MODULE.self_check(grid) == []
    components = MODULE._body_components(grid)
    assert components
    assert max(r for component in components for r, _ in component["cells"]) <= 7
    assert len(MODULE._selector_component(grid)["cells"]) == 4


def test_generator_a5bf62ba0593_sequential_schedule_covers_all_five_codes_visibly():
    grids = [MODULE.generate(1900, index, difficulty="medium") for index in range(5)]
    assert [grid[0][1] for grid in grids] == [1, 2, 3, 4, 5]
    assert all(MODULE._visible_transform(grid) for grid in grids)


def test_generator_a5bf62ba0593_generalized_scenes_rebut_position_and_size_shortcuts():
    # sample_index=1 is outside the strict canonical-profile schedule.
    for band in ("easy", "medium", "hard"):
        grid = MODULE.generate(8128, 1, difficulty=band)
        assert MODULE.strict_canonical_like(grid)
        assert MODULE._selector_not_first(grid)
        assert MODULE._selector_not_largest(grid)
        assert MODULE._visible_transform(grid)


def test_generator_a5bf62ba0593_rejects_targeted_impostors():
    lawful = MODULE.generate(321, 7, difficulty="medium")

    no_header = [[0 for _ in row] for row in lawful]

    selector_equals_target = copy.deepcopy(lawful)
    selector_equals_target[0][2] = selector_equals_target[0][0]

    selector_absent = copy.deepcopy(lawful)
    selector_absent[0][0] = _unused_color(selector_absent)

    target_in_body = copy.deepcopy(lawful)
    component = MODULE._body_components(target_in_body)[0]
    r, c = component["cells"][0]
    target_in_body[r][c] = target_in_body[0][2]

    extra_header_payload = copy.deepcopy(lawful)
    extra_header_payload[0][5] = _unused_color(extra_header_payload)

    tiny_selector = copy.deepcopy(lawful)
    selector_component = MODULE._selector_component(tiny_selector)
    for r, c in selector_component["cells"][1:]:
        tiny_selector[r][c] = 0

    for impostor in (
        no_header,
        selector_equals_target,
        selector_absent,
        target_in_body,
        extra_header_payload,
        tiny_selector,
    ):
        assert MODULE.self_check(impostor), impostor


def test_generator_a5bf62ba0593_materialized_lessons_identify_the_rule():
    # Four demonstrations plus one query cover all transform codes and include
    # generalized shortcut-rebutting scenes.
    pairs = []
    for index in range(5):
        grid = MODULE.generate(4400 + index, index, difficulty="medium")
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    assert MODULE.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_generator_a5bf62ba0593_strict_profile_schedule_is_stable_and_nontrivial():
    for band in ("easy", "medium", "hard"):
        first = [
            MODULE.strict_canonical_like(MODULE.generate(5000 + i, i, difficulty=band))
            == []
            for i in range(40)
        ]
        disjoint = [
            MODULE.strict_canonical_like(MODULE.generate(9000 + i, i, difficulty=band))
            == []
            for i in range(40)
        ]
        assert 10 <= sum(first) <= 16
        assert 10 <= sum(disjoint) <= 16
        assert len(
            {
                json.dumps(MODULE.generate(5000 + i, i, difficulty=band))
                for i in range(40)
            }
        ) >= 35
