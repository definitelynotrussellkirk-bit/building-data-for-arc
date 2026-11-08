"""Native promotion regressions for the parity-key payload relay family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK = "a89702404b3c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
MODES = ("corner_crop", "corner_key_payload")


def load(name, filename):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def canonical_program():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    values = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
    assert len(values) == 1
    return values.pop()


@pytest.fixture(scope="module")
def prototype():
    return load("a897_parametric_prototype", "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("a897_parametric_adapter", "adapter.py")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=128) as runtime:
        yield runtime


def test_contract_and_exact_default(adapter):
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"rule_mode": list(MODES)}
    assert contract["default"] == {"rule_mode": "corner_crop"}
    assert contract["limits"] == {"demos": [3, 6], "queries": [1, 4]}
    assert adapter.program({"rule_mode": "corner_crop"}) == canonical_program()
    assert adapter.program({"rule_mode": "corner_key_payload"}) != canonical_program()


@pytest.mark.parametrize("seed", [0, 17])
def test_matched_inputs_three_demos_identify_rule_and_four_queries(seed, prototype, adapter):
    episodes = {mode: adapter.generate(seed, {"rule_mode": mode}, 3, 4) for mode in MODES}
    inputs = {mode: [p["input"] for p in episodes[mode]["train"] + episodes[mode]["test"]] for mode in MODES}
    assert inputs[MODES[0]] == inputs[MODES[1]]
    assert len({json.dumps(grid) for grid in inputs[MODES[0]]}) == 7
    for mode in MODES:
        report = prototype.assess_demos(episodes[mode]["train"], mode)
        assert report["setting_survivors"] == [mode]
        assert report["harmful_shortcut_survivors"] == []


@pytest.mark.parametrize("demos", [3, 4, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_count_boundaries_and_prefix_stability(prototype, demos, queries):
    episode = prototype.generate_episode(23, "corner_key_payload", demos, queries)
    assert len(episode["train"]) == demos and len(episode["test"]) == queries
    full = prototype.generate_episode(23, "corner_key_payload", 6, 4)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]


def test_fourth_query_is_substantive_30x30(prototype):
    grid = prototype.select_inputs(5, 3, 4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    assert len(occupied) > 700
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}


def test_wrong_key_counterfactual_changes_output(prototype):
    grid = prototype.select_inputs(9, 3, 4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["selected_key"] != case["intermediate_value"]["wrong_key"]
    assert case["output"] != case["counterfactual_output"]


@pytest.mark.parametrize("mode", MODES)
def test_racket_matches_claims(mode, prototype, bridge):
    episode = prototype.generate_episode(31, mode, 3, 4)
    program = prototype.program_for(mode)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.output_for(pair["input"], mode)
        assert execute(bridge, program, pair["input"]) == pair["output"]


def test_racket_executes_counterfactual(prototype, bridge):
    grid = prototype.select_inputs(11, 3, 4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert execute(bridge, case["program"], grid) == case["output"]
    assert execute(bridge, case["counterfactual_program"], grid) == case["counterfactual_output"]


def test_public_turn_hides_private_fields_and_first_turn_is_count_independent(prototype):
    full = prototype.generate_episode(41, "corner_key_payload", 3, 4)
    one = prototype.generate_episode(41, "corner_key_payload", 3, 1)
    assert prototype.public_turn(full, 0) == prototype.public_turn(one, 0)
    public = prototype.public_turn(full, 0)
    assert set(public) == {"train", "test"}
    assert set(public["test"][0]) == {"input"}
    assert "program" not in json.dumps(public).lower()


@pytest.mark.parametrize("settings", [None, {}, {"rule_mode": "bad"}, {"rule_mode": "corner_crop", "x": 1}])
def test_bad_settings_reject(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
