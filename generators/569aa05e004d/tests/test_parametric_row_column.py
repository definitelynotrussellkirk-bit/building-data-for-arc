"""Parametric row-then-column closure tests for 569aa05e004d."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "569aa05e004d"
REPO = find_root(__file__)
HOME = REPO / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("row_column_parametric", PARAMETRIC / "prototype.py")


def _canonical_row() -> dict:
    for line in canonical_path(REPO).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def _apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_default_program_is_byte_exact_canonical(proto):
    assert proto.DEFAULT == {"closure_axis": "rows_only"}
    assert proto.program(proto.DEFAULT) == _canonical_row()["program_solution"]
    assert {setting["closure_axis"] for setting in proto.SETTINGS} == {
        "rows_only",
        "rows_then_columns",
    }
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_rows_then_columns_is_a_real_second_stage(proto):
    grid = proto.make_control_scene(
        13,
        17,
        bridges=[
            {"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))},
        ],
        triples=[
            {"color": 3, "rows": (7, 9, 11), "spans": ((5, 14), (3, 12), (5, 10))},
        ],
        blockers=[(1, 6, 8)],
    )
    first = proto.stage_rows(grid)
    final = proto.stage_columns(first)
    analysis = proto.analyze_scene(grid)
    assert analysis["row_relations"] == 5
    assert analysis["column_relations"] >= 2
    assert analysis["triple_blocked_columns"] >= 1
    assert analysis["stage_b_changed_cells"] > 0
    assert proto.transform(grid, {"closure_axis": "rows_only"}) == first
    assert proto.transform(grid, {"closure_axis": "rows_then_columns"}) == final
    assert final != first
    assert proto.stage_columns(grid) != final  # skipping A consumes the wrong state


def test_column_stage_fills_background_without_overwriting_stage_a_bars(proto):
    intermediate = [[2], [3], [0], [2]]
    assert proto.stage_columns(intermediate) == [[2], [3], [2], [2]]


def test_generation_is_deterministic_count_and_setting_independent(proto):
    for seed in (0, 1, 17, 91):
        rows_short = proto.generate(seed, {"closure_axis": "rows_only"}, 2, 4)
        rows_long = proto.generate(seed, {"closure_axis": "rows_only"}, 6, 4)
        closed = proto.generate(seed, {"closure_axis": "rows_then_columns"}, 2, 4)
        assert rows_short == proto.generate(seed, {"closure_axis": "rows_only"}, 2, 4)
        assert rows_short["train"] == rows_long["train"][:2]
        assert rows_short["test"] == rows_long["test"]
        assert [pair["input"] for pair in rows_short["train"] + rows_short["test"]] == [
            pair["input"] for pair in closed["train"] + closed["test"]
        ]
        assert len(rows_short["train"]) == 2
        assert len(rows_short["test"]) == 4
        assert len({proto.digest(pair["input"]) for pair in rows_short["train"] + rows_short["test"]}) == 6
        assert rows_short["certificate"]["survivors"] == [{"closure_axis": "rows_only"}]
        assert closed["certificate"]["survivors"] == [{"closure_axis": "rows_then_columns"}]
        assert rows_short["certificate"]["shortcut_survivors"] == []
        assert closed["certificate"]["shortcut_survivors"] == []


def test_every_minimum_lesson_breaks_declared_shortcuts(proto):
    for seed in range(64):
        for setting in proto.SETTINGS:
            episode = proto.generate(seed, setting, 2, 4)
            analyses = [proto.analyze_scene(pair["input"]) for pair in episode["train"]]
            assert all(row["stage_b_changed_cells"] > 0 for row in analyses)
            assert any(row["triple_blocked_columns"] > 0 for row in analyses)
            assert any(row["erased_control_cells"] > 0 for row in analyses)
            for name, disagreements in episode["certificate"]["shortcut_disagreements"].items():
                assert disagreements, (seed, setting, name)


def test_query_bank_covers_thin_boundary_and_substantive_30x30(proto):
    episode = proto.generate(31, {"closure_axis": "rows_then_columns"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[0][0] < shapes[0][1]
    assert shapes[1][0] > shapes[1][1]
    assert shapes[-1] == (30, 30)
    grid = episode["test"][-1]["input"]
    analysis = proto.analyze_scene(grid)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert analysis["row_relations"] >= 12
    assert analysis["column_relations"] >= 20
    assert analysis["stage_b_changed_cells"] >= 80
    assert len(occupied) >= 30
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29


def test_crossed_controls_vary_intermediate_and_nuisance_independently(proto):
    controls = proto.crossed_controls()
    varying = controls["different_intermediate_same_profile"]
    assert {tuple(case["analysis"]["shape"]) for case in varying} == {(13, 17)}
    assert len({case["analysis"]["stage_b_changed_cells"] for case in varying}) > 1
    nuisance = controls["same_intermediate_different_raw_nuisance"]
    assert nuisance[0]["input"] != nuisance[1]["input"]
    assert nuisance[0]["intermediate"] == nuisance[1]["intermediate"]
    assert nuisance[0]["output"] == nuisance[1]["output"]


def test_strict_contract_rejects_bad_settings_counts_grids_and_certificates(proto):
    for settings in ({}, {"closure_axis": "columns"}, {"closure_axis": 2},
                     {"closure_axis": "rows_only", "extra": 1}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (("seed", True), ("seed", 1.0), ("demos", 1), ("demos", 7),
                       ("demos", True), ("queries", 3), ("queries", 5), ("queries", True)):
        kwargs = {"seed": 1, "settings": proto.DEFAULT, "demos": 2, "queries": 4}
        kwargs[key] = value
        with pytest.raises((TypeError, ValueError)):
            proto.generate(**kwargs)
    for bad_grid in ([], [[]], [[0], [0, 0]], [[True]], [[10]], "grid"):
        with pytest.raises((TypeError, ValueError)):
            proto.transform(bad_grid, proto.DEFAULT)

    episode = proto.generate(9, {"closure_axis": "rows_then_columns"}, 2, 4)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)
    forged = copy.deepcopy(episode)
    forged["test"][0]["output"] = copy.deepcopy(forged["test"][1]["output"])
    with pytest.raises(ValueError, match="query label"):
        proto.certify(forged)
    stale = copy.deepcopy(episode)
    stale["program_solution"] = "(rule! g)"
    with pytest.raises(ValueError, match="program_solution"):
        proto.certify(stale)


def test_python_mirror_matches_protected_racket_for_both_settings(proto):
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for seed in (0, 17):
            episode = proto.generate(seed, proto.DEFAULT, 2, 4)
            for setting in proto.SETTINGS:
                program = proto.program(setting)
                for pair in episode["train"] + episode["test"]:
                    assert _apply_racket(bridge, program, pair["input"]) == proto.transform(
                        pair["input"], setting
                    )
    finally:
        bridge.close()


def test_adapter_contract_and_skip_stage_a_counterfactual(proto):
    adapter = _load("row_column_adapter", PARAMETRIC / "adapter.py")
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == proto.DEFAULT
    assert promotion["parameters"] == {
        "closure_axis": ["rows_only", "rows_then_columns"]
    }
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert promotion["qualification_demos"] == 2
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)

    counterfactual = (PARAMETRIC / "skip_stage_rows.rkt").read_text(encoding="utf-8")
    bridge = RacketBridge()
    try:
        witness = proto.generate(3, {"closure_axis": "rows_then_columns"}, 2, 4)["test"][0]
        actual = _apply_racket(bridge, proto.program({"closure_axis": "rows_then_columns"}), witness["input"])
        skipped = _apply_racket(bridge, counterfactual, witness["input"])
        assert actual == witness["output"]
        assert skipped != actual
    finally:
        bridge.close()


def test_adversarial_audit_tool_covers_declared_surfaces():
    audit = _load("row_column_audit", PARAMETRIC / "adversarial_audit.py")
    report = audit.run_audit(seeds=range(4), demo_counts=(2, 6), use_racket=False)
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 4 * 2 * 2
    assert report["crossed_controls"]["different_intermediate_same_profile"]
    assert report["crossed_controls"]["same_intermediate_different_raw_nuisance"]
    assert report["negative_certificate_checks"] >= 5
    assert report["foreground_preservation_checks"] == report["pairs_checked"]
    assert report["max_shape"] == [30, 30]
    assert report["shortcut_failures"] == {}
