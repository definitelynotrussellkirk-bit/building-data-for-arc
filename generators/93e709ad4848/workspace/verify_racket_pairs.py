#!/usr/bin/env python3
r"""Bind every distinct lesson-probe input to the public canonical Racket rule.

Run from the extracted packet root, after freezing the selected generator::

    python3 repo/generators/93e709ad4848/workspace/verify_racket_pairs.py \
        --probe checks/lesson-probe-public-policy --out checks/racket-parity --workers 3

``--probe`` accepts a probe directory or its report.json; paths are relative to
the invocation directory. ``--out`` must be a new directory under packet checks/.
Packet discovery walks this script's parents for run_with_racket.py and repo/;
``--packet-root`` explicitly selects a relocated packet. No sibling checkout,
installed arcpuzzles package, private runner function, or Python grid oracle is
used. The local public rule_wrap.wrap_rule string normalizer is used solely to
verify the callable-source digest; every measured output comes from public CLI
Racket execution. Python probe outputs remain diagnostic comparison values.

Each disjoint batch contains at most 64 grids, with at most three public apply
processes running concurrently. The tool retains the exact commands, their
working directories and exit codes, inputs, stdout, stderr, unmodified Racket
receipts, all failures, and a compact Racket-derived pairs.jsonl. The report binds
probe artifacts and sources before execution and checks them again afterward.
Exit 0 means every distinct input has an authenticated Racket output equal to
its diagnostic helper value. Any mismatch, malformed receipt, process failure,
timeout, or source drift gives a nonzero exit; existing output is never resumed
or overwritten. Parity does not upgrade review/admission status or erase probe
failures. Reruns must use a fresh output directory.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import subprocess
import sys
import time
import traceback
import types
from typing import Any


TASK_ID = "93e709ad4848"
GENERATOR = f"generators/{TASK_ID}/generator.py"
CANONICAL = "shared/data/canonical/puzzles.jsonl"
RULE_NORMALIZER = "shared/runtime/puzzle_generators/rule_wrap.py"
RULE_PARSER = "shared/tools/comment_solutions.py"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def packed(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(packed(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(packed(row) + "\n" for row in rows), encoding="utf-8")


def fail(failures: list[dict[str, Any]], category: str, **details: Any) -> None:
    failures.append({"category": category, **details})


def safe_local(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or str(rel) != relative:
        raise ValueError(f"unsafe source path: {relative!r}")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"source path escapes selected root: {relative!r}")
    return result


def packet_root(explicit: Path | None) -> Path:
    candidates = [explicit.resolve()] if explicit else Path(__file__).resolve().parents
    for candidate in candidates:
        if (candidate / "run_with_racket.py").is_file() and (candidate / "repo" / "catalog" / "puzzles.jsonl").is_file():
            return candidate
    raise ValueError("cannot locate a packet with run_with_racket.py and repo/catalog/puzzles.jsonl; use --packet-root")


def grid_valid(grid: Any) -> bool:
    return (isinstance(grid, list) and 1 <= len(grid) <= 30
            and isinstance(grid[0], list) and 1 <= len(grid[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in grid))


def expected_rule(repo: Path) -> dict[str, Any]:
    """Read only this task's rule; normalize text, never apply it to a grid."""
    selector = re.compile(r'"task_id"\s*:\s*"' + re.escape(TASK_ID) + r'"')
    programs: list[str] = []
    with (repo / CANONICAL).open(encoding="utf-8") as handle:
        for line in handle:
            if not selector.search(line):
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError("selected canonical row has no program_solution")
                programs.append(program)
    if not programs or len(set(programs)) != 1:
        raise ValueError("selected canonical task must have one unambiguous rule text")
    path = repo / RULE_NORMALIZER
    spec = importlib.util.spec_from_file_location("parity_rule_text_normalizer", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load rule text normalizer: {path}")
    normalizer = importlib.util.module_from_spec(spec)
    # The normalizer's public parser import uses the disposable runtime's
    # scripts/ name. Resolve that namespace directly to this packet's shared
    # tools, without staging a runtime or importing any runner functionality.
    old_bytecode = sys.dont_write_bytecode
    previous = {name: sys.modules.get(name) for name in ("scripts", "scripts.comment_solutions")}
    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(repo / "shared" / "tools")]
    try:
        sys.dont_write_bytecode = True
        sys.modules["scripts"] = scripts
        sys.modules.pop("scripts.comment_solutions", None)
        spec.loader.exec_module(normalizer)
        source = programs[0]
        callable_text = normalizer.wrap_rule(source)
    finally:
        sys.dont_write_bytecode = old_bytecode
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return {"task_id": TASK_ID, "canonical_row_count": len(programs),
            "source_text_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "executed_rule_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
            "rule_text_sha256": hashlib.sha256(callable_text.encode()).hexdigest(),
            "normalizer_path": RULE_NORMALIZER, "normalizer_sha256": file_digest(path),
            "normalizer_parser_path": RULE_PARSER, "normalizer_parser_sha256": file_digest(repo / RULE_PARSER)}


