from __future__ import annotations

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "9f362acbf729"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)


def _corner_keys(grid: list[list[int]]) -> list[int]:
    return [grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]]


def test_generated_scene_uses_all_four_corner_transform_keys():
    grid = MOD.generate(17, 3, difficulty="medium")
    assert sorted(_corner_keys(grid)) == [1, 2, 3, 4]

    body = [row[:] for row in grid]
    body[0][0] = body[0][-1] = body[-1][0] = body[-1][-1] = 0
    assert any(value != 0 for row in body for value in row)


def test_python_mirror_matches_every_canonical_pair():
    pairs = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
    assert len(pairs) == 4
    for pair in pairs:
        assert MOD.rule_mirror(pair["input"]) == pair["output"]


def _body_crop(grid: list[list[int]]) -> list[list[int]]:
    cleared = [row[:] for row in grid]
    cleared[0][0] = cleared[0][-1] = cleared[-1][0] = cleared[-1][-1] = 0
    cells = [
        (r, c)
        for r, row in enumerate(cleared)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in cleared[r0:r1 + 1]]


def test_exact_overrides_control_body_palette_and_corner_order_on_canonical_canvas():
    grid = MOD.generate(
        101,
        7,
        difficulty="easy",
        body_h=4,
        body_w=3,
        palette_size=3,
        key_order="2-3-4-1",
    )
    assert (len(grid), len(grid[0])) == (5, 5)
    assert _corner_keys(grid) == [2, 3, 4, 1]
    body = _body_crop(grid)
    assert (len(body), len(body[0])) == (4, 3)
    assert len({value for row in body for value in row if value != 0}) == 3
    assert MOD.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 5,
        "body_h": 4,
        "body_w": 3,
        "palette_size": 3,
        "key_order": "2-3-4-1",
    }


def test_two_by_two_monochrome_profile_is_a_supported_three_image_exception():
    grid = MOD.generate(
        4,
        28,
        difficulty="easy",
        body_h=2,
        body_w=2,
        palette_size=1,
        key_order="4-1-3-2",
    )
    assert MOD.self_check(grid) == []
    body = _body_crop(grid)
    orbit = {
        tuple(map(tuple, MOD._transform_by_key(body, key)))
        for key in (1, 2, 3, 4)
    }
    assert len(orbit) == 3


def test_self_check_rejects_three_image_orbit_outside_canonical_exception():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = 1, 2, 3, 4
    for r, c in ((1, 1), (1, 3), (3, 1)):
        grid[r][c] = 7
    assert MOD._analyze(grid)["transform_orbit"] == 3
    assert any("four distinct" in error for error in MOD.self_check(grid))


def test_rule_mirror_rejects_missing_or_repeated_corner_keys():
    grid = MOD.generate(7, 11)
    grid[0][0] = grid[0][-1]
    import pytest
    with pytest.raises(ValueError, match="permutation"):
        MOD.rule_mirror(grid)


def test_generated_scenes_defeat_numeric_quarter_turn_shortcut():
    for seed in range(80):
        grid = MOD.generate(seed, seed * 13 + 5, difficulty=("easy", "medium", "hard")[seed % 3])
        assert MOD.rule_mirror(grid) != MOD.numeric_rotation_rival(grid)
        assert MOD.SEMANTIC_WITNESSES["key_mapping_not_numeric_rotation"](grid)
        assert MOD.SEMANTIC_RIVALS["numeric_rotation"](grid) == MOD.numeric_rotation_rival(grid)
        assert MOD.WITNESS_RIVALS["key_mapping_not_numeric_rotation"] == ["numeric_rotation"]


def test_canonical_inputs_pass_self_check_and_rule_hash_is_source_bound():
    import hashlib
    import json

    pairs = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
    for pair in pairs:
        assert MOD.self_check(pair["input"]) == []

    row = next(
        json.loads(line)
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )
    digest = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert MOD.RULE_HASH == digest == "75692873c100"


