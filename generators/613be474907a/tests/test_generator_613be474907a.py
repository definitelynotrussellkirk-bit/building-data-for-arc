from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "613be474907a"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASES = (
    ROOT / "data/base/solutions/training/d968ffd4__613be474907a.json",
    ROOT / "data/base/solutions/augmented/d968ffd4__c1debe6eeac7.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def unique_canonical_pairs():
    pairs = []
    seen = set()
    for row in canonical_rows():
        for pair in row.get("train", []) + row.get("test", []):
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def independent_oracle(grid):
    flat = sum(grid, [])
    counts = Counter(flat)
    background = max(counts, key=counts.get)
    color1, color2 = sorted(color for color in counts if color != background)

    def box(color):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)

    b1, b2 = box(color1), box(color2)
    if b1[3] < b2[1]:
        orientation, start, end, near, far = "horizontal", b1[3] + 1, b2[1] - 1, color1, color2
    elif b2[3] < b1[1]:
        orientation, start, end, near, far = "horizontal", b2[3] + 1, b1[1] - 1, color2, color1
    elif b1[2] < b2[0]:
        orientation, start, end, near, far = "vertical", b1[2] + 1, b2[0] - 1, color1, color2
    else:
        orientation, start, end, near, far = "vertical", b2[2] + 1, b1[0] - 1, color2, color1
    half = (end - start + 1) // 2
    output = [row[:] for row in grid]
    if orientation == "horizontal":
        for row in range(len(grid)):
            for col in range(start, start + half):
                output[row][col] = near
            for col in range(end - half + 1, end + 1):
                output[row][col] = far
    else:
        for row in range(start, start + half):
            output[row] = [near] * len(grid[0])
        for row in range(end - half + 1, end + 1):
            output[row] = [far] * len(grid[0])
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = unique_canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"] == independent_oracle(grid)
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    orientation, side, parity = profile.split("_")
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["orientation"] == orientation
    assert analysis["facts"]["side"] == side
    assert analysis["facts"]["parity"] == parity
    assert MODULE.rule_mirror(grid) == analysis["output"] == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_extensions_fill_complete_perpendicular_lines():
    horizontal = MODULE.generate(31, 1, scene_profile="horizontal_right_odd")
    facts = MODULE._analysis(horizontal)["facts"]
    output = MODULE.rule_mirror(horizontal)
    half = facts["gap"] // 2
    for col in range(facts["gap_start"], facts["gap_start"] + half):
        assert {row[col] for row in output} == {facts["near_color"]}
    for col in range(facts["gap_end"] - half + 1, facts["gap_end"] + 1):
        assert {row[col] for row in output} == {facts["far_color"]}

    vertical = MODULE.generate(32, 2, scene_profile="vertical_top_even")
    facts = MODULE._analysis(vertical)["facts"]
    output = MODULE.rule_mirror(vertical)
    half = facts["gap"] // 2
    assert all(set(output[row]) == {facts["near_color"]} for row in range(facts["gap_start"], facts["gap_start"] + half))
    assert all(set(output[row]) == {facts["far_color"]} for row in range(facts["gap_end"] - half + 1, facts["gap_end"] + 1))


@pytest.mark.parametrize("profile", [p for p in MODULE.GENERAL_PROFILES if p.endswith("_odd")])
def test_odd_gap_preserves_exact_middle_line(profile):
    grid = MODULE.generate(41 + len(profile), 3, scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    middle = facts["gap_start"] + facts["gap"] // 2
    if facts["orientation"] == "horizontal":
        assert all(grid[row][middle] == output[row][middle] == facts["background"] for row in range(len(grid)))
    else:
        assert grid[middle] == output[middle] == [facts["background"]] * len(grid[0])


@pytest.mark.parametrize("profile", [p for p in MODULE.GENERAL_PROFILES if p.endswith("_even")])
def test_even_gap_is_completely_bridged(profile):
    grid = MODULE.generate(51 + len(profile), 4, scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    if facts["orientation"] == "horizontal":
        assert all(output[row][col] != facts["background"] for row in range(len(grid)) for col in range(facts["gap_start"], facts["gap_end"] + 1))
    else:
        assert all(value != facts["background"] for row in range(facts["gap_start"], facts["gap_end"] + 1) for value in output[row])


def test_horizontal_branch_has_canonical_priority_when_both_axes_are_separated():
    grid = [[0] * 12 for _ in range(9)]
    grid[1][8] = 1
    grid[7][1] = 2
    facts = MODULE._analysis(grid)["facts"]
    assert facts["orientation"] == "horizontal"
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_palette_nuisance_stays_in_canonical_family_but_not_exact_replay():
    public = MODULE.generate(1, 0, scene_profile="public_1")
    remapped = [[{4: 0, 1: 2, 6: 3}[value] for value in row] for row in public]
    analysis = MODULE._analysis(remapped)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == "public_1"
    assert MODULE.canonical_profile_signature(remapped) is None
    assert MODULE.canonical_family_signature(remapped) == "public_1"
    assert MODULE.rule_mirror(remapped) == independent_oracle(remapped)


def test_lawful_geometry_recombination_is_not_mislabeled_canonical_family():
    public = MODULE.generate(1, 0, scene_profile="public_1")
    recombined = [row[:] for row in public]
    for row in range(1, 4):
        recombined[row][12:15] = [6, 6, 4]
    analysis = MODULE._analysis(recombined)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == "horizontal_left_odd"
    assert MODULE.canonical_profile_signature(recombined) is None
    assert MODULE.canonical_family_signature(recombined) is None
    assert MODULE.rule_mirror(recombined) == independent_oracle(recombined)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="vertical_bottom_odd")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="vertical_bottom_odd")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="vertical_bottom_odd") == second


def test_default_prior_covers_public_and_all_general_branches():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1200)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        public = sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles)
        assert public >= 300
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_high_semantic_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(240)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 225
    assert len({frozen(output) for output in outputs}) >= 225
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 45
    assert len({tuple(sorted(set(sum(grid, [])))) for grid in grids}) >= 30


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 3 for _ in range(2)],
        [[0] * 31 for _ in range(3)],
        [[0] * 3 for _ in range(31)],
        [[0] * 3, [0] * 3, [0] * 2],
        [[False] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
        [[0] * 3 for _ in range(3)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="horizontal_left_even")

    missing_color = [row[:] for row in grid]
    facts = MODULE._analysis(grid)["facts"]
    old, replacement = facts["colors"][0], facts["background"]
    missing_color = [[replacement if value == old else value for value in row] for row in missing_color]
    assert MODULE.self_check(missing_color)

    holed_block = [row[:] for row in grid]
    box = facts["boxes"][0]
    holed_block[box[0]][box[1]] = facts["background"]
    assert MODULE.self_check(holed_block)

    tied_mode = [[0, 0, 1], [1, 2, 2], [0, 1, 2]]
    assert MODULE.self_check(tied_mode)

    short_gap = [[0] * 8 for _ in range(4)]
    short_gap[1][1] = 1
    short_gap[1][4] = 2
    assert MODULE.self_check(short_gap)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "no_regions"}, {"difficulty": "expert"}])
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
    assert MODULE.RULE_HASH == digest == "adc52fde010d"
    for path in BASES:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
