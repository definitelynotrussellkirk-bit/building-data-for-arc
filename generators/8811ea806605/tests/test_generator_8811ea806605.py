"""Focused semantic regressions for ARC generator 8811ea806605."""
from __future__ import annotations

from collections import defaultdict
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import shutil

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application


ROOT = Path(__file__).resolve().parents[1]
TASK = "8811ea806605"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATH = ROOT / "data/base/solutions/banks/6bdef6f37fa3/S7_E2__8811ea806605.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _normalized_grid(grid) -> list[list[int]]:
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {
            "input": _normalized_grid(pair["input"]),
            "output": _normalized_grid(pair["output"]),
        }
        for pair in list(row["train"]) + list(test)
    ]


def _frozen(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _column_counts(grid) -> tuple[int, ...]:
    return tuple(sum(row[col] == 1 for row in grid) for col in range(len(grid[0])))


def _canonical_like(grid) -> bool:
    h, w = len(grid), len(grid[0])
    counts = _column_counts(grid)
    positive = [count for count in counts if count]
    rows_used = {row for row, values in enumerate(grid) if 1 in values}
    return (
        h in (6, 7)
        and w in (6, 7, 8)
        and sum(count > 0 for count in counts) >= w - 1
        and max(counts) == 2
        and set(positive) <= {1, 2}
        and w <= sum(counts) <= w + 2
        and len(rows_used) >= 4
        and MODULE._gravity_output(grid) != grid
    )


def test_rule_authorities_and_normalized_hash_are_exactly_synchronized():
    canonical_source = _canonical_row()["program_solution"]
    base_source = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]["target_code"]
    normalized = " ".join(canonical_source.split())
    assert canonical_source == base_source
    assert MODULE.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == "85a21a74f703"


def test_all_public_pairs_are_accepted_and_the_independent_mirror_is_exact_and_pure():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert MODULE._gravity_output(source) == pair["output"]
        assert MODULE.canonical_profile_signature(source) is not None
        assert source == snapshot


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_rule_matches_all_pairs_is_atomic_and_executes_rejected_recombinations():
    source = _canonical_row()["program_solution"]
    pairs = _pairs()
    bridge = RacketBridge()
    try:
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot

        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]

        foreign = copy.deepcopy(pairs[0]["input"])
        row, col = next(
            (r, c)
            for r, values in enumerate(foreign)
            for c, value in enumerate(values)
            if value == 1
        )
        foreign[row][col] = 2
        assert MODULE.self_check(foreign)
        output = bridge.eval_text(rule_application(source, foreign))
        assert len(output) == len(foreign)
        assert all(len(out_row) == len(foreign[0]) for out_row in output)
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 5),
        ("grid_h", 12),
        ("grid_w", 5),
        ("grid_w", 14),
        ("active_cols", 4),
        ("active_cols", 14),
        ("max_stack", 2),
        ("max_stack", 4),
    ],
)
def test_each_declared_axis_boundary_is_realizable_and_observable(axis, value, band):
    grid = MODULE.generate(771, 991, difficulty=band, **{axis: value})
    assert MODULE.self_check(grid, difficulty=band, meta={"overrides": {axis: value}}) == []
    if axis == "grid_h":
        assert len(grid) == value
    elif axis == "grid_w":
        assert len(grid[0]) == value
    else:
        assert MODULE.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_linked_boundary_vectors_are_exact_and_impossible_combinations_fail_loudly(band):
    for overrides in (
        {"grid_h": 5, "grid_w": 5, "active_cols": 4, "max_stack": 2},
        {"grid_h": 12, "grid_w": 14, "active_cols": 14, "max_stack": 4},
    ):
        grid = MODULE.generate(123, 456, difficulty=band, **overrides)
        assert (len(grid), len(grid[0])) == (overrides["grid_h"], overrides["grid_w"])
        assert MODULE.observe_overrides(grid) == {
            "active_cols": overrides["active_cols"],
            "max_stack": overrides["max_stack"],
        }
        assert MODULE.self_check(grid) == []

    with pytest.raises(ValueError, match="active_cols"):
        MODULE.generate(1, 2, difficulty=band, grid_w=5, active_cols=14)
    with pytest.raises(ValueError, match="max_stack"):
        MODULE.generate(1, 2, difficulty=band, grid_h=5, max_stack=5)


