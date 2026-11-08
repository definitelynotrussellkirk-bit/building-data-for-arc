"""Native parametric transform/intersection family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "8862d66fbb3d"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"finish": "all_overlap"},
    {"finish": "adjacent_overlap"},
)


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been built"
    name = "tested_8862d66fbb3d_parametric_adapter"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_canonical_and_alternative_executes():
    adapter = load_adapter()
    assert adapter.program(SETTINGS[0]) == canonical_program()
    assert adapter.program(SETTINGS[1]) != canonical_program()
    pair = adapter.generate(0, SETTINGS[1], demos=2, queries=1)["train"][0]
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, PARAMETRIC):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for settings in SETTINGS:
                assert apply(adapter.program(settings), pair["input"]) == adapter.solve(pair["input"], settings)
        finally:
            bridge.close()


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_prefix_matched_inputs_and_fixed_canonical_domain(demos):
    adapter = load_adapter()
    episodes = [adapter.generate(17, settings, demos=demos, queries=4) for settings in SETTINGS]
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)
    assert all(len(ep["train"]) == demos and len(ep["test"]) == 4 for ep in episodes)
    assert episodes[0]["train"] == one["train"]
    assert episodes[0]["test"][:1] == one["test"]
    inputs = [pair["input"] for split in ("train", "test") for pair in episodes[0][split]]
    assert all([pair["input"] for split in ("train", "test") for pair in ep[split]] == inputs for ep in episodes[1:])
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
    assert all(len(grid) == 4 and len(grid[0]) == 7 for grid in inputs)
    assert all(len(pair["output"]) == len(pair["output"][0]) == 3
               for ep in episodes for split in ("train", "test") for pair in ep[split])
    for ep in episodes:
        public_challenge_bytes(ep)


def test_two_demos_identify_settings_and_refute_declared_rivals():
    adapter = load_adapter()
    for settings in SETTINGS:
        episode = adapter.generate(3, settings, demos=2, queries=4)
        certificate = adapter.teaching_check(episode)
        assert certificate["status"] == "identified"
        assert certificate["surviving_rivals"] == []
        assert certificate["used_query_answers"] is False
        assert all(pair["output"] == adapter.solve(pair["input"], settings) for pair in episode["train"])
    alt = adapter.generate(3, SETTINGS[1], demos=2, queries=4)
    assert all(adapter.changed_cells(pair["output"], adapter.solve(pair["input"], SETTINGS[0])) > 0 for pair in alt["train"])


def test_public_turn_hides_private_state_and_future_queries():
    adapter = load_adapter()
    four = adapter.generate(41, SETTINGS[1], demos=3, queries=4)
    one = adapter.generate(41, SETTINGS[1], demos=3, queries=1)
    first = adapter.public_turn(four, 0)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    public_challenge_bytes(first)
    changed = deepcopy(four)
    changed["settings"] = SETTINGS[0]
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[8]]} for _ in changed["test"][1:]]
    assert adapter.public_turn(changed, 0) == first
    assert adapter.public_turn(four, 1) == {"test": [{"input": four["test"][1]["input"]}]}


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"finish": True}},
        {"settings": {"finish": "unknown"}}, {"settings": {"finish": "all_overlap", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises((TypeError, ValueError)):
        load_adapter().generate(**request)


def test_dependency_trace_and_wrong_intermediate_counterfactual():
    adapter = load_adapter()
    grid = adapter.generate(0, SETTINGS[1], demos=2, queries=4)["train"][0]["input"]
    trace = adapter.dependency_trace(grid, SETTINGS[1])
    assert trace["step_a"] == "transform the right mask by the command and intersect it with the left mask"
    assert trace["intermediate"]["occupied_cells"] >= 3
    assert trace["step_b"] == "keep only overlap cells with an orthogonal overlap neighbor"
    assert 0 < trace["adjacent_overlap_cells"] < trace["intermediate"]["occupied_cells"]
    assert adapter.solve(grid, SETTINGS[1]) != adapter.wrong_intermediate_solve(grid)


def test_protected_racket_labels_and_demo_only_identification():
    load_adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [dict(seed=0, settings=settings, demos=3, queries=4) for settings in SETTINGS]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [[job["settings"]] for job in jobs]
    assert [check["label_count"] for check in result["checks"]] == [7, 7]


def test_self_review_tool_runs_without_racket_for_fast_future_checks():
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "bounded self-review tool has not been built"
    name = "tested_8862d66fbb3d_parametric_audit"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    report = module.build_report(seed_count=2, execute_racket=False)
    assert report["status"] == "passed"
    assert report["structural"]["failures"] == []
    assert report["teaching"]["harmful_survivors"] == []
