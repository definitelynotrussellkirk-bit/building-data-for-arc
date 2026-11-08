"""Focused semantic tests for the fc814cec3976 dense-window generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from statistics import median

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator("fc814cec3976", root=ROOT)
CANONICAL = canonical_path(ROOT)
DATA_ROOT = CANONICAL.parent.parent
BASE_PATHS = (
    DATA_ROOT / "base/solutions/training/9caba7c3__fc814cec3976.json",
    DATA_ROOT / "base/solutions/augmented/9caba7c3__57c0026f8238.json",
)


def _canonical_rows():
    with CANONICAL.open(encoding="utf-8") as handle:
        return [
            row
            for line in handle
            if (row := json.loads(line)).get("task_id") == gen.TASK_ID
        ]


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT)


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _independent_analysis(grid):
    height, width = len(grid), len(grid[0])
    candidates = []
    for top in range(height - 2):
        for left in range(width - 2):
            cells = tuple(
                (top + delta_row, left + delta_col)
                for delta_row in range(3)
                for delta_col in range(3)
            )
            reds = tuple(point for point in cells if grid[point[0]][point[1]] == 2)
            if (
                reds
                and grid[top + 1][left + 1] == 5
                and all(grid[row][col] in (2, 5) for row, col in cells)
            ):
                candidates.append((top, left, cells, reds))
    candidates.sort(key=lambda item: (-len(item[3]), item[0], item[1]))
    selected = []
    rejected = []
    covered = set()
    for candidate in candidates:
        overlap = set(candidate[3]) & covered
        if overlap:
            rejected.append((candidate, overlap))
        else:
            selected.append(candidate)
            covered.update(candidate[3])
    return candidates, selected, rejected, covered


def _independent_oracle(grid):
    _, selected, _, _ = _independent_analysis(grid)
    output = copy.deepcopy(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            hit = next((item for item in selected if (row, col) in item[2]), None)
            if hit is not None and grid[row][col] == 5:
                output[row][col] = 4 if (row, col) == (hit[0] + 1, hit[1] + 1) else 7
    return output


def _components4(grid, colors=(5,)):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in colors
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        components.append(component)
    return components


def test_identity_version_hash_and_curriculum_size():
    assert gen.GENERATOR_ID == gen.TASK_ID == "fc814cec3976"
    assert gen.VERSION == "3.1.0"
    assert gen.SCENE_COUNT == 32765
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    normalized = " ".join(next(iter(rules)).split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_canonical_inventory_has_two_rows_eight_occurrences_and_four_inputs():
    rows = _canonical_rows()
    pairs = _canonical_pairs()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    assert len(rows) == 2
    assert len(pairs) == 8
    assert len({_key(pair["input"]) for pair in pairs}) == 4
    assert {gen.canonical_profile_signature(pair["input"]) for pair in pairs} == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_occurrence_matches_independent_oracle(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original


def test_canonical_candidate_and_overlap_inventory_is_exact():
    expected = {
        "public_1": (7, 4, 3, (6, 4, 3, 3)),
        "public_2": (4, 4, 0, (6, 4, 2, 1)),
        "public_3": (7, 4, 3, (5, 3, 2, 2)),
        "public_4": (6, 4, 2, (3, 3, 2, 2)),
    }
    seen = set()
    for pair in _canonical_pairs():
        profile = gen.canonical_profile_signature(pair["input"])
        if profile in seen:
            continue
        seen.add(profile)
        candidates, selected, rejected, covered = _independent_analysis(pair["input"])
        exp_candidates, exp_selected, exp_rejected, exp_counts = expected[profile]
        assert (len(candidates), len(selected), len(rejected)) == (
            exp_candidates, exp_selected, exp_rejected,
        )
        assert tuple(len(candidate[3]) for candidate in selected) == exp_counts
        assert covered == {
            (row, col)
            for row, values in enumerate(pair["input"])
            for col, value in enumerate(values)
            if value == 2
        }


def test_all_thirty_two_d8_topologies_are_unique_and_semantically_valid():
    assert len(gen._TEMPLATES) == len(gen._RED_LAYOUT_TO_TEMPLATE) == 32
    observed = set()
    for template in gen._TEMPLATES.values():
        grid = [list(row) for row in template["grid"]]
        candidates, selected, _, covered = _independent_analysis(grid)
        reds = {point for point in template["red_key"]}
        assert 4 <= len(candidates) <= 7
        assert len(selected) == 4
        assert covered == reds
        observed.add((template["profile"], template["transform_index"]))
    assert observed == {
        (profile, transform_index)
        for profile in gen.PUBLIC_PROFILES
        for transform_index in range(8)
    }


@pytest.mark.parametrize("profile,code", tuple(zip(gen.PUBLIC_PROFILES, (0, 5, 10, 15))))
def test_forced_anchor_codes_are_exact_fresh_canonical_inputs(profile, code):
    first = gen.generate(100, 7, scene_code=code)
    second = gen.generate(999, 88, difficulty="hard", scene_code=code)
    assert _key(first) == _key(second) == gen._PUBLIC_INPUTS[profile]
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert gen.canonical_profile_signature(first) == profile
    assert gen.canonical_family_signature(first) == profile
    assert gen.observe_overrides(first) == {"scene_code": code}


@pytest.mark.parametrize("code", [1, 2, 3, 4, 16, 123, 4096, 16384, 32763, 32764])
def test_forced_general_codes_are_exact_and_observable(code):
    grid = gen.generate(200 + code, 3, scene_code=code)
    analysis = gen._analysis(grid)
    assert analysis["errors"] == []
    assert gen.observe_overrides(grid) == {"scene_code": code}
    assert gen.canonical_family_signature(grid) is None
    assert analysis["facts"]["transform_index"] in range(1, 8)
    assert gen.rule_mirror(grid) == _independent_oracle(grid)


def test_sparse_code_probe_is_injective_and_exactly_recoverable():
    codes = list(range(0, gen.SCENE_COUNT, 31)) + [gen.SCENE_COUNT - 1]
    grids = [gen.generate(0, 0, scene_code=code) for code in codes]
    assert len({_key(grid) for grid in grids}) == len(codes)
    assert [gen.observe_overrides(grid)["scene_code"] for grid in grids] == codes


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_equal_counter_stream_has_5000_unique_inputs_and_exact_public_rate(difficulty):
    grids = [gen.generate(index, index, difficulty=difficulty) for index in range(5000)]
    assert len({_key(grid) for grid in grids}) == 5000
    public = [gen.canonical_family_signature(grid) for grid in grids]
    assert sum(profile is not None for profile in public) == 1000
    counts = Counter(public)
    assert max(counts[profile] for profile in gen.PUBLIC_PROFILES) - min(
        counts[profile] for profile in gen.PUBLIC_PROFILES
    ) <= 4


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_fixed_seed_stream_has_5000_unique_inputs_and_exact_public_rate(difficulty):
    grids = [gen.generate(7000, index, difficulty=difficulty) for index in range(5000)]
    assert len({_key(grid) for grid in grids}) == 5000
    public = [gen.canonical_family_signature(grid) for grid in grids]
    assert sum(profile is not None for profile in public) == 1000
    counts = Counter(public)
    assert max(counts[profile] for profile in gen.PUBLIC_PROFILES) - min(
        counts[profile] for profile in gen.PUBLIC_PROFILES
    ) <= 4


def test_four_band_health_stream_is_globally_unique():
    grids = []
    for band_index, difficulty in enumerate((None, "easy", "medium", "hard")):
        grids.extend(
            gen.generate(band_index * 100000 + index, index, difficulty=difficulty)
            for index in range(1000)
        )
    assert len({_key(grid) for grid in grids}) == 4000


def test_many_seed_six_sample_probe_is_input_and_pair_unique():
    grids = [
        gen.generate(1 + episode * 101, sample_index)
        for episode in range(50)
        for sample_index in range(6)
    ]
    pairs = {(_key(grid), _key(gen.rule_mirror(grid))) for grid in grids}
    assert len({_key(grid) for grid in grids}) == 300
    assert len(pairs) == 300


def test_linter_pattern_has_full_input_and_output_diversity():
    grids = [
        gen.generate(episode * 101, sample_index)
        for episode in range(24)
        for sample_index in range(6)
    ]
    assert len({_key(grid) for grid in grids}) == 144
    assert len({_key(gen.rule_mirror(grid)) for grid in grids}) == 144


def test_all_eight_symmetries_and_four_profiles_are_reached_naturally():
    analyses = [gen._analysis(gen.generate(index, index)) for index in range(500)]
    assert {analysis["facts"]["transform_index"] for analysis in analyses} == set(range(8))
    assert {
        analysis["facts"]["public_profile"]
        for analysis in analyses
        if analysis["facts"]["public_profile"] is not None
    } == set(gen.PUBLIC_PROFILES)


def test_generated_distribution_matches_dense_official_shape_palette_and_density():
    gray_counts = set()
    object_counts = []
    for index in range(400):
        grid = gen.generate(index, index, difficulty="medium")
        analysis = gen._analysis(grid)
        facts = analysis["facts"]
        assert analysis["errors"] == []
        assert (facts["height"], facts["width"]) == (19, 19)
        assert facts["palette"] == {0, 2, 5}
        assert 177 <= facts["counts"][5] <= 223
        assert facts["counts"][5] >= facts["counts"][0]
        assert 10 <= facts["red_count"] <= 16
        assert len(facts["selected"]) == 4
        gray_counts.add(facts["counts"][5])
        object_counts.append(len(_components4(grid)))
    assert gray_counts == set(range(177, 224))
    assert min(object_counts) >= 18
    assert 35 <= median(object_counts) <= 45
    assert max(object_counts) <= 60


def test_natural_curriculum_contains_clean_and_competing_candidate_lessons():
    rejected_counts = Counter()
    selected_red_profiles = set()
    for index in range(200):
        facts = gen._analysis(gen.generate(index, index))["facts"]
        rejected_counts[len(facts["rejected"])] += 1
        selected_red_profiles.add(tuple(candidate["red_count"] for candidate in facts["selected"]))
    # Structural contrasts add five-candidate scenes with one rejected window.
    assert set(rejected_counts) == {0, 1, 2, 3}
    assert selected_red_profiles == {
        (6, 4, 3, 3),
        (6, 4, 2, 1),
        (5, 3, 2, 2),
        (3, 3, 2, 2),
    }


def test_output_changes_only_selected_gray_cells_and_marks_four_centers():
    for code in (0, 1, 5, 16, 1234, 32764):
        grid = gen.generate(1, 2, scene_code=code)
        output = gen.rule_mirror(grid)
        analysis = gen._analysis(grid)
        selected_cells = {
            point for candidate in analysis["facts"]["selected"] for point in candidate["cells"]
        }
        changes = [
            (row, col, grid[row][col], output[row][col])
            for row in range(19)
            for col in range(19)
            if grid[row][col] != output[row][col]
        ]
        assert changes
        assert all((row, col) in selected_cells and before == 5 and after in (4, 7)
                   for row, col, before, after in changes)
        assert sum(after == 4 for _, _, _, after in changes) == 4
        assert all(output[row][col] == 2 for row in range(19) for col in range(19)
                   if grid[row][col] == 2)


def test_noise_variation_never_changes_candidate_topology_for_a_red_layout():
    codes = [20 + 5 * offset for offset in range(0, 200, 4)]
    signatures = set()
    for code in codes:
        grid = gen.generate(1, 1, scene_code=code)
        candidates, selected, rejected, _ = _independent_analysis(grid)
        signatures.add((
            tuple((item[0], item[1], len(item[3])) for item in candidates),
            tuple((item[0], item[1], len(item[3])) for item in selected),
            len(rejected),
        ))
    assert len(signatures) == 1


def test_rule_mirror_is_broad_input_pure_and_a_b_a_stable():
    first = gen.generate(71, 4, scene_code=1)
    second = gen.generate(72, 5, scene_code=6)
    first_original = copy.deepcopy(first)
    out_a1 = gen.rule_mirror(first)
    out_b = gen.rule_mirror(second)
    out_a2 = gen.rule_mirror(first)
    assert out_a1 == out_a2 == _independent_oracle(first)
    assert out_b == _independent_oracle(second)
    assert first == first_original

    broad = [[0] * 6 for _ in range(6)]
    for row in range(1, 4):
        for col in range(2, 5):
            broad[row][col] = 5
    broad[1][2] = 2
    assert gen.self_check(broad)
    assert gen.rule_mirror(broad) == _independent_oracle(broad)


def test_reading_order_tie_is_exercised_by_d8_views():
    # public_4 has two top-priority candidates with three red cells each.
    orders = set()
    for transform_index in range(8):
        template = gen._TEMPLATES[(3, transform_index)]
        candidates, selected, _, _ = _independent_analysis(template["grid"])
        assert len(candidates[0][3]) == len(candidates[1][3]) == 3
        assert (candidates[0][0], candidates[0][1]) < (candidates[1][0], candidates[1][1])
        orders.add(tuple((item[0], item[1]) for item in selected[:2]))
    assert len(orders) == 8


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(20260722)
    state = random.getstate()
    first = gen.generate(777, 21, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(777, 21, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(777, 21, difficulty="hard") == second


@pytest.mark.parametrize("bad", [
    [],
    [[]],
    [[0, 2], [0]],
    [[False] * 19 for _ in range(19)],
    [[11] * 19 for _ in range(19)],
    [[0] * 18 for _ in range(19)],
    [[0] * 19 for _ in range(18)],
    [[0] * 19 for _ in range(19)],
    [[5] * 19 for _ in range(19)],
])
def test_malformed_and_degenerate_inputs_fail_closed(bad):
    assert gen.self_check(bad)


def test_red_topology_mutation_fails_closed():
    grid = gen.generate(1, 1, scene_code=1234)
    red = next((row, col) for row in range(19) for col in range(19) if grid[row][col] == 2)
    grid[red[0]][red[1]] = 5
    assert any("red cells" in message for message in gen.self_check(grid))


def test_code_bit_mutation_fails_closed_or_decodes_to_a_different_exact_scene():
    code = 1234
    grid = gen.generate(1, 1, scene_code=code)
    template = gen._RED_LAYOUT_TO_TEMPLATE[gen._red_key(grid)]
    row, col = template["bit_positions"][0]
    grid[row][col] = 0 if grid[row][col] == 5 else 5
    errors = gen.self_check(grid)
    assert errors
    assert gen.observe_overrides(grid) == {}


def test_protected_noise_mutation_fails_closed_without_changing_code_bits():
    grid = gen.generate(1, 1, scene_code=4321)
    template = gen._RED_LAYOUT_TO_TEMPLATE[gen._red_key(grid)]
    row, col = next(
        point
        for point in template["protected"]
        if grid[point[0]][point[1]] in (0, 5) and point not in template["bit_positions"]
    )
    grid[row][col] = 0 if grid[row][col] == 5 else 5
    assert any("noise cells" in message for message in gen.self_check(grid))


@pytest.mark.parametrize("overrides", [
    {"scene_code": -1},
    {"scene_code": gen.SCENE_COUNT},
    {"scene_code": "1"},
    {"unknown": 1},
])
def test_invalid_controls_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="extreme")


def test_selected_authorities_match_canonical_and_archival_bytes_are_preserved():
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    canonical = next(iter(rules))
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["target_code"] == canonical
        assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == (
            "98e91a32d7ba35d68ec7ef9dcec53331bdba449e6c2dec5b09a1b7c26e9430a0"
        )
        assert target["needs_conversion"] is False


def test_base_descriptions_explain_dense_noise_priority_overlap_and_colors():
    required = (
        "dense 19x19",
        "red-cell count",
        "reading order",
        "greedily",
        "yellow 4",
        "orange 7",
        "outside noise unchanged",
    )
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        description = base["description_target"]
        assert description["target_status"] == "source_written"
        text = description["target_text"].lower()
        assert all(phrase in text for phrase in required)
        negatives = " ".join(description["negative_constraints"])
        assert "isolated" in negatives
        assert "overlapping candidates independently" in negatives
        assert base["primitive_metadata"]["primitive_chain"][-1] == "cellmap"
