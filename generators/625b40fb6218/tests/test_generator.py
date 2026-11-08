"""Regression and semantic-contract tests for generator 625b40fb6218."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "625b40fb6218"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def split_halves(grid):
    height = len(grid)
    width = len(grid[0])
    separators = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected one full-height separator, found {separators}")
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError("separator must divide equal-width halves")
    left = [row[:separator] for row in grid]
    right = [row[separator + 1 :] for row in grid]
    return left, right


def conflict_right_colors(grid):
    """Favorite-color rivals differ precisely on unequal right-side colors."""
    left, right = split_halves(grid)
    return {b for lr, rr in zip(left, right) for a, b in zip(lr, rr)
            if a != 0 and b != 0 and a != b}


def independent_rule(grid):
    left, right = split_halves(grid)
    output = []
    for left_row, right_row in zip(left, right):
        out_row = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            else:
                out_row.append(left_value)
        output.append(out_row)
    return output


def equal_overlap_only_rival(grid):
    left, right = split_halves(grid)
    output = []
    for left_row, right_row in zip(left, right):
        out_row = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            elif left_value == right_value:
                out_row.append(left_value)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def right_priority_rival(grid):
    left, right = split_halves(grid)
    output = []
    for left_row, right_row in zip(left, right):
        out_row = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                out_row.append(2)
            elif left_value == 0 and right_value != 0:
                out_row.append(1)
            elif left_value != 0 and right_value != 0:
                out_row.append(right_value)
            else:
                out_row.append(0)
        output.append(out_row)
    return output


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "53f987296312"
    assert GEN.VERSION == "2.0.0"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert set(GEN.AXES) == {
        "grid_h",
        "half_w",
        "palette_size",
        "n_left_only",
        "n_right_only",
        "n_shared_equal",
        "n_shared_conflict",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 6,
            "half_w": 4,
            "palette_size": 2,
            "n_left_only": 1,
            "n_right_only": 1,
            "n_shared_equal": 3,
            "n_shared_conflict": 0,
        },
        {
            "grid_h": 10,
            "half_w": 10,
            "palette_size": 3,
            "n_left_only": 2,
            "n_right_only": 2,
            "n_shared_equal": 6,
            "n_shared_conflict": 2,
        },
        {
            "grid_h": 14,
            "half_w": 12,
            "palette_size": 5,
            "n_left_only": 4,
            "n_right_only": 4,
            "n_shared_equal": 8,
            "n_shared_conflict": 4,
        },
    ],
)
def test_exact_overrides_are_constructive_observable_and_band_independent(band, options):
    grid = GEN.generate(183, 7, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    assert independent_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 5},
        {"grid_h": 15},
        {"half_w": 3},
        {"half_w": 13},
        {"palette_size": 1},
        {"palette_size": 6},
        {"n_left_only": 0},
        {"n_left_only": 5},
        {"n_right_only": 0},
        {"n_right_only": 5},
        {"n_shared_equal": 2},
        {"n_shared_equal": 9},
        {"n_shared_conflict": -1},
        {"n_shared_conflict": 5},
        {"grid_h": True},
        {"half_w": 7.5},
        {"palette_size": "3"},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


def test_canonical_inputs_are_accepted_and_oracle_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) >= 4
    for item in pairs:
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]


def test_declared_shortcuts_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    expected = {
        "equal_overlap_only": equal_overlap_only_rival,
        "right_priority_overlap": right_priority_rival,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(expected)
    for name, shortcut in expected.items():
        assert all(shortcut(item["input"]) == item["output"] for item in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_teaches_all_rule_branches_and_varies_inputs(band):
    grids = [GEN.generate(2200 + index, index * 11, difficulty=band) for index in range(160)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all(item["n_left_only"] >= 1 for item in observed)
    assert all(item["n_right_only"] >= 1 for item in observed)
    assert all(item["n_shared_equal"] >= 3 for item in observed)
    assert all(item["n_shared_conflict"] >= 1 for item in observed)
    assert len({(item["grid_h"], item["half_w"]) for item in observed}) >= 5
    assert {item["palette_size"] for item in observed} >= {2, 3, 4, 5}
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 156


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_checked_rotation_refutes_original_rivals_and_checks_color_coverage(band):
    for start in range(10):
        lesson = [pair(GEN.generate(9100 + start, start + offset, difficulty=band)) for offset in range(5)]
        for query_index, query in enumerate(lesson):
            demos = [item for index, item in enumerate(lesson) if index != query_index]
            # The original sampler teaches the two original rivals. New color
            # rivals may survive, and must reject only when this query needs them.
            taught = set().union(*(conflict_right_colors(item["input"]) for item in demos))
            required = conflict_right_colors(query["input"]) - taught
            expected = {
                f"competing rule 'color_priority_{color}' fits every demo but changes the query answer"
                for color in required
            }
            assert set(GEN.lesson_identifiable(demos, query)) == expected
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_unequal_overlap_is_exact_counterexample_to_both_canonical_shortcuts():
    grid = GEN.generate(
        77,
        4,
        grid_h=10,
        half_w=10,
        palette_size=3,
        n_left_only=2,
        n_right_only=2,
        n_shared_equal=6,
        n_shared_conflict=2,
    )
    truth = independent_rule(grid)
    assert GEN.SEMANTIC_WITNESSES["unequal_overlap"](grid)
    assert GEN.SEMANTIC_RIVALS["equal_overlap_only"](grid) == equal_overlap_only_rival(grid)
    assert GEN.SEMANTIC_RIVALS["right_priority_overlap"](grid) == right_priority_rival(grid)
    assert GEN.SEMANTIC_RIVALS["equal_overlap_only"](grid) != truth
    assert GEN.SEMANTIC_RIVALS["right_priority_overlap"](grid) != truth


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(319, index, difficulty=band)
            second = GEN.generate(319, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_self_check_rejects_structural_and_palette_near_misses():
    good = GEN.generate(510, 3, grid_h=10, half_w=10, palette_size=3)
    assert GEN.self_check(good) == []

    missing_separator = deepcopy(good)
    missing_separator[0][10] = 0
    assert GEN.self_check(missing_separator)

    extra_five = deepcopy(good)
    extra_five[0][0] = 5
    assert GEN.self_check(extra_five)

    output_color_in_input = deepcopy(good)
    output_color_in_input[0][0] = 1
    assert GEN.self_check(output_color_in_input)

    ragged = deepcopy(good)
    ragged[0].pop()
    assert GEN.self_check(ragged)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_canonical_support_in_every_band(band):
    exact = 0
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (
            len(grid),
            len(grid[0]),
            len({value for row in grid for value in row}),
        )
        exact += profile in {(10, 21, 4), (10, 21, 5)}
    assert exact >= 1, (band, exact)


def test_reference_probe_replays_canonical_shortcuts_and_generated_witnesses(tmp_path):
    probe_path = HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(samples_per_band=8, lessons_per_band=4)
    assert report["canonical"]["oracle_mismatches"] == 0
    assert report["canonical"]["shortcut_fit_counts"] == {
        "equal_overlap_only": report["canonical"]["pairs"],
        "right_priority_overlap": report["canonical"]["pairs"],
    }
    assert report["generated"]["self_check_errors"] == 0
    assert report["generated"]["oracle_mismatches"] == 0
    assert report["generated"]["rival_agreements"] == {
        "equal_overlap_only": 0,
        "right_priority_overlap": 0,
    }
    # The strengthened hook exposes ordinary color-priority ambiguity;
    # independently count it instead of silently keeping a zero-failure claim.
    expected_failures = 0
    for band in ("easy", "medium", "hard"):
        for ordinal in range(4):
            seed = probe.pinned_seed("lesson", band, ordinal)
            grids = [GEN.generate(seed, ordinal * 13 + offset, difficulty=band)
                     for offset in range(5)]
            for query_index, grid in enumerate(grids):
                taught = set().union(*(conflict_right_colors(other)
                                       for index, other in enumerate(grids)
                                       if index != query_index))
                expected_failures += bool(conflict_right_colors(grid) - taught)
    assert expected_failures == 19
    assert report["lessons"]["rotation_failures"] == expected_failures
    assert all(not item["surviving_rivals"]
               for item in report["lessons"]["failure_examples"])


def test_retained_unequal_overlap_counterexample_is_live_and_minimal():
    import json

    path = HOME / "counterexamples" / "unequal-overlap-shortcuts.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    assert GEN.observe_overrides(grid) == record["observed"]
    assert independent_rule(grid) == record["intended_output"]
    assert equal_overlap_only_rival(grid) == record["rival_outputs"]["equal_overlap_only"]
    assert right_priority_rival(grid) == record["rival_outputs"]["right_priority_overlap"]
    assert record["intended_output"] != record["rival_outputs"]["equal_overlap_only"]
    assert record["intended_output"] != record["rival_outputs"]["right_priority_overlap"]
