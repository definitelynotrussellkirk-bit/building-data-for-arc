#!/usr/bin/env python3
"""Bounded source-bound learnability probe for c58bc02409f6."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "c58bc02409f6"
EXPECTED_SOURCE_SHA256 = "02f418c8b005d8291a8439960a62f5e02c05ee0618d8491330528ff1db728e59"
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))

AREA_PROGRAM = r"""(rule!
  (let ((dummy 0))
    (define (crop-obj obj)
      (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
    (define items
      (sort (map (lambda (obj)
                   (let ((crop (crop-obj obj)))
                     (list (length (obj-cells obj)) (rows crop) (cols crop) (obj-color obj) crop)))
                 (objects g 0))
            (lambda (a b)
              (cond [(not (= (first a) (first b))) (< (first a) (first b))]
                    [(not (= (second a) (second b))) (< (second a) (second b))]
                    [(not (= (third a) (third b))) (< (third a) (third b))]
                    [else (< (fourth a) (fourth b))]))))
    (define crops (map fifth items))
    (define out-h (apply max (map rows crops)))
    (define out-w (+ (apply + (map cols crops)) (max 0 (- (length crops) 1))))
    (let pack ([remaining crops] [c0 0] [out (empty-grid out-h out-w 0)])
      (if (empty? remaining)
          out
          (let* ((crop (first remaining))
                 (r0 (- out-h (rows crop)))
                 (next (for*/fold ([acc out])
                                   ([r (in-range (rows crop))]
                                    [c (in-range (cols crop))])
                         (let ((v (at crop r c)))
                           (if (= v 0) acc (set-cell acc (+ r0 r) (+ c0 c) v))))))
            (pack (rest remaining) (+ c0 (cols crop) 1) next))))))"""


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = [start]
        comp = []
        for r, c in queue:
            comp.append((r, c))
            for dr, dc in CARD:
                q = (r + dr, c + dc)
                if q in unseen and grid[q[0]][q[1]] == color:
                    unseen.remove(q)
                    queue.append(q)
        result.append(sorted(comp))
    return result


def component_record(grid: list[list[int]], comp: list[tuple[int, int]]) -> dict:
    r1, r2 = min(r for r, _ in comp), max(r for r, _ in comp)
    c1, c2 = min(c for _, c in comp), max(c for _, c in comp)
    points = {(r - r1, c - c1) for r, c in comp}
    sh, sw = r2 - r1 + 1, c2 - c1 + 1
    unseen = {(r, c) for r in range(sh) for c in range(sw) if (r, c) not in points}
    holes = 0
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        touches = False
        for r, c in queue:
            touches |= r in {0, sh - 1} or c in {0, sw - 1}
            for dr, dc in CARD:
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    queue.append(q)
        holes += int(not touches)
    crop = [[0 for _ in range(sw)] for _ in range(sh)]
    color = grid[comp[0][0]][comp[0][1]]
    for r, c in points:
        crop[r][c] = color
    return {"holes": holes, "area": len(comp), "height": sh, "width": sw, "color": color, "crop": crop}


def pack(records: Iterable[dict], key) -> list[list[int]]:
    ordered = sorted(records, key=key)
    h = max(r["height"] for r in ordered)
    w = sum(r["width"] for r in ordered) + len(ordered) - 1
    out = [[0] * w for _ in range(h)]
    c0 = 0
    for record in ordered:
        r0 = h - record["height"]
        for r, row in enumerate(record["crop"]):
            for c, value in enumerate(row):
                if value:
                    out[r0 + r][c0 + c] = value
        c0 += record["width"] + 1
    return out


def witness_input() -> list[list[int]]:
    grid = [[0] * 18 for _ in range(12)]
    # 0 holes, area 9: deliberately larger than the one-hole ring.
    for r in range(1, 4):
        for c in range(1, 4):
            grid[r][c] = 4
    # 1 hole, area 8.
    for r in range(1, 4):
        for c in range(7, 10):
            if (r, c) != (2, 8):
                grid[r][c] = 6
    # 2 holes, area 13.
    holes = {(8, 2), (8, 4)}
    for r in range(7, 10):
        for c in range(1, 6):
            if (r, c) not in holes:
                grid[r][c] = 8
    return grid


def literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)

    gen, source_path, source_sha = load_selected_generator(TASK_ID)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"peer source differs: {source_sha}")

    solution_path = Path("shared/data/base/solutions/banks/d7b013a675b4/hard_k18__c58bc02409f6.json")
    solution = json.loads(solution_path.read_text(encoding="utf-8"))
    canonical_program = solution["racket_target"]["target_code"]

    draws = []
    correlation_failures = []
    for difficulty in ("easy", None, "hard"):
        for seed in range(24):
            grid = gen.generate(seed, seed * 13 + 5, difficulty=difficulty)
            records = [component_record(grid, comp) for comp in components(grid)]
            hole_order = [r["color"] for r in sorted(records, key=lambda r: (r["holes"], r["height"], r["width"], r["color"]))]
            area_order = [r["color"] for r in sorted(records, key=lambda r: (r["area"], r["height"], r["width"], r["color"]))]
            if hole_order != area_order:
                correlation_failures.append({"difficulty": difficulty, "seed": seed, "records": records})
            draws.append({"difficulty": difficulty, "seed": seed, "hole_area": sorted((r["holes"], r["area"]) for r in records)})

    grid = witness_input()
    records = [component_record(grid, comp) for comp in components(grid)]
    expected_hole = pack(records, lambda r: (r["holes"], r["height"], r["width"], r["color"]))
    expected_area = pack(records, lambda r: (r["area"], r["height"], r["width"], r["color"]))
    bridge = RacketBridge(timeout=30, max_calls_before_restart=8)
    try:
        true_output = bridge.eval_text(f"({wrap_rule(canonical_program)} {literal(grid)})")
        area_output = bridge.eval_text(f"({wrap_rule(AREA_PROGRAM)} {literal(grid)})")
        runtime = bridge.runtime_identity
    finally:
        bridge.close()
    if true_output != expected_hole:
        raise AssertionError("canonical Racket disagrees with independent hole-order packer")
    if area_output != expected_area:
        raise AssertionError("area Racket disagrees with independent area-order packer")
    changed = sum(a != b for ra, rb in zip(true_output, area_output) for a, b in zip(ra, rb))
    if changed == 0:
        raise AssertionError("witness does not distinguish hole and area order")

    report = {
        "schema": "arcpuzzles-peer-learnability-probe-v1",
        "task_id": TASK_ID,
        "status": "finding",
        "source": {"path": str(source_path), "sha256": source_sha},
        "generated_probe": {
            "draws": len(draws),
            "difficulties": ["easy", "default", "hard"],
            "area_order_disagreements": len(correlation_failures),
            "observed_hole_area_profiles": sorted({tuple(map(tuple, row["hole_area"])) for row in draws}),
        },
        "finding": (
            "Every sampled ordinary draw makes component area strictly increase with hole count, "
            "so sorting crops by area fits all generated lessons even though the canonical rule sorts by holes."
        ),
        "witness": {
            "input": grid,
            "component_records": [{k: r[k] for k in ("holes", "area", "height", "width", "color")} for r in records],
            "canonical_output": true_output,
            "area_shortcut_output": area_output,
            "changed_cells": changed,
            "canonical_program_sha256": hashlib.sha256(canonical_program.encode()).hexdigest(),
            "area_program_sha256": hashlib.sha256(AREA_PROGRAM.encode()).hexdigest(),
            "racket_evaluations": 2,
        },
        "racket": runtime,
        "recommended_repair": (
            "Add at least one ordinary component family where area order conflicts with hole-count order "
            "(for example a 3x3 solid of area 9 paired with a 3x3 one-hole ring of area 8), then retain a lesson-level rival check."
        ),
        "limits": "72 generated draws and one authored protected-Racket disagreement witness; no source repair or owner approval.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "draws": len(draws), "area_order_disagreements": len(correlation_failures), "changed_cells": changed, "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
