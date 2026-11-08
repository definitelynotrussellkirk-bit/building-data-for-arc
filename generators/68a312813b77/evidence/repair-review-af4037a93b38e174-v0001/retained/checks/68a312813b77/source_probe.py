"""Source-bound canonical shortcut and public-focus demonstration replay.

Run from WORK/repo through the packet launcher with a fresh --out path. This
reads only the public focus challenge, never its separate test solution file,
and executes the focus candidate on its two supplied demonstrations only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / "repo"
RUNTIME = ROOT / "shared/runtime"
TASK_ID = "68a312813b77"
FOCUS_ID = "7666fa5d"
EXPECTED_FOCUS_SHA256 = "1b19ed6f202f6b9addff88314b0697b2752f581a55994c0339948f7cf3f8cd6d"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


FOUR_CONNECTED_PROGRAM = """(rule! (lambda (g)
  (foldl
    (lambda (obj acc)
      (let ((bb (obj-bbox obj)))
        (grid-from-fn (rows g) (cols g)
          (lambda (r c)
            (if (and (>= r (first bb)) (<= r (third bb))
                     (>= c (second bb)) (<= c (fourth bb))
                     (= (at acc r c) 0))
                7 (at acc r c))))))
    g (objects g 0))))"""

FOCUS_INTERVAL_PROGRAM = """(rule! (lambda (g)
  (let ((projected
    (map (lambda (obj)
      (let* ((cells (obj-cells obj))
             (us (map (lambda (p) (+ (first p) (second p))) cells))
             (vs (map (lambda (p) (- (first p) (second p))) cells)))
        (list (apply min us) (apply max us) (apply min vs) (apply max vs))))
      (objects-8 g 8))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let ((u (+ r c)) (v (- r c)))
          (if (and (= (at g r c) 8)
                   (for/or ((a (in-list projected)))
                     (for/or ((b (in-list projected)))
                       (and (< (second a) (first b))
                            (< (second a) u) (< u (first b))
                            (<= (max (third a) (third b)) v)
                            (<= v (min (fourth a) (fourth b)))))))
              2 (at g r c))))))))"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def components(grid, background, diagonal):
    """Independent same-color flood fill, in row-major component order."""
    height, width = len(grid), len(grid[0])
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue
            pending, cells = [(row, col)], []
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.append([r, c])
                for dr, dc in deltas:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width and (rr, cc) not in seen
                            and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        pending.append((rr, cc))
            result.append({"color": color, "cells": sorted(cells)})
    return result


def bbox_mirror(grid, diagonal):
    out = deepcopy(grid)
    for obj in components(grid, 0, diagonal):
        cells = obj["cells"]
        for r in range(min(p[0] for p in cells), max(p[0] for p in cells) + 1):
            for c in range(min(p[1] for p in cells), max(p[1] for p in cells) + 1):
                if out[r][c] == 0:
                    out[r][c] = 7
    return out


def projections(grid):
    result = []
    for obj in components(grid, 8, True):
        us = [r + c for r, c in obj["cells"]]
        vs = [r - c for r, c in obj["cells"]]
        result.append({**obj, "u_min": min(us), "u_max": max(us),
                       "v_min": min(vs), "v_max": max(vs)})
    return result


