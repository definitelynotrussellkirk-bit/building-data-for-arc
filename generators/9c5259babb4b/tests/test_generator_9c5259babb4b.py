from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK = "9c5259babb4b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)


def _data_path(relative):
    for prefix in ("data", "shared/data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


BASE_PATHS = (
    _data_path("base/solutions/training/a09f6c25__9c5259babb4b.json"),
    _data_path("base/solutions/augmented/a09f6c25__903ead94696f.json"),
)


def canonical_rows():
    rows = []
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                rows.append(row)
    assert len(rows) == 2
    return rows


def unique_canonical_pairs():
    pairs, seen = [], set()
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def components8(grid, background):
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        other = current_row + dr, current_col + dc
                        if not (dr or dc) or other in seen:
                            continue
                        if not (0 <= other[0] < height and 0 <= other[1] < width):
                            continue
                        if grid[other[0]][other[1]] == color:
                            seen.add(other)
                            queue.append(other)
            result.append(cells)
    return result




def connected4(cells):
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            other = row + dr, col + dc
            if other in remaining and other not in seen:
                seen.add(other)
                stack.append(other)
    return seen == remaining


def independent_oracle(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    background = max(counts, key=lambda value: (counts[value], -value)) if counts else 0
    output = [[background] * len(grid[0]) for _ in grid]
    for cells in components8(grid, background):
        if len(cells) == 1:
            continue
        row0 = min(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        norm = {(row - row0, col - col0) for row, col in cells}
        height = max(row for row, _ in norm) + 1
        width = max(col for _, col in norm) + 1
        horizontal = {(height - 1 - row, col) for row, col in norm} == norm
        vertical = {(row, width - 1 - col) for row, col in norm} == norm
        color = 1 if horizontal else 3 if vertical else 6
        for row, col in cells:
            output[row][col] = color
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_ten_canonical_pair_appearances_are_exact():
    pairs = unique_canonical_pairs()
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 5
    appearances = 0
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            appearances += 1
            grid = pair["input"]
            assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
            assert MODULE.self_check(grid) == []
            assert MODULE.canonical_profile_signature(grid) in MODULE.PUBLIC_PROFILES
            assert MODULE.canonical_family_signature(grid) in MODULE.PUBLIC_PROFILES
    assert appearances == 10
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_profile_is_exact_and_observable(profile, difficulty):
    for seed in range(2):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_public_nuisances_preserve_complete_object_morphology_without_literals():
    literals = {frozen(pair["input"]) for pair in unique_canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        expected = MODULE._PUBLIC_FACTS[profile]
        expected_families = sorted(obj["family_key"] for obj in expected["kept"])
        scenes = [MODULE._public_nuisance(profile, random.Random(seed)) for seed in range(80)]
        assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
        assert all(frozen(grid) not in literals for grid in scenes)
        assert all(
            sorted(obj["family_key"] for obj in MODULE._analysis(grid)["facts"]["kept"]) == expected_families
            for grid in scenes
        )
        assert all(MODULE._analysis(grid)["facts"]["singleton_count"] == expected["singleton_count"] for grid in scenes)
        assert len({frozen(grid) for grid in scenes}) >= 78


def test_general_profiles_have_exact_class_signatures():
    expected = {
        "class_balanced": (2, 2, 1, 0),
        "no_asymmetry": (2, 2, 0, 0),
        "dense_mixed": (3, 2, 2, 0),
        "precedence_both": (2, 2, 1, 1),
    }
    for profile, signature in expected.items():
        for seed in range(30):
            facts = MODULE._analysis(MODULE.generate(seed, seed * 7, scene_profile=profile))["facts"]
            counts = facts["class_counts"]
            assert (counts["h"], counts["v"], counts["a"], counts["both"]) == signature




@pytest.mark.parametrize("profile", ["class_balanced", "dense_mixed", "precedence_both"])
def test_general_asymmetric_profiles_emit_an_8_connected_not_4_connected_witness(profile):
    for seed in range(8):
        grid = MODULE.generate(70_000 + seed, seed * 31, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        asymmetric = [obj for obj in analysis["facts"]["kept"] if obj["kind"] == "a"]
        assert asymmetric
        assert any(not connected4(obj["norm"]) for obj in asymmetric)
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_both_axis_symmetry_uses_top_bottom_precedence():
    grid = [[8] * 12 for _ in range(12)]
    for row, col in ((4, 4), (4, 5), (5, 4), (5, 5), (6, 4), (6, 5)):
        grid[row][col] = 2
    output = MODULE.rule_mirror(grid)
    assert all(output[row][col] == 1 for row, col in ((4, 4), (4, 5), (5, 4), (5, 5), (6, 4), (6, 5)))
    assert output == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_singletons_are_removed_and_all_three_labels_are_spatial():
    grid = MODULE.generate(501, 23, scene_profile="class_balanced")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    for obj in facts["singles"]:
        row, col = obj["cells"][0]
        assert output[row][col] == facts["background"]
    for obj in facts["kept"]:
        assert all(output[row][col] == obj["output_color"] for row, col in obj["cells"])
    assert {value for row in output for value in row} >= {1, 3, 6, facts["background"]}


def test_broad_rule_accepts_other_colors_and_layouts_but_training_rejects():
    grid = [[9] * 14 for _ in range(13)]
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)):
        grid[row][col] = 5
    for row, col in ((6, 7), (7, 6), (7, 7), (7, 8), (8, 7)):
        grid[row][col] = 4
    grid[11][12] = 2
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_band_aware():
    expected = set(MODULE.SCENE_PROFILES)
    bands = {"easy": (18, 21), "medium": (22, 26), "hard": (27, 30)}
    for difficulty, (low, high) in bands.items():
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1200)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        assert set(profiles) == expected
        assert all(count >= 65 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) == len(grids)
        assert len({frozen(item["output"]) for item in analyses}) == len(grids)
        general = [
            (grid, item) for grid, item in zip(grids, analyses)
            if item["scene_profile"] in MODULE.GENERAL_PROFILES
        ]
        assert all(low <= len(grid) <= high and low <= len(grid[0]) <= high for grid, _ in general)
        assert {item["facts"]["background"] for _, item in general} == {4, 7, 8}


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[8] * 11 for _ in range(11)],
        [[False] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[8] * 12 for _ in range(12)],
        [[8] * 12 for _ in range(11)] + [[8] * 11],
        [[8] * 12 for _ in range(12)],
        [[2] * 12 for _ in range(12)],
        [[8 if (row, col) != (5, 5) else 2 for col in range(12)] for row in range(12)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="class_balanced")
    facts = MODULE._analysis(grid)["facts"]
    no_singletons = [row[:] for row in grid]
    for obj in facts["singles"]:
        row, col = obj["cells"][0]
        no_singletons[row][col] = facts["background"]
    assert MODULE.self_check(no_singletons)
    third_color = [row[:] for row in grid]
    row, col = facts["kept"][0]["cells"][0]
    third_color[row][col] = 5
    assert MODULE.self_check(third_color)
    deleted_object = [row[:] for row in grid]
    for row, col in facts["kept"][0]["cells"]:
        deleted_object[row][col] = facts["background"]
    assert MODULE.self_check(deleted_object)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "all_sym"},
        {"grid_h": 19},
        {"n_shapes": 5},
        {"background": 8},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="dense_mixed")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="dense_mixed")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="dense_mixed") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_both_base_sources_match_canonical():
    source = canonical_rows()[0]["program_solution"]
    assert all(row["program_solution"] == source for row in canonical_rows())
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "6a2cfe9a66b0"
    normalized_source = " ".join(source.split())
    for path in BASE_PATHS:
        base = json.loads(path.read_text())
        assert " ".join(base["racket_target"]["raw_code"].split()) == normalized_source
        assert " ".join(base["racket_target"]["target_code"].split()) == normalized_source
