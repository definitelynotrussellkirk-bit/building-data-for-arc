#!/usr/bin/env python3
"""Verify an ARCpuzzles review-response directory or ZIP without mutating it.

The verifier checks the sealed response hashes, nested evidence-bundle inventory,
archive/path safety, declared source-delta scope, referenced receipts, solve-source
bindings, and cross-file assignment metadata.  With ``--original-worktree`` it
also checks the uploaded baseline hashes and runs ``git apply --check`` against a
fresh extraction; it never applies the patch.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
import zipfile

REQUIRED_ROOT = (
    "ASSIGNMENT.json",
    "INTAKE.json",
    "RESULTS.json",
    "REVIEW.md",
    "EVIDENCE-BUNDLE.json",
    "EVIDENCE-BUNDLE.tar.gz",
    "patches/source.patch",
    "solve/summary.json",
    "solve/source/generator.py",
    "solve-blind/summary.json",
    "solve-blind/source/generator.py",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(name: str) -> bool:
    if not name or "\\" in name or "\x00" in name or ":" in name:
        return False
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and path.as_posix() == name
        and all(part not in ("", ".", "..") for part in path.parts)
    )


class _DirectoryReader:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.issues: list[str] = []
        if not self.root.is_dir():
            self.issues.append(f"not a directory: {root}")

    def names(self) -> set[str]:
        if not self.root.is_dir():
            return set()
        names: set[str] = set()
        for path in self.root.rglob("*"):
            if path.is_symlink():
                self.issues.append(f"symlink in response directory: {path.relative_to(self.root).as_posix()}")
                continue
            if path.is_file():
                names.add(path.relative_to(self.root).as_posix())
        return names

    def exists(self, name: str) -> bool:
        if not _safe_relative(name):
            return False
        path = (self.root / name).resolve()
        return path.is_relative_to(self.root) and path.is_file() and not path.is_symlink()

    def read(self, name: str) -> bytes:
        if not self.exists(name):
            raise FileNotFoundError(name)
        return (self.root / name).read_bytes()

    def close(self) -> None:
        return None


class _ZipReader:
    def __init__(self, path: Path):
        self.path = path
        self.issues: list[str] = []
        self.archive: zipfile.ZipFile | None = None
        self.prefix = ""
        try:
            self.archive = zipfile.ZipFile(path)
        except (OSError, zipfile.BadZipFile) as exc:
            self.issues.append(f"cannot open ZIP: {exc}")
            return

        infos = self.archive.infolist()
        seen: set[str] = set()
        logical_files: list[str] = []
        for info in infos:
            name = info.filename.rstrip("/") if info.is_dir() else info.filename
            if not _safe_relative(name):
                self.issues.append(f"unsafe ZIP path: {info.filename!r}")
            if info.filename in seen:
                self.issues.append(f"duplicate ZIP member: {info.filename}")
            seen.add(info.filename)
            if info.flag_bits & 0x1:
                self.issues.append(f"encrypted ZIP member is unsupported: {info.filename}")
            mode = (info.external_attr >> 16) & 0xFFFF
            if mode and stat.S_IFMT(mode) == stat.S_IFLNK:
                self.issues.append(f"symlink ZIP member is unsupported: {info.filename}")
            if not info.is_dir():
                logical_files.append(info.filename)

        raw = set(logical_files)
        if all(name in raw for name in REQUIRED_ROOT):
            self.prefix = ""
        else:
            first_parts = {PurePosixPath(name).parts[0] for name in logical_files if PurePosixPath(name).parts}
            if len(first_parts) == 1:
                candidate = next(iter(first_parts)) + "/"
                if all(candidate + name in raw for name in REQUIRED_ROOT):
                    self.prefix = candidate

        bad = self.archive.testzip()
        if bad is not None:
            self.issues.append(f"ZIP CRC failure: {bad}")

    def names(self) -> set[str]:
        if self.archive is None:
            return set()
        out: set[str] = set()
        for info in self.archive.infolist():
            if info.is_dir() or not info.filename.startswith(self.prefix):
                continue
            logical = info.filename[len(self.prefix):]
            if logical:
                out.add(logical)
        return out

    def exists(self, name: str) -> bool:
        if self.archive is None or not _safe_relative(name):
            return False
        try:
            info = self.archive.getinfo(self.prefix + name)
        except KeyError:
            return False
        return not info.is_dir()

    def read(self, name: str) -> bytes:
        if self.archive is None:
            raise FileNotFoundError(name)
        return self.archive.read(self.prefix + name)

    def close(self) -> None:
        if self.archive is not None:
            self.archive.close()


def _reader(path: Path):
    return _DirectoryReader(path) if path.is_dir() else _ZipReader(path)


def _load_json(reader, name: str, issues: list[str]) -> Any | None:
    try:
        return json.loads(reader.read(name))
    except FileNotFoundError:
        issues.append(f"missing required file: {name}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        issues.append(f"invalid JSON {name}: {exc}")
    return None


def _verify_evidence_bundle(reader, manifest: Any, issues: list[str], facts: dict[str, Any]) -> set[str]:
    if not isinstance(manifest, dict):
        issues.append("EVIDENCE-BUNDLE.json must be an object")
        return set()
    archive_name = manifest.get("archive")
    if not isinstance(archive_name, str) or not _safe_relative(archive_name):
        issues.append("evidence manifest has an invalid archive path")
        return set()
    try:
        archive_bytes = reader.read(archive_name)
    except FileNotFoundError:
        issues.append(f"missing evidence archive: {archive_name}")
        return set()
    expected_archive_hash = manifest.get("archive_sha256")
    got_archive_hash = _sha256(archive_bytes)
    if got_archive_hash != expected_archive_hash:
        issues.append(
            f"evidence archive hash mismatch: {got_archive_hash} != {expected_archive_hash}"
        )

    rows = manifest.get("files")
    if not isinstance(rows, list):
        issues.append("evidence manifest files must be an array")
        return set()
    declared: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            issues.append(f"evidence manifest row {index} is not an object")
            continue
        name = row.get("path")
        if not isinstance(name, str) or not _safe_relative(name):
            issues.append(f"unsafe evidence manifest path at row {index}: {name!r}")
            continue
        if name in declared:
            issues.append(f"duplicate evidence manifest path: {name}")
        declared[name] = row

    try:
        archive = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz")
    except (tarfile.TarError, OSError) as exc:
        issues.append(f"cannot open evidence archive: {exc}")
        return set()

    actual: dict[str, bytes] = {}
    seen_members: set[str] = set()
    try:
        for member in archive.getmembers():
            if not _safe_relative(member.name):
                issues.append(f"unsafe evidence TAR path: {member.name!r}")
            if member.name in seen_members:
                issues.append(f"duplicate evidence TAR member: {member.name}")
            seen_members.add(member.name)
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                issues.append(f"unsupported evidence TAR member type: {member.name}")
                continue
            if member.isfile():
                handle = archive.extractfile(member)
                if handle is None:
                    issues.append(f"cannot read evidence TAR member: {member.name}")
                    continue
                actual[member.name] = handle.read()
    finally:
        archive.close()

    if set(actual) != set(declared):
        missing = sorted(set(declared) - set(actual))
        extra = sorted(set(actual) - set(declared))
        if missing:
            issues.append(f"evidence TAR is missing declared files: {missing[:10]}")
        if extra:
            issues.append(f"evidence TAR has undeclared files: {extra[:10]}")

    expanded_bytes = 0
    for name, data in actual.items():
        expanded_bytes += len(data)
        row = declared.get(name)
        if row is None:
            continue
        if row.get("bytes") != len(data):
            issues.append(f"evidence size mismatch {name}: {len(data)} != {row.get('bytes')}")
        got = _sha256(data)
        if row.get("sha256") != got:
            issues.append(f"evidence hash mismatch {name}: {got} != {row.get('sha256')}")

    if manifest.get("count") != len(actual):
        issues.append(f"evidence count mismatch: {len(actual)} != {manifest.get('count')}")
    if manifest.get("expanded_bytes") != expanded_bytes:
        issues.append(
            f"evidence expanded-byte mismatch: {expanded_bytes} != {manifest.get('expanded_bytes')}"
        )
    facts["evidence_files"] = len(actual)
    facts["evidence_expanded_bytes"] = expanded_bytes
    facts["evidence_archive_sha256"] = got_archive_hash
    return set(actual)


def _verify_original_worktree(
    worktree: Path,
    assignment: dict[str, Any],
    patch_bytes: bytes,
    issues: list[str],
    facts: dict[str, Any],
) -> None:
    root = worktree.resolve()
    if not root.is_dir():
        issues.append(f"original worktree does not exist: {worktree}")
        return
    baseline = assignment.get("baseline_sha256")
    if not isinstance(baseline, dict):
        issues.append("ASSIGNMENT baseline_sha256 must be an object")
        return
    checked = 0
    for name, expected in baseline.items():
        if not isinstance(name, str) or not _safe_relative(name):
            issues.append(f"unsafe baseline path: {name!r}")
            continue
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            issues.append(f"missing original baseline file: {name}")
            continue
        got = _sha256(path.read_bytes())
        if got != expected:
            issues.append(f"original baseline hash mismatch {name}: {got} != {expected}")
        checked += 1
    facts["original_baseline_files_checked"] = checked

    with tempfile.NamedTemporaryFile(suffix=".patch", delete=False) as handle:
        handle.write(patch_bytes)
        patch_path = Path(handle.name)
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "apply", "--check", str(patch_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        issues.append(f"git apply --check could not run: {exc}")
    else:
        facts["git_apply_check_exit_code"] = completed.returncode
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            issues.append(f"git apply --check failed: {detail}")
    finally:
        patch_path.unlink(missing_ok=True)


def verify_path(path: str | Path, *, original_worktree: str | Path | None = None) -> dict[str, Any]:
    target = Path(path)
    reader = _reader(target)
    issues = list(reader.issues)
    facts: dict[str, Any] = {"target": str(target), "target_kind": "directory" if target.is_dir() else "zip"}
    try:
        names = reader.names()
        for name in REQUIRED_ROOT:
            if name not in names:
                issues.append(f"missing required file: {name}")

        assignment = _load_json(reader, "ASSIGNMENT.json", issues)
        intake = _load_json(reader, "INTAKE.json", issues)
        results = _load_json(reader, "RESULTS.json", issues)
        manifest = _load_json(reader, "EVIDENCE-BUNDLE.json", issues)
        solve = _load_json(reader, "solve/summary.json", issues)
        blind = _load_json(reader, "solve-blind/summary.json", issues)

        if isinstance(intake, dict):
            root_hashes = intake.get("evidence_sha256")
            if not isinstance(root_hashes, dict):
                issues.append("INTAKE evidence_sha256 must be an object")
            else:
                checked = 0
                for name, expected in root_hashes.items():
                    if not isinstance(name, str) or not _safe_relative(name):
                        issues.append(f"unsafe root evidence path: {name!r}")
                        continue
                    if not reader.exists(name):
                        issues.append(f"missing root evidence: {name}")
                        continue
                    got = _sha256(reader.read(name))
                    if got != expected:
                        issues.append(f"root hash mismatch {name}: {got} != {expected}")
                    checked += 1
                facts["root_evidence_files_checked"] = checked

        evidence_names = _verify_evidence_bundle(reader, manifest, issues, facts)

        try:
            patch_bytes = reader.read("patches/source.patch")
            patch_text = patch_bytes.decode("utf-8")
        except FileNotFoundError:
            patch_bytes = b""
            patch_text = ""
        except UnicodeDecodeError as exc:
            patch_bytes = b""
            patch_text = ""
            issues.append(f"source patch is not UTF-8 text: {exc}")

        pairs = re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch_text, flags=re.MULTILINE)
        patch_paths: list[str] = []
        for old, new in pairs:
            if old != new:
                issues.append(f"source patch rename is outside the declared model: {old} -> {new}")
            if not _safe_relative(new):
                issues.append(f"unsafe source patch path: {new!r}")
            patch_paths.append(new)
        if "GIT binary patch" in patch_text or re.search(r"^Binary files ", patch_text, re.MULTILINE):
            issues.append("binary source patch is unsupported")
        if isinstance(intake, dict):
            declared_paths = intake.get("changed_paths")
            if not isinstance(declared_paths, list) or any(not isinstance(x, str) for x in declared_paths):
                issues.append("INTAKE changed_paths must be an array of strings")
            elif sorted(declared_paths) != sorted(patch_paths):
                issues.append(
                    f"patch paths differ from INTAKE changed_paths: patch={sorted(patch_paths)!r}, "
                    f"declared={sorted(declared_paths)!r}"
                )
        facts["patch_paths"] = len(patch_paths)
        facts["patch_path_list"] = patch_paths
        facts["patch_sha256"] = _sha256(patch_bytes) if patch_bytes else None

        assignment_id = assignment.get("assignment_id") if isinstance(assignment, dict) else None
        facts["assignment_id"] = assignment_id
        for label, obj in (("INTAKE", intake), ("RESULTS", results), ("solve summary", solve), ("blind solve summary", blind)):
            if isinstance(obj, dict) and obj.get("assignment_id") != assignment_id:
                issues.append(
                    f"{label} assignment_id mismatch: {obj.get('assignment_id')!r} != {assignment_id!r}"
                )
        if isinstance(assignment, dict) and isinstance(intake, dict):
            for key in ("packet_id", "task_id"):
                if intake.get(key) != assignment.get(key):
                    issues.append(f"INTAKE {key} mismatch: {intake.get(key)!r} != {assignment.get(key)!r}")
        if isinstance(results, dict) and results.get("completion_state") != "complete":
            issues.append(f"RESULTS completion_state is not complete: {results.get('completion_state')!r}")
        if isinstance(intake, dict) and intake.get("completion_state") != "complete":
            issues.append(f"INTAKE completion_state is not complete: {intake.get('completion_state')!r}")

        # Cross-check the nested-bundle copy in INTAKE.
        if isinstance(intake, dict) and isinstance(manifest, dict):
            summary = intake.get("evidence_bundle")
            if not isinstance(summary, dict):
                issues.append("INTAKE evidence_bundle must be an object")
            else:
                for key in ("archive", "archive_sha256", "count", "expanded_bytes"):
                    if summary.get(key) != manifest.get(key):
                        issues.append(
                            f"INTAKE evidence_bundle.{key} mismatch: {summary.get(key)!r} != {manifest.get(key)!r}"
                        )

        # Every verification command must point at retained evidence.
        commands = results.get("verification_commands") if isinstance(results, dict) else None
        if not isinstance(commands, list):
            issues.append("RESULTS verification_commands must be an array")
            commands = []
        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                issues.append(f"verification command {index} is not an object")
                continue
            paths = command.get("evidence_paths", [])
            if not isinstance(paths, list):
                issues.append(f"verification command {index} evidence_paths is not an array")
                continue
            for name in paths:
                if not isinstance(name, str) or not _safe_relative(name):
                    issues.append(f"verification command {index} has unsafe evidence path: {name!r}")
                elif not reader.exists(name) and name not in evidence_names:
                    issues.append(f"verification command {index} references missing evidence: {name}")
        facts["verification_commands"] = len(commands)

        # Bind the human-readable final hash and solve summaries to shipped source.
        if reader.exists("REVIEW.md") and reader.exists("solve/source/generator.py"):
            review_text = reader.read("REVIEW.md").decode("utf-8", errors="replace")
            match = re.search(r"final generator SHA-256 `([0-9a-f]{64})`", review_text)
            if not match:
                issues.append("REVIEW.md does not declare a final generator SHA-256")
            else:
                final_hash = _sha256(reader.read("solve/source/generator.py"))
                facts["final_generator_sha256"] = final_hash
                if final_hash != match.group(1):
                    issues.append(
                        f"REVIEW final generator hash mismatch: {final_hash} != {match.group(1)}"
                    )
                if isinstance(intake, dict):
                    declared = (intake.get("reviewer_solve") or {}).get("generator_hash")
                    if declared != final_hash:
                        issues.append(f"INTAKE reviewer_solve generator hash mismatch: {declared} != {final_hash}")
                if isinstance(solve, dict) and solve.get("generator_hash") != final_hash:
                    issues.append(
                        f"solve summary generator hash mismatch: {solve.get('generator_hash')} != {final_hash}"
                    )

        if reader.exists("solve-blind/source/generator.py"):
            blind_hash = _sha256(reader.read("solve-blind/source/generator.py"))
            facts["blind_generator_sha256"] = blind_hash
            if isinstance(intake, dict):
                declared = (intake.get("reviewer_blind_solve") or {}).get("generator_hash")
                if declared != blind_hash:
                    issues.append(
                        f"INTAKE reviewer_blind_solve generator hash mismatch: {declared} != {blind_hash}"
                    )
            if isinstance(blind, dict) and blind.get("generator_hash") != blind_hash:
                issues.append(
                    f"blind solve summary generator hash mismatch: {blind.get('generator_hash')} != {blind_hash}"
                )

        # Parse all shipped root JSON files listed by INTAKE, catching malformed receipts early.
        if isinstance(intake, dict) and isinstance(intake.get("evidence_sha256"), dict):
            parsed_json = 0
            for name in intake["evidence_sha256"]:
                if isinstance(name, str) and name.endswith(".json") and reader.exists(name):
                    try:
                        json.loads(reader.read(name))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        issues.append(f"invalid root evidence JSON {name}: {exc}")
                    parsed_json += 1
            facts["root_json_files_parsed"] = parsed_json

        if original_worktree is not None and isinstance(assignment, dict):
            _verify_original_worktree(
                Path(original_worktree), assignment, patch_bytes, issues, facts
            )
    finally:
        reader.close()

    # Stable output makes reports diffable and machine-friendly.
    issues = list(dict.fromkeys(issues))
    return {
        "schema": "arcpuzzles-review-response-verification-v1",
        "ok": not issues,
        "issues": issues,
        "facts": facts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="review-response directory or ZIP")
    parser.add_argument(
        "--original-worktree",
        type=Path,
        help="optional fresh extraction root for baseline hashes and git apply --check",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON (default is a compact text report)")
    args = parser.parse_args(argv)
    report = verify_path(args.package, original_worktree=args.original_worktree)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PASS" if report["ok"] else "FAIL")
        for issue in report["issues"]:
            print(f"- {issue}")
        for key, value in sorted(report["facts"].items()):
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
