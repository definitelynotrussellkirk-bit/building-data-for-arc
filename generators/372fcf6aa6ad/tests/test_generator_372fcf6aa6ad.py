from __future__ import annotations

import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as _portable_canonical_pairs, find_root

generator = importlib.import_module("puzzle_generators.per_puzzle.372fcf6aa6ad.generator")


REPO_ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")


def _canonical_pairs():
    pairs = _portable_canonical_pairs(
        generator.TASK_ID, root=REPO_ROOT, labeled_only=True
    )
    if not pairs:
        raise AssertionError("canonical task row not found")
    for pair in pairs:
        yield pair["split"], pair["input"], pair["output"]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def test_all_five_canonical_pairs_are_accepted_and_solved_exactly():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 5
    for split, source, expected in pairs:
        before = [row[:] for row in source]
        assert generator.self_check(source) == [], split
        assert generator.rule_mirror(source) == expected
        assert source == before
        assert generator.observe_overrides(source)["lesson_profile"] == "hole_primary"


def test_sample_index_schedule_covers_every_ordering_branch_per_lesson():
    for seed in (7, 70_007):
        for band in BANDS:
            profiles = [
                generator.observe_overrides(
                    generator.generate(seed, sample_index, difficulty=band)
                )["lesson_profile"]
                for sample_index in range(generator.EXAMPLES_NEEDED)
            ]
            assert profiles == list(generator.LESSON_PROFILES)


def test_strict_linked_semantic_census_200_per_band_and_disjoint_stability():
    for start in (0, 100_000):
        for band in BANDS:
            counts = Counter()
            inputs = set()
            outputs = set()
            for offset in range(240):
                sample_index = start + offset
                grid = generator.generate(start + offset, sample_index, difficulty=band)
                assert generator.self_check(grid) == []
                observed = generator.observe_overrides(grid)
                counts[observed["lesson_profile"]] += 1
                inputs.add(_key(grid))
                outputs.add(_key(generator.rule_mirror(grid)))
            assert counts == Counter({profile: 60 for profile in generator.LESSON_PROFILES})
            assert len(inputs) >= 235
            assert len(outputs) >= 210


def test_exact_override_boundaries_are_observable_in_every_band():
    for band in BANDS:
        for grid_h in (14, 20):
            for grid_w in (16, 24):
                for n in (3, 5):
                    for profile in generator.LESSON_PROFILES:
                        grid = generator.generate(
                            grid_h * 1000 + grid_w * 10 + n,
                            17,
                            difficulty=band,
                            grid_h=grid_h,
                            grid_w=grid_w,
                            n=n,
                            lesson_profile=profile,
                        )
                        assert generator.self_check(grid) == []
                        assert generator.observe_overrides(grid) == {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n": n,
                            "lesson_profile": profile,
                        }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"bogus": 1},
        {"grid_h": 13},
        {"grid_h": 21},
        {"grid_w": 15},
        {"grid_w": 25},
        {"n": 2},
        {"n": 6},
        {"lesson_profile": "unknown"},
    ],
)
def test_invalid_controls_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, **kwargs)


def test_self_check_rejects_targeted_structural_impostors():
    valid = generator.generate(
        41,
        0,
        difficulty="medium",
        n=3,
        lesson_profile="hole_primary",
    )
    analysis = generator._analyze(valid)
    assert analysis["errors"] == []

    # 1. Removing one whole object destroys the required object-count grammar.
    missing_object = [row[:] for row in valid]
    for r, c in analysis["components"][0]["cells"]:
        missing_object[r][c] = 0

    # 2. Filling every component bbox destroys the required hole-bearing branch.
    no_holes = [row[:] for row in valid]
    for obj in analysis["components"]:
        r1, c1, r2, c2 = obj["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                no_holes[r][c] = obj["color"]

    # 3. An isolated extra cell reuses a color, creating two objects with one color.
    split_color = [row[:] for row in valid]
    occupied = {cell for obj in analysis["components"] for cell in obj["cells"]}
    for r in range(len(valid)):
        for c in range(len(valid[0])):
            if (r, c) in occupied:
                continue
            if all((r + dr, c + dc) not in occupied for dr, dc in generator._DIR8):
                split_color[r][c] = analysis["components"][0]["color"]
                break
        else:
            continue
        break

    # 4. Recolor one object with another object's color, eliminating color identity.
    duplicate_color = [row[:] for row in valid]
    replacement = analysis["components"][0]["color"]
    for r, c in analysis["components"][1]["cells"]:
        duplicate_color[r][c] = replacement

    # Generic minimal impostors must also fail.
    blank = [[0] * len(valid[0]) for _ in valid]
    singleton = [[0] * len(valid[0]) for _ in valid]
    singleton[1][1] = 4
    short_line = [[0] * len(valid[0]) for _ in valid]
    short_line[1][1:4] = [4, 4, 4]
    solid_2x2 = [[0] * len(valid[0]) for _ in valid]
    solid_2x2[1][1] = solid_2x2[1][2] = solid_2x2[2][1] = solid_2x2[2][2] = 4

    for impostor in (
        missing_object,
        no_holes,
        split_color,
        duplicate_color,
        blank,
        singleton,
        short_line,
        solid_2x2,
    ):
        assert generator.self_check(impostor), impostor


def test_generated_outputs_require_rotation_sorting_and_centered_packing():
    witnessed = set()
    for profile in generator.LESSON_PROFILES:
        grid = generator.generate(
            90 + len(witnessed),
            0,
            difficulty="hard",
            n=5,
            lesson_profile=profile,
        )
        analysis = generator._analyze(grid)
        specs = sorted(
            analysis["specs"],
            key=lambda item: (item["holes"], item["size"], item["top"], item["left"]),
        )
        output = generator.rule_mirror(grid)
        assert output != grid
        assert len(output[0]) > max(
            obj["bbox"][3] - obj["bbox"][1] + 1 for obj in analysis["components"]
        )
        assert [spec["holes"] for spec in specs] == sorted(spec["holes"] for spec in specs)
        witnessed.add(analysis["profile"])
    assert witnessed == set(generator.LESSON_PROFILES)


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(9981)
    state = random.getstate()
    first = generator.generate(19, 31, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
