#!/usr/bin/env python3
"""Small source-bound column-rule probe with actual Racket labels.

From any cwd: PYTHONPATH=/path/to/repo/shared/runtime RACKET_PATH=/path/to/racket
  python /path/to/task/workspace/probe_column_rules.py --out /new/report.json
The packet run_with_racket.py wrapper is also supported. No private scripts or
previous packet imports are used. Defaults: 8 individual draws per difficulty,
3 canonical pairs, 5 saved hand cases, and one fixed ambiguity lesson. This is
finite rival evidence; shared lesson-census owns production/rotation sampling.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
import types

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "49898d244b5f"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def _fill_columns(grid, predicate):
    output = [[0] * len(grid[0]) for _ in grid]
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c] != 0]
        if predicate(values):
            for row in output:
                row[c] = values[0]
    return output


def monochromatic_columns(grid):
    return _fill_columns(grid, lambda values: bool(values) and len(set(values)) == 1)


def nonempty_columns(grid):
    return _fill_columns(grid, bool)


def preserve_distractors(grid):
    filled = _fill_columns(grid, lambda values: len(values) == 1)
    return [[filled[r][c] or grid[r][c] for c in range(len(grid[0]))] for r in range(len(grid))]


def seeded_rows(grid):
    return [[next(value for value in row if value != 0)] * len(row)
            if sum(value != 0 for value in row) == 1 else [0] * len(row) for row in grid]


def identity(grid):
    return deepcopy(grid)


INDEPENDENT_RIVALS = {"monochromatic_columns": monochromatic_columns,
                      "nonempty_columns": nonempty_columns,
                      "preserve_distractors": preserve_distractors,
                      "seeded_rows": seeded_rows, "identity": identity}


def score(rivals, pairs):
    result = {}
    for name, rival in rivals.items():
        row = {"canonical_matches": 0, "canonical_total": 0, "hand_disagrees": 0,
               "generated": {band: {"matches": 0, "disagrees": 0} for band in ("easy", "medium", "hard")},
               "errors": [], "first_disagreement": None}
        for pair in pairs:
            if pair["kind"] == "canonical":
                row["canonical_total"] += 1
            try:
                supplied = deepcopy(pair["input"])
                prediction = rival(supplied)
                if supplied != pair["input"]:
                    raise ValueError("rival mutated its input")
                matches = prediction == pair["racket_output"]
                if pair["kind"] == "canonical":
                    row["canonical_matches"] += int(matches)
                elif pair["kind"] == "hand":
                    row["hand_disagrees"] += int(not matches)
                else:
                    row["generated"][pair["difficulty"]]["matches" if matches else "disagrees"] += 1
                if not matches and row["first_disagreement"] is None:
                    row["first_disagreement"] = {"identity": pair["identity"], "kind": pair["kind"],
                                                "input": pair["input"], "racket_output": pair["racket_output"],
                                                "prediction": prediction}
            except Exception as exc:
                row["errors"].append({"identity": pair["identity"], "error": f"{type(exc).__name__}: {exc}"})
        row["fits_all_canonical"] = row["canonical_matches"] == row["canonical_total"] and not row["errors"]
        result[name] = row
    return result


def run(generator, data_path, seeds, require_contract):
    home = Path(__file__).resolve().parent.parent
    root = find_root(home)
    ledger = canonical_path(root)
    with ledger.open() as handle:
        source = next(row["program_solution"] for line in handle
                      if (row := json.loads(line)).get("task_id") == TASK)
    body = strip_rule_wrapper(strip_line_comments(source))
    rule_hash = digest(" ".join(source.split()).encode())[:12]
    data_bytes, source_bytes = data_path.read_bytes(), generator.read_bytes()
    data = json.loads(data_bytes)
    module = types.ModuleType("column_probe_subject")
    module.__file__ = str(generator)
    exec(compile(source_bytes, str(generator), "exec"), module.__dict__)
    errors = []
    if data["rule_hash"] != rule_hash:
        errors.append("counterexample data rule hash disagrees with selected canonical source")
    subjects = []
    for pair in canonical_pairs(TASK, root=root):
        subjects.append({"kind": "canonical", "identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
                         "input": pair["input"], "stored_output": pair["output"]})
    for case in data["cases"]:
        subjects.append({"kind": "hand", "identity": case["name"], "input": case["input"],
                         "stored_output": case["output"], "positive_generator_domain": case["positive_generator_domain"]})
    for band in ("easy", "medium", "hard"):
        for i in range(seeds):
            try:
                grid = module.generate(i, i, difficulty=band)
                subjects.append({"kind": "generated", "identity": {"seed": i, "sample_index": i, "difficulty": band},
                                 "difficulty": band, "input": grid})
            except Exception as exc:
                errors.append(f"generate({i},{i},difficulty={band}): {type(exc).__name__}: {exc}")
    bridge = RacketBridge()
    labeled = []
    try:
        for pair in subjects:
            try:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                actual = bridge.eval_text(f"(let ([g {literal}]) {body})")
                row = {**pair, "input_sha256": grid_hash(pair["input"]), "racket_output": actual,
                       "racket_output_sha256": grid_hash(actual)}
                if "stored_output" in pair:
                    row["matches_stored_output"] = actual == pair["stored_output"]
                    if not row["matches_stored_output"]:
                        errors.append(f"stored label mismatch: {pair['identity']}")
                row["self_check"] = module.self_check(deepcopy(pair["input"]))
                if (pair["kind"] == "generated" or pair.get("positive_generator_domain", False)) and row["self_check"]:
                    errors.append(f"positive-domain checker rejection: {pair['identity']}")
                mirror = getattr(module, "expected_output", None)
                if callable(mirror):
                    row["mirror_matches_racket"] = mirror(deepcopy(pair["input"])) == actual
                    if not row["mirror_matches_racket"]:
                        errors.append(f"mirror mismatch: {pair['identity']}")
                labeled.append(row)
            except Exception as exc:
                errors.append(f"label/inspect {pair['identity']}: {type(exc).__name__}: {exc}")
    finally:
        bridge.shutdown()
    namespaces = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        declared = getattr(module, namespace, None)
        if declared is None:
            namespaces[namespace] = {"status": "missing", "rivals": {}}
            if require_contract:
                errors.append(f"required {namespace} is missing")
            continue
        if not isinstance(declared, dict) or any(not isinstance(n, str) or not callable(f) for n, f in declared.items()):
            namespaces[namespace] = {"status": "invalid", "rivals": {}}
            errors.append(f"invalid {namespace}")
            continue
        scored = score(declared, labeled)
        namespaces[namespace] = {"status": "scored", "rivals": scored}
        for name, row in scored.items():
            if row["errors"]:
                errors.append(f"{namespace}.{name} prediction errors")
            if namespace == "CANONICAL_SHORTCUTS" and not row["fits_all_canonical"]:
                errors.append(f"claimed canonical shortcut {name} does not fit all authoritative pairs")
    demos = [{"input": p["input"], "output": p["racket_output"]} for p in labeled
             if p["kind"] == "canonical" and p["identity"]["split"] == "train"]
    query = next(p for p in labeled if p["kind"] == "hand" and p["identity"] == data["lesson"]["query_case"])
    query = {"input": query["input"], "output": query["racket_output"]}
    guard = getattr(module, "lesson_identifiable", None)
    lesson = {"label_source": "actual Racket", "demonstrations": demos, "query": query,
              "strong_rival_fits_demos": all(monochromatic_columns(p["input"]) == p["output"] for p in demos),
              "strong_rival_changes_query": monochromatic_columns(query["input"]) != query["output"],
              "guard_status": "missing"}
    if callable(guard):
        lesson["guard_status"] = "scored"
        lesson["guard_reasons"] = guard(deepcopy(demos), deepcopy(query))
        lesson["repaired_demo_reasons"] = guard([deepcopy(demos[0]), deepcopy(query)], deepcopy(query))
        if not any("monochromatic_columns" in reason for reason in lesson["guard_reasons"]):
            errors.append("lesson guard misses monochromatic-columns ambiguity")
        if lesson["repaired_demo_reasons"]:
            errors.append("lesson guard rejects already demonstrated distinction")
    elif require_contract:
        errors.append("required lesson guard is missing")
    tool = Path(__file__).resolve()
    env = {key: os.environ[key] for key in ("TMPDIR", "PYTHONPATH", "RACKET_PATH") if key in os.environ}
    command = " ".join([*(f"{key}={shlex.quote(value)}" for key, value in env.items()), shlex.join([sys.executable, *sys.argv])])
    return {"schema": "49898d244b5f-column-rule-probe-v1", "task_id": TASK,
            "status": "failed" if errors else "passed", "errors": errors, "executed_command": command,
            "cwd": str(Path.cwd()), "generator_path": str(generator), "generator_sha256": digest(source_bytes),
            "tool_sha256": digest(tool.read_bytes()), "data_sha256": digest(data_bytes),
            "executed_rule_hash": rule_hash, "rule_source_sha256": digest(source.encode()),
            "canonical_ledger_sha256": digest(ledger.read_bytes()), "pairs": labeled,
            "pair_counts": {kind: sum(p["kind"] == kind for p in labeled) for kind in ("canonical", "hand", "generated")},
            "independent_rivals": {"source": "five independent implementations in this tool", "rivals": score(INDEPENDENT_RIVALS, labeled)},
            "declared_contract": namespaces, "lesson": lesson,
            "scope": "Small fixed canonical/hand replay and bounded individual draws with actual Racket labels. Missing declarations remain missing. Not production lesson materialization, exhaustive rotation coverage, training admission or approval."}


def main():
    home = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=home / "generator.py")
    parser.add_argument("--data", type=Path, default=home / "counterexamples/column_semantics.json")
    parser.add_argument("--out", required=True, type=Path, help="new report JSON; existing files refused")
    parser.add_argument("--seeds", type=int, default=8, help="individual draws per band, bounded1..30")
    parser.add_argument("--require-contract", action="store_true", help="fail rather than record absent declarations/guard")
    args = parser.parse_args()
    if not 1 <= args.seeds <= 30:
        parser.error("--seeds must be1..30")
    if args.out.exists():
        parser.error("--out must name a new file")
    report = run(args.generator.resolve(), args.data.resolve(), args.seeds, args.require_contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "executed_rule_hash", "pair_counts", "errors")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
