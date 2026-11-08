from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.a16e387b682a import generator as gen


REPO = Path(__file__).resolve().parents[1]


def _paint(grid, color, top, left):
    for r in range(top, top + 2):
        for c in range(left, left + 2):
            grid[r][c] = color


def _blank(h=10, w=10):
    return [[0 for _ in range(w)] for _ in range(h)]


def _canonical_row():
    for line in (REPO / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def test_rule_hash_matches_canonical():
    program = _canonical_row()["program_solution"]
    actual = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "f329ca8c8480"


def test_canonical_inputs_pass_self_check():
    row = _canonical_row()
    grids = [pair["input"] for split in ("train", "test") for pair in row[split]]
    assert len(grids) == 3
    assert [gen.self_check(grid) for grid in grids] == [[], [], []]


@pytest.mark.parametrize("h,w", [(8, 8), (8, 14), (14, 8), (14, 14)])
@pytest.mark.parametrize("rank", [0, 1, 2])
def test_boundary_overrides_are_exact_and_structural(h, w, rank):
    grid = gen.generate(41, 7, difficulty="easy", grid_h=h, grid_w=w, target_rank=rank)
    assert (len(grid), len(grid[0])) == (h, w)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"target_rank": rank}


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(20260723)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert first != second


def test_self_check_rejects_four_targeted_impostor_classes():
    two_objects = _blank()
    _paint(two_objects, 1, 1, 1)
    _paint(two_objects, 2, 7, 7)

    malformed_shape = _blank()
    _paint(malformed_shape, 1, 1, 1)
    _paint(malformed_shape, 2, 4, 4)
    _paint(malformed_shape, 3, 7, 7)
    malformed_shape[2][2] = 0

    touching_objects = _blank()
    _paint(touching_objects, 1, 1, 1)
    _paint(touching_objects, 2, 1, 3)
    _paint(touching_objects, 3, 7, 7)

    tied_minimum = _blank()
    _paint(tied_minimum, 4, 3, 2)
    _paint(tied_minimum, 6, 3, 6)
    _paint(tied_minimum, 2, 7, 4)

    output_color_present = _blank()
    _paint(output_color_present, 1, 1, 1)
    _paint(output_color_present, 2, 4, 4)
    _paint(output_color_present, 8, 7, 7)

    cases = {
        "wrong object count": two_objects,
        "non-solid 2x2": malformed_shape,
        "touching objects": touching_objects,
        "tied canonical minimum": tied_minimum,
        "output color already present": output_color_present,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_degenerate_textures_are_rejected_by_teaching_checker():
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, texture=texture)
        assert gen.self_check(grid), texture


def test_unknown_texture_rejects_loudly():
    with pytest.raises(ValueError, match="unknown texture"):
        gen.generate(0, 0, texture="not_a_texture")
