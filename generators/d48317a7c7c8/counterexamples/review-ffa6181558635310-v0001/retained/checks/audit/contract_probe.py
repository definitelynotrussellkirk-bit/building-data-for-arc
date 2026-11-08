#!/usr/bin/env python3
"""Independent read-only probes for the two assigned audit generators."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path.cwd()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0]) if grid else 0]


def components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        todo = [unseen.pop()]
        comp = []
        while todo:
            r, c = todo.pop()
            comp.append((r, c))
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen:
                    unseen.remove(q)
                    todo.append(q)
        out.append(comp)
    return out


def straight_len3(comp: list[tuple[int, int]]) -> bool:
    if len(comp) != 3:
        return False
    rs = {r for r, _ in comp}; cs = {c for _, c in comp}
    if len(rs) == 1:
        xs = sorted(cs); return xs == list(range(xs[0], xs[0] + 3))
    if len(cs) == 1:
        xs = sorted(rs); return xs == list(range(xs[0], xs[0] + 3))
    return False


def load_generator(tid: str):
    source = ROOT / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{tid}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, source


def probe_d483() -> dict[str, Any]:
    tid = "d48317a7c7c8"
    mod, source = load_generator(tid)
    rejected = None
    try:
        mod.generate(0, 0, difficulty="easy", n_bars=10)
    except Exception as exc:  # exact public contract should accept declared valid value
        rejected = {"type": type(exc).__name__, "message": str(exc)}
    a = mod.generate(0, 0, difficulty="medium", palette_kind="default")
    b = mod.generate(0, 0, difficulty="medium", palette_kind="varied")
    unknown = None
    try:
        g = mod.generate(0, 0, difficulty="medium", __override_contract_unknown_axis__=1)
        unknown = {"accepted": True, "shape": shape(g)}
    except Exception as exc:
        unknown = {"accepted": False, "type": type(exc).__name__, "message": str(exc)}

    samples = []
    non_target_components = 0
    non_yellow_nonzero = 0
    for band in ("easy", "medium", "hard"):
        for i in range(100):
            g = mod.generate(314159, i, difficulty=band)
            comps = components(g, 4)
            non_target_components += sum(not straight_len3(c) for c in comps)
            non_yellow_nonzero += sum(v not in (0, 4) for row in g for v in row)
            samples.append({"band": band, "sample_index": i, "shape": shape(g), "n_components": len(comps)})
    return {
        "task_id": tid,
        "generator_sha256": sha256(source),
        "rule_hash": "b2af6531f18d",
        "command": ["python3", "run_with_racket.py", "python3", "../checks/audit/contract_probe.py", tid, "--out", f"../checks/audit/{tid}/contract-probe.json"],
        "cwd": "packet_root (payload cwd repo)",
        "reproduced_contract_defect": {
            "declared_n_bars_valid": "1..10",
            "easy_n_bars_10": rejected,
            "unknown_key_probe": unknown,
            "palette_kind_default_equals_varied": a == b,
        },
        "distribution_probe": {
            "seed": 314159,
            "samples_per_band": 100,
            "total_samples": len(samples),
            "non_target_yellow_components": non_target_components,
            "non_yellow_nonzero_cells": non_yellow_nonzero,
            "interpretation": "Every sampled ordinary input contains only exact straight length-3 yellow targets; no distractor demonstrates the exact-length/color filter.",
        },
    }


def bbox(grid: list[list[int]]) -> tuple[int,int,int,int]:
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def probe_6eb() -> dict[str, Any]:
    tid = "6ebcd82f8e83"
    mod, source = load_generator(tid)
    overrides = {}
    for axis, lo, hi in (("grid_h",5,12),("grid_w",6,14),("bbox_side",2,9)):
        g_lo = mod.generate(0, 0, difficulty="easy", **{axis: lo})
        g_hi = mod.generate(0, 0, difficulty="easy", **{axis: hi})
        overrides[axis] = {
            "requested_low": lo,
            "requested_high": hi,
            "low_shape": shape(g_lo),
            "high_shape": shape(g_hi),
            "byte_identical": g_lo == g_hi,
            "low_bbox": list(bbox(g_lo)),
            "high_bbox": list(bbox(g_hi)),
        }
    unknown = None
    try:
        g = mod.generate(0, 0, difficulty="easy", __override_contract_unknown_axis__=1)
        unknown = {"accepted": True, "shape": shape(g)}
    except Exception as exc:
        unknown = {"accepted": False, "type": type(exc).__name__, "message": str(exc)}

    missing_tlbr = 0
    hard_oob = []
    for band in ("easy", "medium", "hard"):
        for i in range(100):
            g = mod.generate(271828, i, difficulty=band)
            r1,c1,r2,c2 = bbox(g)
            color = next(v for row in g for v in row if v)
            if g[r1][c1] != color or g[r2][c2] != color:
                missing_tlbr += 1
            if band == "hard" and (len(g) > 12 or len(g[0]) > 14):
                hard_oob.append({"sample_index": i, "shape": shape(g)})
    return {
        "task_id": tid,
        "generator_sha256": sha256(source),
        "rule_hash": "a9a3efecb347",
        "command": ["python3", "run_with_racket.py", "python3", "../checks/audit/contract_probe.py", tid, "--out", f"../checks/audit/{tid}/contract-probe.json"],
        "cwd": "packet_root (payload cwd repo)",
        "reproduced_contract_defect": {
            "exact_override_pairs": overrides,
            "unknown_key_probe": unknown,
            "note": "All three advertised exact overrides are ignored for the same seed/sample; low and high requests produce byte-identical grids.",
        },
        "distribution_probe": {
            "seed": 271828,
            "samples_per_band": 100,
            "total_samples": 300,
            "samples_missing_mandatory_tl_and_br_bbox_markers": missing_tlbr,
            "hard_samples_outside_declared_grid_bounds": len(hard_oob),
            "first_hard_out_of_bounds_witnesses": hard_oob[:5],
            "interpretation": "The sampler always anchors the same diagonal and hard mode often exceeds AXES bounds, restricting geometry while violating its own declared domain.",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id", choices=["d48317a7c7c8", "6ebcd82f8e83"])
    ap.add_argument("--out", required=True)
    ns = ap.parse_args()
    data = probe_d483() if ns.task_id == "d48317a7c7c8" else probe_6eb()
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps(data, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