def read_probe(root: Path, probe_path: Path, failures: list[dict[str, Any]], report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    repo = root / "repo"
    path = probe_path / "report.json" if probe_path.is_dir() else probe_path
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("probe must be retained inside the selected packet")
    probe = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(probe, dict):
        raise ValueError("probe report must be a JSON object")
    report["probe"] = {"report": path.relative_to(root).as_posix(), "report_sha256": file_digest(path),
                       "status": probe.get("status"), "failures": probe.get("failures"),
                       "sampling": probe.get("sampling"), "totals": probe.get("totals"),
                       "replay_command": probe.get("replay_command")}
    for field, expected in (("task_id", TASK_ID), ("selected_generator_path", GENERATOR),
                            ("source_hashes_unchanged_at_end", True)):
        if type(probe.get(field)) is not type(expected) or probe.get(field) != expected:
            fail(failures, "probe_identity", field=field, expected=expected, actual=probe.get(field))
    expected_sources = probe.get("sources_sha256")
    if not isinstance(expected_sources, dict) or not all(isinstance(k, str) and isinstance(v, str) and SHA256.fullmatch(v) for k, v in expected_sources.items()):
        raise ValueError("probe sources_sha256 must map relative source paths to full SHA-256 values")
    report["probe_sources_sha256"] = expected_sources
    for required in (GENERATOR, CANONICAL):
        if required not in expected_sources:
            fail(failures, "missing_required_source", path=required)
    sources: dict[str, Path] = {}
    for relative, expected in sorted(expected_sources.items()):
        source_path = safe_local(repo, relative)
        if not source_path.is_file():
            fail(failures, "missing_probe_source", path=relative)
            continue
        sources[f"repo/{relative}"] = source_path
        actual = file_digest(source_path)
        if actual != expected:
            fail(failures, "probe_source_hash_mismatch", path=relative, expected_sha256=expected, actual_sha256=actual)
    # Bind the public CLI route and its local metadata in addition to the probe's
    # declared sources. These are provenance, not substitute execution receipts.
    support = [root / "run_with_racket.py", root / "setup_racket.py", Path(__file__).resolve(),
               repo / RULE_NORMALIZER, repo / RULE_PARSER, repo / "catalog" / "puzzles.jsonl",
               repo / "catalog" / "runtime_files.json", repo / "catalog" / "authority_files.json"]
    support += sorted((repo / "src" / "arcpuzzles").glob("*.py"))
    for source_path in support:
        source_path = source_path.resolve()
        if not source_path.is_relative_to(root):
            raise ValueError("the verifier itself and all dependencies must be in the selected packet")
        if not source_path.is_file():
            raise ValueError(f"missing public execution support: {source_path.relative_to(root)}")
        sources[source_path.relative_to(root).as_posix()] = source_path
    pairs_path = path.parent / "pairs.jsonl"
    if not pairs_path.is_file():
        raise ValueError(f"missing probe pairs: {pairs_path}")
    pairs_artifact = probe.get("artifacts", {}).get("pairs.jsonl", {})
    actual_pairs_sha = file_digest(pairs_path)
    for field, actual in (("sha256", actual_pairs_sha), ("bytes", pairs_path.stat().st_size)):
        if pairs_artifact.get(field) != actual:
            fail(failures, "probe_pairs_artifact_mismatch", field=field, expected=pairs_artifact.get(field), actual=actual)
    report["probe"]["pairs"] = pairs_path.relative_to(root).as_posix()
    report["probe"]["pairs_sha256"] = actual_pairs_sha
    sources[path.relative_to(root).as_posix()] = path
    sources[pairs_path.relative_to(root).as_posix()] = pairs_path
    distinct: dict[str, dict[str, Any]] = {}
    records = duplicates = 0
    with pairs_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            records += 1
            try:
                pair = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(failures, "invalid_probe_pair_json", line=line_number, error=str(exc), raw_line=line.rstrip("\n"))
                continue
            if not isinstance(pair, dict) or not grid_valid(pair.get("input")) or not grid_valid(pair.get("output")):
                fail(failures, "invalid_probe_pair", line=line_number, pair=pair)
                continue
            for field in ("input", "output"):
                actual = digest(pair[field])
                if pair.get(field + "_sha256") != actual:
                    fail(failures, "probe_pair_digest_mismatch", line=line_number, field=field,
                         expected=pair.get(field + "_sha256"), actual=actual, pair=pair)
            key = digest(pair["input"])
            if key in distinct:
                duplicates += 1
                previous = distinct[key]
                if pair["input"] != previous["input"] or pair["output"] != previous["output"]:
                    fail(failures, "conflicting_duplicate_probe_input", line=line_number, previous_line=previous["probe_line"], pair=pair)
                previous["probe_lines"].append(line_number)
                continue
            distinct[key] = {**pair, "input_sha256": key, "output_sha256": digest(pair["output"]),
                             "probe_line": line_number, "probe_lines": [line_number]}
    report["probe"]["pair_records"] = records
    report["probe"]["duplicate_pair_records"] = duplicates
    report["probe"]["distinct_inputs"] = len(distinct)
    expected_count = probe.get("totals", {}).get("unique_generated_inputs")
    if type(expected_count) is not int or expected_count != len(distinct):
        fail(failures, "probe_unique_input_count_mismatch", expected=expected_count, actual=len(distinct))
    if not distinct:
        fail(failures, "empty_probe_pairs")
    return list(distinct.values()), sources


def verify_receipt(receipt: Any, pairs: list[dict[str, Any]], command: dict[str, Any], expected: dict[str, Any], root: Path, receipt_path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    verified: list[dict[str, Any]] = []
    counts = {"results_received": 0, "input_echoes_verified": 0, "racket_outputs_verified": 0,
              "helper_output_matches": 0, "helper_output_mismatches": 0}
    if not isinstance(receipt, dict):
        fail(failures, "invalid_receipt", receipt_type=type(receipt).__name__)
        return failures, verified, counts
    required = {"schema": "arcpuzzles-apply-v1", "task_id": TASK_ID, "rule_task_id": TASK_ID,
                "reference": "canonical", "rule_file": "data/canonical/puzzles.jsonl",
                "generator_sha256": expected["generator_sha256"],
                "executed_rule_hash": expected["executed_rule_hash"], "catalog_rule_hash": expected["executed_rule_hash"],
                "rule_hash_matches_catalog": True, "rule_text_sha256": expected["rule_text_sha256"],
                "command": ["arcpuzzles", *command["argv"][5:]], "cwd": str(root / "repo")}
    for field, wanted in required.items():
        if type(receipt.get(field)) is not type(wanted) or receipt.get(field) != wanted:
            fail(failures, "receipt_identity_mismatch", field=field, expected=wanted, actual=receipt.get(field))
    authority_verified = not failures and command["exit_code"] == 0 and command["timed_out"] is False
    results = receipt.get("results")
    if not isinstance(results, list):
        fail(failures, "invalid_receipt_results", actual_type=type(results).__name__)
        return failures, verified, counts
    counts["results_received"] = len(results)
    if len(results) != len(pairs):
        fail(failures, "receipt_result_count_mismatch", expected=len(pairs), actual=len(results))
    for index, pair in enumerate(pairs):
        evidence = {"index": index, "probe_lines": pair["probe_lines"], "input_sha256": pair["input_sha256"],
                    "input": pair["input"], "helper_output": pair["output"], "example_replays": pair.get("example_replays", [])}
        if index >= len(results):
            fail(failures, "missing_racket_result", **evidence)
            continue
        result = results[index]
        if not isinstance(result, dict):
            fail(failures, "invalid_racket_result", result=result, **evidence)
            continue
        row_ok = True
        for field, wanted in (("index", index), ("input", pair["input"]), ("input_sha256", pair["input_sha256"])):
            if type(result.get(field)) is not type(wanted) or result.get(field) != wanted:
                fail(failures, "racket_input_receipt_mismatch", field=field, expected=wanted, actual=result.get(field), **evidence)
                row_ok = False
        if not grid_valid(result.get("input")) or digest(result.get("input")) != pair["input_sha256"]:
            fail(failures, "racket_echoed_input_digest_mismatch", actual_echo_sha256=digest(result.get("input")), result=result, **evidence)
            row_ok = False
        if row_ok:
            counts["input_echoes_verified"] += 1
        output = result.get("output")
        if result.get("valid_output") is not True or result.get("error") is not None or not grid_valid(output):
            fail(failures, "racket_output_error", result=result, **evidence)
            row_ok = False
        output_sha = digest(output) if grid_valid(output) else None
        if output_sha is None or result.get("output_sha256") != output_sha:
            fail(failures, "racket_output_digest_mismatch", expected=output_sha, actual=result.get("output_sha256"), result=result, **evidence)
            row_ok = False
        equal = output == pair["output"]
        if not equal:
            fail(failures, "racket_helper_output_mismatch", racket_output=output, racket_output_sha256=output_sha,
                 helper_output_sha256=pair["output_sha256"], **evidence)
        if row_ok and authority_verified:
            counts["racket_outputs_verified"] += 1
            counts["helper_output_matches" if equal else "helper_output_mismatches"] += 1
            verified.append({"task_id": TASK_ID, "input": pair["input"], "output": output,
                             "input_sha256": pair["input_sha256"], "output_sha256": output_sha,
                             "label_source": "canonical Racket via public arcpuzzles apply; audit evidence only",
                             "helper_label_source": pair.get("label_source"), "helper_output_matches": equal,
                             "helper_output_sha256": pair["output_sha256"], "generator_sha256": expected["generator_sha256"],
                             "executed_rule_hash": expected["executed_rule_hash"], "rule_text_sha256": expected["rule_text_sha256"],
                             "probe_lines": pair["probe_lines"], "occurrence_count": pair.get("occurrence_count"),
                             "example_replays": pair.get("example_replays", []), "receipt_path": receipt_path,
                             "receipt_index": index, "command_exit_code": command["exit_code"]})
    for index in range(len(pairs), len(results)):
        fail(failures, "unexpected_racket_result", index=index, result=results[index])
    return failures, verified, counts


def run_batch(root: Path, out: Path, index: int, pairs: list[dict[str, Any]], expected: dict[str, Any], timeout: float) -> dict[str, Any]:
    directory = out / f"batch-{index:04d}"
    directory.mkdir()
    input_path, receipt_path = directory / "input.json", directory / "racket.json"
    input_path.write_text(packed([pair["input"] for pair in pairs]) + "\n", encoding="utf-8")
    input_arg, out_arg = "../" + input_path.relative_to(root).as_posix(), "../" + receipt_path.relative_to(root).as_posix()
    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
            "--input", input_arg, "--out", out_arg]
    command: dict[str, Any] = {"cwd": "packet_root", "argv": argv, "exit_code": None, "timed_out": False,
                              "environment_overrides": {"ARCPUZZLES_HOME": "packet_root/repo", "PYTHONNOUSERSITE": "1"},
                              "evidence_paths": []}
    record: dict[str, Any] = {"batch_index": index, "input_count": len(pairs), "started_at": now(), "command": command,
                              "input_sha256": file_digest(input_path), "expected_source_identity": expected,
                              "status": "RUNNING", "failures": [], "verified_pairs": [], "counts": {}}
    batch_report = directory / "report.json"
    write_json(batch_report, {k: v for k, v in record.items() if k != "verified_pairs"})
    started = time.monotonic()
    try:
        env = dict(os.environ)
        env.update({"ARCPUZZLES_HOME": str(root / "repo"), "PYTHONNOUSERSITE": "1"})
        with (directory / "stdout.log").open("wb") as stdout, (directory / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                command["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                command["timed_out"] = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                command["exit_code"] = process.returncode
                fail(record["failures"], "public_apply_timeout", timeout_seconds=timeout)
        if command["exit_code"] != 0:
            fail(record["failures"], "public_apply_nonzero_exit", exit_code=command["exit_code"])
        if not receipt_path.is_file():
            fail(record["failures"], "missing_public_apply_receipt")
        else:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_failures, verified, counts = verify_receipt(receipt, pairs, command, expected, root, receipt_path.relative_to(root).as_posix())
            record["failures"].extend(receipt_failures)
            record["verified_pairs"], record["counts"] = verified, counts
            record["receipt_sha256"] = file_digest(receipt_path)
            record["receipt_review_status"] = {field: receipt.get(field) for field in ("approved", "catalog_approved", "train_safety", "note")}
    except Exception as exc:
        fail(record["failures"], "batch_exception", exception_type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    record["elapsed_seconds"], record["finished_at"] = round(time.monotonic() - started, 3), now()
    record["status"] = "PASS" if not record["failures"] else "FAIL"
    command["evidence_paths"] = [path.relative_to(root).as_posix() for path in sorted(directory.iterdir()) if path.is_file()]
    write_json(batch_report, {k: v for k, v in record.items() if k != "verified_pairs"})
    return record


def bounded_int(maximum: int):
    def parse(value: str) -> int:
        result = int(value)
        if not 1 <= result <= maximum:
            raise argparse.ArgumentTypeError(f"must be in 1..{maximum}")
        return result
    return parse


def positive_timeout(value: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path)
    parser.add_argument("--workers", type=bounded_int(3), default=3)
    parser.add_argument("--batch-size", type=bounded_int(64), default=64)
    parser.add_argument("--batch-timeout", type=positive_timeout, default=240.0, help="outer per-batch timeout in seconds; public apply retains its own default timeout")
    args = parser.parse_args(argv)
    try:
        root, out = packet_root(args.packet_root), args.out.resolve()
        if not out.is_relative_to(root / "checks") or out == root / "checks":
            raise ValueError("--out must be a fresh child directory of packet_root/checks")
        if out.exists():
            raise FileExistsError(f"output already exists; choose a fresh --out: {out}")
        out.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as exc:
        print(f"parity verifier: {exc}", file=sys.stderr)
        return 2
    started = time.monotonic()
    failures: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    official: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    sources: dict[str, Path] = {}
    report: dict[str, Any] = {"schema": "task-public-racket-parity-v1", "task_id": TASK_ID,
                              "status": "RUNNING", "started_at": now(), "python_version": platform.python_version(),
                              "packet_root_at_execution": str(root), "invocation_cwd": str(Path.cwd()),
                              "invocation_argv": [sys.executable, *sys.argv], "workers": args.workers,
                              "batch_size": args.batch_size, "batch_timeout_seconds": args.batch_timeout,
                              "label_authority": "Actual retained outputs are derived only from canonical Racket through public apply.",
                              "limitation": "Parity covers these distinct inputs only; it does not upgrade approval or resolve independent probe failures."}
    try:
        pairs, sources = read_probe(root, args.probe.resolve(), failures, report)
        report["sources_sha256_at_start"] = {name: file_digest(path) for name, path in sorted(sources.items())}
        # Recheck the actual accepted snapshot: a concurrent edit between the
        # first validation read and this snapshot must not bind a stale probe.
        for relative, wanted in report["probe_sources_sha256"].items():
            actual = report["sources_sha256_at_start"].get(f"repo/{relative}")
            if actual != wanted:
                fail(failures, "probe_source_snapshot_mismatch", path=relative, expected_sha256=wanted, actual_sha256=actual)
        expectation = expected_rule(root / "repo")
        expectation["generator_sha256"] = file_digest(root / "repo" / GENERATOR)
        expectation["canonical_file_sha256"] = file_digest(root / "repo" / CANONICAL)
        report["expected_source_identity"] = expectation
        if not failures:
            groups = [pairs[offset:offset + args.batch_size] for offset in range(0, len(pairs), args.batch_size)]
            report["planned_batch_count"] = len(groups)
            write_json(out / "report.json", report)
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                pending = {executor.submit(run_batch, root, out, index, group, expectation, args.batch_timeout): index for index, group in enumerate(groups)}
                for future in as_completed(pending):
                    try:
                        record = future.result()
                    except Exception as exc:
                        fail(failures, "batch_executor_exception", batch_index=pending[future], exception_type=type(exc).__name__,
                             message=str(exc), traceback=traceback.format_exc())
                        continue
                    batches.append(record)
                    print(packed({"batch": record["batch_index"], "status": record["status"],
                                  "inputs": record["input_count"], "helper_matches": record["counts"].get("helper_output_matches", 0),
                                  "failures": len(record["failures"])}), flush=True)
            batches.sort(key=lambda record: record["batch_index"])
            for record in batches:
                official.extend(record["verified_pairs"])
                for item in record["failures"]:
                    failures.append({"batch_index": record["batch_index"], **item})
    except Exception as exc:
        fail(failures, "verifier_exception", exception_type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    after: dict[str, str | None] = {}
    for name, path in sorted(sources.items()):
        try:
            after[name] = file_digest(path)
        except OSError as exc:
            after[name] = None
            fail(failures, "source_unreadable_after_run", path=name, error=str(exc))
        before = report.get("sources_sha256_at_start", {}).get(name)
        if before is not None and after[name] != before:
            fail(failures, "source_changed_during_run", path=name, before_sha256=before, after_sha256=after[name])
    report["sources_sha256_at_end"] = after
    report["source_hashes_unchanged_at_end"] = bool(sources) and after == report.get("sources_sha256_at_start")
    matched = [pair for pair in official if pair["helper_output_matches"]]
    report["totals"] = {"probe_distinct_inputs": len(pairs), "batches_planned": report.get("planned_batch_count", 0),
                        "batches_completed": len(batches), "batches_passed": sum(row["status"] == "PASS" for row in batches),
                        "public_apply_inputs": sum(row["input_count"] for row in batches),
                        "racket_verified_input_output_pairs": len(official), "unique_racket_inputs": len({row["input_sha256"] for row in official}),
                        "unique_racket_outputs": len({row["output_sha256"] for row in official}),
                        "unique_inputs_matching_helper": len({row["input_sha256"] for row in matched}),
                        "racket_helper_output_mismatches": sum(not row["helper_output_matches"] for row in official),
                        "failure_records": len(failures)}
    if not failures and len(matched) != len(pairs):
        fail(failures, "incomplete_parity", expected=len(pairs), matching=len(matched))
    report["totals"]["failure_records"] = len(failures)
    report["verification_commands"] = [row["command"] for row in batches]
    report["batch_reports"] = [(out / f"batch-{row['batch_index']:04d}" / "report.json").relative_to(root).as_posix() for row in batches]
    write_jsonl(out / "pairs.jsonl", official)
    write_jsonl(out / "failures.jsonl", failures)
    write_jsonl(out / "commands.jsonl", report["verification_commands"])
    report["status"] = "PASS_RACKET_PARITY" if not failures else "FAIL_RACKET_PARITY"
    report["exit_code"] = 0 if not failures else 1
    report["finished_at"], report["elapsed_seconds"] = now(), round(time.monotonic() - started, 3)
    report["artifacts"] = {path.relative_to(out).as_posix(): {"bytes": path.stat().st_size, "sha256": file_digest(path)}
                           for path in sorted(out.rglob("*")) if path.is_file() and path != out / "report.json"}
    write_json(out / "report.json", report)
    print(packed({"status": report["status"], "totals": report["totals"], "report": str(out / "report.json")}), flush=True)
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