def focus_mirror(grid):
    projected = projections(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            u, v = r + c, r - c
            if value == 8 and any(a["u_max"] < u < b["u_min"]
                                 and max(a["v_min"], b["v_min"]) <= v
                                 <= min(a["v_max"], b["v_max"])
                                 for a in projected for b in projected):
                out[r][c] = 2
    return out


def differences(left, right):
    return [{"row": r, "column": c, "left": value, "right": right[r][c]}
            for r, row in enumerate(left) for c, value in enumerate(row)
            if value != right[r][c]]


def bindings():
    paths = [
        ROOT / f"generators/{TASK_ID}/generator.py",
        ROOT / "shared/data/canonical/puzzles.jsonl",
        ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json",
        ROOT / "src/arcpuzzles/parametric_worker.py",
        ROOT / "shared/runtime/arc_repl/racket_bridge.py",
        ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        Path(__file__).resolve(),
    ]
    return {path.relative_to(WORK).as_posix(): sha(path.read_bytes()) for path in paths}


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    before = bindings()
    focus = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())[FOCUS_ID]
    focus_hash = sha(compact(focus))
    if focus_hash != EXPECTED_FOCUS_SHA256:
        raise ValueError("Pinned public-focus challenge bytes differ")
    task = Catalog(ROOT).get(TASK_ID)
    canonical = task["variants"][0]
    if len(canonical["train"]) != 2 or len(canonical["test"]) != 1 or len(focus["train"]) != 2:
        raise ValueError("Unexpected source pair counts")
    program = canonical["program_solution"]
    if {v["program_solution"] for v in task["variants"]} != {program}:
        raise ValueError("Ambiguous canonical source")
    report = {
        "schema": "68a312813b77-source-shortcut-focus-probe-v1",
        "task_id": TASK_ID,
        "status": "running",
        "source_files_sha256": before,
        "generator_sha256": task["generator_sha256"],
        "canonical_rule_hash": task["rule_hash"],
        "canonical_shortcut": {
            "program": program, "program_sha256": sha(program.encode()),
            "rival": "Use monochrome 4-connectivity before filling each object's bounding box.",
            "rival_program": FOUR_CONNECTED_PROGRAM,
            "rival_program_sha256": sha(FOUR_CONNECTED_PROGRAM.encode()),
            "cases": [],
        },
        "public_focus": {
            "source_task_id": FOCUS_ID,
            "source_split": "evaluation",
            "source_path": "shared/data/raw/arc-agi_evaluation_challenges.json",
            "challenge_sha256": focus_hash,
            "candidate_program": FOCUS_INTERVAL_PROGRAM,
            "candidate_program_sha256": sha(FOCUS_INTERVAL_PROGRAM.encode()),
            "candidate": "On background 8, extract same-color 8-connected objects; project to u=r+c and v=r-c; fill background with 2 strictly between ordered u intervals and within their intersected v intervals. No own-object bbox fill.",
            "transferred_idea": "Complete gaps between input-derived diagonal object projections. The native extension uses this bridge after ordinary bbox completion, with background 0 and fill 7, so it is not the same transformation as this focus candidate.",
            "relationship_verified": False,
            "focus_test_solutions_read": False,
            "focus_test_labels_generated": False,
            "cases": [],
        },
        "racket_evaluations": 0,
        "findings": [],
        "training_admitted": False,
        "limits": "Canonical shortcut evidence covers exactly two supplied train pairs and one supplied canonical test pair. Public-focus evidence checks a candidate on the two supplied demonstrations only; it does not establish the evaluation test answer, complete task semantics, verified ancestry, or training admission.",
    }
    bridge = None
    phase = "runtime_setup"
    try:
        with _local_imports(RUNTIME, ROOT / f"generators/{TASK_ID}"):
            apply, identity, bridge = _real_evaluator(RUNTIME)
            report["racket"] = identity

            def execute(source, grid):
                result = _grid(apply(source, _grid(grid)))
                report["racket_evaluations"] += 1
                return result

            for split in ("train", "test"):
                for index, pair in enumerate(canonical[split]):
                    phase = f"canonical:{split}:{index}"
                    grid, expected = _grid(pair["input"]), _grid(pair["output"])
                    actual, rival = execute(program, grid), execute(FOUR_CONNECTED_PROGRAM, grid)
                    row = {"split": split, "index": index, "input": grid,
                           "supplied_output": expected, "canonical_output": actual,
                           "rival_output": rival, "canonical_matches_supplied": actual == expected,
                           "canonical_matches_python_mirror": actual == bbox_mirror(grid, True),
                           "rival_matches_python_mirror": rival == bbox_mirror(grid, False),
                           "rival_matches_supplied": rival == expected,
                           "canonical_rival_differences": differences(actual, rival)}
                    report["canonical_shortcut"]["cases"].append(row)
                    if not all(row[key] for key in ("canonical_matches_supplied", "canonical_matches_python_mirror", "rival_matches_python_mirror")):
                        report["findings"].append({"kind": "canonical_or_rival_label_mismatch", "split": split, "index": index})
                    if (split == "train" and rival != expected) or (split == "test" and len(row["canonical_rival_differences"]) != 4):
                        report["findings"].append({"kind": "expected_shortcut_witness_not_reproduced", "split": split, "index": index})

            for index, pair in enumerate(focus["train"]):
                phase = f"public_focus:train:{index}"
                grid, expected = _grid(pair["input"]), _grid(pair["output"])
                actual = execute(FOCUS_INTERVAL_PROGRAM, grid)
                row = {"split": "train", "index": index, "input": grid,
                       "supplied_output": expected, "candidate_output": actual,
                       "candidate_matches_supplied": actual == expected,
                       "candidate_matches_python_mirror": actual == focus_mirror(grid),
                       "projected_objects": projections(grid),
                       "differences": differences(expected, actual)}
                report["public_focus"]["cases"].append(row)
                if not row["candidate_matches_supplied"] or not row["candidate_matches_python_mirror"]:
                    report["findings"].append({"kind": "focus_candidate_mismatch", "index": index})
            phase = "source_freeze"
            if bindings() != before:
                raise RuntimeError("Bound source changed during execution")
            report["status"] = "passed" if not report["findings"] else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error)}
    finally:
        if bridge is not None:
            bridge.close()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    result = run(parser.parse_args().out)
    print(json.dumps({key: result.get(key) for key in ("status", "racket_evaluations", "findings", "execution_failure")}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
