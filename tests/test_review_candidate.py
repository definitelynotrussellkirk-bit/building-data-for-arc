import json
import difflib
from pathlib import Path
import zipfile

import pytest

from arcpuzzles import Catalog, review
from arcpuzzles.review_return import intake
from arcpuzzles.review_candidate import check_candidate
from arcpuzzles.review_candidate import _RACKET_CHECK
from arcpuzzles.runtime import run_process
import sys


def patch_for(path, before="VERSION = '1.0.0'", after="VERSION = '2.0.0'"):
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            f"@@ -1 +1 @@\n-{before}\n+{after}\n")


def returned(library, tmp_path, patch, *, patch_name="patches/generator.patch"):
    root = tmp_path / "REVIEW"
    assignment = review.pick(Catalog(library), task_id="aaaa00000001", review_root=root)
    contract = (Path(assignment["directory"]) / "ASSIGNMENT.json").read_bytes()
    data = {"schema": "arcpuzzles-review-results-v1", "assignment_id": assignment["id"],
            "generator_id": assignment["task_id"], "completion_state": "complete",
            "changed_components": ["generator"], "patches": [patch_name], "checks": [],
            "remaining_failures": [], "improvement_claim": "Better coverage"}
    archive = tmp_path / "return.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("ASSIGNMENT.json", contract)
        handle.writestr("RESULTS.json", json.dumps(data))
        handle.writestr("REVIEW.md", "Changed one case\n")
        handle.writestr("FEEDBACK_TO_CODEX.md", "No feedback\n")
        handle.writestr(patch_name, patch)
    receipt = intake(root, archive)
    assert receipt["status"] == "accepted"
    return root, assignment


def test_generator_patch_applies_only_to_disposable_workspace(library, tmp_path):
    path = "workspace/puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    root, assignment = returned(library, tmp_path, patch_for(path))
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "failed_checks"  # fixture lacks the real battery
    assert "VERSION = '2.0.0'" in (Path(result["candidate_path"]) / path).read_text()
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '1.0.0'\n"
    assert Path(result["receipt_path"]).is_file()
    assert {item["kind"] for item in result["checks"]} >= {"baseline_battery", "battery"}


def test_patch_code_may_contain_word_copy(library, tmp_path):
    path = "workspace/puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    root, assignment = returned(library, tmp_path, patch_for(path, after="VERSION = '2.0.0'  # copy case"))
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "failed_checks"
    assert "copy case" in (Path(result["candidate_path"]) / path).read_text()


@pytest.mark.parametrize("path", ["workspace/puzzle_generators/per_puzzle/aaaa00000002/generator.py",
                                  "workspace/scripts/shared_helper.py", "../outside.py"])
def test_unrelated_patch_path_is_rejected(library, tmp_path, path):
    root, assignment = returned(library, tmp_path, patch_for(path))
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "rejected_patch"
    assert not result.get("candidate_path")


def test_binary_patch_is_rejected(library, tmp_path):
    path = "workspace/puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    patch = f"diff --git a/{path} b/{path}\nGIT binary patch\nliteral 1\nA\n"
    root, assignment = returned(library, tmp_path, patch)
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "rejected_patch"


def test_symlink_creation_patch_is_rejected(library, tmp_path):
    path = "workspace/notes/aaaa00000001/link"
    patch = (f"diff --git a/{path} b/{path}\nnew file mode 120000\n"
             "--- /dev/null\n" + f"+++ b/{path}\n@@ -0,0 +1 @@\n+../../outside\n")
    root, assignment = returned(library, tmp_path, patch)
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "rejected_patch"
    assert not result.get("candidate_path")


