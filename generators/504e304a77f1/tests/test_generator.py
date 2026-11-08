"""Focused regression tests for the size-ranked frame assignment generator."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "504e304a77f1"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


@pytest.mark.parametrize("pair", _canonical())
def test_self_check_accepts_every_canonical_input(pair):
    assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_core_schedule_hits_canonical_profile_in_every_band(band):
    grid = GEN.generate(17, 0, difficulty=band)
    assert (len(grid), len(grid[0])) == (6, 21)
    assert len({cell for row in grid for cell in row}) == 5
    assert GEN.self_check(grid) == []


def test_python_reference_solver_reproduces_canonical_outputs():
    for pair in _canonical():
        assert GEN._solve_by_size(pair["input"]) == pair["output"]
        assert GEN._bbox_area_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_pairs", [2, 3, 4])
@pytest.mark.parametrize("layout", ["gallery", "scattered"])
@pytest.mark.parametrize("inversion", [False, True])
def test_exact_overrides_are_visible_and_lawful(band, n_pairs, layout, inversion):
    expected = {
        "n_pairs": n_pairs,
        "layout": layout,
        "frame_color": 9,
        "bbox_rank_inversion": inversion,
    }
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        n_pairs=n_pairs,
        layout=layout,
        frame_color=9,
        bbox_rank_inversion=inversion,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert GEN._solve_by_size(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"n_pairs": 1},
        {"n_pairs": 5},
        {"n_pairs": True},
        {"layout": "diagonal"},
        {"frame_color": 0},
        {"frame_color": True},
        {"bbox_rank_inversion": 1},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_samples_are_valid_deterministic_and_never_fallback(band):
    seen_pairs = set()
    seen_layouts = set()
    for sample_index in range(20):
        grid = GEN.generate(123, sample_index, difficulty=band)
        assert grid == GEN.generate(123, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        seen_pairs.add(observed["n_pairs"])
        seen_layouts.add(observed["layout"])
        assert observed["n_pairs"] in {2, 3, 4}
    assert "gallery" in seen_layouts
    assert "scattered" in seen_layouts
    assert 3 in seen_pairs  # canonical-profile schedule is present in every band


def test_bbox_area_shortcut_has_generated_counterexamples_and_two_demo_coverage():
    grids = [GEN.generate(44, index, difficulty="medium") for index in range(10)]
    witness = GEN.SEMANTIC_WITNESSES["cell_count_not_bbox_area"]
    rival = GEN.SEMANTIC_RIVALS["bbox_area_rank"]
    for grid in grids:
        if witness(grid):
            assert rival(grid) == GEN._bbox_area_rival(grid)
            assert rival(grid) != GEN._solve_by_size(grid)
    for first, second in zip(grids, grids[1:]):
        assert witness(first) or witness(second)


def test_default_grid_area_median_stays_inside_defect_lint_guard():
    """Regression: v2/v3 broad canvases made median area 600 vs canonical 126."""
    areas = []
    for band in [None, "easy", "medium", "hard"]:
        for sample_index in range(20):
            grid = GEN.generate(31, sample_index, difficulty=band)
            areas.append(len(grid) * len(grid[0]))
    areas.sort()
    assert areas[len(areas) // 2] <= 4 * 126


def test_retained_bbox_area_counterexample_refutes_canonical_shortcut():
    import json

    path = HOME / "counterexamples" / "bbox_area_rank.json"
    case = json.loads(path.read_text())
    assert GEN.self_check(case["input"]) == []
    assert GEN._solve_by_size(case["input"]) == case["selected_cell_count_output"]
    assert GEN._bbox_area_rival(case["input"]) == case["bbox_area_rival_output"]
    assert case["selected_cell_count_output"] != case["bbox_area_rival_output"]
