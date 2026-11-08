from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("b159f935141a_generator", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def intended(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = (grid[r - 1][c], grid[r + 1][c], grid[r][c - 1], grid[r][c + 1])
            if grid[r][c] == 0 and arms[0] != 0 and len(set(arms)) == 1:
                out[r][c] = arms[0]
    return out


def test_exact_controls_are_observable_from_pixels():
    gen = load_generator()
    assert callable(getattr(gen, "observe_overrides", None)), "missing pixel observer"
    grid = gen.generate(
        17,
        5,
        grid_h=13,
        grid_w=17,
        n_plusses=3,
        n_decoys=6,
    )
    observed = gen.observe_overrides(grid)
    assert observed == {"grid_h": 13, "grid_w": 17, "n_plusses": 3, "n_decoys": 6}
    assert sum(a != b for before, after in zip(grid, intended(grid)) for a, b in zip(before, after)) == 3


def test_horizontal_only_canonical_shortcut_has_a_generated_counterexample():
    gen = load_generator()
    rival = getattr(gen, "CANONICAL_SHORTCUTS", {}).get("horizontal_only")
    witness = getattr(gen, "SEMANTIC_WITNESSES", {}).get("diagonal_cluster")
    assert callable(rival), "horizontal-only shortcut is undeclared"
    assert callable(witness), "horizontal-pair witness is undeclared"
    grid = gen.generate(19, 1, difficulty="easy")
    assert witness(grid)
    assert rival(grid) != intended(grid)


def test_default_schedule_contains_canonical_scale_and_contrastive_support():
    gen = load_generator()
    grids = [gen.generate(23, index, difficulty="hard") for index in range(4)]
    canonical_profiles = {(5, 7, 3), (6, 6, 3), (5, 8, 3), (5, 6, 3)}
    profiles = {
        (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))
        for grid in grids
    }
    assert profiles & canonical_profiles
    for name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert any(predicate(grid) for grid in grids), f"no scheduled witness for {name}"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 7.5},
        {"n_plusses": 0},
        {"n_decoys": 9},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    gen = load_generator()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_diagonal_decoy_counts_as_one_primary_observable_motif():
    gen = load_generator()
    grid = [[0] * 9 for _ in range(9)]
    gen._paint_decoy(grid, 4, 4, "diagonal", 2, 3)
    observed = gen.observe_overrides(grid)
    assert observed["n_decoys"] == 1


def test_default_contrastive_examples_stay_near_canonical_scale():
    gen = load_generator()
    grids = [
        gen.generate(31, sample_index, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
        for sample_index in (1, 2, 3)
    ]
    assert max(len(grid) * len(grid[0]) for grid in grids) <= 144
    assert max(sum(cell != 0 for row in grid for cell in row) for grid in grids) <= 24


def test_default_count_axes_span_multiple_observable_values():
    gen = load_generator()
    observed = [
        gen.observe_overrides(gen.generate(seed, sample_index, difficulty=difficulty))
        for difficulty in ("easy", "medium", "hard")
        for seed in range(12)
        for sample_index in (1, 2, 3)
    ]
    plus_counts = {item["n_plusses"] for item in observed}
    decoy_counts = {item["n_decoys"] for item in observed}
    assert max(plus_counts) - min(plus_counts) >= 2
    assert max(decoy_counts) - min(decoy_counts) >= 2
    assert min(decoy_counts) >= 2


def test_difficulty_bands_change_contrastive_instances():
    gen = load_generator()
    by_seed = [
        {
            repr(gen.generate(seed, seed, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        for seed in range(1, 9)
        if seed % gen.LESSON_SCHEDULE_PERIOD != 0
    ]
    assert any(len(instances) > 1 for instances in by_seed)


def test_canonical_schedule_records_every_exact_axis():
    gen = load_generator()
    from puzzle_generators import base as gen_base

    contexts = []
    gen_base.set_ctx_observer(contexts.append)
    try:
        grid = gen.generate(41, 0, difficulty="hard")
    finally:
        gen_base.set_ctx_observer(None)
    assert len(contexts) == 1
    draws = contexts[0].recorded_draws()
    assert {"grid_h", "grid_w", "n_plusses", "n_decoys"} <= set(draws)
    assert {name: draws[name] for name in ("grid_h", "grid_w", "n_plusses", "n_decoys")} == gen.observe_overrides(grid)


def test_every_cyclic_four_pair_episode_is_identifiable_under_all_query_rotations():
    gen = load_generator()
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for sample_index in range(start, start + 4):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": intended(grid)})
                for query_index in range(4):
                    query = pairs[query_index]
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    assert gen.lesson_identifiable(demos, query) == [], (
                        band,
                        seed,
                        start,
                        query_index,
                        gen.lesson_identifiable(demos, query),
                    )
