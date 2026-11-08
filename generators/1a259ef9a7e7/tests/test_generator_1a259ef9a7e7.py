"""Focused regressions for generator 1a259ef9a7e7."""
from __future__ import annotations

import importlib
import json
import random
from collections import Counter

GEN = importlib.import_module("puzzle_generators.per_puzzle.1a259ef9a7e7.generator")

CANONICAL = (
    (
        [[2, 0], [2, 2], [2, 0]],
        [[0, 2, 2, 0], [2, 2, 2, 2], [0, 2, 2, 0]] * 3,
    ),
    (
        [[0, 8], [0, 0], [0, 8]],
        [[8, 0, 0, 8], [0, 0, 0, 0], [8, 0, 0, 8]] * 3,
    ),
    (
        [[0, 0], [0, 5], [5, 0]],
        [
            [0, 5, 5, 0], [5, 0, 0, 5], [0, 0, 0, 0],
            [0, 0, 0, 0], [5, 0, 0, 5], [0, 5, 5, 0],
            [0, 5, 5, 0], [5, 0, 0, 5], [0, 0, 0, 0],
        ],
    ),
    (
        [[3, 3], [3, 0], [3, 3]],
        [[3, 3, 3, 3], [0, 3, 3, 0], [3, 3, 3, 3]] * 3,
    ),
)


def test_metadata_mask_domain_and_canonical_acceptance():
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == "091b7cbaf545"
    assert len(GEN.BRANCH_VISIBLE_MASKS) == 44
    assert len(set(GEN.BRANCH_VISIBLE_MASKS)) == 44
    for grid, expected in CANONICAL:
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == expected
        assert GEN.canonical_profile_signature(grid) is not None


def test_exact_axes_are_observable_at_boundaries_in_every_band():
    for band in ("easy", "medium", "hard"):
        for color in (1, 9):
            for mask_index in (0, 43):
                grid = GEN.generate(
                    77,
                    19,
                    difficulty=band,
                    grid_h=3,
                    grid_w=2,
                    color=color,
                    mask_index=mask_index,
                )
                expected = {
                    "grid_h": 3,
                    "grid_w": 2,
                    "color": color,
                    "mask_index": mask_index,
                }
                assert GEN.observe_overrides(grid) == expected
                assert GEN.self_check(grid, meta={"overrides": expected}) == []


def test_ordinary_distribution_exposes_both_branches_and_varies_by_band():
    masks_by_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        masks = Counter()
        colors = set()
        serialized = set()
        for offset in range(200):
            seed = 10_000 + band_index * 10_000 + offset
            grid = GEN.generate(seed, offset * 17 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            masks[observed["mask_index"]] += 1
            colors.add(observed["color"])
            serialized.add(json.dumps(grid, separators=(",", ":")))
            role = tuple(tuple(int(value != 0) for value in row) for row in grid)
            assert not GEN._is_lr_symmetric(role)
            assert not GEN._is_ud_symmetric(role)
            output = GEN.rule_mirror(grid)
            assert len(output) == 9 and all(len(row) == 4 for row in output)
            assert output[:3] != output[3:6]
        masks_by_band[band] = set(masks)
        assert len(masks) >= 15
        assert colors == set(range(1, 10))
        assert len(serialized) >= 90
    assert masks_by_band["easy"] != masks_by_band["medium"]
    assert masks_by_band["medium"] != masks_by_band["hard"]


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "wrong_height": [[1, 0], [0, 1]],
        "wrong_width": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "monochrome_zero": [[0, 0], [0, 0], [0, 0]],
        "missing_background": [[4, 4], [4, 4], [4, 4]],
        "two_foregrounds": [[0, 2], [3, 0], [0, 2]],
        "ragged": [[0, 2], [2], [0, 2]],
        "invalid_cell": [[0, 2], [2, 10], [0, 2]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_determinism_freshness_global_rng_and_loud_rejections():
    random.seed(918273)
    before = random.getstate()
    first = GEN.generate(1234, 5678, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(1234, 5678, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

    for kwargs in (
        {"mask_index": -1},
        {"mask_index": 44},
        {"color": 0},
        {"grid_h": 4},
        {"bogus": 1},
    ):
        try:
            GEN.generate(1, 2, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"override should reject loudly: {kwargs}")
    try:
        GEN.generate(1, 2, difficulty="extreme")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown difficulty should reject loudly")
