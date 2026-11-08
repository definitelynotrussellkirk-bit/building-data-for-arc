"""Task-local regression suite for 3ce95b466478."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    canonical_pairs,
    components,
    lesson_reasons,
    load_generator,
    observed,
    perimeter,
    pinned_profile_seed,
    profile,
    solve_by_perimeter,
    solve_by_size,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert solve_by_size(pair["input"]) == pair["output"]


def test_perimeter_shortcut_fits_every_canonical_pair():
    assert all(solve_by_perimeter(pair["input"]) == pair["output"] for pair in canonical_pairs())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_round_trip_in_every_band(band):
    requested = {
        "grid_h": 8,
        "grid_w": 11,
        "n_blobs": 5,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert {key: observed(grid)[key] for key in requested} == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 17),
        ("grid_w", 10),
        ("grid_w", 17),
        ("n_blobs", 2),
        ("n_blobs", 6),
        ("decoration_color", 9),
        ("decoration_size", 2),
        ("grid_h", True),
        ("n_blobs", 4.0),
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_samples_refute_perimeter_shortcut(band):
    for start in range(15):
        demos = []
        for sample_index in range(start, start + 3):
            grid = gen.generate(9001 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": solve_by_size(grid)})
        assert lesson_reasons(demos) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_scheduled_counterexample_is_real_and_lawful(band):
    for sample_index in range(0, 30, 3):
        grid = gen.generate(712, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.SEMANTIC_WITNESSES["size_vs_perimeter"](grid)
        assert gen.SEMANTIC_RIVALS["second_largest_perimeter"](grid) == solve_by_perimeter(grid)
        assert solve_by_perimeter(grid) != solve_by_size(grid)
        sizes = sorted((len(cells) for cells in components(grid)), reverse=True)
        perimeters = sorted((perimeter(cells) for cells in components(grid)), reverse=True)
        assert sizes[0] == 6 and sizes[1] == 5
        assert perimeters[0] == 12 and perimeters[1] == 10


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_support_in_each_band(band):
    hits = 0
    for index in range(20):
        seed = pinned_profile_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        hits += profile(grid) in CANONICAL_PROFILES
    assert hits >= 1


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_and_covers_declared_axes(band):
    blob_counts = set()
    decoration_colors = set()
    decoration_sizes = set()
    profiles = set()
    for index in range(256):
        grid = gen.generate(4200 + index, index * 11 + 1, difficulty=band)
        assert grid == gen.generate(4200 + index, index * 11 + 1, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        blob_counts.add(stats["n_blobs"])
        decoration_colors.add(stats["decoration_color"])
        decoration_sizes.add(stats["decoration_size"])
        profiles.add(profile(grid))
    assert blob_counts == {3, 4, 5}
    assert decoration_colors == set(range(3, 10))
    assert decoration_sizes == {1, 2, 3}
    assert len(profiles) >= 12


def test_override_boundary_matrix_stays_within_stage_budget():
    """The inherited checker runs every case over 3 bands x 30 seeds."""
    checker_path = HOME.parents[1] / "shared" / "tools" / "check_generator_override_contract.py"
    spec = importlib.util.spec_from_file_location("task_override_checker", checker_path)
    assert spec and spec.loader
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    cases = checker._build_cases(gen.AXES)
    assert len(cases) <= 64, f"{len(cases)} cases expand to {len(cases) * 90} draws"


def test_validator_rejects_ties_extra_colors_and_too_few_blobs():
    grid = gen.generate(8, 7, n_blobs=4)

    tied = [[0] * 11 for _ in range(8)]
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        tied[r][c] = 2
    for r, c in ((3, 0), (3, 1), (3, 2)):
        tied[r][c] = 2
    for r, c in ((6, 0), (7, 0), (7, 1)):
        tied[r][c] = 2
    tied[0][10] = 6
    tie_errors = gen.self_check(tied)
    assert any("not distinct" in error for error in tie_errors)

    extra_color = deepcopy(grid)
    extra_color[0][0] = 1 if extra_color[0][0] == 0 else 4
    assert gen.self_check(extra_color)

    too_few = [[0] * 11 for _ in range(8)]
    too_few[0][0] = 2
    too_few[3][3] = 2
    too_few[7][10] = 6
    assert gen.self_check(too_few)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)
