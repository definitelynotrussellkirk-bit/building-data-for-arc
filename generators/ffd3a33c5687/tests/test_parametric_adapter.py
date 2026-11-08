from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/ffd3a33c5687/workspace/parametric"
TASK_ID = "ffd3a33c5687"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("test_ffd3_parametric_adapter", HOME / "adapter.py")


def _centers(width: int) -> tuple[int, int]:
    return (width - 1) // 2, width // 2


def _guide_side(grid: list[list[int]]) -> str:
    width = len(grid[0])
    center_left, center_right = _centers(width)
    rows = [
        row_index
        for row_index, row in enumerate(grid)
        if row[center_left] == 8 and row[center_right] == 8
    ]
    assert len(rows) == 1
    row = grid[rows[0]]
    left = [value for value in row[:center_left] if value != 0]
    right = [value for value in row[center_right + 1 :] if value != 0]
    assert (len(left), len(right)) in {(1, 0), (0, 1)}
    return "left" if left else "right"


def _priority_output(grid: list[list[int]], side: str) -> list[list[int]]:
    assert side in {"left", "right"}
    output = deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            preferred, fallback = (left, right) if side == "left" else (right, left)
            color = preferred if preferred != 0 else fallback
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def _guide_output(grid: list[list[int]]) -> list[list[int]]:
    return _priority_output(grid, _guide_side(grid))


def _orbit_types(grid: list[list[int]]) -> dict[str, int]:
    width = len(grid[0])
    counts = {"singletons": 0, "pairs": 0, "conflicts": 0}
    for row in grid:
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if (left == 0) != (right == 0):
                counts["singletons"] += 1
            elif left != 0 and left == right:
                counts["pairs"] += 1
            elif left != 0 and right != 0 and left != right:
                counts["conflicts"] += 1
    return counts


def _racket_apply(program: str, grid: list[list[int]]) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge(max_calls_before_restart=32) as bridge:
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_default_program_is_exact_canonical_and_contract_is_strict(adapter):
    """Catch canonical drift, setting fallback, and unsupported count coercion."""
    from arcpuzzles import Catalog

    programs = {
        row["program_solution"]
        for row in Catalog(REPO)._variants()[TASK_ID]
        if isinstance(row.get("program_solution"), str)
    }
    assert programs == {adapter.program({"conflict_policy": "left_priority"})}
    assert adapter.program({"conflict_policy": "guide_priority"}) not in programs

    for settings in ({}, None, {"conflict_policy": "unknown"}, {"conflict_policy": "left_priority", "extra": 1}):
        with pytest.raises(ValueError, match="conflict_policy|settings"):
            adapter.program(settings)
    for name, value in (("seed", True), ("seed", -1), ("demos", 1), ("demos", 7), ("queries", 3), ("queries", 5)):
        call = {"seed": 0, "settings": {"conflict_policy": "left_priority"}, "demos": 3, "queries": 4}
        call[name] = value
        with pytest.raises(ValueError, match=name):
            adapter.generate(**call)


def test_counts_are_independent_inputs_are_distinct_and_stress_is_substantive(adapter):
    """Catch hard-coded lesson size, duplicate examples, and padded 30x30 stress."""
    for demos in (2, 3, 6):
        episode = adapter.generate(73, {"conflict_policy": "left_priority"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(fingerprints) == len(set(fingerprints))
        assert {_guide_side(pair["input"]) for pair in episode["train"]} == {"left", "right"}

        stress = episode["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        foreground = {(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value != 0}
        assert any(r == 0 for r, _ in foreground)
        assert any(r == 29 for r, _ in foreground)
        assert any(c == 0 for _, c in foreground)
        assert any(c == 29 for _, c in foreground)
        types = _orbit_types(stress)
        assert types["conflicts"] >= 8
        assert types["singletons"] >= 5
        assert len(foreground) >= 30


def test_settings_share_inputs_and_guide_side_causally_controls_conflicts(adapter):
    """Catch setting-dependent sampling and a guide marker unused by the labeler."""
    canonical = adapter.generate(101, {"conflict_policy": "left_priority"}, 3, 4)
    guided = adapter.generate(101, {"conflict_policy": "guide_priority"}, 3, 4)
    canonical_pairs = canonical["train"] + canonical["test"]
    guided_pairs = guided["train"] + guided["test"]
    assert [pair["input"] for pair in canonical_pairs] == [pair["input"] for pair in guided_pairs]

    differences_by_side = {"left": 0, "right": 0}
    for canonical_pair, guided_pair in zip(canonical_pairs, guided_pairs):
        grid = canonical_pair["input"]
        side = _guide_side(grid)
        assert canonical_pair["output"] == _priority_output(grid, "left")
        assert guided_pair["output"] == _guide_output(grid)
        if canonical_pair["output"] != guided_pair["output"]:
            differences_by_side[side] += 1
    assert differences_by_side["left"] == 0
    assert differences_by_side["right"] > 0


def test_both_programs_execute_in_racket_on_small_and_30x30_cases(adapter):
    """Catch a Python-only alternate, invalid Racket, or boundary-only mismatch."""
    episode = adapter.generate(17, {"conflict_policy": "guide_priority"}, 2, 4)
    grids = [episode["train"][0]["input"], episode["test"][-1]["input"]]
    for grid in grids:
        assert _racket_apply(adapter.program({"conflict_policy": "left_priority"}), grid) == _priority_output(grid, "left")
        assert _racket_apply(adapter.program({"conflict_policy": "guide_priority"}), grid) == _guide_output(grid)


def test_finite_teaching_audit_refutes_rivals_and_checks_first_turn_projection(adapter):
    """Catch demo-fitting shortcut rules and public leakage of private/future data."""
    audit = _load("test_ffd3_parametric_audit", HOME / "audit.py")
    report = audit.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6))
    assert report["schema"] == "arcpuzzles-parametric-teaching-audit-v1"
    assert report["status"] == "passed"
    assert report["ambiguous_cases"] == []
    assert report["episodes_checked"] == 12
    assert report["query_rotations_checked"] == 48
    assert report["projection"]["settings_visible"] is False
    assert report["projection"]["program_visible"] is False
    assert report["projection"]["query_outputs_visible"] is False
    assert report["projection"]["future_queries_visible_on_first_turn"] is False
