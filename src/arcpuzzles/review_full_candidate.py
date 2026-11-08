"""Check full-packet returns in disposable source and runtime copies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from .review_full_packet import packet_member
from .catalog import Catalog, sha256
from .review_candidate import _RACKET_CHECK
from .review_full_return import validate_full_return
from .review_targets import MULTI_SCHEMA, assignment_targets, target_ids, rule_task_ids
from .runtime import prepare_runtime, run_process


def _receipt(review_root: Path, assignment_id: str, version: int) -> dict:
    if not re.fullmatch(r"review-[0-9a-f]{16}", assignment_id) or version < 1:
        raise ValueError("Invalid assignment or version")
    paths = list((review_root / "assignments" / assignment_id / "returns").glob(f"return-{version:04d}-*.json"))
    if len(paths) != 1:
        raise FileNotFoundError(f"Unknown full return {assignment_id} v{version}")
    receipt = json.loads(paths[0].read_text())
    if receipt.get("schema") != "arcpuzzles-full-return-receipt-v2":
        raise ValueError("Not a full-packet return")
    return receipt


def _packet(review_root: Path, packet_id: str) -> Path:
    path = review_root.parent / "var/review/full-packets" / packet_id / "request.zip"
    if not path.is_file():
        raise FileNotFoundError(f"Missing retained full packet: {packet_id}")
    return path


def check_full_candidate(catalog: Catalog, review_root: Path, assignment_id: str,
                         version: int, timeout: float = 4000,
                         lint_override: Path | None = None) -> dict:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    review_root = review_root.resolve()
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Cannot execute an unvalidated return")
    check_dir = review_root.parent / "var/review/full-checks" / assignment_id / f"{version:04d}"
    check_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = check_dir / "result.json"
    if receipt_path.is_file():
        if lint_override is not None:
            raise ValueError("An existing check receipt cannot be replaced by a lint override; archive the failed check and candidate first")
        return json.loads(receipt_path.read_text())
    candidate = review_root.parent / "var/review/full-candidates" / assignment_id / f"{version:04d}"
    if candidate.exists() and any(candidate.iterdir()):
        raise FileExistsError(f"Candidate already exists without check receipt: {candidate}")
    candidate.mkdir(parents=True, exist_ok=True)
    report = {"schema": "arcpuzzles-full-check-v2", "assignment_id": assignment_id,
              "version": version, "status": "unexamined", "candidate_path": str(candidate),
              "paths": [], "checks": [], "candidate_file_sha256": {}, "receipt_path": str(receipt_path)}
    try:
        with zipfile.ZipFile(_packet(review_root, returned["packet_id"])) as packet:
            manifest = json.loads(packet_member(packet, "PACKET-MANIFEST.json"))
            for name, digest in manifest["files"].items():
                if not name.startswith("repo/"):
                    continue
                raw = packet_member(packet, name)
                if hashlib.sha256(raw).hexdigest() != digest:
                    raise ValueError(f"Packet source hash differs: {name}")
                destination = candidate / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
        # Candidates live under this checkout's ignored var/. Give git apply an
        # independent root; otherwise it silently skips repo/ paths relative to
        # the parent checkout while still returning exit code zero.
        initialized = run_process(["git", "init", "-q"], candidate, timeout=min(timeout, 60))
        if initialized["exit_code"] != 0 or initialized["timed_out"]:
            raise ValueError(f"Cannot initialize candidate patch root: {initialized['stderr'][:500]}")
        with zipfile.ZipFile(returned["archive_path"]) as archive:
            checked = validate_full_return(archive, manifest)
            contract = json.loads(archive.read('ASSIGNMENT.json'))
            multi = contract.get('schema') == MULTI_SCHEMA
            if multi:
                report.update(task_ids=target_ids(contract), repair_targets=assignment_targets(contract),
                    checked_task_ids=[], independently_checked=False,
                    verification_scope='static_patch_only_no_target_execution')
            if checked["assignment_id"] != assignment_id:
                raise ValueError("Return assignment mismatch")
            paths = checked["patch_paths"]
            report["paths"] = paths
            patches = sorted(name for name in archive.namelist() if name.startswith("patches/"))
            for index, name in enumerate(patches):
                patch_file = check_dir / f"patch-{index:03d}.patch"
                patch_file.write_bytes(archive.read(name))
                before = run_process(["git", "apply", "--check", str(patch_file)], candidate,
                                     timeout=min(timeout, 60))
                report["checks"].append({"kind": "git_apply_check", **before})
                if before["exit_code"] != 0 or before["timed_out"]:
                    raise ValueError(f"Patch does not apply: {name}: {before['stderr'][:500]}")
                applied = run_process(["git", "apply", str(patch_file)], candidate,
                                      timeout=min(timeout, 60))
                if applied["exit_code"] != 0 or applied["timed_out"]:
                    raise ValueError(f"Patch apply failed: {name}: {applied['stderr'][:500]}")
            canonical = "repo/shared/data/canonical/puzzles.jsonl"
            if canonical in paths:
                from .review_full_return import _canonical_only_task
                with zipfile.ZipFile(_packet(review_root, returned["packet_id"])) as packet:
                    _canonical_only_task(packet_member(packet, canonical), (candidate / canonical).read_bytes(),
                                         rule_task_ids(contract) if multi else manifest["generators"][checked["task_id"]]["rule_task_id"])
            for path in paths:
                target = candidate / path
                if target.is_symlink() or not target.is_file():
                    raise ValueError(f"Unsafe candidate file: {path}")
                report["candidate_file_sha256"][path] = sha256(target)
            if not patches:
                report["status"] = "no_changes"
            elif multi:
                report['status'] = 'patch_verified_checks_pending'
                report['reason'] = ('Three-target delta applied and hashed; no target tests executed. '
                    'Run focused per-target packet checks and retain their evidence; '
                    'lightweight acceptance uses reviewer-reported status.')
            else:
                runtime = candidate / "runtime"
                prepare_runtime(Catalog(candidate / "repo"), runtime, checked["task_id"])
                if lint_override is not None:
                    source = lint_override.resolve()
                    if not source.is_file():
                        raise ValueError(f"Missing lint override: {source}")
                    content = source.read_bytes()
                    target = runtime / "scripts/lint_generator.py"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    report["checker_override"] = {
                        "runtime_path": "scripts/lint_generator.py",
                        "source_path": str(source),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                battery = run_process(["bash", "scripts/run_generator_battery.sh", checked["task_id"],
                                       "after", "--fresh"], runtime, timeout=timeout)
                report["checks"].append({"kind": "battery", **battery})
                racket_paths = {canonical} | {p for p in paths if p.startswith("repo/shared/data/base/")}
                if any(path in racket_paths for path in paths):
                    baseline = check_dir / "baseline-canonical.jsonl"
                    with zipfile.ZipFile(_packet(review_root, returned["packet_id"])) as packet:
                        baseline.write_bytes(packet_member(packet, canonical))
                    racket = run_process([sys.executable, "-c", _RACKET_CHECK,
                                          manifest["generators"][checked["task_id"]]["rule_task_id"],
                                          checked["task_id"], str(baseline)], runtime, timeout=timeout)
                    report["checks"].append({"kind": "racket", **racket})
                report["status"] = "passed" if all(item["exit_code"] == 0 and not item["timed_out"]
                                                    for item in report["checks"]) else "failed_checks"
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile) as exc:
        report["status"] = "rejected_patch"
        report["reason"] = f"{type(exc).__name__}: {exc}"
    receipt_path.write_text(json.dumps(report, sort_keys=True, indent=2, default=str) + "\n")
    return report


def assess_full_candidate(review_root: Path, assignment_id: str, version: int) -> dict:
    from .review_feedback import feedback_items
    review_root = review_root.resolve()
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Cannot assess an invalid return")
    extracted = Path(returned["archive_path"]).parent / "extracted"
    contract = json.loads((extracted / "ASSIGNMENT.json").read_text())
    results = json.loads((extracted / "RESULTS.json").read_text())
    check_path = review_root.parent / "var/review/full-checks" / assignment_id / f"{version:04d}/result.json"
    check = json.loads(check_path.read_text()) if check_path.is_file() else None
    patches = [item["path"] for item in results.get("artifacts", []) if item["kind"] == "patch"]
    blockers = []
    if patches and check is None:
        blockers.append("needs_check")
    elif patches and check["status"] != "passed":
        blockers.append("failed_checks")
    drifted = []
    for target_row in assignment_targets(contract):
        row = target_row['generator']
        generator_path = review_root.parent / row["generator"]
        if not generator_path.is_file() or sha256(generator_path) != row["generator_sha256"]:
            drifted.append(target_row['task_id'])
    if drifted:
        blockers.append("generator_source_drift")
    feedback_path = extracted / "FEEDBACK_TO_CODEX.md"
    report = {"schema": "arcpuzzles-full-assessment-v2", "assignment_id": assignment_id,
              "version": version, "status": "blocked" if blockers else ("ready" if patches else "no_changes"),
              "blockers": blockers, "changed_paths": check.get("paths", []) if check else [],
              "check_status": check["status"] if check else None,
              "decision_path": str(extracted / "DECISIONS.md"),
              "review_path": str(extracted / "REVIEW.md"),
              "audit_path": str(extracted / "AUDIT.md") if (extracted / "AUDIT.md").is_file() else None,
              "question_answer": {"id": contract["question"]["id"],
                                  "version": contract["question"]["version"],
                                  "path": str(extracted / "QUESTION_ANSWER.md")},
              "feedback_path": str(feedback_path),
              "feedback_items": feedback_items(feedback_path.read_text()),
              "remaining_failures": results.get("remaining_failures", []),
              "stopping_reason": results.get("stopping_reason", "")}
    if contract.get('schema') == MULTI_SCHEMA:
        report.update(task_ids=target_ids(contract), repair_targets=assignment_targets(contract),
            source_drift_task_ids=drifted, checked_task_ids=check.get('checked_task_ids', []) if check else [],
            independently_checked=False)
        if check and check['status'] == 'patch_verified_checks_pending':
            report['blockers'] = ['target_checks_not_run' if item == 'failed_checks' else item
                                  for item in report['blockers']]
    target = review_root / "assignments" / assignment_id / "assessments" / f"assessment-{version:04d}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return {**report, "receipt_path": str(target)}
