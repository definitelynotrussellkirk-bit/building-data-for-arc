from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


TASK = "8ef6f191186d"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE = ROOT / "data/base/solutions/banks/fd166f81148e/H147__8ef6f191186d.json"


def as_grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


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


def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def independent_transform(grid, command):
    if command == 1:
        return [row[:] for row in grid]
    if command == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if command == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if command == 4:
        return [list(row) for row in zip(*grid)][::-1]
    if command == 5:
        return [list(reversed(row)) for row in grid]
    if command == 6:
        return [row[:] for row in reversed(grid)]
    return [list(row) for row in zip(*grid)]


def independent_oracle(grid):
    command = grid[0][0]
    sources = [value for value in grid[0][2:] if value]
    targets = [value for value in grid[1][2:] if value]
    mapping = list(zip(sources, targets))
    obj = crop([row[:] for row in grid[2:]])
    remapped = []
    for row in obj:
        remapped.append([next((target for source, target in mapping if source == value), value) if value else 0 for value in row])
    return crop(independent_transform(remapped, command))


def frozen(grid):
    return tuple(map(tuple, grid))


def test_all_canonical_pairs_are_exact_and_strict():
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
        grid = MODULE.generate(11, 17, scene_profile=profile)
        assert grid == as_grid(pair["input"])
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == as_grid(pair["output"])
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.canonical_family_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_command_profile_in_every_band(profile, difficulty):
    expected_command = MODULE._PROFILE_TO_COMMAND[profile]
    for seed in range(4):
        grid = MODULE.generate(20_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert analysis["facts"]["command"] == expected_command
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == analysis["output"]


def test_all_seven_transforms_have_independent_expected_geometry():
    shape = [[1, 2, 0], [3, 4, 5]]
    expected = {
        1: [[1, 2, 0], [3, 4, 5]],
        2: [[3, 1], [4, 2], [5, 0]],
        3: [[5, 4, 3], [0, 2, 1]],
        4: [[0, 5], [2, 4], [1, 3]],
        5: [[0, 2, 1], [5, 4, 3]],
        6: [[3, 4, 5], [1, 2, 0]],
        7: [[1, 3], [2, 4], [0, 5]],
    }
    for command, output in expected.items():
        assert MODULE.apply_command(shape, command) == independent_transform(shape, command) == output


def test_public_nuisance_families_are_band_aware_and_nonliteral():
    literals = {frozen(as_grid(pair["input"])) for pair in canonical_pairs()}
    for profile in MODULE.PUBLIC_PROFILES:
        for difficulty, hrange, wrange in (
            ("easy", (5, 8), (6, 9)),
            ("medium", (8, 12), (9, 13)),
            ("hard", (12, 18), (13, 18)),
        ):
            scenes = [MODULE._make_scene(profile, difficulty, random.Random(seed)) for seed in range(50)]
            assert all(MODULE.canonical_family_signature(grid) == profile for grid in scenes)
            assert all(frozen(grid) not in literals for grid in scenes)
            assert all(hrange[0] <= len(grid) <= hrange[1] and wrange[0] <= len(grid[0]) <= wrange[1] for grid in scenes)
            assert len({frozen(grid) for grid in scenes}) >= 48


def test_mapping_is_applied_before_geometry_and_every_source_is_taught():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(30):
            grid = MODULE.generate(seed, seed * 29, scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            output = MODULE.rule_mirror(grid)
            assert set(facts["sources"]).isdisjoint(facts["targets"])
            assert not ({value for row in output for value in row} & set(facts["sources"]))
            assert {value for row in output for value in row if value} == set(facts["targets"])
            if facts["command"] in (2, 4, 7):
                assert (len(output), len(output[0])) == (facts["object_width"], facts["object_height"])
            else:
                assert (len(output), len(output[0])) == (facts["object_height"], facts["object_width"])


def test_body_padding_and_placement_do_not_affect_tight_output():
    first = [[2, 0, 2, 3, 0, 0], [0, 0, 8, 6, 0, 0], [2, 3, 0, 0, 0, 0], [0, 2, 3, 0, 0, 0], [0, 0, 2, 0, 0, 0]]
    second = [[2, 0, 2, 3, 0, 0, 0, 0], [0, 0, 8, 6, 0, 0, 0, 0], [0] * 8, [0, 0, 0, 2, 3, 0, 0, 0], [0, 0, 0, 0, 2, 3, 0, 0], [0, 0, 0, 0, 0, 2, 0, 0], [0] * 8]
    assert MODULE.rule_mirror(first) == MODULE.rule_mirror(second) == independent_oracle(first)


def test_broad_rule_preserves_unmapped_colors_and_uses_else_as_transpose():
    grid = [[8, 0, 2, 0, 0], [0, 0, 7, 0, 0], [2, 9, 0, 0, 0], [0, 2, 0, 0, 0]]
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert 7 in {value for row in output for value in row}
    assert 9 in {value for row in output for value in row}
    assert MODULE.self_check(grid)


def test_default_distribution_is_complete_diverse_and_nontrivial():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(1400)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(count >= 60 for count in profiles.values())
        assert len({frozen(grid) for grid in grids}) >= 1380
        assert len({frozen(grid) for grid in outputs}) >= 1100
        assert all(set(item["facts"]["sources"]).isdisjoint(item["facts"]["targets"]) for item in analyses)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 3 for _ in range(2)],
        [[False] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
        [[0] * 6 for _ in range(5)],
        [[2, 1, 2, 3, 0, 0], [0, 0, 8, 6, 0, 0], [2, 3, 0, 0, 0, 0]],
    ],
)
def test_malformed_or_uncalibrated_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(91, 7, scene_profile="command_rotate_180")
    facts = MODULE._analysis(grid)["facts"]
    gap = [row[:] for row in grid]
    gap[0][2] = 0
    assert MODULE.self_check(gap)
    unknown = [row[:] for row in grid]
    unknown[facts["object_row0"]][facts["object_col0"]] = 9 if 9 not in facts["sources"] else 8
    assert MODULE.self_check(unknown)
    missing_source = [row[:] for row in grid]
    source = facts["sources"][-1]
    replacement = facts["sources"][0]
    for row in missing_source[2:]:
        for col, value in enumerate(row):
            if value == source:
                row[col] = replacement
    assert MODULE.self_check(missing_source)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_object"},
        {"grid_h": 8},
        {"command": 2},
        {"palette_kind": "warm_remap"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="command_transpose")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="command_transpose")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="command_transpose") == second


def test_axis_contract_is_literal_minimal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_exact():
    source = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "84c7e6d399c7"
    base = json.loads(BASE.read_text())
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source
