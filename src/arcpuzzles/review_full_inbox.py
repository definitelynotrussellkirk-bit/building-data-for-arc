"""Render current task findings and fresh pending reviewer returns."""
from __future__ import annotations

import html
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
import zipfile

from .review_full_return import audit_sections
from .review_curriculum import retained_curriculum
from .review_notes import (append_suggestions, index_path, suggestion_events,
                           read_index, compact_task_state, validate_proposal_assets)
from .catalog import local_path, sha256, jsonl
from .review_targets import MULTI_SCHEMA, assignment_targets, target_ids


def _receipts(review_root: Path) -> list[dict]:
    paths = sorted((review_root / "assignments").glob("*/returns/return-*.json"))
    rows = []
    for path in paths:
        receipt = json.loads(path.read_text())
        if receipt.get("retention_status") == "extracted":
            continue
        if receipt.get("schema") != "arcpuzzles-full-return-receipt-v2":
            continue
        assignment = review_root / "assignments" / receipt["assignment_id"]
        check_path = review_root.parent / "var/review/full-checks" / receipt["assignment_id"] / (
            f"{receipt['version']:04d}/result.json")
        if check_path.is_file():
            receipt["check_status"] = json.loads(check_path.read_text())["status"]
            receipt["check_receipt"] = str(check_path)
        dispositions = assignment / f"dispositions-{receipt['version']:04d}.json"
        receipt["dispositions"] = json.loads(dispositions.read_text())["items"] if dispositions.is_file() else []
        feedback = assignment / f"feedback-{receipt['version']:04d}.json"
        receipt["feedback_dispositions"] = json.loads(feedback.read_text())["items"] if feedback.is_file() else {}
        evidence = review_root.parent / "generators" / receipt["task_id"] / "evidence" / (
            f"review-{receipt['assignment_id']}-v{receipt['version']:04d}.json")
        receipt["disposition_status"] = "unreviewed"
        if evidence.is_file():
            receipt["integration_evidence"] = str(evidence)
            integrated = json.loads(evidence.read_text())
            receipt["disposition_status"] = integrated.get("disposition", "accepted")
            receipt["verification_status"] = integrated.get("verification_status", "see_retained_check")
        # Audit triage and approval of a separately merged source do not accept
        # this whole candidate. The latest generator decision takes precedence.
        generator_decision = next((item for item in reversed(receipt["dispositions"])
                                   if item.get("kind") == "generator"), None)
        if generator_decision is not None:
            receipt["disposition_status"] = generator_decision["status"]
        elif not evidence.is_file():
            # Legacy collision records used a whole-candidate decision rather
            # than a generator item. Keep explicit nonacceptance; a generic
            # acceptance cannot prove this candidate was integrated.
            decision = next((item for item in reversed(receipt["dispositions"])
                             if item.get("kind") == "decision" and item.get("status") in
                             {"deferred", "rejected", "needs_evidence"}), None)
            if decision is not None:
                receipt["disposition_status"] = decision["status"]
        contract_path = assignment/'ASSIGNMENT.json'
        contract = json.loads(contract_path.read_text()) if contract_path.is_file() else {}
        if contract.get('schema') == MULTI_SCHEMA:
            receipt['task_ids'] = target_ids(contract)
            receipt['repair_targets'] = assignment_targets(contract)
            receipt['repair_dispositions'] = {}
            for target_row in assignment_targets(contract):
                tid = target_row['task_id']
                target_evidence = review_root.parent/'generators'/tid/'evidence'/(
                    f"review-{receipt['assignment_id']}-v{receipt['version']:04d}.json")
                item = json.loads(target_evidence.read_text()) if target_evidence.is_file() else {}
                disposition = item.get('disposition', 'unreviewed')
                if generator_decision is not None and generator_decision['status'] != 'accepted':
                    disposition = generator_decision['status']
                receipt['repair_dispositions'][tid] = {
                    'disposition_status': disposition,
                    'integration_evidence': str(target_evidence) if target_evidence.is_file() else None,
                    'verification_status': item.get('verification_status', 'unverified')}
            states = {r['disposition_status'] for r in receipt['repair_dispositions'].values()}
            receipt['disposition_status'] = ('unreviewed' if 'unreviewed' in states else
                'needs_evidence' if states & {'needs_evidence', 'deferred', 'rejected'} else 'accepted')
        rows.append(receipt)
    return rows


