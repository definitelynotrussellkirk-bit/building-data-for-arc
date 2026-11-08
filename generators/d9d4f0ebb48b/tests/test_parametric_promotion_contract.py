"""Executable checks for the native parametric promotion surface."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types


TASK_ID = "d9d4f0ebb48b"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
HOME = HERE.parents[1] / "workspace" / "parametric"
PROMOTION = HOME / "promotion.json"
CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g (- r 1) c) v) (= (at g (+ r 1) c) v) (= (at g r (- c 1)) v) (= (at g r (+ c 1)) v)) (paint-cells out (positions-in-rect (- r 1) (- c 1) (+ r 1) (+ c 1)) v) out)))))"


def _load_adapter(path: Path):
    spec = importlib.util.spec_from_file_location("_test_d9d4_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_contract_loads_declared_adapter_and_resources():
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"fill_color_mode": ["local", "selector_source"]},
        "default": {"fill_color_mode": "local"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/prototype.py"],
    }
    adapter_path = REPO / contract["adapter"]
    assert adapter_path.is_file()
    assert all((REPO / resource).is_file() for resource in contract["resources"])

    adapter = _load_adapter(adapter_path)
    assert adapter.program(contract["default"]) == CANONICAL_PROGRAM
    assert adapter.program({"fill_color_mode": "selector_source"}) != CANONICAL_PROGRAM
    episode = adapter.generate(5, contract["default"], demos=2, queries=4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == CANONICAL_PROGRAM


def test_adapter_ignores_unrelated_ambient_prototype_module():
    poisoned = types.ModuleType("prototype")
    poisoned.program = lambda settings: (_ for _ in ()).throw(AssertionError("ambient module used"))
    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = poisoned
    try:
        adapter = _load_adapter(HOME / "adapter.py")
        assert adapter.program({"fill_color_mode": "local"}) == CANONICAL_PROGRAM
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous
