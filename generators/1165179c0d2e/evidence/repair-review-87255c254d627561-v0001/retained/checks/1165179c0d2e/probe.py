#!/usr/bin/env python3
"""Bounded 3-demo teaching probe; Python selects, protected Racket adjudicates."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = "1165179c0d2e"
SIZE_EXPR = "(map obj-size (filter (lambda (obj) (= (obj-color obj) 6)) (objects g 0)))"
SORT_EXPR = "(sort\n             " + SIZE_EXPR + "\n             >)"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sizes_scan(grid):
    """Diagnostic only: 4-connected same-color components in row-major order."""
    visited, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 6 or (r, c) in visited:
                continue
            todo, cells = [(r, c)], set()
            while todo:
                p = todo.pop()
                if p in cells:
                    continue
                cells.add(p)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = p[0] + dr, p[1] + dc
                    if 0 <= nr < len(grid) and 0 <= nc < len(row) and grid[nr][nc] == 6:
                        todo.append((nr, nc))
            visited.update(cells)
            result.append(len(cells))
    return result


def main():
    started = time.monotonic()
    gen, path, source_hash = load_selected_generator(TASK, root=ROOT)
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if line.strip()]
    matches = [row for row in rows if row.get("task_id") == TASK]
    if len(matches) != 1:
        raise ValueError("canonical rule selection is ambiguous")
    program = matches[0]["program_solution"]
    if program.count(SORT_EXPR) != 1:
        raise ValueError("exact reference sort expression changed")
    rivals = {
        "scan_order": SIZE_EXPR,
        "largest_then_scan_order": "(let* ((values " + SIZE_EXPR + ") (biggest (apply max values))) (cons biggest (remove biggest values)))",
    }
    report = {
        "schema": "1165179c0d2e-bounded-teaching-probe-v1", "task_id": TASK,
        "source_path": path.relative_to(ROOT).as_posix(), "source_sha256": source_hash,
        "program": program, "program_sha256": digest(program.encode()),
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "scope": "at most 32 easy seeds, sample_index 0..3 as 3 demos plus 1 query; two closely related spatial-order rivals",
        "authority": "Python components only select candidates; all retained outputs from actual protected Racket",
        "diagnostic_search": [], "errors": [], "racket_evaluations": 0,
    }
    selected = None
    for seed in range(32):
        if time.monotonic() - started > 105:
            break
        grids = [gen.generate(seed, index, difficulty="easy") for index in range(4)]
        sizes = [sizes_scan(grid) for grid in grids]
        row = {"seed": seed, "difficulty": "easy", "sample_indices": list(range(4)), "scan_sizes": sizes,
               "self_check": [gen.self_check(grid, difficulty="easy") for grid in grids], "rivals": {}}
        for name in rivals:
            alt = []
            for values in sizes:
                if name == "scan_order":
                    alt.append(values)
                else:
                    tail = list(values)
                    largest = max(tail)
                    tail.remove(largest)
                    alt.append([largest] + tail)
            agreement = [a == sorted(b, reverse=True) for a, b in zip(alt, sizes)]
            row["rivals"][name] = agreement
            if agreement == [True, True, True, False] and not any(row["self_check"]):
                selected = (seed, name, grids)
                break
        report["diagnostic_search"].append(row)
        if selected:
            break
    bridge = None
    try:
        if selected:
            seed, name, grids = selected
            rival_program = program.replace(SORT_EXPR, rivals[name])
            report.update(seed=seed, rival=name, rival_program=rival_program,
                          rival_program_sha256=digest(rival_program.encode()))
            bridge = RacketBridge()
            report["runtime"] = bridge.runtime_identity
            if report["runtime"].get("backend") != "racket" or report["runtime"].get("protected") is not True:
                raise ValueError("protected actual Racket required")
            def execute(source, grid):
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                report["racket_evaluations"] += 1
                return bridge.eval_text(f"({wrap_rule(source)} {literal})")
            cases = []
            for index, grid in enumerate(grids):
                actual, alternative = execute(program, grid), execute(rival_program, grid)
                if type(actual) is not list or type(alternative) is not list:
                    raise ValueError("Racket did not return grid lists")
                cases.append({"split": "train" if index < 3 else "test", "sample_index": index,
                              "input": grid, "output": actual, "rival_output": alternative,
                              "agree": actual == alternative,
                              "different_cells": sum(a != b for ra, rb in zip(actual, alternative) for a, b in zip(ra, rb))})
            report["minimal_case"] = {"train": cases[:3], "test": cases[3:]}
            if [case["agree"] for case in cases] != [True, True, True, False]:
                raise ValueError("actual Racket did not confirm diagnostic ambiguity")
            report["status"] = "confirmed_teaching_gap"
        else:
            report["status"] = "bounded_no_finding"
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        report["status"] = "failed_probe"
    finally:
        if bridge is not None:
            bridge.close()
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["seeds_examined"] = len(report["diagnostic_search"])
    report["remaining_limits"] = [
        "Only easy difficulty and these two closely related rivals were considered; no universal lesson uniqueness claim.",
        "Prior fixed-bottom-row/tied-size audit remains open; this probe neither repairs it nor grants qualification or approval."]
    (HERE / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report.get(key) for key in ("status", "seed", "rival", "seeds_examined", "racket_evaluations", "elapsed_seconds", "errors")}))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
