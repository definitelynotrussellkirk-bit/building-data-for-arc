"""Smoke test for the retained bounded parametric self-audit."""
from __future__ import annotations

import importlib.util
import sys

from reviewer_support import find_root

TASK_ID = "15df00eb9323"
ROOT = find_root(__file__)
AUDIT = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "audit.py"


def test_bounded_audit_tool_checks_both_demo_boundaries():
    assert AUDIT.is_file(), "bounded audit tool has not been built"
    name = "_test_15df00eb9323_audit"
    spec = importlib.util.spec_from_file_location(name, AUDIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    report = module.run_audit(seed_count=2, demo_counts=(2, 6))
    assert report["status"] == "passed"
    assert report["bounded"]["seed_count"] == 2
    assert report["checks"]["episodes"] == 8
    assert report["checks"]["declared_program_survivors"] == {
        "majority": ["majority"],
        "unanimous": ["unanimous"],
    }


def test_preflight_compat_normalizes_singleton_and_list_splits():
    compat = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "preflight_compat.py"
    assert compat.is_file(), "source-bound preflight compatibility runner has not been built"
    name = "_test_15df00eb9323_preflight_compat"
    spec = importlib.util.spec_from_file_location(name, compat)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    pair = {"input": [[0]], "output": [[0]]}
    assert module._split_pairs({"test": pair}, "test") == [pair]
    assert module._split_pairs({"train": [pair]}, "train") == [pair]
