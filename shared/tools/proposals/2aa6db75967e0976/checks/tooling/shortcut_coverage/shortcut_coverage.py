#!/usr/bin/env python3
"""Passive, source-bound teaching-coverage diagnostic for public lesson censuses."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import types

PREFIX = "CANONICAL_SHORTCUTS:"


class CoverageError(ValueError):
    pass


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_file_hash(path, expected, label):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise CoverageError(f"{label}: missing or invalid SHA-256 binding")
    actual = file_hash(path)
    if actual != expected:
        raise CoverageError(f"{label}: hash mismatch: expected {expected}, found {actual} at {path}")
    return actual


def read_census(path):
    path = Path(path)
    with (gzip.open(path, "rt") if path.suffix == ".gz" else path.open()) as stream:
        report = json.load(stream)
    if not isinstance(report, dict) or report.get("schema") != "arcpuzzles-lesson-census-v1":
        raise CoverageError("Expected public arcpuzzles-lesson-census-v1 JSON or JSON.gz")
    return report


def discover_shortcuts(report):
    declarations = report.get("rivals")
    if not isinstance(declarations, list) or any(not isinstance(name, str) for name in declarations):
        raise CoverageError("Missing declared rival inventory")
    names = [name for name in declarations if name.startswith(PREFIX)]
    if any(name == PREFIX for name in names) or len(set(names)) != len(names):
        raise CoverageError("Invalid or duplicate canonical shortcut binding")
    return sorted(names)


def normalize_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise CoverageError("Expected a nonempty labelled integer grid")
    result = []
    for row in grid:
        if isinstance(row, str):
            try:
                row = [int(ch) for ch in row if not ch.isspace()]
            except ValueError as error:
                raise CoverageError("Invalid digit row") from error
        if not isinstance(row, list) or not row or any(type(v) is not int or not 0 <= v <= 9 for v in row):
            raise CoverageError("Expected rows of integer ARC colours")
        result.append(list(row))
    if len({len(row) for row in result}) != 1:
        raise CoverageError("Ragged grid")
    return result


def score_window(demos, query, shortcuts):
    pairs = []
    for pair in [*demos, query]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise CoverageError("Missing labelled input/output pair")
        pairs.append({"input": normalize_grid(pair["input"]), "output": normalize_grid(pair["output"])})
    result = {"demo_count": len(demos), "pair_count": len(pairs), "shortcuts": {}}
    for name, shortcut in sorted(shortcuts.items()):
        matches, errors = [], []
        for index, pair in enumerate(pairs):
            try:
                prediction = normalize_grid(shortcut(copy.deepcopy(pair["input"])))
                matches.append(prediction == pair["output"])
            except Exception as error:
                matches.append(None)
                errors.append({"pair_index": index, "error": f"{type(error).__name__}: {error}"})
        known = not errors
        demo_count = sum(match is False for match in matches[:-1]) if known else None
        total = sum(match is False for match in matches) if known else None
        outcome = "error" if not known else "refuted" if demo_count else "survived_all" if matches[-1] else "ambiguous"
        result["shortcuts"][name] = {
            "demo_refutations": demo_count,
            "demo_refutation_indices": [i for i, match in enumerate(matches[:-1]) if match is False],
            "window_refutations": total,
            "pair_matches": matches,
            "query_matches": matches[-1],
            "teaching_covered": demo_count >= 1 if known else None,
            "rotation_robust": total >= 2 if known else None,
            "holdout_demo_refutations": [total - int(match is False) for match in matches] if known else [None] * len(pairs),
            "support_equivalent_on_this_window": all(matches) if known else None,
            "recomputed_outcome": outcome,
            "errors": errors,
        }
    return result


def analyze_census(report, shortcuts):
    names = discover_shortcuts(report)
    if set(names) != set(shortcuts):
        raise CoverageError(f"Canonical shortcut inventory mismatch: evidence={names}, source={sorted(shortcuts)}")
    rows = report.get("lessons")
    if not isinstance(rows, list):
        raise CoverageError("Missing materialized lessons")
    summary = {"requested_lessons": len(rows), "complete_lessons": 0, "incomplete_lessons": 0,
               "canonical_shortcuts": len(names), "scoring_error_rows": 0,
               "saved_outcome_mismatches": 0, "unrefuted_demo_rows": 0, "rotation_fragile_rows": 0}
    result = {"schema": "arcpuzzles-shortcut-coverage-v1", "mode": "passive_rescore",
              "task_id": report.get("task_id"), "summary": summary, "lessons": [], "per_shortcut": {}}
    for row in rows:
        record = {key: row.get(key) for key in ("band", "index", "seed", "sample_index", "instance_sha256")}
        result["lessons"].append(record)
        try:
            instance = row.get("instance")
            if not isinstance(instance, dict):
                raise CoverageError("Lesson was not materialized")
            if json_hash(instance) != row.get("instance_sha256"):
                raise CoverageError("Saved instance hash mismatch")
            demos, queries = instance.get("train"), instance.get("test")
            if not isinstance(demos, list) or not demos or not isinstance(queries, list) or len(queries) != 1:
                raise CoverageError("A complete window needs demonstrations and exactly one labelled query")
            if len(demos) != report.get("sampler", {}).get("n_demos", len(demos)):
                raise CoverageError("Demonstration count differs from the saved sampler")
            if row.get("errors"):
                raise CoverageError(f"Saved lesson has errors: {row['errors']}")
            sampling = instance.get("sampling", {})
            if "accepted_pairs" in sampling:
                accepted = sampling["accepted_pairs"]
                expected = {("train", i): pair for i, pair in enumerate(demos)}
                expected[("test", 0)] = queries[0]
                seen = set()
                for item in accepted:
                    key = (item["split"], item["pair_index"])
                    if key in seen or key not in expected or json_hash(expected[key]["input"]) != item["input_sha256"]:
                        raise CoverageError("Accepted input binding mismatch")
                    seen.add(key)
                if seen != set(expected):
                    raise CoverageError("Incomplete accepted input bindings")
            record.update(score_window(demos, queries[0], shortcuts))
            record["complete"] = True
            summary["complete_lessons"] += 1
        except (CoverageError, KeyError, TypeError) as error:
            record.update({"complete": False, "error": str(error)})
            summary["incomplete_lessons"] += 1
            continue
        for name, metric in record["shortcuts"].items():
            metric["saved_outcome"] = row.get("rivals", {}).get(name)
            mismatch = metric["saved_outcome"] is not None and metric["saved_outcome"] != metric["recomputed_outcome"]
            metric["saved_outcome_consistent"] = not mismatch
            summary["saved_outcome_mismatches"] += int(mismatch)
            summary["scoring_error_rows"] += bool(metric["errors"])
            summary["unrefuted_demo_rows"] += metric["teaching_covered"] is False
            summary["rotation_fragile_rows"] += metric["rotation_robust"] is False
    for name in names:
        metrics = [row["shortcuts"][name] for row in result["lessons"] if row.get("complete")]
        known = [metric for metric in metrics if not metric["errors"]]
        result["per_shortcut"][name] = {
            "scored_lessons": len(known),
            "minimum_demo_refutations": min((m["demo_refutations"] for m in known), default=None),
            "minimum_window_refutations": min((m["window_refutations"] for m in known), default=None),
            "unrefuted_demo_lessons": sum(m["teaching_covered"] is False for m in metrics),
            "rotation_fragile_lessons": sum(m["rotation_robust"] is False for m in metrics),
        }
    incomplete = any(summary[key] for key in ("incomplete_lessons", "scoring_error_rows", "saved_outcome_mismatches"))
    if incomplete or not summary["complete_lessons"] or report.get("errors"):
        result["status"] = "incomplete_evidence"
    elif not names:
        result["status"] = "no_canonical_shortcuts"
    elif summary["unrefuted_demo_rows"] or summary["rotation_fragile_rows"]:
        result["status"] = "coverage_gaps"
    else:
        result["status"] = "coverage_complete"
    result["scope"] = "Counts saved labelled pairs for declared canonical shortcuts only; no new generation or Racket execution."
    return result


def load_bound_shortcuts(report, root, archived_source=None):
    root = Path(root).resolve()
    task = report.get("task_id")
    if not isinstance(task, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]*", task):
        raise CoverageError("Invalid exact task ID")
    manifest = report.get("runtime_manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise CoverageError("Saved runtime manifest is required for source-bound rescoring")
    raw_manifest = (json.dumps(manifest, indent=2) + "\n").encode()
    if hashlib.sha256(raw_manifest).hexdigest() != report.get("runtime_manifest_sha256"):
        raise CoverageError("Saved runtime manifest hash mismatch")
    staged = (root / "RUNTIME_MANIFEST.json").is_file()
    generator_library_path = f"generators/{task}/generator.py"
    source, dependency_root = None, root if staged else root / "shared/runtime"
    verified = []
    for entry in manifest["files"]:
        relative = Path(entry["runtime_path"] if staged else entry["library_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise CoverageError(f"Unsafe saved manifest path: {relative}")
        path = root / relative
        if entry["library_path"] == generator_library_path:
            if source is not None:
                raise CoverageError("Ambiguous generator source selection in saved manifest")
            source = Path(archived_source).resolve() if archived_source else path.resolve()
            path = source
            if entry["sha256"] != report.get("generator_sha256"):
                raise CoverageError("Generator binding differs between census and runtime manifest")
        elif not path.resolve().is_relative_to(root):
            raise CoverageError(f"Saved source path escapes root: {path}")
        require_file_hash(path, entry["sha256"], entry["library_path"])
        verified.append(str(path.resolve()))
    if source is None:
        raise CoverageError("Saved manifest does not bind the task generator")
    helper_path = dependency_root / "reviewer_support.py"
    if str(helper_path.resolve()) not in verified:
        raise CoverageError("Public reviewer_support helper is not source-bound by the saved manifest")
    helper_spec = importlib.util.spec_from_file_location("_shortcut_coverage_reviewer_support", helper_path)
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    if not archived_source:
        module, selected_path, digest = helper.load_selected_generator(task, root=root)
        if selected_path.resolve() != source or digest != report["generator_sha256"]:
            raise CoverageError("Selected generator changed while loading")
        source_mode = "current_selected_via_reviewer_support"
    else:
        # Compile the exact validated archive bytes; no timestamp-based pyc
        # reuse, source substitution, or fake portable selection is involved.
        helper.find_root(root)
        body = source.read_bytes()
        if hashlib.sha256(body).hexdigest() != report["generator_sha256"]:
            raise CoverageError("Archived generator changed while loading")
        name = "_shortcut_coverage_archive_" + report["generator_sha256"]
        module = types.ModuleType(name)
        module.__file__ = str(source)
        sys.modules[name] = module
        previous_path = list(sys.path)
        try:
            sys.path.insert(0, str(dependency_root))
            exec(compile(body, str(source), "exec"), module.__dict__)
        finally:
            sys.path[:] = previous_path
        source_mode = "explicit_exact_archived_bytes"
    if getattr(module, "RULE_HASH", None) != report.get("declared_rule_hash"):
        raise CoverageError("Declared rule hash differs between loaded source and census")
    declarations = getattr(module, "CANONICAL_SHORTCUTS", {})
    if not isinstance(declarations, dict) or any(not isinstance(name, str) or not callable(fn) for name, fn in declarations.items()):
        raise CoverageError("Invalid source CANONICAL_SHORTCUTS declaration")
    shortcuts = {PREFIX + name: fn for name, fn in declarations.items()}
    if set(shortcuts) != set(discover_shortcuts(report)):
        raise CoverageError("Canonical shortcut inventory mismatch between exact source and census")
    return shortcuts, {"source_mode": source_mode, "generator_path": str(source),
                       "generator_sha256": report["generator_sha256"],
                       "runtime_manifest_sha256": report["runtime_manifest_sha256"],
                       "manifest_files_verified": len(verified),
                       "rule_source_sha256_from_census": report.get("rule_source_sha256"),
                       "rule_callable_sha256_from_census": report.get("rule_callable_sha256"),
                       "declared_rule_hash": report.get("declared_rule_hash")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("census", type=Path, help="Public lesson-census JSON or JSON.gz")
    parser.add_argument("--root", required=True, type=Path, help="Exact library or portable runtime root")
    parser.add_argument("--generator", type=Path, help="Explicit archived generator whose bytes exactly match the saved report")
    parser.add_argument("--out", type=Path, help="New output JSON path; omitted means stdout")
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        report = read_census(args.census)
        shortcuts, binding = load_bound_shortcuts(report, args.root, args.generator)
        result = analyze_census(report, shortcuts)
        require_file_hash(binding["generator_path"], binding["generator_sha256"], "generator after rescoring")
        result.update({"source_binding": binding, "census_path": str(args.census.resolve()),
                       "census_file_sha256": file_hash(args.census)})
        code = 2 if result["status"] == "incomplete_evidence" else 1 if result["status"] == "coverage_gaps" else 0
    except Exception as error:
        result = {"schema": "arcpuzzles-shortcut-coverage-v1", "status": "blocked",
                  "error": f"{type(error).__name__}: {error}", "census_path": str(args.census.resolve())}
        code = 2
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        with args.out.open("x") as stream:
            stream.write(text)
        print(json.dumps({"status": result["status"], "summary": result.get("summary"),
                          "error": result.get("error"), "output": str(args.out)}))
    else:
        print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
