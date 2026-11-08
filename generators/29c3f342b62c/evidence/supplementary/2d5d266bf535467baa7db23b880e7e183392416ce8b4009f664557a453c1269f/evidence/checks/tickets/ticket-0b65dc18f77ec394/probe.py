"""One bounded adversarial-witness probe; no peer mutation or census."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK = "29c3f342b62c"
EXPECTED_SOURCE = "a29db6fb193428cff1e92298066a810a8b0f92bc13c7994d897cf7a92da550fa"
EXPECTED_PROGRAM = "5eb351058644a98bd78bfdafedad9fa31a1e1d22be3f3b8bb5a5a95d2df78b49"
TICKET_SEED = "e781b06b4726fbacb0084df49d8aec3de4c5b0926c13c2d365d3565f6e790228"
START = time.monotonic()
result = {"schema": "bounded-adversarial-witness-v1", "ticket_id": "ticket-0b65dc18f77ec394",
          "task_id": TASK, "pinned_rule_hash": "a1a5d656635f", "ticket_seed": TICKET_SEED,
          "hypothesis": "A shortcut may reflect around the grid midpoint instead of locating the full-height gray divider.",
          "targeted_probes": 1, "targeted_probe_limit_seconds": 120,
          "actual_racket_evaluations": 0, "cases": []}
try:
    generator, path, digest = load_selected_generator(TASK, root=REPO)
    assert digest == EXPECTED_SOURCE
    result["generator_source"] = {"path": str(path.relative_to(WORK)), "sha256": digest}
    programs = set()
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    canonical = programs.pop()
    assert hashlib.sha256(canonical.encode()).hexdigest() == EXPECTED_PROGRAM
    start = canonical.index("(find-first")
    depth = 0
    for end in range(start, len(canonical)):
        depth += (canonical[end] == "(") - (canonical[end] == ")")
        if depth == 0:
            break
    original_finder = canonical[start:end+1]
    rival = canonical[:start] + "(quotient (- (cols g) 1) 2)" + canonical[end+1:]
    assert canonical.count(original_finder) == 1
    result["programs"] = {name: {"program_solution": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
                          for name, text in (("canonical", canonical), ("fixed_grid_midpoint", rival))}
    derived_seed = int(TICKET_SEED[:16], 16)
    generated = generator.generate(derived_seed, 0, difficulty="medium")
    witness = [[0] * 11 for _ in range(4)]
    for row in witness:
        row[4] = 5
    witness[0][2] = 2
    witness[3][1] = 7
    expected_witness = [row[:] for row in witness]
    expected_witness[0][6] = 2
    expected_witness[3][7] = 7
    cases = [("one_pinned_seed_generated_draw", generated,
              {"seed": derived_seed, "seed_derivation": "int(ticket_seed[:16],16)", "sample_index": 0, "difficulty": "medium"}),
             ("lawful_noncentral_divider_witness", witness, {"construction": "4x11; gray divider col4; sources(0,2)=2,(3,1)=7; midpointcol5"})]
    with RacketBridge(timeout=10.0) as bridge:
        for name, grid, origin in cases:
            validation = generator.self_check(grid)
            assert not validation, validation
            literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            outputs = {}
            for model, text in (("canonical", canonical), ("fixed_grid_midpoint", rival)):
                assert text.startswith("(rule!") and text.endswith(")")
                body = text[len("(rule!"):-1]
                result["actual_racket_evaluations"] += 1
                outputs[model] = bridge.eval_text(f"(let ((g '{literal})) {body})")
            differences = [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                           if outputs["canonical"][r][c] != outputs["fixed_grid_midpoint"][r][c]]
            case = {"name": name, "origin": origin, "input": grid, "self_check": validation,
                    "outputs": outputs, "difference_cells": differences,
                    "input_sha256": hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()}
            result["cases"].append(case)
            if name == "lawful_noncentral_divider_witness":
                assert outputs["canonical"] == expected_witness
                assert len(differences) == 4
                case["hand_derived_expected_output_matches"] = True
        result["runtime_identity"] = bridge.runtime_identity
    result["status"] = "completed"
    result["conclusion"] = "Canonical execution correctly rejects the fixed-midpoint shortcut on a lawful noncentral-divider witness. This bounded probe found no peer safety defect."
    exit_code = 0
except Exception:
    result["status"] = "probe_failed"
    result["traceback"] = traceback.format_exc()
    exit_code = 1
result["elapsed_seconds"] = round(time.monotonic()-START, 3)
(OUT / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "elapsed_seconds": result["elapsed_seconds"],
                  "actual_racket_evaluations": result["actual_racket_evaluations"],
                  "difference_cells": [len(case["difference_cells"]) for case in result["cases"]]}))
if exit_code:
    print(result["traceback"])
raise SystemExit(exit_code)
