"""Keep multiple-conflict teaching close to authentic source morphology."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
for parent in (HOME, *HOME.parents):
    # Portable snapshots also carry shared/runtime mirrors. Execution-layout
    # dependencies must win so the selected-source loader sees one source tree.
    if (parent / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent))
        break
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent / "shared/runtime"))
        break
else:  # pragma: no cover - packaging contract
    raise RuntimeError("No independent puzzle_generators runtime found")

from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location("morphology_576426a573af", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def partition(grid):
    """Geometry and equal-color relationships, independent of palette labels."""
    labels = {0: 0}
    result = []
    for row in grid:
        normalized = []
        for value in row:
            if value not in labels:
                labels[value] = len(labels)
            normalized.append(labels[value])
        result.append(tuple(normalized))
    return tuple(result)


def component_count(grid, *, rows=None):
    included = range(len(grid)) if rows is None else rows
    remaining = {(r, c) for r in included for c, color in enumerate(grid[r]) if color}
    count = 0
    while remaining:
        frontier = [remaining.pop()]
        count += 1
        while frontier:
            r, c = frontier.pop()
            adjacent = {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} & remaining
            remaining.difference_update(adjacent)
            frontier.extend(adjacent)
    return count


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("overrides", [{}, {"grid_h": 4, "grid_w": 3},
                                      {"grid_h": 4, "grid_w": 18, "fg_palette_size": 3}])
def test_top_source_and_conflict_evidence_each_form_a_connected_region(band, overrides):
    """Randomly scattered mirror endpoints must not fragment the anchored role."""
    for seed in range(24):
        grid = gen.generate(seed, 1, difficulty=band, **overrides)
        half = len(grid) // 2
        assert component_count(grid, rows=range(half)) == 1
        assert component_count(grid, rows=range(len(grid) - half, len(grid))) == 1
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("palette_size", [3, 4])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_two_canonical_roles_include_a_true_training_partition(band, palette_size):
    """Sparse authentic morphology support must not depend on lucky RNG keys."""
    templates = {
        partition(pair["input"])
        for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__))
        if pair["split"] == "train"
        and len({cell for row in pair["input"] for cell in row if cell}) == palette_size
    }
    for seed in (17, 991):
        for start in range(0, 16, 4):
            grids = [gen.generate(seed, index, difficulty=band, fg_palette_size=palette_size)
                     for index in (start, start + 4)]
            assert any(partition(grid) in templates for grid in grids)
            assert all(gen.strict_canonical_like(grid) == [] for grid in grids)


def test_authentic_anchors_keep_random_canonical_geometry_and_a_complete_declared_period():
    templates = {partition(pair["input"])
                 for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__))
                 if pair["split"] == "train"}
    assert hasattr(gen, "LESSON_SCHEDULE_PERIOD"), "Declare the complete anchor/random subcycle"
    period = gen.LESSON_SCHEDULE_PERIOD
    assert period >= 2 * len(gen.SCHEDULE_PROFILES)
    for seed in (17, 991):
        canonical = [gen.generate(seed, index)
                     for index in range(period)
                     if gen.schedule_profile(seed, index) == "canonical_bottom"]
        assert any(partition(grid) in templates for grid in canonical)
        assert any(partition(grid) not in templates for grid in canonical)


@pytest.mark.parametrize("height,width,palette_size", [
    (4, 3, 3), (4, 3, 6), (10, 4, 5), (10, 4, 6), (10, 18, 3), (18, 4, 4), (18, 18, 6),
])
def test_authentic_anchor_falls_back_for_incompatible_exact_controls(height, width, palette_size):
    grid = gen.generate(17, 0, grid_h=height, grid_w=width, fg_palette_size=palette_size)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": height, "grid_w": width, "fg_palette_size": palette_size,
    }
