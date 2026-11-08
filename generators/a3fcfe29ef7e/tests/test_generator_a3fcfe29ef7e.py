from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


HERE = Path(__file__).resolve()
TASK_ID = "a3fcfe29ef7e"
ROOT = find_root(__file__)

# Support both the editable packet layout and the isolated task-test runtime
# without assuming a fixed source depth.
editable_generator = ROOT / "generators" / TASK_ID / "generator.py"
if editable_generator.is_file():
    GENERATOR_PATH = editable_generator
    RUNTIME_ROOT = ROOT / "shared" / "runtime"
else:
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    RUNTIME_ROOT = ROOT

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from puzzle_generators import base  # noqa: E402

spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", GENERATOR_PATH)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def pair(grid):
    return {"input": grid, "output": generator.rule_mirror(grid)}


def facts(grid):
    return generator.semantic_observables(grid)


def test_rule_pin_and_every_canonical_pair_are_exact_accepted_and_input_pure():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == "f7f19079511e"
    assert generator.RULE_HASH == "f7f19079511e"
    assert generator.VERSION == "3.0.0"

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    for item in pairs:
        before = copy.deepcopy(item["input"])
        assert generator.self_check(item["input"]) == []
        assert generator.strict_canonical_like(item["input"]) == []
        assert generator.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_lawful_truth_table_complete_diverse_and_observable(band):
    inputs = set()
    outputs = set()
    counts = set()
    relations = set()
    for index in range(96):
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(100_000 + index, index * 17 + 3, difficulty=band)
        finally:
            base.set_ctx_observer(None)
        assert len(captured) == 1
        assert generator.self_check(grid) == []
        assert all(len(row) == 7 for row in grid)
        observed = facts(grid)
        assert all(observed["state_counts"][state] >= 1 for state in ("00", "10", "01", "11"))
        assert 3 not in {value for row in grid for value in row}
        assert captured[0].recorded_draws() == generator.observe_overrides(grid)
        counts.add(observed["state_counts"]["00"])
        relations.add(observed["color_relation"])
        inputs.add(frozen(grid))
        outputs.add(frozen(generator.rule_mirror(grid)))
    assert relations == {"same", "different"}
    assert len(counts) >= (3 if band == "easy" else 4)
    assert len(inputs) >= 90
    assert len(outputs) >= 60


