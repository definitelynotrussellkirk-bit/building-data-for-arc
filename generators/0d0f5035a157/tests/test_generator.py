"""Regression tests for the row-wise stable left-compaction sampler."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

TASK_ID = "0d0f5035a157"
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
    try:
        from reviewer_support import canonical_pairs, find_root
    except ImportError:
        root = HOME.parents[1]
        with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
            rows = [
                json.loads(line)
                for line in handle
                if json.loads(line).get("task_id") == TASK_ID
            ]
        assert len(rows) == 1
        return [*rows[0]["train"], *rows[0]["test"]]
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _oracle(grid: list[list[int]]) -> list[list[int]]:
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def _has_dense_moved_row(grid: list[list[int]]) -> bool:
    for row in grid:
        positions = [index for index, value in enumerate(row) if value != 0]
        if len(positions) >= 5 and positions != list(range(len(positions))):
            return True
    return False


def test_metadata_pins_authority_and_declares_only_observable_axes():
    assert gen.RULE_HASH == "8b15a51d568d"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "palette_size",
        "max_cells_per_row",
        "n_empty_rows",
        "n_packed_rows",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert tuple(gen.HELPFUL_TEXTURES) == ()
    assert tuple(gen.DEGENERATE_TEXTURES) == ()


@pytest.mark.parametrize(
    "pair", _canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"]
)
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "expected",
    [
        {
            "grid_h": 5,
            "grid_w": 8,
            "palette_size": 1,
            "max_cells_per_row": 3,
            "n_empty_rows": 0,
            "n_packed_rows": 0,
        },
        {
            "grid_h": 10,
            "grid_w": 14,
            "palette_size": 9,
            "max_cells_per_row": 7,
            "n_empty_rows": 2,
            "n_packed_rows": 2,
        },
        {
            "grid_h": 6,
            "grid_w": 9,
            "palette_size": 8,
            "max_cells_per_row": 5,
            "n_empty_rows": 1,
            "n_packed_rows": 1,
        },
    ],
)
def test_exact_overrides_are_realized_in_every_band(band, expected):
    grid = gen.generate(913, 37, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert gen.rule_mirror(grid) == _oracle(grid)


def test_explicit_override_wins_over_dense_schedule():
    grid = gen.generate(19, 0, max_cells_per_row=3)
    assert gen.observe_overrides(grid)["max_cells_per_row"] == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 7},
        {"grid_w": 15},
        {"palette_size": 0},
        {"palette_size": 10},
        {"max_cells_per_row": 2},
        {"max_cells_per_row": 8},
        {"n_empty_rows": -1},
        {"n_empty_rows": 3},
        {"n_packed_rows": -1},
        {"n_packed_rows": 3},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"palette_size": "9"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


def test_default_schedule_is_deterministic_and_every_rotated_lesson_refutes_rival():
    for band in (None, "easy", "medium", "hard"):
        pairs = []
        for index in range(16):
            grid = gen.generate(700 + index, index, difficulty=band)
            assert grid == gen.generate(700 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == _oracle(grid)
            pairs.append({"input": grid, "output": _oracle(grid)})
        for start in range(13):
            window = pairs[start : start + 4]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                assert gen.lesson_identifiable(demos, window[query_index]) == []


def test_dense_schedule_and_named_rival_have_an_exact_counterexample():
    pairs = _canonical_pairs()
    for pair in pairs:
        assert gen.SEMANTIC_RIVALS["pack_at_most_four"](pair["input"]) == pair["output"]

    counterexample = [[0, 1, 0, 2, 0, 3, 4, 5]]
    intended = [[1, 2, 3, 4, 5, 0, 0, 0]]
    assert gen.rule_mirror(counterexample) == intended
    assert gen.SEMANTIC_RIVALS["pack_at_most_four"](counterexample) == counterexample

    for index in range(0, 20, 2):
        grid = gen.generate(1500 + index, index)
        assert _has_dense_moved_row(grid)
        assert gen.SEMANTIC_WITNESSES["dense_moved_row"](grid)
        assert gen.SEMANTIC_RIVALS["pack_at_most_four"](grid) != _oracle(grid)


@pytest.mark.parametrize(
    "malformed",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(5)]],
)
def test_self_check_reports_malformed_grids_without_raising(malformed):
    assert gen.self_check(malformed)


def test_self_check_rejects_noop_and_singleton_impostors():
    already_packed = [[1, 2, 3, 0, 0, 0, 0, 0] for _ in range(5)]
    singleton = [[0] * 8 for _ in range(5)]
    singleton[2][4] = 7
    assert gen.self_check(already_packed)
    assert gen.self_check(singleton)


def test_workspace_review_probe_is_source_bound_and_clean():
    probe_path = HOME / "workspace" / "review_probe.py"
    spec = importlib.util.spec_from_file_location("review_probe_0d0f5035a157", probe_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load review probe from {probe_path}")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(gen, _canonical_pairs(), seeds_per_band=2)
    assert report["status"] == "pass"
    assert report["canonical_shortcuts_checked"] == sorted(gen.CANONICAL_SHORTCUTS)
    assert report["lesson_competitors_checked"] == sorted(gen.LESSON_COMPETITORS)
    assert report["ambiguous_rotations"] == 0
    assert report["override_failures"] == []
