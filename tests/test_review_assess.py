import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles import Catalog, review
from arcpuzzles.review_candidate import check_candidate
from arcpuzzles.review_return import intake
from arcpuzzles.review_assess import assess, integrate, record_feedback
import arcpuzzles.review_assess as review_assess


def returned(library, tmp_path, *, patch=None, feedback="F1: Better focused tooling would help.\n",
             question=None):
    root = tmp_path / "REVIEW"
    if question:
        (root / "questions").mkdir(parents=True)
        (root / "questions/q1.json").write_text(json.dumps({"schema": "arcpuzzles-review-question-v1",
            "id": "q1", "version": 3, "owner": "ARC2HQ", "text": "What should change?"}))
    assignment = review.pick(Catalog(library), task_id="aaaa00000001", review_root=root,
                             question_id="q1" if question else None)
    contract = (Path(assignment["directory"]) / "ASSIGNMENT.json").read_bytes()
    patches = ["patches/generator.patch"] if patch else []
    results = {"schema": "arcpuzzles-review-results-v1", "assignment_id": assignment["id"],
               "generator_id": assignment["task_id"], "completion_state": "complete",
               "changed_components": ["generator"] if patch else [], "patches": patches,
               "checks": [], "remaining_failures": [], "improvement_claim": "Improved edge case"}
    if question:
        results["question_answer"] = "QUESTION_ANSWER.json"
    archive = tmp_path / "return.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for name, value in {"ASSIGNMENT.json": contract, "RESULTS.json": json.dumps(results),
                            "REVIEW.md": "Reviewed findings\n", "FEEDBACK_TO_CODEX.md": feedback}.items():
            handle.writestr(name, value)
        if patch:
            handle.writestr(patches[0], patch)
        if question:
            handle.writestr("QUESTION_ANSWER.json", json.dumps({"answer": "Try focused distribution checks"}))
    assert intake(root, archive)["status"] == "accepted"
    return root, assignment


def generator_patch():
    path = "workspace/puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            "@@ -1 +1 @@\n-VERSION = '1.0.0'\n+VERSION = '2.0.0'\n")


def test_no_patch_return_is_assessable_and_closable(library, tmp_path):
    root, assignment = returned(library, tmp_path)
    report = assess(root, assignment["id"], 1)
    assert report["status"] == "no_changes"
    assert report["feedback_items"][0]["id"] == "F1"
    closed = review.finish(root, assignment["id"], status="completed", note="Findings read")
    assert closed["status"] == "completed"
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '1.0.0'\n"


def test_completed_close_requires_assessment(library, tmp_path):
    root, assignment = returned(library, tmp_path)
    with pytest.raises(ValueError, match="assess"):
        review.finish(root, assignment["id"], status="completed", note="Too early")


def test_completed_close_requires_latest_return_assessment(library, tmp_path):
    root, assignment = returned(library, tmp_path)
    assess(root, assignment["id"], 1)
    contract = (Path(assignment["directory"]) / "ASSIGNMENT.json").read_bytes()
    first = Path(root.parent / "var/review/returns" / assignment["id"] / "0001/extracted/RESULTS.json")
    results = json.loads(first.read_text())
    results["improvement_claim"] = "Updated findings"
    archive = tmp_path / "second.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("ASSIGNMENT.json", contract)
        handle.writestr("RESULTS.json", json.dumps(results))
        handle.writestr("REVIEW.md", "More findings\n")
        handle.writestr("FEEDBACK_TO_CODEX.md", "F1: Updated tooling idea\n")
    assert intake(root, archive)["version"] == 2
    with pytest.raises(ValueError, match="latest"):
        review.finish(root, assignment["id"], status="completed", note="Only v1 assessed")


def test_source_drift_blocks_integration(library, tmp_path):
    root, assignment = returned(library, tmp_path, patch=generator_patch())
    checked = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    checked["status"] = "passed"  # isolate integration behavior from absent fixture battery
    Path(checked["receipt_path"]).write_text(json.dumps(checked))
    (library / "generators/aaaa00000001/generator.py").write_text("VERSION = '3.0.0'\n")
    report = assess(root, assignment["id"], 1)
    assert "source_drift" in report["blockers"]
    assert report["check_comparison"]["baseline_battery"] is False
    assert report["check_comparison"]["candidate_battery"] is False
    with pytest.raises(ValueError, match="drift"):
        integrate(Catalog(library), root, assignment["id"], 1, {"generator"})
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '3.0.0'\n"


