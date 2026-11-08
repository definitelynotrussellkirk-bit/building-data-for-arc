from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

from arc_repl.grid_ops import find_objects

TASK_ID = "4629b6d55040"
ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    override = os.environ.get("GENERATOR_UNDER_TEST")
    if not override:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    path = Path(override)
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task row not found")


def _independent_rule(grid):
    components = sorted(find_objects(grid, bg=0, connectivity=4), key=lambda obj: obj["size"])
    crops = []
    for component in components:
        r1, c1, r2, c2 = component["bbox"]
        crops.append([row[c1:c2 + 1] for row in grid[r1:r2 + 1]])
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for crop in crops:
        top = (height - len(crop)) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value:
                    output[top + r][left + c] = value
        left += len(crop[0]) + 1
    return output


def test_rule_hash_version_and_override_surface_are_pinned():
    assert mod.RULE_HASH == "036057069849"
    assert mod.VERSION == "2.0.0"
    assert set(mod.AXES) == {"n_blobs"}


def test_all_canonical_pairs_are_accepted_and_solved_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert mod.self_check(source) == []
        assert mod.strict_canonical_like(source) == []
        assert mod.rule_mirror(source) == pair["output"]
        assert _independent_rule(source) == pair["output"]
        assert source == pair["input"]


def test_override_axis_is_consumed_and_exactly_observable():
    for band in ("easy", "medium", "hard"):
        for n_blobs in (3, 4, 5):
            grid = mod.generate(
                9137,
                1,
                difficulty=band,
                n_blobs=n_blobs,
            )
            assert mod.self_check(grid) == []
            assert mod.observe_overrides(grid) == {"n_blobs": n_blobs}
            assert len(find_objects(grid, bg=0, connectivity=4)) == n_blobs


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        mod.generate(1, 1, palette_kind="warm")
    with pytest.raises(ValueError, match="3..5"):
        mod.generate(1, 1, n_blobs=2)
    with pytest.raises(ValueError, match="3..5"):
        mod.generate(1, 1, n_blobs=6)


def test_generated_scenes_rebut_core_shortcuts():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = mod.generate(20260725, sample_index, difficulty=band)
            assert mod.self_check(grid) == []
            assert mod.rule_mirror(grid) == _independent_rule(grid)
            assert all(predicate(grid) for predicate in mod.SEMANTIC_WITNESSES.values()) or (
                # Only the exact canonical anchor is intentionally scheduled one
                # sample in four; every other semantic witness is universal.
                not mod.SEMANTIC_WITNESSES["exact_canonical_profile_anchor"](grid)
                and all(
                    predicate(grid)
                    for name, predicate in mod.SEMANTIC_WITNESSES.items()
                    if name != "exact_canonical_profile_anchor"
                )
            )


def test_generated_scenes_make_vertical_centering_answer_observable():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = mod.generate(24681357, sample_index, difficulty=band)
            assert mod._competitor_top_aligned(grid) != mod.rule_mirror(grid)
            assert mod.SEMANTIC_WITNESSES[
                "unequal_crop_heights_require_vertical_centering"
            ](grid)


def test_four_sample_lessons_are_identifiable_across_schedule_offsets():
    for start in range(8):
        pairs = []
        for sample_index in range(start, start + 4):
            inp = mod.generate(8675309, sample_index, difficulty="medium")
            pairs.append({"input": inp, "output": _independent_rule(inp)})
        assert mod.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_determinism_fresh_returns_rule_purity_and_global_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = mod.generate(44, 7, difficulty="hard", n_blobs=5)
    assert random.getstate() == state
    second = mod.generate(44, 7, difficulty="hard", n_blobs=5)
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    original = copy.deepcopy(second)
    result = mod.rule_mirror(second)
    assert second == original
    assert result == _independent_rule(second)

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == mod.generate(44, 7, difficulty="hard", n_blobs=5)


def test_self_check_rejects_tied_sizes_sorted_order_and_touching_objects():
    tied = [[0] * 8 for _ in range(8)]
    tied[0][0:3] = [1, 1, 1]
    tied[3][0:3] = [2, 2, 2]
    tied[6][0:4] = [3, 3, 3, 3]
    assert any("strictly distinct" in error for error in mod.self_check(tied))

    sorted_order = [[0] * 10 for _ in range(10)]
    sorted_order[0][0:3] = [1, 1, 1]
    sorted_order[3][0:4] = [2, 2, 2, 2]
    sorted_order[6][0:5] = [3, 3, 3, 3, 3]
    assert any("already area-sorted" in error for error in mod.self_check(sorted_order))

    touching = [[0] * 10 for _ in range(10)]
    touching[0][0:3] = [1, 1, 1]
    touching[1][0:4] = [2, 2, 2, 2]
    touching[6][0:5] = [3, 3, 3, 3, 3]
    assert any("must not touch" in error for error in mod.self_check(touching))
