"""Task-local red/green regression suite for efb59efe0080."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    absolute_position_xor,
    canonical_pairs,
    cells,
    connected,
    crop_required,
    filled_bbox_xor,
    load_generator,
    normalized_union,
    normalized_xor,
    observed,
    red_mask_only,
    uncropped_xor,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("8x12", "9x13", "10x14", "11x15", "12x16")
BANDS = (None, "easy", "medium", "hard")


def test_rule_pin_and_public_surface_are_narrow_and_exact():
    assert gen.RULE_HASH == "1cb444e6f050"
    assert set(gen.AXES) == {"canvas_profile", "size_2", "size_3"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_inputs_are_accepted_and_independent_oracle_matches():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert normalized_xor(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_exact_override_is_observable_in_every_band(band):
    # Cross boundary sizes with every canonical canvas profile.  The full
    # 5x5 size cross-product is covered below across the two schedule residues.
    for index, profile in enumerate(PROFILES):
        options = {
            "canvas_profile": profile,
            "size_2": 4 if index % 2 == 0 else 8,
            "size_3": 8 if index % 2 == 0 else 4,
        }
        grid = gen.generate(801 + index, index, difficulty=band, **options)
        assert gen.self_check(grid, meta={"overrides": options}) == []
        assert observed(grid) == options
        assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("sample_index", [0, 1])
def test_all_size_pairs_are_constructive_for_each_schedule_profile(sample_index):
    for size_2 in range(4, 9):
        for size_3 in range(4, 9):
            grid = gen.generate(
                1701,
                sample_index,
                difficulty="hard",
                canvas_profile="8x12",
                size_2=size_2,
                size_3=size_3,
            )
            assert gen.self_check(grid) == []
            assert observed(grid) == {
                "canvas_profile": "8x12",
                "size_2": size_2,
                "size_3": size_3,
            }
            assert crop_required(grid) is (sample_index % 2 == 0)
            assert normalized_xor(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"bogus_axis": 1},
        {"canvas_profile": "13x17"},
        {"size_2": 3},
        {"size_2": 9},
        {"size_3": 3},
        {"size_3": 9},
        {"size_2": True},
        {"size_3": 4.5},
    ],
)
def test_invalid_or_unknown_overrides_reject(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(9917)
    before = random.getstate()
    first = gen.generate(55, 23, difficulty="hard")
    after = random.getstate()
    second = gen.generate(55, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_default_distribution_stays_on_canonical_profiles_and_varies_shapes():
    seen_profiles, seen_sizes, seen_inputs = set(), set(), set()
    for band in BANDS:
        for index in range(80):
            grid = gen.generate(3100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            obs = observed(grid)
            seen_profiles.add(obs["canvas_profile"])
            seen_sizes.add((obs["size_2"], obs["size_3"]))
            seen_inputs.add(tuple(tuple(row) for row in grid))
    assert seen_profiles == set(PROFILES)
    assert len(seen_sizes) >= 20
    assert len(seen_inputs) >= 300


def test_each_three_demo_window_teaches_crop_and_refutes_named_rivals():
    for band in BANDS:
        for start in range(8):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(712, index, difficulty=band)
                demos.append({"input": grid, "output": normalized_xor(grid)})
            query_grid = gen.generate(712, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": normalized_xor(query_grid)}
            assert {crop_required(pair["input"]) for pair in demos} == {False, True}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_witnesses_are_real_counterexamples():
    independent = {
        "normalized_union": normalized_union,
        "uncropped_xor": uncropped_xor,
        "filled_bbox_xor": filled_bbox_xor,
        "red_mask_only": red_mask_only,
        "absolute_position_xor": absolute_position_xor,
    }
    for sample_index in (0, 1):
        grid = gen.generate(919, sample_index, size_2=8, size_3=8)
        intended = normalized_xor(grid)
        assert gen.SEMANTIC_WITNESSES["two_sided_overlap"](grid)
        assert gen.SEMANTIC_WITNESSES["shape_detail_not_bbox"](grid)
        assert gen.SEMANTIC_WITNESSES["normalization_required"](grid)
        assert gen.SEMANTIC_WITNESSES["final_crop_required"](grid) is (sample_index == 0)
        for name, oracle in independent.items():
            assert gen.SEMANTIC_RIVALS[name](grid) == oracle(grid)
            if name != "uncropped_xor" or sample_index == 0:
                assert oracle(grid) != intended


def test_self_check_rejects_structural_mutations_with_diagnostics():
    grid = gen.generate(31, 4, canvas_profile="8x12", size_2=5, size_3=6)
    mutations = []

    missing_color = deepcopy(grid)
    for r, row in enumerate(missing_color):
        for c, value in enumerate(row):
            if value == 3:
                missing_color[r][c] = 0
    mutations.append(missing_color)

    stray_color = deepcopy(grid)
    stray_color[0][0] = 8
    mutations.append(stray_color)

    disconnected = deepcopy(grid)
    red = sorted(cells(disconnected, 2))
    r, c = red[0]
    disconnected[r][c] = 0
    disconnected[-1][-1] = 2
    mutations.append(disconnected)

    identical = [[0] * 12 for _ in range(8)]
    shape = {(0, 0), (0, 1), (1, 0), (1, 1)}
    for r, c in shape:
        identical[1 + r][1 + c] = 2
        identical[5 + r][8 + c] = 3
    mutations.append(identical)

    ragged = [[0, 2], [0]]
    malformed = [None, [], [[]], ragged, [[True] * 12 for _ in range(8)]]

    assert all(gen.self_check(candidate) for candidate in mutations + malformed)
    assert connected(cells(grid, 2)) and connected(cells(grid, 3))
