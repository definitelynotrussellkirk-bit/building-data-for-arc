from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/base_preflight_compat.py"


def compat():
    assert SOURCE.is_file(), "task-local singleton-record preflight compatibility tool is missing"
    spec = importlib.util.spec_from_file_location("base_preflight_compat_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_split_pairs_normalizes_list_singleton_and_missing() -> None:
    mod = compat()
    pair = {"input": [[0]], "output": [[0]]}
    assert mod.split_pairs({"train": [pair]}, "train") == [pair]
    assert mod.split_pairs({"test": pair}, "test") == [pair]
    assert mod.split_pairs({}, "test") == []
