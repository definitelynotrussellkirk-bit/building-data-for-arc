"""Focused semantic tests for the 48fee61713bb block-stack generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator("48fee61713bb", root=ROOT)
CANONICAL = canonical_path(ROOT)
BASE_PATHS = (
    CANONICAL.parent.parent / "base/solutions/training/afe3afe9__48fee61713bb.json",
    CANONICAL.parent.parent / "base/solutions/augmented/afe3afe9__a352321255bb.json",
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


def _independent_analyze(grid, color):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    block_height = (bottom - top + 3) // 4
    block_width = (right - left + 3) // 4
    blocks = tuple(
        tuple(
            int(grid[top + 4 * block_row][left + 4 * block_col] == color)
            for block_col in range(block_width)
        )
        for block_row in range(block_height)
    )
    return color, block_height, block_width, blocks, top, left


def _independent_oracle(grid):
    """Implement the canonical count-and-stack rule without generator helpers."""
    infos = [
        _independent_analyze(grid, color)
        for color in sorted({value for row in grid for value in row} - {0, 1})
    ]
    main = next(info for info in infos if info[0] == 8)
    smalls = [info for info in infos if info[0] != 8]
    horizontal = main[2] > main[1]
    main_at_end = (
        main[4] > sum(info[4] for info in smalls) // len(smalls)
        if horizontal
        else main[5] > sum(info[5] for info in smalls) // len(smalls)
    )
    slice_count = main[2] if horizontal else main[1]
    slices = []
    for index in range(slice_count):
        main_count = (
            sum(row[index] for row in main[3])
            if horizontal else sum(main[3][index])
        )
        aligned = None
        local_index = None
        for small in smalls:
            offset = (
                (small[5] - main[5]) // 4
                if horizontal else (small[4] - main[4]) // 4
            )
            extent = small[2] if horizontal else small[1]
            if offset <= index < offset + extent:
                aligned = small
                local_index = index - offset
                break
        if aligned is None:
            slices.append((main_count, 0, 0))
        else:
            small_count = (
                sum(row[local_index] for row in aligned[3])
                if horizontal else sum(aligned[3][local_index])
            )
            slices.append((main_count, small_count, aligned[0]))
    max_height = max(main_count + small_count for main_count, small_count, _ in slices)
    stacks = []
    for main_count, small_count, small_color in slices:
        padding = [0] * (max_height - main_count - small_count)
        cyan = [8] * main_count
        small = [small_color] * small_count
        stacks.append(padding + small + cyan if main_at_end else cyan + small + padding)
    if horizontal:
        return [
            [stacks[col][row] for col in range(slice_count)]
            for row in range(max_height)
        ]
    return stacks


def _canonical_unique():
    unique = {}
    for pair in _canonical_pairs():
        profile = gen.canonical_profile_signature(pair["input"])
        unique.setdefault(profile, pair)
    return unique


def test_identity_version_rule_hash_and_catalog_dimensions():
    assert gen.GENERATOR_ID == gen.TASK_ID == "48fee61713bb"
    assert gen.VERSION == "4.1.0"
    assert (gen.MAIN_COUNT, gen.SMALL_COUNT, gen.PALETTE_COUNT) == (512, 290, 42)
    assert gen.SCENE_COUNT == 7_233_945_600
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
    assert set(_canonical_unique()) == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_occurrence_matches_independent_oracle(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original


@pytest.mark.parametrize("edge", range(4))
def test_public_profiles_reconstruct_exact_canonical_scenes(edge):
    profile = gen.PUBLIC_PROFILES[edge]
    pair = _canonical_unique()[profile]
    public = gen._public_grid(edge)
    assert public == pair["input"]
    assert gen.rule_mirror(public) == pair["output"]
    observed = gen.observe_overrides(public)
    assert gen._grid_from_code(observed["scene_code"]) == public


def test_main_pattern_bank_is_unique_pinned_and_slice_complete():
    assert len(gen.MAIN_PATTERNS) == len(set(gen.MAIN_PATTERNS)) == 512
    counts = set()
    for pattern in gen.MAIN_PATTERNS:
        assert len(pattern) == 7 and all(len(row) == 3 for row in pattern)
        assert all(any(row) for row in pattern)
        assert any(row[0] for row in pattern)
        assert any(row[2] for row in pattern)
        counts.add(sum(map(sum, pattern)))
    assert counts == set(range(10, 19))


def test_small_pattern_bank_is_complete_unique_and_slice_complete():
    assert len(gen.SMALL_PATTERNS) == len(set(gen.SMALL_PATTERNS)) == 290
    for pattern in gen.SMALL_PATTERNS:
        assert len(pattern) == 3 and all(len(row) == 3 for row in pattern)
        assert all(any(row) for row in pattern)
        assert any(row[0] for row in pattern)
        assert any(row[2] for row in pattern)


def test_palette_bank_is_every_ordered_pair_of_lawful_small_colors():
    assert len(gen.PALETTES) == len(set(gen.PALETTES)) == 42
    assert all(
        len(set(palette)) == 2 and set(palette) <= {2, 3, 4, 5, 6, 7, 9}
        for palette in gen.PALETTES
    )


@pytest.mark.parametrize(
    "code",
    (0, 1, 289, 290, 84_099, 84_100, 1_000_003, 7_233_945_599),
)
def test_mixed_radix_scene_codes_round_trip_exactly(code):
    decoded = gen._decode_scene(code)
    assert gen._encode_scene(*decoded) == code
    grid = gen._grid_from_code(code)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_code": code}
    assert gen.rule_mirror(grid) == _independent_oracle(grid)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_natural_1000_sample_lanes_are_unique_balanced_and_valid(band):
    grids = [gen.generate(17, index, difficulty=band) for index in range(1000)]
    assert len({_key(grid) for grid in grids}) == 1000
    assert all(gen.self_check(grid) == [] for grid in grids)
    facts = [gen._analysis(grid)["facts"] for grid in grids]
    assert Counter(fact["edge_name"] for fact in facts) == Counter(
        {name: 250 for name in gen.EDGE_NAMES}
    )
    assert {fact["palette"] for fact in facts} == set(gen.PALETTES)
    main_counts = {fact["main_ring_count"] for fact in facts}
    if band == "easy":
        assert min(main_counts) >= 16
    elif band == "medium":
        assert main_counts == {15}
    elif band == "hard":
        assert max(main_counts) <= 14
    else:
        assert min(main_counts) >= 10 and max(main_counts) <= 18
        assert len(main_counts) >= 4


def test_equal_counter_difficulty_lanes_are_pairwise_disjoint():
    sets = []
    for band in (None, "easy", "medium", "hard"):
        sets.append({_key(gen.generate(23, index, difficulty=band)) for index in range(600)})
    assert sum(len(values) for values in sets) == len(set().union(*sets))


@pytest.mark.parametrize(
    "counter",
    (
        lambda index: (90_000 + index, 0),
        lambda index: (90_000, index),
        lambda index: (90_000 + index, 90_000 + index),
    ),
)
def test_seed_only_sample_only_and_joint_streams_do_not_collapse(counter):
    inputs = set()
    outputs = set()
    edges = set()
    palettes = set()
    for index in range(600):
        seed, sample_index = counter(index)
        grid = gen.generate(seed, sample_index, difficulty="medium")
        facts = gen._analysis(grid)["facts"]
        inputs.add(_key(grid))
        outputs.add(_key(gen.rule_mirror(grid)))
        edges.add(facts["edge_name"])
        palettes.add(facts["palette"])
    assert len(inputs) == len(outputs) == 600
    assert edges == set(gen.EDGE_NAMES)
    assert palettes == set(gen.PALETTES)


def test_multi_pair_episode_schedule_is_unique_across_reused_local_indexes():
    inputs = set()
    outputs = set()
    for episode in range(50):
        for local_index in range(8):
            grid = gen.generate(48_200 + episode, local_index)
            inputs.add(_key(grid))
            outputs.add(_key(gen.rule_mirror(grid)))
    assert len(inputs) == len(outputs) == 400


def test_seed_and_sample_index_both_affect_natural_generation():
    assert gen.generate(2, 100) != gen.generate(3, 100)
    assert gen.generate(2, 100) != gen.generate(2, 101)
    assert gen.generate(2, 100) == gen.generate(2, 100)


def test_generation_returns_fresh_grids_and_does_not_touch_global_rng():
    first = gen.generate(5, 77)
    second = gen.generate(5, 77)
    assert first == second and first is not second and first[0] is not second[0]
    before = random.getstate()
    gen.generate(11, 13, difficulty="hard")
    assert random.getstate() == before


def test_rule_mirror_is_input_pure_on_diverse_generated_scenes():
    for edge in range(4):
        code = gen._encode_scene(edge, 7 + edge, 100 + edge, 40 + edge, 80 + edge)
        grid = gen._grid_from_code(code)
        original = copy.deepcopy(grid)
        assert gen.rule_mirror(grid) == _independent_oracle(grid)
        assert grid == original


def test_swapping_only_the_marker_edge_breaks_the_linked_profile():
    grid = gen._grid_from_code(0)
    grid[0] = [0] * 30
    grid[29] = [1] * 30
    assert gen.canonical_family_signature(grid) is None
    assert any("linked edge/layout" in error for error in gen.self_check(grid))


@pytest.mark.parametrize(
    "mutator",
    (
        lambda grid: grid.__setitem__(0, grid[0][:-1]),
        lambda grid: grid[0].__setitem__(0, 0),
        lambda grid: grid[2].__setitem__(18, 0),
        lambda grid: grid[3].__setitem__(18, 8),
        lambda grid: grid[2].__setitem__(1, 8),
        lambda grid: grid[2].__setitem__(17, 2),
    ),
)
def test_structural_mutations_are_rejected(mutator):
    grid = gen._public_grid(gen.TOP)
    mutator(grid)
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", (-1, gen.SCENE_COUNT, 1.5, True, "3"))
def test_invalid_scene_code_overrides_fail_loudly(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, scene_code=bad)


def test_unknown_override_and_difficulty_fail_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, mystery=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="extreme")


def test_base_sources_are_synced_and_descriptions_are_specific():
    rule = _canonical_rows()[0]["program_solution"]
    for path in BASE_PATHS:
        record = json.loads(path.read_text(encoding="utf-8"))
        target = record["racket_target"]
        assert target["raw_code"] == target["target_code"] == rule
        description = record["description_target"]
        assert description["source"] == description["target_status"] == "source_written"
        assert "hollow 3x3 rings" in description["target_text"]
        assert len(description["solution_steps"]) == 5
        assert len(description["negative_constraints"]) >= 3


def test_forced_scene_output_is_not_noop_or_constant():
    outputs = []
    for edge in range(4):
        code = gen._encode_scene(edge, edge, 20 * edge, 10 * edge, 15 * edge)
        grid = gen._grid_from_code(code)
        output = gen.rule_mirror(grid)
        assert output != grid
        assert len({value for row in output for value in row}) >= 3
        outputs.append(_key(output))
    assert len(set(outputs)) == 4