def _returned_text(receipt: dict, name: str) -> str | None:
    with zipfile.ZipFile(receipt["archive_path"]) as archive:
        if name not in archive.namelist():
            return None
        return archive.read(name).decode("utf-8", errors="replace")


def _incoming_task_index(review_root: Path, task_id: str, *, receipts: list[dict] | None = None) -> dict:
    review_root = review_root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task_id):
        raise ValueError("Invalid task ID")
    current_generator = review_root.parent / "generators" / task_id / "generator.py"
    current_hash = hashlib.sha256(current_generator.read_bytes()).hexdigest() if current_generator.is_file() else None
    decisions, audits, solves, source_hashes, dispositions = [], [], [], {}, {}
    for receipt in (_receipts(review_root) if receipts is None else receipts):
        if receipt["validation_status"] != "accepted":
            continue
        key = f"{receipt['assignment_id']}:v{receipt['version']:04d}"
        if task_id in receipt.get('repair_dispositions', {}):
            receipt = dict(receipt, **receipt['repair_dispositions'][task_id])
        if receipt.get("task_id") == task_id or task_id in receipt.get('task_ids', []):
            with zipfile.ZipFile(receipt["archive_path"]) as archive:
                contract = json.loads(archive.read("ASSIGNMENT.json"))
                if receipt.get('task_id') == task_id and "solve/summary.json" in archive.namelist():
                    solves.append({"return_id": key, "packet_id": receipt["packet_id"],
                        "summary": json.loads(archive.read("solve/summary.json")),
                        "work_log": archive.read("solve/SOLVE_NOTES.md").decode("utf-8")})
            target_contract = next(row for row in assignment_targets(contract) if row['task_id'] == task_id)
            source_hashes[key] = target_contract['generator']['generator_sha256']
            decisions.append({"return_id": key, "packet_id": receipt["packet_id"],
                              "source_sha256": source_hashes[key], "completion": receipt["completion_status"],
                              "historical": source_hashes[key] != current_hash,
                              "validation": receipt["validation_status"],
                              "disposition": receipt.get("disposition_status", "unreviewed"),
                              "verification_status": receipt.get("verification_status", "unverified"),
                              "archive_path": receipt["archive_path"],
                              "text": _returned_text(receipt, "DECISIONS.md"),
                              "review": _returned_text(receipt, "REVIEW.md"),
                              "feedback": (_returned_text(receipt, "FEEDBACK_TO_CODEX.md")
                                           if receipt.get('task_id') == task_id else None),
                              "feedback_dispositions": receipt.get("feedback_dispositions", {})})
            if 'supplementary_tickets' in receipt:
                decisions[-1]['supplementary_tickets'] = receipt['supplementary_tickets']
            curriculum = retained_curriculum(receipt, review_root.parent)
            if curriculum is not None:
                decisions[-1]["curriculum"] = curriculum
            dispositions[key] = receipt.get("disposition_status", "unreviewed")
        targets = receipt.get("audit_targets") or ([receipt["audit_target"]] if receipt.get("audit_target") else [])
        if task_id in targets:
            with zipfile.ZipFile(receipt["archive_path"]) as archive:
                audit = json.loads(archive.read("AUDIT_ASSIGNMENT.json"))
            if audit["schema"] in {"arcpuzzles-full-audit-v3", "arcpuzzles-full-audit-v4"}:
                source_hash = next(row["generator_sha256"] for row in audit["targets"]
                                   if row["task_id"] == task_id)
                finding = audit_sections(_returned_text(receipt, "AUDIT.md") or "")[task_id]
            else:
                source_hash = audit["generator_sha256"]
                finding = _returned_text(receipt, "AUDIT.md")
            audit_record = {"return_id": key, "packet_id": receipt["packet_id"],
                           "source_sha256": source_hash,
                           "historical": source_hash != current_hash,
                           "disposition": "unverified", "archive_path": receipt["archive_path"],
                           "text": finding}
            assets = local_path(review_root.parent,
                f"generators/{task_id}/counterexamples/{receipt['assignment_id']}-v{receipt['version']:04d}/audit_assets.json")
            if assets.is_file():
                evidence = json.loads(assets.read_text())
                if (evidence.get("task_id") != task_id or evidence.get("return_id") != key
                        or evidence.get("audited_generator_sha256") != source_hash
                        or evidence.get("zip_sha256") != receipt["zip_sha256"]):
                    raise ValueError(f"Audit assets identity differs: {assets}")
                for item in evidence["files"]:
                    if not item["path"].startswith(f"generators/{task_id}/counterexamples/"):
                        raise ValueError("Audit asset outside its generator")
                    path = local_path(review_root.parent, item["path"])
                    if not path.is_file() or sha256(path) != item["sha256"]:
                        raise ValueError(f"Missing or changed retained witness: {item['path']}")
                audit_record["assets_manifest"] = assets.relative_to(review_root.parent).as_posix()
                audit_record["assets_manifest_sha256"] = sha256(assets)
            triage = [item for item in receipt.get("dispositions", []) if item.get("kind") == "audit"]
            if triage:
                audit_record["maintainer_dispositions"] = triage
            resolution = receipt.get("audit_resolutions", {}).get(task_id)
            if resolution and resolution.get("source_sha256") == source_hash:
                audit_record.update(resolution=resolution["status"], resolution_reason=resolution["reason"])
            audits.append(audit_record)
    record = {"schema": "arcpuzzles-task-review-index-v2", "task_id": task_id,
              "current_source_sha256": current_hash,
              "decisions": decisions, "audits": audits,
              "source_hashes": source_hashes, "dispositions": dispositions}
    if solves:
        record["solves"] = solves
    return record



