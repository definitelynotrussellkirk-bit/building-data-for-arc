"""Seven normal generated pairs, three finite rivals, protected Racket labels."""
from pathlib import Path
import hashlib
import json

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles import Catalog
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator

TASK = "3d0bcc09b993"
ROOT = find_root(Path.cwd())
OUT = Path(__file__).resolve().parent
module, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
assert source_hash == "af8b9e5d83bc4e3aed9970cacae9c7c8d1daaf2d9584ca083b8f6baa024269a1"
variants = Catalog(ROOT)._variants()[TASK]
programs = {v["program_solution"] for v in variants}
assert len(programs) == 1
canonical = programs.pop()
assert hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12] == "b4e7fe44329f"
assert canonical.count("(- h 1 (first p))") == 1
assert canonical.count("(- w 1 (second p))") == 1
rivals = {
    "local_horizontal_reflection": canonical.replace("(- h 1 (first p))", "(first p)"),
    "local_vertical_reflection": canonical.replace("(- w 1 (second p))", "(second p)"),
    "whole_grid_half_turn": "(rule! (lambda (g) (rotate-180 g)))",
}


def symmetry_facts(grid):
    rows = []
    for color in sorted({v for row in grid for v in row} - {0}):
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        turned = {(top + bottom - r, left + right - c) for r, c in cells}
        rows.append({"color": color, "cells": sorted(cells), "bbox": [top, left, bottom, right],
                     "is_180_symmetric": cells == turned})
    return rows


def execute(bridge, source, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {literal})")


rows = []
with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"] is True
    for index in range(7):
        grid = module.generate(0, index)
        output = execute(bridge, canonical, grid)
        assert type(output) is list and len(output) == len(grid)
        alternatives = {name: execute(bridge, source, grid) for name, source in rivals.items()}
        assert all(type(value) is list and len(value) == len(grid) for value in alternatives.values())
        rows.append({"seed": 0, "sample_index": index, "split": "train" if index < 3 else "test",
                     "input": grid, "output": output, "rival_outputs": alternatives,
                     "component_facts": symmetry_facts(grid), "self_check": module.self_check(grid)})

audits = []
for name in rivals:
    counterexample = next((r["sample_index"] for r in rows[:3] if r["rival_outputs"][name] != r["output"]), None)
    disagreements = [r["sample_index"] for r in rows[3:] if r["rival_outputs"][name] != r["output"]]
    audits.append({"rival": name, "fits_all_visible_demonstrations": counterexample is None,
                   "first_demonstration_refutation": counterexample,
                   "query_disagreement_indices": disagreements,
                   "ambiguous_lesson_found": counterexample is None and bool(disagreements)})
symmetry_cases = [{"sample_index": r["sample_index"], "color": obj["color"]}
                  for r in rows for obj in r["component_facts"] if obj["is_180_symmetric"]]
report = {"schema": "bounded-peer-learnability-v1", "task_id": TASK,
          "generator_sha256": source_hash, "canonical_rule_hash": "b4e7fe44329f",
          "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
          "approval": "unchanged_unapproved", "status": "bounded_check_completed",
          "source_changes": False, "seed": 0, "demos": 3, "queries": 4,
          "protected_racket_evaluations": 28, "racket": identity, "rivals": audits,
          "ambiguous_lesson_found": any(row["ambiguous_lesson_found"] for row in audits),
          "declared_invariant_violation": {"claim": "each motif is non-symmetric (180-rotation differs from itself)",
                                            "observed_symmetric_motifs": symmetry_cases,
                                            "source_cause": "Last L_SHAPES entry is a point-symmetric four-cell zigzag.",
                                            "scope": "A symmetric motif makes its local action invisible; this alone does not prove ambiguity of the complete lesson."},
          "canonical_program": canonical, "rival_programs": rivals, "pairs": rows,
          "limits": "One unfiltered normal seed/index lesson and three finite rivals only. No full battery, acceptance, universal identifiability, or generator repair."}
(OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({key: report[key] for key in ("status", "protected_racket_evaluations", "ambiguous_lesson_found", "declared_invariant_violation")}))
