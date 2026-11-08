"""Focused regression tests for generator a7de0ceaa136."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.a7de0ceaa136 import generator as gen


def _canonical_inputs():
    path = Path(
        "data/base/solutions/banks/01130745873d/"
        "hard_141_decode_dual_code_library_and_center_stamp__a7de0ceaa136.json"
    )
    row = json.loads(path.read_text())
    samples = json.loads(row["visible_context"]["samples_text"])
    return [pair["input"] for split in ("train", "test") for pair in samples[split]]


def test_canonical_inputs_are_accepted():
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [0, len(gen._SOURCE_SHAPES) - 1])
@pytest.mark.parametrize("transform", [1, 6])
@pytest.mark.parametrize("palette_kind", gen.PALETTE_KINDS)
@pytest.mark.parametrize("prototype_slot", [0, 2])
def test_boundary_override_matrix_is_exact(
    difficulty, shape, transform, palette_kind, prototype_slot
):
    grid = gen.generate(
        9127,
        5,
        difficulty=difficulty,
        shape=shape,
        transform=transform,
        palette_kind=palette_kind,
        prototype_slot=prototype_slot,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "shape": shape,
        "transform": transform,
        "palette_kind": palette_kind,
        "prototype_slot": prototype_slot,
    }


def test_six_demo_schedule_covers_every_transform_and_library_slot():
    grids = [gen.generate(433, index, difficulty="medium") for index in range(6)]
    observations = [gen.observe_overrides(grid) for grid in grids]
    assert {row["transform"] for row in observations} == set(range(1, 7))
    assert {row["prototype_slot"] for row in observations} == {0, 1, 2}


def test_self_check_rejects_targeted_impostors():
    good = gen.generate(101, 2, difficulty="hard")

    all_background = [[0 for _ in row] for row in good]
    assert gen.self_check(all_background)

    missing_frame = copy.deepcopy(good)
    for r, row in enumerate(missing_frame):
        for c, value in enumerate(row):
            if value == 8:
                missing_frame[r][c] = 0
    assert gen.self_check(missing_frame)

    broken_frame = copy.deepcopy(good)
    frame = gen._analyze(broken_frame)["frame_bbox"]
    broken_frame[frame[0]][frame[1] + 2] = 0
    assert gen.self_check(broken_frame)

    output_collides = copy.deepcopy(good)
    output_collides[0][2] = output_collides[0][0]
    assert gen.self_check(output_collides)

    extra_object = copy.deepcopy(good)
    extra_object[6][5] = 9
    assert gen.self_check(extra_object)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(77, 4, difficulty="easy")
    after = random.getstate()
    second = gen.generate(77, 4, difficulty="easy")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[0][0] = 9
    assert second[0][0] != 9


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, shape=len(gen._SOURCE_SHAPES))
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(1, 0, palette_kind="neon")