def test_default_distribution_is_valid_deterministic_and_observable():
    import random

    key_orders = set()
    profiles = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(180):
            sample_index = seed * 17 + 9
            random.seed(seed + 1000)
            state = random.getstate()
            first = MOD.generate(seed, sample_index, difficulty=band)
            assert random.getstate() == state
            second = MOD.generate(seed, sample_index, difficulty=band)
            assert first == second
            assert first is not second and first[0] is not second[0]
            assert MOD.self_check(first) == []
            observed = MOD.observe_overrides(first)
            assert observed["grid_h"] == len(first)
            assert observed["grid_w"] == len(first[0])
            assert 2 <= observed["body_h"] <= 4
            assert 2 <= observed["body_w"] <= 4
            assert 1 <= observed["palette_size"] <= 3
            key_orders.add(observed["key_order"])
            profiles.add((observed["body_h"], observed["body_w"], observed["palette_size"]))
    assert len(key_orders) == 24
    assert (2, 2, 1) in profiles
    assert (4, 4, 3) in profiles


def test_every_declared_key_order_and_boundary_profile_can_be_forced():
    for index, key_order in enumerate(MOD._KEY_ORDERS):
        grid = MOD.generate(
            700 + index,
            index,
            body_h=2 if index % 2 == 0 else 4,
            body_w=2 if index % 3 == 0 else 4,
            palette_size=1 if index % 5 == 0 else 3,
            key_order=key_order,
        )
        observed = MOD.observe_overrides(grid)
        assert observed["key_order"] == key_order
        assert MOD.self_check(grid) == []


def test_all_generated_inputs_use_the_canonical_five_by_five_canvas():
    import pytest

    for seed in range(30):
        grid = MOD.generate(seed, seed * 7 + 1, difficulty=("easy", "medium", "hard")[seed % 3])
        assert (len(grid), len(grid[0])) == (5, 5)
    with pytest.raises(ValueError, match="unknown override"):
        MOD.generate(0, 0, grid_h=6)
    with pytest.raises(ValueError, match="unknown override"):
        MOD.generate(0, 0, grid_w=6)


def test_invalid_calls_and_malformed_scenes_fail_closed():
    import pytest

    for bad in (True, False, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(bad, 0)
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(0, bad)
    with pytest.raises(ValueError):
        MOD.generate(0, -1)
    with pytest.raises(ValueError):
        MOD.generate(0, 0, difficulty="extreme")
    for overrides in (
        {"grid_h": 4},
        {"grid_w": 11},
        {"body_h": 1},
        {"body_w": 5},
        {"palette_size": 0},
        {"key_order": "1-1-2-3"},
        {"unknown_axis": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            MOD.generate(1, 2, **overrides)

    malformed = [
        [],
        [[]],
        [[1], [1, 2]],
        [[True] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
    ]
    repeated_keys = MOD.generate(9, 4)
    repeated_keys[0][0] = repeated_keys[0][-1]
    malformed.append(repeated_keys)
    one_cell_body = [[0] * 5 for _ in range(5)]
    one_cell_body[0][0], one_cell_body[0][-1], one_cell_body[-1][0], one_cell_body[-1][-1] = 1, 2, 3, 4
    one_cell_body[2][2] = 7
    malformed.append(one_cell_body)
    for grid in malformed:
        assert MOD.self_check(grid), grid


def test_mosaic_packing_top_aligns_rectangular_transforms_and_right_pads():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = 1, 4, 3, 2
    for r, c in ((2, 1), (3, 1), (3, 2), (3, 3)):
        grid[r][c] = 6
    expected = [
        [6, 6, 0, 6, 6, 0, 0],
        [6, 0, 0, 0, 6, 0, 0],
        [6, 0, 0, 0, 6, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 6, 0, 6, 6, 6],
        [6, 6, 6, 0, 0, 0, 6],
    ]
    assert MOD.rule_mirror(grid) == expected
