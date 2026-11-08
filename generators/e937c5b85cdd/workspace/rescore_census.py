"""Score retained Racket-labelled lessons against the current declared rivals.

No labels are regenerated. Input and live generator hashes are kept separate.
Run through run_with_racket.py to supply the package's Python import paths.
Only complete, error-free arcpuzzles-lesson-census-v1 evidence is accepted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import find_root


COMPLETE_STATUSES = {
    "no_ambiguity_found", "no_declared_ambiguity", "no_contract",
    "warning", "hook_only", "ambiguous",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def valid_grid(grid):
    return (isinstance(grid, list) and bool(grid)
            and isinstance(grid[0], list) and bool(grid[0])
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(value) is int and 0 <= value <= 9 for value in row)
                    for row in grid))


def validate_census(census):
    """Validate completion and retained bindings before scoring any rival."""
    require(isinstance(census, dict), "Expected a census object")
    require(census.get("schema") == "arcpuzzles-lesson-census-v1", "Unsupported census schema")
    task = census.get("task_id")
    require(isinstance(task, str) and task.isalnum(), "Expected an alphanumeric task id")
    for key in ("status", "production_status"):
        require(census.get(key) in COMPLETE_STATUSES, f"Retained census {key} is incomplete or errored")
    require(census.get("rotation_status") in COMPLETE_STATUSES | {"not_requested"},
            "Retained rotation census is incomplete or errored")
    require(census.get("errors") == [], "Retained census contains errors")
    execution = census["execution"]
    expected_exit = 1 if census["status"] == "ambiguous" else 0
    require(execution.get("timed_out") is False
            and type(execution.get("exit_code")) is int
            and execution["exit_code"] == expected_exit, "Retained census execution did not complete")
    lessons, summary = census["lessons"], census["summary"]
    require(isinstance(lessons, list) and bool(lessons), "Retained census has no lessons")
    require(type(summary.get("requested")) is int and summary["requested"] > 0
            and summary["requested"] == summary.get("materialized") == len(lessons),
            "Retained census is partial or has inconsistent lesson counts")
    for key in ("materialization_errors", "scoring_errors", "rotation_scoring_errors"):
        require(summary.get(key) == 0, f"Retained census reports {key}")
    manifest = census["runtime_manifest"]
    manifest_hash = hashlib.sha256((json.dumps(manifest, indent=2) + "\n").encode()).hexdigest()
    require(manifest_hash == census["runtime_manifest_sha256"], "Runtime manifest hash mismatch")
    require(manifest.get("task_id") == task, "Runtime manifest task mismatch")
    entries = [row for row in manifest["files"]
               if row.get("library_path") == f"generators/{task}/generator.py"]
    require(len(entries) == 1 and entries[0].get("sha256") == census["generator_sha256"],
            "Input generator hash is not bound to its runtime manifest")
    pair_count = rotation_count = 0
    per_band, identities = Counter(), set()
    for lesson in lessons:
        require(lesson.get("errors") == [], "Retained lesson contains scoring errors")
        identity = (lesson["band"], lesson["index"])
        require(identity not in identities, "Duplicate retained lesson identity")
        identities.add(identity)
        per_band[lesson["band"]] += 1
        instance = lesson["instance"]
        require(instance.get("task_id") == task
                and instance.get("rule_task_id") == census["rule_task_id"]
                and instance.get("rule_file") == census["rule_file"], "Retained lesson rule binding mismatch")
        train, tests = instance["train"], instance["test"]
        tests = tests if isinstance(tests, list) else [tests]
        require(isinstance(train, list) and bool(train) and len(tests) == 1,
                "Expected nonempty demonstrations and exactly one query")
        for pair in [*train, *tests]:
            require(isinstance(pair, dict) and valid_grid(pair.get("input"))
                    and valid_grid(pair.get("output")), "Missing or malformed retained input/reference output")
        instance_hash = hashlib.sha256(json.dumps(instance, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(instance_hash == lesson["instance_sha256"], "Retained instance hash mismatch")
        rotations = lesson.get("rotations", [])
        require(isinstance(rotations, list)
                and all(row.get("errors") == [] for row in rotations), "Retained rotation contains errors")
        pair_count += len(train) + 1
        rotation_count += len(rotations)
    require(summary.get("pairs") == pair_count and summary.get("rotations") == rotation_count,
            "Retained pair or rotation counts disagree with materialized evidence")
    require(set(census["per_band"]) == set(per_band), "Retained band coverage is inconsistent")
    for band, count in per_band.items():
        require(census["per_band"][band].get("requested")
                == census["per_band"][band].get("materialized") == count,
                f"Retained {band} census is partial")
    return task


def source_unchanged(source, source_hash):
    require(hashlib.sha256(source.read_bytes()).hexdigest() == source_hash,
            "Live rival source changed while rescoring")


def load_rivals(root, task, rule_hash):
    source = root / "generators" / task / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / task / "generator.py"
    raw_source = source.read_bytes()
    source_hash = hashlib.sha256(raw_source).hexdigest()
    spec = importlib.util.spec_from_file_location("live_census_rivals", source)
    gen = importlib.util.module_from_spec(spec)
    # Compile the exact bytes whose hash is reported; bypass stale bytecode.
    exec(compile(raw_source, str(source), "exec"), gen.__dict__)
    require(gen.TASK_ID == task and gen.RULE_HASH == rule_hash,
            "Retained labels and live rivals refer to different tasks or rules")
    rivals, namespaces = {}, {}
    for namespace in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        values = getattr(gen, namespace, {})
        require(isinstance(values, dict), f"{namespace} must map names to callables")
        namespaces[namespace] = list(values)
        for name, rival in values.items():
            require(isinstance(name, str) and bool(name) and callable(rival), "Malformed rival declaration")
            require(name not in rivals or rivals[name] is rival,
                    f"Conflicting rival implementations share name {name}")
            rivals[name] = rival
    require(bool(rivals), "No rivals declared; not a rival pass")
    source_unchanged(source, source_hash)
    return source, source_hash, rivals, namespaces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new path")
    report = {
        "schema": "retained-census-rescore-v1", "census_path": str(args.census),
        "new_reference_executions": 0,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "limits": "Complete retained authoring evidence only; bindings and grid structure are checked, but labels are not independently re-executed. Only declared rivals; no universal identification claim.",
    }
    totals, by_band, findings, errors = Counter(), {}, [], []
    try:
        raw = args.census.read_bytes()
        report["census_sha256"] = hashlib.sha256(raw).hexdigest()
        census = json.loads(raw)
        task = validate_census(census)
        source, source_hash, rivals, namespaces = load_rivals(find_root(__file__), task, census["declared_rule_hash"])
        report.update(task_id=task, input_census_status=census["status"],
                      input_generator_sha256=census["generator_sha256"],
                      live_rivals_generator_sha256=source_hash,
                      rule_hash=census["declared_rule_hash"], declarations=namespaces,
                      retained_runtime_manifest_sha256=census["runtime_manifest_sha256"],
                      retained_rule_source_sha256=census["rule_source_sha256"],
                      retained_rule_callable_sha256=census["rule_callable_sha256"])
        for lesson in census["lessons"]:
            band = lesson["band"]
            counts = by_band.setdefault(band, Counter())
            instance = lesson["instance"]
            tests = instance["test"]
            tests = tests if isinstance(tests, list) else [tests]
            n = len(instance["train"])
            pairs = [*instance["train"], *tests]
            totals["lessons"] += 1
            counts["lessons"] += 1
            for name, rival in rivals.items():
                try:
                    predictions = [rival(deepcopy(p["input"])) for p in pairs]
                    require(all(valid_grid(value) for value in predictions), "Rival returned a malformed grid")
                    fits = [value == pair["output"] for value, pair in zip(predictions, pairs)]
                except Exception as exc:
                    errors.append({"band": band, "index": lesson["index"], "rival": name,
                                   "error": f"{type(exc).__name__}: {exc}"})
                    continue
                production = all(fits[:n]) and not fits[n]
                rotated = [q for q in range(len(pairs))
                           if not fits[q] and all(fits[j] for j in range(len(pairs)) if j != q)]
                for destination in (totals, counts):
                    destination[name + ":production_ambiguous"] += int(production)
                    destination[name + ":ambiguous_rotations"] += len(rotated)
                    destination[name + ":survived_all"] += int(all(fits))
                if production or rotated:
                    findings.append({"band": band, "index": lesson["index"], "seed": lesson["seed"],
                                     "sample_index": lesson["sample_index"],
                                     "instance_sha256": lesson["instance_sha256"], "rival": name,
                                     "fits_in_train_then_test_order": fits,
                                     "production_ambiguous": production, "ambiguous_query_positions": rotated})
        source_unchanged(source, source_hash)
        report["live_source_stable"] = True
    except Exception as exc:
        errors.append({"error": f"{type(exc).__name__}: {exc}"})
    report.update({
        "summary": dict(totals), "per_band": {b: dict(c) for b, c in by_band.items()},
        "findings": findings, "errors": errors,
        "status": "error" if errors else "ambiguity_found" if findings else "no_ambiguity_found",
    })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "summary": report["summary"]}))
    return 2 if errors else 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
