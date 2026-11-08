from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name: str):
    path = HOME / name
    spec = importlib.util.spec_from_file_location(f"c0bd_audit_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structural_audit_exercises_matched_settings_rivals_and_public_turns():
    audit = _load("audit.py")
    report = audit.structural_audit(seed_count=2)
    assert report["status"] == "passed"
    assert report["episodes"] == 2 * 3 * 2
    assert report["matched_input_checks"] == 2 * 3
    assert report["declared_rival_certificates"] == 2 * 3 * 2
    assert report["public_turn_checks"] == 2 * 3 * 2 * 4
    assert report["failures"] == []


def test_counterfactual_is_one_complete_wrong_intermediate_rule():
    audit = _load("audit.py")
    source = audit.wrong_intermediate_program()
    assert source.startswith("(rule!")
    assert "wrong-modes" in source
    assert source.count("(rule!") == 1
