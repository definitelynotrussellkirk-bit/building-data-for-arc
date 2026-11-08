"""Regressions for solid bodies, exact color roles, and teachable crops."""
from collections import Counter
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "b8aea529acfd"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ) if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("crop_contract_generator", GENERATOR_PATH)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def dense_body():
    """Hand-built 6x7 body: 35 fours, 7 ones, and 30 surrounding zeros."""
    grid = [[0] * 9 for _ in range(8)]
    for r in range(1, 7):
        grid[r][1:8] = [1, 4, 4, 4, 4, 4, 4]
    grid[2][2] = 1
    return grid


def _box(points):
    return (
        min(r for r, c in points), min(c for r, c in points),
        max(r for r, c in points), max(c for r, c in points),
    )


def _separates_both_crop_shortcuts(grid):
    """Check geometry and counts independently of generator observables."""
    counts = Counter(cell for row in grid for cell in row)
    foreground = [(r, c) for r, row in enumerate(grid)
                  for c, cell in enumerate(row) if cell != 0]
    majority = max((c for c in counts if c != 0), key=counts.get)
    majority_cells = [(r, c) for r, row in enumerate(grid)
                      for c, cell in enumerate(row) if cell == majority]
    return counts[majority] > counts[0] and _box(majority_cells) != _box(foreground)


def test_self_check_rejects_a_hole_inside_the_declared_solid_body():
    grid = dense_body()
    assert gen.self_check(grid) == []
    grid[3][3] = 0  # Does not change either foreground color or the outer bounds.
    assert gen.self_check(grid), "A hole contradicts the solid-body input contract"


def test_scene_profile_observation_distinguishes_majority_and_accent_roles():
    profile = "e_12x16_5x5_4_1"
    grid = gen.generate(7301, 0, scene_profile=profile)
    assert gen.observe_overrides(grid) == {"scene_profile": profile}
    swapped = [[{1: 4, 4: 1}.get(cell, cell) for cell in row] for row in grid]
    assert gen.observe_overrides(swapped).get("scene_profile") != profile
    assert gen.self_check(swapped, meta={"overrides": {"scene_profile": profile}})


def test_declared_canonical_shortcuts_really_fit_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], (
                name, pair["variant"], pair["split"], pair["pair_index"]
            )


def test_dense_counterexample_preserves_the_racket_checked_full_width():
    grid = dense_body()
    expected = [[4, 4, 4, 4, 4, 4, 1] for _ in range(6)]
    expected[1] = [4, 4, 4, 4, 4, 1, 1]
    assert gen.strict_canonical_like(grid) == []
    assert gen.rule_mirror(grid) == expected
    for name in ("crop_majority_color_bbox", "crop_modal_background"):
        assert name in gen.CANONICAL_SHORTCUTS
        assert gen.CANONICAL_SHORTCUTS[name](grid) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 370, 7301])
def test_every_three_of_four_consecutive_draws_include_a_joint_witness(band, seed):
    made = [gen.generate(seed, i, difficulty=band) for i in range(11)]
    for start in range(8):
        lesson = made[start:start + 4]
        assert len({tuple(map(tuple, grid)) for grid in lesson}) == 4, (
            f"Duplicate skipping can remove a required witness: {band=} {seed=} {start=}"
        )
        for query_position in range(4):
            assert any(
                _separates_both_crop_shortcuts(grid)
                for i, grid in enumerate(lesson) if i != query_position
            ), f"Missing teaching witness: {band=} {seed=} {start=} {query_position=}"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_canvas_and_palette_support_survives_the_witness_schedule(band):
    def profile(grid):
        return len(grid), len(grid[0]), frozenset(cell for row in grid for cell in row)

    canonical = {profile(pair["input"]) for pair in canonical_pairs(TASK, root=ROOT)}
    generated = {profile(gen.generate(7301, i, difficulty=band)) for i in range(20)}
    assert canonical & generated
