"""Independent input-only rival check of publicly generated Racket-verified pairs.

Run from packet_root: python3 checks/audit/generic_mosaic_repair_gen1/probe.py
This does not import the generator or private runtime helpers.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


TASK = "generic_mosaic_repair_gen1"
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
GEN = ROOT / "repo" / "generators" / TASK / "generator.py"
GEN_ARGV = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles",
            "generate", TASK, "--count", "4", "--seed", "0", "--difficulty",
            "medium", "--train", "2", "--test", "1", "--allow-unapproved",
            "--timeout", "120", "--out", "../checks/audit/" + TASK + "/generated.jsonl"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def diagonal_only(grid):
    """Intentional teaching negative: copy only from the transpose, preserving visible cells."""
    return [[v if v else grid[c][r] for c, v in enumerate(row)]
            for r, row in enumerate(grid)]


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


tree = ast.parse(GEN.read_text())
assignments = {t.id: node.value for node in tree.body if isinstance(node, ast.Assign)
               for t in node.targets if isinstance(t, ast.Name)}
program = ast.literal_eval(assignments["PROGRAM"])
sources = {"generator_path": str(GEN.relative_to(ROOT)),
           "generator_sha256": sha(GEN.read_bytes()),
           "program_text_sha256": sha(program.encode()),
           "executed_rule_hash": sha(" ".join(program.split()).encode())[:12],
           "summary_sha256": sha(GEN.with_name("SUMMARY.md").read_bytes()),
           "rival_declarations": {name: name in assignments for name in
                                  ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")},
           "note": "Unchanged final audit source; generic emitted program is the authority."}
episodes = [json.loads(line) for line in (OUT / "generated.jsonl").read_text().splitlines()]
rows, lesson_rows, hashes, witnesses = [], [], [], []
for episode in episodes:
    assert episode["provenance"]["generator_sha256"] == sources["generator_sha256"]
    assert episode["program"] == program
    assert episode["executed_rule_hash"] == sources["executed_rule_hash"]
    split_fits = {}
    retained = {}
    for split in ("train", "test"):
        retained[split], split_fits[split] = [], []
        for index, pair in enumerate(episode[split]):
            grid, actual = pair["input"], pair["output"]
            rival = diagonal_only(grid)
            n = len(grid)
            assert n == len(grid[0]) and 20 <= n <= 26
            assert all(1 <= v <= 9 for row in actual for v in row)
            assert all(not grid[r][c] or grid[r][c] == actual[r][c]
                       for r in range(n) for c in range(n))
            assert all(actual[r][c] == actual[c][r] for r in range(n) for c in range(n))
            axes = [a for a in range(n - 1, n + 3)
                    if all(actual[r][c] == actual[r][a-c]
                           for r in range(n) for c in range(n) if 0 <= a-c < n)
                    and all(actual[r][c] == actual[a-r][c]
                            for r in range(n) for c in range(n) if 0 <= a-r < n)]
            assert axes
            mismatches = [[r, c] for r in range(n) for c in range(n)
                          if rival[r][c] != actual[r][c]]
            row = {"seed": episode["seed"], "sample_index": episode["sample_index"],
                   "episode_index": episode["episode_index"], "split": split,
                   "pair_index": index, "dimension": n, "input_sha256": grid_sha(grid),
                   "actual_output_sha256": grid_sha(actual), "rival_output_sha256": grid_sha(rival),
                   "shared_clean_axes": axes, "rival_matches": not mismatches,
                   "mismatch_cells": mismatches}
            rows.append(row)
            hashes.append(row["input_sha256"])
            split_fits[split].append(not mismatches)
            retained[split].append({**row, "input": grid,
                                    "actual_racket_output": actual, "rival_output": rival})
    gap = all(split_fits["train"]) and not all(split_fits["test"])
    lesson_rows.append({"seed": episode["seed"], "sample_index": episode["sample_index"],
                        "train_all_match": all(split_fits["train"]),
                        "test_all_match": all(split_fits["test"]), "teaching_gap": gap})
    if gap:
        witnesses.append({"task_id": TASK, "intent": "intentional teaching negative",
                          "source_hashes": sources, "seed": episode["seed"],
                          "sample_index": episode["sample_index"], "overrides": {},
                          "difficulty": "medium", "requested_n_train": 2, "requested_n_test": 1,
                          "reference_execution": {"cwd": "packet_root", "runtime_cwd": "repo",
                                                  "argv": GEN_ARGV, "exit_code": 0},
                          "domain": "Actual supported public generation; no separate target validator is defined.",
                          "rival": "For each black cell (r,c), use input[c][r]; preserve other cells.",
                          **retained})
report = {"task_id": TASK, "source_hashes": sources, "phase": "final_unchanged_audit_target",
          "seed_range_inclusive": [0, 3], "sample_indices": [0], "difficulty": "medium",
          "lesson_policy": "Public generate requests 2 train + 1 test; actual returned splits are checked.",
          "episode_count": len(episodes), "pair_count": len(rows), "unique_input_count": len(set(hashes)),
          "rival_pair_matches": sum(row["rival_matches"] for row in rows),
          "train_fit_test_fail_lessons": len(witnesses), "lessons": lesson_rows, "pairs": rows,
          "canonical_claim": "No canonical pairs or rival declarations exist in this generic generator; no canonical-fit claim is made.",
          "limits": "Small deterministic audit only. Generated outputs come from public Racket-verified generation. No full battery or custom-input Racket execution is claimed."}
assert len(witnesses) == 1 and witnesses[0]["seed"] == 1
assert len(witnesses[0]["test"][0]["mismatch_cells"]) == 5
write("sources.json", sources)
write("analysis.json", report)
write("rival_witness.json", witnesses[0])
write("input.json", witnesses[0]["test"][0]["input"])
print(json.dumps({k: report[k] for k in ("episode_count", "pair_count", "unique_input_count",
                                        "rival_pair_matches", "train_fit_test_fail_lessons")}))
