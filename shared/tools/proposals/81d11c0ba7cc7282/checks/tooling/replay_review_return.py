#!/usr/bin/env python3
"""Passive proposal: safely replay one review source patch in a fresh packet."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
import zlib


ORIGINAL_MAX_MEMBERS = 100000
ORIGINAL_MAX_EXPANDED = 2 * 1024 * 1024 * 1024
RETURN_MAX_MEMBERS = 256
RETURN_MAX_EXPANDED = 25 * 1024 * 1024
MAX_PATCH = 25 * 1024 * 1024
PATCH_MEMBER = "patches/source.patch"
DIFF = re.compile(r"diff --git a/(\S+) b/(\S+)")
HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?")


class ReplayError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def safe_path(name: str) -> str:
    """Accept normalized, portable relative names; never permit Git internals."""
    if (not name or name.startswith("/") or "\\" in name or ":" in name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise ReplayError(f"Unsafe path: {name!r}")
    parts = name.split("/")
    if any(not part or part in {".", ".."} or part.casefold() == ".git"
           or part.endswith((" ", "."))
           or re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part, re.I)
           for part in parts):
        raise ReplayError(f"Unsafe path: {name!r}")
    if PurePosixPath(name).as_posix() != name:
        raise ReplayError(f"Non-normalized path: {name!r}")
    return name


def validate_zip(archive: zipfile.ZipFile, *, kind: str = "original",
                 allow_case_distinct_paths: bool = False) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if kind not in {"original", "return"}:
        raise ReplayError(f"Unknown ZIP role: {kind}")
    if allow_case_distinct_paths and kind != "original":
        raise ReplayError("Case-distinct paths may only be enabled for the original ZIP")
    max_members, max_expanded = ((ORIGINAL_MAX_MEMBERS, ORIGINAL_MAX_EXPANDED) if kind == "original"
                                 else (RETURN_MAX_MEMBERS, RETURN_MAX_EXPANDED))
    expanded = sum(info.file_size for info in infos)
    if len(infos) > max_members or expanded > max_expanded:
        raise ReplayError(f"{kind} ZIP exceeds limits: members={len(infos)}/{max_members}; "
                          f"expanded_bytes={expanded}/{max_expanded}")
    seen, regular = set(), set()
    path_key = str if allow_case_distinct_paths else str.casefold
    for info in infos:
        # zipfile truncates filename at NUL; checking the original detects that case.
        if info.orig_filename != info.filename:
            raise ReplayError(f"Truncated ZIP member name: {info.orig_filename!r}")
        name = safe_path(info.filename[:-1] if info.is_dir() else info.filename)
        key = path_key(name)
        if key in seen:
            raise ReplayError(f"Duplicate ZIP member: {name}")
        seen.add(key)
        mode = (info.external_attr >> 16) & 0xffff
        file_kind = stat.S_IFMT(mode)
        if (file_kind not in {0, stat.S_IFREG, stat.S_IFDIR}
                or (file_kind == stat.S_IFDIR and not info.is_dir())
                or (file_kind == stat.S_IFREG and info.is_dir())
                or mode & 0o7000 or (not info.is_dir() and mode & 0o111)):
            raise ReplayError(f"Unsafe ZIP member type or permissions: {name}")
        if (info.flag_bits & 1 or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                or info.file_size < 0 or (info.is_dir() and info.file_size)):
            raise ReplayError(f"Unsupported ZIP member: {name}")
        if not info.is_dir():
            regular.add(key)
    for key in seen:
        if any(path_key(parent.as_posix()) in regular for parent in PurePosixPath(key).parents):
            raise ReplayError(f"ZIP file/directory collision: {key}")
    return infos


def destination_case_sensitive(parent: Path) -> bool:
    """Probe this destination filesystem using two exclusive, case-distinct files."""
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-case-probe-", dir=parent) as temporary:
        lower = Path(temporary) / "casecheck"
        upper = Path(temporary) / "CASECHECK"
        with lower.open("xb") as handle:
            handle.write(b"lower")
        try:
            with upper.open("xb") as handle:
                handle.write(b"upper")
        except FileExistsError:
            return False
        return (not lower.samefile(upper)
                and lower.read_bytes() == b"lower" and upper.read_bytes() == b"upper")


def _unique_json_object(pairs: list[tuple]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise ReplayError(f"Duplicate JSON member in expected-files manifest: {name}")
        result[name] = value
    return result


def load_expected_files_manifest(path: Path, paths: list[dict]) -> tuple[list[dict], dict]:
    """Bind the complete exact patch path set before creating the destination."""
    with path.open("rb") as handle:
        raw = handle.read(MAX_PATCH + 1)
    if len(raw) > MAX_PATCH:
        raise ReplayError("Expected-files manifest exceeds the 25 MiB limit")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReplayError("Expected-files manifest must be UTF-8 JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("changes"), list):
        raise ReplayError("Expected-files manifest must contain a changes list")
    expected, seen = [], set()
    for row in data["changes"]:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ReplayError("Every expected change must have a string path")
        name = safe_path(row["path"])
        if not name.startswith("repo/"):
            raise ReplayError("Expected change paths must begin with repo/")
        if name in seen:
            raise ReplayError(f"Duplicate expected change path: {name}")
        seen.add(name)
        digest = row.get("after_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ReplayError(f"Expected change needs a 64-digit after_sha256: {name}")
        if type(row.get("new_file")) is not bool:
            raise ReplayError(f"Expected change needs a boolean new_file: {name}")
        entry = {"path": name, "after_sha256": digest.lower(), "new_file": row["new_file"]}
        if "bytes" in row:
            if type(row["bytes"]) is not int or row["bytes"] < 0:
                raise ReplayError(f"Invalid expected byte count: {name}")
            entry["bytes"] = row["bytes"]
        expected.append(entry)
    patch_paths = {row["path"]: row for row in paths}
    if seen != set(patch_paths):
        raise ReplayError("Expected-files manifest path set differs from the patch: "
                          f"missing={sorted(set(patch_paths) - seen)}; extra={sorted(seen - set(patch_paths))}")
    for row in expected:
        if row["new_file"] != patch_paths[row["path"]]["new_file"]:
            raise ReplayError(f"Expected new_file status differs from the patch: {row['path']}")
    return expected, {"path": str(path), "sha256": sha256(raw), "path_set_matches": True,
                      "path_count": len(expected), "new_path_count": sum(row["new_file"] for row in expected)}


def verify_expected_files(work: Path, expected: list[dict], receipt: dict) -> None:
    """Hash every modified or new target, retaining all mismatches in the receipt."""
    report = {"status": "checking", "expected_path_count": len(expected), "files": []}
    receipt["expected_files"] = report
    failed = []
    for row in expected:
        name = row["path"]
        parts = PurePosixPath(name).parts
        target = work.joinpath(*parts)
        checked = {"path": name, "new_file": row["new_file"],
                   "expected_sha256": row["after_sha256"], "matches_expected": False}
        report["files"].append(checked)
        try:
            if (any(work.joinpath(*parts[:index]).is_symlink() for index in range(1, len(parts) + 1))
                    or not target.is_file()):
                raise ReplayError("Replayed path is not a regular non-symlink file")
            actual, size = file_sha256(target), target.stat().st_size
            checked.update(actual_sha256=actual, actual_bytes=size,
                           matches_expected=(actual == row["after_sha256"]
                                             and ("bytes" not in row or size == row["bytes"])))
            if "bytes" in row:
                checked["expected_bytes"] = row["bytes"]
        except (OSError, ReplayError) as exc:
            checked["error"] = str(exc)
        if not checked["matches_expected"]:
            failed.append(name)
    report.update(status="failed" if failed else "passed", checked_path_count=len(expected),
                  matched_path_count=len(expected) - len(failed))
    if failed:
        raise ReplayError(f"Replayed files do not match expected manifest: {', '.join(failed)}")


def parse_patch(raw: bytes) -> list[dict]:
    """Parse the builder's narrow text format, counting hunks to prevent hidden headers."""
    if not raw or len(raw) > MAX_PATCH or b"\0" in raw:
        raise ReplayError("Patch must be nonempty UTF-8 text no larger than 25 MiB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReplayError("Patch is not UTF-8") from exc
    records, current, old_left, new_left = [], None, 0, 0
    for line in text.split("\n"):
        if line == "\\ No newline at end of file":
            if current is None or not current["hunks"]:
                raise ReplayError("Unexpected no-newline marker")
            continue
        if old_left or new_left:
            prefix = line[:1]
            if prefix not in {" ", "-", "+"}:
                raise ReplayError("Malformed or truncated patch hunk")
            old_left -= prefix in {" ", "-"}
            new_left -= prefix in {" ", "+"}
            if min(old_left, new_left) < 0:
                raise ReplayError("Patch hunk counts do not match its content")
            continue
        header = DIFF.fullmatch(line)
        if header:
            old, new = header.groups()
            safe_path(old)
            if old != new or not old.startswith("repo/"):
                raise ReplayError("Patch paths must be unchanged repo/... paths")
            if any(row["path"] == old for row in records):
                raise ReplayError(f"Repeated patch path: {old}")
            current = {"path": old, "new_file": False, "old_header": False,
                       "new_header": False, "hunks": 0}
            records.append(current)
        elif not line:
            continue
        elif current is None:
            raise ReplayError("Patch must begin with an unquoted diff --git header")
        elif line == "new file mode 100644" and not current["old_header"] and not current["hunks"]:
            current["new_file"] = True
        elif line.startswith("--- ") and not current["old_header"] and not current["hunks"]:
            expected = "/dev/null" if current["new_file"] else "a/" + current["path"]
            if line[4:] != expected:
                raise ReplayError("Old patch header does not match its diff path")
            current["old_header"] = True
        elif line.startswith("+++ ") and current["old_header"] and not current["new_header"]:
            if line[4:] != "b/" + current["path"]:
                raise ReplayError("New patch header does not match its diff path")
            current["new_header"] = True
        elif HUNK.fullmatch(line) and current["old_header"] and current["new_header"]:
            match = HUNK.fullmatch(line)
            counts = [match.group(2) or "1", match.group(4) or "1"]
            if any(len(value) > len(str(MAX_PATCH)) or int(value) > MAX_PATCH for value in counts):
                raise ReplayError("Hunk counts exceed the patch size limit")
            old_left, new_left = map(int, counts)
            current["hunks"] += 1
        elif re.fullmatch(r"index [0-9a-f]+\.\.[0-9a-f]+(?: 100644)?", line) and not current["old_header"]:
            continue
        else:
            raise ReplayError(f"Unsupported patch metadata: {line[:160]!r}")
    if old_left or new_left or not records:
        raise ReplayError("Patch is empty or has a truncated hunk")
    if any(not row["hunks"] and not row["new_file"] for row in records):
        raise ReplayError("A modified-file patch must contain a hunk")
    return [{"path": row["path"], "new_file": row["new_file"]} for row in records]


def read_delta(path: Path) -> tuple[bytes, dict]:
    identity = {"path": str(path), "sha256": file_sha256(path)}
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = validate_zip(archive, kind="return")
            names = {info.filename for info in infos if not info.is_dir()}
            if PATCH_MEMBER not in names:
                raise ReplayError("Return ZIP has no patches/source.patch; a no-change return has no delta to replay")
            if any(name.startswith("patches/") and name != PATCH_MEMBER for name in names):
                raise ReplayError("Only a single patches/source.patch is supported")
            if archive.getinfo(PATCH_MEMBER).file_size > MAX_PATCH:
                raise ReplayError("Patch exceeds the 25 MiB limit")
            raw = archive.read(PATCH_MEMBER)
            identity["member"] = PATCH_MEMBER
    else:
        with path.open("rb") as handle:
            raw = handle.read(MAX_PATCH + 1)
    identity["patch_sha256"] = sha256(raw)
    return raw, identity


def select_root(infos: list[zipfile.ZipInfo], paths: list[dict]) -> str:
    files = {info.filename for info in infos if not info.is_dir()}
    directories = {info.filename.rstrip("/") for info in infos if info.is_dir()}
    matches = []
    for prefix in ("", "WORK/"):
        if ((prefix + "repo" in directories or any(name.startswith(prefix + "repo/") for name in files))
                and all((prefix + row["path"] not in files) if row["new_file"]
                        else (prefix + row["path"] in files) for row in paths)):
            matches.append(prefix)
    if len(matches) != 1:
        raise ReplayError(f"Expected one flat or WORK/ root matching all patch paths; found {len(matches)}")
    return matches[0]


def extract_original(archive: zipfile.ZipFile, infos: list[zipfile.ZipInfo], destination: Path) -> None:
    """Extract manually into a newly created tree, with no archived links or permissions."""
    destination.mkdir(mode=0o700, exist_ok=False)
    for info in infos:
        target = destination.joinpath(*PurePosixPath(info.filename).parts)
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with archive.open(info) as source, target.open("xb") as output:
            while chunk := source.read(1024 * 1024):
                count += len(chunk)
                if count > info.file_size:
                    raise ReplayError(f"Expanded member exceeds its declared size: {info.filename}")
                output.write(chunk)
        if count != info.file_size:
            raise ReplayError(f"Expanded member size differs: {info.filename}")


def controlled_git_env() -> dict:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0")
    return env


def run_git(git: str, work: Path, args: list[str], receipt: dict, stage: str,
            patch: bytes | None = None) -> str:
    argv = [git, "-c", f"core.hooksPath={os.devnull}", "-c", "core.autocrlf=false", *args]
    entry = {"stage": stage, "cwd": str(work), "argv": argv, "exit_code": None}
    if patch is not None:
        entry["stdin_sha256"] = sha256(patch)
    receipt["commands"].append(entry)
    try:
        result = subprocess.run(argv, cwd=work, env=controlled_git_env(), input=patch,
                                capture_output=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as exc:
        entry["error"] = "Timed out after 60 seconds"
        raise ReplayError(entry["error"]) from exc
    entry["exit_code"] = result.returncode
    for field, raw in (("stdout", result.stdout), ("stderr", result.stderr)):
        if raw:
            entry[field] = raw.decode("utf-8", errors="replace")[:4000]
    if result.returncode:
        raise ReplayError(f"Git {stage} failed with exit code {result.returncode}")
    return result.stdout.decode("utf-8").strip()


def replay(args: argparse.Namespace, receipt: dict) -> None:
    original, delta = Path(args.original_zip).resolve(), Path(args.delta).resolve()
    destination = Path(os.path.abspath(args.destination))
    receipt["destination"] = str(destination)
    if os.path.lexists(destination):
        raise ReplayError("Destination already exists; choose a new directory")
    if not destination.parent.is_dir() or destination.parent.resolve() != destination.parent:
        raise ReplayError("Destination parent must exist and have no symlink components")
    allow_case_distinct = bool(getattr(args, "allow_case_distinct_zip_paths", False))
    receipt["zip_path_policy"] = {"allow_case_distinct_original_paths": allow_case_distinct,
                                  "return_zip_policy": "strict_portable"}
    if allow_case_distinct:
        sensitive = destination_case_sensitive(destination.parent)
        receipt["zip_path_policy"].update(destination_parent=str(destination.parent),
                                         destination_case_sensitive=sensitive)
        if not sensitive:
            raise ReplayError("Case-distinct ZIP paths require a case-sensitive destination parent")
    if args.task_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", args.task_id):
        raise ReplayError("Invalid task ID")
    if args.expected_generator_sha256 and (not args.task_id or not re.fullmatch(
            r"[0-9a-fA-F]{64}", args.expected_generator_sha256)):
        raise ReplayError("Expected generator SHA-256 requires --task-id and a 64-digit hex digest")
    git = shutil.which("git")
    if not git:
        raise ReplayError("Git is not installed; no runtime is installed by this helper")
    git = str(Path(git).resolve())
    patch, identity = read_delta(delta)
    receipt["delta"] = identity
    paths = parse_patch(patch)
    receipt["patch_paths"] = [row["path"] for row in paths]
    expected_files = None
    if getattr(args, "expected_files_manifest", None):
        expected_files, receipt["expected_files_manifest"] = load_expected_files_manifest(
            Path(args.expected_files_manifest).resolve(), paths)
    receipt["original_zip"] = {"path": str(original), "sha256": file_sha256(original)}
    with zipfile.ZipFile(original) as archive:
        infos = validate_zip(archive, kind="original", allow_case_distinct_paths=allow_case_distinct)
        prefix = select_root(infos, paths)
        if args.task_id and prefix + f"repo/generators/{args.task_id}/generator.py" not in {
                info.filename for info in infos if not info.is_dir()}:
            raise ReplayError("Selected generator is absent from the original packet root")
        receipt["layout"] = "nested_WORK" if prefix else "flat"
        work = destination / prefix.rstrip("/") if prefix else destination
        receipt["work_root"] = str(work)
        extract_original(archive, infos, destination)
    generator = work / f"repo/generators/{args.task_id}/generator.py" if args.task_id else None
    if generator:
        receipt["generator"] = {"task_id": args.task_id, "path": str(generator),
                                "before_sha256": file_sha256(generator)}
    run_git(git, work, ["init", "-q", "--template="], receipt, "init")
    root = run_git(git, work, ["rev-parse", "--show-toplevel"], receipt, "verify_root")
    if Path(root).resolve() != work.resolve() or not (work / ".git").is_dir():
        raise ReplayError("Git did not initialize the selected isolated root")
    run_git(git, work, ["apply", "-p1", "--check", "-"], receipt, "check", patch)
    run_git(git, work, ["apply", "-p1", "-"], receipt, "apply", patch)
    if expected_files is not None:
        verify_expected_files(work, expected_files, receipt)
    if generator:
        if generator.is_symlink() or not generator.is_file():
            raise ReplayError("Replayed generator is not a regular file")
        actual = file_sha256(generator)
        receipt["generator"]["after_sha256"] = actual
        if args.expected_generator_sha256:
            expected = args.expected_generator_sha256.lower()
            receipt["generator"].update(expected_sha256=expected, matches_expected=actual == expected)
            if actual != expected:
                raise ReplayError("Replayed generator SHA-256 does not match the expected final source")
    receipt["status"] = "passed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_zip", help="Original issued packet ZIP")
    parser.add_argument("delta", help="UTF-8 source patch or return ZIP containing patches/source.patch")
    parser.add_argument("destination", help="New extraction directory under an existing non-symlink parent")
    parser.add_argument("--task-id", help="Record the selected generator's before/after hashes")
    parser.add_argument("--expected-generator-sha256", help="Require this post-apply hash; needs --task-id")
    parser.add_argument("--allow-case-distinct-zip-paths", action="store_true",
                        help="Allow case-distinct original ZIP paths only after probing the destination filesystem")
    parser.add_argument("--expected-files-manifest",
                        help="Require an exact patch-path/new-file set and every post-apply hash from its changes list")
    args = parser.parse_args(argv)
    receipt = {"schema": "arcpuzzles-passive-replay-proposal-v1", "status": "failed",
               "invocation": {"cwd": str(Path.cwd()), "argv": list(sys.orig_argv) if argv is None else
                              [sys.executable, str(Path(__file__).resolve()), *argv]},
               "commands": []}
    try:
        replay(args, receipt)
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, EOFError, zlib.error) as exc:
        receipt["error"] = str(exc)
    receipt["exit_code"] = 0 if receipt["status"] == "passed" else 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
