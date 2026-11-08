"""Retain and validate returned review ZIPs without touching source code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from typing import Iterable
import zipfile

from .review import _lock


MAX_MEMBERS = 256
MAX_EXPANDED = 25 * 1024 * 1024
ID_PATTERN = re.compile(r"review-[0-9a-f]{16}\Z")


def check_zip_budget(entries: Iterable[tuple[str, int]]) -> None:
    entries = list(entries)
    expanded = sum(size for _, size in entries)
    if len(entries) <= MAX_MEMBERS and expanded <= MAX_EXPANDED:
        return
    groups: dict[str, tuple[int, int]] = {}
    for name, size in entries:
        group = "/".join(name.split("/")[:2])
        count, total = groups.get(group, (0, 0))
        groups[group] = count + 1, total + size
    largest = sorted(groups.items(), key=lambda row: (-row[1][0], -row[1][1], row[0]))[:6]
    details = "; ".join(f"{name}: members={count}, bytes={size}"
                        for name, (count, size) in largest)
    raise ValueError(f"Review ZIP exceeds limit: members={len(entries)}/{MAX_MEMBERS}; "
                     f"expanded_bytes={expanded}/{MAX_EXPANDED}; largest groups: {details}")


def scan_zip(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    check_zip_budget((info.filename, info.file_size) for info in infos)
    seen: set[str] = set()
    files = []
    for info in infos:
        name = info.filename
        parts = PurePosixPath(name).parts
        normalized = PurePosixPath(name.rstrip("/")).as_posix()
        if (not name or name.startswith("/") or "\\" in name or ":" in name
                or normalized != name.rstrip("/")
                or any(part in {".", "..", ""} for part in parts)
                or name.startswith("./")):
            raise ValueError(f"Unsafe ZIP path: {name!r}")
        key = normalized.casefold()
        if key in seen:
            raise ValueError(f"ZIP member collision: {name}")
        seen.add(key)
        mode = (info.external_attr >> 16) & 0xffff
        kind = stat.S_IFMT(mode)
        if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or mode & 0o111:
            raise ValueError(f"Unsafe ZIP member type or executable: {name}")
        if info.flag_bits & 1 or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise ValueError(f"Unsupported ZIP member: {name}")
        if info.is_dir():
            if kind not in {0, stat.S_IFDIR}:
                raise ValueError(f"Unsafe ZIP directory: {name}")
        else:
            if kind == stat.S_IFDIR:
                raise ValueError(f"Unsafe ZIP file: {name}")
            files.append(info)
    return files


def _declared(results: dict) -> set[str]:
    names = set()
    for field in ("patches", "checks"):
        values = results.get(field, [])
        if not isinstance(values, list):
            raise ValueError(f"Invalid {field} declaration; expected list")
        for item in values:
            name = item if isinstance(item, str) else item.get("path")
            if not isinstance(name, str) or not name:
                raise ValueError(f"Invalid {field} declaration")
            names.add(name)
    for field in ("question_answer",):
        item = results.get(field)
        if item:
            names.add(item if isinstance(item, str) else item["path"])
    return names


def intake(review_root: Path, zip_path: Path) -> dict:
    review_root = review_root.resolve()
    raw = zip_path.read_bytes()
    zip_sha = hashlib.sha256(raw).hexdigest()
    archive_root = review_root.parent / "var/review/returns"
    inbox = archive_root / "_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    preserved = inbox / f"{zip_sha}.zip"
    if not preserved.exists():
        preserved.write_bytes(raw)
    status, reason, identifier, files, results = "accepted", "", "unmapped", [], None
    try:
        with zipfile.ZipFile(preserved) as archive:
            files = scan_zip(archive)
            names = {item.filename for item in files}
            if "ASSIGNMENT.json" not in names:
                status, reason = "mapping_required", "No immutable ASSIGNMENT.json; map historical return manually"
            else:
                echoed = archive.read("ASSIGNMENT.json")
                contract = json.loads(echoed)
                candidate_id = contract.get("assignment_id", "")
                if ID_PATTERN.fullmatch(candidate_id):
                    identifier = candidate_id
                assignment = review_root / "assignments" / identifier / "ASSIGNMENT.json"
                if not assignment.is_file() or echoed != assignment.read_bytes():
                    raise ValueError("ASSIGNMENT.json does not match a current prepared assignment")
                required = {"ASSIGNMENT.json", "RESULTS.json", "REVIEW.md", "FEEDBACK_TO_CODEX.md"}
                if not required <= names:
                    raise ValueError(f"Missing required return files: {sorted(required - names)}")
                results = json.loads(archive.read("RESULTS.json"))
                if (not isinstance(results, dict) or results.get("schema") != "arcpuzzles-review-results-v1"
                        or results.get("assignment_id") != identifier
                        or results.get("generator_id") != contract["task_id"]):
                    raise ValueError("RESULTS.json assignment or generator mismatch")
                if results.get("completion_state") not in {"complete", "blocked", "in_progress"}:
                    raise ValueError("RESULTS.json completion_state must be complete, blocked, or in_progress")
                declared = _declared(results)
                if not declared <= names:
                    raise ValueError(f"Declared return file missing: {sorted(declared - names)}")
                undocumented = {name for name in names if name.startswith(("patches/", "checks/", "QUESTION_ANSWER"))} - declared
                if undocumented:
                    raise ValueError(f"Return artifact must be declared in RESULTS.json: {sorted(undocumented)}")
                for info in files:
                    archive.read(info)  # CRC and decompression errors must fail before extraction.
                if results["completion_state"] == "in_progress":
                    status, reason = "partial", "Reviewer marked RESULTS.json in_progress"
    except (ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError, zipfile.BadZipFile, RuntimeError) as exc:
        status, reason = "rejected", str(exc)
    with _lock(review_root):
        receipts = review_root / (f"assignments/{identifier}/returns" if identifier != "unmapped" else "returns/unmapped")
        receipts.mkdir(parents=True, exist_ok=True)
        for old in sorted(receipts.glob("return-*.json")):
            value = json.loads(old.read_text())
            if value["zip_sha256"] == zip_sha:
                return value
        version = len(list(receipts.glob("return-*.json"))) + 1
        destination = archive_root / identifier / f"{version:04d}"
        destination.mkdir(parents=True, exist_ok=False)
        retained = destination / "original.zip"
        shutil.copy2(preserved, retained)
        if status in {"accepted", "partial"}:
            with zipfile.ZipFile(retained) as archive:
                extracted = destination / "extracted"
                extracted.mkdir()
                for info in files:
                    target = extracted / info.filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
        receipt = {"schema": "arcpuzzles-review-return-v1", "assignment_id": identifier,
                   "version": version, "zip_sha256": zip_sha, "status": status,
                   "reason": reason, "archive_path": str(retained)}
        content = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
        receipt_path = receipts / f"return-{version:04d}-{hashlib.sha256(content.encode()).hexdigest()[:16]}.json"
        receipt["receipt_path"] = str(receipt_path)
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        return receipt
