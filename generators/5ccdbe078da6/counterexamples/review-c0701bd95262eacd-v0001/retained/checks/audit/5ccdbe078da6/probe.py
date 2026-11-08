"""Recheck the current source-bound open lesson finding with actual Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process

TASK = "5ccdbe078da6"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
canonical = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
calls = [{"seed": 0, "sample_index": i, "difficulty": "easy"} for i in range(4)]
generated = [GEN.generate(**call) for call in calls]
records = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
           if line.strip() and json.loads(line).get("task_id") == TASK]
assert len(records) == 1
program = records[0]["program_solution"]
all_grids = [pair["input"] for pair in canonical] + generated
with tempfile.TemporaryDirectory(prefix=f"audit-{TASK}-") as directory:
    stage = Path(directory)
    prepare_runtime(Catalog(ROOT), stage, TASK)
    (stage / "request.json").write_text(json.dumps({"program": program, "grids": all_grids}))
    payload = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
    result = run_process([sys.executable, "-B", "-c", payload], stage, timeout=90)
    assert result["exit_code"] == 0 and not result["timed_out"], result
    outputs = json.loads(result["stdout"])
assert len(outputs) == len(all_grids)
canonical_outputs = outputs[:len(canonical)]
labels = outputs[len(canonical):]
rivals = GEN.LESSON_COMPETITORS
matches = {name: [rival(grid) == label for grid, label in zip(generated, labels, strict=True)]
           for name, rival in rivals.items()}
rotations = []
for held_out in range(4):
    demos = [i for i in range(4) if i != held_out]
    survivors = [name for name in rivals if all(matches[name][i] for i in demos)]
    ambiguous = [name for name in survivors if not matches[name][held_out]]
    rotations.append({"demo_indices": demos, "query_index": held_out,
                      "surviving_rivals": survivors, "ambiguous_rivals": ambiguous,
                      "rival_query_outputs": {name: rivals[name](generated[held_out]) for name in ambiguous},
                      "changed_cells": {name: [[r, c, rivals[name](generated[held_out])[r][c], labels[held_out][r][c]]
                                               for r in range(len(labels[held_out])) for c in range(len(labels[held_out][0]))
                                               if rivals[name](generated[held_out])[r][c] != labels[held_out][r][c]]
                                        for name in ambiguous}})
index_path = ROOT / f"generators/{TASK}/evidence/review_index.json"
index = json.loads(index_path.read_text())
report = {
    "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK,
    "source_path": str(SOURCE), "source_sha256": SOURCE_SHA,
    "source_unchanged": hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA,
    "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
    "declared_rule_hash": GEN.RULE_HASH,
    "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "command": "python3 review.py run python3 ../checks/audit/5ccdbe078da6/probe.py", "cwd": str(ROOT.parents[1]),
    "review_index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
    "open_audit_bindings": [{"source_sha256": row.get("source_sha256"), "resolution": row.get("resolution"),
                             "return_id": row.get("return_id")} for row in index.get("audits", [])],
    "rival_scope": "Six task-declared lesson rivals only; shared generic rivals are not exercised.",
    "racket_grids_checked": len(all_grids),
    "canonical": [{"pair_index": i, "self_check": GEN.self_check(pair["input"]),
                   "racket_matches_label": label == pair["output"], "mirror_matches_racket": GEN.rule_mirror(pair["input"]) == label}
                  for i, (pair, label) in enumerate(zip(canonical, canonical_outputs, strict=True))],
    "generated": [{"call": call, "input": grid, "racket_output": label,
                    "self_check": GEN.self_check(grid), "mirror_matches_racket": GEN.rule_mirror(grid) == label}
                   for call, grid, label in zip(calls, generated, labels, strict=True)],
    "rival_matches": matches, "rotations": rotations,
    "primary_lesson": rotations[3],
    "reproduced_current_open_finding": {"numeric_ascending", "ignore_lines"}.issubset(rotations[3]["ambiguous_rivals"]),
}
(OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"source_sha256": SOURCE_SHA, "rule_hash": report["rule_hash"],
                  "racket_grids_checked": len(all_grids),
                  "canonical_reference_matches": sum(row["racket_matches_label"] for row in report["canonical"]),
                  "all_generated_valid": all(not row["self_check"] for row in report["generated"]),
                  "all_generated_mirror_matches_racket": all(row["mirror_matches_racket"] for row in report["generated"]),
                  "primary_ambiguous_rivals": report["primary_lesson"]["ambiguous_rivals"],
                  "primary_disagreement_cells": {name: len(cells) for name, cells in report["primary_lesson"]["changed_cells"].items()},
                  "reproduced_current_open_finding": report["reproduced_current_open_finding"],
                  "report": str(OUT / "report.json")}, indent=2))
