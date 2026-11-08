from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.af72e426e241 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_af72e426e241_accepts_and_solves_every_canonical_pair():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_af72e426e241_four_demo_schedule_identifies_the_rule():
    seed = 987_654
    demos = [
        _pair(gen.generate(seed, index, difficulty="medium"))
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    query = _pair(gen.generate(seed, gen.EXAMPLES_NEEDED, difficulty="medium"))

    observed = [gen.observe_overrides(pair["input"]) for pair in demos]
    assert {row["quadrant"] for row in observed} == set(gen.QUADRANTS)
    assert {(row["motif_h"], row["motif_w"]) for row in observed} == set(gen.MOTIF_DIMS)
    assert {row["row_gap"] for row in observed} == {1, 2}
    assert {row["col_gap"] for row in observed} == {1, 2}
    assert len({row["motif_color"] for row in observed}) == 4
    assert gen.lesson_identifiable(demos, query) == []


def test_af72e426e241_exact_overrides_are_observable_at_boundaries():
    requested = {
        "grid_size": 13,
        "motif_h": 3,
        "motif_w": 3,
        "quadrant": "southeast",
        "row_gap": 2,
        "col_gap": 2,
        "motif_color": 8,
    }
    grid = gen.generate(41, 7, difficulty="easy", **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, meta={"overrides": requested}) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(41, 7, typo_axis=1)


def test_af72e426e241_self_check_rejects_targeted_impostors():
    grid = gen.generate(
        12,
        0,
        grid_size=13,
        motif_h=2,
        motif_w=2,
        quadrant="northwest",
        row_gap=1,
        col_gap=1,
        motif_color=4,
    )
    info, errors = gen._analyze(grid)
    assert errors == []
    anchor_row, anchor_col = info["anchor"]
    r0, c0, r1, c1 = info["bbox"]

    no_anchor = copy.deepcopy(grid)
    no_anchor[anchor_row][anchor_col] = 0

    two_anchors = copy.deepcopy(grid)
    two_anchors[0][0] = 9

    mixed_color = copy.deepcopy(grid)
    motif_row, motif_col = info["motif_cells"][0]
    mixed_color[motif_row][motif_col] = 5

    disconnected = copy.deepcopy(grid)
    disconnected[0][0] = info["motif_color"]

    symmetric = copy.deepcopy(grid)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            symmetric[row][col] = info["motif_color"]

    crosses_axis = copy.deepcopy(grid)
    crosses_axis[anchor_row][c0] = info["motif_color"]

    impostors = {
        "missing anchor": no_anchor,
        "duplicate anchor": two_anchors,
        "mixed motif color": mixed_color,
        "disconnected same-color distractor": disconnected,
        "reflection-symmetric motif": symmetric,
        "motif crosses anchor axis": crosses_axis,
    }
    for label, impostor in impostors.items():
        assert gen.self_check(impostor), label
        assert gen.strict_canonical_like(impostor), label


def test_af72e426e241_deterministic_fresh_and_global_rng_pure():
    random.seed(20260726)
    before = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    after = random.getstate()
    second = gen.generate(123, 456, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[0][0] = 9
    assert second[0][0] == 0
