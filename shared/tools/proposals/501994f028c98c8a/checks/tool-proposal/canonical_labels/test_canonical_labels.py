"""Comparison and report tests use injected receipts, never a Python ARC mirror."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from reviewer_support import find_root


SOURCE = Path(__file__).with_name("canonical_labels.py")
SPEC = importlib.util.spec_from_file_location("proposed_canonical_labels", SOURCE)
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)
PROGRAM = "(rule! (lambda (g) g))"


def row(**updates):
    value = {"task_id": "fixture", "program_solution": PROGRAM, "solution_language": "racket",
             "train": [{"input": ["12", "30"], "output": [[1, 2], [3, 0]]}],
             "test": {"input": [[7]], "output": [[7]]}}
    value.update(updates)
    return value


def fixture_root(tmp_path, rows):
    root = tmp_path / "local-root"
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("".join(json.dumps(value) + "\n" for value in rows))
    return root


def receipt(outputs, *, program=PROGRAM):
    return {"backend": "racket", "program_sha256": TOOL.sha256(program),
            "results": [{"index": index, "status": "ok", "output": value} for index, value in enumerate(outputs)]}


def test_all_variants_normalize_and_only_unlabeled_tests_are_skipped(tmp_path):
    root = fixture_root(tmp_path, [row(), row(train=[{"input": [[8]], "output": [[8]]}],
                                             test=[{"input": [[0]]}])])
    calls = []
    def runner(program, inputs, **kwargs):
        calls.append((program, inputs, kwargs))
        return receipt([[[1, 2], [3, 0]], [[7]], [[8]]])
    report = TOOL.audit_task(root, "fixture", runner=runner)
    assert report["exit_code"] == 0
    assert report["counts"] == {"labeled_pairs": 3, "match": 3, "mismatch": 0, "error": 0}
    assert report["coverage"] == {"all_variants": True, "variant_count": 2,
                                  "labeled_pairs": 3, "attempted_pairs": 3, "skipped_only_unlabeled_test": 1}
    assert calls[0][1] == [[[1, 2], [3, 0]], [[7]], [[8]]]
    assert calls[0][2]["root"] == root.resolve()
    assert [(p["variant"], p["split"], p["pair_index"]) for p in report["pairs"]] == [(0, "train", 0), (0, "test", 0), (1, "train", 0)]


def test_corrupted_label_returns_one_with_exact_witness(tmp_path):
    # Intentional corrupted-label fixture, not a natural source-data finding.
    root = fixture_root(tmp_path, [row(train=[{"input": [[7]], "output": [[8]]}], test=[])])
    report = TOOL.audit_task(root, "fixture", runner=lambda *a, **k: receipt([[[7]]]))
    assert report["exit_code"] == 1 and report["counts"]["mismatch"] == 1
    witness = report["pairs"][0]
    assert witness["input"] == [[7]] and witness["expected"] == [[8]] and witness["actual"] == [[7]]
    assert witness["comparison"]["differences"] == [{"cell": [0, 0], "expected": 8, "actual": 7, "kind": "value_mismatch"}]
    assert "Hold" in report["admission_implication"]


def test_shape_diff_preserves_missing_and_extra_cells():
    diff = TOOL.compare_grids([[1, 2], [3, 4]], [[1, 2, 0]])
    assert diff["shape_mismatch"] and diff["differing_cells"] == 3
    assert diff["differences"] == [
        {"cell": [0, 2], "expected": None, "actual": 0, "kind": "extra_actual_cell"},
        {"cell": [1, 0], "expected": 3, "actual": None, "kind": "missing_actual_cell"},
        {"cell": [1, 1], "expected": 4, "actual": None, "kind": "missing_actual_cell"}]


def test_errors_take_precedence_over_mismatches(tmp_path):
    root = fixture_root(tmp_path, [row()])
    actual = receipt([[[9]], [[7]]])
    actual["results"][1] = {"index": 1, "status": "error", "error_kind": "TimeoutError", "message": "intentional injected failure"}
    report = TOOL.audit_task(root, "fixture", runner=lambda *a, **k: actual)
    assert report["exit_code"] == 2
    assert report["counts"] == {"labeled_pairs": 2, "match": 0, "mismatch": 1, "error": 1}
    assert report["pairs"][1]["execution_error"]["error_kind"] == "TimeoutError"


@pytest.mark.parametrize("broken", [
    row(train=[{"input": [[1]]}], test=[]),
    row(train=[], test=[{"input": [[1]], "output": None}]),
    row(train=[], test=[{"input": [[1], [1, 2]]}]),
    row(train=[], test=[{"input": [[1]]}]),
    row(train=[{"input": [[1]], "output": [[True]]}], test=[]),
    row(train=[{"input": [[1]], "output": [[1.0]]}], test=[]),
])
def test_invalid_or_empty_labeled_data_cannot_pass(tmp_path, broken):
    root = fixture_root(tmp_path, [broken])
    report = TOOL.audit_task(root, "fixture", runner=lambda *a, **k: pytest.fail("must reject before execution"))
    assert report["exit_code"] == 2 and report["error"]["stage"] == "data_binding"


def test_conflicting_variant_programs_and_wrong_pin_fail_before_execution(tmp_path):
    root = fixture_root(tmp_path, [row(), row(program_solution="(rule! (lambda (g) (flip-lr g)))")])
    runner = lambda *a, **k: pytest.fail("binding error must not execute a rule")
    assert TOOL.audit_task(root, "fixture", runner=runner)["exit_code"] == 2
    (root / "shared/data/canonical/puzzles.jsonl").write_text(json.dumps(row()) + "\n")
    assert TOOL.audit_task(root, "fixture", expected_program_sha256="0" * 64, runner=runner)["exit_code"] == 2


def test_identical_inputs_with_conflicting_labels_are_data_errors(tmp_path):
    root = fixture_root(tmp_path, [row(), row(test={"input": [[7]], "output": [[8]]})])
    report = TOOL.audit_task(root, "fixture", runner=lambda *a, **k: pytest.fail("must reject before execution"))
    assert report["exit_code"] == 2 and "Conflicting labels" in report["error"]["message"]


@pytest.mark.parametrize("fault", ["missing", "duplicate", "backend", "hash", "ragged"])
def test_invalid_execution_receipts_are_errors(tmp_path, fault):
    root = fixture_root(tmp_path, [row()])
    actual = receipt([[[1, 2], [3, 0]], [[7]]])
    if fault == "missing":
        actual["results"].pop()
    elif fault == "duplicate":
        actual["results"][1]["index"] = 0
    elif fault == "backend":
        actual["backend"] = "python"
    elif fault == "hash":
        actual["program_sha256"] = "0" * 64
    else:
        actual["results"][0]["output"] = [[1], [2, 3]]
    assert TOOL.audit_task(root, "fixture", runner=lambda *a, **k: deepcopy(actual))["exit_code"] == 2


def test_ledger_cannot_escape_explicit_root(tmp_path):
    root = tmp_path / "root"
    (root / "shared/data/canonical").mkdir(parents=True)
    external = tmp_path / "external.jsonl"
    external.write_text(json.dumps(row()) + "\n")
    (root / "shared/data/canonical/puzzles.jsonl").symlink_to(external)
    report = TOOL.audit_task(root, "fixture", runner=lambda *a, **k: pytest.fail("must not execute"))
    assert report["exit_code"] == 2


def test_raw_adapter_rebinds_after_error_without_retrying_failed_input(monkeypatch):
    from arc_repl import executor as module
    seen, created = [], []
    class FakeExecutor:
        def __init__(self, task, **kwargs):
            assert task == {"train": [], "test": []} and kwargs["use_racket"]
            self.use_racket = True
            self._bridge = SimpleNamespace(timeout=None)
            self.state_summary = {"rule": False}
            self.runtime_identity = {"backend": "racket", "fixture": True}
            self.closed = False
            created.append(self)
        def step(self, source):
            assert source == PROGRAM
            self.state_summary["rule"] = True
            return "rule set"
        def _apply_rule(self, value):
            seen.append(value)
            if len(seen) == 2:
                raise TimeoutError("intentional adapter fixture")
            return [[9]] if len(seen) == 1 else [[3]]
        def close(self):
            self.closed = True
    monkeypatch.setattr(module, "ArcExecutor", FakeExecutor)
    observed = TOOL.execute_racket_batch(PROGRAM, [[[1]], [[2]], [[3]]], root=find_root(SOURCE))
    assert [r["status"] for r in observed["results"]] == ["ok", "error", "ok"]
    assert [r["session_index"] for r in observed["results"]] == [0, 0, 1]
    assert len(seen) == 3 and len(created) == 2 and all(e.closed for e in created)


def test_raw_adapter_binding_error_never_applies_an_unbound_rule(monkeypatch):
    from arc_repl import executor as module
    class FailedBinding:
        def __init__(self, *args, **kwargs):
            self.use_racket = True
            self._bridge = SimpleNamespace(timeout=None)
            self.state_summary = {"rule": False}
        def step(self, source):
            return "ERROR: intentional binding fixture"
        def _apply_rule(self, value):
            pytest.fail("failed binding must prevent application")
        def close(self):
            pass
    monkeypatch.setattr(module, "ArcExecutor", FailedBinding)
    observed = TOOL.execute_racket_batch(PROGRAM, [[[1]]], root=find_root(SOURCE))
    assert observed["results"][0]["status"] == "error"
    assert "Rule load failed" in observed["results"][0]["message"]
