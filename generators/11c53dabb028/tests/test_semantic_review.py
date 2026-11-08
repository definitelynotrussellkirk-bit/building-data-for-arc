"""Regression checks for the repaired selector curriculum and exact domain."""
from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROBE = TASK_HOME / "workspace/review_probe.py"
SPEC = importlib.util.spec_from_file_location("_review_probe_11c53dabb028", PROBE)
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)
gen = review.load_generator()


def test_canonical_pairs_and_executable_shortcuts():
    pairs = review.canonical_pairs()
    assert len(pairs) == 4
    assert gen.CANONICAL_SHORTCUTS
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert review.mirror_output(pair["input"]) == pair["output"]
        for name, fn in gen.CANONICAL_SHORTCUTS.items():
            assert review.normalize_grid(fn(deepcopy(pair["input"]))) == pair["output"], name


@pytest.mark.parametrize("seed,index,band", [
    (0, 1, "medium"),
    (2677872693, 9038, "hard"),
    (2677872693, 9040, "hard"),
    (2677872693, 9041, "hard"),
])
def test_column_major_uses_the_actual_first_occupied_column_position(seed, index, band):
    grid = gen.generate(seed, index, difficulty=band)
    row_first = next(value for row in grid for value in row if value)
    column_first = next(grid[r][c] for c in range(len(grid[0])) for r in range(len(grid)) if grid[r][c])
    assert len({value for row in grid for value in row if value}) == 3
    assert row_first != column_first, (seed, index, band, grid)


@pytest.mark.parametrize("band", [None, *review.BANDS])
def test_all_six_starts_keep_rivals_refuted_under_every_query_rotation(band):
    rivals = review.declared_rivals(gen)
    assert gen.EXAMPLES_NEEDED == 5
    for seed in (73291, 271828, 620017):
        for start in range(6):
            grids = [gen.generate(seed, 24000 + start + offset, difficulty=band) for offset in range(6)]
            assert all(gen.self_check(deepcopy(grid), difficulty=band) == [] for grid in grids)
            assert len({review.digest(grid) for grid in grids}) == 6
            roles = Counter(review.observed(grid)["selector_role"] for grid in grids)
            assert roles == {"mono": 2, "middle": 2, "minimum": 1, "maximum": 1}
            middle_shapes = [(len(grid), len(grid[0])) for grid in grids
                             if review.observed(grid)["selector_role"] == "middle"]
            assert sorted((h > w) - (h < w) for h, w in middle_shapes) == [-1, 1]
            pairs = [{"input": grid, "output": review.mirror_output(grid)} for grid in grids]
            predictions = review.rival_predictions(rivals, pairs)
            for query_index in range(6):
                scored = review.score_query_rotation(gen, rivals, pairs, query_index, predictions)
                assert scored["ambiguous"] == [], (band, seed, start, query_index, scored)
                assert scored["hook_reasons"] == [], (band, seed, start, query_index, scored)


@pytest.mark.parametrize("band", [None, *review.BANDS])
def test_full_shape_density_multicolor_joint_domain(band):
    for index, (case_band, options, feasible) in enumerate(review.joint_cases(full=True)):
        if case_band == band:
            review.check_joint_case(gen, band, options, feasible, index=index)


@pytest.mark.parametrize("options", [
    {"unknown_review_axis": 1}, {"bg_density": 0.1}, {"noise_overlay": 0.1},
    {"texture": "all_zero"}, {"texture": "all_filled"}, {"texture": "monochrome"},
    {"grid_h": True}, {"grid_w": 16}, {"fg_color": 0}, {"fg_density": True},
    {"fg_density": float("nan")}, {"fg_density": float("inf")}, {"multi_color": "false"},
])
def test_invalid_or_removed_controls_fail_loudly(options):
    with pytest.raises(ValueError):
        gen.generate(42, 17, **options)


def test_racket_production_lessons_all_starts_and_cyclic_queries():
    # One portable source snapshot and one persistent Racket process.  This
    # does not silently turn a missing Racket dependency into a passing skip.
    report = review.run_probe(per_band=6, full_joint=False, racket=True, timeout=300)
    assert report["status"] == "passed", report.get("first_failures")
    assert report["executed_rule_hash"] == gen.RULE_HASH
    assert report["racket_parity"]["checked"] >= 108
    assert report["racket_parity"]["mismatches"] == 0
    for band in review.BANDS:
        assert report["lessons"][band]["materialized"] == 6
        assert report["lessons"][band]["query_rotations"] == 36
        assert report["lessons"][band]["requested_start_residues"] == {str(i): 1 for i in range(6)}
    assert report["canonical"]["mirror_matches"] == 4