def test_racket_failure_sets_nonzero_exit_for_candidate_gate(tmp_path):
    (tmp_path / "arc_repl").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data/canonical").mkdir(parents=True)
    (tmp_path / "arc_repl/__init__.py").write_text("")
    (tmp_path / "scripts/__init__.py").write_text("")
    (tmp_path / "arc_repl/racket_bridge.py").write_text(
        "class RacketBridge:\n def eval_text(self, expression): return [[1]]\n def close(self): pass\n")
    (tmp_path / "scripts/rule_smoke.py").write_text(
        "from types import SimpleNamespace\n"
        "def rule_application(source, grid): return source\n"
        "def load_gen(task): return SimpleNamespace(generate=lambda *a, **k: [[1]])\n"
        "def mirror_normalized(value): return value\n"
        "def arc_bounds_violation(value): return None\n"
        "def _norm_grid(value): return [[int(c) for c in row] if isinstance(row,str) else row for row in value]\n")
    (tmp_path / "data/canonical/puzzles.jsonl").write_text(json.dumps({
        "task_id": "task", "program_solution": "(rule! g)",
        "train": [{"input": [[1]], "output": [[2]]}], "test": []}) + "\n")
    baseline = tmp_path / "baseline.jsonl"
    baseline.write_text((tmp_path / "data/canonical/puzzles.jsonl").read_text())
    result = run_process([sys.executable, "-c", _RACKET_CHECK, "task", "task", str(baseline)], tmp_path, timeout=2)
    assert result["exit_code"] != 0
    assert json.loads(result["stdout"])["passed"] is False


def test_racket_gate_uses_generator_id_when_rule_id_differs(tmp_path):
    (tmp_path / "arc_repl").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data/canonical").mkdir(parents=True)
    (tmp_path / "arc_repl/__init__.py").write_text("")
    (tmp_path / "scripts/__init__.py").write_text("")
    (tmp_path / "arc_repl/racket_bridge.py").write_text(
        "class RacketBridge:\n def eval_text(self, expression): return [[1]]\n def close(self): pass\n")
    (tmp_path / "scripts/rule_smoke.py").write_text(
        "from types import SimpleNamespace\n"
        "def rule_application(source, grid): return source\n"
        "def load_gen(task):\n assert task == 'generator-id'\n return SimpleNamespace(generate=lambda *a, **k: [[1]])\n"
        "def mirror_normalized(value): return value\n"
        "def arc_bounds_violation(value): return None\n"
        "def _norm_grid(value): return [[int(c) for c in row] if isinstance(row,str) else row for row in value]\n")
    canonical = tmp_path / "data/canonical/puzzles.jsonl"
    canonical.write_text(json.dumps({"task_id": "rule-id", "program_solution": "(rule! g)",
                                     "train": [{"input": ["1"], "output": ["1"]}],
                                     "test": {"input": ["1"], "output": ["1"]}}) + "\n")
    baseline = tmp_path / "baseline.jsonl"
    baseline.write_text(canonical.read_text())
    result = run_process([sys.executable, "-c", _RACKET_CHECK, "rule-id", "generator-id", str(baseline)], tmp_path, timeout=2)
    assert result["exit_code"] == 0
    report = json.loads(result["stdout"])
    assert report["passed"]
    assert len([item for item in report["checks"] if item["kind"] == "canonical"]) == 2
    assert [item["seed"] for item in report["checks"] if item["kind"] == "parity"] == [0, 1, 17]


def test_canonical_patch_cannot_change_another_task_row(library, tmp_path):
    mapping = library / "catalog/runtime_files.json"
    items = json.loads(mapping.read_text())
    items.append({"path": "shared/data/canonical/puzzles.jsonl", "target": "data/canonical/puzzles.jsonl"})
    mapping.write_text(json.dumps(items))
    canonical = "workspace/data/canonical/puzzles.jsonl"
    lines = (library / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
    changed = json.loads(lines[1])
    changed["written_solution"] = "unrelated edit"
    updated = [*lines]
    updated[1] = json.dumps(changed)
    patch = f"diff --git a/{canonical} b/{canonical}\n" + "\n".join(difflib.unified_diff(
        lines, updated, fromfile=f"a/{canonical}", tofile=f"b/{canonical}",
        lineterm="", n=1)) + "\n"
    root, assignment = returned(library, tmp_path, patch, patch_name="patches/racket.patch")
    result = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    assert result["status"] == "rejected_patch"
    assert "unrelated canonical row" in result["reason"]
