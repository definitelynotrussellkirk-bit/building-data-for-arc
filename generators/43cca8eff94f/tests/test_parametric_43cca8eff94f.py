"""Focused checks for the native frame-docking parametric adapter.

Python labels are claims here. Native qualification independently replays every
selected program and label through the packet's protected Racket runtime.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402


TASK_ID = "43cca8eff94f"
FINISHES = ("dock_only", "contact_projection")
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"
PROMOTION_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "probe.py"
QUERY_SHAPES = [(11, 13), (18, 20), (24, 26), (30, 30)]
STEP = {"right": (0, 1), "left": (0, -1), "down": (1, 0), "up": (-1, 0)}


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_43cca8eff94f_tests", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


def _canonical_program() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as source:
        rows = [json.loads(line) for line in source]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    assert len(programs) == 1
    return next(iter(programs))


def _bbox(cells):
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _oracle(grid, finish):
    """Independent literal-grid oracle for the declared two-setting family."""
    source = deepcopy(grid)
    h, w = len(source), len(source[0])
    red = {(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 2}
    cyan = {(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 8}
    rr1, rc1, rr2, rc2 = _bbox(red)
    fr1, fc1, fr2, fc2 = _bbox(cyan)
    if rc2 < fc1:
        direction = "right"
    elif rc1 > fc2:
        direction = "left"
    elif rr2 < fr1:
        direction = "down"
    else:
        direction = "up"
    dr, dc = STEP[direction]
    blockers = {(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v not in (0, 2)}
    docked = set(red)
    while True:
        nxt = {(r + dr, c + dc) for r, c in docked}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in nxt) or nxt & blockers:
            break
        docked = nxt
    out = deepcopy(source)
    for r, c in red:
        out[r][c] = 0
    for r, c in docked:
        out[r][c] = 2
    contacts = sorted(
        (r + dr, c + dc)
        for r, c in docked
        if 0 <= r + dr < h and 0 <= c + dc < w and out[r + dr][c + dc] == 8
    )
    rays = []
    if finish == "contact_projection":
        for r, c in contacts:
            r, c = r + dr, c + dc
            while 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                rays.append((r, c))
                r, c = r + dr, c + dc
        for r, c in rays:
            out[r][c] = 4
    return out, {"direction": direction, "docked_cells": sorted(docked),
                 "contact_cells": contacts, "projection_cells": sorted(rays)}


def _input_keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_parametric_adapter_is_present():
    assert ADAPTER_PATH.is_file(), "the task-local parametric adapter has not been implemented"


def test_contract_and_default_program_are_exact(adapter):
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"finish": list(FINISHES)},
        "default": {"finish": "dock_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/contact_projection.rkt",
        ],
    }
    canonical = _canonical_program()
    assert tuple(adapter.FINISHES) == FINISHES
    assert adapter.program({"finish": "dock_only"}).encode() == canonical.encode()
    alternative = adapter.program({"finish": "contact_projection"})
    assert alternative.startswith("\n(rule!") and alternative != canonical


def test_literal_projection_uses_sparse_post_dock_contact_cells(adapter):
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 0, 0],
        [0, 2, 2, 2, 0, 8, 0, 0, 0, 8, 0, 0],
        [0, 2, 0, 0, 0, 8, 0, 0, 0, 8, 0, 0],
        [0, 2, 2, 2, 0, 8, 0, 0, 0, 8, 0, 0],
        [0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    canonical, facts = _oracle(grid, "dock_only")
    projected, projected_facts = _oracle(grid, "contact_projection")
    assert facts["direction"] == "right"
    assert projected_facts["contact_cells"] == [(2, 5), (4, 5)]
    assert projected_facts["projection_cells"] == [
        (2, 6), (2, 7), (2, 8), (4, 6), (4, 7), (4, 8)
    ]
    assert adapter.solve(grid, "dock_only") == canonical
    assert adapter.solve(grid, "contact_projection") == projected
    assert adapter.dock_intermediate(grid) == {
        "direction": "right",
        "step": [0, 1],
        "docked_cells": projected_facts["docked_cells"],
        "contact_cells": projected_facts["contact_cells"],
        "projection_cells": projected_facts["projection_cells"],
    }
    # The plausible bbox-span shortcut incorrectly paints the middle row.
    bbox_rival = adapter.bbox_projection_solve(grid)
    assert bbox_rival != projected
    assert bbox_rival[3][6:9] == [4, 4, 4]
    # Projecting before A has no contact seed because the source gap is nonzero.
    assert adapter.wrong_order_solve(grid) == canonical != projected


@pytest.mark.parametrize("finish", FINISHES)
def test_generated_counts_prefixes_and_setting_matched_inputs(adapter, finish):
    setting = {"finish": finish}
    for seed in (0, 17):
        one = adapter.generate(seed, setting, demos=3, queries=1)
        four = adapter.generate(seed, setting, demos=3, queries=4)
        six = adapter.generate(seed, setting, demos=6, queries=4)
        assert one["train"] == four["train"] == six["train"][:3]
        assert one["test"] == four["test"][:1] == six["test"][:1]
        assert four["test"] == six["test"]
        for demos in (2, 3, 6):
            episode = adapter.generate(seed, setting, demos=demos, queries=4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(setting)
            keys = _input_keys(episode)
            assert len(keys) == len(set(keys))
            for split in ("train", "test"):
                for pair in episode[split]:
                    expected, _ = _oracle(pair["input"], finish)
                    assert pair["output"] == expected


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_settings_share_inputs_and_every_demo_separates_them(adapter, seed):
    episodes = {
        finish: adapter.generate(seed, {"finish": finish}, demos=6, queries=4)
        for finish in FINISHES
    }
    assert _input_keys(episodes[FINISHES[0]]) == _input_keys(episodes[FINISHES[1]])
    for index in range(6):
        assert episodes[FINISHES[0]]["train"][index]["output"] != episodes[FINISHES[1]]["train"][index]["output"]


def test_curriculum_reaches_30x30_with_four_directions_and_substantive_content(adapter):
    episode = adapter.generate(20261024, {"finish": "contact_projection"}, demos=6, queries=4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == QUERY_SHAPES
    directions = [adapter.dock_intermediate(p["input"])["direction"] for p in episode["train"] + episode["test"]]
    assert set(directions) == set(STEP)
    largest = episode["test"][-1]
    assert len(largest["input"]) == len(largest["input"][0]) == 30
    assert sum(v != 0 for row in largest["input"] for v in row) >= 110
    assert sum(v == 4 for row in largest["output"] for v in row) >= 35
    facts = adapter.dock_intermediate(largest["input"])
    assert 3 <= len(facts["contact_cells"]) < 11
    assert adapter.bbox_projection_solve(largest["input"]) != largest["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"finish": "unknown"}, {"finish": 1}, {"finish": True},
     {"finish": "dock_only", "extra": 1}],
)
def test_invalid_settings_reject(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4),
     (0, 1, 4), (0, 7, 4), (0, 3, True), (0, 3, 0), (0, 3, 5)],
)
def test_invalid_request_controls_reject(adapter, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"finish": "dock_only"}, demos=demos, queries=queries)


def test_generation_does_not_touch_process_global_rng(adapter):
    random.seed(20261024)
    state = random.getstate()
    first = adapter.generate(77, {"finish": "contact_projection"}, demos=3, queries=4)
    assert random.getstate() == state
    second = adapter.generate(77, {"finish": "contact_projection"}, demos=3, queries=4)
    assert first == second and first is not second



def _load_probe():
    assert PROBE_PATH.is_file(), "the reusable authoring probe has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_43cca8eff94f_probe_tests", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_authoring_probe_reports_bounded_rival_audit(tmp_path):
    probe = _load_probe()
    report = probe.build_report(seeds=[0, 17], demos=6, queries=4)
    assert report["schema"] == "arcpuzzles-parametric-authoring-probe-v1"
    assert report["task_id"] == TASK_ID
    assert report["seeds"] == [0, 17]
    assert report["counts"] == {"demos": 6, "queries": 4, "cases": 20}
    assert report["settings"] == [{"finish": "dock_only"}, {"finish": "contact_projection"}]
    assert report["checks"] == {
        "canonical_program_exact": True,
        "deterministic": True,
        "count_prefix_invariant": True,
        "same_inputs_across_settings": True,
        "every_demo_identifies_setting": True,
        "contact_projection_refutes_bbox_span": True,
        "contact_projection_refutes_wrong_order": True,
        "contains_30x30_query": True,
        "covers_all_cardinal_directions": True,
    }
    assert len(report["episodes"]) == 2
    assert all(item["bbox_mismatches"] == 10 for item in report["episodes"])
    assert all(item["wrong_order_mismatches"] == 10 for item in report["episodes"])
    target = tmp_path / "authoring-probe.json"
    probe.write_report(target, report)
    assert json.loads(target.read_text()) == report
