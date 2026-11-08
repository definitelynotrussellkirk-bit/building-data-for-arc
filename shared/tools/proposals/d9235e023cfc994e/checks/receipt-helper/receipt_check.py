#!/usr/bin/env python3
"""Passively inspect a review RESULTS.json; never execute its recorded commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


SCHEMA = "arcpuzzles-passive-receipt-check-v1"


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def issue(report, severity, code, location, message):
    report[severity].append({"code": code, "location": location, "message": message})


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def within(path, root):
    return path == root or root in path.parents


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_non_json_number(value):
    raise ValueError(f"Non-JSON numeric constant: {value}")


def finite_json_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number exceeds finite floating-point range: {value}")
    return parsed


def default_work_root():
    # Script location, not the caller's cwd or a guessed fixed parent depth.
    for parent in Path(__file__).resolve().parents:
        if parent.name == "WORK" and (parent / "repo").is_dir():
            return parent
    raise ValueError("Cannot discover WORK from this helper's location; supply --work-root.")


def check_cwd(value, root, report, location):
    result = {"recorded": value, "resolved": None, "kind": "unknown", "exists": None}
    if not nonempty_string(value):
        issue(report, "errors", "cwd_invalid", location, "cwd must be a nonempty string without NUL characters.")
        return result
    windows = PureWindowsPath(value)
    if (windows.is_absolute() or PurePosixPath(value).is_absolute()) and not Path(value).is_absolute():
        result["kind"] = "absolute_foreign_platform"
        issue(report, "unknowns", "absolute_cwd_unavailable", location,
              "Recorded absolute cwd belongs to another platform; its historical existence is unverified.")
        return result
    if windows.drive and not Path(value).is_absolute():
        issue(report, "errors", "cwd_invalid", location, "Drive-relative cwd is ambiguous; use a full absolute path.")
        return result
    absolute = Path(value).is_absolute()
    result["kind"] = "packet_root" if value == "packet_root" else "absolute" if absolute else "work_relative"
    candidate = root.parent if value == "packet_root" else Path(value) if absolute else root / value
    try:
        path = candidate.resolve()
        result["resolved"] = str(path)
        if not absolute and value != "packet_root" and not within(path, root):
            issue(report, "errors", "cwd_outside_work", location,
                  "Relative cwd escapes WORK; use packet_root or record the actual absolute cwd.")
        elif path.is_dir():
            result["exists"] = True
        elif absolute and not path.exists():
            result["exists"] = False
            issue(report, "unknowns", "absolute_cwd_unavailable", location,
                  "Recorded absolute cwd is unavailable here; this does not disprove its historical use.")
        else:
            result["exists"] = path.exists()
            issue(report, "errors", "cwd_not_directory", location, "Recorded cwd does not resolve to an existing directory.")
    except (OSError, RuntimeError, ValueError) as exc:
        issue(report, "errors", "cwd_unreadable", location, str(exc))
    return result


def check_evidence(values, root, report, location):
    entries = []
    if not isinstance(values, list) or not values:
        issue(report, "errors", "evidence_paths_invalid", location,
              "evidence_paths must be a nonempty array of WORK-relative paths; absent evidence is not a pass.")
        return entries
    for index, value in enumerate(values):
        at = f"{location}[{index}]"
        entry = {"recorded": value, "resolved": None, "exists": None, "kind": "unknown"}
        entries.append(entry)
        if not nonempty_string(value):
            issue(report, "errors", "evidence_path_invalid", at, "Evidence path must be a nonempty string without NUL characters.")
            continue
        if Path(value).is_absolute() or PureWindowsPath(value).drive:
            issue(report, "errors", "evidence_outside_work", at, "Evidence paths must be relative to WORK, not absolute.")
            continue
        try:
            path = (root / value).resolve()
            entry["resolved"] = str(path)
            if not within(path, root):
                issue(report, "errors", "evidence_outside_work", at,
                      "Evidence escapes WORK after resolving path components and symlinks.")
                continue
            entry["exists"] = path.exists()
            if not path.exists():
                issue(report, "errors", "evidence_missing", at, "Cited evidence does not exist.")
            elif path.is_file():
                entry["kind"] = "file"
            elif path.is_dir():
                entry["kind"] = "directory"
                issue(report, "unknowns", "evidence_directory_not_inventoried", at,
                      "Directory exists; its contents and package inclusion were not inventoried.")
            else:
                issue(report, "errors", "evidence_not_regular", at, "Evidence is neither a regular file nor a directory.")
        except (OSError, RuntimeError, ValueError) as exc:
            issue(report, "errors", "evidence_unreadable", at, str(exc))
    return entries


def python_script_argument(argv):
    """Recognize direct/Python script invocation only, never parse shell payloads."""
    if Path(argv[0]).name == "run_with_racket.py":
        return argv[0]
    if not re.fullmatch(r"python(?:\d+(?:\.\d+)*)?(?:\.exe)?", Path(argv[0]).name):
        return None
    index = 1
    while index < len(argv):
        item = argv[index]
        if item == "-" or item.startswith(("-c", "-m")):
            return None
        if item == "--":
            return argv[index + 1] if index + 1 < len(argv) else None
        if item in {"-W", "-X", "--check-hash-based-pycs"}:
            index += 2
        elif item in {"-b", "-bb", "-B", "-d", "-E", "-i", "-I", "-O", "-OO", "-q", "-s", "-S", "-u", "-v", "-vv"} or item.startswith(("-W", "-X")):
            index += 1
        elif item.startswith("-"):
            # Unrecognized/combined options may contain a code/module switch.
            return None
        else:
            return item
    return None


def check_command(record, index, root, report, legacy_policy):
    location = f"verification_commands[{index}]"
    row = {"index": index, "argv_valid": False, "exit_code": None, "recorded_outcome": "unknown", "evidence": []}
    report["commands"].append(row)
    if not isinstance(record, dict):
        issue(report, "errors", "command_invalid", location, "Command entry must be a JSON object.")
        return
    argv = record.get("argv")
    row["argv_valid"] = (isinstance(argv, list) and bool(argv)
                         and all(isinstance(arg, str) and "\0" not in arg for arg in argv)
                         and bool(argv[0].strip()))
    if not row["argv_valid"]:
        issue(report, "errors", "argv_invalid", location + ".argv",
              "argv must be a nonempty array of strings with a nonempty executable and no NUL characters.")
    row["cwd"] = check_cwd(record.get("cwd"), root, report, location + ".cwd")
    if "exit_code" not in record:
        issue(report, "errors", "exit_code_missing", location + ".exit_code", "Record the actual integer exit code, or null when unknown.")
        issue(report, "unknowns", "exit_code_unknown", location + ".exit_code", "No exit outcome was recorded.")
    elif record["exit_code"] is None:
        issue(report, "unknowns", "exit_code_unknown", location + ".exit_code", "The recorded exit code is unknown.")
    elif type(record["exit_code"]) is not int:
        issue(report, "errors", "exit_code_invalid", location + ".exit_code", "Exit code must be an integer or null; booleans are not exit codes.")
    else:
        row["exit_code"] = record["exit_code"]
        row["recorded_outcome"] = "recorded_zero" if record["exit_code"] == 0 else "recorded_nonzero"
    row["evidence"] = check_evidence(record.get("evidence_paths"), root, report, location + ".evidence_paths")
    if row["argv_valid"] and row["cwd"]["resolved"] == str(root.parent):
        script = python_script_argument(argv)
        if script and not Path(script).is_absolute() and Path(script) == Path("run_with_racket.py"):
            if not (root.parent / script).is_file():
                issue(report, "errors" if legacy_policy == "error" else "warnings", "legacy_wrapper_wrong_cwd", location,
                      "Bare run_with_racket.py is recorded at outer packet_root, but that script is not there. "
                      "The documented wrapper lives in WORK. Record the actual WORK cwd, or the actual outer review.py command; do not rewrite history.")


def check_source(root, task_id, expected, report):
    source = report["source_check"]
    if task_id is None and expected is None:
        issue(report, "unknowns", "final_generator_hash_not_checked", "source_check",
              "No expected final source hash was supplied; evidence/source agreement is not established.")
        return
    source["status"] = "unknown"
    if task_id is None or expected is None:
        issue(report, "errors", "source_options_incomplete", "source_check", "Supply both --task-id and --expected-final-generator-sha256.")
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", task_id):
        issue(report, "errors", "task_id_invalid", "source_check", "Task ID must be a single safe directory name.")
        return
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
        issue(report, "errors", "expected_hash_invalid", "source_check", "Expected SHA-256 must contain exactly 64 hexadecimal digits.")
        return
    source.update(task_id=task_id, expected_sha256=expected.lower())
    try:
        path = (root / "repo" / "generators" / task_id / "generator.py").resolve()
        source["path"] = str(path)
        if not within(path, root):
            issue(report, "errors", "generator_outside_work", "source_check", "Selected generator path escapes WORK through a symlink.")
            return
        if not path.is_file():
            raise OSError("Selected generator is missing or is not a regular file.")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        source["actual_sha256"] = digest.hexdigest()
        source["status"] = "matched" if digest.hexdigest() == expected.lower() else "mismatched"
        if source["status"] == "mismatched":
            issue(report, "errors", "generator_hash_mismatch", "source_check", "Current generator bytes do not match the explicitly supplied final hash.")
    except (OSError, RuntimeError, ValueError) as exc:
        issue(report, "errors", "generator_unreadable", "source_check", str(exc))


def check_results(work_root, results_path=None, *, task_id=None, expected_final_generator_sha256=None, legacy_wrapper_policy="warn"):
    report = {
        "schema": SCHEMA, "validation_status": "invalid", "work_root": None, "results_path": None,
        "verification_status": "not_reexecuted", "semantic_verdict": "not_assessed",
        "actions": {"executed_recorded_commands": False, "edited_results": False, "read_evidence_contents": False},
        "errors": [], "warnings": [], "unknowns": [], "commands": [],
        "source_check": {"status": "not_requested"},
        "reported_completion_state": None, "reported_remaining_failure_count": None,
    }
    try:
        root = Path(work_root).resolve()
        report["work_root"] = str(root)
        if not root.is_dir():
            raise ValueError("--work-root must identify an existing directory.")
        path = Path(results_path).resolve() if results_path is not None else root / "RESULTS.json"
        report["results_path"] = str(path)
    except (OSError, RuntimeError, ValueError) as exc:
        issue(report, "errors", "work_root_invalid", "work_root", str(exc))
        return finish_report(report)
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_keys,
                              parse_constant=reject_non_json_number, parse_float=finite_json_float)
    except (OSError, UnicodeError) as exc:
        issue(report, "errors", "results_unreadable", "RESULTS.json", str(exc))
        return finish_report(report)
    except (ValueError, RecursionError) as exc:
        issue(report, "errors", "results_json_invalid", "RESULTS.json", str(exc))
        return finish_report(report)
    if not isinstance(document, dict):
        issue(report, "errors", "results_not_object", "RESULTS.json", "RESULTS.json must contain one JSON object.")
        return finish_report(report)
    for field in ("completion_state", "stopping_reason"):
        if not nonempty_string(document.get(field)):
            issue(report, "errors", "report_field_invalid", field, f"{field} must be a nonempty string.")
    report["reported_completion_state"] = document.get("completion_state")
    failures = document.get("remaining_failures")
    if not isinstance(failures, list):
        issue(report, "errors", "remaining_failures_invalid", "remaining_failures", "remaining_failures must be an explicit array.")
    else:
        report["reported_remaining_failure_count"] = len(failures)
    commands = document.get("verification_commands")
    if not isinstance(commands, list):
        issue(report, "errors", "verification_commands_invalid", "verification_commands", "verification_commands must be an explicit array.")
    elif not commands:
        issue(report, "unknowns", "no_commands_recorded", "verification_commands", "No verification commands were recorded; no verification success is inferred.")
    else:
        for index, record in enumerate(commands):
            check_command(record, index, root, report, legacy_wrapper_policy)
    check_source(root, task_id, expected_final_generator_sha256, report)
    return finish_report(report)


def finish_report(report):
    report["validation_status"] = "invalid" if report["errors"] else "valid_with_unknowns" if report["unknowns"] else "valid"
    report["counts"] = {
        "commands": len(report["commands"]),
        "cited_evidence_paths": sum(len(row["evidence"]) for row in report["commands"]),
        "recorded_zero_commands": sum(row["recorded_outcome"] == "recorded_zero" for row in report["commands"]),
        "recorded_nonzero_commands": sum(row["recorded_outcome"] == "recorded_nonzero" for row in report["commands"]),
        "unknown_exit_commands": sum(row["recorded_outcome"] == "unknown" for row in report["commands"]),
        **{severity: len(report[severity]) for severity in ("errors", "warnings", "unknowns")},
    }
    return report


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="?", help="RESULTS.json path, relative to the caller's cwd; defaults to WORK/RESULTS.json")
    parser.add_argument("--work-root", help="WORK directory; otherwise discovered from the helper's ancestors")
    parser.add_argument("--task-id", help="Selected generator directory name, used only for the optional byte hash")
    parser.add_argument("--expected-final-generator-sha256", help="Explicit expected SHA-256; requires --task-id")
    parser.add_argument("--legacy-wrapper-policy", choices=("warn", "error"), default="warn",
                        help="How to report bare run_with_racket.py recorded at outer packet_root (default: warn)")
    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        print(json.dumps({"schema": SCHEMA, "validation_status": "invalid", "errors": [
            {"code": "command_line_invalid", "location": "argv", "message": str(exc)}
        ], "verification_status": "not_reexecuted", "semantic_verdict": "not_assessed"}, indent=2))
        return 2
    try:
        root = args.work_root if args.work_root is not None else default_work_root()
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "validation_status": "invalid", "errors": [
            {"code": "work_root_undiscovered", "location": "work_root", "message": str(exc)}
        ], "verification_status": "not_reexecuted", "semantic_verdict": "not_assessed"}, indent=2))
        return 1
    report = check_results(root, args.results, task_id=args.task_id,
                           expected_final_generator_sha256=args.expected_final_generator_sha256,
                           legacy_wrapper_policy=args.legacy_wrapper_policy)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
