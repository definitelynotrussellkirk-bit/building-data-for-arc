"""Regression and semantic-contract tests for the 50b472d4fc63 review."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    exact_output,
    load_generator,
    observed,
    occupancy_exact_three_output,
    same_color_at_least_three_output,
    same_color_component_count,
    same_color_non_singleton_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_h": {"type": "int", "valid": "6..16"},
    "grid_w": {"type": "int", "valid": "6..16"},
    "n_targets": {"type": "int", "valid": "1..2"},
    "n_mixed": {"type": "int", "valid": "1..2"},
    "n_short": {"type": "int", "valid": "0..1"},
    "n_long": {"type": "int", "valid": "0..1"},
    "palette_size": {"type": "int", "valid": "2..4"},
}


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "9af5ed1251ca"
    assert set(gen.AXES) == set(EXPECTED_AXES)
    for name, expected in EXPECTED_AXES.items():
        assert gen.AXES[name]["type"] == expected["type"]
        assert gen.AXES[name]["valid"] == expected["valid"]
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=lambda p: f"{len(p['input'])}x{len(p['input'][0])}"
)
def test_canonical_examples_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert exact_output(pair["input"]) == pair["output"]
    assert gen.strict_canonical_like(pair["input"]) == []


def test_occupancy_only_shortcut_fits_every_canonical_pair():
    assert all(
        occupancy_exact_three_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 6,
            "grid_w": 6,
            "n_targets": 1,
            "n_mixed": 1,
            "n_short": 0,
            "n_long": 0,
            "palette_size": 2,
        },
        {
            "grid_h": 8,
            "grid_w": 7,
            "n_targets": 2,
            "n_mixed": 1,
            "n_short": 1,
            "n_long": 1,
            "palette_size": 3,
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "n_targets": 2,
            "n_mixed": 2,
            "n_short": 1,
            "n_long": 1,
            "palette_size": 4,
        },
    ],
)
def test_exact_overrides_are_pixel_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5),
        ("grid_h", 17),
        ("grid_h", True),
        ("grid_h", "8"),
        ("grid_w", 5),
        ("grid_w", 17),
        ("n_targets", 0),
        ("n_targets", 3),
        ("n_mixed", 0),
        ("n_mixed", 3),
        ("n_short", -1),
        ("n_short", 2),
        ("n_long", -1),
        ("n_long", 2),
        ("palette_size", 1),
        ("palette_size", 5),
        ("palette_size", 2.0),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_teaches_all_declared_distinctions(band):
    palette_sizes = set()
    exact_profiles = 0
    grids = []
    canonical_profiles = {(9, 6, 3), (8, 7, 3), (9, 9, 3)}
    for index in range(80):
        grid = gen.generate(600 + index, index, difficulty=band)
        grids.append(grid)
        assert grid == gen.generate(600 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        palette_sizes.add(stats["palette_size"])
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact_profiles += profile in canonical_profiles
        assert stats["n_mixed"] >= 1
        assert gen.SEMANTIC_WITNESSES["mixed_color_exact_three"](grid)
        assert gen.LESSON_COMPETITORS["occupancy_exact_three"](grid) != exact_output(grid)
        # Canonical-profile branches stay compact; the broad branch may use
        # the upper target/mixed count bounds plus one length distractor.
        feature_count = sum(stats[name] for name in ("n_targets", "n_mixed", "n_short", "n_long"))
        assert feature_count <= (3 if index % 4 != 3 else 5)

    # Any consecutive three demonstrations contain both exact-length negatives,
    # while every individual example contains the color-sensitive counterexample.
    for start in range(len(grids) - 2):
        window = grids[start : start + 3]
        assert any(gen.SEMANTIC_WITNESSES["short_same_color_run"](grid) for grid in window)
        assert any(gen.SEMANTIC_WITNESSES["long_same_color_run"](grid) for grid in window)
        demos = [{"input": grid, "output": exact_output(grid)} for grid in window]
        assert gen.lesson_identifiable(demos, {"input": window[-1], "output": exact_output(window[-1])}) == []
    assert palette_sizes == {2, 3, 4}
    assert exact_profiles >= 50


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_component_count_stays_within_canonical_drift_floor(band):
    counts = sorted(
        same_color_component_count(gen.generate(900 + index, index, difficulty=band))
        for index in range(80)
    )
    # The two canonical training inputs each contain two foreground components;
    # the generic linter permits up to a 3x median expansion for richer lessons.
    assert counts[len(counts) // 2] <= 6


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_example_window_is_identifiable(band):
    for start in range(24):
        demos = []
        for offset in range(3):
            grid = gen.generate(1009 + start, start + offset, difficulty=band)
            demos.append({"input": grid, "output": exact_output(grid)})
        query_grid = gen.generate(1009 + start, start + 3, difficulty=band)
        query = {"input": query_grid, "output": exact_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_of_four_sequential_pairs_is_identifiable(band):
    """The census fixes one query; every pair must also be safe as the query."""
    for start in range(24):
        pairs = []
        for offset in range(4):
            grid = gen.generate(2027 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": exact_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    start,
                    query_index,
                    name,
                )


def test_declared_rivals_match_independent_probes_on_a_teaching_example():
    grid = gen.generate(
        31,
        8,
        grid_h=9,
        grid_w=9,
        n_targets=1,
        n_mixed=1,
        n_short=1,
        n_long=1,
        palette_size=4,
    )
    assert gen.SEMANTIC_RIVALS["occupancy_exact_three"](grid) == occupancy_exact_three_output(grid)
    assert gen.SEMANTIC_RIVALS["all_non_singleton_runs"](grid) == same_color_non_singleton_output(grid)
    assert gen.SEMANTIC_RIVALS["at_least_three_runs"](grid) == same_color_at_least_three_output(grid)
    assert gen.CANONICAL_SHORTCUTS["occupancy_exact_three"](grid) == occupancy_exact_three_output(grid)


def test_output_oracles_do_not_mutate_input():
    grid = gen.generate(71, 5)
    before = deepcopy(grid)
    for oracle in gen.LESSON_COMPETITORS.values():
        oracle(grid)
    assert grid == before


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 6 for _ in range(6)],
        [[8] + [0] * 5 for _ in range(6)],
    ],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_mutation_fixtures_are_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_generation_is_python_hash_seed_independent():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]

def test_reusable_lesson_probe_covers_cyclic_query_rotations(tmp_path):
    report_path = tmp_path / "lesson-probe.json"
    env = dict(
        os.environ,
        PYTHONPATH=str(HOME.parents[1] / "shared" / "runtime"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    subprocess.run(
        [
            sys.executable,
            str(HOME / "workspace" / "lesson_probe.py"),
            "--per-band",
            "8",
            "--out",
            str(report_path),
        ],
        check=True,
        env=env,
        text=True,
    )
    report = json.loads(report_path.read_text())
    assert report["status"] == "pass"
    assert report["generator_sha256"]
    assert report["canonical_shortcuts_fit"]
    for band in ("easy", "medium", "hard"):
        result = report["bands"][band]
        assert result["fixed_query_windows_tested"] == 8
        assert result["query_rotations_tested"] == 32
        assert result["fixed_query_failures"] == []
        assert result["query_rotation_failures"] == []

