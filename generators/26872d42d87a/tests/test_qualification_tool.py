from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parents[1]
TOOL = HERE / "workspace" / "qualify.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("qualification_tool_26872d42d87a", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fast_qualification_reports_complete_semantic_coverage():
    tool = _load_tool()
    report = tool.run_qualification(per_band=8, seed=731)

    assert report["status"] == "passed"
    assert report["summary"]["canonical_pairs"] == 5
    assert report["summary"]["generated_inputs"] == 24
    assert report["summary"]["lesson_rotations"] == 96
    assert report["summary"]["ambiguous_rotations"] == 0
    assert report["summary"]["invalid_inputs"] == 0
    assert report["summary"]["exact_override_cases"] == 15
    assert set(report["schedule_profiles"]) == {
        "h8_w10",
        "h9_w11",
        "h10_w12",
        "h9_w10",
        "h10_w11",
    }
    assert all(
        row["fits_all_canonical"] and row["generated_counterexamples"] == 24
        for row in report["canonical_shortcuts"].values()
    )
    assert report["errors"] == []


def test_default_loader_uses_the_source_file_not_a_staged_task_package(monkeypatch):
    tool = _load_tool()

    def package_import_is_forbidden(*args, **kwargs):
        raise AssertionError("default qualification must not require a staged task package")

    monkeypatch.setattr(tool.importlib, "import_module", package_import_is_forbidden)
    module = tool._load_generator()
    assert module.TASK_ID == "26872d42d87a"
    assert module.RULE_HASH == "bc262329ef0d"
