#!/usr/bin/env python3
"""Lint and execute-verify base solution files.

This is the hard gate for `data/base/solutions/*.json` records. Static checks
catch schema, leakage, image, and function-inventory problems; execution
checks load the Racket `(rule! ...)` and compare outputs against all visible
train pairs plus any verification-only expected test outputs.

Examples:
    python3 scripts/lint_base_solutions.py --limit 20
    python3 scripts/lint_base_solutions.py --task-id 0607ce86
    python3 scripts/lint_base_solutions.py --path data/base/solutions/training/00576224__ecc04b33119c.json
    python3 scripts/lint_base_solutions.py --all --jsonl tmp/base_lint.jsonl
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import re
import signal
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from queue import Empty
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from arc_repl.builtins import _unwrap  # noqa: E402
from arc_repl.executor import ArcExecutor  # noqa: E402
from arc_repl.parser import Symbol, parse_all  # noqa: E402
from lint_puzzles import validate_grid  # noqa: E402
from mine_primitive_usage import (  # noqa: E402
    classify,
    useful_calls,
    unique_in_order,
)

DEFAULT_MANIFEST = ROOT / "data" / "base" / "manifest.json"
DEFAULT_SOLUTIONS_DIR = ROOT / "data" / "base" / "solutions"
PRELUDE_PATH = ROOT / "arc_repl" / "racket_prelude" / "arc-prelude.rkt"


@dataclass(frozen=True)
class LintIssue:
    code: str
    severity: str
    message: str
    field: str = ""


@dataclass
class LintResult:
    path: str
    task_id: str = ""
    content_hash: str = ""
    source: str = ""
    status: str = "unknown"
    issues: list[LintIssue] | None = None
    canonical_functions_used: list[str] | None = None
    unknown_calls: list[str] | None = None
    train_pairs_checked: int = 0
    test_outputs_checked: int = 0

    def error_count(self) -> int:
        return sum(1 for issue in self.issues or [] if issue.severity == "error")

    def warning_count(self) -> int:
        return sum(1 for issue in self.issues or [] if issue.severity == "warning")


def issue(code: str, severity: str, message: str, field: str = "") -> LintIssue:
    return LintIssue(code=code, severity=severity, message=message, field=field)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"manifest not found: {path}")
    return load_json(path)


def known_prelude_functions(path: Path = PRELUDE_PATH) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text()
    names = set(re.findall(r"^\(define\s+\(([^()\s]+)", text, flags=re.MULTILINE))
    names.update(re.findall(r"^\(define\s+([^()\s]+)\s+", text, flags=re.MULTILINE))
    return names


def local_defined_functions(code: str) -> set[str]:
    names = set(re.findall(r"\(define\s+\(([^()\s]+)", code))
    names.update(re.findall(r"\(let\s+([^()\s]+)\s+\(", code))
    return names


def validate_required_shape(record: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    required = {
        "schema_version",
        "base_id",
        "task_id",
        "content_hash",
        "files",
        "visible_context",
        "description_target",
        "racket_target",
        "verification",
    }
    for field in sorted(required):
        if field not in record:
            issues.append(issue("A002", "error", f"missing required field `{field}`", field))

    vc = record.get("visible_context")
    if not isinstance(vc, dict):
        issues.append(issue("A002", "error", "`visible_context` must be an object", "visible_context"))
        return issues
    if not isinstance(vc.get("train"), list):
        issues.append(issue("A002", "error", "`visible_context.train` must be a list", "visible_context.train"))
    if not isinstance(vc.get("test_inputs"), list):
        issues.append(issue("A002", "error", "`visible_context.test_inputs` must be a list", "visible_context.test_inputs"))

    rt = record.get("racket_target")
    if not isinstance(rt, dict):
        issues.append(issue("A002", "error", "`racket_target` must be an object", "racket_target"))
    ver = record.get("verification")
    if not isinstance(ver, dict):
        issues.append(issue("A002", "error", "`verification` must be an object", "verification"))

    return issues


def validate_visible_grids(record: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    vc = record.get("visible_context") or {}

    for idx, pair in enumerate(vc.get("train") or []):
        if not isinstance(pair, dict):
            issues.append(issue("A003", "error", "train pair must be an object", f"visible_context.train[{idx}]"))
            continue
        for key in ("input", "output"):
            errs = validate_grid(pair.get(key), f"visible_context.train[{idx}].{key}")
            issues.extend(issue("A003", "error", err, f"visible_context.train[{idx}].{key}") for err in errs)

    for idx, test in enumerate(vc.get("test_inputs") or []):
        if not isinstance(test, dict):
            issues.append(issue("A003", "error", "test input row must be an object", f"visible_context.test_inputs[{idx}]"))
            continue
        if "output" in test:
            issues.append(issue(
                "A013",
                "error",
                "visible test input leaks an output; outputs belong only in verification.expected_test_outputs",
                f"visible_context.test_inputs[{idx}].output",
            ))
        errs = validate_grid(test.get("input"), f"visible_context.test_inputs[{idx}].input")
        issues.extend(issue("A003", "error", err, f"visible_context.test_inputs[{idx}].input") for err in errs)

    expected = (record.get("verification") or {}).get("expected_test_outputs") or []
    if not isinstance(expected, list):
        issues.append(issue("A002", "error", "`verification.expected_test_outputs` must be a list", "verification.expected_test_outputs"))
    else:
        for idx, grid in enumerate(expected):
            errs = validate_grid(grid, f"verification.expected_test_outputs[{idx}]")
            issues.extend(issue("A003", "error", err, f"verification.expected_test_outputs[{idx}]") for err in errs)

    return issues


def validate_image_file(record: dict[str, Any]) -> list[LintIssue]:
    files = record.get("files") or {}
    image_status = files.get("task_image_status")
    image_rel = files.get("task_image_relpath")
    if image_status != "generated":
        return [issue("A010", "warning", f"task image status is {image_status!r}", "files.task_image_status")]
    if not isinstance(image_rel, str) or not image_rel:
        return [issue("A010", "error", "generated task image has no path", "files.task_image_relpath")]
    image_path = ROOT / image_rel
    if not image_path.exists():
        return [issue("A010", "error", f"task image path does not exist: {image_rel}", "files.task_image_relpath")]
    return []


def validate_description(record: dict[str, Any]) -> list[LintIssue]:
    desc = record.get("description_target") or {}
    if not str(desc.get("target_text") or "").strip():
        return [issue("A011", "warning", "description target is missing", "description_target.target_text")]
    return []


def validate_racket_parse(code: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    try:
        exprs = parse_all(code)
    except SyntaxError as exc:
        return [issue("A004", "error", f"Racket/S-expression parse failed: {exc}", "racket_target.target_code")]
    if not exprs:
        issues.append(issue("A004", "error", "missing top-level expression", "racket_target.target_code"))
        return issues
    if len(exprs) != 1:
        issues.append(issue(
            "A015",
            "warning",
            f"expected one top-level expression; parser found {len(exprs)} and executor will ignore trailing forms",
            "racket_target.target_code",
        ))
    expr = exprs[0]
    if not isinstance(expr, list) or not expr or not isinstance(expr[0], Symbol) or expr[0].name != "rule!":
        issues.append(issue("A004", "error", "top-level expression must be `(rule! ...)`", "racket_target.target_code"))
    if code.lstrip().startswith("(rule! (lambda"):
        issues.append(issue("A012", "warning", "legacy `(rule! (lambda ...))` form; canonical target is `(rule! BODY)`", "racket_target.target_code"))
    if re.search(r"\(for/first\b", code):
        issues.append(issue("A014", "warning", "`for/first` appears; verify it is not being used as a false-skipping search", "racket_target.target_code"))
    return issues


def function_inventory(code: str, known_functions: set[str]) -> tuple[list[str], list[str]]:
    calls = unique_in_order(useful_calls(code, include_unknown=True))
    local_defs = local_defined_functions(code)

    canonical: list[str] = []
    unknown: list[str] = []
    for name in calls:
        if name in local_defs:
            continue
        if name in known_functions or classify(name) != "unknown":
            canonical.append(name)
        else:
            unknown.append(name)
    return canonical, unknown


def validate_primitive_metadata(
    record: dict[str, Any],
    canonical_functions: list[str],
    unknown_calls: list[str],
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    if unknown_calls:
        issues.append(issue(
            "A008",
            "warning",
            "unclassified call heads found: " + ", ".join(unknown_calls[:12]),
            "racket_target.target_code",
        ))

    meta = record.get("primitive_metadata") or {}
    if meta.get("source") == "mined_from_racket":
        stored = meta.get("primitive_chain") or []
        if stored != canonical_functions:
            issues.append(issue(
                "A009",
                "warning",
                "primitive_metadata.primitive_chain is stale relative to target_code",
                "primitive_metadata.primitive_chain",
            ))
    return issues


def normalize_grid_value(grid: Any) -> Any:
    if isinstance(grid, list) and grid and all(isinstance(row, str) for row in grid):
        try:
            return [[int(ch) for ch in row] for row in grid]
        except ValueError:
            return grid
    return grid


def normalize_train_pairs(train: Any) -> list[dict[str, Any]]:
    if not isinstance(train, list):
        return []
    out: list[dict[str, Any]] = []
    for pair in train:
        if not isinstance(pair, dict):
            continue
        item = dict(pair)
        if "input" in item:
            item["input"] = normalize_grid_value(item.get("input"))
        if "output" in item:
            item["output"] = normalize_grid_value(item.get("output"))
        out.append(item)
    return out


def normalize_test_inputs(test_inputs: Any) -> list[dict[str, Any]]:
    if not isinstance(test_inputs, list):
        return []
    out: list[dict[str, Any]] = []
    for item in test_inputs:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        if "input" in row:
            row["input"] = normalize_grid_value(row.get("input"))
        out.append(row)
    return out


def execute_verify(record: dict[str, Any], code: str) -> tuple[list[LintIssue], int, int]:
    issues: list[LintIssue] = []
    vc = record.get("visible_context") or {}
    train = normalize_train_pairs(vc.get("train") or [])
    test_inputs = normalize_test_inputs(vc.get("test_inputs") or [])
    expected_tests = [
        normalize_grid_value(grid)
        for grid in ((record.get("verification") or {}).get("expected_test_outputs") or [])
    ]

    task = {
        "train": train,
        "test": test_inputs,
    }
    ex = ArcExecutor(task, auto_scan_on_load=False, use_racket=True)

    loaded = ex.step(code)
    if loaded.startswith("ERROR:"):
        return [issue("A004", "error", f"rule load failed: {loaded[:500]}", "racket_target.target_code")], 0, 0

    train_checked = 0
    for idx in range(len(train)):
        obs = ex.step(f"(test! {idx})")
        train_checked += 1
        if "PASS" not in obs:
            issues.append(issue("A005", "error", f"train pair {idx} failed: {obs[:800]}", f"visible_context.train[{idx}]"))

    test_checked = 0
    result_refs: list[str] = []
    for idx in range(len(test_inputs)):
        obs = ex.step(f"(apply! {idx})")
        match = re.match(r"(_\d+)", obs)
        if obs.startswith("ERROR:") or match is None:
            issues.append(issue("A006", "error", f"apply! {idx} failed: {obs[:500]}", f"visible_context.test_inputs[{idx}]"))
            continue
        ref = match.group(1)
        result_refs.append(ref)
        if idx < len(expected_tests):
            actual = _unwrap(ex._results.get(ref))
            expected = expected_tests[idx]
            test_checked += 1
            if actual != expected:
                issues.append(issue("A006", "error", f"test output {idx} mismatch", f"verification.expected_test_outputs[{idx}]"))

    if len(expected_tests) != len(test_inputs):
        issues.append(issue(
            "A007",
            "warning",
            f"expected_test_outputs count {len(expected_tests)} does not match test_inputs count {len(test_inputs)}",
            "verification.expected_test_outputs",
        ))

    return issues, train_checked, test_checked


def lint_solution_file(
    path: Path,
    *,
    known_functions: set[str],
    include_needs_conversion: bool,
    execute: bool,
) -> LintResult:
    try:
        record = load_json(path)
    except Exception as exc:
        return LintResult(
            path=str(path),
            status="error",
            issues=[issue("A002", "error", f"cannot read JSON: {exc}")],
        )

    result = LintResult(
        path=str(path),
        task_id=str(record.get("task_id") or ""),
        content_hash=str(record.get("content_hash") or ""),
        source=str(record.get("source") or ""),
        issues=[],
        canonical_functions_used=[],
        unknown_calls=[],
    )

    issues: list[LintIssue] = []
    issues.extend(validate_required_shape(record))
    issues.extend(validate_visible_grids(record))
    issues.extend(validate_image_file(record))
    issues.extend(validate_description(record))

    rt = record.get("racket_target") or {}
    code = str(rt.get("target_code") or "").strip()
    needs_conversion = bool(rt.get("needs_conversion"))
    if not code:
        if include_needs_conversion or not needs_conversion:
            issues.append(issue("A001", "error", "missing Racket target code", "racket_target.target_code"))
        result.status = "skipped_needs_conversion" if needs_conversion else "error"
        result.issues = issues
        return result

    issues.extend(validate_racket_parse(code))
    canonical_functions, unknown_calls = function_inventory(code, known_functions)
    result.canonical_functions_used = canonical_functions
    result.unknown_calls = unknown_calls
    issues.extend(validate_primitive_metadata(record, canonical_functions, unknown_calls))

    if execute and not any(item.severity == "error" and item.code in {"A002", "A003", "A004"} for item in issues):
        exec_issues, train_checked, test_checked = execute_verify(record, code)
        result.train_pairs_checked = train_checked
        result.test_outputs_checked = test_checked
        issues.extend(exec_issues)

    result.issues = issues
    if any(item.severity == "error" for item in issues):
        result.status = "fail"
    elif any(item.severity == "warning" for item in issues):
        result.status = "pass_with_warnings"
    else:
        result.status = "pass"
    return result


def _lint_solution_file_worker(
    queue: mp.Queue,
    path_text: str,
    known_functions: set[str],
    include_needs_conversion: bool,
    execute: bool,
) -> None:
    try:
        os.setsid()
    except OSError:
        pass
    try:
        result = lint_solution_file(
            Path(path_text),
            known_functions=known_functions,
            include_needs_conversion=include_needs_conversion,
            execute=execute,
        )
    except Exception as exc:
        result = LintResult(
            path=path_text,
            status="fail",
            issues=[issue("A017", "error", f"verifier crashed: {exc}")],
        )
    queue.put(result)


def lint_solution_file_with_timeout(
    path: Path,
    *,
    known_functions: set[str],
    include_needs_conversion: bool,
    execute: bool,
    per_file_timeout: float,
) -> LintResult:
    if not execute or per_file_timeout <= 0:
        return lint_solution_file(
            path,
            known_functions=known_functions,
            include_needs_conversion=include_needs_conversion,
            execute=execute,
        )

    ctx = mp.get_context("fork")
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_lint_solution_file_worker,
        args=(queue, str(path), known_functions, include_needs_conversion, execute),
    )
    proc.start()
    proc.join(per_file_timeout)

    if proc.is_alive():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            proc.terminate()
        proc.join(2)
        return LintResult(
            path=str(path),
            status="fail",
            issues=[issue(
                "A016",
                "error",
                f"execution timed out after {per_file_timeout:.1f}s",
                "racket_target.target_code",
            )],
        )

    try:
        return queue.get(timeout=1)
    except Empty:
        return LintResult(
            path=str(path),
            status="fail",
            issues=[issue("A017", "error", f"verifier worker exited with code {proc.exitcode}")],
        )


def select_paths(args: argparse.Namespace) -> list[Path]:
    if args.path:
        return [Path(p) for p in args.path]

    manifest = load_manifest(args.manifest)
    rows = manifest.get("solutions") or []
    paths: list[Path] = []
    wanted_tasks = set(args.task_id or [])
    for row in rows:
        if wanted_tasks and row.get("task_id") not in wanted_tasks:
            continue
        if args.source and row.get("source") != args.source:
            continue
        if args.racket_only and row.get("racket_status") != "verified_racket_available":
            continue
        if args.needs_conversion_only and row.get("racket_status") != "needs_racket_conversion":
            continue
        rel = row.get("solution_relpath")
        if isinstance(rel, str) and rel:
            paths.append(ROOT / rel)

    if args.limit is not None:
        paths = paths[:args.limit]
    return paths


def result_to_jsonable(result: LintResult) -> dict[str, Any]:
    data = asdict(result)
    data["issues"] = [asdict(item) for item in (result.issues or [])]
    return data


def print_summary(results: list[LintResult], *, strict: bool) -> None:
    status_counts = Counter(result.status for result in results)
    issue_counts = Counter(issue.code for result in results for issue in (result.issues or []))
    error_count = sum(result.error_count() for result in results)
    warning_count = sum(result.warning_count() for result in results)
    train_checked = sum(result.train_pairs_checked for result in results)
    test_checked = sum(result.test_outputs_checked for result in results)

    print(f"Base solution lint: {len(results)} file(s)")
    print(f"  statuses: {dict(sorted(status_counts.items()))}")
    print(f"  issues  : {error_count} error(s), {warning_count} warning(s)")
    print(f"  checked : {train_checked} train pair(s), {test_checked} expected test output(s)")
    if issue_counts:
        print("  by code :")
        for code, count in sorted(issue_counts.items()):
            print(f"    {code}: {count}")

    failures = [
        result for result in results
        if result.error_count() or (strict and result.warning_count())
    ]
    for result in failures[:20]:
        print(f"\n{result.status.upper()} {result.path}")
        for item in (result.issues or [])[:8]:
            if item.severity == "warning" and not strict:
                continue
            loc = f" [{item.field}]" if item.field else ""
            print(f"  {item.severity.upper()} {item.code}{loc}: {item.message}")
    if len(failures) > 20:
        print(f"\n... {len(failures) - 20} more failing file(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint and execute-verify base solution files.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--path", action="append", help="Specific solution JSON path. May repeat.")
    parser.add_argument("--task-id", action="append", help="Specific task_id from the manifest. May repeat.")
    parser.add_argument("--source", help="Filter by source exactly, e.g. training or bank:additional_bank.")
    parser.add_argument("--limit", type=int, help="Limit selected paths after filtering.")
    parser.add_argument("--all", action="store_true", help="Explicitly lint all selected manifest rows.")
    parser.add_argument("--racket-only", action="store_true", help="Only lint rows with verified Racket target status.")
    parser.add_argument("--needs-conversion-only", action="store_true", help="Only lint rows still needing conversion.")
    parser.add_argument("--include-needs-conversion", action="store_true", help="Report missing Racket code as an error instead of skipping conversion rows.")
    parser.add_argument("--no-execute", action="store_true", help="Run static checks only; do not execute Racket rules.")
    parser.add_argument("--per-file-timeout", type=float, default=30.0, help="Seconds before a per-file Racket execution check fails; use 0 to disable.")
    parser.add_argument("--progress", action="store_true", help="Print one progress line per selected file to stderr.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--jsonl", type=Path, help="Write per-file lint results as JSONL.")
    args = parser.parse_args()

    if not args.all and not args.path and not args.task_id and args.limit is None:
        # Keep accidental full execution explicit. Static conversion rows can
        # be inspected with --all --no-execute or filtered with --racket-only.
        args.limit = 25

    paths = select_paths(args)
    known_functions = known_prelude_functions()
    results: list[LintResult] = []
    for index, path in enumerate(paths, start=1):
        if args.progress:
            print(f"[{index}/{len(paths)}] {path}", file=sys.stderr, flush=True)
        results.append(lint_solution_file_with_timeout(
            path,
            known_functions=known_functions,
            include_needs_conversion=args.include_needs_conversion,
            execute=not args.no_execute,
            per_file_timeout=args.per_file_timeout,
        ))

    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.jsonl.open("w") as f:
            for result in results:
                f.write(json.dumps(result_to_jsonable(result), sort_keys=True) + "\n")
        print(f"Wrote {args.jsonl}")

    print_summary(results, strict=args.strict)

    has_errors = any(result.error_count() for result in results)
    has_warnings = any(result.warning_count() for result in results)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
