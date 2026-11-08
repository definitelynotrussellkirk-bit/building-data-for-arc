from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from puzzle_generators.base import gen_ctx
from reviewer_support import canonical_path, find_root


TASK = "bf53d21ff9fc"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
BASE = ROOT / "shared/data/base/solutions/training/182e5d0f__bf53d21ff9fc.json"
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    return rows[0]


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_trace(grid, marker):
    """Literal translation of the Racket walk, independent of generator helpers."""
    height, width = len(grid), len(grid[0])
    row, col = marker
    first = next(
        (
            (row + row_delta, col + col_delta)
            for row_delta, col_delta in DELTAS
            if 0 <= row + row_delta < height
            and 0 <= col + col_delta < width
            and grid[row + row_delta][col + col_delta] == 3
        ),
        None,
    )
    if first is None:
        return []
    previous, current = marker, first
    trail = [current]
    for _ in range(max(height, width)):
        following = next(
            (
                (current[0] + row_delta, current[1] + col_delta)
                for row_delta, col_delta in DELTAS
                if 0 <= current[0] + row_delta < height
                and 0 <= current[1] + col_delta < width
                and grid[current[0] + row_delta][current[1] + col_delta] == 3
                and (current[0] + row_delta, current[1] + col_delta) != previous
            ),
            None,
        )
        if following is not None:
            previous, current = current, following
            trail.append(following)
    return trail


def independent_oracle(grid):
    output = [list(row) for row in grid]
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    for marker in markers:
        trail = independent_trace(grid, marker)
        if len(trail) < 2:
            continue
        for row, col in trail:
            output[row][col] = 7
        output[trail[-1][0]][trail[-1][1]] = 3
        output[trail[-2][0]][trail[-2][1]] = 5
        output[marker[0]][marker[1]] = 7
    return output


def test_metadata_rule_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.1.0"
    assert MODULE.RULE_HASH == "29e5cb809c58"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    normalized = " ".join(canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(4))
def test_every_canonical_pair_is_exact_and_anchored(index):
    pair = (canonical_row()["train"] + canonical_row()["test"])[index]
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
    expected = MODULE._PUBLIC_INPUTS[profile]
    assert first == second == expected
    assert first is not expected and first[0] is not expected[0]
    assert MODULE.canonical_profile_signature(first) == profile


