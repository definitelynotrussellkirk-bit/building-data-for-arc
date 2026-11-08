"""Native promotion checks for the routed stencil-cascade parameter family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "fdffdd0bbde7"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
MODES = ("single_stage", "border_routed_cascade")


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
    return _load("parametric_fdffdd0bbde7", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_adapter_fdffdd0bbde7", ADAPTER_PATH)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=128) as runtime:
        yield runtime


def test_contract_declares_bounded_composition_family():
    assert PROMOTION_PATH.is_file(), "promotion contract must be created"
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"composition": list(MODES)},
        "default": {"composition": "single_stage"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


def test_default_program_is_exact_canonical_and_alternate_is_composed(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.canonical_program() == canonical
    assert prototype.rule_text("single_stage") == canonical
    assert adapter.program({"composition": "single_stage"}) == canonical
    alternate = prototype.rule_text("border_routed_cascade")
    assert alternate == adapter.program({"composition": "border_routed_cascade"})
    assert alternate != canonical
    assert "stage-a" in alternate
    assert "touches-border?" in alternate
    assert "route-index (if touches-border?" in alternate
    assert "(grow-centers stage-a (second routed))" in alternate


def test_episode_inputs_are_deterministic_matched_and_distinct(prototype, adapter):
    episodes = {
        mode: adapter.generate(17, {"composition": mode}, 3, 4)
        for mode in MODES
    }
    assert episodes["single_stage"] == adapter.generate(
        17, {"composition": "single_stage"}, 3, 4
    )
    left_inputs = [
        pair["input"] for split in ("train", "test") for pair in episodes[MODES[0]][split]
    ]
    right_inputs = [
        pair["input"] for split in ("train", "test") for pair in episodes[MODES[1]][split]
    ]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == 7
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(episodes[MODES[0]][split], episodes[MODES[1]][split])
    )
    for mode, episode in episodes.items():
        assert episode["program_solution"] == prototype.rule_text(mode)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.output_for(pair["input"], mode)


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_two_demonstrations_identify_each_mode_and_reject_declared_shortcuts(prototype, seed):
    selected = prototype.select_inputs(seed, demos=2, queries=4)
    for chosen in MODES:
        report = prototype.assess_demos(selected["train"], chosen)
        assert report["declared_setting_survivors"] == [chosen]
        assert report["shortcut_survivors"] == []
        assert report["demonstrations"] == 2


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_supported_count_boundaries(prototype, demos, queries):
    episode = prototype.generate_episode(
        41, composition="border_routed_cascade", demos=demos, queries=queries
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + queries


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"composition": "always_next"},
        {"composition": 1},
        {"demos": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"queries": 1.0},
    ],
)
def test_episode_rejects_invalid_boundaries(prototype, kwargs):
    call = {
        "seed": 0,
        "composition": "single_stage",
        "demos": 3,
        "queries": 4,
    }
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate_episode(**call)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"composition": "single_stage", "extra": 1},
        {"composition": "always_next"},
        None,
    ],
)
def test_adapter_rejects_unknown_or_missing_setting_keys(adapter, settings):
    with pytest.raises(ValueError, match="exactly composition|declared composition"):
        adapter.program(settings)


def test_query_stream_is_independent_of_demo_count_and_prefix_stable(prototype):
    short = prototype.select_inputs(73, demos=2, queries=1)
    long = prototype.select_inputs(73, demos=6, queries=4)
    assert [row["input"] for row in short["train"]] == [
        row["input"] for row in long["train"][:2]
    ]
    assert short["test"][0]["input"] == long["test"][0]["input"]


def test_four_queries_include_substantive_exact_30x30_stress(prototype):
    selection = prototype.select_inputs(53, demos=3, queries=4)
    large = [
        row for row in selection["test"]
        if len(row["input"]) == 30 and len(row["input"][0]) == 30
    ]
    assert len(large) == 1
    grid = large[0]["input"]
    info = prototype.analyze_input(grid)
    assert len(info["entries"]) == 4
    assert len(info["body"]) >= 20
    branch_counts = prototype.branch_counts(grid)
    assert branch_counts["border"] >= 4
    assert branch_counts["interior"] >= 4
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert min(r for r, _ in occupied) == 0
    assert max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0
    assert max(c for _, c in occupied) == 29
    assert prototype.output_for(grid, MODES[0]) != prototype.output_for(grid, MODES[1])


def test_sequential_intermediate_controls_second_stage(prototype):
    grid = prototype.select_inputs(89, demos=2, queries=4)["train"][0]["input"]
    cases = prototype.causal_cases(grid)
    assert {case["ablation"] for case in cases} == {"skip_a", "wrong_intermediate"}
    for case in cases:
        assert case["output"] != case["counterfactual_output"]
        assert case["intermediate_value"]["stage_a_cells"] >= 2
        assert case["intermediate_value"]["route"] in {"next", "previous"}


def test_racket_executes_labels_and_demos_leave_one_program(prototype, bridge):
    programs = {mode: prototype.rule_text(mode) for mode in MODES}
    for chosen in MODES:
        episode = prototype.generate_episode(67, composition=chosen, demos=2, queries=4)
        survivors = []
        for mode, program in programs.items():
            if all(
                _execute(bridge, program, pair["input"]) == pair["output"]
                for pair in episode["train"]
            ):
                survivors.append(mode)
        assert survivors == [chosen]
        for pair in episode["test"]:
            assert _execute(bridge, programs[chosen], pair["input"]) == pair["output"]


def test_racket_executes_causal_counterfactuals(prototype, bridge):
    grid = prototype.select_inputs(97, demos=2, queries=4)["train"][0]["input"]
    for case in prototype.causal_cases(grid):
        assert _execute(bridge, case["program"], grid) == case["output"]
        assert _execute(bridge, case["counterfactual_program"], grid) == case["counterfactual_output"]
        assert case["output"] != case["counterfactual_output"]
