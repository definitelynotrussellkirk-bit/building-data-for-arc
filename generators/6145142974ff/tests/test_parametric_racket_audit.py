"""Protected-Racket parity and causal-audit regression."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_protected_racket_audit_matches_python_and_refutes_wrong_intermediate():
    audit = _load("_test_6145142974ff_racket_audit", "racket_audit.py")
    report = audit.audit(seeds=(0,), demo_counts=(2,), queries=1)
    assert report["status"] == "pass"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["selected_label_evaluations"] == 6
    assert report["counterfactual_evaluations"] == 3
    assert report["failures"] == []
    assert report["counterfactual"]["demonstration_mismatch_indices"]
    assert report["counterfactual"]["query_mismatch_indices"]
    assert report["counterfactual"]["changed_cells"] > 0
