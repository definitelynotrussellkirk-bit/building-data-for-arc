#!/usr/bin/env python3
"""Verify an ARCpuzzles full-packet-v2 ZIP without extracting or executing it.

Required-file hashes and canonical manifest encoding follow review.py verify.
Additionally fail on unsafe paths, non-regular entries and duplicate members.
Unlisted safe files are reported but do not fail required-inventory verification,
matching review.py's policy. Memory holds the ZIP index and JSON manifest; file
payloads are hashed in 1 MiB chunks. This is an optional authoring aid, not the
official verifier or a semantic/code-safety review. The manifest is not signed.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import stat
import time
import zipfile
import zlib

CHUNK = 1024 * 1024
MANIFEST = "WORK/PACKET-MANIFEST.json"
SCHEMA = "arcpuzzles-full-packet-v2"
ROOT_ENTRIES = {"START-HERE.md", "review.py"}


def digest_stream(handle):
    digest = hashlib.sha256()
    size = 0
    while chunk := handle.read(CHUNK):
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def path_error(name, directory=False):
    if not isinstance(name, str) or not name:
        return "empty or non-string name"
    if "\x00" in name or "\\" in name:
        return "NUL or backslash in path"
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return "absolute or drive-qualified path"
    parts = name[:-1].split("/") if directory and name.endswith("/") else name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return "empty, dot or parent path component"
    return None


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def verify_packet(archive):
    archive = Path(archive).resolve()
    start = time.monotonic()
    report = {
        "schema": "arcpuzzles-streaming-zip-verification-v1",
        "archive": str(archive),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "archive_sha256": None,
        "manifest_sha256": None,
        "manifest_schema": None,
        "counts": {},
        "missing": [], "changed": [], "unsafe": [], "duplicates": [],
        "unreadable": [], "manifest_errors": [], "unlisted_files": [],
        "scope": "SHA-256 of every manifest-listed WORK file and both root entry files; canonical manifest encoding; ZIP path/type/duplicate checks. No extraction or archive-code execution.",
        "limits": "No authenticity proof: the manifest is unsigned. No generator/runtime semantics checked. Safe unlisted files are reported but not hashed, matching the official required-inventory policy. Memory includes the ZIP index and manifest JSON.",
    }
    counts = report["counts"]
    try:
        with archive.open("rb") as handle:
            report["archive_sha256"], counts["archive_bytes"] = digest_stream(handle)
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            names = defaultdict(list)
            bad_names = set()
            directories = set()
            file_names = set()
            counts.update({
                "members": len(infos),
                "files": sum(not i.is_dir() for i in infos),
                "explicit_directories": sum(i.is_dir() for i in infos),
                "declared_uncompressed_bytes": sum(i.file_size for i in infos),
                "compressed_member_bytes": sum(i.compress_size for i in infos),
                "expected_workspace_files": 0, "expected_root_files": 0,
                "required_files": 0, "hashed_required_files": 0,
                "matched_required_files": 0, "hashed_required_bytes": 0,
            })
            for info in infos:
                name = info.filename
                names[name].append(info)
                error = path_error(info.orig_filename, info.is_dir())
                kind = stat.S_IFMT(info.external_attr >> 16)
                allowed_kind = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
                if kind not in (0, allowed_kind):
                    error = "symlink, special file, or path/type mismatch"
                if info.flag_bits & 1:
                    error = "encrypted member cannot be verified without a password"
                if error:
                    report["unsafe"].append({"path": info.orig_filename, "reason": error})
                    bad_names.add(name)
                    continue
                parts = name.rstrip("/").split("/")
                for length in range(1, len(parts) + int(info.is_dir())):
                    directories.add("/".join(parts[:length]))
                if not info.is_dir():
                    file_names.add(name)
            counts["directories_including_implicit"] = len(directories)
            for name, rows in names.items():
                if len(rows) > 1:
                    report["duplicates"].append({"path": name, "occurrences": len(rows)})
            for name in sorted(file_names & directories):
                report["unsafe"].append({"path": name, "reason": "file is also required as a directory"})
                bad_names.add(name)
            manifest = None
            if MANIFEST not in names:
                report["missing"].append(MANIFEST)
            elif len(names[MANIFEST]) != 1 or MANIFEST in bad_names or names[MANIFEST][0].is_dir():
                report["manifest_errors"].append("Manifest must be one regular, safe file")
            else:
                try:
                    with z.open(names[MANIFEST][0]) as handle:
                        raw = b"".join(iter(lambda: handle.read(CHUNK), b""))
                    report["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
                    manifest = json.loads(raw, object_pairs_hook=unique_json_object)
                    if not isinstance(manifest, dict):
                        raise ValueError("Manifest must be a JSON object")
                    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
                    if raw != canonical:
                        report["manifest_errors"].append("Manifest encoding is not canonical JSON")
                    report["manifest_schema"] = manifest.get("schema")
                    if manifest.get("schema") != SCHEMA:
                        report["manifest_errors"].append(f"Unsupported manifest schema; expected {SCHEMA}")
                except (ValueError, UnicodeError, RuntimeError, OSError, zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError) as exc:
                    report["manifest_errors"].append(str(exc))
                    manifest = None
            expected = {}
            if manifest is not None:
                layout = manifest.get("layout")
                files = manifest.get("files")
                if not isinstance(layout, dict) or layout.get("workspace") != "WORK":
                    report["manifest_errors"].append("layout.workspace must be WORK")
                    layout = {}
                entries = layout.get("entry_files")
                if not isinstance(entries, dict) or set(entries) != ROOT_ENTRIES:
                    report["manifest_errors"].append("layout.entry_files must contain exactly START-HERE.md and review.py")
                    entries = {}
                if not isinstance(files, dict):
                    report["manifest_errors"].append("files must be a path-to-SHA-256 object")
                    files = {}
                counts["expected_workspace_files"] = len(files)
                counts["expected_root_files"] = len(entries)
                for prefix, inventory in (("WORK/", files), ("", entries)):
                    for relative, digest in inventory.items():
                        error = path_error(relative)
                        if error:
                            report["unsafe"].append({"path": relative, "reason": "manifest: " + error})
                            continue
                        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                            report["manifest_errors"].append(f"Invalid SHA-256 for {prefix + relative}")
                            continue
                        expected[prefix + relative] = digest
                counts["required_files"] = len(expected)
                for name, digest in expected.items():
                    rows = names.get(name, [])
                    if not rows:
                        report["missing"].append(name)
                        continue
                    if len(rows) != 1 or name in bad_names:
                        continue
                    if rows[0].is_dir():
                        report["unsafe"].append({"path": name, "reason": "required file is a directory"})
                        continue
                    try:
                        with z.open(rows[0]) as handle:
                            actual, size = digest_stream(handle)
                        counts["hashed_required_files"] += 1
                        counts["hashed_required_bytes"] += size
                        if actual == digest:
                            counts["matched_required_files"] += 1
                        else:
                            report["changed"].append({"path": name, "expected_sha256": digest, "actual_sha256": actual})
                    except (RuntimeError, OSError, zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError) as exc:
                        report["unreadable"].append({"path": name, "reason": str(exc)})
                report["unlisted_files"] = sorted(file_names - set(expected) - {MANIFEST})
    except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        report["unreadable"].append({"path": str(archive), "reason": str(exc)})
    failed = any(report[k] for k in ("missing", "changed", "unsafe", "duplicates", "unreadable", "manifest_errors"))
    report["verified"] = not failed
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--out", type=Path, help="Write a full JSON report; stdout remains a compact summary")
    args = parser.parse_args(argv)
    if args.out and args.out.resolve() == args.zip_path.resolve():
        parser.error("--out must not overwrite the input archive")
    report = verify_packet(args.zip_path)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        summary = {"verified": report["verified"], "archive_sha256": report["archive_sha256"],
                   "counts": report["counts"], "elapsed_seconds": report["elapsed_seconds"],
                   "issues": {k: len(report[k]) for k in ("missing", "changed", "unsafe", "duplicates", "unreadable", "manifest_errors", "unlisted_files")}}
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
