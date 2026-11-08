"""Finite-rival audit must reject missing execution and expose demo ambiguity."""
import importlib.util
from pathlib import Path

import pytest


def audit():
    path = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "audit.py"
    spec = importlib.util.spec_from_file_location("aspect_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_survivor_with_wrong_query_is_a_finding():
    result = audit().assess_predictions([[[2]], [[3]]], [[[4]]], [[[2]], [[3]]], [[[2]]])
    assert result["survives_demonstrations"]
    assert result["ambiguous_queries"] == [0]


def test_query_agreement_cannot_rescue_a_demo_rejection():
    result = audit().assess_predictions([[[2]], [[3]]], [[[4]]], [[[4]], [[3]]], [[[4]]])
    assert not result["survives_demonstrations"]
    assert result["ambiguous_queries"] == []


@pytest.mark.parametrize("predictions", [[], [None], [[[2]]]])
def test_missing_or_failed_execution_never_becomes_rejection_evidence(predictions):
    with pytest.raises(ValueError, match="Missing or failed"):
        audit().assess_predictions([[[2]], [[3]]], [[[4]]], predictions, [[[4]]])