def test_selecting_only_generator_preserves_rule_and_review_hash(library, tmp_path):
    root, assignment = returned(library, tmp_path, patch=generator_patch())
    checked = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    checked["status"] = "passed"
    Path(checked["receipt_path"]).write_text(json.dumps(checked))
    before_rule = (library / "shared/data/canonical/puzzles.jsonl").read_bytes()
    before_catalog = (library / "catalog/puzzles.jsonl").read_bytes()
    assess(root, assignment["id"], 1)
    result = integrate(Catalog(library), root, assignment["id"], 1, {"generator"})
    assert result["status"] == "integrated"
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '2.0.0'\n"
    assert (library / "shared/data/canonical/puzzles.jsonl").read_bytes() == before_rule
    assert (library / "catalog/puzzles.jsonl").read_bytes() == before_catalog
    assert Path(result["evidence_path"]).is_file()


def test_candidate_mutation_after_check_blocks_integration(library, tmp_path):
    root, assignment = returned(library, tmp_path, patch=generator_patch())
    checked = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    checked["status"] = "passed"
    Path(checked["receipt_path"]).write_text(json.dumps(checked))
    assess(root, assignment["id"], 1)
    candidate_file = Path(checked["candidate_path"]) / "workspace/puzzle_generators/per_puzzle/aaaa00000001/generator.py"
    candidate_file.write_text("VERSION = 'malicious'\n")
    with pytest.raises(ValueError, match="candidate"):
        integrate(Catalog(library), root, assignment["id"], 1, {"generator"})
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '1.0.0'\n"


def test_evidence_write_failure_rolls_back_selected_source(library, tmp_path, monkeypatch):
    root, assignment = returned(library, tmp_path, patch=generator_patch())
    checked = check_candidate(Catalog(library), root, assignment["id"], 1, timeout=2)
    checked["status"] = "passed"
    Path(checked["receipt_path"]).write_text(json.dumps(checked))
    assess(root, assignment["id"], 1)
    original = Path.write_text
    def fails_evidence(path, *args, **kwargs):
        if "evidence" in path.parts and path.name.startswith("review-review-"):
            raise OSError("simulated evidence failure")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "write_text", fails_evidence)
    with pytest.raises(OSError, match="evidence failure"):
        integrate(Catalog(library), root, assignment["id"], 1, {"generator"})
    assert (library / "generators/aaaa00000001/generator.py").read_text() == "VERSION = '1.0.0'\n"


def test_question_answer_and_feedback_keep_owner_and_reason(library, tmp_path):
    root, assignment = returned(library, tmp_path, question=True)
    report = assess(root, assignment["id"], 1)
    assert report["question_answer"]["owner"] == "ARC2HQ"
    assert report["question_answer"]["version"] == 3
    with pytest.raises(ValueError, match="reason"):
        record_feedback(root, assignment["id"], 1, "F1", "accepted", "")
    disposition = record_feedback(root, assignment["id"], 1, "F1", "needs_evidence", "Needs a measured example")
    assert disposition["status"] == "needs_evidence"


def test_relocated_packet_can_return_without_sibling_paths(library, tmp_path):
    root = tmp_path / "REVIEW"
    assignment = review.pick(Catalog(library), task_id="aaaa00000001", review_root=root)
    packet = review.pack(root, assignment["id"], tmp_path / "request.zip")
    relocated = tmp_path / "elsewhere" / "packet"
    relocated.mkdir(parents=True)
    with zipfile.ZipFile(packet) as handle:
        handle.extractall(relocated)
    contract = json.loads((relocated / "ASSIGNMENT.json").read_text())
    assert "catalog_root" not in contract
    assert (relocated / "workspace" / contract["generator"]["runtime_path"]).is_file()
    results = json.loads((relocated / "RESULTS.json").read_text())
    results["completion_state"] = "complete"
    results["improvement_claim"] = "No safe change; findings recorded"
    (relocated / "RESULTS.json").write_text(json.dumps(results))
    returned_zip = tmp_path / "elsewhere" / "response.zip"
    with zipfile.ZipFile(returned_zip, "w") as handle:
        for name in ("ASSIGNMENT.json", "RESULTS.json", "REVIEW.md", "FEEDBACK_TO_CODEX.md"):
            handle.write(relocated / name, name)
    assert intake(root, returned_zip)["status"] == "accepted"
    assert assess(root, assignment["id"], 1)["status"] == "no_changes"