def test_schedule_and_every_query_rotation_refute_raw_value_equality():
    assert generator.EXAMPLES_NEEDED == 4
    assert generator.LESSON_SCHEDULE_PERIOD == 2
    assert generator.SCHEDULE_PROFILES == ("different", "same")
    for band in ("easy", "medium", "hard"):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            grids = [generator.generate(808, start + offset, difficulty=band) for offset in range(5)]
            relations = [facts(grid)["color_relation"] for grid in grids]
            assert "same" in relations[:4]
            assert "different" in relations[:4]
            labelled = [pair(grid) for grid in grids]
            for query_index in range(len(labelled)):
                demos = [item for index, item in enumerate(labelled) if index != query_index]
                assert generator.lesson_identifiable(demos, labelled[query_index]) == []
            same_grid = next(grid for grid in grids if facts(grid)["color_relation"] == "same")
            assert generator.raw_value_equality(same_grid) != generator.rule_mirror(same_grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_axis_boundaries_are_honored_and_observable_in_every_band(band):
    cases = [
        {
            "grid_h": 3,
            "left_color": 1,
            "right_color": 1,
            "sep_color": 2,
            "both_zero_count": 1,
            "layout": "random",
        },
        {
            "grid_h": 18,
            "left_color": 9,
            "right_color": 2,
            "sep_color": 8,
            "both_zero_count": 6,
            "layout": "checker",
        },
        {
            "grid_h": 4,
            "left_color": 6,
            "right_color": 5,
            "sep_color": 1,
            "both_zero_count": 5,
            "layout": "cluster",
        },
    ]
    for index, expected in enumerate(cases):
        grid = generator.generate(901 + index, 77 + index, difficulty=band, **expected)
        assert generator.self_check(grid) == []
        assert generator.observe_overrides(grid) == expected


def test_replay_is_deterministic_fresh_and_global_rng_is_untouched():
    random.seed(123456)
    state = random.getstate()
    first = generator.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99


def test_legacy_aliases_map_to_exact_observable_controls():
    grid = generator.generate(
        72,
        11,
        difficulty="medium",
        fg_color=6,
        sep_color=2,
        both_zero_target=2,
        panel_pattern="checker",
    )
    observed = generator.observe_overrides(grid)
    assert observed["left_color"] == 6
    assert observed["right_color"] == 6
    assert observed["sep_color"] == 2
    assert observed["both_zero_count"] == 2
    assert observed["layout"] == "checker"


def test_profile_anchors_cover_canonical_shape_and_palette_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(0, 16, 4):
            window = [generator.generate(5150, start + offset, difficulty=band) for offset in range(4)]
            assert any(
                len(grid) == 4
                and facts(grid)["color_relation"] == "different"
                and len({value for row in grid for value in row}) == 4
                for grid in window
            )


def test_self_check_rejects_structural_palette_and_truth_table_impostors():
    source = generator.generate(42, 5, difficulty="medium")
    observed = facts(source)

    bad_width = [row + [0] for row in source]
    assert any("width" in error for error in generator.self_check(bad_width))

    answer_leak = copy.deepcopy(source)
    answer_leak[0][0] = 3
    assert any("answer color 3" in error for error in generator.self_check(answer_leak))

    varying_separator = copy.deepcopy(source)
    varying_separator[0][3] = 9 if observed["sep_color"] != 9 else 8
    assert any("separator" in error for error in generator.self_check(varying_separator))

    separator_collision = copy.deepcopy(source)
    for row in separator_collision:
        row[3] = observed["left_color"]
    assert any("separator" in error and "differ" in error for error in generator.self_check(separator_collision))

    no_both_zero = copy.deepcopy(source)
    for row in no_both_zero:
        for col in range(3):
            if row[col] == 0 and row[col + 4] == 0:
                row[col] = observed["left_color"]
    assert any("00" in error or "both-zero" in error for error in generator.self_check(no_both_zero))

    no_left_only = copy.deepcopy(source)
    for row in no_left_only:
        for col in range(3):
            if row[col] != 0 and row[col + 4] == 0:
                row[col + 4] = observed["right_color"]
    assert any("10" in error or "left-only" in error for error in generator.self_check(no_left_only))

    no_right_only = copy.deepcopy(source)
    for row in no_right_only:
        for col in range(3):
            if row[col] == 0 and row[col + 4] != 0:
                row[col] = observed["left_color"]
    assert any("01" in error or "right-only" in error for error in generator.self_check(no_right_only))

    no_both_nonzero = copy.deepcopy(source)
    for row in no_both_nonzero:
        for col in range(3):
            if row[col] != 0 and row[col + 4] != 0:
                row[col + 4] = 0
    assert any("11" in error or "both-nonzero" in error for error in generator.self_check(no_both_nonzero))


@pytest.mark.parametrize("texture", ["no_both_zero", "all_both_zero", "same_panels"])
def test_negative_fixtures_execute_the_rule_but_are_outside_the_teaching_grammar(texture):
    grid = generator.generate(812, 4, texture=texture, grid_h=5, left_color=6, right_color=5, sep_color=1)
    assert generator.self_check(grid)
    output = generator.rule_mirror(grid)
    assert len(output) == 5
    assert all(len(row) == 3 for row in output)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 2},
        {"grid_h": 19},
        {"left_color": 0},
        {"left_color": 3},
        {"right_color": 0},
        {"right_color": 3},
        {"sep_color": 0},
        {"sep_color": 3},
        {"both_zero_count": 0},
        {"both_zero_count": 7},
        {"layout": "not-a-layout"},
        {"bogus_axis": 1},
        {"texture": "not-a-texture"},
        {"texture": "checker", "layout": "border"},
        {"panel_pattern": "checker", "layout": "border"},
        {"both_zero_target": 2, "both_zero_count": 3},
        {"fg_color": 6, "left_color": 5},
        {"texture": "no_both_zero", "both_zero_count": 2},
    ],
)
def test_invalid_or_conflicting_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(2, 3, **kwargs)


