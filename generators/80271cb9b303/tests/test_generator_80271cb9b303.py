from __future__ import annotations
from reviewer_support import find_root as _arc_review_root0, canonical_path as _arc_review_canonical0, load_selected_generator as _arc_review_generator0

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


gen = _arc_review_generator0('80271cb9b303', root=_arc_review_root0(__file__))[0]
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (_arc_review_canonical0(_arc_review_root0(__file__))).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical task row not found")


def _canonical_pairs():
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def test_rule_hash_canonical_acceptance_and_python_parity():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    actual_hash = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash == "4cb32d01d908"

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._solve_true(pair["input"]) == pair["output"]


def test_exact_axes_are_observable_at_both_boundaries():
    cases = (
        {
            "grid_h": 5,
            "grid_w": 14,
            "n_active_rows": 2,
            "period": 3,
            "cutoff_style": "partial",
            "leading_zero_style": "all_zero",
            "row_layout": "edge_split",
            "palette_size": 2,
            "palette_family": "canonical",
        },
        {
            "grid_h": 14,
            "grid_w": 22,
            "n_active_rows": 4,
            "period": 6,
            "cutoff_style": "mixed",
            "leading_zero_style": "mixed",
            "row_layout": "alternating",
            "palette_size": 4,
            "palette_family": "broad",
        },
    )
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(20260725, sample_index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []
        assert gen._solve_true(grid) != grid


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="full_grid")
    with pytest.raises(ValueError):
        gen.generate(1, 0, period=2)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_w=13)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(918273645)
    state = random.getstate()
    first = gen.generate(31, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(31, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(31, 7, difficulty="medium")


def test_self_check_rejects_targeted_periodic_impostors():
    valid = gen.generate(
        99,
        0,
        grid_h=8,
        grid_w=18,
        n_active_rows=3,
        period=4,
        cutoff_style="mixed",
        leading_zero_style="mixed",
        row_layout="bottom_block",
        palette_size=3,
        palette_family="canonical",
    )
    assert gen.self_check(valid) == []

    # 1. A completed row hides the extension branch.
    reaches_edge = gen._solve_true(valid)
    assert any("right edge" in error for error in gen.self_check(reaches_edge))

    # 2. Keeping only one row permits a fixed-row shortcut.
    one_row = copy.deepcopy(valid)
    active = gen._active_rows(one_row)
    for row_index in active[1:]:
        one_row[row_index] = [0] * len(one_row[row_index])
    assert any("2-4 active rows" in error for error in gen.self_check(one_row))

    # 3. A scalar constant prefix hides the multi-cell period.
    scalar = copy.deepcopy(valid)
    row_index = gen._active_rows(scalar)[0]
    right = max(c for c, value in enumerate(scalar[row_index]) if value != 0)
    scalar[row_index][: right + 1] = [2] * (right + 1)
    assert any("period 1" in error for error in gen.self_check(scalar))

    # 4. A cross-family color makes the palette-axis label false.
    mixed_palette = copy.deepcopy(valid)
    changed = False
    for row in mixed_palette:
        for col, value in enumerate(row):
            if value != 0:
                row[col] = 8
                changed = True
                break
        if changed:
            break
    assert any("palette families" in error for error in gen.self_check(mixed_palette))

    # 5. Move the three active rows to a layout outside all declared profiles.
    bad_layout = [[0] * len(valid[0]) for _ in valid]
    for source, target in zip(gen._active_rows(valid), (0, 2, 7)):
        bad_layout[target] = list(valid[source])
    assert any("row_layout" in error for error in gen.self_check(bad_layout))


def test_three_sample_lessons_refute_declared_competitors():
    for start in (0, 1, 2, 11, 22):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            input_grid = gen.generate(20260725, sample_index, difficulty="hard")
            pairs.append({"input": input_grid, "output": gen._solve_true(input_grid)})
        assert gen.lesson_identifiable(pairs[: gen.EXAMPLES_NEEDED], pairs[-1]) == []
        observed = [gen.observe_overrides(pair["input"]) for pair in pairs[:3]]
        assert {item["cutoff_style"] for item in observed} == {
            "aligned",
            "partial",
            "mixed",
        }
        assert {item["leading_zero_style"] for item in observed} == {
            "all_zero",
            "all_nonzero",
            "mixed",
        }
