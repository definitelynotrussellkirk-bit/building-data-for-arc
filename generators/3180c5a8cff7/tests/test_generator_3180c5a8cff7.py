from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "3180c5a8cff7"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE = (
    ROOT
    / "data/base/solutions/banks/f234ef852d75/E17__3180c5a8cff7.json"
)


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def _canonical_pairs():
    row = _canonical_row()
    test = row.get("test")
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train") or []) + list(test or [])


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_base_authority_and_all_canonical_pairs():
    row = _canonical_row()
    rule = row["program_solution"]
    digest = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "35f54e2db692"

    base = json.loads(BASE.read_text())
    assert base["racket_target"]["raw_code"] == rule
    assert base["racket_target"]["target_code"] == rule

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        grid = _grid(pair["input"])
        expected = _grid(pair["output"])
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == expected


@pytest.mark.parametrize("height", [5, 12])
@pytest.mark.parametrize("width", [6, 14])
@pytest.mark.parametrize("count", [2, 4])
@pytest.mark.parametrize("texture", MODULE.HELPFUL_TEXTURES)
def test_every_declared_boundary_and_texture_is_exact(
    height, width, count, texture
):
    grid = MODULE.generate(
        101,
        7,
        difficulty="easy",
        grid_h=height,
        grid_w=width,
        num_triplets=count,
        texture=texture,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert MODULE.observe_overrides(grid) == {"num_triplets": count}
    assert MODULE.self_check(
        grid,
        meta={
            "overrides": {
                "num_triplets": count,
                "texture": texture,
            }
        },
    ) == []
    output = MODULE.rule_mirror(grid)
    assert sum(
        left != right
        for input_row, output_row in zip(grid, output)
        for left, right in zip(input_row, output_row)
    ) == count


def test_profiles_exercise_the_intended_linked_branches():
    grids = {
        texture: MODULE.generate(
            303,
            9,
            grid_h=9,
            grid_w=12,
            num_triplets=3,
            texture=texture,
        )
        for texture in MODULE.HELPFUL_TEXTURES
    }
    facts = {name: MODULE._analysis(grid) for name, grid in grids.items()}
    assert len(facts["scattered_rows"]["triplet_rows"]) == 3
    assert facts["shared_row"]["shared_row"]
    assert facts["edge_anchored"]["left_edge"]
    assert facts["edge_anchored"]["right_edge"]
    assert len(facts["distractors"]["distractor_fives"]) >= 3
    assert facts["distractors"]["distractor_adjacent_pairs"]
    assert len({_frozen(grid) for grid in grids.values()}) == len(grids)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(
        73,
        6,
        difficulty="hard",
        num_triplets=4,
        texture="distractors",
    )
    assert random.getstate() == state
    second = MODULE.generate(
        73,
        6,
        difficulty="hard",
        num_triplets=4,
        texture="distractors",
    )
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert MODULE.generate(
        73,
        6,
        difficulty="hard",
        num_triplets=4,
        texture="distractors",
    ) == second


def test_self_check_rejects_targeted_semantic_impostors():
    base = MODULE.generate(
        211,
        4,
        grid_h=9,
        grid_w=12,
        num_triplets=2,
        texture="edge_anchored",
    )

    all_background = [[0] * len(base[0]) for _ in base]
    assert MODULE.self_check(all_background)

    output_color_leak = [row[:] for row in base]
    row, col = MODULE._analysis(output_color_leak)["centres"][0]
    output_color_leak[row][col] = 3
    assert MODULE.self_check(output_color_leak)

    wrong_exact_count = [row[:] for row in base]
    free_row = next(
        row
        for row in range(len(wrong_exact_count))
        if all(value == 0 for value in wrong_exact_count[row])
    )
    assert MODULE._place_triplet(wrong_exact_count, free_row, 3)
    assert MODULE.self_check(
        wrong_exact_count,
        meta={"overrides": {"num_triplets": 2}},
    )

    no_left_edge = [row[:] for row in base]
    left_row, left_col = next(
        centre
        for centre in MODULE._analysis(no_left_edge)["centres"]
        if centre[1] == 1
    )
    no_left_edge[left_row][left_col - 1] = 0
    no_left_edge[left_row][left_col + 1] = 0
    replacement_row = next(
        row
        for row in range(len(no_left_edge))
        if all(value == 0 for value in no_left_edge[row])
    )
    assert MODULE._place_triplet(no_left_edge, replacement_row, 3)
    assert MODULE.self_check(
        no_left_edge,
        meta={
            "overrides": {
                "num_triplets": 2,
                "texture": "edge_anchored",
            }
        },
    )

    distractor_scene = MODULE.generate(
        212,
        4,
        grid_h=9,
        grid_w=12,
        num_triplets=3,
        texture="distractors",
    )
    missing_distractors = [row[:] for row in distractor_scene]
    for row, col in MODULE._analysis(distractor_scene)["distractor_fives"]:
        missing_distractors[row][col] = 0
    assert MODULE.self_check(
        missing_distractors,
        meta={
            "overrides": {
                "num_triplets": 3,
                "texture": "distractors",
            }
        },
    )


@pytest.mark.parametrize(
    "kwargs,exc_type",
    [
        ({"difficulty": "expert"}, ValueError),
        ({"texture": "ignored"}, ValueError),
        ({"num_triplets": 5}, ValueError),
        ({"grid_h": 4}, ValueError),
        ({"grid_w": 15}, ValueError),
        ({"palette_kind": "default"}, TypeError),
    ],
)
def test_invalid_or_retired_controls_fail_loudly(kwargs, exc_type):
    with pytest.raises(exc_type):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "num_triplets",
        "texture",
    }
    assert tuple(MODULE.AXES["texture"]["valid"].split("|")) == (
        MODULE.HELPFUL_TEXTURES
    )
    assert MODULE.DEGENERATE_TEXTURES == ()