def _merge_current(review_root: Path, task_id: str, incoming: dict, *, catalog_records=None) -> dict:
    base = read_index(review_root.parent, task_id)
    audits = {(row["return_id"], row["source_sha256"]): dict(row) for row in base["audits"]}
    for row in incoming["audits"]:
        key = row["return_id"], row["source_sha256"]
        prior = audits.get(key, {})
        audits[key] = {**prior, **row}
        # Intake prose cannot overwrite maintainer status or extracted assets.
        for field in ("resolution", "resolution_reason", "assets_manifest", "assets_manifest_sha256"):
            if field in prior and field not in row:
                audits[key][field] = prior[field]
    return compact_task_state(review_root.parent, task_id,
                              {**base, "audits": list(audits.values())}, catalog_records=catalog_records)


def compile_task_review_index(review_root: Path, task_id: str, *, receipts: list[dict] | None = None) -> dict:
    """Current source-bound state, retaining findings when archived returns are gone."""
    review_root = review_root.resolve()
    incoming = _incoming_task_index(review_root, task_id, receipts=receipts)
    return _merge_current(review_root, task_id, incoming)


def _artifact_link(owner: Path, out: Path, relative: str, label: str) -> str:
    try:
        path = local_path(owner, relative)
        if not path.is_file():
            raise ValueError("Missing artifact")
    except (ValueError, OSError):
        return "Unavailable evidence: " + html.escape(str(relative))
    href = quote(os.path.relpath(path, out), safe="/")
    return f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'


