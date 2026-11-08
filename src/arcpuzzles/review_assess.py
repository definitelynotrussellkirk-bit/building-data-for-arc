"""Review candidate evidence and explicitly integrate selected components."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from .catalog import Catalog, local_path, sha256
from .review import _lock
from .review_candidate import _receipt


COMPONENTS = {"generator", "racket", "tests_notes"}
FEEDBACK_STATES = {"accepted", "implemented", "needs_evidence", "deferred", "declined"}


def _inputs(review_root: Path, assignment_id: str, version: int) -> tuple[Path, dict, dict, dict, Path]:
    returned = _receipt(review_root, assignment_id, version)
    if returned["status"] != "accepted":
        raise ValueError(f"Return is {returned['status']}, not accepted")
    folder = review_root / "assignments" / assignment_id
    assignment = json.loads((folder / "assignment.json").read_text())
    contract = json.loads((folder / "ASSIGNMENT.json").read_text())
    extracted = Path(returned["archive_path"]).parent / "extracted"
    results = json.loads((extracted / "RESULTS.json").read_text())
    return folder, assignment, contract, results, extracted


def _source_drift(catalog_root: Path, contract: dict) -> list[str]:
    expected = [(contract["generator"]["library_path"], contract["generator"]["sha256"]),
                (contract["rule"]["library_path"], contract["rule"]["sha256"])]
    expected += [(item["library_path"], item["sha256"]) for item in contract.get("base_authorities", [])]
    changed = []
    for relative, digest in expected:
        path = local_path(catalog_root, relative)
        if not path.is_file() or sha256(path) != digest:
            changed.append(relative)
    return changed


def _feedback_items(path: Path) -> list[dict]:
    items = []
    for line in path.read_text().splitlines():
        found = re.match(r"\s*(?:[-*]\s*)?(F\d+)\s*:\s*(.+)", line)
        if found:
            items.append({"id": found[1], "text": found[2], "evidence_path": str(path)})
    return items


def assess(review_root: Path, assignment_id: str, version: int) -> dict:
    review_root = review_root.resolve()
    folder, assignment, contract, results, extracted = _inputs(review_root, assignment_id, version)
    check_path = review_root.parent / "var/review/checks" / assignment_id / f"{version:04d}/result.json"
    check = json.loads(check_path.read_text()) if check_path.is_file() else None
    comparison = {}
    if check:
        for item in check.get("checks", []):
            if item.get("kind") in {"baseline_battery", "battery", "racket"}:
                key = "candidate_battery" if item["kind"] == "battery" else item["kind"]
                comparison[key] = item.get("exit_code") == 0 and not item.get("timed_out")
    patches = [item if isinstance(item, str) else item["path"] for item in results.get("patches", [])]
    blockers = []
    drift = _source_drift(Path(assignment["catalog_root"]), contract)
    if drift:
        blockers.append("source_drift")
    if patches and check is None:
        blockers.append("needs_check")
    elif patches and check["status"] != "passed":
        blockers.append("failed_checks")
    answer = None
    if results.get("question_answer"):
        name = results["question_answer"]
        name = name if isinstance(name, str) else name["path"]
        question = contract.get("question")
        answer = {"path": str(extracted / name), "question_id": question["id"] if question else None,
                  "version": question["version"] if question else None,
                  "owner": question["owner"] if question else None}
    report = {"schema": "arcpuzzles-review-assessment-v1", "assignment_id": assignment_id,
              "version": version, "status": "blocked" if blockers else ("ready" if patches else "no_changes"),
              "blockers": blockers, "drifted_sources": drift, "patches": patches,
              "changed_paths": check.get("paths", []) if check else [],
              "check_status": check["status"] if check else None,
              "check_comparison": comparison,
              "check_receipt": str(check_path) if check else None,
              "question_answer": answer,
              "review_path": str(extracted / "REVIEW.md"),
              "feedback_path": str(extracted / "FEEDBACK_TO_CODEX.md"),
              "feedback_items": _feedback_items(extracted / "FEEDBACK_TO_CODEX.md"),
              "remaining_failures": results.get("remaining_failures", []),
              "improvement_claim": results.get("improvement_claim", "")}
    content = json.dumps(report, sort_keys=True, indent=2) + "\n"
    location = folder / "assessments"
    location.mkdir(exist_ok=True)
    target = location / f"assessment-{version:04d}-{hashlib.sha256(content.encode()).hexdigest()[:16]}.json"
    if not target.exists():
        target.write_text(content)
    return {**report, "receipt_path": str(target)}


def _component_paths(contract: dict, changed_paths: set[str]) -> dict[str, dict[str, str]]:
    tid = contract["task_id"]
    mapping = {"generator": {}, "racket": {}, "tests_notes": {}}
    generator = "workspace/" + contract["generator"]["runtime_path"]
    rule = "workspace/" + contract["rule"]["runtime_path"]
    authority = {"workspace/" + item["runtime_path"]: item["library_path"]
                 for item in contract.get("base_authorities", [])}
    for path in changed_paths:
        if path == generator:
            mapping["generator"][path] = contract["generator"]["library_path"]
        elif path == rule:
            mapping["racket"][path] = contract["rule"]["library_path"]
        elif path in authority:
            mapping["racket"][path] = authority[path]
        elif path.startswith(f"workspace/tests/{tid}/"):
            mapping["tests_notes"][path] = f"generators/{tid}/tests/" + path.split(f"workspace/tests/{tid}/", 1)[1]
        elif path.startswith(f"workspace/notes/{tid}/"):
            mapping["tests_notes"][path] = f"generators/{tid}/notes/" + path.split(f"workspace/notes/{tid}/", 1)[1]
        else:
            raise ValueError(f"Unrecognized candidate path: {path}")
    return mapping


def integrate(catalog: Catalog, review_root: Path, assignment_id: str, version: int,
              components: set[str]) -> dict:
    if not components <= COMPONENTS:
        raise ValueError(f"Unknown integration component: {sorted(components - COMPONENTS)}")
    review_root = review_root.resolve()
    with _lock(review_root):
        folder, assignment, contract, results, extracted = _inputs(review_root, assignment_id, version)
        report = assess(review_root, assignment_id, version)
        if components and "source_drift" in report["blockers"]:
            raise ValueError("Source drift since assignment; rebase and recheck before integration")
        if components and report["blockers"]:
            raise ValueError(f"Cannot integrate failed or unchecked candidate: {report['blockers']}")
        check_path = review_root.parent / "var/review/checks" / assignment_id / f"{version:04d}/result.json"
        check = json.loads(check_path.read_text()) if check_path.is_file() else None
        changed = set(check.get("paths", [])) if check else set()
        mapping = _component_paths(contract, changed)
        if any(not mapping[part] for part in components):
            raise ValueError("Selected component has no checked changes")
        selected = {path: target for part in components for path, target in mapping[part].items()}
        candidate = Path(check["candidate_path"]) if check else None
        for source in selected:
            if (not candidate or not (candidate / source).is_file()
                    or sha256(candidate / source) != check.get("candidate_file_sha256", {}).get(source)):
                raise ValueError(f"Checked candidate bytes changed: {source}")
        originals: dict[Path, bytes | None] = {}
        staged = review_root.parent / "var/review/integration-staging" / assignment_id / f"{version:04d}"
        staged.mkdir(parents=True, exist_ok=True)
        evidence_path = catalog.root / "generators" / contract["task_id"] / "evidence" / f"review-{assignment_id}-v{version:04d}.json"
        if evidence_path.exists():
            raise FileExistsError(f"Integration evidence already exists: {evidence_path}")
        try:
            for source, relative in selected.items():
                target = local_path(catalog.root, relative)
                if target.is_symlink():
                    raise ValueError(f"Authoritative source is a symlink: {relative}")
                originals[target] = target.read_bytes() if target.exists() else None
                staged_file = staged / relative
                staged_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate / source, staged_file)
            # The lock protects review state; recheck source hashes immediately before writes.
            if selected and _source_drift(catalog.root, contract):
                raise ValueError("Source drift before integration; rebase required")
            written = []
            for source, relative in selected.items():
                target = local_path(catalog.root, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged / relative, target)
                written.append(target)
        except Exception:
            for target in locals().get("written", []):
                before = originals[target]
                if before is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(before)
            raise
        evidence = {"schema": "arcpuzzles-review-integration-v1", "assignment_id": assignment_id,
                    "return_version": version, "components": sorted(components),
                    "source_hashes_at_assignment": {"generator": contract["generator"]["sha256"],
                                                   "rule_ledger": contract["rule"]["sha256"]},
                    "integrated_files": {relative: sha256(local_path(catalog.root, relative))
                                         for relative in selected.values()},
                    "check_receipt": str(check_path) if check else None,
                    "assessment_receipt": report["receipt_path"]}
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
        except Exception:
            evidence_path.unlink(missing_ok=True)
            for target in written:
                before = originals[target]
                if before is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(before)
            raise
        return {"status": "integrated" if selected else "no_changes", "evidence_path": str(evidence_path),
                "files": sorted(selected.values()), "components": sorted(components)}


def record_feedback(review_root: Path, assignment_id: str, version: int,
                    item_id: str, status: str, reason: str) -> dict:
    if status not in FEEDBACK_STATES or not reason.strip():
        raise ValueError("Feedback status and nonempty reason are required")
    review_root = review_root.resolve()
    contract_path = review_root / "assignments" / assignment_id / "ASSIGNMENT.json"
    contract = json.loads(contract_path.read_text())
    if contract.get("schema") in {"arcpuzzles-full-assignment-v2", "arcpuzzles-full-assignment-v3"}:
        from .review_full_candidate import assess_full_candidate
        report = assess_full_candidate(review_root, assignment_id, version)
    else:
        report = assess(review_root, assignment_id, version)
    item = next((row for row in report["feedback_items"] if row["id"] == item_id), None)
    if item is None:
        raise ValueError(f"Unknown feedback item: {item_id}")
    ledger = review_root / "assignments" / assignment_id / f"feedback-{version:04d}.json"
    with _lock(review_root):
        history = json.loads(ledger.read_text()) if ledger.exists() else {"schema": "arcpuzzles-review-feedback-v1", "items": {}}
        entry = {**item, "status": status, "reason": reason}
        history["items"].setdefault(item_id, []).append(entry)
        ledger.write_text(json.dumps(history, indent=2) + "\n")
        # The assignment ledger is temporary transport. Persist its decision
        # in current shared state immediately, before compaction can retire it.
        from .review_notes import _request_list, _write
        event = {
            "request_id": f"{assignment_id}:v{version:04d}:{item_id}",
            "event": "disposition", "status": status, "reason": reason,
            "return_id": f"{assignment_id}:v{version:04d}", "text": item["text"],
        }
        task_id = contract.get("task_id") or contract.get("generator", {}).get("rule_task_id")
        if task_id:
            event["generator_id"] = task_id
        current = _request_list(review_root, [event])
        _write(review_root / "suggestions.json", current)
    return entry
