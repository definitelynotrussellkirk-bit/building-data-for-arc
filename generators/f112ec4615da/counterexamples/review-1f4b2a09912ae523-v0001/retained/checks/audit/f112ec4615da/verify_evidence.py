"""Bind the retained shortcut witness to the public Racket application receipt."""
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

out = Path(__file__).resolve().parent
root = find_root(__file__)
probe = json.loads((out / "probe.json").read_text())
applied = json.loads((out / "racket.json").read_text())
combined = json.loads((out / "combined/result.json").read_text())
canonical = canonical_pairs("f112ec4615da", root=root, labeled_only=True)
current_source = root / "generators/f112ec4615da/generator.py"
current_hash = hashlib.sha256(current_source.read_bytes()).hexdigest()
assert current_hash == probe["generator_sha256"] == applied["generator_sha256"] == combined["audit_summary"]["generator_sha256"]
rows = applied["results"]
assert len(rows) == len(canonical) + 3 == 10
assert all(item["error"] is None and item["valid_output"] and item["generator_domain"]["status"] == "valid" for item in rows)
canonical_matches = [rows[i]["output"] == pair["output"] for i, pair in enumerate(canonical)]
assert all(canonical_matches) and all(probe["canonical_retained_label_matches"])
lesson = []
for index, pair in enumerate(probe["lesson"]["pairs"]):
    actual = rows[len(canonical)+index]["output"]
    assert actual == pair["python_reference_prediction"]
    grid = pair["input"]
    hh, hw = len(grid)//2, len(grid[0])//2
    colors = [next(v for r in range(hh) for c in range(hw) if (v := grid[top+r][left+c]))
              for top, left in ((0, 0), (0, hw), (hh, 0), (hh, hw))]
    counts = {name: sum(v == color for row in actual for v in row)
              for name, color in zip(("zero", "tl", "tr", "bl", "br"), (0, *colors))}
    assert all(counts.values())
    lesson.append({"sample_index": index, "input": grid, "actual_racket_output": actual,
                   "rival_output": pair["rival_output"], "rival_exact": actual == pair["rival_output"],
                   "generator_domain": rows[len(canonical)+index]["generator_domain"],
                   "winner_counts": counts})
matches = [pair["rival_exact"] for pair in lesson]
assert matches == [True, True, False]
rotations = [{"query_index": i, "demonstration_indices": [j for j in range(3) if j != i],
              "refuting_demonstration_indices": [j for j in range(3) if j != i and not matches[j]],
              "rival_survives_demonstrations": all(matches[j] for j in range(3) if j != i),
              "query_identifiable_against_this_rival": matches[i] or any(not matches[j] for j in range(3) if j != i)}
             for i in range(3)]
query = lesson[2]
differences = [{"row": r, "col": c, "racket": query["actual_racket_output"][r][c], "rival": query["rival_output"][r][c]}
               for r in range(3) for c in range(3)
               if query["actual_racket_output"][r][c] != query["rival_output"][r][c]]
result = {
    "schema": "reviewer-audit-shortcut-counterexample-v1", "task_id": "f112ec4615da",
    "phase": "audit", "intent": "diagnostic_probe", "status": "shortcut_reproduced",
    "generator_sha256": current_hash, "generator_version": probe["generator_version"],
    "canonical_raw_program_sha256": probe["rule_sha256"],
    "executed_rule_hash": applied["executed_rule_hash"],
    "public_apply_rule_text_sha256": applied["rule_text_sha256"],
    "racket_receipt_sha256": hashlib.sha256((out / "racket.json").read_bytes()).hexdigest(),
    "rival": probe["rival"], "declared_rivals": {"CANONICAL_SHORTCUTS": probe["declared_CANONICAL_SHORTCUTS"],
                                                   "LESSON_COMPETITORS": probe["declared_LESSON_COMPETITORS"]},
    "canonical_racket_and_retained_label_matches": sum(canonical_matches), "canonical_pair_count": len(canonical),
    "canonical_rival_matches": sum(probe["canonical_retained_label_matches"]),
    "seed": probe["lesson"]["seed"], "sample_indices": [0, 1, 2], "difficulty": None,
    "overrides": {"grid_h": 6, "grid_w": 6},
    "lesson_policy": "Explicit audit assembly: sample indices 0 and 1 are demonstrations; sample index 2 is the query.",
    "lesson": lesson, "ordered_demonstration_matches": 2, "ordered_query_matches": 0,
    "rotations": rotations, "identifiable_rotation_count": sum(row["query_identifiable_against_this_rival"] for row in rotations),
    "rotation_count": len(rotations), "query_differing_cells": differences,
    "search": {"examined_seed_range": probe["examined_seed_range"], "generated_draw_count": probe["generated_input_count"],
               "unique_draw_count": "not measured across the preliminary search", "retained_lesson_unique_input_count": len({json.dumps(pair["input"]) for pair in lesson}),
               "search_labels": "Python search predictions; only the retained ten inputs were executed by the public Racket apply command."},
    "apply_command": applied["command"], "apply_cwd": applied["cwd"],
    "verification_command": [sys.executable, *sys.argv], "verification_cwd": str(Path.cwd()),
    "limits": ["This reproduces one explicit two-demonstration lesson, not the default exporter ordering or all lesson sizes.",
               "Only the named audit-only numeric-color rival is assessed; no universal identifiability claim.",
               "A source-bound teaching counterexample is not a Racket labeling defect; all ten tested inputs execute correctly.",
               "No target or shared source was edited; full battery and repair are outside this audit."]}
(out / "counterexample.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "canonical_matches": 7, "racket_valid_inputs": 10,
                  "seed": result["seed"], "ordered_demo_matches": 2, "ordered_query_matches": 0,
                  "identifiable_rotations": result["identifiable_rotation_count"], "rotation_count": 3,
                  "query_differing_cells": differences}))
