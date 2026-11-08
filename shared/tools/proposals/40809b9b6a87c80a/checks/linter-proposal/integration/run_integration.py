#!/usr/bin/env python3
"""Export one public runtime and run the proposed full strict defect linter.

Invoke through review.py run so the packet's verified Racket is selected.
Only the disposable runtime receives the proposed shared-tool bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from reviewer_support import find_root

TASK = "2e663d812b7a"
EXPECTED_GENERATOR = "c14518d0be325525090968de13d9598d195cf38a7c5f8732a0d87925cc80ca39"
HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
ROOT = find_root(__file__)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def evidence_path(name):
    path = HERE / name
    return str(path.relative_to(ROOT.parent)) if path.is_relative_to(ROOT.parent) else str(path)


def main():
    if (HERE / "RESULTS.json").exists():
        raise FileExistsError("Integration evidence already exists; preserve this run")
    manifest = json.loads((PROPOSAL / "manifest.json").read_text())
    shared = ROOT / manifest["shared_source"]
    generator = ROOT / "generators" / TASK / "generator.py"
    candidate = PROPOSAL / "candidate_generator_defect_lint.py"
    assert sha256(shared) == manifest["shared_source_sha256"], "Selected shared tool changed"
    assert sha256(candidate) == manifest["candidate_sha256"], "Candidate changed"
    assert sha256(generator) == EXPECTED_GENERATOR, "Selected generator changed"
    racket = Path(os.environ["RACKET_PATH"])
    assert racket.is_file(), "Wrapper did not select Racket"
    result = {"schema": "review-optional-linter-integration-v1",
              "task_id": TASK, "status": "started", "commands": [],
              "generator_sha256": EXPECTED_GENERATOR,
              "selected_shared_sha256": sha256(shared),
              "candidate_sha256": sha256(candidate),
              "python_executable": sys.executable, "python_version": sys.version,
              "racket_executable": str(racket), "racket_executable_sha256": sha256(racket),
              "scope": "Full candidate strict linter in an exported selected-task runtime; selected shared source is unchanged."}
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="arc-linter-integration-") as directory:
            stage = Path(directory)
            result["runtime_directory"] = str(stage)
            export_command = [sys.executable, "-B", "-m", "arcpuzzles", "workspace",
                              "--id", TASK, "--out", str(stage)]
            exported = subprocess.run(export_command, cwd=ROOT, text=True,
                                      capture_output=True, timeout=120)
            result["commands"].append({"cwd": str(ROOT), "argv": export_command,
                                       "exit_code": exported.returncode,
                                       "stdout_sha256": hashlib.sha256(exported.stdout.encode()).hexdigest(),
                                       "stdout_bytes": len(exported.stdout.encode()),
                                       "stderr": exported.stderr})
            if exported.returncode:
                (HERE / "workspace-failure.stdout.log").write_text(exported.stdout)
                raise RuntimeError(f"Public workspace export failed: {exported.stderr}")
            runtime_manifest = stage / "RUNTIME_MANIFEST.json"
            shutil.copyfile(runtime_manifest, HERE / "RUNTIME_MANIFEST.json")
            runtime_receipt = json.loads(runtime_manifest.read_text())
            result["runtime_manifest_sha256"] = sha256(runtime_manifest)
            result["runtime_selected_task_ids"] = runtime_receipt["task_ids"]
            result["runtime_source_file_count"] = len(runtime_receipt["files"])
            (HERE / "workspace.stdout.json").write_text(exported.stdout)
            summary = json.loads(exported.stdout)
            result["export_summary_matches_runtime_manifest"] = (
                summary["directory"] == str(stage)
                and summary["manifest"] == str(runtime_manifest)
                and summary["files"] == len(runtime_receipt["files"])
                and summary["task_id"] == TASK)
            assert result["export_summary_matches_runtime_manifest"]
            tool = stage / "scripts/generator_defect_lint.py"
            original_tool_hash = sha256(tool)
            assert original_tool_hash == manifest["shared_source_sha256"]
            selected = [row for row in runtime_receipt["files"]
                        if row["library_path"] == f"generators/{TASK}/generator.py"]
            assert len(selected) == 1
            staged_generator = stage / selected[0]["runtime_path"]
            assert sha256(staged_generator) == EXPECTED_GENERATOR
            shutil.copyfile(candidate, tool)
            assert sha256(tool) == manifest["candidate_sha256"]
            result["tool_overlay"] = {"runtime_path": "scripts/generator_defect_lint.py",
                                      "exported_sha256": original_tool_hash,
                                      "executed_sha256": sha256(tool),
                                      "proposal_path": "checks/linter-proposal/candidate_generator_defect_lint.py",
                                      "original_runtime_manifest_preserved": True}
            environment = dict(os.environ)
            for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "ARCPUZZLES_HOME"):
                environment.pop(key, None)
            environment["PYTHONPATH"] = str(stage)
            environment["ARCPUZZLES_HOME"] = str(stage)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            report_path = HERE / "strict-linter.json"
            command = [sys.executable, "-B", "-E", "-s", "scripts/generator_defect_lint.py",
                       TASK, "--strict", "--seeds", "8", "--bands", "easy,medium,hard",
                       "--json", str(report_path)]
            command_receipt = {"cwd": str(stage), "argv": command,
                               "environment_overrides": {key: environment[key] for key in
                                                         ("PYTHONPATH", "ARCPUZZLES_HOME", "RACKET_PATH")}}
            result["commands"].append(command_receipt)
            try:
                completed = subprocess.run(command, cwd=stage, env=environment,
                                           text=True, capture_output=True, timeout=240)
                stdout, stderr = completed.stdout, completed.stderr
                exit_code = completed.returncode
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or b""
                stderr = exc.stderr or b""
                stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout
                stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
                exit_code = 124
                command_receipt["timed_out"] = True
            (HERE / "strict-linter.stdout.log").write_text(stdout)
            (HERE / "strict-linter.stderr.log").write_text(stderr)
            command_receipt.update({"exit_code": exit_code,
                                    "stdout_path": evidence_path("strict-linter.stdout.log"),
                                    "stderr_path": evidence_path("strict-linter.stderr.log")})
            reports = json.loads(report_path.read_text()) if report_path.exists() else []
            result["report_count"] = len(reports)
            result["issues"] = sum(len(row.get("issues") or []) for row in reports)
            result["warnings"] = sum(len(row.get("warnings") or []) for row in reports)
            result["errors"] = [row["error"] for row in reports if row.get("error")]
            result["racket_executed"] = bool(reports) and all(row.get("racket") is True for row in reports)
            result["sampling_requests"] = [row.get("sampling", {}) for row in reports]
            result["status"] = ("passed" if exit_code == 0 and len(reports) == 1
                                and not result["issues"] and not result["warnings"]
                                and not result["errors"] and result["racket_executed"] else "failed")
            result["executed_tool_sha256_after_run"] = sha256(tool)
            assert result["executed_tool_sha256_after_run"] == manifest["candidate_sha256"]
            assert sha256(staged_generator) == EXPECTED_GENERATOR
    except Exception as exc:
        result["status"] = "failed"
        result["exception"] = repr(exc)
    result["selected_shared_source_unchanged"] = sha256(shared) == manifest["shared_source_sha256"]
    result["selected_generator_unchanged"] = sha256(generator) == EXPECTED_GENERATOR
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    result["runtime_disposition"] = "Disposable export removed after retaining its manifest, overlay identity and exact run receipts."
    if not result["selected_shared_source_unchanged"] or not result["selected_generator_unchanged"]:
        result["status"] = "failed"
    write_json("RESULTS.json", result)
    print(json.dumps({key: result.get(key) for key in
                     ("status", "issues", "warnings", "errors", "racket_executed",
                      "elapsed_seconds", "exception", "selected_shared_source_unchanged")}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE,
                        help="fresh evidence directory (default: beside this script)")
    arguments = parser.parse_args()
    HERE = arguments.out.resolve()
    HERE.mkdir(parents=True, exist_ok=True)
    raise SystemExit(main())