def _proposal_files(owner: Path, out: Path, row: dict) -> str:
    """Expose retained authored files only after the ordinary retention checks."""
    link = row.get("assets_manifest")
    if not link:
        return ""
    try:
        validate_proposal_assets(owner, {"items": [row]})
        manifest = local_path(owner, link["path"])
        raw = manifest.read_bytes()
        if hashlib.sha256(raw).hexdigest() != link["sha256"]:
            raise ValueError("Proposal manifest changed while building the view")
        record = json.loads(raw)
        entries = {}
        for item in record["files"]:
            name = item["path"]
            label = item.get("source_member") or name
            entries[name] = '<li>' + _artifact_link(owner, out, name, str(label)) + ' · <code>' \
                + html.escape(item["sha256"][:12]) + '</code></li>'
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        return '<p>Retained file links unavailable: ' + html.escape(str(error)) + '</p>'
    return (f'<details class="proposal-files"><summary>Retained files ({len(entries)}) · '
            'hashes checked for this view</summary><p>These are passive review contributions. '
            'Opening a file does not execute or select it, or establish runtime qualification.</p><ul>'
            + ''.join(entries[name] for name in sorted(entries)) + '</ul></details>')


def _review_navigation(owner: Path, out: Path, review: object) -> str:
    """Link current implementation bytes while keeping historical checks explicit."""
    if not isinstance(review, dict):
        return ""
    pins = {}
    for field in ("selected_sources", "selected_source"):
        sources = review.get(field)
        if isinstance(sources, str):
            pins[sources] = review.get("selected_sha256")
        elif isinstance(sources, dict):
            pins.update(sources)
    source_rows = []
    for name, recorded in sorted(pins.items()):
        if not isinstance(name, str):
            continue
        state = "no valid recorded SHA-256"
        try:
            path = local_path(owner, name)
            actual = sha256(path)
            if isinstance(recorded, str) and re.fullmatch(r"[0-9a-f]{64}", recorded):
                state = "matches recorded SHA-256" if actual == recorded else "changed since recorded review"
        except (ValueError, OSError):
            state = "source unavailable"
        source_rows.append('<li>' + _artifact_link(owner, out, name, name) + ' · '
                           + html.escape(state) + '</li>')
    links = []
    for field, label in (("index", "Tool index"), ("verification_receipt", "Recorded verification receipt")):
        name = review.get(field)
        if isinstance(name, str):
            links.append(_artifact_link(owner, out, name, label))
    tests = review.get("tests")
    if isinstance(tests, list):
        links.extend(_artifact_link(owner, out, name, name) for name in tests if isinstance(name, str))
    elif isinstance(tests, dict) and isinstance(tests.get("junit"), str):
        links.append(_artifact_link(owner, out, tests["junit"], "Recorded test receipt"))
    return (('<details><summary>Implementation sources and review files</summary><p>'
             'Source hash checks compare bytes; they do not rerun the recorded tests. '
             'Changed sources need their own verification.</p><ul>' + ''.join(source_rows) + '</ul><p>'
             + ' · '.join(links) + '</p></details>') if source_rows or links else '')


