from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "c5905adcd2cb"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
CANONICAL = canonical_path(ROOT)


def base_solution_path(split, name):
    for data_root in (ROOT / "data", ROOT / "shared" / "data"):
        path = data_root / "base" / "solutions" / split / name
        if path.is_file():
            return path
    raise FileNotFoundError(name)


BASE_PATHS = (
    base_solution_path("training", "6d0160f0__c5905adcd2cb.json"),
    base_solution_path("augmented", "6d0160f0__3adba1c5d4d5.json"),
)


def canonical_rows():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert [(row["source"], len(row["train"]), len(row["test"])) for row in rows] == [
        ("training", 4, 1), ("augmented", 5, 0)
    ]
    return rows


def unique_pairs():
    found = {}
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            found.setdefault(tuple(map(tuple, pair["input"])), pair)
    assert len(found) == 5
    return list(found.values())


def frozen(grid):
    return tuple(map(tuple, grid))


def independent_facts(grid):
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    ]
    if not markers:
        raise ValueError("no marker")
    marker_row, marker_col = markers[0]
    source_row, source_col = marker_row // 4 * 4, marker_col // 4 * 4
    destination_row, destination_col = marker_row % 4 * 4, marker_col % 4 * 4
    source_cells = tuple(
        (row, col, grid[row][col])
        for row in range(source_row, source_row + 3)
        for col in range(source_col, source_col + 3)
        if grid[row][col] not in (0, 5)
    )
    return {
        "marker": (marker_row, marker_col),
        "source": (source_row // 4, source_col // 4),
        "destination": (destination_row // 4, destination_col // 4),
        "source_origin": (source_row, source_col),
        "destination_origin": (destination_row, destination_col),
        "source_cells": source_cells,
    }


def independent_oracle(grid):
    facts = independent_facts(grid)
    output = [[5 if value == 5 else 0 for value in row] for row in grid]
    source_row, source_col = facts["source_origin"]
    destination_row, destination_col = facts["destination_origin"]
    for row, col, value in facts["source_cells"]:
        output[destination_row + row - source_row][destination_col + col - source_col] = value
    return output


def test_metadata_hash_and_control_surface_are_exact():
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "93e6c6c4b04f"
    assert tuple(MODULE.AXES) == ("scene_profile",)
    assert MODULE.SCENE_PROFILES == MODULE.PUBLIC_PROFILES + MODULE.GENERAL_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    programs = {" ".join(row["program_solution"].split()) for row in canonical_rows()}
    assert len(programs) == 1
    assert hashlib.sha256(programs.pop().encode()).hexdigest()[:12] == MODULE.RULE_HASH


@pytest.mark.parametrize("index", range(5))
def test_every_unique_canonical_pair_is_exact_and_anchored(index):
    pair = unique_pairs()[index]
    profile = f"public_{index + 1}"
    assert MODULE.canonical_profile_signature(pair["input"]) == profile
    assert MODULE.canonical_family_signature(pair["input"]) == profile
    assert MODULE.self_check(pair["input"]) == []
    assert MODULE.rule_mirror(pair["input"]) == independent_oracle(pair["input"])
    assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_all_ten_canonical_occurrences_execute_exactly():
    occurrences = 0
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            assert MODULE.rule_mirror(pair["input"]) == pair["output"]
            occurrences += 1
    assert occurrences == 10


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
def test_random_public_recolorings_preserve_complete_official_families(profile):
    grids = [MODULE._embed_public(profile, random.Random(20_000 + seed)) for seed in range(60)]
    assert len({frozen(grid) for grid in grids}) >= 55
    assert all(MODULE.canonical_family_signature(grid) == profile for grid in grids)
    assert all(MODULE.self_check(grid) == [] for grid in grids)
    assert all(MODULE.rule_mirror(grid) == independent_oracle(grid) for grid in grids)


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
        assert len(grid) == len(grid[0]) == 11
        assert analysis["facts"]["changed"] >= 15


def test_general_profiles_encode_distinct_clear_and_copy_boundaries():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(80):
            grid = MODULE.generate(30_000 + seed, seed, difficulty="hard", scene_profile=profile)
            facts = MODULE._analysis(grid)["facts"]
            if profile == "same_destination":
                assert facts["source_macro"] == facts["destination_macro"]
            elif profile == "marker_only":
                assert facts["source_count"] == 1
            elif profile == "full_source":
                assert facts["source_count"] == 9
            elif profile == "empty_destination":
                assert facts["destination_input_count"] == 0
            elif profile == "light_destination":
                assert 1 <= facts["destination_input_count"] <= 4
            else:
                assert facts["destination_input_count"] >= 5


def test_default_census_is_complete_dense_and_band_aware():
    density_medians = {}
    for band in ("easy", "medium", "hard"):
        inputs, outputs = set(), set()
        profiles = Counter()
        sources, destinations, source_counts, changed_counts = set(), set(), set(), set()
        densities = []
        for index in range(1200):
            grid = MODULE.generate(800_000, index, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            assert analysis["output"] == independent_oracle(grid)
            facts = analysis["facts"]
            inputs.add(frozen(grid))
            outputs.add(frozen(analysis["output"]))
            profiles[analysis["scene_profile"]] += 1
            sources.add(facts["source_macro"])
            destinations.add(facts["destination_macro"])
            source_counts.add(facts["source_count"])
            changed_counts.add(facts["changed"])
            densities.append(facts["non_lattice_count"])
        assert len(inputs) >= 1160
        assert len(outputs) >= 980
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert min(profiles.values()) >= 60
        assert sources == destinations == set(MODULE.MACROS)
        assert {1, 3, 4, 5, 6, 9} <= source_counts
        assert min(changed_counts) >= 15 and max(changed_counts) >= 45
        density_medians[band] = sorted(densities)[len(densities) // 2]
    assert density_medians["easy"] < density_medians["medium"] < density_medians["hard"]


def test_rule_copies_marker_and_all_source_colors_then_clears_distractors():
    grid = MODULE.generate(51, 3, difficulty="hard", scene_profile="dense_destination")
    facts = independent_facts(grid)
    output = MODULE.rule_mirror(grid)
    destination_row, destination_col = facts["destination_origin"]
    source_row, source_col = facts["source_origin"]
    copied = {
        (destination_row + row - source_row, destination_col + col - source_col, value)
        for row, col, value in facts["source_cells"]
    }
    assert any(value == 4 for _, _, value in copied)
    assert all(output[row][col] == value for row, col, value in copied)
    assert all(
        value == 5 or (row, col, output[row][col]) in copied or output[row][col] == 0
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )


def test_broad_rule_preserves_gray_outside_the_lattice():
    grid = MODULE.generate(61, 4, difficulty="medium", scene_profile="empty_destination")
    grid[0][0] = 5
    output = MODULE.rule_mirror(grid)
    assert output[0][0] == 5
    assert output == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_broad_rule_uses_first_marker_when_multiple_exist():
    grid = MODULE.generate(71, 5, difficulty="medium", scene_profile="light_destination")
    first = independent_facts(grid)["marker"]
    candidate = next(
        (row, col)
        for row in range(first[0], 11)
        for col in range(11)
        if (row, col) > first and row not in MODULE.SEPARATORS and col not in MODULE.SEPARATORS
        and grid[row][col] == 0
    )
    grid[candidate[0]][candidate[1]] = 4
    assert independent_facts(grid)["marker"] == first
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.self_check(grid)


def test_same_destination_preserves_source_but_clears_every_other_interior():
    grid = MODULE.generate(81, 6, difficulty="hard", scene_profile="same_destination")
    facts = independent_facts(grid)
    assert facts["source"] == facts["destination"]
    output = MODULE.rule_mirror(grid)
    source_positions = {(row, col, value) for row, col, value in facts["source_cells"]}
    assert all(output[row][col] == value for row, col, value in source_positions)
    assert sum(value not in (0, 5) for row in output for value in row) == len(source_positions)


def test_rule_mirror_is_input_pure_and_requires_marker():
    grid = MODULE.generate(91, 9, difficulty="hard")
    before = frozen(grid)
    MODULE.rule_mirror(grid)
    assert frozen(grid) == before
    with pytest.raises(ValueError):
        MODULE.rule_mirror(MODULE._empty_lattice())


@pytest.mark.parametrize(
    "grid",
    [
        [], [[]], [[0] * 11 for _ in range(10)], [[5] * 11 for _ in range(11)],
        [[False] * 11 for _ in range(11)], [[10] * 11 for _ in range(11)],
        [[0] * 11 for _ in range(10)] + [[0] * 10],
    ],
)
def test_malformed_and_degenerate_inputs_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_structural_mutations_fail_closed():
    grid = MODULE.generate(811, 7, difficulty="medium", scene_profile="light_destination")
    broken_row = [row[:] for row in grid]
    broken_row[3][0] = 0
    assert MODULE.self_check(broken_row)
    extra_gray = [row[:] for row in grid]
    extra_gray[0][0] = 5
    assert MODULE.self_check(extra_gray)
    no_marker = [[0 if value == 4 else value for value in row] for row in grid]
    assert MODULE.self_check(no_marker)
    duplicate_marker = [row[:] for row in grid]
    duplicate_marker[0][0] = 4
    assert MODULE.self_check(duplicate_marker)
    sparse = MODULE._empty_lattice()
    sparse[0][0] = 4
    assert MODULE.self_check(sparse)


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
        {"scene_profile": "unknown"}, {"texture": "upper"}, {"grid_size": 16},
        {"source_block": "ul"}, {"palette_kind": "cool"}, {"accent": 3},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **kwargs)


def test_selected_authorities_match_canonical_and_archival_raw_is_equivalent():
    source = next(row for row in canonical_rows() if row["source"] == "training")["program_solution"]
    normalized = " ".join(source.split())
    for path in BASE_PATHS:
        base = json.loads(path.read_text())
        assert base["racket_target"]["target_code"] == source
        assert " ".join(base["racket_target"]["raw_code"].split()) == normalized


@pytest.mark.parametrize("seed", [True, False, 1.0])
def test_generate_rejects_nonliteral_integer_seed(seed):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, -1])
def test_generate_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(991, sample_index)


def test_semantic_contract_accepts_only_lawful_lattice_inputs():
    for pair in unique_pairs():
        assert MODULE.strict_canonical_like(pair["input"]) == []
    malformed = MODULE._empty_lattice()
    assert MODULE.strict_canonical_like(malformed)


def test_semantic_witnesses_refute_their_named_rivals():
    grid = MODULE.generate(1_700_001, 23, difficulty="hard", scene_profile="dense_destination")
    canonical = MODULE.rule_mirror(grid)
    assert set(MODULE.SEMANTIC_WITNESSES) == {"marker_is_payload", "global_clear"}
    assert set(MODULE.SEMANTIC_RIVALS) == {"drop_marker", "preserve_distractors"}
    for witness_name, rival_names in MODULE.WITNESS_RIVALS.items():
        assert MODULE.SEMANTIC_WITNESSES[witness_name](grid) is True
        assert any(MODULE.SEMANTIC_RIVALS[name](grid) != canonical for name in rival_names)


def test_lesson_identifiability_contract_rejects_surviving_wrong_rule():
    grids = [
        MODULE.generate(1_700_002, index, difficulty="medium", scene_profile=profile)
        for index, profile in enumerate(("empty_destination", "same_destination", "full_source", "light_destination"))
    ]
    pairs = [{"input": grid, "output": MODULE.rule_mirror(grid)} for grid in grids]
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []

    wrong_demos = [
        {"input": pair["input"], "output": MODULE.SEMANTIC_RIVALS["drop_marker"](pair["input"])}
        for pair in pairs[:3]
    ]
    reasons = MODULE.lesson_identifiable(wrong_demos, pairs[3])
    assert any("drop_marker" in reason for reason in reasons)
