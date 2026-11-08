"""Regression checks for the native parametric adapter boundary."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "222de43cc4aa"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def test_native_worker_can_consume_the_adapter_episode():
    """A missing native program field must reject this real generated episode."""
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    result = evaluate_contract(
        ROOT,
        TASK_ID,
        contract,
        [{"seed": 0, "settings": {"round_trips": 1}, "demos": 3, "queries": 4}],
    )
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["checks"][0]["survivors"] == [{"round_trips": 1}]
    assert result["checks"][0]["label_count"] == 7
    assert len(result["episodes"][0]["train"]) == 3
    assert len(result["episodes"][0]["test"]) == 4


def test_adapter_ignores_another_tasks_cached_prototype(monkeypatch):
    """A generic cached module must not replace this task's exact program."""
    foreign = types.ModuleType("prototype")
    foreign.rule_source = lambda _: "foreign prototype source"
    monkeypatch.setitem(sys.modules, "prototype", foreign)
    spec = importlib.util.spec_from_file_location(
        "round_trip_native_adapter_regression", PARAMETRIC / "adapter.py"
    )
    assert spec and spec.loader
    adapter = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, adapter)
    spec.loader.exec_module(adapter)
    authority = Catalog(ROOT).describe(TASK_ID).get("rule_task_id", TASK_ID)
    canonical = {row["program_solution"] for row in Catalog(ROOT)._variants()[authority]}
    assert len(canonical) == 1
    assert {adapter.program({"round_trips": 2})} == canonical
