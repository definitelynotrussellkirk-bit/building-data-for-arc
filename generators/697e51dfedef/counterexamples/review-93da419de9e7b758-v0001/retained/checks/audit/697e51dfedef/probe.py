#!/usr/bin/env python3
"""Find and retain a canonical-fitting absolute-area shortcut lesson.

Run through run_with_racket.py from WORK; all source reads are authoring-only.
No target files are modified. The exact witness is checked by public apply.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "697e51dfedef"


def pieces(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            queue, cells = deque([(r, c)]), []
            seen.add((r, c))
            while queue:
                y, x = queue.popleft()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = y + dy, x + dx
                    if (0 <= p[0] < len(grid) and 0 <= p[1] < len(row)
                            and p not in seen and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        queue.append(p)
            result.append({"color": color, "area": len(cells), "cells": sorted(cells)})
    return result


def recolor(grid, *, four_last=False):
    objects = pieces(grid)
    objects.sort(key=(lambda p: (p["area"] == 4, p["area"])) if four_last
                 else (lambda p: p["area"]))
    result = [[0 for _ in row] for row in grid]
    for obj, color in zip(objects, (2, 4, 8)):
        for r, c in obj["cells"]:
            result[r][c] = color
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(Path.cwd())
    generator, source, source_hash = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root)
    canonical_fit = [recolor(pair["input"], four_last=True) == pair["output"] for pair in canonical]
    # The fixed rule is chosen from the canonical cue (four cells always largest),
    # before looking for a generated failure. It is not fitted separately per lesson.
    search, found = [], None
    for seed in range(20):
        for start in range(6):
            grids = [generator.generate(seed, start + i, difficulty="medium") for i in range(4)]
            truth = [recolor(grid) for grid in grids]
            rival = [recolor(grid, four_last=True) for grid in grids]
            matches = [a == b for a, b in zip(truth, rival)]
            search.append({"seed": seed, "start": start, "difficulty": "medium", "matches": matches})
            if all(matches[:3]) and not matches[3]:
                found = {"seed": seed, "start": start, "grids": grids, "truth": truth, "rival": rival}
                break
        if found is not None:
            break
    if found is None:
        raise RuntimeError("No witness in the declared finite search; preserve this failed run")
    grids = [pair["input"] for pair in canonical] + found["grids"]
    inputs = args.out / "inputs.json"
    inputs.write_text(json.dumps(grids) + "\n")
    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
               "--input", str(inputs), "--check-generator-domain", "--timeout", "180",
               "--out", str(args.out / "racket.json")]
    run = subprocess.run(command, capture_output=True, text=True, timeout=210)
    (args.out / "racket.log").write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(f"public Racket apply failed: {run.returncode}")
    reference = json.loads((args.out / "racket.json").read_text())
    labels = [row["output"] for row in reference["results"]]
    assert len(labels) == len(grids)
    assert all(label == recolor(grid) for grid, label in zip(grids, labels))
    assert all(row["error"] is None and row["generator_domain"]["status"] == "valid"
               for row in reference["results"])
    lesson = []
    for i, (grid, output, rival) in enumerate(zip(found["grids"], labels[len(canonical):], found["rival"])):
        lesson.append({"position": i, "role": "demo" if i < 3 else "query",
                       "call": {"seed": found["seed"], "sample_index": found["start"] + i,
                                "difficulty": "medium"},
                       "input": grid, "racket_output": output, "rival_output": rival,
                       "self_check": generator.self_check(grid),
                       "areas": sorted(p["area"] for p in pieces(grid)),
                       "rival_matches": output == rival})
    assert all(row["rival_matches"] for row in lesson[:3]) and not lesson[3]["rival_matches"]
    demos = [{"input": row["input"], "output": row["racket_output"]} for row in lesson[:3]]
    hook_findings = generator.lesson_identifiable(demos, {"input": lesson[3]["input"]})
    report = {"schema": "arcpuzzles-peer-counterexample-v1", "finding_id": "A2-1", "task_id": TASK,
              "generator_sha256": source_hash, "rule_hash": reference["executed_rule_hash"],
              "rule_text_sha256": reference["rule_text_sha256"],
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "rival": "Sort by area, except place an object of exactly four cells last; recolor 2/4/8.",
              "canonical_fit": canonical_fit, "canonical_pairs": len(canonical),
              "search": search, "searched_lessons": len(search),
              "search_scope": "direct consecutive generator calls; seed 0..19, start 0..5, medium; stop at first witness",
              "search_labels": "independent Python area reader; retained witness and canonical labels rechecked by actual Racket",
              "lesson_policy": "three consecutive demonstrations and one query; no query rotation claim",
              "lesson": lesson, "existing_lesson_hook_findings": hook_findings,
              "public_apply_command": command, "public_apply_cwd": str(Path.cwd()), "public_apply_exit_code": run.returncode,
              "source_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == source_hash,
              "limitations": ["A generated ordered lesson counterexample, not a measured frequency in the production materializer.",
                              "No audit target source was patched; adding an area-role rival and teaching support is proposed."]}
    (args.out / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"finding": "A2-1", "seed": found["seed"], "start": found["start"],
                      "searched_lessons": len(search), "canonical_fit": canonical_fit,
                      "racket_checked_inputs": len(grids), "lesson_hook_findings": hook_findings,
                      "query_areas": lesson[3]["areas"], "source_sha256": source_hash}))


if __name__ == "__main__":
    main()
