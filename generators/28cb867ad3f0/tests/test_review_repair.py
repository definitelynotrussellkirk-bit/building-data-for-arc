"""Regression tests for the reviewed 28cb867ad3f0 curriculum."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "28cb867ad3f0"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_scalars_fail_loudly(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def _distinct_cardinal_marker_cells(grid):
    """Shortcut: each adjacent marker cell votes once, not once per incidence."""
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    }
    result = [list(row) for row in grid]
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = []
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        markers = {
            (other_row, other_col)
            for row, col in component
            for other_row, other_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if 0 <= other_row < height
            and 0 <= other_col < width
            and 1 <= grid[other_row][other_col] <= 4
        }
        counts = {
            color: sum(grid[row][col] == color for row, col in markers)
            for color in range(1, 5)
        }
        best = max(counts.values(), default=0)
        winners = [color for color, count in counts.items() if count == best and count > 0]
        if len(winners) == 1:
            for row, col in component:
                result[row][col] = winners[0]
    return result


def test_declares_the_strongest_canonical_fitting_shortcut_only():
    pairs = _pairs()
    assert pairs
    assert all(_distinct_cardinal_marker_cells(pair["input"]) == pair["output"] for pair in pairs)
    assert "distinct_cardinal_marker_cells" in GEN.SEMANTIC_RIVALS
    assert set(GEN.CANONICAL_SHORTCUTS) == {"distinct_cardinal_marker_cells"}
    declared = GEN.CANONICAL_SHORTCUTS["distinct_cardinal_marker_cells"]
    assert all(declared(pair["input"]) == pair["output"] for pair in pairs)


def test_lesson_identifiability_checks_every_named_partial_rival():
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)


def test_full_contrast_profile_is_an_exact_disagreement_witness_for_every_rival():
    grid = GEN.generate(
        20261012,
        0,
        difficulty="medium",
        scene_profile="full_contrast",
    )
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {"scene_profile": "full_contrast"}
    intended = GEN.rule_mirror(grid)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != intended, name


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_every_schedule_window_and_query_rotation_refutes_every_partial_rival():
    assert GEN.LESSON_SCHEDULE_PERIOD == 18
    for band in ("easy", "medium", "hard"):
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(GEN.generate(88555953889319, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_incidence_multiplicity_has_a_named_witness_and_rival_mapping():
    grid = GEN.generate(9, 0, scene_profile="full_contrast")
    name = "boundary_incidence_multiplicity"
    assert name in GEN.SEMANTIC_WITNESSES
    assert GEN.SEMANTIC_WITNESSES[name](grid)
    assert GEN.WITNESS_RIVALS[name] == ["distinct_cardinal_marker_cells"]


@pytest.mark.parametrize("seed", [True, False, 1.0, "1"])
def test_invalid_seed_scalars_fail_loudly(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


def test_reviewed_curriculum_contract_is_pinned():
    assert GEN.VERSION == "3.1.0"
    assert GEN.LESSON_SCHEDULE_PERIOD == 18
    assert GEN.SCHEDULE_PROFILES[0] == "full_contrast"
    assert set(GEN.SCENE_PROFILES) == set(GEN.SCHEDULE_PROFILES)
