from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root

TASK_ID = "73906110dd67"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    records = catalog._variants()[row.get("rule_task_id", TASK_ID)]
    programs = {record["program_solution"] for record in records}
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_canonical_source() -> None:
    adapter = _load("adapter")
    assert adapter.program({"order_metric": "cell_area"}) == _canonical_program()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


def test_two_demo_episode_is_prefix_stable_and_setting_identifying() -> None:
    adapter = _load("adapter")
    for metric in ("cell_area", "bbox_area"):
        short = adapter.generate(17, {"order_metric": metric}, 2, 4)
        long = adapter.generate(17, {"order_metric": metric}, 6, 4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]
        other = "bbox_area" if metric == "cell_area" else "cell_area"
        other_program = adapter.program({"order_metric": other})
        assert other_program != short["program_solution"]
        assert all(
            adapter.transform(pair["input"], other) != pair["output"]
            for pair in short["train"]
        )


def test_inputs_are_matched_across_settings_and_all_pairs_are_distinct() -> None:
    adapter = _load("adapter")
    cell = adapter.generate(41, {"order_metric": "cell_area"}, 6, 4)
    bbox = adapter.generate(41, {"order_metric": "bbox_area"}, 6, 4)
    assert [p["input"] for p in cell["train"] + cell["test"]] == [
        p["input"] for p in bbox["train"] + bbox["test"]
    ]
    serial = [json.dumps(p["input"], separators=(",", ":")) for p in cell["train"] + cell["test"]]
    assert len(serial) == len(set(serial)) == 10


def test_dependency_intermediate_controls_stack_order() -> None:
    adapter = _load("adapter")
    episode = adapter.generate(0, {"order_metric": "bbox_area"}, 2, 4)
    grid = episode["train"][0]["input"]
    facts = adapter.dependency_intermediate(grid, "bbox_area")
    assert facts["selected_object_indices"] != facts["cell_area_order"]
    assert adapter.render_order(grid, facts["selected_object_indices"]) == episode["train"][0]["output"]
    assert adapter.render_order(grid, facts["cell_area_order"]) != episode["train"][0]["output"]


def test_fourth_query_is_distributed_30_by_30_stress() -> None:
    adapter = _load("adapter")
    episode = adapter.generate(5, {"order_metric": "cell_area"}, 2, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied_rows = [r for r, row in enumerate(grid) if any(row)]
    occupied_cols = [c for c in range(30) if any(grid[r][c] for r in range(30))]
    assert min(occupied_rows) <= 2 and max(occupied_rows) >= 26
    assert min(occupied_cols) <= 2 and max(occupied_cols) >= 27
    assert sum(cell != 0 for row in grid for cell in row) >= 22


def test_bounded_audit_rejects_declared_query_changing_shortcuts() -> None:
    adapter = _load("adapter")
    for seed in range(12):
        for metric in ("cell_area", "bbox_area"):
            episode = adapter.generate(seed, {"order_metric": metric}, 2, 4)
            audit = adapter.audit_episode(episode, metric)
            assert audit["ambiguous_query_rivals"] == []
            assert audit["survivors"] == [f"setting:{metric}"]
