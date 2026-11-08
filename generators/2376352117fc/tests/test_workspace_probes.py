"""Canonical storage variants must not break the findings-only audit tool."""
import importlib.util
from pathlib import Path


def load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace/audit_assigned_targets.py"
    spec = importlib.util.spec_from_file_location("audit_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_pairs_normalizes_single_test_and_row_strings():
    probe = load_probe()
    assert callable(getattr(probe, "canonical_pairs", None)), "Missing canonical layout normalization"
    data = {"train": [{"input": ["01"], "output": ["08"]}],
            "test": {"input": [[2, 3]], "output": [[0, 8]]}}
    assert probe.canonical_pairs(data) == [
        {"input": [[0, 1]], "output": [[0, 8]]},
        {"input": [[2, 3]], "output": [[0, 8]]}]


def test_canonical_pairs_accepts_test_list_without_mutating():
    probe = load_probe()
    assert callable(getattr(probe, "canonical_pairs", None)), "Missing canonical layout normalization"
    data = {"train": [], "test": [{"input": ["2"], "output": ["8"]}]}
    assert probe.canonical_pairs(data) == [{"input": [[2]], "output": [[8]]}]
    assert data["test"][0]["input"] == ["2"]
