#!/usr/bin/env python3
"""Read-only process/path metadata and excerpts from an already finished suite.

This does not run tests, open sockets, send signals, resume a checkpoint, or
modify repository source. Its one child process only reads check settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from arcpuzzles import runtime


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_excerpt(path: Path, fields: tuple[str, ...]) -> tuple[dict, dict | None]:
    if not path.is_file():
        return {"path": str(path), "exists": False}, None
    value = json.loads(path.read_text())
    return {
        "path": str(path),
        "exists": True,
        "sha256": digest(path),
        "selected_fields": {key: value[key] for key in fields if key in value},
    }, value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    proc_stat = Path("/proc/self/stat").read_text()
    syscall_pid = os.getpid()
    proc_self_pid = int(proc_stat.split("(", 1)[0])
    result = {
        "schema": "arcpuzzles-repository-test-environment-diagnostic-v1",
        "scope": "Read-only metadata follow-up to existing repository-tests.xml/log; no test rerun.",
        "cwd": str(Path.cwd()),
        "argv": [sys.executable, *sys.argv],
        "script_sha256": digest(Path(__file__)),
        "process_view": {
            "os_getpid": syscall_pid,
            "proc_self_stat_pid": proc_self_pid,
            "pid_views_match": syscall_pid == proc_self_pid,
            "runtime_process_table_supported": runtime._process_table_supported(),
            "runtime_process_identity_for_self": runtime._process_identity(syscall_pid),
        },
        "source_sha256": {
            path: digest(repo / path)
            for path in (
                "src/arcpuzzles/runtime.py", "src/arcpuzzles/check_jobs.py",
                "src/arcpuzzles/review_full_packet_files/setup_racket.py",
                "tests/test_check_signals.py", "tests/test_check_resume.py",
                "tests/test_check_jobs.py", "tests/test_review_runtime.py",
                "tests/test_task_test_prerequisites.py", "tests/test_packet_racket_setup.py",
                "tests/test_archival_reference.py", "tests/test_native_export.py",
                "tests/test_server.py",
            )
        },
        "existing_suite_receipt_excerpts": {},
    }
    temporary_root = Path("/tmp/pytest-of-root/pytest-0")
    excerpts = result["existing_suite_receipt_excerpts"]
    policy_path = temporary_root / "test_resume_recipe_retains_pol0/policy recipe/result.json"
    excerpts["resume_policy"], policy = load_excerpt(policy_path, (
        "status", "passed", "settings", "exit_code", "stdout", "stderr", "runtime_path",
    ))
    isolated_path = temporary_root / "test_preflight_matches_isolate0/ok/result.json"
    excerpts["isolated_interpreter"], _ = load_excerpt(isolated_path, (
        "status", "passed", "command", "test_prerequisite_preflight", "test_interpreter",
        "test_import_diagnostics", "exit_code", "stdout", "stderr", "test_counts",
    ))
    interrupted_path = temporary_root / "test_signal_before_child_exits0/between stages/result.json"
    excerpts["between_stages_interruption"], _ = load_excerpt(interrupted_path, (
        "status", "passed", "child_cleanup", "battery_summary", "interruption",
    ))
    if policy is not None:
        environment = os.environ.copy()
        overrides = {}
        recipe = policy["resume_argv"]
        if recipe[0] != "env":
            raise ValueError("Expected the recorded resume recipe to begin with env")
        for value in recipe[1:]:
            if "=" not in value:
                break
            key, setting = value.split("=", 1)
            overrides[key] = setting
        environment.update(overrides)
        child_code = (
            "import json,sys; from pathlib import Path; "
            "from arcpuzzles.runtime import _check_settings; "
            "print(json.dumps(_check_settings(Path(sys.argv[1])),sort_keys=True))"
        )
        child_argv = [policy["settings"]["python"], "-c", child_code, policy["runtime_path"]]
        child = subprocess.run(child_argv, cwd=repo, env=environment, capture_output=True,
                               text=True, timeout=15)
        child_record = {
            "purpose": "Read base runtime settings with the saved resume interpreter spelling and environment; no check/resume/test execution.",
            "cwd": str(repo), "argv": child_argv, "exit_code": child.returncode,
            "stdout": child.stdout, "stderr": child.stderr,
            "environment_override_keys": sorted(overrides),
            "environment_overrides_sha256": hashlib.sha256(
                json.dumps(overrides, sort_keys=True).encode()).hexdigest(),
        }
        if child.returncode == 0:
            actual = json.loads(child.stdout)
            saved = policy["settings"]
            child_record["actual_base_settings"] = actual
            child_record["base_setting_differences"] = {
                key: {"saved": saved.get(key), "metadata_child": value}
                for key, value in actual.items() if saved.get(key) != value
            }
            child_record["saved_and_child_python_resolve_equal"] = (
                Path(saved["python"]).resolve() == Path(actual["python"]).resolve()
            )
        result["metadata_child"] = child_record
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.out),
        "process_view": result["process_view"],
        "base_setting_differences": result.get("metadata_child", {}).get("base_setting_differences"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
