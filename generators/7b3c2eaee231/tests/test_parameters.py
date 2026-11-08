"""Behavioral tests for the proposed packing-rule family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "7b3c2eaee231"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The assigned runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("packing_parametric_test_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


@pytest.fixture(scope="module")
def racket():
    bridge = RacketBridge()
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True

    def apply(source, grid):
        wrapped = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped} {literal})")

    try:
        yield apply
    finally:
        bridge.close()


def canonical_program():
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_runnable_prototype_exists():
    load_prototype()


def test_default_program_is_exact_canonical_bytes(p):
    source = p.program({"packing_rule": "canonical"})
    assert source == canonical_program()
    assert hashlib.sha256(source.encode()).hexdigest() == p.CANONICAL_PROGRAM_SHA256


def test_tallest_color_controls_axis_and_racket_matches_python(p, racket):
    even = p.sample_input(9, "manual", 0, height=14, width=18, control_parity="even")
    odd = p.sample_input(9, "manual", 1, height=14, width=18, control_parity="odd")
    setting = {"packing_rule": "tallest_color_axis"}

    assert p.control_color(even) % 2 == 0
    assert p.control_color(odd) % 2 == 1
    even_output = p.transform(even, setting)
    odd_output = p.transform(odd, setting)
    assert len(even_output) < len(even_output[0])  # horizontal pack
    assert len(odd_output) > len(odd_output[0])    # vertical pack
    assert racket(p.program(setting), even) == even_output
    assert racket(p.program(setting), odd) == odd_output


def test_minimum_demos_teach_both_control_branches_and_identify_setting(p, racket):
    for rule in ("canonical", "tallest_color_axis"):
        episode = p.generate(17, {"packing_rule": rule}, 2, 4)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert {p.control_color(pair["input"]) % 2 for pair in episode["train"]} == {0, 1}
        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
        assert len({repr(grid) for grid in inputs}) == 6
        chosen = p.program({"packing_rule": rule})
        rival = p.program({"packing_rule": "canonical" if rule != "canonical" else "tallest_color_axis"})
        assert all(racket(chosen, pair["input"]) == pair["output"] for pair in episode["train"])
        assert any(racket(rival, pair["input"]) != pair["output"] for pair in episode["train"])
        assert all(racket(chosen, pair["input"]) == pair["output"] for pair in episode["test"])


def test_inputs_are_setting_independent_and_first_query_is_count_independent(p):
    canonical = p.generate(23, {"packing_rule": "canonical"}, 3, 4)
    composed = p.generate(23, {"packing_rule": "tallest_color_axis"}, 3, 4)
    one = p.generate(23, {"packing_rule": "canonical"}, 3, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in canonical[split]] == [x["input"] for x in composed[split]]
    assert canonical["train"] != composed["train"]
    assert canonical["train"] == one["train"]
    assert canonical["test"][0] == one["test"][0]


def test_30_square_stress_has_large_distributed_objects_and_exact_labels(p, racket):
    grid = p.sample_input(31, "stress", 3, height=30, width=30, control_parity="odd")
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert sum(cell != 0 for row in grid for cell in row) >= 65
    third_counts = [
        sum(grid[r][c] != 0 for r in range(30) for c in range(left, right))
        for left, right in ((0, 10), (10, 20), (20, 30))
    ]
    assert min(third_counts) >= 15
    for rule in ("canonical", "tallest_color_axis"):
        settings = {"packing_rule": rule}
        assert racket(p.program(settings), grid) == p.transform(grid, settings)


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"packing_rule": "canonical"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"packing_rule": "wrong"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"packing_rule": "canonical", "extra": 1}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"packing_rule": "canonical"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"packing_rule": "canonical"}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"packing_rule": "canonical"}, "demos": 2, "queries": 0},
        {"seed": 0, "settings": {"packing_rule": "canonical"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    with pytest.raises(ValueError):
        p.generate(**case)


def test_native_adapter_uses_adjacent_implementation(p):
    spec = importlib.util.spec_from_file_location(
        "packing_native_adapter_test", HOME / "workspace/parametric/adapter.py"
    )
    adapter = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(adapter)
    settings = {"packing_rule": "tallest_color_axis"}
    assert adapter.program(settings) == p.program(settings)
    assert adapter.generate(6, deepcopy(settings), 2, 4) == p.generate(6, settings, 2, 4)


def test_wrong_intermediate_counterfactual_changes_final_output(p, racket):
    grid = p.sample_input(41, "causal", 0, height=18, width=21, control_parity="even")
    intended = p.program({"packing_rule": "tallest_color_axis"})
    counterfactual_path = HOME / "workspace/parametric/rules/wrong_intermediate.rkt"
    assert counterfactual_path.is_file()
    counterfactual = counterfactual_path.read_text(encoding="utf-8")
    assert racket(intended, grid) == p.transform(grid, {"packing_rule": "tallest_color_axis"})
    assert racket(counterfactual, grid) != racket(intended, grid)
