from __future__ import annotations

import hashlib
import json
import random

import pytest
from reviewer_support import canonical_pairs as load_canonical_pairs
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "c5dd8036311b"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
CANONICAL = canonical_path(ROOT)
BASE_PATH = CANONICAL.parent.parent / "base" / "solutions" / "training" / "72a961c9__c5dd8036311b.json"
EXPECTED_PROFILE_COUNTS = {
    "public_1": (0, 1), "public_2": (1, 0), "public_3": (1, 2),
    "public_4": (1, 1), "public_5": (2, 2),
    "double_8": (0, 2), "double_2": (2, 0),
    "triple_8": (0, 3), "triple_2": (3, 0),
    "four_8": (0, 4), "four_2": (4, 0),
    "teaching_5": (3, 2), "teaching_7": (4, 3), "balanced_8": (4, 4),
    "six_mixed": (4, 2),
}


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    assert (rows[0]["source"], len(rows[0]["train"]), len(rows[0]["test"])) == (
        "training", 4, 1
    )
    return rows[0]


def canonical_pairs():
    return load_canonical_pairs(TASK, root=ROOT)


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_facts(grid):
    bar_row = next(row for row, values in enumerate(grid) if 1 in values)
    markers = tuple(
        (col, value)
        for col, value in enumerate(grid[bar_row])
        if value not in (0, 1)
    )
    return bar_row, markers


def independent_oracle(grid):
    bar_row, markers = independent_facts(grid)
    output = [row[:] for row in grid]
    for col, color in markers:
        height = 3 if color == 8 else 4
        for offset in range(height):
            row = bar_row - height + offset
            if 0 <= row < bar_row:
                output[row][col] = color if offset == 0 else 1
    return output


def test_metadata_hash_and_control_surface_are_exact():
    assert isinstance(MODULE.VERSION, str) and MODULE.VERSION
    assert MODULE.RULE_HASH == "fd929da87d08"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert set(MODULE.SCENE_PROFILES) == set(EXPECTED_PROFILE_COUNTS)
    assert MODULE.PROFILE_COUNTS == EXPECTED_PROFILE_COUNTS
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(5))
def test_every_canonical_pair_is_exact_and_anchored(index):
    pair = canonical_pairs()[index]
    profile = f"public_{index + 1}"
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert MODULE.self_check(pair["input"]) == []
    assert MODULE.rule_mirror(pair["input"]) == independent_oracle(pair["input"])
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_forced_public_profiles_are_exact_fresh_anchors(profile, band):
    first = MODULE.generate(19, 7, difficulty=band, scene_profile=profile)
    second = MODULE.generate(999, 333, difficulty=band, scene_profile=profile)
    expected = canonical_pairs()[int(profile.removeprefix("public_")) - 1]["input"]
    assert first == second == expected
    assert first is not expected and first[0] is not expected[0]
    assert MODULE.canonical_profile_signature(first) == profile
    assert MODULE.observe_overrides(first) == {"scene_profile": profile}


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    for index in range(12):
        grid = MODULE.generate(10_000 + index * 37, index, difficulty=band, scene_profile=profile)
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)
        row, markers = independent_facts(grid)
        assert (sum(color == 2 for _, color in markers),
                sum(color == 8 for _, color in markers)) == EXPECTED_PROFILE_COUNTS[profile]
        assert 8 <= len(grid) <= 30 and 6 <= len(grid[0]) <= 30
        assert len(markers) + 1 <= len(grid[0])
        assert row >= max(3 if color == 8 else 4 for _, color in markers)


def test_default_bands_reach_canonical_and_large_shapes():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({color for row in pair["input"] for color in row}))
        for pair in canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        inputs = set()
        shapes = set()
        observed_profiles = set()
        # Exercise public draws instead of requiring disjoint band heights,
        # exact profile balance, or a private enumeration implementation.
        for sample_index in range(120):
            grid = MODULE.generate(38_401 + 104_729 * sample_index, sample_index,
                                   difficulty=band)
            assert MODULE.self_check(grid) == []
            assert MODULE.rule_mirror(grid) == independent_oracle(grid)
            inputs.add(frozen(grid))
            shapes.add((len(grid), len(grid[0])))
            observed_profiles.add((len(grid), len(grid[0]),
                                   len({color for row in grid for color in row})))
        assert len(inputs) > 1
        assert canonical_profiles & observed_profiles
        assert any(max(shape) > 20 for shape in shapes)
        assert (30, 30) in shapes


