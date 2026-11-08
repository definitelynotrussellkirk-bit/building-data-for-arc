import json

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_notes import audit_state, migrate_notes, record_audit_status, compact_task_state
from arcpuzzles.review_full_return import _allowed
from arcpuzzles.review_full_integrate import _component


def _index(task_id):
    return {"schema": "arcpuzzles-task-review-index-v2", "task_id": task_id,
            "decisions": [{"return_id": "review-one:v0001", "source_sha256": "old",
                "feedback": "F1: Better shape diagnostics.\nInclude row lengths.",
                "feedback_dispositions": {"F1": [
                    {"status": "accepted", "reason": "Useful."},
                    {"status": "deferred", "reason": "Needs a design."}]}}],
            "audits": [{"return_id": "review-other:v0001", "source_sha256": "old",
                        "text": "Shape mismatch", "historical": True}]}


def test_migration_preserves_current_audits_and_compacts_suggestions(library):
    task_id = "aaaa00000001"
    old = library / "REVIEW/task_indexes" / f"{task_id}.json"
    old.parent.mkdir(parents=True)
    raw = json.dumps(_index(task_id)).encode()
    old.write_bytes(raw)
    assert migrate_notes(library)["indexes_to_move"] == 1
    assert old.exists()
    assert migrate_notes(library, apply=True)["suggestion_rows_changed"] == 1
    new = library / f"generators/{task_id}/evidence/review_index.json"
    assert json.loads(new.read_text())["schema"] == "arcpuzzles-task-review-current-v1"
    assert not old.exists()
    events = (library / "REVIEW/suggestions.json").read_bytes()
    assert migrate_notes(library, apply=True)["suggestion_rows_changed"] == 0
    assert (library / "REVIEW/suggestions.json").read_bytes() == events
    assert json.loads(new.read_text())["audits"][0]["text"] == "Shape mismatch"


def test_migration_conflict_is_preflighted_before_any_move(library):
    old = library / "REVIEW/task_indexes/aaaa00000001.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps(_index("aaaa00000001")))
    target = library / "generators/aaaa00000001/evidence/review_index.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({**_index("aaaa00000001"), "decisions": []}))
    with pytest.raises(ValueError, match="Conflicting"):
        migrate_notes(library, apply=True)
    assert old.exists()
    assert not (library / "REVIEW/suggestions.json").exists()


def test_audit_flag_requires_explicit_resolution_and_can_be_reopened(library):
    task_id = "aaaa00000001"
    path = library / f"generators/{task_id}/evidence/review_index.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_index(task_id)))
    assert audit_state(library, task_id)["audit_pending_triage_count"] == 1
    assert Catalog(library).describe(task_id)["audit_unresolved"]
    assert [r["id"] for r in Catalog(library).query(audit_unresolved=True)] == [task_id]
    record_audit_status(library, task_id, "review-other:v0001", "resolved", "test_shape covers it")
    assert not Catalog(library).describe(task_id)["audit_unresolved"]
    assert json.loads(path.read_text())["audits"] == []
    # Reopening requires a concrete source-bound finding, not an archived event.
    reopened = _index(task_id)
    reopened["audits"][0].update(text="New failing witness", resolution="unresolved")
    compact_task_state(library, task_id, reopened, apply=True)
    assert Catalog(library).describe(task_id)["audit_unresolved"]
    assert not (path.parent / "audit_dispositions.jsonl").exists()
    with pytest.raises(ValueError, match="existing task audit"):
        record_audit_status(library, task_id, "missing:v0001", "no_issue", "Checked")


def test_notes_have_one_source_and_counterexamples_are_task_scoped(library):
    tid = "aaaa00000001"
    (library / f"generators/{tid}/notes.md").write_text("Current rule; open limit.")
    row = Catalog(library).get(tid)
    assert row["notes"] == row["working_notes"] == "Current rule; open limit."
    path = f"repo/generators/{tid}/counterexamples/shape.json"
    assert _allowed(path, {"task_id": tid, "baseline_sha256": {}})
    assert _component(path, tid) == "tests_notes"
    assert not _allowed(path.replace(tid, "aaaa00000002"), {"task_id": tid, "baseline_sha256": {}})
    assert not _allowed(f"repo/generators/{tid}/evidence/audit_dispositions.jsonl", {"task_id": tid, "baseline_sha256": {}})


def test_inbox_routes_both_audits_to_their_targets_and_retries_without_duplicate_requests(library, tmp_path):
    from test_review_full_collect import _return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_inbox import build_full_inbox
    contract, _ = _return(library, tmp_path, audit=True, feedback_text="F1: Add shape diagnostics.")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    targets = collected["receipts"][0]["audit_targets"]
    assert len(targets) == 2
    build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    for tid in targets:
        record = json.loads((library / f"generators/{tid}/evidence/review_index.json").read_text())
        assert record["task_id"] == tid and len(record["audits"]) == 1
        assert record["audits"][0]["return_id"] == contract["assignment_id"] + ":v0001"
    requests = (library / "REVIEW/suggestions.json").read_bytes()
    build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    assert (library / "REVIEW/suggestions.json").read_bytes() == requests


def test_old_index_audit_flag_is_visible_before_migration(library):
    old = library / "REVIEW/task_indexes/aaaa00000001.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps(_index("aaaa00000001")))
    assert Catalog(library).describe("aaaa00000001")["audit_unresolved"]
