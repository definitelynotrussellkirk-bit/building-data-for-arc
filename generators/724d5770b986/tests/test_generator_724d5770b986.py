from __future__ import annotations

import hashlib
import json
import random

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "724d5770b986"
ROOT = find_root(__file__)
MODULE, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
BASES = (
    ROOT / "shared/data/base/solutions/training/f0df5ff0__724d5770b986.json",
    ROOT / "shared/data/base/solutions/augmented/f0df5ff0__d108787d5395.json",
)


def canonical_rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    return rows


def unique_canonical_pairs():
    pairs, seen = [], set()
    for row in canonical_rows():
        for pair in row.get("train", []) + row.get("test", []):
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    triggers = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 1]
    for trigger_row, trigger_col in triggers:
        for row in range(max(0, trigger_row - 1), min(height, trigger_row + 2)):
            for col in range(max(0, trigger_col - 1), min(width, trigger_col + 2)):
                if grid[row][col] == 0:
                    output[row][col] = 1
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
    assert MODULE.canonical_family_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["blue_count"] >= 1
    assert analysis["facts"]["decoy_count"] >= 1
    assert analysis["facts"]["paintable_count"] >= 1
    assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_blocked_dense_preserves_many_colored_neighbours():
    grid = MODULE.generate(31, 1, scene_profile="blocked_dense")
    analysis = MODULE._analysis(grid)
    output = MODULE.rule_mirror(grid)
    assert analysis["facts"]["blocked_ratio"] >= 0.34
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] not in (0, 1):
                assert output[row][col] == grid[row][col]


@pytest.mark.parametrize("profile", ["edge_clipped", "corner_clipped"])
def test_boundary_neighbourhoods_clip_to_canvas(profile):
    grid = MODULE.generate(41 + len(profile), 2, scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["edge_blues"] >= 1
    assert facts["corner_blues"] == (1 if profile == "corner_clipped" else 0)
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


@pytest.mark.parametrize(
    "profile,adjacent,overlap",
    [
        ("touching_blues", True, False),
        ("overlapping_neighbourhoods", False, True),
        ("mixed_geometry", True, True),
    ],
)
def test_blue_topology_contrasts(profile, adjacent, overlap):
    grid = MODULE.generate(51 + len(profile), 3, scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert bool(facts["adjacent_pairs"]) is adjacent
    assert bool(facts["overlap_pairs"]) is overlap
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_public_family_retains_linked_blue_geometry_and_histogram():
    exact = MODULE.generate(1, 0, scene_profile="public_4")
    ordinary = next(
        grid
        for seed in range(100)
        for grid in [MODULE.generate(60_000 + seed, seed)]
        if MODULE._analysis(grid)["scene_profile"] == "public_4" and grid != exact
    )
    assert MODULE._blue_positions(ordinary) == MODULE._blue_positions(exact)
    assert MODULE._family_key(ordinary) == MODULE._family_key(exact)
    assert MODULE.canonical_profile_signature(ordinary) is None
    assert MODULE.canonical_family_signature(ordinary) == "public_4"


def test_lawful_feature_recombination_is_not_mislabeled_public_family():
    grid = MODULE.generate(71, 4, scene_profile="isolated_dense")
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE._analysis(grid)["scene_profile"] == "isolated_dense"


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_geometry")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_geometry")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 2 if first[0][0] == 0 else 0
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_geometry") == second


def test_default_prior_covers_every_profile_and_public_family():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1400)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        assert sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles) >= 400
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_high_semantic_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(300)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 285
    assert len({frozen(output) for output in outputs}) >= 285
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 55
    assert {value for output in outputs for row in output for value in row} == set(range(10))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 8 for _ in range(7)],
        [[0] * 31 for _ in range(8)],
        [[0] * 8 for _ in range(31)],
        [[0] * 8 for _ in range(7)] + [[0] * 7],
        [[False] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="isolated_dense")

    no_blues = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if no_blues[row][col] == 1:
                no_blues[row][col] = 0
    assert MODULE.self_check(no_blues)

    no_decoys = [[1 if value == 1 else 0 for value in row] for row in grid]
    assert MODULE.self_check(no_decoys)

    no_change = [[2] * 8 for _ in range(8)]
    no_change[4][4] = 1
    assert MODULE.self_check(no_change)

    density_gap = [[0] * 10 for _ in range(10)]
    density_gap[4][4] = 1
    for index in range(23):
        row, col = divmod(index, 10)
        density_gap[row][col] = 2 + index % 2
    assert MODULE.self_check(density_gap)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_blues"},
        {"n_blues": 3},
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
    assert MODULE.RULE_HASH == digest == "e39c8a4e2b02"
    for path in BASES:
        base = json.loads(path.read_text())
        normalize = lambda text: " ".join(text.split())
        assert normalize(base["racket_target"]["raw_code"]) == normalize(source)
        assert normalize(base["racket_target"]["target_code"]) == normalize(source)
