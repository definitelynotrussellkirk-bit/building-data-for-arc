"""Regressions for source-bound shortcuts missed by the v3.0.0 review."""
from itertools import product
import os
from pathlib import Path
import sys

import pytest

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT / "workspace"))
from reference_probe import canonical_pairs, geometry_output, load_generator  # noqa: E402
from reviewer_support import find_root, load_selected_generator  # noqa: E402
from shortcut_probe import (  # noqa: E402
    color_coded_pattern,
    diagonal_double_tie,
    multicolumn_source,
)

_SOURCE_OVERRIDE = os.environ.get("GENERATOR_UNDER_TEST")
GEN = (
    load_generator(_SOURCE_OVERRIDE)
    if _SOURCE_OVERRIDE
    else load_selected_generator("77e3acd21c5d", root=find_root(__file__))[0]
)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_background_varies_across_seeds_at_one_scheduled_position(band):
    # A background derived solely from sample_index would teach an irrelevant
    # color/branch association even if all ten colors occur in a long census.
    backgrounds = {
        GEN.generate(seed, 13, difficulty=band)[0][0]
        for seed in range(16)
    }
    assert len(backgrounds) > 1, backgrounds


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_refute_reconstructing_markers_from_background(band):
    grids = [GEN.generate(8000 + index, index, difficulty=band) for index in range(40)]
    assert any(color_coded_pattern(grid) != geometry_output(grid) for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_require_width_instead_of_marker_column_shape(band):
    grids = [GEN.generate(8000 + index, index, difficulty=band) for index in range(60)]
    assert any(multicolumn_source(grid) != geometry_output(grid) for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_six_pair_window_teaches_cartesian_double_ties_under_rotation(band):
    # The profile and semantic schedules may have different periods. Enumerate
    # every residue of their declared joint period, with the independent rival.
    period = getattr(GEN, "LESSON_SCHEDULE_PERIOD", 20)
    for start in range(period):
        pairs = []
        for offset in range(6):
            grid = GEN.generate(20000 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": geometry_output(grid)})
        correct = [diagonal_double_tie(pair["input"]) == pair["output"] for pair in pairs]
        for query_index in range(6):
            demo_matches = [match for index, match in enumerate(correct) if index != query_index]
            assert not (all(demo_matches) and not correct[query_index]), {
                "start": start,
                "query_index": query_index,
                "modes": [GEN.observe_overrides(pair["input"])["marker_mode"] for pair in pairs],
            }
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_schedule_does_not_alias_marker_modes_to_profile_parity():
    # In particular, a six-cycle and four profiles would omit half the possible
    # profile/mode combinations. The seven-cycle reaches all within 28 draws.
    observed = {
        (facts["profile"], facts["marker_mode"])
        for index in range(28)
        for facts in [GEN.observe_overrides(GEN.generate(700, index))]
    }
    assert observed == set(product(GEN.PROFILES, GEN.MARKER_MODES))


def test_diagonal_rival_is_declared_and_matches_independent_implementation():
    assert "diagonal_double_tie" in GEN.LESSON_COMPETITORS
    rival = GEN.LESSON_COMPETITORS["diagonal_double_tie"]
    for profile, mode in product(GEN.PROFILES, GEN.MARKER_MODES):
        grid = GEN.generate(17, 9, profile=profile, marker_mode=mode)
        assert rival(grid) == diagonal_double_tie(grid)


def test_canonical_examples_do_not_teach_double_tie_cartesian_product():
    assert all(diagonal_double_tie(pair["input"]) == pair["output"] for pair in canonical_pairs())


def test_canonical_examples_require_width_instead_of_marker_column_shape():
    assert any(multicolumn_source(pair["input"]) != pair["output"] for pair in canonical_pairs())
