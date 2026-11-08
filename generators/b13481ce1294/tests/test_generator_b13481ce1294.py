from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.b13481ce1294 import generator as gen
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)


BANDS = ("easy", "medium", "hard")


def test_b13481ce1294_accepts_all_canonical_pairs_and_mirrors_outputs():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_b13481ce1294_axis_boundaries_are_exact_and_observable():
    for band in BANDS:
        for height in (3, 10):
            for panel_w in (2, 8):
                for palette_size in (2, 5):
                    for profile in gen.BRANCH_PROFILES:
                        grid = gen.generate(
                            91001,
                            17,
                            difficulty=band,
                            grid_h=height,
                            panel_w=panel_w,
                            palette_size=palette_size,
                            branch_profile=profile,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.strict_canonical_like(grid) == []
                        assert gen._teaching_errors(grid) == []
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "panel_w": panel_w,
                            "palette_size": palette_size,
                            "branch_profile": profile,
                        }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis=3)


def test_b13481ce1294_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260727)
    before = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(77, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    second[0][0] = (second[0][0] + 1) % 10
    assert first != second


def test_b13481ce1294_self_check_rejects_targeted_structural_impostors():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_b13481ce1294_strict_semantic_census_200_per_band():
    for band_index, band in enumerate(BANDS):
        witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        strict = 0
        distinct_inputs: set[str] = set()
        distinct_outputs: set[str] = set()
        for index in range(200):
            grid = gen.generate(200_000 + band_index * 1000 + index, index, difficulty=band)
            if not gen.strict_canonical_like(grid):
                strict += 1
            distinct_inputs.add(repr(grid))
            distinct_outputs.add(repr(gen.rule_mirror(grid)))
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                witness_counts[name] += int(predicate(grid))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != gen.rule_mirror(grid), (band, index, name)
        assert strict == 200
        assert len(distinct_inputs) >= 190
        assert len(distinct_outputs) >= 180
        for required in (
            "left_only_branch",
            "right_only_branch",
            "same_color_overlap",
            "different_color_overlap",
            "both_zero_branch",
            "multicolor_xor_output",
        ):
            assert witness_counts[required] == 200
        canonical_shapes = sum(
            int(gen._canonical_shape(gen.generate(
                200_000 + band_index * 1000 + index, index, difficulty=band
            )))
            for index in range(200)
        )
        assert canonical_shapes == 100


def test_b13481ce1294_every_sliding_lesson_window_is_identifiable():
    for band_index, band in enumerate(BANDS):
        pairs = []
        for index in range(16):
            grid = gen.generate(700_000 + band_index * 1000 + index, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(len(pairs) - gen.EXAMPLES_NEEDED):
            demos = pairs[start:start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == [], (band, start)
