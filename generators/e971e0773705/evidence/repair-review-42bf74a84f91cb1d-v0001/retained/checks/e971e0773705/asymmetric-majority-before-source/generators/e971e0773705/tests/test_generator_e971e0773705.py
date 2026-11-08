"""Focused semantic tests for the e971e0773705 T-count generator."""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.e971e0773705 import generator as gen


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/d5c634a2__e971e0773705.json",
    ROOT / "data/base/solutions/augmented/d5c634a2__385c3447384b.json",
)


def _canonical_rows():
    rows = []
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    return [
        pair
        for row in _canonical_rows()
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]


def _components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for point in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        result.append(tuple(sorted(cells)))
    return tuple(result)


def _normalized(component):
    min_row = min(row for row, _ in component)
    min_col = min(col for _, col in component)
    return tuple(sorted((row - min_row, col - min_col) for row, col in component))


def _independent_oracle(grid):
    top_count = 0
    bottom_count = 0
    for component in _components(grid):
        top_row = min(row for row, _ in component)
        if sum(row == top_row for row, _ in component) >= 3:
            top_count += 1
        else:
            bottom_count += 1
    output = [[0] * 6 for _ in range(3)]
    green = ((0, 0), (2, 0), (0, 2), (2, 2))
    blue = ((0, 3), (2, 3), (0, 5), (2, 5))
    for row, col in green[:min(bottom_count, 4)]:
        output[row][col] = 3
    for row, col in blue[:min(top_count, 4)]:
        output[row][col] = 1
    return output


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _code(profile):
    return gen.PROFILE_TO_CODE[profile]


def test_identity_and_hash_pin():
    assert gen.GENERATOR_ID == gen.TASK_ID == "e971e0773705"
    assert gen.VERSION == "3.0.1"
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 24
    rules = {" ".join(row["program_solution"].split()) for row in _canonical_rows()}
    assert len(rules) == 1
    assert hashlib.sha256(next(iter(rules)).encode()).hexdigest()[:12] == gen.RULE_HASH


def test_canonical_inventory_has_two_rows_and_eighteen_occurrences():
    rows = _canonical_rows()
    pairs = _canonical_pairs()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    assert len(rows) == 2
    assert len(pairs) == 18
    assert len({_grid_key(pair["input"]) for pair in pairs}) == 9


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_pair_matches_independent_oracle(pair):
    original = [row[:] for row in pair["input"]]
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original
    assert gen.self_check(pair["input"]) == []


def test_all_nine_unique_canonical_inputs_have_exact_profile_anchors():
    profiles = {}
    for pair in _canonical_pairs():
        profile = gen.canonical_profile_signature(pair["input"])
        assert profile in gen.PUBLIC_PROFILES
        profiles[_grid_key(pair["input"])] = profile
    assert set(profiles.values()) == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("profile", gen.PUBLIC_PROFILES)
def test_forced_public_profiles_return_exact_fresh_anchors(profile):
    first = gen.generate(91, 7, scene_code=_code(profile))
    second = gen.generate(91, 7, scene_code=_code(profile))
    assert first == second == gen._PUBLIC_INPUTS[profile]
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert gen.canonical_profile_signature(first) == profile
    assert gen.canonical_family_signature(first) == profile
    assert gen.observe_overrides(first) == {"scene_code": _code(profile)}