def test_profile_marker_multisets_cover_both_heights_and_dense_mixed_cases():
    counts = set()
    marker_totals = set()
    for profile in MODULE.SCENE_PROFILES:
        n2, n8 = MODULE.PROFILE_COUNTS[profile]
        counts.add((n2, n8))
        marker_totals.add(n2 + n8)
    assert {1, 2, 3, 4, 5, 6, 7, 8} <= marker_totals
    assert (1, 0) in counts and (0, 1) in counts
    assert (1, 1) in counts and (2, 2) in counts
    assert (4, 0) in counts and (0, 4) in counts
    assert (3, 2) in counts and (4, 3) in counts and (4, 4) in counts and (4, 2) in counts


def test_rule_uses_marker_tip_then_color_one_and_preserves_everything_else():
    grid = [[0] * 8 for _ in range(9)]
    grid[6] = [1, 8, 1, 3, 1, 2, 1, 1]
    grid[8][7] = 9
    output = MODULE.rule_mirror(grid)
    assert [output[row][1] for row in range(3, 6)] == [8, 1, 1]
    assert [output[row][3] for row in range(2, 6)] == [3, 1, 1, 1]
    assert [output[row][5] for row in range(2, 6)] == [2, 1, 1, 1]
    assert output[6] == grid[6]
    assert output[8][7] == 9
    assert output == independent_oracle(grid)


def test_broad_rule_clips_columns_exactly_like_canonical_racket():
    grid = [[0] * 6 for _ in range(6)]
    grid[2] = [1, 3, 1, 1, 1, 1]
    output = MODULE.rule_mirror(grid)
    assert output[0][1] == output[1][1] == 1
    assert all(output[row][col] == grid[row][col] for row in range(6) for col in range(6) if col != 1)
    assert output == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_broad_rule_uses_first_row_containing_one_even_if_later_bar_exists():
    grid = [[0] * 7 for _ in range(8)]
    grid[2][4] = 1
    grid[6] = [1, 2, 1, 8, 1, 1, 1]
    assert MODULE.rule_mirror(grid) == grid
    assert MODULE.self_check(grid)


def test_rule_mirror_is_input_pure():
    grid = MODULE.generate(91, 9, difficulty="hard")
    before = frozen(grid)
    first = MODULE.rule_mirror(grid)
    second = MODULE.rule_mirror(grid)
    assert frozen(grid) == before
    assert first == second and first is not second and first[0] is not second[0]


@pytest.mark.parametrize(
    "grid",
    [
        [], [[]], [[0] * 6 for _ in range(8)], [[1] * 5 for _ in range(7)],
        [[False] * 6 for _ in range(8)], [[10] * 6 for _ in range(8)],
        [[0] * 6 for _ in range(7)] + [[0] * 5],
    ],
)
def test_malformed_and_degenerate_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium")
    bar_row, markers = independent_facts(grid)
    marker_col = markers[0][0]

    stray = [row[:] for row in grid]
    stray[-1][0] = 9
    assert MODULE.self_check(stray)

    second_bar = [row[:] for row in grid]
    second_bar[-1][0] = 1
    assert MODULE.self_check(second_bar)

    bad_marker = [row[:] for row in grid]
    bad_marker[bar_row][marker_col] = 3
    assert MODULE.self_check(bad_marker)

    no_marker = [row[:] for row in grid]
    for col, value in enumerate(no_marker[bar_row]):
        if value in (2, 8):
            no_marker[bar_row][col] = 1
    assert MODULE.self_check(no_marker)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(123_456)
    state = random.getstate()
    first = MODULE.generate(731, 19, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(731, 19, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 9
    assert second[0][0] == original
    assert MODULE.generate(731, 20, difficulty="hard") != second


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"}, {"texture": "no_bar"},
        {"grid_h": 10}, {"n_markers": 2}, {"include_8": False},
        {"difficulty": "expert"},
    ],
)
def test_unknown_and_retired_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


@pytest.mark.parametrize("name", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
def test_nonliteral_integer_draw_coordinates_fail_closed(name, value):
    kwargs = {"seed": 1, "sample_index": 2, name: value}
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(**kwargs)


def test_base_authority_and_reviewed_metadata_match_canonical_program():
    base = json.loads(BASE_PATH.read_text())
    source = canonical_row()["program_solution"]
    # Historical raw bytes can retain formatting; the selected target is exact.
    assert " ".join(base["racket_target"]["raw_code"].split()) == " ".join(source.split())
    assert base["racket_target"]["target_code"] == source
    description = base["description_target"]
    assert description["target_status"] == "reviewed_semantic_description"
    assert description["generator_parameters"] == ["scene_profile"]
    assert "color-8" in description["target_text"] or "color 8" in description["target_text"]
    assert "color-2" in description["target_text"] or "color 2" in description["target_text"]
