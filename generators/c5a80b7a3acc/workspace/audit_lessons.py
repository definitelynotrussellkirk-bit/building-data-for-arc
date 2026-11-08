#!/usr/bin/env python3
"""Audit saved Racket-labeled lessons, including every cyclic query choice.

Authoring-only: verifies claimed canonical shortcuts against canonical pairs.
No new labels, reference execution, or private runner imports. Exit 1 means
ambiguity/error/missing witness; survived_all is reported separately.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "c5a80b7a3acc"
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_generator(root):
    source = root / "generators" / TASK / "generator.py"
    if not source.exists():
        source = root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("lesson_audit_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen, source


def features(pair):
    grid, output = pair["input"], pair["output"]
    cells = [{(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
             for color in (2, 3)]
    tops = [min(r for r, c in shape) for shape in cells]
    lefts = [min(c for r, c in shape) for shape in cells]
    compare = lambda a, b: "less" if a < b else "greater" if a > b else "equal"
    positions = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    mode = "AND" if positions else "XOR"
    values = {"source_size_order": compare(len(cells[0]), len(cells[1])),
              "source_top_order": compare(*tops), "source_left_order": compare(*lefts),
              "empty_answer": str(output == [[0]]),
              "input_dimensions": f"{len(grid)}x{len(grid[0])}",
              "marker_palette": "7+9" if positions and any(9 in row for row in grid) else
                                "7" if positions else "9" if any(9 in row for row in grid) else "none",
              "seven_position": "absent" if not positions else "top_left" if (0, 0) in positions else
                                "top_row" if any(r == 0 for r, c in positions) else "other_row"}
    if mode == "XOR":
        values["answer_cell_parity"] = "odd" if sum(v == 8 for row in output for v in row) % 2 else "even"
    return mode, values


def analyze(path):
    root = find_root(__file__)
    gen, source = load_generator(root)
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("schema") != "arcpuzzles-lesson-census-v1" or data.get("task_id") != TASK:
        raise ValueError("Wrong census schema or task")
    if data.get("generator_sha256") != sha(source):
        raise ValueError("Census generator hash differs from live selected source")
    if data.get("status") != "no_declared_ambiguity" or data.get("errors"):
        raise ValueError("Expected complete error-free no_declared_ambiguity census")
    sampler = data["sampler"]
    if (gen.EXAMPLES_NEEDED, sampler["n_demos"], sampler["n_queries"], sampler["period"]) != (5, 5, 1, 3):
        raise ValueError("Expected EXAMPLES_NEEDED=5, five demos, one query, period 3")
    execution = data.get("execution", {})
    if execution.get("timed_out") or execution.get("exit_code", 0) != 0:
        raise ValueError("Interrupted census execution")
    rivals = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declared = getattr(gen, namespace)
        if not isinstance(declared, dict) or not declared:
            raise ValueError(f"{namespace}: expected nonempty mapping")
        for name, fn in declared.items():
            if not isinstance(name, str) or not callable(fn):
                raise ValueError(f"{namespace}: invalid declaration")
            rivals[f"{namespace}:{name}"] = fn
    if not set(rivals) <= set(data["rivals"]):
        raise ValueError("Census declaration inventory differs from live generator")
    ledger = canonical_path(root)
    records = [json.loads(line) for line in ledger.read_text().splitlines()
               if line.strip() and json.loads(line).get("task_id") == TASK]
    rule_hashes = {hashlib.sha256(row["program_solution"].encode()).hexdigest() for row in records}
    if data.get("rule_source_sha256") not in rule_hashes:
        raise ValueError("Census rule source does not match canonical authority")
    hashes = {"generator_sha256": sha(source), "canonical_ledger_sha256": sha(ledger),
              "rule_source_sha256": data["rule_source_sha256"],
              "rule_callable_sha256": data["rule_callable_sha256"],
              "census_sha256": hashlib.sha256(raw).hexdigest(), "audit_sha256": sha(__file__)}
    report = {"schema": "c5a80b7a3acc-cyclic-lesson-audit-v1", "task_id": TASK,
              "source_hashes": hashes, "canonical_fit": {}, "witnesses": {},
              "bands": {}, "failures": [], "survivals": [], "errors": [],
              "limits": ["Finite declared rivals only; no universal uniqueness claim.",
                         "Cyclic rotations reuse six existing Racket-labeled pairs.",
                         "Accepted indices recovered by input-only replay within the materializer's 30-attempt bound."]}
    canonical = canonical_pairs(TASK, root=root)
    for name, fn in rivals.items():
        fitted = [normalize_grid(fn(deepcopy(pair["input"]))) == pair["output"] for pair in canonical]
        report["canonical_fit"][name] = {"pairs": len(canonical), "fits": sum(fitted)}
        if name.startswith("CANONICAL_SHORTCUTS:") and not all(fitted):
            raise ValueError(f"Claimed shortcut {name} does not fit every canonical pair")
    unique = set()
    bands = sampler["bands"]
    if len(data["lessons"]) != len(bands) * sampler["per_band"]:
        raise ValueError("Partial census lesson count")
    for band in bands:
        rows = [row for row in data["lessons"] if row["band"] == band]
        if len(rows) != sampler["per_band"] or {r["index"] for r in rows} != set(range(len(rows))):
            raise ValueError(f"Incomplete/duplicate lesson indices for {band}")
        counts = {name: Counter() for name in rivals}
        distribution, band_unique = {}, set()
        for row in rows:
            if row.get("errors") or row.get("ambiguous") or "instance" not in row:
                raise ValueError(f"Unusable census lesson {band}:{row['index']}")
            instance = row["instance"]
            if digest(instance) != row["instance_sha256"]:
                raise ValueError("Materialized instance digest mismatch")
            if len(instance["train"]) != 5 or len(instance["test"]) != 1:
                raise ValueError("Wrong materialized lesson size")
            pairs = instance["train"] + instance["test"]
            accepted, next_index = [], instance["sample_index"]
            for pair in pairs:
                pair["input"] = normalize_grid(pair["input"])
                pair["output"] = normalize_grid(pair["output"])
                while next_index < instance["sample_index"] + 30:
                    trial_index = next_index
                    next_index += 1
                    if gen.generate(instance["seed"], trial_index, difficulty=band) == pair["input"]:
                        accepted.append(trial_index)
                        break
                else:
                    raise ValueError("Cannot recover exact generated pair sample index")
                key = digest(pair["input"])
                unique.add(key)
                band_unique.add(key)
                mode, values = features(pair)
                for category, value in values.items():
                    distribution.setdefault(mode, {}).setdefault(category, Counter())[value] += 1
            predictions = {}
            for name, fn in rivals.items():
                try:
                    predictions[name] = [normalize_grid(fn(deepcopy(p["input"]))) for p in pairs]
                except Exception as exc:
                    report["errors"].append({"band": band, "seed": instance["seed"],
                        "lesson_index": row["index"], "rival": name, "pairs": pairs,
                        "sample_indices": accepted, "error": f"{type(exc).__name__}: {exc}"})
                    counts[name]["error"] += 6
                    continue
                matches = [predicted == pair["output"] for predicted, pair in zip(predictions[name], pairs)]
                if name.startswith("CANONICAL_SHORTCUTS:") and name not in report["witnesses"] and not all(matches):
                    i = matches.index(False)
                    report["witnesses"][name] = {"band": band, "seed": instance["seed"],
                        "lesson_index": row["index"], "pair_position": i, "sample_index": accepted[i],
                        "input": pairs[i]["input"], "racket_output": pairs[i]["output"],
                        "rival_output": predictions[name][i], "source_hashes": hashes}
                for query in range(6):
                    demo_indices = [(query + offset) % 6 for offset in range(1, 6)]
                    status = "refuted" if not all(matches[i] for i in demo_indices) else (
                        "survived_all" if matches[query] else "ambiguous_query")
                    counts[name][status] += 1
                    if status != "refuted":
                        detail = {"band": band, "seed": instance["seed"], "lesson_index": row["index"],
                                  "rival": name, "status": status, "query_position": query,
                                  "query_sample_index": accepted[query], "demo_positions": demo_indices,
                                  "pairs": pairs, "sample_indices": accepted,
                                  "rival_outputs": predictions[name]}
                        report["failures" if status == "ambiguous_query" else "survivals"].append(detail)
        report["bands"][band] = {"lessons": len(rows), "cyclic_query_windows": 6 * len(rows),
            "pairs": 6 * len(rows), "unique_inputs": len(band_unique),
            "rivals": {name: {status: c[status] for status in ("refuted", "survived_all", "ambiguous_query", "error")}
                       for name, c in counts.items()}, "distribution": distribution}
    missing = set(gen.CANONICAL_SHORTCUTS) - {name.split(":", 1)[1] for name in report["witnesses"]}
    if missing:
        report["errors"].append(f"No generated Racket-backed witness for shortcuts: {sorted(missing)}")
    if sha(source) != hashes["generator_sha256"] or sha(ledger) != hashes["canonical_ledger_sha256"]:
        raise ValueError("Sources changed during analysis")
    report["unique_inputs"] = len(unique)
    report["passed"] = not report["failures"] and not report["errors"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output must be a new path (no clobber)")
    try:
        report = analyze(args.census)
    except Exception as exc:
        report = {"passed": False, "errors": [f"{type(exc).__name__}: {exc}"],
                  "claims": "No census conclusions: validation or analysis failed."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"passed": report["passed"], "errors": report["errors"],
                      "ambiguities": len(report.get("failures", [])),
                      "survivals": len(report.get("survivals", [])),
                      "unique_inputs": report.get("unique_inputs"), "output": str(args.out)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
