#!/usr/bin/env python3
"""Replay a final ARCpuzzles delta against its untouched original packet.

Usage (paths are resolved relative to the caller's working directory)::

    python3 replay_return.py --original original_packet.zip \
        --return candidate_return.zip --out /tmp/new_fresh_packet \
        --report checks/fresh-replay.json \
        --expected-generator-sha256 FINAL_GENERATOR_SHA256

The output directory and report must not exist; their parent directories must
already exist and contain no symlinks. This tool needs Python 3.12+, Git, and the
Python test dependencies used by the packet. It uses the original packet's own
offline Racket setup and wrapper, without downloading dependencies.

Only standard-library modules are imported here. Every original ZIP member is
verified against PACKET-MANIFEST.json before the original packet's return
validator is imported in a separate isolated Python process. The accepted patch
is applied from the fresh packet root, then all selected-task tests run through
that fresh packet's wrapper. No assignment is drawn, submitted solver is run,
or private query-label file is opened. The JSON report retains commands, actual
working directories, output, exit codes, and source/patch/archive hashes.

A nonzero exit leaves the fresh directory, if created, and a truthful failure
report for inspection. Nothing is overwritten or automatically deleted. A
successful replay certifies the recorded checks, not hidden-query correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time
import zipfile


MANIFEST = "PACKET-MANIFEST.json"
SCHEMA = "arcpuzzles-full-packet-v2"
MAX_ORIGINAL_FILES = 100_000
MAX_ORIGINAL_BYTES = 2 * 1024**3
MAX_MANIFEST_BYTES = 16 * 1024**2
MAX_RETURN_ARCHIVE_BYTES = 32 * 1024**2
SHA256 = re.compile(r"[0-9a-f]{64}\Z")

# This code runs only with cwd set to the verified, fresh original packet.
# Isolated mode removes inherited Python paths; the sole added source directory
# belongs to that fresh packet. The full validator result is not printed.
VALIDATOR_CODE = """\
import json, sys, zipfile
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / 'repo' / 'src'))
from arcpuzzles.review_full_return import validate_full_return
manifest = json.loads((root / 'PACKET-MANIFEST.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(sys.argv[1]) as archive:
    checked = validate_full_return(archive, manifest)
    patch_members = sorted(n for n in archive.namelist() if n.startswith('patches/'))
    solve = checked.get('reviewer_solve') or {}
    source = archive.read('solve/source/generator.py') if 'solve/source/generator.py' in archive.namelist() else None
    import hashlib
    result = {key: checked.get(key) for key in
              ('packet_id', 'assignment_id', 'task_id', 'completion_state', 'patch_paths')}
    result.update(patch_members=patch_members, solve_status=solve.get('status'),
                  solve_generator_sha256=solve.get('generator_hash'),
                  solve_source_sha256=hashlib.sha256(source).hexdigest() if source is not None else None)
print(json.dumps(result, sort_keys=True))
"""


class ReplayError(ValueError):
    """A replay requirement failed; the report contains the available evidence."""


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _absolute(value: str | Path) -> Path:
    # Do not resolve(): doing so would silently follow a caller-supplied symlink.
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def _safe_parents(path: Path) -> None:
    for parent in reversed(path.parents):
        mode = parent.lstat().st_mode
        if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
            raise ReplayError(f"Parent is a symlink or not a directory: {parent}")


def _regular_file(path: Path) -> None:
    _safe_parents(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ReplayError(f"Expected a regular file without symlinks: {path}")


def _safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or name != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts)
            or any(char in name for char in ("\\", ":", "\0"))):
        raise ReplayError(f"Unsafe original ZIP member: {name!r}")
    return path


def _original_manifest(archive: zipfile.ZipFile) -> tuple[dict, list[zipfile.ZipInfo]]:
    infos = archive.infolist()
    if len(infos) > MAX_ORIGINAL_FILES or sum(info.file_size for info in infos) > MAX_ORIGINAL_BYTES:
        raise ReplayError("Original packet exceeds the 100,000-file / 2-GiB extraction limit")
    seen: set[str] = set()
    for info in infos:
        _safe_member(info.filename)
        mode = (info.external_attr >> 16) & 0xFFFF
        if (info.orig_filename != info.filename or info.is_dir()
                or stat.S_IFMT(mode) not in {0, stat.S_IFREG} or mode & 0o111
                or info.flag_bits & 1
                or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
            raise ReplayError(f"Original member is not a supported regular file: {info.filename}")
        key = info.filename.casefold()
        if key in seen:
            raise ReplayError(f"Duplicate or case-colliding original member: {info.filename}")
        seen.add(key)
    for name in seen:
        if any(parent.as_posix().casefold() in seen for parent in PurePosixPath(name).parents):
            raise ReplayError(f"Original member conflicts with a directory: {name}")
    by_name = {info.filename: info for info in infos}
    if MANIFEST not in by_name or by_name[MANIFEST].file_size > MAX_MANIFEST_BYTES:
        raise ReplayError("Original packet needs a root PACKET-MANIFEST.json of at most 16 MiB")
    manifest = json.loads(archive.read(MANIFEST))
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or not isinstance(files, dict):
        raise ReplayError("Unsupported original packet manifest")
    if set(by_name) != set(files) | {MANIFEST} or MANIFEST in files:
        raise ReplayError("Original ZIP inventory differs from its manifest")
    if any(not isinstance(value, str) or SHA256.fullmatch(value) is None for value in files.values()):
        raise ReplayError("Original manifest contains an invalid file SHA-256")
    return manifest, infos


def extract_original(original: Path, out: Path, report: dict) -> dict:
    """Extract one manifest-bound full packet into a newly created directory."""
    _regular_file(original)
    _safe_parents(out)
    if out.exists() or out.is_symlink():
        raise ReplayError(f"Output directory already exists: {out}")
    with zipfile.ZipFile(original) as archive:
        manifest, infos = _original_manifest(archive)
        identity = hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                                             separators=(",", ":")).encode("utf-8")).hexdigest()
        report["original"] = {"path": str(original), "sha256": _sha_file(original),
                              "packet_id": identity, "file_count": len(infos),
                              "expanded_bytes": sum(info.file_size for info in infos),
                              "all_manifest_files_verified": False}
        out.mkdir()
        for info in infos:
            destination = out.joinpath(*_safe_member(info.filename).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            _safe_parents(destination)
            digest, count = hashlib.sha256(), 0
            with archive.open(info) as source, destination.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    count += len(chunk)
                    if count > info.file_size:
                        raise ReplayError(f"Original member exceeds its declared size: {info.filename}")
                    target.write(chunk)
                    digest.update(chunk)
            if count != info.file_size:
                raise ReplayError(f"Original member size differs: {info.filename}")
            expected = manifest["files"].get(info.filename)
            if expected is not None and digest.hexdigest() != expected:
                raise ReplayError(f"Original member hash differs: {info.filename}")
        report["original"]["all_manifest_files_verified"] = True
        return manifest


def _environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if key not in {"PYTHONPATH", "PYTHONHOME", "RACKET_PATH"} and not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return env


def _text(value: str | bytes | None) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def run_command(stage: str, argv: list[str], root: Path, report: dict, timeout: float,
                *, stdin: bytes | None = None, runtime_cwd: str | None = None) -> dict:
    row = {"stage": stage, "argv": argv, "cwd": "packet_root", "actual_cwd": str(root),
           "exit_code": None, "stdout": "", "stderr": ""}
    if runtime_cwd is not None:
        row.update(runtime_cwd=runtime_cwd, actual_runtime_cwd=str(root / runtime_cwd))
    if stdin is not None:
        row["stdin_sha256"] = hashlib.sha256(stdin).hexdigest()
    report.setdefault("verification_commands", []).append(row)
    report["current_stage"] = stage
    print(f"[{stage}] cwd={root}", file=sys.stderr, flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=root, env=_environment(), input=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        row.update(exit_code=result.returncode, stdout=_text(result.stdout), stderr=_text(result.stderr))
    except subprocess.TimeoutExpired as exc:
        row.update(timed_out=True, stdout=_text(exc.stdout), stderr=_text(exc.stderr))
        raise ReplayError(f"{stage} timed out after {timeout:g} seconds") from exc
    except OSError as exc:
        row["error"] = str(exc)
        raise ReplayError(f"{stage} could not start: {exc}") from exc
    finally:
        row["elapsed_seconds"] = round(time.monotonic() - started, 6)
    if row["exit_code"] != 0:
        raise ReplayError(f"{stage} exited with status {row['exit_code']}")
    return row


def apply_return_patch(root: Path, patch: bytes, expected_paths: list[str], report: dict, timeout: float) -> None:
    report["patch"] = {"member": "patches/source.patch", "sha256": hashlib.sha256(patch).hexdigest(),
                       "bytes": len(patch)}
    # Let Git enumerate the paths it will actually use. This detects extra
    # quoted/standalone diff headers that a text-level validator could miss.
    routes = run_command("git_patch_paths", ["git", "apply", "--numstat", "-z", "-"],
                         root, report, timeout, stdin=patch)
    paths = []
    for record in routes["stdout"].split("\0"):
        if not record:
            continue
        parts = record.split("\t", 2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ReplayError("Git reported a binary or unsupported patch entry")
        _safe_member(parts[2])
        paths.append(parts[2])
    report["patch"]["git_reported_paths"] = paths
    if not paths or len(paths) != len(set(paths)) or sorted(paths) != sorted(expected_paths):
        raise ReplayError("Git patch paths differ from the statically validated allowed paths")
    run_command("git_apply_check", ["git", "apply", "--check", "--whitespace=nowarn", "-"],
                root, report, timeout, stdin=patch)
    run_command("git_apply", ["git", "apply", "--whitespace=nowarn", "-"],
                root, report, timeout, stdin=patch)


def verify_patched_source(root: Path, manifest: dict, changed_paths: list[str], report: dict) -> None:
    """Require untouched original tools/data and only declared repository additions."""
    allowed = set(changed_paths)
    original = manifest["files"]
    for name, expected in original.items():
        source = root.joinpath(*PurePosixPath(name).parts)
        _regular_file(source)
        if name not in allowed and _sha_file(source) != expected:
            raise ReplayError(f"Patch changed original source outside validated paths: {name}")
    for directory, dirs, files in os.walk(root / "repo", followlinks=False):
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ReplayError(f"Symlink directory appeared in patched repository: {name}")
        for name in files:
            source = Path(directory) / name
            _regular_file(source)
            relative = source.relative_to(root).as_posix()
            if relative not in original and relative not in allowed:
                raise ReplayError(f"Undeclared file appeared in patched repository: {relative}")
    report["patched_source_invariants"] = {"passed": True, "original_files_checked": len(original),
                                            "allowed_changed_paths": sorted(allowed)}


def bind_generator(root: Path, validated: dict, expected: str | None, report: dict) -> Path:
    task = validated.get("task_id")
    if not isinstance(task, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task) is None:
        raise ReplayError("Validated return has an unsafe task identifier")
    source = root / "repo" / "generators" / task / "generator.py"
    _regular_file(source)
    actual = _sha_file(source)
    solve_hash = validated.get("solve_generator_sha256")
    report["generator"] = {"path": source.relative_to(root).as_posix(), "sha256": actual,
                           "solve_generator_sha256": solve_hash,
                           "solve_source_sha256": validated.get("solve_source_sha256"),
                           "expected_sha256": expected}
    if (validated.get("solve_status") != "finished" or not isinstance(solve_hash, str)
            or SHA256.fullmatch(solve_hash) is None):
        raise ReplayError("Return needs a finished post-repair solve with a generator SHA-256")
    if actual != solve_hash or actual != validated.get("solve_source_sha256"):
        raise ReplayError("Patched generator does not match the returned final solve generator")
    if expected is not None and (SHA256.fullmatch(expected) is None or actual != expected):
        raise ReplayError("Patched generator does not match --expected-generator-sha256")
    return source


def focused_test_argv(task: str) -> list[str]:
    return [sys.executable, "run_with_racket.py", sys.executable, "-m", "pytest", "-q",
            f"generators/{task}/tests"]


def replay(args: argparse.Namespace, report: dict) -> None:
    original, returned, out = (_absolute(args.original), _absolute(args.return_zip), _absolute(args.out))
    report.update(fresh_packet_root=str(out), current_stage="verify_original")
    _regular_file(returned)
    with returned.open("rb") as handle:
        return_bytes = handle.read(MAX_RETURN_ARCHIVE_BYTES + 1)
    if len(return_bytes) > MAX_RETURN_ARCHIVE_BYTES:
        raise ReplayError("Return archive exceeds the 32-MiB input limit")
    report["return"] = {"path": str(returned), "sha256": hashlib.sha256(return_bytes).hexdigest()}
    manifest = extract_original(original, out, report)
    # Validate and replay the same captured bytes even if the caller later
    # replaces the candidate path. Keep that exact input in the fresh copy.
    snapshot = out / ".replay-return.zip"
    with snapshot.open("xb") as handle:
        handle.write(return_bytes)
    report["return"]["snapshot"] = snapshot.relative_to(out).as_posix()
    validation = run_command("validate_return", [sys.executable, "-I", "-B", "-c", VALIDATOR_CODE, str(snapshot)],
                             out, report, args.timeout)
    validated = json.loads(validation["stdout"])
    report["validated_return"] = validated
    report["current_stage"] = "verify_return_identity"
    if validated.get("packet_id") != report["original"]["packet_id"]:
        raise ReplayError("Return packet identity differs from the verified original")
    if validated.get("patch_members") != ["patches/source.patch"]:
        raise ReplayError("Expected exactly the builder's patches/source.patch")
    with zipfile.ZipFile(io.BytesIO(return_bytes)) as archive:
        patch = archive.read("patches/source.patch")
    apply_return_patch(out, patch, validated["patch_paths"], report, args.timeout)
    report["current_stage"] = "verify_patched_source"
    verify_patched_source(out, manifest, validated["patch_paths"], report)
    report["current_stage"] = "bind_generator"
    source = bind_generator(out, validated, args.expected_generator_sha256, report)
    tests = out / "repo" / "generators" / validated["task_id"] / "tests"
    _safe_parents(tests)
    if not tests.is_dir() or tests.is_symlink():
        raise ReplayError(f"Selected task has no regular tests directory: {tests}")
    run_command("setup_racket", [sys.executable, "setup_racket.py"], out, report, args.timeout)
    run_command("focused_tests", focused_test_argv(validated["task_id"]), out, report,
                args.timeout, runtime_cwd="repo")
    report["current_stage"] = "verify_final_source"
    report["generator"]["sha256_after_tests"] = _sha_file(source)
    if report["generator"]["sha256_after_tests"] != report["generator"]["sha256"]:
        raise ReplayError("Generator bytes changed while running the focused tests")
    if _sha_file(snapshot) != report["return"]["sha256"]:
        raise ReplayError("Captured return archive bytes changed during replay")
    report.update(completion_state="complete", current_stage="complete", exit_code=0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original", required=True, help="Untouched original full-packet ZIP")
    parser.add_argument("--return", dest="return_zip", required=True, help="Candidate delta ZIP from package_return.py")
    parser.add_argument("--out", required=True, help="New fresh extraction directory; parent must exist")
    parser.add_argument("--report", required=True, help="New JSON evidence file; parent must exist")
    parser.add_argument("--expected-generator-sha256", help="Optional independently recorded final source SHA-256")
    parser.add_argument("--timeout", type=float, default=600, help="Per-command timeout in seconds (default: 600)")
    args = parser.parse_args(argv)
    report_path = _absolute(args.report)
    report = {"schema": "arcpuzzles-fresh-replay-v1", "completion_state": "blocked", "exit_code": 1,
              "verification_commands": [], "invocation_argv": list(argv) if argv is not None else sys.argv[1:]}
    try:
        _safe_parents(report_path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(report_path, flags, 0o644)
    except (OSError, ValueError) as exc:
        print(f"Cannot create a new report without overwriting or following links: {exc}", file=sys.stderr)
        return 2
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        try:
            if args.timeout <= 0:
                raise ReplayError("--timeout must be positive")
            replay(args, report)
        except Exception as exc:
            report.update(error=f"{type(exc).__name__}: {exc}", failed_stage=report.get("current_stage", "arguments"))
        for command in report["verification_commands"]:
            if command["stage"] == "focused_tests":
                report["test_counts"] = {kind: int(count) for count, kind in
                    re.findall(r"(\d+) (passed|failed|skipped|xfailed|xpassed|errors?|deselected)\b", command["stdout"])}
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"completion_state": report["completion_state"], "report": str(report_path),
                      "exit_code": report["exit_code"]}, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
