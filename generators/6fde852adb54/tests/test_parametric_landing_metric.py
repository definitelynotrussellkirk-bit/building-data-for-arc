"""Native landing-metric family: contract, teaching, privacy, and Racket parity."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load("_landing_metric_prototype_test", PARAMETRIC / "prototype.py")


@pytest.fixture(scope="module")
def adapter():
    return load("_landing_metric_adapter_test", PARAMETRIC / "adapter.py")


def canonical_program() -> str:
    from reviewer_support import canonical_path, find_root

    with canonical_path(find_root(__file__)).open() as stream:
        row = next(json.loads(line) for line in stream if json.loads(line)["task_id"] == "6fde852adb54")
    return row["program_solution"]


def test_default_program_is_exact_canonical_and_adapter_is_thin(prototype, adapter):
    default = {"landing_metric": "total_cells"}
    alternate = {"landing_metric": "longest_vertical_run"}
    assert prototype.program(default) == canonical_program()
    assert adapter.program(default) == canonical_program()
    assert prototype.program(alternate) == adapter.program(alternate)
    assert prototype.program(alternate) != canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_and_finite_setting_identification(prototype, adapter, demos):
    episodes = [
        adapter.generate(17, {"landing_metric": metric}, demos, 4)
        for metric in prototype.METRICS
    ]
    for metric, episode in zip(prototype.METRICS, episodes):
        assert episode["program_solution"] == prototype.program({"landing_metric": metric})
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == demos + 4
        report = prototype.teaching_report(
            episode["train"], [pair["input"] for pair in episode["test"]], metric
        )
        assert report["setting_survivors"] == [metric]
        if demos >= 3:
            assert report["harmful_survivors"] == []
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]


def test_default_three_demo_lesson_rejects_declared_shortcuts(prototype):
    for seed in (0, 1, 17, 91):
        for metric in prototype.METRICS:
            episode = prototype.generate(seed, {"landing_metric": metric}, 3, 4)
            report = prototype.teaching_report(
                episode["train"], [pair["input"] for pair in episode["test"]], metric
            )
            assert report["setting_survivors"] == [metric]
            assert report["harmful_survivors"] == []
            assert set(report["tested_models"]) >= {
                "total_cells",
                "longest_vertical_run",
                "stay_in_source_column",
                "leftmost_best_column",
                "rightmost_best_column",
                "no_shelf_clearing",
                "tips_ignore_obstacles",
                "bottom_touching_run",
            }


def test_query_schedule_has_real_boundaries_and_substantive_30x30(prototype):
    episode = prototype.generate(23, {"landing_metric": "total_cells"}, 3, 4)
    grids = [pair["input"] for pair in episode["test"]]
    assert [(len(g), len(g[0])) for g in grids] == [(14, 14), (18, 20), (24, 24), (30, 30)]
    large = grids[-1]
    analysis = prototype.analyze(large)
    obstacle_cells = analysis["obstacle_cells"]
    assert len(obstacle_cells) >= 35
    assert len(analysis["obstacle_components"]) >= 8
    rows = [r for r, _ in obstacle_cells]
    cols = [c for _, c in obstacle_cells]
    assert min(rows) <= 4 and max(rows) >= 28
    assert min(cols) <= 1 and max(cols) >= 28
    assert any(len(component) >= 8 for component in analysis["obstacle_components"])


def test_generation_prefixes_do_not_depend_on_requested_totals(prototype):
    settings = {"landing_metric": "longest_vertical_run"}
    short = prototype.generate(31, settings, 2, 4)
    long = prototype.generate(31, settings, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]


def test_public_turn_is_sequential_and_private_invariant(prototype):
    episode = prototype.generate(7, {"landing_metric": "total_cells"}, 3, 4)
    first = prototype.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    assert prototype.public_turn_bytes(episode, 0) == prototype.public_turn_bytes(episode, 0)
    assert len(prototype.public_turn_id(episode, 0)) == 64

    changed = deepcopy(episode)
    changed["program_solution"] = "private mutation"
    changed["settings"] = {"landing_metric": "secret"}
    changed["seed"] = 999
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert prototype.public_turn_bytes(changed, 0) == prototype.public_turn_bytes(episode, 0)
    assert prototype.public_turn_id(changed, 0) == prototype.public_turn_id(episode, 0)
    assert prototype.public_turn(episode, 1)["test"][0]["input"] == episode["test"][1]["input"]
    assert prototype.public_turn_bytes(episode, 1) != prototype.public_turn_bytes(episode, 0)


def test_trace_exposes_real_component_then_metric_then_landing_dependency(prototype):
    episode = prototype.generate(0, {"landing_metric": "total_cells"}, 3, 4)
    grid = episode["train"][0]["input"]
    total = prototype.predict_with_trace(grid, "total_cells")
    runs = prototype.predict_with_trace(grid, "longest_vertical_run")
    total_body = next(item for item in total["columns"] if item["kind"] == "body" and item["component"])
    run_body = next(item for item in runs["columns"] if item["source_col"] == total_body["source_col"])
    assert total_body["component"] == run_body["component"]
    assert total_body["scores"] != run_body["scores"]
    assert total_body["landing_col"] != run_body["landing_col"]
    assert total["output"] != runs["output"]


def test_python_claims_match_both_racket_programs_on_all_profiles(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episodes = [
        prototype.generate(5, {"landing_metric": metric}, 6, 4)
        for metric in prototype.METRICS
    ]
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for metric, episode in zip(prototype.METRICS, episodes):
            wrapped = wrap_rule(prototype.program({"landing_metric": metric}))
            for pair in episode["train"] + episode["test"]:
                bridge.define_grid("g", pair["input"])
                assert bridge.eval_text(f"({wrapped} g)") == pair["output"]


@pytest.mark.parametrize(
    "settings",
    [{}, {"landing_metric": True}, {"landing_metric": "unknown"}, {"landing_metric": "total_cells", "x": 1}],
)
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.generate(0, settings, 3, 4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (2**63, 3, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, 3),
        (0, 3, 5),
        (0, 3, 4.0),
    ],
)
def test_invalid_requests_fail(prototype, seed, demos, queries):
    with pytest.raises(ValueError):
        prototype.generate(seed, {"landing_metric": "total_cells"}, demos, queries)


def test_reusable_audit_python_preflight_is_clean():
    audit = load("_landing_metric_audit_test", PARAMETRIC / "audit.py")
    report = audit.python_preflight([0], demo_counts=(2, 3, 6))
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 6
    assert report["setting_neutral_inputs"] is True
    assert report["failures"] == []
    assert set(report["tested_models"]) >= {
        "total_cells",
        "longest_vertical_run",
        "stay_in_source_column",
        "leftmost_best_column",
        "rightmost_best_column",
        "no_shelf_clearing",
        "tips_ignore_obstacles",
        "bottom_touching_run",
    }


def test_skip_assignment_counterfactual_changes_default_witness(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate(0, {"landing_metric": "total_cells"}, 3, 4)
    pair = episode["train"][0]
    counterfactual = (PARAMETRIC / "counterfactual_skip_assignment.rkt").read_text()
    with RacketBridge(max_calls_before_restart=8) as bridge:
        bridge.define_grid("g", pair["input"])
        actual = bridge.eval_text(f"({wrap_rule(prototype.program({'landing_metric': 'total_cells'}))} g)")
        skipped = bridge.eval_text(f"({wrap_rule(counterfactual)} g)")
    assert actual == pair["output"]
    assert skipped != actual
