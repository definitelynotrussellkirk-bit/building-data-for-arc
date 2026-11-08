"""Role-aware status vocabulary for check_task_authority_sync.

Run: python3 -m pytest tests/test_check_task_authority_sync.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "cts", ROOT / "scripts/check_task_authority_sync.py"
)
cts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cts)


def _write_fixture(tmp_path, *, raw_code, target_code, program_solution):
    canonical = tmp_path / "puzzles.jsonl"
    canonical.write_text(
        json.dumps(
            {
                "task_id": "fixturetask00",
                "train": [{"input": [[1]], "output": [[1]]}],
                "test": [{"input": [[2]], "output": [[2]]}],
                "program_solution": program_solution,
            }
        )
        + "\n"
    )
    base = tmp_path / "solutions"
    base.mkdir()
    (base / "x__fixturetask00.json").write_text(
        json.dumps(
            {
                "task_id": "fixturetask00",
                "racket_target": {
                    "raw_code": raw_code,
                    "target_code": target_code,
                },
            }
        )
    )
    cts.CANONICAL = canonical
    cts.BASE_SOLUTIONS = base


def test_all_synchronized(tmp_path):
    rule = "(rule! (lambda (g) g))"
    _write_fixture(
        tmp_path, raw_code=rule, target_code=rule, program_solution=rule
    )
    audit = cts.audit_task("fixturetask00")
    assert audit["status"] == "synchronized"
    assert audit["archival_divergent"] == []
    assert audit["selected_group_counts"]["exact_sha256"] == 1


def test_archival_divergence_is_not_diagnostic(tmp_path):
    rule = "(rule! (lambda (g) g))"
    _write_fixture(
        tmp_path,
        raw_code=";; archival bundle\n" + rule,
        target_code=rule,
        program_solution=rule,
    )
    audit = cts.audit_task("fixturetask00")
    assert audit["status"] == "selected_synchronized_archival_divergent"
    assert len(audit["archival_divergent"]) == 1
    assert audit["selected_group_counts"]["exact_sha256"] == 1
    assert audit["group_counts"]["exact_sha256"] == 2


def test_active_divergence_stays_diagnostic(tmp_path):
    _write_fixture(
        tmp_path,
        raw_code="(rule! (lambda (g) g))",
        target_code="(rule! (lambda (g) g))",
        program_solution="(rule! (lambda (g) (flip-lr g)))",
    )
    audit = cts.audit_task("fixturetask00")
    assert audit["status"] == "diagnostic_divergence"


def test_execution_parity_fails_loud_on_wrong_archival(tmp_path):
    _write_fixture(
        tmp_path,
        raw_code="(rule! (lambda (g) (flip-ud (flip-ud (recolor g 1 3)))))",
        target_code="(rule! (lambda (g) g))",
        program_solution="(rule! (lambda (g) g))",
    )
    audit = cts.audit_task("fixturetask00")
    parity = cts.verify_execution_parity(audit)
    assert parity["status"] == "FAIL"
    failing = [
        s for s in parity["sources"] if not s.get("solves_all_canonical_pairs")
    ]
    assert failing and "archival_or_executable_raw" in failing[0]["roles"]


def test_execution_parity_passes_equivalent_texts(tmp_path):
    _write_fixture(
        tmp_path,
        raw_code=";; same semantics, different text\n(rule! (lambda (g) g))",
        target_code="(rule! (lambda (g) g))",
        program_solution="(rule! (lambda (g) g))",
    )
    audit = cts.audit_task("fixturetask00")
    parity = cts.verify_execution_parity(audit)
    assert parity["status"] == "PASS"
    assert len(parity["sources"]) == 2
