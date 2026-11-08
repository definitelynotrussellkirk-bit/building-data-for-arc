"""Focused regressions for the 8f6a6ec3ae21 generator repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

TASK_ID = "8f6a6ec3ae21"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs, find_root

    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _oracle(grid: list[list[int]]) -> list[list[int]]:
    rows = [r for r in range(len(grid)) if grid[r][0] == 1]
    cols = [c for c in range(len(grid[0])) if grid[0][c] == 2]
    return [
        [8 if r in rows and c in cols else 0 for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def _is_gapped(values: list[int]) -> bool:
    return len(values) >= 2 and values[-1] - values[0] + 1 > len(values)


def test_metadata_pins_authority_and_advertises_only_observable_controls():
    assert gen.RULE_HASH == "ca6d5269f15c"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 2
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_marks_1",
        "n_marks_2",
        "n_row_decoys",
        "n_col_decoys",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 6,
            "grid_w": 7,
            "n_marks_1": 2,
            "n_marks_2": 2,
            "n_row_decoys": 0,
            "n_col_decoys": 0,
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "n_marks_1": 4,
            "n_marks_2": 4,
            "n_row_decoys": 1,
            "n_col_decoys": 1,
        },
        {
            "grid_h": 6,
            "grid_w": 12,
            "n_marks_1": 4,
            "n_marks_2": 3,
            "n_row_decoys": 1,
            "n_col_decoys": 1,
        },
    ],
)
def test_every_advertised_override_is_exact_and_constructive_in_every_band(band, overrides):
    grid = gen.generate(913, 37, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert gen.rule_mirror(grid) == _oracle(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 5},
        {"grid_h": 11},
        {"grid_w": 6},
        {"grid_w": 13},
        {"n_marks_1": 1},
        {"n_marks_1": 5},
        {"n_marks_2": True},
        {"n_marks_2": 2.0},
        {"n_row_decoys": -1},
        {"n_row_decoys": 2},
        {"n_col_decoys": "1"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


def test_default_distribution_is_deterministic_diverse_and_canonical_anchored_per_band():
    canonical_profiles = {(6, 8, 3), (6, 9, 3), (7, 9, 3)}
    for band in ("easy", "medium", "hard"):
        profiles = set()
        counts_1 = set()
        counts_2 = set()
        row_decoys = set()
        col_decoys = set()
        canonical_hits = 0
        unique = set()
        for index in range(96):
            grid = gen.generate(1700 + index, index, difficulty=band)
            assert grid == gen.generate(1700 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            obs = gen.observe_overrides(grid)
            profile = (obs["grid_h"], obs["grid_w"], len({v for row in grid for v in row}))
            profiles.add(profile[:2])
            counts_1.add(obs["n_marks_1"])
            counts_2.add(obs["n_marks_2"])
            row_decoys.add(obs["n_row_decoys"])
            col_decoys.add(obs["n_col_decoys"])
            canonical_hits += profile in canonical_profiles
            unique.add(tuple(tuple(row) for row in grid))
            assert obs["n_row_decoys"] + obs["n_col_decoys"] >= 1
        assert canonical_hits > 0
        assert counts_1 == {2, 3, 4}
        assert counts_2 == {2, 3, 4}
        assert row_decoys == {0, 1}
        assert col_decoys == {0, 1}
        assert len(profiles) >= 6
        assert len(unique) >= 80


def test_generated_marker_sets_are_gapped_and_role_decoys_are_semantically_effective():
    for index in range(128):
        grid = gen.generate(4200 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        rows = [r for r in range(1, len(grid)) if grid[r][0] == 1]
        cols = [c for c in range(1, len(grid[0])) if grid[0][c] == 2]
        assert _is_gapped(rows)
        assert _is_gapped(cols)
        official = _oracle(grid)
        assert gen.SEMANTIC_WITNESSES["cartesian_product"](grid)
        assert gen.SEMANTIC_WITNESSES["gapped_axes"](grid)
        assert gen.SEMANTIC_WITNESSES["clear_markers"](grid)
        assert gen.SEMANTIC_WITNESSES["role_specific_markers"](grid)
        for rival in gen.LESSON_COMPETITORS.values():
            assert rival(grid) != official


def test_any_nonzero_axis_shortcut_fits_canonical_but_every_default_draw_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["any_nonzero_axes"]
    assert rival is gen.SEMANTIC_RIVALS["any_nonzero_axes"]
    assert rival is gen.LESSON_COMPETITORS["any_nonzero_axes"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]
    for index in range(64):
        grid = gen.generate(7700 + index, index)
        assert rival(grid) != _oracle(grid)


def test_two_demo_lessons_rule_out_every_declared_competitor_for_rotated_queries():
    pairs = []
    for index in range(8):
        grid = gen.generate(8800, index, difficulty="medium")
        pairs.append({"input": grid, "output": _oracle(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index][: gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "mutation",
    [
        "origin",
        "body_color",
        "unknown_color",
        "too_few_marks",
        "too_many_decoys",
        "contiguous_rows",
        "contiguous_cols",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        51,
        7,
        grid_h=8,
        grid_w=9,
        n_marks_1=3,
        n_marks_2=3,
        n_row_decoys=1,
        n_col_decoys=1,
    )
    changed = deepcopy(grid)
    if mutation == "origin":
        changed[0][0] = 1
    elif mutation == "body_color":
        changed[-1][-1] = 1
    elif mutation == "unknown_color":
        changed[-1][-1] = 9
    elif mutation == "too_few_marks":
        for r in range(1, len(changed)):
            if changed[r][0] == 1:
                changed[r][0] = 0
                break
        for r in range(1, len(changed)):
            if changed[r][0] == 1:
                changed[r][0] = 0
                break
    elif mutation == "too_many_decoys":
        for c in range(1, len(changed[0])):
            if changed[0][c] == 0:
                changed[0][c] = 1
                break
    elif mutation == "contiguous_rows":
        for r in range(1, len(changed)):
            if changed[r][0] == 1:
                changed[r][0] = 0
        for r in (1, 2, 3):
            changed[r][0] = 1
        if changed[2][0] == 2:
            changed[2][0] = 1
    else:
        for c in range(1, len(changed[0])):
            if changed[0][c] == 2:
                changed[0][c] = 0
        for c in (1, 2, 3):
            changed[0][c] = 2
        if changed[0][2] == 1:
            changed[0][2] = 2
    assert gen.self_check(changed)


@pytest.mark.parametrize(
    "malformed",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(6)], [[0.0] * 8 for _ in range(6)]],
)
def test_self_check_reports_malformed_grids_without_raising(malformed):
    assert gen.self_check(malformed)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
