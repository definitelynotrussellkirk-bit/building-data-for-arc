from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "a44e3443619f"
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
def generator():
    return _load("a44_base_generator", HOME / "generator.py")


@pytest.fixture(scope="module")
def proto():
    return _load("a44_parametric_prototype", PARAMETRIC / "prototype.py")


def _canonical_row() -> dict:
    for line in canonical_path(REPO).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def _x_centers(grid: list[list[int]], *, corner_color: int = 2) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    return {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and all(
            grid[r + dr][c + dc] == corner_color
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        )
    }


def _apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_base_canonical_pairs_and_exact_program_are_preserved(generator):
    row = _canonical_row()
    assert generator.rule_program() == row["program_solution"]
    for pair in [*row["train"], *row["test"]]:
        original = copy.deepcopy(pair["input"])
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_base_generation_constructs_exactly_the_declared_two_or_three_x_patterns(generator):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(96):
            grid = generator.generate(seed, seed % 7, difficulty=difficulty)
            centers = _x_centers(grid)
            assert len(centers) in {2, 3}, (difficulty, seed, centers)
            assert generator.self_check(grid) == []
    for count in (2, 3):
        for seed in range(24):
            grid = generator.generate(seed, 3, difficulty="medium", n_quads=count)
            assert len(_x_centers(grid)) == count
    for invalid in (1, 4, True, 2.0):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(1, 0, n_quads=invalid)


def test_default_parametric_program_is_byte_exact_canonical(proto):
    assert proto.DEFAULT == {"completion_depth": "single"}
    assert proto.program(proto.DEFAULT) == _canonical_row()["program_solution"]
    assert {s["completion_depth"] for s in proto.SETTINGS} == {"single", "cascade"}
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_cascade_is_a_real_second_pass_over_the_stage_one_grid(proto):
    grid = proto.make_control_scene(
        13,
        13,
        complete=[(0, 0), (8, 8)],
        incomplete=[(0, 8)],
        standalone=[(9, 1)],
        nuisance=[(6, 6)],
    )
    stage_one = proto.stage_one(grid)
    final = proto.stage_two(stage_one)
    analysis = proto.analyze_scene(grid)
    assert analysis["stage_one_centers"] == 4 * 2 + 3 + 1
    assert analysis["cascade_targets"] == 2
    assert proto.transform(grid, {"completion_depth": "single"}) == stage_one
    assert proto.transform(grid, {"completion_depth": "cascade"}) == final
    assert final != stage_one
    assert proto.stage_two(grid) == grid  # skipping A cannot create the green targets
    assert sum(cell == 3 for row in final for cell in row) == 2


def test_generation_is_deterministic_count_independent_and_settings_independent(proto):
    for seed in (0, 1, 17, 91):
        single_short = proto.generate(seed, {"completion_depth": "single"}, 2, 4)
        single_long = proto.generate(seed, {"completion_depth": "single"}, 6, 4)
        cascade = proto.generate(seed, {"completion_depth": "cascade"}, 2, 4)
        assert single_short == proto.generate(seed, {"completion_depth": "single"}, 2, 4)
        assert single_short["train"] == single_long["train"][:2]
        assert single_short["test"] == single_long["test"]
        assert [p["input"] for p in single_short["train"] + single_short["test"]] == [
            p["input"] for p in cascade["train"] + cascade["test"]
        ]
        assert len(single_short["train"]) == 2
        assert len(single_short["test"]) == 4
        assert len({proto.digest(p["input"]) for p in single_short["train"] + single_short["test"]}) == 6
        assert single_short["certificate"]["survivors"] == [{"completion_depth": "single"}]
        assert cascade["certificate"]["survivors"] == [{"completion_depth": "cascade"}]
        assert single_short["certificate"]["shortcut_survivors"] == []
        assert cascade["certificate"]["shortcut_survivors"] == []


