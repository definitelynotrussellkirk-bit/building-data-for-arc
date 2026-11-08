"""Focused regressions for the red-component size-spectrum generator."""
from __future__ import annotations

import importlib
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "52d56c2a0191"
EXPECTED_RULE_HASH = "5c9566dd0981"
SCENE_PROFILES = ("canonical", "repeated", "diagonal", "large")
CANVAS_PROFILES = (
    "h10_w12_p7",
    "h10_w13_p5",
    "h11_w10_p4",
    "h13_w11_p5",
    "h13_w13_p5",
)


def _load_generator():
    try:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError:
        source = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(f"task_generator_{TASK_ID}", source)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


gen = _load_generator()
ROOT = find_root(__file__)


def _red_sizes(grid, *, diagonal=False):
    height, width = len(grid), len(grid[0])
    seen = set()
    sizes = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 2 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            size = 0
            while stack:
                current_row, current_column = stack.pop()
                size += 1
                for dr, dc in directions:
                    nr, nc = current_row + dr, current_column + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(size)
    return sorted(sizes)


def _intended(grid):
    return [_red_sizes(grid)]


def test_rule_pin_and_every_canonical_pair_match_the_component_oracle():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _intended(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("scene_profile", SCENE_PROFILES)
@pytest.mark.parametrize("canvas_profile", CANVAS_PROFILES)
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_profiles_round_trip_in_every_band(scene_profile, canvas_profile, difficulty):
    requested = {"scene_profile": scene_profile, "canvas_profile": canvas_profile}
    grid = gen.generate(1701, 9, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == _intended(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"scene_profile": "missing"},
        {"scene_profile": 1},
        {"canvas_profile": "h9_w9_p2"},
        {"canvas_profile": True},
        {"texture": "no_red"},
    ],
)
def test_bad_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_bad_sample_indices_fail_loudly(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, sample_index)


def test_generated_semantic_profiles_have_the_promised_counterexamples():
    grids = {
        profile: gen.generate(77, 0, scene_profile=profile, canvas_profile="h10_w12_p7")
        for profile in SCENE_PROFILES
    }
    canonical_sizes = _red_sizes(grids["canonical"])
    assert len(canonical_sizes) == len(set(canonical_sizes))
    assert max(canonical_sizes) <= 5
    assert _red_sizes(grids["canonical"], diagonal=True) == canonical_sizes

    repeated_sizes = _red_sizes(grids["repeated"])
    assert len(repeated_sizes) > len(set(repeated_sizes))
    assert _red_sizes(grids["repeated"], diagonal=True) == repeated_sizes

    diagonal_sizes = _red_sizes(grids["diagonal"])
    assert _red_sizes(grids["diagonal"], diagonal=True) != diagonal_sizes
    assert max(diagonal_sizes) > 5

    large_sizes = _red_sizes(grids["large"])
    assert len(large_sizes) == 5
    assert len(large_sizes) > len(set(large_sizes))
    assert _red_sizes(grids["large"], diagonal=True) != large_sizes
    assert max(large_sizes) > 5


def test_every_canonical_shortcut_fits_public_pairs_and_generated_witnesses_refute_it():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "unique_red_sizes",
        "eight_connected_red_sizes",
        "clip_sizes_at_five",
    }
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    witnesses = {
        "unique_red_sizes": gen.generate(42, 0, scene_profile="repeated"),
        "eight_connected_red_sizes": gen.generate(42, 0, scene_profile="diagonal"),
        "clip_sizes_at_five": gen.generate(42, 0, scene_profile="large"),
    }
    for name, grid in witnesses.items():
        assert gen.CANONICAL_SHORTCUTS[name](grid) != gen.rule_mirror(grid), name


def test_default_schedule_and_all_query_rotations_refute_every_competitor():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for index in range(start, start + 4):
                grid = gen.generate(661_029, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": _intended(grid)})
            assert [gen.observe_overrides(pair["input"])["scene_profile"] for pair in pairs] == [
                SCENE_PROFILES[index % 4] for index in range(start, start + 4)
            ]
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_generation_is_deterministic_rng_pure_and_covers_every_canvas_profile_per_band():
    for difficulty in ("easy", "medium", "hard"):
        observed_canvases = set()
        observed_scenes = set()
        for index in range(80):
            seed = 80_000 + index
            state = random.getstate()
            grid = gen.generate(seed, index, difficulty=difficulty)
            assert random.getstate() == state
            assert grid == gen.generate(seed, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            observed_canvases.add(observed["canvas_profile"])
            observed_scenes.add(observed["scene_profile"])
        assert observed_canvases == set(CANVAS_PROFILES)
        assert observed_scenes == set(SCENE_PROFILES)


def test_self_check_rejects_no_red_and_malformed_inputs():
    bad = [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(10)],
        [[0] * 12 for _ in range(10)],
        [[3 if (row + column) % 7 == 0 else 0 for column in range(12)] for row in range(10)],
    ]
    for grid in bad:
        assert gen.self_check(grid)


def test_declared_witnesses_are_real_rival_disagreements():
    grids = [gen.generate(991_337, index) for index in range(16)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        predicate = gen.SEMANTIC_WITNESSES[witness_name]
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(predicate(grid) and rival(grid) != gen.rule_mirror(grid) for grid in grids)


def test_default_sampler_has_broad_count_output_support():
    outputs = {
        tuple(_red_sizes(gen.generate(seed, index)))
        for seed in range(0, 24 * 101, 101)
        for index in range(6)
    }
    # The lint diversity probe evaluates the same 24-by-6 seed/index lattice.
    # Keep well above its 35% floor rather than hiding a collapsed sampler behind
    # a false finite-codomain declaration.
    assert len(outputs) >= 60


def test_difficulty_bands_change_surface_form_without_changing_exact_profiles():
    grids = {
        difficulty: gen.generate(314159, 11, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    assert len({tuple(tuple(row) for row in grid) for grid in grids.values()}) == 3
    observations = {difficulty: gen.observe_overrides(grid) for difficulty, grid in grids.items()}
    assert len({tuple(sorted(value.items())) for value in observations.values()}) == 1
