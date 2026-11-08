"""One bounded allocation probe: three pinned records, seven draws each."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import signal
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge


TICKET = "ticket-3aa94d93c00948cd"
SEED = "90d58f7e07b543d2023381b52fe46c7b8490297ef815078f8ee2fa868fb24ccb"
ANCHOR = "6b88648ff0e0"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
OUT = Path(__file__).with_name("probe_result.json")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def signature(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def timeout_handler(signum, frame):
    raise TimeoutError("single targeted probe reached its 115-second internal limit")


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(115)
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
    assignment = json.loads((WORK / "AUDIT_ASSIGNMENT.json").read_text())
    ticket = next(row for row in assignment["tickets"] if row["ticket_id"] == TICKET)
    assert ticket["seed"] == SEED and ticket["task_id"] == ANCHOR
    ids = [ANCHOR] + random.Random(int(SEED, 16)).sample(
        sorted(set(manifest["all_ids"]) - {ANCHOR}), 2)
    assert ids == ["6b88648ff0e0", "1a259ef9a7e7", "424c822d69f3"]
    catalog = {row["id"]: row for row in map(json.loads, (REPO / "catalog/puzzles.jsonl").open())
               if row["id"] in ids}
    canonical = {task_id: [] for task_id in ids}
    for row in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").open()):
        if row.get("task_id") in ids:
            canonical[row["task_id"]].append(row)
    priority = manifest["parametric_priority"]
    focus = manifest["main_draw_policy"]["evaluation_focus"]
    result = {
        "ticket_id": TICKET, "seed": SEED, "selected_ids": ids,
        "sampling_method": "pinned anchor plus Random(int(seed,16)).sample(sorted(all_ids minus anchor),2); no reroll",
        "command": "python3 run_with_racket.py python3 ../checks/tickets/ticket-3aa94d93c00948cd/allocation_probe.py",
        "cwd": "WORK", "probe_limit_seconds": 120,
        "input_seed": int(SEED[:8], 16), "sample_indices": list(range(7)),
        "manifest_sha256": digest((WORK / "PACKET-MANIFEST.json").read_bytes()),
        "assignment_sha256": digest((WORK / "AUDIT_ASSIGNMENT.json").read_bytes()),
        "catalog_sha256": digest((REPO / "catalog/puzzles.jsonl").read_bytes()),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "packet": {
            "included_records": len(manifest["all_ids"]),
            "main_ids": len(manifest["main_ids"]),
            "normal_ids": len(manifest["main_draw_policy"]["normal_ids"]),
            "selection_policy": manifest["selection"]["policy"],
            "selection_quotas": manifest["selection"]["quotas"],
            "owner_generator_count": manifest["selection"]["owner_generator_count"],
            "priority_counts": priority["counts"],
            "selected_tier": priority["selected_tier"],
            "covered_original_tasks": priority["covered_original_tasks"],
            "provided_tasks": priority["provided_tasks"],
            "evaluation_focus": {k: v for k, v in focus.items() if k != "anchors"},
            "evaluation_anchor_count": len(focus["anchors"]),
        },
        "records": [], "status": "running",
    }
    bridge = None
    try:
        start_bridge = time.monotonic()
        bridge = RacketBridge(timeout=10, startup_timeout=30)
        result["racket_startup_seconds"] = time.monotonic() - start_bridge
        for task_id in ids:
            info = manifest["generators"][task_id]
            home = REPO / "generators" / task_id
            source = home / "generator.py"
            source_hash = digest(source.read_bytes())
            assert source_hash == info["generator_sha256"]
            spec = importlib.util.spec_from_file_location("allocation_" + task_id, source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            matches = [row for row in canonical[task_id]
                       if digest(" ".join(row["program_solution"].split()).encode())[:12] == info["rule_hash"]]
            assert matches, "No matching canonical rule"
            program = matches[0]["program_solution"]
            start_draw = time.monotonic()
            inputs = [module.generate(result["input_seed"], index) for index in range(7)]
            draw_seconds = time.monotonic() - start_draw
            checks = [module.self_check(grid) for grid in inputs]
            start_labels = time.monotonic()
            bridge.eval_text(f"(define allocation-rule (let ((rule! (lambda (fn) fn))) {program}))")
            bridge.define_value("allocation-inputs", inputs)
            outputs = bridge.eval_text("(map allocation-rule allocation-inputs)")
            label_seconds = time.monotonic() - start_labels
            assert len(outputs) == 7
            mirror = getattr(module, "rule_mirror", getattr(module, "_intended", None))
            parity = [mirror(value) == output for value, output in zip(inputs, outputs)] if mirror else None
            demos = [{"input": value, "output": output} for value, output in zip(inputs[:3], outputs[:3])]
            rivals = getattr(module, "LESSON_COMPETITORS", {})
            eliminated = {
                name: [i for i, pair in enumerate(demos) if solver(pair["input"]) != pair["output"]]
                for name, solver in rivals.items()
            }
            evidence = {}
            for relative in ("notes.md", "evidence/associated_notes.jsonl", "evidence/review_index.json"):
                path = home / relative
                if path.exists():
                    evidence[str(path.relative_to(WORK))] = digest(path.read_bytes())
            cat = catalog[task_id]
            result["records"].append({
                "task_id": task_id, "generator_sha256": source_hash,
                "rule_hash": info["rule_hash"], "program_sha256": digest(program.encode()),
                "canonical_matching_rows": len(matches),
                "catalog": {key: cat.get(key) for key in ("summary", "sources", "mix_weight", "train_safety", "review_status", "approval_verification_status")},
                "lineage_and_prototype": priority["related_generators"].get(task_id),
                "in_normal_authoring_pool": task_id in manifest["main_draw_policy"]["normal_ids"],
                "parametric_directory_present": (home / "workspace/parametric").exists(),
                "generation_seconds": draw_seconds, "racket_label_seconds": label_seconds,
                "generated_count": len(inputs), "distinct_inputs": len(set(map(signature, inputs))),
                "distinct_outputs": len(set(map(signature, outputs))),
                "total_input_cells": sum(sum(map(len, value)) for value in inputs),
                "total_output_cells": sum(sum(map(len, value)) for value in outputs),
                "self_check_errors": checks, "racket_mirror_agreement": parity,
                "input_sha256": list(map(signature, inputs)), "output_sha256": list(map(signature, outputs)),
                "declared_rivals_eliminated_from_first_three_demos": eliminated,
                "four_query_scope": "last four are fresh Racket-labeled candidate queries; finite teaching checked only where declared rivals are available",
                "retained_evidence_sha256": evidence,
            })
        result["status"] = "completed"
        result["exit_code"] = 0
    except Exception as exc:
        result["status"] = "blocked"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["exit_code"] = 1
    finally:
        if bridge is not None:
            bridge.shutdown()
        signal.alarm(0)
        result["elapsed_probe_seconds"] = time.monotonic() - started
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "selected_ids": ids,
                      "elapsed_probe_seconds": result["elapsed_probe_seconds"],
                      "error": result.get("error")}))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
