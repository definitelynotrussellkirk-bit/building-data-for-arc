#!/usr/bin/env python3
"""Reproduce the selected generator's filled-bounding-box teaching shortcut.

From WORK: python3 checks/audit/fa103c7aa88b/probe.py run
Native labels come only from the recorded arcpuzzles apply command.
No generator, reference, catalog, or assignment files are changed.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone

TASK = "fa103c7aa88b"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE_SHA = "2b6d2213316f09c1f806db076b6e99df434e51f84e7a524bb970b6b0b0a0b7f3"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError(f"Preserve previous evidence; already exists: {path}")
    path.write_text(json.dumps(value, indent=2) + "\n")


def components(grid):
    """Independent same-color, four-neighbor component extraction."""
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, grid[0][0]) or (r, c) in seen:
                continue
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                p = stack.pop()
                cells.append(p)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = p[0] + dr, p[1] + dc
                    if (0 <= rr < len(grid) and 0 <= cc < len(row)
                            and (rr, cc) not in seen and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
            c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
            result.append(dict(color=color, cells=cells, size=len(cells),
                               bbox=[r0, c0, r1, c1], h=r1-r0+1, w=c1-c0+1))
    return sorted(result, key=lambda c: (-c["size"], c["h"], c["w"]))


def bbox_signature(grid):
    return [grid[0][0], sorted([c["h"], c["w"]] for c in components(grid)[:2])]


def bbox_rival(grid):
    """Keep object selection but replace each selected shape by its filled bbox."""
    a, b = components(grid)[:2]
    aa = {(r, c) for r in range(a["h"]) for c in range(a["w"])}
    bb = {(r, c) for r in range(b["h"]) for c in range(b["w"])}
    key = grid[0][0]
    occ = aa | bb if key == 1 else aa & bb if key == 2 else aa ^ bb
    if not occ:
        return [[0]]
    r0, r1 = min(p[0] for p in occ), max(p[0] for p in occ)
    c0, c1 = min(p[1] for p in occ), max(p[1] for p in occ)
    return [[8 if (r, c) in occ else 0 for c in range(c0, c1+1)]
            for r in range(r0, r1+1)]


def prepare():
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK, root=root)
    assert source_sha == SOURCE_SHA, ("Source changed", source_sha)
    catalog_row = Catalog(root).get(TASK)
    variants = catalog_row["variants"]
    assert len(variants) == 1
    rule_sha = hashlib.sha256(" ".join(variants[0]["program_solution"].split()).encode()).hexdigest()
    cases = []
    for band in ("easy", "medium", "hard"):
        for i in range(6):
            seed, index = 20261013 + i * 7919, i * 17 + 5
            grid = module.generate(seed, index, difficulty=band)
            cs = components(grid)
            cases.append(dict(kind="ordinary", difficulty=band, seed=seed,
                              sample_index=index, overrides={}, input=grid,
                              input_sha256=digest(grid), self_check=module.self_check(grid),
                              bbox_signature=bbox_signature(grid),
                              main_shapes_filled=all(c["size"] == c["h"] * c["w"] for c in cs[:2]),
                              component_sizes=[c["size"] for c in cs]))

    # First eligible ordinary input supplies a strictly lawful counterfactual:
    # removing an interior shared cell preserves each bbox and connectivity.
    # A union needs the cell removed from both shapes; other operations need one.
    for parent_index, case in enumerate(cases):
        cs = components(case["input"])
        if any(min(c["h"], c["w"]) < 3 for c in cs[:2]):
            continue
        changed = copy.deepcopy(case["input"])
        removals = []
        for component in cs[:2 if changed[0][0] == 1 else 1]:
            r, c = component["bbox"][0] + 1, component["bbox"][1] + 1
            removals.append([r, c, changed[r][c]])
            changed[r][c] = 0
        errors = module.self_check(changed)
        if errors or bbox_signature(changed) != case["bbox_signature"]:
            continue
        cases.append(dict(kind="lawful_counterfactual", parent_index=parent_index,
                          removed_cells=removals, input=changed, input_sha256=digest(changed),
                          self_check=errors, bbox_signature=bbox_signature(changed)))
        break
    else:
        raise AssertionError("No lawful counterfactual found in the fixed 18-draw probe")

    pair, = [p for p in canonical_pairs(TASK, root=root, variant=0, labeled_only=True)
             if p["split"] == "train" and p["pair_index"] == 1]
    cases.append(dict(kind="canonical_train_1", input=pair["input"],
                      recorded_canonical_output=pair["output"],
                      input_sha256=digest(pair["input"]), self_check=module.self_check(pair["input"]),
                      bbox_signature=bbox_signature(pair["input"])))
    for case in cases:
        case["rival_output"] = bbox_rival(case["input"])
    save("input.json", {"inputs": [c["input"] for c in cases]})
    save("probe_meta.json", dict(task_id=TASK, generator_path=str(source.relative_to(root)),
                                 generator_sha256=source_sha,
                                 rule_source="shared/data/canonical/puzzles.jsonl",
                                 normalized_rule_sha256=rule_sha,
                                 catalog_rule_hash=catalog_row["rule_hash"],
                                 canonical_variant_sha256=digest(variants[0]),
                                 task_local_tests=sorted(str(p.relative_to(root)) for p in
                                                         (root / "generators" / TASK / "tests").rglob("test*.py")),
                                 cases=cases))
    save("rival.json", {"rival": "filled_main_bounding_boxes",
                         "outputs": [c["rival_output"] for c in cases]})
    print(json.dumps({"inputs_prepared": len(cases), "ordinary": 18,
                      "self_check_valid": sum(not c["self_check"] for c in cases),
                      "ordinary_key_counts": dict(Counter(c["input"][0][0] for c in cases[:18]))}))


def assess():
    from reviewer_support import find_root, load_selected_generator
    meta = json.loads((HERE / "probe_meta.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    cases, results = meta["cases"], receipt["results"]
    _, _, current_sha = load_selected_generator(TASK, root=find_root(__file__))
    assert current_sha == meta["generator_sha256"] == SOURCE_SHA
    assert receipt["executed_rule_hash"] == meta["catalog_rule_hash"] == meta["normalized_rule_sha256"][:12]
    assert len(results) == len(cases) == 20
    assert all(row["error"] is None for row in results), results
    assert all(not case["self_check"] for case in cases)
    ordinary = [i for i, case in enumerate(cases) if case["kind"] == "ordinary"]
    assert all(cases[i]["main_shapes_filled"] for i in ordinary)
    matches = [results[i]["output"] == cases[i]["rival_output"] for i in ordinary]
    assert all(matches)
    mutated_index, = [i for i, c in enumerate(cases) if c["kind"] == "lawful_counterfactual"]
    mutated = cases[mutated_index]
    parent_index = mutated["parent_index"]
    assert mutated["bbox_signature"] == cases[parent_index]["bbox_signature"]
    assert mutated["rival_output"] == cases[parent_index]["rival_output"]
    assert results[mutated_index]["output"] != results[parent_index]["output"]
    assert results[-1]["output"] == cases[-1]["recorded_canonical_output"]
    assert results[-1]["output"] != cases[-1]["rival_output"]
    summary = dict(verdict="reproduced_teaching_defect", task_id=TASK,
                   generator_sha256=current_sha, executed_rule_hash=receipt["executed_rule_hash"],
                   normalized_rule_sha256=meta["normalized_rule_sha256"],
                   counts={"ordinary_generated": len(ordinary), "ordinary_rival_matches": sum(matches),
                           "authoritative_labels": len(results), "racket_errors": 0,
                           "self_check_valid": len(cases), "lawful_rival_counterexamples": 2,
                           "ordinary_by_difficulty": dict(Counter(cases[i]["difficulty"] for i in ordinary)),
                           "ordinary_key_counts": dict(Counter(cases[i]["input"][0][0] for i in ordinary))},
                   witness={"parent_index": parent_index, "counterfactual_index": mutated_index,
                            "key": mutated["input"][0][0], "removed_cells": mutated["removed_cells"],
                            "unchanged_bbox_signature": mutated["bbox_signature"],
                            "ordinary_racket_output": results[parent_index]["output"],
                            "counterfactual_racket_output": results[mutated_index]["output"],
                            "rival_output_for_both": mutated["rival_output"]},
                   canonical_witness={"input_index": len(cases)-1, "split": "train", "pair_index": 1,
                                      "racket_output": results[-1]["output"],
                                      "rival_output": cases[-1]["rival_output"]})
    save("summary.json", summary)
    print(json.dumps(summary, indent=2))


def run():
    log_path = HERE / "commands.json"
    if log_path.exists():
        raise FileExistsError("commands.json exists; preserve previous run")
    relative = HERE.relative_to(WORK).as_posix()
    command_specs = [
        ("prepare", ["python3", "run_with_racket.py", "python3", f"../{relative}/probe.py", "prepare"]),
        ("apply", ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                   "--input", f"../{relative}/input.json", "--out", f"../{relative}/racket.json"]),
        ("assess", ["python3", "run_with_racket.py", "python3", f"../{relative}/probe.py", "assess"]),
    ]
    records = []
    for label, argv in command_specs:
        started = datetime.now(timezone.utc).isoformat()
        before = time.monotonic()
        process = subprocess.run(argv, cwd=WORK, capture_output=True, text=True, timeout=180)
        (HERE / f"{label}.stdout.log").write_text(process.stdout)
        (HERE / f"{label}.stderr.log").write_text(process.stderr)
        records.append(dict(cwd=".", effective_payload_cwd="repo", argv=argv,
                            exit_code=process.returncode, utc_start=started,
                            elapsed_seconds=round(time.monotonic()-before, 3),
                            evidence_paths=[f"{relative}/{label}.stdout.log", f"{relative}/{label}.stderr.log"]))
        log_path.write_text(json.dumps(records, indent=2) + "\n")
        print(f"{label}: exit={process.returncode}", flush=True)
        if process.returncode:
            print(process.stdout + process.stderr, file=sys.stderr)
            return process.returncode
    print((HERE / "summary.json").read_text())
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode == "prepare":
        prepare()
    elif mode == "assess":
        assess()
    elif mode == "run":
        raise SystemExit(run())
    else:
        raise SystemExit(__doc__)
