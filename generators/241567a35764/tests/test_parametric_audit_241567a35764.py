from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load():
    path = HOME / "audit.py"
    spec = importlib.util.spec_from_file_location("audit_241567a35764", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structural_audit_covers_matched_settings_rivals_public_turns_and_stress():
    audit = _load()
    report = audit.structural_audit(seed_count=2)
    assert report["status"] == "passed"
    assert report["episodes"] == 2 * 3 * 2
    assert report["matched_input_checks"] == 2 * 3
    assert report["declared_rival_certificates"] == 2 * 3 * 2
    assert report["public_turn_checks"] == 2 * 3 * 2 * 4
    assert report["stress_30x30_checks"] == 2 * 3 * 2
    assert report["failures"] == []


def test_counterfactual_is_one_complete_untransformed_intermediate_rule():
    audit = _load()
    source = audit.wrong_intermediate_program()
    assert source.startswith("(rule!")
    assert "wrong-shape" in source
    assert source.count("(rule!") == 1
