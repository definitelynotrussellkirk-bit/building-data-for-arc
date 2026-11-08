from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_ID = "d349f4dfe492"
REPO = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def test_rule_hash_pins_selected_authority():
    assert gen.RULE_HASH == "e47d7c8767c3"

import copy
import sys

sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs


def test_all_canonical_pairs_are_accepted_and_python_mirror_matches():
    pairs = canonical_pairs(TASK_ID, root=REPO)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def _blank(h=7, w=7):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_self_check_accepts_repeated_colors_but_rejects_overlapping_radius_two_zones():
    valid = _blank()
    valid[0][0] = 4
    valid[6][6] = 4
    assert gen.self_check(valid) == []

    overlap = _blank()
    overlap[2][1] = 3
    overlap[2][5] = 7  # L1 distance 4: closed radius-two zones touch.
    errors = gen.self_check(overlap)
    assert errors and "radius-two" in " ".join(errors).lower()

import random
import pytest


EXPECTED_AXES = {
    "grid_h": ("int", "7..18"),
    "grid_w": ("int", "7..18"),
    "n_seeds": ("int", "1..5"),
}


def test_axis_surface_is_exact_small_and_observable_in_every_band():
    assert set(gen.AXES) == set(EXPECTED_AXES)
    for name, (kind, valid) in EXPECTED_AXES.items():
        assert gen.AXES[name]["type"] == kind
        assert gen.AXES[name]["valid"] == valid
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []

    cases = [
        {"grid_h": 7, "grid_w": 7, "n_seeds": 1},
        {"grid_h": 7, "grid_w": 7, "n_seeds": 5},
        {"grid_h": 18, "grid_w": 7, "n_seeds": 5},
        {"grid_h": 7, "grid_w": 18, "n_seeds": 4},
        {"grid_h": 18, "grid_w": 18, "n_seeds": 5},
    ]
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index, options in enumerate(cases):
            grid = gen.generate(901 + sample_index, sample_index, difficulty=difficulty, **options)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == options


def test_generation_rejects_unknown_overrides_and_is_deterministic_fresh_rng_pure():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(0, 0, __unknown_axis__=1)

    random.seed(918273)
    state = random.getstate()
    first = gen.generate(41, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(41, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

EXPECTED_PROFILES = (
    "canonical_anchor",
    "clipped_border",
    "repeated_colors",
)
EXPECTED_RIVALS = {
    "filled_radius_two",
    "chebyshev_radius_two",
    "axial_only_radius_two",
    "skip_border_seeds",
    "first_two_seeds_only",
    "deduplicate_seed_colors",
    "ignore_color_one",
}


def _lesson(seed: int, start: int, difficulty: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed + offset, start + offset, difficulty=difficulty)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed + 99, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}


def test_three_profile_schedule_and_named_rivals_make_every_window_identifiable():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == EXPECTED_PROFILES
    assert set(gen.SEMANTIC_RIVALS) == EXPECTED_RIVALS
    assert set(gen.LESSON_COMPETITORS) == EXPECTED_RIVALS
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "skip_border_seeds",
        "first_two_seeds_only",
        "deduplicate_seed_colors",
        "ignore_color_one",
    }

    for start in range(12):
        profiles = {
            gen.schedule_profile(17, start + offset, difficulty="medium")
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert profiles == set(EXPECTED_PROFILES)

    for difficulty in ("easy", "medium", "hard"):
        for start in range(9):
            demos, query = _lesson(3000 + start * 10, start, difficulty)
            assert gen.lesson_identifiable(demos, query) == []
            assert all(gen.strict_canonical_like(pair["input"]) == [] for pair in demos)


def test_schedule_exposes_clipping_more_than_two_seeds_and_repeated_colors():
    grids = {
        gen.schedule_profile(0, index): gen.generate(123, index, difficulty="medium")
        for index in range(3)
    }
    clipped = grids["clipped_border"]
    h, w = len(clipped), len(clipped[0])
    assert any(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in gen._seed_cells(clipped))

    repeated = grids["repeated_colors"]
    colors = [value for _r, _c, value in gen._seed_cells(repeated)]
    assert len(colors) >= 3
    assert len(set(colors)) < len(colors)
    assert 1 in {value for grid in grids.values() for _r, _c, value in gen._seed_cells(grid)}


def test_single_seed_edge_case_is_a_border_clipping_lesson_not_an_unconstrained_impostor():
    centered = _blank(9, 9)
    centered[4][4] = 3
    assert gen.self_check(centered)

    border = _blank(9, 9)
    border[0][4] = 3
    assert gen.self_check(border) == []

    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(77, 0, difficulty=difficulty, n_seeds=1)
        seeds = gen._seed_cells(grid)
        assert len(seeds) == 1
        r, c, _value = seeds[0]
        assert r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)


def test_only_the_clipping_profile_requires_outer_border_seeds():
    grids = {
        gen.schedule_profile(0, index): gen.generate(222, index, difficulty="medium")
        for index in range(3)
    }
    for profile in ("canonical_anchor", "repeated_colors"):
        grid = grids[profile]
        h, w = len(grid), len(grid[0])
        seeds = gen._seed_cells(grid)
        assert all(r not in (0, h - 1) and c not in (0, w - 1) for r, c, _ in seeds)
        assert any(2 <= r <= h - 3 and 2 <= c <= w - 3 for r, c, _ in seeds)

    clipped = grids["clipped_border"]
    h, w = len(clipped), len(clipped[0])
    assert any(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in gen._seed_cells(clipped))
