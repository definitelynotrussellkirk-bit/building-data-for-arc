"""Focused semantic tests for the 40ad7195c775 stripe-route generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.40ad7195c775.generator"
)

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/7e576d6e__40ad7195c775.json",
    ROOT / "data/base/solutions/augmented/7e576d6e__30ac55d7fb96.json",
)


def _canonical_rows():
    with CANONICAL.open(encoding="utf-8") as handle:
        return [
            row
            for line in handle
            if (row := json.loads(line)).get("task_id") == gen.TASK_ID
        ]


def _canonical_pairs():
    return [
        pair
        for row in _canonical_rows()
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _independent_scene(grid):
    """Recover semantic roles and normalized geometry without generator helpers."""
    counts = Counter(value for row in grid for value in row)
    background = min(counts, key=lambda color: (-counts[color], color))
    endpoint = next(color for color in sorted(counts) if counts[color] == 2)
    others = [color for color in sorted(counts) if color not in (background, endpoint)]
    stripe = next(color for color in others if counts[color] > 30)
    waypoint = next(
        color for color in others if color != stripe and 2 < counts[color] < 30
    )
    stripe_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == stripe
    ]
    row_peak = max(Counter(row for row, _ in stripe_cells).values())
    col_peak = max(Counter(col for _, col in stripe_cells).values())
    orientation = gen.HORIZONTAL if row_peak > col_peak else gen.VERTICAL
    normalized = copy.deepcopy(grid) if orientation == gen.HORIZONTAL else _transpose(grid)
    endpoints = sorted(
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == endpoint
    )
    stripes = []
    for row, values in enumerate(normalized):
        if sum(value == stripe for value in values) < len(values) - 5:
            continue
        marker_cols = [col for col, value in enumerate(values) if value == waypoint]
        assert len(marker_cols) == 3
        assert marker_cols == list(range(marker_cols[0], marker_cols[0] + 3))
        stripes.append((row, marker_cols[1]))
    palette = (background, endpoint, stripe, waypoint)
    geometry = (orientation, endpoints[0], endpoints[1], tuple(stripes))
    return palette, geometry, normalized


def _paint(output, row1, col1, row2, col2, color):
    assert row1 == row2 or col1 == col2
    if row1 == row2:
        for col in range(min(col1, col2), max(col1, col2) + 1):
            output[row1][col] = color
    else:
        for row in range(min(row1, row2), max(row1, row2) + 1):
            output[row][col1] = color


def _independent_oracle(grid):
    palette, geometry, normalized = _independent_scene(grid)
    _, endpoint, _, _ = palette
    orientation, start, goal, stripes = geometry
    output = copy.deepcopy(normalized)
    current_row, current_col = start[0] + 1, start[1]
    for stripe_row, marker_col in stripes:
        _paint(output, current_row, current_col, stripe_row - 1, current_col, endpoint)
        _paint(output, stripe_row - 1, current_col, stripe_row - 1, marker_col, endpoint)
        output[stripe_row][marker_col] = endpoint
        current_row, current_col = stripe_row + 1, marker_col
    for row in range(current_row, goal[0]):
        output[row][current_col] = endpoint
    _paint(output, goal[0], current_col, goal[0], goal[1], endpoint)
    return output if orientation == gen.HORIZONTAL else _transpose(output)


def _independent_profile(grid):
    """Return the complete official geometry profile, ignoring lawful color renaming."""
    _, geometry, _ = _independent_scene(grid)
    official = {
        _independent_scene(pair["input"])[1]
        for pair in _canonical_pairs()
    }
    return geometry if geometry in official else None


def test_identity_version_normalized_hash_and_curriculum_size():
    assert gen.GENERATOR_ID == gen.TASK_ID == "40ad7195c775"
    assert gen.VERSION == "3.0.0"
    assert len(gen.GEOMETRIES) == 32
    assert gen.PALETTE_COUNT == 3024
    assert gen.SCENE_COUNT == 96768
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    normalized = " ".join(next(iter(rules)).split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_canonical_inventory_has_two_rows_eight_occurrences_and_four_inputs():
    rows = _canonical_rows()
    pairs = _canonical_pairs()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    assert len(rows) == 2
    assert len(pairs) == 8
    assert len({_key(pair["input"]) for pair in pairs}) == 4
    assert {
        gen.canonical_profile_signature(pair["input"]) for pair in pairs
    } == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_occurrence_matches_independent_oracle(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original


def test_canonical_geometries_palettes_and_frequencies_are_exact():
    expected_counts = ((808, 2, 81, 9), (808, 2, 81, 9),
                       (778, 2, 108, 12), (778, 2, 108, 12))
    unique = {}
    for pair in _canonical_pairs():
        profile = gen.canonical_profile_signature(pair["input"])
        unique.setdefault(profile, pair["input"])
    for index, profile in enumerate(gen.PUBLIC_PROFILES):
        palette, geometry, _ = _independent_scene(unique[profile])
        counts = Counter(value for row in unique[profile] for value in row)
        assert palette == gen.PUBLIC_PALETTES[index]
        assert geometry == gen.PUBLIC_GEOMETRIES[index]
        assert tuple(counts[color] for color in palette) == expected_counts[index]


def test_all_thirty_two_geometries_are_unique_valid_and_cover_required_branches():
    assert len(set(gen.GEOMETRIES)) == 32
    branches = set()
    for index, geometry in enumerate(gen.GEOMETRIES):
        grid = gen._make_grid(geometry, (1, 2, 3, 4))
        palette, recovered, _ = _independent_scene(grid)
        assert palette == (1, 2, 3, 4)
        assert recovered == geometry
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_code": index * gen.PALETTE_COUNT}
        branches.add((geometry[0], len(geometry[3])))
    assert branches == {
        (gen.HORIZONTAL, 3), (gen.HORIZONTAL, 4),
        (gen.VERTICAL, 3), (gen.VERTICAL, 4),
    }


def test_plausible_cross_profile_recombination_is_not_an_official_profile():
    unique = {}
    for pair in _canonical_pairs():
        _, geometry, _ = _independent_scene(pair["input"])
        unique.setdefault(geometry, pair["input"])
    geometries = list(unique)
    first, second = geometries[0], geometries[1]
    recombined = (first[0], first[1], first[2], second[3])
    assert recombined not in set(geometries)
    grid = gen._make_grid(recombined, (1, 2, 3, 4))
    assert _independent_scene(grid)[1] == recombined
    assert _independent_profile(grid) is None


def test_palette_inventory_is_every_ordered_choice_of_four_nonzero_colors():
    assert len(gen.PALETTES) == len(set(gen.PALETTES)) == 3024
    assert all(len(set(palette)) == 4 and set(palette) <= set(range(1, 10))
               for palette in gen.PALETTES)
    assert gen.PALETTES[0] == (1, 2, 3, 4)
    assert gen.PALETTES[-1] == (9, 8, 7, 6)


@pytest.mark.parametrize(
    "profile,code",
    zip(gen.PUBLIC_PROFILES, (931, 5484, 6342, 11511)),
)
def test_forced_public_codes_are_exact_fresh_canonical_inputs(profile, code):
    canonical = next(
        pair["input"] for pair in _canonical_pairs()
        if gen.canonical_profile_signature(pair["input"]) == profile
    )
    first = gen.generate(1, 2, scene_code=code)
    second = gen.generate(999, 88, difficulty="hard", scene_code=code)
    assert first == second == canonical
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert gen.canonical_family_signature(first) == profile
    assert gen.observe_overrides(first) == {"scene_code": code}


@pytest.mark.parametrize("code", [0, 1, 3023, 3024, 12000, 48000, 96766, 96767])
def test_forced_scene_codes_are_exact_observable_and_semantically_valid(code):
    grid = gen.generate(7, 9, scene_code=code)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_code": code}
    assert gen.rule_mirror(grid) == _independent_oracle(grid)


def test_sparse_scene_code_probe_is_injective_and_exactly_recoverable():
    codes = list(range(0, gen.SCENE_COUNT, 97)) + [gen.SCENE_COUNT - 1]
    grids = [gen.generate(0, 0, scene_code=code) for code in codes]
    assert len({_key(grid) for grid in grids}) == len(codes)
    assert [gen.observe_overrides(grid)["scene_code"] for grid in grids] == codes


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("stream", ["equal", "fixed"])
def test_five_thousand_scene_schedule_is_unique_balanced_and_exact(stream, difficulty):
    codes = [
        gen._natural_scene_code(index if stream == "equal" else 7000, index, difficulty)
        for index in range(5000)
    ]
    geometry_indexes = [code // gen.PALETTE_COUNT for code in codes]
    public = [index for index in geometry_indexes if index < 4]
    assert len(set(codes)) == 5000
    assert len(public) == 1000
    assert Counter(public) == Counter({0: 250, 1: 250, 2: 250, 3: 250})
    assert set(geometry_indexes) == set(range(32))
    stripe_counts = Counter(
        len(gen.GEOMETRIES[geometry_index][3])
        for geometry_index in geometry_indexes
    )
    if difficulty == "easy":
        assert stripe_counts[3] > 2 * stripe_counts[4]
    elif difficulty == "hard":
        assert stripe_counts[4] > 2 * stripe_counts[3]
    else:
        assert abs(stripe_counts[3] - stripe_counts[4]) <= 30


def test_four_band_health_schedule_is_globally_unique():
    codes = []
    for band_index, difficulty in enumerate((None, "easy", "medium", "hard")):
        codes.extend(
            gen._natural_scene_code(band_index * 100000 + index, index, difficulty)
            for index in range(1000)
        )
    assert len(set(codes)) == len(codes) == 4000


def test_seed_and_sample_index_each_materially_affect_natural_generation():
    assert len({gen._natural_scene_code(seed, 7, "medium") for seed in range(1000)}) >= 250
    assert len({gen._natural_scene_code(7000, sample, "medium") for sample in range(5000)}) == 5000


def test_many_seed_and_linter_streams_have_full_input_output_pair_diversity():
    many = [
        gen.generate(1 + episode * 101, sample_index)
        for episode in range(50)
        for sample_index in range(6)
    ]
    assert len({_key(grid) for grid in many}) == 300
    assert len({(_key(grid), _key(gen.rule_mirror(grid))) for grid in many}) == 300
    linter = [
        gen.generate(episode * 101, sample_index)
        for episode in range(24)
        for sample_index in range(6)
    ]
    assert len({_key(grid) for grid in linter}) == 144
    assert len({_key(gen.rule_mirror(grid)) for grid in linter}) == 144


def test_generated_distribution_matches_dense_official_family():
    branches = set()
    palettes = set()
    for index in range(400):
        grid = gen.generate(index, index, difficulty="medium")
        palette, geometry, _ = _independent_scene(grid)
        counts = Counter(value for row in grid for value in row)
        stripe_count = len(geometry[3])
        assert len(grid) == len(grid[0]) == 30
        assert 0 not in counts and len(counts) == 4
        assert tuple(counts[color] for color in palette) == (
            808 if stripe_count == 3 else 778,
            2,
            81 if stripe_count == 3 else 108,
            9 if stripe_count == 3 else 12,
        )
        branches.add((geometry[0], stripe_count))
        palettes.add(palette)
    assert branches == {
        (gen.HORIZONTAL, 3), (gen.HORIZONTAL, 4),
        (gen.VERTICAL, 3), (gen.VERTICAL, 4),
    }
    assert len(palettes) >= 300


def test_output_is_endpoint_colored_route_and_preserves_every_other_cell():
    for code in (0, 931, 5484, 6342, 11511, 48000, 96767):
        grid = gen.generate(1, 2, scene_code=code)
        output = gen.rule_mirror(grid)
        palette, geometry, normalized = _independent_scene(grid)
        endpoint = palette[1]
        expected = _independent_oracle(grid)
        assert output == expected
        changes = [
            (row, col)
            for row in range(30)
            for col in range(30)
            if grid[row][col] != output[row][col]
        ]
        assert changes
        assert all(output[row][col] == endpoint for row, col in changes)
        for row, col in changes:
            assert expected[row][col] == endpoint
        orientation, _, _, stripes = geometry
        normalized_output = output if orientation == gen.HORIZONTAL else _transpose(output)
        for stripe_row, marker_col in stripes:
            assert normalized[stripe_row][marker_col] == palette[3]
            assert normalized_output[stripe_row][marker_col] == endpoint


def test_rule_mirror_is_broad_input_pure_and_a_b_a_stable():
    first = gen.generate(71, 4, scene_code=1)
    second = gen.generate(72, 5, scene_code=48000)
    original = copy.deepcopy(first)
    out_a1 = gen.rule_mirror(first)
    out_b = gen.rule_mirror(second)
    out_a2 = gen.rule_mirror(first)
    assert out_a1 == out_a2 == _independent_oracle(first)
    assert out_b == _independent_oracle(second)
    assert first == original

    # A structurally valid 15x15 mirror input lies outside the exact curriculum
    # yet still exercises the broad executable rule semantics.
    broad = [[1] * 15 for _ in range(15)]
    broad[0][2] = broad[14][12] = 2
    for row, marker in ((3, 4), (7, 10), (11, 6)):
        broad[row] = [3] * 15
        for col in range(marker - 1, marker + 2):
            broad[row][col] = 4
    assert gen.self_check(broad)
    assert gen.rule_mirror(broad) == _independent_oracle(broad)


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(20260722)
    state = random.getstate()
    first = gen.generate(777, 21, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(777, 21, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(777, 21, difficulty="hard") == second


@pytest.mark.parametrize("bad", [
    [],
    [[]],
    [[1, 2], [1]],
    [[False] * 30 for _ in range(30)],
    [[10] * 30 for _ in range(30)],
    [[1] * 29 for _ in range(30)],
    [[1] * 30 for _ in range(29)],
    [[0] * 30 for _ in range(30)],
    [[1] * 30 for _ in range(30)],
])
def test_malformed_and_degenerate_inputs_fail_closed(bad):
    assert gen.self_check(bad)
    assert gen.observe_overrides(bad) == {}


def test_role_geometry_and_exact_reconstruction_mutations_fail_closed():
    grid = gen.generate(1, 1, scene_code=48000)
    palette, geometry, _ = _independent_scene(grid)
    orientation, start, _, stripes = geometry
    normalized = grid if orientation == gen.HORIZONTAL else _transpose(grid)

    endpoint_mutation = copy.deepcopy(normalized)
    endpoint_mutation[start[0]][start[1]] = palette[0]
    if orientation == gen.VERTICAL:
        endpoint_mutation = _transpose(endpoint_mutation)
    assert gen.self_check(endpoint_mutation)
    assert gen.observe_overrides(endpoint_mutation) == {}

    marker_mutation = copy.deepcopy(normalized)
    stripe_row, marker_col = stripes[0]
    marker_mutation[stripe_row][marker_col] = palette[2]
    if orientation == gen.VERTICAL:
        marker_mutation = _transpose(marker_mutation)
    assert gen.self_check(marker_mutation)
    assert gen.observe_overrides(marker_mutation) == {}

    background_mutation = copy.deepcopy(grid)
    background_mutation[15][15] = palette[1]
    assert gen.self_check(background_mutation)
    assert gen.observe_overrides(background_mutation) == {}


@pytest.mark.parametrize("overrides", [
    {"scene_code": -1},
    {"scene_code": gen.SCENE_COUNT},
    {"scene_code": "1"},
    {"scene_code": True},
    {"unknown": 1},
])
def test_invalid_controls_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="extreme")


def test_base_authorities_are_byte_identical_to_canonical_rule():
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    canonical = next(iter(rules))
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["raw_code"] == target["target_code"] == canonical
        assert target["needs_conversion"] is False


def test_base_descriptions_explain_roles_route_transpose_and_negative_constraints():
    required_target = ("frequency-identified", "staircase", "middle", "transpose", "preserve")
    required_steps = ("modal background", "more than 30", "transpose", "three-cell", "lower endpoint")
    required_negatives = ("black", "numeric value", "middle cell", "outside", "horizontal")
    canonical_primitives = [
        "color-frequency", "mode", "find-first", "grid-colors", "filter",
        "find-color", "max-of", "count-if", "first", "map", "second",
        "rows", "cols", "at", "range", "nth", "recolor-cells",
        "set-cell", "transpose",
    ]
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        description = base["description_target"]
        assert description["source"] == "canonical.written_solution"
        assert description["target_status"] == "source_written"
        assert all(word in description["target_text"].lower() for word in required_target)
        steps = " ".join(description["solution_steps"]).lower()
        negatives = " ".join(description["negative_constraints"]).lower()
        assert all(word in steps for word in required_steps)
        assert all(word in negatives for word in required_negatives)
        assert base["primitive_metadata"]["primitive_chain"] == canonical_primitives
