"""Behavioral tests for the proposed orientation-controlled motif family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "74e83caa0660"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The assigned runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("orientation_parametric_test_subject", PROTOTYPE)
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
    source = p.program({"completion_rule": "canonical_x"})
    assert source == canonical_program()
    assert hashlib.sha256(source.encode()).hexdigest() == p.CANONICAL_PROGRAM_SHA256


def test_orientation_controls_x_or_plus_and_racket_matches_python(p, racket):
    grid = p.sample_input(9, "manual", 0, height=12, width=15, pair_count=4)
    orientations = {pair["orientation"] for pair in p.pairs(grid)}
    assert orientations == {"main", "anti"}

    canonical = {"completion_rule": "canonical_x"}
    composed = {"completion_rule": "orientation_selects_motif"}
    canonical_out = p.transform(grid, canonical)
    composed_out = p.transform(grid, composed)
    assert canonical_out != composed_out
    assert racket(p.program(canonical), grid) == canonical_out
    assert racket(p.program(composed), grid) == composed_out

    for pair in p.pairs(grid):
        color = pair["color"]
        top, left = pair["top"], pair["left"]
        cells = {
            (r, c)
            for r in range(top, top + 3)
            for c in range(left, left + 3)
            if composed_out[r][c] == color
        }
        expected_x = {
            (top, left), (top, left + 2), (top + 1, left + 1),
            (top + 2, left), (top + 2, left + 2),
        }
        expected_plus = {
            (top, left + 1), (top + 1, left), (top + 1, left + 1),
            (top + 1, left + 2), (top + 2, left + 1),
        }
        assert cells == (expected_x if pair["orientation"] == "main" else expected_plus)


def test_minimum_demos_identify_setting_and_reject_always_plus(p, racket):
    always_plus = (PARAMETRIC / "rules/always_plus.rkt").read_text(encoding="utf-8")
    for rule in ("canonical_x", "orientation_selects_motif"):
        episode = p.generate(17, {"completion_rule": rule}, 2, 4)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert all(
            {pair["orientation"] for pair in p.pairs(item["input"])} == {"main", "anti"}
            for item in episode["train"]
        )
        all_inputs = [item["input"] for split in ("train", "test") for item in episode[split]]
        assert len({repr(grid) for grid in all_inputs}) == 6
        chosen = p.program({"completion_rule": rule})
        rival_name = "canonical_x" if rule != "canonical_x" else "orientation_selects_motif"
        rival = p.program({"completion_rule": rival_name})
        assert all(racket(chosen, item["input"]) == item["output"] for item in episode["train"])
        assert any(racket(rival, item["input"]) != item["output"] for item in episode["train"])
        assert any(racket(always_plus, item["input"]) != item["output"] for item in episode["train"])
        assert all(racket(chosen, item["input"]) == item["output"] for item in episode["test"])


def test_inputs_are_setting_independent_and_query_prefix_stable(p):
    canonical = p.generate(23, {"completion_rule": "canonical_x"}, 3, 4)
    composed = p.generate(23, {"completion_rule": "orientation_selects_motif"}, 3, 4)
    for split in ("train", "test"):
        assert [item["input"] for item in canonical[split]] == [item["input"] for item in composed[split]]
    assert canonical["train"] != composed["train"]
    for queries in range(1, 5):
        prefix = p.generate(23, {"completion_rule": "orientation_selects_motif"}, 3, queries)
        assert prefix["train"] == composed["train"]
        assert prefix["test"] == composed["test"][:queries]


def test_30_square_stress_is_populated_distributed_and_exact(p, racket):
    grid = p.sample_input(31, "stress", 3, height=30, width=30, pair_count=8)
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert len(p.pairs(grid)) == 8
    occupied_quadrants = {
        (pair["top"] // 15, pair["left"] // 15)
        for pair in p.pairs(grid)
    }
    assert occupied_quadrants == {(0, 0), (0, 1), (1, 0), (1, 1)}
    for rule in ("canonical_x", "orientation_selects_motif"):
        settings = {"completion_rule": rule}
        assert racket(p.program(settings), grid) == p.transform(grid, settings)


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"completion_rule": "canonical_x"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"completion_rule": "wrong"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"completion_rule": "canonical_x", "extra": 1}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"completion_rule": "canonical_x"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"completion_rule": "canonical_x"}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"completion_rule": "canonical_x"}, "demos": 2, "queries": 0},
        {"seed": 0, "settings": {"completion_rule": "canonical_x"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    with pytest.raises(ValueError):
        p.generate(**case)


def test_native_adapter_uses_adjacent_implementation(p):
    adapter_path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("orientation_native_adapter_test", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(adapter)
    settings = {"completion_rule": "orientation_selects_motif"}
    assert adapter.program(settings) == p.program(settings)
    assert adapter.generate(6, deepcopy(settings), 2, 4) == p.generate(6, settings, 2, 4)


def test_wrong_intermediate_counterfactual_changes_final_output(p, racket):
    grid = p.sample_input(41, "causal", 0, height=15, width=18, pair_count=5)
    intended = p.program({"completion_rule": "orientation_selects_motif"})
    counterfactual_path = PARAMETRIC / "rules/wrong_intermediate.rkt"
    assert counterfactual_path.is_file()
    counterfactual = counterfactual_path.read_text(encoding="utf-8")
    assert racket(intended, grid) == p.transform(grid, {"completion_rule": "orientation_selects_motif"})
    assert racket(counterfactual, grid) != racket(intended, grid)
