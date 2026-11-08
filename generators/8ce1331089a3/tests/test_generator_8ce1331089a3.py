"""Focused semantic regression tests for generator 8ce1331089a3."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_8ce1331089a3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "8ce1331089a3" and row.get("source") == "training":
                return [*row["train"], *row["test"]]
    raise AssertionError("canonical task 8ce1331089a3 is missing")


def interior_values(grid: list[list[int]]) -> list[int]:
    return [
        grid[row][col]
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] != 0
    ]


def edge_colors(grid: list[list[int]]) -> tuple[int, int, int, int]:
    return grid[0][1], grid[-1][1], grid[1][0], grid[1][-1]


def pair_for(gen, grid: list[list[int]]) -> dict:
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_owned_and_python_mirror_matches_outputs() -> None:
    gen = load_generator()
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_default_schedule_matches_canonical_profile_support_and_keeps_distractors() -> None:
    gen = load_generator()
    expected_profiles = {(12, 12, 7), (10, 15, 6), (14, 11, 6), (14, 17, 8)}
    for band in ("easy", "medium", "hard"):
        observed_profiles = set()
        for sample_index in range(8):
            grid = gen.generate(1729, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            palette = set(value for row in grid for value in row)
            observed_profiles.add((len(grid), len(grid[0]), len(palette)))
            edges = set(edge_colors(grid))
            interior = interior_values(grid)
            assert any(value in edges for value in interior)
            assert any(value not in edges for value in interior)
        assert observed_profiles == expected_profiles


def test_exact_override_boundaries_round_trip_in_every_band() -> None:
    gen = load_generator()
    cases = (
        {"grid_h": 8, "grid_w": 8, "n_pixels": 6, "palette_size": 6},
        {"grid_h": 18, "grid_w": 18, "n_pixels": 16, "palette_size": 8},
        {"grid_h": 8, "grid_w": 18, "n_pixels": 16, "palette_size": 7},
        {"grid_h": 18, "grid_w": 8, "n_pixels": 16, "palette_size": 8},
    )
    for band in ("easy", "medium", "hard"):
        for sample_index, overrides in enumerate(cases):
            grid = gen.generate(991 + sample_index, 31 + sample_index, difficulty=band, **overrides)
            assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
            assert gen.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_fail_closed() -> None:
    gen = load_generator()
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="palette_size"):
        gen.generate(0, 0, palette_size=5)
    with pytest.raises(ValueError, match="n_pixels"):
        gen.generate(0, 0, n_pixels=17)


def test_rule_moves_matching_pixels_and_removes_distractors() -> None:
    gen = load_generator()
    grid = gen.generate(2026, 3, difficulty="hard")
    output = gen.rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    top, bottom, left, right = edge_colors(grid)
    for row in range(1, h - 1):
        for col in range(1, w - 1):
            value = grid[row][col]
            if value == top:
                assert output[1][col] == value
            elif value == bottom:
                assert output[h - 2][col] == value
            elif value == left:
                assert output[row][1] == value
            elif value == right:
                assert output[row][w - 2] == value
            elif value != 0:
                assert all(output[r][c] != value for r in range(h) for c in range(w))
    assert gen.self_check(output)


def test_semantic_contract_witnesses_fire_and_named_rivals_are_refuted() -> None:
    gen = load_generator()
    assert set(gen.SEMANTIC_WITNESSES) == {
        "routes_to_top",
        "routes_to_bottom",
        "routes_to_left",
        "routes_to_right",
        "removes_distractor",
        "preserves_multiple_same_route",
    }
    assert set(gen.SEMANTIC_RIVALS) >= {
        "clear_interior",
        "keep_distractors",
        "move_first_per_route",
        "swap_vertical_routes",
        "swap_horizontal_routes",
    }
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        disagreements = {name: 0 for name in gen.SEMANTIC_RIVALS}
        for sample_index in range(24):
            grid = gen.generate(4000 + sample_index, sample_index, difficulty=band)
            expected = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hits[name] += int(witness(grid))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                disagreements[name] += int(rival(copy.deepcopy(grid)) != expected)
        assert all(hits.values()), (band, hits)
        assert all(disagreements.values()), (band, disagreements)


def test_every_sliding_three_demo_window_is_identifiable() -> None:
    gen = load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [
                pair_for(gen, gen.generate(7300 + start, sample_index, difficulty=band))
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1)
            ]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_self_check_rejects_targeted_impostors() -> None:
    gen = load_generator()
    valid = gen.generate(5150, 0, difficulty="medium")
    h, w = len(valid), len(valid[0])

    bad_corner = copy.deepcopy(valid)
    bad_corner[0][0] = bad_corner[0][1]
    assert gen.self_check(bad_corner)

    no_distractor = copy.deepcopy(valid)
    edges = set(edge_colors(no_distractor))
    replacement = no_distractor[0][1]
    for row in range(1, h - 1):
        for col in range(1, w - 1):
            if no_distractor[row][col] not in edges | {0}:
                no_distractor[row][col] = replacement
    assert gen.self_check(no_distractor)

    adjacent_to_border = copy.deepcopy(valid)
    source = next(
        (r, c)
        for r in range(2, h - 2)
        for c in range(2, w - 2)
        if adjacent_to_border[r][c] != 0
    )
    value = adjacent_to_border[source[0]][source[1]]
    adjacent_to_border[source[0]][source[1]] = 0
    adjacent_to_border[1][source[1]] = value
    assert gen.self_check(adjacent_to_border)


def test_replay_freshness_and_process_global_rng_purity() -> None:
    gen = load_generator()
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(918, 27, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(918, 27, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_difficulty_bands_change_layout_without_changing_canonical_profile() -> None:
    gen = load_generator()
    for sample_index in range(4):
        grids = [
            gen.generate(6060, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 3
        expected = gen.CANONICAL_PROFILES[sample_index]
        for grid in grids:
            facts = gen.observe_overrides(grid)
            assert (
                facts["grid_h"],
                facts["grid_w"],
                facts["palette_size"],
                facts["n_pixels"],
            ) == expected
