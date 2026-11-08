"""Focused contracts for the vertical-flip/cue-axis parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root

TASK_ID = "a6294f07bff6"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
MODES = ("canonical_ud", "cue_axis")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _family():
    return _load("a6294f07bff6_family_tests", PARAMETRIC / "family.py")


def _adapter():
    return _load("a6294f07bff6_adapter_tests", PARAMETRIC / "adapter.py")


def _generator():
    return _load("a6294f07bff6_generator_tests", HOME / "generator.py")


def _canonical_program() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    programs = {
        record["program_solution"]
        for record in catalog._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_ordinary_generator_still_produces_visible_asymmetric_flips():
    generator = _generator()
    for difficulty in (None, "medium"):
        for seed in (0, 17, 91):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            assert grid != grid[::-1]
            assert any(row != row[::-1] for row in grid)


def test_contract_and_default_program_are_exact():
    adapter = _adapter()
    expected = {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"flip_rule": list(MODES)},
        "default": {"flip_rule": "canonical_ud"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/cue_axis.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit.py",
            f"generators/{TASK_ID}/workspace/parametric/README.md",
        ],
    }
    assert json.loads((PARAMETRIC / "promotion.json").read_text()) == expected
    canonical = _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    assert adapter.program({"flip_rule": "canonical_ud"}) == canonical
    assert adapter.program({"flip_rule": "cue_axis"}) != canonical


def test_literal_fixture_defines_cue_axis_dependency():
    family = _family()
    grid = [
        [1, 2, 3, 4],
        [9, 0, 5, 6],
        [7, 8, 1, 2],
    ]
    assert family.dependency_intermediate(grid) == {"cue": [1, 0], "axis": "lr"}
    assert family.solve(grid, "canonical_ud") == grid[::-1]
    assert family.solve(grid, "cue_axis") == [row[::-1] for row in grid]
    assert family.solve(grid, "canonical_ud") != family.solve(grid, "cue_axis")


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_match_settings_and_prefixes_are_stable(seed):
    adapter = _adapter()
    full = {
        mode: adapter.generate(seed, {"flip_rule": mode}, demos=6, queries=4)
        for mode in MODES
    }
    assert _inputs(full[MODES[0]]) == _inputs(full[MODES[1]])
    assert len({json.dumps(grid) for grid in _inputs(full[MODES[0]])}) == 10
    for mode, baseline in full.items():
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(seed, {"flip_rule": mode}, demos=demos, queries=queries)
                assert episode["train"] == baseline["train"][:demos]
                assert episode["test"] == baseline["test"][:queries]
                assert episode["program_solution"] == adapter.program({"flip_rule": mode})


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("mode", MODES)
def test_first_two_demos_identify_setting_and_refute_declared_rivals(seed, mode):
    family = _family()
    episode = family.generate(seed, {"flip_rule": mode}, demos=2, queries=4)
    survivors = [
        candidate for candidate in MODES
        if all(family.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    assert survivors == [mode]
    for name in family.RIVALS:
        assert any(family.rival_output(pair["input"], name) != pair["output"] for pair in episode["train"]), name
        assert any(family.rival_output(pair["input"], name) != pair["output"] for pair in episode["test"]), name


def test_fourth_query_is_substantive_30x30_with_boundary_content():
    family = _family()
    episode = family.generate(20261025, {"flip_rule": "cue_axis"}, demos=3, queries=4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(occupied) >= 600
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29
    assert pair["output"] != grid


def test_wrong_axis_intermediate_changes_final_output():
    family = _family()
    grid = family.input_bank(89)[0][0]
    case = family.causal_case(grid)
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["axis"] != case["intermediate_value"]["wrong_axis"]
    assert case["output"] != case["counterfactual_output"]


@pytest.mark.parametrize("bad", [None, {}, [], {"flip_rule": True}, {"flip_rule": "bad"}, {"flip_rule": "canonical_ud", "x": 1}])
def test_invalid_settings_reject(bad):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, demos=3, queries=4)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 3, True), (0, 3, 0), (0, 3, 5),
])
def test_invalid_request_controls_reject(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"flip_rule": "canonical_ud"}, demos=demos, queries=queries)


def test_public_projection_ignores_private_fields_and_query_answers():
    family = _family()
    episode = family.generate(77, {"flip_rule": "cue_axis"}, demos=3, queries=4)
    public = family.public_turn(episode, 2)
    assert public == {"train": episode["train"], "test": [{"input": episode["test"][2]["input"]}]}
    altered = copy.deepcopy(episode)
    altered["program_solution"] = "private"
    altered["settings"] = {"flip_rule": "canonical_ud"}
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert family.public_turn(altered, 2) == public
    assert family.public_id(altered, 2) == family.public_id(episode, 2)


def test_protected_racket_matches_python_and_counterfactual():
    family = _family()
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for mode in MODES:
            episode = family.generate(17, {"flip_rule": mode}, demos=2, queries=1)
            program = family.program({"flip_rule": mode})
            for pair in episode["train"] + episode["test"]:
                assert _execute(bridge, program, pair["input"]) == pair["output"]
        case = family.causal_case(family.input_bank(17)[0][0])
        assert _execute(bridge, case["program"], case["input"]) == case["output"]
        assert _execute(bridge, case["counterfactual_program"], case["input"]) == case["counterfactual_output"]
        assert case["output"] != case["counterfactual_output"]
