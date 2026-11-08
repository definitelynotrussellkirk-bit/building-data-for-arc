"""Regression for the task-local legacy canonical-record compatibility tool."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/151f4dc0c08f/workspace/tools/base_preflight_compat.py"


def _load():
    spec = importlib.util.spec_from_file_location("preflight_compat_151f", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalizes_historical_single_test_pair_and_preserves_pair_lists():
    tool = _load()
    pair = {"input": [[1]], "output": [[1]]}
    assert tool.split_pairs({"test": pair}, "test") == [pair]
    assert tool.split_pairs({"train": [pair]}, "train") == [pair]
    with pytest.raises(ValueError, match="Invalid canonical"):
        tool.split_pairs({"test": "input"}, "test")