@pytest.mark.parametrize("profile,counts", gen.GENERAL_COUNTS.items())
def test_forced_general_profiles_realize_exact_counts(profile, counts):
    grid = gen.generate(500 + len(profile), 19, difficulty="hard", scene_code=_code(profile))
    facts = gen._analysis(grid)["facts"]
    assert (facts["top_count"], facts["bottom_count"]) == counts
    assert gen.observe_overrides(grid) == {"scene_code": _code(profile)}
    assert gen.canonical_family_signature(grid) is None
    assert gen.rule_mirror(grid) == _independent_oracle(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_stream_is_balanced_and_semantically_exact(difficulty):
    counts = Counter()
    seen = set()
    for index in range(560):
        grid = gen.generate(index, index, difficulty=difficulty)
        analysis = gen._analysis(grid)
        assert analysis["errors"] == []
        assert gen.rule_mirror(grid) == _independent_oracle(grid)
        counts[analysis["scene_profile"]] += 1
        seen.add(_grid_key(grid))
    assert set(counts) == set(gen.SCENE_PROFILES)
    assert set(counts.values()) == {20}
    assert len(seen) >= 555


def test_difficulty_streams_are_live_and_materially_distinct():
    streams = {}
    for difficulty in (None, "easy", "medium", "hard"):
        streams[difficulty] = {
            _grid_key(gen.generate(index, index, difficulty=difficulty))
            for index in range(120)
        }
    assert all(len(stream) >= 118 for stream in streams.values())
    bands = list(streams)
    for left_index, left in enumerate(bands):
        for right in bands[left_index + 1:]:
            assert streams[left] != streams[right]
            assert len(streams[left] & streams[right]) <= 4


def test_all_generated_components_are_exact_vertical_t_tetrominoes():
    allowed = {gen.TOP_T, gen.BOTTOM_T}
    for index in range(240):
        grid = gen.generate(8000 + index, index, difficulty="medium")
        components = _components(grid)
        assert components
        assert {_normalized(component) for component in components} <= allowed
        assert all(len(component) == 4 for component in components)
        assert sum(value == 2 for row in grid for value in row) == 4 * len(components)


def test_tally_order_and_saturation_are_exact():
    expected = {
        "top_only": [[0, 0, 0, 1, 0, 1], [0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0]],
        "bottom_only": [[3, 0, 3, 0, 0, 0], [0, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0]],
        "top_cap": [[3, 0, 0, 1, 0, 1], [0, 0, 0, 0, 0, 0], [3, 0, 0, 1, 0, 1]],
        "bottom_cap": [[3, 0, 3, 1, 0, 0], [0, 0, 0, 0, 0, 0], [3, 0, 3, 1, 0, 0]],
        "both_cap": [[3, 0, 3, 1, 0, 1], [0, 0, 0, 0, 0, 0], [3, 0, 3, 1, 0, 1]],
    }
    for profile, output in expected.items():
        grid = gen.generate(77, 4, scene_code=_code(profile))
        assert gen.rule_mirror(grid) == output


def test_curriculum_covers_every_nonempty_capped_emblem_state():
    outputs = {
        _grid_key(gen.rule_mirror(gen.generate(700 + index, index, scene_code=_code(profile))))
        for index, profile in enumerate(gen.SCENE_PROFILES)
    }
    expected = {
        _grid_key(gen._emblem(top_count, bottom_count))
        for top_count in range(5)
        for bottom_count in range(5)
        if top_count or bottom_count
    }
    assert outputs == expected


def test_broad_rule_mirror_follows_executable_top_row_threshold():
    grid = [
        [2, 2, 2, 0, 2, 2],
        [0, 0, 0, 0, 2, 2],
        [0, 0, 0, 0, 0, 0],
    ]
    assert gen.self_check(grid)
    assert gen.rule_mirror(grid) == [
        [3, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 2], [0]],
        [[False, 2], [0, 0]],
        [[0, 11], [0, 2]],
        [[0] * 4 for _ in range(5)],
        [[2] * 4 for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_and_degenerate_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_non_t_component():
    grid = gen.generate(0, 0, scene_code=_code("public_4"))
    grid[0][1] = 0
    assert any("exact top-bar or bottom-bar T" in message for message in gen.self_check(grid))


def test_self_check_rejects_wrong_palette_even_when_red_t_shapes_survive():
    grid = gen.generate(0, 0, scene_code=_code("public_1"))
    grid[2][0] = 4
    assert any("exactly background 0 and red 2" in message for message in gen.self_check(grid))


def test_self_check_rejects_cross_profile_count_dimension_recombination():
    rng = random.Random(123)
    grid = gen._place_scene(18, 4, 2, 2, rng)
    assert gen._facts(grid)["exact_t"]
    assert gen.self_check(grid)
    assert gen.canonical_family_signature(grid) is None


def test_unknown_controls_and_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, retired_control=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, scene_code="publik_1")
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 2, scene_code=28)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="extreme")


def test_generation_is_deterministic_and_returns_fresh_rows():
    first = gen.generate(913, 21, difficulty="medium")
    second = gen.generate(913, 21, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_generation_preserves_global_random_state():
    random.seed(20260722)
    expected = [random.random() for _ in range(8)]
    random.seed(20260722)
    gen.generate(44, 18, difficulty="hard")
    observed = [random.random() for _ in range(8)]
    assert observed == expected


def test_base_authorities_are_byte_identical_to_canonical_rule():
    canonical_rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(canonical_rules) == 1
    canonical = next(iter(canonical_rules))
    for path in BASE_PATHS:
        row = json.loads(path.read_text(encoding="utf-8"))
        target = row["racket_target"]
        assert target["raw_code"] == canonical
        assert target["target_code"] == canonical
        assert target["needs_conversion"] is False


def test_base_descriptions_name_orientation_colors_order_and_cap():
    for path in BASE_PATHS:
        text = json.loads(path.read_text(encoding="utf-8"))["description_target"]["target_text"]
        lowered = text.lower()
        for phrase in ("top-bar", "bottom-bar", "blue", "green", "3x6", "four"):
            assert phrase in lowered
