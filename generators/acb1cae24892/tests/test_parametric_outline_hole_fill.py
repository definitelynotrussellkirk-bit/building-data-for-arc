"""Native promotion regressions for outline construction then hole filling."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK = "acb1cae24892"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"
MODES = ("outline_only", "fill_largest_hole")


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
    return load("acb_parametric_prototype", "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("acb_parametric_adapter", "adapter.py")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=128) as runtime:
        yield runtime


def test_contract_and_exact_default(adapter):
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"finish_mode": list(MODES)}
    assert contract["default"] == {"finish_mode": "outline_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program({"finish_mode": "outline_only"}) == canonical_program()


@pytest.mark.parametrize("seed", [0, 17])
def test_matched_inputs_two_demos_identify_rule(seed, prototype, adapter):
    episodes = {mode: adapter.generate(seed, {"finish_mode": mode}, 2, 4) for mode in MODES}
    inputs = {mode: [p["input"] for p in episodes[mode]["train"] + episodes[mode]["test"]] for mode in MODES}
    assert inputs[MODES[0]] == inputs[MODES[1]]
    assert len({json.dumps(g) for g in inputs[MODES[0]]}) == 6
    for mode in MODES:
        report = prototype.assess_demos(episodes[mode]["train"], mode)
        assert report["setting_survivors"] == [mode]
        assert report["harmful_shortcut_survivors"] == []


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_count_boundaries_prefix_stability(prototype, demos, queries):
    episode = prototype.generate_episode(8, "fill_largest_hole", demos, queries)
    full = prototype.generate_episode(8, "fill_largest_hole", 6, 4)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]


def test_fourth_query_is_30x30_with_large_topological_intermediate(prototype):
    grid = prototype.select_inputs(13, 3, 4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    canonical = prototype.output_for(grid, "outline_only")
    assert sum(v != 0 for row in canonical for v in row) >= 140
    info = prototype.analyze_input(grid)
    assert info["largest_hole_size"] > 250
    assert info["largest_hole_size"] != info["smallest_hole_size"]


def test_smallest_hole_counterfactual_changes_output(prototype):
    grid = prototype.select_inputs(21, 2, 4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] != case["counterfactual_output"]
    assert case["intermediate_value"]["largest_hole_size"] != case["intermediate_value"]["smallest_hole_size"]


@pytest.mark.parametrize("mode", MODES)
def test_racket_matches_claims(mode, prototype, bridge):
    episode = prototype.generate_episode(29, mode, 2, 4)
    program = prototype.program_for(mode)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.output_for(pair["input"], mode)
        assert execute(bridge, program, pair["input"]) == pair["output"]


def test_racket_executes_counterfactual(prototype, bridge):
    grid = prototype.select_inputs(33, 2, 4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert execute(bridge, case["program"], grid) == case["output"]
    assert execute(bridge, case["counterfactual_program"], grid) == case["counterfactual_output"]


def test_public_turn_is_private_and_count_independent(prototype):
    full = prototype.generate_episode(7, "fill_largest_hole", 3, 4)
    one = prototype.generate_episode(7, "fill_largest_hole", 3, 1)
    assert prototype.public_turn(full, 0) == prototype.public_turn(one, 0)
    assert set(prototype.public_turn(full, 0)["test"][0]) == {"input"}


@pytest.mark.parametrize("settings", [None, {}, {"finish_mode": "bad"}, {"finish_mode": "outline_only", "x": 1}])
def test_bad_settings_reject(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)

def test_preflight_compat_normalizes_only_single_pair_object_shape():
    path = HOME / "preflight_compat.py"
    spec = importlib.util.spec_from_file_location("acb_preflight_compat", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    pair = {"input": [[0]], "output": [[0]]}
    assert module.pair_list(pair) == [pair]
    assert module.pair_list([pair]) == [pair]
    with pytest.raises(ValueError, match="list or one pair object"):
        module.pair_list("bad")

