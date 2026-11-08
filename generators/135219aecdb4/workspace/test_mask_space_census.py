from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_tool():
    path = Path(__file__).with_name("mask_space_census.py")
    spec = importlib.util.spec_from_file_location("mask_space_census", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_census_exposes_base_dependent_three_pass_masks():
    tool = _load_tool()
    census = tool.build_census(erasure_counts=(5, 6, 7))
    by_key = {
        (row["base_index"], row["n_erased"]): row
        for row in census["rows"]
    }
    assert by_key[(0, 5)]["pass_histogram"].get("3", 0) == 0
    assert by_key[(1, 5)]["pass_histogram"].get("3", 0) > 0
    assert sum(
        row["pass_histogram"].get("3", 0) for row in census["rows"]
    ) > 0
