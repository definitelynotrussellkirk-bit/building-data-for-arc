"""Focused regression tests for generator 24d677c76640."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base

REPO_ROOT = Path(__file__).resolve().parents[1]
gen = importlib.import_module("puzzle_generators.per_puzzle.24d677c76640.generator")


def _canonical_row():
    with (REPO_ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _clear_anchor(grid):
    out = copy.deepcopy(grid)
    for row in range(len(out)):
        for col in range(len(out[0])):
            if out[row][col] == 1:
                out[row][col] = 0
    return out


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    for pair in list(row["train"]) + [row["test"]]:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_every_exact_axis_boundary_and_relation_is_observable():
    for band in ("easy", "medium", "hard"):
        for height, width in ((7, 7), (7, 12), (12, 7), (12, 12)):
            for shape_id in range(len(gen.SHAPES)):
                for relation in gen.RELATIONS:
                    grid = gen.generate(
                        1000 + shape_id,
                        2000 + height + width,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        shape_id=shape_id,
                        shape_color=2 if shape_id % 2 == 0 else 9,
                        anchor_relation=relation,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "shape_id": shape_id,
                        "shape_color": 2 if shape_id % 2 == 0 else 9,
                        "anchor_relation": relation,
                    }


def test_default_keyed_axes_match_returned_grid():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(30):
                grid = gen.generate(
                    30000 + band_index * 1000 + seed,
                    seed * 19 + 7,
                    difficulty=band,
                )
                ctx = captured[-1]
                expected = {name: ctx.axis_value(name) for name in gen.AXES}
                assert gen.observe_overrides(grid) == expected
    finally:
        generator_base.set_ctx_observer(None)


def test_four_pair_episode_schedule_covers_every_relation():
    observed = set()
    for seed in range(8):
        lesson_relations = {
            gen.observe_overrides(gen.generate(seed, sample_index))["anchor_relation"]
            for sample_index in range(4)
        }
        assert len(lesson_relations) == 4
        observed.update(lesson_relations)
    assert observed == set(gen.RELATIONS)


def test_determinism_fresh_returns_and_global_rng():
    random.seed(246776)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_impostors_are_rejected():
    base = gen.generate(
        901,
        77,
        difficulty="hard",
        grid_h=9,
        grid_w=9,
        shape_id=2,
        shape_color=4,
        anchor_relation="se",
    )
    analysis = gen._analysis(base)
    mutations = []

    no_anchor = _clear_anchor(base)
    mutations.append(no_anchor)

    two_anchors = copy.deepcopy(base)
    clear = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base[0]))
        if base[row][col] == 0
    )
    two_anchors[clear[0]][clear[1]] = 1
    mutations.append(two_anchors)

    no_shape = copy.deepcopy(base)
    for row, col in analysis["shape_cells"]:
        no_shape[row][col] = 0
    mutations.append(no_shape)

    multicolor = copy.deepcopy(base)
    row, col = next(iter(analysis["shape_cells"]))
    multicolor[row][col] = 7
    mutations.append(multicolor)

    disconnected = copy.deepcopy(base)
    row, col = next(iter(analysis["shape_cells"]))
    disconnected[row][col] = 0
    disconnected[0][0] = 4
    mutations.append(disconnected)

    identity = _clear_anchor(base)
    top, left, _, _ = analysis["source_bbox"]
    assert identity[top][left] == 0  # canonical plus has an empty bbox corner
    identity[top][left] = 1
    mutations.append(identity)

    clipped = _clear_anchor(base)
    clipped[-1][-1] = 1
    mutations.append(clipped)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_absent_color_recombination_is_distribution_invalid():
    grid = gen.generate(
        333,
        444,
        difficulty="medium",
        shape_id=10,
        shape_color=3,
        anchor_relation="nw",
    )
    analysis = gen._analysis(grid)
    replacement = next(color for color in range(2, 10) if color not in {1, 3})
    recombined = copy.deepcopy(grid)
    row, col = next(iter(analysis["shape_cells"]))
    recombined[row][col] = replacement
    assert replacement not in {
        value
        for r, values in enumerate(grid)
        for c, value in enumerate(values)
        if (r, c) != (row, col)
    }
    assert gen.self_check(recombined)


def test_invalid_calls_reject_loudly():
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError):
        gen.generate(1, 1, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 1, shape_id=12)
    with pytest.raises(ValueError):
        gen.generate(1, 1, anchor_relation="inside")
