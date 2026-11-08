from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/8c5406fbf66c/workspace/parametric"


def load(name: str, filename: str):
    path = HOME / filename
    assert path.is_file()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_audit_tool_covers_count_boundaries_settings_and_causal_ablation():
    verify = load("_test_8c54_verify", "verify.py")
    adapter = verify.load_adapter()
    programs = {
        adapter.program({"window_scope": scope}): scope
        for scope in ("all", "key_count_relay")
    }

    def execute(program, grid):
        return adapter.prototype.solve_python(grid, programs[program])

    report = verify.audit(
        seeds=(0,),
        count_cases=((2, 1), (3, 4), (6, 4)),
        execute=execute,
        runtime_identity={"backend": "test", "protected": False},
    )
    assert report["status"] == "passed"
    assert report["settings"] == 2
    assert report["jobs"] == 6
    assert report["episodes"] == 6
    assert report["label_count"] == (3 + 7 + 10) * 2
    assert report["count_cases"] == [[2, 1], [3, 4], [6, 4]]
    assert report["causal_ablation"]["changed_output"] is True
    assert report["large_query"]["dimensions"] == [30, 30]
    assert report["large_query"]["nonzero_cells"] >= 190
    assert report["finite_rivals"]
