"""Task-local regressions for the rigid-gravity teaching distribution."""
from __future__ import annotations

from copy import deepcopy

import pytest

from puzzle_generators.per_puzzle.d2d40680cd25 import generator as gen
from reviewer_support import canonical_pairs, find_root


_CANONICAL_PROFILES = {
    (9, 10, 4),
    (9, 11, 5),
    (10, 12, 5),
}


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_band_has_material_canonical_profile_support(band):
    """Canonical-scale examples must not live only in the easy curriculum."""
    profiles = [
        _profile(gen.generate(5000 + index, 11 * index + 7, difficulty=band))
        for index in range(64)
    ]
    exact = sum(profile in _CANONICAL_PROFILES for profile in profiles)
    envelope = sum(
        9 <= height <= 10 and 10 <= width <= 12 and 4 <= palette <= 5
        for height, width, palette in profiles
    )
    assert exact >= 12, (band, exact, profiles)
    assert envelope >= 16, (band, envelope, profiles)


def test_decorative_wall_shortcut_fits_canonical_demonstrations():
    """The declared shortcut must really be compatible with every demonstration."""
    rival = gen.CANONICAL_SHORTCUTS["decorative_wall"]
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert rival(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_scenes_refute_decorative_wall_shortcut(band):
    """Every ordinary lesson contains a real wall-collision counterexample."""
    rival = gen.SEMANTIC_RIVALS["decorative_wall"]
    witness = gen.SEMANTIC_WITNESSES["wall_support"]
    for index in range(24):
        grid = gen.generate(7100 + index, 17 * index + 3, difficulty=band)
        original = deepcopy(grid)
        assert gen.strict_canonical_like(grid) == []
        assert witness(grid)
        assert rival(grid) != gen.rule_mirror(grid)
        assert grid == original


def test_exact_overrides_bypass_profile_anchoring():
    """Profile support must not narrow or silently replace advertised overrides."""
    options = {
        "grid_h": 14,
        "grid_w": 14,
        "wall_size": 6,
        "n_blobs": 4,
        "palette_kind": "high",
        "wall_position": "right",
        "interaction_mode": "wall_and_stack",
    }
    for index in range(12):
        grid = gen.generate(8800 + index, index, difficulty="easy", **options)
        observed = gen.observe_overrides(grid)
        assert (len(grid), len(grid[0])) == (14, 14)
        assert observed == {
            "wall_size": 6,
            "n_blobs": 4,
            "palette_kind": "high",
            "wall_position": "right",
            "interaction_mode": "wall_and_stack",
        }
