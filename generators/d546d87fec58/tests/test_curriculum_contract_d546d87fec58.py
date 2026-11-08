"""Regression tests for canonical anchoring and semantic shortcut coverage."""
from __future__ import annotations

import hashlib
from collections import Counter, deque
from statistics import median

from generators.d546d87fec58 import generator as gen


CANONICAL_INPUT_PROFILES = {(16, 16, 8), (16, 16, 9)}


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def test_default_sampler_hits_canonical_profiles_without_rate_warnings():
    hits_by_band = {}
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grid = gen.generate(
                seed,
                seed % 7919 + index,
                difficulty=band,
            )
            profiles.append(_profile(grid))
        hits_by_band[band] = sum(
            profile in CANONICAL_INPUT_PROFILES for profile in profiles
        )
        assert hits_by_band[band] >= 1, (band, profiles)

    # The strict profile gate warns below a 25% canonical-envelope rate.
    assert sum(hits_by_band.values()) >= 15, hits_by_band


def _nonmodal_component_count(grid):
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    components = 0
    while unseen:
        components += 1
        start = unseen.pop()
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
    return components


def test_canonical_anchor_does_not_collapse_morphology_distribution():
    counts = [
        _nonmodal_component_count(gen.generate(seed, seed, difficulty=band))
        for band in ("easy", "medium", "hard")
        for seed in range(1, 41)
    ]
    # Canonical median is 9; the distribution gate permits at most 3x drift.
    assert median(counts) >= 3, Counter(counts)


def test_semantic_contract_refutes_the_canonical_fitting_rot180_shortcut():
    assert callable(getattr(gen, "strict_canonical_like", None))
    assert gen.MIN_STRICT_FRAC == 1.0
    assert "fallback_required" in gen.SEMANTIC_WITNESSES
    assert "rot180_only" in gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS["fallback_required"] == ["rot180_only"]
    assert gen.CANONICAL_SHORTCUTS["rot180_only"] is gen.SEMANTIC_RIVALS["rot180_only"]

    witness = gen.SEMANTIC_WITNESSES["fallback_required"]
    rival = gen.SEMANTIC_RIVALS["rot180_only"]
    for profile in ("horizontal_fallback", "mixed_fallback"):
        grid = gen.generate(
            913,
            27,
            difficulty="medium",
            grid_size=16,
            palette_size=8,
            block_h=3,
            block_w=4,
            mask_profile=profile,
        )
        assert gen.strict_canonical_like(grid) == []
        assert witness(grid)
        assert rival(grid) != gen.rule_mirror(grid)


def test_every_four_consecutive_demos_refute_rot180_only():
    rival = gen.SEMANTIC_RIVALS["rot180_only"]
    probes = (
        ("easy", 901940102, 53),
        ("medium", 1188453127, 0),
        ("hard", 3558411388, 0),
    )
    for band, seed, first_start in probes:
        for start in range(first_start, first_start + 6):
            demos = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            assert any(
                rival(grid) != gen.rule_mirror(grid) for grid in demos
            ), (band, seed, start, [gen.observe_overrides(grid) for grid in demos])


def test_default_mask_profile_is_a_keyed_draw_with_cyclic_value():
    from puzzle_generators import base

    contexts = []
    base.set_ctx_observer(contexts.append)
    try:
        for sample_index, expected in enumerate(gen.MASK_PROFILES * 2):
            gen.generate(44017, sample_index, difficulty="medium")
            ctx = contexts[-1]
            assert ctx.recorded_draws()["mask_profile"] == expected
            assert ctx.draw_options("mask_profile") is not None
    finally:
        base.set_ctx_observer(None)
