import json
from pathlib import Path

from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_inbox import build_full_inbox, compile_task_review_index, _receipts
from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_candidate import check_full_candidate
from test_review_full_collect import _return


def test_later_audit_and_merge_decisions_do_not_accept_deferred_generator(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path, audit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    for kind, status, reason in (
        ("generator", "accepted", "Earlier decision."),
        ("generator", "deferred", "Whole candidate deferred; selected improvements merged separately."),
        ("audit", "accepted", "Retain audit findings."),
        ("decision", "accepted", "Separate merged-source approval."),
    ):
        record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                                kind, status, reason)
    index = compile_task_review_index(library / "REVIEW", contract["task_id"])
    assert index["decisions"] == []
    assert _receipts(library / "REVIEW")[0]["disposition_status"] == "deferred"
    audit = compile_task_review_index(library / "REVIEW", "aaaa00000001")["audits"][0]
    assert audit["triage"]["status"] == "accepted"
    assert audit["resolution"] == "needs_triage"


def test_audit_only_disposition_leaves_generator_unreviewed(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path, audit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "audit", "accepted", "Audit triage only.")
    index = compile_task_review_index(library / "REVIEW", contract["task_id"])
    assert index["decisions"] == []
    assert _receipts(library / "REVIEW")[0]["disposition_status"] == "unreviewed"


def test_legacy_whole_candidate_deferral_survives_later_audit(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path, audit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "decision", "deferred", "Competing whole candidate retained.")
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "audit", "accepted", "Audit findings retained independently.")
    index = compile_task_review_index(library / "REVIEW", contract["task_id"])
    assert index["decisions"] == []
    assert _receipts(library / "REVIEW")[0]["disposition_status"] == "deferred"


def test_latest_generator_disposition_overrides_old_integration_status(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path)
    collect_full_returns(library / "REVIEW", tmp_path)
    evidence = library / "generators" / contract["task_id"] / "evidence" / (
        f"review-{contract['assignment_id']}-v0001.json")
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps({"disposition": "accepted", "verification_status": "reviewer_reported"}))
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "generator", "deferred", "Later whole-candidate decision.")
    decision = _receipts(library / "REVIEW")[0]
    assert compile_task_review_index(library / "REVIEW", contract["task_id"])["decisions"] == []
    assert decision["disposition_status"] == "deferred"
    assert decision["verification_status"] == "reviewer_reported"


def test_inbox_groups_collision_and_links_originals(library, tmp_path):
    _return(library, tmp_path, seed=2, edit=True)
    _return(library, tmp_path, seed=5, edit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    result = build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    data = json.loads(Path(result["json"]).read_text())
    group = data["generators"]["aaaa00000003"]
    assert len(group) == 2
    assert all(Path(row["archive_path"]).is_file() for row in group)
    assert all(row["disposition_status"] == "unreviewed" for row in group)


def test_open_audits_but_no_return_narrative_travel_in_next_packet(library, tmp_path):
    _return(library, tmp_path, seed=2, audit=True, state="blocked")
    _return(library, tmp_path, seed=1, audit=True, state="complete")
    collect_full_returns(library / "REVIEW", tmp_path)
    main_index = compile_task_review_index(library / "REVIEW", "aaaa00000003")
    audit_index = compile_task_review_index(library / "REVIEW", "aaaa00000001")
    assert main_index["decisions"] == []
    assert len(audit_index["audits"]) == 2
    assert all(row["text"].startswith("## aaaa00000001") for row in audit_index["audits"])
    build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    fresh = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "next.zip")
    import zipfile
    with zipfile.ZipFile(fresh["zip"]) as packet:
        assert "repo/generators/aaaa00000003/evidence/review_index.json" in packet.namelist()
        assert "DECISIONS" not in packet.read("repo/generators/aaaa00000003/evidence/review_index.json").decode()


def test_inbox_rebuild_is_deterministic_and_escapes_review_text(library, tmp_path):
    _return(library, tmp_path, decision_text="<script>alert('bad')</script>\n")
    collect_full_returns(library / "REVIEW", tmp_path)
    # The inbox must treat all captured reviewer prose as data.
    first = build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    before = (Path(first["json"]).read_bytes(), Path(first["html"]).read_bytes())
    assert "<script>" not in before[1].decode()
    assert "&lt;script&gt;" in before[1].decode()
    second = build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    assert before == (Path(second["json"]).read_bytes(), Path(second["html"]).read_bytes())