@pytest.mark.parametrize("profile", MODULE.PUBLIC_PROFILES)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_randomized_public_embeddings_stay_in_the_exact_d4_family(profile, band):
    grids = [MODULE._embed_public(profile, band, random.Random(20_000 + seed)) for seed in range(50)]
    assert len({frozen(grid) for grid in grids}) >= 47
    assert len({frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 47
    assert all(MODULE.canonical_family_signature(grid) == profile for grid in grids)
    assert all(MODULE.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_and_band_is_observable_valid_and_oracle_exact(profile, band):
    for seed in range(8):
        grid = MODULE.generate(10_000 + seed, seed * 31, difficulty=band, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
        facts = analysis["facts"]
        assert facts["palette"] == (0, 3, 5, 7)
        assert 1 <= len(facts["markers"]) <= 4
        assert facts["active_lengths"] and min(facts["active_lengths"]) >= 2


def test_general_profiles_encode_distinct_active_inactive_dormant_contrasts():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(80):
            grid = MODULE.generate(30_000 + seed, seed, difficulty="hard", scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            active = len(facts["active_markers"])
            inactive = len(facts["inactive_markers"])
            dormant = len(facts["dormant_components"])
            if profile == "single_active":
                assert (active, inactive, dormant) == (1, 0, 0)
            elif profile == "multi_active":
                assert 3 <= active <= 4 and inactive == dormant == 0
            elif profile == "mixed_markers":
                assert active >= 1 and inactive >= 1
            else:
                assert active >= 1 and inactive == 0 and dormant >= 1


def test_default_census_is_complete_balanced_and_highly_diverse():
    area_medians = {}
    for band in ("easy", "medium", "hard"):
        inputs, outputs, lengths = set(), set(), set()
        active_counts, inactive_counts, dormant_counts = set(), set(), set()
        profiles = Counter()
        areas = []
        for index in range(1200):
            grid = MODULE.generate(800_000, index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            facts = analysis["facts"]
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles[analysis["scene_profile"]] += 1
            lengths.update(facts["active_lengths"])
            active_counts.add(len(facts["active_markers"]))
            inactive_counts.add(len(facts["inactive_markers"]))
            dormant_counts.add(len(facts["dormant_components"]))
            areas.append(len(grid) * len(grid[0]))
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert min(profiles.values()) >= 90
        assert len(inputs) >= 1170
        assert len(outputs) >= 1170
        assert {1, 2} <= active_counts
        assert {0, 1} <= inactive_counts
        assert {0, 1} <= dormant_counts
        assert min(lengths) >= 3 and max(lengths) >= 9
        area_medians[band] = sorted(areas)[len(areas) // 2]
    assert area_medians["easy"] < area_medians["medium"] < area_medians["hard"]


def test_default_keyed_scene_profile_matches_the_returned_scene_profile():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            sample_index = seed * 7
            ctx = gen_ctx(
                seed=seed,
                sample_index=sample_index,
                version=MODULE.VERSION,
                task_id=MODULE.TASK_ID,
                difficulty=band,
                overrides={},
            )
            drawn = ctx.draw_choice(
                "scene_profile", MODULE._default_profile_choices(sample_index)
            )
            returned = MODULE._analysis(
                MODULE.generate(seed, sample_index, difficulty=band)
            )["scene_profile"]
            assert returned == drawn


def test_broad_rule_preserves_inactive_marker_dormant_route_zeros_and_unrelated_cells():
    grid = [[7] * 13 for _ in range(10)]
    grid[1][1] = 5
    for col in range(2, 8):
        grid[1][col] = 3
    grid[0][7] = grid[2][7] = 0
    grid[7][1] = 5
    grid[6][9] = grid[6][10] = grid[6][11] = 3
    grid[5][11] = grid[7][11] = 0
    before = frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert frozen(grid) == before
    assert output[7][1] == 5
    assert output[6][9:12] == [3, 3, 3]
    assert output[0][7] == output[2][7] == output[5][11] == output[7][11] == 0


def test_broad_rule_uses_cardinal_priority_up_down_left_right():
    grid = [[7] * 9 for _ in range(9)]
    grid[4][4] = 5
    grid[3][4] = grid[2][4] = grid[1][4] = 3
    grid[5][4] = grid[6][4] = grid[7][4] = 3
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert output[1][4] == 3 and output[2][4] == 5
    assert output[5][4] == output[6][4] == output[7][4] == 3


def test_broad_rule_reads_every_route_from_original_but_writes_cumulatively():
    grid = [[7] * 11 for _ in range(7)]
    grid[3][1] = grid[3][9] = 5
    for col in range(2, 9):
        grid[3][col] = 3
    first_trail = independent_trace(grid, (3, 1))
    second_trail = independent_trace(grid, (3, 9))
    assert first_trail == [(3, col) for col in range(2, 9)]
    assert second_trail == [(3, col) for col in range(8, 1, -1)]
    output = MODULE.rule_mirror(grid)
    assert output == independent_oracle(grid)
    assert output[3][2] == 3 and output[3][3] == 5
    assert output[3][8] == 7
    assert output[3][1] == output[3][9] == 7


def test_broad_rule_leaves_one_cell_trail_and_marker_unchanged():
    grid = [[7] * 7 for _ in range(7)]
    grid[3][3] = 5
    grid[3][4] = 3
    assert independent_trace(grid, (3, 3)) == [(3, 4)]
    assert MODULE.rule_mirror(grid) == grid


def test_broad_rule_matches_bounded_priority_walk_on_branch_and_cycle():
    branch = [[7] * 9 for _ in range(9)]
    branch[4][1] = 5
    for cell in ((4, 2), (4, 3), (3, 3), (5, 3), (5, 4)):
        branch[cell[0]][cell[1]] = 3
    cycle = [[7] * 9 for _ in range(9)]
    cycle[4][1] = 5
    for cell in ((4, 2), (3, 2), (2, 2), (2, 3), (2, 4), (3, 4), (4, 4), (4, 3)):
        cycle[cell[0]][cell[1]] = 3
    for grid in (branch, cycle):
        before = frozen(grid)
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)
        assert frozen(grid) == before


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[7] * 9 for _ in range(9)],
        [[False] * 9 for _ in range(9)],
        [[10] * 9 for _ in range(9)],
        [[7] * 9 for _ in range(8)] + [[7] * 8],
        [[0] * 9 for _ in range(9)],
        [[7 if (row, col) != (4, 4) else 5 for col in range(9)] for row in range(9)],
    ],
)
def test_malformed_and_minimal_impostors_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="single_active")
    facts = MODULE._analysis(grid)["facts"]

    no_zeros = [[7 if value == 0 else value for value in row] for row in grid]
    assert MODULE.self_check(no_zeros)

    no_green = [[7 if value == 3 else value for value in row] for row in grid]
    assert MODULE.self_check(no_green)

    extra_marker = [row[:] for row in grid]
    placed = 0
    greens = set(MODULE._positions(grid, 3))
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if extra_marker[row][col] == 7 and all(
                (row + dr, col + dc) not in greens for dr, dc in DELTAS
            ):
                extra_marker[row][col] = 5
                placed += 1
                if placed == 4:
                    break
        if placed == 4:
            break
    assert placed == 4 and MODULE.self_check(extra_marker)

    branch = [row[:] for row in grid]
    trail = facts["traces"][facts["active_markers"][0]]
    added = False
    trail_set = set(trail)
    for row, col in trail[1:-1]:
        for dr, dc in DELTAS:
            candidate = (row + dr, col + dc)
            if (
                candidate not in trail_set
                and 0 <= candidate[0] < len(branch)
                and 0 <= candidate[1] < len(branch[0])
                and branch[candidate[0]][candidate[1]] == 7
            ):
                branch[candidate[0]][candidate[1]] = 3
                added = True
                break
        if added:
            break
    assert added and MODULE.self_check(branch)


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


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_must_be_a_literal_integer(seed):
    with pytest.raises(ValueError, match="seed must be a literal integer"):
        MODULE.generate(seed, 2)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1, None])
