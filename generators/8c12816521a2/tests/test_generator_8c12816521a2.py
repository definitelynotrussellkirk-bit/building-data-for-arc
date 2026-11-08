from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK = "8c12816521a2"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
BASE = next(
    path
    for path in (
        ROOT / "data/base/solutions/training/05a7bcf2__8c12816521a2.json",
        ROOT / "shared/data/base/solutions/training/05a7bcf2__8c12816521a2.json",
    )
    if path.is_file()
)


def canonical_row():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == TASK:
                return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    horizontal = any(all(grid[row][col] == 8 for col in range(width)) for row in range(height))
    normalized = transpose(grid) if horizontal else [row[:] for row in grid]
    nheight, nwidth = len(normalized), len(normalized[0])
    separator = next(col for col in range(nwidth) if all(normalized[row][col] == 8 for row in range(nheight)))
    left_count = sum(normalized[row][col] == 4 for row in range(nheight) for col in range(separator))
    right_count = sum(normalized[row][col] == 4 for row in range(nheight) for col in range(separator + 1, nwidth))
    yellow_left = left_count > right_count
    output = [row[:] for row in normalized]
    for row in range(nheight):
        yellow_side = range(separator) if yellow_left else range(separator + 1, nwidth)
        red_side = range(separator + 1, nwidth) if yellow_left else range(separator)
        yellow = [col for col in yellow_side if normalized[row][col] == 4]
        if not yellow:
            continue
        red_count = sum(normalized[row][col] == 2 for col in red_side)
        for col, value in enumerate(normalized[row]):
            if value == 4:
                output[row][col] = 3
            elif col == separator:
                output[row][col] = 8
            elif yellow_left and col < separator and col > max(yellow):
                output[row][col] = 4
            elif not yellow_left and col > separator and col < min(yellow):
                output[row][col] = 4
            elif yellow_left and separator < col < nwidth - red_count:
                output[row][col] = 8
            elif not yellow_left and red_count <= col < separator:
                output[row][col] = 8
            elif yellow_left and col >= nwidth - red_count:
                output[row][col] = 2
            elif not yellow_left and col < red_count:
                output[row][col] = 2
            else:
                output[row][col] = value
    return transpose(output) if horizontal else output


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_pairs_are_exact_and_strict():
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.canonical_family_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    for seed in range(4):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_profiles_are_semantically_distinct_and_observable():
    for seed in range(30):
        facts = {profile: MODULE._analysis(MODULE.generate(seed, seed * 7, scene_profile=profile))["facts"] for profile in MODULE.GENERAL_PROFILES}
        assert (facts["vertical_left"]["orientation"], facts["vertical_left"]["yellow_side"]) == ("vertical", "left")
        assert (facts["vertical_right"]["orientation"], facts["vertical_right"]["yellow_side"]) == ("vertical", "right")
        assert (facts["horizontal_above"]["orientation"], facts["horizontal_above"]["yellow_side"]) == ("horizontal", "above")
        assert (facts["horizontal_below"]["orientation"], facts["horizontal_below"]["yellow_side"]) == ("horizontal", "below")
        assert facts["multi_yellow"]["yellow_components"] == 2
        assert facts["deep_yellow"]["yellow_components"] == 1
        assert facts["deep_yellow"]["trigger_lanes"] * 2 >= facts["deep_yellow"]["height"]
        assert facts["near_edge_separator"]["near_edge"]


def test_public_nuisance_families_are_band_aware_and_nonliteral():
    literals = {frozen(pair["input"]) for pair in canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        for difficulty, low, high in (("easy", 15, 18), ("medium", 19, 24), ("hard", 25, 30)):
            scenes = [MODULE._make_scene(profile, difficulty, random.Random(seed)) for seed in range(50)]
            assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
            assert all(frozen(grid) not in literals for grid in scenes)
            assert all(low <= len(grid) <= high and low <= len(grid[0]) <= high for grid in scenes)
            assert len({frozen(grid) for grid in scenes}) == 50


def test_triggered_lanes_rebuild_red_count_and_nontriggered_lanes_are_unchanged():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(20):
            grid = MODULE.generate(seed, seed * 31, scene_profile=profile)
            normalized, horizontal, separator = MODULE._normalize(grid)
            output = MODULE.rule_mirror(grid)
            normalized_output = transpose(output) if horizontal else output
            facts = MODULE._analysis(grid)["facts"]
            yellow_left = facts["yellow_left"]
            for row, values in enumerate(normalized):
                yellow_side = range(separator) if yellow_left else range(separator + 1, len(values))
                red_side = range(separator + 1, len(values)) if yellow_left else range(separator)
                yellow = [col for col in yellow_side if values[col] == 4]
                if not yellow:
                    assert normalized_output[row] == values
                    continue
                red_count = sum(values[col] == 2 for col in red_side)
                assert sum(value == 3 for value in normalized_output[row]) == sum(value == 4 for value in values)
                if yellow_left:
                    assert normalized_output[row][-red_count:] == [2] * red_count
                else:
                    assert normalized_output[row][:red_count] == [2] * red_count


def test_tie_selects_right_side_and_broad_rule_preserves_untriggered_content():
    grid = [[0] * 12 for _ in range(10)]
    for row in range(10):
        grid[row][5] = 8
    grid[2][2] = 4
    grid[7][8] = 4
    grid[7][1:3] = [2, 2]
    grid[4][10] = 7
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert output[2] == grid[2]
    assert output[4][10] == 7
    assert output[7] != grid[7]
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_nontrivial():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1400)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(count >= 60 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) == len(grids)
        assert len({frozen(grid) for grid in outputs}) == len(outputs)
        assert all(grid != output for grid, output in zip(grids, outputs))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 12 for _ in range(12)],
        [[8] * 12 for _ in range(12)],
    ],
)
def test_malformed_or_uncalibrated_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="multi_yellow")
    facts = MODULE._analysis(grid)["facts"]
    wrong_red = [row[:] for row in grid]
    wrong_red[0][0 if facts["yellow_side"] == "left" else -1] = 2
    assert MODULE.self_check(wrong_red)
    mixed_palette = [row[:] for row in grid]
    mixed_palette[0][0] = 6
    assert MODULE.self_check(mixed_palette)
    broken_separator = [row[:] for row in grid]
    broken_separator[0][facts["separator"]] = 0
    assert MODULE.self_check(broken_separator)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_separator"},
        {"height": 30},
        {"orientation": "vertical"},
        {"n_rows": 5},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="horizontal_below")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="horizontal_below")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="horizontal_below") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_semantically_exact():
    source = canonical_row()["program_solution"]
    normalized = " ".join(source.split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "bdca6d13f74f"
    base = json.loads(BASE.read_text())
    assert " ".join(base["racket_target"]["raw_code"].split()) == normalized
    assert " ".join(base["racket_target"]["target_code"].split()) == normalized
