#!/usr/bin/env python3
"""Run pytest files separately, retaining evidence and bounding temporary storage.

Use an interpreter with pytest installed outside user-site if tests stage isolated
children. The caller supplies the repository and its runtime environment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, report: dict) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-per-file", type=float, default=600)
    parser.add_argument("--bind-source", action="append", default=[])
    parser.add_argument("test_files", nargs="*")
    args = parser.parse_args()
    if args.timeout_per_file <= 0:
        parser.error("--timeout-per-file must be positive")
    repo = args.repo.resolve(strict=True)
    chosen = args.test_files or sorted(str(p.relative_to(repo)) for p in (repo / "tests").glob("test_*.py"))
    if not chosen:
        parser.error("no test files found")
    paths = [(repo / name).resolve(strict=True) for name in chosen]
    sources = [(repo / name).resolve(strict=True) for name in args.bind_source]
    if any(not p.is_file() or not p.is_relative_to(repo) for p in paths + sources):
        parser.error("test files and bound sources must be files within --repo")
    bindings = {str(p.relative_to(repo)): sha256(p) for p in sources}
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "bounded-pytest-v1", "status": "running", "repo": str(repo),
        "python": sys.executable, "python_version": sys.version,
        "pytest_version": importlib.metadata.version("pytest"),
        "tool_sha256": sha256(Path(__file__)), "source_sha256_before": bindings,
        "policy": "One pytest process per file; only its owned temporary directory is removed after it exits.",
        "selected_files": [str(p.relative_to(repo)) for p in paths],
        "totals": {key: 0 for key in ("tests", "passed", "failures", "errors", "skipped")}, "runs": [],
    }
    write_report(out / "result.json", report)
    for index, path in enumerate(paths):
        stem = f"{index:03d}-{path.stem}"
        log, junit = out / f"{stem}.log", out / f"{stem}.xml"
        started, timed_out = time.monotonic(), False
        with tempfile.TemporaryDirectory(prefix="owned-pytest-", dir=out) as temporary:
            env = os.environ.copy()
            env["TMPDIR"] = temporary
            argv = [sys.executable, "-m", "pytest", "-q", str(path.relative_to(repo)),
                    "--basetemp", str(Path(temporary) / "pytest"), "--junitxml", str(junit)]
            with log.open("w") as stream:
                process = subprocess.Popen(argv, cwd=repo, env=env, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = process.wait(timeout=args.timeout_per_file)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    code = process.wait()
        counts = {key: 0 for key in report["totals"]}
        parse_error = None
        if junit.exists():
            try:
                root = ET.parse(junit).getroot()
                suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
                for suite in suites:
                    for key in ("tests", "failures", "errors", "skipped"):
                        counts[key] += int(suite.get(key, "0"))
                counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
            except (ET.ParseError, ValueError) as exc:
                parse_error = str(exc)
        else:
            parse_error = "JUnit report missing"
        item = {"test_file": str(path.relative_to(repo)), "argv": argv, "cwd": str(repo),
                "exit_code": code, "timed_out": timed_out, "counts": counts,
                "seconds": round(time.monotonic() - started, 3),
                "log": log.name, "junit": junit.name if junit.exists() else None, "report_error": parse_error}
        report["runs"].append(item)
        for key, value in counts.items():
            report["totals"][key] += value
        write_report(out / "result.json", report)
        print(json.dumps({"file": item["test_file"], "exit_code": code, "counts": counts}), flush=True)
    report["source_sha256_after"] = {str(p.relative_to(repo)): sha256(p) for p in sources}
    report["sources_unchanged"] = report["source_sha256_after"] == bindings
    report["failed_files"] = [item["test_file"] for item in report["runs"]
                              if item["exit_code"] != 0 or item["timed_out"] or item["report_error"]
                              or item["counts"]["failures"] or item["counts"]["errors"]]
    report["status"] = "passed" if not report["failed_files"] and report["sources_unchanged"] else "failed"
    write_report(out / "result.json", report)
    print(json.dumps({"status": report["status"], "totals": report["totals"], "failed_files": report["failed_files"]}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