def test_every_minimum_lesson_has_multiple_causal_targets_and_near_misses(proto):
    for seed in range(64):
        for setting in proto.SETTINGS:
            episode = proto.generate(seed, setting, 2, 4)
            train_analysis = [proto.analyze_scene(pair["input"]) for pair in episode["train"]]
            assert all(row["cascade_targets"] >= 1 for row in train_analysis)
            assert any(row["cascade_targets"] >= 2 for row in train_analysis)
            assert any(row["incomplete_motifs"] >= 1 for row in train_analysis)
            assert any(row["standalone_x"] >= 1 for row in train_analysis)
            # Demos alone must eliminate every declared wrong shortcut before queries are read.
            for name, disagreements in episode["certificate"]["shortcut_disagreements"].items():
                assert disagreements, (seed, setting, name)


def test_query_bank_includes_boundary_thin_axis_swap_and_substantive_30x30(proto):
    episode = proto.generate(31, {"completion_depth": "cascade"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[0][0] < shapes[0][1]
    assert shapes[1][0] > shapes[1][1]
    assert shapes[-1] == (30, 30)
    grid = episode["test"][-1]["input"]
    analysis = proto.analyze_scene(grid)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert analysis["cascade_targets"] >= 8
    assert analysis["incomplete_motifs"] >= 4
    assert analysis["standalone_x"] >= 2
    assert len(occupied) >= 100
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29


def test_crossed_controls_change_intermediate_not_dimensions_and_change_nuisance_not_targets(proto):
    controls = proto.crossed_controls()
    different_intermediate = controls["different_intermediate_same_profile"]
    assert {tuple(map(len, [case["input"], case["input"][0]])) for case in different_intermediate} == {(13, 13)}
    assert len({case["analysis"]["cascade_targets"] for case in different_intermediate}) == 2
    same_targets = controls["same_targets_different_nuisance"]
    assert len({tuple(case["analysis"]["target_cells"]) for case in same_targets}) == 1
    assert same_targets[0]["input"] != same_targets[1]["input"]
    assert same_targets[0]["analysis"]["cascade_targets"] == same_targets[1]["analysis"]["cascade_targets"]


def test_strict_contract_rejects_malformed_settings_counts_grids_and_certificates(proto):
    for settings in ({}, {"completion_depth": "double"}, {"completion_depth": 2},
                     {"completion_depth": "single", "extra": 1}):
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

    episode = proto.generate(9, {"completion_depth": "cascade"}, 2, 4)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)
    forged = copy.deepcopy(episode)
    forged["test"][0]["output"] = copy.deepcopy(forged["test"][1]["output"])
    with pytest.raises(ValueError, match="query label"):
        proto.certify(forged)


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
                    assert _apply_racket(bridge, program, pair["input"]) == proto.transform(pair["input"], setting)
    finally:
        bridge.close()


def test_adapter_contract_and_counterfactual_are_complete(proto):
    adapter = _load("a44_parametric_adapter", PARAMETRIC / "adapter.py")
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["default"] == proto.DEFAULT
    assert promotion["parameters"] == {"completion_depth": ["single", "cascade"]}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert promotion["qualification_demos"] == 2
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)
    counterfactual = (PARAMETRIC / "skip_stage_one.rkt").read_text(encoding="utf-8")
    bridge = RacketBridge()
    try:
        witness = proto.generate(3, {"completion_depth": "cascade"}, 2, 4)["test"][0]
        actual = _apply_racket(bridge, proto.program({"completion_depth": "cascade"}), witness["input"])
        skipped = _apply_racket(bridge, counterfactual, witness["input"])
        assert actual == witness["output"]
        assert skipped != actual
    finally:
        bridge.close()


def test_adversarial_audit_tool_covers_declared_surfaces():
    audit = _load("a44_adversarial_audit", PARAMETRIC / "adversarial_audit.py")
    report = audit.run_audit(seeds=range(4), demo_counts=(2, 6), use_racket=False)
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 4 * 2 * 2
    assert report["pairs_checked"] == report["episodes_checked"] * (4 + (2 + 6) / 2)
    assert report["crossed_controls"]["different_intermediate_same_profile"]
    assert report["crossed_controls"]["same_targets_different_nuisance"]
    assert report["negative_certificate_checks"] >= 4
    assert report["max_shape"] == [30, 30]
