from __future__ import annotations
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]


def load_audit():
    path = HOME / "workspace/parametric/audit_native.py"
    spec = importlib.util.spec_from_file_location("audit_public_eval_31f7f899", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_rivals_are_total_and_have_distinct_meanings():
    audit = load_audit()
    assert len(audit.RIVALS) >= 8
    assert set(audit.RIVALS) == set(audit.RIVAL_MEANINGS)
    programs = audit.rival_programs()
    assert set(programs) == set(audit.RIVALS)
    assert len(set(programs.values())) == len(programs)
    assert all(program.startswith("(rule!") for program in programs.values())


def test_bounded_protected_audit_finds_no_demo_consistent_query_disagreement(tmp_path):
    audit = load_audit()
    report = audit.run_audit(tmp_path / "audit.json", seeds=(0, 17), demos=2)
    assert report["status"] == "passed"
    assert report["protected"] is True
    assert report["evaluations"] > 100
    assert report["query_disagreements"] == []
    assert report["refuted_rivals"] >= 8
