"""Regressions for first-match teaching support and absent override semantics."""
from __future__ import annotations

import importlib.util
from collections import Counter
import json

import pytest
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "d3575d4206d7"
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("first_match_subject", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_none_overrides_preserve_scheduled_draw(band):
    # GenCtx explicitly treats None as an absent override, including scheduled axes.
    for index in range(4):
        expected = gen.generate(0, index, difficulty=band)
        for axis in gen.AXES:
            assert gen.generate(0, index, difficulty=band, **{axis: None}) == expected, axis


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("index", [0, 1, 2])
def test_early_phase_demonstrates_global_first_color_and_filtered_axes(band, index):
    grid = gen.generate(193, index, difficulty=band)
    analysis = gen._analysis(grid)
    assert analysis["errors"] == []
    primary = [trace for trace in analysis["traces"] if trace["branch"] == "primary"]
    assert primary
    for trace in primary:
        colors = [gen._mask_value(panel, trace["mask"]) for panel in trace["matches"]]
        counts = Counter(colors)
        first = colors[0]
        assert len(counts) >= 2, "homogeneous matches cannot teach target-color selection"
        if index in (0, 2):
            assert counts[first] < max(counts.values()), colors
        else:
            assert counts[first] > min(counts.values()), colors
        assert first != colors[-1], colors
        if index == 0:
            assert first < max(colors), colors
        else:
            assert first > min(colors), colors
        marker = trace["marked"]
        aligned = [panel for panel in trace["matches"]
                   if panel["ri"] == marker["ri"] or panel["ci"] == marker["ci"]]
        assert gen._mask_value(aligned[0], trace["mask"]) != first
        row_aligned = [panel for panel in trace["matches"] if panel["ri"] == marker["ri"]]
        assert gen._mask_value(row_aligned[0], trace["mask"]) != first
        assert gen.SEMANTIC_RIVALS["primary_ignore_selector_color"](grid) != analysis["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_later_phase_counterbalances_minority_color_shortcut(band):
    grid = gen.generate(419, 3, difficulty=band)
    for trace in gen._analysis(grid)["traces"]:
        if trace["branch"] != "primary":
            continue
        colors = [gen._mask_value(panel, trace["mask"]) for panel in trace["matches"]]
        counts = Counter(colors)
        assert len(counts) >= 2, colors
        assert counts[colors[0]] > min(counts.values()), colors


def test_canonical_shortcut_declarations_fit_all_retained_labels():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_three_demo_lessons_survive_every_single_query_holdout(band):
    for start in range(4):
        pairs = []
        for index in range(start, start + 4):
            grid = gen.generate(80173, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)


@pytest.mark.parametrize("values,expected", [
    ([3, 3, 0, 0, 3, 0, 3, 0], 0),
    ([1, 9], 9),
    ([9, 1], 1),
    ([1, 9, 9, 1], 9),
    ([2, 9], 9),
    ([9, 2], 9),
    ([3, 3, 0], 3),
])
def test_fallback_mode_matches_pinned_racket_tie_cases(values, expected):
    # Literal labels from Racket 8.10, not from the Python implementation.
    assert gen._mode_first(values) == expected


def test_fallback_mirror_rejects_uncalibrated_wide_palette_ties():
    with pytest.raises(ValueError, match="three distinct"):
        gen._mode_first([0, 1, 2, 3])

