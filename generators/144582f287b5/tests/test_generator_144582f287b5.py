"""Review regressions for ARC generator 144582f287b5.

These tests encode the canonical fixed-offset rule, the compact four-profile
lesson schedule, exact override observability, and fail-closed validation.
"""
from __future__ import annotations

import copy
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.144582f287b5.generator"
)
PROFILES = ("none", "corners", "source_halo", "edge_midpoints")
SOURCE_POSITIONS = ((1, 1), (1, 2), (2, 1), (2, 2))


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def independent_oracle(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    out[0][0] = grid[1][1]
    out[0][w - 1] = grid[1][2]
    out[h - 1][0] = grid[2][1]
    out[h - 1][w - 1] = grid[2][2]
    return out


def expected_decoy_positions(name, h, w):
    if name == "none":
        return set()
    if name == "corners":
        return {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    if name == "source_halo":
        return {(0, 1), (1, 0), (2, 3), (3, 2)}
    if name == "edge_midpoints":
        return {
            (0, w // 2),
            (h // 2, w - 1),
            (h - 1, (w - 1) // 2),
            ((h - 1) // 2, 0),
        }
    raise AssertionError(name)


def outside_nonzero_positions(grid):
    source = set(SOURCE_POSITIONS)
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in source
    }


def labeled_pair(grid):
    return {"input": copy.deepcopy(grid), "output": independent_oracle(grid)}


def test_metadata_and_declared_control_surface_are_exact():
    assert MODULE.GENERATOR_ID == MODULE.TASK_ID == "144582f287b5"
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "acb1a0ae5f73"
    assert tuple(MODULE.AXES) == ("grid_h", "grid_w", "decoy_pattern")
    assert MODULE.EXAMPLES_NEEDED == 3
    assert MODULE.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(MODULE.SCHEDULE_PROFILES) == PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_canonical_pairs_are_owned_and_rule_exact():
    pairs = canonical_pairs(MODULE.TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert MODULE.self_check(copy.deepcopy(pair["input"])) == []
        assert MODULE.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert MODULE.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]
        assert independent_oracle(pair["input"]) == pair["output"]



def test_active_racket_authority_is_exactly_the_selected_canonical_source():
    root = find_root(__file__)
    selected = None
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == MODULE.TASK_ID and row.get("program_solution"):
                    selected = row["program_solution"]
                    break
    assert selected is not None
    candidates = (
        root / "data/base/solutions/training/66e6c45b__144582f287b5.json",
        root / "shared/data/base/solutions/training/66e6c45b__144582f287b5.json",
    )
    authority_path = next(path for path in candidates if path.is_file())
    authority = json.loads(authority_path.read_text(encoding="utf-8"))["racket_target"]
    assert authority["raw_code"] == selected
    assert authority["target_code"] == selected

def test_every_declared_override_combination_is_constructible_and_observable():
    for band in ("easy", "medium", "hard"):
        for h in range(4, 9):
            for w in range(4, 9):
                for pattern in PROFILES:
                    requested = {
                        "grid_h": h,
                        "grid_w": w,
                        "decoy_pattern": pattern,
                    }
                    grid = MODULE.generate(801, h * 100 + w, difficulty=band, **requested)
                    assert MODULE.self_check(grid) == []
                    assert MODULE.observe_overrides(grid) == requested
                    assert outside_nonzero_positions(grid) == expected_decoy_positions(
                        pattern, h, w
                    )
                    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_unknown_invalid_and_coercible_overrides_are_rejected_loudly():
    for kwargs in (
        {"texture": "mixed_4"},
        {"center_pattern": "mixed_4"},
        {"unknown_axis": 4},
        {"grid_h": 3},
        {"grid_w": 9},
        {"decoy_pattern": "random"},
    ):
        with pytest.raises((TypeError, ValueError, KeyError)):
            MODULE.generate(3, 4, difficulty="medium", **kwargs)
    for bad in (True, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            MODULE.generate(3, 4, grid_h=bad)
    with pytest.raises(ValueError):
        MODULE.generate(3, 4, difficulty="legendary")


def test_schedule_is_four_profile_periodic_and_every_window_is_complete():
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 17, 987654321):
            profiles = [
                MODULE.schedule_profile(seed, index, difficulty=band)
                for index in range(16)
            ]
            assert profiles == [PROFILES[index % 4] for index in range(16)]
            for start in range(13):
                assert set(profiles[start : start + 4]) == set(PROFILES)


def test_default_schedule_has_exact_canonical_anchor_and_compact_broad_witnesses():
    expected_dims = {
        "easy": ((4, 4), (4, 4), (6, 6), (6, 4)),
        "medium": ((4, 4), (4, 4), (7, 7), (7, 5)),
        "hard": ((4, 4), (4, 4), (8, 8), (8, 6)),
    }
    for band, dims in expected_dims.items():
        for start in range(12):
            grids = [MODULE.generate(7100 + start, start + i, difficulty=band) for i in range(4)]
            for offset, grid in enumerate(grids):
                index = start + offset
                profile = PROFILES[index % 4]
                expected_h, expected_w = dims[index % 4]
                assert (len(grid), len(grid[0])) == (expected_h, expected_w)
                assert MODULE.observe_overrides(grid)["decoy_pattern"] == profile
                source = [grid[r][c] for r, c in SOURCE_POSITIONS]
                assert len(set(source)) == 4 and all(type(v) is int and 1 <= v <= 9 for v in source)
                assert MODULE.self_check(grid) == []
                assert MODULE.rule_mirror(grid) == independent_oracle(grid)
            anchor = next(g for i, g in enumerate(grids, start) if i % 4 == 0)
            assert MODULE.strict_canonical_like(anchor) == []
            corner_contrast = next(g for i, g in enumerate(grids, start) if i % 4 == 1)
            assert (len(corner_contrast), len(corner_contrast[0])) == (4, 4)
            assert len({value for row in corner_contrast for value in row}) == 5
            for i, grid in enumerate(grids, start):
                if i % 4:
                    assert MODULE.strict_canonical_like(grid)


def test_default_generation_is_deterministic_fresh_rng_pure_and_diverse():
    inputs = set()
    outputs = set()
    for band in ("easy", "medium", "hard"):
        for index in range(80):
            random.seed(123456)
            state = random.getstate()
            first = MODULE.generate(90_000 + index, index, difficulty=band)
            assert random.getstate() == state
            replay = MODULE.generate(90_000 + index, index, difficulty=band)
            assert replay == first
            assert replay is not first and all(a is not b for a, b in zip(first, replay))
            before = frozen(first)
            output = MODULE.rule_mirror(first)
            assert frozen(first) == before
            inputs.add(before)
            outputs.add(frozen(output))
    # Both 4x4 profiles are deliberately band-invariant, so their 40 draws
    # repeat across the three bands; the two shape profiles remain band-distinct.
    assert len(inputs) >= 155
    assert len(outputs) >= 155


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[False] * 4 for _ in range(4)],
        [[10] * 4 for _ in range(4)],
        [[0] * 3 for _ in range(3)],
        [[0] * 9 for _ in range(9)],
        [[0] * 4 for _ in range(4)],
        [[1] * 4 for _ in range(4)],
    ],
)
def test_malformed_and_semantic_impostors_fail_closed(grid):
    assert MODULE.self_check(copy.deepcopy(grid))


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(
        812, 5, difficulty="medium", grid_h=6, grid_w=7, decoy_pattern="corners"
    )

    duplicate_source = copy.deepcopy(grid)
    duplicate_source[1][2] = duplicate_source[1][1]
    assert MODULE.self_check(duplicate_source)

    zero_source = copy.deepcopy(grid)
    zero_source[2][2] = 0
    assert MODULE.self_check(zero_source)

    mixed_decoy_colors = copy.deepcopy(grid)
    mixed_decoy_colors[0][0] = grid[1][1]
    assert MODULE.self_check(mixed_decoy_colors)

    extra_cell = copy.deepcopy(grid)
    extra_cell[0][1] = 9 if 9 not in {grid[r][c] for r, c in SOURCE_POSITIONS} else 8
    assert MODULE.self_check(extra_cell)

    for bad in (
        [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
        [[1, 1, 1, 1] for _ in range(4)],
    ):
        assert MODULE.self_check(bad)


def test_rule_mirror_rejects_malformed_inputs_instead_of_guessing():
    for bad in (None, [], [[]], [[0] * 4 for _ in range(4)], [[1] * 4 for _ in range(4)]):
        with pytest.raises(ValueError):
            MODULE.rule_mirror(copy.deepcopy(bad))


def test_declared_canonical_shortcuts_fit_canonical_but_are_refuted_broadly():
    shortcuts = MODULE.CANONICAL_SHORTCUTS
    assert set(shortcuts) == {
        "geometric_center",
        "first_four_nonzero",
        "nonzero_bbox_corners",
        "fixed_4x4_output",
    }
    for name, rival in shortcuts.items():
        for pair in canonical_pairs(MODULE.TASK_ID, root=find_root(__file__)):
            assert rival(copy.deepcopy(pair["input"])) == pair["output"], name
        disagreements = 0
        for index in range(1, 4):
            grid = MODULE.generate(5521, index, difficulty="medium")
            disagreements += rival(copy.deepcopy(grid)) != independent_oracle(grid)
        assert disagreements >= 2, (name, disagreements)


def test_every_rotated_scheduled_lesson_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 41, 20261007):
            for start in range(16):
                pairs = [
                    labeled_pair(MODULE.generate(seed, start + offset, difficulty=band))
                    for offset in range(4)
                ]
                for held_out in range(4):
                    demos = [copy.deepcopy(pair) for i, pair in enumerate(pairs) if i != held_out]
                    query = copy.deepcopy(pairs[held_out])
                    assert MODULE.lesson_identifiable(demos, query) == []


def test_ambiguous_canonical_only_lesson_is_reported_and_malformed_pairs_do_not_throw():
    canonical = canonical_pairs(MODULE.TASK_ID, root=find_root(__file__))[0]
    broad_query = labeled_pair(MODULE.generate(911, 1, difficulty="medium"))
    reasons = MODULE.lesson_identifiable(
        [copy.deepcopy(canonical) for _ in range(3)], copy.deepcopy(broad_query)
    )
    assert reasons
    assert all(isinstance(reason, str) and reason for reason in reasons)

    good_grid = MODULE.generate(0, 0)
    good_pair = labeled_pair(good_grid)
    malformed_pairs = (
        ({"input": None, "output": []}, good_pair),
        ({"input": good_grid, "output": [[False] * 4 for _ in range(4)]}, good_pair),
        (good_pair, {"input": "bad", "output": []}),
    )
    for bad_demo, query in malformed_pairs:
        findings = MODULE.lesson_identifiable(
            [copy.deepcopy(good_pair), copy.deepcopy(good_pair), copy.deepcopy(bad_demo)],
            copy.deepcopy(query),
        )
        assert findings and all(isinstance(item, str) for item in findings)
