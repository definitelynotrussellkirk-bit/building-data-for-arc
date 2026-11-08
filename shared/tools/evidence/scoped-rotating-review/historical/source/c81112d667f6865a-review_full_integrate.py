"""Explicit component integration and conflict-aware full-return combinations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from .review_full_packet import packet_member, packet_names
from .catalog import Catalog, local_path, sha256
from .review import _lock
from .review_full_candidate import _receipt, assess_full_candidate
from .review_full_return import _canonical_only_task
from .review_full_return import validate_full_return
from .runtime import run_process


COMPONENTS = {"generator", "racket", "tests_notes"}


def _component(path: str, task_id: str) -> str:
    home = f"repo/generators/{task_id}/"
    if path == home + "generator.py":
        return "generator"
    if path.startswith("repo/shared/data/canonical/") or path.startswith("repo/shared/data/base/"):
        return "racket"
    if path.startswith(home) and (path in {home + "notes.md", home + "SUMMARY.md"}
                                  or path.startswith((home + "workspace/", home + "tests/", home + "counterexamples/"))):
        return "tests_notes"
    raise ValueError(f"Unknown integration path: {path}")


def _checked(review_root: Path, assignment_id: str, version: int) -> tuple[dict, dict, Path]:
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Return failed static validation")
    path = review_root.parent / "var/review/full-checks" / assignment_id / f"{version:04d}/result.json"
    if not path.is_file():
        raise ValueError("Candidate needs a check")
    check = json.loads(path.read_text())
    if check.get("status") != "passed":
        raise ValueError("Candidate did not pass checks")
    candidate = Path(check["candidate_path"])
    for item in check.get("paths", []):
        target = candidate / item
        if target.is_symlink() or not target.is_file() or sha256(target) != check["candidate_file_sha256"].get(item):
            raise ValueError(f"Checked candidate changed: {item}")
    return returned, check, candidate


def _merge_rule(baseline: bytes, proposed: bytes, current: bytes, task_id: str) -> bytes:
    _canonical_only_task(baseline, proposed, task_id)
    before, after, now = baseline.splitlines(), proposed.splitlines(), current.splitlines()
    # A rotating packet contains only its selected tasks. Match the complete
    # selected task's row sequence, preserving every other owner-library row.
    selected = lambda rows: [row for row in rows if json.loads(row).get("task_id") == task_id]
    if selected(now) != selected(before):
        raise ValueError("Canonical task row drift or collision; manual rebase required")
    merged = list(now)
    replacements = iter(selected(after))
    for index, old in enumerate(now):
        if json.loads(old).get("task_id") == task_id:
            merged[index] = next(replacements)
    return b"\n".join(merged) + b"\n"


def _reported(review_root: Path, assignment_id: str, version: int) -> tuple[dict, dict, Path]:
    """Prepare only changed files; accept reviewer evidence without executing it."""
    returned = _receipt(review_root, assignment_id, version)
    if returned["validation_status"] != "accepted":
        raise ValueError("Return failed static validation")
    candidate = review_root.parent / "var/review/reported-candidates" / assignment_id / f"{version:04d}"
    if candidate.exists():
        raise FileExistsError(f"Reported candidate already exists: {candidate}")
    candidate.mkdir(parents=True)
    packet_path = review_root.parent / "var/review/full-packets" / returned["packet_id"] / "request.zip"
    with zipfile.ZipFile(packet_path) as packet, zipfile.ZipFile(returned["archive_path"]) as archive:
        manifest = json.loads(packet_member(packet, "PACKET-MANIFEST.json"))
        checked = validate_full_return(archive, manifest)
        paths = checked["patch_paths"]
        for name in paths:
            if name in manifest["files"]:
                raw = packet_member(packet, name)
                if hashlib.sha256(raw).hexdigest() != manifest["files"][name]:
                    raise ValueError(f"Packet source hash differs: {name}")
                target = candidate / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        initialized = run_process(["git", "init", "-q"], candidate, timeout=10)
        if initialized["exit_code"] != 0:
            raise ValueError("Cannot initialize patch root")
        for index, name in enumerate(sorted(n for n in archive.namelist() if n.startswith("patches/"))):
            patch = candidate / f"patch-{index:03d}.patch"
            patch.write_bytes(archive.read(name))
            result = run_process(["git", "apply", str(patch)], candidate, timeout=15)
            if result["exit_code"] != 0 or result["timed_out"]:
                raise ValueError(f"Patch does not apply: {result['stderr'][:500]}")
    for name in paths:
        target = candidate / name
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"Unsafe candidate file: {name}")
    report = {"schema": "arcpuzzles-reported-acceptance-v1", "assignment_id": assignment_id,
              "version": version, "status": "reviewer_reported", "paths": paths,
              "candidate_file_sha256": {name: sha256(candidate / name) for name in paths},
              "candidate_path": str(candidate), "verification_status": "reviewer_reported",
              "training_admitted": False, "checks": [], "receipt_path": str(candidate / "ACCEPTANCE.json")}
    Path(report["receipt_path"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return returned, report, candidate


def integrate_full_candidate(catalog: Catalog, review_root: Path, assignment_id: str,
                             version: int, components: set[str], *, reviewer_reported: bool = False) -> dict:
    if not components <= COMPONENTS:
        raise ValueError(f"Unknown components: {sorted(components - COMPONENTS)}")
    review_root = review_root.resolve()
    with _lock(review_root):
        if not components:
            returned = _receipt(review_root, assignment_id, version)
            if returned["validation_status"] != "accepted":
                raise ValueError("Return failed static validation")
            with zipfile.ZipFile(returned["archive_path"]) as archive:
                results = json.loads(archive.read("RESULTS.json"))
            if any(item.get("kind") == "patch" for item in results["artifacts"]):
                raise ValueError("Patched return needs explicit component disposition")
            tid = returned["task_id"]
            evidence_path = catalog.root / "generators" / tid / "evidence" / f"review-{assignment_id}-v{version:04d}.json"
            if evidence_path.exists():
                raise FileExistsError("This return already has integration evidence")
            evidence = {"schema": "arcpuzzles-full-integration-v2", "assignment_id": assignment_id,
                        "version": version, "packet_id": returned["packet_id"], "components": [],
                        "integrated_files": {}, "disposition": "no_changes",
                        "stopping_reason": results.get("stopping_reason", "")}
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
            return {"status": "no_changes", "files": [], "components": [],
                    "evidence_path": str(evidence_path)}
        returned, check, candidate = (_reported if reviewer_reported else _checked)(review_root, assignment_id, version)
        contract = json.loads((review_root / "assignments" / assignment_id / "ASSIGNMENT.json").read_text())
        tid = contract["task_id"]
        paths = [path for path in check["paths"] if _component(path, tid) in components]
        if components - {_component(path, tid) for path in paths}:
            raise ValueError("Selected component has no checked change")
        evidence_path = catalog.root / "generators" / tid / "evidence" / f"review-{assignment_id}-v{version:04d}.json"
        if evidence_path.exists():
            raise FileExistsError("This return already has integration evidence")
        packet_path = review_root.parent / "var/review/full-packets" / returned["packet_id"] / "request.zip"
        desired: dict[str, bytes] = {}
        originals: dict[Path, bytes | None] = {}
        with zipfile.ZipFile(packet_path) as packet:
            for item in paths:
                relative = item.removeprefix("repo/")
                target = local_path(catalog.root, relative)
                if target.is_symlink():
                    raise ValueError(f"Authoritative symlink: {relative}")
                before = packet_member(packet, item) if item in packet_names(packet) else None
                current = target.read_bytes() if target.is_file() else None
                proposed = (candidate / item).read_bytes()
                if item == "repo/shared/data/canonical/puzzles.jsonl":
                    if before is None or current is None:
                        raise ValueError("Missing canonical ledger")
                    desired[relative] = _merge_rule(before, proposed, current,
                                                    contract["generator"]["rule_task_id"])
                else:
                    if current != before:
                        raise ValueError(f"Source drift or collision at {relative}; manual rebase required")
                    desired[relative] = proposed
                originals[target] = current
        stage = review_root.parent / "var/review/integration-staging" / assignment_id / f"{version:04d}"
        stage.mkdir(parents=True, exist_ok=True)
        for relative, raw in desired.items():
            staged = stage / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(raw)
        written: list[Path] = []
        try:
            for relative, raw in desired.items():
                target = local_path(catalog.root, relative)
                expected = originals[target]
                if (target.read_bytes() if target.is_file() else None) != expected:
                    raise ValueError(f"Source changed during integration: {relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(stage / relative, target)
                written.append(target)
            evidence = {"schema": "arcpuzzles-full-integration-v2", "assignment_id": assignment_id,
                        "version": version, "packet_id": returned["packet_id"],
                        "components": sorted(components),
                        "check_receipt": None if reviewer_reported else check["receipt_path"],
                        "verification_status": "reviewer_reported" if reviewer_reported else "independently_checked",
                        "reported_acceptance_receipt": check["receipt_path"] if reviewer_reported else None,
                        "integrated_files": {name: sha256(local_path(catalog.root, name)) for name in desired},
                        "rule_hash_at_integration": Catalog(catalog.root).describe(tid)["rule_hash"],
                        "source_hashes_at_assignment": contract["baseline_sha256"],
                        "disposition": "accepted"}
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
        except Exception:
            for target in written:
                raw = originals[target]
                if raw is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(raw)
            evidence_path.unlink(missing_ok=True)
            raise
        result = {"status": "integrated" if desired else "no_changes", "files": sorted(desired),
                  "components": sorted(components), "evidence_path": str(evidence_path)}
        if components:
            from .review_approval import approve_reviews
            result["approval"] = approve_reviews(catalog, review_root,
                                                 assignment_id=assignment_id, version=version)
    return result


def stage_full_combination(review_root: Path, sources: list[tuple[str, int]], out: Path) -> dict:
    review_root = review_root.resolve()
    out = out.resolve()
    if len(sources) < 2 or len(set(sources)) != len(sources):
        raise ValueError("Combination needs at least two distinct checked returns")
    checks, candidates, receipts = [], [], []
    for assignment_id, version in sources:
        receipt, check, candidate = _checked(review_root, assignment_id, version)
        checks.append(check)
        candidates.append(candidate)
        receipts.append(receipt)
    if len({r["packet_id"] for r in receipts}) != 1 or len({r["task_id"] for r in receipts}) != 1:
        raise ValueError("Combination sources must share packet and task")
    paths: dict[str, list[tuple[int, str]]] = {}
    for index, check in enumerate(checks):
        for path in check["paths"]:
            paths.setdefault(path, []).append((index, check["candidate_file_sha256"][path]))
    conflicts = {path: values for path, values in paths.items() if len({digest for _, digest in values}) > 1}
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": "arcpuzzles-full-combination-v2", "status": "conflict" if conflicts else "staged_unchecked",
              "sources": [{"assignment_id": aid, "version": ver, "zip_sha256": receipt["zip_sha256"]}
                          for (aid, ver), receipt in zip(sources, receipts)],
              "task_id": receipts[0]["task_id"], "packet_id": receipts[0]["packet_id"],
              "conflicts": conflicts, "paths": sorted(paths),
              "warning": "A combination needs its own fresh checks before integration"}
    if not conflicts:
        shutil.copytree(candidates[0] / "repo", out / "repo")
        for path, entries in paths.items():
            source_index = entries[-1][0]
            target = out / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidates[source_index] / path, target)
    (out / "COMBINATION.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return {**report, "directory": str(out)}


def record_full_disposition(review_root: Path, assignment_id: str, version: int,
                            kind: str, status: str, reason: str) -> dict:
    if kind not in COMPONENTS | {"audit", "feedback", "decision"} or status not in {
            "accepted", "rejected", "needs_evidence", "deferred", "implemented"} or not reason.strip():
        raise ValueError("Disposition needs valid kind, status, and nonempty reason")
    review_root = review_root.resolve()
    _receipt(review_root, assignment_id, version)
    path = review_root / "assignments" / assignment_id / f"dispositions-{version:04d}.json"
    with _lock(review_root):
        document = json.loads(path.read_text()) if path.is_file() else {
            "schema": "arcpuzzles-full-dispositions-v2", "assignment_id": assignment_id,
            "version": version, "items": []}
        document["items"].append({"kind": kind, "status": status, "reason": reason})
        path.write_text(json.dumps(document, sort_keys=True, indent=2) + "\n")
    return {"path": str(path), "item": document["items"][-1]}
