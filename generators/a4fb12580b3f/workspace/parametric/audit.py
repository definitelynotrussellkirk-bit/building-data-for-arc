"""Bounded, reproducible protected-Racket teaching audit for future reviewers.

Every rival executes successfully on every retained pair. Fit decisions use
demonstrations alone; only then are surviving predictions checked on queries.
The audit covers a declared finite rival set, never universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def assess_predictions(expected_train, expected_test, rival_train, rival_test):
    if (not expected_train or not expected_test or len(expected_train) != len(rival_train)
            or len(expected_test) != len(rival_test)):
        raise ValueError("Every rival must successfully predict every demonstration and query")
    matches = [a == b for a, b in zip(expected_train, rival_train)]
    disagreements = [i for i, (a, b) in enumerate(zip(expected_test, rival_test)) if a != b]
    survives = all(matches)
    return {"demo_matches": matches, "survives_demonstrations": survives,
            "query_disagreements": disagreements, "harmful_survivor": survives and bool(disagreements)}


def run(output, *, seeds=(0, 17), demo_counts=(2, 3, 6)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    home = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    spec = importlib.util.spec_from_file_location("_a4fb_audit_adapter", home / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    rules, prototype = adapter._rules, adapter._load("prototype.py")
    source_names = ("adapter.py", "rules.py", "prototype.py", "canonical.rkt", "audit.py")
    source_hashes = {name: hashlib.sha256((home / name).read_bytes()).hexdigest() for name in source_names}
    cache, wrapped, rows, witnesses = {}, {}, [], {}
    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("A live protected Racket backend is required")

    def execute(source, grid):
        key = (source, json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            if source not in wrapped:
                wrapped[source] = wrap_rule(source)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            cache[key] = bridge.eval_text(f"({wrapped[source]} {literal})")
            value = cache[key]
            if (type(value) is not list or len(value) != len(grid)
                    or any(type(row) is not list or len(row) != len(grid[0])
                           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in value)):
                raise ValueError("Rival returned an invalid typed grid; errors are not teaching evidence")
        return cache[key]

    try:
        for seed in seeds:
            for demos in demo_counts:
                for mode in rules.MODES:
                    episode = adapter.generate(seed, {"mode": mode}, demos, 4)
                    source = episode["program_solution"]
                    labels = {split: [execute(source, pair["input"]) for pair in episode[split]]
                              for split in ("train", "test")}
                    if any(labels[split] != [pair["output"] for pair in episode[split]] for split in labels):
                        raise ValueError("Python label claim differs from protected Racket")
                    rivals = {}
                    for name, rival in rules.rival_programs(mode).items():
                        predictions = {split: [execute(rival, pair["input"]) for pair in episode[split]]
                                       for split in ("train", "test")}
                        verdict = assess_predictions(labels["train"], labels["test"], predictions["train"], predictions["test"])
                        rivals[name] = verdict
                        witness_key = f"{mode}/{name}"
                        if witness_key not in witnesses and not verdict["survives_demonstrations"]:
                            index = verdict["demo_matches"].index(False)
                            witnesses[witness_key] = {"seed": seed, "demos": demos, "demo_index": index,
                                "settings": {"mode": mode}, "input": episode["train"][index]["input"],
                                "program": source, "output": labels["train"][index],
                                "rival_program": rival, "rival_output": predictions["train"][index]}
                        elif verdict["harmful_survivor"]:
                            index = verdict["query_disagreements"][0]
                            witnesses[witness_key] = {"seed": seed, "demos": demos,
                                "settings": {"mode": mode}, "finding": "demo-surviving query-disagreeing rival",
                                "train": episode["train"], "rival_train_outputs": predictions["train"],
                                "query_index": index, "input": episode["test"][index]["input"],
                                "program": source, "output": labels["test"][index],
                                "rival_program": rival, "rival_output": predictions["test"][index]}
                    rows.append({"seed": seed, "settings": {"mode": mode}, "demos": demos, "queries": 4,
                        "rivals": rivals, "input_metrics": {split: [prototype.analyze(pair["input"]) for pair in episode[split]]
                                                           for split in ("train", "test")}})
    finally:
        bridge.close()
    if source_hashes != {name: hashlib.sha256((home / name).read_bytes()).hexdigest() for name in source_names}:
        raise ValueError("Audited source changed during execution")
    harmful = [{"seed": row["seed"], "demos": row["demos"], "settings": row["settings"], "rival": name,
                "query_disagreements": value["query_disagreements"]}
               for row in rows for name, value in row["rivals"].items() if value["harmful_survivor"]]
    report = {"schema": "a4fb12580b3f-finite-teaching-audit-v1", "status": "passed" if not harmful else "failed",
        "source_sha256": source_hashes, "racket": {key: value for key, value in identity.items() if key.endswith("sha256") or key in ("schema", "backend", "protected")},
        "episodes": len(rows), "racket_evaluations": len(cache), "harmful_survivors": harmful, "checks": rows,
        "scope": "Declared rivals and retained seeds/counts only; no universal uniqueness or training admission.",
        "training_admitted": False}
    output.mkdir(parents=True)
    (output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "witnesses.json").write_text(json.dumps({"source_sha256": source_hashes, "cases": witnesses}, separators=(",", ":")) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--demos", action="append", type=int)
    args = parser.parse_args()
    report = run(args.out, seeds=args.seed or (0, 17), demo_counts=args.demos or (2, 3, 6))
    print(json.dumps({key: report[key] for key in ("status", "episodes", "racket_evaluations", "harmful_survivors")}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