def test_unknown_control_values_fail_closed():
    with pytest.raises(ValueError, match="unknown difficulty"):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(0, 0, invented_axis=1)


def test_generation_is_deterministic_fresh_mutation_safe_and_global_rng_independent():
    random.seed(987654321)
    state = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]

    frozen = _frozen(second)
    first[0][0] = 1 - first[0][0]
    assert _frozen(MODULE.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(MODULE.generate(seed, 17, difficulty="medium")) for seed in range(12)}
    by_index = {_frozen(MODULE.generate(17, index, difficulty="medium")) for index in range(12)}
    assert len(by_seed) >= 10
    assert len(by_index) >= 10


def test_self_check_rejects_structural_impostors_noops_and_foreign_colors_without_mutation():
    valid = MODULE.generate(424242, 11, difficulty="medium")
    h, w = len(valid), len(valid[0])
    cases = {
        "all_background": [[0] * w for _ in range(h)],
        "full_one_color": [[1] * w for _ in range(h)],
        "singleton": [[1 if (r, c) == (h // 2, w // 2) else 0 for c in range(w)] for r in range(h)],
        "solid_2x2": [
            [1 if h // 2 - 1 <= r <= h // 2 and w // 2 - 1 <= c <= w // 2 else 0 for c in range(w)]
            for r in range(h)
        ],
        "short_line": [[1 if r == h // 2 and 1 <= c <= min(w - 2, 4) else 0 for c in range(w)] for r in range(h)],
        "already_packed": MODULE._gravity_output(valid),
    }
    foreign = copy.deepcopy(valid)
    foreign[0][0] = 2
    cases["foreign_color"] = foreign

    for grid in cases.values():
        snapshot = copy.deepcopy(grid)
        assert MODULE.self_check(grid)
        assert grid == snapshot

    assert MODULE.self_check([])
    assert MODULE.self_check([[0, 1], [0]])
    assert MODULE.self_check([[True] * 5 for _ in range(5)])


def test_equal_histograms_ignore_source_rows_but_equal_totals_do_not_define_the_answer():
    same_hist_a = [
        [1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    same_hist_b = [
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert _column_counts(same_hist_a) == _column_counts(same_hist_b)
    assert MODULE.self_check(same_hist_a) == MODULE.self_check(same_hist_b) == []
    assert MODULE._gravity_output(same_hist_a) == MODULE._gravity_output(same_hist_b)

    histogram_a = [
        [1, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    histogram_b = [
        [1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert sum(_column_counts(histogram_a)) == sum(_column_counts(histogram_b)) == 6
    assert _column_counts(histogram_a) != _column_counts(histogram_b)
    assert MODULE.self_check(histogram_a) == MODULE.self_check(histogram_b) == []
    assert MODULE._gravity_output(histogram_a) != MODULE._gravity_output(histogram_b)


def test_disjoint_default_census_covers_canonical_and_anti_shortcut_branches():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = []
        histogram_groups: dict[int, set[tuple[int, ...]]] = defaultdict(set)
        for offset in range(200):
            seed = 300_000 + 10_000 * band_index + offset
            grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
            assert MODULE.self_check(grid) == []
            counts = _column_counts(grid)
            histogram_groups[sum(counts)].add(counts)
            grids.append(grid)

        canonical_count = sum(_canonical_like(grid) for grid in grids)
        bottom_count = sum(1 in grid[-1] for grid in grids)
        all_active = sum(all(count > 0 for count in _column_counts(grid)) for grid in grids)
        has_empty = sum(any(count == 0 for count in _column_counts(grid)) for grid in grids)
        count_four = sum(4 in _column_counts(grid) for grid in grids)

        assert canonical_count >= 40
        assert 60 <= bottom_count <= 140
        assert all_active >= 30 and has_empty >= 30
        assert sum(len(group) >= 2 for group in histogram_groups.values()) >= 8
        assert len({_frozen(grid) for grid in grids}) >= 195
        assert len({_frozen(MODULE._gravity_output(grid)) for grid in grids}) >= 190
        if band == "hard":
            assert count_four >= 40
