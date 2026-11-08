"""Task-local regression suite for the checkerboard-parity marker generator."""
from __future__ import annotations

from collections import Counter
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    MARKER_COLORS,
    PARITIES,
    PROFILE_SPECS,
    RIVALS,
    apply_rule,
    canonical_pairs,
    gray_components,
    independent_observation,
    load_generator,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_declares_pinned_rule_and_only_observable_axes():
    assert getattr(gen, "RULE_HASH", None) == "d29d80b108a0"
    assert set(gen.AXES) == {"scene_profile", "marker_color", "marker_parity"}
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_and_solves_every_canonical_pair(pair):
    assert gen.self_check(pair["input"]) == []
    strict = getattr(gen, "strict_canonical_like", None)
    assert callable(strict), "strict_canonical_like must be executable"
    assert strict(pair["input"]) == []
    assert apply_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", tuple(PROFILE_SPECS))
@pytest.mark.parametrize("color", MARKER_COLORS)
@pytest.mark.parametrize("parity", PARITIES)
def test_every_exact_override_combination_is_legal_and_observable(band, profile, color, parity):
    expected = {
        "scene_profile": profile,
        "marker_color": color,
        "marker_parity": parity,
    }
    grid = gen.generate(917, 23, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert independent_observation(grid) == expected
    observe = getattr(gen, "observe_overrides", None)
    assert callable(observe), "observe_overrides must recover exact axes from pixels"
    assert observe(grid) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": "x"},
        {"scene_profile": "canonical_12x12"},
        {"scene_profile": 13},
        {"marker_color": 0},
        {"marker_color": 5},
        {"marker_color": 10},
        {"marker_color": True},
        {"marker_color": "2"},
        {"marker_parity": "p22"},
        {"marker_parity": 0},
    ],
)
def test_rejects_unknown_or_invalid_overrides(kwargs):
    with pytest.raises(ValueError):
        gen.generate(1, 2, **kwargs)


def test_generated_distribution_matches_canonical_density_and_component_scale():
    profile_counts = Counter()
    parity_counts = Counter()
    color_counts = Counter()
    component_counts = []
    largest_components = []
    unique = set()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for index in range(72):
            grid = gen.generate(5100 + band_index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            observed = independent_observation(grid)
            assert gen.observe_overrides(grid) == observed
            profile_counts[(band, observed["scene_profile"])] += 1
            parity_counts[(band, observed["marker_parity"])] += 1
            color_counts[(band, observed["marker_color"])] += 1
            sizes = gray_components(grid)
            component_counts.append(len(sizes) + 1)  # gray components plus marker
            largest_components.append(sizes[0])
            unique.add(tuple(tuple(row) for row in grid))
            intended = apply_rule(grid)
            assert intended != grid
            assert all(rival(grid) != intended for rival in RIVALS.values())
    for band in (None, "easy", "medium", "hard"):
        assert all(profile_counts[(band, profile)] > 0 for profile in PROFILE_SPECS)
        assert all(parity_counts[(band, parity)] > 0 for parity in PARITIES)
        assert all(color_counts[(band, color)] > 0 for color in MARKER_COLORS)
    assert len(unique) >= 270
    ordered = sorted(component_counts)
    median = ordered[len(ordered) // 2]
    assert 10 <= median <= 13
    assert min(component_counts) >= 6
    assert max(component_counts) <= 19
    largest_ordered = sorted(largest_components)
    largest_median = largest_ordered[len(largest_ordered) // 2]
    assert 20 <= largest_median <= 45


def test_semantic_contract_names_real_counterexamples():
    expected_rivals = set(RIVALS)
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals
    assert set(gen.LESSON_COMPETITORS) == expected_rivals
    assert set(gen.WITNESS_RIVALS)
    for index in range(32):
        grid = gen.generate(712, index)
        intended = apply_rule(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) == RIVALS[name](grid)
            assert rival(grid) != intended
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), witness_name
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended


def test_three_demo_lesson_is_identifiable_against_declared_rivals():
    pairs = []
    for index in range(4):
        grid = gen.generate(800, index, difficulty="medium")
        pairs.append({"input": grid, "output": apply_rule(grid)})
    checker = getattr(gen, "lesson_identifiable", None)
    assert callable(checker)
    assert checker(pairs[:3], pairs[3]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert not all(rival(pair["input"]) == pair["output"] for pair in pairs[:3]), name


def test_difficulty_bands_change_layout_without_changing_exact_axes():
    grids = {
        band: gen.generate(404, 11, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    observations = {band: independent_observation(grid) for band, grid in grids.items()}
    assert len({tuple(tuple(row) for row in grid) for grid in grids.values()}) == 3
    assert len({tuple(sorted(observed.items())) for observed in observations.values()}) == 1
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids.values())


def test_keyed_rng_is_deterministic_and_hash_seed_independent():
    grid = gen.generate(41, 17, difficulty="hard")
    assert grid == gen.generate(41, 17, difficulty="hard")
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(41,17,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_validator_rejects_sparse_and_destructive_impostors():
    sparse = [[0] * 13 for _ in range(13)]
    sparse[6][6] = 2
    assert gen.self_check(sparse)

    valid = gen.generate(12, 4)
    malformed = [row[:] for row in valid]
    malformed[0][0] = 9 if malformed[0][0] in (0, 5) else 6
    assert gen.self_check(malformed)

    wrong_gray_count = [row[:] for row in valid]
    changed = False
    for r, row in enumerate(wrong_gray_count):
        for c, value in enumerate(row):
            if value == 5:
                wrong_gray_count[r][c] = 0
                changed = True
                break
        if changed:
            break
    assert gen.strict_canonical_like(wrong_gray_count)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(13)]])
def test_malformed_inputs_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_rejects_non_literal_integer_seed(seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", None, -1])
def test_rejects_invalid_sample_index(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(1, sample_index)


def test_every_four_pair_lesson_refutes_color_order_shortcuts_under_rotation():
    """Every three-demo support must include markers on both sides of gray-5."""
    period = len(gen.MARKER_COLORS)
    for start in range(period):
        colors = [gen.schedule_marker_color(0, start + offset) for offset in range(4)]
        for query_index in range(4):
            demos = colors[:query_index] + colors[query_index + 1 :]
            assert any(color < 5 for color in demos), (start, query_index, colors)
            assert any(color > 5 for color in demos), (start, query_index, colors)
