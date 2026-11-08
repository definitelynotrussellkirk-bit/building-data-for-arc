"""Task-local regression tests for the reviewed f4dc936dfcbb sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "f4dc936dfcbb"
HOME = Path(__file__).resolve().parents[1]
CANONICAL_PROFILES = {
    (8, 10, 4),
    (8, 11, 4),
    (9, 9, 4),
    (9, 12, 4),
    (10, 10, 4),
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_f4dc936dfcbb", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _spans(grid):
    h, w = len(grid), len(grid[0])
    row_spans = []
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 2]
        if len(cols) >= 2:
            row_spans.append((r, min(cols), max(cols)))
    col_spans = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 3]
        if len(rows) >= 2:
            col_spans.append((c, min(rows), max(rows)))
    return row_spans, col_spans


def intended_output(grid):
    """Independent Python oracle for the unchanged Racket rule."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    row_spans, col_spans = _spans(grid)
    for r, c0, c1 in row_spans:
        for c, r0, r1 in col_spans:
            if c0 <= c <= c1 and r0 <= r <= r1:
                out[r][c] = 8
    return out


def observed(grid):
    row_spans, col_spans = _spans(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_spans": len(row_spans),
        "n_col_spans": len(col_spans),
        "n_distractors": sum(
            value not in (0, 2, 3)
            for row in grid
            for value in row
        ),
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__), labeled_only=True),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_oracle_matches_outputs(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_contract_pins_authority_and_advertises_only_observable_controls():
    assert gen.RULE_HASH == "b804c88a8a55"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_row_spans",
        "n_col_spans",
        "n_distractors",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.SEMANTIC_RIVALS) == {
        "all_span_pairs",
        "horizontal_only",
        "vertical_only",
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_observable_and_deterministic(band):
    options = {
        "grid_h": 8,
        "grid_w": 9,
        "n_row_spans": 3,
        "n_col_spans": 3,
        "n_distractors": 4,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)
    assert len({value for row in grid for value in row}) == 4


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 19),
        ("grid_w", 8),
        ("grid_w", 21),
        ("n_row_spans", 0),
        ("n_row_spans", 4),
        ("n_col_spans", 0),
        ("n_col_spans", 4),
        ("n_distractors", 0),
        ("n_distractors", 5),
        ("grid_h", True),
        ("grid_w", 10.0),
        ("n_row_spans", "2"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_canonical_profile_support_diversity_and_teaching_witnesses(band):
    profiles = set()
    inputs = set()
    for index in range(80):
        grid = gen.generate(4100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        values = observed(grid)
        palette_size = len({value for row in grid for value in row})
        profiles.add((values["grid_h"], values["grid_w"], palette_size))
        inputs.add(tuple(tuple(row) for row in grid))
        assert gen.SEMANTIC_WITNESSES["horizontal_gate_rejection"](grid)
        assert gen.SEMANTIC_WITNESSES["vertical_gate_rejection"](grid)
    assert profiles & CANONICAL_PROFILES
    assert len(profiles) >= 10
    assert len(inputs) >= 76


def test_semantic_rivals_are_real_counterexamples_on_every_default_draw():
    for index in range(24):
        grid = gen.generate(712, index)
        expected = intended_output(grid)
        assert gen.SEMANTIC_WITNESSES["horizontal_gate_rejection"](grid)
        assert gen.SEMANTIC_WITNESSES["vertical_gate_rejection"](grid)
        for name, rival_fn in gen.SEMANTIC_RIVALS.items():
            rival = rival_fn(grid)
            assert rival != expected, name
            assert gen.LESSON_COMPETITORS[name](grid) == rival


def test_single_span_overrides_remain_constructive_without_claiming_rich_witnesses():
    grid = gen.generate(
        91,
        7,
        grid_h=8,
        grid_w=9,
        n_row_spans=1,
        n_col_spans=1,
        n_distractors=1,
    )
    assert gen.self_check(grid) == []
    assert observed(grid)["n_row_spans"] == 1
    assert observed(grid)["n_col_spans"] == 1
    assert sum(value == 8 for row in intended_output(grid) for value in row) == 1


def test_self_check_rejects_vacuity_ambiguous_markers_palette_drift_and_bad_values():
    base = gen.generate(
        91,
        7,
        grid_h=9,
        grid_w=12,
        n_row_spans=2,
        n_col_spans=2,
        n_distractors=2,
    )
    mutations = []

    no_rows = deepcopy(base)
    for row in no_rows:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    mutations.append(no_rows)

    no_cols = deepcopy(base)
    for row in no_cols:
        for c, value in enumerate(row):
            if value == 3:
                row[c] = 0
    mutations.append(no_cols)

    three_twos = deepcopy(base)
    row_index = next(r for r, row in enumerate(three_twos) if row.count(2) == 2)
    free_col = next(c for c, value in enumerate(three_twos[row_index]) if value == 0)
    three_twos[row_index][free_col] = 2
    mutations.append(three_twos)

    second_decor_color = deepcopy(base)
    r, c = next(
        (r, c)
        for r, row in enumerate(second_decor_color)
        for c, value in enumerate(row)
        if value == 0
    )
    used_decor = next(
        value for row in second_decor_color for value in row if value not in (0, 2, 3)
    )
    second_decor_color[r][c] = 1 if used_decor != 1 else 4
    mutations.append(second_decor_color)

    illegal_output_color = deepcopy(base)
    illegal_output_color[0][0] = 8
    mutations.append(illegal_output_color)

    ragged = deepcopy(base)
    ragged[-1] = ragged[-1][:-1]
    mutations.append(ragged)

    for grid in mutations:
        assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[False] * 9 for _ in range(8)]])
def test_self_check_reports_malformed_inputs_instead_of_raising(grid):
    assert gen.self_check(grid)
