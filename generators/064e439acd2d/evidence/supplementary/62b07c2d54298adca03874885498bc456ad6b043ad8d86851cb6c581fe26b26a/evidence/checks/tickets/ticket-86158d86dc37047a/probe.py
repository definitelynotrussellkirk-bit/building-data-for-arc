"""One source-bound border-only shortcut probe; no peer safety certification."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


def main():
    started = time.monotonic()
    work = Path(__file__).resolve().parents[3]
    repo = work / "repo"
    sys.path.insert(0, str(repo / "shared/runtime"))
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    task = "064e439acd2d"
    tickets = json.loads((work / "AUDIT_ASSIGNMENT.json").read_text())["tickets"]
    ticket = next(t for t in tickets if t["ticket_id"] == "ticket-86158d86dc37047a")
    source = repo / "generators" / task / "generator.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == ticket["generator_sha256"], "source changed from assigned ticket"
    spec = importlib.util.spec_from_file_location("bounded_ticket_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    records = [json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").open()]
    records = [r for r in records if r.get("task_id") == task]
    programs = {r["program_solution"] for r in records}
    assert len(programs) == 1
    program = programs.pop()
    anchor = "(color (nth dot 2)))\n                       (cond"
    assert program.count(anchor) == 1
    rival = program.replace(anchor, anchor + "\n                         ((and (> r 0) (< r (- h 1)) (> c 0) (< c (- w 1))) acc)", 1)
    callables = {"canonical": strip_rule_wrapper(program), "border_only": strip_rule_wrapper(rival)}

    seed = int(ticket["seed"], 16)
    grid = generator.generate(seed, 0)
    domain_errors = generator.self_check(grid)
    assert domain_errors == [], domain_errors
    pairs = {}
    for record in records:
        for pair in record.get("train", []) + record.get("test", []):
            if "output" in pair:
                pairs[json.dumps(pair["input"], separators=(",", ":"))] = pair

    with RacketBridge(timeout=20.0) as bridge:
        def predict(name, value):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in value) + ")"
            return bridge.eval_text(f"({callables[name]} {literal})")

        canonical_checks = []
        for pair in pairs.values():
            expected = predict("canonical", pair["input"])
            shortcut = predict("border_only", pair["input"])
            canonical_checks.append({"canonical_label_matches": expected == pair["output"],
                                     "rival_fits": shortcut == expected})
        output = predict("canonical", grid)
        rival_output = predict("border_only", grid)
        assert all(c["canonical_label_matches"] for c in canonical_checks)
        assert output == generator._diagnostic_projection_prediction(grid)
        assert rival_output == generator.SEMANTIC_RIVALS["border_only"](grid)
        changed = [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                   if output[r][c] != rival_output[r][c]]
        assert changed, "assigned current draw failed to refute the rival"

    record = {
        "ticket_id": ticket["ticket_id"], "type": ticket["type"], "status": "completed",
        "consumer": ticket["consumer"], "generator_id": task,
        "generator_sha256": digest, "rule_hash": ticket["rule_hash"],
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
        "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "ticket_seed": ticket["seed"], "generate_seed": seed, "sample_index": 0,
        "targeted_probe_count": 1, "domain_errors": domain_errors,
        "canonical_pairs_checked": len(canonical_checks), "canonical_pair_results": canonical_checks,
        "input": grid, "racket_output": output, "racket_rival_output": rival_output,
        "different_cells": changed, "canonical_program": program, "rival_program": rival,
        "summary": "The border-only shortcut fits all retained canonical examples, but one lawful current rich draw refutes it through real Racket. This is a retained teaching witness, not a new safety finding.",
        "scope_limit": "One assigned seed/index and one rival. No corpus census, full peer battery, approval or training admission.",
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    (Path(__file__).parent / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("ticket_id", "status", "canonical_pairs_checked", "different_cells", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
