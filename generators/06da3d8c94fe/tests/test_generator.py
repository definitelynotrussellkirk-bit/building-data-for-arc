"""Focused regression tests for five-panel operation inference."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_outputs_distinct,
    canonical_pairs,
    fixed_operation,
    independent_rule,
    infer_kind,
    load_generator,
    never_union,
    palette,
    panel_component_counts,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
KINDS = ("union", "intersection", "xor")


def test_rule_pin_and_all_canonical_pairs_are_owned():
    assert gen.RULE_HASH == "b01bd9f14dbe"
    pairs = canonical_pairs()
    assert [infer_kind(pair["input"]) for pair in pairs] == ["xor", "intersection", "union"]
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("panel_w", [3, 4, 5])
@pytest.mark.parametrize("grid_h", [4, 7, 10])
@pytest.mark.parametrize("kind", KINDS)
def test_every_exact_axis_override_is_observable_and_lawful(band, panel_w, grid_h, kind):
    grid = gen.generate(
        1701,
        29,
        difficulty=band,
        panel_w=panel_w,
        grid_h=grid_h,
        kind=kind,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "panel_w": panel_w,
        "grid_h": grid_h,
        "kind": kind,
    }
    assert infer_kind(grid) == kind
    assert independent_rule(grid) == gen.rule_mirror(grid)
    assert all_outputs_distinct(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"panel_w": 2},
        {"panel_w": 6},
        {"panel_w": True},
        {"panel_w": 4.0},
        {"panel_w": "4"},
        {"grid_h": 3},
        {"grid_h": 11},
        {"kind": "difference"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, sample_index)


@pytest.mark.parametrize("difficulty", ["novice", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=difficulty)


def test_six_draw_schedule_covers_each_operation_twice_and_all_profiles():
    expected_profiles = set(gen.SCHEDULE_PROFILES)
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(7000 + start, start + offset, difficulty=band) for offset in range(6)]
            assert Counter(infer_kind(grid) for grid in grids) == Counter({kind: 2 for kind in KINDS})
            assert {gen.schedule_profile(7000 + start, start + offset, band) for offset in range(6)} == expected_profiles


def test_canonical_profile_branch_has_exact_scale_palette_and_structure():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(0, 12, 2):
            grid = gen.generate(8000 + sample_index, sample_index, difficulty=band)
            assert (len(grid), len(grid[0]), len(palette(grid))) == (4, 24, 3)
            assert palette(grid) == {0, 2, 5}
            assert panel_component_counts(grid) == [1, 1, 1, 1, 1]
            assert gen.self_check(grid) == []


def test_every_rotation_of_six_draw_window_refutes_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            grids = [gen.generate(9100 + start, start + offset, difficulty=band) for offset in range(6)]
            pairs = [{"input": grid, "output": independent_rule(grid)} for grid in grids]
            for query_index in range(6):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for rival in gen.LESSON_COMPETITORS.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_witness_claims_are_real_query_counterexamples():
    for kind in KINDS:
        grid = gen.generate(12000, KINDS.index(kind), kind=kind)
        witness_name = f"{kind}_branch"
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        authority = independent_rule(grid)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != authority


def test_never_union_is_the_canonical_demo_shortcut_and_generated_union_refutes_it():
    pairs = canonical_pairs()
    assert all(never_union(pair["input"]) == pair["output"] for pair in pairs[:2])
    assert never_union(pairs[2]["input"]) != pairs[2]["output"]
    union_grid = gen.generate(13000, 0, kind="union")
    assert gen.SEMANTIC_RIVALS["never_union"](union_grid) == never_union(union_grid)
    assert never_union(union_grid) != independent_rule(union_grid)


def test_kind_override_changes_only_demo_result_for_same_draw():
    boards = {kind: gen.generate(14000, 17, panel_w=5, grid_h=8, kind=kind) for kind in KINDS}
    # p1,p2,p4,p5 and dividers stay byte-identical; only p3 identifies the operation.
    width = len(next(iter(boards.values()))[0])
    panel_w = (width - 4) // 5
    p3_cols = set(range(2 * (panel_w + 1), 2 * (panel_w + 1) + panel_w))
    for left_kind in KINDS:
        for right_kind in KINDS:
            for row_left, row_right in zip(boards[left_kind], boards[right_kind]):
                assert all(
                    value_left == value_right
                    for column, (value_left, value_right) in enumerate(zip(row_left, row_right))
                    if column not in p3_cols
                )


def test_self_check_rejects_ambiguous_or_malformed_inputs():
    grid = gen.generate(15000, 4, panel_w=4, grid_h=6, kind="union")
    width = len(grid[0])
    panel_w = (width - 4) // 5
    p3_left = 2 * (panel_w + 1)
    # Erase p3: it no longer matches the unique intended operation.
    for row in grid:
        for column in range(p3_left, p3_left + panel_w):
            row[column] = 0
    assert gen.self_check(grid)
    assert gen.self_check([])
    assert gen.self_check([[0], [0, 1]])
    assert gen.self_check([[True] * 24 for _ in range(4)])


def test_deterministic_and_input_pure():
    first = gen.generate(16000, 21, difficulty="hard")
    second = gen.generate(16000, 21, difficulty="hard")
    assert first == second
    snapshot = deepcopy(first)
    assert gen.rule_mirror(first) == independent_rule(first)
    assert first == snapshot


def test_retained_never_union_counterexample_is_reproducible():
    import json

    path = HOME / "counterexamples/never_union-shortcut.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    grid = data["input"]
    intended = independent_rule(grid)
    rival = never_union(grid)
    assert data["task_id"] == gen.TASK_ID
    assert data["shortcut"] == "never_union"
    assert gen.self_check(grid) == []
    assert infer_kind(grid) == "union"
    assert intended == data["intended_output"]
    assert rival == data["shortcut_output"]
    assert intended != rival
    assert data["differing_cells"] == [
        [row, column]
        for row in range(len(intended))
        for column in range(len(intended[0]))
        if intended[row][column] != rival[row][column]
    ]