def _request_sections(owner: Path, out: Path, rows: list[dict], *, answers: bool = False) -> str:
    """Render the current list, folding identical prose without merging decisions."""
    by_status = {}
    for row in rows:
        by_status.setdefault(row.get("status", "unclassified"), []).append(row)
    order = ["needs_evidence", "deferred", "proposed", "accepted", "implemented", "declined"]
    sections = []
    for status in sorted(by_status, key=lambda value: (order.index(value) if value in order else len(order), value)):
        status_rows = by_status[status]
        groups = {}
        for row in status_rows:
            text = row.get("text") or ""
            groups.setdefault(text or row["request_id"], []).append(row)
        cards = []
        for group in groups.values():
            text = group[0].get("text") or ""
            title = text.strip().splitlines()[0][:180] if text.strip() else group[0]["request_id"]
            sources = []
            for row in group:
                links = []
                if row.get("generator_id"):
                    links.append(_artifact_link(owner, out, f"generators/{row['generator_id']}/notes.md", "Generator notes"))
                manifest = row.get("assets_manifest")
                if isinstance(manifest, dict) and isinstance(manifest.get("path"), str):
                    links.append(_artifact_link(owner, out, manifest["path"], "Retained proposal/evidence"))
                identity = {key: row[key] for key in ("request_id", "return_id", "generator_id", "source_sha256") if key in row}
                review = row.get("owner_tool_review")
                sources.append('<section><h4>' + html.escape(row["request_id"]) + '</h4><p>'
                    + ' · '.join(links) + '</p><pre>' + html.escape(json.dumps(identity, indent=2)) + '</pre>'
                    + '<p>Current reason:</p><pre>' + html.escape(row.get("reason") or "No maintainer reason recorded.") + '</pre>'
                    + _proposal_files(owner, out, row)
                    + _review_navigation(owner, out, review)
                    + ('<details><summary>Maintainer review and verification scope</summary><pre>'
                       + html.escape(json.dumps(review, indent=2, ensure_ascii=False)) + '</pre></details>' if review else '')
                    + '</section>')
            repeated = f" · same text in {len(group)} requests; decisions remain separate" if len(group) > 1 else ""
            cards.append('<details class="request"><summary>' + html.escape(title + repeated) + '</summary><pre>'
                         + html.escape(text or "No request text recorded.") + '</pre>' + ''.join(sources) + '</details>')
        opened = ' open' if status == 'needs_evidence' and not answers else ''
        sections.append(f'<details class="request-status"{opened}><summary>{html.escape(status)} '
                        f'({len(status_rows)})</summary>' + ''.join(cards) + '</details>')
    return ''.join(sections) or '<p>None recorded.</p>'


def build_full_inbox(review_root: Path, out: Path) -> dict:
    from .review import _lock
    with _lock(review_root):
        return _build_full_inbox(review_root, out)


