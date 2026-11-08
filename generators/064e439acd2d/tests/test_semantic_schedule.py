"""Focused semantic and teaching-schedule checks for the projection task.

Canonical comparisons use recorded answers. Generated-pair predictions below
are analytic diagnostics for these fast tests, not label verification; the
Racket-backed semantic gate and lesson census supply that separate evidence.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


_spec = importlib.util.spec_from_file_location(
    "projection_semantic_contract_support", Path(__file__).with_name("contract_support.py"))
support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(support)
GEN, SOURCE, ROOT = support.load_generator(__file__)
CANONICAL = support.canonical_pairs(support.TASK_ID, root=ROOT, labeled_only=True)

RIVAL_NAMES = {
    "border_only", "project_diagonal_to_corner", "rectangle_only",
    "ignore_touching_sources", "one_per_color", "move_sources",
    "horizontal_projection_only", "vertical_projection_only",
}
SHORTCUT_NAMES = {
    "border_only", "project_diagonal_to_corner", "rectangle_only",
    "ignore_touching_sources",
}
PROFILE_CYCLE = ("rich_hline", "broad", "rich_vline", "broad")


def _canonical_case_id(pair):
    return f"variant-{pair['variant']}-{pair['split']}-{pair['pair_index']}"


def _assert_pure_acceptance(grid, band=None):
    before = deepcopy(grid)
    assert GEN.self_check(grid, difficulty=band) == []
    assert grid == before, "self_check changed its input"
    assert GEN.strict_canonical_like(grid) == []
    assert grid == before, "strict_canonical_like changed its input"


def _analytic_pair(grid):
    # This is deliberately named analytic: tests must not confuse a Python
    # prediction with the selected Racket authority's generated label.
    return {"input": grid, "output": GEN._diagnostic_projection_prediction(grid)}


def test_registry_covers_the_eight_rivals_and_four_canonical_shortcuts():
    assert len(CANONICAL) == 4, "the complete four-pair canonical set was not loaded"
    assert set(GEN.SEMANTIC_RIVALS) == RIVAL_NAMES
    assert set(GEN.LESSON_COMPETITORS) == RIVAL_NAMES
    assert set(GEN.CANONICAL_SHORTCUTS) == SHORTCUT_NAMES
    assert len(GEN.SEMANTIC_WITNESSES) == 8
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    claimed = {name for names in GEN.WITNESS_RIVALS.values() for name in names}
    assert claimed == RIVAL_NAMES
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.SCHEDULE_PROFILES) == set(PROFILE_CYCLE)
    assert max(support.observe(pair["input"])["aligned_count"] for pair in CANONICAL) == 7


@pytest.mark.parametrize("pair", CANONICAL, ids=_canonical_case_id)
def test_canonical_shortcuts_fit_recorded_answers_and_strict_hook_accepts(pair):
    before = deepcopy(pair)
    _assert_pure_acceptance(pair["input"])
    assert GEN._diagnostic_projection_prediction(pair["input"]) == pair["output"]
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert rival(pair["input"]) == pair["output"], name
    assert pair == before, "canonical diagnostic or shortcut changed a recorded pair"


@pytest.mark.parametrize("band", support.BANDS, ids=("default", "easy", "medium", "hard"))
@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("sample_index", range(8))
def test_default_profiles_and_rich_pixels_refute_every_rival(seed, sample_index, band):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    before = deepcopy(grid)
    observed = support.observe(grid)
    assert GEN.schedule_profile(seed, sample_index, difficulty=band) == PROFILE_CYCLE[sample_index % 4]
    assert observed["shape_kind"] in support.SHAPES
    assert observed["aligned_count"] == observed["unique_target_count"]
    _assert_pure_acceptance(grid, band)
    if sample_index % 2:
        return

    assert observed["shape_kind"] == ("hline" if sample_index % 4 == 0 else "vline")
    assert (observed["grid_h"], observed["grid_w"]) == (10, 10)
    assert observed["aligned_count"] == 3
    assert observed["diagonal_count"] == 1
    assert len({color for row in grid for color in row}) == 5
    colors = Counter(dot["color"] for dot in observed["aligned"])
    assert sorted(colors.values()) == [1, 2]
    assert observed["diagonal"][0]["color"] not in colors
    sides = {dot["side"] for dot in observed["aligned"]}
    assert sides & {"left", "right"}, "rich draw omitted horizontal projection"
    assert sides & {"above", "below"}, "rich draw omitted vertical projection"
    touching_nonborder = []
    for dot in observed["aligned"]:
        r, c = dot["source"]
        tr, tc = dot["target"]
        if 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1:
            if abs(r - tr) + abs(c - tc) == 1:
                touching_nonborder.append(dot)
    assert touching_nonborder, "no touching source away from the outer grid border"

    rmin, rmax, cmin, cmax = observed["bbox"]
    assert max(rmax - rmin + 1, cmax - cmin + 1) >= 4
    diagonal = observed["diagonal"][0]
    dr, dc = diagonal["source"]
    assert not rmin <= dr <= rmax and not cmin <= dc <= cmax
    corner = min(max(dr, rmin), rmax), min(max(dc, cmin), cmax)
    targets = {tuple(dot["target"]) for dot in observed["aligned"]}
    assert corner not in targets, "an intended projection masks the diagonal counterexample"
    assert grid[corner[0]][corner[1]] == 8

    expected = GEN._diagnostic_projection_prediction(grid)
    assert expected != grid
    assert expected[corner[0]][corner[1]] == 8
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert rival(grid) != expected, f"rich draw did not refute {name}"
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert witness(grid) is True, f"rich draw did not fire {name}"
        assert any(GEN.SEMANTIC_RIVALS[rival](grid) != expected
                   for rival in GEN.WITNESS_RIVALS[name]), name
    assert grid == before, "semantic diagnostic, rival, or witness changed its input"


@pytest.mark.parametrize("band", support.BANDS, ids=("default", "easy", "medium", "hard"))
@pytest.mark.parametrize("seed", range(8))
def test_every_five_pair_query_holdout_has_a_refuting_demo(seed, band):
    # Starts 0..7 enumerate the four-period boundary twice. Each check holds
    # out all five possible query positions; no single initial offset is used.
    for start in range(8):
        indices = list(range(start, start + 5))
        pairs = [_analytic_pair(GEN.generate(seed, index, difficulty=band)) for index in indices]
        before = deepcopy(pairs)
        profiles = [GEN.schedule_profile(seed, index, difficulty=band) for index in indices]
        for held_out in range(5):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            demo_profiles = [profile for index, profile in enumerate(profiles) if index != held_out]
            query = pairs[held_out]
            assert any(profile.startswith("rich_") for profile in demo_profiles)
            assert "broad" in demo_profiles
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    f"{name} survived demos: seed={seed}, band={band}, "
                    f"start={start}, query_index={indices[held_out]}")
            assert GEN.lesson_identifiable(demos, query) == []
        assert pairs == before, "lesson diagnostics changed the materialized inputs or predictions"


def test_lesson_hook_reports_canonical_fitting_shortcuts_on_a_rich_query():
    query = _analytic_pair(GEN.generate(0, 0))
    before = deepcopy((CANONICAL, query))
    reasons = GEN.lesson_identifiable(CANONICAL, query)
    assert isinstance(reasons, list) and len(reasons) == len(SHORTCUT_NAMES)
    assert all(isinstance(reason, str) for reason in reasons)
    for name in SHORTCUT_NAMES:
        assert any(name in reason for reason in reasons), f"surviving shortcut {name} was not named"
    assert (CANONICAL, query) == before


def test_lesson_hook_does_not_reject_rivals_agreeing_on_the_query():
    # The four canonical shortcuts survive these demos but agree on this
    # query. This is survived_all, not an alternative answer to the query.
    before = deepcopy(CANONICAL)
    assert GEN.lesson_identifiable(CANONICAL, CANONICAL[0]) == []
    assert CANONICAL == before


@pytest.mark.parametrize("band", support.BANDS, ids=("default", "easy", "medium", "hard"))
def test_broad_default_draws_retain_shapes_and_line_count_variation(band):
    # Rich slots intentionally fix count and canvas size. The ordinary default
    # slots must retain the sampler's shape/count breadth without overrides.
    shapes = Counter()
    line_counts = {"hline": set(), "vline": set()}
    for seed in range(8):
        for sample_index in range(1, 16, 2):
            observed = support.observe(GEN.generate(seed, sample_index, difficulty=band))
            kind = observed["shape_kind"]
            shapes[kind] += 1
            if kind in line_counts:
                line_counts[kind].add(observed["aligned_count"])
    assert set(shapes) == set(support.SHAPES), (
        f"ordinary default draws lost shape support in {band}: {dict(shapes)}")
    for kind, counts in line_counts.items():
        assert counts - {3}, f"ordinary {kind} draws only use the rich count in {band}: {counts}"
