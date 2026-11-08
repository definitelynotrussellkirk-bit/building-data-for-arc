import json
import shutil
import zipfile
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main, draw_audit
from arcpuzzles.review_full_return import build_full_return
from arcpuzzles.review_full_collect import collect_full_returns


def _return(library, tmp_path, seed=0, audit=False, state="complete", edit=False, decision_text=None,
            feedback_text=None):
    question = library / "REVIEW/questions/q.json"
    question.parent.mkdir(parents=True, exist_ok=True)
    question.write_text(json.dumps({"schema": "arcpuzzles-review-question-v1", "id": "q",
        "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    built = build_full_packet(Catalog(library), library / "REVIEW", tmp_path / f"request-{seed}.zip")
    packet = tmp_path / f"packet-{seed}"
    packet.mkdir()
    with zipfile.ZipFile(built["zip"]) as archive:
        archive.extractall(packet)
    contract = draw_main(packet, seed.to_bytes(32, "big"))
    if edit:
        (packet / "repo/generators/aaaa00000003/generator.py").write_text("VERSION = '2.0'\n")
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (packet / name).write_text(name + "\n")
    if feedback_text is not None:
        (packet / "FEEDBACK_TO_CODEX.md").write_text(feedback_text)
    if decision_text is not None:
        (packet / "DECISIONS.md").write_text(decision_text)
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": state, "stopping_reason": "test"}))
    if audit:
        audit_contract = draw_audit(packet, bytes(32))
        (packet / "AUDIT.md").write_text("".join(
            f"## {row['task_id']}\nquestionable shortcut\n\n" for row in audit_contract["targets"]))
    result = build_full_return(packet, tmp_path / f"review_response_{seed}.zip")
    return contract, result


def test_collect_registers_offline_draw_without_precreated_assignment(library, tmp_path):
    contract, result = _return(library, tmp_path)
    assert not (library / "REVIEW/assignments" / contract["assignment_id"]).exists()
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    assert Path(collected["inbox"]).is_file()
    receipt = next(r for r in collected["receipts"] if r["zip_sha256"] == result["zip_sha256"])
    assert receipt["validation_status"] == "accepted"
    assert receipt["assignment_id"] == contract["assignment_id"]
    assert (library / "REVIEW/assignments" / contract["assignment_id"] / "ASSIGNMENT.json").is_file()
    assert (library / "var/review/returns/_inbox" / f"{result['zip_sha256']}.zip").is_file()


def test_batch_isolates_failures_duplicates_partial_and_audit(library, tmp_path):
    first, result = _return(library, tmp_path, audit=True)
    shutil.copy2(result["zip"], tmp_path / "review_response_duplicate.zip")
    second, partial = _return(library, tmp_path, seed=1, state="blocked")
    for seed in (2, 3, 4):
        _return(library, tmp_path, seed=seed)
    (tmp_path / "review_response_malformed.zip").write_bytes(b"not a zip")
    missing = tmp_path / "review_response_missing_packet.zip"
    with zipfile.ZipFile(result["zip"]) as source, zipfile.ZipFile(missing, "w") as target:
        for name in source.namelist():
            raw = source.read(name)
            if name == "ASSIGNMENT.json":
                value = json.loads(raw)
                value["packet_id"] = "0" * 64
                raw = json.dumps(value).encode()
            target.writestr(name, raw)
    (tmp_path / "ignore.txt").write_text("other")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    assert len(collected["receipts"]) == 8
    assert collected["counts"]["accepted"] >= 5
    assert collected["counts"]["malformed_zip"] == 1
    assert collected["counts"]["missing_packet"] == 1
    inbox = json.loads(Path(collected["inbox_json"]).read_text())
    assert {item["validation_status"] for item in inbox["invalid"]} == {"malformed_zip", "missing_packet"}
    assert "ignore.txt" in collected["ignored"]
    receipts = [r for r in collected["receipts"] if r["zip_sha256"] == result["zip_sha256"]]
    assert len(receipts) == 2 and receipts[0]["receipt_path"] == receipts[1]["receipt_path"]
    assert any(r["completion_status"] == "blocked" for r in collected["receipts"])
    assert any(r["audit_target"] == "aaaa00000001" for r in collected["receipts"])
    assert any(len(r.get("audit_targets", [])) == 2 for r in collected["receipts"])


def test_repeated_collect_is_idempotent(library, tmp_path):
    contract, result = _return(library, tmp_path)
    a = collect_full_returns(library / "REVIEW", tmp_path)
    b = collect_full_returns(library / "REVIEW", tmp_path)
    path = library / "REVIEW/assignments" / contract["assignment_id"] / "returns"
    assert len(list(path.glob("return-*.json"))) == 1
    assert a["receipts"][0]["receipt_path"] == b["receipts"][0]["receipt_path"]


def test_return_versions_allow_independent_approvals_without_return_identity(tmp_path):
    from arcpuzzles.review_full_collect import _next_return_version

    review_root = tmp_path / "REVIEW"
    review_root.mkdir()
    index = tmp_path / "generators/task/evidence/review_index.json"
    index.parent.mkdir(parents=True)
    identifier = "review-0123456789abcdef"
    index.write_text(json.dumps({
        "decisions": [{"return_id": None, "verification_status": "independently_checked"}],
        "audits": [{"return_id": identifier + ":v0002"}],
    }))
    (review_root / "suggestions.json").write_text(json.dumps({
        "items": [{"return_id": None, "request_id": None},
                  {"request_id": identifier + ":v0003:F1"}],
    }))

    assert _next_return_version(review_root, review_root / "returns", identifier,
                                {"task_id": "task"}) == 4


def test_collect_exposes_verified_intake_summary(library, tmp_path):
    _, result = _return(library, tmp_path, feedback_text="**F1: Show progress.**\n\nKeep stage logs.\n")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    receipt = next(row for row in collected["receipts"] if row["zip_sha256"] == result["zip_sha256"])
    assert receipt["intake_summary"]["feedback_items"] == [
        {"id": "F1", "text": "Show progress.\n\nKeep stage logs."}]
    assert receipt["intake_summary"]["verification_status"] == "reviewer_reported_requires_maintainer_replay"


def test_revised_return_after_compaction_keeps_distinct_audit_identity(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    from arcpuzzles.review_retention import compact_reviews

    contract, returned = _return(library, tmp_path, audit=True,
                                 feedback_text="**F1: First review.**\n")
    packet = tmp_path / "packet-0"
    audit = json.loads((packet / "AUDIT_ASSIGNMENT.json").read_text())
    sections = []
    for target in audit["targets"]:
        tid = target["task_id"]
        evidence = packet / f"checks/audit/{tid}/reproduction.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps({"task_id": tid, "finding": "questionable shortcut"}))
        sections.append(f"## {tid}\nQuestionable shortcut: `checks/audit/{tid}/reproduction.json`.\n")
    (packet / "AUDIT.md").write_text("\n".join(sections))
    Path(returned["zip"]).unlink()
    build_full_return(packet, Path(returned["zip"]))
    first = collect_full_returns(library / "REVIEW", tmp_path)["receipts"][0]
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "decision", "deferred", "Retain first round's audits.")
    compact_reviews(library, apply=True)
    assert not Path(first["archive_path"]).exists()
    old_assets = {
        path: path.read_bytes()
        for path in (library / "generators").glob(
            f"*/counterexamples/{contract['assignment_id']}-v0001/audit_assets.json")
    }
    assert len(old_assets) == 2
    Path(returned["zip"]).unlink(missing_ok=True)
    (tmp_path / "packet-0/FEEDBACK_TO_CODEX.md").write_text("**F1: Second review.**\n")
    build_full_return(tmp_path / "packet-0", tmp_path / "review_response_second.zip")
    second = collect_full_returns(library / "REVIEW", tmp_path)["receipts"][0]
    assert second["version"] == 2
    assert second["validation_status"] == "accepted"
    assert all(path.read_bytes() == raw for path, raw in old_assets.items())