def test_sample_index_must_be_a_nonnegative_literal_integer(sample_index):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative literal integer"):
        MODULE.generate(1, sample_index)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "warm"},
        {"grid_h": 17},
        {"palette_kind": "broad"},
        {"marker_count": 3},
        {"route_kind": "branch"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_pinned_profile_floor_has_exact_support_in_every_band_and_envelope_support():
    pairs = canonical_row()["train"] + canonical_row()["test"]
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in pairs
    }
    heights = [profile[0] for profile in canonical_profiles]
    widths = [profile[1] for profile in canonical_profiles]
    palettes = [profile[2] for profile in canonical_profiles]
    envelope = (
        (min(heights), max(heights)),
        (min(widths), max(widths)),
        (min(palettes), max(palettes)),
    )
    exact_total = 0
    envelope_total = 0
    per_band_exact = {}
    for band in ("easy", "medium", "hard"):
        band_exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = MODULE.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid), len(grid[0]),
                len({value for row in grid for value in row}),
            )
            is_exact = profile in canonical_profiles
            band_exact += is_exact
            exact_total += is_exact
            envelope_total += (
                envelope[0][0] <= profile[0] <= envelope[0][1]
                and envelope[1][0] <= profile[1] <= envelope[1][1]
                and envelope[2][0] <= profile[2] <= envelope[2][1]
            )
        per_band_exact[band] = band_exact
    assert all(count >= 1 for count in per_band_exact.values()), per_band_exact
    assert exact_total >= 3
    assert envelope_total >= 15


def test_semantic_contract_accepts_authority_and_refutes_declared_rivals():
    assert MODULE.EXAMPLES_NEEDED == 3
    assert MODULE.MIN_STRICT_FRAC == 1.0
    assert set(MODULE.SEMANTIC_RIVALS) == set(MODULE.LESSON_COMPETITORS)
    assert set(MODULE.WITNESS_RIVALS) <= set(MODULE.SEMANTIC_WITNESSES)
    assert set(MODULE.BRANCH_WITNESSES) <= set(MODULE.SEMANTIC_WITNESSES)

    for pair in canonical_row()["train"] + canonical_row()["test"]:
        assert MODULE.strict_canonical_like(pair["input"]) == []

    single = MODULE.generate(101, 3, scene_profile="single_active")
    expected = MODULE.rule_mirror(single)
    for witness_name in ("penultimate_not_endpoint", "route_is_consumed"):
        assert MODULE.SEMANTIC_WITNESSES[witness_name](single) is True
        claimed = MODULE.WITNESS_RIVALS[witness_name]
        assert claimed
        assert any(MODULE.SEMANTIC_RIVALS[name](single) != expected for name in claimed)

    branch_cases = {
        "multiple_active_markers": MODULE.generate(102, 4, difficulty="hard", scene_profile="multi_active"),
        "inactive_marker_preserved": MODULE.generate(103, 5, scene_profile="mixed_markers"),
        "dormant_route_preserved": MODULE.generate(104, 6, scene_profile="dormant_routes"),
    }
    for witness_name, grid in branch_cases.items():
        assert MODULE.SEMANTIC_WITNESSES[witness_name](grid) is True

    demo_inputs = [
        MODULE.generate(201, 1, scene_profile="single_active"),
        MODULE.generate(202, 2, scene_profile="mixed_markers"),
        MODULE.generate(203, 3, scene_profile="dormant_routes"),
    ]
    demos = [{"input": grid, "output": MODULE.rule_mirror(grid)} for grid in demo_inputs]
    query_grid = MODULE.generate(204, 4, difficulty="hard", scene_profile="multi_active")
    assert MODULE.lesson_identifiable(demos, {"input": query_grid}) == []

    corrupted = [{"input": demos[0]["input"], "output": demos[0]["input"]}, *demos[1:]]
    assert MODULE.lesson_identifiable(corrupted, {"input": query_grid})


def test_base_source_and_description_are_synchronized_to_canonical_authority():
    row = canonical_row()
    base = json.loads(BASE.read_text())
    target = base["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert " ".join(target["raw_code"].split()) == " ".join(row["program_solution"].split())
    assert target["raw_code"] != target["target_code"]
    assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == (
        "97e20ab83b05f4eee4624c2985fd2db5f07bbfd9e5c1e01b1573d4947dfb9611"
    )
    description = base["description_target"]
    assert description["target_status"] == "reviewed_semantic_description"
    notes = description["ambiguity_notes"]
    assert "original input" in notes
    assert "cumulative output" in notes
    assert "up/down/left/right" in notes
    constraints = " ".join(description["negative_constraints"])
    assert "inactive gray markers" in constraints
    assert "zero endpoint caps" in constraints
