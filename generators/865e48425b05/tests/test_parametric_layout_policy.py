"""Native parametric layout-policy family for palette-mask multiplication."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "865e48425b05"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"layout_policy": "horizontal"},
    {"layout_policy": "vertical"},
    {"layout_policy": "dominant_axis"},
)


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "the requested native parametric adapter has not been built"
    name = "tested_865e48425b05_parametric_adapter"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
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


def mask_bbox(grid: list[list[int]]) -> tuple[int, int, int]:
    cells = [
        (row, col)
        for row in range(2, len(grid))
        for col, value in enumerate(grid[row])
        if value == 1
    ]
    assert cells
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return bottom - top + 1, right - left + 1, len(cells)


def layout_of(output: list[list[int]], mask_h: int, mask_w: int, colors: int) -> str:
    if len(output) == mask_h and len(output[0]) == colors * mask_w + colors - 1:
        return "horizontal"
    if len(output) == colors * mask_h + colors - 1 and len(output[0]) == mask_w:
        return "vertical"
    raise AssertionError(
        f"unexpected output shape {len(output)}x{len(output[0])} for "
        f"mask {mask_h}x{mask_w} and {colors} colors"
    )


def test_default_program_is_exact_canonical_and_all_programs_execute():
    adapter = load_adapter()
    assert adapter.program(SETTINGS[0]) == canonical_program()
    assert len({adapter.program(settings) for settings in SETTINGS}) == 3

    grids = adapter.generate(0, SETTINGS[0], demos=2, queries=1)["train"]
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, PARAMETRIC):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            # One protected execution per declared program is enough here; the
            # retained audit exercises every selected/rival label at scale.
            for index, settings in enumerate(SETTINGS):
                grid = grids[index % len(grids)]["input"]
                assert apply(adapter.program(settings), grid) == adapter.solve(grid, settings)
        finally:
            bridge.close()


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_prefix_matched_inputs_distinctness_and_large_stress(demos):
    adapter = load_adapter()
    episodes = [adapter.generate(17, settings, demos=demos, queries=4) for settings in SETTINGS]
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert all(len(episode["train"]) == demos and len(episode["test"]) == 4 for episode in episodes)
    assert episodes[0]["train"] == one["train"]
    assert episodes[0]["test"][:1] == one["test"]

    inputs = [pair["input"] for split in ("train", "test") for pair in episodes[0][split]]
    assert all(
        [pair["input"] for split in ("train", "test") for pair in episode[split]] == inputs
        for episode in episodes[1:]
    )
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
    assert all(1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30 for grid in inputs)

    large = episodes[0]["test"][-1]["input"]
    assert len(large) == len(large[0]) == 30
    mask_h, mask_w, mask_cells = mask_bbox(large)
    assert {mask_h, mask_w} == {12, 14}
    assert mask_cells >= 70
    assert any(large[-1]) and any(row[-1] == 1 for row in large)
    assert sum(value != 0 for row in large for value in row) >= 72

    for episode in episodes:
        public_challenge_bytes(episode)
        assert all(len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30
                   for split in ("train", "test") for pair in episode[split])


def test_first_two_demos_identify_all_settings_and_defeat_named_rivals():
    adapter = load_adapter()
    layouts = []
    for settings in SETTINGS:
        episode = adapter.generate(3, settings, demos=2, queries=4)
        certificate = adapter.teaching_check(episode)
        assert certificate["status"] == "identified"
        assert certificate["surviving_rivals"] == []
        assert certificate["used_query_answers"] is False
        pair_layouts = []
        for pair in episode["train"]:
            mask_h, mask_w, _ = mask_bbox(pair["input"])
            colors = sum(value != 0 for value in pair["input"][0])
            pair_layouts.append(layout_of(pair["output"], mask_h, mask_w, colors))
        layouts.append(pair_layouts)

    assert layouts == [
        ["horizontal", "horizontal"],
        ["vertical", "vertical"],
        ["horizontal", "vertical"],
    ]
    first = adapter.generate(3, SETTINGS[0], demos=2, queries=1)["train"]
    first_h, first_w, _ = mask_bbox(first[0]["input"])
    second_h, second_w, _ = mask_bbox(first[1]["input"])
    assert first_w > first_h and len(first[0]["input"]) > len(first[0]["input"][0])
    assert second_h > second_w and len(first[1]["input"]) < len(first[1]["input"][0])


def test_public_turn_is_single_query_private_invariant_and_prefix_identical():
    adapter = load_adapter()
    four = adapter.generate(41, SETTINGS[2], demos=3, queries=4)
    one = adapter.generate(41, SETTINGS[2], demos=3, queries=1)
    first = adapter.public_turn(four, 0)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    assert len(first["train"]) == 3
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    public_challenge_bytes(first)

    changed = deepcopy(four)
    changed["settings"] = {"layout_policy": "horizontal"}
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[8]]} for _ in changed["test"][1:]]
    assert adapter.public_turn(changed, 0) == first
    assert adapter.public_turn(four, 1) == {"test": [{"input": four["test"][1]["input"]}]}


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"layout_policy": True}},
        {"settings": {"layout_policy": "diagonal"}},
        {"settings": {"layout_policy": "horizontal", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)


def test_dependency_trace_and_skip_analysis_counterfactual():
    adapter = load_adapter()
    episode = adapter.generate(0, SETTINGS[2], demos=2, queries=4)
    tall = episode["train"][1]["input"]
    trace = adapter.dependency_trace(tall, SETTINGS[2])
    assert trace["step_a"] == "crop the color-1 mask and measure its bbox"
    assert trace["intermediate"]["mask_height"] > trace["intermediate"]["mask_width"]
    assert trace["intermediate"]["dominant_axis"] == "vertical"
    assert trace["step_b"] == "pack recolored copies along the selected axis"
    ordinary = adapter.solve(tall, SETTINGS[2])
    skipped = adapter.solve(tall, SETTINGS[0])
    assert ordinary != skipped
    assert trace["selected_axis"] == "vertical"


def test_protected_racket_labels_and_demo_only_setting_identification():
    load_adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [
        dict(seed=0, settings=settings, demos=3, queries=4)
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["protected"] is True
    assert result["racket_evaluations"] == len(jobs) * (len(SETTINGS) * 3 + 4)
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [7] * len(jobs)


def load_audit():
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "the bounded protected-Racket audit has not been built"
    name = "tested_865e48425b05_parametric_audit"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_reproducible_audit_checks_rivals_public_turns_and_causal_witness():
    # Exercise report construction cheaply in the task suite. The retained
    # command receipt/report runs the same audit with protected Racket over
    # 18 episodes and 288 evaluations.
    report = load_audit().build_report(seeds=(0,), demo_counts=(2,), execute_racket=False)
    assert report["schema"] == "865e48425b05-parametric-audit-v1"
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 3
    assert report["harmful_survivors"] == []
    assert report["python_racket_mismatches"] == []
    assert report["racket"]["protected"] is False
    assert report["public_projection"]["failures"] == []
    assert report["public_projection"]["turns_checked"] == 12
    witness = report["sequential_dependency_witness"]
    assert witness["setting"] == {"layout_policy": "dominant_axis"}
    assert witness["intermediate"]["dominant_axis"] == "vertical"
    assert witness["counterfactual"] == "skip A and always pack horizontally"
    assert witness["mismatched_cells"] > 0
