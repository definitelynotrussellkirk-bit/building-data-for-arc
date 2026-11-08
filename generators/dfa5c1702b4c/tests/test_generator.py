"""Source/runtime portable regressions, using an independent geometry oracle."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators" / "dfa5c1702b4c"
if not (HOME / "generator.py").is_file():
    HOME = ROOT / "puzzle_generators" / "per_puzzle" / "dfa5c1702b4c"
spec = importlib.util.spec_from_file_location("dfa5c1702b4c_sampler_probe", HOME / "workspace" / "probe_sampler.py")
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)
gen = probe.load_generator()


def rectangle_grid(boxes, height=12, width=14):
    grid = [[0] * width for _ in range(height)]
    for color, r0, r1, c0, c1 in boxes:
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                grid[row][col] = color
    return grid


def assert_domain(grid):
    assert probe.geometry_errors(grid) == []
    assert gen.self_check(grid) == []
    assert all(len(box["rows"]) <= 4 and len(box["cols"]) <= 4 for box in probe.color_boxes(grid))


@pytest.mark.parametrize("pair", probe.get_canonical_pairs(),
                         ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    grid = deepcopy(pair["input"])
    assert probe.geometry_errors(grid) == []
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert probe.oracle(grid) == pair["output"]
    assert grid == pair["input"]


def test_retained_racket_witnesses_support_domain_and_independent_oracle():
    evidence = json.loads((HOME / "counterexamples" / "current-review-racket-witnesses.json").read_text())
    assert evidence["executed_rule_hash"] == probe.RULE_HASH
    assert evidence["rule_hash_matches_catalog"] is True
    assert len(evidence["results"]) == 2
    for pair in evidence["results"]:
        assert pair["valid_output"] and pair["error"] is None
        assert gen.self_check(pair["input"]) == []
        assert probe.geometry_errors(pair["input"]) == []
        assert probe.oracle(pair["input"]) == pair["output"]


def test_public_axes_are_only_exact_integer_controls():
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_distinct_colors"}


def test_original_exact_control_regression():
    options = {"grid_h": 20, "grid_w": 20, "n_distinct_colors": 7}
    grid = gen.generate(0, 0, difficulty="easy", **options)
    assert probe.observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert_domain(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,count", [(10, 11, 7), (10, 20, 2), (20, 11, 2), (20, 20, 7)])
def test_exact_controls_override_every_difficulty(band, height, width, count):
    options = {"grid_h": height, "grid_w": width, "n_distinct_colors": count}
    for sample_index in (0, 1):
        grid = gen.generate(47, sample_index, difficulty=band, **options)
        assert probe.observed(grid) == options
        assert gen.observe_overrides(grid) == options
        assert_domain(grid)
        assert grid == gen.generate(47, sample_index, difficulty=band, **options)


def test_every_joint_integer_axis_combination_is_constructive():
    for height in range(10, 21):
        for width in range(11, 21):
            for count in range(2, 8):
                options = {"grid_h": height, "grid_w": width, "n_distinct_colors": count}
                grid = gen.generate(29, height + width + count, **options)
                assert probe.observed(grid) == options, options
                assert_domain(grid)


@pytest.mark.parametrize("key,value", [
    ("grid_h", 9), ("grid_h", 21), ("grid_w", 10), ("grid_w", 21),
    ("n_distinct_colors", 1), ("n_distinct_colors", 8),
    ("grid_h", True), ("grid_h", False), ("grid_h", 10.0), ("grid_h", "10"),
    ("grid_w", True), ("grid_w", 11.0), ("grid_w", "11"),
    ("n_distinct_colors", True), ("n_distinct_colors", 3.0),
    ("n_distinct_colors", "3"),
    ("palette_size", 7), ("palette_kind", "warm"), ("texture", "no_blobs"),
    ("position_bias", "varied"), ("anchor_corner", True), ("asymmetry_force", True),
    ("unknown_axis", 2),
])
def test_invalid_and_removed_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("key", ["grid_h", "grid_w", "n_distinct_colors"])
def test_none_controls_follow_the_shared_no_override_convention(key):
    # GenCtx.draw_int_strict explicitly reserves None for an omitted override.
    for index in (0, 1):
        assert gen.generate(19, index, difficulty="easy", **{key: None}) == gen.generate(
            19, index, difficulty="easy")


@pytest.mark.parametrize("grid", [
    None, False, 2, "00", [], [[]], [None], [[0], [0, 0]],
    [[0, True], [0, 1]], [[0, 1.0], [0, 2]], [[0, "1"], [0, 2]],
    [[0, -1], [0, 2]], [[0, 10], [0, 2]],
])
def test_malformed_grid_is_rejected_without_crashing(grid):
    original = deepcopy(grid)
    reasons = gen.self_check(grid)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) for reason in reasons)
    assert grid == original


@pytest.mark.parametrize("invalid", [True, False, 8.0, "8", None, -1, 10])
def test_invalid_color_types_are_rejected_in_otherwise_legal_geometry(invalid):
    grid = rectangle_grid([(8, 1, 4, 1, 3), (3, 1, 1, 7, 9), (6, 6, 8, 2, 4)])
    grid = [[invalid if value == 8 else value for value in row] for row in grid]
    assert gen.self_check(grid), repr(invalid)


@pytest.mark.parametrize("mutation", ["hole", "touching", "reused_color", "one_blob", "empty", "full"])
def test_validator_rejects_material_domain_violations(mutation):
    grid = rectangle_grid([(8, 1, 4, 1, 3), (3, 1, 1, 7, 9), (6, 6, 8, 2, 4)])
    if mutation == "hole":
        grid[2][2] = 0
    elif mutation == "touching":
        grid[5][4] = 2
    elif mutation == "reused_color":
        grid[10][12] = 8
    elif mutation == "one_blob":
        grid = [[value if value == 8 else 0 for value in row] for row in grid]
    elif mutation == "empty":
        grid = [[0] * 14 for _ in range(12)]
    else:
        grid = [[8] * 14 for _ in range(12)]
    assert probe.geometry_errors(grid)
    assert gen.self_check(grid)


def test_canonical_shortcut_declarations_are_actual_all_pair_fits():
    pairs = probe.get_canonical_pairs()
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert shortcuts, "declare the known canonical-fitting geometry shortcuts"
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert name in gen.SEMANTIC_RIVALS
    assert set(gen.SEMANTIC_RIVALS) <= set(gen.LESSON_COMPETITORS)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_teaching_draws_refute_every_rival(band):
    rivals = getattr(gen, "SEMANTIC_RIVALS", {})
    assert rivals, "teaching has no declared semantic rivals"
    for seed in (0, 6, 47):
        for index in (0, 2, 38):
            grid = gen.generate(seed, index, difficulty=band)
            assert gen.schedule_profile(seed, index, difficulty=band) == "teaching"
            assert_domain(grid)
            expected = probe.oracle(grid)
            assert {0, 1, 2, 3} <= {value for row in expected for value in row}
            for name, rival in rivals.items():
                before = deepcopy(grid)
                assert rival(grid) != expected, (band, seed, index, name)
                assert grid == before
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid) and witness_name in gen.WITNESS_RIVALS:
                    names = gen.WITNESS_RIVALS[witness_name]
                    if isinstance(names, str):
                        names = [names]
                    assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in names)


def test_original_seed_six_row_column_lesson_is_now_taught():
    pairs = []
    for index in (38, 39, 40, 41):
        grid = gen.generate(6, index, difficulty="medium")
        pairs.append({"input": grid, "output": probe.oracle(grid)})
    demo_values = {value for pair in pairs[:3] for row in pair["output"] for value in row}
    assert {1, 2} <= demo_values, {"demo_values": sorted(demo_values)}
    swapped = probe.INDEPENDENT_RIVALS["swap_codes"]
    assert not (all(swapped(pair["input"]) == pair["output"] for pair in pairs[:3]) and
                swapped(pairs[3]["input"]) != pairs[3]["output"])
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_equal_top_left_tiebreak_is_taught():
    pairs = []
    for index in range(4):
        grid = gen.generate(6, index, difficulty="easy")
        pairs.append({"input": grid, "output": probe.oracle(grid)})
    rival = probe.INDEPENDENT_RIVALS["top_tie_reverse"]
    fits_demos = all(rival(pair["input"]) == pair["output"] for pair in pairs[:3])
    changes_query = rival(pairs[3]["input"]) != pairs[3]["output"]
    assert not (fits_demos and changes_query), "easy seed6 indices0..3 do not teach the equal-top left tiebreak"
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_cyclic_starts_and_query_rotations_are_supported_by_actual_demos():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 2
    report = probe.audit(module=gen, seeds=(0, 6, 17), samples_per_seed=12)
    assert report["covers_all_declared_starts"]
    assert report["window_count"] == 18 and report["rotation_count"] == 72
    assert report["contract_errors"] == []
    assert report["failures"] == [], report["failures"][:2]
    for name in report["declared_rivals"]:
        assert report["rivals"][name]["production"]["refuted"] == 18, name
        assert report["rivals"][name]["rotations"]["refuted"] == 72, name


def test_two_object_sorting_equivalence_is_not_reported_as_ambiguity():
    for second in ((2, 1, 1, 7, 8), (2, 6, 7, 1, 2), (2, 6, 7, 7, 8)):
        grid = rectangle_grid([(8, 1, 2, 1, 2), second])
        pair = {"input": grid, "output": probe.oracle(grid)}
        assert gen.self_check(grid) == []
        for order in ("bottom", "center", "left", "color"):
            assert probe.oracle(grid, order=order) == pair["output"]
        assert gen.lesson_identifiable([deepcopy(pair) for _ in range(3)], deepcopy(pair)) == []


def test_lesson_hook_rejects_a_real_unseen_row_column_branch_without_mutation():
    demos = []
    for offset in range(3):
        grid = rectangle_grid([(8, 1, 2, 1, 2), (3, 6 + offset, 6 + offset, 8, 9)])
        demos.append({"input": grid, "output": probe.oracle(grid)})
    query_grid = rectangle_grid([(8, 1, 2, 1, 2), (3, 1, 2, 8, 9)])
    query = {"input": query_grid, "output": probe.oracle(query_grid)}
    before = deepcopy((demos, query))
    reasons = gen.lesson_identifiable(demos, query)
    assert isinstance(reasons, list) and reasons
    assert (demos, query) == before


def test_default_sampling_retains_canonical_profiles_and_variety_in_each_band():
    report = probe.audit(module=gen, seeds=(19,), samples_per_seed=48)
    assert report["status"] == "no_ambiguity_found", report["failures"][:1]
    for band, facts in report["per_band"].items():
        assert facts["unique_inputs"] >= 45, (band, facts)
        assert facts["shape_count"] >= 3, (band, facts)
        assert len(facts["object_counts"]) >= 3, (band, facts)
        assert facts["canonical_profile_hits"] > 0, (band, facts)
        assert facts["dimension_four_hits"] > 0, (band, facts)


def test_probe_uses_actual_declarations_and_retains_complete_bindings():
    report = probe.audit(module=gen, seeds=(17,), bands=("easy",), samples_per_seed=0)
    assert report["draw_count"] == 5
    assert report["window_count"] == 2 and report["rotation_count"] == 8
    assert report["declared_rivals"] == sorted(probe.declared_rivals(gen))
    assert {item["sample_index"] for item in report["draw_bindings"]} == set(range(5))
    assert all(len(item["input_sha256"]) == 64 for item in report["draw_bindings"])
    assert report["canonical_pairs"] == len(probe.get_canonical_pairs())
