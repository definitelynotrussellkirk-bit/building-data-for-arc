"""Regression for the compact reviewer qualification helper."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_tool():
    path = Path(__file__).resolve().parents[1] / "workspace" / "qualify.py"
    spec = importlib.util.spec_from_file_location("f7_qualify", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_compact_qualification_reproduces_core_contract():
    tool = _load_tool()
    report = tool.run_qualification(seed=91, per_band=4)
    assert report["ok"] is True
    assert report["canonical_shortcut_fits"] == {"passed": 5, "total": 5}
    assert report["generated"]["count"] == 12
    assert report["generated"]["strict_passed"] == 12
    assert report["generated"]["bbox_area_tie"] == 12
    assert report["generated"]["rival_disagreed"] == 12
    assert report["override_probe"]["observed"] == report["override_probe"]["requested"]
