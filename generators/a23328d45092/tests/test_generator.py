"""Base-generator regression and teaching tests for a23328d45092."""
from __future__ import annotations

from copy import deepcopy
import json
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "a23328d45092"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generator_a23328d45092", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK, root=find_root(__file__))


def test_python_mirror_matches_every_original_label_and_validator_owns_inputs():
    for pair in _pairs():
        assert GEN.self_check(deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(deepcopy(pair["input"])) == pair["output"]


def test_three_role_schedule_repeats_all_priority_witnesses():
    assert GEN.SCHEDULE_PROFILES == ("tl_over_tr", "tr_over_bl", "bl_over_br")
    for start in range(12):
        assert {
            GEN.schedule_profile(0, start + offset, None)
            for offset in range(3)
        } == set(GEN.SCHEDULE_PROFILES)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_three_demo_window_refutes_all_noncanonical_priority_orders(difficulty):
    for start in range(9):
        demos = []
        for offset in range(3):
            grid = GEN.generate(700 + start, start + offset, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.surviving_priority_rivals(demos) == []


@pytest.mark.parametrize("difficulty,expected", [("easy", (7, 7)), (None, (9, 9)), ("medium", (9, 9)), ("hard", (13, 13))])
def test_default_dimensions_are_stable_within_difficulty(difficulty, expected):
    assert {
        (len(GEN.generate(99, index, difficulty=difficulty)), len(GEN.generate(99, index, difficulty=difficulty)[0]))
        for index in range(9)
    } == {expected}


@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", 1.0), ("sample_index", True), ("sample_index", -1),
    ("difficulty", "invalid"),
])
def test_invalid_scalar_calls_fail_closed(argument, value):
    args = {"seed": 1, "sample_index": 0, "difficulty": None}
    args[argument] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(args["seed"], args["sample_index"], difficulty=args["difficulty"])


def test_declared_overrides_are_realized_and_unknown_axes_rejected():
    grid = GEN.generate(
        3, 1, difficulty="easy", grid_h=11, grid_w=13,
        palette_kind="broad", quadrant_density="dense",
        sep_position="off_center", include_overlap=False, anchor_corner=True,
    )
    assert (len(grid), len(grid[0])) == (11, 13)
    assert GEN.self_check(grid) == []
    with pytest.raises(KeyError):
        GEN.generate(1, 0, typo_axis=1)


def test_bounded_base_teaching_audit_emits_receipt(tmp_path):
    audit_path = HOME / "workspace/parametric/audit_base_teaching.py"
    assert audit_path.is_file(), "base teaching audit tool has not been implemented"
    spec = importlib.util.spec_from_file_location("base_teaching_audit_a23328d45092", audit_path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    receipt = audit.run_audit(2)
    assert receipt["status"] == "passed"
    assert receipt["seed_count"] == 2
    assert receipt["ambiguous_windows"] == 0
    assert receipt["window_count"] == 96
    out = tmp_path / "base-audit.json"
    audit.write_receipt(receipt, out)
    assert json.loads(out.read_text()) == receipt


def test_role_witness_survives_empty_quadrant_repair():
    demos = []
    for sample_index in range(7, 10):
        grid = GEN.generate(110, sample_index, difficulty="easy")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.surviving_priority_rivals(demos) == []
