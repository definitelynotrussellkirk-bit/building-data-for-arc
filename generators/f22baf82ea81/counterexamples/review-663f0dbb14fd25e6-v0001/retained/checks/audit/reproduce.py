#!/usr/bin/env python3
"""Reproduce the two assigned adversarial distribution audits.

Run from the packet's ``repo`` directory with::

    PYTHONPATH=shared/runtime:src python3 ../checks/audit/reproduce.py

The script never supplies labels. It measures sampler support, checks the saved
counterexamples against ``self_check``, and compares the saved wrong-rival grid
to the already retained Racket output.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

HERE = Path(__file__).resolve().parent
REPO = Path.cwd().resolve()
if not (REPO / "generators").is_dir():
    raise SystemExit("run from the packet repo directory")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def nonzero_bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return min(r for r, _ in cells), max(r for r, _ in cells), min(c for _, c in cells), max(c for _, c in cells)


def audit_f22():
    task = "f22baf82ea81"
    gen, path = load(task)
    solid = centered = 0
    signatures = set()
    for index in range(200):
        grid = gen.generate(100 + index, index)
        r0, r1, c0, c1 = nonzero_bbox(grid)
        outer = grid[r0][c0]
        inner_cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                       if grid[r][c] != outer]
        ir0, ir1 = min(r for r, _ in inner_cells), max(r for r, _ in inner_cells)
        ic0, ic1 = min(c for _, c in inner_cells), max(c for _, c in inner_cells)
        is_solid = len(inner_cells) == (ir1 - ir0 + 1) * (ic1 - ic0 + 1)
        solid += is_solid
        rh, rw, ih, iw = r1-r0+1, c1-c0+1, ir1-ir0+1, ic1-ic0+1
        is_centered = (ir0, ic0) == (r0 + (rh-ih)//2, c0 + (rw-iw)//2)
        centered += is_centered
        signatures.add((rh, rw, ih, iw, is_solid, is_centered))
    inp = json.loads((HERE / task / "input.json").read_text())
    racket = json.loads((HERE / task / "racket.json").read_text())["results"][0]["output"]
    rival = json.loads((HERE / task / "rival.json").read_text())
    report = {
        "schema": "arc-audit-probe-v1", "task_id": task,
        "generator_sha256": sha(path), "samples": 200,
        "solid_inner_rectangle": solid,
        "centered_inner_rectangle": centered,
        "distinct_shape_signatures": len(signatures),
        "counterexample_self_check": gen.self_check(inp),
        "rival_differs_from_racket": rival != racket,
        "finding": "sampler invariant not required by self_check: inner color is always a centered solid rectangle",
    }
    (HERE / task / "probe.json").write_text(json.dumps(report, indent=2) + "\n")


def audit_b7():
    task = "b7fbb716d189"
    gen, path = load(task)
    positions = []
    for index in range(100):
        grid = gen.generate(500 + index, index)
        positions.append(next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                              if value in {1, 2, 3, 4}))
    canonical = canonical_pairs(task, root=REPO)
    canonical_tokens = []
    for pair in canonical:
        pos = [(r, c, value) for r, row in enumerate(pair["input"])
               for c, value in enumerate(row) if value in {1, 2, 3, 4}]
        canonical_tokens.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"], "tokens": pos,
            "self_check": gen.self_check(pair["input"]),
        })
    inp = json.loads((HERE / task / "input.json").read_text())
    racket = json.loads((HERE / task / "racket.json").read_text())["results"][0]["output"]
    rival = json.loads((HERE / task / "rival.json").read_text())
    report = {
        "schema": "arc-audit-probe-v1", "task_id": task,
        "generator_sha256": sha(path), "samples": 100,
        "generated_token_positions": sorted({str(p) for p in positions}),
        "canonical_tokens": canonical_tokens,
        "counterexample_self_check": gen.self_check(inp),
        "rival_differs_from_racket": rival != racket,
        "finding": "sampler fixes the control token at top-left although canonical authority places it at other corners",
    }
    (HERE / task / "probe.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    audit_f22()
    audit_b7()
    print("wrote", HERE / "f22baf82ea81/probe.json")
    print("wrote", HERE / "b7fbb716d189/probe.json")
