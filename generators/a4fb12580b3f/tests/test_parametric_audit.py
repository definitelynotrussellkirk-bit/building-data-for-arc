"""A rival is selected using demos only, before query disagreement is examined."""
from pathlib import Path
import importlib.util
import pytest


def load_audit():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/audit.py"
    assert path.is_file(), "Finite-rival teaching audit is not implemented yet"
    spec = importlib.util.spec_from_file_location("a4fb_audit_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_query_disagreement_cannot_disqualify_a_demo_survivor():
    result = load_audit().assess_predictions([[[1]], [[2]]], [[[3]]], [[[1]], [[2]]], [[[4]]])
    assert result == {"demo_matches": [True, True], "survives_demonstrations": True,
                      "query_disagreements": [0], "harmful_survivor": True}


def test_counterexample_demo_disqualifies_the_wrong_rule():
    result = load_audit().assess_predictions([[[1]], [[2]]], [[[3]]], [[[1]], [[4]]], [[[4]]])
    assert result["survives_demonstrations"] is False
    assert result["harmful_survivor"] is False
    assert result["demo_matches"] == [True, False]


def test_equivalent_survivor_is_reported_without_claiming_unique_rule():
    result = load_audit().assess_predictions([[[1]], [[2]]], [[[3]]], [[[1]], [[2]]], [[[3]]])
    assert result["survives_demonstrations"] is True
    assert result["query_disagreements"] == []
    assert result["harmful_survivor"] is False


def test_missing_prediction_is_an_error_not_refuting_evidence():
    with pytest.raises(ValueError):
        load_audit().assess_predictions([[[1]], [[2]]], [[[3]]], [[[1]]], [[[3]]])
