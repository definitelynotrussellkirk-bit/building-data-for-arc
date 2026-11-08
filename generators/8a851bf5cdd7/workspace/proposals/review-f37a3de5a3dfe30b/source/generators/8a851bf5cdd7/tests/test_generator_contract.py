"""Canonical generator regressions for 8a851bf5cdd7."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_generator_8a851bf5cdd7_contract", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _panels(grid):
    h, w = len(grid), len(grid[0])
    pw = (w - 2) // 3
    return [
        [[grid[r][p * (pw + 1) + c] for c in range(pw)] for r in range(h)]
        for p in range(3)
    ]


def _edit_counts(grid):
    a, b, _ = _panels(grid)
    additions = sum(a[r][c] == 0 and b[r][c] != 0 for r in range(len(a)) for c in range(len(a[0])))
    deletions = sum(a[r][c] != 0 and b[r][c] == 0 for r in range(len(a)) for c in range(len(a[0])))
    return additions, deletions


def _visible_counts(grid):
    a, b, c = _panels(grid)
    additions = sum(
        a[r][col] == 0 and b[r][col] != 0 and c[r][col] == 0
        for r in range(len(a)) for col in range(len(a[0]))
    )
    deletions = sum(
        a[r][col] != 0 and b[r][col] == 0 and c[r][col] != 0
        for r in range(len(a)) for col in range(len(a[0]))
    )
    return additions, deletions


def _nonseparator_colors(grid):
    return {cell for row in grid for cell in row if cell not in (0, 8)}


def _canonical_inputs():
    from reviewer_support import canonical_path, find_root

    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    record = next(row for row in rows if row["task_id"] == gen.TASK_ID)
    pairs = list(record["train"])
    test = record["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return [pair["input"] for pair in pairs]


def test_original_inputs_remain_in_domain():
    assert len(_canonical_inputs()) >= 3
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_unknown_and_invalid_declared_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="palette_size"):
        gen.generate(1, 0, palette_size=2)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_unlabelable_no_separator_branch_is_not_generated():
    assert "no_separator" not in gen.AXES["texture"]["valid"]
    with pytest.raises(ValueError, match="texture"):
        gen.generate(0, 0, difficulty="easy", texture="no_separator")


def test_self_check_is_total_on_ragged_and_noninteger_grids():
    assert gen.self_check([[8, 0, 8], [8]])
    assert gen.self_check([[0, 8, 0], [0, True, 0]])
    assert gen.self_check([])


def test_variant_override_controls_exact_edit_cardinality():
    counts = []
    grids = []
    for variant in range(3):
        grid = gen.generate(314159, 7, difficulty="medium", variant=variant)
        assert gen.self_check(grid) == []
        grids.append(grid)
        counts.append(_edit_counts(grid))
    assert counts == [(1, 1), (2, 2), (3, 3)]
    assert len({json.dumps(grid) for grid in grids}) == 3


def test_palette_controls_are_observable_and_texture_is_an_alias():
    warm = gen.generate(2026, 4, palette_kind="warm", variant=1)
    cool = gen.generate(2026, 4, palette_kind="cool", variant=1)
    assert warm != cool
    assert _nonseparator_colors(warm) != _nonseparator_colors(cool)
    assert gen.generate(2026, 4, texture="warm", variant=1) == warm
    with pytest.raises(ValueError, match="conflicting"):
        gen.generate(2026, 4, palette_kind="cool", texture="warm")


def test_known_identity_witness_now_has_visible_addition_and_deletion():
    grid = gen.generate(1006, 6, difficulty=None)
    assert gen.self_check(grid) == []
    visible_additions, visible_deletions = _visible_counts(grid)
    assert visible_additions >= 1
    assert visible_deletions >= 1


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(987654)
    state = random.getstate()
    first = gen.generate(88, 5, difficulty="hard", variant=2, palette_kind="varied")
    assert random.getstate() == state
    second = gen.generate(88, 5, difficulty="hard", variant=2, palette_kind="varied")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