def test_inbox_exposes_current_requests_without_mixing_reviewer_answers(library, tmp_path):
    from arcpuzzles.review_notes import REQUEST_SCHEMA
    requests = {"schema": REQUEST_SCHEMA, "items": [
        {"request_id": "tool:first", "status": "deferred", "generator_id": "aaaa00000001",
         "text": "Find exact replay data\n\n<script>alert('unsafe')</script>",
         "reason": "Keep original evidence.", "assets_manifest": {"path": "shared/tools/proposals/demo/manifest.json"},
         "owner_tool_review": {"status": "not_selected", "scope": "Static only."}},
        {"request_id": "tool:done", "status": "implemented", "text": "Already implemented", "reason": "Tested."},
        {"request_id": "question:aaaa00000001:x", "status": "proposed", "text": "A reviewer answer", "reason": None},
        {"request_id": "tool:bad-link", "status": "needs_evidence", "text": "Missing proposal",
         "reason": None, "assets_manifest": {"path": "javascript:alert(1)"}},
    ]}
    source = library / 'REVIEW/suggestions.json'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(requests))
    (library / 'generators/aaaa00000001/notes.md').write_text('Current generator notes.\n')
    manifest = library / 'shared/tools/proposals/demo/manifest.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{}')
    before = source.read_bytes()
    out = library / 'var/review/full-inbox'
    result = build_full_inbox(library / 'REVIEW', out)
    data = json.loads(Path(result['json']).read_text())
    assert data['counts']['tool_requests'] == 3
    assert data['counts']['open_tool_requests'] == 2
    assert data['counts']['reviewer_answers'] == 1
    page = Path(result['html']).read_text()
    assert 'Current tool requests' in page and 'Reviewer answers' in page
    assert '<details' in page and 'Find exact replay data' in page
    assert '&lt;script&gt;' in page and '<script>' not in page
    assert 'not_selected' in page and 'Static only.' in page
    assert 'href="../../../shared/tools/proposals/demo/manifest.json"' in page
    assert 'href="../../../generators/aaaa00000001/notes.md"' in page
    assert 'href="../../../REVIEW/suggestions.json"' in page
    assert 'href="javascript:' not in page
    assert 'Unavailable evidence' in page
    assert {row['request_id']: row for row in json.loads(source.read_text())['items']} == {
        row['request_id']: row for row in json.loads(before)['items']}
    assert "id='audits'" in page


def test_inbox_folds_only_identical_prose_and_preserves_separate_decisions(library):
    from arcpuzzles.review_notes import REQUEST_SCHEMA
    text = "Improve replay\n\nAn exact shared request body."
    rows = [
        {"request_id": "tool:one", "status": "deferred", "text": text,
         "generator_id": "aaaa00000001", "reason": "Needs source binding.",
         "source_sha256": "a" * 64},
        {"request_id": "tool:two", "status": "deferred", "text": text,
         "generator_id": "aaaa00000002", "reason": "Needs relocation checks.",
         "source_sha256": "b" * 64},
        {"request_id": "tool:other-status", "status": "implemented", "text": text,
         "reason": "Qualified separately."},
    ]
    source = library / 'REVIEW/suggestions.json'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps({"schema": REQUEST_SCHEMA, "items": rows}))
    result = build_full_inbox(library / 'REVIEW', library / 'var/review/full-inbox')
    page = Path(result['html']).read_text()
    assert page.count('<pre>' + text + '</pre>') == 2
    assert 'same text in 2 requests; decisions remain separate' in page
    for row in rows:
        assert row['request_id'] in page
        assert row['reason'] in page
    assert 'a' * 64 in page and 'b' * 64 in page
    assert {row['request_id']: row for row in json.loads(source.read_text())['items']} == {
        row['request_id']: row for row in rows}


def test_inbox_reads_latest_check_receipt(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    checked = check_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"], 1, timeout=2)
    inbox = build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    data = json.loads(Path(inbox["json"]).read_text())
    assert data["generators"][contract["task_id"]][0]["check_status"] == checked["status"]


def test_old_source_audit_remains_actionable_with_original_hash(library, tmp_path):
    _return(library, tmp_path, audit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    (library / "generators/aaaa00000001/generator.py").write_text("VERSION = 'new'\n")
    index = compile_task_review_index(library / "REVIEW", "aaaa00000001")
    assert index["audits"][0]["resolution"] == "needs_triage"
    assert index["current_source_sha256"] != index["audits"][0]["source_sha256"]


def test_tool_feedback_and_disposition_travel_with_task_context(library, tmp_path):
    contract, _ = _return(library, tmp_path, feedback_text="## F1: Better probe\nReproducer retained.\n")
    collect_full_returns(library / "REVIEW", tmp_path)
    ledger = library / "REVIEW/assignments" / contract["assignment_id"] / "feedback-0001.json"
    ledger.write_text(json.dumps({"schema": "arcpuzzles-review-feedback-v1", "items": {
        "F1": [{"id": "F1", "status": "implemented", "reason": "Shared probe added."}]}}))
    build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    items = json.loads((library / "REVIEW/suggestions.json").read_text())["items"]
    assert len(items) == 1
    assert "Reproducer retained." in items[0]["text"]
    assert items[0]["status"] == "implemented"


def test_audit_triage_survives_packet_transport_without_claiming_verification(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path, audit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "audit", "accepted", "Current-source repair lead; reviewer-reported.")
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "generator", "deferred", "Not an audit decision.")
    index = compile_task_review_index(library / "REVIEW", "aaaa00000001")
    audit = index["audits"][0]
    assert audit["verification_status"] == "reviewer_reported"
    assert audit["triage"] == {"status": "accepted",
        "reason": "Current-source repair lead; reviewer-reported."}
    (library / "generators/aaaa00000001/generator.py").write_text("VERSION = 'new'\n")
    updated = compile_task_review_index(library / "REVIEW", "aaaa00000001")
    old = updated["audits"][0]
    assert old["source_sha256"] != updated["current_source_sha256"]
    assert old["resolution"] == "needs_triage"
    assert old["triage"] == audit["triage"]
    build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    fresh = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / "next.zip")
    import zipfile
    with zipfile.ZipFile(fresh["zip"]) as packet:
        transported = json.loads(packet.read("repo/generators/aaaa00000001/evidence/review_index.json"))
    assert transported["audits"][0]["triage"] == audit["triage"]
