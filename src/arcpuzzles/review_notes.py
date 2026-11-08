"""Current task-owned findings and the shared current tool-request list.

Legacy ledgers are migration inputs only. Current notes own decisions; this
module neither grants approval nor infers audit resolution from source changes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .catalog import local_path, jsonl
from .review import _lock
from .review_feedback import feedback_items

CURRENT_SCHEMA = "arcpuzzles-task-review-current-v1"
LEGACY_SCHEMA = "arcpuzzles-task-review-index-v2"
REQUEST_SCHEMA = "arcpuzzles-tool-requests-v1"
CLOSED_AUDITS = {"resolved", "no_issue"}
_ASSESSMENT_START = "<!-- arcpuzzles-current-audit-assessment:start -->"
_ASSESSMENT_END = "<!-- arcpuzzles-current-audit-assessment:end -->"


def _write(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def validate_index(record: dict, task_id: str) -> None:
    if (record.get("schema") not in {LEGACY_SCHEMA, CURRENT_SCHEMA}
            or record.get("task_id") != task_id
            or not isinstance(record.get("decisions"), list)
            or not isinstance(record.get("audits"), list)):
        raise ValueError(f"Invalid task index identity or schema: {task_id}")


def index_path(root: Path, task_id: str) -> Path:
    return local_path(root, f"generators/{task_id}/evidence/review_index.json")


def read_index(root: Path, task_id: str) -> dict:
    path = index_path(root, task_id)
    legacy = local_path(root, f"REVIEW/task_indexes/{task_id}.json")
    if not path.is_file() and legacy.is_file():
        path = legacy
    record = json.loads(path.read_text()) if path.is_file() else {
        "schema": CURRENT_SCHEMA, "task_id": task_id, "decisions": [], "audits": []}
    validate_index(record, task_id)
    return record


def audit_state(root: Path, task_id: str, record: dict | None = None) -> dict:
    """Read explicit current audit status; old-source findings stay actionable."""
    record = read_index(root, task_id) if record is None else record
    validate_index(record, task_id)
    history = local_path(root, f"generators/{task_id}/evidence/audit_dispositions.jsonl")
    latest = {}
    for event in jsonl(history) if history.is_file() and record["schema"] == LEGACY_SCHEMA else []:
        latest[(event["return_id"], event["source_sha256"])] = event
    audits = []
    for audit in record["audits"]:
        event = latest.get((audit["return_id"], audit["source_sha256"]))
        audits.append({**audit, "resolution": event["status"] if event else audit.get("resolution", "needs_triage"),
                       "resolution_reason": event["reason"] if event else audit.get("resolution_reason")})
    unresolved = sum(a["resolution"] not in CLOSED_AUDITS for a in audits)
    return {"audit_unresolved": bool(unresolved), "audit_unresolved_count": unresolved,
            "audit_pending_triage_count": sum(a["resolution"] == "needs_triage" for a in audits),
            "audits": audits}


def compact_task_state(root: Path, task_id: str, legacy_record: dict | None = None,
                       *, apply: bool = False, catalog_records: dict | None = None) -> dict:
    """Select current findings and exact-source approval identity, without ZIP reads.

    Call after useful decision prose has been incorporated into notes.md and
    audit assets extracted. This function never deletes archives or assets.
    A caller may add/update the existing assets_manifest fields before calling.
    """
    root = root.resolve()
    record = read_index(root, task_id) if legacy_record is None else legacy_record
    validate_index(record, task_id)
    source = local_path(root, f"generators/{task_id}/generator.py")
    current_hash = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    audits = {}
    for audit in audit_state(root, task_id, record)["audits"]:
        if audit["resolution"] in CLOSED_AUDITS:
            continue
        fields = ("return_id", "source_sha256", "text", "resolution", "resolution_reason",
                  "assets_manifest", "assets_manifest_sha256")
        item = {key: audit[key] for key in fields if key in audit}
        item["verification_status"] = audit.get("verification_status", "reviewer_reported")
        triage = audit.get("maintainer_dispositions", [])
        if triage:
            item["triage"] = {key: triage[-1][key] for key in ("status", "reason") if key in triage[-1]}
        elif audit.get("triage"):
            item["triage"] = audit["triage"]
        audits[(item["return_id"], item["source_sha256"])] = item
    decisions = []
    # The catalog receipt selects the accepted source. Assignment baseline hashes
    # are not repaired-source hashes and cannot identify the current decision.
    catalog = root / "catalog/puzzles.jsonl"
    row = (catalog_records.get(task_id, {}) if catalog_records is not None else
           next((r for r in jsonl(catalog) if r.get("id") == task_id), {}) if catalog.is_file() else {})
    approval_name = row.get("approval_receipt")
    if approval_name:
        path = local_path(root, approval_name)
        if path.is_file():
            approval = json.loads(path.read_text())
            if (approval.get("generator_sha256") == current_hash
                    and row.get("reviewed_generator_sha256") == current_hash):
                return_id = approval.get("return_id")
                if not return_id and approval.get("assignment_id") and type(approval.get("version")) is int:
                    return_id = f"{approval['assignment_id']}:v{approval['version']:04d}"
                decisions = [{"return_id": return_id,
                              "source_sha256": current_hash, "rule_hash": approval.get("rule_hash"),
                              "approval_receipt": approval_name,
                              "verification_status": approval.get("verification_status", "unknown")}]
    current = {"schema": CURRENT_SCHEMA, "task_id": task_id,
               "current_source_sha256": current_hash,
               "notes_path": f"generators/{task_id}/notes.md",
               "decisions": decisions, "audits": list(audits.values())}
    if apply:
        _write(index_path(root, task_id), current)
        # The latest explicit status is now inline; no event replay is needed.
        local_path(root, f"generators/{task_id}/evidence/audit_dispositions.jsonl").unlink(missing_ok=True)
    return current


def _retain_audit_assessment(root: Path, task_id: str, audit: dict) -> None:
    """Keep one explicit current assessment in notes, not a closed-event ledger."""
    note = local_path(root, f"generators/{task_id}/notes.md")
    original = note.read_text() if note.is_file() else f"# Working notes: {task_id}\n"
    status, return_id = audit['resolution'], audit['return_id']
    start, end = original.find(_ASSESSMENT_START), original.find(_ASSESSMENT_END)
    if (original.count(_ASSESSMENT_START) != original.count(_ASSESSMENT_END)
            or original.count(_ASSESSMENT_START) > 1 or start > end):
        raise ValueError(f"Invalid current audit assessment markers: {task_id}")
    if start >= 0:
        end += len(_ASSESSMENT_END)
    else:
        # Migrate the one formerly hand-authored assessment section without
        # overwriting adjacent author sections or recreating earlier history.
        heading = '## Current bounded audit assessment\n'
        start = 0 if original.startswith(heading) else original.find('\n' + heading)
        if start >= 0:
            next_section = original.find('\n## ', start + 1)
            end = next_section if next_section >= 0 else len(original)
    if status not in CLOSED_AUDITS:
        if start < 0 or f'Return: `{return_id}`' not in original[start:end]:
            return
    source = local_path(root, f"generators/{task_id}/generator.py")
    current_hash = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    audited_hash = audit.get('source_sha256', 'unknown')
    binding = ('At disposition, audited bytes match the current source.' if current_hash == audited_hash else
               'At disposition, the audited source differs from the current source; this assessment covers audited bytes only.')
    def safe_text(value):
        text = str(value)
        for marker in (_ASSESSMENT_START, _ASSESSMENT_END):
            text = text.replace(marker, marker.replace('<', '&lt;'))
        return text.strip()
    section = (_ASSESSMENT_START + '\n## Current bounded audit assessment\n\n'
        + f'Return: `{return_id}`. Disposition: **{status}**. '
        + f"Evidence basis: `{safe_text(audit.get('verification_status', 'reviewer_reported'))}`.\n\n"
        + f'Audited source SHA-256: `{audited_hash}`. {binding}\n\n'
        + '### Current decision\n\n' + safe_text(audit.get('resolution_reason', '')) + '\n\n'
        + '### Assessment or prior finding\n\n' + safe_text(audit.get('text', '')) + '\n\n'
        + 'The disposition records an explicit decision. It does not imply a fresh execution, '
          'universal correctness, closure of other findings, or training admission.\n')
    if audit.get('assets_manifest'):
        asset = audit['assets_manifest']
        try:
            relative = Path(asset).relative_to(Path('generators') / task_id).as_posix()
            section += f'\n[Retained evidence]({relative}), manifest SHA-256 '
            section += f"`{audit.get('assets_manifest_sha256', 'unknown')}`.\n"
        except ValueError:
            section += '\nRetained evidence manifest: `' + safe_text(asset) + '`.\n'
    section += _ASSESSMENT_END
    text = (original[:start].rstrip() + '\n\n' + section + original[end:] if start >= 0 else
            original.rstrip() + '\n\n' + section + '\n')
    if text != original:
        temporary = note.with_suffix(note.suffix + '.tmp')
        temporary.write_text(text)
        temporary.replace(note)


def record_audit_status(root: Path, task_id: str, return_id: str, status: str, reason: str) -> dict:
    if status not in {"unresolved", "resolved", "no_issue", "disputed", "needs_evidence"} or not reason.strip():
        raise ValueError("Audit status and a nonempty evidence/reason are required")
    root = root.resolve()
    with _lock(root / "REVIEW"):
        record = read_index(root, task_id)
        audits = audit_state(root, task_id, record)["audits"]
        matches = [a for a in audits if a["return_id"] == return_id]
        if len(matches) != 1:
            raise ValueError("Select exactly one existing task audit by return ID")
        event = {"return_id": return_id, "source_sha256": matches[0]["source_sha256"],
                 "status": status, "reason": reason.strip()}
        matches[0].update(resolution=status, resolution_reason=reason.strip())
        # Closed findings leave the actionable index. Preserve their useful
        # assessment before that reduction, while its original text is present.
        _retain_audit_assessment(root, task_id, matches[0])
        record["audits"] = audits
        record["schema"] = CURRENT_SCHEMA
        # Pending receipts retain only the latest explicit status, so rebuilding
        # the inbox cannot resurrect an audit already resolved by the maintainer.
        assignment_id, _, version_text = return_id.partition(":v")
        if version_text.isdigit():
            for path in (root / "REVIEW/assignments" / assignment_id / "returns").glob(
                    f"return-{int(version_text):04d}-*.json"):
                receipt = json.loads(path.read_text())
                receipt.setdefault("audit_resolutions", {})[task_id] = event
                _write(path, receipt)
        compact_task_state(root, task_id, record, apply=True)
    return event


def suggestion_events(record: dict) -> list[dict]:
    """Read old/fresh feedback; callers immediately reduce it to current rows."""
    events = []
    for decision in record["decisions"]:
        text = decision.get("feedback") or ""
        items = feedback_items(text)
        if text.strip() and not items:
            items = [{"id": "unstructured", "text": text.strip()}]
        for item in items:
            request_id = f"{decision['return_id']}:{item['id']}"
            base = {"request_id": request_id, "generator_id": record["task_id"],
                    "return_id": decision["return_id"], "source_sha256": decision.get("source_sha256")}
            events.append({**base, "event": "suggestion", "text": item["text"]})
            for disposition in decision.get("feedback_dispositions", {}).get(item["id"], []):
                events.append({**base, "event": "disposition",
                               "status": disposition["status"], "reason": disposition["reason"]})
    return events


def _request_list(review_root: Path, events: list[dict]) -> dict:
    path = local_path(review_root, "suggestions.json")
    current = json.loads(path.read_text()) if path.is_file() else {"schema": REQUEST_SCHEMA, "items": []}
    if current.get("schema") != REQUEST_SCHEMA:
        raise ValueError("Invalid current tool-request list")
    rows = {row["request_id"]: dict(row) for row in current["items"]}
    latest = {}
    for event in events:
        merged = latest.setdefault(event["request_id"], {})
        for field in ("generator_id", "return_id", "source_sha256", "text", "status", "reason", "assets_manifest"):
            if field in event:
                merged[field] = event[field]
    for key, event in latest.items():
        row = rows.setdefault(key, {"request_id": key, "status": "proposed", "reason": None})
        for field in ("generator_id", "return_id", "source_sha256", "text", "assets_manifest"):
            if field in event:
                row[field] = event[field]
        if "status" in event:
            source = hashlib.sha256(json.dumps([event["status"], event.get("reason")],
                                                ensure_ascii=False).encode()).hexdigest()
            # Replaying the same source feedback cannot undo an edit to the
            # current request list. A genuinely changed source decision can.
            if source != row.get("source_disposition_sha256"):
                row.update(status=event["status"], reason=event.get("reason"),
                           source_disposition_sha256=source)
    return {"schema": REQUEST_SCHEMA, "items": [rows[key] for key in sorted(rows)]}


def compact_suggestions(review_root: Path, *, apply: bool = False) -> dict:
    """Replace event churn with one latest row for each separately identified request."""
    review_root = review_root.resolve()
    legacy = local_path(review_root, "suggestions.jsonl")
    events = list(jsonl(legacy)) if legacy.is_file() else []
    result = _request_list(review_root, events)
    if apply:
        _write(local_path(review_root, "suggestions.json"), result)
        legacy.unlink(missing_ok=True)
    return result


def validate_proposal_assets(root: Path, requests: dict) -> set[str]:
    """Verify passive reviewer contributions before packaging or disposal."""
    retained = set()
    for request in requests.get("items", []):
        link = request.get("assets_manifest")
        if not link:
            continue
        base = "shared/tools/proposals/" + hashlib.sha256(request["request_id"].encode()).hexdigest()[:16] + "/"
        if not isinstance(link, dict) or link.get("path") != base + "manifest.json":
            raise ValueError("Invalid proposal manifest path")
        manifest = local_path(root, link["path"])
        if (manifest.is_symlink() or not manifest.is_file()
                or hashlib.sha256(manifest.read_bytes()).hexdigest() != link.get("sha256")):
            raise ValueError(f"Missing or changed proposal manifest: {link['path']}")
        record = json.loads(manifest.read_text())
        if (record.get("schema") != "arcpuzzles-tool-proposal-assets-v1"
                or record.get("request_id") != request["request_id"]
                or record.get("runtime_approved") is not False
                or not isinstance(record.get("files"), list) or not record["files"]):
            raise ValueError(f"Invalid proposal asset identity: {link['path']}")
        for item in record["files"]:
            name = item.get("path", "")
            if not name.startswith(base):
                raise ValueError(f"Proposal asset outside its request: {name}")
            path = local_path(root, name)
            if (path.is_symlink() or not path.is_file()
                    or hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256")):
                raise ValueError(f"Missing or changed proposal asset: {name}")
            retained.add(name)
    return retained


def append_suggestions(review_root: Path, events: list[dict]) -> int:
    """Compatibility API: upsert current requests, never append an event ledger."""
    review_root = review_root.resolve()
    with _lock(review_root):
        compact_suggestions(review_root, apply=True)
        path = local_path(review_root, "suggestions.json")
        before = json.loads(path.read_text())
        after = _request_list(review_root, events)
        old = {row["request_id"]: row for row in before["items"]}
        changed = sum(old.get(row["request_id"]) != row for row in after["items"])
        if changed:
            _write(path, after)
    return changed


def migrate_notes(root: Path, *, apply: bool = False) -> dict:
    with _lock(root.resolve() / 'REVIEW'):
        return _migrate_notes(root, apply=apply)


def _migrate_notes(root: Path, *, apply: bool = False) -> dict:
    """Compact current review metadata; archive extraction/disposal is separate."""
    root = root.resolve()
    records = {}
    legacy_paths = sorted((root / "REVIEW/task_indexes").glob("*.json"))
    for path in [*legacy_paths, *sorted((root / "generators").glob("*/evidence/review_index.json"))]:
        tid = path.stem if path.name != "review_index.json" else path.parent.parent.name
        record = json.loads(path.read_text())
        validate_index(record, tid)
        if tid in records and records[tid] != record:
            raise ValueError(f"Conflicting task index: {tid}")
        records[tid] = record
    events = [event for record in records.values() for event in suggestion_events(record)]
    catalog_records = {row["id"]: row for row in jsonl(root / "catalog/puzzles.jsonl")}
    states = {tid: compact_task_state(root, tid, record, catalog_records=catalog_records)
              for tid, record in records.items()}
    changed = 0
    if apply:
        changed = append_suggestions(root / "REVIEW", events)
        for tid, state in states.items():
            compact_task_state(root, tid, state, apply=True, catalog_records=catalog_records)
        for path in legacy_paths:
            path.unlink()
    return {"mode": "apply" if apply else "preview", "indexes_to_move": len(legacy_paths),
            "current_task_records": len(states), "suggestion_rows_changed": changed,
            "archives_deleted": 0, "archive_disposal_ready": False,
            "remaining_gate": "Extract useful task evidence and migrate archive consumers before disposal."}
