#!/usr/bin/env python3
"""Apply the packaged source patch to a fresh packet and verify every changed path."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> dict:
    proc = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True)
    return {
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    for info in archive.infolist():
        member = PurePosixPath(info.filename)
        if member.is_absolute() or ".." in member.parts:
            raise ValueError(f"unsafe archive member: {info.filename!r}")
    archive.extractall(destination)


def find_workspace(extracted: Path) -> Path:
    candidate = extracted / "WORK"
    if not (candidate / "PACKET-MANIFEST.json").is_file():
        raise RuntimeError("fresh packet has no WORK/PACKET-MANIFEST.json")
    return candidate.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    packet_zip = args.packet_zip.resolve()
    patch = args.patch.resolve()
    manifest_path = args.manifest.resolve()
    report_path = args.report.resolve()
    manifest = json.loads(manifest_path.read_text())
    report: dict = {
        "schema": "arcpuzzles-fresh-patch-replay-v1",
        "packet_zip": str(packet_zip),
        "packet_zip_sha256": sha256(packet_zip),
        "patch": str(patch),
        "patch_sha256": sha256(patch),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "expected_generator_sha256": manifest["expected_generator_sha256"],
        "passed": False,
    }

    try:
        with tempfile.TemporaryDirectory(prefix="arcpuzzles-fresh-replay-") as tmp:
            extracted = Path(tmp) / "packet"
            extracted.mkdir()
            with zipfile.ZipFile(packet_zip) as archive:
                safe_extract(archive, extracted)
            work = find_workspace(extracted)
            report["workspace_relative_to_extraction"] = work.relative_to(extracted).as_posix()

            packet_manifest_path = work / "PACKET-MANIFEST.json"
            packet_manifest = json.loads(packet_manifest_path.read_text())
            canonical_manifest = json.dumps(
                packet_manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
            observed_packet_id = hashlib.sha256(canonical_manifest).hexdigest()
            report["observed_packet_id"] = observed_packet_id
            if observed_packet_id != manifest["packet_id"]:
                raise AssertionError("fresh extraction packet identity mismatch")

            before_rows = []
            for row in manifest["changed_paths"]:
                target = work / row["path"]
                observed = sha256(target) if target.is_file() else None
                before_rows.append({"path": row["path"], "expected": row["before_sha256"], "observed": observed})
                if observed != row["before_sha256"]:
                    raise AssertionError(f"fresh baseline mismatch: {row['path']}: {observed} != {row['before_sha256']}")
            report["before_paths"] = before_rows

            git_init = run(["git", "init", "-q"], cwd=work)
            report["git_init"] = git_init
            if git_init["exit_code"] != 0:
                raise RuntimeError("git init failed")
            top = run(["git", "rev-parse", "--show-toplevel"], cwd=work)
            report["git_toplevel"] = top
            if top["exit_code"] != 0 or Path(top["stdout"].strip()).resolve() != work:
                raise AssertionError("git toplevel is not the exact fresh WORK directory")

            check = run(["git", "apply", "--check", str(patch)], cwd=work)
            report["git_apply_check"] = check
            if check["exit_code"] != 0:
                raise RuntimeError("git apply --check failed")
            apply = run(["git", "apply", str(patch)], cwd=work)
            report["git_apply"] = apply
            if apply["exit_code"] != 0:
                raise RuntimeError("git apply failed")

            after_rows = []
            for row in manifest["changed_paths"]:
                target = work / row["path"]
                observed = sha256(target) if target.is_file() else None
                after_rows.append({"path": row["path"], "expected": row["after_sha256"], "observed": observed})
                if observed != row["after_sha256"]:
                    raise AssertionError(f"patched path mismatch: {row['path']}: {observed} != {row['after_sha256']}")
            report["after_paths"] = after_rows

            unchanged_rows = []
            for row in manifest.get("unchanged_paths", []):
                target = work / row["path"]
                observed = sha256(target) if target.is_file() else None
                unchanged_rows.append({"path": row["path"], "expected": row["sha256"], "observed": observed})
                if observed != row["sha256"]:
                    raise AssertionError(f"unchanged path mismatch: {row['path']}: {observed} != {row['sha256']}")
            report["unchanged_paths"] = unchanged_rows

            generator = work / "repo/generators/4e6862c442fd/generator.py"
            report["generator_sha256"] = sha256(generator)
            if report["generator_sha256"] != manifest["expected_generator_sha256"]:
                raise AssertionError("final generator hash mismatch")

            env = os.environ.copy()
            runtime = work / "repo/shared/runtime"
            env["PYTHONPATH"] = str(runtime)
            tests = run(
                [sys.executable, "-m", "pytest", "-q", "generators/4e6862c442fd/tests/test_review_regressions.py"],
                cwd=work / "repo",
                env=env,
            )
            report["focused_tests"] = tests
            if tests["exit_code"] != 0:
                raise RuntimeError("focused tests failed in fresh extraction")

            report["passed"] = True
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "passed": report["passed"],
        "generator_sha256": report.get("generator_sha256"),
        "focused_test_exit_code": report.get("focused_tests", {}).get("exit_code"),
        "report": str(report_path),
        "error": report.get("error"),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
