"""Focused base-generator regression checks found during parametric review."""
from __future__ import annotations

import importlib.util
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location("base_539", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_span_count_contract_matches_nine_available_nonbackground_colors():
    module = _load()
    assert module.AXES["span_count"]["valid"] == "1..9"
    grid = module.generate(11, 0, grid_h=10, grid_w=16, span_count=9)
    assert module.self_check(grid) == []
    assert sum(any(value for value in row) for row in grid) == 9
