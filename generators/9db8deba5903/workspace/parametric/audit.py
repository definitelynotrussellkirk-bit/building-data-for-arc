#!/usr/bin/env python3
"""Protected-Racket finite-rival audit and causal witness builder.

This is a task-local reviewer tool, not part of episode generation.  It executes
all retained labels and each declared wrong rule in the protected runtime, then
writes compact JSON evidence for exact current source bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("rotation_component_audit_prototype", HERE / "prototype.py")
ADAPTER = _load("rotation_component_audit_adapter", HERE / "adapter.py")

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


REPEAT_IDENTITY = """(rule! (lambda (g)
  (let* ((n (rows g)))
    (build-grid (* n 2) (* n 2) (r c)
      (at g (mod r n) (mod c n))))))"""

SWAP_QUARTER_TURNS = """(rule! (lambda (g)
  (let* ((n (rows g)))
    (build-grid (* n 2) (* n 2) (r c)
      (let ((qr (/ r n)) (qc (/ c n))
            (lr (mod r n)) (lc (mod c n)))
        (cond
          ((and (zero? qr) (zero? qc)) (at g lr lc))
          ((and (zero? qr) (= qc 1)) (at g (- (- n 1) lc) lr))
          ((and (= qr 1) (zero? qc)) (at g (- (- n 1) lr) (- (- n 1) lc)))
          (else (at g lc (- (- n 1) lr)))))))))"""

RECOLOR_ALL_TARGET = """(rule! (lambda (g)
  (let* ((n (rows g))
         (mosaic
          (build-grid (* n 2) (* n 2) (r c)
            (let ((qr (/ r n)) (qc (/ c n))
                  (lr (mod r n)) (lc (mod c n)))
              (cond
                ((and (zero? qr) (zero? qc)) (at g lr lc))
                ((and (zero? qr) (= qc 1)) (at g lc (- (- n 1) lr)))
                ((and (= qr 1) (zero? qc)) (at g (- (- n 1) lr) (- (- n 1) lc)))
                (else (at g (- (- n 1) lc) lr)))))))
    (recolor mosaic 1 9))))"""

LARGEST_BEFORE_TILING = """(rule! (lambda (g)
  (let* ((targets (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0)))
         (largest (first (sort targets (lambda (a b) (> (obj-size a) (obj-size b))))))
         (marked (paint-cells g (obj-cells largest) 9))
         (n (rows marked)))
    (build-grid (* n 2) (* n 2) (r c)
      (let ((qr (/ r n)) (qc (/ c n))
            (lr (mod r n)) (lc (mod c n)))
        (cond
          ((and (zero? qr) (zero? qc)) (at marked lr lc))
          ((and (zero? qr) (= qc 1)) (at marked lc (- (- n 1) lr)))
          ((and (= qr 1) (zero? qc)) (at marked (- (- n 1) lr) (- (- n 1) lc)))
          (else (at marked (- (- n 1) lc) lr))))))))"""

REPEAT_IDENTITY_INTERMEDIATE = """(rule! (lambda (g)
  (let* ((n (rows g))
         (mosaic (build-grid (* n 2) (* n 2) (r c)
                   (at g (mod r n) (mod c n))))
         (targets (filter (lambda (obj) (= (obj-color obj) 1)) (objects mosaic 0)))
         (largest (first (sort targets (lambda (a b) (> (obj-size a) (obj-size b)))))))
    (paint-cells mosaic (obj-cells largest) 9))))"""

FIRST_COMPONENT = """(rule! (lambda (g)
  (let* ((n (rows g))
         (mosaic
          (build-grid (* n 2) (* n 2) (r c)
            (let ((qr (/ r n)) (qc (/ c n))
                  (lr (mod r n)) (lc (mod c n)))
              (cond
                ((and (zero? qr) (zero? qc)) (at g lr lc))
                ((and (zero? qr) (= qc 1)) (at g lc (- (- n 1) lr)))
                ((and (= qr 1) (zero? qc)) (at g (- (- n 1) lr) (- (- n 1) lc)))
                (else (at g (- (- n 1) lc) lr))))))
         (target (first (filter (lambda (obj) (= (obj-color obj) 1))
                                (objects mosaic 0)))))
    (paint-cells mosaic (obj-cells target) 9))))"""

RIVALS = {
    "canonical": {
        "repeat_identity": REPEAT_IDENTITY,
        "swap_quarter_turns": SWAP_QUARTER_TURNS,
        "apply_relay_stage": ADAPTER.program({"mode": "largest_tiled_component"}),
    },
    "largest_tiled_component": {
        "skip_stage_b": ADAPTER.program({"mode": "canonical"}),
        "recolor_all_target_cells": RECOLOR_ALL_TARGET,
        "largest_before_tiling": LARGEST_BEFORE_TILING,
        "repeat_identity_intermediate": REPEAT_IDENTITY_INTERMEDIATE,
        "row_major_first_component": FIRST_COMPONENT,
    },
}

FIXTURE = [
    [8, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1],
    [0, 0, 1, 1, 0, 0],
    [0, 0, 1, 0, 8, 0],
    [1, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 8],
]


def _literal(grid) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _execute(bridge: RacketBridge, program: str, grid):
    return bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})")


def run_audit(seeds=(0, 17)) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "rotation-component-finite-rival-audit-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "seeds": list(seeds),
        "jobs": [],
        "protected_racket_evaluations": 0,
        "harmful_survivors": [],
    }
    bridge = RacketBridge()
    try:
        result["runtime"] = bridge.runtime_identity
        for seed in seeds:
            for mode in PROTOTYPE.MODES:
                episode = ADAPTER.generate(seed, {"mode": mode}, demos=2, queries=4)
                pairs = episode["train"] + episode["test"]
                intended_program = ADAPTER.program({"mode": mode})
                intended_matches = []
                for pair in pairs:
                    actual = _execute(bridge, intended_program, pair["input"])
                    result["protected_racket_evaluations"] += 1
                    intended_matches.append(actual == pair["output"])
                if not all(intended_matches):
                    raise AssertionError((seed, mode, "intended label mismatch"))

                rival_rows = []
                for name, program in RIVALS[mode].items():
                    matches = []
                    for pair in pairs:
                        actual = _execute(bridge, program, pair["input"])
                        result["protected_racket_evaluations"] += 1
                        matches.append(actual == pair["output"])
                    demo_fit = all(matches[:2])
                    query_disagreement = not all(matches[2:])
                    rival_rows.append({
                        "name": name,
                        "program_sha256": _sha(program),
                        "demo_matches": matches[:2],
                        "query_matches": matches[2:],
                        "fits_all_demos": demo_fit,
                        "disagrees_on_query": query_disagreement,
                    })
                    if demo_fit and query_disagreement:
                        result["harmful_survivors"].append({
                            "seed": seed,
                            "mode": mode,
                            "rival": name,
                        })
                result["jobs"].append({
                    "seed": seed,
                    "mode": mode,
                    "intended_program_sha256": _sha(intended_program),
                    "intended_label_matches": intended_matches,
                    "rivals": rival_rows,
                })
    finally:
        bridge.close()
    if result["harmful_survivors"]:
        raise AssertionError(result["harmful_survivors"])
    return result


def run_witness() -> dict[str, Any]:
    intended_program = ADAPTER.program({"mode": "largest_tiled_component"})
    wrong_program = REPEAT_IDENTITY_INTERMEDIATE
    intended_intermediate = PROTOTYPE.tile_rotations(FIXTURE)
    wrong_intermediate = PROTOTYPE._repeat_identity(FIXTURE)
    bridge = RacketBridge()
    try:
        intended_output = _execute(bridge, intended_program, FIXTURE)
        wrong_output = _execute(bridge, wrong_program, FIXTURE)
        runtime = bridge.runtime_identity
    finally:
        bridge.close()
    expected = PROTOTYPE.solve(FIXTURE, "largest_tiled_component")
    if intended_output != expected or wrong_output == intended_output:
        raise AssertionError("causal witness did not replay")
    return {
        "schema": "arcpuzzles-parametric-sequential-witness-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "setting": {"mode": "largest_tiled_component"},
        "step_a": "Construct the canonical 2x2 rotation mosaic: identity, CCW, 180, CW.",
        "intermediate": "The 12x12 rotation mosaic; rotated copies merge color-1 objects across seams.",
        "step_b": "Find the unique largest four-connected color-1 component in that mosaic and recolor it 9.",
        "why_b_depends_on_a": (
            "The canonical intermediate creates a unique size-8 seam component. "
            "Replacing it with four identity copies leaves only size-4 maxima and changes the selected cells."
        ),
        "input": FIXTURE,
        "intended_program": intended_program,
        "intended_program_sha256": _sha(intended_program),
        "wrong_intermediate_program": wrong_program,
        "wrong_intermediate_program_sha256": _sha(wrong_program),
        "intended_intermediate": intended_intermediate,
        "wrong_intermediate": wrong_intermediate,
        "intended_component_sizes": PROTOTYPE.analyze(FIXTURE)["component_sizes"],
        "intended_output": intended_output,
        "wrong_output": wrong_output,
        "outputs_differ": intended_output != wrong_output,
        "runtime": runtime,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path, required=True)
    args = parser.parse_args()
    audit = run_audit()
    witness = run_witness()
    args.audit_out.parent.mkdir(parents=True, exist_ok=True)
    args.witness_out.parent.mkdir(parents=True, exist_ok=True)
    args.audit_out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    args.witness_out.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "audit": str(args.audit_out),
        "witness": str(args.witness_out),
        "jobs": len(audit["jobs"]),
        "protected_racket_evaluations": audit["protected_racket_evaluations"],
        "harmful_survivors": len(audit["harmful_survivors"]),
        "outputs_differ": witness["outputs_differ"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