def _build_full_inbox(review_root: Path, out: Path) -> dict:
    review_root, out = review_root.resolve(), out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipts = _receipts(review_root)
    invalid = [json.loads(path.read_text()) for path in
               sorted((review_root / "returns/unmapped").glob("return-*.json"))]
    groups = {}
    incoming_ids = set()
    for receipt in receipts:
        if receipt["validation_status"] != "accepted":
            continue
        for tid in receipt.get('task_ids', [receipt['task_id']]):
            projection = dict(receipt, task_id=tid,
                              **receipt.get('repair_dispositions', {}).get(tid, {}))
            groups.setdefault(tid, []).append(projection)
            incoming_ids.add(tid)
        incoming_ids.update(receipt.get("audit_targets") or
                            ([receipt["audit_target"]] if receipt.get("audit_target") else []))
    current_ids = {p.parent.parent.name for p in
                   (review_root.parent / "generators").glob("*/evidence/review_index.json")}
    records, events = {}, []
    catalog_records = {row["id"]: row for row in jsonl(review_root.parent / "catalog/puzzles.jsonl")}
    for tid in sorted(incoming_ids | current_ids):
        incoming = _incoming_task_index(review_root, tid, receipts=receipts)
        events.extend(suggestion_events(incoming))
        # Extract old feedback into the current request list before dropping prose.
        events.extend(suggestion_events(read_index(review_root.parent, tid)))
        current = _merge_current(review_root, tid, incoming, catalog_records=catalog_records)
        records[tid] = compact_task_state(review_root.parent, tid, current, apply=True, catalog_records=catalog_records)
    append_suggestions(review_root, events)
    requests = json.loads((review_root / "suggestions.json").read_text())["items"]
    answers = [row for row in requests if row["request_id"].startswith("question:")]
    tools = [row for row in requests if not row["request_id"].startswith("question:")]
    audit_groups = {tid: record["audits"] for tid, record in records.items() if record["audits"]}
    data = {"schema": "arcpuzzles-full-inbox-v2", "generators": dict(sorted(groups.items())),
            "audits": audit_groups, "current_states": records, "invalid": invalid,
            "counts": {"returns": len(receipts) + len(invalid), "generator_groups": len(groups),
                       "audit_groups": len(audit_groups), "invalid": len(invalid),
                       "tool_requests": len(tools), "reviewer_answers": len(answers),
                       "open_tool_requests": sum(row.get("status") not in {"implemented", "declined"} for row in tools),
                       "collisions": sum(len(rows) > 1 for rows in groups.values())}}
    ticket_reports = [dict(item, return_id=f"{receipt['assignment_id']}:v{receipt['version']:04d}")
                      for receipt in receipts for item in receipt.get('supplementary_tickets', [])]
    if ticket_reports:
        data['supplementary_tickets'] = ticket_reports
        data['counts']['supplementary_tickets'] = len(ticket_reports)
    json_path = out / "index.json"
    json_path.write_text(json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    cards = []
    for tid, rows in sorted(groups.items()):
        for row in rows:
            key = f"{row['assignment_id']}:v{row['version']:04d}"
            decision = _returned_text(row, "DECISIONS.md") or ""
            link = Path(row["archive_path"]).as_uri()
            cards.append(f"<article><h3>{html.escape(tid)}: {html.escape(key)}</h3>"
                         f"<p>Completion: {html.escape(row['completion_status'])}; disposition: "
                         f"{html.escape(row['disposition_status'])}</p>"
                         f"<a href='{html.escape(link, quote=True)}'>Incoming ZIP</a>"
                         f"<pre>{html.escape(decision)}</pre></article>")
    findings = []
    for tid, rows in sorted(audit_groups.items()):
        for row in rows:
            findings.append(f"<article><h3>{html.escape(tid)}: {html.escape(row['return_id'])}</h3>"
                            f"<p>{html.escape(row['resolution'])}; source {html.escape(row['source_sha256'])}</p>"
                            f"<pre>{html.escape(row.get('text') or '')}</pre></article>")
    page = ("<!doctype html><html lang='en'><meta charset='utf-8'><title>ARCpuzzles review inbox</title>"
            "<style>body{font:16px system-ui;max-width:1100px;margin:auto;padding:2rem}"
            "article,.request{border:1px solid #ccc;padding:1rem;margin:1rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
            "summary{cursor:pointer}.request-status{margin:1rem 0}section{border-top:1px solid #ddd;padding-top:.5rem}</style>"
            "<h1>Current generator review work</h1><p>Current decisions live in generator notes. "
            "Processed archives are unnecessary after verified extraction.</p>"
            "<nav><a href='#tool-requests'>Tool requests</a> · <a href='#reviewer-answers'>Reviewer answers</a> · "
            "<a href='#audits'>Open audits</a> · <a href='../solves/index.html'>Reviewer solve tracker</a></nav>"
            f"<h2 id='tool-requests'>Current tool requests</h2><p>{len(tools)} requests; "
            f"{data['counts']['open_tool_requests']} await implementation or evidence. "
            "Accepted means retained for follow-up. Only the maintainer review states whether code is selected.</p>"
            "<p>Editable source: " + _artifact_link(review_root.parent, out, "REVIEW/suggestions.json", "Current request list")
            + ". This page is a generated view; rebuild with <code>arcpuzzles review inbox</code>. "
            "Use your browser's Find command to search request text and IDs.</p>"
            + _request_sections(review_root.parent, out, tools)
            + f"<h2 id='reviewer-answers'>Reviewer answers</h2><p>{len(answers)} retained answers; "
            "these are reviewer insights, not additional open tool tickets.</p>"
            + _request_sections(review_root.parent, out, answers, answers=True)
            +
            "<h2>Incoming returns</h2>" + "".join(cards) + "<h2 id='audits'>Open adversarial findings</h2>"
            + "".join(findings) + "<h2>Invalid or unmatched returns</h2><pre>"
            + html.escape(json.dumps(invalid, indent=2)) + "</pre></html>\n")
    html_path = out / "index.html"
    html_path.write_text(page)
    from .review_solve_tracker import build_solve_tracker
    solve_tracker = build_solve_tracker(review_root, review_root.parent / "var/review/solves")
    return {"html": str(html_path), "json": str(json_path), "counts": data["counts"], "solves": solve_tracker}
