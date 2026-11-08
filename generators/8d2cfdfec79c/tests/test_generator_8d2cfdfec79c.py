"""Focused regressions for the opposite-corner rectangle-border sampler."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "8d2cfdfec79c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
SPEC = importlib.util.spec_from_file_location("reviewed_rectangles", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                source = " ".join(str(row["program_solution"]).split())
                return hashlib.sha256(source.encode()).hexdigest()[:12]
    raise AssertionError("canonical rule missing")


def _nonzero_counts(grid):
    return Counter(value for row in grid for value in row if value)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_and_all_canonical_pairs_are_owned_and_mirrored():
    assert GEN.RULE_HASH == _canonical_rule_hash() == "23e27bc62b89"
    assert len(CANONICAL) == 5
    for pair in CANONICAL:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._predict(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(8, 10), (8, 14), (13, 10), (13, 14)])
@pytest.mark.parametrize("rectangles", [2, 3, 4])
@pytest.mark.parametrize("layout_kind", ["disjoint", "nested", "crossing"])
def test_full_override_domain_is_constructive_and_pixel_observable(
    band, shape, rectangles, layout_kind
):
    h, w = shape
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        rectangles=rectangles,
        layout_kind=layout_kind,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "rectangles": rectangles,
        "layout_kind": layout_kind,
    }
    assert sorted(_nonzero_counts(grid).values()) == [2] * rectangles


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_h": 7},
        {"grid_w": 15},
        {"rectangles": 1},
        {"rectangles": 5},
        {"layout_kind": "other"},
    ],
)
def test_unknown_and_invalid_overrides_fail_closed(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


def test_crossing_scene_exposes_first_appearance_overwrite_semantics():
    grid = GEN.generate(
        17,
        1,
        grid_h=9,
        grid_w=12,
        rectangles=2,
        layout_kind="crossing",
    )
    intended = GEN._predict(grid)
    assert GEN.observe_overrides(grid)["layout_kind"] == "crossing"
    for name in ("reverse_order", "completion_order", "restore_clues"):
        assert GEN.LESSON_COMPETITORS[name](grid) != intended


def test_axis_defaults_describe_the_live_four_position_schedule():
    assert GEN.AXES["rectangles"]["default"] == "curriculum schedule 2,2,3,3"
    assert (
        GEN.AXES["layout_kind"]["default"]
        == "curriculum schedule crossing,disjoint,crossing,nested"
    )


def test_each_three_demo_default_window_refutes_every_declared_competitor():
    for band in ("easy", "medium", "hard"):
        demos = [GEN.generate(23, index, difficulty=band) for index in range(3)]
        expected = [GEN._predict(grid) for grid in demos]
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(grid) != answer for grid, answer in zip(demos, expected)), name


def test_each_band_retains_exact_canonical_profile_support():
    canonical_profiles = {_profile(pair["input"]) for pair in CANONICAL}
    for band in ("easy", "medium", "hard"):
        profiles = {
            _profile(GEN.generate(seed, seed % 7919 + index, difficulty=band))
            for index, seed in enumerate(range(20))
        }
        assert profiles & canonical_profiles


def test_validator_rejects_bad_multiplicity_collinearity_and_arc_values():
    singleton = [[0] * 10 for _ in range(8)]
    singleton[0][0] = 2
    singleton[2][2] = 4
    singleton[5][5] = 4
    assert GEN.self_check(singleton)

    collinear = [[0] * 10 for _ in range(8)]
    collinear[1][1] = collinear[1][7] = 2
    collinear[3][2] = collinear[6][8] = 4
    assert GEN.self_check(collinear)

    bad_value = [[0] * 10 for _ in range(8)]
    bad_value[1][1] = bad_value[5][5] = True
    bad_value[2][2] = bad_value[6][6] = 4
    assert GEN.self_check(bad_value)

@pytest.mark.parametrize("sample_index", [True, False, -1])
def test_sample_index_rejects_invalid_scalars(sample_index):
    with pytest.raises(ValueError):
        GEN.generate(0, sample_index)


def test_difficulty_bands_enter_default_sampling_without_changing_legality():
    grids = [GEN.generate(31, 4, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({tuple(map(tuple, grid)) for grid in grids}) == 3
    assert all(GEN.self_check(grid) == [] for grid in grids)

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_keeps_each_declared_rival_refuted(band):
    period = GEN.LESSON_SCHEDULE_PERIOD
    for start in range(period):
        lesson = [GEN.generate(101, start + offset, difficulty=band) for offset in range(4)]
        for query_index in range(4):
            train = [grid for index, grid in enumerate(lesson) if index != query_index]
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(grid) != GEN._predict(grid) for grid in train), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_retained_canonical_crossing_counterexample_stays_owned():
    path = HOME / "counterexamples" / "canonical_crossing_rectangles.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    grid = record["input"]
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["layout_kind"] == "crossing"
    assert GEN._predict(grid) == record["expected_output"]
