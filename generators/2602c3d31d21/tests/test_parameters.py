"""Native promotion checks for the pairwise-signature parameter family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


TASK_ID = "2602c3d31d21"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
METRICS = ("squared_euclidean", "manhattan")


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
    return _load("parametric_2602c3d31d21", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_adapter_2602c3d31d21", ADAPTER_PATH)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=64) as runtime:
        yield runtime


def test_contract_declares_bounded_metric_family():
    assert PROMOTION_PATH.is_file(), "promotion contract must be created"
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"metric": list(METRICS)},
        "default": {"metric": "squared_euclidean"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


def test_default_program_is_exact_canonical_and_alternate_is_guarded(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.canonical_program() == canonical
    assert prototype.rule_text("squared_euclidean") == canonical
    assert adapter.program({"metric": "squared_euclidean"}) == canonical
    alternate = prototype.rule_text("manhattan")
    assert alternate == adapter.program({"metric": "manhattan"})
    assert alternate != canonical
    assert "(abs (- (first c1) (first c2)))" in alternate
    assert prototype.restore_canonical(alternate) == canonical


def test_episode_inputs_are_deterministic_matched_and_distinct(prototype, adapter):
    episodes = {
        metric: adapter.generate(17, {"metric": metric}, 3, 4)
        for metric in METRICS
    }
    repeated = adapter.generate(17, {"metric": "squared_euclidean"}, 3, 4)
    assert episodes["squared_euclidean"] == repeated
    left_inputs = [pair["input"] for split in ("train", "test") for pair in episodes[METRICS[0]][split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in episodes[METRICS[1]][split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == 7
    assert any(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(episodes[METRICS[0]][split], episodes[METRICS[1]][split])
    )
    for metric, episode in episodes.items():
        assert episode["program_solution"] == prototype.rule_text(metric)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.output_for(pair["input"], metric)


def test_two_demonstrations_identify_each_metric_against_declared_rival(prototype):
    inputs = prototype.select_inputs(29, demos=2, queries=4)
    for chosen in METRICS:
        labels = [prototype.output_for(row["input"], chosen) for row in inputs["train"]]
        survivors = [
            metric
            for metric in METRICS
            if all(
                prototype.output_for(row["input"], metric) == label
                for row, label in zip(inputs["train"], labels)
            )
        ]
        assert survivors == [chosen]
    first = inputs["train"][0]["input"]
    assert prototype.output_for(first, METRICS[0]) != prototype.output_for(first, METRICS[1])


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_supported_count_boundaries(prototype, demos, queries):
    episode = prototype.generate_episode(41, metric="manhattan", demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + queries


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"metric": "chebyshev"},
        {"metric": 1},
        {"demos": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"queries": 1.0},
    ],
)
def test_episode_rejects_invalid_boundaries(prototype, kwargs):
    call = {"seed": 0, "metric": "squared_euclidean", "demos": 3, "queries": 4}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate_episode(**call)


@pytest.mark.parametrize(
    "settings",
    [{}, {"metric": "squared_euclidean", "extra": 1}, {"metric": "chebyshev"}, None],
)
def test_adapter_rejects_unknown_or_missing_setting_keys(adapter, settings):
    with pytest.raises(ValueError, match="exactly metric|declared metric"):
        adapter.program(settings)


def test_four_queries_include_substantive_exact_30x30_stress(prototype):
    selection = prototype.select_inputs(53, demos=3, queries=4)
    large = [row for row in selection["test"] if len(row["input"]) == 30 and len(row["input"][0]) == 30]
    assert len(large) == 1
    grid = large[0]["input"]
    info = prototype.analyze_input(grid)
    body = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row[:-1]) if value]
    assert len(info["shapes"]) == 7
    assert len(body) >= 55
    assert {min(r for r, _ in body), max(r for r, _ in body)} == {0, 29}
    assert min(c for _, c in body) == 0
    assert max(c for _, c in body) >= 26
    assert sum(value != 0 for value in (row[-1] for row in grid)) == 7
    assert prototype.output_for(grid, METRICS[0]) != prototype.output_for(grid, METRICS[1])


def test_racket_executes_labels_and_demos_leave_one_program(prototype, bridge):
    programs = {metric: prototype.rule_text(metric) for metric in METRICS}
    for chosen in METRICS:
        episode = prototype.generate_episode(67, metric=chosen, demos=2, queries=4)
        survivors = []
        for metric, program in programs.items():
            if all(_execute(bridge, program, pair["input"]) == pair["output"] for pair in episode["train"]):
                survivors.append(metric)
        assert survivors == [chosen]
        for pair in episode["test"]:
            assert _execute(bridge, programs[chosen], pair["input"]) == pair["output"]


def test_query_outputs_are_not_needed_to_fit_demonstration_survivor(prototype):
    episode = prototype.generate_episode(71, metric="squared_euclidean", demos=2, queries=4)
    mutated = copy.deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    demos = episode["train"]
    survivors = [
        metric
        for metric in METRICS
        if all(prototype.output_for(pair["input"], metric) == pair["output"] for pair in demos)
    ]
    assert survivors == ["squared_euclidean"]
    assert mutated["train"] == episode["train"]
