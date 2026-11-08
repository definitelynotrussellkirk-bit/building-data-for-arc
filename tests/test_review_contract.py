import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog, review


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_packet_binds_sources_and_orders_work(library, tmp_path):
    root = tmp_path / "REVIEW"
    (root / "questions").mkdir(parents=True)
    question = {"schema": "arcpuzzles-review-question-v1", "id": "q1", "version": 2,
                "owner": "ARCpuzzles", "text": "Which generator edge case remains?"}
    (root / "questions/q1.json").write_text(json.dumps(question))
    chosen = review.pick(Catalog(library), task_id="aaaa00000001", review_root=root, question_id="q1")
    folder = Path(chosen["directory"])
    contract = json.loads((folder / "ASSIGNMENT.json").read_text())
    assert contract["assignment_id"] == chosen["id"]
    assert contract["generator"]["sha256"] == digest(library / "generators/aaaa00000001/generator.py")
    assert contract["rule"]["task_id"] == "aaaa00000001"
    assert contract["rule"]["sha256"] == digest(library / "shared/data/canonical/puzzles.jsonl")
    assert contract["runtime_manifest_sha256"] == digest(folder / "workspace/RUNTIME_MANIFEST.json")
    assert contract["question"]["version"] == 2
    assert contract["question"]["sha256"] == digest(root / "questions/q1.json")
    request = (folder / "REQUEST.md").read_text().lower()
    assert request.index("iterate") < request.index("remaining failures") < request.index("answer the assigned question") < request.index("general feedback")
    assert (folder / "RESULTS.json").is_file()
    assert (folder / "REVIEW.md").is_file()
    assert (folder / "FEEDBACK_TO_CODEX.md").is_file()


def test_cohort_restricts_selection_and_detects_staleness(library, tmp_path):
    root = tmp_path / "REVIEW"
    cohort = tmp_path / "cohort"
    cohort.mkdir()
    row = {"generator_id": "aaaa00000002", "generator_sha256": digest(library / "generators/aaaa00000002/generator.py")}
    (cohort / "rows.jsonl").write_text(json.dumps(row) + "\n")
    sources = {name: digest(library / name) for name in
               ("catalog/puzzles.jsonl", "shared/data/canonical/puzzles.jsonl")}
    receipt = {"schema": "verified-unapproved-official-generator-review-v1",
               "rows_sha256": digest(cohort / "rows.jsonl"), "source_sha256": sources}
    (cohort / "receipt.json").write_text(json.dumps(receipt))
    chosen = review.pick(Catalog(library), review_root=root, cohort_receipt=cohort / "receipt.json")
    assert chosen["task_id"] == "aaaa00000002"
    contract = json.loads((Path(chosen["directory"]) / "ASSIGNMENT.json").read_text())
    assert contract["cohort"]["rows_sha256"] == receipt["rows_sha256"]
    assert contract["cohort"]["eligible_count"] == 1
    assert "receipt_path" not in contract["cohort"]
    (cohort / "rows.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="cohort"):
        review.pick(Catalog(library), review_root=tmp_path / "other", cohort_receipt=cohort / "receipt.json")
    assert not list((tmp_path / "other").glob("assignments/*"))


def test_source_change_during_preparation_releases_claim(library, tmp_path, monkeypatch):
    original = review.prepare_runtime
    def changed(catalog, destination, task_id):
        receipt = original(catalog, destination, task_id)
        (library / "generators/aaaa00000001/generator.py").write_text("VERSION = 'changed'\n")
        return receipt
    monkeypatch.setattr(review, "prepare_runtime", changed)
    root = tmp_path / "REVIEW"
    with pytest.raises(RuntimeError, match="changed"):
        review.pick(Catalog(library), task_id="aaaa00000001", review_root=root)
    assert review.assignments(root)[0]["status"] == "preparation_failed"
