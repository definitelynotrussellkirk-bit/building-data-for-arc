"""Regression tests for singleton canonical split normalization."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
SOURCE = HERE.parents[1] / "workspace" / "parametric" / "preflight_compat.py"


def _load():
    spec = importlib.util.spec_from_file_location("fad48869c581_preflight_compat_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_singleton_test_pair_is_wrapped_without_mutating_record():
    assert SOURCE.is_file(), "compatibility launcher has not been implemented"
    compat = _load()
    pair = {"input": [[1]], "output": [[1]]}
    record = {"train": [pair], "test": pair, "program_solution": "(rule! g)"}
    normalized = compat.normalize_records([record])
    assert normalized[0]["train"] == [pair]
    assert normalized[0]["test"] == [pair]
    assert record["test"] is pair
    assert normalized[0] is not record


def test_normalizer_rejects_non_pair_split_shapes():
    assert SOURCE.is_file(), "compatibility launcher has not been implemented"
    compat = _load()
    with pytest.raises(TypeError, match="train must be a pair list"):
        compat.normalize_records([{"train": "bad", "test": []}])
