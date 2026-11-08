from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "78645c33b002"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASES = (
    ROOT / "data/base/solutions/training/eb5a1d5d__78645c33b002.json",
    ROOT / "data/base/solutions/augmented/eb5a1d5d__4a659dfef116.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def unique_canonical_pairs():
    pairs, seen = [], set()
    for row in canonical_rows():
        for pair in row.get("train", []) + row.get("test", []):
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def independent_layers(grid):
    height, width = len(grid), len(grid[0])
    bbox = 0, 0, height - 1, width - 1
    colors = []
    while True:
        row0, col0, row1, col1 = bbox
        outer = grid[row0][col0]
        colors.append(outer)
        different = [
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if grid[row][col] != outer
        ]
        if not different:
            return colors
        bbox = (
            min(row for row, _ in different),
            min(col for _, col in different),
            max(row for row, _ in different),
            max(col for _, col in different),
        )


def independent_oracle(grid):
    colors = independent_layers(grid)
    size = 2 * len(colors) - 1
    middle = size // 2
    return [
        [colors[len(colors) - 1 - max(abs(row - middle), abs(col - middle))] for col in range(size)]
        for row in range(size)
    ]


def frozen(grid):
    return tuple(map(tuple, grid))


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = unique_canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"] == independent_oracle(grid)
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.canonical_family_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert 2 <= analysis["facts"]["layer_count"] <= 6
    assert min(analysis["facts"]["innermost_shape"]) >= 3
    assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_output_is_one_ring_per_ordered_input_layer():
    grid = MODULE.generate(31, 1, scene_profile="six_layers")
    layers = independent_layers(grid)
    output = MODULE.rule_mirror(grid)
    assert len(output) == len(output[0]) == 2 * len(layers) - 1 == 11
    middle = len(output) // 2
    assert output[middle][middle] == layers[-1]
    for distance, color in enumerate(reversed(layers)):
        assert output[middle - distance][middle] == color


def test_thickness_and_offset_do_not_change_normalized_output():
    colors = [7, 2, 9]
    centered = MODULE._paint_nested(23, 25, [(2, 2, 2, 2), (3, 3, 3, 3)], colors)
    offcenter = MODULE._paint_nested(23, 25, [(1, 4, 3, 2), (4, 2, 2, 5)], colors)
    assert MODULE.rule_mirror(centered) == MODULE.rule_mirror(offcenter) == independent_oracle(centered)


def test_nonadjacent_color_can_repeat_at_center():
    grid = MODULE.generate(41, 2, scene_profile="repeated_colors")
    layers = MODULE._analysis(grid)["facts"]["layers"]
    assert layers[0] == layers[-1]
    assert all(first != second for first, second in zip(layers, layers[1:]))
    output = MODULE.rule_mirror(grid)
    assert output[0][0] == output[len(output) // 2][len(output) // 2]


def test_public_family_allows_only_d4_and_palette_nuisance():
    exact = MODULE.generate(1, 0, scene_profile="public_3")
    ordinary = next(
        grid
        for seed in range(500)
        for grid in [MODULE.generate(60_000 + seed, seed)]
        if MODULE._analysis(grid)["scene_profile"] == "public_3" and grid != exact
    )
    assert MODULE.canonical_profile_signature(ordinary) is None
    assert MODULE.canonical_family_signature(ordinary) == "public_3"
    assert MODULE._analysis(ordinary)["facts"]["color_pattern"] == (0, 1, 2, 3)


def test_lawful_recombination_is_not_mislabeled_public_family():
    grid = MODULE.generate(71, 4, scene_profile="rectangular_centered")
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE._analysis(grid)["scene_profile"] == "rectangular_centered"


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="wide_offcenter")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="wide_offcenter")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="wide_offcenter") == second


def test_default_prior_covers_every_profile_and_public_family():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1400)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        assert sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles) >= 500
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_strong_input_and_lawful_output_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(300)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 290
    assert len({frozen(output) for output in outputs}) >= 255
    assert {len(output) for output in outputs} == {3, 5, 7, 9, 11}
    assert {value for output in outputs for row in output for value in row} == set(range(10))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 12 for _ in range(11)],
        [[0] * 33 for _ in range(12)],
        [[0] * 12 for _ in range(33)],
        [[0] * 12 for _ in range(11)] + [[0] * 11],
        [[False] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[4] * 12 for _ in range(12)],
    ],
)
def test_malformed_or_single_layer_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="rectangular_centered")

    breached = [row[:] for row in grid]
    breached[0][-1] = (breached[0][0] + 1) % 10
    assert MODULE.self_check(breached)

    shuffled = [row[:] for row in grid]
    inner_top = MODULE._analysis(grid)["facts"]["bboxes"][1][0]
    shuffled[inner_top - 1], shuffled[inner_top] = shuffled[inner_top], shuffled[inner_top - 1]
    assert MODULE.self_check(shuffled)

    singleton = [[0] * 12 for _ in range(12)]
    singleton[6][6] = 2
    assert MODULE.self_check(singleton)

    short_line = [[0] * 12 for _ in range(12)]
    short_line[6][5:8] = [2, 2, 2]
    assert MODULE.self_check(short_line)

    inner_2x2 = [[0] * 12 for _ in range(12)]
    for row in (5, 6):
        for col in (5, 6):
            inner_2x2[row][col] = 2
    assert MODULE.self_check(inner_2x2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "solid_block"},
        {"n_layers": 4},
        {"grid_h": 22},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_exactly_synchronized():
    sources = {row["program_solution"] for row in canonical_rows()}
    assert len(sources) == 1
    source = sources.pop()
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "d565393b63e9"
    for path in BASES:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
