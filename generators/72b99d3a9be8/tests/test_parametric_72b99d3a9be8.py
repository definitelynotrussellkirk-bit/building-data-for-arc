from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root

TASK_ID = "72b99d3a9be8"
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
    assert adapter.program({"reflector_color": 2}) == _canonical_program()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


def test_two_demo_episode_is_prefix_stable_and_setting_identifying() -> None:
    adapter = _load("adapter")
    for color in (2, 3):
        short = adapter.generate(17, {"reflector_color": color}, 2, 4)
        long = adapter.generate(17, {"reflector_color": color}, 6, 4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]
        other = 3 if color == 2 else 2
        assert all(
            adapter.transform(pair["input"], other) != pair["output"]
            for pair in short["train"]
        )


def test_inputs_are_matched_across_settings_and_distinct() -> None:
    adapter = _load("adapter")
    two = adapter.generate(41, {"reflector_color": 2}, 6, 4)
    three = adapter.generate(41, {"reflector_color": 3}, 6, 4)
    assert [p["input"] for p in two["train"] + two["test"]] == [
        p["input"] for p in three["train"] + three["test"]
    ]
    serial = [json.dumps(p["input"], separators=(",", ":")) for p in two["train"] + two["test"]]
    assert len(serial) == len(set(serial)) == 10


def test_dependency_intermediate_changes_with_reflector_color() -> None:
    adapter = _load("adapter")
    episode = adapter.generate(0, {"reflector_color": 3}, 2, 4)
    grid = episode["train"][0]["input"]
    selected = adapter.dependency_intermediate(grid, 3)
    wrong = adapter.dependency_intermediate(grid, 2)
    assert selected["bounce_events"] != wrong["bounce_events"]
    assert adapter.transform(grid, 3) == episode["train"][0]["output"]
    assert adapter.transform(grid, 2) != episode["train"][0]["output"]


def test_fourth_query_is_substantive_30_by_30_stress() -> None:
    adapter = _load("adapter")
    episode = adapter.generate(5, {"reflector_color": 2}, 2, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert (len(output), len(output[0])) == (30, 30)
    assert sum(cell != 0 for row in grid for cell in row) >= 45
    changed = sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b))
    assert changed >= 20


def test_bounded_audit_rejects_declared_query_changing_shortcuts() -> None:
    adapter = _load("adapter")
    for seed in range(12):
        for color in (2, 3):
            episode = adapter.generate(seed, {"reflector_color": color}, 2, 4)
            audit = adapter.audit_episode(episode, color)
            assert audit["ambiguous_query_rivals"] == []
            assert audit["survivors"] == [f"setting:{color}"]
