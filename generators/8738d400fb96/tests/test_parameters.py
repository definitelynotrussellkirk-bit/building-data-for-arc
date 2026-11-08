"""Native promotion checks for the translated-footprint relay family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "8738d400fb96"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
MODES = ("translate_only", "translated_cue_relay")


def _load(name: str, path: Path):
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_8738d400fb96", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_adapter_8738d400fb96", ADAPTER_PATH)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=128) as runtime:
        yield runtime


def test_contract_declares_bounded_family():
    assert json.loads(PROMOTION_PATH.read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"finish_rule": list(MODES)},
        "default": {"finish_rule": "translate_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/translated_cue_relay.rkt",
        ],
    }


def test_default_program_is_exact_canonical(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program_for("translate_only") == canonical
    assert adapter.program({"finish_rule": "translate_only"}) == canonical
    alternate = adapter.program({"finish_rule": "translated_cue_relay"})
    assert alternate != canonical
    assert "cue-colors" in alternate
    assert "relay-cells" in alternate


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_are_matched_distinct_and_two_demos_identify_setting(prototype, adapter, seed):
    episodes = {
        mode: adapter.generate(seed, {"finish_rule": mode}, 2, 4)
        for mode in MODES
    }
    inputs = {
        mode: [pair["input"] for pair in episodes[mode]["train"] + episodes[mode]["test"]]
        for mode in MODES
    }
    assert inputs[MODES[0]] == inputs[MODES[1]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs[MODES[0]]}) == 6
    for chosen in MODES:
        report = prototype.assess_demos(episodes[chosen]["train"], chosen)
        assert report["setting_survivors"] == [chosen]
        assert report["harmful_shortcut_survivors"] == []


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_supported_count_boundaries(prototype, demos, queries):
    episode = prototype.generate_episode(41, "translated_cue_relay", demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert len({json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]}) == demos + queries


def test_demo_and_query_prefixes_are_count_independent(prototype):
    short = prototype.select_inputs(73, demos=2, queries=1)
    long = prototype.select_inputs(73, demos=6, queries=4)
    assert [x["input"] for x in short["train"]] == [x["input"] for x in long["train"][:2]]
    assert short["test"][0]["input"] == long["test"][0]["input"]


def test_four_queries_include_substantive_30x30_and_boundary_case(prototype):
    selected = prototype.select_inputs(53, demos=3, queries=4)
    grid = selected["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29
    assert len(occupied) >= 80
    info = prototype.analyze_input(grid)
    assert info["retained_moved_cells"] >= 4
    assert len(info["relay_cells"]) >= 8


def test_wrong_intermediate_changes_relay_output(prototype):
    grid = prototype.select_inputs(89, demos=2, queries=4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] != case["counterfactual_output"]
    assert case["intermediate_value"]["cue_color"] != case["intermediate_value"]["wrong_cue_color"]


@pytest.mark.parametrize("bad", [None, {}, {"finish_rule": "bad"}, {"finish_rule": "translate_only", "x": 1}])
def test_adapter_rejects_bad_settings(adapter, bad):
    with pytest.raises(ValueError):
        adapter.program(bad)


@pytest.mark.parametrize("mode", MODES)
def test_racket_matches_python_mirror_and_identifies_setting(prototype, bridge, mode):
    episode = prototype.generate_episode(67, mode, 2, 4)
    programs = {candidate: prototype.program_for(candidate) for candidate in MODES}
    survivors = []
    for candidate, program in programs.items():
        if all(_execute(bridge, program, pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(candidate)
    assert survivors == [mode]
    for pair in episode["train"] + episode["test"]:
        assert _execute(bridge, programs[mode], pair["input"]) == pair["output"]
        assert pair["output"] == prototype.output_for(pair["input"], mode)


def test_racket_executes_causal_counterfactual(prototype, bridge):
    grid = prototype.select_inputs(97, demos=2, queries=4)["train"][0]["input"]
    case = prototype.causal_case(grid)
    assert _execute(bridge, case["program"], grid) == case["output"]
    assert _execute(bridge, case["counterfactual_program"], grid) == case["counterfactual_output"]
    assert case["output"] != case["counterfactual_output"]
