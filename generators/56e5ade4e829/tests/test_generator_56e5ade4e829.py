"""Task-local regressions for 56e5ade4e829.

Expected outputs and observations come from ``workspace/reference_probe.py``,
which re-derives the rule without importing production geometry helpers.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "56e5ade4e829"
ROOT = find_root(__file__)
HOME = next(
    path
    for path in (
        ROOT / "generators" / TASK,
        ROOT / "puzzle_generators" / "per_puzzle" / TASK,
    )
    if (path / "generator.py").is_file()
)
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    control,
    geometry_output,
    ignore_intersection_marker,
    marker,
    observed,
)

SPEC = importlib.util.spec_from_file_location("reviewed_56e5ade4e829_tests", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK, root=ROOT, labeled_only=True)
CANONICAL_DIMS = {(8, 10), (8, 11), (9, 12), (9, 13), (10, 12)}


def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row["program_solution"]
    raise AssertionError("canonical row missing")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": geometry_output(grid)}


def test_rule_pin_canonical_ownership_and_independent_oracle():
    expected_hash = hashlib.sha256(
        " ".join(_canonical_program().split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash == "b85aae646e78"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert geometry_output(pair["input"]) == pair["output"]
        assert GEN.oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_selected_active_target_text_matches_canonical_when_repository_copy_is_present():
    authority = (
        ROOT
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "banks"
        / "e00836ab832d"
        / "H133__56e5ade4e829.json"
    )
    if not authority.is_file():
        pytest.skip("portable task runtime omits repository authority archive")
    row = json.loads(authority.read_text(encoding="utf-8"))
    assert row["racket_target"]["target_code"] == _canonical_program()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(8, 10), (10, 13)])
@pytest.mark.parametrize("ctrl", [0, 1, 2])
@pytest.mark.parametrize("relation", ["partial", "subset"])
def test_every_advertised_exact_override_is_constructive_and_observable(
    band, height, width, ctrl, relation
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "ctrl": ctrl,
        "relation": relation,
    }
    grid = GEN.generate(413, 29, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"__unknown_axis__": 1},
        {"grid_h": 7}, {"grid_h": 11}, {"grid_h": True}, {"grid_h": 8.0},
        {"grid_w": 9}, {"grid_w": 14}, {"grid_w": False},
        {"ctrl": -1}, {"ctrl": 3}, {"ctrl": True}, {"ctrl": "1"},
        {"relation": "identical"}, {"relation": True},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3, 0.5])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_none_override_uses_shared_unset_convention(band):
    baseline = GEN.generate(22, 7, difficulty=band)
    for key in GEN.AXES:
        assert GEN.generate(22, 7, difficulty=band, **{key: None}) == baseline


@pytest.mark.parametrize("band_index,band", enumerate(["easy", "medium", "hard"]))
def test_control_schedule_does_not_alias_when_seed_and_index_advance_together(band_index, band):
    controls = {
        observed(
            GEN.generate(
                70_001 + 1000 * band_index + index,
                17 * index + 5,
                difficulty=band,
            )
        )["ctrl"]
        for index in range(18)
    }
    assert controls == {0, 1, 2}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_defaults_are_strict_reproducible_diverse_and_cover_every_branch(band):
    controls = set()
    relations = set()
    xor_markers = set()
    inputs = set()
    outputs = set()
    for index in range(120):
        seed = 9000 + index
        sample_index = 13 * index + 1
        grid = GEN.generate(seed, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert grid == GEN.generate(seed, sample_index, difficulty=band)
        assert (len(grid), len(grid[0])) in CANONICAL_DIMS
        stats = observed(grid)
        controls.add(stats["ctrl"])
        relations.add(stats["relation"])
        if stats["ctrl"] == 0:
            xor_markers.add(marker(grid))
        inputs.add(repr(grid))
        outputs.add(repr(geometry_output(grid)))
    assert controls == {0, 1, 2}
    assert relations == {"partial", "subset"}
    assert xor_markers >= {5, 6, 7, 8, 9}
    assert len(inputs) >= 115
    assert len(outputs) >= 90


def test_canonical_shortcut_is_real_and_generated_intersection_refutes_it():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"ignore_intersection_marker"}
    assert all(
        ignore_intersection_marker(pair["input"]) == pair["output"]
        for pair in PAIRS
    )
    grid = GEN.generate(314159, 7, ctrl=1, relation="partial")
    assert control(grid) == 1
    assert geometry_output(grid) != ignore_intersection_marker(grid)
    assert GEN.SEMANTIC_WITNESSES["intersection_marker_counterexample"](grid)
    assert (
        GEN.SEMANTIC_RIVALS["ignore_intersection_marker"](grid)
        == ignore_intersection_marker(grid)
    )
    assert GEN.WITNESS_RIVALS["intersection_marker_counterexample"] == [
        "ignore_intersection_marker"
    ]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_and_every_query_rotation_is_identifiable(band):
    assert GEN.EXAMPLES_NEEDED == 5
    for seed in (97, 98, 99):
        for start in range(9):
            lesson = [
                _pair(GEN.generate(seed, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(lesson):
                demos = [pair for i, pair in enumerate(lesson) if i != query_index]
                assert {control(pair["input"]) for pair in demos} == {0, 1, 2}
                assert GEN.lesson_identifiable(demos, query) == []
                assert any(
                    ignore_intersection_marker(pair["input"]) != pair["output"]
                    for pair in demos
                )


def test_same_geometry_has_three_distinct_control_outputs():
    grids = [
        GEN.generate(
            7001,
            11,
            grid_h=9,
            grid_w=12,
            ctrl=ctrl,
            relation="subset",
        )
        for ctrl in (0, 1, 2)
    ]
    assert [observed(grid)["ctrl"] for grid in grids] == [0, 1, 2]
    # Non-control pixels are identical because geometry has its own keyed RNG.
    stripped = [
        [[0 if value not in (0, 1, 2) else value for value in row] for row in grid]
        for grid in grids
    ]
    assert stripped[0] == stripped[1] == stripped[2]
    assert len({repr(geometry_output(grid)) for grid in grids}) == 3


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_color",
        "extra_marker",
        "erase_marker",
        "disconnect_color_1",
        "remove_color_2",
        "touch_bounding_boxes",
        "make_shapes_identical",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = GEN.generate(
        31,
        8,
        grid_h=10,
        grid_w=13,
        ctrl=1,
        relation="partial",
    )
    if mutation == "unknown_color":
        target = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0)
        grid[target[0]][target[1]] = 10
    elif mutation == "extra_marker":
        target = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0)
        grid[target[0]][target[1]] = 5
    elif mutation == "erase_marker":
        for row in grid:
            for c, value in enumerate(row):
                if value not in (0, 1, 2):
                    row[c] = 0
    elif mutation == "disconnect_color_1":
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
        r, c = cells[-1]
        grid[r][c] = 0
        target = next(
            (rr, cc)
            for rr, row in enumerate(grid)
            for cc, value in enumerate(row)
            if value == 0 and all(abs(rr-r0) + abs(cc-c0) > 1 for r0, c0 in cells[:-1])
        )
        grid[target[0]][target[1]] = 1
    elif mutation == "remove_color_2":
        for row in grid:
            for c, value in enumerate(row):
                if value == 2:
                    row[c] = 0
    elif mutation == "touch_bounding_boxes":
        one = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
        two = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
        left, right = (one, two) if max(c for _, c in one) < min(c for _, c in two) else (two, one)
        color = grid[right[0][0]][right[0][1]]
        row, col = min(right, key=lambda point: point[1])
        for cc in range(max(c for _, c in left) + 1, col):
            grid[row][cc] = color
    elif mutation == "make_shapes_identical":
        one = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
        top = min(r for r, _ in one)
        left = min(c for _, c in one)
        normalized = {(r - top, c - left) for r, c in one}
        marker_cell = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value not in (0, 1, 2)
        )
        for row in grid:
            for c, value in enumerate(row):
                if value == 2:
                    row[c] = 0
        placed = False
        for r0 in range(len(grid)):
            for c0 in range(len(grid[0])):
                candidate = {(r0 + r, c0 + c) for r, c in normalized}
                if any(r >= len(grid) or c >= len(grid[0]) for r, c in candidate):
                    continue
                if marker_cell in candidate or candidate & one:
                    continue
                a = (min(r for r, _ in one), min(c for _, c in one),
                     max(r for r, _ in one), max(c for _, c in one))
                b = (min(r for r, _ in candidate), min(c for _, c in candidate),
                     max(r for r, _ in candidate), max(c for _, c in candidate))
                separated = (
                    a[2] + 1 < b[0] or b[2] + 1 < a[0]
                    or a[3] + 1 < b[1] or b[3] + 1 < a[1]
                )
                if separated:
                    for r, c in candidate:
                        grid[r][c] = 2
                    placed = True
                    break
            if placed:
                break
        assert placed
    assert GEN.self_check(grid), mutation


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 0]], [[True] * 10 for _ in range(8)],
     [[0.0] * 10 for _ in range(8)], [[0] * 9 for _ in range(7)]],
)
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list)
    assert errors
    assert all(isinstance(error, str) and error for error in errors)


def test_oracle_observer_and_validator_are_pure_and_global_rng_is_untouched():
    random.seed(20261005)
    state = random.getstate()
    grid = GEN.generate(77, 12, ctrl=1, relation="subset")
    original = copy.deepcopy(grid)
    GEN.oracle_output(grid)
    GEN.observe_overrides(grid)
    GEN.self_check(grid)
    assert grid == original
    assert random.getstate() == state