def test_separator_color_collisions_report_precise_incompatible_axes():
    with pytest.raises(ValueError) as caught:
        generator.generate(2, 3, left_color=7, sep_color=7)
    assert set(caught.value.incompatible_axes) == {"left_color", "sep_color"}

    with pytest.raises(ValueError) as caught:
        generator.generate(2, 3, right_color=5, sep_color=5)
    assert set(caught.value.incompatible_axes) == {"right_color", "sep_color"}


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(2, 3, difficulty="extreme")


def test_declared_semantic_contract_is_live_on_every_normal_draw():
    assert set(generator.CANONICAL_SHORTCUTS) == {"raw_value_equality"}
    assert generator.LESSON_COMPETITORS == generator.SEMANTIC_RIVALS
    expected_rivals = {
        "constant_zero",
        "left_zero",
        "right_zero",
        "occupancy_equal",
        "occupancy_xor",
        "both_nonzero",
        "either_zero",
        "raw_value_equality",
    }
    assert set(generator.SEMANTIC_RIVALS) == expected_rivals

    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = generator.generate(20_000 + index, index, difficulty=band)
            official = generator.rule_mirror(grid)
            for name, rival in generator.SEMANTIC_RIVALS.items():
                if name == "raw_value_equality" and facts(grid)["color_relation"] == "different":
                    continue
                assert rival(grid) != official, (band, index, name)


def test_lesson_hook_rejects_too_few_or_incorrect_demos():
    grids = [generator.generate(44, index) for index in range(5)]
    labelled = [pair(grid) for grid in grids]
    assert generator.lesson_identifiable(labelled[:3], labelled[4])
    bad_demo = copy.deepcopy(labelled[0])
    bad_demo["output"] = [[0 for _ in row] for row in bad_demo["output"]]
    assert generator.lesson_identifiable([bad_demo] + labelled[1:4], labelled[4])


def test_color_axis_metadata_excludes_background_and_answer_color():
    for axis in ("left_color", "right_color", "sep_color"):
        assert generator.AXES[axis]["valid"] == "1..9 (≠3)"


def test_schedule_probe_tool_enumerates_every_declared_start_and_query_rotation():
    tool_path = HERE.parent.parent / "workspace" / "probe_schedule_contract.py"
    spec = importlib.util.spec_from_file_location("probe_schedule_contract", tool_path)
    assert spec and spec.loader
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    report = tool.probe(generator, seed=20261008)
    assert report["schema"] == "a3fcfe29ef7e-schedule-probe-v1"
    assert report["summary"] == {
        "bands": 3,
        "schedule_starts": 6,
        "query_rotations": 30,
        "invalid_pairs": 0,
        "ambiguous_rotations": 0,
    }
    assert report["failures"] == []


def test_retained_raw_value_equality_counterexample_is_executable():
    path = HERE.parent.parent / "counterexamples" / "raw-value-equality.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    grid = payload["input"]
    intended = generator.rule_mirror(grid)
    rival = generator.raw_value_equality(grid)

    assert payload["schema"] == "a3fcfe29ef7e-counterexample-v1"
    assert payload["task_id"] == TASK_ID
    assert generator.self_check(grid) == []
    assert facts(grid)["color_relation"] == "same"
    assert facts(grid)["state_counts"]["11"] >= 1
    assert intended == payload["intended_output"]
    assert rival == payload["rival_output"]
    assert intended != rival
