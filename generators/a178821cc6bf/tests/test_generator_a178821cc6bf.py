from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve()
TASK_ID = "a178821cc6bf"

# The authoritative file lives under generators/<id>/tests.  During the review
# battery this test is copied to runtime-root/tests.  Support both placements so
# the focused test can also be run directly while editing the packet.
if (HERE.parent.parent / "generator.py").is_file():
    REPO = HERE.parents[3]
    RUNTIME_ROOT = REPO / "shared" / "runtime"
    GENERATOR_PATH = HERE.parent.parent / "generator.py"
else:
    REPO = HERE.parents[1]
    RUNTIME_ROOT = REPO
    GENERATOR_PATH = REPO / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"

sys.path.insert(0, str(RUNTIME_ROOT))
from puzzle_generators import base  # noqa: E402

spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", GENERATOR_PATH)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def canonical_row() -> dict:
    path = (
        REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
        if (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file()
        else REPO / "data" / "canonical" / "puzzles.jsonl"
    )
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def facts(grid):
    return generator.semantic_observables(grid)


def test_every_canonical_pair_is_accepted_exact_and_input_pure():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == "ff2f0d5fbd0c"
    assert generator.RULE_HASH == "ff2f0d5fbd0c"

    pairs = row["train"] + row["test"]
    assert len(pairs) == 6
    for pair in pairs:
        before = [line[:] for line in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_use_true_geometry_and_teach_all_four_states(band):
    inputs = set()
    outputs = set()
    both_zero_counts = set()
    relations = set()
    for seed in range(160):
        grid = generator.generate(100_000 + seed, seed * 17 + 3, difficulty=band)
        assert generator.self_check(grid) == []
        assert all(len(row) == 8 for row in grid)
        observed = facts(grid)
        assert all(observed["state_counts"][state] >= 1 for state in ("00", "10", "01", "11"))
        assert 4 not in {value for row in grid for value in row}
        both_zero_counts.add(observed["state_counts"]["00"])
        relations.add(observed["color_relation"])
        inputs.add(frozen(grid))
        outputs.add(frozen(generator.rule_mirror(grid)))
    assert relations == {"same", "different"}
    assert len(both_zero_counts) >= 4
    assert len(inputs) >= 150
    assert len(outputs) >= 100


def test_two_consecutive_examples_refute_raw_value_equality_shortcut():
    for start in range(20):
        demos = []
        relations = []
        for sample_index in (start, start + 1):
            grid = generator.generate(808, sample_index, difficulty="medium")
            relations.append(facts(grid)["color_relation"])
            demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        query_grid = generator.generate(808, start + 2, difficulty="medium")
        query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
        assert set(relations) == {"same", "different"}
        assert generator.lesson_identifiable(demos, query) == []
        same_demo = next(pair for pair in demos if facts(pair["input"])["color_relation"] == "same")
        assert generator.raw_value_equality(same_demo["input"]) != same_demo["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_override_boundaries_are_exact_and_observable(band):
    cases = [
        {"grid_h": 3, "left_color": 1, "right_color": 1, "both_zero_count": 1, "layout": "random"},
        {"grid_h": 18, "left_color": 9, "right_color": 2, "both_zero_count": 8, "layout": "checker"},
        {"grid_h": 4, "left_color": 6, "right_color": 5, "both_zero_count": 5, "layout": "cluster"},
    ]
    for index, kwargs in enumerate(cases):
        grid = generator.generate(7 + index, 19 + index, difficulty=band, **kwargs)
        assert generator.self_check(grid) == []
        observed = generator.observe_overrides(grid)
        for key, expected in kwargs.items():
            assert observed[key] == expected


def test_default_draw_provenance_matches_returned_grid():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(seed, seed * 31 + 1, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            drawn = captured[0].recorded_draws()
            observed = generator.observe_overrides(grid)
            for axis in generator.AXES:
                assert drawn[axis] == observed[axis]


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(12345)
    before_state = random.getstate()
    first = generator.generate(77, 91, difficulty="hard")
    after_state = random.getstate()
    second = generator.generate(77, 91, difficulty="hard")
    assert before_state == after_state
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 99
    assert second[0][0] != 99


def test_self_check_rejects_targeted_structural_and_semantic_impostors():
    source = generator.generate(42, 5, difficulty="medium")

    bad_width = [row + [0] for row in source]
    assert any("width" in error for error in generator.self_check(bad_width))

    answer_leak = [row[:] for row in source]
    answer_leak[0][0] = 4
    assert any("color 4" in error for error in generator.self_check(answer_leak))

    no_both_zero = [row[:] for row in source]
    left_color = facts(source)["left_color"]
    for row in no_both_zero:
        for col in range(4):
            if row[col] == 0 and row[col + 4] == 0:
                row[col] = left_color
    assert any("00" in error or "both-zero" in error for error in generator.self_check(no_both_zero))

    no_left_only = [row[:] for row in source]
    right_color = facts(source)["right_color"]
    for row in no_left_only:
        for col in range(4):
            if row[col] != 0 and row[col + 4] == 0:
                row[col + 4] = right_color
    assert any("10" in error or "left-only" in error for error in generator.self_check(no_left_only))


def test_degenerate_negative_controls_are_rejected_but_oracle_executes():
    for name in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(8, 13, difficulty="medium", texture=name)
        assert generator.self_check(grid)
        output = generator.rule_mirror(grid)
        assert len(output) == len(grid)
        assert all(len(row) == 4 for row in output)


def test_conflicting_out_of_range_or_unknown_overrides_reject_loudly():
    bad = [
        {"left_color": 0},
        {"right_color": 4},
        {"grid_h": 2},
        {"grid_h": 19},
        {"both_zero_count": 0},
        {"both_zero_count": 9},
        {"layout": "unknown"},
        {"bogus": 1},
        {"texture": "same_occupancy", "layout": "random"},
    ]
    for kwargs in bad:
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 0, **kwargs)


def test_every_difficulty_band_has_regular_canonical_profile_anchors():
    for band in ("easy", "medium", "hard"):
        for start in range(0, 16, 4):
            window = [
                generator.generate(5150, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert any(
                len(grid) == 4
                and facts(grid)["color_relation"] == "different"
                and len({value for row in grid for value in row}) == 3
                for grid in window
            )


def test_color_axis_metadata_machine_declares_answer_color_exclusion():
    for axis in ("left_color", "right_color"):
        assert generator.AXES[axis]["valid"] == "1..9 (≠4)"
