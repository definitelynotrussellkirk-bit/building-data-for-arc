from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import defaultdict
from pathlib import Path

import pytest
from reviewer_support import find_root, canonical_path, load_selected_generator
from arc_repl.parser import parse_all


TASK = "6b88648ff0e0"
ROOT = find_root(__file__)
MODULE = load_selected_generator(TASK, root=ROOT)[0]
DATA = canonical_path(ROOT).parent.parent
BASES = (
    DATA / "base/solutions/training/aab50785__6b88648ff0e0.json",
    DATA / "base/solutions/augmented/aab50785__927ad6211f20.json",
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
    by_row = defaultdict(list)
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            if all(grid[r][c] == 8 for r in (row, row + 1) for c in (col, col + 1)):
                by_row[row].append(col)
    output = []
    for top in sorted(by_row):
        left, right = min(by_row[top]), max(by_row[top])
        output.extend([grid[row][left + 2:right] for row in (top, top + 1)])
    return [row[:] for row in output]


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
    count = int(profile.split("_")[0].removeprefix("groups"))
    kind = profile.split("_")[1]
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["group_count"] == count
    assert analysis["facts"]["content_width"] in ((3, 4) if kind == "narrow" else (5, 6, 7))
    assert analysis["facts"]["output_shape"] == (2 * count, analysis["facts"]["content_width"])
    assert set(sum(grid, [])) == set(range(10))
    assert MODULE.rule_mirror(grid) == analysis["output"] == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_zero_is_lawful_inside_extracted_content():
    pair = unique_canonical_pairs()[0]
    assert any(value == 0 for row in pair["output"] for value in row)
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]
    assert MODULE.self_check(pair["input"]) == []


def test_noise_outside_marked_interiors_is_discarded():
    grid = MODULE.generate(31, 1, scene_profile="groups3_wide")
    before = MODULE.rule_mirror(grid)
    groups = MODULE._detected_groups(grid)
    protected = {
        (row, col)
        for top, cols in groups
        for row in (top, top + 1)
        for col in range(min(cols), max(cols) + 2)
    }
    changed = [row[:] for row in grid]
    target = next((row, col) for row in range(len(grid)) for col in range(len(grid[0])) if (row, col) not in protected and grid[row][col] not in (7, 8))
    changed[target[0]][target[1]] = 7
    assert MODULE.rule_mirror(changed) == before


def test_strips_stack_in_top_to_bottom_order():
    grid = MODULE.generate(41, 2, scene_profile="groups4_narrow")
    groups = MODULE._detected_groups(grid)
    output = MODULE.rule_mirror(grid)
    for index, (top, cols) in enumerate(groups):
        expected = [grid[row][min(cols) + 2:max(cols)] for row in (top, top + 1)]
        assert output[2 * index:2 * index + 2] == expected


def test_marker_columns_may_vary_between_groups():
    witnessed = False
    for seed in range(100):
        grid = MODULE.generate(50_000 + seed, seed, scene_profile="groups4_wide")
        pairs = {(min(cols), max(cols)) for _, cols in MODULE._detected_groups(grid)}
        witnessed |= len(pairs) > 1
    assert witnessed


def test_palette_nuisance_preserves_complete_public_geometry():
    exact = MODULE.generate(1, 0, scene_profile="public_6")
    ordinary = next(
        grid
        for seed in range(1000)
        for grid in [MODULE.generate(60_000 + seed, seed)]
        if MODULE._analysis(grid)["scene_profile"] == "public_6" and grid != exact
    )
    assert MODULE.canonical_profile_signature(ordinary) is None
    assert MODULE.canonical_family_signature(ordinary) == "public_6"
    assert MODULE.rule_mirror(ordinary) == independent_oracle(ordinary)


def test_lawful_marker_recombination_is_not_mislabeled_public_family():
    grid = MODULE.generate(71, 4, scene_profile="groups2_narrow")
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE._analysis(grid)["scene_profile"] == "groups2_narrow"


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="groups4_wide")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="groups4_wide")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 8
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="groups4_wide") == second


def test_default_prior_covers_every_profile_and_public_family():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1200)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        assert sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles) >= 280
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_high_input_and_output_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(240)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 235
    assert len({frozen(output) for output in outputs}) >= 230
    assert {(len(output), len(output[0])) for output in outputs} == {
        (rows, width) for rows in (2, 4, 6, 8) for width in (3, 4, 5, 6, 7)
    }
    assert {value for grid in grids for row in grid for value in row} == set(range(10))


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
        [[0] * 8 for _ in range(8)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="groups3_wide")
    groups = MODULE._detected_groups(grid)

    broken_marker = [row[:] for row in grid]
    top, cols = groups[0]
    broken_marker[top][cols[0]] = 0
    assert MODULE.self_check(broken_marker)

    stray_cyan = [row[:] for row in grid]
    target = next((row, col) for row in range(len(grid)) for col in range(len(grid[0])) if grid[row][col] != 8)
    stray_cyan[target[0]][target[1]] = 8
    assert MODULE.self_check(stray_cyan)

    missing_palette = [[0 if value == 7 else value for value in row] for row in grid]
    assert MODULE.self_check(missing_palette)

    all_cyan = [[8] * len(grid[0]) for _ in grid]
    assert MODULE.self_check(all_cyan)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "no_bookends"}, {"n_groups": 3}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_archival_program_structures_agree():
    sources = {row["program_solution"] for row in canonical_rows()}
    assert len(sources) == 1
    source = sources.pop()
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "7bc08a76718f"
    for path in BASES:
        base = json.loads(path.read_text())
        assert parse_all(base["racket_target"]["raw_code"]) == parse_all(source)
        assert parse_all(base["racket_target"]["target_code"]) == parse_all(source)
